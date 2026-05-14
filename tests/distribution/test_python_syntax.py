"""test_python_syntax — every bundled .py file parses (ast)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from .conftest import PACKAGE_ROOT


def _python_paths():
    out = []
    for p in sorted(PACKAGE_ROOT.rglob("*.py")):
        rel = p.relative_to(PACKAGE_ROOT).as_posix()
        if rel.startswith("runs/") or rel.startswith("bootstrap/dist/"):
            continue
        if "__pycache__" in rel.split("/"):
            continue
        # We test the build script separately if desired, but it lives
        # outside the bundle's content so skipping it keeps this scope clean.
        if rel == "bootstrap/build.py":
            continue
        out.append(p)
    return out


PYTHON_PATHS = _python_paths()


@pytest.mark.parametrize("py_path", PYTHON_PATHS, ids=lambda p: p.relative_to(PACKAGE_ROOT).as_posix())
def test_python_file_parses(py_path: Path):
    src = py_path.read_text(encoding="utf-8")
    ast.parse(src, filename=str(py_path))


def test_we_found_some_python_files():
    assert len(PYTHON_PATHS) > 0, "Expected at least one bundled .py"
