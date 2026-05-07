# SPEC: `bug-fix-loop-discipline`

## Trigger conditions

### Direct triggers — activate immediately

- "Fix this bug."
- "The e2e test failed; debug it."
- "Why doesn't this work in production?"
- Any failing live scenario / failing CI build.

### Proactive triggers — offer the skill without being asked

Offer when:

- A live e2e test fails or stalls (per `live-test-after-substantive-merge`).
- A unit test exposes a behavior gap.
- A user reports a bug with reproduction steps but no test coverage.
- A code review uncovers an untested edge case.

Do NOT offer for:
- Pure refactors (no behavior change to lock down).
- Doc fixes.
- Style / lint cleanup.

## Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `failing_test` | (required) | The e2e or live test that surfaced the bug. |
| `hypothesis_required` | `true` | Whether to require an explicit written hypothesis before any fix. |
| `regression_test_required` | `true` | Whether to require a unit test before fixing. |
| `pr_required` | `true` | Whether each loop produces its own PR (vs bundling fixes). |

## Outputs

- A new branch `claude/fix-<short-bug-id>` containing:
  - 1+ unit tests covering the bug (named after the symptom).
  - The minimal fix.
  - Updated docs / `AGENTS.md` rules where applicable.
- A PR with the loop documented in the body.
- A re-run of the original failing test, confirming pass.
- Updated `harness/RUNS.md` (if the surfacing test was a live scenario).

## Workflow steps

1. **Hypothesis first.** Before writing any code, write the cause in
   1-3 sentences. State exactly what the bug is, where it lives, and
   why it produces the observed symptom. If you can't articulate
   this, you can't write a meaningful test.

   *Example:* "`_retry_put` retries on Exception without any sleep
   between attempts. With three concurrent writers, all three retry
   in microseconds and continue to collide on the `_agent_runs`
   ref. Default retries=3 exhausts before any writer settles."

2. **Test that would have caught it.** Write the unit test. The test
   MUST FAIL on the unfixed code. If it passes immediately, the test
   isn't testing what you think.

   *Naming convention:* `test_<subject>_<symptom>` —
   `test_retry_put_sleeps_with_backoff_between_attempts`,
   `test_workflow_provides_agent_login_env_with_fallback`.

3. **Verify it fails.** Run only the new test:
   ```
   python -m pytest tests/unit/test_<file>.py::test_<name> -v
   ```
   If it passes on the unfixed code: stop. The hypothesis is wrong
   or the test isn't tight enough. Go back to step 1 or 2.

4. **Fix the code.** Keep the change minimal — same scope as the
   hypothesis. Don't refactor, don't add unrelated improvements.
   Each loop is one logical change.

5. **Verify the test passes.** Run only the new test first to
   confirm scope; then run the whole suite to confirm no regressions:
   ```
   python -m pytest tests/unit/test_<file>.py::test_<name> -v
   python -m pytest tests/ -q --tb=line
   ```

6. **Re-run the original e2e** that surfaced the bug. Pass = closed.
   Fail = back to step 1, hypothesis was wrong.

7. **Document the loop in the PR body.** Use the template below. The
   PR body becomes the bug's permanent record.

8. **Open + merge the PR.** The fix should land before any
   subsequent work — so the next session inherits a clean state.

## Templates

### PR body template

```markdown
## Summary

<One-sentence symptom> surfaced by <where it surfaced (live test, CI, user report)>.

**Root cause:** <hypothesis from step 1; 1-3 sentences>

**Fix:** <one-sentence description of the change>

## Test plan

- [x] N new regression tests in `tests/unit/test_<file>.py`:
  - `test_<a>` — covers <aspect>.
  - `test_<b>` — covers <aspect>.
  - ...
- [x] Tests fail on the unfixed code (verified pre-fix).
- [x] Tests pass post-fix.
- [x] Full suite still green (was X / now Y).
- [ ] Re-run original e2e (<scenario / link>).

https://claude.ai/code/session_<id>
```

### Hypothesis template

A good hypothesis has three parts:

1. **What.** What is the bug? Concrete: "function `_retry_put`
   retries on Exception without any sleep between attempts."
2. **Where.** Where in the code? Concrete: "`.agent/scripts/handler.py`
   lines ~404-415."
3. **Why.** Why does this produce the observed symptom? Concrete:
   "with three concurrent writers, all three retry in microseconds
   and continue to collide on the `_agent_runs` ref."

If any of these three parts is hand-wavy ("the retry logic is bad"),
write more.

## Anti-patterns

- **Skipping step 2 (the failing test).** The fix becomes a
  snowflake — works once, regresses in six months, nobody remembers
  why. The test is the permanent record.
- **Writing a test that passes on the broken code.** Means the test
  isn't actually exercising the bug. Easy to miss when both tests
  look "right". **Always run the test pre-fix and verify it fails.**
- **Bundling multiple bug fixes into one PR.** Each loop produces
  one commit. One PR per loop. Reviewers replay one bug at a time.
- **Hypothesis-by-fix-attempt.** "Let me try this and see if it
  works" is not a hypothesis. State the cause first, in writing,
  before writing any code.
- **Fixing the symptom instead of the cause.** Catching the
  exception higher up the stack hides the bug; it doesn't fix it.
  Trace to the actual mismatch and fix there.
- **Skipping the e2e re-run.** Unit tests pass ≠ bug fixed. The e2e
  that surfaced the bug is the only thing that confirms closure.
- **Refactoring during a fix.** Tempting to "clean up while I'm
  here." Don't. Each unrelated change muddies the loop and risks
  re-introducing the bug. Refactor in a separate PR.

## Implementation notes

- **The pattern is process, not code.** It's training material for
  the next session, not something to "implement" as a tool.
  However, automation is possible: a CI check that requires every
  bug-fix PR to include ≥1 new test would be a useful enforcement
  mechanism.
- **Per-loop PR overhead.** Each PR adds CI cycles. For small fixes
  (one-line) it can feel heavy. The discipline pays off when the
  same regression resurfaces six months later and you can point at
  the test that catches it.
- **Hypothesis quality determines test quality.** A vague hypothesis
  produces a vague test that doesn't pin the actual cause. Spend
  time on step 1.

## Test plan

- This skill is process / discipline, not code. Validation is
  observational: each bug-fix PR in the project's history should
  follow the loop. PRs that don't can be retro-reviewed and amended.
- An optional CI check could enforce: bug-fix PR commits must
  include ≥1 new test file or ≥1 new test function. False positives
  (legitimate doc-only PRs labeled "fix") need an opt-out label.

## Living document

Amend this spec when:
- A new pattern of bug emerges that the standard loop doesn't cover well.
- The PR-body template needs to absorb additional metadata (e.g., a "downstream impact" section for cross-repo bugs).
- The naming conventions for regression tests evolve.

Provenance: session 3 — applied twice cleanly:
1. PR #56 (`vars.AGENT_LOGIN` fallback) caught by 4 YAML-shape unit tests.
2. PR #68 (`_retry_put` jittered exponential backoff) caught by 5 retry-behavior unit tests.

Both regressions are now permanently locked closed.
