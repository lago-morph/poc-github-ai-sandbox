# Scenario 02 — multi subagent (3 under one primary)

## Objective
Drive three subagents (`alpha`, `beta`, `gamma`) under one primary
issue. Each posts its own `echo` envelope on its own subagent branch.
The primary fans-out, polls every comment to terminal, merges the
three subagent branches into the feature branch, then opens and
merges a PR.

## Prereqs
- Same as scenario 01.
- Label `harness-scenario-02` exists or will be created.

## Setup
1. `run_id = new_run_id()`.
2. `feature = feature_branch(2, run_id)`.
3. For each `sub_id` in `["alpha", "beta", "gamma"]`:
   `sub_branches[sub_id] = subagent_branch(feature, sub_id)`.
4. Create `feature` from `main` via `mcp__github__create_branch`.
5. Create each subagent branch from `feature`.
6. Commit a distinct file on each subagent branch via
   `mcp__github__create_or_update_file` (e.g. `alpha.txt`, `beta.txt`,
   `gamma.txt`) so the merge has substantive content. Capture each
   branch's new HEAD sha.

## Agent steps
1. `make-initial-meta` for the primary issue with `feature_branch =
   feature`. Create issue, lock it, label
   `["agent-task","harness-scenario-02"]`. Capture issue `N`.
2. `claim-meta` and update issue body.
3. For each subagent (sequentially is fine for the POC):
   a. Build request envelope with `--command echo --branch <sub_branch>
      --sha <sub_head> --subagent-id <sub_id> --args
      '{"message":"hello from <sub_id>"}'`.
   b. Post envelope as a comment via `mcp__github__add_issue_comment`.
      Capture comment id.
4. Poll each comment to `run_status="completed"`. Heartbeat once per
   poll cycle via `python -m agent_lib heartbeat-meta`.
5. After all three are completed, no merge of subagent branches into
   feature is exercised here (the in-memory merge logic is unit-tested
   elsewhere); the dispatcher just opens the PR `feature -> main`.
6. `finish-meta`, update issue body.
7. Create PR via `mcp__github__create_pull_request`. Merge via
   `mcp__github__merge_pull_request`.

## Workflow expectations
- Handler picks up each comment independently and emits a terminal
  `completed` envelope with the matching `subagent_id` in the
  envelope.

## Assertions
- All three terminal envelopes have `run_status=="completed"`.
- For each, `summary.message == "hello from <sub_id>"` (use
  `assert_summary_matches`).
- `assert_meta_status(final_body, "finished")`.
- `assert_pr_merged(pr)`.
- Three distinct comment ids (no de-dupe collisions in `_agent_runs`).

## Forensic artifacts
- Issue `N`, three completed comments, three subagent branches
  (still present unless merge step deleted them — depends on workflow
  config; assertion above does not require deletion).
- PR (merged), `_agent_runs/runs/N/{C1,C2,C3}/`.
