# Scenario 09 — failed dependency, primary declines

## Objective
A primary issue declares `depends_on_prs: [P]` for a PR that gets
closed-without-merge. The primary calls `should_decline` (from
`skills/task-dag/plan.py`) and abandons the issue with reason
`dependency_failed`.

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`.
2. Create branch `dep-feature-<run_id>` from `main`. Commit a
   placeholder file.
3. Open PR `dep-feature-<run_id> -> main`. Capture PR number `P`.
4. Close PR `P` WITHOUT merging via `mcp__github__pull_request_review_write`
   or `mcp__github__update_pull_request` (action `update`,
   `state="closed"`).
5. `feature = feature_branch(9, run_id)`. Create from `main`.

## Agent steps
1. Build initial meta with `depends_on_prs=[P]`:
   `python -m agent_lib make-initial-meta '{"feature_branch":"<feature>","base_branch":"main","instructions_inline":"Should decline","depends_on_prs":[<P>]}'`.
2. Create issue with labels `["agent-task","harness-scenario-09"]`
   (do NOT lock at creation — see SPEC §3). Claim meta.
3. The dispatcher fetches PR `P` via `mcp__github__pull_request_read`
   and observes `state="closed"`, `merged=False`.
4. `abandon-meta` with `--reason "dependency_failed: PR #<P> closed without merge"`.

## Workflow expectations
- No request envelopes posted; no handler dispatch happens for this
  scenario.

## Assertions
- `assert_meta_status(final_body, "abandoned")`.
- `parse_body(final)['abandon_reason']` contains
  `dependency_failed: PR #<P>`.
- No comments matching the protocol envelope shape on issue `N`.
- PR `P` is closed-without-merge (sanity check).

## Forensic artifacts
- Issue `N` (abandoned), one PR (`P`, closed-without-merge), branch
  `dep-feature-<run_id>`, branch `feature`. No protocol comments.
