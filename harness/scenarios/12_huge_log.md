# Scenario 12 — huge log forces chunk rotation

## Objective
Invoke the `chatty` test command with `lines=20000` so the LogWriter
rotates ≥2 chunks. Verify the manifest's `chunks` array contains
multiple entries and that all of them exist on the `_agent_runs`
branch.

## Prereqs
- `.agent/config.json` includes `"chatty"` in `commands` (added by
  this branch).
- `chatty` schema (`bad-summary` schema's sibling) declares
  `summary_completed` requires `lines_emitted` and `message`.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(12, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + lock + label issue (`harness-scenario-12`); claim meta.

## Agent steps
1. Build envelope::

       python -m agent_lib make-request '{"lines": 20000}' \
         --command chatty \
         --branch <feature> --sha <feature_head> \
         --subagent-id alpha

2. Post envelope as comment.
3. Poll until `completed`. (Heartbeat the issue meta — the run can
   take longer than a quick echo.)
4. Read manifest via
   `mcp__github__get_file_contents`(`runs/N/C/manifest.json`).
5. For each `chunk` in `manifest["chunks"]`, fetch
   `runs/N/C/<chunk.path>` to confirm presence.
6. `finish-meta`, open + merge PR.

## Workflow expectations
- LogWriter rotates after compressed-chunk size exceeds
  `cfg.logs.max_chunk_bytes_compressed` (524 288 default), producing
  multiple `log-NNNN.jsonl.gz` files.

## Assertions
- `assert_envelope_terminal(envelope, "completed")`.
- `summary["lines_emitted"] == 20000`.
- `len(manifest["chunks"]) >= 2`.
- All chunk files exist (each fetch returns content).
- `assert_pr_merged(pr)`.

## Forensic artifacts
- Issue `N`, one terminal comment, log artifacts including ≥2 chunk
  files. One merged PR.
