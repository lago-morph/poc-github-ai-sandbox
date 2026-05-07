# SPEC: AGENTS.md additions (session 3 harvest)

12 do/don't rules harvested from session 3's live-testing run. Each
rule:

- Is grounded in a specific session event (provenance phrase).
- Is phrased as a concrete do/don't statement.
- Is ready to drop into `AGENTS.md` verbatim.

Suggested target sections in `AGENTS.md` are noted in italics. If
the section doesn't exist, create it; if it does, slot the rule into
the existing rhythm.

---

### 1. Drive live e2e immediately after substantive merges.

*Suggested section: `Spec discipline`.*

"After merging a PR that touches workflow YAMLs, env-var sourcing,
retry/backoff logic, or schema dispatch order, drive at least one
happy-path live scenario before moving on. Unit tests pass on broken
deployments."

*Grounded in: scenario 01 first attempt stalled because
`vars.AGENT_LOGIN` was unset — invisible to all 437 passing unit tests.*

---

### 2. Don't remove the YAML literal fallback.

*Suggested section: `Project-specific facts` (deployment notes).*

"Don't remove `${{ vars.AGENT_LOGIN || 'jonathanmanton' }}` from any
workflow file. The literal is the deployment-friction safety net for
the canonical repo. Unit tests in `tests/unit/test_workflow_yamls.py`
will catch its removal, but the rule should be in the human-facing
playbook too."

*Grounded in: PR #56's bug surfaced exactly this — a literal-free
workflow silently exits 1 on unset env var.*

---

### 3. All retry loops over CAS / version-mismatch errors must include backoff.

*Suggested section: `Workflow scripts`.*

"If you write a retry loop around an HTTP call that can return
412/422/409 or any 'version mismatch' status, you MUST include
exponential backoff with jitter. No-backoff retry is functionally
equivalent to no retry under N>1 concurrent writers."

*Grounded in: PR #68 — `_retry_put` retried 3 times in microseconds;
concurrent writers all collided in the same race window.*

---

### 4. Indirect blocking sleeps so tests can stub them.

*Suggested section: `Workflow scripts` (testing patterns).*

"Wrap any `time.sleep(...)` in a module-level `_<name>_sleep` helper.
Unit tests can monkey-patch the helper without affecting other
tests' use of `time.sleep`."

*Grounded in: PR #68's tests would have been brittle without
`handler._retry_sleep` indirection.*

---

### 5. Webhook-triggered workflows execute from default branch — period.

*Suggested section: `Branch and PR coordination`.*

"When you change a `.github/workflows/*.yml` file, the change does
NOT take effect for issue/PR/comment events until merged to default
branch. Test infra changes pre-merge by hand-running the script with
environment variables set."

*Grounded in: at end of session-3 implementation phase, a note in
HANDOFF.md flagged this — and Step 3 was deferred for exactly this
reason until the user merged PR #54.*

---

### 6. Self-diagnostic comments are the only debugging surface from MCP.

*Suggested section: `Workflow scripts`.*

"If you write a new workflow script, copy the
self-diagnostic-comment pattern from `handler.py`
(`_post_debug_comment`). Workflow logs are auth-walled even on public
repos. Without the diagnostic, MCP-only operators see only silence
on crash."

*Grounded in: bug #2 (the `_retry_put` race) was diagnosable only
because the existing self-diagnostic pattern surfaced the 422
traceback inline.*

---

### 7. Pipeline e2e error scenarios; serialize PR-merging scenarios.

*Suggested section: a new `Live testing` section, or fold into
`Spec discipline`.*

"When driving multiple live scenarios, pipeline ones that share no
branches and no merge targets. Serialize ones that open + merge PRs
(close-on-merge runs once per merge and races branch cleanup if you
parallel-merge)."

*Grounded in: this session's Phase 3 — 6 forensic scenarios
pipelined in parallel finished in 4 minutes; the 5 PR-opening
scenarios ran serially.*

---

### 8. Default to ack-via-follow-up for any new live scenario.

*Suggested section: `Working with the GitHub MCP server`.*

"When ack'ing a batch-job-request comment in a new scenario, prefer
the follow-up `kind: \"agent-ack\"` form over in-place edit. The
handler accepts both, but the follow-up form exercises the
post-session-3 code path."

*Grounded in: every PR-completed scenario in this session validated
the new ack form for the first time live.*

---

### 9. Test commands need entropy in their payloads when testing gzip rotation.

*Suggested section: a new `Test commands` section under `Project-specific facts`.*

"If a command like `chatty` exists to force log rotation, its
emitted records MUST include high-entropy per-line content (e.g.,
SHA-256 chains seeded by line number). Constant pads compress to a
fixed small size and rotation never fires."

*Grounded in: Step 2's first chatty implementation used a constant
pad and 500 lines compressed to ~6 KB total — no rotation. Fixed by
adding SHA-256-chained payload.*

---

### 10. State the bug-fix loop steps in the PR body verbatim.

*Suggested section: `Branch and PR coordination`.*

"When fixing a bug surfaced by an e2e test, the PR body should list:
hypothesis, the unit tests that catch it, the fix, the test count
delta, and a confirmation that re-running the original e2e passes.
Reviewers replay the loop to verify the regression is closed."

*Grounded in: PR #56 and PR #68 both follow this structure; both
regressions are now locked closed by their respective tests.*

---

### 11. A scenario marked `abandoned` is forensic — leave its branches.

*Suggested section: `Branch and PR coordination`.*

"When a scenario is intentionally abandoned (forensic error
scenarios, real bugs the next session will retry), don't manually
delete its branches. They linger because no PR was merged. Listing
them via `list_branches` is fine; deleting via `git push --delete`
is blocked by the sandbox proxy and would lose forensic state
anyway."

*Grounded in: ~11 forensic branches still present at end of session
3; close-on-merge correctly only sweeps merged-PR-head patterns.*

---

### 12. When the live system disagrees with unit tests, trust the live system.

*Suggested section: `Spec discipline`.*

"If a live scenario fails but every unit test passes, the bug is in
the deployment env or in concurrent execution semantics — both
invisible to unit tests. Do not 'fix' the unit tests to match.
Reproduce the bug in a new unit test as the first step."

*Grounded in: both bugs in session 3 fit this pattern. PR #56 added
`test_workflow_yamls.py`; PR #68 added `test_retry_put_*`.*

---

## Application order (suggested)

1. **High-priority (apply first):** rules 1, 3, 5, 12 — they
   crystallize the highest-impact lessons (live testing matters,
   retries need backoff, workflows run from main, trust the live
   system).
2. **Medium-priority:** rules 2, 4, 6, 7, 10 — concrete tactics that
   improve hygiene.
3. **Low-priority:** rules 8, 9, 11 — narrow but useful for the
   specific contexts they address.

The user decides ordering and which to accept.

## Anti-patterns when applying these rules

- **Don't bulk-paste.** Read each rule, decide, integrate. Bulk
  paste produces a wall of text that's harder to internalize.
- **Don't change the grounding phrase.** "Grounded in: X" is the
  audit trail. If the rule is amended, leave the original grounding
  so future readers can see the source event.
- **Don't add rules without a session-event grounding.** Generic
  advice ("write good tests") is noise. Every rule must trace to
  something that actually happened.

## Living document

Amend this directory when:
- A rule has been applied to `AGENTS.md` — strike it from the
  proposal list (or move to an `accepted/` subdirectory).
- A rule has been rejected — record the rationale.
- A new rule emerges from a future session that fits the same shape.

Provenance: harvested from session 3's inline retrospective (Mode A,
2026-05-06), Part 3.
