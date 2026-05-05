"""Tests for ``.agent/scripts/lock_and_sweep.py``."""

from __future__ import annotations

import lock_and_sweep
from tests.conftest import make_agent_meta

import agent_protocol_common as common


def _seed(client, *, user="my-bot", with_meta=True, prose="P"):
    if with_meta:
        body = common.render_agent_meta(make_agent_meta(), prose=prose)
    else:
        body = "Just a regular human issue body, no meta."
    issue = client.create_issue(title="t", body=body, user=user)
    return issue


def test_locks_and_labels_when_meta_and_creator_is_agent(client, base_config):
    issue = _seed(client, user=base_config["agent_login"])
    res = lock_and_sweep.run(
        client, issue["number"], config=base_config,
    )
    assert res["action"] == "locked"
    fresh = client.get_issue(issue["number"])
    assert fresh["locked"] is True
    labels = [l["name"] for l in fresh["labels"]]
    assert "agent-task" in labels


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


def test_sweeps_non_agent_comments_pre_lock(client, base_config):
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
    assert res["action"] == "locked"
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
