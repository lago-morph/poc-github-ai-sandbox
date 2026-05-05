"""Tests for ``.agent/scripts/close_on_merge.py``."""

from __future__ import annotations

import close_on_merge
from tests.conftest import make_agent_meta

import agent_protocol_common as common


def _make_finished_issue(client, status="finished"):
    meta = make_agent_meta(status=status, status_ts=common.iso_now())
    body = common.render_agent_meta(meta, prose="x")
    issue = client.create_issue(title="t", body=body, user="jonathanmanton",
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
    fresh = client.get_issue(issue["number"])
    assert fresh["state"] == "closed"
    # close_on_merge now also locks the issue post-close as the audit
    # tamper-prevention seal (lock at close, not at creation — see SPEC §3).
    assert fresh["locked"] is True


def test_locks_issue_after_close(client, base_config, monkeypatch):
    """Regression: close_on_merge must call lock_issue after closing."""
    issue = _make_finished_issue(client)
    pr = _make_merged_pr(client, body=f"Closes #{issue['number']}")

    locked_calls = []
    real_lock = client.lock_issue

    def _spy(n, *a, **kw):
        locked_calls.append(n)
        return real_lock(n, *a, **kw)

    monkeypatch.setattr(client, "lock_issue", _spy)
    close_on_merge.run(client, pr["number"], config=base_config)
    assert issue["number"] in locked_calls


def test_does_not_double_lock_already_locked_issue(client, base_config, monkeypatch):
    """If the issue is already locked, close_on_merge should not call
    lock_issue again (idempotent)."""
    issue = _make_finished_issue(client)
    client.lock_issue(issue["number"])
    pr = _make_merged_pr(client, body=f"Closes #{issue['number']}")

    locked_calls = []
    real_lock = client.lock_issue

    def _spy(n, *a, **kw):
        locked_calls.append(n)
        return real_lock(n, *a, **kw)

    monkeypatch.setattr(client, "lock_issue", _spy)
    close_on_merge.run(client, pr["number"], config=base_config)
    assert locked_calls == []


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


def test_noop_when_no_closes_refs(client, base_config):
    pr = _make_merged_pr(client, body="A merge with no Closes #N references.")
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "noop"
    assert res["reason"] == "no_closes_refs"


def test_skipped_when_issue_missing(client, base_config):
    """Closes #N where N doesn't exist → skipped with reason=missing."""
    pr = _make_merged_pr(client, body="Closes #99999")
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "closed"
    assert any(s["reason"] == "missing" for s in res["skipped"])


def test_skipped_when_issue_has_no_agent_meta(client, base_config):
    """Closes #N for an issue with no agent-meta → skipped with no_agent_meta."""
    issue = client.create_issue(title="plain", body="Just text, no meta block.",
                                 user="jonathanmanton")
    pr = _make_merged_pr(client, body=f"Closes #{issue['number']}")
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "closed"
    assert any(
        s["issue"] == issue["number"] and s["reason"] == "no_agent_meta"
        for s in res["skipped"]
    )


def test_parse_closes_refs_finds_multiple_aliases():
    refs = close_on_merge.parse_closes_refs(
        "Fixes #1\nResolved #2\nclose #3 and CLOSES #4 also."
    )
    assert sorted(refs) == [1, 2, 3, 4]


def test_parse_closes_refs_returns_empty_for_none():
    assert close_on_merge.parse_closes_refs(None) == []
    assert close_on_merge.parse_closes_refs("") == []


# ---------------------------------------------------------------------------
# Branch auto-deletion on merge
# ---------------------------------------------------------------------------

def test_close_on_merge_deletes_feature_branch(client, base_config):
    """A merged PR whose head is ``agent/<feature>`` has the head branch
    deleted after the issue is closed."""
    issue = _make_finished_issue(client)
    pr = _make_merged_pr(
        client,
        body=f"Closes #{issue['number']}",
        head="agent/harness-01-foo",
    )
    assert "agent/harness-01-foo" in client._branches
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "closed"
    assert "agent/harness-01-foo" in res["deleted_branches"]
    assert "agent/harness-01-foo" not in client._branches


def test_close_on_merge_deletes_subagent_branches(client, base_config):
    """Merging a feature also sweeps any ``<feature>--sub-*`` siblings."""
    issue = _make_finished_issue(client)
    pr = _make_merged_pr(
        client,
        body=f"Closes #{issue['number']}",
        head="agent/harness-01-foo",
    )
    # Seed two subagent branches.
    client.put_file_contents("a", b"a", "alpha", "agent/harness-01-foo--sub-alpha")
    client.put_file_contents("b", b"b", "beta", "agent/harness-01-foo--sub-beta")
    assert "agent/harness-01-foo--sub-alpha" in client._branches
    assert "agent/harness-01-foo--sub-beta" in client._branches

    res = close_on_merge.run(client, pr["number"], config=base_config)
    deleted = set(res["deleted_branches"])
    assert "agent/harness-01-foo" in deleted
    assert "agent/harness-01-foo--sub-alpha" in deleted
    assert "agent/harness-01-foo--sub-beta" in deleted
    assert len(deleted) == 3
    for name in (
        "agent/harness-01-foo",
        "agent/harness-01-foo--sub-alpha",
        "agent/harness-01-foo--sub-beta",
    ):
        assert name not in client._branches


def test_close_on_merge_does_not_delete_main(client, base_config):
    """``main`` must never be deleted, even if it somehow appears as a head ref."""
    issue = _make_finished_issue(client)
    # Construct a PR whose head is ``main``. We use the in-memory client
    # directly because _make_merged_pr would attempt to put a file on
    # ``main`` (still fine, but we want explicit clarity).
    if "main" not in client._branches:
        client.create_branch("main")
    pr = client.create_pull_request(
        title="T", head="main", base="main",
        body=f"Closes #{issue['number']}",
    )
    client.merge_pull_request(pr["number"])
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert "main" not in res["deleted_branches"]
    assert "main" in client._branches


def test_close_on_merge_does_not_delete_agent_runs(client, base_config):
    """``_agent_runs`` (orphan audit branch) must be preserved."""
    issue = _make_finished_issue(client)
    # Seed _agent_runs.
    client.put_file_contents("manifest.json", b"{}", "init", "_agent_runs")
    pr = _make_merged_pr(
        client,
        body=f"Closes #{issue['number']}",
        head="agent/harness-01-foo",
    )
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert "_agent_runs" not in res["deleted_branches"]
    assert "_agent_runs" in client._branches


def test_close_on_merge_does_not_delete_non_agent_branches(client, base_config):
    """Branches outside the ``agent/`` namespace are left untouched even
    if they otherwise look like sub-* siblings of the feature branch."""
    issue = _make_finished_issue(client)
    # PR head is a non-agent branch (defensive: shouldn't happen, but we
    # must never delete it).
    pr = _make_merged_pr(
        client,
        body=f"Closes #{issue['number']}",
        head="feature/foo",
    )
    # Also seed an unrelated non-agent branch that happens to share a prefix.
    client.put_file_contents("z", b"z", "z", "feature/foo--sub-alpha")

    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["deleted_branches"] == []
    assert "feature/foo" in client._branches
    assert "feature/foo--sub-alpha" in client._branches


def test_close_on_merge_tolerates_missing_branch(client, base_config, monkeypatch):
    """``delete_branch`` raising (e.g. branch already gone) must not fail
    the workflow; close_on_merge swallows the error and moves on."""
    issue = _make_finished_issue(client)
    pr = _make_merged_pr(
        client,
        body=f"Closes #{issue['number']}",
        head="agent/harness-01-foo",
    )

    def _raise(name):
        raise RuntimeError(f"boom: {name}")

    monkeypatch.setattr(client, "delete_branch", _raise)

    # Should not raise.
    res = close_on_merge.run(client, pr["number"], config=base_config)
    # Issue still got closed, branch deletion is best-effort.
    assert res["action"] == "closed"
    assert res["deleted_branches"] == []
