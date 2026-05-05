# Bitbucket adapter — decision package

You are a fresh agent session. Your job in this session is **NOT to
implement** the Bitbucket adapter. Your job is to drive a structured
conversation that helps the user decide *which* adapter to build.

## How to use this package

Read these files in order:

1. `README.md` — this file (the procedure)
2. `POC-REVIEW.md` — instructions for reviewing the as-built GitHub POC
   *first*, before consulting any prior research
3. `BACKGROUND.md` — consolidated research from earlier sessions
   (Bitbucket / Jira / Confluence facts as of May 2026; do not redo
   this research unless something looks stale)
4. `ALTERNATIVES.md` — five candidate adapter shapes, A through E
5. `DECISION-QUESTIONS.md` — the questions to walk the user through
6. `OUTPUT-TEMPLATE.md` — the document structure your final synthesis
   should follow

Then drive the conversation as described under "Procedure" below.

## Procedure

### Step 1 — POC review (mandatory first step)

Before reading `BACKGROUND.md` or `ALTERNATIVES.md`, follow
`POC-REVIEW.md`. The GitHub POC was in progress when this package was
written. The point of the review is to surface anything the POC
discovered (workarounds, schema changes, unexpected MCP behaviours)
that should inform the Bitbucket design.

Write your findings into a section in your final document called "POC
deltas." If the POC matches `SPEC.md` exactly, say so. If it deviates,
note each deviation, where, and why (from commit messages or
`ITERATION_REPORT.md` if present).

Open the conversation with the user by reporting the POC deltas, BEFORE
asking any other questions. This grounds everything that follows.

### Step 2 — Confirm assumptions still hold

Briefly summarise the load-bearing facts from `BACKGROUND.md` and ask
the user whether any have changed since the brief was written. The
following are the ones most likely to drift:

- Bitbucket Cloud Issues sunset date.
- Atlassian Rovo MCP coverage of Bitbucket Cloud (especially issues
  tracker support, which was missing in May 2026).
- Free-tier limits for Jira Software, Bitbucket, Confluence.
- Pipelines build-minute caps on Free.

If anything has changed, run a brief web search to confirm before
proceeding. Otherwise carry on.

### Step 3 — Walk the decision questions

Use `DECISION-QUESTIONS.md` as the question script. Ask one
decision-cluster at a time; do not dump the whole list. After each
answer:

- Reflect back what you heard ("OK, so Jira is in scope but Confluence
  is not.").
- Note which alternatives in `ALTERNATIVES.md` survive and which are
  eliminated.
- Tell the user which question is next and why it matters.

If the user pushes back or seems uncertain, slow down. The goal is a
decision the user is confident in, not a fast traversal.

### Step 4 — Probe the awkward parts

Some answers will reveal trade-offs the user may not have weighed.
Specifically test:

- If they said "Bitbucket-only," confirm they understand the
  PR-as-task-record consequences (no separate "task without code yet"
  state; first commit must precede first job).
- If they said "Jira-yes, Confluence-no," confirm they understand the
  Jira Description field is the only place for long-form briefs, with
  Jira's editor limitations.
- If they said "all three Atlassian products," confirm they understand
  the user-cap maths on Free tier with their team size + agent service
  accounts.
- If they said anything that requires Pipelines triggering on Jira
  events, confirm they understand the Jira-Automation-as-relay design
  and have an Atlassian admin who can configure it.

### Step 5 — Synthesise

Produce a final document at `proposals/bitbucket-adapter/DECISION.md`
following `OUTPUT-TEMPLATE.md`. Commit it. Tell the user it's ready and
that a separate, future agent session can implement against it.

Do NOT begin implementation. Do not modify any code. Do not write any
new driver. The implementation pass is a separate exercise scoped from
your output document.

## Tone and pacing

- This is a planning conversation, not a code review.
- Speak in trade-offs, not absolutes.
- When the user makes a decision, write it down — do not trust it will
  survive the rest of the conversation. The synthesis at the end
  should feel like recapitulation, not new content.
- Short messages. One decision-cluster per turn.

## What if the user is partway through a different decision

If the user enters this conversation already leaning toward a specific
alternative, start there: skip to the relevant cluster of decision
questions, but still complete Step 1 (POC review) so the conversation
is grounded in the actual POC, not the SPEC's idealised design.

## What success looks like

A `DECISION.md` document that:

- Names a single chosen alternative (one of A–E or a clearly described
  hybrid).
- Lists the user's answers to each decision cluster.
- Lists open questions that came up but were deferred.
- Lists "POC deltas" the implementation must respect.
- Lists Atlassian admin / configuration prerequisites.
- Is short enough that a future implementation agent can read it in
  five minutes and produce a refined implementation brief.

If you cannot reach a single named alternative — because the user
genuinely needs more time, or because a load-bearing fact has changed
and needs research — produce `DECISION.md` documenting the impasse and
what would resolve it. Do not force a decision.
