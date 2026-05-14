"""orchestrate-issue — 10-phase primary-agent loop.

This module is a **docstring-level stub**. The actual orchestration is
performed by the SKILL.md procedure invoking the harness's Agent tool
and composing the ``batch-job`` and ``task-dag`` skills' Python helpers
(canonically installed at ``.agent/scripts/agent_lib``).

The function signatures below mirror the inputs and outputs documented
in ``SPEC.md``. They are present here so callers and tests have a
stable Python surface to import against; runtime behavior is delegated
to the SKILL.md flow plus the installed ``agent_lib`` and the sibling
``task-dag`` / ``batch-job`` ``lib/`` packages.

The 10 phases (see ``SKILL.md`` for full detail):

    0. pre-flight       — self-install, run_id, resume detection
    1. claim            — delegate to task-dag.claim
    2. plan             — delegate to task-dag.plan
    3. write state.json — durability anchor on the feature branch
    4. create sub-branches — double-dash separator (POC SPEC §6)
    5. fanout (parallel) — Agent tool, isolation=worktree, single message
    6. collect          — parse deliverables, update state.json
    7. merge in plan order — task-dag.merge_subagent_branches
    8. open PR          — feature_branch -> base_branch
    9. finalise issue   — write status=finished, close issue
   10. schedule successors — task-dag.schedule_successors (optional)

These functions are documented but not implemented at runtime — the
SKILL.md procedure is the canonical execution path. The
``parallel-subagent-fanout`` skill from software-factory is a pattern
reference, not an install-time dependency.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


def orchestrate_issue(
    issue_number: Optional[int] = None,
    agent_id: Optional[str] = None,
    agent_login: Optional[str] = None,
    max_parallel: int = 4,
    conflict_strategy: str = "fail",
    subagent_type: str = "general-purpose",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Drive the end-to-end primary-agent loop for one issue.

    Inputs
    ------
    issue_number : int, optional
        If omitted, the skill scans for an unclaimed or stale issue.
    agent_id : str, optional
        Defaults to a generated UUID.
    agent_login : str, optional
        Resolved via ``mcp__github__get_me`` when omitted.
    max_parallel : int
        Cap on concurrent subagents per wave. Default 4.
    conflict_strategy : str
        One of ``fail`` (default), ``ours``, ``theirs``, ``manual``.
    subagent_type : str
        Per the harness's Agent tool. Default ``general-purpose``.
    dry_run : bool
        If True, run Phases 0-3 and stop before dispatch.

    Returns
    -------
    dict
        Shape per ``SPEC.md`` Outputs::

            {
                "issue_number": int,
                "feature_branch": str,
                "subagent_branches": list[str],
                "pr_number": int,
                "pr_url": str,
                "tests_delta": str,
                "run_report_path": str,
                "successors_scheduled": list[int],
                "elapsed_seconds": int,
            }

    Notes
    -----
    Stub. Actual orchestration lives in ``SKILL.md`` plus the installed
    ``.agent/scripts/agent_lib`` package and the sibling ``task-dag``
    and ``batch-job`` ``lib/`` packages.
    """
    raise NotImplementedError(
        "orchestrate_issue is a docstring stub; see SKILL.md for the "
        "canonical 10-phase procedure."
    )


def phase_0_preflight(run_id: Optional[str] = None) -> dict[str, Any]:
    """Phase 0 — pre-flight checks and self-install.

    - Self-install protocol templates if missing (superset of
      batch-job + task-dag install logic; idempotent).
    - Resolve ``agent_login`` via ``mcp__github__get_me`` if absent.
    - Generate ``run_id`` as ``YYYYMMDD-HHMMSS`` UTC.
    - Detect any in-progress run for the same agent on the same
      feature branch and jump to restart recovery.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_1_claim(
    agent_id: str,
    agent_login: str,
    issue_number: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    """Phase 1 — claim the issue via task-dag.claim.

    Returns ``None`` if no claimable issue is available and
    ``issue_number`` was not provided; the caller surfaces
    ``{"reason": "no_work"}`` in that case.

    Stub. Delegates to the installed ``task-dag.claim`` Python helper.
    """
    raise NotImplementedError


def phase_2_plan(issue_number: int, agent_login: str) -> dict[str, Any]:
    """Phase 2 — plan subagents via task-dag.plan.

    Returns the subagent layout per the YAML shape in SPEC.md.
    Subtasks must touch disjoint file paths.

    Stub. Delegates to the installed ``task-dag.plan`` Python helper.
    """
    raise NotImplementedError


def phase_3_write_state(
    run_id: str,
    issue_number: int,
    feature_branch: str,
    subtasks: list[dict[str, Any]],
) -> str:
    """Phase 3 — write ``.agent/runs/<run_id>/state.json``.

    Commits and pushes the state file on the feature branch. Returns
    the absolute path to the written state.json.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_4_create_sub_branches(
    feature_branch: str,
    subtasks: list[dict[str, Any]],
) -> list[str]:
    """Phase 4 — create ``<feature_branch>--<sub_id>`` for each subtask.

    Double-dash separator (POC SPEC §6). Never single-slash.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_5_fanout(
    subtasks: list[dict[str, Any]],
    max_parallel: int,
    subagent_type: str,
    brief_template_path: str,
    heartbeat: Optional[Callable[[], None]] = None,
) -> list[dict[str, Any]]:
    """Phase 5 — dispatch subagents in waves via the Agent tool.

    All Agent calls in one wave go in a **single dispatcher message**;
    the harness only parallelises within one message. Each call uses
    ``isolation: "worktree"`` to prevent branch contamination.

    Briefs are rendered from ``templates/brief-template.md`` (the
    9-section subagent-prompting template specialised for the
    agent-job protocol).

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_6_collect(reports: list[dict[str, Any]], state_path: str) -> dict[str, Any]:
    """Phase 6 — parse subagent reports and update state.json.

    Sets each subtask's ``status`` to ``dispatched_ok`` or ``failed``.
    Persists after each update for restart-safety.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_7_merge(
    feature_branch: str,
    subagent_branches: list[str],
    conflict_strategy: str = "fail",
) -> dict[str, Any]:
    """Phase 7 — merge sub-branches in plan order (not completion order).

    Delegates to the installed ``task-dag.merge_subagent_branches``.
    Returns ``{"merged": [...], "conflicts": [...], "skipped": [...]}``.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_8_open_pr(
    feature_branch: str,
    base_branch: str,
    issue_number: int,
    run_report_path: str,
) -> dict[str, Any]:
    """Phase 8 — open the PR from feature_branch to base_branch.

    Returns ``{"pr_number": int, "pr_url": str}``. On persistent
    failure writes ``.PENDING_PR.md`` and raises a typed error.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_9_finalise_issue(issue_number: int, pr_url: str) -> None:
    """Phase 9 — write ``status: finished`` and close the issue.

    The ``close-on-merge.yml`` workflow handles the post-close lock
    when the PR merges.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_10_schedule_successors(
    successors: list[dict[str, Any]],
    base_branch: str,
) -> list[int]:
    """Phase 10 — create successor issues with ``status: null``.

    Delegates to the installed ``task-dag.schedule_successors``.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


__all__ = [
    "orchestrate_issue",
    "phase_0_preflight",
    "phase_1_claim",
    "phase_2_plan",
    "phase_3_write_state",
    "phase_4_create_sub_branches",
    "phase_5_fanout",
    "phase_6_collect",
    "phase_7_merge",
    "phase_8_open_pr",
    "phase_9_finalise_issue",
    "phase_10_schedule_successors",
]
