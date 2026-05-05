# Harness runs

Each row records one scenario invocation. The dispatcher appends a
row when a subagent finishes (success, failure, or abandoned).

| Scenario | Run ID | Issue # | Feature branch | PRs | Result | Started | Finished | Notes |
|----------|--------|---------|----------------|-----|--------|---------|----------|-------|
| 01 | 7e991050 | 18 | agent/harness-01-7e991050 | #19 | completed end-to-end | 2026-05-05T14:54Z | 2026-05-05T14:58Z | first live success after 6 bug fixes |
| 03 | d1581ee9 | 21 | agent/harness-03-d1581ee9 | none | parse_error (schema_validation_failed) | 2026-05-05T15:03Z | 2026-05-05T15:06Z | first comment was wrapped in ```json fence and ignored (no_protocol_markers); reposted bare JSON, comment 4380540184 received terminal envelope (workflow_run_id=25384548379). Issue marked abandoned (open). |
| 04 | 52ed0261 | 22 | agent/harness-04-52ed0261 | none | error (branch_sha_mismatch) | 2026-05-05T15:08Z | 2026-05-05T15:09Z | comment 4380557819 terminal envelope (workflow_run_id=25384675159); 40-zeros SHA detected vs HEAD=5e9dcfc. Issue marked abandoned (open). |
| 05 | b12c13fa | 23 | agent/harness-05-b12c13fa | none | parse_error (unsupported_version) | 2026-05-05T15:10Z | 2026-05-05T15:11Z | comment 4380574909 terminal envelope (workflow_run_id=25384797532); protocol_version=2 rejected before schema validation. Issue marked abandoned (open). |
