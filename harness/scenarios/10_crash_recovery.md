# Scenario 10 — primary crash + successor takeover

## Objective
A primary claims an issue, posts one comment, and "crashes" (the
subagent simulating crash simply stops without finalising). A second
primary later notices the stale `status_ts`, takes over, completes
the work, and finishes the issue. Validates SPEC §10's crash-recovery
flow.

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(10, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) issue (`harness-scenario-10`).

## Agent steps — primary 1 (crash simulation)
1. `claim-meta` with `agent_id = "primary-1-<short>"`. Update issue.
2. Post one valid `echo` envelope as a comment.
3. Poll briefly (one cycle) — DO NOT wait for terminal.
4. STOP. Do not finalise, do not abandon. The subagent process
   terminates here.

## Agent steps — back-date status_ts
The dispatcher (acting as test harness, not as a protocol agent)
forces the issue's `status_ts` into the past so that the next
claimant sees it as stale.

5. Re-fetch issue body via `mcp__github__issue_read`.
6. Parse meta via `python -m agent_lib parse-meta`.
7. Modify `status_ts` to a timestamp older than
   `cfg.issue.stale_seconds` (default 7200s) — for live runs use
   `1970-01-01T00:00:00Z`.
8. Render new body via `python -m agent_lib replace-meta` with the
   modified meta, and update the issue.

## Agent steps — primary 2 (successor)
9. Spawn a fresh subagent. It calls
   `mcp__github__issue_read`, parses meta, sees
   `status="working"` but `status_ts` ancient -> stale.
10. `claim-meta` with a NEW `agent_id`. Update issue.
11. Re-read issue, verify `agent_id` matches the new one.
12. Poll the original comment to terminal (the workflow already
    processed it, so the comment is already terminal — see
    'Workflow expectations').
13. `finish-meta`. Update issue.
14. Open + merge a PR `feature -> main`.

## Workflow expectations
- The handler picks up the comment posted in step 2 and writes the
  terminal envelope independently of the agent crashing — handler
  dispatch is decoupled from agent presence.

## Assertions
- After step 11, `parse_body(issue['body'])["agent_id"]` equals the
  new agent id.
- `assert_envelope_terminal(envelope, "completed")` for the
  comment posted in step 2.
- `assert_meta_status(final_body, "finished")`.
- `assert_pr_merged(pr)`.

## Forensic artifacts
- Issue `N` (closed, finished), one terminal-completed comment, one
  PR (merged). Branches as in scenario 01.
