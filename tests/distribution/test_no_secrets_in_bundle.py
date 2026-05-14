"""test_no_secrets_in_bundle — smoke scan for common secret shapes.

Patterns target the obvious leak shapes: GitHub PATs, AWS keys, JWTs,
RSA private key headers, and assignment-style secrets like
``password = "..."``. False positives are allowed for fixture content
that explicitly looks like schema examples or test-only placeholders.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from .conftest import PACKAGE_ROOT

PATTERNS = [
    (re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "PRIVATE KEY header"),
    (re.compile(rb"ghp_[A-Za-z0-9]{36,}"), "GitHub PAT (ghp_)"),
    (re.compile(rb"github_pat_[A-Za-z0-9_]{82,}"), "GitHub fine-grained PAT"),
    (re.compile(rb"gho_[A-Za-z0-9]{36,}"), "GitHub OAuth token"),
    (re.compile(rb"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(rb"AIza[0-9A-Za-z\\-_]{35}"), "Google API key"),
    (re.compile(rb"xox[baprs]-[0-9A-Za-z-]{10,}"), "Slack token"),
    (re.compile(rb"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}"), "JWT"),
    (re.compile(rb"(?i)password\s*=\s*[\"'][^\"']{8,}[\"']"), "literal password assignment"),
    (re.compile(rb"(?i)api_?key\s*=\s*[\"'][^\"']{16,}[\"']"), "literal api key assignment"),
]

ALLOWLIST_FILENAMES = {
    # No allowlist needed yet; placeholder for future schema-example
    # patterns that intentionally use one of the regexes above.
}


def _iter_bundle_files():
    """Iterate over every file under pipeline-skills-package/ that would
    end up in the bundle. We use the source tree (not the tarball) so
    this test stays meaningful even if the build script changes."""
    for p in PACKAGE_ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(PACKAGE_ROOT).as_posix()
        # skip non-shipped paths
        if rel.startswith("runs/") or rel.startswith("bootstrap/dist/"):
            continue
        if rel == "bootstrap/build.py" or rel == "bootstrap/distribution-exclude.txt":
            continue
        if rel.endswith(".pyc") or "__pycache__" in rel.split("/"):
            continue
        if rel in {"PLAN-PACKAGE.md", "RESUME.md"}:
            continue
        yield p


def test_no_secret_pattern_matches():
    hits = []
    for path in _iter_bundle_files():
        rel = path.relative_to(PACKAGE_ROOT).as_posix()
        if rel in ALLOWLIST_FILENAMES:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for regex, name in PATTERNS:
            m = regex.search(data)
            if m:
                hits.append(f"{rel}: matches {name!r} at byte offset {m.start()}")
    assert not hits, "Potential secrets found in bundle:\n  " + "\n  ".join(hits)
