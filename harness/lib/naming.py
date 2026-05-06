"""Pure name/id helpers for the harness.

These helpers compute deterministic identifiers (branch names, scenario
labels, runs paths) and a fresh run-id. They perform no I/O.
"""

from __future__ import annotations

import secrets


def new_run_id() -> str:
    """Return a fresh 8-char lowercase hex run id."""
    return secrets.token_hex(4)


def feature_branch(issue_number: int, run_id: str) -> str:
    """Compose the per-run feature branch name."""
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise ValueError("issue_number must be a positive int")
    if not run_id:
        raise ValueError("run_id must be a non-empty string")
    return f"agent/harness-{issue_number:02d}-{run_id}"


def subagent_branch(feature: str, sub_id: str) -> str:
    """Compose a sub-agent branch name from the feature branch.

    Uses a DOUBLE-dash separator (``--sub-``). The single-slash form
    collides with git's ref-prefix rule when both ``foo`` and ``foo/bar``
    exist as refs (discovered live during scenario 01).
    """
    if not feature:
        raise ValueError("feature must be a non-empty string")
    if not sub_id:
        raise ValueError("sub_id must be a non-empty string")
    return f"{feature}--sub-{sub_id}"


def scenario_label(scenario_number: int) -> str:
    """Compose the canonical ``harness-scenario-NN`` label."""
    if not isinstance(scenario_number, int) or scenario_number <= 0:
        raise ValueError("scenario_number must be a positive int")
    return f"harness-scenario-{scenario_number:02d}"


def runs_path(issue_number: int, comment_id: int) -> str:
    """Compose the ``runs/<issue>/<comment>`` artifact directory path."""
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise ValueError("issue_number must be a positive int")
    if not isinstance(comment_id, int) or comment_id <= 0:
        raise ValueError("comment_id must be a positive int")
    return f"runs/{issue_number}/{comment_id}"


__all__ = [
    "feature_branch",
    "new_run_id",
    "runs_path",
    "scenario_label",
    "subagent_branch",
]
