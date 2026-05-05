"""Tests for ``.agent/scripts/handler.py``."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import agent_protocol_common as common
import handler  # from .agent/scripts via pythonpath
from tests.conftest import make_envelope


REPO_ROOT = Path(__file__).resolve().parents[2]


def _post_envelope(client, issue_number: int, envelope: dict[str, Any]) -> int:
    body = json.dumps(envelope, indent=2)
    c = client.add_comment(issue_number, body)
    return c["id"]


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

def test_echo_happy_path(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", args={"message": "hi"},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    result = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert result["action"] == "ran"
    assert result["run_status"] == "completed"
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "completed"
    assert final["summary"]["message"] == "hi"
    assert final["log_manifest_path"].startswith(f"runs/{fix['issue_number']}/")
    # summary.json in _agent_runs
    summary_raw = client.get_file_contents(
        final["log_manifest_path"].rsplit("/", 1)[0] + "/summary.json",
        "_agent_runs",
    )
    assert summary_raw is not None
    sj = json.loads(summary_raw)
    assert sj["run_status"] == "completed"


def test_run_tests_happy_path(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="run-tests", args={"suite": "unit"},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    result = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert result["run_status"] == "completed"
    final = json.loads(client.get_comment(cid)["body"])
    for k in ("passed", "failed", "skipped", "duration_seconds"):
        assert k in final["summary"]


# ---------------------------------------------------------------------------
# Parse / validation errors
# ---------------------------------------------------------------------------

def test_invalid_json_body_silently_ignored(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    cid = client.add_comment(fix["issue_number"], "not valid json {[")["id"]
    other_cid = client.add_comment(fix["issue_number"], "totally unrelated")["id"]
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ignored"
    # Body is unchanged
    assert client.get_comment(cid)["body"] == "not valid json {["
    assert client.get_comment(other_cid)["body"] == "totally unrelated"


def test_json_without_protocol_markers_ignored(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    cid = client.add_comment(fix["issue_number"], json.dumps({"foo": "bar"}))["id"]
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ignored"
    assert json.loads(client.get_comment(cid)["body"]) == {"foo": "bar"}


def test_envelope_schema_violation_writes_parse_error(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    bad = {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "command": "echo",
        # missing branch, commit_sha, etc.
    }
    cid = client.add_comment(fix["issue_number"], json.dumps(bad))["id"]
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "parse_error"
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "parse_error"
    assert "original_body_b64" in final
    assert final["original_body_b64"]


def test_args_schema_violation_yields_parse_or_terminal_error(client, base_config, locked_issue_with_branch):
    """Per SPEC §5.2.4 args validation IS schema validation: parse_error + schema_validation_failed."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="run-tests", args={"suite": "not-a-valid-suite"},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    assert res["action"] == "parse_error"
    assert final["run_status"] == "parse_error"
    assert final["error_kind"] == "schema_validation_failed"
    assert "original_body_b64" in final and final["original_body_b64"]


# ---------------------------------------------------------------------------
# Protocol version handling (iter 2)
# ---------------------------------------------------------------------------

def test_unsupported_version_yields_parse_error(client, base_config, locked_issue_with_branch):
    """Iter 2: ``protocol_version`` other than 1 → parse_error ``unsupported_version``."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    env["protocol_version"] = 2
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "parse_error"
    assert res["error_kind"] == "unsupported_version"
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "parse_error"
    assert final["error_kind"] == "unsupported_version"
    assert final["original_body_b64"]


def test_supported_version_passes_through(client, base_config, locked_issue_with_branch):
    """Iter 2: ``protocol_version: 1`` is fine; the run proceeds normally."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    assert env["protocol_version"] == 1
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ran"
    assert res["run_status"] == "completed"


def test_short_sha_in_envelope_fails_schema(client, base_config, locked_issue_with_branch):
    """Envelope schema requires a 40-char lowercase-hex commit_sha."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"],
        commit_sha="abcdef1",  # 7 chars, schema requires 40
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "parse_error"
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "parse_error"
    assert final["error_kind"] == "schema_validation_failed"


# ---------------------------------------------------------------------------
# Branch/SHA mismatch
# ---------------------------------------------------------------------------

def test_branch_missing_writes_terminal_error(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo",
        branch="agent/does-not-exist",
        commit_sha="0123456789abcdef0123456789abcdef01234567",
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "error"
    assert res["error_kind"] == "branch_sha_mismatch"
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "error"
    assert final["error_kind"] == "branch_sha_mismatch"


def test_commit_sha_mismatch_writes_terminal_error(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"],
        commit_sha="0" * 40,  # wrong sha
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["error_kind"] == "branch_sha_mismatch"
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "error"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_idempotency_already_terminal_noop(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    body_before = client.get_comment(cid)["body"]
    res2 = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res2["action"] == "noop"
    assert client.get_comment(cid)["body"] == body_before


# ---------------------------------------------------------------------------
# Unknown command
# ---------------------------------------------------------------------------

def test_unknown_command_yields_error(client, base_config, locked_issue_with_branch):
    """Per iter-2 impl: unknown command is a terminal `error` (not parse_error)."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="not-a-real-command", args={},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    assert res["action"] == "error"
    assert res["error_kind"] == "unknown_command"
    assert final["run_status"] == "error"
    assert final["error_kind"] == "unknown_command"


# ---------------------------------------------------------------------------
# Summary schema violation
# ---------------------------------------------------------------------------

def test_summary_schema_violation_terminal_error(
    client, base_config, locked_issue_with_branch, monkeypatch
):
    fix = locked_issue_with_branch

    def bad_run(args, log_writer, workspace):
        # Returns something that violates echo's summary_completed schema.
        return {"echoed_args": "not-an-object", "message": 123}

    fake_module = type(sys)("_fake_echo")
    fake_module.run = bad_run
    monkeypatch.setattr(handler, "_load_command_handler", lambda command: bad_run)

    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    assert res["run_status"] == "error"
    assert final["run_status"] == "error"
    assert final["error_kind"] == "summary_schema_violation"


def test_command_exception_yields_terminal_error(
    client, base_config, locked_issue_with_branch, monkeypatch
):
    """If the command handler raises, we get a terminal `error` envelope
    with the exception class name as the error_kind."""
    fix = locked_issue_with_branch

    class CommandFailed(RuntimeError):
        pass

    def boom(args, log_writer, workspace):
        raise CommandFailed("synthetic failure")

    monkeypatch.setattr(handler, "_load_command_handler", lambda command: boom)

    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    assert res["run_status"] == "error"
    assert final["run_status"] == "error"
    # exception class name surfaces as error_kind for the surrounding envelope.
    assert final["error_kind"] == "CommandFailed"
    assert "synthetic failure" in final["error_detail"]


# ---------------------------------------------------------------------------
# Log writer / manifest checks
# ---------------------------------------------------------------------------

def test_log_writer_produces_at_least_one_chunk_for_echo(
    client, base_config, locked_issue_with_branch
):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert len(res["chunks"]) >= 1


def test_manifest_validates_against_schema(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    manifest_path = final["log_manifest_path"]
    raw = client.get_file_contents(manifest_path, "_agent_runs")
    manifest = json.loads(raw)
    schema = common.load_schema("log-manifest.schema.json", REPO_ROOT)
    common.validate(manifest, schema)


# ---------------------------------------------------------------------------
# Workflow guard boundary (Section D)
#
# These tests document that handler.run does NOT itself check lock/label/
# author state — those gates are enforced by the workflow YAML's `if:`
# expression. The handler trusts its caller; the tests below pin that
# behavior so a future "tighten in python" decision is a deliberate change.
# ---------------------------------------------------------------------------

def test_handler_proceeds_on_unlocked_issue(client, base_config, locked_issue_with_branch):
    """Handler runs even if the issue is not locked — gating is in the YAML."""
    fix = locked_issue_with_branch
    # Forcibly un-lock; lock_issue is the only setter, so we mutate state.
    client._issues[fix["issue_number"]].locked = False
    assert client.get_issue(fix["issue_number"])["locked"] is False

    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    # Handler does NOT enforce lock; it ran successfully.
    assert res["action"] == "ran"
    assert res["run_status"] == "completed"


def test_handler_proceeds_when_label_missing(client, base_config, locked_issue_with_branch):
    """Handler runs even if the agent-task label is missing."""
    fix = locked_issue_with_branch
    client._issues[fix["issue_number"]].labels = []
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ran"
    assert res["run_status"] == "completed"


def test_handler_proceeds_when_comment_author_is_random(client, base_config, locked_issue_with_branch):
    """Handler runs irrespective of comment author; YAML gates that."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    with client.as_user("some-random-human"):
        cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ran"
    assert res["run_status"] == "completed"


# ---------------------------------------------------------------------------
# Iter 3: Section E — missing_schema error kind
# ---------------------------------------------------------------------------

def test_handler_missing_schema_yields_error_with_missing_schema_kind(
    client, base_config, locked_issue_with_branch,
):
    """A command registered in cfg['commands'] but with no schema file on disk
    must produce a terminal error with error_kind='missing_schema'."""
    fix = locked_issue_with_branch
    # Augment config with a phantom command (no .schema.json file).
    cfg = json.loads(json.dumps(base_config))  # deep copy
    cfg["commands"] = list(cfg["commands"]) + ["phantom-cmd"]

    env = make_envelope(
        command="phantom-cmd", args={},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=cfg, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    assert res["action"] == "error"
    assert res["error_kind"] == "missing_schema"
    assert final["run_status"] == "error"
    assert final["error_kind"] == "missing_schema"
    assert "phantom-cmd" in final["error_detail"]


# ---------------------------------------------------------------------------
# Iter 3: Section H — additional handler edge cases
# ---------------------------------------------------------------------------

def test_handler_command_raises_during_run_records_partial_logs(
    client, base_config, locked_issue_with_branch, monkeypatch,
):
    """Command writes some logs before raising — manifest still records them
    and the terminal envelope is the error variant."""
    fix = locked_issue_with_branch

    def writes_then_raises(args, log_writer, workspace):
        log_writer.write({"ts": common.iso_now(), "stream": "stdout",
                          "phase": "exec", "data": "step 1 done"})
        log_writer.write({"ts": common.iso_now(), "stream": "stderr",
                          "phase": "exec", "data": "warning: weird input"})
        raise RuntimeError("boom mid-run")

    monkeypatch.setattr(handler, "_load_command_handler", lambda command: writes_then_raises)

    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    assert res["run_status"] == "error"
    assert final["run_status"] == "error"
    assert final["error_kind"] == "RuntimeError"
    # Manifest path was recorded and is reachable on the logs branch.
    manifest_raw = client.get_file_contents(final["log_manifest_path"], "_agent_runs")
    assert manifest_raw is not None
    manifest = json.loads(manifest_raw)
    # Partial logs survived — at least one chunk with the lines we wrote
    # (plus the traceback line that the handler itself writes on exception).
    total_lines = sum(c["lines"] for c in manifest["chunks"])
    assert total_lines >= 2  # our two writes + traceback


def test_concurrent_terminal_writes_idempotent(
    client, base_config, locked_issue_with_branch,
):
    """Calling handler.run twice on the same comment is a no-op the second
    time AND chunks are not duplicated under _agent_runs."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="echo", branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res1 = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res1["action"] == "ran"

    final1 = json.loads(client.get_comment(cid)["body"])
    log_dir = final1["log_manifest_path"].rsplit("/", 1)[0]

    # Capture the chunk-listing on _agent_runs by walking commits' files.
    head = client.get_branch_head_sha("_agent_runs")
    files_before = dict(client._commits[head].files)
    chunks_before = sorted(p for p in files_before if p.startswith(f"{log_dir}/log-"))

    # Second run on the same comment — must noop on the envelope side.
    res2 = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res2["action"] == "noop"

    head2 = client.get_branch_head_sha("_agent_runs")
    files_after = dict(client._commits[head2].files)
    chunks_after = sorted(p for p in files_after if p.startswith(f"{log_dir}/log-"))
    # No new chunk files for this run dir.
    assert chunks_after == chunks_before
