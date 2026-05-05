"""Tests for the ``main()`` POC stubs in workflow scripts.

The POC scripts (``handler``, ``lock_and_sweep``, ``close_on_merge``) all
expose a ``main()`` that:

- Prints the required and optional environment variables on stderr.
- Exits with code 0 even when env vars are missing (POC stub semantics).
- When env vars *are* set, prints a "would dispatch" message instead.

These tests pin those behaviours.
"""

from __future__ import annotations

import os
from typing import Iterable

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

def test_handler_main_no_env_exits_zero_with_message(capsys, monkeypatch):
    _clear_env(monkeypatch, [
        "ISSUE_NUMBER", "COMMENT_ID", "GITHUB_TOKEN", "GITHUB_REPOSITORY",
        "WORKFLOW_RUN_ID", "GITHUB_WORKSPACE",
    ])
    rc = handler.main()
    assert rc == 0
    captured = capsys.readouterr()
    err = captured.err
    # Required env list and "missing" diagnostic are both informative.
    assert "ISSUE_NUMBER" in err
    assert "COMMENT_ID" in err
    assert "GITHUB_TOKEN" in err
    assert "GITHUB_REPOSITORY" in err
    assert "missing env vars" in err.lower()


def test_handler_main_with_all_env_set_prints_would_dispatch(capsys, monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "42")
    monkeypatch.setenv("COMMENT_ID", "1000001")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    rc = handler.main()
    assert rc == 0
    err = capsys.readouterr().err
    assert "would dispatch" in err.lower()
    assert "42" in err
    assert "1000001" in err


# ---------------------------------------------------------------------------
# lock_and_sweep.main()
# ---------------------------------------------------------------------------

def test_lock_and_sweep_main_no_env_exits_zero(capsys, monkeypatch):
    _clear_env(monkeypatch, [
        "ISSUE_NUMBER", "GITHUB_TOKEN", "GITHUB_REPOSITORY",
        "AGENT_LOGIN", "AGENT_TASK_LABEL",
    ])
    rc = lock_and_sweep.main()
    assert rc == 0
    err = capsys.readouterr().err
    assert "ISSUE_NUMBER" in err
    assert "GITHUB_TOKEN" in err
    assert "GITHUB_REPOSITORY" in err
    assert "missing env vars" in err.lower()


def test_lock_and_sweep_main_with_env_prints_would_process(capsys, monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "7")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    rc = lock_and_sweep.main()
    assert rc == 0
    err = capsys.readouterr().err
    assert "would process issue" in err.lower()
    assert "#7" in err


# ---------------------------------------------------------------------------
# close_on_merge.main()
# ---------------------------------------------------------------------------

def test_close_on_merge_main_no_env_exits_zero(capsys, monkeypatch):
    _clear_env(monkeypatch, [
        "PR_NUMBER", "GITHUB_TOKEN", "GITHUB_REPOSITORY",
    ])
    rc = close_on_merge.main()
    assert rc == 0
    err = capsys.readouterr().err
    assert "PR_NUMBER" in err
    assert "GITHUB_TOKEN" in err
    assert "GITHUB_REPOSITORY" in err
    assert "missing env vars" in err.lower()


def test_close_on_merge_main_with_env_prints_would_handle(capsys, monkeypatch):
    monkeypatch.setenv("PR_NUMBER", "5050")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    rc = close_on_merge.main()
    assert rc == 0
    err = capsys.readouterr().err
    assert "would handle pr" in err.lower()
    assert "#5050" in err
