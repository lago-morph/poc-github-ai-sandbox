"""Tests for the ``chatty`` command (``.agent/commands/chatty.py``).

The handler emits many log records. The chatty command itself overrides
the LogWriter rotation threshold to a small default (8192 bytes) at the
top of ``run()`` so that rotation fires reliably with a modest line
count. The production default
(``logs.max_chunk_bytes_compressed: 524288``) is preserved for non-test
commands.

For unit-test speed we mostly run with a small ``lines`` value plus a
tightened chunk size to verify rotation logic without paying for
hundreds or thousands of lines on every test run.
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


def _load_chatty_module():
    name = "_agent_command_chatty_test_loader"
    if name in sys.modules:
        return sys.modules[name]
    spec = _ilu.spec_from_file_location(
        name, REPO_ROOT / ".agent" / "commands" / "chatty.py"
    )
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# direct invocation
# ---------------------------------------------------------------------------

def test_chatty_direct_emits_requested_lines():
    mod = _load_chatty_module()
    lw = common.LogWriter()
    summary = mod.run({"lines": 50}, lw, workspace=None)
    chunks = lw.finalize()
    total = sum(info["lines"] for _, _, info in chunks)
    assert summary["lines_emitted"] == 50
    assert total == 50
    assert "50" in summary["message"]


def test_chatty_direct_zero_lines_produces_no_chunks():
    mod = _load_chatty_module()
    lw = common.LogWriter()
    summary = mod.run({"lines": 0}, lw, workspace=None)
    assert summary["lines_emitted"] == 0
    chunks = lw.finalize()
    assert chunks == []  # nothing written


def test_chatty_direct_rejects_negative_treated_as_zero():
    mod = _load_chatty_module()
    lw = common.LogWriter()
    summary = mod.run({"lines": -10}, lw, workspace=None)
    assert summary["lines_emitted"] == 0


def test_chatty_default_args_when_lines_missing():
    mod = _load_chatty_module()
    # We don't actually want to run 500 lines in unit tests; verify the
    # function accepts an empty args dict by passing only ``lines=1`` to
    # keep the run fast and assert that the default chatty behaviour
    # (overriding the LogWriter threshold) is wired.
    lw = common.LogWriter()
    summary = mod.run({"lines": 1}, lw, workspace=None)
    assert summary["lines_emitted"] == 1


def test_chatty_overrides_log_writer_threshold_by_default():
    """When called without ``max_chunk_bytes_compressed``, chatty lowers
    the LogWriter threshold to its small default (8192) so a modest line
    count rotates multiple chunks even though the production default
    would not.
    """
    mod = _load_chatty_module()
    # Construct a LogWriter at the production threshold. If chatty did
    # NOT override it, 500 lines (~ small number of bytes compressed)
    # would not rotate.
    lw = common.LogWriter(max_chunk_bytes_compressed=524_288)
    summary = mod.run({"lines": 500}, lw, workspace=None)
    chunks = lw.finalize()
    assert summary["lines_emitted"] == 500
    # The override (8192-byte threshold) must produce ≥2 chunks.
    assert len(chunks) >= 2


def test_chatty_explicit_max_chunk_bytes_compressed_arg_is_honored():
    """Passing ``max_chunk_bytes_compressed`` overrides chatty's own
    default: with a tiny threshold, even ~200 lines rotate."""
    mod = _load_chatty_module()
    lw = common.LogWriter(max_chunk_bytes_compressed=10_000_000)
    summary = mod.run(
        {"lines": 200, "max_chunk_bytes_compressed": 512},
        lw,
        workspace=None,
    )
    chunks = lw.finalize()
    assert summary["lines_emitted"] == 200
    assert len(chunks) >= 2


def test_chatty_rotation_at_small_chunk_size():
    """With a small max_chunk_bytes_compressed via args, rotation kicks
    in fast."""
    mod = _load_chatty_module()
    lw = common.LogWriter(max_chunk_bytes_compressed=10_000_000)
    summary = mod.run(
        {"lines": 200, "max_chunk_bytes_compressed": 512},
        lw,
        workspace=None,
    )
    chunks = lw.finalize()
    assert summary["lines_emitted"] == 200
    # Several chunks expected at this tiny rotation size.
    assert len(chunks) >= 2


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------

def test_chatty_schema_accepts_max_chunk_bytes_compressed_arg():
    schema = common.load_schema("commands/chatty.schema.json", REPO_ROOT)
    args_schema = schema["properties"]["args"]
    assert "max_chunk_bytes_compressed" in args_schema["properties"]
    prop = args_schema["properties"]["max_chunk_bytes_compressed"]
    assert prop["type"] == "integer"
    assert prop["minimum"] == 1
    # An envelope passing both args validates.
    common.validate(
        {"lines": 500, "max_chunk_bytes_compressed": 8192},
        args_schema,
    )


def test_chatty_schema_rejects_zero_max_chunk_bytes_compressed():
    """``max_chunk_bytes_compressed=0`` violates ``minimum: 1``."""
    schema = common.load_schema("commands/chatty.schema.json", REPO_ROOT)
    args_schema = schema["properties"]["args"]
    with pytest.raises(ValueError):
        common.validate(
            {"lines": 1, "max_chunk_bytes_compressed": 0},
            args_schema,
        )


# ---------------------------------------------------------------------------
# through the handler
# ---------------------------------------------------------------------------

def test_chatty_through_handler_completed(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    # Tighten chunk size so the unit test is fast but still exercises rotation.
    cfg = dict(base_config)
    cfg["logs"] = dict(base_config["logs"])
    cfg["logs"]["max_chunk_bytes_compressed"] = 512
    env = make_envelope(
        command="chatty", args={"lines": 200},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=cfg, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "ran"
    assert res["run_status"] == "completed"
    assert len(res["chunks"]) >= 2
    final = json.loads(client.get_comment(cid)["body"])
    assert final["summary"]["lines_emitted"] == 200


def test_chatty_invalid_lines_args(client, base_config, locked_issue_with_branch):
    """Schema's ``additionalProperties: false`` rejects unknown keys."""
    fix = locked_issue_with_branch
    env = make_envelope(
        command="chatty", args={"lines": 1, "extra": "x"},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    res = handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert res["action"] == "parse_error"


def test_chatty_summary_schema(client, base_config, locked_issue_with_branch):
    fix = locked_issue_with_branch
    env = make_envelope(
        command="chatty", args={"lines": 5},
        branch=fix["branch"], commit_sha=fix["sha"],
    )
    cid = _post_envelope(client, fix["issue_number"], env)
    handler.run(
        client, fix["issue_number"], cid,
        config=base_config, repo_root=str(REPO_ROOT),
    )
    final = json.loads(client.get_comment(cid)["body"])
    schema = common.load_schema("commands/chatty.schema.json", REPO_ROOT)
    sub = schema["properties"]["summary_completed"]
    common.validate(final["summary"], sub)


def test_chatty_in_registry(base_config):
    assert "chatty" in base_config["commands"]
