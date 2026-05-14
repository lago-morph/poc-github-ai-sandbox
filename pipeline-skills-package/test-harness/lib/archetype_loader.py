"""Load and materialise archetype fixture trees for the test-harness.

An archetype is a directory under ``test-harness/archetypes/<name>/``
holding a ``manifest.json`` plus the actual fixture files listed in
``manifest["files"]``. The loader knows nothing about scenarios; it
only knows how to (a) read a manifest and (b) copy a tree.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


ARCHETYPES_DIR_NAME = "archetypes"


def _archetypes_root(harness_root: Path | None = None) -> Path:
    """Return the absolute path to the archetypes directory.

    ``harness_root`` defaults to the directory containing this file's
    parent (i.e. ``test-harness/``).
    """
    if harness_root is None:
        harness_root = Path(__file__).resolve().parent.parent
    return harness_root / ARCHETYPES_DIR_NAME


def load(name: str, harness_root: Path | None = None) -> dict[str, Any]:
    """Load the manifest for archetype ``name``.

    Returns the parsed manifest dict. Raises :class:`FileNotFoundError`
    if the archetype directory or its manifest is missing, and
    :class:`ValueError` if the manifest is missing required keys.

    Contract:
      - Manifest must have keys: ``name``, ``description``,
        ``expected_discovery``, ``files``.
      - ``manifest["name"]`` must equal ``name``.
    """
    root = _archetypes_root(harness_root)
    archetype_dir = root / name
    manifest_path = archetype_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"archetype manifest not found: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as fp:
        manifest = json.load(fp)
    required = {"name", "description", "expected_discovery", "files"}
    missing = required - set(manifest)
    if missing:
        raise ValueError(
            f"archetype {name!r} manifest missing required keys: {sorted(missing)}"
        )
    if manifest["name"] != name:
        raise ValueError(
            f"archetype manifest name {manifest['name']!r} does not match "
            f"directory name {name!r}"
        )
    return manifest


def list_archetypes(harness_root: Path | None = None) -> list[str]:
    """Return the sorted list of archetype names available on disk."""
    root = _archetypes_root(harness_root)
    if not root.is_dir():
        return []
    return sorted(
        p.name for p in root.iterdir()
        if p.is_dir() and (p / "manifest.json").is_file()
    )


def materialise(
    name: str,
    target_dir: Path,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Copy archetype ``name`` into ``target_dir``.

    The archetype's ``manifest.json`` is *not* copied — only the files
    listed in ``manifest["files"]``. The target directory is created
    if it does not exist. Existing files at the target paths are
    overwritten.

    Returns the manifest dict so callers can inspect
    ``expected_discovery`` without a second load.
    """
    manifest = load(name, harness_root=harness_root)
    src_root = _archetypes_root(harness_root) / name
    target_dir.mkdir(parents=True, exist_ok=True)
    for rel in manifest["files"]:
        src = src_root / rel
        dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.is_file():
            raise FileNotFoundError(
                f"archetype {name!r} declares {rel!r} but file is missing at {src}"
            )
        shutil.copy2(src, dst)
    return manifest


__all__ = ["load", "list_archetypes", "materialise"]
