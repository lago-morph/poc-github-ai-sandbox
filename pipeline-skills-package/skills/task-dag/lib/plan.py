"""``task-dag/plan`` — load the work brief for a claimed issue.

Reads either ``instructions_inline`` from the agent-meta or fetches
``instructions_path`` via the GitHub client. Returns the brief plus
any pre-declared structure the spec leaves room for in v1.

Also exposes :func:`should_decline` which inspects ``depends_on_prs``
on an issue's agent-meta and reports whether the issue should be
declined (per SPEC §4.1, §12: failed required dependency leads to
``status="abandoned"``).
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

try:
    from .common import GitHubClient, parse_agent_meta
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
    parse_agent_meta = _mod.parse_agent_meta


class PlanError(RuntimeError):
    """Raised when neither inline nor pathed instructions are available."""


def plan(
    client: GitHubClient,
    *,
    issue_number: int,
    base_branch: Optional[str] = None,
) -> dict[str, Any]:
    """Return ``{brief, source}`` for the issue's instructions."""
    issue = client.get_issue(issue_number)
    meta = parse_agent_meta(issue.get("body"))
    if meta is None:
        raise PlanError(f"issue #{issue_number} has no agent-meta")

    inline = meta.get("instructions_inline")
    path = meta.get("instructions_path")
    base = base_branch or meta.get("base_branch") or "main"

    if inline:
        return {
            "issue_number": issue_number,
            "brief": inline,
            "source": "inline",
            "base_branch": base,
            "feature_branch": meta.get("feature_branch"),
            "depends_on_prs": meta.get("depends_on_prs") or [],
        }

    if path:
        contents = client.get_file_contents(path, base)
        if contents is None:
            raise PlanError(
                f"instructions_path {path!r} not found on {base!r}"
            )
        return {
            "issue_number": issue_number,
            "brief": contents,
            "source": "path",
            "instructions_path": path,
            "base_branch": base,
            "feature_branch": meta.get("feature_branch"),
            "depends_on_prs": meta.get("depends_on_prs") or [],
        }

    raise PlanError(
        f"issue #{issue_number} has neither instructions_inline nor _path"
    )


def should_decline(
    client: GitHubClient,
    issue: dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """Per SPEC §4.1, §12: decide whether to decline (abandon) this issue.

    Inspects ``depends_on_prs`` on the issue's agent-meta. For each listed
    PR number:

    - If the PR is closed-without-merge (``state == "closed"`` and
      ``merged is False``) -> declines with reason
      ``"dependency_failed: PR #<N> closed without merge"``.
    - If the PR cannot be fetched (raises) -> declines with reason
      ``"dependency_missing: PR #<N>"``.

    Returns ``(False, None)`` when no listed PR is in a failure state.
    Returns ``(True, reason)`` on the first failure encountered.
    """
    meta = parse_agent_meta(issue.get("body")) or {}
    depends = meta.get("depends_on_prs") or []
    for n in depends:
        try:
            pr = client.get_pull_request(int(n))
        except Exception:  # noqa: BLE001 - any fetch failure -> dependency missing
            return True, f"dependency_missing: PR #{n}"

        state = pr.get("state")
        merged = bool(pr.get("merged"))
        if state == "closed" and not merged:
            return True, f"dependency_failed: PR #{n} closed without merge"

    return False, None
