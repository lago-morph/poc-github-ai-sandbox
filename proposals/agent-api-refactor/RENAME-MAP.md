# Rename map

Concrete rename plan, file-by-file. References are anchored to current
HEAD (`5e9dcfc`). Line numbers are advisory; if drift, find the symbol.

## skills/batch-job/submit.py

| Was | Now |
|---|---|
| `submit(client: GitHubClient, *, issue_number: int, ...)` | `submit(backend: TaskBackend, *, task_id: TaskHandle, ...)` |
| `client.get_issue(issue_number)` (in `preflight`) | `backend.read_task(task_id)` |
| Manual `agent-meta` parse via `parse_agent_meta(issue.get("body"))` | Removed: `Task` already carries the parsed fields |
| `client.add_comment(issue_number, body)` returning `{"id": ...}` | `backend.submit_job(task_id=..., command=..., args=..., branch=..., commit_sha=..., subagent_id=...)` returning `Job` |
| Returns: comment dict | Returns: `Job` |
| Envelope JSON construction in `submit()` | Removed: the driver builds whatever envelope the platform needs |

The `preflight()` helper becomes a small private function in
`submit.py` that operates on a `Task` object (from `backend.read_task`),
not on a raw issue dict. It checks: `agent-task` equivalent (the driver
exposes whether the task is recognised), `agent_id` match, presence of
a brief.

## skills/batch-job/poll.py

| Was | Now |
|---|---|
| `poll(client: GitHubClient, *, comment_id: int, command: str, ...)` | `poll(backend: TaskBackend, *, job_id: JobHandle, command: str, ...)` |
| `client.get_comment(comment_id)` + JSON parse of body | `backend.read_job(job_id)` returning `Job` |
| `is_terminal_run_status(envelope.get("run_status"))` | `job.status in {"completed", "errored", "parse_error"}` |
| `client.get_file_contents(summary_path, logs_branch)` | `backend.read_summary_blob(job)` |
| `client.update_comment(comment_id, json.dumps(envelope, indent=2))` | `backend.ack_job(job_id)` |
| `_open_runner_failure_issue(...)` | Removed from poll: stays in driver. Skill raises `PollTimeout` with a `failure_record_id` (opaque string) when the driver chooses to record one |
| `RuntimeError` on JSON-decode of comment body | Removed: `read_job` always returns a parseable `Job` (driver handles parse_error states) |

`PollTimeout` keeps its current shape; only the skill no longer creates
side effects when raising it (the driver records the failure record if
it wishes).

## skills/task-dag/claim.py

| Was | Now |
|---|---|
| `claim(client, *, agent_id, candidate_issues, config, ...)` | `claim_task(backend, *, agent_id=None)` |
| `select_candidate(issues, ...)` operating on issue dicts | Internal: operates on `Task` objects from `backend.find_claimable_tasks()` |
| `_is_stale(meta, stale_seconds)` | Internal: operates on `Task.updated_ts` |
| `client.update_issue(number, body=new_body)` for claim | `backend.write_task_fields(task_id, agent_id=..., session_id=..., status="working")` (driver writes agent-meta) |
| Re-read body, parse meta, compare | Re-read `Task` and compare `agent_id` |
| `heartbeat(client, *, issue_number, agent_id)` | `heartbeat(backend, *, task_id, agent_id)` |
| `abandon(client, issue_number, reason)` | `abandon(backend, task_id, reason)` |

`candidate_issues` parameter is REMOVED. The skill always asks the
backend; if the in-memory test wants to constrain candidates, do it on
the driver side.

## skills/task-dag/plan.py

| Was | Now |
|---|---|
| `plan(client, issue_number=...)` reading `instructions_inline` / `instructions_path` from issue body | `plan(backend, task_id=...)` calling `backend.read_brief(task)` |

Returns the same `{brief, source, ...}` shape but with `source` set to
a driver-supplied tag (e.g. `"task-field"`, `"repo-file"`, `"confluence-page"`).

## skills/task-dag/merge.py

Almost unchanged in shape; the operations on branches map 1:1 to the
neutral file/branch primitives.

| Was | Now |
|---|---|
| `merge_subagent_branches(client, *, feature_branch, subagent_branches)` | `merge_subagent_branches(backend, *, feature_branch, subagent_branches)` |
| Branch ops on `client.get_branch_head_sha`, `client.commit_files`, `client.delete_branch` | `backend.get_branch_head`, `backend.commit_file` (loop), `backend.delete_branch` |

If the existing `commit_files` call commits multiple files atomically,
add `commit_files` (plural) to the Protocol — call it out in the PR
description as a Protocol addition.

## skills/task-dag/schedule_successors.py

| Was | Now |
|---|---|
| `schedule_successors(client, successors, base_branch)` creating issues with `agent-meta` blocks | `backend.create_task(...)` for each successor; `depends_on` carried as opaque IDs |

## skills/*/common.py

Both files currently re-export from `.agent/scripts/common.py`. Replace
with:

- `skills/backend.py` — the new neutral types and Protocol.
- `skills/drivers/github.py` — the `GithubDriver`.
- The existing `skills/*/common.py` files re-export `Task`, `Job`,
  `JobResult`, `TaskBackend`, `GithubDriver`, `iso_now`, `new_uuid`,
  `validate`, `load_config`, `load_schema` for skill scripts.

The agent-meta helpers (`parse_agent_meta`, `render_agent_meta`,
`b64_encode`, `b64_decode`, `is_terminal_run_status`,
`has_protocol_markers`) move into `skills/drivers/github.py` as private
helpers — they are implementation details of the GitHub driver, not
neutral primitives. `.agent/scripts/common.py` keeps its copy for the
workflow scripts; we duplicate rather than share to keep the agent-side
free of any dependency on `.agent/scripts/`.

## SKILL.md updates

### skills/batch-job/SKILL.md

Replace the "Inputs" section with neutral names:

```
- task_id (str)
- command (str, must be in the configured commands)
- args (object, validated against the per-command schema)
- branch (str)
- commit_sha (str)
- subagent_id (str)
```

Replace the "Procedure" step 1 — drop "Pre-flight: assert locked == true,
agent-task label present, issue body parses as agent-meta." with:
"Pre-flight: backend confirms the task is recognised and the caller's
`agent_id` matches the task owner."

Replace the "Outputs" Python dict — drop `envelope`, replace with:

```python
JobResult(
    job=Job(...),       # neutral Job dataclass
    summary=...,        # the inline summary
    summary_blob=...,   # the parsed large summary, if available
)
```

Drop the "Inside an Actions runner" invocation note — it's
GitHub-specific and lives in the driver docs now.

### skills/task-dag/SKILL.md

Replace `agent-task` references with "claimable task" and remove the
note about the CAS-by-re-read handshake being driven from `claim.py`
(it's still true mechanically but the agent doesn't need to know).

Replace input/output bullets to use neutral types.

## Tests

Tests under `tests/unit/` and `tests/e2e/` that exercise the skills:

- Where they construct `InMemoryGitHubClient` and pass it into a skill,
  wrap it in `GithubDriver(client)` first.
- Where they assert on GitHub-shaped output (e.g. `comment["body"]`
  envelope JSON), keep that assertion but move it into a test of
  `GithubDriver` directly. The skill-level tests should assert on
  neutral dataclass fields.

Add at least these new tests:

- `tests/unit/test_github_driver.py`: round-trip Task/Job through
  `GithubDriver` over `InMemoryGitHubClient`. Verify the agent-meta
  block is correctly maintained in the underlying issue body and the
  envelope is correctly constructed in the underlying comment.
- `tests/unit/test_skill_neutrality.py`: import the skills, grep
  symbols for forbidden words (`issue`, `comment`, `envelope`,
  `agent-meta`, `_agent_runs`, `lock`, `agent-task`). Fail if any
  appear in the public symbols of `skills.batch_job` or
  `skills.task_dag`. (You may need a small Python introspection
  helper.)
