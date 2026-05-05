# `agents-md-template` — repo-level conventions spec

> Specification for what to add to `AGENTS.md` (or `CLAUDE.md`) in
> projects like this, so the lessons from this session don't have to
> be relearned.

## Why this exists

`AGENTS.md` is a high-leverage file. A few well-chosen lines save
hours of re-discovery in every future session.

This session produced ~10 conventions that earned their place in
`AGENTS.md` — each grounded in something that went wrong (or nearly
did) without it. The conventions cover:

- Branch naming (avoiding ref-prefix collisions)
- Workflow YAML conventions (don't lock issues that need writes)
- MCP transport quirks (HTML escape, comment trailers)
- Subagent commit-then-stop discipline
- Identity sourcing (don't use placeholder `agent_login`)
- PR / branch coordination (don't force-push mid-PR)

This package is a **spec for AGENTS.md changes**, not the AGENTS.md
itself. A future task will use this spec to:

1. Either add an `AGENTS.md` to a fresh project, OR
2. Augment an existing `AGENTS.md` with the conventions here.

## When this would have helped

Every future project that uses `mcp__github__*` will benefit from
the GitHub MCP-tips conventions. Every project that uses subagents
will benefit from the subagent conventions. Every project with
workflows that talk back will benefit from the lock-vs-bot rule.

In this session, **all of these were learned the hard way**. The
session's `ITERATION_REPORT.md` Phase 4 section narrates each
discovery; this spec turns those discoveries into reusable rules.

## What good looks like

A `AGENTS.md` that:

- Is short (under 200 lines)
- Each rule has a 1-line "do/don't" statement
- Each rule has a 1-2 sentence "why" grounded in real failure
- Skill-cousins are referenced (so the agent can load deeper docs
  if needed)

## Status

- Spec only — see `SPEC.md`.
- A future task will produce the actual AGENTS.md edit using this
  spec.
