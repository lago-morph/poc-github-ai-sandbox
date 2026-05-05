"""Tests for the ``task-dag`` skill (claim, plan, merge, schedule)."""

from __future__ import annotations

import importlib.util as _ilu
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, file_name: str):
    full = f"skills_taskdag_{name}"
    if full in sys.modules:
        return sys.modules[full]
    path = REPO_ROOT / "skills" / "task-dag" / file_name
    spec = _ilu.spec_from_file_location(full, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


claim_mod = _load("claim", "claim.py")
plan_mod = _load("plan", "plan.py")
merge_mod = _load("merge", "merge.py")
sched_mod = _load("schedule_successors", "schedule_successors.py")

import agent_protocol_common as common
from tests.conftest import make_agent_meta


def _seed_unclaimed(client, *, status=None, agent_id=None, status_ts=None,
                     instructions_inline="Do work.",
                     instructions_path=None,
                     base_branch="main",
                     feature_branch="agent/1-x",
                     extra_label=True):
    meta = make_agent_meta(
        feature_branch=feature_branch, base_branch=base_branch,
        status=status, agent_id=agent_id, status_ts=status_ts,
        instructions_inline=instructions_inline,
        instructions_path=instructions_path,
    )
    body = common.render_agent_meta(meta, prose="P")
    labels = ["agent-task"] if extra_label else []
    issue = client.create_issue(title="t", body=body, user="my-bot",
                                labels=labels)
    client.lock_issue(issue["number"])
    return client.get_issue(issue["number"]), meta


# ---------------------------------------------------------------------------
# claim
# ---------------------------------------------------------------------------

def test_claim_picks_null_issue(client, base_config):
    issue, _ = _seed_unclaimed(client)
    res = claim_mod.claim(
        client, agent_id="A1",
        candidate_issues=[issue], config=base_config,
    )
    assert res is not None
    assert res["agent_id"] == "A1"
    fresh_meta = common.parse_agent_meta(client.get_issue(issue["number"])["body"])
    assert fresh_meta["agent_id"] == "A1"
    assert fresh_meta["status"] == "working"


def test_claim_returns_none_when_no_candidates(client, base_config):
    issue, _ = _seed_unclaimed(client, status="working", agent_id="X",
                                status_ts=common.iso_now())
    res = claim_mod.claim(
        client, agent_id="A1",
        candidate_issues=[issue], config=base_config,
    )
    assert res is None


def test_claim_takes_over_stale_issue(client, base_config):
    old_ts = (datetime.now(tz=timezone.utc) - timedelta(seconds=10_000)) \
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    issue, _ = _seed_unclaimed(client, status="working",
                                 agent_id="OLD", status_ts=old_ts)
    res = claim_mod.claim(
        client, agent_id="NEW",
        candidate_issues=[issue], config=base_config,
    )
    assert res is not None
    assert res["agent_id"] == "NEW"


def test_claim_loser_self_abandons_when_meta_changed(client, base_config, monkeypatch):
    issue, _ = _seed_unclaimed(client)

    # The verify-fetch is the only call to client.get_issue with this number
    # in the claim() flow when candidate_issues is supplied.
    real_get_issue = client.get_issue

    def faked(n):
        result = real_get_issue(n)
        meta = common.parse_agent_meta(result["body"]) or {}
        meta["agent_id"] = "OTHER"  # someone else wrote here between
        new_body = common.render_agent_meta(meta, prose="")
        return {**result, "body": new_body}

    monkeypatch.setattr(client, "get_issue", faked)
    res = claim_mod.claim(
        client, agent_id="ME",
        candidate_issues=[issue], config=base_config,
    )
    assert res is None


# ---------------------------------------------------------------------------
# heartbeat
# ---------------------------------------------------------------------------

def test_heartbeat_updates_status_ts(client, base_config):
    issue, _ = _seed_unclaimed(client, status="working", agent_id="A",
                                 status_ts=common.iso_now())
    pre = common.parse_agent_meta(client.get_issue(issue["number"])["body"])
    ok = claim_mod.heartbeat(client, issue_number=issue["number"], agent_id="A")
    assert ok
    post = common.parse_agent_meta(client.get_issue(issue["number"])["body"])
    assert post["status_ts"] is not None


def test_heartbeat_self_abandons_on_displacement(client, base_config):
    issue, _ = _seed_unclaimed(client, status="working", agent_id="A",
                                 status_ts=common.iso_now())
    ok = claim_mod.heartbeat(client, issue_number=issue["number"], agent_id="DIFFERENT")
    assert ok is False


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------

def test_plan_reads_inline_instructions(client, base_config):
    issue, _ = _seed_unclaimed(client, instructions_inline="Inline brief here.")
    out = plan_mod.plan(client, issue_number=issue["number"])
    assert out["brief"] == "Inline brief here."
    assert out["source"] == "inline"


def test_plan_reads_instructions_path_from_base(client, base_config):
    if "main" not in client._branches:
        client.create_branch("main")
    client.put_file_contents("docs/brief.md", b"# Plan\nDo stuff.", "msg", "main")
    issue, _ = _seed_unclaimed(
        client,
        instructions_inline=None,
        instructions_path="docs/brief.md",
    )
    out = plan_mod.plan(client, issue_number=issue["number"])
    assert "Do stuff" in out["brief"]
    assert out["source"] == "path"


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

def test_merge_consolidates_subagent_branches(client, base_config):
    client.create_branch("main")
    client.put_file_contents("README", b"main", "init", "agent/1-x")
    feat = "agent/1-x"
    sub_a = "agent/1-x/sub-alpha"
    sub_b = "agent/1-x/sub-beta"
    client.create_branch(sub_a, from_branch=feat)
    client.commit_files(sub_a, {"a.txt": b"a-content"}, "alpha work")
    client.create_branch(sub_b, from_branch=feat)
    client.commit_files(sub_b, {"b.txt": b"b-content"}, "beta work")

    res = merge_mod.merge_subagent_branches(
        client, feature_branch=feat, subagent_branches=[sub_a, sub_b],
    )
    assert len(res["merged"]) == 2
    # both files now appear on the feature branch
    assert client.get_file_bytes("a.txt", feat) == b"a-content"
    assert client.get_file_bytes("b.txt", feat) == b"b-content"


def _seed_two_subagent_branches(client):
    client.create_branch("main")
    client.put_file_contents("README", b"main", "init", "agent/1-x")
    feat = "agent/1-x"
    sub_a = "agent/1-x/sub-alpha"
    sub_b = "agent/1-x/sub-beta"
    client.create_branch(sub_a, from_branch=feat)
    client.commit_files(sub_a, {"a.txt": b"a-content"}, "alpha work")
    client.create_branch(sub_b, from_branch=feat)
    client.commit_files(sub_b, {"b.txt": b"b-content"}, "beta work")
    return feat, sub_a, sub_b


def test_merge_deletes_subagent_branches_by_default(client, base_config):
    """Iter 2: merge.py deletes subagent branches after merge by default."""
    feat, sub_a, sub_b = _seed_two_subagent_branches(client)
    res = merge_mod.merge_subagent_branches(
        client, feature_branch=feat, subagent_branches=[sub_a, sub_b],
    )
    assert sorted(res["deleted"]) == sorted([sub_a, sub_b])
    assert client.get_branch_head_sha(sub_a) is None
    assert client.get_branch_head_sha(sub_b) is None
    # Feature branch is still present and carries both files.
    assert client.get_branch_head_sha(feat) is not None
    assert client.get_file_bytes("a.txt", feat) == b"a-content"
    assert client.get_file_bytes("b.txt", feat) == b"b-content"


def test_merge_keeps_subagent_branches_when_disabled(client, base_config):
    """``delete_branches=False`` leaves subagent refs intact."""
    feat, sub_a, sub_b = _seed_two_subagent_branches(client)
    res = merge_mod.merge_subagent_branches(
        client, feature_branch=feat, subagent_branches=[sub_a, sub_b],
        delete_branches=False,
    )
    assert res["deleted"] == []
    assert client.get_branch_head_sha(sub_a) is not None
    assert client.get_branch_head_sha(sub_b) is not None


def test_merge_skipped_branch_not_deleted(client, base_config):
    """Skipped (missing) subagent branches are not added to deleted list."""
    client.create_branch("main")
    client.put_file_contents("README", b"main", "init", "agent/1-x")
    feat = "agent/1-x"
    sub_a = "agent/1-x/sub-alpha"
    client.create_branch(sub_a, from_branch=feat)
    client.commit_files(sub_a, {"a.txt": b"a-content"}, "alpha work")
    missing = "agent/1-x/sub-ghost"

    res = merge_mod.merge_subagent_branches(
        client, feature_branch=feat, subagent_branches=[sub_a, missing],
    )
    assert sub_a in res["deleted"]
    assert missing not in res["deleted"]
    assert any(s["branch"] == missing for s in res["skipped"])


# ---------------------------------------------------------------------------
# Working -> abandoned transitions (Section E)
# ---------------------------------------------------------------------------

def test_abandon_when_displaced(client, base_config):
    """Heartbeat detects a different agent_id and reports loss-of-ownership.

    The current heartbeat impl returns False on displacement (does NOT itself
    write status="abandoned"); this documents that boundary. The status_ts
    is left untouched (stale) so a downstream sweeper can mark abandoned.
    """
    issue, _ = _seed_unclaimed(client, status="working", agent_id="OWNER",
                                 status_ts=common.iso_now())
    n = issue["number"]

    # A second agent overrides the agent_id on the issue (lost-the-race)
    meta_now = common.parse_agent_meta(client.get_issue(n)["body"])
    pre_status_ts = meta_now["status_ts"]
    meta_now["agent_id"] = "DISPLACER"
    client.update_issue(n, body=common.render_agent_meta(meta_now, prose="P"))

    ok = claim_mod.heartbeat(client, issue_number=n, agent_id="OWNER")
    assert ok is False  # OWNER no longer holds the issue

    fresh_meta = common.parse_agent_meta(client.get_issue(n)["body"])
    # Heartbeat must NOT have touched status_ts when it doesn't own the issue.
    assert fresh_meta["status_ts"] == pre_status_ts
    # ...and the displacer's agent_id is preserved.
    assert fresh_meta["agent_id"] == "DISPLACER"


def test_abandon_on_failed_dependency_documented_gap(client, base_config):
    """task-dag does not currently expose a 'decline on failed dep' API.

    Documenting the gap: ``plan`` reads ``depends_on_prs`` but doesn't yet
    have a hook that aborts the claim if a listed PR is unmerged/closed.
    Iter 3 may add :func:`task_dag.decline_if_dependency_failed`.
    """
    issue, _ = _seed_unclaimed(
        client, instructions_inline="Do step C",
    )
    # Mutate meta to add a depends_on_prs reference.
    meta = common.parse_agent_meta(client.get_issue(issue["number"])["body"])
    meta["depends_on_prs"] = [9999]  # dangling reference
    client.update_issue(
        issue["number"],
        body=common.render_agent_meta(meta, prose="P"),
    )

    out = plan_mod.plan(client, issue_number=issue["number"])
    assert out["depends_on_prs"] == [9999]
    # No decline path exists today; the test documents that plan returns
    # the brief regardless of dependency state.
    assert out["brief"] == "Do step C"


# ---------------------------------------------------------------------------
# Merge conflict (Section F)
# ---------------------------------------------------------------------------

def test_merge_conflict_two_branches_modify_same_file(client, base_config):
    """Two subagent branches modify the same file. Pin to last-writer-wins.

    The in-memory POC merge applies file-overlays in subagent_branches list
    order (sorted, then iterated). The last branch to overlay wins for any
    overlapping path. This documents the actual implementation choice.
    """
    client.create_branch("main")
    client.put_file_contents("shared.txt", b"base", "init", "agent/1-x")
    feat = "agent/1-x"

    sub_a = "agent/1-x/sub-alpha"
    sub_b = "agent/1-x/sub-beta"
    client.create_branch(sub_a, from_branch=feat)
    client.commit_files(sub_a, {"shared.txt": b"alpha-version"}, "alpha")
    client.create_branch(sub_b, from_branch=feat)
    client.commit_files(sub_b, {"shared.txt": b"beta-version"}, "beta")

    # Note: sub_a < sub_b lexically, so sub_b is applied after sub_a.
    res = merge_mod.merge_subagent_branches(
        client, feature_branch=feat, subagent_branches=[sub_a, sub_b],
    )
    assert len(res["merged"]) == 2
    # Last-writer-wins semantic: sub_b wins (overlay applied last).
    assert client.get_file_bytes("shared.txt", feat) == b"beta-version"

    # Reverse order: sub_a wins.
    client2 = client  # alias for clarity; we'll re-seed instead
    # Reset feat to a known pre-merge state with both subs available.
    client.commit_files(feat, {"shared.txt": b"base"}, "reset")
    # Re-create the deleted subagent branches.
    client.create_branch(sub_a, from_branch=feat)
    client.commit_files(sub_a, {"shared.txt": b"alpha-version"}, "alpha")
    client.create_branch(sub_b, from_branch=feat)
    client.commit_files(sub_b, {"shared.txt": b"beta-version"}, "beta")
    res2 = merge_mod.merge_subagent_branches(
        client, feature_branch=feat, subagent_branches=[sub_b, sub_a],
    )
    assert len(res2["merged"]) == 2
    assert client.get_file_bytes("shared.txt", feat) == b"alpha-version"


# ---------------------------------------------------------------------------
# schedule_successors
# ---------------------------------------------------------------------------

def test_schedule_successors_creates_null_issues_with_depends(client, base_config):
    successors = [
        {"title": "Step B", "instructions_inline": "Do B",
         "depends_on_prs": [101]},
        {"title": "Step C", "instructions_inline": "Do C",
         "depends_on_prs": [101, 102]},
    ]
    issues = sched_mod.schedule_successors(
        client, successors=successors, base_branch="main", parent_issue=99,
    )
    assert len(issues) == 2

    metas = [common.parse_agent_meta(i["body"]) for i in issues]
    # Pin exact list values, not just truthiness.
    assert metas[0]["depends_on_prs"] == [101]
    assert metas[1]["depends_on_prs"] == [101, 102]
    for m in metas:
        assert m["status"] is None
        assert m["agent_id"] is None
        assert m["session_id"] is None
        assert m["parent_issue"] == 99
        assert m["base_branch"] == "main"
