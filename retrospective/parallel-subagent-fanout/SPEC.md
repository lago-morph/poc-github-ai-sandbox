# `parallel-subagent-fanout` — implementation spec

A skill that takes a user task that decomposes into N independent
pieces and orchestrates the full multi-subagent workflow:
**plan → branch → dispatch → wait → merge → PR + report**.

## 1. Trigger conditions

The skill should activate when the user's request fits the pattern
"do N independent things and produce one cohesive deliverable":

- "Implement the four CRUD endpoints in parallel"
- "Add tests for these six modules"
- "Decompose this and parallelize"
- "Fan this out into N subagents"
- "Run this against each of these <items>"
- "Plan and dispatch this work as a multi-agent build"

Negative triggers (skill should NOT activate):
- Sequential work where step N depends on step N-1 (use
  `agent-dispatch-loop` instead).
- Single-shot tasks that don't benefit from parallelism.
- Pure read/research tasks (use `Explore` agent directly).

## 2. Inputs

The skill takes from the dispatcher:

- **Goal** (string) — the overall task, in user's words.
- **Decomposition hint** (optional list[string]) — if the user
  enumerated the subtasks, use them; else the skill decomposes.
- **Feature branch name** (optional) — if absent, derive from the
  goal: `feat/<slugified-goal>` or similar.
- **Base branch** (default: `main`).
- **Concurrency cap** (default: 4) — max subagents in flight at once.
- **Cleanup mode** (default: `auto-on-merge`) — see
  `forensic-vs-aggressive-cleanup`.
- **Test command** (optional) — if provided, run after the merge step
  and include results in the report.

## 3. Outputs

- A merged feature branch with all subagent commits.
- A PR (open or merged, depending on user preference) with body
  containing the run report.
- A return value to the dispatcher: `{ pr_number, feature_branch,
  subtasks: [{branch, agent_id, status, summary}] }`.

## 4. Workflow steps (the spine of the skill)

### Step 1 — plan

Main agent reads the goal and produces a `Plan` document:

```yaml
plan:
  goal: "<verbatim goal>"
  feature_branch: "feat/<slug>"
  base_branch: "main"
  subtasks:
    - id: "alpha"
      title: "<short>"
      brief: "<self-contained spec — see template in §6>"
      depends_on: []          # for future sequential variant; all empty in fanout
      expected_files: ["src/foo.py", "tests/test_foo.py"]
    - id: "beta"
      ...
```

The plan is written to `harness/plans/<run_id>.md` (or wherever the
project's plan-archive convention says) AND printed inline to the
dispatcher's chat for user review **before** any branch is created.

If the user has not pre-decomposed, the skill proposes a decomposition
and **waits for confirmation** by default (configurable: `--auto`).
The user often catches "you split this wrong" at the plan stage,
which is much cheaper than catching it after dispatch.

### Step 2 — branches

Once the plan is approved:

1. Create the feature branch from the base: `git checkout -b <feature>`
   or via `mcp__github__create_branch`. Capture HEAD sha.
2. For each subtask, create a sub-branch: `<feature>--sub-<id>`.
   **Use double-dash separator** (single `/` collides with the feature
   branch's git ref — see `github-mcp-tips`). Branch is created off the
   feature branch's HEAD.

All branches are created sequentially to avoid race conditions on the
default branch's tip.

### Step 3 — dispatch

For each subtask, spawn a subagent. Send all `Agent` tool calls in a
**single dispatcher message** so they run concurrently.

Each subagent's prompt is built from the brief template (§6) plus
constants:

- The repo path
- Its assigned sub-branch (e.g. `<feature>--sub-alpha`)
- Conventions (don't refactor, don't push to main, commit + push to
  the sub-branch, etc.)
- The deliverable shape (commit message, test commands, report format)

Subagents are dispatched with `run_in_background=false` for small
fanouts (≤4) and `true` for larger ones, so the dispatcher gets
notifications instead of inline returns.

### Step 4 — wait

Dispatcher receives async completion notifications (one per subagent).
For each one:

- Capture the subagent's report (summary, files changed, any test
  failures, any deviations from the brief).
- Record into a per-run state object.
- If a subagent reports failure or non-trivial deviation, the
  dispatcher pauses and surfaces the issue to the user before
  continuing — don't blindly merge half-done work.

If a subagent's wallclock exceeds an upper bound (default 30 min), the
dispatcher emits a "stalled subagent" notice and offers the user to
abort or wait.

### Step 5 — merge

Once all subagents are done (or explicitly abandoned):

1. Fetch every sub-branch tip locally.
2. For each in plan-order, merge into the feature branch:
   - `git checkout <feature>`
   - `git merge --no-ff <feature>--sub-<id> -m "merge sub-<id>"`
3. On conflict:
   - Halt the merge sequence.
   - Capture the conflicting paths.
   - Decide based on `conflict_strategy` parameter:
     - `fail` (default): abort the whole orchestration, report
       conflicts to user, leave sub-branches untouched.
     - `last-writer-wins`: take the latest sub-branch's version.
     - `first-writer-wins`: take the earliest's.
     - `manual`: open the conflict in the dispatcher's editor (if
       supported) and let the user resolve.
4. Push the feature branch.

### Step 6 — PR

`mcp__github__create_pull_request`:
- title: derived from goal (`feat: <goal-summary>`)
- base: `<base_branch>`
- head: `<feature_branch>`
- body: the **run report** (§7).

If the user pre-set a `Closes #N`, include it. Otherwise leave it for
manual addition.

### Step 7 — cleanup

Sub-branches stay until the PR is merged. On merge,
`close_on_merge.py`-style auto-deletion (per `forensic-vs-aggressive-cleanup`)
sweeps them. If the project doesn't have that workflow, the skill
falls back to deleting sub-branches itself after PR creation.

## 5. State machine (short form)

```
PLANNED -> BRANCHED -> DISPATCHED -> WAITING -> MERGED -> PR_OPENED -> DONE
                                  |
                                  v
                              ABANDONED (on subagent failure or user abort)
```

State is persisted to `harness/runs/<run_id>/state.json` so a
dispatcher restart can recover.

## 6. Subagent brief template

The brief sent to each subagent. Variables in `{{...}}` are filled
from the plan.

```
You are subagent {{id}} for fanout run {{run_id}}.

## Goal (your slice)
{{title}}

{{brief_body}}

## Your assignment
- Repo: /home/user/{{repo_dir}} (already checked out)
- Branch: {{sub_branch}} (already created at HEAD={{feature_head_sha}})
- Base branch: {{feature_branch}}

## Conventions
- DO commit + push to {{sub_branch}}.
- DO NOT push to main, the feature branch, or any other branch.
- DO NOT touch files outside your assignment area unless strictly
  necessary; if you do, justify in your final report.
- DO NOT refactor unrelated code.
- Run `{{test_command}}` before reporting "done"; include count.
- Keep your final report under 400 words.

## Deliverable
1. Code committed to {{sub_branch}}.
2. Test results.
3. A final report containing:
   - Files changed (paths)
   - Test count delta (was N, now M)
   - Any deviations from this brief, with reasons
   - Any blockers you couldn't resolve

When done, your code should already be pushed. Just return the report.
```

## 7. Run report template

The PR body format. Lives in `harness/runs/<run_id>/report.md` too.

```markdown
# Run report — {{goal_summary}}

- Run ID: {{run_id}}
- Feature branch: {{feature_branch}}
- Started: {{started_at}}
- Finished: {{finished_at}}
- Duration: {{duration}}
- Concurrency: {{n_subagents}} subagents

## Subtasks

| ID | Title | Branch | Status | Files | Tests |
|----|-------|--------|--------|-------|-------|
| alpha | … | …--sub-alpha | ✅ | 3 | +12 |
| beta  | … | …--sub-beta  | ✅ | 5 | +8 |
| gamma | … | …--sub-gamma | ⚠ deviated | 2 | +0 |

## Merge

- Strategy: {{conflict_strategy}}
- Conflicts: {{conflicts_list_or_none}}
- Final feature branch HEAD: {{sha}}

## Test summary
{{test_run_output}}

## Deviations / notes
{{aggregated_subagent_deviation_notes}}

## Cleanup
Sub-branches will be auto-deleted by close_on_merge on PR merge.
```

## 8. Anti-patterns

- **Don't dispatch before user approves the plan.** The user almost
  always wants to tweak the decomposition. Adding 30s of plan-review
  saves 10 minutes of "you split it wrong, redo."
- **Don't use `/sub-` separator.** It collides with the feature
  branch's git ref. Use `--sub-`. Encoded in the template.
- **Don't merge in arbitrary order.** Use plan-order so the run
  report's subtask table aligns with merge results, and so conflicts
  are reproducible.
- **Don't force-merge on conflict.** Default `fail` makes conflicts
  visible. The user picks the strategy if they want last-writer-wins.
- **Don't run >~6 subagents concurrently.** GitHub API rate limits and
  notification noise become problems. Default cap is 4.
- **Don't re-decompose after dispatch.** If a subtask turns out to be
  wrong-sized mid-run, abort the whole orchestration and replan. Don't
  patch live.
- **Don't skip the run report.** It's the single most useful artifact
  for the user reviewing the PR — never an "optional extra."

## 9. Implementation notes for the builder

The skill probably wants three modules:

- A **planner** that turns a goal into a `Plan` (LLM-driven, schema
  validated against §4 step 1's structure).
- An **orchestrator** that walks the state machine, dispatches
  subagents, polls for completions, runs the merge.
- A **reporter** that renders the run report.

Suggested file layout if implemented in Python (under
`skills/parallel-subagent-fanout/`):
- `SKILL.md` — user-facing description + activation docs
- `plan.py` — Plan schema + decomposition prompt
- `orchestrate.py` — state machine + dispatch + merge
- `report.py` — run report rendering
- `templates/{brief.md, report.md}` — Jinja-style templates

The skill should be agent-harness-agnostic: the dispatcher's `Agent`
tool is the only orchestration primitive needed. If the harness
exposes `mcp__github__*`, those handle branches/PRs; else use git CLI.

## 10. Test plan (when built)

- Unit: planner produces a valid Plan schema for a simple goal.
- Unit: orchestrator handles fail-on-conflict correctly (raises with
  conflict list, doesn't push half-merged feature branch).
- Unit: reporter renders the report from a Plan + result dict.
- Integration: dry-run mode that prints all the steps but doesn't
  dispatch — for review.
- Live: end-to-end on a scratch repo with a 3-subagent fanout (e.g.,
  "add tests for these three modules"). Verify all the artifacts: 3
  sub-branches → merged → PR → report.

## 11. Future variants

- **Sequential mode** — when subtasks have `depends_on` populated, walk
  the DAG instead of fan out.
- **Iterative mode** — combine with `agent-dispatch-loop` so the
  fan-out is a single iteration of a larger N-loop.
- **Heterogeneous mode** — different subagents get different
  `subagent_type` (e.g., one for impl, one for tests, one for docs).

These are explicit non-goals for v1.
