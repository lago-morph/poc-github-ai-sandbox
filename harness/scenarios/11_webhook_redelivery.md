# Scenario 11 — webhook redelivery is idempotent

## Objective
Post a single envelope, let the handler write a terminal envelope,
then trigger handler re-processing of the SAME comment (simulated by
re-posting the same comment edit, or by manually re-dispatching the
workflow). Verify the handler's idempotency check
(`is_terminal_run_status` early-return) does not produce duplicate
log chunks or replace `summary.json`.

## Prereqs
- Same as scenario 01.
- The workflow can be manually re-dispatched against an already-terminal
  comment. If that's not wired, this scenario substitutes "edit the
  comment with byte-equal content" to avoid changing the body. The
  handler's `noop` branch (`already_terminal`) protects against this.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(11, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) issue (`harness-scenario-11`); claim meta.

## Agent steps
1. Post valid `echo` request as a comment. Capture comment id `C`.
2. Poll until terminal (`completed`).
3. Capture the artifact list under `runs/N/C/` via
   `mcp__github__get_file_contents` listing or by reading the
   manifest's `chunks` array. Record:
   - `manifest_v1 = manifest body bytes`
   - `chunk_paths_v1 = sorted list of chunk paths`
   - `summary_v1 = summary.json bytes`
4. Trigger redelivery:
   - Preferred: re-dispatch the workflow against the same `(N, C)`
     pair.
   - Fallback: edit the comment to itself (post the same body text via
     `mcp__github__add_comment_to_pending_review` — DOES NOT APPLY for
     issue comments; instead use the issue-comment update flow if
     wired, otherwise SKIP this fallback and document the limitation).
5. Wait `runner_pickup_timeout_seconds` worth of polling.
6. Re-fetch artifacts; record `manifest_v2`, `chunk_paths_v2`,
   `summary_v2`.
7. `finish-meta` and merge the PR (`feature -> main`).

## Workflow expectations
- On the second invocation the handler reads the comment, sees
  `is_terminal_run_status(parsed["run_status"])`, and returns
  `{action: "noop", reason: "already_terminal"}` WITHOUT writing new
  artifacts.

## Assertions
- `manifest_v2 == manifest_v1` (byte equality).
- `chunk_paths_v2 == chunk_paths_v1`.
- `summary_v2 == summary_v1`.
- `assert_envelope_terminal(envelope, "completed")` (still completed,
  not flipped back to running).
- `assert_pr_merged(pr)`.

## Forensic artifacts
- Issue `N`, comment `C`, exactly one set of `runs/N/C/` artifacts,
  one merged PR.
