# `parallel-subagent-fanout` skill

> A single-trigger orchestration that turns "I want to do <X> in parallel"
> into: feature branch → plan → packaged subagent specs → per-subagent
> sub-branches → dispatch → wait → merge → PR with run report.

## Why this skill

This is the workflow the user said they reach for **constantly** but is
"a lot of typing each time." Every time, the dispatcher has to:

1. Figure out the right feature branch name
2. Decompose the task into independent subtasks
3. Write a self-contained brief for each subagent (with the same
   conventions, the same don'ts, the same deliverable shape)
4. Create a sub-branch per subagent (with the right separator —
   `--sub-` not `/sub-`, learned the hard way)
5. Dispatch them in parallel via the agent tool
6. Wait for completions (notifications arrive asynchronously)
7. Merge each subagent branch into the feature branch
8. Reconcile any conflicts
9. Open a PR from feature → main with `Closes #N`
10. Write a run report capturing what each subagent did and any issues

That's 10 mechanical steps that are *the same every time*. A skill
collapses them into a single invocation: "fan this out into 4 parallel
pieces and report back."

## When this would have helped (in this session)

Several phases naturally fit this pattern but were orchestrated ad-hoc:

- **Phase 1 + Phase 0** (parallel): RestGitHubClient + agent_lib helpers.
  Two subagents, disjoint files, ~10 minutes of dispatcher coordination
  to get them committed cleanly. With this skill: one invocation.
- **Wave 1 scenarios (03, 04, 05)**: three near-identical "post a
  malformed comment, verify terminal envelope" runs. The dispatcher
  wrote one big prompt that drove all three sequentially; with this
  skill they could have run in parallel against three fresh issues,
  cutting wall time by ~3x.
- **Branch cleanup pass**: 28 branches needed deletion via the cleanup
  workflow. The subagent that did it pushed 12 PRs serially. Parallel
  fan-out (one subagent per branch family) would have been ~4x faster.

In all three cases, the dispatcher manually re-typed conventions
(branch naming, "don't refactor", "report back PR# + test count") that
this skill would have boilerplated.

## What this skill removes

- The "did I remember to commit before push?" anxiety (the skill's
  template includes the commit step)
- The "did I get the branch separator right?" footgun (the template
  uses `--sub-`)
- The merge step (`merge.py` in `task-dag` exists but is fiddly to
  invoke; the skill wraps it)
- The boilerplate of writing a self-contained brief 4 times when the
  conventions are 90% identical

## What good looks like

User: "Build out the four CRUD endpoints in parallel and PR them."

Skill activates. Outputs:

- A plan dict with 4 subtasks
- 4 sub-branches created off `feat/crud-endpoints` (or whatever the
  feature branch is)
- 4 subagents dispatched concurrently, each with a self-contained brief
- A polling loop that batches notifications until all complete
- A merge step that consolidates the 4 sub-branches into the feature
  branch (reporting any conflicts)
- A PR opened with `Closes #N` and a run-report appendix listing what
  each subagent built

User reviews the PR, optionally tweaks, merges. Total dispatcher work:
the initial sentence.

## Cousins

- **`agent-dispatch-loop`** is the *iterative* variant (impl → review →
  test → review → run → analyze, loop N times). This skill is the
  *one-shot fan-out* variant.
- **`subagent-prompting`** provides the brief-writing patterns this
  skill calls into.
- **`forensic-vs-aggressive-cleanup`** governs what happens to
  sub-branches after merge (auto-delete on PR merge by default).

## Status

- Spec only — see `SPEC.md`.
- Examples and templates in this directory.
- No code yet.
