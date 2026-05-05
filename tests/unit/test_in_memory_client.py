"""Tests for :class:`InMemoryGitHubClient`."""

from __future__ import annotations

import pytest


def test_create_and_get_issue(client):
    issue = client.create_issue(title="t", body="b", user="alice")
    fetched = client.get_issue(issue["number"])
    assert fetched["title"] == "t"
    assert fetched["body"] == "b"
    assert fetched["user"]["login"] == "alice"
    assert fetched["state"] == "open"


def test_update_issue_body_and_state(client):
    issue = client.create_issue(title="t", body="b")
    n = issue["number"]
    client.update_issue(n, body="new")
    assert client.get_issue(n)["body"] == "new"
    client.update_issue(n, state="closed")
    assert client.get_issue(n)["state"] == "closed"


def test_lock_issue_marks_locked(client):
    issue = client.create_issue(title="t", body="b")
    assert issue["locked"] is False
    client.lock_issue(issue["number"])
    assert client.get_issue(issue["number"])["locked"] is True


def test_add_label_idempotent(client):
    issue = client.create_issue(title="t", body="b")
    n = issue["number"]
    client.add_label(n, "agent-task")
    client.add_label(n, "agent-task")
    labels = [l["name"] for l in client.get_issue(n)["labels"]]
    assert labels.count("agent-task") == 1


def test_list_comments_only_for_target_issue(client):
    a = client.create_issue(title="a", body="x")
    b = client.create_issue(title="b", body="y")
    client.add_comment(a["number"], "hello-a")
    client.add_comment(b["number"], "hello-b")
    a_comments = client.list_comments(a["number"])
    assert len(a_comments) == 1
    assert a_comments[0]["body"] == "hello-a"


def test_comment_lifecycle(client):
    issue = client.create_issue(title="t", body="b")
    c = client.add_comment(issue["number"], "first")
    cid = c["id"]
    assert client.get_comment(cid)["body"] == "first"
    client.update_comment(cid, "second")
    assert client.get_comment(cid)["body"] == "second"
    client.delete_comment(cid)
    with pytest.raises(KeyError):
        client.get_comment(cid)


def test_get_branch_head_sha_returns_none_for_missing(client):
    assert client.get_branch_head_sha("ghost-branch") is None


def test_put_file_creates_orphan_branch(client):
    res = client.put_file_contents("a.txt", b"hi", "msg", "_agent_runs")
    assert res["branch"] == "_agent_runs"
    sha = client.get_branch_head_sha("_agent_runs")
    assert sha is not None
    assert client.get_file_bytes("a.txt", "_agent_runs") == b"hi"


def test_put_file_preserves_prior_files(client):
    client.put_file_contents("a.txt", b"1", "msg", "br")
    client.put_file_contents("b.txt", b"2", "msg", "br")
    assert client.get_file_bytes("a.txt", "br") == b"1"
    assert client.get_file_bytes("b.txt", "br") == b"2"


def test_create_pull_request(client):
    client.create_branch("main")
    client.put_file_contents("x", b"y", "m", "feat")
    pr = client.create_pull_request(title="T", head="feat", base="main", body="body")
    # In-memory client's PR numbering starts at 5000 and increments by 1.
    assert pr["number"] == 5000
    assert pr["head"]["ref"] == "feat"
    assert pr["base"]["ref"] == "main"
    assert pr["state"] == "open"
    assert pr["merged"] is False

    # Subsequent create yields the next PR number exactly.
    client.put_file_contents("y", b"z", "m", "feat2")
    pr2 = client.create_pull_request(title="T2", head="feat2", base="main", body="b")
    assert pr2["number"] == 5001


def test_get_pull_request_returns_same_pr(client):
    client.create_branch("main")
    client.put_file_contents("x", b"y", "m", "feat")
    pr = client.create_pull_request(title="T", head="feat", base="main", body="b")
    again = client.get_pull_request(pr["number"])
    assert again["number"] == pr["number"]
    assert again["title"] == "T"


def test_merge_pull_request_marks_merged(client):
    client.create_branch("main")
    client.put_file_contents("x", b"y", "m", "feat")
    pr = client.create_pull_request(title="T", head="feat", base="main", body="b")
    merged = client.merge_pull_request(pr["number"])
    assert merged["merged"] is True
    assert merged["state"] == "closed"
    assert merged["merge_commit_sha"]


# ---------------------------------------------------------------------------
# delete_branch (iter 2 addition)
# ---------------------------------------------------------------------------

def test_delete_branch_existing(client):
    client.create_branch("victim")
    assert client.get_branch_head_sha("victim") is not None
    client.delete_branch("victim")
    assert client.get_branch_head_sha("victim") is None


def test_delete_branch_idempotent(client):
    """Deleting a missing branch is a silent no-op (matches GitHub semantics)."""
    # Never created — should not raise.
    client.delete_branch("nope")
    # Create + delete twice in a row — second call is also a no-op.
    client.create_branch("victim")
    client.delete_branch("victim")
    client.delete_branch("victim")
    assert client.get_branch_head_sha("victim") is None


def test_delete_branch_does_not_affect_others(client):
    client.create_branch("a")
    client.create_branch("b")
    client.delete_branch("a")
    assert client.get_branch_head_sha("a") is None
    assert client.get_branch_head_sha("b") is not None


# ---------------------------------------------------------------------------
# Iter 3: Section F — create_issue Protocol-compliant signature
# ---------------------------------------------------------------------------

def test_in_memory_create_issue_returns_dict_with_number():
    """``create_issue(title, body, labels=...)`` matches the protocol shape:
    title/body/labels round-trip; the new issue is fetchable via get_issue;
    if body has an agent-meta block, parse_agent_meta returns it."""
    import agent_protocol_common as common
    from tests.conftest import make_agent_meta

    c = common.InMemoryGitHubClient(default_user="jonathanmanton")
    meta = make_agent_meta(
        feature_branch="agent/42-x",
        instructions_inline="Investigate runner failure.",
    )
    body = common.render_agent_meta(meta, prose="Some prose here")
    out = c.create_issue(
        title="runner-failure: investigate",
        body=body,
        labels=["runner-failure", "agent-task"],
    )
    assert "number" in out and isinstance(out["number"], int)

    fetched = c.get_issue(out["number"])
    assert fetched["title"] == "runner-failure: investigate"
    assert fetched["body"] == body
    label_names = sorted(l["name"] for l in fetched["labels"])
    assert label_names == ["agent-task", "runner-failure"]
    # agent-meta round-trips.
    parsed = common.parse_agent_meta(fetched["body"])
    assert parsed is not None
    assert parsed["feature_branch"] == "agent/42-x"
    assert parsed["instructions_inline"] == "Investigate runner failure."


# ---------------------------------------------------------------------------
# In-memory client error paths (boosts common.py branch coverage)
# ---------------------------------------------------------------------------

def test_create_branch_duplicate_raises(client):
    client.create_branch("dup")
    with pytest.raises(ValueError):
        client.create_branch("dup")


def test_create_branch_unknown_source_raises(client):
    with pytest.raises(ValueError):
        client.create_branch("child", from_branch="not-a-branch")


def test_get_issue_missing_raises(client):
    with pytest.raises(KeyError):
        client.get_issue(99_999)


def test_update_issue_invalid_state_raises(client):
    issue = client.create_issue(title="t", body="b")
    with pytest.raises(ValueError):
        client.update_issue(issue["number"], state="not-a-real-state")


def test_update_issue_missing_raises(client):
    with pytest.raises(KeyError):
        client.update_issue(99_999, body="x")


def test_lock_issue_missing_raises(client):
    with pytest.raises(KeyError):
        client.lock_issue(99_999)


def test_add_label_missing_raises(client):
    with pytest.raises(KeyError):
        client.add_label(99_999, "agent-task")


def test_get_comment_missing_raises(client):
    with pytest.raises(KeyError):
        client.get_comment(404_404)


def test_update_comment_missing_raises(client):
    with pytest.raises(KeyError):
        client.update_comment(404_404, "x")


def test_add_comment_missing_issue_raises(client):
    with pytest.raises(KeyError):
        client.add_comment(99_999, "hello")


def test_delete_comment_missing_is_noop(client):
    """delete_comment swallows missing comments silently."""
    # Should not raise.
    client.delete_comment(404_404)


def test_create_pr_missing_head_raises(client):
    client.create_branch("main")
    with pytest.raises(ValueError):
        client.create_pull_request(title="t", head="ghost", base="main", body="b")


def test_create_pr_missing_base_raises(client):
    client.create_branch("feat")
    with pytest.raises(ValueError):
        client.create_pull_request(title="t", head="feat", base="ghost", body="b")


def test_get_pr_missing_raises(client):
    with pytest.raises(KeyError):
        client.get_pull_request(99_999)


def test_merge_pr_missing_raises(client):
    with pytest.raises(KeyError):
        client.merge_pull_request(99_999)


def test_get_file_contents_returns_b64_for_binary(client):
    """Non-utf-8 bytes get base64-encoded by get_file_contents (returned as ASCII)."""
    binary_blob = b"\xff\xfe\x00garbage\x80\x9d"
    client.put_file_contents("blob.bin", binary_blob, "msg", "br")
    out = client.get_file_contents("blob.bin", "br")
    # Must be a non-None string (b64-encoded) since the bytes are not valid utf-8.
    assert out is not None
    import base64 as _b64
    assert _b64.b64decode(out.encode("ascii")) == binary_blob


def test_get_file_contents_missing_path_returns_none(client):
    client.create_branch("br")
    assert client.get_file_contents("missing.txt", "br") is None


def test_get_file_bytes_missing_path_returns_none(client):
    client.create_branch("br")
    assert client.get_file_bytes("missing.txt", "br") is None
    # Missing branch also returns None.
    assert client.get_file_bytes("anything", "ghost-branch") is None
