# Scenario 05 — unsupported protocol_version

## Objective
Verify the handler rejects an envelope with `protocol_version != 1`
with a terminal `parse_error` and
`error_kind="unsupported_version"`.

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(5, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + lock + label issue (`harness-scenario-05`); claim meta.

## Agent steps
1. Build envelope manually (do NOT use `make-request`)::

       {
         "protocol_version": 2,
         "kind": "batch-job-request",
         "command": "echo",
         "args": {"message": "hi"},
         "branch": "<feature>",
         "commit_sha": "<feature_head>",
         "subagent_id": "alpha",
         "submitted_at": "<iso_now>",
         "run_status": null,
         "agent_ack": null
       }

2. Post via `mcp__github__add_issue_comment`.
3. Poll until `run_status == "parse_error"`.
4. `abandon-meta`.

## Workflow expectations
- Handler's pre-schema branch (`if parsed.get("protocol_version") !=
  1`) emits `_write_parse_error` with `error_kind ==
  "unsupported_version"` and `error_detail` mentioning the offending
  version.

## Assertions
- `assert_envelope_terminal(envelope, "parse_error",
  expected_error_kind="unsupported_version")`.
- `original_body_b64` is non-empty.
- `assert_meta_status(final_body, "abandoned")`.

## Forensic artifacts
- Issue `N` (abandoned), one parse_error comment. No PR.
