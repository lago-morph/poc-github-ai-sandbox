"""``batch-job/poll`` skill script.

Polls a comment until ``run_status`` is terminal, validates the
summary against the command schema, fetches ``summary.json`` from the
log branch, and writes the agent_ack into the comment envelope.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

try:
    from .common import (
        GitHubClient,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        render_agent_meta,
        repo_root,
        validate,
    )
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_batchjob_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_batchjob_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    is_terminal_run_status = _mod.is_terminal_run_status
    iso_now = _mod.iso_now
    load_config = _mod.load_config
    load_schema = _mod.load_schema
    render_agent_meta = _mod.render_agent_meta
    repo_root = _mod.repo_root
    validate = _mod.validate


class PollTimeout(RuntimeError):
    """Raised when polling exceeds runner-pickup or running deadlines."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def _interval_for_elapsed(elapsed: float, cfg: dict[str, Any]) -> float:
    base = float(cfg["comment"].get("poll_initial_seconds", 30))
    backoff = cfg["comment"].get("poll_backoff", []) or []
    chosen = base
    for step in backoff:
        if elapsed >= float(step["after_seconds"]):
            chosen = float(step["interval_seconds"])
    return chosen


def _open_runner_failure_issue(
    client: GitHubClient,
    *,
    original_envelope: dict[str, Any],
    comment_id: int,
    timeout_kind: str,
    cfg: Optional[dict[str, Any]] = None,
) -> Optional[dict[str, Any]]:
    """Open a fresh ``runner-failure`` issue (SPEC §9.4 steps 4-5, §14).

    The issue is labelled ``runner-failure`` AND ``agent-task`` so it is
    visible to the same protocol that handles agent tasks. Its body
    carries an ``agent-meta`` block with ``status=null`` so the lifecycle
    can be picked up by an ops agent or human triager.

    Returns the created issue dict, or ``None`` if ``client.create_issue``
    is not available (e.g. a stub client). Failures during issue creation
    are swallowed so they do not mask the underlying timeout.
    """
    create_issue = getattr(client, "create_issue", None)
    if create_issue is None:
        return None

    cfg = cfg or {}
    labels_cfg = cfg.get("labels", {}) or {}
    runner_failure_label = labels_cfg.get("runner_failure", "runner-failure")
    agent_task_label = labels_cfg.get("agent_task", "agent-task")

    issue_number = original_envelope.get("issue_number")
    title = (
        f"runner-failure: {timeout_kind} on issue "
        f"#{issue_number} comment {comment_id}"
    )

    now_iso = iso_now()
    meta = {
        "protocol_version": 1,
        "agent_id": None,
        "session_id": None,
        "status": None,
        "status_ts": None,
        "feature_branch": None,
        "base_branch": None,
        "parent_issue": issue_number,
        "depends_on_prs": [],
        "instructions_path": None,
        "instructions_inline": (
            f"Investigate runner failure ({timeout_kind}) for comment "
            f"{comment_id} on issue #{issue_number}."
        ),
        "created_at": now_iso,
        "runner_failure": {
            "timeout_kind": timeout_kind,
            "comment_id": comment_id,
            "ts": now_iso,
        },
    }

    prose = (
        f"Runner failure: `{timeout_kind}` for comment `{comment_id}`"
        f" on issue #{issue_number} at {now_iso}.\n\n"
        f"Original envelope:\n\n```json\n"
        f"{json.dumps(original_envelope, indent=2)}\n```\n"
    )
    body = render_agent_meta(meta, prose=prose)

    try:
        return create_issue(
            title=title,
            body=body,
            labels=[runner_failure_label, agent_task_label],
        )
    except Exception:  # noqa: BLE001 - best-effort; never mask the timeout
        return None


def poll(
    client: GitHubClient,
    *,
    comment_id: int,
    command: str,
    config: Optional[dict[str, Any]] = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
    ack: bool = True,
    heartbeat: Optional[Callable[[], None]] = None,
) -> dict[str, Any]:
    """Poll the comment until terminal. Returns ``{envelope, summary, summary_json}``.

    Raises :class:`PollTimeout` if the runner-pickup or running deadline
    elapses without progress.

    If ``heartbeat`` is provided, it is invoked once per poll iteration
    AFTER the comment has been read (per SPEC §9.4 step 3) — typical
    callers use this to refresh ``status_ts`` on the parent issue while
    waiting for the runner.
    """
    cfg = config or load_config(repo_root() / ".agent" / "config.json")
    pickup_deadline = float(cfg["comment"].get("runner_pickup_timeout_seconds", 300))
    running_deadline = float(cfg["comment"].get("running_timeout_seconds", 3600))
    total_deadline = float(cfg["comment"].get("poll_total_timeout_seconds", 3600))
    logs_branch = cfg.get("logs", {}).get("branch", "_agent_runs")

    started = now()
    saw_running_at: Optional[float] = None
    # Capture the first envelope we read so we can attach it to a
    # runner-failure issue if a timeout fires.
    first_envelope: Optional[dict[str, Any]] = None
    # Try to fold the parent issue id into envelopes that don't already
    # carry it, so the runner-failure issue can reference it.
    parent_issue_number: Optional[int] = None
    try:
        parent_issue_number = client.get_comment(comment_id).get("issue_number")
    except Exception:  # noqa: BLE001
        parent_issue_number = None

    while True:
        comment = client.get_comment(comment_id)
        body = comment.get("body") or "{}"
        try:
            envelope = json.loads(body)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"comment body is not JSON: {e}") from e

        if first_envelope is None:
            first_envelope = dict(envelope)
            if (
                parent_issue_number is not None
                and "issue_number" not in first_envelope
            ):
                first_envelope["issue_number"] = parent_issue_number

        # SPEC §9.4 step 3: heartbeat each cycle after reading the comment,
        # before deciding whether to break or sleep again.
        if heartbeat is not None:
            heartbeat()

        run_status = envelope.get("run_status")
        if is_terminal_run_status(run_status):
            break

        elapsed = now() - started
        if run_status is None and elapsed > pickup_deadline:
            _open_runner_failure_issue(
                client,
                original_envelope=first_envelope or envelope,
                comment_id=comment_id,
                timeout_kind="runner_pickup_timeout",
                cfg=cfg,
            )
            raise PollTimeout(
                "runner_pickup_timeout",
                f"runner did not pick up within {pickup_deadline}s",
            )
        if run_status == "running":
            if saw_running_at is None:
                saw_running_at = now()
            if (now() - saw_running_at) > running_deadline:
                _open_runner_failure_issue(
                    client,
                    original_envelope=first_envelope or envelope,
                    comment_id=comment_id,
                    timeout_kind="running_timeout",
                    cfg=cfg,
                )
                raise PollTimeout(
                    "running_timeout",
                    f"workflow ran longer than {running_deadline}s",
                )
        if elapsed > total_deadline:
            raise PollTimeout(
                "poll_total_timeout",
                f"polling exceeded total deadline {total_deadline}s",
            )

        sleep(_interval_for_elapsed(elapsed, cfg))

    summary = envelope.get("summary") or {}
    summary_json: Optional[dict[str, Any]] = None
    log_path = envelope.get("log_manifest_path")
    if log_path:
        # summary.json sits next to manifest.json
        summary_path = log_path.rsplit("/", 1)[0] + "/summary.json"
        raw = client.get_file_contents(summary_path, logs_branch)
        if raw is not None:
            try:
                summary_json = json.loads(raw)
            except json.JSONDecodeError:
                summary_json = None

    # Validate summary against the schema (defense in depth).
    try:
        schema = load_schema(f"commands/{command}.schema.json", repo_root())
        if envelope.get("run_status") == "completed":
            sub = schema.get("properties", {}).get("summary_completed")
        else:
            sub = schema.get("properties", {}).get("summary_error")
        if sub is not None:
            validate(summary, sub)
    except FileNotFoundError:
        pass

    # Ack ----------------------------------------------------------------
    if ack and envelope.get("agent_ack") != "finished":
        envelope["agent_ack"] = "finished"
        envelope["agent_acked_at"] = iso_now()
        client.update_comment(comment_id, json.dumps(envelope, indent=2))

    return {
        "envelope": envelope,
        "summary": summary,
        "summary_json": summary_json,
    }
