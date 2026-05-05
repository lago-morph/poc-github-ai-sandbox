# batch-job

Submit a single batch job from an active issue and consume the result.

## Inputs

- `issue_number` (int)
- `command` (string, must be in `.agent/config.json :: commands`)
- `args` (object, validated against the per-command schema)
- `branch` (string)
- `commit_sha` (string)
- `subagent_id` (string)

## Procedure

1. Pre-flight: assert `locked == true`, `agent-task` label present,
   issue body parses as `agent-meta`. Caller's `agent_id` matches.
2. `submit.submit(...)` posts a `batch-job-request` envelope as a
   comment.
3. `poll.poll(...)` loops until `run_status` is terminal
   (`completed` / `error` / `parse_error`), respecting
   `runner_pickup_timeout_seconds` and `running_timeout_seconds` from
   `.agent/config.json`. Pass an optional `heartbeat` callable to be
   invoked once per poll iteration (after the comment is read) so the
   caller can refresh `status_ts` on the parent issue while waiting —
   per SPEC §9.4 step 3.
4. The summary is validated against the per-command summary schema.
5. The skill writes `agent_ack: finished` into the comment.

## Invocation modes

- **Programmatic / tests.** Call `submit(client=..., ...)` and
  `poll(client=..., comment_id=..., command=...)` directly with any
  `GitHubClient` (the in-memory client works end-to-end).
- **Inside an Actions runner.** Wire a REST-backed `GitHubClient`
  (not implemented in the POC) and reuse the same calls.

## Outputs

`poll(...)` returns:

```python
{
  "envelope": <full JSON envelope, terminal>,
  "summary": <inline summary>,
  "summary_json": <contents of summary.json on _agent_runs, or None>,
}
```
