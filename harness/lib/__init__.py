"""Public API for the harness scenario library.

Exposes pure naming helpers and post-MCP assertion predicates used by
harness scenario playbooks and their tests. No I/O happens here.
"""

from __future__ import annotations

from .asserts import (
    HarnessAssertionError,
    assert_envelope_terminal,
    assert_issue_has_label,
    assert_issue_locked,
    assert_meta_status,
    assert_pr_merged,
    assert_summary_matches,
)
from .naming import (
    feature_branch,
    new_run_id,
    runs_path,
    scenario_label,
    subagent_branch,
)


__all__ = [
    "HarnessAssertionError",
    "assert_envelope_terminal",
    "assert_issue_has_label",
    "assert_issue_locked",
    "assert_meta_status",
    "assert_pr_merged",
    "assert_summary_matches",
    "feature_branch",
    "new_run_id",
    "runs_path",
    "scenario_label",
    "subagent_branch",
]
