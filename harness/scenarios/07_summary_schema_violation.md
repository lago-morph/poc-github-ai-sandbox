# Scenario 07 — summary_schema_violation

## Objective
Exercise the handler's defense-in-depth summary validation: the
`bad-summary` test command's handler returns `{}` but the schema
requires `required_field`. Handler must rewrite the comment with
`run_status="error"` and `error_kind="summary_schema_violation"`.

## Prereqs
- `.agent/config.json` lists `"bad-summary"` in `commands` (added by
  this branch).
- `.agent/commands/bad_summary.py` and
  `.agent/schemas/commands/bad-summary.schema.json` exist.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(7, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) issue (`harness-scenario-07`), claim meta.

## Agent steps
1. Build envelope::

       python -m agent_lib make-request '{}' \
         --command bad-summary \
         --branch <feature> --sha <feature_head> \
         --subagent-id alpha

2. Post envelope as comment.
3. Poll until terminal.
4. `abandon-meta` after observing terminal error.

## Workflow expectations
- Handler dispatches `bad-summary`, captures the empty summary,
  validates against `summary_completed` (missing `required_field`),
  flips `run_status` to `error` with
  `error_kind="summary_schema_violation"`, replaces summary with
  `{error_kind, error_detail}`, and continues writing logs.

## Assertions
- `assert_envelope_terminal(envelope, "error",
  expected_error_kind="summary_schema_violation")`.
- `summary["error_kind"] == "summary_schema_violation"`.
- `error_detail` is non-empty and mentions `required_field`.
- `assert_meta_status(final_body, "abandoned")`.
- `runs/N/C/manifest.json` and `summary.json` still exist (logs are
  written even on schema-violation path).

## Forensic artifacts
- Issue `N` (abandoned), one terminal-error comment, log artifacts.
