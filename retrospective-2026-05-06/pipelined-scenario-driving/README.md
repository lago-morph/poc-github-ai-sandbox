# Skill: `pipelined-scenario-driving`

## Why this skill matters

Live e2e scenarios that finish in tens of seconds each are still slow
to drive serially. The bottleneck is GHA workflow startup latency
(~30-60s per scenario) and the per-scenario polling intervals — not
the actual run time. Driving N scenarios serially can take N × 3
minutes; driving them in pipelined parallel can take ~3 minutes
total.

The skill is non-obvious because not every scenario pipelines
cleanly. Scenarios that share branches, share merge targets, or
share the `_agent_runs` writer race when pipelined and may produce
flaky results. A clean pipelining pass requires identifying which
scenarios commute.

## When it would have helped

**Session 3, Phase 3:** drove 6 forensic-only error scenarios
(03 parse_error, 04 sha_mismatch, 05 unsupported_version, 06
unknown_command, 07 summary_schema_violation, 13 unicode_summary)
in pipelined parallel. Posted 6 envelopes within 30s; waited
3 minutes once; verified all 6 in batch. Total wall time: ~4 minutes.

Serial driving of the same 6 scenarios would have been ~30 minutes
(60s setup + 90s polling × 6 = ~15 min, plus per-scenario
verification time).

The other 5 PR-completing scenarios in the session were driven
serially because each merges to main, and parallel close-on-merge
runs would race branch cleanup.

Without this skill: a regression rerun of all 9 already-tested
scenarios (per Step 3 of the original HANDOFF plan) would have taken
hours. With pipelining of the forensic subset, it took minutes.

## What "good looks like"

- A regression rerun of N scenarios completes in O(slowest scenario)
  wall time, not O(N × scenario time).
- The pipelining decision is explicit and documented per scenario:
  which scenarios commute, which don't, and why.
- A shared timing budget (e.g., 3-minute wait after the last envelope
  posts) covers all scenarios; per-scenario polling is replaced by a
  single batched check.
- Forensic artifacts (issues, comments, log manifests) are captured
  for every scenario regardless of pipelining order.

## Cousin skills

- [`live-test-after-substantive-merge`](../live-test-after-substantive-merge/) — context for when you'd run regressions at all.
- `retrospective/parallel-subagent-fanout` (session 2) — related but
  about subagent execution, not e2e scenario driving.

## Status

**Spec only — no code yet.** The pattern was applied ad-hoc in
session 3's Phase 3. The spec generalizes it for the next session.
