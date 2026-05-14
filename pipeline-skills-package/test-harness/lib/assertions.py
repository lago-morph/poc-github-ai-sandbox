"""Pure assertions used by scenarios in the test-harness.

These mirror the spirit of ``harness/lib/asserts.py`` in the POC but
target the development-only harness's needs: archetype-shape
verification, dialog-file inspection, scenario phase post-conditions.

Each ``assert_*`` helper raises :class:`HarnessAssertionError` (a
subclass of :class:`AssertionError`) on failure so pytest treats it
as a regular assertion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class HarnessAssertionError(AssertionError):
    """Raised when a harness predicate fails."""


def assert_file_exists(path: Path) -> None:
    """Raise if ``path`` does not exist as a regular file."""
    if not path.is_file():
        raise HarnessAssertionError(f"expected file does not exist: {path}")


def assert_file_absent(path: Path) -> None:
    """Raise if ``path`` exists."""
    if path.exists():
        raise HarnessAssertionError(f"expected file to be absent: {path}")


def assert_yaml_parses(path: Path) -> Any:
    """Parse ``path`` as YAML; raise if it does not parse."""
    assert_file_exists(path)
    try:
        with path.open("r", encoding="utf-8") as fp:
            return yaml.safe_load(fp)
    except yaml.YAMLError as exc:
        raise HarnessAssertionError(f"YAML parse failed for {path}: {exc}") from exc


def assert_json_parses(path: Path) -> Any:
    """Parse ``path`` as JSON; raise if it does not parse."""
    assert_file_exists(path)
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError as exc:
        raise HarnessAssertionError(f"JSON parse failed for {path}: {exc}") from exc


def assert_dialog_questions_answered_count(
    dialog_path: Path,
    expected_count: int,
) -> None:
    """Assert the dialog file at ``dialog_path`` has exactly ``expected_count``
    answered questions.

    A "question" is identified by an ``H3 (###)`` heading; an "answered"
    question is one whose section contains at least one non-empty
    response body line. This is a deliberately loose definition — the
    real onboarding skill will provide a stricter parser; scenarios use
    this stub to verify rough counts.
    """
    assert_file_exists(dialog_path)
    text = dialog_path.read_text(encoding="utf-8")
    answered = 0
    in_section = False
    has_answer = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_section and has_answer:
                answered += 1
            in_section = True
            has_answer = False
            continue
        if in_section and stripped and not stripped.startswith("#"):
            has_answer = True
    if in_section and has_answer:
        answered += 1
    if answered != expected_count:
        raise HarnessAssertionError(
            f"dialog {dialog_path}: expected {expected_count} answered "
            f"questions, found {answered}"
        )


def assert_dialog_questions_answered_at_least(
    dialog_path: Path,
    minimum: int,
) -> None:
    """Like :func:`assert_dialog_questions_answered_count` but requires
    at least ``minimum`` answered questions."""
    assert_file_exists(dialog_path)
    text = dialog_path.read_text(encoding="utf-8")
    answered = 0
    in_section = False
    has_answer = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_section and has_answer:
                answered += 1
            in_section = True
            has_answer = False
            continue
        if in_section and stripped and not stripped.startswith("#"):
            has_answer = True
    if in_section and has_answer:
        answered += 1
    if answered < minimum:
        raise HarnessAssertionError(
            f"dialog {dialog_path}: expected at least {minimum} answered "
            f"questions, found {answered}"
        )


def assert_directory_contains(parent: Path, relative: str) -> None:
    """Assert ``parent / relative`` exists (file or directory)."""
    candidate = parent / relative
    if not candidate.exists():
        raise HarnessAssertionError(f"missing entry {relative!r} under {parent}")


def assert_keys_present(payload: dict[str, Any], keys: list[str]) -> None:
    """Assert every key in ``keys`` is present in ``payload``."""
    if not isinstance(payload, dict):
        raise HarnessAssertionError(f"expected dict, got {type(payload).__name__}")
    missing = [k for k in keys if k not in payload]
    if missing:
        raise HarnessAssertionError(f"missing keys {missing} in payload")


__all__ = [
    "HarnessAssertionError",
    "assert_dialog_questions_answered_at_least",
    "assert_dialog_questions_answered_count",
    "assert_directory_contains",
    "assert_file_absent",
    "assert_file_exists",
    "assert_json_parses",
    "assert_keys_present",
    "assert_yaml_parses",
]
