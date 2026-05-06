"""Pure predicates for verifying post-MCP state in harness scenarios.

Each ``assert_*`` helper raises :class:`HarnessAssertionError` (a
subclass of :class:`AssertionError`) on failure so pytest treats it as
a regular assertion. The helpers perform no I/O — callers pass in the
plain dicts already fetched via MCP.
"""

from __future__ import annotations

from typing import Any, Mapping

import agent_lib


# Terminal run_status values per the request envelope schema.
_TERMINAL_STATUSES = frozenset({"completed", "error", "parse_error"})


class HarnessAssertionError(AssertionError):
    """Raised when a harness predicate fails."""


def _require_dict(value: Any, name: str) -> None:
    if not isinstance(value, dict):
        raise HarnessAssertionError(
            f"{name} must be a dict, got {type(value).__name__}"
        )


def assert_issue_locked(issue: Any) -> None:
    """Raise if ``issue["locked"]`` is not truthy."""
    _require_dict(issue, "issue")
    if not issue.get("locked"):
        raise HarnessAssertionError(
            f"issue #{issue.get('number')} is not locked"
        )


def assert_issue_has_label(issue: Any, label: str) -> None:
    """Raise if ``label`` is not present on the issue.

    Accepts labels in either GraphQL/REST shapes:
    ``[{"name": "x"}, ...]`` or ``["x", ...]``.
    """
    _require_dict(issue, "issue")
    if "labels" not in issue:
        raise HarnessAssertionError(
            f"issue #{issue.get('number')} has no labels key"
        )
    names: list[str] = []
    for entry in issue["labels"] or []:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict) and "name" in entry:
            names.append(entry["name"])
    if label not in names:
        raise HarnessAssertionError(
            f"issue #{issue.get('number')} missing label {label!r} "
            f"(have {names!r})"
        )


def assert_envelope_terminal(
    envelope: Any,
    expected_status: str,
    *,
    expected_error_kind: str | None = None,
) -> None:
    """Validate the envelope's ``run_status`` matches a terminal value.

    ``expected_status`` itself must be one of the terminal statuses.
    When ``expected_error_kind`` is given, it must match the envelope's
    ``error_kind``.
    """
    _require_dict(envelope, "envelope")
    if expected_status not in _TERMINAL_STATUSES:
        raise HarnessAssertionError(
            f"expected_status {expected_status!r} must be terminal "
            f"(one of {sorted(_TERMINAL_STATUSES)})"
        )
    actual = envelope.get("run_status")
    if actual != expected_status:
        raise HarnessAssertionError(
            f"run_status mismatch: expected {expected_status!r}, "
            f"got {actual!r}"
        )
    if expected_error_kind is not None:
        actual_kind = envelope.get("error_kind")
        if actual_kind != expected_error_kind:
            raise HarnessAssertionError(
                f"error_kind mismatch: expected {expected_error_kind!r}, "
                f"got {actual_kind!r}"
            )


def assert_meta_status(body: Any, expected_status: str | None) -> None:
    """Parse the agent-meta block from ``body`` and assert its status.

    Raises if no parseable agent-meta block is present, or if the
    parsed ``status`` differs from ``expected_status``.
    """
    meta = agent_lib.parse_body(body)
    if meta is None:
        raise HarnessAssertionError("no parseable agent-meta block in body")
    actual = meta.get("status")
    if actual != expected_status:
        raise HarnessAssertionError(
            f"agent-meta status mismatch: expected {expected_status!r}, "
            f"got {actual!r}"
        )


def assert_summary_matches(
    summary: Any,
    expected_subset: Any,
) -> None:
    """Assert every key in ``expected_subset`` is in ``summary`` and equal."""
    _require_dict(summary, "summary")
    _require_dict(expected_subset, "expected_subset")
    for key, want in expected_subset.items():
        if key not in summary:
            raise HarnessAssertionError(
                f"summary missing required key {key!r}"
            )
        got = summary[key]
        if got != want:
            raise HarnessAssertionError(
                f"summary[{key!r}] mismatch: expected {want!r}, got {got!r}"
            )


def assert_pr_merged(pr: Any) -> None:
    """Raise if the pull request dict is not merged."""
    _require_dict(pr, "pr")
    if not pr.get("merged"):
        raise HarnessAssertionError(
            f"PR #{pr.get('number')} not merged "
            f"(state={pr.get('state')!r})"
        )


__all__ = [
    "HarnessAssertionError",
    "assert_envelope_terminal",
    "assert_issue_has_label",
    "assert_issue_locked",
    "assert_meta_status",
    "assert_pr_merged",
    "assert_summary_matches",
]
