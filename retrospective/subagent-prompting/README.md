# `subagent-prompting` skill

> Patterns that produce useful subagent work without burning the
> dispatcher's context. The brief-writing rules that emerged from
> ~14 subagent dispatches in this session.

## Why this skill

A subagent has zero context. It hasn't seen the conversation, doesn't
know what's been tried, doesn't know the conventions. Every
unspecified detail is a coin flip — sometimes the subagent guesses
right, sometimes it scope-creeps, sometimes it picks a different
approach than the dispatcher wanted.

A 200-word brief that's vague produces a different result than a
600-word brief that's precise. The difference is whether the
dispatcher can use the result or has to redo the work.

This skill encodes:

- The **structure** of a useful brief
- **Constraints** that almost always belong (don't refactor, don't
  add features, etc.)
- **Deliverable specs** that prevent ambiguous "done"
- **Length budgets** for both the brief and the report
- The **parallel vs serial** dispatch decision

## When this would have helped

Direct examples from this session:

- The **iter 2 test-writer subagent** received a ~1500-word brief
  with explicit pinning targets, new-behavior tests, build coverage,
  workflow-guard tests, edge cases. It produced 110 tests in one
  shot. A vaguer brief would have produced "more tests" without
  hitting the specific gaps.
- The **debug-workflow-non-execution subagent** got a brief that
  enumerated **7 hypotheses** to investigate plus an explicit
  pivot-if-stuck instruction. It found the root cause (lock-vs-bot)
  in ~13 minutes. Without the hypothesis list it would have spelunked
  for an hour.
- A **scenario-running subagent** got a ~2000-word brief with
  per-scenario steps, naming conventions, expected terminal states,
  and a "what to do on each failure mode" matrix. It drove 3
  scenarios end-to-end with no clarification round-trips.

In contrast, the **lock-vs-bot fix subagent** ran out of usage
mid-task partly because its brief was too ambitious (multiple file
changes + spec amendments + test updates). A tighter scoping would
have gotten further.

## What good looks like

A subagent brief that:

- Restates the goal in 1-2 sentences
- Names the exact files/branches involved
- Lists exact deliverables ("commit + push to <branch>; open PR
  via mcp tool with title X; report PR# + test count")
- Caps both the work and the response
- Explicitly excludes scope expansions
- Tells the subagent what to do on common failure modes
- Provides traps and known footguns (e.g., "if pytest can't import
  jsonschema, run X first")

## Cousins

- **`agent-dispatch-loop`** uses these patterns at every step.
- **`parallel-subagent-fanout`** uses them to template the per-subagent
  briefs from a Plan dict.
- **`self-retrospective`** is invoked AFTER the subagent dispatch loop
  is done.

## Status

- Spec only — see `SPEC.md`.
- Examples in `examples/` showing good vs bad briefs from this
  session.
- No code yet.
