"""Tests for ``.agent/scripts/close_on_merge.py``."""

from __future__ import annotations

import close_on_merge
from tests.conftest import make_agent_meta

import agent_protocol_common as common


def _make_finished_issue(client, status="finished"):
    meta = make_agent_meta(status=status, status_ts=common.iso_now())
    body = common.render_agent_meta(meta, prose="x")
    issue = client.create_issue(title="t", body=body, user="my-bot",
                                labels=["agent-task"])
    return issue


def _make_merged_pr(client, body, base="main", head="feat"):
    if base not in client._branches:
        client.create_branch(base)
    if head not in client._branches:
        client.put_file_contents("x", b"y", "msg", head)
    pr = client.create_pull_request(title="T", head=head, base=base, body=body)
    return client.merge_pull_request(pr["number"])


def test_closes_finished_issue_when_pr_body_has_closes_n(client, base_config):
    issue = _make_finished_issue(client)
    pr = _make_merged_pr(client, body=f"Description.\n\nCloses #{issue['number']}")
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "closed"
    assert issue["number"] in res["issues_closed"]
    assert client.get_issue(issue["number"])["state"] == "closed"


def test_noop_when_issue_not_finished(client, base_config):
    issue = _make_finished_issue(client, status="working")
    pr = _make_merged_pr(client, body=f"Closes #{issue['number']}")
    res = close_on_merge.run(client, pr["number"], config=base_config)
    # action is "closed" with skipped, but the issue is not actually closed.
    assert client.get_issue(issue["number"])["state"] == "open"
    assert any(s["reason"] == "not_finished" for s in res.get("skipped", []))


def test_noop_when_pr_not_merged(client, base_config):
    issue = _make_finished_issue(client)
    if "main" not in client._branches:
        client.create_branch("main")
    if "feat" not in client._branches:
        client.put_file_contents("x", b"y", "msg", "feat")
    pr = client.create_pull_request(
        title="T", head="feat", base="main",
        body=f"Closes #{issue['number']}",
    )
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "noop"
    assert res["reason"] == "pr_not_merged"
    assert client.get_issue(issue["number"])["state"] == "open"
