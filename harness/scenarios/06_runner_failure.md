# Scenario 06 — unknown command + workflow-not-fired sub-scenario

## Objective
Two sub-scenarios sharing one issue:

(a) Submit a request against a command that is not in
`.agent/config.json`'s `commands` list. Verify the handler returns a
terminal `error` with `error_kind="unknown_command"`.

(b) Post a comment on a NON-locked or NON-labeled issue and verify
the workflow does not run (no terminal envelope is ever written;
comment body remains the original).

## Prereqs
- Same as scenario 01. The command name `bogus-not-registered` must
  not appear in `.agent/config.json`.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(6, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create issue A (this is the locked+labeled one). Lock and label
   `["agent-task","harness-scenario-06"]`. Claim meta.
4. Create issue B (this is the gating-test one). DO NOT lock.
   DO NOT add the `agent-task` label. Just label
   `harness-scenario-06`.

## Agent steps (a) — unknown_command
1. Build envelope manually (skip `make-request` since it wouldn't
   know the command schema): set `command = "bogus-not-registered"`
   with otherwise valid envelope shape pointing at `feature`.
2. Post envelope on issue A.
3. Poll until terminal.
4. After observing terminal error, do not abandon yet — proceed to
   sub-scenario (b).

## Agent steps (b) — workflow-not-fired
1. Build a perfectly valid `echo` request envelope (use
   `make-request`).
2. Post it as a comment on issue B (the unlocked, unlabelled one).
3. Wait `2 * runner_pickup_timeout_seconds` (or a deterministic
   override; for the live harness, use the
   `runner_pickup_timeout_seconds` from `.agent/config.json` — by
   default 300s; the harness can override via fast-poll config).
4. Re-read the comment via `mcp__github__issue_read`.
5. Verify the body is byte-equal to what was posted (no terminal
   envelope was written).

After (b): close issue B by setting `state="closed"` and abandon issue
A's meta with `--reason "scenario_06_done"`.

## Workflow expectations
- (a) Handler emits terminal `error` with
  `error_kind="unknown_command"` and `error_detail` referencing the
  bogus command name.
- (b) The lock-and-sweep / dispatch path does not enqueue an unlocked
  or unlabeled issue's comments, so the body is never edited.

## Assertions
- (a) `assert_envelope_terminal(env_a, "error",
  expected_error_kind="unknown_command")`.
- (b) `comment_b_after['body'] == comment_b_initial['body']` (use a
  raw equality check; the harness records the posted body string).
- Both issues end with their final desired state (issue A abandoned,
  issue B closed).

## Forensic artifacts
- Issue A (abandoned, one terminal-error comment). Issue B
  (closed, one untouched comment).
