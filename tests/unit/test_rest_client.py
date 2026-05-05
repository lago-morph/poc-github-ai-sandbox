"""Unit tests for :class:`RestGitHubClient`.

All HTTP traffic is mocked with the :mod:`responses` library so the
tests never touch the network. Coverage focuses on:

- Basic CRUD: issues, comments, labels, lock.
- The orphan-branch creation flow used for ``_agent_runs`` (blob ->
  tree -> commit -> ref) and the follow-up commit flow that includes
  ``base_tree`` and a parent.
- Retry behaviour on 5xx.
- 404 returning ``None`` for ``get_branch_head_sha`` and
  ``get_file_contents``.
"""

from __future__ import annotations

import base64
import json

import pytest
import responses
from responses import matchers

from rest_client import RestGitHubClient


OWNER = "owner"
REPO = "repo"
BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"


@pytest.fixture
def client():
    return RestGitHubClient(
        token="t0k3n", owner=OWNER, repo=REPO, sleep=lambda _s: None
    )


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------

@responses.activate
def test_get_issue(client):
    responses.add(
        responses.GET,
        f"{BASE}/issues/42",
        json={"number": 42, "title": "x", "body": "b"},
        status=200,
    )
    issue = client.get_issue(42)
    assert issue["number"] == 42
    # Authorization header is sent.
    assert responses.calls[0].request.headers["Authorization"] == "Bearer t0k3n"
    assert responses.calls[0].request.headers["X-GitHub-Api-Version"] == "2022-11-28"


@responses.activate
def test_update_issue_sends_only_provided_fields(client):
    responses.add(
        responses.PATCH,
        f"{BASE}/issues/42",
        json={"number": 42, "state": "closed"},
        status=200,
        match=[matchers.json_params_matcher({"state": "closed"})],
    )
    out = client.update_issue(42, state="closed")
    assert out["state"] == "closed"


@responses.activate
def test_lock_issue_puts_to_lock_endpoint(client):
    responses.add(
        responses.PUT,
        f"{BASE}/issues/42/lock",
        status=204,
    )
    client.lock_issue(42)
    assert responses.calls[0].request.url.endswith("/issues/42/lock")


@responses.activate
def test_add_label(client):
    responses.add(
        responses.POST,
        f"{BASE}/issues/42/labels",
        json=[{"name": "agent-task"}],
        status=200,
        match=[matchers.json_params_matcher({"labels": ["agent-task"]})],
    )
    client.add_label(42, "agent-task")


@responses.activate
def test_add_comment(client):
    responses.add(
        responses.POST,
        f"{BASE}/issues/42/comments",
        json={"id": 9, "body": "hi"},
        status=201,
        match=[matchers.json_params_matcher({"body": "hi"})],
    )
    out = client.add_comment(42, "hi")
    assert out["id"] == 9


@responses.activate
def test_update_comment(client):
    responses.add(
        responses.PATCH,
        f"{BASE}/issues/comments/9",
        json={"id": 9, "body": "new"},
        status=200,
        match=[matchers.json_params_matcher({"body": "new"})],
    )
    out = client.update_comment(9, "new")
    assert out["body"] == "new"


@responses.activate
def test_get_comment(client):
    responses.add(
        responses.GET,
        f"{BASE}/issues/comments/9",
        json={"id": 9, "body": "hi"},
        status=200,
    )
    out = client.get_comment(9)
    assert out["id"] == 9


@responses.activate
def test_list_comments_paginates(client):
    page1 = [{"id": 1}, {"id": 2}]
    page2 = [{"id": 3}]
    responses.add(
        responses.GET,
        f"{BASE}/issues/42/comments",
        json=page1,
        status=200,
        headers={
            "Link": f'<{BASE}/issues/42/comments?page=2>; rel="next", '
                    f'<{BASE}/issues/42/comments?page=2>; rel="last"'
        },
    )
    responses.add(
        responses.GET,
        f"{BASE}/issues/42/comments",
        json=page2,
        status=200,
    )
    out = client.list_comments(42)
    assert [c["id"] for c in out] == [1, 2, 3]


@responses.activate
def test_delete_comment(client):
    responses.add(
        responses.DELETE,
        f"{BASE}/issues/comments/9",
        status=204,
    )
    client.delete_comment(9)


@responses.activate
def test_create_issue(client):
    responses.add(
        responses.POST,
        f"{BASE}/issues",
        json={"number": 100, "title": "t", "body": "b"},
        status=201,
        match=[matchers.json_params_matcher({"title": "t", "body": "b", "labels": ["L"]})],
    )
    out = client.create_issue("t", "b", labels=["L"])
    assert out["number"] == 100


# ---------------------------------------------------------------------------
# get_file_contents
# ---------------------------------------------------------------------------

@responses.activate
def test_get_file_contents_returns_utf8(client):
    encoded = base64.b64encode(b"hello world").decode("ascii")
    responses.add(
        responses.GET,
        f"{BASE}/contents/path/to/file.txt",
        json={"encoding": "base64", "content": encoded},
        status=200,
    )
    assert client.get_file_contents("path/to/file.txt", "main") == "hello world"


@responses.activate
def test_get_file_contents_404_returns_none(client):
    responses.add(
        responses.GET,
        f"{BASE}/contents/nope.txt",
        status=404,
        json={"message": "Not Found"},
    )
    assert client.get_file_contents("nope.txt", "main") is None


# ---------------------------------------------------------------------------
# get_branch_head_sha
# ---------------------------------------------------------------------------

@responses.activate
def test_get_branch_head_sha_existing(client):
    responses.add(
        responses.GET,
        f"{BASE}/git/refs/heads/main",
        json={"ref": "refs/heads/main", "object": {"sha": "abc123"}},
        status=200,
    )
    assert client.get_branch_head_sha("main") == "abc123"


@responses.activate
def test_get_branch_head_sha_404_returns_none(client):
    responses.add(
        responses.GET,
        f"{BASE}/git/refs/heads/_agent_runs",
        status=404,
        json={"message": "Not Found"},
    )
    assert client.get_branch_head_sha("_agent_runs") is None


# ---------------------------------------------------------------------------
# Orphan branch flow
# ---------------------------------------------------------------------------

@responses.activate
def test_put_file_contents_creates_orphan_branch(client):
    # 1. Branch lookup -> 404 (orphan).
    responses.add(
        responses.GET,
        f"{BASE}/git/refs/heads/_agent_runs",
        status=404,
        json={"message": "Not Found"},
    )
    # 2. Create blob.
    responses.add(
        responses.POST,
        f"{BASE}/git/blobs",
        json={"sha": "blobsha"},
        status=201,
        match=[matchers.json_params_matcher({
            "content": base64.b64encode(b"hello").decode("ascii"),
            "encoding": "base64",
        })],
    )
    # 3. Create tree (no base_tree on orphan).
    responses.add(
        responses.POST,
        f"{BASE}/git/trees",
        json={"sha": "treesha"},
        status=201,
        match=[matchers.json_params_matcher({
            "tree": [
                {"path": "runs/1/2/manifest.json", "mode": "100644",
                 "type": "blob", "sha": "blobsha"}
            ],
        })],
    )
    # 4. Create commit with empty parents (orphan).
    responses.add(
        responses.POST,
        f"{BASE}/git/commits",
        json={"sha": "commitsha"},
        status=201,
        match=[matchers.json_params_matcher({
            "message": "msg",
            "tree": "treesha",
            "parents": [],
        })],
    )
    # 5. Create ref.
    responses.add(
        responses.POST,
        f"{BASE}/git/refs",
        json={"ref": "refs/heads/_agent_runs", "object": {"sha": "commitsha"}},
        status=201,
        match=[matchers.json_params_matcher({
            "ref": "refs/heads/_agent_runs",
            "sha": "commitsha",
        })],
    )

    out = client.put_file_contents(
        "runs/1/2/manifest.json", b"hello", "msg", "_agent_runs"
    )
    assert out["branch"] == "_agent_runs"
    assert out["commit"]["sha"] == "commitsha"
    assert out["size"] == 5
    # Verify we hit all five endpoints.
    assert len(responses.calls) == 5


@responses.activate
def test_put_file_contents_appends_to_existing_branch(client):
    # 1. Branch lookup -> existing.
    responses.add(
        responses.GET,
        f"{BASE}/git/refs/heads/_agent_runs",
        json={"ref": "refs/heads/_agent_runs", "object": {"sha": "parentsha"}},
        status=200,
    )
    # 2. Get parent commit -> tree.
    responses.add(
        responses.GET,
        f"{BASE}/git/commits/parentsha",
        json={"sha": "parentsha", "tree": {"sha": "parenttreesha"}},
        status=200,
    )
    # 3. Create blob.
    responses.add(
        responses.POST,
        f"{BASE}/git/blobs",
        json={"sha": "blob2"},
        status=201,
    )
    # 4. Create tree with base_tree.
    responses.add(
        responses.POST,
        f"{BASE}/git/trees",
        json={"sha": "tree2"},
        status=201,
        match=[matchers.json_params_matcher({
            "base_tree": "parenttreesha",
            "tree": [
                {"path": "runs/1/2/summary.json", "mode": "100644",
                 "type": "blob", "sha": "blob2"}
            ],
        })],
    )
    # 5. Create commit with parent.
    responses.add(
        responses.POST,
        f"{BASE}/git/commits",
        json={"sha": "commit2"},
        status=201,
        match=[matchers.json_params_matcher({
            "message": "msg2",
            "tree": "tree2",
            "parents": ["parentsha"],
        })],
    )
    # 6. PATCH ref.
    responses.add(
        responses.PATCH,
        f"{BASE}/git/refs/heads/_agent_runs",
        json={"ref": "refs/heads/_agent_runs", "object": {"sha": "commit2"}},
        status=200,
        match=[matchers.json_params_matcher({"sha": "commit2"})],
    )

    out = client.put_file_contents(
        "runs/1/2/summary.json", b"{}", "msg2", "_agent_runs"
    )
    assert out["commit"]["sha"] == "commit2"
    assert len(responses.calls) == 6


# ---------------------------------------------------------------------------
# Retry behaviour
# ---------------------------------------------------------------------------

@responses.activate
def test_get_issue_retries_on_5xx(client):
    responses.add(
        responses.GET,
        f"{BASE}/issues/42",
        status=503,
        json={"message": "Service Unavailable"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/issues/42",
        json={"number": 42},
        status=200,
    )
    out = client.get_issue(42)
    assert out["number"] == 42
    assert len(responses.calls) == 2


@responses.activate
def test_does_not_retry_on_422(client):
    responses.add(
        responses.PATCH,
        f"{BASE}/issues/42",
        json={"message": "Validation Failed"},
        status=422,
    )
    with pytest.raises(Exception):
        client.update_issue(42, state="bogus")
    assert len(responses.calls) == 1


@responses.activate
def test_rate_limited_403_retries_and_succeeds(client):
    responses.add(
        responses.GET,
        f"{BASE}/issues/42",
        status=403,
        json={"message": "API rate limit exceeded"},
        headers={"X-RateLimit-Remaining": "0", "Retry-After": "0"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/issues/42",
        json={"number": 42},
        status=200,
    )
    out = client.get_issue(42)
    assert out["number"] == 42
    assert len(responses.calls) == 2


# ---------------------------------------------------------------------------
# Branch deletion + PR endpoints
# ---------------------------------------------------------------------------

@responses.activate
def test_delete_branch_idempotent_on_404(client):
    responses.add(
        responses.DELETE,
        f"{BASE}/git/refs/heads/missing",
        status=404,
        json={"message": "Not Found"},
    )
    # Should NOT raise.
    client.delete_branch("missing")


@responses.activate
def test_create_pull_request(client):
    responses.add(
        responses.POST,
        f"{BASE}/pulls",
        json={"number": 5001, "head": {"ref": "h"}, "base": {"ref": "b"}},
        status=201,
        match=[matchers.json_params_matcher({
            "title": "T", "head": "h", "base": "b", "body": "B"
        })],
    )
    out = client.create_pull_request("T", "h", "b", "B")
    assert out["number"] == 5001


@responses.activate
def test_get_pull_request(client):
    responses.add(
        responses.GET,
        f"{BASE}/pulls/5001",
        json={"number": 5001, "merged": True},
        status=200,
    )
    assert client.get_pull_request(5001)["merged"] is True


# ---------------------------------------------------------------------------
# Misc: client honours protocol
# ---------------------------------------------------------------------------

def test_satisfies_protocol():
    """RestGitHubClient is structurally compatible with GitHubClient."""
    from common import GitHubClient
    c = RestGitHubClient(token="x", owner="o", repo="r", sleep=lambda _s: None)
    assert isinstance(c, GitHubClient)


def test_constructor_validates_inputs():
    with pytest.raises(ValueError):
        RestGitHubClient(token="", owner="o", repo="r")
    with pytest.raises(ValueError):
        RestGitHubClient(token="t", owner="", repo="r")
    with pytest.raises(ValueError):
        RestGitHubClient(token="t", owner="o", repo="")
