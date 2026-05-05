# Scenario 04 — branch_sha_mismatch

## Objective
Verify the workflow rejects a request whose `commit_sha` does not
match the live HEAD of `branch`, with a terminal `error` envelope
carrying `error_kind="branch_sha_mismatch"`.

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(4, run_id)`.
2. Create `feature` from `main`. Record initial HEAD `sha0`.
3. Commit a file (`note.txt`) on `feature` via
   `mcp__github__create_or_update_file`. Record new HEAD `sha1`.
4. Create + lock + label issue (`harness-scenario-04`); claim meta.

## Agent steps
1. Build request envelope with `--branch <feature> --sha <sha0>`
   (the OLD sha — deliberately stale). Use `--no-validate` is NOT
   appropriate here since the envelope itself is structurally valid;
   `make-request` accepts any 40-hex string.
2. Post envelope as a comment.
3. Poll for terminal status.
4. `abandon-meta` after observing the terminal error.

## Workflow expectations
- Handler computes `head_sha != commit_sha` and emits a terminal
  `error` envelope with `error_kind="branch_sha_mismatch"` and
  `error_detail` mentioning both shas.

## Assertions
- `assert_envelope_terminal(envelope, "error",
  expected_error_kind="branch_sha_mismatch")`.
- `error_detail` contains the substring `HEAD=`.
- `summary` is `{"error_kind": "branch_sha_mismatch", "error_detail":
  ...}`.
- `assert_meta_status(final_body, "abandoned")`.

## Forensic artifacts
- Issue `N` (abandoned), one terminal-error comment. No PR.
