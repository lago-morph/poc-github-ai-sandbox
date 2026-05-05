# Scenario 03 — malformed JSON envelope yields parse_error

## Objective
Verify that when the agent posts a comment whose body has the
`protocol_version` and `kind` markers but is otherwise schema-invalid
(e.g. wrong type for `commit_sha`, missing `subagent_id`), the
workflow handler rewrites the comment with a terminal `parse_error`
envelope carrying `error_kind="schema_validation_failed"`.

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(3, run_id)`.
2. Create `feature` from `main`. Capture HEAD sha.

## Agent steps
1. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) parent issue (label `harness-scenario-03`).
2. Claim meta and update issue body.
3. Construct an INTENTIONALLY MALFORMED envelope JSON, e.g.::

       {
         "protocol_version": 1,
         "kind": "batch-job-request",
         "command": "echo",
         "args": {"message": "hi"},
         "branch": "<feature>",
         "commit_sha": "not-a-sha",
         "subagent_id": ""
       }

   Note: this MUST NOT go through `python -m agent_lib make-request`
   (which would reject it). Build it manually in the agent's tool
   stream.
4. Post as a comment via `mcp__github__add_issue_comment`. Capture
   comment id `C`.
5. Poll `mcp__github__issue_read` (action `get_comment`) until
   `run_status == "parse_error"` (use `parse-comment`).
6. `abandon-meta` with `--reason "scenario_03_done"`; update issue.

## Workflow expectations
- `_write_parse_error` path in handler runs.
- Comment is rewritten with:
  - `run_status: "parse_error"`
  - `error_kind: "schema_validation_failed"`
  - `original_body_b64` containing the original posted body.

## Assertions
- `assert_envelope_terminal(envelope, "parse_error",
  expected_error_kind="schema_validation_failed")`.
- `original_body_b64` is non-empty.
- `assert_meta_status(final_body, "abandoned")`.

## Forensic artifacts
- Issue `N` (abandoned), one parse_error comment. No PR. No
  `summary.json` written for this comment (parse_error path skips
  artifact uploads).
