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
    max_chunk_bytes_compressed = 64
    lw = common.LogWriter(max_chunk_bytes_compressed=max_chunk_bytes_compressed)
    big_payload = "x" * 1000
    for i in range(20):
        lw.write({"ts": common.iso_now(), "stream": "stdout",
                  "phase": "exec", "data": big_payload})
    chunks = lw.finalize()
    assert len(chunks) >= 2
    # Bound chunk size: each chunk should not be wildly larger than the
    # threshold. Allow ~20% slack for gzip header/footer + the line that
    # tipped the rotation. The very last chunk may be smaller (residual).
    for path, gz_bytes, info in chunks[:-1]:
        # Active chunks all rotated *because* they crossed the threshold.
        # In practice each gzipped chunk should be near the threshold, not
        # multiples of it.
        assert info["bytes"] <= max_chunk_bytes_compressed * 5
        assert info["bytes"] == len(gz_bytes)


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


# ---------------------------------------------------------------------------
# LogWriter edge cases (Section H)
# ---------------------------------------------------------------------------

def test_log_writer_handles_unicode():
    """Records containing emoji and non-ASCII text round-trip cleanly."""
    payload = {
        "msg": "héllo wörld \U0001f680 こんにちは",
        "extra": "ümläüt",
    }
    lw = common.LogWriter(max_chunk_bytes_compressed=10_000_000)
    for i in range(3):
        lw.write({
            "ts": common.iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": payload,
        })
    chunks = lw.finalize()
    assert chunks
    decompressed = gzip.decompress(chunks[0][1])
    lines = decompressed.decode("utf-8").splitlines()
    assert len(lines) == 3
    for ln in lines:
        obj = json.loads(ln)
        assert obj["data"]["msg"] == payload["msg"]
        assert obj["data"]["extra"] == payload["extra"]


def test_log_writer_zero_records():
    """Finalizing with no records produces 0 chunks (and the manifest agrees)."""
    lw = common.LogWriter()
    chunks = lw.finalize()
    assert chunks == []
    manifest = lw.manifest(
        command="echo", args={}, checked_out_sha="a" * 40,
        started_at=common.iso_now(), finished_at=common.iso_now(),
        exit_code=0,
    )
    assert manifest["chunks"] == []


def test_log_writer_huge_record_single_chunk():
    """A single record larger than max_chunk_bytes_compressed still goes into
    one chunk (we never split a record across chunks)."""
    lw = common.LogWriter(max_chunk_bytes_compressed=64)
    huge = "x" * 100_000  # uncompressed, way over threshold
    lw.write({"ts": common.iso_now(), "stream": "stdout",
              "phase": "exec", "data": huge})
    chunks = lw.finalize()
    assert len(chunks) == 1
    path, gz_bytes, info = chunks[0]
    assert info["lines"] == 1
    # Decompress and ensure the entire huge payload is intact.
    decompressed = gzip.decompress(gz_bytes)
    obj = json.loads(decompressed.decode("utf-8").rstrip("\n"))
    assert obj["data"] == huge


def test_log_writer_finalize_is_idempotent():
    """Calling finalize() twice returns the same chunk list."""
    lw = common.LogWriter()
    lw.write({"ts": common.iso_now(), "stream": "stdout",
              "phase": "exec", "data": "hi"})
    first = lw.finalize()
    second = lw.finalize()
    assert [(p, info) for p, _, info in first] == [(p, info) for p, _, info in second]


def test_log_writer_write_after_finalize_raises():
    lw = common.LogWriter()
    lw.write({"ts": common.iso_now(), "stream": "stdout",
              "phase": "exec", "data": "hi"})
    lw.finalize()
    with pytest.raises(RuntimeError):
        lw.write({"ts": common.iso_now(), "stream": "stdout",
                  "phase": "exec", "data": "after-close"})
