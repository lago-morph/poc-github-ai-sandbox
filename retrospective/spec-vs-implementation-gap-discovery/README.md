# `spec-vs-implementation-gap-discovery` skill

> Why running scenarios live catches bugs unit tests can't, and how
> to do that systematically.

## Why this skill

Unit tests are a measurement of **the implementation against the
spec as you understood it**. They cannot catch:

- Spec defects (the design itself is broken)
- Transport quirks (real APIs behave differently than the mock)
- Identity / permission asymmetries (who can do what differs from
  what you assumed)
- Naming collisions in real namespaces (filesystems, refs, indexes)
- Real timing (webhook latency, queue delays, rate limits)
- Defaults that turn out to be wrong under load

This session demonstrated this dramatically: 380 unit tests passing
at 95% coverage didn't catch the **lock-vs-bot** spec contradiction.
That bug only surfaced when the protocol was driven against real
GitHub.

The skill encodes the discipline of **a separate live-execution
phase** beyond unit tests, plus the patterns for what to look for
and how to capture findings.

## When this would have helped

Direct example: this session's Phase 4 was driven by user push-back
("you're testing python, not really using it"). Without that prompt,
the project would have shipped with 7 latent bugs and a spec
contradiction that made it actually unusable.

A skill that says "after unit tests pass, do live execution" — and
provides the structure for it — turns this from a happy accident
into a routine phase.

## What good looks like

- A clear distinction in the project plan between "unit/integration
  testing against mocks" and "live execution against real
  systems."
- A scenario library that exercises each architecturally-distinct
  code path (not just permutations of the same path).
- For each scenario, explicit pre-conditions, expected post-conditions
  in the **real system**, and assertions written against real-system
  state.
- A discipline of annotating spec with "real-world correction" notes
  when discoveries change the design.

## Cousins

- **`live-debug-from-mcp-only`** — when scenarios fail, this is how
  you find out why.
- **`forensic-vs-aggressive-cleanup`** — failed scenarios should
  leave artifacts; this skill specifies that.
- **`agent-dispatch-loop`** — live execution can be one phase of
  the loop's iteration.

## Status

- Spec only — see `SPEC.md`.
- No code yet.
