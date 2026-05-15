"""test_self_extracting_installer — install.py is the primary install path.

These tests gate the self-extracting Python installer at
`bootstrap/dist/install.py`:

- it exists, compiles, and exposes the expected metadata constants
- its embedded payload's sha256 + byte-count match the sibling tarball
- its FILE_COUNT matches MANIFEST.txt
- `--verify-only` succeeds
- `--list` matches the manifest's bundle paths
- extracting to a tmp dir produces a tree byte-identical to extracting
  the sibling tarball directly
- it is idempotent on second run (zero writes)
- it refuses to overwrite differing files without --force, and exits 3
- it overwrites correctly under --force
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from .conftest import BUNDLE_DIST, sha256_of


INSTALLER_PATH = BUNDLE_DIST / "install.py"


@pytest.fixture(scope="session")
def installer_path() -> Path:
    if not INSTALLER_PATH.exists():
        pytest.skip("install.py not built yet")
    return INSTALLER_PATH


@pytest.fixture(scope="session")
def installer_constants(installer_path: Path) -> dict:
    """Parse install.py's module-level assignments without executing it."""
    tree = ast.parse(installer_path.read_text(encoding="utf-8"))
    out: dict = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name in {"BUNDLE_NAME", "GENERATED_AT", "FILE_COUNT",
                    "TARBALL_BYTES", "TARBALL_SHA256", "TARBALL_BASE64"}:
            try:
                out[name] = ast.literal_eval(node.value)
            except ValueError:
                # TARBALL_BASE64 is a joined string concat; literal_eval still works
                # for plain string literals.
                pass
    return out


def test_installer_compiles(installer_path: Path):
    text = installer_path.read_text(encoding="utf-8")
    compile(text, str(installer_path), "exec")


def test_installer_exposes_required_constants(installer_constants: dict):
    for key in ("BUNDLE_NAME", "GENERATED_AT", "FILE_COUNT",
                "TARBALL_BYTES", "TARBALL_SHA256", "TARBALL_BASE64"):
        assert key in installer_constants, f"installer missing constant {key}"
    assert installer_constants["BUNDLE_NAME"] == "pipeline-skills-package"
    assert isinstance(installer_constants["FILE_COUNT"], int)
    assert installer_constants["FILE_COUNT"] > 0
    assert len(installer_constants["TARBALL_SHA256"]) == 64


def test_installer_payload_matches_sibling_tarball(installer_constants: dict, tarball_path: Path):
    tarball_bytes = tarball_path.read_bytes()
    assert installer_constants["TARBALL_BYTES"] == len(tarball_bytes), (
        "embedded TARBALL_BYTES does not match dist tarball size"
    )
    expected_sha = hashlib.sha256(tarball_bytes).hexdigest()
    assert installer_constants["TARBALL_SHA256"] == expected_sha, (
        "embedded TARBALL_SHA256 does not match dist tarball sha256"
    )


def test_installer_file_count_matches_manifest(installer_constants: dict,
                                                manifest_entries: list):
    assert installer_constants["FILE_COUNT"] == len(manifest_entries)


def test_installer_verify_only_succeeds(installer_path: Path):
    result = subprocess.run(
        [sys.executable, str(installer_path), "--verify-only"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"--verify-only failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "integrity:    OK" in result.stdout


def test_installer_list_matches_manifest(installer_path: Path, manifest_entries: list):
    result = subprocess.run(
        [sys.executable, str(installer_path), "--list"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    # Each path is printed on its own line with no leading whitespace.
    # Filter out the header banner ("pipeline-skills-package installer",
    # "  generated_at: ...", etc.) by keeping only non-indented lines
    # that look like file paths (no colons, which header lines all have).
    listed = {
        line for line in result.stdout.splitlines()
        if line and line == line.lstrip() and ":" not in line
        and not line.startswith("pipeline-skills-package")
    }
    manifest_paths = {bundle for _digest, _size, bundle in manifest_entries}
    assert listed == manifest_paths, (
        f"installer --list output differs from manifest. "
        f"only-in-list: {sorted(listed - manifest_paths)[:5]}; "
        f"only-in-manifest: {sorted(manifest_paths - listed)[:5]}"
    )


def _walk(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): sha256_of(p)
        for p in root.rglob("*") if p.is_file()
    }


def _extract_tarball(tarball_path: Path, dest: Path) -> None:
    with tarfile.open(tarball_path, "r:gz") as tar:
        tar.extractall(dest)


def test_installer_extract_matches_tarball_extract(installer_path: Path,
                                                   tarball_path: Path,
                                                   tmp_path: Path):
    via_installer = tmp_path / "via-installer"
    via_tar = tmp_path / "via-tar"
    via_installer.mkdir()
    via_tar.mkdir()

    result = subprocess.run(
        [sys.executable, str(installer_path), "--target", str(via_installer)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"install failed: {result.stderr}"

    _extract_tarball(tarball_path, via_tar)

    installer_map = _walk(via_installer)
    tar_map = _walk(via_tar)

    assert set(installer_map) == set(tar_map), (
        f"installer/tarball file sets differ. "
        f"only-in-installer: {sorted(set(installer_map) - set(tar_map))[:5]}; "
        f"only-in-tar: {sorted(set(tar_map) - set(installer_map))[:5]}"
    )
    mismatches = [k for k in installer_map if installer_map[k] != tar_map[k]]
    assert not mismatches, f"content mismatch on: {mismatches[:5]}"


def test_installer_is_idempotent(installer_path: Path, tmp_path: Path):
    target = tmp_path / "idem"
    target.mkdir()
    # First run.
    r1 = subprocess.run(
        [sys.executable, str(installer_path), "--target", str(target)],
        capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0
    assert "wrote:        " in r1.stdout
    # Second run on the populated target.
    r2 = subprocess.run(
        [sys.executable, str(installer_path), "--target", str(target)],
        capture_output=True, text=True, timeout=60,
    )
    assert r2.returncode == 0, f"idempotent re-run failed: {r2.stderr}"
    assert "wrote:        0 file(s)" in r2.stdout, (
        f"second run was not idempotent. stdout={r2.stdout}"
    )


def test_installer_refuses_conflicting_overwrite(installer_path: Path, tmp_path: Path):
    target = tmp_path / "conflict"
    target.mkdir()
    r1 = subprocess.run(
        [sys.executable, str(installer_path), "--target", str(target)],
        capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0

    # Tamper with one extracted file.
    tampered = target / "bootstrap" / "install.md"
    assert tampered.exists()
    tampered.write_text("tampered content\n", encoding="utf-8")

    r2 = subprocess.run(
        [sys.executable, str(installer_path), "--target", str(target)],
        capture_output=True, text=True, timeout=60,
    )
    assert r2.returncode == 3, (
        f"expected exit 3 on conflict, got {r2.returncode}. "
        f"stdout={r2.stdout!r} stderr={r2.stderr!r}"
    )
    assert "Refusing to overwrite" in r2.stderr
    # Content remains tampered (no write happened).
    assert tampered.read_text() == "tampered content\n"


def test_installer_force_overwrites_conflicts(installer_path: Path, tmp_path: Path):
    target = tmp_path / "force"
    target.mkdir()
    subprocess.run(
        [sys.executable, str(installer_path), "--target", str(target)],
        capture_output=True, text=True, timeout=60, check=True,
    )
    tampered = target / "bootstrap" / "install.md"
    original = tampered.read_text(encoding="utf-8")
    tampered.write_text("tampered\n", encoding="utf-8")

    r = subprocess.run(
        [sys.executable, str(installer_path), "--target", str(target), "--force"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, f"--force run failed: {r.stderr}"
    assert tampered.read_text(encoding="utf-8") == original
