"""Render the recommendations Markdown from the dialog data.

The output structure mirrors SPEC.md §"Phase 4 — write
recommendations" and matches the template at
``templates/recommendations-template.md``. AGENTS.md and CLAUDE.md
NEVER appear in the "non-pointer edits" section — that is enforced
here, not just by policy.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable


_SACRED_FILES = frozenset({"AGENTS.md", "CLAUDE.md"})


def render_recommendations(dialog: Dict[str, Any], repo_name: str = "<repo>") -> str:
    """Produce the recommendations.md content as a string.

    ``dialog`` is the structured dict returned by
    ``lib.dialog.load_dialog``. ``repo_name`` is interpolated into the
    H1.

    The full implementation will:

    - Pull non-pointer-edit candidates from a discovery summary
      (passed separately), not from the dialog directly.
    - Diff each candidate against the current default branch and
      embed a short diff preview.
    - Hard-fail if a sacred file appears in the non-pointer list
      (defensive — that should never happen given the call sites).
    """
    answers: Dict[str, str] = dialog.get("answers") or {}

    def _get(qid: str, default: str = "_<not answered>_") -> str:
        return answers.get(qid, default)

    lines: list = []
    lines.append(f"# Onboarding recommendations — {repo_name}")
    lines.append("")
    lines.append("## Statement of intent")
    lines.append("")
    lines.append(f"- Purpose: {_get('intent.purpose')}")
    lines.append(f"- Audience: {_get('intent.audience')}")
    lines.append(f"- 1-3 month goal: {_get('intent.goal')}")
    lines.append("")

    lines.append("## Problems addressed")
    lines.append("")
    lines.append(f"- Friction addressed: {_get('problems.friction')}")
    lines.append(f"- Pain points captured: {_get('problems.freeform')}")
    lines.append("")

    lines.append("## Files to add (no edits to existing files)")
    lines.append("")
    for path in (
        ".agent/config.json (from batch-job/task-dag template)",
        ".agent/scripts/... (full inventory)",
        ".github/workflows/lock-and-sweep.yml",
        ".github/workflows/batch-job-handler.yml",
        ".github/workflows/close-on-merge.yml",
        ".agent/schemas/...",
    ):
        lines.append(f"- {path}")
    lines.append("")

    lines.append("## Files proposed for additive edits (pointer-only)")
    lines.append("")
    lines.append("- `AGENTS.md`: add one line under a new \"Agent-job protocol\" section:")
    lines.append("  > See `.agent/onboarding/recommendations.md` for protocol conventions.")
    lines.append("- `CLAUDE.md`: identical pointer line.")
    lines.append("")

    lines.append("## Files proposed for non-pointer edits")
    lines.append("")
    non_pointer = list(_filter_non_pointer(dialog.get("non_pointer_candidates") or []))
    if non_pointer:
        for path, rationale in non_pointer:
            lines.append(f"- `{path}` — {rationale}")
    else:
        lines.append("- _(none proposed by this run)_")
    lines.append("")

    lines.append("## Before/after workflow")
    lines.append("")
    lines.append(f"- Today: {_get('current_workflow.summary_accurate', '<agent summary>')}")
    lines.append(f"- After: see integration depth `{_get('integration.depth')}`")
    lines.append("")

    lines.append("## Next steps if accepted")
    lines.append("")
    lines.append("1. The onboarding skill will apply the proposed edits with your")
    lines.append("   explicit per-file approval.")
    lines.append("2. Run `/orchestrate-issue` on any unclaimed agent-task issue to")
    lines.append("   exercise the new flow.")
    lines.append("3. Re-run `/onboarding` later to revise integration choices.")
    lines.append("")

    return "\n".join(lines)


def _filter_non_pointer(candidates: Iterable) -> Iterable:
    """Strip sacred files from the non-pointer-edit candidate list.

    Defensive belt-and-braces: AGENTS.md / CLAUDE.md must never reach
    the non-pointer section. If a caller passes them in, drop them
    silently rather than render them.
    """
    for item in candidates:
        # Expect (path, rationale) tuples; tolerate plain strings too.
        if isinstance(item, tuple) and len(item) == 2:
            path, rationale = item
        else:
            path, rationale = str(item), ""
        if path in _SACRED_FILES:
            continue
        yield (path, rationale)
