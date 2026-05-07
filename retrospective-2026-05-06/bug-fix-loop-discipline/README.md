# Skill: `bug-fix-loop-discipline`

## Why this skill matters

When an e2e test surfaces a bug, the temptation is to fix the
symptom directly. The discipline is to write a **failing unit test
that would have caught the bug FIRST**, only then fix the code. This
locks the regression closed: the unit test becomes the permanent
guard that future refactors can't accidentally remove.

The pattern looks slow but it's the opposite. Each step takes a few
minutes and produces evidence that the bug is real, the fix is
correct, and the regression won't return. Without the discipline,
fixes become snowflakes — they work once, regress in six months,
and nobody remembers why.

This is one of the highest-ROI patterns for stability over time.

## When it would have helped

**Session 3, two bugs, two clean fix loops:**

### Bug #1 — `vars.AGENT_LOGIN` unset (PR #56)

1. **Hypothesis:** `vars.AGENT_LOGIN` not set on canonical repo →
   workflow YAML reads empty → script exits 1 silently.
2. **Failing test:** `test_workflow_yamls.py` asserts the literal
   fallback `vars.AGENT_LOGIN ||` is present in each YAML. Tests
   fail on the unfixed code (literal not present).
3. **Fix:** add `${{ vars.AGENT_LOGIN || 'jonathanmanton' }}` to
   each YAML.
4. **Tests pass.** 4 new tests; full suite 437 → 441.
5. **Re-run live:** scenario 01 retry (issue #57) — labeled in 30s,
   completed in 3 minutes. Bug closed.

### Bug #2 — `_retry_put` no-backoff race (PR #68)

1. **Hypothesis:** `_retry_put` retried without delay → 3 concurrent
   writers raced in the same microsecond window → all retries
   exhausted before any could settle.
2. **Failing tests:** 5 tests covering retry behavior; 2 fail on the
   unfixed code (no backoff schedule, default retries=3 not ≥5).
3. **Fix:** jittered exponential backoff + retries 3→6 + indirected sleep.
4. **Tests pass.** Full suite 437 → 446.
5. **Re-run live:** scenario 02 retry (issue #69) — all three
   subagents completed cleanly. Bug closed.

Without this skill: both fixes would have shipped without unit-test
coverage. The next refactor that touched workflow YAML or `_retry_put`
would silently regress.

## What "good looks like"

- Every bug-fix PR's body documents the loop: hypothesis, failing
  tests, fix, test count delta, re-run confirmation.
- Reviewers can replay the loop to verify the regression is closed:
  `git checkout <commit-before-fix>` → run the new tests → confirm
  they fail → checkout the fix → confirm they pass.
- Test count grows monotonically; new tests are named after the bug
  they catch (`test_retry_put_sleeps_with_backoff_between_attempts`).
- The original e2e that surfaced the bug is re-run AFTER the loop;
  its pass is the final closure signal.

## Cousin skills

- [`live-test-after-substantive-merge`](../live-test-after-substantive-merge/) — what surfaces bugs in the first place.
- `retrospective/spec-vs-implementation-gap-discovery` (session 2) — the precursor: how to know whether the bug is implementation or spec.
- `retrospective/live-debug-from-mcp-only` (session 2) — how to read evidence when workflow logs are auth-walled.

## Status

**Spec only — process docs only, no code.** The pattern was applied
twice in session 3 (PR #56, PR #68). The spec generalizes it.
