"""test_archetype_manifests — test-harness archetypes have valid manifests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .conftest import PACKAGE_ROOT


ARCHETYPES_ROOT = PACKAGE_ROOT / "test-harness" / "archetypes"
EXPECTED_ARCHETYPES = {
    "blank-repo",
    "python-gha-with-agents-md",
    "node-circleci-no-agents-md",
    "monorepo-multi-language",
    "existing-skills-conflict",
    "partial-protocol",
    "protocol-installed-not-onboarded",
    "gitlab-only",
}


def _archetype_dirs():
    if not ARCHETYPES_ROOT.is_dir():
        return []
    return sorted(p for p in ARCHETYPES_ROOT.iterdir() if p.is_dir())


def test_archetypes_dir_exists():
    assert ARCHETYPES_ROOT.is_dir()


def test_eight_archetypes_present():
    dirs = {p.name for p in _archetype_dirs()}
    assert dirs == EXPECTED_ARCHETYPES, (
        f"unexpected archetypes: extra={dirs - EXPECTED_ARCHETYPES}, "
        f"missing={EXPECTED_ARCHETYPES - dirs}"
    )


@pytest.mark.parametrize("archetype_dir", _archetype_dirs(), ids=lambda p: p.name)
def test_archetype_manifest_parses(archetype_dir: Path):
    manifest = archetype_dir / "manifest.json"
    assert manifest.is_file(), f"missing manifest: {manifest}"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    for key in ("name", "description", "expected_discovery", "files"):
        assert key in data, f"{manifest} missing key {key!r}"
    assert isinstance(data["expected_discovery"], dict)
    assert isinstance(data["files"], list)


@pytest.mark.parametrize("archetype_dir", _archetype_dirs(), ids=lambda p: p.name)
def test_archetype_manifest_files_match_disk(archetype_dir: Path):
    manifest = json.loads((archetype_dir / "manifest.json").read_text(encoding="utf-8"))
    on_disk = sorted(
        p.relative_to(archetype_dir).as_posix()
        for p in archetype_dir.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    )
    declared = sorted(manifest["files"])
    assert declared == on_disk, (
        f"{archetype_dir.name}: manifest.files != on-disk content\n"
        f"  declared={declared}\n"
        f"  on_disk ={on_disk}"
    )
