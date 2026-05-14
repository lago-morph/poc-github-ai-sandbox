"""``task-dag/schedule_successors`` — create successor issues with status null.

The protocol expresses dependencies via ``depends_on_prs`` on each
successor's agent-meta block; the actual scheduling is expressed by
opening the issues with ``status: null`` so any qualifying agent can
claim them.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional

try:
    from .common import (
        GitHubClient,
        iso_now,
        new_uuid,
        render_agent_meta,
        slugify,
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
    new_uuid = _mod.new_uuid
    render_agent_meta = _mod.render_agent_meta
    slugify = _mod.slugify


def schedule_successors(
    client: GitHubClient,
    *,
    successors: list[dict[str, Any]],
    base_branch: str = "main",
    parent_issue: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Open one issue per successor spec.

    Each successor dict has at minimum:

    - ``title`` (string)
    - ``instructions_inline`` OR ``instructions_path`` (string)
    - optional ``depends_on_prs`` (list[int])
    - optional ``feature_branch`` (string; defaults to slug-derived)
    """
    out: list[dict[str, Any]] = []

    # We can't reliably know the next issue number ahead of time; for
    # the in-memory client, ``create_issue`` is a test helper. Real
    # clients would use POST /issues.
    create_issue = getattr(client, "create_issue", None)
    if create_issue is None:
        raise RuntimeError(
            "client lacks create_issue(); a real REST client would POST /issues"
        )

    for spec in successors:
        title = spec["title"]
        slug = spec.get("slug") or slugify(title)
        # Without knowing the issue number yet, derive a placeholder
        # feature branch and tweak after creation.
        feature_branch = spec.get("feature_branch") or f"agent/<n>-{slug}"

        meta = {
            "protocol_version": 1,
            "agent_id": None,
            "session_id": None,
            "status": None,
            "status_ts": None,
            "feature_branch": feature_branch,
            "base_branch": spec.get("base_branch") or base_branch,
            "parent_issue": spec.get("parent_issue", parent_issue),
            "depends_on_prs": list(spec.get("depends_on_prs") or []),
            "instructions_path": spec.get("instructions_path"),
            "instructions_inline": spec.get("instructions_inline"),
            "created_at": iso_now(),
        }

        prose = spec.get("prose") or ""
        body = render_agent_meta(meta, prose=prose)

        issue = create_issue(title=title, body=body)
        # Substitute the real issue number into the feature branch placeholder.
        n = issue["number"]
        if "<n>" in feature_branch:
            meta["feature_branch"] = feature_branch.replace("<n>", str(n))
            new_body = render_agent_meta(meta, prose=prose)
            client.update_issue(n, body=new_body)
            issue = client.get_issue(n)
        out.append(issue)

    return out
