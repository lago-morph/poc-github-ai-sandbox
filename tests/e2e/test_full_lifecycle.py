"""End-to-end happy-path and error-recovery scenarios using the in-memory client."""

from __future__ import annotations

import importlib.util as _ilu
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(full: str, path: Path):
    if full in sys.modules:
        return sys.modules[full]
    spec = _ilu.spec_from_file_location(full, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


submit_mod = _load(
    "skills_batchjob_submit", REPO_ROOT / "skills" / "batch-job" / "submit.py"
)
poll_mod = _load(
    "skills_batchjob_poll", REPO_ROOT / "skills" / "batch-job" / "poll.py"
)

import agent_protocol_common as common
import handler
import lock_and_sweep
import close_on_merge
from tests.conftest import make_agent_meta


def _no_sleep(t):
    return None


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def test_full_happy_lifecycle(client, base_config):
    # Step 1: human (acting as bot) creates issue
    meta = make_agent_meta(
        feature_branch="agent/42-demo",
        instructions_inline="Run echo job.",
    )
    body = common.render_agent_meta(meta, prose="Demo")
    with client.as_user("my-bot"):
        issue = client.create_issue(title="demo", body=body)
    n = issue["number"]

    # Step 2: lock_and_sweep
    res = lock_and_sweep.run(client, n, config=base_config)
    assert res["action"] == "locked"

    # Step 3: claim (write agent_id and status=working)
    new_meta = dict(meta)
    new_meta["agent_id"] = "primary-1"
    new_meta["status"] = "working"
    new_meta["status_ts"] = common.iso_now()
    new_meta["session_id"] = "session-1"
    client.update_issue(n, body=common.render_agent_meta(new_meta, prose="Demo"))

    # Seed feature branch
    client.create_branch("main")
    sha = client.create_branch("agent/42-demo", from_branch="main")
    client.commit_files("agent/42-demo", {"file.txt": b"work"}, "subagent edit")
    sha = client.get_branch_head_sha("agent/42-demo")

    # Step 4: submit batch-job-request (echo) under the agent identity
    with client.as_user("my-bot"):
        comment = submit_mod.submit(
            client, issue_number=n, command="echo",
            args={"message": "hello world"},
            branch="agent/42-demo", commit_sha=sha,
            subagent_id="alpha", agent_id="primary-1",
            config=base_config,
        )
    cid = comment["id"]

    # Step 5: handler runs
    handler.run(client, n, cid, config=base_config, repo_root=str(REPO_ROOT))
    final = json.loads(client.get_comment(cid)["body"])
    assert final["run_status"] == "completed"

    # Step 6: poll/ack
    out = poll_mod.poll(
        client, comment_id=cid, command="echo",
        config=base_config, sleep=_no_sleep, now=_Clock(),
    )
    assert out["envelope"]["agent_ack"] == "finished"
    assert out["summary_json"]["run_status"] == "completed"

    # Step 7: open PR
    pr = client.create_pull_request(
        title="Demo", head="agent/42-demo", base="main",
        body=f"Closes #{n}\nResults attached.",
    )

    # Step 8: write status=finished, close issue
    final_meta = common.parse_agent_meta(client.get_issue(n)["body"])
    final_meta["status"] = "finished"
    final_meta["status_ts"] = common.iso_now()
    client.update_issue(n, body=common.render_agent_meta(final_meta, prose="Demo"))
    client.update_issue(n, state="closed")

    # Step 9: simulate PR merge → close-on-merge re-asserts
    client.merge_pull_request(pr["number"])
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "closed"

    # Step 10: assertions
    fetched = client.get_issue(n)
    assert fetched["state"] == "closed"
    assert fetched["locked"] is True
    final_comment = json.loads(client.get_comment(cid)["body"])
    assert final_comment["run_status"] == "completed"
    assert final_comment["agent_ack"] == "finished"
    # Logs landed on _agent_runs
    manifest_path = final_comment["log_manifest_path"]
    assert client.get_file_contents(manifest_path, "_agent_runs") is not None


def test_e2e_error_recovery_then_retry(client, base_config):
    """Submit with bad SHA → handler errors → resubmit with corrected SHA."""
    meta = make_agent_meta(
        feature_branch="agent/9-fix", instructions_inline="Fix it.",
    )
    body = common.render_agent_meta(meta, prose="P")
    with client.as_user("my-bot"):
        issue = client.create_issue(title="fix", body=body)
    n = issue["number"]
    lock_and_sweep.run(client, n, config=base_config)

    new_meta = dict(meta)
    new_meta.update({
        "agent_id": "primary-2", "status": "working",
        "status_ts": common.iso_now(), "session_id": "s",
    })
    client.update_issue(n, body=common.render_agent_meta(new_meta, prose="P"))

    client.create_branch("main")
    real_sha = client.create_branch("agent/9-fix")
    bad_sha = "0" * 40

    # First submit: wrong sha
    with client.as_user("my-bot"):
        c1 = submit_mod.submit(
            client, issue_number=n, command="echo",
            args={"message": "first"},
            branch="agent/9-fix", commit_sha=bad_sha,
            subagent_id="alpha", agent_id="primary-2",
            config=base_config,
        )
    handler.run(client, n, c1["id"], config=base_config, repo_root=str(REPO_ROOT))
    e1 = json.loads(client.get_comment(c1["id"])["body"])
    assert e1["run_status"] == "error"
    assert e1["error_kind"] == "branch_sha_mismatch"

    # Second submit: corrected sha
    with client.as_user("my-bot"):
        c2 = submit_mod.submit(
            client, issue_number=n, command="echo",
            args={"message": "second"},
            branch="agent/9-fix", commit_sha=real_sha,
            subagent_id="alpha", agent_id="primary-2",
            config=base_config,
        )
    handler.run(client, n, c2["id"], config=base_config, repo_root=str(REPO_ROOT))
    e2 = json.loads(client.get_comment(c2["id"])["body"])
    assert e2["run_status"] == "completed"
    assert e2["summary"]["message"] == "second"


# ---------------------------------------------------------------------------
# Iter 2 e2e expansion (Section G)
# ---------------------------------------------------------------------------

merge_mod = _load(
    "skills_taskdag_merge", REPO_ROOT / "skills" / "task-dag" / "merge.py"
)


def test_e2e_with_subagent_branches(client, base_config):
    """Primary spawns 2 subagent branches, each posts a job, primary merges,
    opens PR, finishes — full subagent lifecycle."""
    meta = make_agent_meta(
        feature_branch="agent/77-multi",
        instructions_inline="Coordinate multiple subagents.",
    )
    body = common.render_agent_meta(meta, prose="multi")
    with client.as_user("my-bot"):
        issue = client.create_issue(title="multi", body=body)
    n = issue["number"]
    lock_and_sweep.run(client, n, config=base_config)

    # Claim
    new_meta = dict(meta)
    new_meta.update({
        "agent_id": "primary-multi", "status": "working",
        "session_id": "s-multi", "status_ts": common.iso_now(),
    })
    client.update_issue(n, body=common.render_agent_meta(new_meta, prose="multi"))

    # Set up base + feature + 2 subagent branches.
    client.create_branch("main")
    client.create_branch("agent/77-multi", from_branch="main")
    sub_a = "agent/77-multi/sub-alpha"
    sub_b = "agent/77-multi/sub-beta"
    client.create_branch(sub_a, from_branch="agent/77-multi")
    client.commit_files(sub_a, {"alpha.txt": b"alpha-data"}, "alpha")
    client.create_branch(sub_b, from_branch="agent/77-multi")
    client.commit_files(sub_b, {"beta.txt": b"beta-data"}, "beta")

    # Each subagent posts a job comment that the handler runs.
    sub_results = {}
    for sub_name, sub_branch in (("alpha", sub_a), ("beta", sub_b)):
        sha = client.get_branch_head_sha(sub_branch)
        with client.as_user("my-bot"):
            comment = submit_mod.submit(
                client, issue_number=n, command="echo",
                args={"message": f"work-{sub_name}"},
                branch=sub_branch, commit_sha=sha,
                subagent_id=sub_name, agent_id="primary-multi",
                config=base_config,
            )
        handler.run(client, n, comment["id"], config=base_config, repo_root=str(REPO_ROOT))
        env = json.loads(client.get_comment(comment["id"])["body"])
        assert env["run_status"] == "completed"
        sub_results[sub_name] = env

    # Primary merges the subagent branches into the feature branch.
    merge_res = merge_mod.merge_subagent_branches(
        client, feature_branch="agent/77-multi",
        subagent_branches=[sub_a, sub_b],
    )
    assert len(merge_res["merged"]) == 2
    assert sorted(merge_res["deleted"]) == sorted([sub_a, sub_b])
    assert client.get_file_bytes("alpha.txt", "agent/77-multi") == b"alpha-data"
    assert client.get_file_bytes("beta.txt", "agent/77-multi") == b"beta-data"

    # Subagent branches are gone after the merge.
    assert client.get_branch_head_sha(sub_a) is None
    assert client.get_branch_head_sha(sub_b) is None

    # Open PR + finish.
    pr = client.create_pull_request(
        title="multi", head="agent/77-multi", base="main",
        body=f"Closes #{n}\nMulti subagent run.",
    )
    final_meta = common.parse_agent_meta(client.get_issue(n)["body"])
    final_meta["status"] = "finished"
    final_meta["status_ts"] = common.iso_now()
    client.update_issue(n, body=common.render_agent_meta(final_meta, prose="multi"))
    client.update_issue(n, state="closed")
    client.merge_pull_request(pr["number"])
    res = close_on_merge.run(client, pr["number"], config=base_config)
    assert res["action"] == "closed"
    assert n in res["issues_closed"]


def test_e2e_unsupported_version_recovery(client, base_config):
    """Submit an envelope with protocol_version=2; handler reports parse_error
    with error_kind=unsupported_version; agent then resubmits as v1 and runs."""
    meta = make_agent_meta(
        feature_branch="agent/13-ver",
        instructions_inline="Resubmit after version error.",
    )
    body = common.render_agent_meta(meta, prose="v")
    with client.as_user("my-bot"):
        issue = client.create_issue(title="v", body=body)
    n = issue["number"]
    lock_and_sweep.run(client, n, config=base_config)

    new_meta = dict(meta)
    new_meta.update({
        "agent_id": "primary-ver", "status": "working",
        "session_id": "s", "status_ts": common.iso_now(),
    })
    client.update_issue(n, body=common.render_agent_meta(new_meta, prose="v"))

    client.create_branch("main")
    sha = client.create_branch("agent/13-ver")

    # First submit — bad protocol_version — bypass submit() (which uses v1)
    # and post the comment directly.
    bad_envelope = {
        "protocol_version": 2,
        "kind": "batch-job-request",
        "command": "echo",
        "args": {"message": "first"},
        "branch": "agent/13-ver",
        "commit_sha": sha,
        "subagent_id": "alpha",
        "submitted_at": common.iso_now(),
        "run_status": None,
        "agent_ack": None,
    }
    with client.as_user("my-bot"):
        c1 = client.add_comment(n, json.dumps(bad_envelope, indent=2))
    handler.run(client, n, c1["id"], config=base_config, repo_root=str(REPO_ROOT))
    e1 = json.loads(client.get_comment(c1["id"])["body"])
    assert e1["run_status"] == "parse_error"
    assert e1["error_kind"] == "unsupported_version"
    assert e1["original_body_b64"]

    # Agent reads the error, re-submits with protocol_version=1 via submit().
    with client.as_user("my-bot"):
        c2 = submit_mod.submit(
            client, issue_number=n, command="echo",
            args={"message": "second"},
            branch="agent/13-ver", commit_sha=sha,
            subagent_id="alpha", agent_id="primary-ver",
            config=base_config,
        )
    handler.run(client, n, c2["id"], config=base_config, repo_root=str(REPO_ROOT))
    e2 = json.loads(client.get_comment(c2["id"])["body"])
    assert e2["run_status"] == "completed"
    assert e2["summary"]["message"] == "second"
