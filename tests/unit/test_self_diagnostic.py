"""Tests for the self-diagnostic comment posted by handler.main()
and friends when an uncaught exception occurs.

The diagnostic posts a comment to the issue (or PR for close_on_merge)
via a direct ``requests.post`` call so that MCP-only operators — who
cannot read GitHub Actions workflow logs — can see the traceback. The
diagnostic must never mask the original non-zero exit, and must never
echo the bearer token's value.
"""

from __future__ import annotations

from unittest import mock

import pytest

import close_on_merge
import handler
import lock_and_sweep


# ---------------------------------------------------------------------------
# handler.main()
# ---------------------------------------------------------------------------

def test_handler_main_posts_debug_comment_on_exception(capsys, monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "42")
    monkeypatch.setenv("COMMENT_ID", "1000001")
    monkeypatch.setenv("GH_TOKEN", "secret-token-value")
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token-value")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_RUN_ID", "9999")
    # Default ON, but be explicit:
    monkeypatch.setenv("HANDLER_DEBUG_COMMENT", "1")

    fake_resp = mock.Mock()
    fake_resp.status_code = 201
    fake_resp.text = "{}"

    with mock.patch.object(handler, "run", autospec=True) as mrun, \
         mock.patch("requests.post", return_value=fake_resp) as mpost:
        mrun.side_effect = RuntimeError("boom-from-run")
        rc = handler.main()

    assert rc == 1, "uncaught exception must still produce nonzero exit"
    assert mpost.call_count == 1, "diagnostic comment must be posted exactly once"

    call = mpost.call_args
    url = call.args[0]
    assert url == "https://api.github.com/repos/owner/repo/issues/42/comments"

    # Authorization header uses Bearer token.
    headers = call.kwargs["headers"]
    assert headers["Authorization"] == "Bearer secret-token-value"
    assert headers["Accept"] == "application/vnd.github+json"

    body = call.kwargs["json"]["body"]
    # Repr of exception + traceback should both appear.
    assert "boom-from-run" in body
    assert "RuntimeError" in body
    assert "Traceback" in body
    # Comment id and workflow run id should be referenced.
    assert "1000001" in body
    assert "9999" in body
    # Token VALUE must NOT leak into the body.
    assert "secret-token-value" not in body
    # Token presence summary should report 'set'.
    assert "set" in body


def test_handler_main_does_not_mask_original_exit(monkeypatch):
    """If the diagnostic POST itself raises, main() must still return 1."""
    monkeypatch.setenv("ISSUE_NUMBER", "42")
    monkeypatch.setenv("COMMENT_ID", "1000001")
    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("HANDLER_DEBUG_COMMENT", "1")

    with mock.patch.object(handler, "run", autospec=True) as mrun, \
         mock.patch("requests.post", side_effect=RuntimeError("network down")):
        mrun.side_effect = RuntimeError("boom-from-run")
        rc = handler.main()

    assert rc == 1


def test_handler_main_diagnostic_disabled_by_env(monkeypatch):
    """``HANDLER_DEBUG_COMMENT=0`` suppresses the diagnostic post."""
    monkeypatch.setenv("ISSUE_NUMBER", "42")
    monkeypatch.setenv("COMMENT_ID", "1000001")
    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("HANDLER_DEBUG_COMMENT", "0")

    with mock.patch.object(handler, "run", autospec=True) as mrun, \
         mock.patch("requests.post") as mpost:
        mrun.side_effect = RuntimeError("boom")
        rc = handler.main()

    assert rc == 1
    assert mpost.call_count == 0


# ---------------------------------------------------------------------------
# lock_and_sweep.main()
# ---------------------------------------------------------------------------

def test_lock_and_sweep_main_posts_debug_comment_on_exception(monkeypatch):
    monkeypatch.setenv("ISSUE_NUMBER", "7")
    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("HANDLER_DEBUG_COMMENT", "1")

    fake_resp = mock.Mock()
    fake_resp.status_code = 201
    fake_resp.text = "{}"

    with mock.patch.object(lock_and_sweep, "run", autospec=True) as mrun, \
         mock.patch("requests.post", return_value=fake_resp) as mpost:
        mrun.side_effect = RuntimeError("lock-boom")
        rc = lock_and_sweep.main()

    assert rc == 1
    assert mpost.call_count == 1
    url = mpost.call_args.args[0]
    assert url == "https://api.github.com/repos/owner/repo/issues/7/comments"
    body = mpost.call_args.kwargs["json"]["body"]
    assert "lock-boom" in body
    assert "lock_and_sweep.py" in body


# ---------------------------------------------------------------------------
# close_on_merge.main()
# ---------------------------------------------------------------------------

def test_close_on_merge_main_posts_debug_comment_to_pr_when_no_closes(monkeypatch):
    """When ``Closes #N`` is missing from the PR body, fall back to PR."""
    monkeypatch.setenv("PR_NUMBER", "5050")
    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("HANDLER_DEBUG_COMMENT", "1")

    fake_post = mock.Mock()
    fake_post.status_code = 201
    fake_post.text = "{}"

    fake_get = mock.Mock()
    fake_get.status_code = 200
    fake_get.json = mock.Mock(return_value={"body": "no closes here"})

    with mock.patch.object(close_on_merge, "run", autospec=True) as mrun, \
         mock.patch("requests.post", return_value=fake_post) as mpost, \
         mock.patch("requests.get", return_value=fake_get):
        mrun.side_effect = RuntimeError("merge-boom")
        rc = close_on_merge.main()

    assert rc == 1
    assert mpost.call_count == 1
    url = mpost.call_args.args[0]
    # Falls back to the PR number itself.
    assert url == "https://api.github.com/repos/owner/repo/issues/5050/comments"
    body = mpost.call_args.kwargs["json"]["body"]
    assert "merge-boom" in body
    assert "close_on_merge.py" in body


def test_close_on_merge_main_posts_debug_comment_to_closed_issue(monkeypatch):
    """When the PR body contains ``Closes #N``, post diagnostic to that issue."""
    monkeypatch.setenv("PR_NUMBER", "5050")
    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("HANDLER_DEBUG_COMMENT", "1")

    fake_post = mock.Mock()
    fake_post.status_code = 201
    fake_post.text = "{}"

    fake_get = mock.Mock()
    fake_get.status_code = 200
    fake_get.json = mock.Mock(return_value={"body": "Closes #123\n"})

    with mock.patch.object(close_on_merge, "run", autospec=True) as mrun, \
         mock.patch("requests.post", return_value=fake_post) as mpost, \
         mock.patch("requests.get", return_value=fake_get):
        mrun.side_effect = RuntimeError("merge-boom")
        rc = close_on_merge.main()

    assert rc == 1
    assert mpost.call_count == 1
    url = mpost.call_args.args[0]
    assert url == "https://api.github.com/repos/owner/repo/issues/123/comments"


# ---------------------------------------------------------------------------
# _post_debug_comment unit-level checks
# ---------------------------------------------------------------------------

def test_post_debug_comment_does_not_leak_token_value(monkeypatch):
    """The token VALUE must never be present in the comment body."""
    monkeypatch.setenv("GH_TOKEN", "very-secret-token-12345")
    monkeypatch.setenv("GITHUB_TOKEN", "very-secret-token-12345")

    fake_resp = mock.Mock()
    fake_resp.status_code = 201
    fake_resp.text = "{}"

    with mock.patch("requests.post", return_value=fake_resp) as mpost:
        try:
            raise ValueError("test exception")
        except ValueError as e:
            handler._post_debug_comment(
                token="very-secret-token-12345",
                owner="owner",
                repo="repo",
                issue_number=1,
                script="handler.py",
                exc=e,
                extra_fields={"comment": 999},
            )

    body = mpost.call_args.kwargs["json"]["body"]
    assert "very-secret-token-12345" not in body
    # Header IS allowed to contain it (that's how it authenticates).
    assert mpost.call_args.kwargs["headers"]["Authorization"] == \
        "Bearer very-secret-token-12345"
