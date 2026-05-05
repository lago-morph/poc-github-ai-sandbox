"""Tests for ``harness.lib``: naming + asserts predicates."""

from __future__ import annotations

import pytest

from harness.lib import (
    HarnessAssertionError,
    assert_envelope_terminal,
    assert_issue_has_label,
    assert_issue_locked,
    assert_meta_status,
    assert_pr_merged,
    assert_summary_matches,
    feature_branch,
    new_run_id,
    runs_path,
    scenario_label,
    subagent_branch,
)
from agent_lib import make_initial_meta, render_body


# ---------------------------------------------------------------------------
# naming
# ---------------------------------------------------------------------------

def test_new_run_id_is_8_hex_chars():
    rid = new_run_id()
    assert isinstance(rid, str)
    assert len(rid) == 8
    int(rid, 16)  # parses


def test_new_run_id_distinct_calls():
    a = new_run_id()
    b = new_run_id()
    # Cosmically tiny chance of collision (1 / 2**32).
    assert a != b


def test_feature_branch_format():
    assert feature_branch(1, "abcd1234") == "agent/harness-01-abcd1234"
    assert feature_branch(15, "deadbeef") == "agent/harness-15-deadbeef"


def test_feature_branch_validation():
    with pytest.raises(ValueError):
        feature_branch(0, "abcd1234")
    with pytest.raises(ValueError):
        feature_branch(1, "")


def test_subagent_branch_format():
    assert subagent_branch("agent/harness-01-abcd1234", "alpha") == \
        "agent/harness-01-abcd1234/sub-alpha"


def test_subagent_branch_validation():
    with pytest.raises(ValueError):
        subagent_branch("", "alpha")
    with pytest.raises(ValueError):
        subagent_branch("agent/x", "")


def test_scenario_label():
    assert scenario_label(1) == "harness-scenario-01"
    assert scenario_label(15) == "harness-scenario-15"


def test_scenario_label_validation():
    with pytest.raises(ValueError):
        scenario_label(0)


def test_runs_path():
    assert runs_path(7, 1234) == "runs/7/1234"


@pytest.mark.parametrize("bad", [(0, 1), (-1, 1), (1, 0), (1, -1)])
def test_runs_path_validation(bad):
    with pytest.raises(ValueError):
        runs_path(*bad)


# ---------------------------------------------------------------------------
# asserts
# ---------------------------------------------------------------------------

def test_assert_issue_locked_ok():
    assert_issue_locked({"locked": True, "number": 1})


def test_assert_issue_locked_raises_when_unlocked():
    with pytest.raises(HarnessAssertionError, match="not locked"):
        assert_issue_locked({"locked": False, "number": 1})


def test_assert_issue_locked_raises_on_non_dict():
    with pytest.raises(HarnessAssertionError):
        assert_issue_locked("not a dict")  # type: ignore[arg-type]


def test_assert_issue_has_label_with_dict_labels():
    issue = {"number": 1, "labels": [{"name": "agent-task"}, {"name": "x"}]}
    assert_issue_has_label(issue, "agent-task")


def test_assert_issue_has_label_with_string_labels():
    issue = {"number": 1, "labels": ["agent-task", "x"]}
    assert_issue_has_label(issue, "agent-task")


def test_assert_issue_has_label_missing():
    issue = {"number": 7, "labels": [{"name": "other"}]}
    with pytest.raises(HarnessAssertionError, match="missing label"):
        assert_issue_has_label(issue, "agent-task")


def test_assert_issue_has_label_handles_no_labels_key():
    issue = {"number": 1}
    with pytest.raises(HarnessAssertionError):
        assert_issue_has_label(issue, "x")


def test_assert_issue_has_label_non_dict_input():
    with pytest.raises(HarnessAssertionError):
        assert_issue_has_label(123, "x")  # type: ignore[arg-type]


def test_assert_envelope_terminal_completed():
    assert_envelope_terminal({"run_status": "completed"}, "completed")


def test_assert_envelope_terminal_with_error_kind():
    env = {"run_status": "error", "error_kind": "branch_sha_mismatch"}
    assert_envelope_terminal(env, "error",
                              expected_error_kind="branch_sha_mismatch")


def test_assert_envelope_terminal_status_mismatch():
    with pytest.raises(HarnessAssertionError, match="run_status mismatch"):
        assert_envelope_terminal({"run_status": "running"}, "completed")


def test_assert_envelope_terminal_error_kind_mismatch():
    env = {"run_status": "error", "error_kind": "x"}
    with pytest.raises(HarnessAssertionError, match="error_kind mismatch"):
        assert_envelope_terminal(env, "error", expected_error_kind="y")


def test_assert_envelope_terminal_rejects_non_terminal_expected():
    with pytest.raises(HarnessAssertionError, match="must be terminal"):
        assert_envelope_terminal({"run_status": "running"}, "running")


def test_assert_envelope_terminal_rejects_non_dict():
    with pytest.raises(HarnessAssertionError):
        assert_envelope_terminal("x", "completed")  # type: ignore[arg-type]


def test_assert_meta_status_ok():
    meta = make_initial_meta(feature_branch="agent/1", instructions_inline="x")
    body = render_body(meta)
    assert_meta_status(body, None)


def test_assert_meta_status_mismatch():
    meta = make_initial_meta(feature_branch="agent/1", instructions_inline="x")
    body = render_body(meta)
    with pytest.raises(HarnessAssertionError, match="status mismatch"):
        assert_meta_status(body, "finished")


def test_assert_meta_status_no_block_raises():
    with pytest.raises(HarnessAssertionError, match="no parseable agent-meta"):
        assert_meta_status("just prose", None)


def test_assert_summary_matches_subset_ok():
    assert_summary_matches({"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 2})


def test_assert_summary_matches_missing_key():
    with pytest.raises(HarnessAssertionError, match="missing required key"):
        assert_summary_matches({"a": 1}, {"a": 1, "b": 2})


def test_assert_summary_matches_value_mismatch():
    with pytest.raises(HarnessAssertionError, match="mismatch"):
        assert_summary_matches({"a": 1}, {"a": 2})


def test_assert_summary_matches_non_dict_summary():
    with pytest.raises(HarnessAssertionError):
        assert_summary_matches("x", {"a": 1})  # type: ignore[arg-type]


def test_assert_summary_matches_non_dict_expected():
    with pytest.raises(HarnessAssertionError):
        assert_summary_matches({}, "x")  # type: ignore[arg-type]


def test_assert_pr_merged_ok():
    assert_pr_merged({"number": 1, "merged": True, "state": "closed"})


def test_assert_pr_merged_not_merged():
    with pytest.raises(HarnessAssertionError, match="not merged"):
        assert_pr_merged({"number": 2, "merged": False, "state": "open"})


def test_assert_pr_merged_non_dict():
    with pytest.raises(HarnessAssertionError):
        assert_pr_merged("x")  # type: ignore[arg-type]
