# Scenario 01 — happy single subagent

## Objective
Drive one subagent through the full agent-job-protocol lifecycle:
issue created with labels and lock, subagent posts an `echo` request,
the workflow handler picks it up, writes a terminal `completed`
envelope plus log/manifest/summary artifacts, and the primary
finalises the issue and merges a clean PR. This is the smoke test for
the entire harness.

## Prereqs
- Workflow side wired up: the GitHub Actions handler for
  `mcp__github` events posts terminal envelopes within the
  `runner_pickup_timeout_seconds` window from `.agent/config.json`.
- Repository has labels `agent-task` and `harness-scenario-01`. Create
  via `mcp__github__issue_write` with `set_labels` on a throwaway
  issue, or accept that the first run defines them.
- `main` branch exists.

## Setup
1. `python -m agent_lib` is callable with the repo on `PYTHONPATH`.
2. Generate `run_id = harness.lib.naming.new_run_id()`.
3. Compute names:
   - `feature = harness.lib.naming.feature_branch(1, run_id)`
   - `sub_id = "alpha"`
   - `sub_branch = harness.lib.naming.subagent_branch(feature, sub_id)`
4. Create branch `feature` from `main` via
   `mcp__github__create_branch`. Capture HEAD sha.
5. Create branch `sub_branch` from `feature` via
   `mcp__github__create_branch`. Capture HEAD sha.

## Agent steps
1. Build the initial agent-meta and body markdown:
   `python -m agent_lib make-initial-meta '{"feature_branch": "<feature>", "base_branch": "main", "instructions_inline": "Run echo and finalise."}' --prose "Harness scenario 01 single subagent run <run_id>."`
2. Create the parent issue via `mcp__github__issue_write` (action
   `create`) with title
   `harness 01 single subagent <run_id>`, body from step 1, labels
   `["agent-task", "harness-scenario-01"]`. Capture issue number `N`.
3. Lock the issue via `mcp__github__issue_write` (action `update`,
   `lock_reason=resolved`) — the protocol gates handler dispatch on a
   locked issue.
4. Read the issue, extract `meta` via `python -m agent_lib parse-meta
   "$(...issue body...)"`.
5. Build claim body:
   `python -m agent_lib claim-meta '<meta-json>' --agent-id <new-uuid>
   --session-id <new-uuid> --prose "<original prose>"`. Update issue
   body with `mcp__github__issue_write`.
6. Build the request envelope:
   `python -m agent_lib make-request '{"message": "hello world"}'
   --command echo --branch <sub_branch> --sha <sub_branch_head>
   --subagent-id alpha`.
7. Post envelope JSON as a comment via `mcp__github__add_issue_comment`.
   Capture comment id `C`.
8. Poll `mcp__github__issue_read` (action `get_comment`) every ~30s.
   For each fetched body run
   `python -m agent_lib parse-comment '<body>'`. Stop when
   `run_status` is `"completed"`. Heartbeat the issue meta between
   polls via `python -m agent_lib heartbeat-meta`.
9. Fetch summary artifact via `mcp__github__get_file_contents` for
   `runs/N/C/summary.json` on the `_agent_runs` branch.
10. Mark the issue `finished` via
    `python -m agent_lib finish-meta` and update the issue body.
11. Open a PR `feature -> main` via
    `mcp__github__create_pull_request`.
12. Merge the PR via `mcp__github__merge_pull_request`.

## Workflow expectations
- Handler validates the envelope, sets `run_status=running` once,
  invokes the `echo` command, and writes the terminal envelope with
  `run_status=completed`, summary `{echoed_args, message}`, plus
  `log_manifest_path=runs/N/C/manifest.json`.
- `_agent_runs/runs/N/C/manifest.json`, at least one
  `log-0001.jsonl.gz`, and `summary.json` exist.

## Assertions
- `harness.lib.asserts.assert_issue_locked(issue)` after step 3.
- `harness.lib.asserts.assert_issue_has_label(issue, "agent-task")`.
- `harness.lib.asserts.assert_envelope_terminal(envelope, "completed")`
  for the polled comment.
- `harness.lib.asserts.assert_summary_matches(summary, {"message":
  "hello world"})`.
- `harness.lib.asserts.assert_meta_status(issue_body_after_finish,
  "finished")`.
- `harness.lib.asserts.assert_pr_merged(pr)` after merge.

## Forensic artifacts
- Issue `N` (closed, finished agent-meta).
- Comment `C` containing the terminal envelope.
- Branches `feature`, `sub_branch` (the latter may have been deleted by
  workflow merge). Branch `_agent_runs` carries `runs/N/C/`.
- One PR (merged).
