"""test_recipe_idempotent — apply the recipe twice; second run is a no-op."""

from __future__ import annotations

import filecmp
from pathlib import Path

import pytest

from .conftest import parse_recipe


def _apply_recipe(files: dict[str, str], target: Path) -> dict[str, list[str]]:
    """Apply the recipe to target/. Returns report with 'written' and 'skipped'."""
    report = {"written": [], "skipped": []}
    for bundle_path, content in files.items():
        dest = target / bundle_path
        if dest.exists() and dest.read_text(encoding="utf-8") == content:
            report["skipped"].append(bundle_path)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        report["written"].append(bundle_path)
    return report


def test_recipe_apply_then_apply_is_noop_second_time(tmp_path: Path, recipe_path: Path):
    files = parse_recipe(recipe_path.read_text(encoding="utf-8"))
    assert files, "recipe parsed zero file entries"
    first = _apply_recipe(files, tmp_path / "first")
    (tmp_path / "first").mkdir(exist_ok=True)
    target = tmp_path / "second"
    target.mkdir()
    initial = _apply_recipe(files, target)
    second = _apply_recipe(files, target)
    assert initial["written"], "first recipe application wrote nothing"
    assert not second["written"], (
        "second recipe application wrote files (should be idempotent): "
        + ", ".join(second["written"][:10])
    )
    assert len(second["skipped"]) == len(files), (
        f"Expected all {len(files)} files skipped on second pass; got {len(second['skipped'])}"
    )


def test_recipe_partial_state_resumes_cleanly(tmp_path: Path, recipe_path: Path):
    """Simulate an interrupted install: partial files on disk, re-apply
    should complete the rest without touching the existing ones."""
    files = parse_recipe(recipe_path.read_text(encoding="utf-8"))
    target = tmp_path / "partial"
    target.mkdir()
    # Write half the files
    half = list(files.items())[: len(files) // 2]
    for bundle_path, content in half:
        dest = target / bundle_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    # Re-apply
    report = _apply_recipe(files, target)
    # The half we wrote should be skipped; the other half should be written.
    assert len(report["skipped"]) == len(half)
    assert len(report["written"]) == len(files) - len(half)
