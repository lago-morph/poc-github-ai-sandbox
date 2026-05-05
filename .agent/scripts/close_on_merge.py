"""``close-on-merge`` script (§7.3).

Triggered on merged PRs. Reads the PR body for ``Closes #N``, verifies
the linked issue is in ``status: finished``, then closes the issue and
comments the merge SHA.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any, Optional

if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        iso_now,
        load_config,
        parse_agent_meta,
    )
else:
    from .common import GitHubClient, iso_now, load_config, parse_agent_meta


_CLOSES_RE = re.compile(
    r"\b(?:closes|closed|close|fixes|fixed|fix|resolves|resolved|resolve)\s+#(\d+)\b",
    re.IGNORECASE,
)


def parse_closes_refs(body: Optional[str]) -> list[int]:
    """Return list of issue numbers the PR claims to close."""
    if not body:
        return []
    return [int(m.group(1)) for m in _CLOSES_RE.finditer(body)]


def run(
    client: GitHubClient,
    pr_number: int,
    *,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Close issues referenced by a merged PR. Returns a result dict."""
    cfg = config or load_config()

    pr = client.get_pull_request(pr_number)
    if not pr.get("merged"):
        return {"action": "noop", "reason": "pr_not_merged"}

    refs = parse_closes_refs(pr.get("body"))
    if not refs:
        return {"action": "noop", "reason": "no_closes_refs"}

    closed: list[int] = []
    skipped: list[dict[str, Any]] = []

    for issue_number in refs:
        try:
            issue = client.get_issue(issue_number)
        except KeyError:
            skipped.append({"issue": issue_number, "reason": "missing"})
            continue

        meta = parse_agent_meta(issue.get("body"))
        if meta is None:
            skipped.append({"issue": issue_number, "reason": "no_agent_meta"})
            continue

        if meta.get("status") != "finished":
            skipped.append({
                "issue": issue_number,
                "reason": "not_finished",
                "status": meta.get("status"),
            })
            continue

        if issue.get("state") != "closed":
            client.update_issue(issue_number, state="closed")

        msg = (
            f"Issue closed by merge of #{pr_number} "
            f"(merge_sha={pr.get('merge_commit_sha')}). "
            f"Closed at {iso_now()}."
        )
        client.add_comment(issue_number, msg)
        closed.append(issue_number)

    return {"action": "closed", "issues_closed": closed, "skipped": skipped}


def main() -> int:
    """POC stub for the ``close-on-merge`` workflow entry point.

    Required environment variables:
      - ``PR_NUMBER``          the merged pull request number
      - ``GITHUB_TOKEN``       token authenticating REST calls
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug

    Exits 0 (POC stub successfully reached). Tests call ``run()`` directly
    with an in-memory client; real workflow integration will instantiate
    a REST-backed ``GitHubClient`` here.
    """
    required = ["PR_NUMBER", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    missing = [k for k in required if not os.environ.get(k)]
    print(
        "close_on_merge: POC stub. Required env vars: " + ", ".join(required) + ".",
        file=sys.stderr,
    )
    if missing:
        print(f"close_on_merge: missing env vars (POC stub, exit 0 anyway): {missing}", file=sys.stderr)
    else:
        print(
            f"close_on_merge: would handle PR #{os.environ['PR_NUMBER']}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
