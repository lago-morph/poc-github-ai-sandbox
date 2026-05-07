# SPEC: `live-test-after-substantive-merge`

## Trigger conditions

### Direct triggers — activate immediately

- "We just merged X — should we live-test?"
- "Does it actually work?"
- "Drive an e2e against main."
- `/live-test` (or equivalent slash command if implemented).

### Proactive triggers — offer the skill without being asked

Offer when the previous turn included **any** of these merge events:

- A PR merged that changed `.github/workflows/*.yml`.
- A PR merged that changed env-var sourcing, config-key reads, or secret-/variable-reading code.
- A PR merged that changed retry, backoff, or concurrency control.
- A PR merged that changed schema validation order or dispatch-on-kind logic.
- A PR merged that changed any code path that runs only inside CI (cannot be exercised by unit tests with full fidelity).

Do NOT offer for:
- Doc-only PRs (`docs/`, `*.md` only).
- Refactors with no behavior change AND no infra surface change.
- Sessions where live infra is unavailable (e.g., the user explicitly said "skip Step 3").

## Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_scenario_id` | `01` (happy path) | Which scenario to drive first. The simplest scenario covering the changed subsystem. |
| `wait_budget_seconds` | `300` | How long to wait for label / terminal before declaring stall. |
| `regression_set` | `[01, ...]` | Scenarios to re-drive as regressions after the target succeeds. |

## Outputs

- A live forensic record on the canonical repo: issues + PRs + log manifests on `_agent_runs`.
- An updated `harness/RUNS.md` row per scenario (Started/Finished timestamps, workflow_run_id, manifest path, terminal status).
- If a bug is discovered: a separate fix-loop branch (handled by `bug-fix-loop-discipline`).
- If everything passes: a one-line "live-verified at <commit-sha>" record on the merge PR (a comment).

## Workflow steps

1. **Identify the smallest covering scenario.** If the merge changed schema dispatch, scenario 01 (happy path) covers it. If the merge changed retry logic, scenario 02 (multi-subagent) covers it because it forces concurrent writes. Pick the simplest scenario that actually exercises the changed code.

2. **Pre-flight.** Pull latest main locally. Run `python -m pytest tests/ -q` to confirm unit tests still pass on the merged main (sanity check that nothing was missed in the merge).

3. **Generate scenario IDs.** Use `harness.lib.new_run_id()` and `feature_branch(N, run_id)` for the right N. Set `AGENT_LOGIN` env var if your skill scripts need it (`os.environ.setdefault('AGENT_LOGIN', '<bot-login>')`).

4. **Create the issue with `agent-meta`.** Body must contain a fenced ` ```agent-meta ` block with `status: null`. Add the scenario-specific custom label (`harness-scenario-NN`) but NOT `agent-task` — lock-and-sweep applies that.

5. **Wait for the label.** Poll the issue every 30s up to `wait_budget_seconds`. Expected: `agent-task` label appears within ~60s. **If it doesn't appear within the budget, the deployment env is broken** — go straight to the bug-fix loop, not "wait longer".

6. **Drive the scenario lifecycle.** Build envelope via `python -m agent_lib make-request`, post via `mcp__github__add_issue_comment`. Wait for terminal `run_status`. Ack via the new follow-up form (`mcp__github__add_issue_comment` with a `kind: "agent-ack"` envelope).

7. **For PR-completing scenarios:** open PR, mark issue `finished`, close, merge. Verify `close-on-merge` cleaned both feature + sub branches.

8. **For forensic-only scenarios:** mark issue `abandoned` with a reason (e.g., `"unsupported_version parse_error received — abandoning per harness protocol"`), close with `state_reason=not_planned`. Branches linger; that's expected.

9. **Run the regression set.** For each scenario in `regression_set` that doesn't conflict with the target on shared resources, drive in pipeline (see `pipelined-scenario-driving`). Otherwise drive serially.

10. **Update `harness/RUNS.md`.** Append a row per scenario with run_id, issue#, PR#, started/finished, terminal status, notes. Commit + push + merge the doc change.

11. **Update HANDOFF.md** if any scenario surfaced a bug or required a fix-loop. Note the bug + PR# under "What this session changed".

## Templates

### Pre-flight script (Bash)

```bash
git fetch origin main && git pull origin main
python -m pytest tests/ -q --tb=line | tail -3
PYTHONPATH=.agent/scripts:harness python -c "
from harness.lib import new_run_id, feature_branch
rid = new_run_id()
print(f'{rid} {feature_branch(1, rid)}')"
```

### Issue body shape

```markdown
Scenario NN — <short description> (session X live test).

\`\`\`agent-meta
{
  "protocol_version": 1,
  "agent_id": null,
  "session_id": null,
  "status": null,
  "status_ts": null,
  "feature_branch": "agent/harness-NN-<run_id>",
  "base_branch": "main",
  "parent_issue": null,
  "depends_on_prs": [],
  "instructions_path": null,
  "instructions_inline": "<one-sentence brief>",
  "created_at": "<ISO timestamp>"
}
\`\`\`
```

### Wait-for-label loop (Bash; uses notification, not blocking sleep)

```bash
sleep 90 && echo "90s elapsed"
# run_in_background: true
# Then check via mcp__github__issue_read after notification arrives.
```

## Anti-patterns

- **Treating "all unit tests pass" as a green light to ship.** Unit tests can't see deployment env, GHA variable scope, or concurrent execution semantics.
- **Driving the scenario from a feature branch and expecting to test the feature-branch code.** GHA workflows for `issues.opened` / `issue_comment.created` execute from the **default branch's** checkout. Test infra changes pre-merge by hand-running the script with env vars set, OR merge first then live-drive.
- **Waiting only 60s before declaring the workflow didn't fire.** Lock-and-sweep can take 90s in a queue.
- **Polling without a budget.** Set `wait_budget_seconds` and respect it — a stalled workflow is signal, not noise.
- **Skipping the regression set.** "But scenario 01 passed" doesn't mean scenario 12 still does. Re-drive at least the scenarios that exercise paths your merge touched.
- **Manually deleting forensic branches.** They linger by design when no PR is merged. Sandbox proxy blocks `git push --delete` anyway.

## Implementation notes

- The skill is harness-specific in this repo (uses `agent_lib`, `harness.lib`, `mcp__github__*`). The general pattern (drive a happy-path live test after merge; budget the wait; pivot to bug-fix loop on stall) generalizes to any system with a CI runtime distinct from the unit-test runtime.
- For other deployments, replace MCP tooling with REST + a token. The pattern stays the same.
- The skill should NOT itself implement the bug-fix loop. When a stall is detected, hand off to `bug-fix-loop-discipline`.

## Test plan

- **Unit-test the harness library helpers** used by this skill (`new_run_id`, `feature_branch`, `subagent_branch`, the meta-block builders) — already covered by `tests/unit/test_harness_lib.py` (38 tests).
- **Behavioural test:** mock the MCP layer with the in-memory client; drive a synthetic scenario; assert the lifecycle state transitions match the spec.
- **Smoke test:** run against the canonical repo whenever a substantive merge lands; treat its success as the primary regression signal.

## Living document

This is a living spec. Amend when:
- A new failure mode is discovered live that the skill should detect proactively.
- The bug-fix-loop hand-off contract changes.
- The harness library API changes (rename a helper, add a new state-transition).

Provenance: derived from session 3's live-testing run on 2026-05-06,
specifically the discovery + fix of the `vars.AGENT_LOGIN` deployment-friction
bug (PR #56) and the `_retry_put` concurrent-writer race (PR #68). Both bugs
were invisible to 437 passing unit tests; both surfaced within minutes of
driving the live happy path.
