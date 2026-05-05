"""Tests for the ``build`` command (``.agent/commands/build.py``).

Exercises the command handler through the high-level :func:`handler.run`
flow so we cover envelope parsing + args validation + per-command summary
schema. We also call ``build.run`` directly for fine-grained checks.
"""

from __future__ import annotations

import importlib.util as _ilu
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import agent_protocol_common as common
import handler
from tests.conftest import make_envelope


REPO_ROOT = Path(__file__).resolve().parents[2]


def _post_envelope(client, issue_number: int, envelope: dict[str, Any]) -> int:
    body = json.dumps(envelope, indent=2)
    return client.add_comment(issue_number, body)["id"]


def _load_build_module():
    name = "_agent_command_build_test_loader"
    if name in sys.modules:
        return sys.modules[name]
    spec = _ilu.spec_from_file_location(
        name, REPO_ROOT / ".agent" / "commands" / "build.py"
    )
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# happy paths
# ---------------------------------------------------------------------------

def test_build_default_target_through_handler(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="build", args={},  # all-default: target=default, release=False
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ran"
    assert res["run_status"] == "completed"
    final = json.loads(client.get_comment(cid)["body"])
    summary = final["summary"]
    # Required by build.schema.json (summary_completed):
    assert "artifact_path" in summary
    assert "size_bytes" in summary
    assert "duration_seconds" in summary
    assert summary["artifact_path"].startswith("build/out/")
    assert summary["size_bytes"] >= 0
    assert summary["duration_seconds"] >= 0


def test_build_release_flag_changes_artifact_name(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="build", args={"target": "alpha", "release": True},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    summary = final["summary"]
    assert "alpha" in summary["artifact_path"]
    assert "release" in summary["artifact_path"]
    assert res["run_status"] == "completed"


def test_build_summary_validates_against_schema(client, base_config, locked_issue_with_branch):
    """Defense in depth: the summary returned should validate against
    ``build.schema.json``'s ``summary_completed`` sub-schema."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="build", args={"target": "x"},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    schema = common.load_schema("commands/build.schema.json", REPO_ROOT)
    sub = schema["properties"]["summary_completed"]
    common.validate(final["summary"], sub)


# ---------------------------------------------------------------------------
# args validation
# ---------------------------------------------------------------------------

def test_build_invalid_args_yields_parse_error(client, base_config, locked_issue_with_branch):
    """Unknown property in args fails the command-args schema (parse_error)."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="build", args={"target": "x", "extra": "not-allowed"},
        branch=fix["branch"], commit_sha=fix["sha"],
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


def test_build_empty_target_args_rejected(client, base_config, locked_issue_with_branch):
    """``target`` is a string with minLength 1; an empty string is rejected."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="build", args={"target": ""},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "parse_error"


# ---------------------------------------------------------------------------
# direct invocation
# ---------------------------------------------------------------------------

def test_build_direct_run_writes_logs():
    build_mod = _load_build_module()
    lw = common.LogWriter()
    summary = build_mod.run({"target": "thing", "release": True}, lw, workspace=None)
    chunks = lw.finalize()
    # build emits 3 records: setup, exec, teardown.
    total_lines = sum(info["lines"] for _, _, info in chunks)
    assert total_lines == 3
    # Summary fields:
    assert summary["artifact_path"] == "build/out/thing-release.bin"
    assert summary["size_bytes"] == 1024 * 4096
    assert isinstance(summary["duration_seconds"], (int, float))


def test_build_direct_run_default_args_no_release():
    build_mod = _load_build_module()
    lw = common.LogWriter()
    summary = build_mod.run({}, lw, workspace=None)
    assert summary["artifact_path"] == "build/out/default.bin"
    assert summary["size_bytes"] == 1024 * 2048
