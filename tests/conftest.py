"""Shared fixtures for the agent-protocol POC test suite.

Sets up sys.path for the .agent/scripts and skill-relative module
loaders, and provides factory helpers used by most tests.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import pytest


# The static ``agent_login`` config key was removed in session 3. Tests
# that need a bot login pull it from the ``agent_login`` fixture (or the
# ``AGENT_LOGIN`` env var) instead of ``base_config["agent_login"]``.
TEST_AGENT_LOGIN = "jonathanmanton"
os.environ.setdefault("AGENT_LOGIN", TEST_AGENT_LOGIN)

# Make sure the repo root and key script directories are importable. We
# also pre-load the central common module so other modules don't end up
# with conflicting copies.
REPO_ROOT = Path(__file__).resolve().parent.parent
for p in (REPO_ROOT, REPO_ROOT / ".agent" / "scripts"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

# Import once via the script path so that ``common`` is well-defined
# regardless of test order.
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location(
    "agent_protocol_common",
    REPO_ROOT / ".agent" / "scripts" / "common.py",
)
_common = _ilu.module_from_spec(_spec)
sys.modules.setdefault("agent_protocol_common", _common)
_spec.loader.exec_module(_common)

# Also expose under the bare ``common`` name so handler.py's standalone
# import path resolves to the same module instance.
sys.modules.setdefault("common", _common)


InMemoryGitHubClient = _common.InMemoryGitHubClient
iso_now = _common.iso_now
render_agent_meta = _common.render_agent_meta
new_uuid = _common.new_uuid


# ---------------------------------------------------------------------------
# Path / config fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_root_path() -> Path:
    return REPO_ROOT


@pytest.fixture
def base_config() -> dict[str, Any]:
    """A copy of .agent/config.json for tests to mutate freely.

    The ``agent_login`` key is INJECTED into the returned dict for
    backwards compatibility with tests written against the old shape.
    The on-disk config no longer carries this key (removed in session 3
    — see SPEC §3 / §5.5). Tests that exercise the actual file should
    use :func:`load_config` and assert ``agent_login`` is absent.
    """
    with (REPO_ROOT / ".agent" / "config.json").open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("agent_login", TEST_AGENT_LOGIN)
    return cfg


@pytest.fixture
def agent_login() -> str:
    """Bot login for tests. Mirrors the AGENT_LOGIN env var."""
    return TEST_AGENT_LOGIN


@pytest.fixture
def fast_poll_config(base_config: dict[str, Any]) -> dict[str, Any]:
    """Config with tiny polling timeouts for unit tests."""
    cfg = dict(base_config)
    cfg["comment"] = dict(base_config["comment"])
    cfg["comment"]["runner_pickup_timeout_seconds"] = 1
    cfg["comment"]["running_timeout_seconds"] = 1
    cfg["comment"]["poll_total_timeout_seconds"] = 5
    cfg["comment"]["poll_initial_seconds"] = 0
    cfg["comment"]["poll_backoff"] = []
    return cfg


# ---------------------------------------------------------------------------
# Client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> Any:
    """A fresh InMemoryGitHubClient acting as ``jonathanmanton`` by default."""
    return InMemoryGitHubClient(default_user="jonathanmanton")


# ---------------------------------------------------------------------------
# Factory helpers (also exposed as fixtures)
# ---------------------------------------------------------------------------

def make_agent_meta(
    *,
    feature_branch: str = "agent/1-demo",
    base_branch: str = "main",
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    instructions_inline: Optional[str] = "Do the thing.",
    instructions_path: Optional[str] = None,
    parent_issue: Optional[int] = None,
    depends_on_prs: Optional[list[int]] = None,
    session_id: Optional[str] = None,
    status_ts: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "protocol_version": 1,
        "agent_id": agent_id,
        "session_id": session_id,
        "status": status,
        "status_ts": status_ts,
        "feature_branch": feature_branch,
        "base_branch": base_branch,
        "parent_issue": parent_issue,
        "depends_on_prs": depends_on_prs or [],
        "instructions_path": instructions_path,
        "instructions_inline": instructions_inline,
        "created_at": iso_now(),
    }


def make_envelope(
    *,
    command: str = "echo",
    args: Optional[dict[str, Any]] = None,
    branch: str = "agent/1-demo",
    commit_sha: str = "0" * 40,
    subagent_id: str = "alpha",
) -> dict[str, Any]:
    return {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "command": command,
        "args": args if args is not None else {"message": "hello"},
        "branch": branch,
        "commit_sha": commit_sha,
        "subagent_id": subagent_id,
        "submitted_at": iso_now(),
        "run_status": None,
        "agent_ack": None,
    }


def seed_agent_issue(
    client: Any,
    *,
    title: str = "Demo task",
    user: str = "jonathanmanton",
    locked: bool = False,
    labels: Optional[list[str]] = None,
    meta: Optional[dict[str, Any]] = None,
    prose: str = "Test prose.",
) -> dict[str, Any]:
    """Create an agent-style issue. Returns the dict returned by create_issue."""
    body = render_agent_meta(meta or make_agent_meta(), prose=prose)
    issue = client.create_issue(title=title, body=body, user=user, labels=labels)
    if locked:
        client.lock_issue(issue["number"])
    return client.get_issue(issue["number"])


def seed_branch_at(
    client: Any,
    branch: str,
    *,
    files: Optional[dict[str, bytes]] = None,
) -> str:
    """Create the branch with optional initial files. Returns head sha."""
    if branch not in client._branches:
        sha = client.create_branch(branch)
    else:
        sha = client.get_branch_head_sha(branch)
    if files:
        sha = client.commit_files(branch, files, "test seed")
    return sha


@pytest.fixture
def make_envelope_fixture():
    return make_envelope


@pytest.fixture
def make_agent_meta_fixture():
    return make_agent_meta


@pytest.fixture
def seed_issue():
    return seed_agent_issue


@pytest.fixture
def seed_branch():
    return seed_branch_at


@pytest.fixture
def locked_issue_with_branch(client):
    """Lock+labelled issue with a feature branch + matching commit_sha.

    Returns ``{issue, meta, branch, sha, agent_id}``.
    """
    agent_id = new_uuid()
    meta = make_agent_meta(
        feature_branch="agent/1-demo",
        agent_id=agent_id,
        status="working",
        status_ts=iso_now(),
    )
    issue = seed_agent_issue(
        client,
        meta=meta,
        locked=True,
        labels=["agent-task"],
    )
    sha = seed_branch_at(client, "agent/1-demo", files={"README.md": b"hi"})
    # also seed the base branch
    if "main" not in client._branches:
        client.create_branch("main")
    return {
        "issue": issue,
        "meta": meta,
        "branch": "agent/1-demo",
        "sha": sha,
        "agent_id": agent_id,
        "issue_number": issue["number"],
    }
