# Specification: GitHub-Native Agent Job & Task Protocol

Status: Draft v1
Audience: Implementers of agent skills and repository workflow operators

## 0. Goals and non-goals

### Goals

- Provide AI agents with a portable, restart-safe interface for running batch jobs in GitHub Actions, using only a GitHub MCP server as transport (no direct GitHub REST/GraphQL API access required from the agent).
- Provide a higher-level scheduler that uses issue dependencies to express a task DAG.
- Operate safely on a public repository, with access control rooted in `lock`.
- Produce a complete audit trail: every job's exact code SHA, full structured log, typed summary, and agent acknowledgement is durable on GitHub.
- Offer a human-facing dashboard view of agent activity (Projects v2) with no agent-side burden.
- Be agent-harness-agnostic. Skills are written so that any agent CLI capable of invoking shell commands and using a GitHub MCP server can drive them.

### Non-goals (v1)

- Hiding GitHub primitives behind a wrapper MCP server. Skills include scripts (Python or Bash) that the agent invokes for high-level operations; for everything else, the agent uses GitHub MCP tools directly.
- Cross-repository coordination. Single-repository in v1.
- Private-repo Actions-minute optimisation.
- Replacing CI for human-driven PRs. This protocol is an agent-facing layer that rides alongside whatever human CI exists.
- A `cancel-job` primitive. Out of v1 scope.

## 1. Glossary

- **Primary agent.** The agent that owns an issue end-to-end. Exactly one per issue at a time.
- **Subagent.** A child agent dispatched by the primary to do work on a single dedicated branch. Multiple subagents may run in parallel under one primary.
- **Issue.** A task node. Carries metadata, status, and instructions in the body.
- **Comment.** A batch-job record. The body is a JSON envelope; status fields evolve through the run.
- **Feature branch.** The branch created from `base_branch` at issue creation. Becomes the PR head.
- **Subagent branch.** A branch off the feature branch; one per subagent. All commits a subagent makes go here. Primary merges these into the feature branch before opening the PR.
- **Run.** One execution of `batch-job-handler` triggered by the creation of one comment.
- **Envelope.** The JSON document occupying a comment body.
- **Command.** A named, schema-typed operation the workflow knows how to execute (e.g. `run-tests`, `deploy-staging`).

## 2. Repository layout

On the **default branch** (no agent edits these during normal operation):

```
.github/workflows/
  lock-and-sweep.yml         # on: issues.opened
  batch-job-handler.yml      # on: issue_comment.created
  close-on-merge.yml         # on: pull_request.closed (merged)
.agent/
  config.json                # central tunables and timeouts
  schemas/
    issue-body.schema.json
    comment-envelope.schema.json
    log-manifest.schema.json
    commands/
      <command-name>.schema.json    # one per registered command
  scripts/
    handler.py
    lock_and_sweep.py
    close_on_merge.py
    common.py
  commands/
    <command-name>.py          # one handler module per command
skills/
  batch-job/
    SKILL.md
    submit.py
    poll.py
    common.py
  task-dag/
    SKILL.md
    claim.py
    plan.py
    merge.py
    schedule_successors.py
    common.py
prompts/
  <issue-number>.md            # optional long-form instructions
README.md
SPEC.md
```

On the **`_agent_runs` orphan branch** (no shared history with code):

```
runs/<issue-number>/<comment-id>/
  manifest.json
  log-0001.jsonl.gz
  log-0002.jsonl.gz
  ...
  summary.json
```

**Intent.** Logs live on a dedicated orphan branch so log writes never conflict with code commits and never pollute feature-branch history. Per-(issue, comment) paths mean no semantic conflicts between concurrent runs; only push-time non-fast-forward conditions occur, which a retry loop handles. Agents fetch logs via `get_file_contents` against `_agent_runs`.

## 3. Identities and access control

- A single GitHub bot account (the agent identity) owns all agent-side writes. The login is recorded in `.agent/config.json` as `agent_login`.
- All structured agent issues carry the label `agent-task`. The lock-and-sweep workflow applies this label.
- Agents only act on comments where `author == agent_login` AND the body parses as a valid envelope. Foreign comments are inert.
- Workflow defense-in-depth: `batch-job-handler.yml` no-ops unless the issue carries `agent-task` and `comment.user.login == agent_login`.
- After the issue's PR is merged, `close-on-merge` locks the issue as a tamper-prevention seal on the audit record.

**Intent.** Public repositories accept arbitrary issues and comments from anonymous users. The label + author filter is individually weak but jointly sufficient to make the protocol safe by default: the label distinguishes agent issues from human bug reports, and the author check blocks any injection by a non-bot identity. Foreign comments do not trigger the handler's `if:` clause, so they are inert.

**Real-world correction (discovered during live POC runs).** The original draft locked agent issues at creation. In practice, GitHub refuses comments from `GITHUB_TOKEN` on locked issues — including the workflow's own terminal envelope writes. The handler is therefore unable to produce its required output if the issue is locked during processing. The corrected design: apply the `agent-task` label at creation (so the workflow's label check is satisfied) and **lock the issue only at close** (post-merge), turning the lock into an audit-tamper-prevention seal rather than an injection guard. The injection-guard role is filled by the workflow's author + label `if:` filter, which makes foreign comments inert without needing the lock.

## 4. State machines

### 4.1 Issue

States in body field `status`:

| status | meaning | who writes |
|---|---|---|
| `null` | Unclaimed scheduled work. Any qualifying agent may claim. | Issue creator (agent or human) |
| `working` | A primary owns this and is active. | Primary; updated on every poll cycle. |
| `abandoned` | Primary gave up or was displaced. Comments may be inconsistent. | Primary, or successor on takeover. |
| `finished` | All comments terminal AND PR exists. Issue is closed. | Primary at end of work. |

#### Transitions

- `null → working` on claim. Claimer writes its `agent_id` and a fresh `status_ts`. Verifies 5 seconds later that its `agent_id` is still in the body; if not, it lost the race and abandons quietly.
- `working → working` on every primary poll cycle (heartbeat updates `status_ts`).
- `working (stale) → working (new agent)`: a different agent reads `status_ts` older than `issue.stale_seconds` (default 7200), takes over with the same handshake as `null → working`. The displaced agent, if still alive, will discover on its next heartbeat that its `agent_id` is gone and must self-abandon.
- `working → abandoned` if the primary gives up, or if a successor declines to continue (e.g. discovers a failed required dependency).
- `working → finished` only when:
  - every comment has `run_status` ∈ {`completed`, `error`, `parse_error`} AND `agent_ack == finished`, AND
  - the PR for this issue exists.

Primary writes `finished`, posts a final comment summarising the work, then closes the issue.

#### Lock state (orthogonal to `status`)

The GitHub-level `locked` flag is **not** part of the issue `status` machine, but it has a single, well-defined transition:

| event | locked? |
|---|---|
| Issue opened by `agent_login` | `false` (lock-and-sweep applies the `agent-task` label only) |
| Issue body or comments mutated during the working lifecycle | `false` (the batch-job-handler must remain able to write terminal envelopes; `GITHUB_TOKEN` cannot comment on locked issues) |
| PR merged → close-on-merge fires | `true` (set immediately after the issue is closed; acts as a tamper-prevention seal on the audit record) |

Once an issue is closed and locked, no further protocol writes are expected. The lock is preserved to make the comment thread an immutable audit log.

**Intent.** The `null` state lets external schedulers (a human, another agent, or a teardown step at end of a previous issue) queue work without requiring a live agent. The takeover handshake is loose CAS-by-re-read; it is sufficient because spurious takeovers are rare and self-correcting. Deferring the lock to close-time avoids a hard contradiction with the workflow's own writes (see §3 "Real-world correction").

### 4.2 Comment

Two independent fields.

`run_status` (workflow-owned):

| value | meaning |
|---|---|
| `null` | Workflow has not started (or never fired). |
| `running` | Workflow has claimed this comment. |
| `completed` | Job finished cleanly. Terminal. |
| `error` | Job ran but exited non-zero. Terminal. |
| `parse_error` | Envelope was malformed. Terminal. |

`agent_ack` (agent-owned):

| value | meaning |
|---|---|
| `null` | Agent has not consumed result yet. |
| `finished` | Agent has read summary and integrated outcome. |

The workflow only writes the comment while `run_status` is non-terminal. The agent only writes after `run_status` is terminal. There is therefore no concurrent-writer window.

**Intent.** Splitting the fields preserves the workflow's verdict (`completed` vs `error`) after the agent acks, and lets restart logic distinguish "completed but unread" from "in flight" without ambiguity.

## 5. Schemas

### 5.1 Issue body

The body is human-readable Markdown with one fenced JSON block tagged `agent-meta`. The block is the source of truth for protocol state; surrounding prose is for humans only.

````markdown
<short human-readable description, optional>

```agent-meta
{
  "protocol_version": 1,
  "agent_id": null,
  "session_id": null,
  "status": null,
  "status_ts": null,
  "feature_branch": "agent/42-add-rate-limit",
  "base_branch": "main",
  "parent_issue": null,
  "depends_on_prs": [],
  "instructions_path": null,
  "instructions_inline": "Add rate limiting to the public API.",
  "created_at": "2026-05-05T12:00:00Z"
}
```
````

Field notes:

- `agent_id`: stable identifier of the owning primary, distinct from `agent_login`. Multiple agent processes may share `agent_login` (a bot account) but have distinct `agent_id` values. UUID recommended.
- `session_id`: identifier of the current claim session. New on each `null → working` or stale takeover.
- `feature_branch`: pattern is configurable in `.agent/config.json`. Default `agent/<issue>-<slug>`.
- `instructions_path`: when non-null, the canonical instructions live at this path on `base_branch`. Used when instructions exceed the practical body size or contain rich content.
- `instructions_inline`: short brief, must be small. Either `instructions_path` or `instructions_inline` is required.
- `depends_on_prs`: list of PR numbers (in this repo) that must be `merged` before any work proceeds.

JSON schema: `.agent/schemas/issue-body.schema.json`.

**Intent.** Markdown wrapping keeps the issue legible to humans on the GitHub UI; the fenced block is unambiguous to parse. Splitting `agent_login` (account) from `agent_id` (process/session) supports multiple agent instances behind one bot account.

### 5.2 Comment envelope

The comment body is a JSON object with no surrounding prose. Two distinct shapes — request (agent-written) and post-run (workflow-written) — are merged in place over the lifecycle.

#### 5.2.1 Request (written by agent at create time)

```json
{
  "protocol_version": 1,
  "kind": "batch-job-request",
  "command": "run-tests",
  "args": { "suite": "e2e", "shard": 11 },
  "branch": "agent/42-add-rate-limit/sub-alpha",
  "commit_sha": "abc123def456...",
  "subagent_id": "alpha",
  "submitted_at": "2026-05-05T12:01:00Z",
  "run_status": null,
  "agent_ack": null
}
```

#### 5.2.2 Post-run (workflow has edited)

```json
{
  "protocol_version": 1,
  "kind": "batch-job-request",
  "command": "run-tests",
  "args": { "suite": "e2e", "shard": 11 },
  "branch": "agent/42-add-rate-limit/sub-alpha",
  "commit_sha": "abc123def456...",
  "subagent_id": "alpha",
  "submitted_at": "2026-05-05T12:01:00Z",

  "run_status": "completed",
  "run_started_at": "2026-05-05T12:01:14Z",
  "run_finished_at": "2026-05-05T12:04:32Z",
  "workflow_run_id": 9876543210,
  "checked_out_sha": "abc123def456...",
  "summary": { "passed": 42, "failed": 0, "skipped": 1, "duration_seconds": 198 },
  "log_manifest_branch": "_agent_runs",
  "log_manifest_path": "runs/42/<comment-id>/manifest.json",

  "agent_ack": null
}
```

After the agent reads the summary:

```json
{ "...": "...", "agent_ack": "finished", "agent_acked_at": "2026-05-05T12:05:01Z" }
```

#### 5.2.3 Branch + SHA semantics

- The workflow checks out `branch` and verifies that `git rev-parse HEAD == commit_sha`.
- If `branch` does not exist, or `HEAD != commit_sha`, the workflow writes terminal `run_status: error` with `error_kind: "branch_sha_mismatch"` and details in the summary. The agent must not retry without correcting one or the other.
- Branch is the natural human reference; SHA is the integrity check. Both are required. They guard against both branch deletion and concurrent commits sneaking in between submission and dispatch.

#### 5.2.4 Parse errors

If the comment body contains a parseable JSON object with `protocol_version` and `kind` markers but fails schema validation, the workflow REPLACES the body with:

```json
{
  "protocol_version": 1,
  "kind": "batch-job-request",
  "run_status": "parse_error",
  "error_kind": "schema_validation_failed",
  "error_detail": "args.shard: expected integer, got string",
  "original_body_b64": "<base64 of original body>",
  "run_started_at": "2026-05-05T12:01:14Z",
  "run_finished_at": "2026-05-05T12:01:15Z",
  "workflow_run_id": 9876543210,
  "agent_ack": null
}
```

If the comment body has neither `protocol_version` nor `kind` markers (e.g. a stray human comment that slipped past filters), the workflow ignores it silently — that is not a protocol comment.

**Real-world note:** Some MCP servers (notably Claude Code's GitHub MCP) automatically append a trailer line like `\n---\n_Generated by ..._` to every comment they post. The handler tolerates this by parsing the longest JSON-object prefix at the start of the body. The spec's "no surrounding prose" requirement is upheld by the agent (don't intentionally add prose) but the handler is robust to MCP-injected trailers.

JSON schema: `.agent/schemas/comment-envelope.schema.json`.

**Intent.** Editing the comment in place rather than posting a new one keeps the 1-comment-per-job invariant. Preserving the original body under `original_body_b64` lets the agent (or a human) recover the original input verbatim. Distinguishing "no envelope at all" from "malformed envelope" prevents the protocol from polluting issues with parse_error records for non-protocol comments.

### 5.3 Per-command schemas

Each registered command has a JSON Schema document at `.agent/schemas/commands/<command>.schema.json` defining:

- `args` schema: validated against the request envelope's `args` field.
- `summary` schema: the workflow MUST produce a `summary` field conforming to this when `run_status == completed`. (For `error` and `parse_error`, the summary may be a smaller error-shaped object; this is also defined in the command schema.)

Example `.agent/schemas/commands/run-tests.schema.json` (sketch):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "run-tests",
  "type": "object",
  "properties": {
    "args": {
      "type": "object",
      "required": ["suite"],
      "properties": {
        "suite": { "enum": ["unit", "integration", "e2e"] },
        "shard": { "type": "integer", "minimum": 0 },
        "filter": { "type": "string" }
      },
      "additionalProperties": false
    },
    "summary_completed": {
      "type": "object",
      "required": ["passed", "failed", "skipped", "duration_seconds"],
      "properties": {
        "passed": { "type": "integer", "minimum": 0 },
        "failed": { "type": "integer", "minimum": 0 },
        "skipped": { "type": "integer", "minimum": 0 },
        "duration_seconds": { "type": "number" },
        "failed_tests": {
          "type": "array",
          "items": { "type": "object",
            "properties": { "name": {"type": "string"}, "message": {"type": "string"} } }
        }
      }
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      }
    }
  },
  "required": ["args", "summary_completed", "summary_error"]
}
```

The workflow validates `args` against the schema before running, and validates the produced `summary` against the appropriate `summary_*` schema before writing the terminal envelope. Validation failure on output is itself a workflow bug and is reported as `run_status: error` with `error_kind: "summary_schema_violation"`.

**Intent.** Per-command schemas give the agent a strong contract for both inputs and outputs, decoupling it from command implementation details. Adding a new command means adding a schema and a handler module — agents that don't know the command are unaffected.

### 5.4 Log manifest and chunks

`runs/<issue>/<comment>/manifest.json`:

```json
{
  "protocol_version": 1,
  "schema": {
    "chunk_format": "jsonl-gz",
    "fields": {
      "ts":     { "type": "string", "description": "ISO 8601" },
      "stream": { "enum": ["stdout", "stderr", "meta"] },
      "phase":  { "enum": ["setup", "exec", "teardown"] },
      "data":   { "type": ["string", "object"] }
    }
  },
  "command": "run-tests",
  "args": { "suite": "e2e", "shard": 11 },
  "checked_out_sha": "abc123def456...",
  "started_at": "2026-05-05T12:01:14Z",
  "finished_at": "2026-05-05T12:04:32Z",
  "exit_code": 0,
  "chunks": [
    { "path": "log-0001.jsonl.gz", "bytes": 491200, "lines": 8421 },
    { "path": "log-0002.jsonl.gz", "bytes": 412044, "lines": 7099 }
  ]
}
```

Each chunk is JSON Lines (one record per line), gzipped. Cap chunks at `logs.max_chunk_bytes_compressed` (default 524288 bytes ≈ 512 KB) so each file is fetchable through `get_file_contents`. Within a chunk, records may be heterogeneous (per the schema); jq users can filter by `phase` or `stream`.

`summary.json` is written alongside as the agent's first read; it contains the same `summary` field the workflow writes into the comment envelope, plus optionally additional structured detail too large for the comment body (e.g. all 200 failing test names).

JSON schema: `.agent/schemas/log-manifest.schema.json`.

**Intent.** Embedding the schema in each manifest means consumers (human or agent) don't need to look up external docs to interpret the log. Different commands may emit different record shapes; the manifest documents the run's own structure.

### 5.5 Central config (`.agent/config.json`)

```json
{
  "protocol_version": 1,
  "agent_login": "my-bot",
  "labels": {
    "agent_task": "agent-task",
    "runner_failure": "runner-failure"
  },
  "issue": {
    "stale_seconds": 7200,
    "heartbeat_min_interval_seconds": 60
  },
  "comment": {
    "runner_pickup_timeout_seconds": 300,
    "running_timeout_seconds": 3600,
    "poll_initial_seconds": 30,
    "poll_backoff": [
      { "after_seconds": 300, "interval_seconds": 60 },
      { "after_seconds": 600, "interval_seconds": 120 }
    ],
    "poll_total_timeout_seconds": 3600
  },
  "logs": {
    "branch": "_agent_runs",
    "max_chunk_bytes_compressed": 524288
  },
  "branches": {
    "feature_pattern": "agent/<issue>-<slug>",
    "subagent_pattern": "<feature_branch>/sub-<subagent_id>"
  },
  "commands": ["run-tests", "build", "deploy-staging"]
}
```

Both workflows and skills load this file. It is the single source of truth for tunables and the registry of accepted commands.

## 6. Branching model

- **Feature branch** `agent/<issue>/<slug>` is created from `base_branch` at issue creation. PR target is `base_branch`; PR head is the feature branch.
- **Subagent branch** `agent/<issue>/<slug>/sub-<subagent_id>` is created from the current tip of the feature branch when the primary dispatches a subagent. All of that subagent's commits land here.
- A subagent may submit multiple batch jobs against its branch, with new commits between them. Each comment pins to `branch + commit_sha`; commits made *after* `agent_ack` belong to subsequent comments by the same subagent.
- The primary, before opening the PR, merges all subagent branches into the feature branch in an order it chooses. Merge conflicts are the primary's responsibility.
- Subagent branches are deleted after the PR is opened.

**Intent.** Branches are the human-readable mechanism for "what work happened where"; SHAs are the verification mechanism. Per-subagent branches make parallel subagents non-conflicting at the git layer. Per-subagent (rather than per-comment) granularity lets a subagent's iteration commits between jobs naturally chain on the same branch.

## 7. Workflows

### 7.1 `lock-and-sweep.yml`

Triggered on `issues.opened`. Runs against the default branch's workflow file with `GITHUB_TOKEN`.

```yaml
name: lock-and-sweep
on:
  issues:
    types: [opened]
permissions:
  issues: write
  contents: read
concurrency:
  group: lock-${{ github.event.issue.number }}
  cancel-in-progress: false
jobs:
  lock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r .agent/scripts/requirements.txt
      - run: python .agent/scripts/lock_and_sweep.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
```

Script behaviour:
1. Fetch the issue. Parse `agent-meta` from the body.
2. If body lacks `agent-meta` or the issue creator is not `agent_login`, no-op (this is a human or non-protocol issue).
3. Apply `agent-task` label.
4. List existing comments (sweeping any that snuck in before the label was applied). Delete comments not authored by `agent_login`. Comments authored by `agent_login` are unexpected at this stage but left alone (an agent sending a job before label-apply is a protocol bug, not an attack).

> **Note on locking.** Earlier drafts of this spec had `lock-and-sweep` lock the issue at this point. We removed that step: locking the issue blocks the batch-job-handler from writing its terminal envelope back (GitHub refuses comments from `GITHUB_TOKEN` on locked issues). The lock is now applied by `close-on-merge.yml` once the PR is merged. See §3 "Real-world correction".

**Intent.** Pre-label comment deletion is the workflow's responsibility because the MCP transport may not expose comment deletion. The workflow uses REST inside the runner — the no-API constraint applies to agents, not workflows.

### 7.2 `batch-job-handler.yml`

Triggered on `issue_comment.created`. Runs against the default branch's workflow file.

```yaml
name: batch-job-handler
on:
  issue_comment:
    types: [created]
permissions:
  contents: write
  issues: write
concurrency:
  group: comment-${{ github.event.comment.id }}
  cancel-in-progress: false
jobs:
  handle:
    if: |
      contains(github.event.issue.labels.*.name, 'agent-task') &&
      github.event.comment.user.login == vars.AGENT_LOGIN
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r .agent/scripts/requirements.txt
      - run: python .agent/scripts/handler.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          COMMENT_ID: ${{ github.event.comment.id }}
```

`handler.py` flow:
1. Fetch the comment. Parse the envelope.
   - Unparseable / no markers → exit silently (not a protocol comment).
   - Parseable but invalid against schema → write `parse_error` envelope and exit.
2. Idempotency check: if `run_status` is already terminal, exit (webhook redelivery).
3. Validate `branch` exists and `git rev-parse HEAD == commit_sha`. On mismatch, write terminal `error` with `error_kind: "branch_sha_mismatch"` and exit.
4. Edit the comment to set `run_status: running`, `run_started_at`, `workflow_run_id`, `checked_out_sha`.
5. Dispatch on `command` to `.agent/commands/<command>.py`. Each command module exposes a `run(args, log_writer, workspace)` entry point. The handler streams structured records into the log writer.
6. Log writer rotates chunks at `logs.max_chunk_bytes_compressed`, gzips each chunk, accumulates them in a temporary directory.
7. On command return:
   - Compute `summary` per the command's `summary_completed` or `summary_error` schema.
   - Validate `summary` against the schema. Failure → terminal `error` with `error_kind: "summary_schema_violation"`.
   - Push manifest, chunks, and `summary.json` to `_agent_runs` in a single commit, with retry-on-non-fast-forward.
   - Edit the comment with terminal `run_status`, `summary`, `log_manifest_path`, `run_finished_at`.
8. All terminal-state writes are wrapped in `try/finally` so any uncaught exception still produces a terminal `error` envelope.

### 7.3 `close-on-merge.yml`

Triggered on `pull_request.closed` with `merged == true`.

```yaml
name: close-on-merge
on:
  pull_request:
    types: [closed]
permissions:
  issues: write
  pull-requests: read
jobs:
  close:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r .agent/scripts/requirements.txt
      - run: python .agent/scripts/close_on_merge.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
```

The script:
1. Reads the merged PR body for `Closes #N` or an explicit `agent-meta` cross-reference.
2. Verifies the linked issue is in `finished` state.
3. Closes the issue if not already closed and posts a comment with the merge SHA and PR link.
4. Locks the issue (`PUT /repos/{owner}/{repo}/issues/{n}/lock`) once the close-and-final-comment step has succeeded. This is idempotent: if the issue is already locked, the lock is left as-is.

**Intent.** Closing on merge is mechanically separate from the agent's `finished` write because human reviewers may sit on the PR for an arbitrary time. The agent's responsibility ends at PR creation; merge-time closure is a property of the repo's review process. Locking is performed here (rather than at issue creation) because the batch-job-handler needs to keep writing terminal envelopes throughout the working lifecycle, and `GITHUB_TOKEN` cannot comment on locked issues. After close, the lock acts as a tamper-prevention seal on the audit record.

## 8. Polling and heartbeat schedule

Defaults from `.agent/config.json`:

- Initial poll interval: 30 seconds.
- After 5 minutes: switch to 60 seconds.
- After 10 minutes: switch to 120 seconds.
- Total timeout: 3600 seconds (1 hour). Configurable per command if needed.

Every poll cycle, the primary also performs a heartbeat: re-reads its own issue body, asserts that `agent_id` matches its own (else self-abandons), and writes a fresh `status_ts`. Heartbeats are throttled to no more than once per `issue.heartbeat_min_interval_seconds` (default 60).

**Intent.** Long-running batch jobs can starve the heartbeat if the primary only updates `status_ts` on commit/return events. Tying heartbeat to the poll loop guarantees liveness signal even during a 90-minute test suite.

## 9. Skill 1: `batch-job`

### 9.1 Purpose

Submit one batch job from an active issue and return the result. Independent of `task-dag`. Usable by any agent harness that exposes a GitHub MCP server and can invoke shell commands.

### 9.2 Inputs

- `issue_number`
- `command`
- `args` (JSON, validated against the command schema before submission)
- `branch`
- `commit_sha`
- `subagent_id`

### 9.3 Outputs

- Resolved comment envelope on terminal status.
- Parsed `summary.json` (already validated against the command's summary schema).
- On runner-failure / poll-timeout: a structured error indicating which timeout fired.

### 9.4 Procedure

1. **Pre-flight.** Read issue via the GitHub MCP (`issue_read`). Assert `locked == true`, `agent-task` label present, body parses as `agent-meta`. Assert caller's `agent_id` matches the issue's `agent_id`.
2. **Submit.** `add_issue_comment` with the request envelope. Capture the comment id.
3. **Poll.** Read the comment via MCP at the configured intervals. On each poll, also call `heartbeat()`.
4. **Runner-pickup deadline.** If `run_status == null` after `comment.runner_pickup_timeout_seconds`, open a new issue labeled `runner-failure` containing the original comment id, the workflow file SHA on default branch at submission time, and the request envelope. Raise to caller.
5. **Running deadline.** If `run_status == running` past `comment.running_timeout_seconds`, same as above.
6. **Terminal.** Fetch `summary.json` via `get_file_contents` from `_agent_runs`. Validate against the command's `summary_completed` or `summary_error` schema (defense in depth). Optionally fetch chunks if drilling in.
7. **Ack.** Edit the comment to set `agent_ack: finished` and `agent_acked_at`. This is the only write the agent makes to the comment.
8. **Return** the envelope and summary.

### 9.5 Implementation

Two small Python scripts, `submit.py` and `poll.py`, plus a shared `common.py`. They use `PyGithub` or direct REST calls **only when invoked from inside an Actions runner**; when invoked from an agent harness, they call out to the GitHub MCP server through whatever mechanism the harness exposes (typically by emitting tool-call directives that the agent itself relays). The skill's `SKILL.md` documents both invocation modes.

**Intent.** The skill stays minimal and protocol-pure: envelope construction, polling, ack. Anything richer (dispatching multiple subagents, opening PRs) belongs in `task-dag`.

## 10. Skill 2: `task-dag`

### 10.1 Purpose

Manage the lifecycle of an issue as a DAG node: claim, plan subagents, dispatch jobs (via `batch-job`), merge subagent branches, open PR, schedule successors. Independent of `batch-job` only in the sense that it depends on it; `batch-job` is usable standalone.

### 10.2 Subskills / scripts

- `claim.py`: scan open issues with `agent-task` label; pick one whose `status` is `null`, or whose `status == working` with stale `status_ts`. Run the claim handshake. Return issue metadata if claimed, else null.
- `plan.py`: given an issue, read `instructions_inline` or fetch `instructions_path`; return the brief and any pre-declared subagent layout.
- `merge.py`: list subagent branches under the feature branch's prefix, merge each into the feature branch, push, delete subagent branches.
- `schedule_successors.py`: given a manifest of next-step issues (with optional `depends_on_prs`), create them with `status: null` so any qualifying agent can pick them up.

### 10.3 Procedure (high level)

1. `claim.py` selects an issue. Exits if none available.
2. `plan.py` produces the work brief.
3. The agent harness spawns subagents (mechanism is harness-specific; protocol does not require any particular isolation method). Each subagent:
   - Creates a subagent branch off the current feature-branch tip.
   - Iterates: edit code, commit, invoke `batch-job` skill to run a job, read result, possibly fix, repeat.
   - Returns its terminal SHA to the primary.
4. The primary heartbeats throughout.
5. When all subagents report success: `merge.py` consolidates their branches into the feature branch.
6. The primary creates a PR (`create_pull_request`) referencing the issue with `Closes #N` and listing run summaries.
7. The primary writes `status: finished` and closes the issue.
8. Optionally, `schedule_successors.py` creates next-step issues from the original plan.

### 10.4 Crash recovery

A new agent process running `claim.py` will discover stale issues and adopt them. After takeover:
1. Read the issue body and all comments.
2. Classify each comment: in-flight (`run_status` not terminal), terminal-unacked, terminal-acked.
3. For terminal-unacked: read the summary, decide next step, then ack.
4. For in-flight: wait for terminal status (subject to runner-pickup / running deadlines) or convert to abandoned if the deadlines have already elapsed.
5. If subagent branches exist but feature-branch merges are partial, restart from `merge.py` (idempotent: skip already-merged branches).

**Intent.** All recovery state is on GitHub; no local agent state is required for resumption. A successor with a completely empty workspace can pick up.

## 11. Human dashboard: GitHub Projects v2

### 11.1 Purpose

Provide humans (operators, reviewers, observers) with a real-time view of agent activity without requiring any agent-side action.

### 11.2 Setup (one-time, manual UI step)

1. Create a Projects v2 board at the org or user level.
2. Configure an **auto-add rule** with filter: `is:issue label:agent-task repo:<owner>/<repo>`.
3. Add custom fields (text/number/single-select) mapped from the `agent-meta` block:
   - `Issue Status` (single-select): `null`, `working`, `abandoned`, `finished`.
   - `Agent ID` (text).
   - `Status TS` (date-time).
   - `Feature Branch` (text).
   - `Parent Issue` (number).
   - `Depends On PRs` (text).
4. Configure built-in Project workflows:
   - When item added: set `Issue Status` from issue body parse.
   - When PR linked / merged: move card to Done.
5. Build views:
   - **Active**: filter `Issue Status: working`, sorted by `Status TS` ascending (stale at top).
   - **Backlog**: filter `Issue Status: null`.
   - **DAG**: table grouped by `Parent Issue`.
   - **Stuck**: filter `Issue Status: working` AND `Status TS` older than the staleness threshold.

### 11.3 How fields stay in sync

A small workflow `sync-projects.yml` (optional, recommended) runs on `issues.edited` and updates the Project item's custom fields by re-parsing `agent-meta`. This requires a Projects v2 GraphQL token with `project` scope; it lives in repo secrets and is used only by the workflow, never by the agent.

If the sync workflow is omitted, fields can still be populated by hand in the UI for tracked issues; the auto-add rule and built-in workflows will keep the basic add/close lifecycle correct.

**Intent.** Projects v2 is read-only from the agent's perspective. The agent operates on issue and comment primitives; Projects observes those. No agent change is required to enable or disable the dashboard.

## 12. Failure modes and recovery

| Failure | Detection | Recovery |
|---|---|---|
| Primary agent crashes | `status_ts` goes stale (> `issue.stale_seconds`) | Successor agent claims via takeover handshake |
| Workflow never fires | `run_status == null` past `comment.runner_pickup_timeout_seconds` | Agent opens `runner-failure` issue with workflow SHA + request envelope; gives up on this comment |
| Workflow hangs | `run_status == running` past `comment.running_timeout_seconds` | Same as above |
| Workflow killed before terminal write | `run_status == running` past timeout | Same as above |
| Branch SHA mismatch | Workflow detects in step 3 | Workflow writes terminal `error`; agent corrects and retries with a new comment |
| Concurrent takeover | Both agents wrote `agent_id`; re-read shows different `agent_id` | Loser self-abandons silently |
| Webhook redelivery | Workflow re-fires on same comment | Concurrency group serialises; idempotency check (`if run_status terminal, exit`) no-ops the dupe |
| Default-branch workflow broken | All `runner_pickup_timeout_seconds` exceed | Multiple `runner-failure` issues open; humans triage on the `runner-failure` label |
| Summary fails its schema | Workflow detects post-run | Terminal `error` with `error_kind: "summary_schema_violation"`; bug in command handler |
| Failed required dependency PR | Successor inspects `depends_on_prs`; finds closed-without-merge | Issue moved to `abandoned` |

## 13. Versioning and migration

- `protocol_version: 1` appears in every envelope, manifest, and config.
- Workflows reject envelopes with unknown `protocol_version` by writing `parse_error` with `error_kind: "unsupported_version"`.
- Bumping major version requires shipping the new workflow and command handlers on the default branch first; agents may then start emitting v2.
- Per-command schemas are independently versioned via filename (`run-tests.v2.schema.json`); the command name itself encodes the major version when needed (`run-tests-v2`).

## 14. Security notes

- **Public-repo log content is world-readable.** Logs may contain stack traces with paths and environment fragments. The handler should pass log records through a sanitiser that drops anything matching common secret patterns before writing chunks.
- **`GITHUB_TOKEN` permissions** in the handler workflow should be the minimum required (`contents: write`, `issues: write`). If the workflow is extended to do deploys, it pulls deploy credentials from repo secrets — those secrets are never readable by the agent and never appear in logs unless leaked by the command handler.
- **Author check is necessary but not sufficient.** A compromised `agent_login` account can submit arbitrary jobs. Treat the agent's PAT or App credentials as production secrets.
- **Runner-failure issues** must themselves carry the `agent-task` label and `agent-meta` so the same protocol covers their lifecycle. They are typically resolved by a human or a dedicated ops agent that has permission to edit workflow files on the default branch.

## 15. What this enables

Because the workflow runs in a regular GitHub Actions runner with whatever secrets and permissions the repo grants it, the protocol generalises beyond CI. Any operation expressible as a workflow command — and registered in `.agent/config.json` `commands` — is reachable by the agent through the same `batch-job` skill:

- Build, lint, type-check, run tests
- Container image build and push
- Cloud deploys (any provider with a published Action)
- Infrastructure-as-code apply (Terraform, Pulumi, CDK)
- Release tagging, changelog generation, package publish
- Cross-repo dispatch (a command handler that opens issues in another repo using a finer-grained PAT in repo secrets)
- Long-running data jobs up to the runner's max wall time (6 hours on hosted runners; longer on self-hosted)

Adding a capability is a workflow-side change (one new command schema and one handler module). Agents that don't know the new command are unaffected. Agents that do can use it through the same skill they already use for tests.

## 16. Compatibility

The skills are written to work with any agent harness that:

- Exposes a GitHub MCP server (or equivalent) capable of reading and writing issues, comments, and file contents.
- Can invoke shell commands (Python or Bash).
- Has some mechanism for the agent to dispatch sub-tasks (parallel sub-conversations, separate processes, separate worktrees — implementation is harness-specific).

Tested invocation modes:
- Locally, the skill scripts call the GitHub MCP server through the harness's tool relay.
- Inside Actions runners, the same scripts can call REST directly when given a token; this is used by the workflow handlers, not by the agent skills.

The protocol does not depend on any agent-specific feature. Agent CLIs other than the one used in initial development should work without modification, provided their MCP capability set covers the operations listed in §3 and §9.

## 17. Open questions

- Whether to provide schema-typed structured records inside log chunks, or leave them free-form by command (current spec leaves it to the command's manifest).
- Whether `summary.json` should be allowed to grow large enough to be more useful than the inline `summary` field. Current bias: yes, with the inline copy as a strict subset.
- Whether to add a lightweight `info` comment kind separate from `batch-job-request` for primary-to-self notes that should not trigger the workflow. Currently agents are expected not to post non-job comments at all.
