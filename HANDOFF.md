# HANDOFF — picking up from session 3 (post live testing)

> If you're a new agent landing in this repo and there's no clear
> ongoing task, this is your starting point. Read this whole file
> first, then `AGENTS.md`, then act.

## TL;DR

Session 3 implemented the four steps from session 2's plan AND drove
live regression + new scenarios. All four steps done. All 11 chosen
live scenarios pass. Two new bugs surfaced during live testing and
were fixed inline:

- **Step 1 done.** `kind: "agent-ack"` envelope shipped (schema, handler
  dispatch, agent_lib helpers, CLI, follow-up-vs-inline ack on the
  batch-job/poll skill, regression tests). **Validated live** in
  scenarios 01, 02-retry, 10.
- **Step 2 done.** `chatty` test command now lowers the LogWriter
  rotation threshold per-invocation (default 8 KiB, 500 lines), so
  rotation fires reliably under realistic line counts. Production
  defaults (524 288 bytes) are untouched. **Validated live** in
  scenario 12 (10 chunks at the new threshold vs 1 chunk in
  session 1's `chatty(20000)`).
- **Step 3 done.** 9 already-tested scenarios re-driven for regression;
  2 new scenarios (08 merge_conflict, 10 crash_recovery) driven for
  the first time. 11/11 PASS. Forensic artifacts preserved on
  issues #57-#71 and PRs #58/#66/#72/#73.
- **Step 4 done (all three sub-items).** `agent_login` indirection
  removed from `.agent/config.json`; workflows source from
  `vars.AGENT_LOGIN || 'jonathanmanton'` (PR #56 added the literal
  fallback after live testing surfaced a deployment-friction bug).
  Real-world correction notes for §3 / §6 merged into the primary
  narrative. Self-diagnostic-comment pattern promoted to SPEC §7.4.
- **Bonus.** `harness.lib` (naming + asserts helpers) was missing on
  `main`; the matching `tests/unit/test_harness_lib.py` was failing
  to even collect. Implemented during this session so the suite is
  green.

## Current state snapshot

- **446 unit + e2e tests passing** (was 348 baseline; +98 across
  session 3 work + 9 bug-fix regression tests).
- **11/11 live scenarios PASS** on 2026-05-06 against post-merge main.
- **9 real-world bugs** total now caught + fixed across sessions
  (7 from sessions 1–2, 2 new from session 3).
- Forensic artifacts from session 3's live runs preserved on the real
  repo (issues #55-#71; PRs #56, #58, #66, #68, #72, #73, #74; the
  `_agent_runs` orphan branch carries new manifests under
  `runs/{57,59-65,67,69-71}/`).
- Forensic artifacts from prior sessions still preserved on the real
  repo (issues #18, #21-#23, #25-#28, #31; merged PRs #19, #29, #30).
- Skill specs (`retrospective/`) remain committed for reference; not
  implemented in this repo.

For the full narrative, read `ITERATION_REPORT.md` and
`harness/RUNS.md` (the latter has session 3's live results).

## What's working (you can rely on these)

- **All three workflows live**: `lock-and-sweep.yml`,
  `batch-job-handler.yml`, `close-on-merge.yml`. They run on real
  GitHub Actions runners and produce real artifacts.
- **`vars.AGENT_LOGIN` with literal fallback.** Workflows source the
  bot login from `${{ vars.AGENT_LOGIN || 'jonathanmanton' }}`. New
  deployments override with their own repo variable; the canonical
  repo works without any admin setup.
- **`_retry_put` with jittered exponential backoff** (PR #68). Six
  retries, 0.5/1/2/4/8/16s base × random `[0.5, 1.5)`. Covers the
  concurrent-writer race on `_agent_runs` that scenario 02 surfaced.
- **`RestGitHubClient`** in `.agent/scripts/rest_client.py` covers
  the full `GitHubClient` Protocol. 24 mocked HTTP tests.
- **Workflow markers + self-diagnostic comment** patterns are baked
  in. Crashes leave readable evidence on the originating issue.
  Validated again in session 3 — the diagnostic comment posted by
  the beta subagent's crash is what made the `_retry_put` bug
  diagnosable from MCP-only.
- **Auto-delete branches on PR merge**: `close_on_merge.py` sweeps
  the head branch + any `<feature>--sub-*` siblings. Defensive
  namespace gates protect `main`, `_agent_runs`, etc.
- **`agent_lib/` CLI**: pure-python helpers for envelope construction,
  meta block transitions, terminal-status parsing, **and the new
  `make-ack` subcommand** for the follow-up agent-ack form.
- **Both ack forms** (in-place edit + follow-up `kind: "agent-ack"`
  comment) are accepted by the working→finished gate. MCP-only
  primaries default to the follow-up form.

## Bugs fixed during session 3 live testing

### Bug — `vars.AGENT_LOGIN` not set (PR #56)

**Symptom:** First scenario 01 attempt (issue #55) stalled. `lock-and-sweep`
ran but exited 1 silently with `missing env vars: ['AGENT_LOGIN']` because
the canonical repo had not had the GitHub Actions repo variable set.
Without the `agent-task` label, batch-job-handler also could not fire on
subsequent comments.

**Fix:** Add a YAML-level fallback `${{ vars.AGENT_LOGIN || 'jonathanmanton' }}`
in all three workflow `env:` blocks and in the batch-job-handler
`if:`-clause. Unit tests (`tests/unit/test_workflow_yamls.py`, 4 tests)
pin the fallback string in each YAML so regression cannot reach main.

### Bug — `_retry_put` no-backoff race (PR #68)

**Symptom:** First scenario 02 retry (issue #67). Three concurrent
echo-handler workflows ran in parallel; beta crashed with `422
Unprocessable Entity` on the `_agent_runs` PATCH-ref API after
exhausting all 3 retries in microseconds. Comment 4385451782 stuck in
`run_status: "running"`. Workflow self-diagnostic comment surfaced the
HTTP 422 traceback.

**Fix:** Jittered exponential backoff in `_retry_put` (0.5/1/2/4/8/16s
base × random `[0.5, 1.5)`), retries 3 → 6, sleep indirected through
`_retry_sleep` so unit tests can stub it. 5 new regression tests
(`tests/unit/test_handler.py::test_retry_put_*`).

## Decisions locked in (session 3)

The user re-confirmed the four-step plan from session 2 with two
additional calls during session 3:

- **`agent_login` indirection** → take the **bigger refactor**: remove
  the static `agent_login` config key entirely; workflows source it
  from `vars.AGENT_LOGIN` and agent harnesses source it from
  `mcp__github__get_me`. (SPEC §3.1 documents the new contract.)
  PR #56 added a literal fallback so the canonical repo works
  without admin setting `vars.AGENT_LOGIN`.
- **End-to-end gate** → both pytest e2e (`tests/e2e/`) AND live MCP
  scenarios (`harness/scenarios/`) count. Apply the bug-fix loop to
  failures from either layer.
- **`harness.lib`** → implement (was a missing-module test failure
  on `main`).

The original session-2 calls (still in force):

- **`agent_ack` for MCP-only agents** → ack lives in a follow-up
  `kind: agent-ack` comment with `ack_for: <comment_id>`. The
  `working → finished` gate accepts either form.
- **`chatty` command** → lower the per-invocation chunk-size
  threshold inside chatty itself; production defaults stay intact.
- **Skills in `retrospective/`** → **NOT implemented in this repo.**
- **Spec polish (§6 in the session-2 queue)** → all three items done.

## What this session changed (session 3 patch summary)

### Step 1 — agent-ack comment kind

- New schema: `.agent/schemas/comment-ack-envelope.schema.json`.
- `handler.py`: dispatches on `kind`; agent-ack comments return
  `{action: noop, reason: ack_comment}` and are not parse-errored.
- `agent_lib/envelope.py`: `make_ack_envelope(...)` builder.
- `agent_lib/poll.py`: `parse_ack_comment`, `is_request_acked` (the
  bi-form working→finished gate predicate).
- `agent_lib/cli.py`: `make-ack` subcommand + wiring.
- `skills/batch-job/poll.py`: new `ack_mode: "inline" | "follow_up"`
  parameter (default `inline` to preserve existing callers); when
  `follow_up`, posts a sibling agent-ack comment instead of editing
  the request comment in place; falls back to the comment's
  `issue_number` field when not passed an explicit `issue_number`;
  raises ValueError on misconfiguration; reports `ack_comment_id` in
  the return dict.
- New tests: `tests/unit/test_agent_ack.py` (28 tests for envelope
  shape, handler dispatch, parse/predicate); plus 6 CLI tests in
  `test_agent_lib.py` and 7 ack-mode tests in `test_skill_batch_job.py`.

### Step 2 — chatty rotation threshold

- `LogWriter.set_max_chunk_bytes(int)` public method on
  `.agent/scripts/common.py` (raises on closed/invalid).
- `chatty.py`: defaults `lines=500`, `max_chunk_bytes_compressed=8192`;
  applies the override via `set_max_chunk_bytes` at the top of `run()`.
  Per-line payload uses an SHA-256-chain-derived high-entropy string so
  gzip can't compress 500 lines below 8 KiB.
- `chatty.schema.json`: declares the new `max_chunk_bytes_compressed`
  arg (`integer, minimum: 1`).
- `harness/scenarios/12_huge_log.md`: updated to use the new defaults
  and document the per-invocation override.
- New unit tests in `test_command_chatty.py` and `test_common.py`.

### Step 4a — `agent_login` indirection removed

- `.agent/config.json`: `agent_login` key removed.
- `.github/workflows/batch-job-handler.yml`: literal
  `'jonathanmanton'` replaced with `vars.AGENT_LOGIN`; the handler
  step now also receives `AGENT_LOGIN` via env. `lock-and-sweep.yml`
  and `close-on-merge.yml` similarly pass `AGENT_LOGIN`.
- `lock_and_sweep.py` and `submit.py`: resolution order is **explicit
  arg → AGENT_LOGIN env var → raise**. Clear `RuntimeError` on
  missing.
- `tests/conftest.py`: sets `AGENT_LOGIN=jonathanmanton` at import
  time; `base_config` fixture **injects** `agent_login` into the
  returned dict for backwards compatibility with existing tests; new
  `agent_login` fixture available.
- `tests/unit/test_lock_and_sweep.py`: 3 new tests (env-var path,
  missing-everywhere → RuntimeError, explicit-arg precedence).
- `tests/unit/test_common.py`: asserts the on-disk config does **not**
  carry `agent_login`.

### Step 4b — Real-world correction notes merged into primary narrative

- SPEC §3, §6: the corrected design (lock-at-close, `--sub-`
  separator) is now the primary text. The "Real-world correction"
  asides have been integrated into the surrounding bullets and intent
  notes; the historical record lives in `ITERATION_REPORT.md`.

### Step 4c — Self-diagnostic comments are first-class

- New SPEC §7.4 documents when, what, and how the workflow handler
  emits self-diagnostic comments: emit conditions, comment shape
  (markdown not JSON, redacted secrets, `<details>` envelope/traceback
  blocks), and consumer expectations.

### Bonus — harness/lib

- New `harness/__init__.py` and `harness/lib/{__init__,naming,asserts}.py`.
- `.gitignore`: added `!harness/lib/` to override the global `lib/`
  exclusion.
- `tests/unit/test_harness_lib.py` now collects and passes (38 tests).

## Step 3 — Live regression + new scenarios (DONE this session)

After PR #54 merged session 3 to main, session 3 also drove all 11
chosen live scenarios on 2026-05-06.

**Live results — 11/11 PASS (full ledger in `harness/RUNS.md`):**

| Scenario | Issue | PR | Result |
|----------|-------|----|--------|
| 01 happy_single_subagent | #57 | #58 | completed end-to-end |
| 02 multi-subagent (1st)  | #67 | —   | **abandoned (bug → PR #68)** |
| 02 multi-subagent (retry)| #69 | #73 | completed end-to-end |
| 03 parse_error            | #61 | —   | parse_error (forensic) |
| 04 sha_mismatch           | #62 | —   | error/branch_sha_mismatch (forensic) |
| 05 unsupported_version    | #63 | —   | parse_error/unsupported_version (forensic) |
| 06 unknown_command        | #64 | —   | error/unknown_command (forensic) |
| 07 summary_schema_violation | #65 | — | error/summary_schema_violation (forensic) |
| 08 merge_conflict (NEW)   | #70 | —   | abandoned (merge_conflict) |
| 10 crash_recovery (NEW)   | #71 | #72 | completed end-to-end via takeover |
| 12 huge_log               | #59 | #66 | completed (10 chunks at new threshold) |
| 13 unicode_summary        | #60 | —   | completed (forensic, no PR) |

**Skipped scenarios** (per session-2 plan): 09 failed_dependency,
11 webhook_redelivery, 14 concurrent_claim, 15 stale_takeover.
Reasons in `ITERATION_REPORT.md` Phase 4 "Scenarios deliberately
not driven". Revisit only if a concrete use case appears.

**Validations achieved live for the first time:**

- Session 3's `kind: "agent-ack"` follow-up form (handler dispatches
  on kind, gate accepts both forms).
- Session 3's chatty defaults (10 chunks rotated under new threshold
  vs 1 chunk under session 1's `chatty(20000)`).
- `vars.AGENT_LOGIN || 'jonathanmanton'` fallback (PR #56).
- `_retry_put` jittered exponential backoff (PR #68).

## Open work (next session picks up here)

There is no urgent open work right now. The protocol POC is feature-
complete for the v1 spec; the four-step plan from session 2 is fully
implemented and live-validated.

Possible future work, in rough priority order:

1. **Drive the four skipped scenarios** (09, 11, 14, 15) only when a
   concrete need arises. Each requires non-trivial setup; the
   in-memory pytest e2e suite already covers their state machines.
2. **Implement the retrospective skill specs** in a separate repo
   (per session 2's decision — they stay as specs here).
3. **Backend-neutral API refactor** — see `proposals/agent-api-refactor/`
   for the full brief. Bitbucket adapter is a worked example in
   `proposals/bitbucket-adapter/`.
4. **Add a `crash-after-N` test command** for a workflow-side crash
   scenario distinct from scenario 10's primary-side crash. The
   session 2 HANDOFF mentioned this as a prerequisite for scenario
   10, but scenario 10 as written tests primary-crash recovery (no
   workflow-side crash needed). A separate scenario for workflow
   crash would round out the failure-mode coverage.
5. **Schema evolution / protocol_version=2** — when a v2 envelope
   shape becomes necessary, ship the v2 handler on main first, then
   start emitting v2 envelopes. Per-command schemas independently
   versioned via filename suffix.

## Things the next agent should NOT do

- **Don't implement skills from `retrospective/`** in this repo. They
  are processed elsewhere. The specs stay committed for reference.
- **Don't lock issues at creation.** This was bug #6 — the protocol's
  highest-impact spec defect. Lock at close, never at creation.
- **Don't use `<feature>/sub-<id>` as a subagent branch separator.**
  Git ref-prefix collision. Use `<feature>--sub-<id>`.
- **Don't push -f a feature branch back to main while a PR from it
  is open.** GitHub auto-closes the PR. (Lost PR #6 this way; recovered
  from reflog.)
- **Don't trust unit tests as the bar for "done."** They only catch
  implementation defects. Spec defects and transport quirks need
  live execution. Session 3 confirmed this twice: PR #56's
  deployment-friction bug (`vars.AGENT_LOGIN` unset) and PR #68's
  concurrent-writer race in `_retry_put` were both invisible to
  unit tests — the live drive exposed them in minutes.
- **Don't assume `vars.AGENT_LOGIN` is set on a fresh deployment.**
  The workflow YAMLs include a literal fallback to `jonathanmanton`,
  but new deployments still need to set the repo variable to point
  at their own bot account.
- **Don't remove the literal fallback in workflow YAMLs.** It's the
  only thing keeping the canonical repo functional without admin
  setup of `vars.AGENT_LOGIN`. New deployments override; the literal
  is a safety net.

## Known traps (live and active right now)

- **MCP returns issue/comment bodies HTML-escaped.** `&#34;` instead
  of `"`. Always `html.unescape()` before JSON-parsing.
- **MCP's `add_issue_comment` appends a Claude Code trailer** to
  every comment. Strict `json.loads()` fails. Use
  `JSONDecoder().raw_decode()`.
- **Locked issues block `GITHUB_TOKEN` writes** even with `issues:
  write` permission. Don't lock until close.
- **Workflow logs are auth-walled** even on public repos. Use marker
  comments + base64-embedded stdout for diagnostics. Patterns are in
  `retrospective/live-debug-from-mcp-only/SPEC.md` and already
  baked into `batch-job-handler.yml`.
- **`git push --delete <branch>` is blocked by the local proxy in
  this sandbox.** If you need to delete branches, drive deletion
  through `close_on_merge` or the `delete_branch` REST call (the
  `RestGitHubClient` has it).
- **The MCP server authenticates as `jonathanmanton`, not as a bot.**
  All workflow `if:` filters comparing to a bot login won't match.
  Sourced via `mcp__github__get_me` if you need to verify.

## Useful entry points

| Need | Read |
|------|------|
| Where things stand overall | This file |
| What conventions to follow | `AGENTS.md` |
| Full session narrative | `ITERATION_REPORT.md` |
| Protocol design | `SPEC.md` |
| What's been live-tested | `harness/RUNS.md` |
| Skill specs (reference only; not built here) | `retrospective/<skill>/SPEC.md` |
| MCP quirks reference | `retrospective/github-mcp-tips/excerpts.jsonl` |
| Pre-existing live artifacts | Issues #18-#31 on the repo |

## Default plan if the user gives no specific direction

1. Read `AGENTS.md` and this file.
2. Run the unit + e2e tests to confirm nothing has regressed:
   ```
   cd /home/user/poc-github-ai-sandbox
   python -m pytest tests/ -q --tb=short
   ```
   Expect **446 passing** (session 3 baseline). Coverage ≈93% across
   `.agent/`, `skills/`, and `harness/lib/`.
3. The four-step plan from session 2 is **fully done and live-validated**
   (see §"What's working" and §"Step 3 — Live regression + new
   scenarios"). There is no urgent open work. If the user has not
   given a specific direction, pick from §"Open work (next session
   picks up here)" — items there are roughly priority-ordered, but
   each is genuinely optional.
4. Update this HANDOFF.md at the end of each session with what
   changed (per §"Provenance" — the file is the project's
   current-state document).

## Provenance

This handoff was written at the end of session 1 by the dispatcher
that built and live-tested the POC. It's the synthesis of:

- `ITERATION_REPORT.md` Phases 1-4
- `harness/RUNS.md` ledger
- The "What I'd recommend next" section at the end of
  `ITERATION_REPORT.md`
- The retrospective skill specs in `retrospective/`

Updated in session 2 with the user's decisions on the open priority
queue and the resulting four-step plan. PR #50 / #51 (skill specs)
confirmed merged.

Updated in session 3 (PR #54) with the implementation of the
four-step plan, then again (PR #75) with the live regression /
new-scenario results: 11/11 PASS, two new bugs fixed inline
(PR #56 `vars.AGENT_LOGIN` fallback, PR #68 `_retry_put` backoff).
The default-plan and "Open work" sections were rewritten to reflect
that the v1 spec is now feature-complete and live-validated.

Update this file at the start of each new session with what's
changed; treat it as the project's current-state document.
