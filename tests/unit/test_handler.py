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
    """Per the spec, an args validation failure produces parse_error (impl choice)."""
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
    assert res["action"] in ("parse_error", "error")
    assert final["run_status"] in ("parse_error", "error")


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
    assert res["action"] in ("parse_error", "error")
    assert final["run_status"] in ("parse_error", "error")


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
