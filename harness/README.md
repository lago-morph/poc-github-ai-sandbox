# Agent-Mode Harness

This directory hosts the **agent-side** end-to-end test harness for
the agent-job-protocol POC. The protocol's workflow side is exercised
by `tests/` (unit + e2e) using an in-memory client; the harness here
drives the protocol against a **live** GitHub repo using only the
`mcp__github__*` MCP tools — no `gh` CLI, no direct REST calls.

## Architecture

```
+------------------------+        +----------------------+
| Dispatcher AI          |  spawns|  Subagent (per       |
| (Claude orchestrator)  +-------->  scenario)           |
+----------+-------------+        +----------+-----------+
           |                                 |
           | Bash:                           | mcp__github__*
           | python -m agent_lib ...         | MCP calls only
           |                                 |
           v                                 v
+------------------------+        +----------------------+
| .agent/scripts/agent_lib|       |  GitHub             |
| pure helpers + CLI      |       | (live repo state)   |
+------------------------+        +----------------------+
```

The dispatcher reads scenario specs in [`scenarios/`](scenarios/),
spawns one subagent per scenario, and aggregates results in
[`RUNS.md`](RUNS.md).

Each subagent uses two ingredients:

1. **`mcp__github__*` tools** to read/write GitHub state (issues,
   comments, branches, files, PRs).
2. **`python -m agent_lib <subcommand>`** invoked via the `Bash` tool
   to construct envelopes, render agent-meta blocks, and parse comment
   bodies. The CLI prints JSON / markdown to stdout; the agent feeds
   that output into the next MCP call.

The agent never invokes the workflow side directly — it relies on the
GitHub Actions handler to dispatch on `issue_comment` events and
write terminal envelopes back. Polling is implemented by repeated
`mcp__github__issue_read` calls.

## Repository conventions

- **Scenario label**: each scenario carries label
  `harness-scenario-NN` (`NN` = scenario number, zero-padded). The
  dispatcher uses these to filter forensic artifacts on later runs.
- **Agent-task label**: every protocol-managed issue carries
  `agent-task` (per `.agent/config.json`). Without this label the
  workflow does not dispatch.
- **Run id**: 8 hex chars, freshly generated per scenario invocation
  via `harness.lib.naming.new_run_id()`.
- **Unique id format**: `<scenario>-<run_id>` (e.g. `01-7e3f9a4c`).
  Used in branch names, issue titles, and `RUNS.md` rows.
- **Feature branch**: `agent/harness-NN-<run_id>` (see
  `harness.lib.naming.feature_branch`).
- **Subagent branch**: `<feature>/sub-<sub_id>` (see
  `harness.lib.naming.subagent_branch`).
- **Run artifacts** live on the orphan branch `_agent_runs` under
  `runs/<issue_n>/<comment_id>/`:
  - `manifest.json` — log manifest (per
    `.agent/schemas/log-manifest.schema.json`).
  - `log-NNNN.jsonl.gz` — one or more compressed log chunks.
  - `summary.json` — flat summary record.

## State map (where things live)

| Concern               | Location                                              |
|-----------------------|-------------------------------------------------------|
| Primary issue body    | `mcp__github__issue_read` -> agent-meta JSON block    |
| Subagent request      | comment body on the primary issue (envelope JSON)     |
| Terminal envelope     | same comment, body rewritten by handler               |
| Logs / manifest /     | `_agent_runs/runs/<issue_n>/<comment_id>/`            |
| summary               |                                                       |
| Feature work          | `agent/harness-NN-<run_id>` branch                    |
| Subagent work         | `agent/harness-NN-<run_id>/sub-<sub_id>` branches     |
| Final delivery        | PR head=feature branch -> base=main                   |

## Driving a scenario

The dispatcher:

1. Picks a scenario file from `scenarios/`.
2. Generates a `run_id`.
3. Spawns a subagent and hands it the scenario spec plus the
   computed identifiers (run_id, label, feature branch name).
4. The subagent follows the spec section by section:
   1. **Setup** steps create the branches, issue, labels.
   2. **Agent steps** make the lifecycle MCP calls.
   3. **Workflow expectations** describe what the workflow side
      should do automatically (no agent action required).
   4. **Assertions** are post-conditions verified via
      `harness.lib.asserts.*`.
   5. **Forensic artifacts** are what the dispatcher records in
      `RUNS.md` so future runs can clean up or replay.
5. The subagent reports back JSON containing
   `{run_id, issue_number, feature_branch, prs, result, ...}`.
6. The dispatcher appends a row to `RUNS.md`.

## Library

- `harness/lib/naming.py` — pure name/id helpers.
- `harness/lib/asserts.py` — pure predicates for post-MCP state.
- `.agent/scripts/agent_lib/` — pure helpers + CLI for envelope /
  agent-meta / terminal-status work. See package docstring for the
  full subcommand list.

## Test commands added for harness coverage

- `bad-summary` (used by scenario 07) — handler returns invalid
  summary; tests `summary_schema_violation` path.
- `chatty` (used by scenario 12) — emits enough log lines to force
  ≥2 log chunks.

Both commands are registered in `.agent/config.json` and have schemas
under `.agent/schemas/commands/`. They are exercised by unit tests
matching the existing `test_command_*` style.
