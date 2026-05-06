"""Tests for the ``agent_lib`` package (pure helpers + CLI).

The package lives at ``.agent/scripts/agent_lib/`` and is the
agent-mode counterpart to the workflow-side helpers. We exercise
it both as Python imports and as CLI subprocesses to mirror how the
dispatcher will use it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import agent_lib
import agent_protocol_common as common
from agent_lib import (
    EnvelopeArgsInvalid,
    abandon_meta,
    claim_meta,
    finish_meta,
    heartbeat_meta,
    is_terminal,
    make_initial_meta,
    make_request_envelope,
    manifest_path_for,
    parse_body,
    parse_terminal_status,
    render_body,
    replace_meta_in_body,
    summary_path_for,
)
from agent_lib._common_loader import locate_repo_root, load_common


REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# _common_loader
# ---------------------------------------------------------------------------

def test_load_common_returns_central_module():
    mod = load_common()
    assert mod is common
    # Idempotent: calling twice returns the same instance.
    assert load_common() is mod


def test_locate_repo_root_finds_marker():
    root = locate_repo_root()
    assert (root / ".agent" / "config.json").exists()


def test_locate_repo_root_raises_when_no_marker(tmp_path: Path):
    with pytest.raises(RuntimeError):
        locate_repo_root(start=tmp_path)


# ---------------------------------------------------------------------------
# envelope.make_request_envelope
# ---------------------------------------------------------------------------

def test_make_request_envelope_happy_echo():
    env = make_request_envelope(
        "echo",
        {"message": "hello"},
        "agent/1-demo",
        "0" * 40,
        "alpha",
    )
    assert env["protocol_version"] == 1
    assert env["kind"] == "batch-job-request"
    assert env["command"] == "echo"
    assert env["args"] == {"message": "hello"}
    assert env["branch"] == "agent/1-demo"
    assert env["commit_sha"] == "0" * 40
    assert env["subagent_id"] == "alpha"
    assert env["run_status"] is None
    assert env["agent_ack"] is None
    assert env["submitted_at"].endswith("Z")


def test_make_request_envelope_validates_args_against_schema():
    # build's schema rejects unknown property "extra"
    with pytest.raises(EnvelopeArgsInvalid) as exc:
        make_request_envelope(
            "build",
            {"target": "x", "extra": "nope"},
            "agent/1",
            "0" * 40,
            "alpha",
        )
    assert exc.value.command == "build"


def test_make_request_envelope_skip_validation():
    # Same payload but skipping validation succeeds.
    env = make_request_envelope(
        "build",
        {"target": "x", "extra": "nope"},
        "agent/1",
        "0" * 40,
        "alpha",
        validate_args=False,
    )
    assert env["args"]["extra"] == "nope"


def test_make_request_envelope_unknown_command_raises():
    with pytest.raises(EnvelopeArgsInvalid):
        make_request_envelope(
            "no-such-command",
            {},
            "agent/1",
            "0" * 40,
            "alpha",
        )


def test_make_request_envelope_uses_supplied_submitted_at():
    env = make_request_envelope(
        "echo",
        {"message": "x"},
        "agent/1",
        "0" * 40,
        "alpha",
        submitted_at="2025-01-01T00:00:00Z",
    )
    assert env["submitted_at"] == "2025-01-01T00:00:00Z"


@pytest.mark.parametrize("bad", [
    {"command": "", "msg": "command must"},
    {"branch": "", "msg": "branch must"},
    {"sha": "", "msg": "commit_sha must"},
    {"sub": "", "msg": "subagent_id must"},
])
def test_make_request_envelope_rejects_empty_strings(bad):
    kwargs = dict(
        command="echo",
        args={"message": "hi"},
        branch="agent/1",
        commit_sha="0" * 40,
        subagent_id="alpha",
    )
    if "command" in bad:
        kwargs["command"] = bad["command"]
    if "branch" in bad:
        kwargs["branch"] = bad["branch"]
    if "sha" in bad:
        kwargs["commit_sha"] = bad["sha"]
    if "sub" in bad:
        kwargs["subagent_id"] = bad["sub"]
    with pytest.raises((ValueError, TypeError)):
        make_request_envelope(
            kwargs["command"], kwargs["args"], kwargs["branch"],
            kwargs["commit_sha"], kwargs["subagent_id"],
        )


def test_make_request_envelope_rejects_non_dict_args():
    with pytest.raises(TypeError):
        make_request_envelope(
            "echo", "not-a-dict",  # type: ignore[arg-type]
            "agent/1", "0" * 40, "alpha",
        )


# ---------------------------------------------------------------------------
# meta helpers
# ---------------------------------------------------------------------------

def test_make_initial_meta_inline():
    meta = make_initial_meta(
        feature_branch="agent/1",
        instructions_inline="Do the thing.",
        parent_issue=42,
        depends_on_prs=[1, 2],
    )
    assert meta["status"] is None
    assert meta["feature_branch"] == "agent/1"
    assert meta["base_branch"] == "main"
    assert meta["parent_issue"] == 42
    assert meta["depends_on_prs"] == [1, 2]
    assert meta["instructions_inline"] == "Do the thing."
    assert meta["instructions_path"] is None
    assert meta["created_at"].endswith("Z")
    assert meta["protocol_version"] == 1


def test_make_initial_meta_path_only():
    meta = make_initial_meta(
        feature_branch="agent/2",
        instructions_path=".agent/briefs/x.md",
    )
    assert meta["instructions_path"] == ".agent/briefs/x.md"
    assert meta["instructions_inline"] is None


def test_make_initial_meta_missing_instructions_raises():
    with pytest.raises(ValueError):
        make_initial_meta(feature_branch="agent/1")


def test_make_initial_meta_missing_feature_branch_raises():
    with pytest.raises(ValueError):
        make_initial_meta(feature_branch="", instructions_inline="x")


def test_make_initial_meta_extra_fields():
    meta = make_initial_meta(
        feature_branch="agent/1",
        instructions_inline="x",
        extra={"custom_key": "yes"},
    )
    assert meta["custom_key"] == "yes"


def test_claim_meta_sets_working_status():
    base = make_initial_meta(
        feature_branch="agent/1", instructions_inline="x"
    )
    claimed = claim_meta(base, "agent-x", "session-y")
    assert base["status"] is None  # original unmutated
    assert claimed["status"] == "working"
    assert claimed["agent_id"] == "agent-x"
    assert claimed["session_id"] == "session-y"
    assert claimed["status_ts"].endswith("Z")


def test_claim_meta_rejects_empty_ids():
    base = make_initial_meta(
        feature_branch="agent/1", instructions_inline="x"
    )
    with pytest.raises(ValueError):
        claim_meta(base, "", "s")
    with pytest.raises(ValueError):
        claim_meta(base, "a", "")


def test_heartbeat_meta_only_changes_status_ts():
    base = claim_meta(
        make_initial_meta(feature_branch="agent/1", instructions_inline="x"),
        "agent-x", "session-y",
    )
    earlier_ts = base["status_ts"]
    # Force a different timestamp by mutating then heartbeating.
    base["status_ts"] = "2020-01-01T00:00:00Z"
    out = heartbeat_meta(base)
    assert out["status_ts"] != "2020-01-01T00:00:00Z"
    assert out["status"] == "working"
    assert out["agent_id"] == "agent-x"


def test_finish_meta_marks_finished():
    meta = claim_meta(
        make_initial_meta(feature_branch="agent/1", instructions_inline="x"),
        "agent-x", "session-y",
    )
    fin = finish_meta(meta)
    assert fin["status"] == "finished"
    assert fin["agent_id"] == "agent-x"


def test_abandon_meta_records_reason():
    meta = make_initial_meta(feature_branch="agent/1", instructions_inline="x")
    out = abandon_meta(meta, "merge_conflict")
    assert out["status"] == "abandoned"
    assert out["abandon_reason"] == "merge_conflict"


def test_render_body_round_trips_through_parse_body():
    meta = make_initial_meta(feature_branch="agent/1", instructions_inline="x")
    body = render_body(meta, prose="A note")
    parsed = parse_body(body)
    assert parsed is not None
    assert parsed["feature_branch"] == "agent/1"
    assert "A note" in body


def test_parse_body_returns_none_for_empty_or_no_block():
    assert parse_body(None) is None
    assert parse_body("") is None
    assert parse_body("just prose") is None
    # Block present but invalid JSON inside:
    assert parse_body("```agent-meta\n{not json}\n```") is None


def test_replace_meta_in_body_preserves_prose():
    meta1 = make_initial_meta(
        feature_branch="agent/1", instructions_inline="x"
    )
    body = render_body(meta1, prose="Original prose here.")
    meta2 = claim_meta(meta1, "agent-Z", "sess-Z")
    new_body = replace_meta_in_body(body, meta2)
    assert "Original prose here." in new_body
    parsed = parse_body(new_body)
    assert parsed["agent_id"] == "agent-Z"


def test_replace_meta_in_body_no_prior_block():
    meta = make_initial_meta(
        feature_branch="agent/1", instructions_inline="x"
    )
    new_body = replace_meta_in_body("just prose", meta)
    assert "agent-meta" in new_body
    assert "just prose" in new_body


def test_replace_meta_in_body_handles_none_body():
    meta = make_initial_meta(
        feature_branch="agent/1", instructions_inline="x"
    )
    new_body = replace_meta_in_body(None, meta)
    parsed = parse_body(new_body)
    assert parsed["feature_branch"] == "agent/1"


# ---------------------------------------------------------------------------
# poll helpers
# ---------------------------------------------------------------------------

def test_parse_terminal_status_completed():
    body = json.dumps({
        "protocol_version": 1, "kind": "batch-job-request",
        "run_status": "completed",
        "summary": {"message": "x", "echoed_args": {}},
        "log_manifest_path": "runs/1/2/manifest.json",
    })
    status, parsed = parse_terminal_status(body)
    assert status == "completed"
    assert parsed["summary"]["message"] == "x"


@pytest.mark.parametrize("rs", ["error", "parse_error"])
def test_parse_terminal_status_terminal_variants(rs):
    body = json.dumps({"run_status": rs, "kind": "batch-job-request",
                       "protocol_version": 1})
    status, _ = parse_terminal_status(body)
    assert status == rs


def test_parse_terminal_status_running_returns_none():
    body = json.dumps({"run_status": "running", "kind": "batch-job-request",
                       "protocol_version": 1})
    status, parsed = parse_terminal_status(body)
    assert status is None
    assert parsed["run_status"] == "running"


def test_parse_terminal_status_invalid_json():
    status, parsed = parse_terminal_status("not json")
    assert status is None
    assert parsed == {}


def test_parse_terminal_status_non_dict_json():
    status, parsed = parse_terminal_status("[1,2,3]")
    assert status is None
    assert parsed == {}


def test_parse_terminal_status_tolerates_trailer():
    """parse_terminal_status must tolerate the trailer Claude Code's
    GitHub MCP appends to every comment (the agent uses this to read
    its own comments back via MCP)."""
    body = json.dumps({
        "protocol_version": 1, "kind": "batch-job-request",
        "run_status": "completed",
        "summary": {"message": "x", "echoed_args": {}},
        "log_manifest_path": "runs/1/2/manifest.json",
    }) + "\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_"
    status, parsed = parse_terminal_status(body)
    assert status == "completed"
    assert parsed["summary"]["message"] == "x"
    assert parsed["log_manifest_path"] == "runs/1/2/manifest.json"


def test_parse_terminal_status_rejects_non_string():
    with pytest.raises(TypeError):
        parse_terminal_status(123)  # type: ignore[arg-type]


def test_summary_path_for_format():
    assert summary_path_for(1, 2) == "runs/1/2/summary.json"
    assert summary_path_for(99, 1234567) == "runs/99/1234567/summary.json"


def test_manifest_path_for_format():
    assert manifest_path_for(1, 2) == "runs/1/2/manifest.json"


@pytest.mark.parametrize("bad", [(0, 1), (-1, 1), (1, 0), (1, -1)])
def test_summary_path_for_validation(bad):
    with pytest.raises(ValueError):
        summary_path_for(*bad)


def test_is_terminal_predicate():
    assert is_terminal({"run_status": "completed"})
    assert is_terminal({"run_status": "error"})
    assert is_terminal({"run_status": "parse_error"})
    assert not is_terminal({"run_status": "running"})
    assert not is_terminal({"run_status": None})
    assert not is_terminal({})


# ---------------------------------------------------------------------------
# CLI subprocess tests
# ---------------------------------------------------------------------------

def _cli_env() -> dict[str, str]:
    env = os.environ.copy()
    pp = env.get("PYTHONPATH", "")
    extra = str(REPO_ROOT / ".agent" / "scripts")
    env["PYTHONPATH"] = extra + (os.pathsep + pp if pp else "")
    return env


def _run_cli(*args: str, expect_zero: bool = True) -> subprocess.CompletedProcess:
    cp = subprocess.run(
        [sys.executable, "-m", "agent_lib", *args],
        env=_cli_env(),
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if expect_zero and cp.returncode != 0:
        raise AssertionError(
            f"agent_lib CLI exited {cp.returncode}: {cp.stderr}"
        )
    return cp


def test_cli_make_request_happy():
    cp = _run_cli(
        "make-request", '{"message": "hi"}',
        "--command", "echo",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
    )
    env = json.loads(cp.stdout)
    assert env["command"] == "echo"
    assert env["args"]["message"] == "hi"


def test_cli_make_request_invalid_json_arg():
    cp = _run_cli(
        "make-request", "not-json",
        "--command", "echo",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
        expect_zero=False,
    )
    assert cp.returncode != 0
    err = json.loads(cp.stderr.strip().splitlines()[-1])
    assert "invalid JSON" in err["error"]


def test_cli_make_request_validation_failure():
    cp = _run_cli(
        "make-request", '{"target": "x", "extra": "no"}',
        "--command", "build",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_make_request_no_validate_flag():
    cp = _run_cli(
        "make-request", '{"target": "x", "extra": "yes"}',
        "--command", "build",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
        "--no-validate",
    )
    env = json.loads(cp.stdout)
    assert env["args"]["extra"] == "yes"


def test_cli_make_request_args_not_object():
    cp = _run_cli(
        "make-request", '"a-string"',
        "--command", "echo",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_make_initial_meta_emits_body_markdown():
    cp = _run_cli(
        "make-initial-meta",
        json.dumps({
            "feature_branch": "agent/x",
            "instructions_inline": "Do.",
        }),
        "--prose", "Hello prose",
    )
    out = cp.stdout
    assert "Hello prose" in out
    assert "agent-meta" in out


def test_cli_make_initial_meta_invalid_payload():
    cp = _run_cli(
        "make-initial-meta", '"not-a-dict"',
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_make_initial_meta_missing_required():
    cp = _run_cli(
        "make-initial-meta", '{"feature_branch": "agent/x"}',
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_make_initial_meta_unsupported_key():
    cp = _run_cli(
        "make-initial-meta",
        json.dumps({
            "feature_branch": "agent/x",
            "instructions_inline": "x",
            "no_such_arg": True,
        }),
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_claim_meta_round_trip():
    initial = make_initial_meta(
        feature_branch="agent/y", instructions_inline="x"
    )
    cp = _run_cli(
        "claim-meta", json.dumps(initial),
        "--agent-id", "ag-1", "--session-id", "sess-1",
    )
    new_meta = parse_body(cp.stdout)
    assert new_meta["status"] == "working"
    assert new_meta["agent_id"] == "ag-1"


def test_cli_claim_meta_invalid_input():
    cp = _run_cli(
        "claim-meta", "[]",
        "--agent-id", "x", "--session-id", "y",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_claim_meta_missing_agent_id():
    initial = make_initial_meta(
        feature_branch="agent/y", instructions_inline="x"
    )
    cp = _run_cli(
        "claim-meta", json.dumps(initial),
        "--agent-id", "", "--session-id", "y",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_heartbeat_meta_round_trip():
    initial = claim_meta(
        make_initial_meta(feature_branch="agent/y", instructions_inline="x"),
        "ag", "sess",
    )
    cp = _run_cli("heartbeat-meta", json.dumps(initial))
    new_meta = parse_body(cp.stdout)
    assert new_meta["status"] == "working"


def test_cli_heartbeat_meta_invalid_input():
    cp = _run_cli("heartbeat-meta", "null", expect_zero=False)
    assert cp.returncode != 0


def test_cli_finish_meta_round_trip():
    initial = claim_meta(
        make_initial_meta(feature_branch="agent/y", instructions_inline="x"),
        "ag", "sess",
    )
    cp = _run_cli("finish-meta", json.dumps(initial))
    parsed = parse_body(cp.stdout)
    assert parsed["status"] == "finished"


def test_cli_finish_meta_invalid_input():
    cp = _run_cli("finish-meta", "null", expect_zero=False)
    assert cp.returncode != 0


def test_cli_abandon_meta_round_trip():
    initial = claim_meta(
        make_initial_meta(feature_branch="agent/y", instructions_inline="x"),
        "ag", "sess",
    )
    cp = _run_cli(
        "abandon-meta", json.dumps(initial),
        "--reason", "merge_conflict",
    )
    parsed = parse_body(cp.stdout)
    assert parsed["status"] == "abandoned"
    assert parsed["abandon_reason"] == "merge_conflict"


def test_cli_abandon_meta_invalid_input():
    cp = _run_cli(
        "abandon-meta", "null", "--reason", "x",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_parse_comment_terminal():
    body = json.dumps({
        "protocol_version": 1, "kind": "batch-job-request",
        "run_status": "completed",
        "summary": {"x": 1},
        "log_manifest_path": "runs/5/9/manifest.json",
    })
    cp = _run_cli("parse-comment", body)
    out = json.loads(cp.stdout)
    assert out["run_status"] == "completed"
    assert out["summary_path"] == "runs/5/9/summary.json"
    assert out["log_manifest_path"] == "runs/5/9/manifest.json"


def test_cli_parse_comment_running():
    body = json.dumps({"run_status": "running", "kind": "batch-job-request",
                       "protocol_version": 1})
    cp = _run_cli("parse-comment", body)
    out = json.loads(cp.stdout)
    assert out["run_status"] is None  # not terminal
    assert out["summary_path"] is None


def test_cli_parse_comment_invalid_body():
    cp = _run_cli("parse-comment", "not json")
    out = json.loads(cp.stdout)
    assert out["run_status"] is None
    assert out["envelope"] == {}


def test_cli_parse_meta_returns_dict():
    meta = make_initial_meta(
        feature_branch="agent/p", instructions_inline="x"
    )
    body = render_body(meta, prose="ok")
    cp = _run_cli("parse-meta", body)
    out = json.loads(cp.stdout)
    assert out["feature_branch"] == "agent/p"


def test_cli_parse_meta_returns_null_when_missing():
    cp = _run_cli("parse-meta", "no block here")
    assert cp.stdout.strip() == "null"


def test_cli_summary_path():
    cp = _run_cli("summary-path", "--issue", "7", "--comment", "12345")
    out = json.loads(cp.stdout)
    assert out["summary_path"] == "runs/7/12345/summary.json"


def test_cli_summary_path_validation():
    cp = _run_cli(
        "summary-path", "--issue", "0", "--comment", "1",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_replace_meta_preserves_prose():
    meta1 = make_initial_meta(
        feature_branch="agent/q", instructions_inline="x"
    )
    body = render_body(meta1, prose="Some prose")
    meta2 = claim_meta(meta1, "ag", "sess")
    cp = _run_cli(
        "replace-meta", body, "--meta-json", json.dumps(meta2),
    )
    assert "Some prose" in cp.stdout
    parsed = parse_body(cp.stdout)
    assert parsed["status"] == "working"


def test_cli_replace_meta_invalid():
    cp = _run_cli(
        "replace-meta", "body", "--meta-json", "null",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_validate_summary_completed_ok():
    summary = {
        "echoed_args": {"message": "x"},
        "message": "x",
    }
    cp = _run_cli(
        "validate-summary", json.dumps(summary),
        "--command", "echo", "--status", "completed",
    )
    out = json.loads(cp.stdout)
    assert out["valid"] is True


def test_cli_validate_summary_completed_invalid():
    cp = _run_cli(
        "validate-summary", "{}",
        "--command", "echo", "--status", "completed",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_validate_summary_error_branch_ok():
    summary = {"error_kind": "x", "error_detail": "y"}
    cp = _run_cli(
        "validate-summary", json.dumps(summary),
        "--command", "echo", "--status", "error",
    )
    out = json.loads(cp.stdout)
    assert out["valid"] is True


def test_cli_validate_summary_unknown_command():
    cp = _run_cli(
        "validate-summary", "{}",
        "--command", "no-such", "--status", "completed",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_cli_validate_summary_invalid_json_input():
    cp = _run_cli(
        "validate-summary", "not-json",
        "--command", "echo", "--status", "completed",
        expect_zero=False,
    )
    assert cp.returncode != 0


def test_package_dunder_all_is_complete():
    # smoke: all named exports are importable.
    for name in agent_lib.__all__:
        assert getattr(agent_lib, name) is not None


# ---------------------------------------------------------------------------
# In-process CLI tests (for coverage of cli.py)
# ---------------------------------------------------------------------------

def _call_main(capsys, argv):
    from agent_lib import cli  # local import so coverage tracks the module
    rc = cli.main(argv)
    out = capsys.readouterr()
    return rc, out


def _call_main_expect_exit(capsys, argv):
    from agent_lib import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    out = capsys.readouterr()
    return exc.value.code, out


def test_main_make_request_in_process(capsys):
    rc, out = _call_main(capsys, [
        "make-request", '{"message": "x"}',
        "--command", "echo",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
    ])
    assert rc == 0
    env = json.loads(out.out)
    assert env["command"] == "echo"


def test_main_make_request_invalid_json(capsys):
    code, out = _call_main_expect_exit(capsys, [
        "make-request", "not-json",
        "--command", "echo",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
    ])
    assert code != 0
    assert "invalid JSON" in out.err


def test_main_make_request_args_must_be_object(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "make-request", '"a-string"',
        "--command", "echo",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
    ])
    assert code != 0


def test_main_make_request_envelope_invalid_args(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "make-request", '{"target": "x", "extra": "y"}',
        "--command", "build",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
    ])
    assert code != 0


def test_main_make_request_skip_validate(capsys):
    rc, out = _call_main(capsys, [
        "make-request", '{"target": "x", "extra": "y"}',
        "--command", "build",
        "--branch", "agent/1",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
        "--no-validate",
    ])
    assert rc == 0


def test_main_make_request_propagates_value_error(capsys):
    """The pure helper raises ValueError on empty branch."""
    code, _ = _call_main_expect_exit(capsys, [
        "make-request", '{"message": "x"}',
        "--command", "echo",
        "--branch", "",
        "--sha", "0" * 40,
        "--subagent-id", "alpha",
    ])
    assert code != 0


def test_main_make_initial_meta(capsys):
    payload = json.dumps({
        "feature_branch": "agent/x",
        "instructions_inline": "Do.",
    })
    rc, out = _call_main(capsys, [
        "make-initial-meta", payload, "--prose", "P",
    ])
    assert rc == 0
    assert "P" in out.out
    assert "agent-meta" in out.out


def test_main_make_initial_meta_payload_must_be_object(capsys):
    code, _ = _call_main_expect_exit(
        capsys, ["make-initial-meta", '"x"']
    )
    assert code != 0


def test_main_make_initial_meta_invalid_payload_value(capsys):
    code, _ = _call_main_expect_exit(
        capsys, ["make-initial-meta", '{"feature_branch": ""}'],
    )
    assert code != 0


def test_main_make_initial_meta_unsupported_kwarg(capsys):
    code, _ = _call_main_expect_exit(
        capsys,
        ["make-initial-meta",
         json.dumps({"feature_branch": "x", "instructions_inline": "x",
                     "no_such_kw": True})],
    )
    assert code != 0


def test_main_claim_meta(capsys):
    initial = make_initial_meta(
        feature_branch="agent/y", instructions_inline="x"
    )
    rc, out = _call_main(capsys, [
        "claim-meta", json.dumps(initial),
        "--agent-id", "ag", "--session-id", "ss",
    ])
    assert rc == 0
    parsed = parse_body(out.out)
    assert parsed["agent_id"] == "ag"


def test_main_claim_meta_invalid_meta(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "claim-meta", "[]", "--agent-id", "x", "--session-id", "y",
    ])
    assert code != 0


def test_main_claim_meta_invalid_args(capsys):
    initial = make_initial_meta(
        feature_branch="agent/y", instructions_inline="x"
    )
    code, _ = _call_main_expect_exit(capsys, [
        "claim-meta", json.dumps(initial),
        "--agent-id", "", "--session-id", "ss",
    ])
    assert code != 0


def test_main_heartbeat_meta(capsys):
    base = claim_meta(
        make_initial_meta(feature_branch="agent/y", instructions_inline="x"),
        "ag", "ss",
    )
    rc, out = _call_main(capsys, ["heartbeat-meta", json.dumps(base)])
    assert rc == 0
    parsed = parse_body(out.out)
    assert parsed["status"] == "working"


def test_main_heartbeat_meta_invalid(capsys):
    code, _ = _call_main_expect_exit(capsys, ["heartbeat-meta", "null"])
    assert code != 0


def test_main_finish_meta(capsys):
    base = claim_meta(
        make_initial_meta(feature_branch="agent/y", instructions_inline="x"),
        "ag", "ss",
    )
    rc, out = _call_main(capsys, ["finish-meta", json.dumps(base)])
    assert rc == 0
    parsed = parse_body(out.out)
    assert parsed["status"] == "finished"


def test_main_finish_meta_invalid(capsys):
    code, _ = _call_main_expect_exit(capsys, ["finish-meta", "null"])
    assert code != 0


def test_main_abandon_meta(capsys):
    base = claim_meta(
        make_initial_meta(feature_branch="agent/y", instructions_inline="x"),
        "ag", "ss",
    )
    rc, out = _call_main(capsys, [
        "abandon-meta", json.dumps(base), "--reason", "x",
    ])
    assert rc == 0


def test_main_abandon_meta_invalid(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "abandon-meta", "null", "--reason", "x",
    ])
    assert code != 0


def test_main_parse_comment_terminal(capsys):
    body = json.dumps({
        "protocol_version": 1, "kind": "batch-job-request",
        "run_status": "completed",
        "summary": {"x": 1},
        "log_manifest_path": "runs/5/9/manifest.json",
    })
    rc, out = _call_main(capsys, ["parse-comment", body])
    assert rc == 0
    res = json.loads(out.out)
    assert res["summary_path"] == "runs/5/9/summary.json"


def test_main_parse_comment_terminal_no_manifest_path(capsys):
    body = json.dumps({
        "protocol_version": 1, "kind": "batch-job-request",
        "run_status": "completed",
        "summary": {"x": 1},
    })
    rc, out = _call_main(capsys, ["parse-comment", body])
    res = json.loads(out.out)
    assert res["summary_path"] is None
    assert res["log_manifest_path"] is None


def test_main_parse_meta_present(capsys):
    meta = make_initial_meta(feature_branch="agent/p", instructions_inline="x")
    body = render_body(meta)
    rc, out = _call_main(capsys, ["parse-meta", body])
    assert rc == 0
    parsed = json.loads(out.out)
    assert parsed["feature_branch"] == "agent/p"


def test_main_parse_meta_absent(capsys):
    rc, out = _call_main(capsys, ["parse-meta", "no block"])
    assert rc == 0
    assert out.out.strip() == "null"


def test_main_summary_path(capsys):
    rc, out = _call_main(capsys, [
        "summary-path", "--issue", "3", "--comment", "44",
    ])
    assert rc == 0
    res = json.loads(out.out)
    assert res["summary_path"] == "runs/3/44/summary.json"


def test_main_summary_path_invalid(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "summary-path", "--issue", "0", "--comment", "1",
    ])
    assert code != 0


def test_main_replace_meta(capsys):
    meta1 = make_initial_meta(
        feature_branch="agent/q", instructions_inline="x"
    )
    body = render_body(meta1, prose="P")
    meta2 = claim_meta(meta1, "ag", "ss")
    rc, out = _call_main(capsys, [
        "replace-meta", body, "--meta-json", json.dumps(meta2),
    ])
    assert rc == 0
    assert "P" in out.out


def test_main_replace_meta_invalid(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "replace-meta", "body", "--meta-json", "null",
    ])
    assert code != 0


def test_main_validate_summary_ok(capsys):
    summary = {"echoed_args": {}, "message": "x"}
    rc, out = _call_main(capsys, [
        "validate-summary", json.dumps(summary),
        "--command", "echo", "--status", "completed",
    ])
    assert rc == 0


def test_main_validate_summary_bad(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "validate-summary", "{}",
        "--command", "echo", "--status", "completed",
    ])
    assert code != 0


def test_main_validate_summary_error_status(capsys):
    summary = {"error_kind": "x", "error_detail": "y"}
    rc, _ = _call_main(capsys, [
        "validate-summary", json.dumps(summary),
        "--command", "echo", "--status", "error",
    ])
    assert rc == 0


def test_main_validate_summary_unknown_command(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "validate-summary", "{}",
        "--command", "not-real", "--status", "completed",
    ])
    assert code != 0


def test_main_validate_summary_missing_subschema(capsys, tmp_path, monkeypatch):
    """If the schema lacks a summary_completed sub-schema, fail clearly."""
    # Stub _common.load_schema to return a schema without the desired subkey.
    from agent_lib import cli
    real = cli._common.load_schema

    def fake(name, root=None):
        return {"properties": {"args": {"type": "object"}}}

    monkeypatch.setattr(cli._common, "load_schema", fake)
    code, out = _call_main_expect_exit(capsys, [
        "validate-summary", "{}",
        "--command", "echo", "--status", "completed",
    ])
    monkeypatch.setattr(cli._common, "load_schema", real)
    assert code != 0
    assert "no summary_completed sub-schema" in out.err


def test_main_validate_summary_invalid_json(capsys):
    code, _ = _call_main_expect_exit(capsys, [
        "validate-summary", "not-json",
        "--command", "echo", "--status", "completed",
    ])
    assert code != 0


# ---------------------------------------------------------------------------
# CLI: make-ack subcommand
# ---------------------------------------------------------------------------

def test_cli_make_ack_happy():
    cp = _run_cli("make-ack", "--ack-for", "42")
    env = json.loads(cp.stdout)
    assert env["protocol_version"] == 1
    assert env["kind"] == "agent-ack"
    assert env["ack_for"] == 42
    assert env["agent_acked_at"].endswith("Z")


def test_cli_make_ack_with_optional_fields():
    cp = _run_cli(
        "make-ack",
        "--ack-for", "7",
        "--agent-id", "A1",
        "--session-id", "S1",
        "--note", "follow-up",
    )
    env = json.loads(cp.stdout)
    assert env["agent_id"] == "A1"
    assert env["session_id"] == "S1"
    assert env["note"] == "follow-up"


def test_cli_make_ack_rejects_zero_ack_for():
    cp = _run_cli("make-ack", "--ack-for", "0", expect_zero=False)
    assert cp.returncode != 0
    err = json.loads(cp.stderr.strip().splitlines()[-1])
    assert "ack_for" in err["error"]


def test_cli_make_ack_rejects_negative_ack_for():
    cp = _run_cli("make-ack", "--ack-for", "-3", expect_zero=False)
    assert cp.returncode != 0


def test_cli_make_ack_requires_ack_for():
    cp = _run_cli("make-ack", expect_zero=False)
    # argparse error on missing required arg → non-zero exit.
    assert cp.returncode != 0


def test_main_make_ack_happy(capsys):
    """Exercise the in-process main() path for coverage."""
    from agent_lib import cli
    rc = cli.main(["make-ack", "--ack-for", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    env = json.loads(out)
    assert env["ack_for"] == 5
    assert env["kind"] == "agent-ack"
