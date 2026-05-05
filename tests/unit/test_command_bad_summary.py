"""Tests for the ``bad-summary`` command (``.agent/commands/bad_summary.py``).

The handler intentionally returns ``{}``; the workflow handler must
detect the schema violation and emit a terminal ``error`` envelope
with ``error_kind="summary_schema_violation"``.
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


def _load_bad_summary_module():
    name = "_agent_command_bad_summary_test_loader"
    if name in sys.modules:
        return sys.modules[name]
    spec = _ilu.spec_from_file_location(
        name, REPO_ROOT / ".agent" / "commands" / "bad_summary.py"
    )
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# direct invocation
# ---------------------------------------------------------------------------

def test_bad_summary_direct_returns_empty_dict():
    mod = _load_bad_summary_module()
    lw = common.LogWriter()
    result = mod.run({}, lw, workspace=None)
    assert result == {}
    chunks = lw.finalize()
    total_lines = sum(info["lines"] for _, _, info in chunks)
    assert total_lines == 1


# ---------------------------------------------------------------------------
# through the handler
# ---------------------------------------------------------------------------

def test_bad_summary_through_handler_yields_summary_schema_violation(
    client, base_config, locked_issue_with_branch
):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="bad-summary",
        args={},
        branch=fix["branch"],
        commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ran"
    assert res["run_status"] == "error"
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "error"
    assert final["error_kind"] == "summary_schema_violation"
    assert final["summary"]["error_kind"] == "summary_schema_violation"
    assert "required_field" in final["error_detail"]


def test_bad_summary_logs_and_summary_artifacts_still_written(
    client, base_config, locked_issue_with_branch
):
    """Even on summary_schema_violation, manifest/logs/summary should land."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="bad-summary", args={},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    branch = base_config["logs"]["branch"]
    manifest_raw = client.get_file_contents(
        f"runs/{fix['issue_number']}/{cid}/manifest.json", branch,
    )
    summary_raw = client.get_file_contents(
        f"runs/{fix['issue_number']}/{cid}/summary.json", branch,
    )
    assert manifest_raw is not None
    assert summary_raw is not None
    summary_json = json.loads(summary_raw)
    assert summary_json["run_status"] == "error"
    assert summary_json["summary"]["error_kind"] == "summary_schema_violation"


def test_bad_summary_in_registry(base_config):
    assert "bad-summary" in base_config["commands"]
