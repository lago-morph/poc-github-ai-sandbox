# task-dag

Manage the lifecycle of an agent-task issue as a DAG node.

## Subskills

- `claim.py` — find an unclaimed (or stale) issue and claim it via the
  CAS-by-re-read handshake. Provides a `heartbeat()` helper.
- `plan.py` — produce a work brief from `instructions_inline` or
  `instructions_path`.
- `merge.py` — overlay subagent branches onto the feature branch.
- `schedule_successors.py` — open follow-up issues with `status: null`.

## Inputs / outputs

- `claim.claim(client, candidate_issues=[...]) -> {issue, meta, agent_id, session_id} | None`
- `plan.plan(client, issue_number=...) -> {brief, source, ...}`
- `merge.merge_subagent_branches(client, feature_branch=..., subagent_branches=[...])`
- `schedule_successors.schedule_successors(client, successors=[...], base_branch=...)`

The skills are deliberately mechanical; orchestration (parallel
subagents, harness-specific dispatch) is the agent's job.

## Crash recovery

Per §10.4 a fresh agent process running `claim.py` will pick up
stale issues by `status_ts`. After takeover the agent classifies
each comment (in-flight / terminal-unacked / terminal-acked) and acts
accordingly via the `batch-job` skill.
