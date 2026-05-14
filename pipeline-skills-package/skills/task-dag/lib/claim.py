"""``task-dag/claim`` — pick up an unclaimed or stale issue.

Algorithm (§10):
1. Iterate open issues with the ``agent-task`` label.
2. Select one whose ``status`` is ``null``, OR whose ``status`` is
   ``working`` with a ``status_ts`` older than
   ``issue.stale_seconds``.
3. Write our agent-id and timestamp into the agent-meta block.
4. Re-read 5s later (or with a configurable verify delay) to confirm
   ownership.

The in-memory POC verifies immediately (verify_delay defaults to 0).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Optional

try:
    from .common import (
        GitHubClient,
        iso_now,
        load_config,
        new_uuid,
        parse_agent_meta,
        render_agent_meta,
        repo_root,
    )
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_taskdag_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_taskdag_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    iso_now = _mod.iso_now
    load_config = _mod.load_config
    new_uuid = _mod.new_uuid
    parse_agent_meta = _mod.parse_agent_meta
    render_agent_meta = _mod.render_agent_meta
    repo_root = _mod.repo_root


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _is_stale(meta: dict[str, Any], stale_seconds: float) -> bool:
    if meta.get("status") != "working":
        return False
    parsed = _parse_iso(meta.get("status_ts"))
    if parsed is None:
        return True  # missing timestamp counts as stale
    age = (datetime.now(tz=timezone.utc) - parsed).total_seconds()
    return age > stale_seconds


def select_candidate(
    issues: Iterable[dict[str, Any]],
    *,
    agent_task_label: str,
    stale_seconds: float,
) -> Optional[tuple[dict[str, Any], dict[str, Any]]]:
    """Return ``(issue, meta)`` for the first claimable issue."""
    null_first: list[tuple[dict[str, Any], dict[str, Any]]] = []
    stale: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for issue in issues:
        labels = {l["name"] for l in (issue.get("labels") or [])}
        if agent_task_label not in labels:
            continue
        meta = parse_agent_meta(issue.get("body"))
        if meta is None:
            continue
        status = meta.get("status")
        if status is None:
            null_first.append((issue, meta))
        elif _is_stale(meta, stale_seconds):
            stale.append((issue, meta))
    if null_first:
        return null_first[0]
    if stale:
        return stale[0]
    return None


def claim(
    client: GitHubClient,
    *,
    agent_id: Optional[str] = None,
    candidate_issues: Optional[list[dict[str, Any]]] = None,
    config: Optional[dict[str, Any]] = None,
    verify_delay: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Optional[dict[str, Any]]:
    """Claim one issue. Returns ``{issue, meta}`` on success, else None.

    ``candidate_issues`` allows callers to pass a pre-listed set; the
    in-memory client doesn't expose a generic list-issues call.
    """
    cfg = config or load_config(repo_root() / ".agent" / "config.json")
    agent_id = agent_id or new_uuid()
    agent_task_label = cfg.get("labels", {}).get("agent_task", "agent-task")
    stale_seconds = float(cfg.get("issue", {}).get("stale_seconds", 7200))

    if candidate_issues is None:
        # In a real client we'd call an issue-search; the in-memory
        # client only exposes get_issue. Skill callers typically pass
        # the candidate list explicitly.
        candidate_issues = []

    pick = select_candidate(
        candidate_issues,
        agent_task_label=agent_task_label,
        stale_seconds=stale_seconds,
    )
    if pick is None:
        return None

    issue, meta = pick
    number = issue["number"]
    session_id = new_uuid()

    new_meta = dict(meta)
    new_meta["agent_id"] = agent_id
    new_meta["session_id"] = session_id
    new_meta["status"] = "working"
    new_meta["status_ts"] = iso_now()

    new_body = render_agent_meta(new_meta, prose=_extract_prose(issue.get("body") or ""))
    client.update_issue(number, body=new_body)

    if verify_delay > 0:
        sleep(verify_delay)

    fresh = client.get_issue(number)
    fresh_meta = parse_agent_meta(fresh.get("body")) or {}
    if fresh_meta.get("agent_id") != agent_id:
        # We lost the race; abandon quietly.
        return None

    return {
        "issue": fresh,
        "meta": fresh_meta,
        "agent_id": agent_id,
        "session_id": session_id,
    }


def _extract_prose(body: str) -> str:
    """Return everything before the agent-meta fenced block, if any."""
    marker = "```agent-meta"
    idx = body.find(marker)
    if idx == -1:
        return body
    return body[:idx].rstrip()


def heartbeat(
    client: GitHubClient,
    *,
    issue_number: int,
    agent_id: str,
) -> bool:
    """Refresh ``status_ts`` if we still own the issue. Returns True if so."""
    issue = client.get_issue(issue_number)
    meta = parse_agent_meta(issue.get("body")) or {}
    if meta.get("agent_id") != agent_id:
        return False
    meta["status_ts"] = iso_now()
    new_body = render_agent_meta(meta, prose=_extract_prose(issue.get("body") or ""))
    client.update_issue(issue_number, body=new_body)
    return True


def abandon(
    client: GitHubClient,
    issue_number: int,
    reason: str,
) -> dict[str, Any]:
    """Mark an issue as ``abandoned`` (SPEC §4.1, §12).

    Sets ``status="abandoned"`` in the issue's agent-meta and posts a
    comment "Abandoning: <reason>". Returns the updated meta dict.

    Idempotent: if the issue is already abandoned, no second comment is
    posted and the meta is returned unchanged.
    """
    issue = client.get_issue(issue_number)
    meta = parse_agent_meta(issue.get("body")) or {}

    if meta.get("status") == "abandoned":
        return meta

    meta["status"] = "abandoned"
    meta["status_ts"] = iso_now()
    new_body = render_agent_meta(
        meta, prose=_extract_prose(issue.get("body") or "")
    )
    client.update_issue(issue_number, body=new_body)
    client.add_comment(issue_number, f"Abandoning: {reason}")
    return meta
