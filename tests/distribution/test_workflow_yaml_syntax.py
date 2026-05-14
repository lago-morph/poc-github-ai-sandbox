"""test_workflow_yaml_syntax — bundled GHA YAMLs parse and look sane.

Includes a regression test for PR #56 (AGENT_LOGIN fallback): every
workflow that references ``vars.AGENT_LOGIN`` must use the
``${{ vars.AGENT_LOGIN || 'jonathanmanton' }}`` fallback pattern.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from .conftest import PACKAGE_ROOT, SKILLS_WITH_TEMPLATES


def _workflow_paths():
    out = []
    for skill in SKILLS_WITH_TEMPLATES:
        wf_root = PACKAGE_ROOT / "skills" / skill / "templates" / "github" / "workflows"
        if not wf_root.is_dir():
            continue
        for p in sorted(wf_root.glob("*.yml")):
            out.append(p)
    return out


WORKFLOW_PATHS = _workflow_paths()


@pytest.mark.parametrize("wf_path", WORKFLOW_PATHS, ids=lambda p: p.relative_to(PACKAGE_ROOT).as_posix())
def test_workflow_yaml_parses(wf_path: Path):
    data = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{wf_path} did not parse as a YAML mapping"


@pytest.mark.parametrize("wf_path", WORKFLOW_PATHS, ids=lambda p: p.relative_to(PACKAGE_ROOT).as_posix())
def test_workflow_has_jobs_block(wf_path: Path):
    data = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
    assert "jobs" in data, f"{wf_path} missing 'jobs' block"
    assert isinstance(data["jobs"], dict)
    assert data["jobs"], f"{wf_path} has empty 'jobs' block"


@pytest.mark.parametrize("wf_path", WORKFLOW_PATHS, ids=lambda p: p.relative_to(PACKAGE_ROOT).as_posix())
def test_workflow_agent_login_has_fallback(wf_path: Path):
    """Regression test for PR #56: any reference to ``vars.AGENT_LOGIN`` must
    fall back to ``'jonathanmanton'`` so the workflow runs in forks that
    haven't set the repo variable."""
    text = wf_path.read_text(encoding="utf-8")
    if "vars.AGENT_LOGIN" not in text:
        pytest.skip("workflow does not reference vars.AGENT_LOGIN")
    assert "vars.AGENT_LOGIN || 'jonathanmanton'" in text, (
        f"{wf_path} references vars.AGENT_LOGIN without the documented "
        "|| 'jonathanmanton' fallback"
    )


def test_we_found_workflows():
    assert len(WORKFLOW_PATHS) > 0, "Expected at least one bundled workflow"
