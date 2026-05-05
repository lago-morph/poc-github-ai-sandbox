"""Tests for the ``main()`` entry points in workflow scripts.

The workflow scripts (``handler``, ``lock_and_sweep``, ``close_on_merge``)
expose a ``main()`` that:

- Prints the required environment variables on stderr.
- Returns non-zero (1) when required env vars are missing.
- When env vars are set, constructs a real :class:`RestGitHubClient` and
  calls :func:`run`. If the live HTTP call fails the script exits 1.

These tests pin those behaviours. Live HTTP is mocked / blocked.
"""

from __future__ import annotations

from typing import Iterable
from unittest import mock

import pytest

import close_on_merge
import handler
import lock_and_sweep


def _clear_env(monkeypatch, names: Iterable[str]) -> None:
    for n in names:
        monkeypatch.delenv(n, raising=False)


# ---------------------------------------------------------------------------
# handler.main()
# ---------------------------------------------------------------------------

def test_handler_main_no_env_returns_nonzero(capsys, monkeypatch):
    _clear_env(monkeypatch, [
        "ISSUE_NUMBER", "COMMENT_ID", "GITHUB_TOKEN", "GH_TOKEN",
        "GITHUB_REPOSITORY", "WORKFLOW_RUN_ID", "GITHUB_RUN_ID",
        "GITHUB_WORKSPACE",
    ])
    rc = handler.main()
    assert rc == 1
    err = capsys.readouterr().err
    # Required env list and "missing" diagnostic are both informative.
    assert "ISSUE_NUMBER" in err
    assert "COMMENT_ID" in err
    assert "GITHUB_TOKEN" in err
    assert "GITHUB_REPOSITORY" in err
    assert "missing env vars" in err.lower()


def test_handler_main_bad_repo_slug_returns_nonzero(capsys, monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "42")
    monkeypatch.setenv("COMMENT_ID", "1000001")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "no-slash")
    rc = handler.main()
    assert rc == 1
    assert "owner/repo" in capsys.readouterr().err


def test_handler_main_dispatches_to_run(capsys, monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "42")
    monkeypatch.setenv("COMMENT_ID", "1000001")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_RUN_ID", "9999")
    monkeypatch.setenv("GITHUB_WORKSPACE", "/tmp/ws")

    with mock.patch.object(handler, "run", autospec=True) as mrun:
        mrun.return_value = {"action": "ran"}
        rc = handler.main()

    assert rc == 0
    assert mrun.call_count == 1
    args, kwargs = mrun.call_args
    # Positional: client, issue_number, comment_id
    assert args[1] == 42
    assert args[2] == 1000001
    assert kwargs["workflow_run_id"] == 9999
    assert kwargs["workspace"] == "/tmp/ws"
    err = capsys.readouterr().err
    assert "dispatching" in err.lower()
    assert "42" in err
    assert "1000001" in err


def test_handler_main_uncaught_exception_returns_nonzero(capsys, monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "42")
    monkeypatch.setenv("COMMENT_ID", "1000001")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    with mock.patch.object(handler, "run", autospec=True) as mrun:
        mrun.side_effect = RuntimeError("boom")
        rc = handler.main()
    assert rc == 1
    assert "boom" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# lock_and_sweep.main()
# ---------------------------------------------------------------------------

def test_lock_and_sweep_main_no_env_returns_nonzero(capsys, monkeypatch):
    _clear_env(monkeypatch, [
        "ISSUE_NUMBER", "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_REPOSITORY",
        "AGENT_LOGIN", "AGENT_TASK_LABEL",
    ])
    rc = lock_and_sweep.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "ISSUE_NUMBER" in err
    assert "GITHUB_TOKEN" in err
    assert "GITHUB_REPOSITORY" in err
    assert "missing env vars" in err.lower()


def test_lock_and_sweep_main_dispatches_to_run(capsys, monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "7")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    with mock.patch.object(lock_and_sweep, "run", autospec=True) as mrun:
        mrun.return_value = {"action": "locked"}
        rc = lock_and_sweep.main()
    assert rc == 0
    assert mrun.call_count == 1
    args, kwargs = mrun.call_args
    assert args[1] == 7
    err = capsys.readouterr().err
    assert "processing issue" in err.lower()
    assert "#7" in err


def test_lock_and_sweep_main_uncaught_exception_returns_nonzero(monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "7")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    with mock.patch.object(lock_and_sweep, "run", autospec=True) as mrun:
        mrun.side_effect = RuntimeError("nope")
        rc = lock_and_sweep.main()
    assert rc == 1


# ---------------------------------------------------------------------------
# close_on_merge.main()
# ---------------------------------------------------------------------------

def test_close_on_merge_main_no_env_returns_nonzero(capsys, monkeypatch):
    _clear_env(monkeypatch, [
        "PR_NUMBER", "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_REPOSITORY",
    ])
    rc = close_on_merge.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "PR_NUMBER" in err
    assert "GITHUB_TOKEN" in err
    assert "GITHUB_REPOSITORY" in err
    assert "missing env vars" in err.lower()


def test_close_on_merge_main_dispatches_to_run(capsys, monkeypatch):
    monkeypatch.setenv("PR_NUMBER", "5050")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    with mock.patch.object(close_on_merge, "run", autospec=True) as mrun:
        mrun.return_value = {"action": "closed"}
        rc = close_on_merge.main()
    assert rc == 0
    assert mrun.call_count == 1
    args, kwargs = mrun.call_args
    assert args[1] == 5050
    err = capsys.readouterr().err
    assert "handling pr" in err.lower()
    assert "#5050" in err


def test_close_on_merge_main_uncaught_exception_returns_nonzero(monkeypatch):
    monkeypatch.setenv("PR_NUMBER", "5050")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    with mock.patch.object(close_on_merge, "run", autospec=True) as mrun:
        mrun.side_effect = RuntimeError("nope")
        rc = close_on_merge.main()
    assert rc == 1
