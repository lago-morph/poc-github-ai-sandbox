"""Unit tests for ``.agent/scripts/common.py``."""

from __future__ import annotations

import gzip
import io
import json
import re

import pytest

import agent_protocol_common as common
from tests.conftest import make_agent_meta


# ---------------------------------------------------------------------------
# parse_agent_meta / render_agent_meta
# ---------------------------------------------------------------------------

def test_parse_render_round_trip_preserves_data():
    meta = make_agent_meta(feature_branch="agent/7-x", instructions_inline="Hi")
    body = common.render_agent_meta(meta, prose="Some prose")
    parsed = common.parse_agent_meta(body)
    assert parsed == meta


def test_parse_agent_meta_returns_none_when_no_block():
    assert common.parse_agent_meta("just a plain markdown body") is None
    assert common.parse_agent_meta("") is None
    assert common.parse_agent_meta(None) is None


def test_parse_agent_meta_returns_none_on_malformed_json():
    body = "Hi\n\n```agent-meta\nthis is not { valid json\n```\n"
    assert common.parse_agent_meta(body) is None


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

_SCHEMA = {
    "type": "object",
    "required": ["x"],
    "properties": {"x": {"type": "integer"}},
    "additionalProperties": False,
}


def test_validate_accepts_valid_input():
    common.validate({"x": 3}, _SCHEMA)


@pytest.mark.parametrize(
    "obj",
    [
        {},
        {"x": "not-int"},
        {"x": 3, "y": 1},
    ],
)
def test_validate_rejects_invalid_input(obj):
    with pytest.raises(Exception):
        common.validate(obj, _SCHEMA)


# ---------------------------------------------------------------------------
# iso_now
# ---------------------------------------------------------------------------

def test_iso_now_format():
    s = common.iso_now()
    # Z suffix, ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
    assert s.endswith("Z")
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", s)


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_reads_default_file(repo_root_path):
    cfg = common.load_config(repo_root_path / ".agent" / "config.json")
    assert cfg["protocol_version"] == 1
    assert cfg["agent_login"] == "my-bot"
    assert "echo" in cfg["commands"]


# ---------------------------------------------------------------------------
# LogWriter
# ---------------------------------------------------------------------------

def test_log_writer_single_chunk_manifest():
    lw = common.LogWriter(max_chunk_bytes_compressed=10_000_000)
    for i in range(5):
        lw.write({"ts": common.iso_now(), "stream": "stdout",
                  "phase": "exec", "data": f"line {i}"})
    chunks = lw.finalize()
    manifest = lw.manifest(
        command="echo", args={}, checked_out_sha="a" * 40,
        started_at=common.iso_now(), finished_at=common.iso_now(),
        exit_code=0,
    )
    assert len(chunks) == 1
    assert len(manifest["chunks"]) == 1
    assert manifest["chunks"][0]["lines"] == 5


def test_log_writer_rotates_after_threshold():
    lw = common.LogWriter(max_chunk_bytes_compressed=64)
    big_payload = "x" * 1000
    for i in range(20):
        lw.write({"ts": common.iso_now(), "stream": "stdout",
                  "phase": "exec", "data": big_payload})
    chunks = lw.finalize()
    assert len(chunks) >= 2


def test_log_writer_chunks_are_valid_gzip_jsonl():
    lw = common.LogWriter(max_chunk_bytes_compressed=64)
    for i in range(10):
        lw.write({"ts": common.iso_now(), "stream": "stdout",
                  "phase": "exec", "data": f"x" * 200 + str(i)})
    chunks = lw.finalize()
    assert chunks
    for path, gz_bytes, info in chunks:
        decompressed = gzip.decompress(gz_bytes)
        lines = decompressed.decode("utf-8").splitlines()
        assert len(lines) == info["lines"]
        for ln in lines:
            obj = json.loads(ln)
            assert "stream" in obj


def test_log_writer_manifest_sums_across_chunks():
    lw = common.LogWriter(max_chunk_bytes_compressed=64)
    n = 30
    for i in range(n):
        lw.write({"ts": common.iso_now(), "stream": "stdout",
                  "phase": "exec", "data": "x" * 200})
    manifest = lw.manifest(
        command="echo", args={}, checked_out_sha="a" * 40,
        started_at=common.iso_now(), finished_at=common.iso_now(),
        exit_code=0,
    )
    total_lines = sum(c["lines"] for c in manifest["chunks"])
    total_bytes = sum(c["bytes"] for c in manifest["chunks"])
    assert total_lines == n
    assert total_bytes > 0
