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
