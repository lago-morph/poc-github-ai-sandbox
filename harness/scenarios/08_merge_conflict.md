# Scenario 08 — merge conflict, primary abandons

## Objective
Two subagent branches commit conflicting changes to the same file.
The primary attempts to merge with `conflict_strategy="fail"` (the
default in `skills/task-dag/merge.py`), the merge raises
`MergeConflictError`, the primary abandons the issue, and no PR is
opened. This validates SPEC §6 ("merge conflicts are the primary's
responsibility").

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(8, run_id)`.
2. Create `feature` from `main`.
3. Create subagent branches `sub_branches["alpha"]`,
   `sub_branches["beta"]` from `feature`.
4. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) issue (`harness-scenario-08`); claim meta.
5. Commit `conflict.txt` with content `"alpha-version"` on the
   `alpha` subagent branch.
6. Commit `conflict.txt` with content `"beta-version"` on the
   `beta` subagent branch.

## Agent steps
1. Build and post `echo` request envelopes for `alpha` and `beta`.
2. Poll both to terminal `completed`.
3. The dispatcher (or a subagent acting as primary) attempts to merge
   `alpha` and `beta` into `feature`. In the live harness this is done
   by sequentially calling `mcp__github__create_or_update_file` to
   replay each branch's diff onto `feature`; conflict detection is
   performed by reading both branches' versions of `conflict.txt` and
   noticing the divergence. **For scenario 08 the dispatcher must
   detect that the two branches set different content for the same
   path and refuse to merge.**
4. `abandon-meta` with `--reason "merge_conflict_on_conflict.txt"`.

## Workflow expectations
- Both `echo` runs terminate as `completed` independently.
- No PR open/merge attempts are made.

## Assertions
- Both terminal envelopes are `completed`.
- `assert_meta_status(final_body, "abandoned")`.
- The body's `abandon_reason` mentions `merge_conflict`.
- No open PRs head=`feature` (use
  `mcp__github__list_pull_requests`).
- `feature` HEAD is unchanged from before the merge attempt.

## Forensic artifacts
- Issue `N` (abandoned), two completed comments, both subagent
  branches still present (since merge was refused). No PR.
