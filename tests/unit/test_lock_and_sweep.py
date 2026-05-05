"""Tests for ``.agent/scripts/lock_and_sweep.py``."""

from __future__ import annotations

import lock_and_sweep
from tests.conftest import make_agent_meta

import agent_protocol_common as common


def _seed(client, *, user="jonathanmanton", with_meta=True, prose="P"):
    if with_meta:
        body = common.render_agent_meta(make_agent_meta(), prose=prose)
    else:
        body = "Just a regular human issue body, no meta."
    issue = client.create_issue(title="t", body=body, user=user)
    return issue


def test_labels_but_does_not_lock_when_meta_and_creator_is_agent(client, base_config):
    """The handler's own GITHUB_TOKEN cannot comment on locked issues,
    so lock-and-sweep applies the label only and defers locking until
    close_on_merge. See SPEC.md §3 (Real-world correction)."""
    issue = _seed(client, user=base_config["agent_login"])
    res = lock_and_sweep.run(
        client, issue["number"], config=base_config,
    )
    assert res["action"] == "labeled"
    fresh = client.get_issue(issue["number"])
    # CRITICAL: the issue must NOT be locked at this stage. Locking
    # earlier blocks the batch-job-handler's terminal envelope writes.
    assert fresh["locked"] is False
    labels = [l["name"] for l in fresh["labels"]]
    assert "agent-task" in labels


def test_lock_and_sweep_never_calls_lock_issue(client, base_config, monkeypatch):
    """Regression: lock_and_sweep must not invoke client.lock_issue.
    Locking moved to close_on_merge.py (post-merge tamper seal)."""
    issue = _seed(client, user=base_config["agent_login"])
    calls = []
    real_lock = client.lock_issue

    def _spy(n, *a, **kw):
        calls.append(n)
        return real_lock(n, *a, **kw)

    monkeypatch.setattr(client, "lock_issue", _spy)
    lock_and_sweep.run(client, issue["number"], config=base_config)
    assert calls == [], (
        "lock_and_sweep must not lock the issue; locking moved to "
        "close_on_merge.py to avoid blocking GITHUB_TOKEN comments"
    )


def test_noop_when_no_agent_meta(client, base_config):
    issue = _seed(client, user=base_config["agent_login"], with_meta=False)
    res = lock_and_sweep.run(
        client, issue["number"], config=base_config,
    )
    assert res["action"] == "noop"
    assert res["reason"] == "no_agent_meta"
    assert client.get_issue(issue["number"])["locked"] is False


def test_noop_when_creator_is_not_agent_login(client, base_config):
    issue = _seed(client, user="random-human")
    res = lock_and_sweep.run(
        client, issue["number"], config=base_config,
    )
    assert res["action"] == "noop"
    assert res["reason"] == "creator_not_agent_login"
    assert client.get_issue(issue["number"])["locked"] is False


def test_sweeps_non_agent_comments_pre_label(client, base_config):
    """Foreign comments that snuck in before the label was applied are
    swept. (Previously this was 'pre-lock' but we no longer lock at
    creation; the label + workflow author/label filter is the gate.)"""
    issue = _seed(client, user=base_config["agent_login"])
    n = issue["number"]
    # Add a "human" comment by switching actor.
    with client.as_user("intruder"):
        client.add_comment(n, "spam")
    with client.as_user("another-intruder"):
        client.add_comment(n, "more spam")
    # Add an agent comment too.
    with client.as_user(base_config["agent_login"]):
        client.add_comment(n, "agent note")

    res = lock_and_sweep.run(
        client, issue["number"], config=base_config,
    )
    assert res["action"] == "labeled"
    assert res["deleted_comments"] == 2
    assert res["kept_agent_comments"] == 1
    bodies = [c["body"] for c in client.list_comments(n)]
    assert bodies == ["agent note"]


def test_preserves_agent_authored_comments(client, base_config):
    issue = _seed(client, user=base_config["agent_login"])
    n = issue["number"]
    with client.as_user(base_config["agent_login"]):
        client.add_comment(n, "agent-1")
        client.add_comment(n, "agent-2")
    lock_and_sweep.run(client, n, config=base_config)
    bodies = sorted(c["body"] for c in client.list_comments(n))
    assert bodies == ["agent-1", "agent-2"]
