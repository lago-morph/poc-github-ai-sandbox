# `agent-dispatch-loop` skill

> The 7-step iterated build loop: implement → review → test-write →
> test-review → run → analyze → continue/exit. The dispatcher pattern
> that produced 177 tests at 95% coverage in this session.

## Why this skill

When the user wants substantial work done iteratively — "build X and
keep refining it until tests pass" — the dispatcher needs a stable
loop structure. Without one, each iteration drifts: sometimes you skip
the review, sometimes the test-runner doesn't get full logs, sometimes
the dispatcher loses track of which iteration it's on.

The 7-step loop in this session:

1. Implement (or fix bugs from prior iteration)
2. Review the impl PR
3. Write or expand tests
4. Review the test PR
5. Run all tests with detailed logging
6. Deeply analyze failures (real impl bug? test bug? skip?)
7. Continue / exit decision (configurable stop condition)

Each step is a subagent dispatch. The dispatcher is small: it
sequences the steps, tracks state via TodoWrite, and decides
continue/exit.

## When this would have helped

The user explicitly invoked this loop in this session ("loop at least
3 times then exit if all pass") and it worked cleanly. Without a skill
encoding it, every project that wants this pattern has to re-explain
the 7 steps to the dispatcher each time.

This skill turns "do iterative SDLC on this project" into one
invocation. The dispatcher reads the skill and executes the loop with
the right defaults.

## What good looks like

User: "Build the data pipeline iteratively. Aim for ≥3 loops, exit
when all tests pass."

Skill activates with parameters:
- min_loops = 3
- stop_condition = "all_tests_pass"
- max_loops = 10

Output:
- N PRs (one per iteration's impl + tests)
- A final report (`ITERATION_REPORT.md`-style) summarizing each
  iteration's deltas
- All work merged to main
- The dispatcher's chat shows only summaries; full subagent reports
  archived to disk

## Cousins

- **`parallel-subagent-fanout`** is the *one-shot* variant. This skill
  is the *iterative* variant.
- **`subagent-prompting`** provides the brief-writing patterns each
  step calls into.
- **`self-retrospective`** is what runs at the end of the loop — the
  exit step writes the iteration report.

## Status

- Spec only — see `SPEC.md`.
- No code yet.
