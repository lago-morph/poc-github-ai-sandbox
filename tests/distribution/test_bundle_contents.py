"""test_bundle_contents — MANIFEST matches tarball and recipe."""

from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path

import pytest

from .conftest import parse_recipe


def test_manifest_entries_match_tarball(manifest_entries, tarball_path: Path):
    manifest_paths = {bundle for _digest, _size, bundle in manifest_entries}
    with tarfile.open(tarball_path, "r:gz") as tar:
        tarball_paths = {m.name for m in tar.getmembers() if m.isfile()}
    only_manifest = manifest_paths - tarball_paths
    only_tarball = tarball_paths - manifest_paths
    assert not only_manifest, f"manifest entries missing from tarball: {sorted(only_manifest)[:10]}"
    assert not only_tarball, f"tarball entries missing from manifest: {sorted(only_tarball)[:10]}"


def test_manifest_sha256_matches_tarball_contents(manifest_entries, tarball_path: Path):
    by_path = {bundle: digest for digest, _size, bundle in manifest_entries}
    with tarfile.open(tarball_path, "r:gz") as tar:
        mismatches = []
        for m in tar.getmembers():
            if not m.isfile():
                continue
            fh = tar.extractfile(m)
            assert fh is not None
            digest = hashlib.sha256(fh.read()).hexdigest()
            expected = by_path.get(m.name)
            if expected != digest:
                mismatches.append(f"{m.name}: manifest={expected[:8] if expected else None} actual={digest[:8]}")
    assert not mismatches, "Manifest/tarball sha256 mismatches:\n  " + "\n  ".join(mismatches[:5])


def test_manifest_sizes_match_tarball(manifest_entries, tarball_path: Path):
    by_path = {bundle: size for _digest, size, bundle in manifest_entries}
    with tarfile.open(tarball_path, "r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            assert by_path[m.name] == m.size, f"size mismatch for {m.name}: manifest={by_path[m.name]} tar={m.size}"


def test_recipe_includes_every_manifest_path(manifest_entries, recipe_path: Path):
    recipe_files = parse_recipe(recipe_path.read_text(encoding="utf-8"))
    manifest_paths = {bundle for _digest, _size, bundle in manifest_entries}
    only_manifest = manifest_paths - set(recipe_files)
    assert not only_manifest, f"manifest paths missing from recipe: {sorted(only_manifest)[:10]}"
