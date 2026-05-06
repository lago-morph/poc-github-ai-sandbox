# HANDOFF — picking up from session 3

> If you're a new agent landing in this repo and there's no clear
> ongoing task, this is your starting point. Read this whole file
> first, then `AGENTS.md`, then act.

## TL;DR

Session 3 implemented the four steps queued at the end of session 2:

- **Step 1 done.** `kind: "agent-ack"` envelope shipped (schema, handler
  dispatch, agent_lib helpers, CLI, follow-up-vs-inline ack on the
  batch-job/poll skill, regression tests).
- **Step 2 done.** `chatty` test command now lowers the LogWriter
  rotation threshold per-invocation (default 8 KiB, 500 lines), so
  rotation fires reliably under realistic line counts. Production
  defaults (524 288 bytes) are untouched.
- **Step 3 (live scenarios).** Not yet driven this session — see the
  open work below.
- **Step 4 done (all three sub-items).** `agent_login` removed from
  `.agent/config.json`; sourced from `vars.AGENT_LOGIN` in CI and
  `mcp__github__get_me` in agent harnesses (SPEC §3.1). Real-world
  correction notes for §3 / §6 merged into the primary narrative.
  Self-diagnostic-comment pattern promoted to a dedicated SPEC §7.4.
- **Bonus.** `harness.lib` (naming + asserts helpers) was missing on
  `main`; the matching `tests/unit/test_harness_lib.py` was failing
  to even collect. Implemented during this session so the suite is
  green.

## Current state snapshot

- 437 unit + e2e tests passing.
- All Step 1, 2, 4a/b/c work landed; Step 3 (live scenarios) deferred.
- 7 real-world bugs from sessions 1–2 already merged; this session's
  changes are spec-discipline, not new bug discoveries.
- Forensic artifacts from prior live scenarios still preserved on the
  real repo (issues #18, #21, #22, #23, #25, #26, #27, #28, #31;
  merged PRs #19, #29, #30; `_agent_runs` orphan branch with manifests
  + log chunks).
- Skill specs (`retrospective/`) remain committed for reference; not
  implemented in this repo.

For the full narrative, read `ITERATION_REPORT.md`.

## What's working (you can rely on these)

- **All three workflows live**: `lock-and-sweep.yml`,
  `batch-job-handler.yml`, `close-on-merge.yml`. They run on real
  GitHub Actions runners and produce real artifacts.
- **`RestGitHubClient`** in `.agent/scripts/rest_client.py` covers
  the full `GitHubClient` Protocol. 24 mocked HTTP tests.
- **Workflow markers + self-diagnostic comment** patterns are baked
  in. Crashes leave readable evidence on the originating issue.
- **Auto-delete branches on PR merge**: `close_on_merge.py` sweeps
  the head branch + any `<feature>--sub-*` siblings. Defensive
  namespace gates protect `main`, `_agent_runs`, etc.
- **`agent_lib/` CLI**: pure-python helpers for envelope construction,
  meta block transitions, terminal-status parsing. Used by the agent
  side of live scenarios.

## Decisions locked in (session 3)

The user re-confirmed the four-step plan from session 2 with two
additional calls during session 3:

- **`agent_login` indirection** → take the **bigger refactor**: remove
  the static `agent_login` config key entirely; workflows source it
  from `vars.AGENT_LOGIN` and agent harnesses source it from
  `mcp__github__get_me`. (SPEC §3.1 documents the new contract.)
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

## Open work (next session picks up here)

### Step 3 — Drive deferred + regression-rerun the tested scenarios

**Not driven this session. Cannot be driven from this branch.**

GitHub Actions workflow files for `issues.opened` and
`issue_comment.created` events execute from the **default branch's**
`.github/workflows/` checkout — not from a feature branch's checkout.
The session-3 changes (new `agent-ack` envelope kind, new chatty
defaults, `AGENT_LOGIN` env var sourcing, removal of `agent_login`
from `.agent/config.json`) only land in the live system after this
branch is merged to `main`. Driving scenarios from this branch would
exercise main's pre-session-3 code, which is the same code session 1
already validated — providing no incremental signal.

**Pre-flight before next live run:**

1. Merge `claude/implement-handoff-parallel-4d5AY` to `main`.
2. Set `vars.AGENT_LOGIN = jonathanmanton` (or whichever bot account
   the deployment uses) as a repo-level GitHub Actions variable.
   Without this, the workflow `if:` clause never fires.
3. Verify the merged main still passes `python -m pytest tests/ -q`.

**Then drive:**

- **Suggested deferred scenarios:** 08 (merge_conflict against the
  runner's actual `git merge`) and 10 (crash_recovery — needs a
  `crash-after-N` test command in `.agent/commands/` first).
- **Skip:** 09, 11, 14, 15.
- **Regression-rerun the 9 already-tested scenarios.** Step 1 changed
  ack semantics and Step 2 changed chatty defaults; the bi-form
  working→finished gate and the new threshold are not exercised by
  unit tests against real GitHub, so live verification is the only
  way to confirm.
- **Bug-fix loop**: spec or code → unit test → log in
  `harness/RUNS.md` → rerun.

**Expected new failure modes to watch for after merge:**

- A scenario that posts the new `kind: "agent-ack"` follow-up form
  must NOT trigger a `parse_error` from the workflow handler. (Main's
  pre-session-3 handler would have parse-errored such comments because
  it had no kind dispatch.)
- Scenarios calling `chatty` should now default to lines=500 with the
  per-invocation chunk threshold of 8192 — old scenario doc text or
  old envelope payloads that pass `lines=20000` would still work, but
  the rotation behavior changed.
- Workflows that don't receive `AGENT_LOGIN` env var (because admin
  forgot to set `vars.AGENT_LOGIN`) will now fail loudly with a
  `RuntimeError` instead of silently mis-comparing — this is intended
  but a fresh deployment will need the variable set.

Work the plan top to bottom. Re-run the unit tests after each step
and update this HANDOFF.md at the end of each step so the next agent
inherits an accurate snapshot.

The Step 1 / Step 2 / Step 4 work from session 2's queue is complete
(see "What this session changed" above). What remains is **Step 3**:
drive deferred scenarios + regression-rerun the tested ones, with
specific attention to:

- The new agent-ack follow-up form (default for MCP-only primaries).
- The `vars.AGENT_LOGIN` variable being set on the live repo.
- The `chatty` command now defaulting to `lines=500,
  max_chunk_bytes_compressed=8192` — scenarios that called it with
  the old `lines=20000` need updating before they run live.

If `vars.AGENT_LOGIN` is not configured on the live repo, the workflow
will need that one-time admin step before live scenarios can run.

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
  live execution.
- **Don't skip the regression rerun in step 3.** Step 1 changes ack
  semantics; the only way to confirm nothing regressed is to re-drive
  the 9 already-tested scenarios end-to-end.

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
2. Run the unit tests to confirm nothing has regressed:
   ```
   cd /home/user/poc-github-ai-sandbox
   python -m pytest tests/ -q --tb=short
   ```
   Expect 386 passing.
3. Start at the top of §"Plan for the next session" — Step 1
   (subagent-ack comment kind). Don't skip ahead; later steps depend
   on the ack semantics landing first.
4. Update this HANDOFF.md at the end of each step with what changed
   (per §"Provenance" — the file is the project's current-state
   document).

## Provenance

This handoff was written at the end of session 1 by the dispatcher
that built and live-tested the POC. It's the synthesis of:

- `ITERATION_REPORT.md` Phases 1-4
- `harness/RUNS.md` ledger
- The "What I'd recommend next" section at the end of
  `ITERATION_REPORT.md`
- The retrospective skill specs in `retrospective/`

Updated in session 2 with the user's decisions on the open priority
queue and the resulting four-step plan above. PR #50 / #51 (skill
specs) confirmed merged.

Update this file at the start of each new session with what's
changed; treat it as the project's current-state document.
