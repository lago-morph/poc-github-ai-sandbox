"""test_distribution_excludes — distribution-exclude.txt is honored."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from .conftest import PACKAGE_ROOT


EXCLUDE_FILE = PACKAGE_ROOT / "bootstrap" / "distribution-exclude.txt"


def test_exclude_file_exists():
    assert EXCLUDE_FILE.is_file()


def test_bundle_does_not_contain_runs(manifest_entries):
    for _digest, _size, bundle in manifest_entries:
        assert "runs/" not in bundle, f"bundle contains runs/ path: {bundle}"


def test_bundle_does_not_contain_build_outputs(manifest_entries):
    for _digest, _size, bundle in manifest_entries:
        assert not bundle.startswith("bootstrap/dist/"), f"bundle contains its own output: {bundle}"


def test_bundle_does_not_contain_build_py(manifest_entries):
    for _digest, _size, bundle in manifest_entries:
        # Allow .agent/commands/build.py (a POC command template)
        # but disallow bootstrap/build.py.
        assert bundle != "bootstrap/build.py"


def test_bundle_does_not_contain_distribution_exclude(manifest_entries):
    for _digest, _size, bundle in manifest_entries:
        assert bundle != "bootstrap/distribution-exclude.txt"


def test_bundle_does_not_contain_plan_package(manifest_entries):
    """PLAN-PACKAGE.md is POC-local execution detail; new repo doesn't need it."""
    for _digest, _size, bundle in manifest_entries:
        assert bundle != "PLAN-PACKAGE.md"
        assert bundle != "docs/PLAN-PACKAGE.md"


def test_bundle_does_not_contain_resume_md(manifest_entries):
    for _digest, _size, bundle in manifest_entries:
        assert bundle != "RESUME.md"
        assert bundle != "docs/RESUME.md"


def test_bundle_does_not_contain_pycache(manifest_entries):
    for _digest, _size, bundle in manifest_entries:
        assert "__pycache__" not in bundle.split("/"), f"pycache in bundle: {bundle}"
        assert not bundle.endswith(".pyc"), f"pyc in bundle: {bundle}"
