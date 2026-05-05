"""``batch-job/submit`` skill script.

Constructs a ``batch-job-request`` envelope and posts it as a comment
on the issue. Pre-flight: validates that the issue carries the
agent-task label and that args conform to the command schema.

Note: the issue is **not** required to be locked at submit time. The
original draft of the protocol locked agent issues at creation, but
GitHub refuses comments from ``GITHUB_TOKEN`` on locked issues, which
breaks the batch-job-handler's terminal envelope writes. Locking is
therefore deferred to ``close_on_merge`` (post-merge); the
batch-job-handler's ``if:`` filter (label + author) is what makes
foreign comments inert.

Importable: :func:`submit` (programmatic) or run as
``python -m skills.batch-job.submit`` (not wired up here for the POC).
"""

from __future__ import annotations

import json
from typing import Any, Optional

try:
    from .common import (
        GitHubClient,
        iso_now,
        load_config,
        load_schema,
        parse_agent_meta,
        repo_root,
        validate,
    )
except ImportError:
    # Standalone (not imported as a package): load the sibling
    # ``common.py`` by file path to avoid collisions with any other
    # ``common`` already in ``sys.modules``.
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_batchjob_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_batchjob_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    iso_now = _mod.iso_now
    load_config = _mod.load_config
    load_schema = _mod.load_schema
    parse_agent_meta = _mod.parse_agent_meta
    repo_root = _mod.repo_root
    validate = _mod.validate


class PreflightError(RuntimeError):
    """Raised when the issue is not in a state that accepts jobs."""


def preflight(
    client: GitHubClient,
    issue_number: int,
    *,
    agent_id: Optional[str] = None,
    agent_login: Optional[str] = None,
    agent_task_label: str = "agent-task",
) -> dict[str, Any]:
    issue = client.get_issue(issue_number)
    # Intentionally NOT checking ``issue.get("locked")`` here: locking
    # is deferred until post-merge (see module docstring).
    labels = {l["name"] for l in (issue.get("labels") or [])}
    if agent_task_label not in labels:
        raise PreflightError(
            f"issue #{issue_number} missing label {agent_task_label}"
        )
    meta = parse_agent_meta(issue.get("body"))
    if meta is None:
        raise PreflightError(f"issue #{issue_number} body has no agent-meta")
    if agent_id is not None and meta.get("agent_id") != agent_id:
        raise PreflightError(
            f"agent_id mismatch: meta has {meta.get('agent_id')!r}, "
            f"caller has {agent_id!r}"
        )
    if agent_login is not None:
        creator = (issue.get("user") or {}).get("login")
        if creator != agent_login:
            raise PreflightError(
                f"issue creator {creator!r} != agent_login {agent_login!r}"
            )
    return meta


def submit(
    client: GitHubClient,
    *,
    issue_number: int,
    command: str,
    args: dict[str, Any],
    branch: str,
    commit_sha: str,
    subagent_id: str,
    agent_id: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build the envelope and post it. Returns the new comment dict."""
    cfg = config or load_config(repo_root() / ".agent" / "config.json")
    agent_login = cfg["agent_login"]
    agent_task_label = cfg.get("labels", {}).get("agent_task", "agent-task")

    if command not in cfg.get("commands", []):
        raise ValueError(f"unknown command: {command}")

    # Pre-flight.
    preflight(
        client,
        issue_number,
        agent_id=agent_id,
        agent_login=agent_login,
        agent_task_label=agent_task_label,
    )

    # Validate args against the command's schema.
    schema = load_schema(f"commands/{command}.schema.json", repo_root())
    args_schema = schema.get("properties", {}).get("args")
    if args_schema is not None:
        validate(args, args_schema)

    envelope = {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "command": command,
        "args": args,
        "branch": branch,
        "commit_sha": commit_sha,
        "subagent_id": subagent_id,
        "submitted_at": iso_now(),
        "run_status": None,
        "agent_ack": None,
    }

    body = json.dumps(envelope, indent=2)
    comment = client.add_comment(issue_number, body)
    return comment
