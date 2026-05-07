# Skill: `live-test-after-substantive-merge`

## Why this skill matters

A merge that introduces new control-plane code (config sourcing, retry
policy, schema dispatch order, env-var propagation) commonly passes
all unit tests AND silently breaks the deployment env. The bug
surface is in the runtime, not the code: a repo variable not set, an
env var not propagated, a workflow YAML that takes effect only after
merge to default branch.

Unit tests cannot see those gaps. The fastest way to surface them is
to drive a live happy-path scenario within minutes of the merge —
before any other work piles on, and while context is fresh enough to
diagnose.

## When it would have helped

**Session 3, 2026-05-06:** PR #54 merged session-3 changes (including
removal of `agent_login` from config and a switch to `vars.AGENT_LOGIN`).
All 437 unit tests passed on the merged main. First live scenario
(scenario 01, issue #55) created an issue and waited for the
`agent-task` label that lock-and-sweep applies. **Stalled for 4+
minutes** — `vars.AGENT_LOGIN` was not set on the canonical repo, the
env var passed to the script was empty, the script exited 1 silently.

Diagnosed by elimination in ~10 minutes (workflow logs auth-walled,
no diagnostic comment because `return 1` doesn't trigger the
self-diagnostic path). Fixed via PR #56 in 6 minutes
(`${{ vars.AGENT_LOGIN || 'jonathanmanton' }}` literal fallback +
unit tests pinning the fallback in YAML). Live scenario 01 retry
(issue #57) succeeded in 3 minutes.

Without this skill: the bug would have shipped to a fresh deployment
and presented as "the protocol just doesn't work" with no obvious
diagnostic.

## What "good looks like"

- Within 10 minutes of merging a substantive PR, the simplest live
  happy-path scenario for the affected subsystem has been driven and
  reached its expected terminal state.
- If anything stalls or fails, the bug-fix loop kicks in:
  hypothesis → failing unit test → fix → re-run live scenario.
- Forensic artifacts (issues, PRs, log manifests on `_agent_runs`)
  are preserved so the next session can audit what happened.
- Scenarios that previously worked are re-driven as regressions,
  cheap given the infra is already set up.

## Cousin skills

- [`bug-fix-loop-discipline`](../bug-fix-loop-discipline/) — what to
  do once the live test fails.
- [`pipelined-scenario-driving`](../pipelined-scenario-driving/) —
  how to amortize the cost across multiple scenarios.
- `retrospective/spec-vs-implementation-gap-discovery` (session 2) —
  related but distinct: that skill is about *types* of gaps; this
  skill is about *when* to look.
- `retrospective/live-debug-from-mcp-only` (session 2) — what to do
  when the live test fails and you can't read workflow logs.

## Status

**Spec only — no code yet.** See `SPEC.md` for the implementation brief.
