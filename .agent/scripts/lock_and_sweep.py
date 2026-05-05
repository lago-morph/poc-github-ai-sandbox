"""``lock-and-sweep`` script (§7.1).

Run on ``issues.opened``. Validates the issue belongs to the protocol
(creator is ``agent_login`` and body contains a parsable ``agent-meta``
block); applies the ``agent-task`` label; locks the issue; sweeps any
non-agent comments that snuck in pre-lock.

Importable as a module: call :func:`run` directly with a
``GitHubClient`` for tests. The ``__main__`` entry point reads
environment variables (``ISSUE_NUMBER``) and is wired up by the
workflow file.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

# When run as a script the package isn't on sys.path; add repo root.
if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        load_config,
        parse_agent_meta,
    )
else:
    from .common import GitHubClient, load_config, parse_agent_meta


def run(
    client: GitHubClient,
    issue_number: int,
    agent_login: Optional[str] = None,
    agent_task_label: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Apply lock-and-sweep behaviour to an issue.

    Returns a small dict describing what happened (useful for tests).
    """
    cfg = config or load_config()
    agent_login = agent_login or cfg["agent_login"]
    agent_task_label = (
        agent_task_label
        or cfg.get("labels", {}).get("agent_task", "agent-task")
    )

    issue = client.get_issue(issue_number)
    body = issue.get("body") or ""
    creator_login = (issue.get("user") or {}).get("login")

    meta = parse_agent_meta(body)
    if meta is None:
        return {"action": "noop", "reason": "no_agent_meta"}
    if creator_login != agent_login:
        return {"action": "noop", "reason": "creator_not_agent_login"}

    # 1. Apply label.
    client.add_label(issue_number, agent_task_label)
    # 2. Lock the issue.
    client.lock_issue(issue_number)

    # 3. Sweep non-agent comments.
    deleted = 0
    kept_unexpected = 0
    for c in client.list_comments(issue_number):
        author = (c.get("user") or {}).get("login")
        cid = c["id"]
        if author == agent_login:
            kept_unexpected += 1
            continue
        client.delete_comment(cid)
        deleted += 1

    return {
        "action": "locked",
        "label_applied": agent_task_label,
        "deleted_comments": deleted,
        "kept_agent_comments": kept_unexpected,
    }


def main() -> int:
    issue_number_env = os.environ.get("ISSUE_NUMBER")
    if not issue_number_env:
        print("ISSUE_NUMBER is required", file=sys.stderr)
        return 2
    # In production this would build a REST-backed client. The POC
    # has no real REST client, so we exit cleanly here. Tests call
    # ``run()`` directly with a mocked client.
    print(
        "lock_and_sweep: live REST client not implemented in POC; "
        f"would process issue #{issue_number_env}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
