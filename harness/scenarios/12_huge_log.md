# Scenario 12 — huge log forces chunk rotation

## Objective
Invoke the `chatty` test command with `lines=500,
max_chunk_bytes_compressed=8192` so the LogWriter rotates ≥2 chunks
under a *test-only* reduced threshold. Verify the manifest's `chunks`
array contains multiple entries and that all of them exist on the
`_agent_runs` branch.

## Design note — why the threshold is overridden per-invocation
Live execution showed that forcing rotation at the production default
(`logs.max_chunk_bytes_compressed: 524288`) required ~20 000 lines,
which was unreliable and slow on real GitHub Actions runners. Rather
than weaken the production default, the `chatty` command accepts a
`max_chunk_bytes_compressed` arg and calls
`LogWriter.set_max_chunk_bytes(...)` at the top of its run. The
production default in `.agent/config.json` is preserved (524 288 bytes)
for every non-test command path; only `chatty` overrides the value,
and only for its own LogWriter instance.

## Prereqs
- `.agent/config.json` includes `"chatty"` in `commands` (added by
  this branch) and keeps `logs.max_chunk_bytes_compressed: 524288`.
- `chatty` schema declares args `lines` and
  `max_chunk_bytes_compressed`, and `summary_completed` requires
  `lines_emitted` and `message`.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(12, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) issue (`harness-scenario-12`); claim meta.

## Agent steps
1. Build envelope::

       python -m agent_lib make-request \
         '{"lines": 500, "max_chunk_bytes_compressed": 8192}' \
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
- LogWriter rotates after the *per-invocation* compressed-chunk size
  exceeds the value supplied in `args.max_chunk_bytes_compressed`
  (8 192 bytes here), producing multiple `log-NNNN.jsonl.gz` files.
- The production `cfg.logs.max_chunk_bytes_compressed` (524 288) is
  unchanged — the override only applies to this command's LogWriter
  via `set_max_chunk_bytes(...)` and does not leak into any other
  command's run.

## Assertions
- `assert_envelope_terminal(envelope, "completed")`.
- `summary["lines_emitted"] == 500`.
- `len(manifest["chunks"]) >= 2`.
- All chunk files exist (each fetch returns content).
- `assert_pr_merged(pr)`.

## Forensic artifacts
- Issue `N`, one terminal comment, log artifacts including ≥2 chunk
  files. One merged PR.
