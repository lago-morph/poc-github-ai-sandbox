# HANDOFF — picking up from session 1

> If you're a new agent landing in this repo and there's no clear
> ongoing task, this is your starting point. Read this whole file
> first, then `AGENTS.md`, then act.

## TL;DR

A multi-day session built and live-tested a proof-of-concept of the
GitHub-Native Agent Job Protocol. The protocol works end-to-end on
real GitHub, with 7 design bugs discovered and patched along the way.
**The unit-test side is done.** **The live-test side is partial.**
**The skills harvest is done as specs (not code).** Several work
streams remain.

## Current state snapshot

- `main` HEAD reflects all merged work from session 1, including the
  retrospective skill specs (PR #50, PR #51).
- 386 unit tests passing, ≥95% coverage.
- 9 of 15 harness scenarios driven live; 6 deferred (see below).
- 7 real-world bugs caught and fixed; spec amendments inline in
  `SPEC.md` as "Real-world correction" notes.
- Forensic artifacts from live scenarios preserved on the real repo
  (issues #18, #21, #22, #23, #25, #26, #27, #28, #31; merged PRs
  #19, #29, #30; `_agent_runs` orphan branch with manifests + log
  chunks).
- Skill specs (`retrospective/`) are committed but **will not be
  implemented in this repo** — they will be processed elsewhere.

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

## Decisions locked in (session 2)

The user reviewed the open priority queue and made the following calls:

- **`agent_ack` for MCP-only agents** → take **Option A**: ack lives
  in a follow-up `kind: agent-ack` comment with
  `ack_for: <comment_id>`. The workflow's restart-recovery /
  `working → finished` gate must recognize either form.
- **`chatty` command** → fix by **lowering the chunk-size threshold
  for the test command** (so the `chatty` invocation triggers
  rotation under realistic line counts). Update scenario 12's spec
  to document the choice.
- **Skills in `retrospective/`** → **NOT implemented in this repo.**
  They will be processed elsewhere. Do not start a build task here.
- **Spec polish (§6 below in the old queue)** → **do all three
  items**.

## Plan for the next session (in this order)

Work the plan top to bottom. Re-run the unit tests after each step
and update this HANDOFF.md at the end of each step so the next agent
inherits an accurate snapshot.

### Step 1 — Implement subagent-ack comment kind + spec update

- Define a new comment envelope `kind: "agent-ack"` with field
  `ack_for: <original_comment_id>` (and `agent_acked_at` timestamp).
  Add the JSON Schema at `.agent/schemas/comment-envelope.schema.json`
  (or a sibling file) and wire it into validation.
- Update `SPEC.md`:
  - **§5.2** — document the new envelope shape alongside the existing
    `batch-job-request` shape.
  - **§9.4 step 7** — the agent posts a fresh ack comment instead of
    editing the batch-job-request comment in place.
  - **§4.1** — the `working → finished` gate accepts either an
    in-place `agent_ack: finished` *or* a matching follow-up
    `kind: agent-ack` comment with `ack_for` pointing at the
    relevant batch-job-request comment id.
- Update the workflow handler / restart-recovery logic
  (`.agent/scripts/handler.py`, `agent_lib/`) so it treats both forms
  as ack-equivalent. The MCP-only primary path should emit the new
  follow-up form by default.
- Add a regression test for ack handling (both forms accepted; mixed
  state across multiple comments behaves correctly).
- Refresh the comment-envelope unit tests; expect ≥386 passing after
  the new tests land.

### Step 2 — Lower chunk-size threshold for the test command

- In `.agent/commands/chatty.py` (or its config), reduce the
  chunk-size threshold used by the test command so a modest line
  count reliably triggers `logs.max_chunk_bytes_compressed`-driven
  rotation. Keep production defaults intact.
- Update `harness/scenarios/12_*.md` to document the chosen fix and
  the new expected behavior.
- Add / refresh the unit test that asserts rotation fires at the
  reduced threshold.

### Step 3 — Run the suggested deferred scenarios + regression-rerun the tested ones

- **Suggested deferred scenarios (do these):**
  - **08 merge_conflict** — actual `git merge` on the runner (not the
    in-memory overlay used in scenario 02).
  - **10 crash_recovery** — requires a `crash-after-N` test command
    in `.agent/commands/` to induce a deterministic workflow crash
    mid-run. Build the command first, then drive the scenario.
- **Skip:** 09 failed_dependency, 11 webhook_redelivery,
  14 concurrent_claim, 15 stale_takeover. (Reasons in
  `ITERATION_REPORT.md` Phase 4 "Scenarios deliberately not driven".
  Revisit only if a concrete use case appears.)
- **Re-run the 9 already-tested scenarios** end-to-end. This is
  *both* belt-and-suspenders coverage *and* a regression check for
  step 1's ack-semantics change — if the new follow-up ack form
  isn't wired correctly, `working → finished` will hang here.
- **Bug-fix loop**: when a scenario fails, fix the root cause
  (spec or code), add a unit test if applicable, log the bug + fix
  in `harness/RUNS.md`, and rerun. Repeat until all chosen scenarios
  reach their expected terminal state.

### Step 4 — Spec polish

Three items, all mechanical:

- **Drop the `agent_login` Actions-variable indirection.** The
  literal `'jonathanmanton'` is currently hard-coded in the workflow
  YAML. Replace with a setup step that sources `agent_login` from
  `.agent/config.json` at runtime, so multi-user deployment works
  without YAML edits.
- **Merge the SPEC §3 / §6 "Real-world correction" notes into the
  main spec text** so the corrected design is the primary narrative
  and the historical note is removed (or moved to a changelog
  appendix).
- **Promote the self-diagnostic-comment pattern to a first-class
  SPEC section.** It currently lives only as an amendment / inline
  reference. Give it a dedicated section describing when the
  workflow handler emits a diagnostic comment, the envelope shape,
  and the consumer expectations.

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
