"""test_template_parity — bundled templates byte-match POC source.

The most important contract test in this directory. If it fails, the
POC source has drifted from the bundled copies and the bundle is not
shippable until the build is re-run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import PACKAGE_ROOT, POC_ROOT, SKILLS_WITH_TEMPLATES, sha256_of

# Skills whose templates are byte-copies of POC source (vs skill-authored).
# Onboarding bundles only new templates (dialog skeletons, interview YAML)
# that have no POC origin.
SKILLS_WITH_POC_SOURCED_TEMPLATES = ("batch-job", "task-dag", "orchestrate-issue")


def _iter_template_files(skill: str):
    """Yield every (bundled_path, poc_source_path) pair for the given skill."""
    root = PACKAGE_ROOT / "skills" / skill / "templates"
    if not root.is_dir():
        return
    for bundled in sorted(root.rglob("*")):
        if not bundled.is_file():
            continue
        rel = bundled.relative_to(root).as_posix()
        # Map templates/agent/<rest>  -> .agent/<rest>
        # Map templates/github/<rest> -> .github/<rest>
        first, _, rest = rel.partition("/")
        if first == "agent":
            poc = POC_ROOT / ".agent" / rest
        elif first == "github":
            poc = POC_ROOT / ".github" / rest
        else:
            poc = None
        yield bundled, poc


@pytest.mark.parametrize("skill", SKILLS_WITH_TEMPLATES)
def test_each_skill_has_templates_dir(skill: str):
    assert (PACKAGE_ROOT / "skills" / skill / "templates").is_dir()


@pytest.mark.parametrize("skill", SKILLS_WITH_POC_SOURCED_TEMPLATES)
def test_template_files_byte_match_poc_source(skill: str):
    failures: list[str] = []
    checked = 0
    for bundled, poc in _iter_template_files(skill):
        if poc is None:
            # Skill-internal assets like brief-template.md (orchestrate-issue);
            # not derived from POC source — skipped by this test.
            continue
        if not poc.exists():
            failures.append(f"missing POC source for bundled file: {bundled} (expected {poc})")
            continue
        if sha256_of(bundled) != sha256_of(poc):
            failures.append(f"byte mismatch: {bundled} vs {poc}")
        checked += 1
    assert not failures, "Template parity failures:\n  " + "\n  ".join(failures)
    assert checked > 0, f"No POC-sourced templates found under {skill}/templates/"


def test_shared_templates_match_across_skills():
    """Files that appear in multiple skill packages must be byte-identical."""
    by_relpath: dict[str, list[Path]] = {}
    for skill in SKILLS_WITH_TEMPLATES:
        root = PACKAGE_ROOT / "skills" / skill / "templates"
        for bundled in root.rglob("*"):
            if not bundled.is_file():
                continue
            rel = bundled.relative_to(root).as_posix()
            by_relpath.setdefault(rel, []).append(bundled)
    mismatches: list[str] = []
    for rel, copies in by_relpath.items():
        if len(copies) < 2:
            continue
        digests = {sha256_of(p): p for p in copies}
        if len(digests) > 1:
            mismatches.append(
                f"{rel}: {len(digests)} distinct copies — " + ", ".join(
                    f"{d[:8]}={p.relative_to(PACKAGE_ROOT)}" for d, p in digests.items()
                )
            )
    assert not mismatches, "Cross-skill template drift:\n  " + "\n  ".join(mismatches)
