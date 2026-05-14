"""test_archive_round_trip — tarball extract matches recipe apply."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from .conftest import parse_recipe, sha256_of


def _extract(tarball_path: Path, dest: Path):
    with tarfile.open(tarball_path, "r:gz") as tar:
        for m in tar.getmembers():
            # Guard against any path traversal
            assert not m.name.startswith("/")
            assert ".." not in Path(m.name).parts
        tar.extractall(dest)


def _walk_files(root: Path) -> dict[str, str]:
    """Return {rel_path: sha256}."""
    out: dict[str, str] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        out[rel] = sha256_of(p)
    return out


def test_extract_matches_recipe_apply(tmp_path: Path, tarball_path: Path, recipe_path: Path):
    extract_dir = tmp_path / "extract"
    apply_dir = tmp_path / "apply"
    extract_dir.mkdir()
    apply_dir.mkdir()

    _extract(tarball_path, extract_dir)

    files = parse_recipe(recipe_path.read_text(encoding="utf-8"))
    assert files
    for bundle_path, content in files.items():
        dest = apply_dir / bundle_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    extract_map = _walk_files(extract_dir)
    apply_map = _walk_files(apply_dir)

    only_in_extract = set(extract_map) - set(apply_map)
    only_in_apply = set(apply_map) - set(extract_map)
    assert not only_in_extract, (
        f"Files only in tarball: {sorted(only_in_extract)[:10]}"
    )
    assert not only_in_apply, (
        f"Files only in recipe-applied tree: {sorted(only_in_apply)[:10]}"
    )

    mismatches = [
        rel for rel in extract_map
        if extract_map[rel] != apply_map[rel]
    ]
    assert not mismatches, (
        f"Content mismatch between tarball and recipe for {len(mismatches)} files: "
        + ", ".join(sorted(mismatches)[:5])
    )


def test_tarball_has_no_absolute_or_traversing_paths(tarball_path: Path):
    with tarfile.open(tarball_path, "r:gz") as tar:
        for m in tar.getmembers():
            assert not m.name.startswith("/"), f"absolute path in tarball: {m.name}"
            parts = Path(m.name).parts
            assert ".." not in parts, f"traversing path in tarball: {m.name}"


def test_tarball_entries_have_normalised_ownership(tarball_path: Path):
    """Build script should zero out uid/gid/uname/gname for reproducibility."""
    with tarfile.open(tarball_path, "r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            assert m.uid == 0, f"{m.name}: uid={m.uid}"
            assert m.gid == 0, f"{m.name}: gid={m.gid}"
            assert m.uname == "", f"{m.name}: uname={m.uname!r}"
            assert m.gname == "", f"{m.name}: gname={m.gname!r}"
