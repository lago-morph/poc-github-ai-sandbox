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

- `main` HEAD reflects all merged work from session 1.
- 386 unit tests passing, ≥95% coverage.
- 9 of 15 harness scenarios driven live; 6 deferred (see below).
- 7 real-world bugs caught and fixed; spec amendments inline in
  `SPEC.md` as "Real-world correction" notes.
- Forensic artifacts from live scenarios preserved on the real repo
  (issues #18, #21, #22, #23, #25, #26, #27, #28, #31; merged PRs
  #19, #29, #30; `_agent_runs` orphan branch with manifests + log
  chunks).
- `feat/retrospective-skill-specs` branch (PR #50) holds the skill
  specs harvested from session 1. Not merged yet — the user reviews
  before merging.

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

## What's not done (the priority queue for the next agent)

These are ranked by impact + tractability. Pick from the top.

### 1. Fix `agent_ack` for MCP-only agents — high impact

The protocol's spec (§9.4 step 7) requires the agent to **edit** the
batch-job-request comment to set `agent_ack: finished`. The MCP
server doesn't expose `update_comment`. The protocol is therefore
unimplementable end-to-end via MCP.

In the live scenarios, this was skipped (terminal envelopes are
unack'd; issues still close cleanly). But the spec needs to formalize
either:

- **Option A**: Spec amendment — ack lives in a follow-up
  `kind: agent-ack` comment with `ack_for: <comment_id>`. The
  workflow's restart-recovery logic recognizes either form.
- **Option B**: A direct REST helper invoked from the Actions runner
  (the runner can edit comments, just not via MCP). The agent posts
  a "please ack" comment that the workflow handler interprets and
  edits the original.

Recommend **Option A**. It keeps the protocol agent-self-contained
without requiring a workflow round-trip for every ack. Update SPEC §5
and §9, add a test command for ack handling, regression-test it.

### 2. Run the deferred live scenarios — medium impact

Six of the original 15 scenarios were deferred from session 1 with
documented reasons (see `ITERATION_REPORT.md` Phase 4 "Scenarios
deliberately not driven"):

- **08 merge_conflict** — needs an actual `git merge` on the runner
  rather than the in-memory overlay used in scenario 02. Real merge
  semantics will surface either confirmation or a new bug.
- **09 failed_dependency** — pure agent-side; mechanically identical
  to abandon paths already exercised. **Skip unless you want
  belt-and-suspenders coverage.**
- **10 crash_recovery** — requires inducing a workflow crash mid-run.
  Hard to do via MCP. Consider a "panic" command (`crash-after-N`)
  added to the registry.
- **11 webhook_redelivery** — idempotency is unit-tested.
  Re-triggering is hard via MCP. **Lower priority.**
- **14 concurrent_claim** — a true race needs two distinct identities
  (two MCP servers / tokens). Probably out of scope for a single-agent
  build.
- **15 stale_takeover** — requires back-dating `status_ts` by
  ≥7200s. Mechanically a body update; the takeover handshake is
  unit-tested. Forensically uninteresting. **Skip.**

**Recommended**: do 08 and 10. Skip the rest until there's a use case.

### 3. Strengthen `chatty` command default — low impact

Scenario 12 (huge log) discovered that `chatty(20000)` doesn't
trigger chunk rotation under the default config — the output
compresses too well. The session's workaround was to invoke with
`lines=60000`. Either:

- Raise `chatty.py`'s default `lines` to ≥50000, OR
- Pad each line less compressibly so 20000 is enough, OR
- Lower the chunk-size threshold for the test command.

Update scenario 12's spec to reflect whichever fix.

### 4. Build the skills from `retrospective/` — high leverage

PR #50 holds 9 skill specs + an AGENTS.md template spec. None are
implemented. Each `SPEC.md` is self-contained enough to dispatch as
a separate build task.

Recommended build order:

1. **`subagent-prompting`** — foundational for the rest. Quick win.
2. **`agent-dispatch-loop`** — the iterative loop pattern; this
   project's bread and butter.
3. **`parallel-subagent-fanout`** — the workflow the user explicitly
   asked to encode ("I often want this but it's a lot of typing").
4. **`github-mcp-tips`** — high payoff for any future GitHub project.
5. **`live-debug-from-mcp-only`** — pairs with `github-mcp-tips`.
6. **`forensic-vs-aggressive-cleanup`** — needed before the next
   live-execution session.
7. **`spec-vs-implementation-gap-discovery`** — process discipline;
   the most "soft" of the bunch.
8. **`self-retrospective`** — meta-skill. Build last so it can be
   tested on itself.
9. **`polling-without-sleep-in-restricted-sandbox`** — small enough
   to inline if you want.

### 5. Write the actual `AGENTS.md` from the spec — quick win

`retrospective/agents-md-template/SPEC.md` enumerates 15 conventions
to add. The current `AGENTS.md` (this branch) is a starter; the
spec has more rules to harvest.

This is largely mechanical: read the spec, write the file. ~30
minutes of work. Highest leverage relative to time spent.

### 6. Address spec-side nice-to-haves — low impact

Documented in `ITERATION_REPORT.md` Phase 4 "What I'd recommend
next":

- **Drop the `agent_login` Actions-variable indirection** — already
  done in this session as the literal `'jonathanmanton'` in the
  workflow YAML. For multi-user deployment, source from
  `.agent/config.json` at runtime via a setup step.
- **Update SPEC §6 branch model** — already done with the
  "Real-world correction" note. Could be cleaned up to merge the
  correction into the main text.
- **Promote the diagnostic-comment pattern to a first-class spec
  feature** — mentioned in the SPEC's amendments; could be
  formalized as a dedicated section.

These are spec polish, not blocking work.

## Things the next agent should NOT do

- **Don't merge PR #50** unless the user requests it. The user
  reviews skill spec packages before merging — that's part of the
  value of mode B retrospectives.
- **Don't auto-implement skills from `retrospective/`** without
  user direction. Each skill is a separate task.
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
| Skill specs to build | `retrospective/<skill>/SPEC.md` |
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
3. Ask the user which work stream they want next, presenting the
   priority queue from §"What's not done" above.
4. If the user defers, default to:
   - Build `subagent-prompting` skill from
     `retrospective/subagent-prompting/SPEC.md`. It's the quickest,
     highest-utility skill build.

## Provenance

This handoff was written at the end of session 1 by the dispatcher
that built and live-tested the POC. It's the synthesis of:

- `ITERATION_REPORT.md` Phases 1-4
- `harness/RUNS.md` ledger
- The "What I'd recommend next" section at the end of
  `ITERATION_REPORT.md`
- The retrospective skill specs in `retrospective/`

Update this file at the start of each new session with what's
changed; treat it as the project's current-state document.
