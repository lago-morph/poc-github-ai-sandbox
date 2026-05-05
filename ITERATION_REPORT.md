# POC Iteration Report

Multi-agent dispatch run that built a proof-of-concept implementation of the
GitHub-Native Agent Job & Task Protocol described in `SPEC.md`.

The dispatcher (a long-running coordinating agent) spawned focused subagents
for each implementation, review, test-writing, test-review, test-execution,
and analysis step. Three full iterations were completed; all tests passed; the
loop exited cleanly per the stop condition (≥3 iterations and all tests
green).

## Summary metrics

| Iter | Impl PR | Test PR | Tests | Coverage | All pass? |
|---:|:---|:---|---:|---:|:---|
| 1 | #1 (initial) | #2 | 67 | 87% | ✅ |
| 2 | #3 | #4 | 110 | 92% | ✅ |
| 3 | #5 | #6 → #7 (re-open) | 177 | 95% | ✅ |

Final aggregate (on `main` after all merges):

- 177 tests, 0 failed, 0 xfail, runtime ~0.25s
- 95% line coverage across `.agent/` and `skills/`
- All three command handlers (`echo`, `build`, `run_tests`) at 100%

## Loop structure

Each iteration ran the seven steps from the dispatch instructions:

1. Implementation (or fix-up) subagent → PR
2. Implementation review subagent → comments / approve
3. Test-writer subagent → PR
4. Test review subagent → comments / approve
5. Test runner → detailed log
6. Failure analysis subagent (skipped when no failures)
7. Continue / exit decision

Subagents were dispatched with self-contained briefs so the dispatcher's
context window stayed focused on coordination.

## Iteration 1

### Goal
Build the protocol's core: schemas, scripts, command handlers, skills, and
workflow YAMLs per `SPEC.md` §2–§10.

### Implementation (PR #1)
- 33 files; full directory layout per spec.
- Six JSON Schemas (Draft 2020-12): issue body, comment envelope (with
  `allOf` for lifecycle phases), log manifest, and three command schemas
  (`run-tests`, `build`, `echo`).
- Scripts: `handler.py`, `lock_and_sweep.py`, `close_on_merge.py`, plus a
  `common.py` exposing a `GitHubClient` Protocol and a fully-functional
  `InMemoryGitHubClient` for tests.
- Skills: `batch-job/{submit,poll}` and `task-dag/{claim,plan,merge,schedule_successors}`.
- Workflow YAMLs for all three triggers, matching §7 verbatim.
- `LogWriter` with gzip rotation and manifest aggregation.

### Implementation review (no blocking issues)
The review approved as-is and called out 9 non-blocking items, including:
- Unknown-command path used `parse_error` (review preferred terminal `error`).
- `commit_sha` schema pattern allowed 7–64 chars but the handler required
  exact match → drift potential.
- `merge.delete_branches` parameter was accepted but never acted on.
- `poll()` did not invoke a heartbeat callback (spec §9.4 step 3).

### Test writing (PR #2) — 67 tests
Coverage across all major components:
- `tests/unit/test_common.py`: parse/render round-trip, schema validation,
  `LogWriter` rotation + gzip + JSONL invariants.
- `tests/unit/test_in_memory_client.py`: full CRUD over issues, comments,
  branches, files, PRs.
- `tests/unit/test_handler.py`: happy paths for `echo` and `run-tests`,
  parse-error and branch/SHA-mismatch flows, idempotency, summary-schema
  violation via monkeypatching.
- `tests/unit/test_lock_and_sweep.py`, `tests/unit/test_close_on_merge.py`.
- `tests/unit/test_skill_batch_job.py`: submit + poll lifecycle, runner-pickup
  and running timeouts using a manual clock.
- `tests/unit/test_skill_task_dag.py`: claim, race-loser self-abandon, stale
  takeover, heartbeat, plan, merge, schedule_successors.
- `tests/e2e/test_full_lifecycle.py`: end-to-end happy path + SHA-mismatch
  recovery scenario.

### Test review
APPROVE with notes: a few assertions were "either-or" permissive (unknown
command, args validation, running timeout); the dependency assertion was a
truthiness check rather than exact list; chunk-size bound was loose. Five
recommendations recorded for iter 2.

### Test run
67/67 pass at 87% coverage. `build.py` had 0% coverage (no test exercised it).

## Iteration 2

### Goal
Address spec gaps surfaced in the iter-1 reviews and broaden test coverage.

### Implementation (PR #3) — tightening
- `commit_sha` and `checked_out_sha` schema patterns tightened to
  `^[0-9a-f]{40}$` (matches the handler's exact-match check).
- Unknown command now writes terminal `run_status: error` with
  `error_kind: unknown_command` (per §5.2.4 reserving `parse_error` for
  envelope-schema violations).
- New `protocol_version != 1` early check writes
  `parse_error` / `error_kind: unsupported_version` (per §13).
- `GitHubClient.delete_branch` added; `merge.py` now defaults to
  `delete_branches=True` and reports a `deleted` list.
- `poll()` accepts an optional `heartbeat: Callable | None` parameter,
  invoked once per cycle (per §9.4 step 3).
- The `__main__` entrypoints in the three scripts now print required env
  vars and exit cleanly.

### Test expansion (PR #4) — 110 tests, 92% coverage
- Pinned the six "either-or" assertions from iter 1 to exact values.
- Added tests for every iter-2 behavior: `unsupported_version`,
  `delete_branch` (existence/idempotency/non-affecting), `poll(heartbeat=…)`,
  short-SHA rejection, `main()` stub env-var reporting.
- New `tests/unit/test_command_build.py` (build at 100%).
- New `tests/unit/test_main_stubs.py` for the three workflow entrypoints.
- Workflow-guard boundary tests document the handler's no-enforcement
  policy (gating lives in the YAML `if:`).
- Merge-conflict test pinned current "last writer wins" behavior; flagged
  as needing iter-3 impl change because §6 says conflicts are the primary's
  responsibility.
- `working → abandoned`-on-displacement coverage; failed-dependency case
  documented as gap pending iter 3.
- LogWriter edge cases: unicode, zero records, single huge record.

### Reviews
Both PRs approved. Test review highlighted that the merge-conflict test
codified a behavior the spec doesn't endorse, and recommended iter 3 should
change the implementation rather than the test.

### Test run
110/110 pass at 92% coverage.

## Iteration 3

### Goal
Implement the most spec-aligned behaviors still outstanding, then expand
tests to lock them in.

### Implementation (PR #5)
- **Merge-conflict detection** (§6). `merge_subagent_branches` now takes a
  `conflict_strategy: Literal["fail", "last-writer-wins", "first-writer-wins"]`
  parameter (default `fail`). The default raises `MergeConflictError` with
  the conflicting paths *before* any branch is merged. The other strategies
  surface conflicts via `result["conflicts"]`. `result["delete_failed"]`
  records branches whose post-merge cleanup raised, replacing the old
  silent `try/except: pass`.
- **Decline path** (§4.1, §12). New `should_decline(client, issue)` in
  `task-dag/plan.py` walks `depends_on_prs` and returns `(True, reason)` if
  any PR is closed-without-merge or missing. New idempotent
  `abandon(client, issue_number, reason)` in `task-dag/claim.py` writes
  `status: abandoned` and posts an "Abandoning: …" comment.
- **Runner-failure issue creation** (§9.4 steps 4-5, §14). `poll()` now
  opens a fresh runner-failure issue (labelled `runner-failure` +
  `agent-task`, body carrying a fresh `agent-meta` with `status: null` and
  the original envelope JSON) before raising `PollTimeout`. Failure to
  create the runner-failure issue is swallowed so it cannot mask the
  underlying `PollTimeout`.
- **Log sanitization** (§14). New `sanitize_record()` in `common.py`
  redacts GitHub tokens (`gh[ps]_…`), AWS access keys (`AKIA…`), Bearer
  tokens, and `api_key|secret|token|password` patterns. Recurses through
  dict / list / tuple values. `LogWriter` invokes it by default; opt-out
  via `LogWriter(sanitize=False)`.
- **`missing_schema` error kind**. The handler now emits a more specific
  `error_kind: missing_schema` when a registered command lacks its schema
  file.
- **`create_issue`** added to the `GitHubClient` Protocol so skills can
  open new issues without reaching for impl-specific helpers.

### Test expansion (PR #6 → re-opened as #7) — 177 tests, 95% coverage
- Merge-conflict matrix: default-fail raises with feature SHA unchanged;
  first-writer-wins; last-writer-wins; three-branch case; disjoint paths;
  delete-branch failure recorded.
- `should_decline` + `abandon` matrix: no-deps / all-merged /
  closed-unmerged / missing PR / open dep; abandon idempotency; abandon on
  null-status issue.
- Runner-failure: pickup-timeout + running-timeout both create the issue;
  `create_issue` raising does *not* mask `PollTimeout`; body contains
  comment id + envelope JSON.
- Sanitization: every secret pattern positively matched and assert that
  non-secret context survives unredacted; `LogWriter` default-on and
  opt-out paths.
- Two new e2e flows: merge-conflict-then-abandon (no PR opened) and
  runner-failure-path (handler intentionally not invoked).

### Reviews
Both PRs approved. Test review verdict: APPROVE; noted that one
sanitization assertion paired inclusion (`***` present) with exclusion
(plaintext absent), and that the e2e merge-conflict test verifies no PR is
created. Three remaining spec gaps were recorded for any future iter 4
(non-blocking): per-issue `base_branch`, delete-vs-modify merge conflict,
`lock_and_sweep` malformed-meta defensive branch.

### Test run
177/177 pass at 95% coverage. No failures. No flakes. Median test runtime
under 0.005s; total wallclock ~0.25s.

## Decision: exit

The dispatch instructions specify: "if all test cases pass and we have gone
through loop at least 3 times, then exit and write detailed report on each
iteration to repository." We are at iteration 3 with 177/177 green, so the
loop exits here.

## Coverage details (final)

```
.agent/commands/build.py                   100%
.agent/commands/echo.py                    100%
.agent/commands/run_tests.py               100%
.agent/scripts/close_on_merge.py            95%
.agent/scripts/common.py                    98%
.agent/scripts/handler.py                   94%
.agent/scripts/lock_and_sweep.py            93%
skills/batch-job/common.py                  78% (relative-import fallback)
skills/batch-job/poll.py                    97%
skills/batch-job/submit.py                  94%
skills/task-dag/claim.py                    97%
skills/task-dag/common.py                   75% (relative-import fallback)
skills/task-dag/merge.py                    94%
skills/task-dag/plan.py                    100%
skills/task-dag/schedule_successors.py      97%
TOTAL                                       95%
```

The 75–78% lines in `skills/*/common.py` are the relative-import fallback
branches that only fire when the parent package import path breaks. They
are unreachable from inside the test process because tests import via the
`pythonpath` setting; the fallback exists to support direct script
invocation from the workflow runner. Worth a future test that fork-execs
the scripts with `cwd=skills/batch-job`, but not blocking for the POC.

## Spec coverage matrix

| §  | Topic | Status |
|----|---|---|
| §2 | Repository layout | ✅ |
| §3 | Identities & access control (lock + label + author) | ✅ |
| §4 | Issue / comment state machines | ✅ (incl. `working → abandoned` via decline) |
| §5 | Schemas (issue body, comment envelope, log manifest, per-command) | ✅ |
| §6 | Branching model + conflict handling | ✅ (3-strategy merge) |
| §7 | Workflows YAML | ✅ |
| §8 | Polling + heartbeat | ✅ (heartbeat callable in poll) |
| §9 | `batch-job` skill | ✅ (incl. runner-failure side-effect) |
| §10 | `task-dag` skill | ✅ (claim, plan, merge, schedule_successors, abandon) |
| §11 | Projects v2 dashboard | n/a — manual UI step, not implementable in code |
| §12 | Failure modes table | ✅ (every entry has matching impl + test) |
| §13 | Versioning + `unsupported_version` | ✅ |
| §14 | Security + log sanitization | ✅ |

## Notable deviations / deferrals

- **Live REST/MCP client implementation is intentionally deferred.** The
  Protocol is fully specified and `InMemoryGitHubClient` covers every
  operation. A REST client can be dropped in without touching any caller.
- **Workflow YAMLs invoke stub `__main__` entrypoints.** Each script's
  `__main__` reports its required env vars and exits 0. Wiring up real
  REST calls is one straightforward adapter module away.
- **Per-issue `base_branch`** support beyond `main` is untested.
- **Delete-vs-modify** is not handled as a merge conflict (only
  modify-vs-modify is detected).

## Process notes

- 9 subagents were dispatched: 3 impl, 3 review, 3 test-write, plus
  inline test-runs at iter 2/3 boundaries.
- One operational mishap mid-iter-3: a stray `git push -f` synced the
  feature branch to `main` before the test PR was merged, which auto-closed
  PR #6 and lost the test commit on the remote. The commit was recoverable
  from the local reflog (`2dc96ca` was still a dangling object), and a
  fresh PR (#7) was opened and merged. No work was lost.
- Total elapsed wallclock for the three iterations: ~70 minutes of
  subagent time (sum of subagent durations). Dispatcher idle time during
  agent runs is not included.

## Final repository state

- `main` HEAD: `6ae826d` (`test(iter3): expanded coverage for iter-3 behaviors`)
- 1265 statements, 58 missed, 95% coverage
- 177 tests, all passing
