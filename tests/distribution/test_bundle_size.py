"""test_bundle_size — bundle stays under reasonable caps."""

from __future__ import annotations

from pathlib import Path

SOFT_CAP_BYTES = 10 * 1024 * 1024  # 10 MiB
HARD_CAP_BYTES = 50 * 1024 * 1024  # 50 MiB


def test_total_bundle_size_under_hard_cap(manifest_entries):
    total = sum(size for _digest, size, _bundle in manifest_entries)
    assert total < HARD_CAP_BYTES, (
        f"Bundle total content size {total} exceeds hard cap {HARD_CAP_BYTES}"
    )


def test_tarball_under_hard_cap(tarball_path: Path):
    size = tarball_path.stat().st_size
    assert size < HARD_CAP_BYTES, (
        f"Tarball size {size} exceeds hard cap {HARD_CAP_BYTES}"
    )


def test_recipe_under_hard_cap(recipe_path: Path):
    size = recipe_path.stat().st_size
    assert size < HARD_CAP_BYTES, (
        f"Recipe size {size} exceeds hard cap {HARD_CAP_BYTES}"
    )


def test_bundle_warn_soft_cap(manifest_entries):
    """Pass; emit a warning via assertion message if soft cap exceeded."""
    total = sum(size for _digest, size, _bundle in manifest_entries)
    # We don't fail here — just leave a visible signal in test output.
    if total >= SOFT_CAP_BYTES:
        import warnings
        warnings.warn(f"Bundle size {total} exceeds soft cap {SOFT_CAP_BYTES}")
