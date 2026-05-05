# `self-retrospective` skill

> Turn a long session into reusable knowledge before it's lost to
> context truncation. Three-part output: phase narrative, skill
> harvest, repo conventions.

## Why this skill

Long sessions accumulate enormous tacit value:

- Bugs you fixed
- Workarounds you invented
- Recurring patterns you typed multiple times
- Operational mishaps you recovered from
- Decisions about what to skip and why
- Discoveries about the runtime / tools / sandbox

If the session ends without harvesting these, they're lost when the
context is compacted. The next time the same problem comes up, the
agent rediscovers it from scratch.

This skill provides a structured way to extract durable lessons
from a session before it ends. The output is **suggestions, not
implementations** — the user picks which lessons survive into
skills, AGENTS.md entries, or other reusable artifacts.

This skill itself is the natural exit step of `agent-dispatch-loop`
and is also the meta-skill that produced this entire `retrospective/`
directory.

## When this would have helped

In this session: at the end of every major phase, but especially:

- **End of Phase A** (3-iteration loop). Already had the iteration
  report; this skill would have additionally surfaced the loop
  pattern itself as a candidate skill.
- **End of Phase B** (live execution). The 7 real-world bugs would
  each have been a candidate AGENTS.md entry, immediately captured.
- **End of session** (now). This is precisely what we did.

The user prompted explicitly for the retrospective; with a skill,
the agent could offer it proactively when long sessions end.

## What good looks like

Output is three sections:

### Part 1 — narrative
Phase-by-phase summary. What happened, what was unplanned, key
decisions, key surprises. Includes a metrics table (subagents
dispatched, PRs, bugs, tests added).

### Part 2 — skill harvest
A list of skill candidates, each with a uniform shape (purpose,
trigger, content, anti-patterns, examples). Detailed enough that
later building from each spec is straightforward.

### Part 3 — repo conventions
One-line rules, suitable for dropping into AGENTS.md / CLAUDE.md.
Each rule is grounded in something that went wrong without it.

Plus: a summary table of all proposed skills with priority + scope.

## When to use this vs the agent-dispatch-loop's exit step

- `agent-dispatch-loop` exits with an **iteration report** — focused
  on what each iteration shipped.
- `self-retrospective` produces a **session-wide retrospective** —
  focused on patterns, lessons, and reusable knowledge.

They're complementary. Iteration report goes in the repo (e.g., as
`ITERATION_REPORT.md`). Session retrospective produces the input to
build new skills (e.g., this `retrospective/` directory).

## Status

- Spec only — see `SPEC.md`.
- This whole directory IS the meta-example of the skill in action.
- No code yet.
