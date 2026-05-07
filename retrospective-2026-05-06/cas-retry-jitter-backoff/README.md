# Skill: `cas-retry-jitter-backoff`

## Why this skill matters

Multiple concurrent writers performing compare-and-swap (CAS) on the
same resource — a git ref, an etag-versioned doc, an OCC database
row, an `If-Match`-protected HTTP PUT — race when their retries fire
in the same sub-millisecond window. **No-backoff retry is functionally
equivalent to no retry at all** under N>1 concurrent writers: every
attempt collides with the same competitors, every retry exhausts at
the same time.

The fix is well-known in the distributed-systems literature
(exponential backoff with jitter), but it must be applied
deliberately. A retry loop without jitter creates a synchronized
herd; a retry loop without an exponential base under-allocates
the retry budget; a retry loop without a max cap can hang
indefinitely.

## When it would have helped

**Session 3, scenario 02 (issue #67):** three concurrent
batch-job-handler workflows all attempted to PATCH the
`refs/heads/_agent_runs` ref API. Alpha and gamma succeeded; beta
crashed with `422 Unprocessable Entity` after exhausting all 3
retries in microseconds. Comment 4385451782 stuck in
`run_status: "running"` forever. Self-diagnostic comment surfaced
the traceback inline, which is the only reason the bug was
diagnosable from MCP-only.

**Fix (PR #68):** introduced jittered exponential backoff
(0.5/1/2/4/8/16s base × random `[0.5, 1.5)`), bumped retries 3 → 6,
indirected the sleep through `_retry_sleep` for unit-test stubbing.
Re-ran scenario 02 (issue #69) — all three subagents completed
cleanly, no 422 race.

Without this skill: any system with N concurrent writers to a
single shared CAS-protected resource will race intermittently in
production. The bug is hard to reproduce locally because timing
matters; it shows up in real workloads.

## What "good looks like"

- Every retry call to `client.put_file_contents()` (or any other
  CAS-protected primitive) goes through a helper that:
  - Refreshes the read-side state on every attempt.
  - Sleeps `base * 2^attempt * random(0.5, 1.5)` between attempts.
  - Caps the per-attempt sleep at a sane max (30s default).
  - Allows the sleep to be stubbed for unit tests.
  - Defaults to ≥5 retries (sized for N=3 concurrent writers).
- Unit tests pin the contract: positive sleeps, non-decreasing,
  ≥5 default retries, retries actually re-call the underlying
  function (not bypass head_sha refresh).

## Cousin skills

- [`live-test-after-substantive-merge`](../live-test-after-substantive-merge/) — how to surface this kind of bug.
- [`bug-fix-loop-discipline`](../bug-fix-loop-discipline/) — how to lock the regression closed.
- `retrospective/forensic-vs-aggressive-cleanup` (session 2) — related: when concurrent writers collide on cleanup operations rather than logs.

## Status

**Spec only — no code yet.** The `_retry_put` implementation in
`.agent/scripts/handler.py` is a working reference. SPEC.md
generalizes it.
