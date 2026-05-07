# retrospective-2026-05-06 — session 3 live-testing harvest

This directory holds skill specs and an `AGENTS.md` template harvested
from session 3's live-testing run on 2026-05-06. Specs only — **no
implementation code** lives here. A future agent can build any of these
by treating the corresponding `SPEC.md` as a self-contained brief.

The earlier `retrospective/` directory holds session-2's harvest
(different skills, no overlap). Both are kept side-by-side so each
session's lessons stay traceable to the session that produced them.

## Skill index

| Directory | Priority | One-line summary |
|-----------|----------|------------------|
| [`live-test-after-substantive-merge`](./live-test-after-substantive-merge/) | high | Drive live e2e immediately after merging non-trivial control-plane changes — unit tests pass on broken deployments. |
| [`cas-retry-jitter-backoff`](./cas-retry-jitter-backoff/) | high | Concurrent compare-and-swap retry with jittered exponential backoff. Without jitter, no-backoff retry is functionally equivalent to no retry. |
| [`yaml-literal-fallback`](./yaml-literal-fallback/) | med | `${{ vars.X || 'literal' }}` keeps GHA workflows functional on fresh deployments before admin sets the repo variable. |
| [`pipelined-scenario-driving`](./pipelined-scenario-driving/) | med | Issue many e2e scenarios in parallel, then poll en masse — cuts wall time roughly N× for non-conflicting scenarios. |
| [`bug-fix-loop-discipline`](./bug-fix-loop-discipline/) | high | Hypothesis → failing unit test → fix → unit test passes → re-run e2e. Locks regressions closed; applied twice this session, caught two real bugs. |
| [`agents-md-template`](./agents-md-template/) | — | 12 do/don't rules harvested from session 3 events, ready to drop into the project's `AGENTS.md`. |

## How to consume this package

- **For each skill you want to build:** read its `README.md` for motivation and the "good looks like" example, then use `SPEC.md` as the implementation brief. Spawn a subagent with the `SPEC.md` as the brief — the spec is detailed enough that the subagent does not need access to the original session.
- **For the AGENTS.md additions:** review `agents-md-template/SPEC.md`. Each rule is grounded in a session event with a one-line provenance phrase, so you can evaluate them individually.
- **Cross-references:** these skills are cousins to several entries in the older `retrospective/` directory. Each `README.md` lists its cousins; honor those when implementing to avoid duplication.

## Provenance

Authored at the end of session 3 by the agent that drove 11 live
scenarios (issues #57-#71, PRs #56/#58/#66/#68/#72/#73/#74/#75) on
the canonical `lago-morph/poc-github-ai-sandbox` repository. The
session-3 inline retrospective in chat is the source material; this
package mirrors Part 2 (skills) and Part 3 (AGENTS.md) of that
retrospective into per-skill files.

Status: spec only — none of these skills have been implemented yet.
