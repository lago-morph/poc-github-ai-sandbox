"""Tests for the ``batch-job`` skill (submit and poll)."""

from __future__ import annotations

import importlib.util as _ilu
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_skill_module(name: str, file_name: str):
    full = f"skills_batchjob_{name}"
    if full in sys.modules:
        return sys.modules[full]
    path = REPO_ROOT / "skills" / "batch-job" / file_name
    spec = _ilu.spec_from_file_location(full, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


submit_mod = _load_skill_module("submit", "submit.py")
poll_mod = _load_skill_module("poll", "poll.py")
PreflightError = submit_mod.PreflightError
PollTimeout = poll_mod.PollTimeout

import agent_protocol_common as common
import handler  # noqa: F401  (preload for shared sys.modules state)
from tests.conftest import make_agent_meta


def _seed_locked_issue(client, *, agent_id="A", labels=("agent-task",), prose="P"):
    meta = make_agent_meta(agent_id=agent_id, status="working",
                           status_ts=common.iso_now())
    body = common.render_agent_meta(meta, prose=prose)
    issue = client.create_issue(title="t", body=body, user="my-bot",
                                labels=list(labels))
    client.lock_issue(issue["number"])
    return client.get_issue(issue["number"]), meta


# ---------------------------------------------------------------------------
# submit
# ---------------------------------------------------------------------------

def test_submit_builds_envelope_and_posts(client, base_config):
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("agent/1-demo")
    res = submit_mod.submit(
        client,
        issue_number=issue["number"],
        command="echo",
        args={"message": "hi"},
        branch="agent/1-demo",
        commit_sha=sha,
        subagent_id="alpha",
        agent_id="A",
        config=base_config,
    )
    assert res["id"]
    body = json.loads(res["body"])
    assert body["protocol_version"] == 1
    assert body["kind"] == "batch-job-request"
    assert body["command"] == "echo"
    assert body["args"]["message"] == "hi"
    assert body["branch"] == "agent/1-demo"
    assert body["commit_sha"] == sha
    assert body["subagent_id"] == "alpha"
    assert body["run_status"] is None


def test_submit_preflight_unlocked(client, base_config):
    meta = make_agent_meta(agent_id="A")
    body = common.render_agent_meta(meta, prose="P")
    issue = client.create_issue(title="t", body=body, user="my-bot",
                                labels=["agent-task"])
    # not locked
    with pytest.raises(PreflightError):
        submit_mod.submit(
            client,
            issue_number=issue["number"], command="echo",
            args={"message": "x"}, branch="b", commit_sha="0" * 40,
            subagent_id="alpha", agent_id="A", config=base_config,
        )


def test_submit_preflight_label_missing(client, base_config):
    meta = make_agent_meta(agent_id="A")
    body = common.render_agent_meta(meta, prose="P")
    issue = client.create_issue(title="t", body=body, user="my-bot")
    client.lock_issue(issue["number"])
    # no agent-task label
    with pytest.raises(PreflightError):
        submit_mod.submit(
            client,
            issue_number=issue["number"], command="echo",
            args={"message": "x"}, branch="b", commit_sha="0" * 40,
            subagent_id="alpha", agent_id="A", config=base_config,
        )


def test_submit_preflight_agent_id_mismatch(client, base_config):
    issue, _ = _seed_locked_issue(client, agent_id="OWNER-1")
    with pytest.raises(PreflightError):
        submit_mod.submit(
            client,
            issue_number=issue["number"], command="echo",
            args={"message": "x"}, branch="b", commit_sha="0" * 40,
            subagent_id="alpha", agent_id="OTHER", config=base_config,
        )


def test_submit_invalid_args_raises(client, base_config):
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("agent/1-demo")
    with pytest.raises(Exception):
        submit_mod.submit(
            client,
            issue_number=issue["number"], command="run-tests",
            args={"suite": "not-a-real-suite"},
            branch="agent/1-demo", commit_sha=sha,
            subagent_id="alpha", agent_id="A", config=base_config,
        )


# ---------------------------------------------------------------------------
# poll
# ---------------------------------------------------------------------------

class _ManualClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def _no_sleep(t):
    return None


def _post_request(client, issue_number, sha):
    env = {
        "protocol_version": 1, "kind": "batch-job-request",
        "command": "echo", "args": {"message": "x"},
        "branch": "br", "commit_sha": sha, "subagent_id": "alpha",
        "submitted_at": common.iso_now(),
        "run_status": None, "agent_ack": None,
    }
    return client.add_comment(issue_number, json.dumps(env))


def test_poll_returns_terminal_completed_with_summary(client, base_config):
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("br")
    c = _post_request(client, issue["number"], sha)
    # simulate handler completing the run
    final_env = json.loads(c["body"])
    final_env.update({
        "run_status": "completed",
        "run_started_at": common.iso_now(),
        "run_finished_at": common.iso_now(),
        "workflow_run_id": 7,
        "checked_out_sha": sha,
        "summary": {"echoed_args": {"message": "x"}, "message": "x"},
        "log_manifest_branch": "_agent_runs",
        "log_manifest_path": f"runs/{issue['number']}/{c['id']}/manifest.json",
    })
    client.update_comment(c["id"], json.dumps(final_env))
    # also seed summary.json
    client.put_file_contents(
        f"runs/{issue['number']}/{c['id']}/summary.json",
        json.dumps({"summary": final_env["summary"], "run_status": "completed"}).encode(),
        "msg", "_agent_runs",
    )
    out = poll_mod.poll(
        client, comment_id=c["id"], command="echo",
        config=base_config, sleep=_no_sleep, now=_ManualClock(),
    )
    assert out["envelope"]["agent_ack"] == "finished"
    assert out["summary"]["message"] == "x"
    assert out["summary_json"]["run_status"] == "completed"


def test_poll_returns_terminal_error(client, base_config):
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("br")
    c = _post_request(client, issue["number"], sha)
    env = json.loads(c["body"])
    env.update({
        "run_status": "error",
        "run_started_at": common.iso_now(),
        "run_finished_at": common.iso_now(),
        "workflow_run_id": 9,
        "error_kind": "branch_sha_mismatch",
        "error_detail": "broken",
        "summary": {"error_kind": "branch_sha_mismatch", "error_detail": "broken"},
    })
    client.update_comment(c["id"], json.dumps(env))
    out = poll_mod.poll(
        client, comment_id=c["id"], command="echo",
        config=base_config, sleep=_no_sleep, now=_ManualClock(),
    )
    assert out["envelope"]["run_status"] == "error"
    assert out["envelope"]["agent_ack"] == "finished"


def test_poll_runner_pickup_timeout(client, fast_poll_config):
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("br")
    c = _post_request(client, issue["number"], sha)
    clock = _ManualClock()

    def adv_sleep(t):
        clock.advance(max(t, 1.0))  # ensure forward progress

    with pytest.raises(PollTimeout) as ei:
        poll_mod.poll(
            client, comment_id=c["id"], command="echo",
            config=fast_poll_config, sleep=adv_sleep, now=clock,
        )
    assert ei.value.kind == "runner_pickup_timeout"


def test_poll_running_timeout(client, fast_poll_config):
    """Pin to running_timeout exactly: short running_timeout, generous total_timeout."""
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("br")
    c = _post_request(client, issue["number"], sha)
    env = json.loads(c["body"])
    env["run_status"] = "running"
    env["run_started_at"] = common.iso_now()
    env["workflow_run_id"] = 1
    env["checked_out_sha"] = sha
    client.update_comment(c["id"], json.dumps(env))

    # Tighten running deadline; widen the total deadline so only the
    # running deadline can fire first.
    cfg = json.loads(json.dumps(fast_poll_config))  # deep copy
    cfg["comment"]["running_timeout_seconds"] = 1
    cfg["comment"]["poll_total_timeout_seconds"] = 300

    clock = _ManualClock()

    def adv_sleep(t):
        clock.advance(max(t, 1.0))

    with pytest.raises(PollTimeout) as ei:
        poll_mod.poll(
            client, comment_id=c["id"], command="echo",
            config=cfg, sleep=adv_sleep, now=clock,
        )
    assert ei.value.kind == "running_timeout"


# ---------------------------------------------------------------------------
# heartbeat callable (iter 2)
# ---------------------------------------------------------------------------

def test_poll_invokes_heartbeat_each_cycle(client, fast_poll_config):
    """poll() should call ``heartbeat`` once per cycle when it loops."""
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("br")
    c = _post_request(client, issue["number"], sha)

    counter = {"calls": 0}

    def hb():
        counter["calls"] += 1
        # After two cycles, transition to terminal so we exit cleanly.
        if counter["calls"] >= 2:
            env = json.loads(client.get_comment(c["id"])["body"])
            env.update({
                "run_status": "completed",
                "run_started_at": common.iso_now(),
                "run_finished_at": common.iso_now(),
                "workflow_run_id": 1,
                "checked_out_sha": sha,
                "summary": {"echoed_args": {"message": "x"}, "message": "x"},
                "log_manifest_branch": "_agent_runs",
                "log_manifest_path": f"runs/{issue['number']}/{c['id']}/manifest.json",
            })
            client.update_comment(c["id"], json.dumps(env))

    clock = _ManualClock()

    def adv_sleep(t):
        clock.advance(max(t, 1.0))

    out = poll_mod.poll(
        client, comment_id=c["id"], command="echo",
        config=fast_poll_config, sleep=adv_sleep, now=clock,
        heartbeat=hb,
    )
    assert out["envelope"]["run_status"] == "completed"
    # heartbeat should have fired at least twice (once for each loop iter).
    assert counter["calls"] >= 2


def test_poll_without_heartbeat_works(client, base_config):
    """Default behaviour: passing no ``heartbeat`` callable still polls fine."""
    issue, _ = _seed_locked_issue(client, agent_id="A")
    sha = client.create_branch("br")
    c = _post_request(client, issue["number"], sha)
    # Mark already-terminal so poll exits on first iteration.
    env = json.loads(c["body"])
    env.update({
        "run_status": "completed",
        "run_started_at": common.iso_now(),
        "run_finished_at": common.iso_now(),
        "workflow_run_id": 1,
        "checked_out_sha": sha,
        "summary": {"echoed_args": {"message": "x"}, "message": "x"},
        "log_manifest_branch": "_agent_runs",
        "log_manifest_path": f"runs/{issue['number']}/{c['id']}/manifest.json",
    })
    client.update_comment(c["id"], json.dumps(env))
    out = poll_mod.poll(
        client, comment_id=c["id"], command="echo",
        config=base_config, sleep=_no_sleep, now=_ManualClock(),
    )
    assert out["envelope"]["run_status"] == "completed"
    assert out["envelope"]["agent_ack"] == "finished"
