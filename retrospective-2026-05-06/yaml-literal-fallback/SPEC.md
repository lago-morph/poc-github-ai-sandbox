# SPEC: `yaml-literal-fallback`

## Trigger conditions

### Direct triggers — activate immediately

- "Set up vars for the new repo."
- "Why isn't the workflow firing?"
- "Move this from a literal to a repo variable."
- A code review where someone is removing a hardcoded login or other identity in favor of `vars.X`.

### Proactive triggers — offer the skill without being asked

Offer when reviewing any change that:

- Adds `${{ vars.X }}` to an `if:` clause or `env:` block in a workflow YAML.
- Removes a literal value (login, label name, branch name) from a workflow in favor of a variable read.
- Documents a new GHA repo variable as a deployment requirement.

Do NOT offer for:
- Variables where there is genuinely no sensible default (e.g., a per-user secret with no shared canonical value).
- Workflows that intentionally fail-loud when a variable is missing (e.g., a deployment safety check).

## Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `variable_name` | (required) | The `vars.X` name being read. |
| `canonical_default` | (required) | The known-good literal value for the canonical / reference deployment. |
| `applies_to` | `["if-clause", "env-block"]` | Where in the YAML the fallback must appear. |
| `pin_in_tests` | `true` | Whether to add a unit test asserting the literal pattern. |

## Outputs

- An updated workflow YAML using `${{ vars.X || 'canonical_default' }}`.
- Unit tests pinning the literal pattern in the YAML file.
- A new "don't remove" rule in `AGENTS.md` (or HANDOFF.md "Things the next agent should NOT do").
- A SPEC note documenting the contract: which value wins when both are set, and when admin should set the variable.

## Workflow steps

1. **Identify all read sites.** `grep -rn "vars.${VARIABLE_NAME}" .github/workflows/` shows every YAML location that reads the variable. Often there are two per workflow (`if:` clause + `env:` block).

2. **Apply the fallback in each location.** Replace `${{ vars.X }}` with `${{ vars.X || 'canonical_default' }}`. In `if:` clauses, parenthesize for grouping if combining with other expressions: `==  (vars.X || 'literal')`.

3. **Pin the literal in unit tests.** Add a test that reads each YAML as plain text and asserts the literal substring `"vars.X ||"` is present. Plain-text assertions are sufficient — no need to YAML-parse, and a `||` substring match catches the fallback shape.

4. **Document the contract.** In SPEC.md (or equivalent project doc) add a section explaining:
   - Which value wins when both `vars.X` and the literal are present (vars wins when non-empty).
   - When to set `vars.X` (multi-deployment scenarios where multiple bots/accounts share this protocol).
   - Why the literal exists (deployment friction / new-user experience).

5. **Add the "don't remove" rule.** Update `AGENTS.md` or `HANDOFF.md` "Things the next agent should NOT do" with a one-liner: "Don't remove the YAML literal fallback in workflow YAMLs. The literal is the deployment-friction safety net; new deployments override by setting `vars.X` instead."

6. **Verify with live drive (optional but valuable).** Drive the simplest happy-path live scenario after deployment to confirm the fallback works. Per `live-test-after-substantive-merge`, this is the only way to catch the silent-break failure mode.

## Templates

### YAML — `if:` clause with fallback

```yaml
jobs:
  handle:
    if: |
      contains(github.event.issue.labels.*.name, 'agent-task') &&
      github.event.comment.user.login == (vars.AGENT_LOGIN || 'jonathanmanton')
```

### YAML — `env:` block with fallback

```yaml
- run: python .agent/scripts/handler.py
  env:
    AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}
```

### Unit test pinning the literal

```python
import pytest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"

@pytest.mark.parametrize("name", [
    "lock-and-sweep.yml",
    "batch-job-handler.yml",
    "close-on-merge.yml",
])
def test_workflow_provides_agent_login_env_with_fallback(name):
    text = (WORKFLOWS / name).read_text(encoding="utf-8")
    assert "AGENT_LOGIN:" in text, (
        f"{name} must pass AGENT_LOGIN env var to its script step"
    )
    assert "vars.AGENT_LOGIN ||" in text, (
        f"{name} must use a fallback like "
        f"`${{{{ vars.AGENT_LOGIN || 'jonathanmanton' }}}}`"
    )
```

### `AGENTS.md` rule (suggested)

> N. **Don't remove the YAML literal fallback.**
> "Don't remove `${{ vars.X || 'literal' }}` expressions from workflow files. The literal is the deployment-friction safety net for the canonical repo. New deployments override by setting `vars.X`."
> *Grounded in: PR #56's deployment-friction bug — a fallback-free workflow silently exits 1 on unset env var.*

## Anti-patterns

- **Removing the fallback during a "let's clean this up" refactor.** Future you will not remember why it was there. The unit tests + AGENTS.md rule + this SPEC exist precisely to defeat this temptation.
- **Hardcoding the literal in multiple YAML files without a shared variable name.** Increases drift risk. If the canonical repo's identity ever changes, every YAML needs an edit.
- **Treating a fresh deployment as "broken" when the variable isn't set.** A new repo should produce useful behavior out of the box. The fallback is the mechanism.
- **Setting the literal to a placeholder ("my-bot", "TODO", "<set this>").** Defeats the purpose. The literal must be the canonical repo's actual known-good value.
- **Pinning the literal with regex that's too specific.** A regex like `r"vars\.AGENT_LOGIN \|\| 'jonathanmanton'"` will fail if someone changes the literal to a different valid login. A substring match on `"vars.AGENT_LOGIN ||"` is more flexible — it asserts "fallback exists" without dictating its value.

## Implementation notes

- This pattern is GHA-specific (the `||` operator is GHA expression syntax). The general principle (deployment-friction-safe defaults) translates to other CI systems but the syntax differs.
- For non-GHA systems, prefer reading the variable in a setup script with a `default=...` argument, then exporting it. The end goal is the same: missing variable produces the canonical default, not silent failure.
- The skill is small but high-value: a one-line YAML change prevents an entire class of silent-break deployment bugs.

## Test plan

- 1 test per workflow YAML pinning the fallback substring (3 in this repo).
- 1 test pinning the `if:` clause if the workflow gates on a variable.
- All tests should run as part of the standard suite (`tests/unit/test_workflow_yamls.py`).

## Living document

Amend this spec when:
- A new YAML location starts reading the variable (add a test).
- The canonical repo's literal value changes (update both YAML and tests).
- A new repo variable is introduced and the fallback pattern is applied.

Provenance: PR #56 — added `${{ vars.AGENT_LOGIN || 'jonathanmanton' }}`
to all three workflow YAMLs and pinned the literal in
`tests/unit/test_workflow_yamls.py`. Live discovery in scenario 01
first attempt (issue #55), which stalled because `vars.AGENT_LOGIN`
was unset on the canonical repo.
