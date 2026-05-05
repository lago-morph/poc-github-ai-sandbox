"""``batch-job-handler`` script (§7.2).

Loads a comment from GitHub via the abstract :class:`GitHubClient`,
parses the JSON envelope, dispatches to a registered command handler,
writes structured logs into ``_agent_runs/runs/<issue>/<comment>/`` and
edits the comment with the terminal envelope.

Importable as ``run(client, issue_number, comment_id, ...)`` for tests.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )
else:
    from .common import (
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    *,
    workflow_run_id: int = 0,
    workspace: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Process a single comment. Returns a summary dict for tests."""
    cfg = config or load_config(Path(repo_root) / ".agent" / "config.json")

    comment = client.get_comment(comment_id)
    raw_body = comment.get("body") or ""

    # Step 1: parse envelope ----------------------------------------------
    parsed: Optional[dict[str, Any]]
    try:
        parsed = json.loads(raw_body)
    except (json.JSONDecodeError, TypeError):
        parsed = None

    if not has_protocol_markers(parsed):
        return {"action": "ignored", "reason": "no_protocol_markers"}

    assert isinstance(parsed, dict)  # for type checkers

    # Idempotency on already-terminal envelopes (webhook redelivery).
    if is_terminal_run_status(parsed.get("run_status")):
        return {"action": "noop", "reason": "already_terminal", "run_status": parsed["run_status"]}

    envelope_schema = load_schema("comment-envelope.schema.json", repo_root)

    started_at = iso_now()

    # Validate base envelope shape.
    try:
        validate(parsed, envelope_schema)
    except Exception as e:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="schema_validation_failed",
            error_detail=str(e),
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    command = parsed.get("command")
    if not command or command not in cfg.get("commands", []):
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="unknown_command",
            error_detail=f"command not in registry: {command!r}",
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    # Validate args via per-command schema.
    cmd_schema_path = f"commands/{command}.schema.json"
    try:
        cmd_schema = load_schema(cmd_schema_path, repo_root)
    except FileNotFoundError:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="unknown_command",
            error_detail=f"no schema file for command {command}",
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    args_schema = cmd_schema.get("properties", {}).get("args")
    if args_schema:
        try:
            validate(parsed.get("args", {}), args_schema)
        except Exception as e:
            return _write_parse_error(
                client,
                comment_id,
                original_body=raw_body,
                error_kind="schema_validation_failed",
                error_detail=f"args: {e}",
                workflow_run_id=workflow_run_id,
                started_at=started_at,
            )

    # Step 3: branch+SHA check --------------------------------------------
    branch = parsed["branch"]
    expected_sha = parsed["commit_sha"]
    head_sha = client.get_branch_head_sha(branch)
    if head_sha is None:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"branch does not exist: {branch}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )
    if head_sha != expected_sha:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"HEAD={head_sha} != commit_sha={expected_sha}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    # Step 4: mark running ------------------------------------------------
    running_envelope = dict(parsed)
    running_envelope["run_status"] = "running"
    running_envelope["run_started_at"] = started_at
    running_envelope["workflow_run_id"] = workflow_run_id
    running_envelope["checked_out_sha"] = head_sha
    client.update_comment(comment_id, json.dumps(running_envelope, indent=2))

    # Step 5: dispatch ----------------------------------------------------
    log_writer = LogWriter(
        max_chunk_bytes_compressed=cfg.get("logs", {}).get("max_chunk_bytes_compressed", 524_288)
    )

    try:
        handler_fn = _load_command_handler(command)
        summary = handler_fn(parsed.get("args", {}) or {}, log_writer, workspace)
        run_status = "completed"
        error_kind: Optional[str] = None
        error_detail: Optional[str] = None
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log_writer.write({
            "ts": iso_now(),
            "stream": "stderr",
            "phase": "exec",
            "data": tb,
        })
        summary = {
            "error_kind": type(e).__name__,
            "error_detail": str(e),
        }
        run_status = "error"
        error_kind = type(e).__name__
        error_detail = str(e)

    finished_at = iso_now()

    # Step 6: validate summary against the command schema -----------------
    summary_schema_key = (
        "summary_completed" if run_status == "completed" else "summary_error"
    )
    summary_schema = cmd_schema.get("properties", {}).get(summary_schema_key)
    if summary_schema is not None:
        try:
            validate(summary, summary_schema)
        except Exception as e:
            run_status = "error"
            error_kind = "summary_schema_violation"
            error_detail = str(e)
            summary = {
                "error_kind": "summary_schema_violation",
                "error_detail": str(e),
            }
            log_writer.write({
                "ts": iso_now(),
                "stream": "stderr",
                "phase": "teardown",
                "data": f"summary schema violation: {e}",
            })

    # Step 7: write logs to _agent_runs ----------------------------------
    chunks = log_writer.finalize()
    manifest = log_writer.manifest(
        command=command,
        args=parsed.get("args", {}) or {},
        checked_out_sha=head_sha,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=0 if run_status == "completed" else 1,
    )

    # Validate the manifest against its schema (defense in depth).
    try:
        manifest_schema = load_schema("log-manifest.schema.json", repo_root)
        validate(manifest, manifest_schema)
    except Exception as e:  # pragma: no cover - manifest is built by us
        log_writer = None  # mark unused
        run_status = "error"
        error_kind = "manifest_schema_violation"
        error_detail = str(e)

    logs_branch = cfg.get("logs", {}).get("branch", "_agent_runs")
    log_dir = f"runs/{issue_number}/{comment_id}"

    summary_json = {
        "summary": summary,
        "run_status": run_status,
        "command": command,
        "args": parsed.get("args", {}) or {},
        "checked_out_sha": head_sha,
        "started_at": started_at,
        "finished_at": finished_at,
    }

    # Ensure the orphan branch exists by writing the manifest first
    # (put_file_contents auto-creates the branch as orphan if missing).
    _retry_put(client, f"{log_dir}/manifest.json",
               json.dumps(manifest, indent=2).encode("utf-8"),
               f"manifest for run {issue_number}/{comment_id}",
               logs_branch)
    for path, gz_bytes, _info in chunks:
        _retry_put(client, f"{log_dir}/{path}", gz_bytes,
                   f"log chunk for {issue_number}/{comment_id}", logs_branch)
    _retry_put(client, f"{log_dir}/summary.json",
               json.dumps(summary_json, indent=2).encode("utf-8"),
               f"summary for {issue_number}/{comment_id}", logs_branch)

    # Step 8: write terminal envelope ------------------------------------
    terminal = dict(running_envelope)
    terminal["run_status"] = run_status
    terminal["run_finished_at"] = finished_at
    terminal["summary"] = summary
    terminal["log_manifest_branch"] = logs_branch
    terminal["log_manifest_path"] = f"{log_dir}/manifest.json"
    if error_kind is not None:
        terminal["error_kind"] = error_kind
    if error_detail is not None:
        terminal["error_detail"] = error_detail

    client.update_comment(comment_id, json.dumps(terminal, indent=2))

    return {
        "action": "ran",
        "command": command,
        "run_status": run_status,
        "summary": summary,
        "log_manifest_path": f"{log_dir}/manifest.json",
        "chunks": [c[0] for c in chunks],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_command_handler(command: str):
    """Import ``.agent/commands/<command>.py`` and return its ``run``."""
    module_name = command.replace("-", "_")
    # Determine the path to the commands directory relative to this file.
    here = os.path.dirname(os.path.abspath(__file__))
    cmd_dir = os.path.normpath(os.path.join(here, os.pardir, "commands"))
    cmd_path = os.path.join(cmd_dir, f"{module_name}.py")
    if not os.path.isfile(cmd_path):
        raise ImportError(f"no command module at {cmd_path}")
    # Use a unique cached module name so dataclass etc. work correctly.
    sys_name = f"_agent_command_{module_name}"
    if sys_name in sys.modules:
        mod = sys.modules[sys_name]
    else:
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location(sys_name, cmd_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not build spec for {cmd_path}")
        mod = module_from_spec(spec)
        sys.modules[sys_name] = mod
        spec.loader.exec_module(mod)
    if not hasattr(mod, "run"):
        raise ImportError(f"command module {module_name} has no run()")
    return mod.run


def _retry_put(
    client: GitHubClient,
    path: str,
    content: bytes,
    message: str,
    branch: str,
    *,
    retries: int = 3,
) -> None:
    """Put a file with simple retry-on-non-fast-forward semantics."""
    last_exc: Optional[BaseException] = None
    for attempt in range(retries):
        try:
            client.put_file_contents(path, content, message, branch)
            return
        except Exception as e:  # noqa: BLE001
            last_exc = e
    if last_exc is not None:
        raise last_exc


def _write_parse_error(
    client: GitHubClient,
    comment_id: int,
    *,
    original_body: str,
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    started_at: str,
) -> dict[str, Any]:
    """Replace the comment body with a ``parse_error`` envelope (§5.2.4)."""
    finished_at = iso_now()
    body = {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "run_status": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
        "original_body_b64": b64_encode(original_body),
        "run_started_at": started_at,
        "run_finished_at": finished_at,
        "workflow_run_id": workflow_run_id,
        "agent_ack": None,
    }
    client.update_comment(comment_id, json.dumps(body, indent=2))
    return {
        "action": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def _write_terminal_error(
    *,
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    envelope: dict[str, Any],
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    run_started_at: str,
    cfg: dict[str, Any],
    repo_root: str,
) -> dict[str, Any]:
    """Write a terminal ``error`` envelope (e.g. branch_sha_mismatch)."""
    finished_at = iso_now()
    terminal = dict(envelope)
    terminal["run_status"] = "error"
    terminal["run_started_at"] = run_started_at
    terminal["run_finished_at"] = finished_at
    terminal["workflow_run_id"] = workflow_run_id
    terminal["error_kind"] = error_kind
    terminal["error_detail"] = error_detail
    terminal["summary"] = {"error_kind": error_kind, "error_detail": error_detail}
    client.update_comment(comment_id, json.dumps(terminal, indent=2))
    return {
        "action": "error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def main() -> int:
    issue = os.environ.get("ISSUE_NUMBER")
    cid = os.environ.get("COMMENT_ID")
    if not issue or not cid:
        print("ISSUE_NUMBER and COMMENT_ID are required", file=sys.stderr)
        return 2
    print(
        "handler: live REST client not implemented in POC; would handle "
        f"issue #{issue} comment {cid}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
