# Scenario 15 — stale takeover; original agent self-abandons on heartbeat

## Objective
A primary claims an issue and starts working. Its `status_ts` is
artificially back-dated to make it look stale. A successor primary
observes the staleness and takes over by writing a fresh
`agent_id`. When the original agent next attempts to heartbeat, it
must observe the new `agent_id` and self-abandon (its in-process
state).

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(15, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) issue (`harness-scenario-15`).

## Agent steps — primary 1
1. Subagent `primary-1` claims with `agent_id = "p1-<short>"`.
2. Updates issue body via `mcp__github__issue_write`.
3. Pauses (does not yet post a request envelope).

## Agent steps — back-date status_ts (test harness, not protocol)
4. Read issue, parse meta, force `status_ts` to
   `1970-01-01T00:00:00Z`. `replace-meta` and write back.

## Agent steps — primary 2 (successor)
5. Subagent `primary-2` reads the issue, parses meta, sees
   `status="working"` but `status_ts` ancient -> stale.
6. `primary-2` claims with `agent_id = "p2-<short>"` and writes the
   body.

## Agent steps — primary 1 self-abandon
7. The dispatcher invokes `primary-1` again to do a heartbeat:
   - Re-read issue body.
   - Parse meta.
   - Compare `meta["agent_id"]` against `primary-1`'s id.
   - On mismatch: `primary-1` MUST NOT write a heartbeat — it
     self-abandons by exiting cleanly. Log the mismatch.

## Agent steps — primary 2 finalises
8. `primary-2` posts a valid `echo` envelope, polls to terminal,
   `finish-meta`, opens + merges PR.

## Workflow expectations
- Standard `echo` lifecycle for `primary-2`'s comment.

## Assertions
- After step 6, `parse_body(issue['body'])["agent_id"] == "p2-<short>"`.
- After step 7, the issue body is unchanged from step 6 (primary-1
  did not overwrite).
- `assert_meta_status(final_body, "finished")` after step 8.
- `assert_pr_merged(pr)`.

## Forensic artifacts
- Issue `N` (closed, finished). One terminal comment from primary-2.
  One merged PR. No primary-1 comments.
