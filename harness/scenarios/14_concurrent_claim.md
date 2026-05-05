# Scenario 14 — concurrent claim race; only one wins

## Objective
Two primaries attempt to claim the same null-status issue without
delay. The CAS handshake (read meta, write claim, re-read, verify
`agent_id`) must allow only one to win; the loser observes that its
claim was clobbered and self-abandons.

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(14, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + lock + label issue (`harness-scenario-14`). DO NOT claim
   yet.

## Agent steps
1. The dispatcher spawns two subagents `primary-A` and `primary-B`
   simultaneously (parallel tool calls).
2. Each:
   a. Reads issue body via `mcp__github__issue_read`.
   b. Parses meta via `python -m agent_lib parse-meta`.
   c. Builds claim body with its OWN `agent_id` via `claim-meta`.
   d. Writes the body via `mcp__github__issue_write` (action
      `update`).
   e. Re-reads the issue, parses meta, compares `agent_id`.
3. The winner observes its own `agent_id` and continues.
4. The loser observes the other agent's `agent_id` and abandons its
   plan WITHOUT writing further to the issue.
5. The winner posts a valid `echo` envelope, polls to terminal,
   `finish-meta`, opens + merges PR.

## Workflow expectations
- Standard `echo` lifecycle for the winner.

## Assertions
- After the dust settles, `parse_body(issue['body'])["agent_id"]`
  equals exactly one of the two subagents' agent ids (the winner).
- The loser must NOT have left a stale agent-id in the body.
- The loser's local `should_proceed` flag (its own bookkeeping)
  is False.
- Final state: `assert_meta_status(final_body, "finished")`.
- `assert_pr_merged(pr)`.

## Forensic artifacts
- Issue `N` (closed, finished), one terminal comment from the winner,
  one merged PR. No artifacts from the loser.
