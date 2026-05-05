# Retrospective skill packages

This directory contains **specs for skills**, not the skills themselves.
Each subdirectory is a self-contained package that a future build pass can
turn into a Claude Code skill (or equivalent).

## Why this exists

A long session produced ~7 hours of agent work and surfaced patterns,
workarounds, and lessons that are valuable across future projects. Rather
than let those evaporate when the session is compacted, we capture each one
as a structured spec with:

- `README.md` — human-readable motivation: why does this skill matter?
  When would it have helped? What pain does it remove?
- `SPEC.md` — implementation-grade detail: trigger conditions, core
  content, anti-patterns, examples, and any code or templates the skill
  should ship with.
- `excerpts.jsonl` (where useful) — actual session-recorded evidence
  (errors, fixes, prompts) that motivates and concretizes the skill.

The user reviews this package, picks which to build, and dispatches
implementation tasks with each `SPEC.md` as the brief. **No skills are
implemented in this branch.**

## Skill index

| Priority | Skill | One-line summary |
|----------|-------|------------------|
| high | [`agent-dispatch-loop/`](./agent-dispatch-loop/) | The 7-step impl/review/test-write/test-review/run/analyze loop |
| high | [`github-mcp-tips/`](./github-mcp-tips/) | Quirks, gaps, and workarounds for the GitHub MCP server |
| high | [`subagent-prompting/`](./subagent-prompting/) | Patterns that produce useful subagent work without burning context |
| high | [`self-retrospective/`](./self-retrospective/) | Turn a long session into reusable knowledge before it's lost |
| high | [`parallel-subagent-fanout/`](./parallel-subagent-fanout/) | Plan → branch → fan out → merge → PR — invokable end-to-end |
| medium | [`live-debug-from-mcp-only/`](./live-debug-from-mcp-only/) | Debugging CI when you can't read the logs |
| medium | [`forensic-vs-aggressive-cleanup/`](./forensic-vs-aggressive-cleanup/) | Managing artifacts on real systems |
| medium | [`spec-vs-implementation-gap-discovery/`](./spec-vs-implementation-gap-discovery/) | Why live runs catch bugs unit tests can't |
| low | [`polling-without-sleep-in-restricted-sandbox/`](./polling-without-sleep-in-restricted-sandbox/) | A small recurring pattern |

## Repo-level conventions

| | | |
|---|---|---|
| | [`agents-md-template/`](./agents-md-template/) | Spec for AGENTS.md additions that capture session-wide lessons |

## How to consume this package

A future task that wants to build skill `<X>`:

1. Read `retrospective/<X>/README.md` for the human-level motivation.
2. Read `retrospective/<X>/SPEC.md` for the implementation brief.
3. Skim `retrospective/<X>/excerpts.jsonl` (if present) for concrete
   evidence to test the skill against.
4. Build the skill in the appropriate location for the harness (e.g.
   `~/.claude/skills/<x>/SKILL.md` for Claude Code skills, or wherever
   the target system's skill registry lives).
5. The spec is intended to be self-contained — a fresh subagent should
   be able to build the skill from it without needing this session's
   conversation history.

## Provenance

All material in this directory derives from a single multi-day session
implementing the GitHub-Native Agent Job & Task Protocol. The session's
narrative is in `ITERATION_REPORT.md` at the repo root; this directory
distills its lessons into reusable form.
