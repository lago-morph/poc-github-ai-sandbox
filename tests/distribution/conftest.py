"""Shared fixtures for tests/distribution/.

Exposes the POC root, the pipeline-skills-package source root, the
bundle output dir, and constants used across the contract tests.
"""

from __future__ import annotations

import hashlib
import re
import tarfile
from pathlib import Path

import pytest

POC_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = POC_ROOT / "pipeline-skills-package"
BUNDLE_DIST = PACKAGE_ROOT / "bootstrap" / "dist"

DISTRIBUTABLE_SKILLS = (
    "batch-job",
    "task-dag",
    "orchestrate-issue",
    "onboarding",
    "composition-guide",
)

# Skills whose package bundles target-repo templates.
SKILLS_WITH_TEMPLATES = ("batch-job", "task-dag", "orchestrate-issue", "onboarding")


@pytest.fixture(scope="session")
def poc_root() -> Path:
    return POC_ROOT


@pytest.fixture(scope="session")
def package_root() -> Path:
    return PACKAGE_ROOT


@pytest.fixture(scope="session")
def bundle_dist() -> Path:
    return BUNDLE_DIST


@pytest.fixture(scope="session")
def manifest_entries() -> list[tuple[str, int, str]]:
    """Return parsed MANIFEST.txt entries as (sha256, size, bundle_path)."""
    path = BUNDLE_DIST / "MANIFEST.txt"
    if not path.exists():
        pytest.skip("Bundle MANIFEST.txt not built yet")
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        digest, size_s, bundle = parts
        out.append((digest, int(size_s), bundle))
    return out


@pytest.fixture(scope="session")
def tarball_path() -> Path:
    path = BUNDLE_DIST / "pipeline-skills-package.tar.gz"
    if not path.exists():
        pytest.skip("Bundle tarball not built yet")
    return path


@pytest.fixture(scope="session")
def recipe_path() -> Path:
    path = BUNDLE_DIST / "install.md"
    if not path.exists():
        pytest.skip("Bundle recipe install.md not built yet")
    return path


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# Pattern for parsing the recipe's `### <path>` headers + fenced
# code blocks. The fence delimiter may be `\`\`\`` or longer (the
# build script uses longer fences when a file contains backticks).
_HEADER_RE = re.compile(r"^### (.+)$", re.MULTILINE)


def parse_recipe(recipe_text: str) -> dict[str, str]:
    """Parse the recipe Markdown's Section 4 into {bundle_path: content}.

    The Section 4 inlined-files format is:
        ### <path>
        <blank line>
        ```text
        <verbatim contents>
        ```

    The leading `### ` headers appear in many sections of the recipe
    (it inlines install.md too). We restrict to headers that look like
    paths (contain a slash OR end in a known top-level filename)."""
    out: dict[str, str] = {}
    lines = recipe_text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = _HEADER_RE.match(line)
        if not m:
            i += 1
            continue
        candidate = m.group(1).strip()
        if not _looks_like_bundle_path(candidate):
            i += 1
            continue
        j = i + 1
        # skip blank lines until a fence
        while j < n and not lines[j].lstrip().startswith("```"):
            if lines[j].strip():
                break
            j += 1
        if j >= n or not lines[j].lstrip().startswith("```"):
            i += 1
            continue
        fence_line = lines[j].lstrip()
        fence = "`" * (len(fence_line) - len(fence_line.lstrip("`")))
        content_lines: list[str] = []
        k = j + 1
        while k < n and lines[k] != fence:
            content_lines.append(lines[k])
            k += 1
        content = "\n".join(content_lines)
        out[candidate] = content
        i = k + 1
    return out


_TOP_FILES = {"NEW-REPO-PLAN.md", "TESTING-IN-POC.md"}


def _looks_like_bundle_path(s: str) -> bool:
    if s in _TOP_FILES:
        return True
    if "/" not in s:
        return False
    # Section headers in install.md sometimes look like `### Section ...`
    if s.startswith("Section "):
        return False
    return True


__all__ = [
    "DISTRIBUTABLE_SKILLS",
    "SKILLS_WITH_TEMPLATES",
    "parse_recipe",
    "sha256_of",
]
