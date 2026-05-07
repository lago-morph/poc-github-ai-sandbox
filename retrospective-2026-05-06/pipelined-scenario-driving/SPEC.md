# SPEC: `pipelined-scenario-driving`

## Trigger conditions

### Direct triggers — activate immediately

- "Drive all the regression scenarios."
- "Re-run the e2e suite live."
- "How long will it take to drive 10 scenarios?"
- A request to drive ≥3 e2e scenarios in one session.

### Proactive triggers — offer the skill without being asked

Offer when:

- The HANDOFF.md or session plan calls for ≥3 live scenario drives.
- A `live-test-after-substantive-merge` invocation is about to drive multiple scenarios.
- The user says "regression rerun" (implies multiple scenarios).

Do NOT offer for:
- Single-scenario drives.
- Scenarios that all share the same merge target (they must serialize).

## Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `scenarios` | (required) | List of scenario IDs to drive. |
| `pipelined_subset` | (auto-detected) | Subset that can pipeline cleanly (no shared branches, no merge targets). |
| `serial_subset` | (auto-detected) | Subset that must serialize (PR-merging or shared resources). |
| `wait_budget_seconds` | `300` | Per-scenario maximum wait for terminal status. |

## Outputs

- One forensic record per scenario (issue + branches + envelope + terminal envelope + log manifest).
- A single `harness/RUNS.md` update covering all driven scenarios.
- Wall-time savings record for the session retrospective.

## Workflow steps

1. **Classify each scenario as PIPELINE-SAFE or SERIAL.**
   - **PIPELINE-SAFE:** scenario reaches a terminal state without opening a PR. No shared branches with other pipelined scenarios. Examples in this repo: 03, 04, 05, 06, 07, 08 (merge-conflict path), 13.
   - **SERIAL:** scenario opens + merges a PR, OR shares branches with another scenario in the batch. Examples: 01, 02, 10, 12.

2. **For the SERIAL set, drive in dependency order.** Each scenario opens, drives, acks, opens PR, closes issue, merges PR, waits for close-on-merge cleanup. Then move to the next.

3. **For the PIPELINE-SAFE set, fan out:**
   - Generate run_ids and feature branches for all scenarios up front.
   - Create issues for all scenarios in rapid succession (≤30s total).
   - Wait briefly (~60s) for lock-and-sweep to label all of them.
   - Create the branches (where needed for SHA-validating scenarios) in rapid succession.
   - Post envelopes for all scenarios in rapid succession.
   - Wait once for `wait_budget_seconds` (cover all scenarios with one wait).
   - Check all scenarios in batch via `mcp__github__issue_read`'s `get_comments` method.
   - Mark each scenario abandoned/finished + close, in any order.

4. **Update `harness/RUNS.md` once.** Append all scenarios' rows in a single commit. Reduces churn vs per-scenario commits.

5. **Verify branches.** After close-on-merge has fired for the SERIAL scenarios, list branches via `mcp__github__list_branches`. Forensic-only branches (from PIPELINE-SAFE forensic scenarios) linger; that's expected.

## Templates

### Pipeline-safe-vs-serial classifier (Python)

```python
PIPELINE_SAFE = {3, 4, 5, 6, 7, 8, 13}  # this repo's forensic scenarios
SERIAL = {1, 2, 10, 12}  # this repo's PR-completing scenarios

def classify(scenario_ids):
    pipe = [s for s in scenario_ids if int(s) in PIPELINE_SAFE]
    serial = [s for s in scenario_ids if int(s) in SERIAL]
    return pipe, serial
```

### Pipelined fan-out (pseudocode)

```python
# Phase A: create N issues + branches
issues = {}
for sid in pipeline_safe:
    body, run_id = make_issue_body(sid)
    issues[sid] = create_issue(title=f"[harness-{sid:02d}]", body=body, labels=[f"harness-scenario-{sid:02d}"])
# Phase B: wait once for labels
wait_for_label_on(issues.values(), label="agent-task", budget_s=90)
# Phase C: post envelopes for all
for sid, issue in issues.items():
    envelope = build_envelope(sid, run_id)
    post_comment(issue, json.dumps(envelope))
# Phase D: wait once
wait_seconds(180)
# Phase E: verify all
for sid, issue in issues.items():
    comments = get_comments(issue)
    request_comment = first_protocol_marker_comment(comments)
    envelope = json.loads(request_comment["body"])
    assert envelope["run_status"] in {"completed", "error", "parse_error"}, \
        f"scenario {sid} not terminal: {envelope!r}"
```

### `harness/RUNS.md` row template

```markdown
| NN | run_id | issue # | branch | PR# | terminal_kind | started | finished | one-line note |
```

Append one row per scenario in alphabetical/numeric order within the
session's section.

## Anti-patterns

- **Pipelining scenarios that each open + merge a PR.** Each merge
  fires close-on-merge. Two close-on-merge runs targeting the same
  branch pattern race. Branch cleanup is non-deterministic.
- **Posting N envelopes before the lock-and-sweep workflow has
  applied the `agent-task` label.** The batch-job-handler's `if:`
  clause filters on the label. Unlabeled issue = no run.
- **Forgetting that `_agent_runs` is shared.** N concurrent
  log-writing handlers race on it. Without
  `cas-retry-jitter-backoff`, this race produces 422s. With
  backoff (PR #68), it's safe.
- **Single-poll with too-short budget.** The slowest scenario in
  the batch sets the budget. If chatty(500) takes ~30s, that's
  fine; if it takes 90s, the wait must accommodate.
- **Serializing scenarios that don't need to be serial.** The
  default of "serialize for safety" undoes the wall-time savings.
  Be explicit about which scenarios commute.
- **No batch verification.** Per-scenario polling defeats
  pipelining. After the single wait, check all scenarios in one
  pass.

## Implementation notes

- **The 30s envelope-post window is approximate.** GHA can throttle
  rapid-fire issue/comment events from the same identity. If you hit
  rate limits, slow down to ~5s between envelopes; total wall time
  still beats serial.
- **Shared `_agent_runs` writer.** With `cas-retry-jitter-backoff`
  in place, concurrent writes are safe. Without it (pre-PR-#68),
  the backoff pattern is the prerequisite for pipelining anything.
- **The classification of pipeline-safe vs serial is per-repo.**
  In this repo's protocol, scenarios that abandon-without-PR are
  pipeline-safe. In another protocol, the boundary may be different.
- **Generalization.** This skill is harness-specific in shape but
  generic in principle: any e2e suite where scenarios are
  independent-modulo-some-shared-state benefits from this pattern.

## Test plan

- The skill is operational, not code-bearing in this repo. No unit
  tests are required for the pattern itself.
- Validate on the next session's regression rerun: classify, drive,
  measure wall time, compare to the per-scenario time × N estimate.
  Expect 5–10× speedup for forensic subsets.

## Living document

Amend this spec when:
- A new scenario is added — classify it as pipeline-safe or serial.
- The shared-resource list changes (e.g., a new orphan branch joins `_agent_runs`).
- The harness library evolves to formalize the classification (e.g., a `harness.lib.is_pipeline_safe(scenario_id)` helper).

Provenance: session 3, Phase 3 — drove scenarios 03/04/05/06/07/13
in pipelined parallel; total wall time ~4 minutes vs ~30 minutes
serial estimate.
