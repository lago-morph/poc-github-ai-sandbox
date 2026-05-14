"""test_install_dry_run — install logic against a mock filesystem.

The four self-installing skills (batch-job, task-dag, orchestrate-issue,
onboarding) copy their bundled templates/ tree into the target repo.
We exercise that copy in dry-run form by replicating the templates/
tree to tmp_path and asserting:
  - the right files appear at the right destinations
  - re-running the copy is idempotent (no extra files written)
  - if a target file already exists with different content, the dry-run
    surfaces the conflict (we model "skip" as the chosen resolution)
"""

from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

import pytest

from .conftest import PACKAGE_ROOT


def _templates_root(skill: str) -> Path:
    return PACKAGE_ROOT / "skills" / skill / "templates"


def _apply_install(skill: str, target: Path, conflict_resolution: str = "overwrite") -> dict:
    """Mock-apply the skill's templates onto target/.

    The mapping convention (per each skill's SPEC.md "Bundled templates"):
        templates/agent/<rest>  -> target/.agent/<rest>
        templates/github/<rest> -> target/.github/<rest>

    Returns a report with lists: written, skipped, conflicted.
    """
    src_root = _templates_root(skill)
    report = {"written": [], "skipped": [], "conflicted": []}
    for src in src_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(src_root).as_posix()
        first, _, rest = rel.partition("/")
        if first == "agent":
            dest = target / ".agent" / rest
        elif first == "github":
            dest = target / ".github" / rest
        else:
            # Skill-internal asset (e.g. brief-template.md); not installed
            continue
        if dest.exists():
            if filecmp.cmp(src, dest, shallow=False):
                # byte-identical: no-op
                continue
            report["conflicted"].append(str(dest.relative_to(target)))
            if conflict_resolution == "skip":
                report["skipped"].append(str(dest.relative_to(target)))
                continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        report["written"].append(str(dest.relative_to(target)))
    return report


@pytest.mark.parametrize("skill", ["batch-job", "task-dag", "orchestrate-issue"])
def test_dry_run_install_writes_expected_files(skill: str, tmp_path: Path):
    target = tmp_path / "blank-repo"
    target.mkdir()
    report = _apply_install(skill, target)
    # At minimum, install always lays down config.json and the batch-job-handler workflow.
    assert (target / ".agent" / "config.json").is_file()
    assert (target / ".github" / "workflows" / "batch-job-handler.yml").is_file()
    assert report["written"], "install wrote zero files"
    assert not report["conflicted"]


@pytest.mark.parametrize("skill", ["batch-job", "task-dag", "orchestrate-issue"])
def test_install_is_idempotent_second_run(skill: str, tmp_path: Path):
    target = tmp_path / "blank-repo"
    target.mkdir()
    first = _apply_install(skill, target)
    second = _apply_install(skill, target)
    assert first["written"], "first install wrote nothing"
    assert not second["written"], (
        "second install wrote files (should be idempotent): " + ", ".join(second["written"])
    )
    assert not second["conflicted"]


def test_conflict_with_different_content_surfaces(tmp_path: Path):
    target = tmp_path / "with-conflict"
    target.mkdir()
    conflicted = target / ".agent" / "config.json"
    conflicted.parent.mkdir(parents=True, exist_ok=True)
    conflicted.write_text('{"protocol_version": 999, "altered": true}\n')
    report = _apply_install("batch-job", target, conflict_resolution="skip")
    assert ".agent/config.json" in report["conflicted"], (
        f"expected conflict on .agent/config.json; report={report}"
    )
    assert ".agent/config.json" in report["skipped"]
    # The pre-existing content must remain untouched.
    assert conflicted.read_text().startswith("{")
    assert "altered" in conflicted.read_text()


def test_onboarding_install_does_not_lay_down_protocol_templates(tmp_path: Path):
    """The onboarding skill's templates/ has ONLY onboarding-specific files
    (dialog template, recommendations template, interview questions). It
    must NOT install protocol templates — that is the other skills' job."""
    target = tmp_path / "blank-repo"
    target.mkdir()
    src_root = _templates_root("onboarding")
    files = [p for p in src_root.rglob("*") if p.is_file()]
    assert files, "onboarding skill bundles zero templates"
    for f in files:
        rel = f.relative_to(src_root).as_posix()
        # Onboarding-specific files live at the top of templates/
        assert "/" not in rel, (
            f"onboarding bundled unexpected nested template {rel}; "
            "protocol templates belong to batch-job/task-dag/orchestrate-issue"
        )
