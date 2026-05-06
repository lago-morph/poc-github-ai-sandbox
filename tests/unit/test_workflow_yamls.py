"""Tests pinning the workflow YAML files to required deployment shapes.

These are read-only sanity checks: they parse the YAML as plain text
(no PyYAML dependency required) and assert that critical strings are
present. Caught a real deployment failure: vars.AGENT_LOGIN must have
a YAML-level fallback so workflows still function on repos where the
admin hasn't set the GitHub Actions repo variable.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


# ---------------------------------------------------------------------------
# AGENT_LOGIN fallback (deployment friction fix)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "lock-and-sweep.yml",
    "batch-job-handler.yml",
    "close-on-merge.yml",
])
def test_workflow_provides_agent_login_env_with_fallback(name):
    """Each workflow that runs a script must pass AGENT_LOGIN as an env
    var, with a YAML-level fallback so deployments don't silently break
    when ``vars.AGENT_LOGIN`` is not set.

    The fallback uses GHA's `||` expression: ``vars.AGENT_LOGIN ||
    'jonathanmanton'``. When ``vars.AGENT_LOGIN`` is set, it wins; when
    not, the literal default keeps the protocol functional for the
    poc-github-ai-sandbox deployment.
    """
    path = WORKFLOWS / name
    text = path.read_text(encoding="utf-8")
    assert "AGENT_LOGIN:" in text, (
        f"{name} must pass AGENT_LOGIN env var to its script step "
        f"(see SPEC §3.1)"
    )
    assert "vars.AGENT_LOGIN ||" in text, (
        f"{name} must use a fallback like "
        f"`${{{{ vars.AGENT_LOGIN || 'jonathanmanton' }}}}` so the "
        f"workflow keeps working when the repo variable is unset. "
        f"Without this, lock-and-sweep silently exits 1 on missing "
        f"AGENT_LOGIN and the issue never gets labeled."
    )


def test_batch_job_handler_if_clause_uses_agent_login_fallback():
    """The if-clause in batch-job-handler.yml gates the entire job. If
    `vars.AGENT_LOGIN` is unset, the comparison `comment.user.login ==
    null` is false and the workflow never fires on any comment. The
    fallback ensures the comparison is meaningful.
    """
    path = WORKFLOWS / "batch-job-handler.yml"
    text = path.read_text(encoding="utf-8")
    # Find the if: clause
    assert "github.event.comment.user.login ==" in text
    # Either it uses the fallback expression or a literal — both work for
    # the deployment but the fallback is the documented design.
    assert (
        "vars.AGENT_LOGIN ||" in text
        or "github.event.comment.user.login == 'jonathanmanton'" in text
    ), (
        "batch-job-handler.yml's `if:` must compare comment.user.login "
        "against a non-null value. Use `vars.AGENT_LOGIN || 'jonathanmanton'`."
    )
