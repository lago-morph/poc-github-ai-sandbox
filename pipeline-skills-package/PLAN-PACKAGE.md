# PLAN-PACKAGE — building the bootstrap bundle in this POC

Status: design-stage. Designed for **overnight, unattended,
parallel execution** by a Claude Code dispatcher in this POC repo.
Audience: the dispatcher agent that picks this up next.

> Read `OVERVIEW.md` and `SPEC-PACKAGE.md` before this file. Read
> the per-skill SPECs at least once before dispatching their build
> subagents.

## What this plan does

Produces, in this POC repo under `pipeline-skills-package/`:

- All 5 distributable skill packages with bundled templates, lib/, SKILL.md.
- The test-harness skill (archetypes + scenarios + lib).
- The bootstrap bundle in two forms (recipe Markdown + tarball) at `pipeline-skills-package/bootstrap/dist/`.
- A build script at `pipeline-skills-package/bootstrap/build.py`.
- Contract tests under `tests/distribution/`.
- A run report at `pipeline-skills-package/runs/<run_id>/report.md`.

Does **not** modify any POC operational file: `.agent/`, `.github/workflows/`, `_agent_runs`, existing `tests/unit/` or `tests/e2e/`, existing `skills/batch-job/` or `skills/task-dag/` (those stay as POC reference implementations).

## Execution model

This plan follows the `parallel-subagent-fanout` pattern from
`software-factory/.claude/skills/parallel-subagent-fanout/`:

- Dispatcher (the agent reading this plan) owns planning, branching, state, merging.
- Subagents own work inside their sub-branches.
- All multi-subagent waves dispatch in a **single message** with `isolation: "worktree"`.
- State persists in `pipeline-skills-package/runs/<run_id>/state.json`.

Defaults:

- `run_id` = `YYYYMMDD-HHMMSS` UTC (derive via `date -u +%Y%m%d-%H%M%S`).
- Working branch = `pipeline-skills-package/build-<run_id>` (off the current branch, which should be `claude/assess-project-status-YBFY9` or main if merged).
- `MAX_PARALLEL` = 4.
- `CONFLICT_STRATEGY` = `fail` (all subagents touch disjoint paths, so conflicts should be impossible; fail is the safety net).

## Phases

| Phase | Mode | Wall-clock estimate | Blocks | Output |
|---|---|---|---|---|
| 0 — pre-flight | serial | ~5 min | Aborts on failure | State seeded |
| 1 — fan out skill builds | parallel (6 subagents, 2 waves) | ~45 min | Wave 1 must complete before wave 2 | 6 sub-branches |
| 2 — merge skill sub-branches | serial | ~10 min | Conflicts → abort | One feature branch |
| 3 — build the bootstrap | serial | ~15 min | Build script writes recipe + tarball | dist/ artifacts |
| 4 — contract tests | serial | ~10 min | Tests must pass | Green test report |
| 5 — self-retrospective + report | serial | ~10 min | None | report.md + handoff |
| 6 — commit + push | serial | ~5 min | None | All work on origin |

Total: ~100 minutes wall clock, dominated by Phase 1 subagent work.

## Phase 0 — pre-flight

Single-thread, dispatcher executes directly.

Steps:

1. Verify working tree clean: `git status --short` returns empty.
2. Verify on a feature branch (`git branch --show-current` ≠ `main`).
3. Verify POC test baseline: run `python -m pytest tests/ -q --tb=short`. Expect 446 passing. **If this fails, abort the entire plan.**
4. Create `pipeline-skills-package/runs/<run_id>/` directory.
5. Write initial `state.json`:

   ```json
   {
     "run_id": "<run_id>",
     "plan": "PLAN-PACKAGE.md",
     "started_at": "<utc>",
     "phases": [
       {"name": "pre-flight", "status": "in_progress"},
       {"name": "fanout-build", "status": "pending"},
       {"name": "merge", "status": "pending"},
       {"name": "build-bootstrap", "status": "pending"},
       {"name": "contract-tests", "status": "pending"},
       {"name": "retrospective", "status": "pending"},
       {"name": "commit-push", "status": "pending"}
     ],
     "subtasks": [
       {"id": "sub-01", "name": "batch-job", "status": "pending", "branch": "pipeline-skills-package/build-<run_id>--sub-01-batch-job"},
       {"id": "sub-02", "name": "task-dag", "status": "pending", "branch": "..."},
       {"id": "sub-03", "name": "orchestrate-issue", "status": "pending", "branch": "..."},
       {"id": "sub-04", "name": "onboarding", "status": "pending", "branch": "..."},
       {"id": "sub-05", "name": "composition-guide", "status": "pending", "branch": "..."},
       {"id": "sub-06", "name": "test-harness", "status": "pending", "branch": "..."}
     ]
   }
   ```

6. Commit `state.json` to working branch and push.
7. Mark phase 0 done in state.json; commit.

If anything in steps 1-3 fails, abort with a clear error and exit.

## Phase 1 — fanout skill builds

Six subagents, dispatched in two waves of 4 + 2 (or one wave of 6 if
the dispatcher's MAX_PARALLEL config allows).

### Step 1.1 — create sub-branches

For each subtask in plan order:

```bash
git checkout pipeline-skills-package/build-<run_id>
git checkout -b <subtask.branch>
git push -u origin <subtask.branch>
```

### Step 1.2 — dispatch wave 1 (4 subagents in one message)

Subtasks `sub-01` (batch-job), `sub-02` (task-dag), `sub-03` (orchestrate-issue), `sub-04` (onboarding).

Dispatch all 4 in a **single message** with multiple `Agent` tool
calls. Every call uses `isolation: "worktree"` and
`subagent_type: "general-purpose"`.

Each subagent's brief follows the subagent-prompting 9-section
template, populated from the recipe below.

#### Common brief boilerplate (every subagent gets this)

```
## Identity + goal
You are sub-<id> in a parallel fanout building the
pipeline-skills-package bootstrap bundle. Your subtask is to build
the `<skill-name>` skill package per its SPEC.

Run ID: <run_id>

## Context
You are working inside POC repo poc-github-ai-sandbox. The package
you are building lives at pipeline-skills-package/. Read these files
before doing any work:
  - pipeline-skills-package/OVERVIEW.md
  - pipeline-skills-package/SPEC-PACKAGE.md
  - pipeline-skills-package/skills/<skill-name>/SPEC.md (your spec)
  - The POC's SPEC.md (root)
  - The POC's existing skills/<skill-name>/ if it exists (reference impl)

## Repo and branch
- Repo root: /home/user/poc-github-ai-sandbox
- Branch: <subtask.branch>  ← commit and push here ONLY
- Do not switch to another branch.

## What to build
Inside pipeline-skills-package/skills/<skill-name>/ (already exists,
contains only SPEC.md):

1. Create SKILL.md per the spec's "SKILL.md frontmatter" section,
   plus a full body that explains trigger/inputs/outputs/procedure
   in agent-readable form. The SKILL.md is the user-facing skill;
   the SPEC.md is the implementation-spec for maintainers.

2. Create templates/ directory mirroring the spec's "Bundled
   templates" section. Each file is a byte-for-byte copy of the
   corresponding POC source file. For example, for batch-job:
     templates/agent/scripts/common.py  ← copy of .agent/scripts/common.py
     templates/agent/scripts/handler.py ← copy of .agent/scripts/handler.py
     [etc per the SPEC]

   Use `cp -a` or equivalent to preserve exact bytes.

3. Create lib/ directory if the skill needs runtime Python helpers
   (batch-job, task-dag, orchestrate-issue, onboarding do; composition-
   guide does not). Lift helpers from the POC's existing skill code
   where applicable, byte-for-byte for shared code.

4. Add a small README.md inside the skill directory that points the
   reader at SKILL.md (the entry point) and SPEC.md (the design doc).

## Don't do
- Do NOT modify the POC's .agent/, .github/workflows/, _agent_runs,
  tests/unit/, tests/e2e/, or existing skills/<skill-name>/.
- Do NOT add features or behaviors beyond the SPEC.
- Do NOT touch any other subtask's directory.
- Do NOT switch branches.
- Do NOT merge.

## Validation
Before reporting back:
1. `git status` on your branch shows only files under
   pipeline-skills-package/skills/<skill-name>/ (or test-harness/ for sub-06).
2. Every file listed in your SPEC's "Bundled templates" section
   exists in your templates/ directory.
3. Every templates/ file byte-matches the corresponding POC source
   file (verify with `cmp` or `sha256sum` comparison).
4. SKILL.md frontmatter parses as valid YAML.
5. `git push origin <subtask.branch>` succeeded.

## Deliverable shape
Report back with:
- Sub-branch name: <subtask.branch>
- Files created (count + list of top-level paths)
- SKILL.md size: <N> bytes
- Templates copied: <count> files
- Validation results: all <count>/<count> passed, or list failures
- Time elapsed: <seconds>
- Any deviations from the SPEC: <list or "none">

## Traps
- The POC's MCP returns body content HTML-escaped. Use html.unescape()
  before parsing.
- MCP add_issue_comment appends a Claude Code trailer; use
  raw_decode for JSON parsing.
- Branch sub-separator is double-dash (--sub-), never slash.
- Some `lib/` files may need to be Python packages; ensure
  `__init__.py` exists.
- For composition-guide: SKILL.md only, no templates, no lib.
```

#### Per-subagent customisations

Each subagent gets the boilerplate with `<id>`, `<skill-name>`,
`<subtask.branch>` substituted. The per-skill SPEC list is:

| id | skill-name | scope |
|---|---|---|
| sub-01 | batch-job | full templates + lib + SKILL.md |
| sub-02 | task-dag | full templates + lib + SKILL.md |
| sub-03 | orchestrate-issue | templates (superset) + lib + SKILL.md + brief-template.md |
| sub-04 | onboarding | dialog/recommendations/questions templates + lib + SKILL.md |

### Step 1.3 — collect wave 1 results

For each subagent's report:

- Parse the deliverable shape.
- Update `state.json` subtask entry: status to `dispatched_ok` or `failed`, fill in metrics.
- If failed, record the failure detail.

**Do not proceed to wave 2 until wave 1 is fully collected.** This is
a guardrail: failures in wave 1 should be visible before more work
fans out.

If any subtask failed, the dispatcher decides:

- For unattended/overnight execution: skip the failed subtask, continue with wave 2, mark for follow-up in the report.
- For attended execution: surface to the user.

### Step 1.4 — dispatch wave 2 (2 subagents in one message)

Subtasks `sub-05` (composition-guide) and `sub-06` (test-harness).
Same dispatch pattern as wave 1. The boilerplate adjusts for:

- `composition-guide`: SKILL.md only, no templates, no lib. Subagent's task is a thorough render of all 8 sections from its SPEC.
- `test-harness`: archetypes + scenarios + lib + SKILL.md, plus the initial 18-scenario catalog as YAML files. This is the largest subagent task.

### Step 1.5 — collect wave 2

Same as 1.3.

## Phase 2 — merge skill sub-branches

Single-thread, dispatcher executes directly.

Merge in plan order (sub-01 through sub-06):

```bash
git checkout pipeline-skills-package/build-<run_id>
for sub in sub-01 sub-02 sub-03 sub-04 sub-05 sub-06; do
  git merge --no-ff pipeline-skills-package/build-<run_id>--$sub-<name>
  # if conflict (should not happen given disjoint paths): abort, surface to user
  git push origin pipeline-skills-package/build-<run_id>
  git push origin --delete pipeline-skills-package/build-<run_id>--$sub-<name>
done
```

Update `state.json` after each successful merge.

If a merge produces a conflict, abort the plan, surface the
conflicting files, and require user resolution. This indicates a
subagent touched files outside its assigned scope.

## Phase 3 — build the bootstrap

Single-thread. The dispatcher creates the build script and runs it.

### Step 3.1 — write `bootstrap/build.py`

The script reads `pipeline-skills-package/` (excluding files listed
in `bootstrap/distribution-exclude.txt`) and produces:

- `bootstrap/dist/install.md` (recipe form)
- `bootstrap/dist/pipeline-skills-package.tar.gz` (tarball form)
- `bootstrap/dist/MANIFEST.txt` (sha256 sums of every included file)

Recipe Markdown structure:

```markdown
# Bootstrap recipe — pipeline-skills-package

This is a self-executing installation guide. Read it top to bottom
and create each file in the location its header specifies.

## Step 1 — verify environment
[install.md prologue from bootstrap/install.md]

## Step 2 — write files

### .claude/skills/batch-job/SKILL.md

```text
<inline content of that file>
```

### .claude/skills/batch-job/templates/agent/scripts/common.py

```text
<inline content>
```

[... repeat for every file in the bundle ...]

## Step 3 — verify install
[verification commands]
```

For binary files (none expected in v1) the recipe uses
base64-encoded blocks.

### Step 3.2 — write `bootstrap/distribution-exclude.txt`

Files NOT to include in the bundle:

```
pipeline-skills-package/runs/
pipeline-skills-package/bootstrap/dist/
pipeline-skills-package/bootstrap/build.py
pipeline-skills-package/PLAN-PACKAGE.md
pipeline-skills-package/RESUME.md
**/__pycache__/
**/.pyc
```

PLAN-PACKAGE.md and RESUME.md are POC-local; the new repo doesn't
need them. The new repo gets NEW-REPO-PLAN.md, TESTING-IN-POC.md
(for reference), and the OVERVIEW.md and SPEC-PACKAGE.md.

### Step 3.3 — run the build

```bash
python pipeline-skills-package/bootstrap/build.py \
  --source pipeline-skills-package/ \
  --output pipeline-skills-package/bootstrap/dist/
```

Verify the dist/ outputs exist and are non-empty. Compute manifest.

Update `state.json`.

## Phase 4 — contract tests

Single-thread. Run the test suite in `tests/distribution/`.

```bash
python -m pytest tests/distribution/ -v --tb=short
```

All tests must pass. If any fail, abort the plan and surface the
failures — the bundle is not shippable.

Also run the **full POC test suite** to verify no regression:

```bash
python -m pytest tests/ -q --tb=short
```

Expect 446 passing (POC baseline) plus the new distribution tests.

Update `state.json`.

## Phase 5 — self-retrospective + report

Single-thread.

Apply the `self-retrospective` pattern from
`software-factory/.claude/skills/self-retrospective/`:

### Step 5.1 — verify date

Call `date -u` and record the UTC date for the retrospective filename.

### Step 5.2 — write the run report

`pipeline-skills-package/runs/<run_id>/report.md`:

```markdown
# Build run report — <run_id>

Built the pipeline-skills-package bootstrap bundle.

## Summary
| Phase | Status | Elapsed | Notes |
| 0 — pre-flight | done | <s> | POC baseline confirmed at 446 tests |
| 1 — fanout | done | <s> | 6 subagents, 2 waves |
| 2 — merge | done | <s> | No conflicts |
| 3 — bootstrap build | done | <s> | Recipe + tarball, <N> files, <bytes> total |
| 4 — contract tests | done | <s> | <count> tests passed |
| 5 — retrospective | done | <s> | This file |

## Subagent results
| id | skill | files | bytes | status |
| sub-01 | batch-job | <n> | <b> | merged |
| ... |

## Bundle manifest
- Files: <count>
- Total size: <bytes>
- Recipe size: <bytes>
- Tarball size: <bytes>

## Deviations from plan
<list or "None">

## Bugs surfaced (if any)
<list with one-line evidence each>

## Recommendations for the new repo
<observations that should feed NEW-REPO-PLAN.md execution>

## Next step
The bundle is at pipeline-skills-package/bootstrap/dist/. Copy
either install.md or pipeline-skills-package.tar.gz into a fresh
pipeline-ai-sandbox repo and run the bootstrap there.
```

### Step 5.3 — write per-skill retrospective specs (if any new lessons)

If the build surfaced reusable lessons, draft per-skill retrospective
specs under `pipeline-skills-package/runs/<run_id>/retrospective/`.
Otherwise skip.

### Step 5.4 — update SPEC-PACKAGE.md if needed

If the build clarified a contract that's not yet documented in
SPEC-PACKAGE.md, propose the addition in the report (not in
SPEC-PACKAGE.md directly — let the user review).

## Phase 6 — commit + push

Single-thread.

1. `git add pipeline-skills-package/runs/<run_id>/`
2. `git add pipeline-skills-package/bootstrap/dist/` (if not gitignored — likely YES for tarball; the recipe MD may be desirable to commit for diffability)
3. Update `pipeline-skills-package/runs/<run_id>/state.json` with `commit-push` phase done.
4. `git commit -m "build pipeline-skills-package <run_id>"` with a body summarising the report.
5. `git push -u origin pipeline-skills-package/build-<run_id>`
6. Print the final state and the path to `report.md`.

## Overnight execution

For unattended overnight execution, set these flags before starting:

- `UNATTENDED=1` — failures in Phase 1 skip the failed subtask and continue.
- `CONFLICT_STRATEGY=fail` — keep the safety net; an unexpected conflict aborts cleanly.
- `MAX_PARALLEL=4` — keep within the parallel-subagent-fanout recommended cap.

If the plan aborts mid-execution, the next dispatcher session reads
`state.json` and resumes from the earliest incomplete phase. See
"Restart recovery" below.

## Restart recovery

On invocation, the dispatcher checks for an in-progress run:

1. Look for `pipeline-skills-package/runs/*/state.json` with any phase in `in_progress` or first `pending` after `done`.
2. If found, show the user (or auto-resume if `UNATTENDED=1`):
   - The run_id
   - Last completed phase
   - Next pending phase
   - Subtasks pending/dispatched/merged/failed
3. Resume from the earliest incomplete phase.
4. Never re-dispatch a subtask with status `merged` — it's already on the feature branch.
5. Never re-merge a sub-branch with status `merged` — it has been deleted from origin.

## Anti-patterns (this plan-specific)

- **Don't** modify any POC operational file. Read-only access to
  `.agent/`, `.github/workflows/`, `_agent_runs`, `tests/unit/`,
  `tests/e2e/` only.
- **Don't** dispatch subagents in separate messages — the harness
  only parallelises within one message.
- **Don't** dispatch without `isolation: "worktree"`.
- **Don't** merge sub-branches in completion order. Plan order only.
- **Don't** edit the recipe Markdown by hand. The build script
  regenerates it.
- **Don't** commit `pipeline-skills-package/bootstrap/dist/*.tar.gz`
  unless explicitly enabled (binary in git is friction). The recipe
  Markdown is OK to commit.

## Plan output

When the plan completes, `pipeline-skills-package/` contains:

```
pipeline-skills-package/
  OVERVIEW.md                           (already exists)
  SPEC-PACKAGE.md                       (already exists)
  PLAN-PACKAGE.md                       (already exists — this file)
  TESTING-IN-POC.md                     (already exists)
  NEW-REPO-PLAN.md                      (already exists)
  RESUME.md                             (already exists)
  skills/
    batch-job/
      SPEC.md                           (already exists)
      SKILL.md                          (NEW — written by sub-01)
      templates/                        (NEW)
      lib/                              (NEW)
      README.md                         (NEW)
    [task-dag, orchestrate-issue, onboarding, composition-guide similarly]
  test-harness/
    SPEC.md                             (already exists)
    SKILL.md                            (NEW — written by sub-06)
    archetypes/                         (NEW, 8 archetypes)
    scenarios/                          (NEW, 18 scenarios)
    lib/                                (NEW)
  bootstrap/
    install.md                          (already exists)
    build.py                            (NEW)
    distribution-exclude.txt            (NEW)
    dist/
      install.md                        (NEW — the recipe)
      pipeline-skills-package.tar.gz    (NEW — the tarball)
      MANIFEST.txt                      (NEW)
  runs/
    <run_id>/
      state.json
      report.md
tests/
  distribution/                         (NEW — contract tests)
    test_template_parity.py
    test_schema_validity.py
    test_skill_md_frontmatter.py
    test_install_dry_run.py
    test_recipe_idempotent.py
    test_archive_round_trip.py
    test_bundle_contents.py
    test_no_secrets_in_bundle.py
```

Plus a clean POC test baseline + new distribution tests all passing.

## When this plan completes, the next step is

The user takes `pipeline-skills-package/bootstrap/dist/install.md`
(recipe) OR `pipeline-skills-package/bootstrap/dist/pipeline-skills-package.tar.gz`
(tarball), copies it into a fresh `pipeline-ai-sandbox` repo, and
executes `NEW-REPO-PLAN.md` there.
