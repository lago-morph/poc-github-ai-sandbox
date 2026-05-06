"""Tests for the ``agent-ack`` follow-up comment kind (SPEC §4.1, §5.2).

Covers:
  - ``agent_lib.make_ack_envelope`` happy path + validation errors.
  - The new envelope validates against
    ``.agent/schemas/comment-ack-envelope.schema.json``.
  - Handler skips ``kind: agent-ack`` comments instead of treating them
    as a batch-job-request (no parse_error, no body mutation).
  - ``agent_lib.parse_ack_comment`` parses valid bodies, rejects the
    obvious negatives, and tolerates the same MCP quirks
    ``parse_terminal_status`` does (HTML escaping, trailer prose).
  - ``agent_lib.is_request_acked`` accepts BOTH the in-place
    (``agent_ack: finished``) and follow-up (``kind: agent-ack``)
    ack forms.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import pytest

import agent_protocol_common as common
import handler  # from .agent/scripts via pythonpath
from agent_lib import (
    is_request_acked,
    make_ack_envelope,
    parse_ack_comment,
)
from tests.conftest import make_envelope


REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# make_ack_envelope
# ---------------------------------------------------------------------------

def test_make_ack_envelope_happy_path():
    env = make_ack_envelope(123)
    assert env["protocol_version"] == 1
    assert env["kind"] == "agent-ack"
    assert env["ack_for"] == 123
    # iso-8601 UTC zulu form (matches iso_now())
    assert env["agent_acked_at"].endswith("Z")
    # optional fields not present when unset
    assert "agent_id" not in env
    assert "session_id" not in env
    assert "note" not in env


def test_make_ack_envelope_optional_fields():
    env = make_ack_envelope(
        7, agent_id="A", session_id="S", note="hi",
    )
    assert env["agent_id"] == "A"
    assert env["session_id"] == "S"
    assert env["note"] == "hi"


def test_make_ack_envelope_supplied_timestamp():
    ts = "2030-01-02T03:04:05Z"
    env = make_ack_envelope(1, agent_acked_at=ts)
    assert env["agent_acked_at"] == ts


@pytest.mark.parametrize(
    "bad",
    [0, -1, "1", 1.5, None, True, False],
)
def test_make_ack_envelope_rejects_bad_ack_for(bad):
    with pytest.raises(ValueError):
        make_ack_envelope(bad)  # type: ignore[arg-type]


def test_make_ack_envelope_validates_against_schema():
    schema = common.load_schema(
        "comment-ack-envelope.schema.json", str(REPO_ROOT)
    )
    env = make_ack_envelope(42, agent_id="A", note="ok")
    # Should not raise.
    common.validate(env, schema)


def test_make_ack_envelope_schema_rejects_wrong_kind():
    schema = common.load_schema(
        "comment-ack-envelope.schema.json", str(REPO_ROOT)
    )
    bad = {
        "protocol_version": 1,
        "kind": "batch-job-request",  # wrong const
        "ack_for": 1,
        "agent_acked_at": common.iso_now(),
    }
    with pytest.raises(Exception):
        common.validate(bad, schema)


# ---------------------------------------------------------------------------
# Handler dispatch — agent-ack must be a noop
# ---------------------------------------------------------------------------

def test_handler_treats_agent_ack_as_noop(client, base_config,
                                          locked_issue_with_branch):
    """Posting a ``kind: agent-ack`` comment must NOT be schema-validated
    against ``comment-envelope.schema.json`` (which says
    ``kind: const "batch-job-request"``). The handler should return a
    noop and leave the body unchanged."""
    fix = locked_issue_with_branch
    ack_env = make_ack_envelope(999, agent_id="A")
    body = json.dumps(ack_env, indent=2)
    c = client.add_comment(fix["issue_number"], body)

    result = handler.run(
        client, fix["issue_number"], c["id"],
        config=base_config, repo_root=str(REPO_ROOT),
    )
    assert result["action"] == "noop"
    assert result["reason"] == "ack_comment"
    assert result.get("kind") == "agent-ack"
    # Body was NOT replaced with a parse_error envelope.
    after = client.get_comment(c["id"])
    assert after["body"] == body
    parsed = json.loads(after["body"])
    assert parsed["kind"] == "agent-ack"
    assert "run_status" not in parsed  # handler did not append one


def test_handler_does_not_parse_error_on_agent_ack(client, base_config,
                                                   locked_issue_with_branch):
    """Regression: without the kind dispatch, the next step would be
    schema validation against comment-envelope.schema.json, which would
    fail and rewrite the body as a parse_error envelope."""
    fix = locked_issue_with_branch
    ack_env = make_ack_envelope(1)
    body = json.dumps(ack_env, indent=2)
    c = client.add_comment(fix["issue_number"], body)

    handler.run(
        client, fix["issue_number"], c["id"],
        config=base_config, repo_root=str(REPO_ROOT),
    )
    # No parse_error envelope was written.
    after_body = client.get_comment(c["id"])["body"]
    parsed = json.loads(after_body)
    assert parsed.get("run_status") != "parse_error"
    assert parsed["kind"] == "agent-ack"


# ---------------------------------------------------------------------------
# parse_ack_comment
# ---------------------------------------------------------------------------

def test_parse_ack_comment_valid_body():
    env = make_ack_envelope(11)
    parsed = parse_ack_comment(json.dumps(env))
    assert parsed is not None
    assert parsed["kind"] == "agent-ack"
    assert parsed["ack_for"] == 11


def test_parse_ack_comment_non_json_returns_none():
    assert parse_ack_comment("not json at all") is None
    assert parse_ack_comment("") is None
    assert parse_ack_comment("   ") is None


def test_parse_ack_comment_non_string_returns_none():
    assert parse_ack_comment(None) is None  # type: ignore[arg-type]
    assert parse_ack_comment(123) is None  # type: ignore[arg-type]
    assert parse_ack_comment(["a"]) is None  # type: ignore[arg-type]


def test_parse_ack_comment_wrong_kind_returns_none():
    body = json.dumps(make_envelope(command="echo"))
    assert parse_ack_comment(body) is None


def test_parse_ack_comment_wrong_protocol_version_returns_none():
    body = json.dumps({
        "protocol_version": 2,
        "kind": "agent-ack",
        "ack_for": 1,
        "agent_acked_at": common.iso_now(),
    })
    assert parse_ack_comment(body) is None


def test_parse_ack_comment_handles_html_escaped_body():
    """MCP returns issue/comment bodies HTML-escaped (e.g. &#34; for ").
    parse_ack_comment must unescape before JSON-parsing."""
    raw = json.dumps(make_ack_envelope(5))
    # Roundtrip-escape the JSON string the way MCP would.
    escaped = (
        raw.replace("&", "&amp;")
           .replace('"', "&#34;")
    )
    assert html.unescape(escaped) == raw  # sanity
    parsed = parse_ack_comment(escaped)
    assert parsed is not None
    assert parsed["kind"] == "agent-ack"
    assert parsed["ack_for"] == 5


def test_parse_ack_comment_tolerates_trailer():
    """Claude Code's GitHub MCP appends a markdown trailer to every
    posted comment. Strict json.loads would fail; raw_decode must
    accept the leading JSON-object prefix."""
    env = make_ack_envelope(8)
    body = (
        json.dumps(env, indent=2)
        + "\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_\n"
    )
    parsed = parse_ack_comment(body)
    assert parsed is not None
    assert parsed["ack_for"] == 8


def test_parse_ack_comment_non_dict_json_returns_none():
    assert parse_ack_comment("[]") is None
    assert parse_ack_comment('"a string"') is None
    assert parse_ack_comment("42") is None


# ---------------------------------------------------------------------------
# is_request_acked
# ---------------------------------------------------------------------------

def test_is_request_acked_true_for_inplace_finished():
    env = {"agent_ack": "finished"}
    assert is_request_acked(env, request_comment_id=10,
                            other_comment_bodies=[]) is True


def test_is_request_acked_true_for_followup_with_matching_ack_for():
    request_env = {"agent_ack": None}
    follow = json.dumps(make_ack_envelope(42))
    assert is_request_acked(
        request_env,
        request_comment_id=42,
        other_comment_bodies=["unrelated chatter", follow],
    ) is True


def test_is_request_acked_false_when_no_ack_anywhere():
    request_env = {"agent_ack": None}
    assert is_request_acked(
        request_env,
        request_comment_id=1,
        other_comment_bodies=["hi", "no JSON here either"],
    ) is False


def test_is_request_acked_false_when_followup_ack_for_mismatches():
    request_env = {"agent_ack": None}
    follow = json.dumps(make_ack_envelope(99))
    assert is_request_acked(
        request_env,
        request_comment_id=42,
        other_comment_bodies=[follow],
    ) is False


def test_is_request_acked_false_when_followup_is_request_kind():
    """A follow-up that's really a batch-job-request must not count."""
    request_env = {"agent_ack": None}
    not_an_ack = json.dumps(make_envelope(command="echo"))
    assert is_request_acked(
        request_env,
        request_comment_id=42,
        other_comment_bodies=[not_an_ack],
    ) is False


def test_is_request_acked_inplace_takes_precedence_over_followup():
    """When the request comment itself is acked in-place, we don't
    even need to scan the follow-ups."""
    request_env = {"agent_ack": "finished"}
    # Pass garbage other-bodies; should still return True.
    assert is_request_acked(
        request_env,
        request_comment_id=1,
        other_comment_bodies=["junk"],
    ) is True
