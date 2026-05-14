# Bootstrap recipe — pipeline-skills-package

This file is a self-executing installation guide. An agent reads
it top to bottom and creates each file at the path its
`### <path>` header specifies, using the content from the fenced
code block immediately below the header.

Two forms exist for this bundle: this recipe Markdown (what you
are reading) and `pipeline-skills-package.tar.gz`. They produce
byte-identical file trees.

## Section 1 — install instructions

The instructions below come verbatim from `bootstrap/install.md`
in this same bundle. Follow them.

# install.md — bootstrap contract for the new pipeline-ai-sandbox repo

Status: agent-facing contract.
Audience: the Claude Code agent that's been told "unpack this archive
and follow install.md" in a freshly created `pipeline-ai-sandbox` repo.

> If you are a human reading this: you don't run this yourself.
> Copy either `install.md` (recipe form) or
> `pipeline-skills-package.tar.gz` (tarball form) into your fresh
> `pipeline-ai-sandbox` repo, then tell a Claude Code agent:
> "Read install.md at the repo root and follow it."

## What you (the agent) are doing

You are bootstrapping a brand-new repo called `pipeline-ai-sandbox`.
This repo will become the maintenance project for a set of Claude
Code skills that implement the agent-job dispatch protocol described
in `docs/SPEC-PACKAGE.md`.

There are two forms of this bundle. You can be reading **either**:

- **Recipe form**: this `install.md` file is itself the entire
  bundle. Below in Section 4 you will find every file's content
  inlined in code blocks. Your job is to create each file at the
  path its header specifies.
- **Tarball form**: this `install.md` lives at the top of a tar.gz
  archive. The archive has already been extracted somewhere — verify
  the file tree is present, then proceed.

Look at Section 4. If it contains inlined file contents, you're in
recipe form. If Section 4 is short and points at sibling files, you're
in tarball form (the archive has been extracted and files are sitting
on disk already).

## Section 1 — pre-flight (always run)

Before writing anything, verify:

1. You are in a git repository:
   ```bash
   git rev-parse --is-inside-work-tree
   ```
   Must return `true`. If not, abort and tell the user to `git init`.

2. The repository has the expected name. Check `git remote -v` for an
   origin URL ending in `pipeline-ai-sandbox.git`. If not, **warn the
   user** and ask for explicit confirmation before continuing — this
   bundle is intended for the `pipeline-ai-sandbox` repo only.

3. The working tree is clean OR contains only this archive's files
   plus a `README.md`:
   ```bash
   git status --short
   ```
   If unrelated files are present, ask the user to stash them or
   confirm overwrite.

4. Your GitHub MCP credentials work:
   ```
   Invoke mcp__github__get_me
   ```
   Record the login. You'll need it later for `vars.AGENT_LOGIN`.

5. Verify Python 3.12 is available (or fall back to 3.11 if not):
   ```bash
   python --version
   ```

If any pre-flight step fails, abort and report the failure.

## Section 2 — file tree target

After install completes, the repo should contain:

```
pipeline-ai-sandbox/
  .claude/skills/
    batch-job/                 # full skill package
      SKILL.md
      templates/
        agent/...
        github/...
      lib/
      README.md
    task-dag/                  # same shape
    orchestrate-issue/         # same shape
    onboarding/                # same shape
    composition-guide/         # SKILL.md only
  test-harness/                # development-only test scaffolding
    SKILL.md
    SPEC.md
    archetypes/                # 8 archetypes
    scenarios/                 # 18 scenarios as YAML
    lib/                       # archetype loader, scenario runner, assertions
    runs/.gitkeep
  docs/                        # reference docs (copies from the POC's pipeline-skills-package/)
    OVERVIEW.md
    SPEC-PACKAGE.md
    skills/
      batch-job/SPEC.md
      task-dag/SPEC.md
      orchestrate-issue/SPEC.md
      onboarding/SPEC.md
      composition-guide/SPEC.md
    test-harness/SPEC.md
  bootstrap/
    install.md                 # this file, kept for reference
  NEW-REPO-PLAN.md             # the next step
  TESTING-IN-POC.md            # for reference (what was tested in the POC)
  README.md                    # written by NEW-REPO-PLAN.md Phase 1, not here
```

Note: README.md, AGENTS.md, CLAUDE.md, .github/workflows/, .agent/,
.gitignore, pytest.ini, etc. are **not** part of this bundle. They
get written by the dispatcher running `NEW-REPO-PLAN.md` Phase 1 and
Phase 2.

## Section 3 — install procedure

### If recipe form (Section 4 has inlined file contents)

For each block in Section 4:

1. Read the header `### <path>`.
2. Create any missing parent directories.
3. Write the file's content from the fenced code block immediately
   below the header.
4. After writing every file, run Section 5's verification.

Order does not matter for file writes (no file depends on another's
existence at write time).

### If tarball form (Section 4 points at sibling files)

The tarball has already been extracted. The file tree should already
match Section 2 except for files marked as `# written by ...`. Walk
the tree and verify presence. Run Section 5's verification.

### Conflict handling

If any file you're about to write already exists with content
differing from the bundle:

- **Don't overwrite silently.** Show the user the diff.
- Ask: "Overwrite, skip, or write to `<path>.new`?"
- Honor the user's choice.

For `README.md` specifically: it should not yet exist (Section 2 has
no README in the bundle). If it does, surface to the user.

`.gitignore` is in the same boat — if one exists, surface to user.

## Section 4 — bundled files

> **In recipe form, this section contains every file's content
> inlined.** It is large. Each file's content lives in a fenced code
> block immediately under a `### <path>` header. The content between
> the fences is the verbatim file content.
>
> **In tarball form, this section contains only a manifest listing.**
> The actual files have already been extracted.

[At build time, `bootstrap/build.py` generates this section as one of
two variants. The plan-time scaffolding looks like:]

```
### .claude/skills/batch-job/SKILL.md

<full SKILL.md content for batch-job>

### .claude/skills/batch-job/templates/agent/config.json

<copy of POC's .agent/config.json>

### .claude/skills/batch-job/templates/agent/scripts/common.py

<copy of POC's .agent/scripts/common.py>

[... continues for every file in the bundle ...]
```

## Section 5 — verification (always run after install)

After all files are written (or verified present in tarball form):

1. Walk the file tree against the expected manifest:
   ```bash
   find .claude/skills -type f
   find test-harness -type f
   find docs -type f
   ```
   Compare to the manifest in `MANIFEST.txt` (also bundled).

2. Verify SKILL.md frontmatter for each of the 5 + 1 skills:
   - File starts with `---`
   - Has `name`, `description`, `allowed-tools` keys

3. Verify Python files compile:
   ```bash
   find test-harness -name "*.py" -exec python -m py_compile {} +
   find .claude/skills -name "*.py" -exec python -m py_compile {} +
   ```

4. Verify YAML files parse:
   ```bash
   find test-harness/scenarios -name "*.yml" | xargs -I {} python -c "import yaml; yaml.safe_load(open('{}'))"
   find test-harness/archetypes -name "manifest.json" | xargs -I {} python -c "import json; json.load(open('{}'))"
   ```

5. Print a verification summary to the user:
   ```
   pipeline-ai-sandbox bootstrap install report
   - Files written: <count>
   - Files matched manifest: <count>
   - SKILL.md frontmatter valid: 6/6
   - Python files compiled: <count>
   - YAML files parsed: <count>
   - Status: SUCCESS
   ```

If anything fails verification, surface it and stop. Do not advance
to Section 6.

## Section 6 — next step

After successful verification:

1. Make an initial commit:
   ```bash
   git add .
   git commit -m "bootstrap pipeline-ai-sandbox from pipeline-skills-package bundle"
   ```

2. Push to origin (if origin is configured):
   ```bash
   git push -u origin main
   ```

3. Tell the user:
   ```
   Bootstrap complete. Next step:

   Read NEW-REPO-PLAN.md at the repo root. It describes a
   long-running, parallel, overnight-executable plan to:
     - Scaffold the maintenance project (README, AGENTS.md, CI)
     - Self-install the agent-job protocol in this repo
     - Materialise and validate all test harness archetypes
     - Implement and drive all 18 scenarios against live GitHub
     - Dogfood orchestrate-issue end-to-end
     - Write a retrospective

   When you're ready to start: tell a Claude Code agent
     "Read NEW-REPO-PLAN.md and execute it. UNATTENDED=1 if you
     want overnight, otherwise interactive."
   ```

## Recovery

If install was interrupted mid-recipe:

1. Re-run install.md from the beginning.
2. Section 3's conflict handling will detect already-written files
   and skip them (after confirming content matches).
3. Verification (Section 5) catches any partial writes.

Idempotency is a design goal — running install twice should be
safe.

## What this bundle does NOT do

- Set up `vars.AGENT_LOGIN` on the GitHub repo (`NEW-REPO-PLAN.md`
  Phase 0 handles that).
- Create the `agent-task` label (skills self-create on first install).
- Create the `_agent_runs` orphan branch (skills self-create).
- Configure GitHub Actions secrets (none required — uses default
  `GITHUB_TOKEN`).

## Provenance

This bundle was generated by `pipeline-skills-package/bootstrap/build.py`
in the POC repo `lago-morph/poc-github-ai-sandbox`. The manifest's
`generated_at` timestamp records when. Each bundled file's
`sha256` lives in `MANIFEST.txt`.

If you need to regenerate the bundle (because the POC source changed),
re-run the build script in the POC repo.

## Section 4 — bundled files (inlined)

Each `### <path>` header below identifies a destination path in
the repo root. The fenced code block beneath is the verbatim file
contents. Create any missing parent directories, then write the
file. Binary files appear in `base64` fences and must be decoded.

### NEW-REPO-PLAN.md

````text
# NEW-REPO-PLAN — the maintenance project for the 5 skills

Status: design-stage. Designed for **overnight, unattended, parallel
execution** by a Claude Code dispatcher in the new
`pipeline-ai-sandbox` repo.

Audience: the dispatcher agent that bootstraps and exercises the
new `pipeline-ai-sandbox` repo after the bundle has been applied.

> Read `OVERVIEW.md`, `SPEC-PACKAGE.md`, and the per-skill SPECs
> first. This plan assumes the bootstrap (`bootstrap/install.md`)
> has already laid out the file tree in the new repo.

## Prerequisites

Before this plan runs, the new repo must:

- Exist on GitHub as `<agent-account>/pipeline-ai-sandbox` (e.g. `jonathanmanton/pipeline-ai-sandbox`).
- Be checked out locally at a known path.
- Contain the bootstrap-applied file tree (see `bootstrap/install.md`).
- Have the dispatcher agent's GitHub MCP credentials available.

If any of these are unmet, the plan aborts in Phase 0.

## What this plan does

In the new `pipeline-ai-sandbox` repo, produces:

- An operational test harness with full archetype + scenario catalog
- A passing test baseline (target ~80% of scenarios green end-to-end)
- A CI setup that runs the test harness on every PR
- A README + AGENTS.md + CLAUDE.md tuned for the maintenance project
- An initial `agent-task` issue + protocol install (dogfooding)
- A retrospective document harvesting lessons from the new repo's
  first run

Does **not** modify the bootstrap-installed files except through
explicit, approved edits.

## Execution model

Same as `PLAN-PACKAGE.md`: parallel-subagent-fanout pattern,
state.json restart safety, MAX_PARALLEL=4, single-message dispatch
with `isolation: "worktree"`.

Working branch: `claude/initial-setup-<run_id>` off `main`.

## Phases

| Phase | Mode | Wall-clock estimate | Output |
|---|---|---|---|
| 0 — pre-flight | serial | ~5 min | Environment verified, state seeded |
| 1 — fanout: initial scaffolding | parallel (4 subagents) | ~30 min | CI, docs, .gitignore, project setup |
| 2 — apply protocol install | serial | ~10 min | `.agent/` + workflows live in this repo |
| 3 — fanout: archetype materialisation | parallel (8 subagents, 2 waves) | ~60 min | All 8 archetypes ready in `test-harness/archetypes/` (already there from bootstrap, this phase fleshes them out + validates) |
| 4 — fanout: scenario implementation | parallel (up to 8 waves of 4) | ~3 hours | All 18 scenarios as executable spec runners |
| 5 — fanout: drive scenarios live | parallel (waves of 4) | ~4 hours | Live execution against real GitHub; results captured |
| 6 — analyze results | serial | ~30 min | Test summary report; surface failures |
| 7 — dogfood: run orchestrate-issue end-to-end | serial | ~45 min | Open issue, drive orchestrate-issue, verify PR |
| 8 — self-retrospective | serial | ~15 min | Retrospective doc + per-skill specs if new lessons |
| 9 — commit + PR | serial | ~10 min | PR opened against main with full results |

Total: ~9-10 hours, dominated by live scenario execution. Suitable
for overnight.

## Phase 0 — pre-flight

Single-thread.

1. Verify on `main` branch initially: `git branch --show-current` returns `main`.
2. Verify working tree clean.
3. Verify the bootstrap-applied file tree is present:
   - `.claude/skills/batch-job/SKILL.md`
   - `.claude/skills/task-dag/SKILL.md`
   - `.claude/skills/orchestrate-issue/SKILL.md`
   - `.claude/skills/onboarding/SKILL.md`
   - `.claude/skills/composition-guide/SKILL.md`
   - `test-harness/SKILL.md`
   - `docs/OVERVIEW.md`
   - `docs/SPEC-PACKAGE.md`
   - `docs/skills/<name>/SPEC.md` (all 6)
   - `bootstrap/install.md` (kept for reference)
4. Verify the dispatcher's GitHub MCP credentials via `mcp__github__get_me`. Record the login as `agent_login`.
5. Verify Actions secrets / repo vars:
   - Set `vars.AGENT_LOGIN` to the agent_login from step 4 if not present (via REST through MCP if available; else surface a manual setup note).
6. Switch to a working branch: `git checkout -b claude/initial-setup-<run_id>`.
7. Create `runs/<run_id>/` directory.
8. Write initial `state.json`.

If anything fails in steps 1-5, abort.

## Phase 1 — fanout: initial scaffolding

Four subagents in parallel. Each touches disjoint paths.

| id | scope |
|---|---|
| sub-01 | Write top-level `README.md` for the maintenance project; document purpose, structure, how to run the test harness |
| sub-02 | Write `AGENTS.md` + `CLAUDE.md` for this repo (this is OK — it's a new repo, no pre-existing copies); include pointer to test harness conventions and the bundled docs |
| sub-03 | Write `.gitignore`, `pytest.ini`, `pyproject.toml` (Python dependencies); add `requirements.txt` for any dev deps |
| sub-04 | Write `.github/workflows/test-harness-ci.yml` to run the harness on every PR + a daily cron; write `.github/workflows/contract-tests.yml` if applicable |

Each subagent's brief follows the same 9-section pattern as
`PLAN-PACKAGE.md`'s Phase 1. Key constraints:

- Do not modify any bootstrap-installed file.
- Do not touch other subagents' assigned paths.
- Use `isolation: "worktree"`.
- Commit and push your sub-branch before reporting back.

Merge in plan order after all 4 complete.

## Phase 2 — apply protocol install (dogfood self-install)

Single-thread.

This phase invokes the **distributable skills' own self-install logic**
to lay out `.agent/` and `.github/workflows/` in this new repo. This is
the protocol's first dogfooding moment: the skills install themselves
in their own development repo.

Steps:

1. Read each of `batch-job`, `task-dag`, `orchestrate-issue`'s SKILL.md.
2. Execute their self-install logic (in dispatcher mode — the dispatcher
   plays the role of the invoking agent).
3. Verify `.agent/config.json`, `.agent/scripts/*`, `.agent/schemas/*`,
   `.github/workflows/{lock-and-sweep,batch-job-handler,close-on-merge}.yml`
   are in place.
4. Create the `agent-task` label on the GitHub repo (idempotent).
5. Create the `_agent_runs` orphan branch (idempotent).
6. Commit and push.

If any install step fails, the failure is interesting — it's a real
bug in the skill's install logic. Surface to the run report.

## Phase 3 — fanout: archetype materialisation

The 8 archetypes are already in the bootstrap. This phase **verifies**
each archetype is correctly materialised and adds any
archetype-specific runtime initialisation (e.g. for the `partial-protocol`
archetype, pre-populating `.agent/config.json` without workflows).

Eight subagents, two waves of 4.

| id | archetype | task |
|---|---|---|
| sub-01 | blank-repo | Verify manifest matches files; confirm `manifest.json` `expected_discovery` is correct |
| sub-02 | python-gha-with-agents-md | Same + verify pytest baseline runs in the archetype |
| sub-03 | node-circleci-no-agents-md | Same + verify `npm install` succeeds (if Node is available in sandbox) |
| sub-04 | monorepo-multi-language | Same + verify both GHA and Jenkinsfile parse |
| sub-05 | existing-skills-conflict | Same + verify the conflicting older skill file is present and differs from current bundle |
| sub-06 | partial-protocol | Same + verify `.agent/config.json` but no workflows |
| sub-07 | protocol-installed-not-onboarded | Same + verify full protocol install with no dialog file |
| sub-08 | gitlab-only | Same + verify `.gitlab-ci.yml` is present |

## Phase 4 — fanout: scenario implementation

The 18 scenarios from `test-harness/SPEC.md` need executable runners.
Each scenario's `lib/scenario_runner.py` orchestrates phases per the
YAML spec.

Dispatch in **5 waves of 4** (last wave has 2):

| Wave | Scenarios |
|---|---|
| 1 | `batch-job-happy-path`, `batch-job-parse-error`, `batch-job-branch-sha-mismatch`, `batch-job-runner-pickup-timeout` |
| 2 | `task-dag-claim-and-plan`, `task-dag-stale-takeover`, `task-dag-merge-conflicts`, `orchestrate-issue-single-subagent` |
| 3 | `orchestrate-issue-parallel-fanout`, `orchestrate-issue-restart-recovery`, `onboarding-blank-repo`, `onboarding-existing-agents-md` |
| 4 | `onboarding-resume-mid-interview`, `onboarding-decline`, `onboarding-revise`, `composition-guide-render` |
| 5 | `multi-scenario-soak`, `protocol-installed-not-onboarded` |

Each subagent's task: implement one scenario's runner. The brief
includes:

- Scenario YAML spec
- Archetype to use
- Skill under test
- Expected assertions per phase
- File path to write the runner to (`test-harness/runners/<scenario_id>.py`)
- Don't touch other scenarios' runners

Collect results between waves. If wave N produces a high failure
rate, surface to the run report before dispatching wave N+1.

## Phase 5 — fanout: drive scenarios live

For each implemented scenario, run it. The dispatcher does this in
**waves of 4** to balance throughput against the new repo's GitHub
quota (rate limit, Actions minutes).

For each wave:

1. Pick 4 scenarios ready to run (their runners are merged).
2. Dispatch 4 subagents in one message, each running one scenario.
3. Each subagent uses `target: live-new-repo` for scenarios that
   require live GitHub.
4. Each subagent creates a temporary GitHub repo per
   `test-harness/SPEC.md` (using `mcp__github__create_repository`
   under the dispatcher's GitHub identity), runs the scenario, and
   reports back results.
5. Wait for the wave to complete. Update state. Continue.

Failed scenarios:

- For `UNATTENDED=1`: leave the test repo for forensics, mark scenario failed, continue.
- Each failed scenario's temporary repo + diagnostics get linked in the run report.

## Phase 6 — analyze results

Single-thread.

1. Read every `harness/runs/<run_id>/<scenario_id>/state.json`.
2. Aggregate: total scenarios, pass count, fail count, error count.
3. For each failure, capture: scenario id, last completed phase, expected vs actual, link to the temporary GitHub repo + workflow runs.
4. Identify patterns: are failures concentrated in one skill? In one phase across scenarios? In live-GitHub flakiness?
5. Write `runs/<run_id>/test-results.md` with full summary.

## Phase 7 — dogfood: run orchestrate-issue end-to-end

Single-thread, but the orchestrate-issue invocation itself fans out
subagents internally.

This is the **dogfooding test**: use the protocol the new repo
maintains to do real work on the new repo.

1. Open a real `agent-task` issue in `pipeline-ai-sandbox`:
   - Title: "Add per-archetype README templates"
   - Body: includes `agent-meta` block; instructions say to add a 1-paragraph README to each archetype directory describing its purpose.
2. Invoke `orchestrate-issue` against that issue.
3. The skill claims the issue, plans subagents (one per archetype = 8 subagents), fans them out, merges, opens a PR.
4. The dispatcher monitors the run; if it gets stuck, intervene; otherwise wait for completion.
5. Verify the PR has 8 README files added, one per archetype.

This is the most ambitious live test. If it works, the protocol is
end-to-end validated in its own dev repo.

## Phase 8 — self-retrospective

Single-thread. Apply the `self-retrospective` skill pattern.

1. Verify UTC date via `date -u`.
2. Write `retrospective/YYYY-MM-DD-NN.md`:

```markdown
# Retrospective — new repo bootstrap run <run_id>

## Goal
Bootstrap pipeline-ai-sandbox and validate the 5 distributable skills
+ test harness end-to-end against real GitHub.

## Phases
[summary table from state.json]

## Live test results
[summary from Phase 6]

## Dogfooding result (Phase 7)
[did orchestrate-issue end-to-end succeed?]

## Bugs surfaced
[one bullet per bug; ground in concrete evidence]

## Workarounds invented
[anything where the as-designed behavior didn't work and we hand-patched]

## Patterns to harvest
[reusable lessons; if any merit a skill spec, list them]

## Specs/SPEC.md updates needed
[anything that should flow back to the SPEC]
```

3. If any new reusable lessons emerged, draft per-skill specs at
   `retrospective/<date>-<seq>/skills/<skill-name>/SPEC.md` per the
   `self-retrospective` skill output structure.

4. Draft `AGENTS-suggestions.md` with 5-15 proposed `AGENTS.md`
   additions, each with a copy-paste-ready rule and a one-line
   rationale.

## Phase 9 — commit + open PR

Single-thread.

1. Merge any remaining sub-branches into the working branch.
2. Push the working branch to origin.
3. Open a PR via `mcp__github__create_pull_request`:
   - Title: `Initial setup + first live-test sweep (<run_id>)`
   - Body: summary table from `runs/<run_id>/test-results.md`,
     dogfooding result, retrospective excerpt.
   - Target: `main`.
4. Print the PR URL.

The user reviews the PR in the morning and merges (or comments back
with adjustments).

## Restart recovery

Same model as `PLAN-PACKAGE.md`. On restart:

1. Read `runs/<run_id>/state.json`.
2. Identify the earliest incomplete phase.
3. For Phase 4 and Phase 5 (the long parallel ones), per-scenario
   sub-state lives in `harness/runs/<run_id>/<scenario_id>/state.json`.
   Resume per scenario based on its sub-state.

## Anti-patterns (this plan-specific)

- **Don't** create real GitHub repos outside the test harness's
  temporary-repo namespace. Production-like repos belong to the user.
- **Don't** run live scenarios in parallel waves bigger than the
  agent's GitHub rate limit allows. Default wave size 4 is
  conservative; raise only after observing slack.
- **Don't** leave failed scenarios' temporary repos around silently —
  link them in the run report.
- **Don't** skip the dogfood phase (Phase 7) — it's the single most
  valuable test in this plan.
- **Don't** modify any bootstrap-installed file as part of this plan
  without explicit user approval. If a bug requires a fix, the fix
  belongs in the source POC + a re-build of the bundle.

## Plan output

When the plan completes, `pipeline-ai-sandbox` contains:

```
pipeline-ai-sandbox/
  README.md                    (Phase 1)
  AGENTS.md, CLAUDE.md         (Phase 1)
  .gitignore, pytest.ini, …    (Phase 1)
  .agent/                      (Phase 2 — self-install)
  .github/workflows/           (Phase 2 + Phase 1 CI)
  .claude/skills/              (from bootstrap, unchanged)
  test-harness/
    archetypes/                (validated in Phase 3)
    scenarios/                 (unchanged)
    runners/                   (NEW — Phase 4)
    runs/<run_id>/             (Phase 5)
  retrospective/<date>/        (Phase 8)
  runs/<run_id>/
    state.json
    test-results.md
    report.md
  docs/                        (from bootstrap, unchanged)
```

And one PR opened against `main` with the run report and
retrospective.

## What happens after this plan succeeds

The new repo is the home for ongoing skill maintenance:

- New scenarios are added under `test-harness/scenarios/`.
- New archetypes for newly-observed real-world setups go under `test-harness/archetypes/`.
- Skill changes go through the protocol they implement: open an `agent-task` issue, invoke `orchestrate-issue`, review the PR.
- Periodic retrospectives harvest reusable lessons.
- When a release is ready, a separate "build distribution" workflow
  produces a refreshed `pipeline-skills-package.tar.gz` (only the
  user-facing 5 skills — not the test harness).

The POC repo (`poc-github-ai-sandbox`) is no longer modified. It
remains as a historical reference.

````

### docs/OVERVIEW.md

````text
# OVERVIEW — pipeline-skills-package

> If you are picking this work up cold, read this file first. It is the
> map for everything else in `pipeline-skills-package/`.

This directory is the **derived work** product of the
`poc-github-ai-sandbox` proof-of-concept. The POC validated a protocol
for AI agents to dispatch work into GitHub Actions runners using only
GitHub MCP transport. This directory packages that protocol as a set of
distributable Claude Code skills, plus the bootstrap and plans for the
next phase of work.

The POC repo (everything outside this directory) is preserved as-is.
Nothing under `pipeline-skills-package/` modifies POC code, tests,
workflows, or the `_agent_runs` branch.

## Three artifacts, two destinations

```
This POC repo (poc-github-ai-sandbox)
   │
   │  Partial testing here against bundled skill templates,
   │  schema validators, and onboarding interview logic.
   │  POC's existing 446 tests stay untouched.
   │
   ▼
Build the self-extracting bootstrap bundle
   │  (lives at pipeline-skills-package/bootstrap/dist/ once built)
   │
   │  Archive contains: 5 distributable skills + test harness +
   │  per-skill specs + install.md + new-repo plan + design docs.
   │  Two forms generated from one source: a single recipe Markdown
   │  file AND a tar.gz, byte-equivalent in content.
   │
   ▼
User copies archive into a brand-new repo named `pipeline-ai-sandbox`
   │
   │  Tells an agent: "unzip/expand and follow install.md"
   │
   ▼
New repo (pipeline-ai-sandbox, the maintenance project)
   │
   │  Test harness runs here (real GitHub via the agent's own MCP
   │  credentials — no separate test account).
   │  Full testing, ongoing development of the 5 skills.
   │  POC repo stays preserved as historical reference.
   │
   ▼
Future distribution builds (5 user-facing skills only;
test harness stays in the maintenance repo).
```

## The three pieces

### 1. This POC repo

The home of the original protocol implementation. Everything under
`.agent/`, `.github/workflows/`, `skills/batch-job/`, `skills/task-dag/`,
`harness/`, `tests/`, and `_agent_runs` is the POC. It will not be
modified by this packaging work.

Inside the POC, `pipeline-skills-package/` is a new subdirectory that
contains:

- This file (`OVERVIEW.md`)
- A package-level spec (`SPEC-PACKAGE.md`)
- Implementation plans (`PLAN-PACKAGE.md`, `NEW-REPO-PLAN.md`)
- Per-skill specs under `skills/<name>/SPEC.md`
- Test-harness spec under `test-harness/SPEC.md`
- A testing strategy doc (`TESTING-IN-POC.md`)
- A bootstrap install contract (`bootstrap/install.md`)
- A handoff prompt (`RESUME.md`)

The eventual build artifacts (recipe + tarball) land under
`pipeline-skills-package/bootstrap/dist/` — that path is gitignored by
default but the recipe is small enough to commit if desired.

### 2. The self-extracting bootstrap bundle

Two forms, same content:

- **Recipe Markdown** — a single file with all bundled files inlined in
  fenced code blocks. An agent reads it top to bottom and creates each
  file in the location its header specifies. Pure text. Diffs cleanly.
- **Tarball (tar.gz)** — a traditional archive arranged so that
  extracting at repo root places everything correctly. Faster to apply
  in one step.

Both forms include `install.md` as their entry point. `install.md`
tells the agent what to verify, what to copy where, and how to confirm
the install succeeded. Both forms are generated from one source
directory by a small build script.

### 3. The new repo: pipeline-ai-sandbox

A freshly created GitHub repo. The user copies the archive in,
tells an agent to extract and run `install.md`, and the resulting repo
contains:

- The 5 distributable skill packages with bundled templates
- The test harness (development-only — does not ship in future
  distributions)
- All per-skill specs and design docs
- A working CI setup so the test harness can drive real GitHub Actions
- A README explaining the maintenance project's purpose

From there, the new repo is the home for ongoing skill development.
It dogfoods the protocol: the test harness drives real issues, real
batch-jobs, real subagent fanout against the new repo itself, using
the agent's own MCP credentials. No separate test account required.

## The five distributable skills

| Skill | Role |
|---|---|
| `batch-job` | Submit one batch job from an active issue, poll for terminal status, ack. Self-installs its templates on first invocation. |
| `task-dag` | Claim issue, plan subagents, merge sub-branches, schedule successors. Self-installs its templates. |
| `orchestrate-issue` | End-to-end primary-agent loop for heavy adoption. Wraps `task-dag` + `batch-job` into one invocation: claim → plan → fan out → batch-job → merge → PR. |
| `onboarding` | Interview-based discovery of an existing repo's workflow; produces a recommendations document and optionally applies edits. Triggered automatically when other skills detect they are uninstalled, or on demand. |
| `composition-guide` | SKILL.md-only reference explaining how to compose the four implementation skills above for users who prefer the primitives over the orchestrator. |

Each skill is a fully self-contained Claude Code skill package:

- `SKILL.md` with frontmatter for skill-tool discovery
- Bundled templates (workflow YAMLs, `.agent/` scripts, schemas, config)
- Self-install logic embedded in SKILL.md ("if these files are missing,
  copy them from this skill's `templates/` directory into the target
  repo at these paths")

A skill is "installed" in the target repo when `.agent/config.json`
is present. A repo is "onboarded" when both `.agent/config.json` and
the onboarding dialog file (on the well-known branch
`agent-job-protocol/onboarding`) are present.

## The test harness (development only)

The test harness is the 6th skill in the bundle but it is
**not part of the eventual end-user distribution**. It lives only in
the new repo. Its purpose:

- Generate synthetic repo archetypes (with/without AGENTS.md,
  with/without CI, GitLab vs GHA vs Jenkins, etc.).
- Drive the 5 distributable skills against those archetypes.
- Validate end-to-end behavior against real GitHub from an agent
  sandbox using the agent's own MCP credentials.

See `test-harness/SPEC.md` for full detail.

## What "install" means at each level

| Boundary | What "install" does |
|---|---|
| Skill into target repo | Each skill, on first invocation, detects whether its templates are present in the target repo (under `.agent/`, `.github/workflows/`, `.claude/skills/<name>/`). If missing, the skill copies its bundled templates into place via tool calls. |
| Bootstrap into new repo | The agent in the new repo expands the archive (extract tarball or follow recipe Markdown), then runs the install.md procedure to lay out the skills, test harness, specs, and CI files. |
| Future end-user adoption | A user in any project invokes any of the 5 skills directly. The skill self-installs its templates. The onboarding skill can also be invoked explicitly for guided adoption. |

## Why this structure

- **POC stays a POC.** Treating it as historical reference makes it
  reliable as a source of truth for the protocol's working state.
- **One subdirectory contains all derived work.** Reviewers and future
  agents can tell at a glance what is POC and what is package.
- **The archive is the handoff.** It is the only artifact that
  crosses the boundary between this repo and the new one. Everything
  the new repo needs to bootstrap is inside it.
- **Templates are contract-tested copies, not symlinks.** A test in
  this POC asserts that bundled templates byte-match the POC's
  working source. The POC remains canonical until the new repo
  takes over.
- **Self-installation per skill.** Each skill is independently usable
  in any project that has Claude Code skills enabled. No global
  installer step.

## How to navigate this directory

| If you want to … | Read |
|---|---|
| Understand the whole package | This file, then `SPEC-PACKAGE.md` |
| Know how each skill behaves | `skills/<name>/SPEC.md` |
| Know how the test harness behaves | `test-harness/SPEC.md` |
| Build the bootstrap archive in this repo | `PLAN-PACKAGE.md` |
| Test the work in this repo without disrupting the POC | `TESTING-IN-POC.md` |
| Set up the new `pipeline-ai-sandbox` repo from the archive | `bootstrap/install.md`, then `NEW-REPO-PLAN.md` |
| Continue this work in a future session | `RESUME.md` |

## Provenance

This directory was created on a `claude/assess-project-status-YBFY9`
branch in `lago-morph/poc-github-ai-sandbox`. The design decisions
captured here came from a single planning conversation that reviewed
the POC's state, distilled the protocol from `SPEC.md`, and produced
the architecture described above.

````

### docs/SPEC-PACKAGE.md

````text
# SPEC-PACKAGE — pipeline-skills-package

Status: design-stage
Audience: implementers building the bootstrap bundle in this POC repo

> Read `OVERVIEW.md` before this file. This is the meta-spec that
> cross-references the per-skill SPECs and defines the package-level
> contracts that apply to all of them.

## The 6 skill specs

| Skill | SPEC | Distributable? | Self-installs? |
|---|---|---|---|
| `batch-job` | [`skills/batch-job/SPEC.md`](./skills/batch-job/SPEC.md) | yes | yes |
| `task-dag` | [`skills/task-dag/SPEC.md`](./skills/task-dag/SPEC.md) | yes | yes |
| `orchestrate-issue` | [`skills/orchestrate-issue/SPEC.md`](./skills/orchestrate-issue/SPEC.md) | yes | yes |
| `onboarding` | [`skills/onboarding/SPEC.md`](./skills/onboarding/SPEC.md) | yes | indirectly (creates well-known branch + dialog dir) |
| `composition-guide` | [`skills/composition-guide/SPEC.md`](./skills/composition-guide/SPEC.md) | yes | no (docs-only) |
| `test-harness` | [`test-harness/SPEC.md`](./test-harness/SPEC.md) | **no** (dev only) | no |

The 5 distributable skills are what end users invoke. The
test-harness skill is bundled with the bootstrap (so the new repo
has it from day one) but excluded from any future distribution build.

## Package-level contracts

These contracts apply across all 5 distributable skills.

### Skill installation scope

All skills install at the **project level**: `.claude/skills/<name>/`
inside the target repo. Never at the user level (`~/.claude/skills/`)
in v1. Rationale: the protocol's `.agent/` directory and workflow
YAMLs live in the repo; the skills that drive them should too — same
audit boundary, same versioning, same review surface.

### Self-install marker

A skill considers the protocol "installed" when `.agent/config.json`
exists in the target repo. Each skill, on invocation, checks this
marker and self-installs its bundled templates if missing.

A skill considers the repo "onboarded" when both:

- `.agent/config.json` is present
- A dialog file exists on the well-known branch `agent-job-protocol/onboarding`

Not-onboarded is fine. The 4 protocol skills work standalone. The
onboarding skill is offered, never required.

### Conflict handling on install

If a target file exists at a path the skill wants to install:

1. If content is byte-identical to the bundled template → no-op.
2. If content differs:
   - Compute a diff and show to the user.
   - Ask: "overwrite, skip, or write to `<path>.new` for manual merge?"
3. If the user declines and selects skip, the skill records the skip
   in its own state log (`.agent/installs/<skill>.log`) and proceeds.

`AGENTS.md` and `CLAUDE.md` are **never** in the installable file
list of any of the 5 skills. The onboarding skill alone can propose
pointer-line edits to those files, and only with explicit per-file
user approval.

### Bundled templates discipline

Each skill bundles **its own** copy of every template file it needs.
Some files (e.g. `.agent/scripts/common.py`) appear in multiple skill
packages. The contract test (`tests/distribution/test_template_parity.py`)
asserts that:

- Each bundled template byte-matches the POC's working source.
- Across skills, copies of the same template are byte-identical to each other.

If the POC source changes, the contract test fails until the bundled
copies are regenerated.

### SKILL.md frontmatter

Every distributable skill's SKILL.md has:

```yaml
---
name: <skill-name>
description: |
  <2-4 sentence description, includes trigger phrases the skill matches>
allowed-tools:
  - <list of tools the skill calls>
---
```

`description` is the substring Claude Code matches when routing the
Skill tool. It must mention at least one canonical trigger phrase
and must end with the self-install note (where applicable).

### Versioning

Each skill's `SKILL.md` carries a `# Version` header at the bottom:

```markdown
---
Version: 1.0.0
Protocol-version: 1
Last-synced-from-POC: 2026-05-14
---
```

Bumping `Protocol-version` requires shipping the new handler on the
default branch first (per POC SPEC §13).

## Cross-skill behaviors

### Skill A invokes skill B

When `orchestrate-issue` invokes `batch-job` or `task-dag`, it calls
into the **Python helpers** (importable as a library), not the
Skill-tool invocation. The Python helpers are part of the bundled
templates and live at `.agent/scripts/agent_lib/` plus the skill's
own `lib/` directory.

Calling another skill via the Skill tool from inside an executing
skill is **not supported** in v1 — too easy to recurse.

### Onboarding referrals

When any of the 4 protocol skills self-installs and notices the
absence of an onboarding dialog file, it emits a one-time message:

> Protocol installed. Onboarding has not been run in this repo. Run
> `/onboarding` for guided integration with your existing workflow,
> or skip — the skills work standalone.

The message appears once per skill per session (skill records the
hint in `.agent/installs/<skill>.log`).

## Bundle structure

The bootstrap bundle has this layout (the recipe Markdown and the
tarball both produce this tree when applied/extracted):

```
<repo-root>/
  .claude/skills/
    batch-job/
      SKILL.md
      templates/agent/...
      templates/github/...
      lib/...
    task-dag/
      SKILL.md
      templates/...
      lib/...
    orchestrate-issue/
      SKILL.md
      templates/...
      lib/...
    onboarding/
      SKILL.md
      templates/...
      lib/...
    composition-guide/
      SKILL.md
  test-harness/
    SKILL.md
    archetypes/...
    scenarios/...
    lib/...
    runs/.gitkeep
  docs/
    OVERVIEW.md             (the same OVERVIEW.md the POC has)
    SPEC-PACKAGE.md
    skills/<name>/SPEC.md   (all 6 specs replicated for in-repo reference)
    test-harness/SPEC.md
  bootstrap/
    install.md              (the agent-facing contract)
  NEW-REPO-PLAN.md
  TESTING-IN-POC.md         (so the new repo has a copy of the POC's testing strategy for reference)
  README.md                  (new-repo-specific README written by install.md)
```

The recipe Markdown also includes `install.md` as its first section so
the agent reading it executes installation top-to-bottom.

## Build process

A small script at `pipeline-skills-package/bootstrap/build.py` generates
both forms from one source:

1. Walks `pipeline-skills-package/`.
2. Excludes files listed in `bootstrap/distribution-exclude.txt`.
3. Generates `bootstrap/dist/install.md` (the recipe).
4. Generates `bootstrap/dist/pipeline-skills-package.tar.gz` (the tarball).
5. Generates `bootstrap/dist/MANIFEST.txt` listing all included files
   with sha256 sums.

The script is the single source of truth. Manual edits to the recipe
or tarball are forbidden (the build script re-generates them).

## Contract tests in this POC

A new directory `tests/distribution/` houses the contract tests. The
POC's `pytest.ini` already restricts test discovery to `tests/`, so
adding files under `tests/distribution/` is picked up automatically.

The tests:

| Test | Asserts |
|---|---|
| `test_template_parity.py` | Every bundled template byte-matches the POC's working source |
| `test_schema_validity.py` | Every bundled JSON schema is a valid Draft 2020-12 document |
| `test_skill_md_frontmatter.py` | Every SKILL.md has the required frontmatter keys |
| `test_install_dry_run.py` | Install logic against a mock filesystem produces the right file list |
| `test_recipe_idempotent.py` | Applying the recipe twice in a row is a no-op the second time |
| `test_archive_round_trip.py` | Extracting the tarball matches applying the recipe byte-for-byte |
| `test_bundle_contents.py` | Manifest matches the actual files in the tarball / recipe |
| `test_no_secrets_in_bundle.py` | No file in the bundle contains anything matching common secret patterns |

These tests run with the POC's normal pytest invocation. They do not
touch `.agent/`, `.github/workflows/`, or any other POC operational
file.

## Out-of-scope for v1

- Backend abstraction (Bitbucket/Jira adapter). See
  `proposals/agent-api-refactor/` in this POC for the design brief.
- User-level skills (`~/.claude/skills/`).
- Skill registries other than Claude Code's project-level scope.
- Auto-update of installed skills (overwrite logic stays manual).

These belong in v2.

## Cross-document references

- `OVERVIEW.md` — high-level explanation with the flow diagram
- `PLAN-PACKAGE.md` — how to build this package in this POC repo
- `TESTING-IN-POC.md` — partial-testing strategy
- `NEW-REPO-PLAN.md` — what happens after the archive lands in the new repo
- `bootstrap/install.md` — the agent contract for the new repo
- `RESUME.md` — handoff prompt for a future session

````

### TESTING-IN-POC.md

````text
# TESTING-IN-POC — partial-testing strategy

Status: design-stage
Audience: implementers of the contract tests + dispatcher running `PLAN-PACKAGE.md`

> Read `OVERVIEW.md` and `SPEC-PACKAGE.md` first. This file
> describes what CAN and what CANNOT be tested in this POC repo,
> and how to structure the partial-testing work to maximise
> coverage without disrupting the POC.

## The constraint

The POC repo (`poc-github-ai-sandbox`) is preserved as a proof of
concept. Modifying its operational files (`.agent/`,
`.github/workflows/`, `_agent_runs` branch, existing `skills/batch-job/`,
existing `skills/task-dag/`, existing `tests/unit/`, existing
`tests/e2e/`) is forbidden by this work's scope.

This places a hard ceiling on what can be tested here:

- **Yes**: contract tests, schema validation, dry-run install logic, mock-based unit tests, lint/round-trip tests of the bundle.
- **No**: live skill execution against real GitHub from this repo, end-to-end onboarding interview, parallel subagent fanout exercising the actual protocol workflows.

The "no" items are covered in the new `pipeline-ai-sandbox` repo by
the test harness (see `test-harness/SPEC.md` + `NEW-REPO-PLAN.md`).

Accept this. The remainder is meaningful coverage, not theater.

## Test surface (in this POC)

All new tests live under `tests/distribution/`. The POC's
`pytest.ini` has `testpaths = tests`, so `tests/distribution/` is
picked up automatically. The existing 446 POC tests under
`tests/unit/` and `tests/e2e/` remain untouched.

The new test directory:

```
tests/distribution/
  __init__.py
  conftest.py                       # fixtures: POC source paths, bundle paths
  test_template_parity.py           # bundled templates byte-match POC source
  test_schema_validity.py           # bundled JSON schemas are Draft 2020-12 valid
  test_skill_md_frontmatter.py      # every SKILL.md parses + has required keys
  test_install_dry_run.py           # mock filesystem install logic
  test_recipe_idempotent.py         # apply recipe twice = no-op second time
  test_archive_round_trip.py        # tarball extract == recipe apply
  test_bundle_contents.py           # manifest matches actual bundle contents
  test_no_secrets_in_bundle.py      # no secret patterns in any bundled file
  test_distribution_excludes.py     # distribution-exclude.txt is honored
  test_bundle_size.py               # bundle stays under reasonable size cap
  test_workflow_yaml_syntax.py      # bundled GHA YAMLs parse + validate against schema
  test_python_syntax.py             # every bundled .py file imports without syntax errors
  test_onboarding_questions.py      # interview-questions.yml schema + tree completeness
  test_archetype_manifests.py       # test-harness archetypes have valid manifests
  test_scenario_yamls.py            # test-harness scenarios have valid spec
  fixtures/
    fake_repos/                     # synthetic repo trees for dry-run install tests
      blank-repo/
      with-agents-md/
      with-conflicting-skill/
    expected_recipe_excerpts/       # expected snippets in the generated recipe
```

## Per-test detail

### `test_template_parity.py`

```python
# For each skill that bundles templates:
#   For each path in the skill's templates/ tree:
#     The bundled file's bytes must equal the POC source file's bytes.
#
# Skills checked: batch-job, task-dag, orchestrate-issue, onboarding
# (composition-guide bundles nothing; test-harness bundles non-POC files)
```

This is the **most important** test in this directory. If it fails,
the POC source has drifted from the bundled copies and the next
build must re-sync.

### `test_schema_validity.py`

Every bundled `*.schema.json` file:

- Is valid JSON
- Has `$schema` set to `https://json-schema.org/draft/2020-12/schema`
- Validates against the meta-schema (use `jsonschema.Draft202012Validator.check_schema(...)`)

### `test_skill_md_frontmatter.py`

Each `SKILL.md` in the bundle:

- Has a leading `---` YAML frontmatter block
- Frontmatter contains `name`, `description`, `allowed-tools`
- `name` matches the directory name
- `description` is non-empty
- `allowed-tools` is a list of strings

### `test_install_dry_run.py`

For each skill that self-installs, simulate the install against a
synthetic empty repo (under `fixtures/fake_repos/blank-repo/`) using
a mocked filesystem (`tmp_path` fixture). Assert:

- The skill identifies the correct file list to copy.
- After install, every expected file is present at its expected path.
- Re-running the install on the same fixture is a no-op (idempotent).

Also test conflict handling:

- Pre-create one of the target files with different content under `fixtures/fake_repos/with-conflicting-skill/`.
- Run the install in a mode that simulates "user chose: skip".
- Assert the pre-existing file is untouched and the install log records the skip.

### `test_recipe_idempotent.py`

Apply the recipe's instructions against an empty fixture directory.
Then apply them again. Second application:

- Detects every file already exists with matching content.
- Performs zero writes.
- Reports "no changes" cleanly.

This tests that an interrupted bootstrap install can be resumed
safely.

### `test_archive_round_trip.py`

Extract the bundled tarball to a temp directory. Apply the bundled
recipe to a different temp directory. Compare the two trees:

- Same file list.
- Same file contents (bytewise).
- Same permissions where preservable.

### `test_bundle_contents.py`

Read `bootstrap/dist/MANIFEST.txt`. Walk the tarball. Walk the
recipe-extracted tree. Three views must agree:

- Same file paths
- Same sha256 sums

### `test_no_secrets_in_bundle.py`

For every bundled file, scan for patterns matching common secret
shapes (PAT, AWS key, JWT, GitHub token prefixes, password assignments,
private key headers). Use a small allowlist for known-safe matches
(e.g., schema examples).

This is a smoke test, not a security guarantee. It prevents the
most obvious leaks.

### `test_distribution_excludes.py`

Read `bootstrap/distribution-exclude.txt`. Verify every excluded
path/pattern is honored:

- `pipeline-skills-package/runs/` is NOT in the bundle.
- `pipeline-skills-package/bootstrap/dist/` is NOT in the bundle (no recursion).
- `PLAN-PACKAGE.md` and `RESUME.md` are NOT in the bundle.

### `test_bundle_size.py`

The total bundle size should stay under a reasonable cap. Soft cap
~10 MB; hard cap 50 MB. Exceeding the hard cap fails the test.

### `test_workflow_yaml_syntax.py`

Each bundled `.github/workflows/*.yml` template:

- Parses as YAML
- Validates against the GitHub Actions workflow schema
- Has the `${{ vars.AGENT_LOGIN || 'jonathanmanton' }}` fallback (regression test for PR #56 in the POC)

### `test_python_syntax.py`

Every bundled `.py` file:

- Parses with `ast.parse`
- Has no syntax errors

Does **not** import the modules (they may have external dependencies
not satisfied in the test environment); just check syntax.

### `test_onboarding_questions.py`

`interview-questions.yml`:

- Parses as YAML
- Has the 6 expected top-level categories (intent, problems, current-workflow, integration-preferences, sensitive-files, confirmation)
- Each question has `id`, `text`, `type`, and optional `branches`
- No duplicate question IDs

### `test_archetype_manifests.py`

For each archetype under `test-harness/archetypes/`:

- `manifest.json` parses
- Lists every file in the archetype directory
- Notes expected discovery outputs

### `test_scenario_yamls.py`

For each scenario under `test-harness/scenarios/`:

- YAML parses
- References a valid archetype name
- References a valid skill name
- Has at least one phase
- Phase names are unique within a scenario

## Test categories: what they cover vs don't

| Category | Covered here | Deferred to new repo |
|---|---|---|
| Template content correctness | ✅ byte-match against POC source | Live execution of templates |
| Schema validity | ✅ all schemas valid | Live envelope round-trip |
| SKILL.md format | ✅ frontmatter present + valid | Skill-tool routing in Claude Code |
| Install logic — dry run | ✅ mock filesystem | Live install in real repo |
| Bundle round-trip | ✅ recipe vs tarball byte-equal | User actually copying + extracting |
| No secrets | ✅ pattern scan | Threat-model security review |
| Workflow YAML syntax | ✅ parse + schema | Actual GitHub Actions execution |
| Python syntax | ✅ ast.parse | Runtime behaviour |
| Onboarding interview content | ✅ structure | Live interview with user |
| Archetype + scenario YAMLs | ✅ structure | Live scenario execution |

## Running the tests

```bash
# All distribution tests
python -m pytest tests/distribution/ -v --tb=short

# All POC tests (includes distribution)
python -m pytest tests/ -q --tb=short
```

The POC's existing 446 tests must continue to pass. The new
distribution tests add to that baseline. The expected total after
implementation: 446 + ~25-40 new tests = ~470-485 passing.

## Coverage targets

| Module | POC coverage | New target |
|---|---|---|
| Existing `.agent/`, `skills/`, `harness/lib/` | ~93% | Unchanged |
| `pipeline-skills-package/bootstrap/build.py` | N/A | ≥90% |
| `pipeline-skills-package/skills/*/lib/` | N/A | tested transitively via dry-run install + contract tests; full coverage in new repo |

## What NOT to do in this POC

- **Don't** invoke any of the 5 distributable skills against a real
  GitHub repo from this sandbox. That is the new repo's test harness's
  job, not this POC's.
- **Don't** test the full onboarding interview interactively. The
  interview-state-machine unit tests are sufficient here.
- **Don't** install the bundle into this POC repo to test it
  end-to-end. The POC already has a working install of the protocol
  via its `.agent/`; installing the bundled version on top would
  conflict.
- **Don't** modify any of the POC's existing tests.

## Failure handling

If `tests/distribution/` fails:

1. The build (Phase 4 in `PLAN-PACKAGE.md`) aborts.
2. The dispatcher updates `runs/<run_id>/state.json` with the failure.
3. The dispatcher writes a remediation note in the run report.
4. The bundle is **not shipped** until tests pass.

If `tests/unit/` or `tests/e2e/` (existing POC tests) start failing
during this work:

1. **Something in the new code touched the POC.** This is a serious
   violation of scope.
2. Abort immediately and surface to the user.
3. Identify and revert the offending change.

## Integration with `PLAN-PACKAGE.md`

Phase 4 of the build plan runs these tests. The plan's success
criterion is "all tests pass." Until they do, the bundle is not
considered built.

## Integration with `NEW-REPO-PLAN.md`

The full test surface (live execution, real GitHub, interactive
onboarding) is covered in the new repo by the test harness. The
distribution tests run here are the **gate** — only after they
pass does the bundle become shippable to the new repo.

````

### bootstrap/install.md

````text
# install.md — bootstrap contract for the new pipeline-ai-sandbox repo

Status: agent-facing contract.
Audience: the Claude Code agent that's been told "unpack this archive
and follow install.md" in a freshly created `pipeline-ai-sandbox` repo.

> If you are a human reading this: you don't run this yourself.
> Copy either `install.md` (recipe form) or
> `pipeline-skills-package.tar.gz` (tarball form) into your fresh
> `pipeline-ai-sandbox` repo, then tell a Claude Code agent:
> "Read install.md at the repo root and follow it."

## What you (the agent) are doing

You are bootstrapping a brand-new repo called `pipeline-ai-sandbox`.
This repo will become the maintenance project for a set of Claude
Code skills that implement the agent-job dispatch protocol described
in `docs/SPEC-PACKAGE.md`.

There are two forms of this bundle. You can be reading **either**:

- **Recipe form**: this `install.md` file is itself the entire
  bundle. Below in Section 4 you will find every file's content
  inlined in code blocks. Your job is to create each file at the
  path its header specifies.
- **Tarball form**: this `install.md` lives at the top of a tar.gz
  archive. The archive has already been extracted somewhere — verify
  the file tree is present, then proceed.

Look at Section 4. If it contains inlined file contents, you're in
recipe form. If Section 4 is short and points at sibling files, you're
in tarball form (the archive has been extracted and files are sitting
on disk already).

## Section 1 — pre-flight (always run)

Before writing anything, verify:

1. You are in a git repository:
   ```bash
   git rev-parse --is-inside-work-tree
   ```
   Must return `true`. If not, abort and tell the user to `git init`.

2. The repository has the expected name. Check `git remote -v` for an
   origin URL ending in `pipeline-ai-sandbox.git`. If not, **warn the
   user** and ask for explicit confirmation before continuing — this
   bundle is intended for the `pipeline-ai-sandbox` repo only.

3. The working tree is clean OR contains only this archive's files
   plus a `README.md`:
   ```bash
   git status --short
   ```
   If unrelated files are present, ask the user to stash them or
   confirm overwrite.

4. Your GitHub MCP credentials work:
   ```
   Invoke mcp__github__get_me
   ```
   Record the login. You'll need it later for `vars.AGENT_LOGIN`.

5. Verify Python 3.12 is available (or fall back to 3.11 if not):
   ```bash
   python --version
   ```

If any pre-flight step fails, abort and report the failure.

## Section 2 — file tree target

After install completes, the repo should contain:

```
pipeline-ai-sandbox/
  .claude/skills/
    batch-job/                 # full skill package
      SKILL.md
      templates/
        agent/...
        github/...
      lib/
      README.md
    task-dag/                  # same shape
    orchestrate-issue/         # same shape
    onboarding/                # same shape
    composition-guide/         # SKILL.md only
  test-harness/                # development-only test scaffolding
    SKILL.md
    SPEC.md
    archetypes/                # 8 archetypes
    scenarios/                 # 18 scenarios as YAML
    lib/                       # archetype loader, scenario runner, assertions
    runs/.gitkeep
  docs/                        # reference docs (copies from the POC's pipeline-skills-package/)
    OVERVIEW.md
    SPEC-PACKAGE.md
    skills/
      batch-job/SPEC.md
      task-dag/SPEC.md
      orchestrate-issue/SPEC.md
      onboarding/SPEC.md
      composition-guide/SPEC.md
    test-harness/SPEC.md
  bootstrap/
    install.md                 # this file, kept for reference
  NEW-REPO-PLAN.md             # the next step
  TESTING-IN-POC.md            # for reference (what was tested in the POC)
  README.md                    # written by NEW-REPO-PLAN.md Phase 1, not here
```

Note: README.md, AGENTS.md, CLAUDE.md, .github/workflows/, .agent/,
.gitignore, pytest.ini, etc. are **not** part of this bundle. They
get written by the dispatcher running `NEW-REPO-PLAN.md` Phase 1 and
Phase 2.

## Section 3 — install procedure

### If recipe form (Section 4 has inlined file contents)

For each block in Section 4:

1. Read the header `### <path>`.
2. Create any missing parent directories.
3. Write the file's content from the fenced code block immediately
   below the header.
4. After writing every file, run Section 5's verification.

Order does not matter for file writes (no file depends on another's
existence at write time).

### If tarball form (Section 4 points at sibling files)

The tarball has already been extracted. The file tree should already
match Section 2 except for files marked as `# written by ...`. Walk
the tree and verify presence. Run Section 5's verification.

### Conflict handling

If any file you're about to write already exists with content
differing from the bundle:

- **Don't overwrite silently.** Show the user the diff.
- Ask: "Overwrite, skip, or write to `<path>.new`?"
- Honor the user's choice.

For `README.md` specifically: it should not yet exist (Section 2 has
no README in the bundle). If it does, surface to the user.

`.gitignore` is in the same boat — if one exists, surface to user.

## Section 4 — bundled files

> **In recipe form, this section contains every file's content
> inlined.** It is large. Each file's content lives in a fenced code
> block immediately under a `### <path>` header. The content between
> the fences is the verbatim file content.
>
> **In tarball form, this section contains only a manifest listing.**
> The actual files have already been extracted.

[At build time, `bootstrap/build.py` generates this section as one of
two variants. The plan-time scaffolding looks like:]

```
### .claude/skills/batch-job/SKILL.md

<full SKILL.md content for batch-job>

### .claude/skills/batch-job/templates/agent/config.json

<copy of POC's .agent/config.json>

### .claude/skills/batch-job/templates/agent/scripts/common.py

<copy of POC's .agent/scripts/common.py>

[... continues for every file in the bundle ...]
```

## Section 5 — verification (always run after install)

After all files are written (or verified present in tarball form):

1. Walk the file tree against the expected manifest:
   ```bash
   find .claude/skills -type f
   find test-harness -type f
   find docs -type f
   ```
   Compare to the manifest in `MANIFEST.txt` (also bundled).

2. Verify SKILL.md frontmatter for each of the 5 + 1 skills:
   - File starts with `---`
   - Has `name`, `description`, `allowed-tools` keys

3. Verify Python files compile:
   ```bash
   find test-harness -name "*.py" -exec python -m py_compile {} +
   find .claude/skills -name "*.py" -exec python -m py_compile {} +
   ```

4. Verify YAML files parse:
   ```bash
   find test-harness/scenarios -name "*.yml" | xargs -I {} python -c "import yaml; yaml.safe_load(open('{}'))"
   find test-harness/archetypes -name "manifest.json" | xargs -I {} python -c "import json; json.load(open('{}'))"
   ```

5. Print a verification summary to the user:
   ```
   pipeline-ai-sandbox bootstrap install report
   - Files written: <count>
   - Files matched manifest: <count>
   - SKILL.md frontmatter valid: 6/6
   - Python files compiled: <count>
   - YAML files parsed: <count>
   - Status: SUCCESS
   ```

If anything fails verification, surface it and stop. Do not advance
to Section 6.

## Section 6 — next step

After successful verification:

1. Make an initial commit:
   ```bash
   git add .
   git commit -m "bootstrap pipeline-ai-sandbox from pipeline-skills-package bundle"
   ```

2. Push to origin (if origin is configured):
   ```bash
   git push -u origin main
   ```

3. Tell the user:
   ```
   Bootstrap complete. Next step:

   Read NEW-REPO-PLAN.md at the repo root. It describes a
   long-running, parallel, overnight-executable plan to:
     - Scaffold the maintenance project (README, AGENTS.md, CI)
     - Self-install the agent-job protocol in this repo
     - Materialise and validate all test harness archetypes
     - Implement and drive all 18 scenarios against live GitHub
     - Dogfood orchestrate-issue end-to-end
     - Write a retrospective

   When you're ready to start: tell a Claude Code agent
     "Read NEW-REPO-PLAN.md and execute it. UNATTENDED=1 if you
     want overnight, otherwise interactive."
   ```

## Recovery

If install was interrupted mid-recipe:

1. Re-run install.md from the beginning.
2. Section 3's conflict handling will detect already-written files
   and skip them (after confirming content matches).
3. Verification (Section 5) catches any partial writes.

Idempotency is a design goal — running install twice should be
safe.

## What this bundle does NOT do

- Set up `vars.AGENT_LOGIN` on the GitHub repo (`NEW-REPO-PLAN.md`
  Phase 0 handles that).
- Create the `agent-task` label (skills self-create on first install).
- Create the `_agent_runs` orphan branch (skills self-create).
- Configure GitHub Actions secrets (none required — uses default
  `GITHUB_TOKEN`).

## Provenance

This bundle was generated by `pipeline-skills-package/bootstrap/build.py`
in the POC repo `lago-morph/poc-github-ai-sandbox`. The manifest's
`generated_at` timestamp records when. Each bundled file's
`sha256` lives in `MANIFEST.txt`.

If you need to regenerate the bundle (because the POC source changed),
re-run the build script in the POC repo.

````

### .claude/skills/batch-job/README.md

```text
This is the `batch-job` distributable skill. Entry point: SKILL.md. Implementation spec: SPEC.md. Templates self-installed into the target repo on first invocation.

```

### .claude/skills/batch-job/SKILL.md

````text
---
name: batch-job
description: |
  Submit one batch job from an active GitHub issue using the agent-job
  protocol; poll for terminal status; ack the result. Use when an agent
  needs to run a workflow command (tests, build, deploy) inside a GitHub
  Actions runner without holding secrets locally. Self-installs templates
  on first invocation if .agent/config.json is missing.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__github__issue_read
  - mcp__github__add_issue_comment
  - mcp__github__get_file_contents
---

# batch-job

Submit a single batch job from an active GitHub issue, poll until the
workflow runner reports a terminal status, validate the summary, and
acknowledge the result. This skill is the agent-side primitive for
running any command registered in `.agent/config.json :: commands`
against a GitHub Actions runner.

This skill is a pure execution primitive. It does **not** claim issues,
plan subagents, or open pull requests — those belong to `task-dag` and
`orchestrate-issue`.

## When this skill triggers

Invoke this skill when an agent is asked to do any of the following:

- "Run tests on branch X for issue Y."
- "Submit a batch job for command Z."
- "Dispatch one job against issue N."
- "Use the batch-job skill."

It does **not** trigger on general "run tests" requests outside the
GitHub-native protocol. A local `pytest` invocation is not a batch job.

## Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `issue_number` | int | yes | Must be an open issue with `agent-task` label and a valid `agent-meta` block |
| `command` | string | yes | Must appear in `.agent/config.json :: commands` |
| `args` | object | yes | Validated against `.agent/schemas/commands/<command>.schema.json` before submission |
| `branch` | string | yes | Must already exist on origin |
| `commit_sha` | string | yes | Full 40-char SHA; verified by the runner |
| `subagent_id` | string | yes | Identifier of the calling agent |
| `agent_id` | string | yes | The primary's process-level identity; must match the issue's `agent-meta.agent_id` |
| `ack_mode` | enum | no | `"follow_up"` (default for MCP-only callers) or `"inline"` (for REST-credentialed callers) |
| `heartbeat` | callable | no | Invoked once per poll cycle so the caller can refresh `status_ts` on the parent issue |

## Outputs

On success, the skill returns:

```json
{
  "envelope": { "...": "terminal batch-job-request comment body..." },
  "summary": { "...": "inline summary field from envelope..." },
  "summary_json": { "...": "fetched from _agent_runs/runs/<n>/<cid>/summary.json..." },
  "ack_comment_id": 1234567890,
  "log_manifest_path": "runs/42/9876/manifest.json"
}
```

On failure, the skill raises a typed exception that the caller can
match against:

- `RunnerPickupTimeoutError`
- `RunningTimeoutError`
- `BranchShaMismatchError`
- `ParseErrorTerminal`
- `SummarySchemaViolation`

Each exception carries the comment id, `run_status`, `error_kind`, and
any partial summary content available at the time of failure.

## Procedure

The protocol's §9 in the POC `SPEC.md` is the canonical procedure. This
skill packages it into seven steps:

1. **Pre-flight.** Read the issue via the GitHub MCP
   (`mcp__github__issue_read`). Assert the `agent-task` label is
   present, the body parses as a valid `agent-meta` block, and the
   caller's `agent_id` matches the issue's `agent-meta.agent_id`.
2. **Submit.** Post the request envelope as a new comment via
   `mcp__github__add_issue_comment`. Capture the returned comment id.
   Tolerate trailing prose (the Claude Code MCP trailer) when
   re-reading the body — the MCP may HTML-escape body content and
   append a prose trailer; both must be stripped before envelope parse.
3. **Poll.** Read the comment at the schedule defined in
   `.agent/config.json :: comment.poll_*`. On each cycle, invoke the
   optional `heartbeat()` callable so the caller can refresh
   `status_ts` on the parent issue while waiting.
4. **Deadlines.** If `run_status == null` past
   `comment.runner_pickup_timeout_seconds`, open a `runner-failure`
   issue first (so the operator has audit material), then raise
   `RunnerPickupTimeoutError`. If `run_status == "running"` past
   `comment.running_timeout_seconds`, do the same and raise
   `RunningTimeoutError`.
5. **Terminal.** When `run_status` is terminal (`completed`, `error`,
   or `parse_error`), fetch `summary.json` from `_agent_runs` via
   `mcp__github__get_file_contents`. Validate against the command's
   `summary_completed` or `summary_error` schema (defense in depth).
6. **Ack.** Per `ack_mode`:
   - `follow_up` (default): post a `kind: "agent-ack"` comment whose
     `ack_for` matches the request comment id. The original request
     comment is not modified.
   - `inline`: edit the request comment to set `agent_ack: "finished"`
     and `agent_acked_at`. This is the only write the agent makes to
     the comment.
7. **Return** the result dict shown above.

## Self-install logic

A repo is "installed" for this protocol when `.agent/config.json`
exists. The presence of that file is the install marker.

On invocation, this skill checks for each of the following paths in
the target repo and copies the matching template if missing:

| Target path | Bundled template |
|---|---|
| `.agent/config.json` | `templates/agent/config.json` |
| `.agent/scripts/common.py` | `templates/agent/scripts/common.py` |
| `.agent/scripts/rest_client.py` | `templates/agent/scripts/rest_client.py` |
| `.agent/scripts/handler.py` | `templates/agent/scripts/handler.py` |
| `.agent/scripts/requirements.txt` | `templates/agent/scripts/requirements.txt` |
| `.agent/scripts/agent_lib/__init__.py` | `templates/agent/scripts/agent_lib/__init__.py` |
| `.agent/scripts/agent_lib/__main__.py` | `templates/agent/scripts/agent_lib/__main__.py` |
| `.agent/scripts/agent_lib/_common_loader.py` | `templates/agent/scripts/agent_lib/_common_loader.py` |
| `.agent/scripts/agent_lib/cli.py` | `templates/agent/scripts/agent_lib/cli.py` |
| `.agent/scripts/agent_lib/envelope.py` | `templates/agent/scripts/agent_lib/envelope.py` |
| `.agent/scripts/agent_lib/meta.py` | `templates/agent/scripts/agent_lib/meta.py` |
| `.agent/scripts/agent_lib/poll.py` | `templates/agent/scripts/agent_lib/poll.py` |
| `.agent/schemas/comment-envelope.schema.json` | `templates/agent/schemas/comment-envelope.schema.json` |
| `.agent/schemas/comment-ack-envelope.schema.json` | `templates/agent/schemas/comment-ack-envelope.schema.json` |
| `.agent/schemas/log-manifest.schema.json` | `templates/agent/schemas/log-manifest.schema.json` |
| `.agent/schemas/issue-body.schema.json` | `templates/agent/schemas/issue-body.schema.json` |
| `.agent/schemas/commands/bad-summary.schema.json` | `templates/agent/schemas/commands/bad-summary.schema.json` |
| `.agent/schemas/commands/build.schema.json` | `templates/agent/schemas/commands/build.schema.json` |
| `.agent/schemas/commands/chatty.schema.json` | `templates/agent/schemas/commands/chatty.schema.json` |
| `.agent/schemas/commands/echo.schema.json` | `templates/agent/schemas/commands/echo.schema.json` |
| `.agent/schemas/commands/run-tests.schema.json` | `templates/agent/schemas/commands/run-tests.schema.json` |
| `.agent/commands/__init__.py` | `templates/agent/commands/__init__.py` |
| `.agent/commands/bad_summary.py` | `templates/agent/commands/bad_summary.py` |
| `.agent/commands/build.py` | `templates/agent/commands/build.py` |
| `.agent/commands/chatty.py` | `templates/agent/commands/chatty.py` |
| `.agent/commands/echo.py` | `templates/agent/commands/echo.py` |
| `.agent/commands/run_tests.py` | `templates/agent/commands/run_tests.py` |
| `.github/workflows/batch-job-handler.yml` | `templates/github/workflows/batch-job-handler.yml` |
| `agent-task` label on the GitHub repo | Created via `mcp__github__` (no schema; REST POST) |

**Install marker.** `.agent/config.json` is the canonical marker. If
the file is present, the skill considers the protocol installed and
proceeds to step 1 of the procedure. If absent, the skill performs the
copy table above before proceeding.

**Conflict handling.** If a target file exists at a path the skill
wants to install:

1. If content is byte-identical to the bundled template — no-op.
2. If content differs — compute a diff and show it to the user; ask
   "overwrite, skip, or write to `<path>.new` for manual merge?"
3. If the user selects skip, record the skip in
   `.agent/installs/batch-job.log` and proceed.

If `.agent/config.json` exists with a different `protocol_version`, the
skill refuses to overwrite and prompts the user. It does **not**
silently upgrade.

After install, the skill checks for an onboarding dialog file on the
well-known `agent-job-protocol/onboarding` branch. If absent, it emits
the one-time message offering to invoke the `onboarding` skill. Decline
is fine — this skill works standalone.

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Issue not found | MCP returns 404 | Raise `IssueNotFoundError` |
| Issue lacks `agent-task` label | Pre-flight check | Raise `PreflightFailedError`, suggest onboarding |
| Body lacks `agent-meta` | Pre-flight check | Raise `PreflightFailedError` |
| `agent_id` mismatch | Pre-flight check | Raise `AgentIdMismatchError`, do not submit |
| Args fail schema | Pre-submit check | Raise `InvalidArgsError` with schema error |
| Comment post fails | MCP error | Retry with backoff; raise after 3 attempts |
| Runner-pickup timeout | Poll loop | Open `runner-failure` issue; raise `RunnerPickupTimeoutError` |
| Running timeout | Poll loop | Open `runner-failure` issue; raise `RunningTimeoutError` |
| Branch SHA mismatch (terminal) | Runner-written envelope | Raise `BranchShaMismatchError` |
| Parse error (terminal) | Runner-written envelope | Raise `ParseErrorTerminal` |
| Summary schema violation (terminal) | Runner-written envelope | Raise `SummarySchemaViolation` |
| Ack write fails | MCP error | Retry with backoff; emit warning if persistent |
| MCP HTML-escapes comment body | Re-read of own comment | Decode entities before envelope parse; tolerate Claude Code MCP prose trailer |

## Anti-patterns

- **Do not** modify `agent-meta` from inside this skill. That is
  `task-dag`'s job.
- **Do not** open pull requests from this skill. PR creation belongs to
  `orchestrate-issue` or the caller.
- **Do not** retry a `branch_sha_mismatch` with the same branch + SHA —
  surface the error to the caller.
- **Do not** silently upgrade `.agent/config.json` to a newer
  `protocol_version`. Refuse and prompt the user.
- **Do not** call other skills via the Skill tool from inside this
  skill. If composition is needed, the caller (`orchestrate-issue`)
  imports this skill's `lib/` helpers directly.

---
Version: 1.0.0
Protocol-version: 1
Last-synced-from-POC: 2026-05-14
---

````

### docs/skills/batch-job/SPEC.md

````text
# SPEC — batch-job skill

Status: design-stage
Audience: implementers of the skill in the new `pipeline-ai-sandbox` repo

## Purpose

Submit one batch job from an active issue, poll until the workflow
runner reports a terminal status, validate the summary, and
acknowledge the result. The skill is the agent-side primitive for
running any command registered in `.agent/config.json :: commands`
against a GitHub Actions runner.

This skill is a pure execution primitive. It does not claim issues,
plan subagents, or open PRs — those belong to `task-dag` and
`orchestrate-issue`.

## Trigger conditions

The skill matches when an agent is asked to:

- "Run tests on branch X for issue Y"
- "Submit a batch job for command Z"
- "Dispatch one job against issue N"
- "Use the batch-job skill"

It does **not** match general "run tests" requests outside the
GitHub-native protocol (a local pytest is not a batch job).

## Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `issue_number` | int | yes | Must be an open issue with `agent-task` label and a valid `agent-meta` block |
| `command` | string | yes | Must appear in `.agent/config.json :: commands` |
| `args` | object | yes | Validated against `.agent/schemas/commands/<command>.schema.json` before submission |
| `branch` | string | yes | Must already exist on origin |
| `commit_sha` | string | yes | Full 40-char SHA; verified by the runner |
| `subagent_id` | string | yes | Identifier of the calling agent |
| `agent_id` | string | yes | The primary's process-level identity; must match the issue's `agent-meta.agent_id` |
| `ack_mode` | enum | no | `"follow_up"` (default for MCP-only callers) or `"inline"` (for REST-credentialed callers) |
| `heartbeat` | callable | no | Invoked once per poll cycle so the caller can refresh `status_ts` on the parent issue |

## Outputs

On success:

```json
{
  "envelope": { "...": "terminal batch-job-request comment body..." },
  "summary": { "...": "inline summary field from envelope..." },
  "summary_json": { "...": "fetched from _agent_runs/runs/<n>/<cid>/summary.json..." },
  "ack_comment_id": 1234567890,
  "log_manifest_path": "runs/42/9876/manifest.json"
}
```

On failure (timeouts, branch_sha_mismatch, parse_error, summary_schema_violation):

- Raise a typed exception that the caller can match: `RunnerPickupTimeoutError`, `RunningTimeoutError`, `BranchShaMismatchError`, `ParseErrorTerminal`, `SummarySchemaViolation`.
- Each exception carries the comment id, run_status, error_kind, and any partial summary content.

## Procedure

The protocol's §9 in `SPEC.md` (POC root) is the canonical procedure.
This skill packages it as follows:

1. **Pre-flight.** Read the issue via the GitHub MCP. Assert `agent-task` label present, body parses as `agent-meta`, caller's `agent_id` matches.
2. **Submit.** Post the request envelope as a new comment via `mcp__github__add_issue_comment`. Capture the returned comment id. Tolerate trailing prose (Claude Code MCP trailer) when re-reading the body.
3. **Poll.** Read the comment at the schedule defined in `.agent/config.json :: comment.poll_*`. On each cycle, invoke the optional `heartbeat()` callable.
4. **Deadlines.** If `run_status == null` past `runner_pickup_timeout_seconds`, raise `RunnerPickupTimeoutError`. If `run_status == "running"` past `running_timeout_seconds`, raise `RunningTimeoutError`. In either case open a `runner-failure` issue first so the operator has audit material.
5. **Terminal.** When `run_status` is terminal, fetch `summary.json` from `_agent_runs` via `mcp__github__get_file_contents`. Validate against the command's `summary_completed` or `summary_error` schema.
6. **Ack.** Per `ack_mode`:
   - `follow_up` (default): post a `kind: "agent-ack"` comment whose `ack_for` matches the request comment id.
   - `inline`: edit the request comment to set `agent_ack: "finished"` and `agent_acked_at`.
7. **Return** the result dict above.

## Self-install logic

On invocation, the skill checks for the presence of:

| File or path | Action if missing |
|---|---|
| `.agent/config.json` | Copy from `templates/agent/config.json` |
| `.agent/scripts/common.py` | Copy from `templates/agent/scripts/common.py` |
| `.agent/scripts/rest_client.py` | Copy from `templates/agent/scripts/rest_client.py` |
| `.agent/scripts/handler.py` | Copy from `templates/agent/scripts/handler.py` |
| `.agent/scripts/agent_lib/` | Copy directory from `templates/agent/scripts/agent_lib/` |
| `.agent/schemas/comment-envelope.schema.json` | Copy from `templates/agent/schemas/` |
| `.agent/schemas/comment-ack-envelope.schema.json` | Copy from `templates/agent/schemas/` |
| `.agent/schemas/log-manifest.schema.json` | Copy from `templates/agent/schemas/` |
| `.agent/schemas/commands/` (directory) | Copy entire directory |
| `.github/workflows/batch-job-handler.yml` | Copy from `templates/github/workflows/` |
| `agent-task` label on the GitHub repo | Create via `mcp__github__` (no schema match — REST POST) |

If `.agent/config.json` exists with a different `protocol_version`, the
skill refuses to overwrite and prompts the user. It does **not**
silently upgrade.

If a workflow YAML exists at the target path with content different
from the bundled template, the skill shows a diff and asks the user
how to proceed (overwrite, skip, write to `.new` for manual merge).

After install, the skill informs the user that onboarding has not been
run and offers to invoke the `onboarding` skill. Decline is fine —
this skill works standalone.

## Bundled templates

The skill's `templates/` directory contains byte-identical copies of
the POC's working source:

```
templates/
  agent/
    config.json                        # from .agent/config.json
    scripts/
      common.py                        # from .agent/scripts/common.py
      rest_client.py
      handler.py
      requirements.txt
      agent_lib/                       # entire directory
    schemas/
      comment-envelope.schema.json
      comment-ack-envelope.schema.json
      log-manifest.schema.json
      issue-body.schema.json
      commands/                        # entire directory
    commands/                          # entire directory
  github/
    workflows/
      batch-job-handler.yml
```

A contract test in this POC (`tests/distribution/test_template_parity.py`)
asserts byte-equivalence between each `templates/<path>` and the
corresponding POC source file.

## SKILL.md frontmatter

```yaml
---
name: batch-job
description: |
  Submit one batch job from an active GitHub issue using the agent-job
  protocol; poll for terminal status; ack the result. Use when an agent
  needs to run a workflow command (tests, build, deploy) inside a GitHub
  Actions runner without holding secrets locally. Self-installs templates
  on first invocation if .agent/config.json is missing.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__github__issue_read
  - mcp__github__add_issue_comment
  - mcp__github__get_file_contents
---
```

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Issue not found | MCP returns 404 | Raise `IssueNotFoundError` |
| Issue lacks `agent-task` label | Pre-flight check | Raise `PreflightFailedError`, suggest onboarding |
| Body lacks `agent-meta` | Pre-flight check | Raise `PreflightFailedError` |
| `agent_id` mismatch | Pre-flight check | Raise `AgentIdMismatchError`, do not submit |
| Args fail schema | Pre-submit check | Raise `InvalidArgsError` with schema error |
| Comment post fails | MCP error | Retry with backoff; raise after 3 attempts |
| Runner-pickup timeout | Poll loop | Open `runner-failure` issue; raise `RunnerPickupTimeoutError` |
| Running timeout | Poll loop | Same as above |
| Branch SHA mismatch (terminal) | Runner-written envelope | Raise `BranchShaMismatchError` |
| Parse error (terminal) | Runner-written envelope | Raise `ParseErrorTerminal` |
| Summary schema violation (terminal) | Runner-written envelope | Raise `SummarySchemaViolation` |
| Ack write fails | MCP error | Retry with backoff; emit warning if persistent |

## Tests

### In this POC (partial)

- **Contract test** (`tests/distribution/test_template_parity.py`): verify each bundled template byte-matches the POC source.
- **Schema validity** (`tests/distribution/test_schema_validity.py`): each bundled schema is valid JSON Schema draft 2020-12.
- **Dry-run install**: mock filesystem; assert the skill's install logic identifies the right files to copy.
- **SKILL.md frontmatter validity**: parse YAML, assert required keys present.

### In the new repo (full)

- Reuse the POC's existing `tests/unit/test_skill_batch_job.py` as the baseline.
- Add real-GitHub e2e tests driven by the test harness: dispatch the skill against synthetic archetypes; verify ack arrives, summary validates, log manifest is fetchable.
- Cover all `ack_mode` paths (inline + follow_up).
- Cover all failure-mode exceptions against deliberately broken inputs.

## Anti-patterns

- **Do not** modify `agent-meta` from inside this skill. That is `task-dag`'s job.
- **Do not** open PRs from this skill. PR creation belongs to `orchestrate-issue` or the caller.
- **Do not** retry a `branch_sha_mismatch` with the same branch+SHA — surface the error to the caller.
- **Do not** silently upgrade `.agent/config.json` to a newer `protocol_version`.

## Dependencies

- **None** at the skill level. `batch-job` is self-contained and self-installs all required templates.
- At runtime, depends on a GitHub MCP server reachable from the agent.

````

### .claude/skills/batch-job/lib/__init__.py

```text
"""Skill: batch-job — submit and poll one batch job."""

```

### .claude/skills/batch-job/lib/common.py

```text
"""Shared helpers for the ``batch-job`` skill scripts.

Re-exports the central :mod:`.agent.scripts.common` symbols by
ensuring the repo root is on ``sys.path`` first, then loading the
module by file path. This keeps the skill scripts runnable both as
package-style imports and as standalone CLI scripts.
"""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _locate_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".agent" / "config.json").exists():
            return parent
    raise RuntimeError("could not locate repo root (no .agent/config.json found)")


REPO_ROOT = _locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_common():
    name = "agent_protocol_common"
    if name in sys.modules:
        return sys.modules[name]
    path = REPO_ROOT / ".agent" / "scripts" / "common.py"
    spec = spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = module_from_spec(spec)
    sys.modules[name] = mod  # register before exec so dataclass works
    spec.loader.exec_module(mod)
    return mod


_common = _load_common()

GitHubClient = _common.GitHubClient
InMemoryGitHubClient = _common.InMemoryGitHubClient
iso_now = _common.iso_now
load_config = _common.load_config
load_schema = _common.load_schema
validate = _common.validate
parse_agent_meta = _common.parse_agent_meta
render_agent_meta = _common.render_agent_meta
b64_encode = _common.b64_encode
b64_decode = _common.b64_decode
new_uuid = _common.new_uuid
is_terminal_run_status = _common.is_terminal_run_status
has_protocol_markers = _common.has_protocol_markers


def repo_root() -> Path:
    return REPO_ROOT


__all__ = [
    "GitHubClient",
    "InMemoryGitHubClient",
    "iso_now",
    "load_config",
    "load_schema",
    "validate",
    "parse_agent_meta",
    "render_agent_meta",
    "b64_encode",
    "b64_decode",
    "new_uuid",
    "is_terminal_run_status",
    "has_protocol_markers",
    "repo_root",
]

```

### .claude/skills/batch-job/lib/poll.py

````text
"""``batch-job/poll`` skill script.

Polls a comment until ``run_status`` is terminal, validates the
summary against the command schema, fetches ``summary.json`` from the
log branch, and writes the agent_ack into the comment envelope.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

try:
    from .common import (
        GitHubClient,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        render_agent_meta,
        repo_root,
        validate,
    )
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_batchjob_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_batchjob_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    is_terminal_run_status = _mod.is_terminal_run_status
    iso_now = _mod.iso_now
    load_config = _mod.load_config
    load_schema = _mod.load_schema
    render_agent_meta = _mod.render_agent_meta
    repo_root = _mod.repo_root
    validate = _mod.validate


class PollTimeout(RuntimeError):
    """Raised when polling exceeds runner-pickup or running deadlines."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def _interval_for_elapsed(elapsed: float, cfg: dict[str, Any]) -> float:
    base = float(cfg["comment"].get("poll_initial_seconds", 30))
    backoff = cfg["comment"].get("poll_backoff", []) or []
    chosen = base
    for step in backoff:
        if elapsed >= float(step["after_seconds"]):
            chosen = float(step["interval_seconds"])
    return chosen


def _open_runner_failure_issue(
    client: GitHubClient,
    *,
    original_envelope: dict[str, Any],
    comment_id: int,
    timeout_kind: str,
    cfg: Optional[dict[str, Any]] = None,
) -> Optional[dict[str, Any]]:
    """Open a fresh ``runner-failure`` issue (SPEC §9.4 steps 4-5, §14).

    The issue is labelled ``runner-failure`` AND ``agent-task`` so it is
    visible to the same protocol that handles agent tasks. Its body
    carries an ``agent-meta`` block with ``status=null`` so the lifecycle
    can be picked up by an ops agent or human triager.

    Returns the created issue dict, or ``None`` if ``client.create_issue``
    is not available (e.g. a stub client). Failures during issue creation
    are swallowed so they do not mask the underlying timeout.
    """
    create_issue = getattr(client, "create_issue", None)
    if create_issue is None:
        return None

    cfg = cfg or {}
    labels_cfg = cfg.get("labels", {}) or {}
    runner_failure_label = labels_cfg.get("runner_failure", "runner-failure")
    agent_task_label = labels_cfg.get("agent_task", "agent-task")

    issue_number = original_envelope.get("issue_number")
    title = (
        f"runner-failure: {timeout_kind} on issue "
        f"#{issue_number} comment {comment_id}"
    )

    now_iso = iso_now()
    meta = {
        "protocol_version": 1,
        "agent_id": None,
        "session_id": None,
        "status": None,
        "status_ts": None,
        "feature_branch": None,
        "base_branch": None,
        "parent_issue": issue_number,
        "depends_on_prs": [],
        "instructions_path": None,
        "instructions_inline": (
            f"Investigate runner failure ({timeout_kind}) for comment "
            f"{comment_id} on issue #{issue_number}."
        ),
        "created_at": now_iso,
        "runner_failure": {
            "timeout_kind": timeout_kind,
            "comment_id": comment_id,
            "ts": now_iso,
        },
    }

    prose = (
        f"Runner failure: `{timeout_kind}` for comment `{comment_id}`"
        f" on issue #{issue_number} at {now_iso}.\n\n"
        f"Original envelope:\n\n```json\n"
        f"{json.dumps(original_envelope, indent=2)}\n```\n"
    )
    body = render_agent_meta(meta, prose=prose)

    try:
        return create_issue(
            title=title,
            body=body,
            labels=[runner_failure_label, agent_task_label],
        )
    except Exception:  # noqa: BLE001 - best-effort; never mask the timeout
        return None


def poll(
    client: GitHubClient,
    *,
    comment_id: int,
    command: str,
    config: Optional[dict[str, Any]] = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
    ack: bool = True,
    ack_mode: str = "inline",
    issue_number: Optional[int] = None,
    heartbeat: Optional[Callable[[], None]] = None,
) -> dict[str, Any]:
    """Poll the comment until terminal. Returns ``{envelope, summary, summary_json}``.

    Raises :class:`PollTimeout` if the runner-pickup or running deadline
    elapses without progress.

    If ``heartbeat`` is provided, it is invoked once per poll iteration
    AFTER the comment has been read (per SPEC §9.4 step 3) — typical
    callers use this to refresh ``status_ts`` on the parent issue while
    waiting for the runner.

    ``ack_mode`` controls the form of the agent ack (SPEC §4.1):
      - ``"inline"`` (default): edit the request comment in place setting
        ``agent_ack: finished`` and ``agent_acked_at`` (legacy form).
      - ``"follow_up"``: leave the request comment untouched and post a
        NEW ``kind: agent-ack`` comment on the issue with
        ``ack_for: comment_id``. Requires either ``issue_number`` to be
        passed in or for the GitHub client to surface ``issue_number``
        on the comment dict (the in-memory and REST clients both do).
        When the follow-up form is used, the returned dict contains an
        additional ``ack_comment_id`` key (the id of the new comment).
    """
    if ack_mode not in ("inline", "follow_up"):
        raise ValueError(
            f"ack_mode must be 'inline' or 'follow_up', got {ack_mode!r}"
        )
    cfg = config or load_config(repo_root() / ".agent" / "config.json")
    pickup_deadline = float(cfg["comment"].get("runner_pickup_timeout_seconds", 300))
    running_deadline = float(cfg["comment"].get("running_timeout_seconds", 3600))
    total_deadline = float(cfg["comment"].get("poll_total_timeout_seconds", 3600))
    logs_branch = cfg.get("logs", {}).get("branch", "_agent_runs")

    started = now()
    saw_running_at: Optional[float] = None
    # Capture the first envelope we read so we can attach it to a
    # runner-failure issue if a timeout fires.
    first_envelope: Optional[dict[str, Any]] = None
    # Try to fold the parent issue id into envelopes that don't already
    # carry it, so the runner-failure issue can reference it.
    parent_issue_number: Optional[int] = None
    try:
        parent_issue_number = client.get_comment(comment_id).get("issue_number")
    except Exception:  # noqa: BLE001
        parent_issue_number = None

    while True:
        comment = client.get_comment(comment_id)
        body = comment.get("body") or "{}"
        try:
            envelope = json.loads(body)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"comment body is not JSON: {e}") from e

        if first_envelope is None:
            first_envelope = dict(envelope)
            if (
                parent_issue_number is not None
                and "issue_number" not in first_envelope
            ):
                first_envelope["issue_number"] = parent_issue_number

        # SPEC §9.4 step 3: heartbeat each cycle after reading the comment,
        # before deciding whether to break or sleep again.
        if heartbeat is not None:
            heartbeat()

        run_status = envelope.get("run_status")
        if is_terminal_run_status(run_status):
            break

        elapsed = now() - started
        if run_status is None and elapsed > pickup_deadline:
            _open_runner_failure_issue(
                client,
                original_envelope=first_envelope or envelope,
                comment_id=comment_id,
                timeout_kind="runner_pickup_timeout",
                cfg=cfg,
            )
            raise PollTimeout(
                "runner_pickup_timeout",
                f"runner did not pick up within {pickup_deadline}s",
            )
        if run_status == "running":
            if saw_running_at is None:
                saw_running_at = now()
            if (now() - saw_running_at) > running_deadline:
                _open_runner_failure_issue(
                    client,
                    original_envelope=first_envelope or envelope,
                    comment_id=comment_id,
                    timeout_kind="running_timeout",
                    cfg=cfg,
                )
                raise PollTimeout(
                    "running_timeout",
                    f"workflow ran longer than {running_deadline}s",
                )
        if elapsed > total_deadline:
            raise PollTimeout(
                "poll_total_timeout",
                f"polling exceeded total deadline {total_deadline}s",
            )

        sleep(_interval_for_elapsed(elapsed, cfg))

    summary = envelope.get("summary") or {}
    summary_json: Optional[dict[str, Any]] = None
    log_path = envelope.get("log_manifest_path")
    if log_path:
        # summary.json sits next to manifest.json
        summary_path = log_path.rsplit("/", 1)[0] + "/summary.json"
        raw = client.get_file_contents(summary_path, logs_branch)
        if raw is not None:
            try:
                summary_json = json.loads(raw)
            except json.JSONDecodeError:
                summary_json = None

    # Validate summary against the schema (defense in depth).
    try:
        schema = load_schema(f"commands/{command}.schema.json", repo_root())
        if envelope.get("run_status") == "completed":
            sub = schema.get("properties", {}).get("summary_completed")
        else:
            sub = schema.get("properties", {}).get("summary_error")
        if sub is not None:
            validate(summary, sub)
    except FileNotFoundError:
        pass

    # Ack ----------------------------------------------------------------
    ack_comment_id: Optional[int] = None
    if ack:
        if ack_mode == "inline":
            if envelope.get("agent_ack") != "finished":
                envelope["agent_ack"] = "finished"
                envelope["agent_acked_at"] = iso_now()
                client.update_comment(
                    comment_id, json.dumps(envelope, indent=2)
                )
        else:  # ack_mode == "follow_up"
            target_issue = issue_number
            if target_issue is None:
                # Fall back to the issue_number we read from the comment
                # itself (parent_issue_number is captured at the top of
                # poll() above).
                target_issue = parent_issue_number
            if target_issue is None:
                raise ValueError(
                    "ack_mode='follow_up' requires issue_number "
                    "(client.get_comment did not surface it either)"
                )
            ack_env = {
                "protocol_version": 1,
                "kind": "agent-ack",
                "ack_for": comment_id,
                "agent_acked_at": iso_now(),
            }
            new_comment = client.add_comment(
                target_issue, json.dumps(ack_env, indent=2)
            )
            ack_comment_id = (
                new_comment.get("id") if isinstance(new_comment, dict) else None
            )

    result: dict[str, Any] = {
        "envelope": envelope,
        "summary": summary,
        "summary_json": summary_json,
    }
    if ack_mode == "follow_up":
        result["ack_comment_id"] = ack_comment_id
    return result

````

### .claude/skills/batch-job/lib/submit.py

```text
"""``batch-job/submit`` skill script.

Constructs a ``batch-job-request`` envelope and posts it as a comment
on the issue. Pre-flight: validates that the issue carries the
agent-task label and that args conform to the command schema.

Note: the issue is **not** required to be locked at submit time. The
original draft of the protocol locked agent issues at creation, but
GitHub refuses comments from ``GITHUB_TOKEN`` on locked issues, which
breaks the batch-job-handler's terminal envelope writes. Locking is
therefore deferred to ``close_on_merge`` (post-merge); the
batch-job-handler's ``if:`` filter (label + author) is what makes
foreign comments inert.

``agent_login`` resolution order: explicit ``agent_login`` keyword
argument → ``AGENT_LOGIN`` environment variable → raise. There is no
fallback to a static config key (removed in session 3): agent harnesses
are expected to discover their own login via ``mcp__github__get_me``
and pass it explicitly, while CI invocations populate ``AGENT_LOGIN``
from a repo-level ``vars.AGENT_LOGIN``.

Importable: :func:`submit` (programmatic) or run as
``python -m skills.batch-job.submit`` (not wired up here for the POC).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

try:
    from .common import (
        GitHubClient,
        iso_now,
        load_config,
        load_schema,
        parse_agent_meta,
        repo_root,
        validate,
    )
except ImportError:
    # Standalone (not imported as a package): load the sibling
    # ``common.py`` by file path to avoid collisions with any other
    # ``common`` already in ``sys.modules``.
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_batchjob_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_batchjob_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    iso_now = _mod.iso_now
    load_config = _mod.load_config
    load_schema = _mod.load_schema
    parse_agent_meta = _mod.parse_agent_meta
    repo_root = _mod.repo_root
    validate = _mod.validate


class PreflightError(RuntimeError):
    """Raised when the issue is not in a state that accepts jobs."""


def preflight(
    client: GitHubClient,
    issue_number: int,
    *,
    agent_id: Optional[str] = None,
    agent_login: Optional[str] = None,
    agent_task_label: str = "agent-task",
) -> dict[str, Any]:
    issue = client.get_issue(issue_number)
    # Intentionally NOT checking ``issue.get("locked")`` here: locking
    # is deferred until post-merge (see module docstring).
    labels = {l["name"] for l in (issue.get("labels") or [])}
    if agent_task_label not in labels:
        raise PreflightError(
            f"issue #{issue_number} missing label {agent_task_label}"
        )
    meta = parse_agent_meta(issue.get("body"))
    if meta is None:
        raise PreflightError(f"issue #{issue_number} body has no agent-meta")
    if agent_id is not None and meta.get("agent_id") != agent_id:
        raise PreflightError(
            f"agent_id mismatch: meta has {meta.get('agent_id')!r}, "
            f"caller has {agent_id!r}"
        )
    if agent_login is not None:
        creator = (issue.get("user") or {}).get("login")
        if creator != agent_login:
            raise PreflightError(
                f"issue creator {creator!r} != agent_login {agent_login!r}"
            )
    return meta


def submit(
    client: GitHubClient,
    *,
    issue_number: int,
    command: str,
    args: dict[str, Any],
    branch: str,
    commit_sha: str,
    subagent_id: str,
    agent_id: Optional[str] = None,
    agent_login: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build the envelope and post it. Returns the new comment dict.

    ``agent_login`` is required. Resolution order: explicit argument →
    ``AGENT_LOGIN`` environment variable → raise. There is no fallback
    to ``cfg["agent_login"]`` — that key was removed from the static
    config in session 3.
    """
    cfg = config or load_config(repo_root() / ".agent" / "config.json")
    if agent_login is None:
        agent_login = os.environ.get("AGENT_LOGIN") or None
    if not agent_login:
        raise RuntimeError(
            "agent_login is required: pass it explicitly or set the "
            "AGENT_LOGIN environment variable (typically populated by "
            "the workflow from vars.AGENT_LOGIN, or by the agent "
            "harness from mcp__github__get_me at session start)"
        )
    agent_task_label = cfg.get("labels", {}).get("agent_task", "agent-task")

    if command not in cfg.get("commands", []):
        raise ValueError(f"unknown command: {command}")

    # Pre-flight.
    preflight(
        client,
        issue_number,
        agent_id=agent_id,
        agent_login=agent_login,
        agent_task_label=agent_task_label,
    )

    # Validate args against the command's schema.
    schema = load_schema(f"commands/{command}.schema.json", repo_root())
    args_schema = schema.get("properties", {}).get("args")
    if args_schema is not None:
        validate(args, args_schema)

    envelope = {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "command": command,
        "args": args,
        "branch": branch,
        "commit_sha": commit_sha,
        "subagent_id": subagent_id,
        "submitted_at": iso_now(),
        "run_status": None,
        "agent_ack": None,
    }

    body = json.dumps(envelope, indent=2)
    comment = client.add_comment(issue_number, body)
    return comment

```

### .claude/skills/batch-job/templates/agent/commands/__init__.py

```text
"""Command handler modules. Each command is a sibling module exposing
``run(args, log_writer, workspace) -> dict`` returning the summary."""

```

### .claude/skills/batch-job/templates/agent/commands/bad_summary.py

```text
"""``bad-summary`` test command — intentionally returns invalid summary.

Used by harness scenario 07 (``07_summary_schema_violation.md``) to
exercise the handler's defense-in-depth ``summary_schema_violation``
path. The schema demands ``required_field`` in the completed summary,
but this handler returns ``{}`` so the validator must reject it.
"""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": "bad-summary about to return invalid summary",
    })
    # Intentionally missing the schema-required ``required_field``.
    return {}

```

### .claude/skills/batch-job/templates/agent/commands/build.py

```text
"""``build`` command stub. Pretends to build a target."""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    target = args.get("target", "default")
    release = bool(args.get("release", False))

    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "setup",
        "data": {"msg": "build started", "target": target, "release": release},
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": f"compiling {target}{' (release)' if release else ''}",
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "teardown",
        "data": {"msg": "build complete"},
    })

    artifact = f"build/out/{target}{'-release' if release else ''}.bin"
    return {
        "artifact_path": artifact,
        "size_bytes": 1024 * (4096 if release else 2048),
        "duration_seconds": 3.5 if release else 1.25,
    }

```

### .claude/skills/batch-job/templates/agent/commands/chatty.py

```text
"""``chatty`` test command — emits many log records to force chunk rotation.

Used by harness scenario 12 (``12_huge_log.md``). Args:

- ``lines`` (int, default 500): number of log records to emit.
- ``max_chunk_bytes_compressed`` (int, default 8192): rotation threshold
  applied to the LogWriter for this invocation only. The production
  default (524 288 bytes) remains untouched for non-test commands.

Rationale: live execution showed that triggering rotation at the full
production threshold required ~20 000 lines, which is timing-sensitive
and slow on real GitHub Actions runners. Lowering the per-invocation
threshold for the test command makes rotation fire reliably with a
modest line count, while production defaults are preserved because
chatty calls :py:meth:`LogWriter.set_max_chunk_bytes` itself rather
than mutating any shared config.

Each emitted record carries a high-entropy (per-line unique) payload so
that gzip cannot dedupe the stream down below the rotation threshold —
without this, 500 highly-repetitive lines compressed to <8 KB and never
rotated.
"""

from __future__ import annotations

import hashlib
from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ))
    from common import iso_now  # type: ignore[import-not-found]


def _entropy_payload(i: int, length: int = 192) -> str:
    """Build a high-entropy, per-line-unique string of ~``length`` chars.

    gzip compresses repeated text aggressively, so a constant pad would
    let 500 lines compress well below an 8 KiB rotation threshold. We
    derive a chain of SHA-256 hex digests seeded by ``i`` and concatenate
    them — this is effectively incompressible and grows linearly with
    line count.
    """
    out_parts: list[str] = []
    seed = f"chatty-line-{i:08d}".encode("utf-8")
    h = hashlib.sha256(seed).hexdigest()  # 64 hex chars
    out_parts.append(h)
    while sum(len(p) for p in out_parts) < length:
        h = hashlib.sha256(h.encode("utf-8")).hexdigest()
        out_parts.append(h)
    return "-".join(out_parts)[:length]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    # Override the rotation threshold up-front so every record we emit
    # is governed by the test-friendly size.
    max_chunk = int(args.get("max_chunk_bytes_compressed", 8192))
    log_writer.set_max_chunk_bytes(max_chunk)

    n = int(args.get("lines", 500))
    if n < 0:
        n = 0
    for i in range(n):
        log_writer.write({
            "ts": iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": f"line {i:08d} {_entropy_payload(i)}",
        })
    return {
        "lines_emitted": n,
        "message": f"chatty emitted {n} lines",
    }

```

### .claude/skills/batch-job/templates/agent/commands/echo.py

```text
"""``echo`` command: trivial demonstration handler.

Echoes its args back inside the summary. Useful for end-to-end POC
testing without depending on any synthetic test data.
"""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    message = str(args.get("message", "")) or "hello"
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": message,
    })
    return {
        "echoed_args": dict(args),
        "message": message,
    }

```

### .claude/skills/batch-job/templates/agent/commands/run_tests.py

```text
"""``run-tests`` command stub.

Pretends to run a suite and returns a fake-but-realistic summary that
conforms to ``commands/run-tests.schema.json``'s ``summary_completed``
shape. Streams a few records through ``log_writer`` so the manifest
contains real chunks.
"""

from __future__ import annotations

import random
from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    """Execute the (faked) test command.

    ``args`` is already validated against the command schema by the
    handler, so ``suite`` is guaranteed present.
    """
    suite = args["suite"]
    shard = args.get("shard")
    filter_ = args.get("filter")

    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "setup",
        "data": {
            "msg": "starting run-tests",
            "suite": suite,
            "shard": shard,
            "filter": filter_,
        },
    })

    # Deterministic-ish fake numbers based on suite size.
    base_counts = {"unit": 120, "integration": 40, "e2e": 12}
    total = base_counts.get(suite, 25)
    rng = random.Random(f"{suite}:{shard}:{filter_}")

    failed = rng.randint(0, max(1, total // 25))
    skipped = rng.randint(0, max(1, total // 30))
    passed = total - failed - skipped
    duration = round(rng.uniform(2.0, 12.0) + total * 0.1, 2)

    failed_tests: list[dict[str, str]] = []
    for i in range(failed):
        log_writer.write({
            "ts": iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": f"FAIL test_{suite}_{i}",
        })
        failed_tests.append({
            "name": f"test_{suite}_{i}",
            "message": "AssertionError: synthetic failure",
        })

    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": f"ran {total} {suite} tests in {duration}s",
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "teardown",
        "data": {"msg": "run-tests complete"},
    })

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_seconds": duration,
        "failed_tests": failed_tests,
    }

```

### .claude/skills/batch-job/templates/agent/config.json

```text
{
  "protocol_version": 1,
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
    "subagent_pattern": "<feature_branch>--sub-<subagent_id>"
  },
  "commands": ["run-tests", "build", "echo", "bad-summary", "chatty"]
}

```

### .claude/skills/batch-job/templates/agent/schemas/commands/bad-summary.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/bad-summary.schema.json",
  "title": "bad-summary",
  "description": "Test command whose handler intentionally returns an invalid summary so the handler's summary_schema_violation path is exercised.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "additionalProperties": true
    },
    "summary_completed": {
      "type": "object",
      "required": ["required_field"],
      "properties": {
        "required_field": { "type": "string" }
      },
      "additionalProperties": true
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/batch-job/templates/agent/schemas/commands/build.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/build.schema.json",
  "title": "build",
  "description": "Schema for the build command. Stub for the POC.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "target": { "type": "string", "minLength": 1 },
        "release": { "type": "boolean" }
      },
      "additionalProperties": false
    },
    "summary_completed": {
      "type": "object",
      "required": ["artifact_path", "size_bytes", "duration_seconds"],
      "properties": {
        "artifact_path": { "type": "string" },
        "size_bytes": { "type": "integer", "minimum": 0 },
        "duration_seconds": { "type": "number", "minimum": 0 }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/batch-job/templates/agent/schemas/commands/chatty.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/chatty.schema.json",
  "title": "chatty",
  "description": "Test command that emits many log records to force chunk rotation.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "lines": { "type": "integer", "minimum": 0 },
        "max_chunk_bytes_compressed": { "type": "integer", "minimum": 1 }
      },
      "additionalProperties": false
    },
    "summary_completed": {
      "type": "object",
      "required": ["lines_emitted", "message"],
      "properties": {
        "lines_emitted": { "type": "integer", "minimum": 0 },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/batch-job/templates/agent/schemas/commands/echo.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/echo.schema.json",
  "title": "echo",
  "description": "Schema for the echo command: trivial demonstration command that returns its args.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "message": { "type": "string" }
      },
      "additionalProperties": true
    },
    "summary_completed": {
      "type": "object",
      "required": ["echoed_args", "message"],
      "properties": {
        "echoed_args": { "type": "object" },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/batch-job/templates/agent/schemas/commands/run-tests.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/run-tests.schema.json",
  "title": "run-tests",
  "description": "Schema for the run-tests command: validates args and the produced summary.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
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
        "duration_seconds": { "type": "number", "minimum": 0 },
        "failed_tests": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name"],
            "properties": {
              "name": { "type": "string" },
              "message": { "type": "string" }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/batch-job/templates/agent/schemas/comment-ack-envelope.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/comment-ack-envelope.schema.json",
  "title": "comment envelope (agent-ack)",
  "description": "Follow-up comment that acknowledges a batch-job-request without editing it in place.",
  "type": "object",
  "required": ["protocol_version", "kind", "ack_for", "agent_acked_at"],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "kind": { "type": "string", "const": "agent-ack" },
    "ack_for": { "type": "integer", "minimum": 1 },
    "agent_acked_at": { "type": "string", "format": "date-time" },
    "agent_id": { "type": ["string", "null"] },
    "session_id": { "type": ["string", "null"] },
    "note": { "type": ["string", "null"] }
  },
  "additionalProperties": true
}

```

### .claude/skills/batch-job/templates/agent/schemas/comment-envelope.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/comment-envelope.schema.json",
  "title": "comment envelope (batch-job-request)",
  "description": "Lifecycle-aware schema for comment-body envelopes. Supports request, post-run, and parse_error shapes.",
  "type": "object",
  "required": ["protocol_version", "kind"],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "kind": { "type": "string", "const": "batch-job-request" },
    "command": { "type": "string", "minLength": 1 },
    "args": { "type": "object" },
    "branch": { "type": "string", "minLength": 1 },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{40}$"
    },
    "subagent_id": { "type": "string", "minLength": 1 },
    "submitted_at": { "type": "string", "format": "date-time" },

    "run_status": {
      "type": ["string", "null"],
      "enum": [null, "running", "completed", "error", "parse_error"]
    },
    "run_started_at": { "type": ["string", "null"], "format": "date-time" },
    "run_finished_at": { "type": ["string", "null"], "format": "date-time" },
    "workflow_run_id": { "type": ["integer", "null"] },
    "checked_out_sha": {
      "type": ["string", "null"],
      "pattern": "^[0-9a-f]{40}$"
    },
    "summary": { "type": ["object", "null"] },
    "log_manifest_branch": { "type": ["string", "null"] },
    "log_manifest_path": { "type": ["string", "null"] },

    "agent_ack": {
      "type": ["string", "null"],
      "enum": [null, "finished"]
    },
    "agent_acked_at": { "type": ["string", "null"], "format": "date-time" },

    "error_kind": { "type": ["string", "null"] },
    "error_detail": { "type": ["string", "null"] },
    "original_body_b64": { "type": ["string", "null"] }
  },
  "allOf": [
    {
      "description": "If run_status is null/running/completed/error (i.e. a real request was submitted), the request fields must be present.",
      "if": {
        "properties": {
          "run_status": { "enum": [null, "running", "completed", "error"] }
        }
      },
      "then": {
        "required": ["command", "args", "branch", "commit_sha", "subagent_id", "submitted_at"]
      }
    },
    {
      "description": "If run_status is 'completed', summary and log manifest fields are required.",
      "if": {
        "properties": { "run_status": { "const": "completed" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id",
          "checked_out_sha",
          "summary",
          "log_manifest_branch",
          "log_manifest_path"
        ]
      }
    },
    {
      "description": "If run_status is 'error', error_kind and run timing must be present.",
      "if": {
        "properties": { "run_status": { "const": "error" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id",
          "error_kind"
        ]
      }
    },
    {
      "description": "If run_status is 'parse_error', original_body_b64 and error_kind must be present.",
      "if": {
        "properties": { "run_status": { "const": "parse_error" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "error_kind",
          "original_body_b64",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id"
        ]
      }
    }
  ],
  "additionalProperties": true
}

```

### .claude/skills/batch-job/templates/agent/schemas/issue-body.schema.json

````text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/issue-body.schema.json",
  "title": "agent-meta block (issue body)",
  "description": "Schema for the JSON object inside an issue body's fenced ```agent-meta block.",
  "type": "object",
  "required": [
    "protocol_version",
    "agent_id",
    "session_id",
    "status",
    "status_ts",
    "feature_branch",
    "base_branch",
    "parent_issue",
    "depends_on_prs",
    "instructions_path",
    "instructions_inline",
    "created_at"
  ],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "agent_id": { "type": ["string", "null"] },
    "session_id": { "type": ["string", "null"] },
    "status": {
      "type": ["string", "null"],
      "enum": [null, "working", "abandoned", "finished"]
    },
    "status_ts": {
      "type": ["string", "null"],
      "format": "date-time"
    },
    "feature_branch": { "type": "string", "minLength": 1 },
    "base_branch": { "type": "string", "minLength": 1 },
    "parent_issue": { "type": ["integer", "null"], "minimum": 1 },
    "depends_on_prs": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 }
    },
    "instructions_path": { "type": ["string", "null"] },
    "instructions_inline": { "type": ["string", "null"] },
    "created_at": { "type": "string", "format": "date-time" }
  },
  "anyOf": [
    { "properties": { "instructions_inline": { "type": "string", "minLength": 1 } }, "required": ["instructions_inline"] },
    { "properties": { "instructions_path": { "type": "string", "minLength": 1 } }, "required": ["instructions_path"] }
  ],
  "additionalProperties": true
}

````

### .claude/skills/batch-job/templates/agent/schemas/log-manifest.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/log-manifest.schema.json",
  "title": "log manifest",
  "description": "Schema for runs/<issue>/<comment>/manifest.json on the _agent_runs orphan branch.",
  "type": "object",
  "required": [
    "protocol_version",
    "schema",
    "command",
    "args",
    "checked_out_sha",
    "started_at",
    "finished_at",
    "exit_code",
    "chunks"
  ],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "schema": {
      "type": "object",
      "required": ["chunk_format", "fields"],
      "properties": {
        "chunk_format": { "type": "string", "const": "jsonl-gz" },
        "fields": { "type": "object" }
      }
    },
    "command": { "type": "string", "minLength": 1 },
    "args": { "type": "object" },
    "checked_out_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,64}$"
    },
    "started_at": { "type": "string", "format": "date-time" },
    "finished_at": { "type": "string", "format": "date-time" },
    "exit_code": { "type": "integer" },
    "chunks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "bytes", "lines"],
        "properties": {
          "path": { "type": "string", "minLength": 1 },
          "bytes": { "type": "integer", "minimum": 0 },
          "lines": { "type": "integer", "minimum": 0 }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": true
}

```

### .claude/skills/batch-job/templates/agent/scripts/agent_lib/__init__.py

```text
"""Pure-Python helpers for the agent-mode harness.

This package is the agent-side counterpart to the workflow-side handler.

The dispatcher AI cannot pass MCP tools as Python callables, so the
"skill" lifecycle in agent mode is split into:

- Pure helpers (here): envelope construction, agent-meta marshalling,
  terminal-status parsing, summary path derivation, schema validation.
- Markdown playbooks (under ``harness/scenarios/``): tell the agent
  which MCP calls to make and in what order.

Pure helpers run inside the sandbox — invoked via ``python -m agent_lib
<sub> ...``; the printed JSON is consumed by the agent's tool-use
stream.

This module deliberately performs **no** I/O against GitHub.
"""

from __future__ import annotations

from .envelope import (
    EnvelopeArgsInvalid,
    make_ack_envelope,
    make_request_envelope,
)
from .meta import (
    abandon_meta,
    claim_meta,
    finish_meta,
    heartbeat_meta,
    make_initial_meta,
    parse_body,
    render_body,
    replace_meta_in_body,
)
from .poll import (
    is_request_acked,
    is_terminal,
    manifest_path_for,
    parse_ack_comment,
    parse_terminal_status,
    summary_path_for,
)


__all__ = [
    "EnvelopeArgsInvalid",
    "abandon_meta",
    "claim_meta",
    "finish_meta",
    "heartbeat_meta",
    "is_request_acked",
    "is_terminal",
    "make_ack_envelope",
    "make_initial_meta",
    "make_request_envelope",
    "manifest_path_for",
    "parse_ack_comment",
    "parse_body",
    "parse_terminal_status",
    "render_body",
    "replace_meta_in_body",
    "summary_path_for",
]

```

### .claude/skills/batch-job/templates/agent/scripts/agent_lib/__main__.py

```text
"""Make ``python -m agent_lib`` invoke the CLI."""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())

```

### .claude/skills/batch-job/templates/agent/scripts/agent_lib/_common_loader.py

```text
"""Locate and load the central ``common.py`` module by file path.

The agent-mode helpers run from many entry points (CLI, tests,
imported by subagents). We deliberately keep the import shape as
robust as ``skills/batch-job/common.py`` so a stray ``common`` already
in ``sys.modules`` does not break us.
"""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def locate_repo_root(start: Path | None = None) -> Path:
    """Walk upwards from ``start`` looking for ``.agent/config.json``."""
    here = (start or Path(__file__)).resolve()
    candidates = [here] if here.is_dir() else [here.parent, *here.parents]
    for parent in candidates:
        if (parent / ".agent" / "config.json").exists():
            return parent
    raise RuntimeError("could not locate repo root (no .agent/config.json found)")


REPO_ROOT = locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_common() -> ModuleType:
    """Return the central agent-protocol ``common`` module, loaded once."""
    name = "agent_protocol_common"
    if name in sys.modules:
        return sys.modules[name]
    path = REPO_ROOT / ".agent" / "scripts" / "common.py"
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - import path
        raise RuntimeError(f"could not load common module from {path}")
    mod = module_from_spec(spec)
    sys.modules[name] = mod  # register before exec so dataclasses work
    spec.loader.exec_module(mod)
    return mod

```

### .claude/skills/batch-job/templates/agent/scripts/agent_lib/cli.py

```text
"""Thin CLI wrapper around the pure helpers.

Designed to be invoked by the dispatcher agent via ``Bash`` calls of
the form::

    python -m agent_lib <subcommand> <positional args> [--option ...]

All subcommands print JSON to stdout (the parsed structure or the
markdown body) so the agent can pipe the result into a subsequent MCP
call. Validation failures exit with a non-zero status; the error
message goes to stderr as a single ``{"error": "..."}`` JSON object.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional

from . import (
    EnvelopeArgsInvalid,
    abandon_meta,
    claim_meta,
    finish_meta,
    heartbeat_meta,
    make_ack_envelope,
    make_initial_meta,
    make_request_envelope,
    parse_body,
    parse_terminal_status,
    render_body,
    summary_path_for,
)
from ._common_loader import REPO_ROOT, load_common
from .meta import replace_meta_in_body


_common = load_common()


def _die(msg: str, code: int = 1) -> None:
    sys.stderr.write(json.dumps({"error": msg}) + "\n")
    raise SystemExit(code)


def _loads(s: str, *, name: str) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError) as e:
        _die(f"{name}: invalid JSON: {e}")


def _print(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------

def cmd_make_request(ns: argparse.Namespace) -> int:
    args = _loads(ns.args_json, name="args")
    if not isinstance(args, dict):
        _die("args must be a JSON object")
    try:
        env = make_request_envelope(
            ns.command,
            args,
            ns.branch,
            ns.sha,
            ns.subagent_id,
            validate_args=not ns.no_validate,
        )
    except EnvelopeArgsInvalid as e:
        _die(str(e))
    except (TypeError, ValueError) as e:
        _die(str(e))
    _print(env)
    return 0


def cmd_make_ack(ns: argparse.Namespace) -> int:
    try:
        env = make_ack_envelope(
            ns.ack_for,
            agent_id=ns.agent_id,
            session_id=ns.session_id,
            note=ns.note,
        )
    except ValueError as e:
        _die(str(e))
    _print(env)
    return 0


def cmd_make_initial_meta(ns: argparse.Namespace) -> int:
    payload = _loads(ns.json_payload, name="payload")
    if not isinstance(payload, dict):
        _die("payload must be a JSON object")
    try:
        meta = make_initial_meta(**payload)
    except TypeError as e:
        _die(f"unsupported arguments: {e}")
    except ValueError as e:
        _die(str(e))
    body = render_body(meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_claim_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    try:
        new_meta = claim_meta(meta, ns.agent_id, ns.session_id)
    except ValueError as e:
        _die(str(e))
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_heartbeat_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = heartbeat_meta(meta)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_finish_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = finish_meta(meta)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_abandon_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = abandon_meta(meta, ns.reason)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_parse_comment(ns: argparse.Namespace) -> int:
    run_status, parsed = parse_terminal_status(ns.body)
    summary_path: Optional[str] = None
    log_manifest_path: Optional[str] = None
    if run_status is not None:
        log_manifest_path = parsed.get("log_manifest_path")
        if log_manifest_path:
            base = log_manifest_path.rsplit("/", 1)[0]
            summary_path = base + "/summary.json"
    out = {
        "run_status": run_status,
        "summary": parsed.get("summary"),
        "log_manifest_path": log_manifest_path,
        "summary_path": summary_path,
        "envelope": parsed,
    }
    _print(out)
    return 0


def cmd_parse_meta(ns: argparse.Namespace) -> int:
    meta = parse_body(ns.body)
    if meta is None:
        _print(None)
    else:
        _print(meta)
    return 0


def cmd_summary_path(ns: argparse.Namespace) -> int:
    try:
        path = summary_path_for(ns.issue, ns.comment)
    except ValueError as e:
        _die(str(e))
    _print({"summary_path": path})
    return 0


def cmd_replace_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    body = replace_meta_in_body(ns.body, meta)
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_validate_summary(ns: argparse.Namespace) -> int:
    summary = _loads(ns.summary_json, name="summary")
    try:
        schema = _common.load_schema(
            f"commands/{ns.command}.schema.json", REPO_ROOT
        )
    except FileNotFoundError as e:
        _die(f"no schema for command {ns.command}: {e}")
    key = "summary_completed" if ns.status == "completed" else "summary_error"
    sub = schema.get("properties", {}).get(key)
    if sub is None:
        _die(f"schema has no {key} sub-schema for {ns.command}")
    try:
        _common.validate(summary, sub)
    except Exception as e:  # noqa: BLE001
        _die(f"invalid: {e}")
    _print({"valid": True, "command": ns.command, "status": ns.status})
    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent_lib")
    sub = p.add_subparsers(dest="cmd", required=True)

    # make-request
    s = sub.add_parser("make-request", help="build a batch-job-request envelope")
    s.add_argument("args_json", help="JSON object: command args")
    s.add_argument("--command", required=True)
    s.add_argument("--branch", required=True)
    s.add_argument("--sha", required=True, help="commit_sha (40 hex chars)")
    s.add_argument("--subagent-id", required=True)
    s.add_argument("--no-validate", action="store_true",
                   help="skip args schema validation")
    s.set_defaults(func=cmd_make_request)

    # make-ack
    s = sub.add_parser(
        "make-ack",
        help="build a follow-up agent-ack comment envelope",
    )
    s.add_argument(
        "--ack-for", type=int, dest="ack_for", required=True,
        help="comment_id of the batch-job-request to ack",
    )
    s.add_argument("--agent-id", dest="agent_id", default=None)
    s.add_argument("--session-id", dest="session_id", default=None)
    s.add_argument("--note", default=None)
    s.set_defaults(func=cmd_make_ack)

    # make-initial-meta
    s = sub.add_parser("make-initial-meta",
                       help="build initial agent-meta block + body markdown")
    s.add_argument("json_payload",
                   help="JSON object of kwargs for make_initial_meta")
    s.add_argument("--prose", default="", help="prose to put before block")
    s.set_defaults(func=cmd_make_initial_meta)

    # claim-meta
    s = sub.add_parser("claim-meta",
                       help="produce new body markdown for a claim")
    s.add_argument("meta_json", help="existing meta JSON")
    s.add_argument("--agent-id", required=True)
    s.add_argument("--session-id", required=True)
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_claim_meta)

    # heartbeat-meta
    s = sub.add_parser("heartbeat-meta",
                       help="produce new body markdown with refreshed status_ts")
    s.add_argument("meta_json")
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_heartbeat_meta)

    # finish-meta
    s = sub.add_parser("finish-meta",
                       help="produce new body markdown with status=finished")
    s.add_argument("meta_json")
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_finish_meta)

    # abandon-meta
    s = sub.add_parser("abandon-meta",
                       help="produce new body markdown with status=abandoned")
    s.add_argument("meta_json")
    s.add_argument("--reason", required=True)
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_abandon_meta)

    # parse-comment
    s = sub.add_parser("parse-comment",
                       help="extract run_status / summary / paths from comment body")
    s.add_argument("body", help="raw comment body text")
    s.set_defaults(func=cmd_parse_comment)

    # parse-meta
    s = sub.add_parser("parse-meta",
                       help="parse the agent-meta block out of an issue body")
    s.add_argument("body", help="raw issue body markdown")
    s.set_defaults(func=cmd_parse_meta)

    # summary-path
    s = sub.add_parser("summary-path",
                       help="compute the summary.json path for issue/comment")
    s.add_argument("--issue", type=int, required=True)
    s.add_argument("--comment", type=int, required=True)
    s.set_defaults(func=cmd_summary_path)

    # replace-meta
    s = sub.add_parser("replace-meta",
                       help="replace the agent-meta block in an existing body")
    s.add_argument("body")
    s.add_argument("--meta-json", dest="meta_json", required=True)
    s.set_defaults(func=cmd_replace_meta)

    # validate-summary
    s = sub.add_parser("validate-summary",
                       help="validate a summary against the command schema")
    s.add_argument("summary_json")
    s.add_argument("--command", required=True)
    s.add_argument("--status", choices=("completed", "error"), required=True)
    s.set_defaults(func=cmd_validate_summary)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":  # pragma: no cover - dispatched by __main__.py
    raise SystemExit(main())

```

### .claude/skills/batch-job/templates/agent/scripts/agent_lib/envelope.py

```text
"""Envelope construction helpers for the agent harness.

Pure functions that build a ``batch-job-request`` envelope dict and
optionally validate args against the command's args sub-schema.

No I/O is performed: schemas are loaded from disk via
:mod:`agent_protocol_common`, but no network is touched.
"""

from __future__ import annotations

from typing import Any, Optional

from ._common_loader import REPO_ROOT, load_common


_common = load_common()


class EnvelopeArgsInvalid(ValueError):
    """Raised when ``args`` fail to validate against the command schema."""

    def __init__(self, command: str, message: str) -> None:
        super().__init__(f"args invalid for command {command!r}: {message}")
        self.command = command
        self.message = message


def make_request_envelope(
    command: str,
    args: dict[str, Any],
    branch: str,
    commit_sha: str,
    subagent_id: str,
    *,
    validate_args: bool = True,
    submitted_at: Optional[str] = None,
) -> dict[str, Any]:
    """Construct an unsubmitted ``batch-job-request`` envelope.

    Mirrors :func:`skills.batch-job.submit.submit` minus the I/O. When
    ``validate_args`` is True (default), ``args`` is checked against the
    command's ``args`` sub-schema; an ``EnvelopeArgsInvalid`` is raised
    on failure.

    The ``submitted_at`` timestamp is filled with :func:`iso_now` when
    not provided by the caller.
    """
    if not isinstance(command, str) or not command:
        raise ValueError("command must be a non-empty string")
    if not isinstance(args, dict):
        raise TypeError("args must be a dict")
    if not isinstance(branch, str) or not branch:
        raise ValueError("branch must be a non-empty string")
    if not isinstance(commit_sha, str) or not commit_sha:
        raise ValueError("commit_sha must be a non-empty string")
    if not isinstance(subagent_id, str) or not subagent_id:
        raise ValueError("subagent_id must be a non-empty string")

    if validate_args:
        try:
            schema = _common.load_schema(
                f"commands/{command}.schema.json", REPO_ROOT
            )
        except FileNotFoundError as e:
            raise EnvelopeArgsInvalid(command, f"no schema file: {e}") from e
        args_schema = schema.get("properties", {}).get("args")
        if args_schema is not None:
            try:
                _common.validate(args, args_schema)
            except Exception as e:  # noqa: BLE001 - rewrap
                raise EnvelopeArgsInvalid(command, str(e)) from e

    return {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "command": command,
        "args": dict(args),
        "branch": branch,
        "commit_sha": commit_sha,
        "subagent_id": subagent_id,
        "submitted_at": submitted_at or _common.iso_now(),
        "run_status": None,
        "agent_ack": None,
    }


def make_ack_envelope(
    ack_for: int,
    *,
    agent_acked_at: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    note: Optional[str] = None,
) -> dict[str, Any]:
    """Construct an agent-ack follow-up comment envelope.

    ``ack_for`` is the comment_id of the original batch-job-request whose
    terminal envelope this comment acknowledges (SPEC §5.2). The
    handler treats agent-ack comments as informational; the
    working->finished gate (SPEC §4.1) accepts EITHER an in-place
    ``agent_ack: finished`` on the request comment OR a follow-up
    ``kind: agent-ack`` comment with ``ack_for`` matching the request.
    """
    if not isinstance(ack_for, int) or isinstance(ack_for, bool) or ack_for < 1:
        raise ValueError("ack_for must be a positive integer (comment_id)")
    env: dict[str, Any] = {
        "protocol_version": 1,
        "kind": "agent-ack",
        "ack_for": ack_for,
        "agent_acked_at": agent_acked_at or _common.iso_now(),
    }
    if agent_id is not None:
        env["agent_id"] = agent_id
    if session_id is not None:
        env["session_id"] = session_id
    if note is not None:
        env["note"] = note
    return env


__all__ = ["EnvelopeArgsInvalid", "make_request_envelope", "make_ack_envelope"]

```

### .claude/skills/batch-job/templates/agent/scripts/agent_lib/meta.py

````text
"""Pure helpers that produce / mutate ``agent-meta`` blocks.

Each function takes either a meta dict (for transformations) or kwargs
(for ``make_initial_meta``) and returns either a new dict or the
markdown body string ready to be sent to ``mcp__github__issue_write``
as the ``body`` field.

No GitHub I/O is performed.
"""

from __future__ import annotations

from typing import Any, Optional

from ._common_loader import load_common


_common = load_common()


def _extract_prose(body: Optional[str]) -> str:
    """Return everything before the agent-meta fenced block, if any."""
    if not body:
        return ""
    marker = "```agent-meta"
    idx = body.find(marker)
    if idx == -1:
        return body
    return body[:idx].rstrip()


def make_initial_meta(
    *,
    feature_branch: str,
    base_branch: str = "main",
    instructions_inline: Optional[str] = None,
    instructions_path: Optional[str] = None,
    parent_issue: Optional[int] = None,
    depends_on_prs: Optional[list[int]] = None,
    protocol_version: int = 1,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a fresh agent-meta dict with ``status=None``.

    Either ``instructions_inline`` or ``instructions_path`` must be
    provided (matching the schema's ``anyOf``).
    """
    if not feature_branch:
        raise ValueError("feature_branch is required")
    if not instructions_inline and not instructions_path:
        raise ValueError(
            "either instructions_inline or instructions_path must be set"
        )
    meta = {
        "protocol_version": protocol_version,
        "agent_id": None,
        "session_id": None,
        "status": None,
        "status_ts": None,
        "feature_branch": feature_branch,
        "base_branch": base_branch,
        "parent_issue": parent_issue,
        "depends_on_prs": list(depends_on_prs or []),
        "instructions_path": instructions_path,
        "instructions_inline": instructions_inline,
        "created_at": _common.iso_now(),
    }
    if extra:
        for k, v in extra.items():
            meta[k] = v
    return meta


def claim_meta(
    meta: dict[str, Any],
    agent_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Mark the meta as claimed by ``agent_id``/``session_id``.

    Returns a new dict; the input is not mutated.
    """
    if not agent_id:
        raise ValueError("agent_id is required")
    if not session_id:
        raise ValueError("session_id is required")
    new_meta = dict(meta)
    new_meta["agent_id"] = agent_id
    new_meta["session_id"] = session_id
    new_meta["status"] = "working"
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def heartbeat_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Refresh ``status_ts`` to now. Returns a new dict."""
    new_meta = dict(meta)
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def finish_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Mark the meta as ``status="finished"``. Returns a new dict."""
    new_meta = dict(meta)
    new_meta["status"] = "finished"
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def abandon_meta(meta: dict[str, Any], reason: str) -> dict[str, Any]:
    """Mark the meta as ``abandoned`` with a recorded reason.

    The ``reason`` is stored under the ``abandon_reason`` key (additional
    properties are allowed by the issue-body schema).
    """
    new_meta = dict(meta)
    new_meta["status"] = "abandoned"
    new_meta["status_ts"] = _common.iso_now()
    new_meta["abandon_reason"] = reason
    return new_meta


def render_body(meta: dict[str, Any], prose: str = "") -> str:
    """Convenience: render an issue body with the given meta."""
    return _common.render_agent_meta(meta, prose=prose)


def parse_body(body: Optional[str]) -> Optional[dict[str, Any]]:
    """Convenience: parse an agent-meta block out of a body."""
    return _common.parse_agent_meta(body)


def replace_meta_in_body(
    body: Optional[str],
    new_meta: dict[str, Any],
) -> str:
    """Replace the agent-meta block in ``body`` with ``new_meta``.

    The prose before the block is preserved; if there was no block, the
    new meta is appended.
    """
    prose = _extract_prose(body)
    return _common.render_agent_meta(new_meta, prose=prose)


__all__ = [
    "make_initial_meta",
    "claim_meta",
    "heartbeat_meta",
    "finish_meta",
    "abandon_meta",
    "render_body",
    "parse_body",
    "replace_meta_in_body",
]

````

### .claude/skills/batch-job/templates/agent/scripts/agent_lib/poll.py

```text
"""Helpers for parsing terminal-status comments.

Polling itself is performed by the agent via repeated MCP calls; the
helpers here just classify a comment body and tell the agent what
``summary.json`` path to read once the comment has reached a terminal
state.
"""

from __future__ import annotations

import html
import json
from typing import Any, Optional

from ._common_loader import load_common


_common = load_common()


_TERMINAL_STATUSES = {"completed", "error", "parse_error"}


def parse_terminal_status(
    envelope_json: str,
) -> tuple[Optional[str], dict[str, Any]]:
    """Classify a comment body.

    Returns a tuple ``(run_status, parsed)``:
      - On JSON parse failure: returns ``(None, {})``.
      - On non-terminal envelope (run_status=None or "running"): returns
        ``(None, parsed)``.
      - On terminal envelope: returns ``(run_status, parsed)``.

    The caller is expected to use the parsed envelope to look up the
    summary path via :func:`summary_path_for` when terminal.
    """
    if not isinstance(envelope_json, str):
        raise TypeError("envelope_json must be a string")
    # MCP returns comment bodies HTML-escaped (&#34; for ", etc.) and
    # Claude Code's GitHub MCP additionally appends a trailer line like
    # ``\n---\n_Generated by [Claude Code](https://claude.ai/code)_`` to
    # every posted comment. We unescape (no-op on REST content) and then
    # use raw_decode to parse the longest JSON-object prefix at the
    # start of the body, tolerating any trailing prose.
    unescaped = html.unescape(envelope_json).lstrip()
    if not unescaped:
        return None, {}
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(unescaped)
    except (json.JSONDecodeError, ValueError):
        return None, {}
    if not isinstance(parsed, dict):
        return None, {}
    status = parsed.get("run_status")
    if status in _TERMINAL_STATUSES:
        return status, parsed
    return None, parsed


def summary_path_for(issue_number: int, comment_id: int) -> str:
    """Return the ``summary.json`` path under the ``_agent_runs`` branch."""
    if not isinstance(issue_number, int) or issue_number < 1:
        raise ValueError("issue_number must be a positive integer")
    if not isinstance(comment_id, int) or comment_id < 1:
        raise ValueError("comment_id must be a positive integer")
    return f"runs/{issue_number}/{comment_id}/summary.json"


def manifest_path_for(issue_number: int, comment_id: int) -> str:
    """Return the ``manifest.json`` path under the ``_agent_runs`` branch."""
    return f"runs/{issue_number}/{comment_id}/manifest.json"


def is_terminal(envelope: dict[str, Any]) -> bool:
    """True if the envelope's ``run_status`` is terminal."""
    return _common.is_terminal_run_status(envelope.get("run_status"))


def parse_ack_comment(body: str) -> Optional[dict[str, Any]]:
    """If body is an agent-ack envelope, return parsed dict; else None.

    Tolerates HTML-escaped bodies and trailing prose (matching the
    parse_terminal_status conventions).
    """
    if not isinstance(body, str):
        return None
    unescaped = html.unescape(body).lstrip()
    if not unescaped:
        return None
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(unescaped)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    if parsed.get("protocol_version") != 1 or parsed.get("kind") != "agent-ack":
        return None
    return parsed


def is_request_acked(
    request_envelope: dict[str, Any],
    request_comment_id: int,
    other_comment_bodies: list[str],
) -> bool:
    """Return True if the request is acked via either form (SPEC §4.1).

    EITHER ``request_envelope["agent_ack"] == "finished"`` (in-place form)
    OR there is at least one comment in ``other_comment_bodies`` that is
    a valid ``kind: agent-ack`` envelope with ``ack_for == request_comment_id``.
    """
    if request_envelope.get("agent_ack") == "finished":
        return True
    for body in other_comment_bodies:
        ack = parse_ack_comment(body)
        if ack and ack.get("ack_for") == request_comment_id:
            return True
    return False


__all__ = [
    "parse_terminal_status",
    "summary_path_for",
    "manifest_path_for",
    "is_terminal",
    "parse_ack_comment",
    "is_request_acked",
]

```

### .claude/skills/batch-job/templates/agent/scripts/common.py

````text
"""Common helpers for the agent protocol POC.

Provides:
- ``GitHubClient`` Protocol/abstract definition of the operations the
  scripts need.
- ``InMemoryGitHubClient`` — fully working in-memory implementation
  used in tests and for local POC demonstrations.
- Envelope/agent-meta helpers (parse, render).
- ``LogWriter`` — a JSONL/gzip log writer that rotates by compressed
  size and produces a manifest.
- ``load_config`` and ``validate`` JSON-schema helpers.

The real GitHub REST integration is intentionally **not** implemented
here; for the POC we exercise behaviour through the in-memory client.
"""

from __future__ import annotations

import base64
import gzip
import html
import io
import json
import os
import re
import secrets
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Optional,
    Protocol,
    runtime_checkable,
)

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - jsonschema is in requirements
    Draft202012Validator = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Time and config helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    """Return the current UTC time as an ISO-8601 string with ``Z`` suffix."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config(path: str | os.PathLike[str] = ".agent/config.json") -> dict[str, Any]:
    """Load the central agent configuration JSON file."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(json_obj: Any, schema_obj: dict[str, Any]) -> None:
    """Validate a JSON object against a JSON schema (Draft 2020-12).

    Raises ``jsonschema.ValidationError`` on the first error encountered.
    """
    if Draft202012Validator is None:  # pragma: no cover
        raise RuntimeError("jsonschema is not installed; cannot validate")
    validator = Draft202012Validator(schema_obj)
    errors = sorted(validator.iter_errors(json_obj), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.absolute_path) or "<root>"
        raise ValueError(f"schema validation failed at {path}: {first.message}")


# ---------------------------------------------------------------------------
# agent-meta block parsing / rendering
# ---------------------------------------------------------------------------

_AGENT_META_RE = re.compile(
    r"```agent-meta\s*\n(?P<json>.*?)\n```",
    re.DOTALL,
)


def parse_agent_meta(body: Optional[str]) -> Optional[dict[str, Any]]:
    """Extract the JSON object inside the fenced ``agent-meta`` block.

    Returns ``None`` when:
    - the body is ``None`` or empty, OR
    - no ``agent-meta`` fenced block is present, OR
    - the block exists but its body is not valid JSON.

    The MCP server returns issue bodies with HTML-escaped entities
    (``&#34;`` for ``"``, etc.). We unescape the JSON region before
    parsing so the same parser works against MCP and REST responses.
    Workflow REST responses contain literal quotes so unescape is a
    no-op there.
    """
    if not body:
        return None
    m = _AGENT_META_RE.search(body)
    if not m:
        return None
    raw = html.unescape(m.group("json"))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def render_agent_meta(meta: dict[str, Any], prose: str = "") -> str:
    """Render an issue body markdown with the given ``agent-meta`` block.

    The prose is placed before the fenced block; a blank line separates
    them when both are non-empty.
    """
    block = "```agent-meta\n" + json.dumps(meta, indent=2) + "\n```"
    if prose:
        return f"{prose.rstrip()}\n\n{block}\n"
    return block + "\n"


# ---------------------------------------------------------------------------
# GitHub client abstraction
# ---------------------------------------------------------------------------

@runtime_checkable
class GitHubClient(Protocol):
    """Minimal protocol for the operations the agent scripts need.

    Implementations may use the REST API, an MCP relay, or the
    in-memory mock used for the POC. Errors are raised as exceptions.
    """

    # Issue operations -----------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]: ...
    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]: ...
    def lock_issue(self, number: int) -> None: ...
    def add_label(self, number: int, label: str) -> None: ...
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]: ...

    # Comment operations ---------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]: ...
    def get_comment(self, comment_id: int) -> dict[str, Any]: ...
    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]: ...
    def delete_comment(self, comment_id: int) -> None: ...
    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]: ...

    # File / branch operations --------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]: ...
    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]: ...
    def get_branch_head_sha(self, branch: str) -> Optional[str]: ...
    def delete_branch(self, name: str) -> None: ...
    def list_branches(self) -> list[dict[str, Any]]: ...

    # PR operations --------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]: ...
    def get_pull_request(self, number: int) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# In-memory GitHub client (POC + tests)
# ---------------------------------------------------------------------------

@dataclass
class _Commit:
    sha: str
    parent: Optional[str]
    message: str
    files: dict[str, bytes]  # path -> content


@dataclass
class _Branch:
    name: str
    head_sha: Optional[str]  # None means orphan/uninitialised


@dataclass
class _Comment:
    id: int
    issue_number: int
    user: str
    body: str
    created_at: str
    updated_at: str


@dataclass
class _Issue:
    number: int
    title: str
    body: str
    user: str
    state: str = "open"
    locked: bool = False
    labels: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=iso_now)
    updated_at: str = field(default_factory=iso_now)


@dataclass
class _PullRequest:
    number: int
    title: str
    head: str
    base: str
    body: str
    state: str = "open"
    merged: bool = False
    merge_commit_sha: Optional[str] = None
    user: str = "agent"
    created_at: str = field(default_factory=iso_now)


class InMemoryGitHubClient:
    """In-memory simulation of the subset of GitHub the protocol uses.

    Each call returns dict-shaped data resembling the REST API responses
    so that calling code is portable to a real REST client.
    """

    def __init__(self, default_user: str = "agent") -> None:
        self._lock = threading.RLock()
        self._issues: dict[int, _Issue] = {}
        self._comments: dict[int, _Comment] = {}
        self._comments_by_issue: dict[int, list[int]] = {}
        self._branches: dict[str, _Branch] = {}
        self._commits: dict[str, _Commit] = {}
        self._pulls: dict[int, _PullRequest] = {}
        self._next_issue_number = 1
        self._next_comment_id = 1_000_000
        self._next_pr_number = 5000
        self._default_user = default_user
        self._actor_stack: list[str] = [default_user]

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------
    def as_user(self, login: str) -> "_ActAs":
        """Context manager: switch the effective acting user temporarily."""
        return _ActAs(self, login)

    @property
    def current_user(self) -> str:
        return self._actor_stack[-1]

    def create_issue(
        self,
        title: str,
        body: str,
        user: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Test helper: create a fresh issue in the in-memory state."""
        with self._lock:
            number = self._next_issue_number
            self._next_issue_number += 1
            issue = _Issue(
                number=number,
                title=title,
                body=body,
                user=user or self.current_user,
                labels=list(labels or []),
            )
            self._issues[number] = issue
            self._comments_by_issue[number] = []
            return self._issue_to_dict(issue)

    def create_branch(self, name: str, from_branch: Optional[str] = None) -> str:
        """Create a branch (optionally branching from another). Returns sha."""
        with self._lock:
            if name in self._branches:
                raise ValueError(f"branch already exists: {name}")
            parent_sha: Optional[str] = None
            files: dict[str, bytes] = {}
            if from_branch is not None:
                src = self._branches.get(from_branch)
                if src is None:
                    raise ValueError(f"unknown source branch: {from_branch}")
                parent_sha = src.head_sha
                if parent_sha is not None:
                    files = dict(self._commits[parent_sha].files)
            sha = _new_sha()
            commit = _Commit(
                sha=sha,
                parent=parent_sha,
                message=f"create branch {name}",
                files=files,
            )
            self._commits[sha] = commit
            self._branches[name] = _Branch(name=name, head_sha=sha)
            return sha

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _issue_to_dict(self, issue: _Issue) -> dict[str, Any]:
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "user": {"login": issue.user},
            "state": issue.state,
            "locked": issue.locked,
            "labels": [{"name": n} for n in issue.labels],
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
        }

    def _comment_to_dict(self, c: _Comment) -> dict[str, Any]:
        return {
            "id": c.id,
            "issue_number": c.issue_number,
            "user": {"login": c.user},
            "body": c.body,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }

    # ------------------------------------------------------------------
    # Issue API
    # ------------------------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            return self._issue_to_dict(issue)

    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            if body is not None:
                issue.body = body
            if state is not None:
                if state not in ("open", "closed"):
                    raise ValueError(f"bad state: {state}")
                issue.state = state
            if labels is not None:
                issue.labels = list(labels)
            issue.updated_at = iso_now()
            return self._issue_to_dict(issue)

    def lock_issue(self, number: int) -> None:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            issue.locked = True
            issue.updated_at = iso_now()

    def add_label(self, number: int, label: str) -> None:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            if label not in issue.labels:
                issue.labels.append(label)
            issue.updated_at = iso_now()

    # ------------------------------------------------------------------
    # Comment API
    # ------------------------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]:
        with self._lock:
            ids = self._comments_by_issue.get(issue_number, [])
            return [self._comment_to_dict(self._comments[i]) for i in ids]

    def get_comment(self, comment_id: int) -> dict[str, Any]:
        with self._lock:
            c = self._comments.get(comment_id)
            if c is None:
                raise KeyError(f"no such comment: {comment_id}")
            return self._comment_to_dict(c)

    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        with self._lock:
            c = self._comments.get(comment_id)
            if c is None:
                raise KeyError(f"no such comment: {comment_id}")
            c.body = body
            c.updated_at = iso_now()
            return self._comment_to_dict(c)

    def delete_comment(self, comment_id: int) -> None:
        with self._lock:
            c = self._comments.pop(comment_id, None)
            if c is None:
                return
            self._comments_by_issue.get(c.issue_number, []).remove(comment_id)

    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        with self._lock:
            if issue_number not in self._issues:
                raise KeyError(f"no such issue: {issue_number}")
            cid = self._next_comment_id
            self._next_comment_id += 1
            now = iso_now()
            c = _Comment(
                id=cid,
                issue_number=issue_number,
                user=self.current_user,
                body=body,
                created_at=now,
                updated_at=now,
            )
            self._comments[cid] = c
            self._comments_by_issue.setdefault(issue_number, []).append(cid)
            return self._comment_to_dict(c)

    # ------------------------------------------------------------------
    # Files / branches / commits
    # ------------------------------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]:
        with self._lock:
            branch = self._branches.get(ref)
            if branch is None or branch.head_sha is None:
                return None
            commit = self._commits[branch.head_sha]
            data = commit.files.get(path)
            if data is None:
                return None
            # Returned as text (utf-8) or base64 if binary; we always return
            # decoded utf-8 if possible, else b64. Tests typically compare
            # bytes via separate helpers.
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(data).decode("ascii")

    def get_file_bytes(self, path: str, ref: str) -> Optional[bytes]:
        """Test convenience: raw bytes of a file at ref."""
        with self._lock:
            branch = self._branches.get(ref)
            if branch is None or branch.head_sha is None:
                return None
            commit = self._commits[branch.head_sha]
            return commit.files.get(path)

    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                # Auto-create as orphan branch (no parent)
                br = _Branch(name=branch, head_sha=None)
                self._branches[branch] = br
            parent = br.head_sha
            files = dict(self._commits[parent].files) if parent else {}
            files[path] = content_bytes
            sha = _new_sha()
            commit = _Commit(sha=sha, parent=parent, message=message, files=files)
            self._commits[sha] = commit
            br.head_sha = sha
            return {
                "path": path,
                "branch": branch,
                "commit": {"sha": sha, "message": message},
                "size": len(content_bytes),
            }

    def get_branch_head_sha(self, branch: str) -> Optional[str]:
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                return None
            return br.head_sha

    def delete_branch(self, name: str) -> None:
        """Delete a branch ref. Idempotent: missing branches are ignored.

        Note: commits are not garbage-collected from the in-memory store —
        only the branch ref is removed (mirrors GitHub's ref-delete semantics).
        """
        with self._lock:
            self._branches.pop(name, None)

    def list_branches(self) -> list[dict[str, Any]]:
        """List all branches as dicts ``{name, sha, protected}``.

        Mirrors a paginated REST ``GET /repos/{owner}/{repo}/branches``
        response shape. The in-memory client has no notion of branch
        protection, so ``protected`` is always ``False``.
        """
        with self._lock:
            return [
                {"name": b.name, "sha": b.head_sha, "protected": False}
                for b in self._branches.values()
            ]

    def commit_files(
        self,
        branch: str,
        files: dict[str, bytes],
        message: str,
    ) -> str:
        """Test helper: commit multiple files atomically. Returns new sha."""
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                br = _Branch(name=branch, head_sha=None)
                self._branches[branch] = br
            parent = br.head_sha
            current = dict(self._commits[parent].files) if parent else {}
            current.update(files)
            sha = _new_sha()
            self._commits[sha] = _Commit(
                sha=sha, parent=parent, message=message, files=current
            )
            br.head_sha = sha
            return sha

    # ------------------------------------------------------------------
    # PR API
    # ------------------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]:
        with self._lock:
            if head not in self._branches:
                raise ValueError(f"head branch does not exist: {head}")
            if base not in self._branches:
                raise ValueError(f"base branch does not exist: {base}")
            number = self._next_pr_number
            self._next_pr_number += 1
            pr = _PullRequest(
                number=number,
                title=title,
                head=head,
                base=base,
                body=body,
                user=self.current_user,
            )
            self._pulls[number] = pr
            return self._pr_to_dict(pr)

    def get_pull_request(self, number: int) -> dict[str, Any]:
        with self._lock:
            pr = self._pulls.get(number)
            if pr is None:
                raise KeyError(f"no such PR: {number}")
            return self._pr_to_dict(pr)

    def merge_pull_request(self, number: int) -> dict[str, Any]:
        """Test helper: simulate a merged PR."""
        with self._lock:
            pr = self._pulls.get(number)
            if pr is None:
                raise KeyError(f"no such PR: {number}")
            pr.state = "closed"
            pr.merged = True
            pr.merge_commit_sha = _new_sha()
            return self._pr_to_dict(pr)

    def _pr_to_dict(self, pr: _PullRequest) -> dict[str, Any]:
        return {
            "number": pr.number,
            "title": pr.title,
            "head": {"ref": pr.head},
            "base": {"ref": pr.base},
            "body": pr.body,
            "state": pr.state,
            "merged": pr.merged,
            "merge_commit_sha": pr.merge_commit_sha,
            "user": {"login": pr.user},
            "created_at": pr.created_at,
        }


class _ActAs:
    """Context manager to switch the in-memory client's acting user."""

    def __init__(self, client: InMemoryGitHubClient, login: str) -> None:
        self._client = client
        self._login = login

    def __enter__(self) -> InMemoryGitHubClient:
        self._client._actor_stack.append(self._login)
        return self._client

    def __exit__(self, exc_type, exc, tb) -> None:
        self._client._actor_stack.pop()


def _new_sha() -> str:
    """Generate a 40-character lowercase hex 'sha'."""
    return secrets.token_hex(20)


# ---------------------------------------------------------------------------
# Log sanitisation (SPEC §14)
# ---------------------------------------------------------------------------

# GitHub PAT/OAuth-style tokens.
_RE_GH_TOKEN = re.compile(r"gh[ps]_[A-Za-z0-9]{36,}")
# AWS access key id.
_RE_AWS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
# Bearer tokens in Authorization-style strings.
_RE_BEARER = re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")
# Generic key=value patterns where the key looks secret-shaped. We
# intentionally redact only the captured group so the rest of the
# string (including the key name and separator) survives for context.
_RE_GENERIC_SECRET = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password)[\"'\s:=]+([A-Za-z0-9_\-]{16,})"
)


def _sanitize_string(s: str) -> str:
    """Redact common secret patterns in a single string."""
    out = _RE_GH_TOKEN.sub("***", s)
    out = _RE_AWS_KEY.sub("***", out)
    out = _RE_BEARER.sub("Bearer ***", out)

    def _redact_group(m: re.Match[str]) -> str:
        whole = m.group(0)
        captured = m.group(1)
        # Replace just the captured secret value with ``***``.
        start, end = m.span(1)
        # m.span is relative to the whole input string, not to ``whole``.
        return whole[: start - m.start()] + "***" + whole[end - m.start():]

    out = _RE_GENERIC_SECRET.sub(_redact_group, out)
    return out


def sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copied record with common secret patterns redacted.

    Per SPEC §14: log content on a public repo is world-readable, so
    the handler should pass log records through a sanitiser that drops
    anything matching common secret patterns before writing chunks.

    The original ``record`` is NOT mutated.
    """

    def _walk(node: Any) -> Any:
        if isinstance(node, str):
            return _sanitize_string(node)
        if isinstance(node, dict):
            return {k: _walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(v) for v in node]
        if isinstance(node, tuple):
            return tuple(_walk(v) for v in node)
        return node

    return _walk(record)


# ---------------------------------------------------------------------------
# LogWriter
# ---------------------------------------------------------------------------

@dataclass
class _ChunkInfo:
    path: str
    bytes_: int
    lines: int
    data: bytes


class LogWriter:
    """Append JSONL records, gzip-rotate at a configured size threshold.

    Usage::

        lw = LogWriter(max_chunk_bytes_compressed=512_000)
        lw.write({"ts": iso_now(), "stream": "stdout", "phase": "exec",
                  "data": "hello"})
        ...
        chunks = lw.finalize()        # list[(path, bytes, dict)]
        manifest = lw.manifest(...)   # build manifest dict

    Records are passed through :func:`sanitize_record` before being
    serialised, unless the writer was constructed with
    ``sanitize=False``.
    """

    def __init__(
        self,
        max_chunk_bytes_compressed: int = 524_288,
        chunk_name_template: str = "log-{n:04d}.jsonl.gz",
        sanitize: bool = True,
    ) -> None:
        self._max = int(max_chunk_bytes_compressed)
        self._template = chunk_name_template
        self._sanitize = bool(sanitize)
        self._buf = io.BytesIO()
        self._gz = gzip.GzipFile(fileobj=self._buf, mode="wb", mtime=0)
        self._cur_lines = 0
        self._chunk_index = 1
        self._chunks: list[_ChunkInfo] = []
        self._closed = False

    # ------------------------------------------------------------------
    def set_max_chunk_bytes(self, max_chunk_bytes_compressed: int) -> None:
        """Update the rotation threshold mid-stream (use sparingly).

        Useful for test commands like chatty that want to force rotation
        at a smaller threshold than the production default.
        """
        if self._closed:
            raise RuntimeError("LogWriter is closed")
        n = int(max_chunk_bytes_compressed)
        if n < 1:
            raise ValueError("max_chunk_bytes_compressed must be >= 1")
        self._max = n

    # ------------------------------------------------------------------
    def _rotate_if_needed(self) -> None:
        # Flush current gzip stream to estimate compressed size.
        self._gz.flush()
        if self._buf.tell() >= self._max and self._cur_lines > 0:
            self._close_current_chunk()
            self._open_new_chunk()

    def _close_current_chunk(self) -> None:
        self._gz.close()
        data = self._buf.getvalue()
        path = self._template.format(n=self._chunk_index)
        self._chunks.append(
            _ChunkInfo(path=path, bytes_=len(data), lines=self._cur_lines, data=data)
        )
        self._chunk_index += 1

    def _open_new_chunk(self) -> None:
        self._buf = io.BytesIO()
        self._gz = gzip.GzipFile(fileobj=self._buf, mode="wb", mtime=0)
        self._cur_lines = 0

    # ------------------------------------------------------------------
    def write(self, record: dict[str, Any]) -> None:
        """Append one JSON record (one line) to the current chunk.

        When ``sanitize=True`` (default), the record is passed through
        :func:`sanitize_record` before serialisation.
        """
        if self._closed:
            raise RuntimeError("LogWriter is closed")
        payload = sanitize_record(record) if self._sanitize else record
        line = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        self._gz.write(line)
        self._cur_lines += 1
        # Rotate after writing so chunks contain at least one line.
        self._rotate_if_needed()

    def finalize(self) -> list[tuple[str, bytes, dict[str, int]]]:
        """Close the writer; return list of ``(path, gz_bytes, info)``.

        ``info`` contains keys ``bytes`` and ``lines``.
        """
        if self._closed:
            return [(c.path, c.data, {"bytes": c.bytes_, "lines": c.lines}) for c in self._chunks]
        # Close current chunk if it has any lines.
        if self._cur_lines > 0:
            self._close_current_chunk()
        else:
            # discard empty buffer
            try:
                self._gz.close()
            except Exception:
                pass
        self._closed = True
        return [(c.path, c.data, {"bytes": c.bytes_, "lines": c.lines}) for c in self._chunks]

    def manifest(
        self,
        *,
        command: str,
        args: dict[str, Any],
        checked_out_sha: str,
        started_at: str,
        finished_at: str,
        exit_code: int,
        protocol_version: int = 1,
        extra_schema_fields: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build a manifest dict matching ``log-manifest.schema.json``."""
        if not self._closed:
            self.finalize()
        fields = {
            "ts": {"type": "string", "description": "ISO 8601"},
            "stream": {"enum": ["stdout", "stderr", "meta"]},
            "phase": {"enum": ["setup", "exec", "teardown"]},
            "data": {"type": ["string", "object"]},
        }
        if extra_schema_fields:
            fields.update(extra_schema_fields)
        return {
            "protocol_version": protocol_version,
            "schema": {
                "chunk_format": "jsonl-gz",
                "fields": fields,
            },
            "command": command,
            "args": args,
            "checked_out_sha": checked_out_sha,
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "chunks": [
                {"path": c.path, "bytes": c.bytes_, "lines": c.lines}
                for c in self._chunks
            ],
        }

    # Convenience for tests / debugging
    def chunks(self) -> list[tuple[str, bytes, dict[str, int]]]:
        return self.finalize()


# ---------------------------------------------------------------------------
# Schema loading helpers
# ---------------------------------------------------------------------------

def schemas_root(repo_root: str | os.PathLike[str] = ".") -> Path:
    return Path(repo_root) / ".agent" / "schemas"


def load_schema(name: str, repo_root: str | os.PathLike[str] = ".") -> dict[str, Any]:
    """Load a schema by relative name (e.g. ``commands/run-tests.schema.json``)."""
    p = schemas_root(repo_root) / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def b64_encode(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("ascii")


def b64_decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def new_uuid() -> str:
    return str(uuid.uuid4())


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "task"


def is_terminal_run_status(status: Optional[str]) -> bool:
    return status in {"completed", "error", "parse_error"}


def has_protocol_markers(obj: Any) -> bool:
    """Return True if a parsed JSON object has ``protocol_version`` and ``kind``."""
    return (
        isinstance(obj, dict)
        and "protocol_version" in obj
        and "kind" in obj
    )


__all__ = [
    "GitHubClient",
    "InMemoryGitHubClient",
    "LogWriter",
    "iso_now",
    "load_config",
    "load_schema",
    "validate",
    "parse_agent_meta",
    "render_agent_meta",
    "b64_encode",
    "b64_decode",
    "new_uuid",
    "slugify",
    "is_terminal_run_status",
    "has_protocol_markers",
    "sanitize_record",
]

````

### .claude/skills/batch-job/templates/agent/scripts/handler.py

````text
"""``batch-job-handler`` script (§7.2).

Loads a comment from GitHub via the abstract :class:`GitHubClient`,
parses the JSON envelope, dispatches to a registered command handler,
writes structured logs into ``_agent_runs/runs/<issue>/<comment>/`` and
edits the comment with the terminal envelope.

Importable as ``run(client, issue_number, comment_id, ...)`` for tests.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Optional


def _parse_envelope_lenient(body: str) -> Optional[dict[str, Any]]:
    """Parse the longest JSON-object prefix at the start of ``body``.

    SPEC §5.2 says the comment body is a JSON object with no surrounding
    prose. We interpret "no surrounding prose" liberally to mean **JSON
    must start at the beginning of the body** (after any leading
    whitespace), but trailing prose is tolerated. This is necessary
    because some MCP servers (notably Claude Code's GitHub MCP)
    automatically append a trailer like
    ``\\n---\\n_Generated by [Claude Code](https://claude.ai/code)_``
    to every comment they post.

    Returns the parsed dict, or ``None`` if:
      - ``body`` is not a string, OR
      - the body (after stripping leading whitespace) does not start
        with a valid JSON object.
    """
    if not isinstance(body, str):
        return None
    stripped = body.lstrip()
    if not stripped:
        return None
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(stripped)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed

if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )
else:
    from .common import (
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    *,
    workflow_run_id: int = 0,
    workspace: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Process a single comment. Returns a summary dict for tests."""
    cfg = config or load_config(Path(repo_root) / ".agent" / "config.json")

    comment = client.get_comment(comment_id)
    raw_body = comment.get("body") or ""

    # Step 1: parse envelope ----------------------------------------------
    # Tolerate trailing prose (e.g. the trailer Claude Code's GitHub MCP
    # appends to every comment); see _parse_envelope_lenient.
    parsed: Optional[dict[str, Any]] = _parse_envelope_lenient(raw_body)

    if not has_protocol_markers(parsed):
        return {"action": "ignored", "reason": "no_protocol_markers"}

    assert isinstance(parsed, dict)  # for type checkers

    # Dispatch on envelope kind. Acks are informational follow-up comments;
    # the handler does not process them as batch jobs. They are surfaced
    # through the working->finished gate (SPEC §4.1). Without this dispatch
    # the schema validation step below would parse-error every agent-ack
    # comment because comment-envelope.schema.json says
    # ``kind: const "batch-job-request"``.
    kind = parsed.get("kind")
    if kind == "agent-ack":
        return {"action": "noop", "reason": "ack_comment", "kind": "agent-ack"}

    # Idempotency on already-terminal envelopes (webhook redelivery).
    if is_terminal_run_status(parsed.get("run_status")):
        return {"action": "noop", "reason": "already_terminal", "run_status": parsed["run_status"]}

    envelope_schema = load_schema("comment-envelope.schema.json", repo_root)

    started_at = iso_now()

    # SPEC §13: reject envelopes with unknown protocol_version BEFORE schema
    # validation. We already know parsed has both protocol_version and kind
    # markers (has_protocol_markers above).
    if parsed.get("protocol_version") != 1:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="unsupported_version",
            error_detail=(
                f"protocol_version {parsed.get('protocol_version')!r} is not supported"
            ),
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    # Validate base envelope shape.
    try:
        validate(parsed, envelope_schema)
    except Exception as e:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="schema_validation_failed",
            error_detail=str(e),
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    command = parsed.get("command")
    if not command or command not in cfg.get("commands", []):
        # SPEC §5.2.4 reserves parse_error for envelope-schema failures only.
        # An unknown command is a valid envelope referring to an unregistered
        # command — this is a terminal `error` with error_kind=unknown_command.
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="unknown_command",
            error_detail=f"command not in registry: {command!r}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    # Validate args via per-command schema.
    cmd_schema_path = f"commands/{command}.schema.json"
    try:
        cmd_schema = load_schema(cmd_schema_path, repo_root)
    except FileNotFoundError:
        # Command exists in the registry but the schema file is missing —
        # treat as a more specific terminal error so operators can tell
        # this case apart from a truly unknown command.
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="missing_schema",
            error_detail=f"no schema file for command {command}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    args_schema = cmd_schema.get("properties", {}).get("args")
    if args_schema:
        try:
            validate(parsed.get("args", {}), args_schema)
        except Exception as e:
            return _write_parse_error(
                client,
                comment_id,
                original_body=raw_body,
                error_kind="schema_validation_failed",
                error_detail=f"args: {e}",
                workflow_run_id=workflow_run_id,
                started_at=started_at,
            )

    # Step 3: branch+SHA check --------------------------------------------
    branch = parsed["branch"]
    expected_sha = parsed["commit_sha"]
    head_sha = client.get_branch_head_sha(branch)
    if head_sha is None:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"branch does not exist: {branch}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )
    if head_sha != expected_sha:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"HEAD={head_sha} != commit_sha={expected_sha}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    # Step 4: mark running ------------------------------------------------
    running_envelope = dict(parsed)
    running_envelope["run_status"] = "running"
    running_envelope["run_started_at"] = started_at
    running_envelope["workflow_run_id"] = workflow_run_id
    running_envelope["checked_out_sha"] = head_sha
    client.update_comment(comment_id, json.dumps(running_envelope, indent=2))

    # Step 5: dispatch ----------------------------------------------------
    log_writer = LogWriter(
        max_chunk_bytes_compressed=cfg.get("logs", {}).get("max_chunk_bytes_compressed", 524_288)
    )

    try:
        handler_fn = _load_command_handler(command)
        summary = handler_fn(parsed.get("args", {}) or {}, log_writer, workspace)
        run_status = "completed"
        error_kind: Optional[str] = None
        error_detail: Optional[str] = None
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log_writer.write({
            "ts": iso_now(),
            "stream": "stderr",
            "phase": "exec",
            "data": tb,
        })
        summary = {
            "error_kind": type(e).__name__,
            "error_detail": str(e),
        }
        run_status = "error"
        error_kind = type(e).__name__
        error_detail = str(e)

    finished_at = iso_now()

    # Step 6: validate summary against the command schema -----------------
    summary_schema_key = (
        "summary_completed" if run_status == "completed" else "summary_error"
    )
    summary_schema = cmd_schema.get("properties", {}).get(summary_schema_key)
    if summary_schema is not None:
        try:
            validate(summary, summary_schema)
        except Exception as e:
            run_status = "error"
            error_kind = "summary_schema_violation"
            error_detail = str(e)
            summary = {
                "error_kind": "summary_schema_violation",
                "error_detail": str(e),
            }
            log_writer.write({
                "ts": iso_now(),
                "stream": "stderr",
                "phase": "teardown",
                "data": f"summary schema violation: {e}",
            })

    # Step 7: write logs to _agent_runs ----------------------------------
    chunks = log_writer.finalize()
    manifest = log_writer.manifest(
        command=command,
        args=parsed.get("args", {}) or {},
        checked_out_sha=head_sha,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=0 if run_status == "completed" else 1,
    )

    # Validate the manifest against its schema (defense in depth).
    try:
        manifest_schema = load_schema("log-manifest.schema.json", repo_root)
        validate(manifest, manifest_schema)
    except Exception as e:  # pragma: no cover - manifest is built by us
        log_writer = None  # mark unused
        run_status = "error"
        error_kind = "manifest_schema_violation"
        error_detail = str(e)

    logs_branch = cfg.get("logs", {}).get("branch", "_agent_runs")
    log_dir = f"runs/{issue_number}/{comment_id}"

    summary_json = {
        "summary": summary,
        "run_status": run_status,
        "command": command,
        "args": parsed.get("args", {}) or {},
        "checked_out_sha": head_sha,
        "started_at": started_at,
        "finished_at": finished_at,
    }

    # Ensure the orphan branch exists by writing the manifest first
    # (put_file_contents auto-creates the branch as orphan if missing).
    _retry_put(client, f"{log_dir}/manifest.json",
               json.dumps(manifest, indent=2).encode("utf-8"),
               f"manifest for run {issue_number}/{comment_id}",
               logs_branch)
    for path, gz_bytes, _info in chunks:
        _retry_put(client, f"{log_dir}/{path}", gz_bytes,
                   f"log chunk for {issue_number}/{comment_id}", logs_branch)
    _retry_put(client, f"{log_dir}/summary.json",
               json.dumps(summary_json, indent=2).encode("utf-8"),
               f"summary for {issue_number}/{comment_id}", logs_branch)

    # Step 8: write terminal envelope ------------------------------------
    terminal = dict(running_envelope)
    terminal["run_status"] = run_status
    terminal["run_finished_at"] = finished_at
    terminal["summary"] = summary
    terminal["log_manifest_branch"] = logs_branch
    terminal["log_manifest_path"] = f"{log_dir}/manifest.json"
    if error_kind is not None:
        terminal["error_kind"] = error_kind
    if error_detail is not None:
        terminal["error_detail"] = error_detail

    client.update_comment(comment_id, json.dumps(terminal, indent=2))

    return {
        "action": "ran",
        "command": command,
        "run_status": run_status,
        "summary": summary,
        "log_manifest_path": f"{log_dir}/manifest.json",
        "chunks": [c[0] for c in chunks],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_command_handler(command: str):
    """Import ``.agent/commands/<command>.py`` and return its ``run``."""
    module_name = command.replace("-", "_")
    # Determine the path to the commands directory relative to this file.
    here = os.path.dirname(os.path.abspath(__file__))
    cmd_dir = os.path.normpath(os.path.join(here, os.pardir, "commands"))
    cmd_path = os.path.join(cmd_dir, f"{module_name}.py")
    if not os.path.isfile(cmd_path):
        raise ImportError(f"no command module at {cmd_path}")
    # Use a unique cached module name so dataclass etc. work correctly.
    sys_name = f"_agent_command_{module_name}"
    if sys_name in sys.modules:
        mod = sys.modules[sys_name]
    else:
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location(sys_name, cmd_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not build spec for {cmd_path}")
        mod = module_from_spec(spec)
        sys.modules[sys_name] = mod
        spec.loader.exec_module(mod)
    if not hasattr(mod, "run"):
        raise ImportError(f"command module {module_name} has no run()")
    return mod.run


def _retry_sleep(seconds: float) -> None:
    """Backoff sleep helper. Indirected so tests can stub it out."""
    import time as _time
    _time.sleep(seconds)


def _retry_put(
    client: GitHubClient,
    path: str,
    content: bytes,
    message: str,
    branch: str,
    *,
    retries: int = 6,
) -> None:
    """Put a file with retry + jittered exponential backoff.

    ``put_file_contents`` re-fetches the branch HEAD on each call, so
    each retry sees a fresh ``head_sha``. The backoff between attempts
    spreads out concurrent writers so they don't all collide in the
    same sub-millisecond race window — discovered live during scenario
    02 (multi-subagent), where three handlers writing to ``_agent_runs``
    collided and the (then) no-backoff retry loop exhausted all three
    attempts before any of them could settle.

    Backoff schedule (no-jitter base): 0.5s, 1s, 2s, 4s, 8s, 16s — caps
    at 30s. Each delay is multiplied by a random factor in [0.5, 1.5)
    to spread out concurrent writers further.
    """
    import random as _random

    last_exc: Optional[BaseException] = None
    for attempt in range(retries):
        try:
            client.put_file_contents(path, content, message, branch)
            return
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt + 1 >= retries:
                break
            base = min(0.5 * (2 ** attempt), 30.0)
            jitter = _random.uniform(0.5, 1.5)
            _retry_sleep(base * jitter)
    if last_exc is not None:
        raise last_exc


def _write_parse_error(
    client: GitHubClient,
    comment_id: int,
    *,
    original_body: str,
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    started_at: str,
) -> dict[str, Any]:
    """Replace the comment body with a ``parse_error`` envelope (§5.2.4)."""
    finished_at = iso_now()
    body = {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "run_status": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
        "original_body_b64": b64_encode(original_body),
        "run_started_at": started_at,
        "run_finished_at": finished_at,
        "workflow_run_id": workflow_run_id,
        "agent_ack": None,
    }
    client.update_comment(comment_id, json.dumps(body, indent=2))
    return {
        "action": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def _write_terminal_error(
    *,
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    envelope: dict[str, Any],
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    run_started_at: str,
    cfg: dict[str, Any],
    repo_root: str,
) -> dict[str, Any]:
    """Write a terminal ``error`` envelope (e.g. branch_sha_mismatch)."""
    finished_at = iso_now()
    terminal = dict(envelope)
    terminal["run_status"] = "error"
    terminal["run_started_at"] = run_started_at
    terminal["run_finished_at"] = finished_at
    terminal["workflow_run_id"] = workflow_run_id
    terminal["error_kind"] = error_kind
    terminal["error_detail"] = error_detail
    terminal["summary"] = {"error_kind": error_kind, "error_detail": error_detail}
    client.update_comment(comment_id, json.dumps(terminal, indent=2))
    return {
        "action": "error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def main() -> int:
    """``batch-job-handler`` workflow entry point.

    Required environment variables:
      - ``ISSUE_NUMBER``       issue carrying the request comment
      - ``COMMENT_ID``         comment id holding the envelope
      - ``GH_TOKEN`` / ``GITHUB_TOKEN``  REST API token
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug
    Optional:
      - ``GITHUB_RUN_ID`` / ``WORKFLOW_RUN_ID``  workflow run id echoed
        into the running envelope (default ``0``)
      - ``GITHUB_WORKSPACE``   checkout root passed to command handlers

    On success exits 0; on uncaught exception prints to stderr and
    exits 1. Tests call :func:`run` directly with an in-memory client.
    """
    required = ["ISSUE_NUMBER", "COMMENT_ID", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    print(
        "handler: required env vars: "
        + ", ".join(required)
        + ". Optional: GITHUB_RUN_ID, GITHUB_WORKSPACE.",
        file=sys.stderr,
    )
    issue_number = os.environ.get("ISSUE_NUMBER")
    comment_id = os.environ.get("COMMENT_ID")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    missing = [
        name for name, val in (
            ("ISSUE_NUMBER", issue_number),
            ("COMMENT_ID", comment_id),
            ("GITHUB_TOKEN", token),
            ("GITHUB_REPOSITORY", repo_slug),
        ) if not val
    ]
    if missing:
        print(f"handler: missing env vars: {missing}", file=sys.stderr)
        return 1
    assert issue_number is not None and comment_id is not None
    assert token is not None and repo_slug is not None
    if "/" not in repo_slug:
        print(
            f"handler: GITHUB_REPOSITORY must be 'owner/repo', got: {repo_slug!r}",
            file=sys.stderr,
        )
        return 1
    owner, repo = repo_slug.split("/", 1)
    workflow_run_id_str = (
        os.environ.get("GITHUB_RUN_ID") or os.environ.get("WORKFLOW_RUN_ID") or "0"
    )
    try:
        workflow_run_id = int(workflow_run_id_str)
    except ValueError:
        workflow_run_id = 0
    workspace = os.environ.get("GITHUB_WORKSPACE")
    print(
        "handler: dispatching issue "
        f"#{issue_number} comment {comment_id}",
        file=sys.stderr,
    )
    try:
        # Imported lazily so this script remains usable even if requests
        # is missing (e.g. when only run() is invoked from tests).
        if __package__ in (None, ""):
            from rest_client import RestGitHubClient  # type: ignore[import-not-found]
        else:
            from .rest_client import RestGitHubClient
        client = RestGitHubClient(token=token, owner=owner, repo=repo)
        run(
            client,
            int(issue_number),
            int(comment_id),
            workflow_run_id=workflow_run_id,
            workspace=workspace,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"handler: uncaught exception: {exc!r}", file=sys.stderr)
        traceback.print_exc()
        # Self-diagnostic: post a comment on the originating issue with the
        # traceback, so MCP-only operators (who can't read workflow logs)
        # can see what went wrong. Wrapped in its own try/except so a
        # failure here can't mask the original exit code.
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                _post_debug_comment(
                    token=token,
                    owner=owner,
                    repo=repo,
                    issue_number=int(issue_number),
                    script="handler.py",
                    exc=exc,
                    extra_fields={
                        "comment": comment_id,
                        "workflow run": workflow_run_id,
                    },
                )
            except Exception as diag_exc:  # noqa: BLE001
                print(
                    f"handler: failed to post debug comment: {diag_exc!r}",
                    file=sys.stderr,
                )
        return 1
    return 0


def _post_debug_comment(
    *,
    token: str,
    owner: str,
    repo: str,
    issue_number: int,
    script: str,
    exc: BaseException,
    extra_fields: Optional[dict[str, Any]] = None,
) -> None:
    """Post a self-diagnostic comment with traceback to the given issue.

    Uses ``requests.post`` directly to avoid depending on any code path
    that might itself be the source of the bug being diagnosed. Secrets
    are never echoed; the env-var summary only reports presence/absence.
    """
    import requests  # local import: keeps run() importable without requests

    # Summarise env vars without leaking secrets.
    secret_names = {"GH_TOKEN", "GITHUB_TOKEN"}
    relevant = [
        "ISSUE_NUMBER", "COMMENT_ID", "PR_NUMBER",
        "GH_TOKEN", "GITHUB_TOKEN", "GITHUB_REPOSITORY",
        "GITHUB_RUN_ID", "WORKFLOW_RUN_ID", "GITHUB_WORKSPACE",
        "AGENT_LOGIN", "AGENT_TASK_LABEL",
    ]
    env_lines = []
    for name in relevant:
        val = os.environ.get(name)
        if name in secret_names:
            env_lines.append(f"  - {name}: {'set' if val else 'unset'}")
        elif val is not None:
            env_lines.append(f"  - {name}: {val!r}")
        else:
            env_lines.append(f"  - {name}: unset")

    fields_lines = [f"- script: `{script}`", f"- issue: #{issue_number}"]
    for k, v in (extra_fields or {}).items():
        fields_lines.append(f"- {k}: {v}")
    fields_lines.append(f"- python: {sys.version.split()[0]}")

    debug_body = (
        "**handler self-diagnostic — uncaught exception**\n\n"
        + "\n".join(fields_lines)
        + "\n\n"
        + f"```\n{exc!r}\n```\n\n"
        + "<details><summary>Traceback</summary>\n\n"
        + f"```\n{traceback.format_exc()}```\n\n"
        + "</details>\n\n"
        + "<details><summary>Environment</summary>\n\n"
        + "\n".join(env_lines)
        + "\n\n</details>\n"
    )

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.post(url, headers=headers, json={"body": debug_body}, timeout=15)
    # Don't raise — caller wraps us anyway; but record non-2xx status.
    if resp.status_code >= 300:
        print(
            f"handler: debug comment POST returned {resp.status_code}: {resp.text[:200]!r}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(main())

````

### .claude/skills/batch-job/templates/agent/scripts/requirements.txt

```text
jsonschema>=4.21.0
PyYAML>=6.0
requests>=2.31.0

```

### .claude/skills/batch-job/templates/agent/scripts/rest_client.py

```text
"""Live REST-backed implementation of the :class:`GitHubClient` Protocol.

This is the workflow side of the agent-job protocol: it is invoked from
GitHub Actions runners using ``GITHUB_TOKEN`` and talks to the
GitHub REST API.

The implementation focuses on the operations the workflow scripts need:

- Issues / labels / lock
- Comments (list, get, add, update, delete)
- Files (read, write — including orphan-branch creation for ``_agent_runs``)
- Branches (head SHA lookup, delete)
- Pull requests (create, get)

It also performs:

- Bearer-token auth with the standard GitHub headers.
- Bounded retry-with-backoff for 5xx and rate-limited 403 responses.
- The blob/tree/commit/ref dance required to commit to a fresh
  orphan branch (the Contents API cannot create branches).
"""

from __future__ import annotations

import base64
import time
from typing import Any, Optional

import requests


_DEFAULT_BASE_URL = "https://api.github.com"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 5
_BACKOFF_SECONDS = (1.0, 2.0, 4.0, 8.0, 16.0)


class RestGitHubClient:
    """REST implementation of the protocol used by the workflow scripts."""

    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        session: Optional[requests.Session] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        sleep: Any = time.sleep,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        if not owner or not repo:
            raise ValueError("owner and repo are required")
        self._token = token
        self._owner = owner
        self._repo = repo
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._sleep = sleep

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @property
    def _repo_path(self) -> str:
        return f"/repos/{self._owner}/{self._repo}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-job-protocol-poc",
        }

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self._base_url + path

    def _is_rate_limited(self, resp: requests.Response) -> bool:
        if resp.status_code != 403:
            return False
        # Primary rate limit signalled by remaining=0.
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining == "0":
            return True
        # Secondary rate limit / abuse detection signalled by Retry-After.
        if resp.headers.get("Retry-After"):
            return True
        # Some endpoints simply put it in the body.
        try:
            j = resp.json()
        except ValueError:
            return False
        msg = (j.get("message") or "").lower() if isinstance(j, dict) else ""
        return "rate limit" in msg or "abuse" in msg or "secondary rate" in msg

    def _rate_limit_sleep(self, resp: requests.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        reset = resp.headers.get("X-RateLimit-Reset")
        if reset:
            try:
                delta = float(reset) - time.time()
                if delta > 0:
                    # Cap the backoff so a clock-skew or far-future reset
                    # doesn't stall the runner forever.
                    return min(delta, 60.0)
            except ValueError:
                pass
        # Fall back to exponential backoff.
        return _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        allow_404: bool = False,
    ) -> requests.Response:
        """Perform an HTTP request with retry on 5xx and rate-limited 403.

        Retries up to ``_MAX_RETRIES`` times. 4xx (other than rate-limited
        403) raise immediately via ``raise_for_status``. When ``allow_404``
        is True, a 404 response is returned without raising.
        """
        url = self._url(path)
        last_resp: Optional[requests.Response] = None
        for attempt in range(_MAX_RETRIES):
            resp = self._session.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=params,
                timeout=self._timeout,
            )
            last_resp = resp
            if 200 <= resp.status_code < 300:
                return resp
            if resp.status_code == 404 and allow_404:
                return resp
            # Deterministic client errors: do NOT retry.
            if resp.status_code in (400, 401, 404, 405, 409, 410, 422):
                resp.raise_for_status()
                return resp  # unreachable; for mypy
            # Rate-limited 403: sleep then retry.
            if resp.status_code == 403 and self._is_rate_limited(resp):
                if attempt < _MAX_RETRIES - 1:
                    self._sleep(self._rate_limit_sleep(resp, attempt))
                    continue
                resp.raise_for_status()
                return resp
            # Other 4xx (e.g. plain 403 forbidden) — don't retry.
            if 400 <= resp.status_code < 500:
                resp.raise_for_status()
                return resp
            # 5xx — retry with exponential backoff.
            if attempt < _MAX_RETRIES - 1:
                self._sleep(_BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)])
                continue
            resp.raise_for_status()
            return resp
        assert last_resp is not None
        last_resp.raise_for_status()
        return last_resp  # unreachable

    # ------------------------------------------------------------------
    # Issue API
    # ------------------------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/issues/{number}")
        return resp.json()

    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        if labels is not None:
            payload["labels"] = list(labels)
        resp = self._request("PATCH", f"{self._repo_path}/issues/{number}", json=payload)
        return resp.json()

    def lock_issue(self, number: int) -> None:
        # PUT /repos/{owner}/{repo}/issues/{n}/lock returns 204 No Content.
        self._request("PUT", f"{self._repo_path}/issues/{number}/lock", json={})

    def add_label(self, number: int, label: str) -> None:
        self._request(
            "POST",
            f"{self._repo_path}/issues/{number}/labels",
            json={"labels": [label]},
        )

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = list(labels)
        resp = self._request("POST", f"{self._repo_path}/issues", json=payload)
        return resp.json()

    # ------------------------------------------------------------------
    # Comment API
    # ------------------------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]:
        # Paginate by following the Link header's ``rel="next"``.
        out: list[dict[str, Any]] = []
        path = f"{self._repo_path}/issues/{issue_number}/comments"
        params: Optional[dict[str, Any]] = {"per_page": 100}
        while True:
            resp = self._request("GET", path, params=params)
            page = resp.json() or []
            out.extend(page)
            next_url = _next_link(resp.headers.get("Link", ""))
            if not next_url:
                break
            path = next_url
            params = None  # the URL already contains the query string
        return out

    def get_comment(self, comment_id: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/issues/comments/{comment_id}")
        return resp.json()

    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        resp = self._request(
            "PATCH",
            f"{self._repo_path}/issues/comments/{comment_id}",
            json={"body": body},
        )
        return resp.json()

    def delete_comment(self, comment_id: int) -> None:
        self._request("DELETE", f"{self._repo_path}/issues/comments/{comment_id}")

    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        resp = self._request(
            "POST",
            f"{self._repo_path}/issues/{issue_number}/comments",
            json={"body": body},
        )
        return resp.json()

    # ------------------------------------------------------------------
    # File / branch operations
    # ------------------------------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]:
        """Return the file contents at ``ref`` (utf-8 text or base64).

        Returns ``None`` on 404. Mirrors :class:`InMemoryGitHubClient`:
        attempts utf-8 decoding; returns base64 on failure.
        """
        resp = self._request(
            "GET",
            f"{self._repo_path}/contents/{path}",
            params={"ref": ref},
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        if isinstance(body, list):
            # ``path`` resolved to a directory — treat like "no file".
            return None
        encoding = body.get("encoding")
        content = body.get("content") or ""
        if encoding == "base64":
            try:
                raw = base64.b64decode(content)
            except (ValueError, base64.binascii.Error):  # type: ignore[attr-defined]
                return content
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(raw).decode("ascii")
        # Unknown encoding: return as-is.
        return content if isinstance(content, str) else None

    def _get_file_sha(self, path: str, branch: str) -> Optional[str]:
        """Return the blob sha of ``path`` on ``branch`` if it exists."""
        resp = self._request(
            "GET",
            f"{self._repo_path}/contents/{path}",
            params={"ref": branch},
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        if isinstance(body, list):
            return None
        sha = body.get("sha")
        return sha if isinstance(sha, str) else None

    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        """Commit a file to ``branch``.

        If ``branch`` does not exist, create it as an orphan via the Git
        Database API (blob/tree/commit with empty parents/ref). If the
        branch exists, prefer the simple Contents API path; if that fails
        we fall back to the Git Database API for the next-commit case
        (blob/tree-with-base/commit-with-parent/patch-ref) so additional
        files on ``_agent_runs`` accumulate into the tree correctly.
        """
        head_sha = self.get_branch_head_sha(branch)
        if head_sha is None:
            return self._create_orphan_commit(path, content_bytes, message, branch)
        # Branch exists — use the Git Database API so the tree is
        # explicitly built from the previous commit, preserving existing
        # files (Contents API would also do this implicitly, but the GDB
        # path is what we tested for orphan-branch follow-ups).
        return self._append_commit(path, content_bytes, message, branch, head_sha)

    def _create_orphan_commit(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        blob_sha = self._create_blob(content_bytes)
        tree_sha = self._create_tree(
            [{"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}],
            base_tree=None,
        )
        commit_sha = self._create_commit(message, tree_sha, parents=[])
        # Create the ref; raises if it already exists.
        self._request(
            "POST",
            f"{self._repo_path}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": commit_sha},
        )
        return {
            "path": path,
            "branch": branch,
            "commit": {"sha": commit_sha, "message": message},
            "size": len(content_bytes),
        }

    def _append_commit(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
        parent_sha: str,
    ) -> dict[str, Any]:
        # Get the parent commit's tree sha.
        resp = self._request("GET", f"{self._repo_path}/git/commits/{parent_sha}")
        parent_tree_sha = resp.json()["tree"]["sha"]
        blob_sha = self._create_blob(content_bytes)
        tree_sha = self._create_tree(
            [{"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}],
            base_tree=parent_tree_sha,
        )
        commit_sha = self._create_commit(message, tree_sha, parents=[parent_sha])
        self._request(
            "PATCH",
            f"{self._repo_path}/git/refs/heads/{branch}",
            json={"sha": commit_sha},
        )
        return {
            "path": path,
            "branch": branch,
            "commit": {"sha": commit_sha, "message": message},
            "size": len(content_bytes),
        }

    def _create_blob(self, content_bytes: bytes) -> str:
        b64 = base64.b64encode(content_bytes).decode("ascii")
        resp = self._request(
            "POST",
            f"{self._repo_path}/git/blobs",
            json={"content": b64, "encoding": "base64"},
        )
        return resp.json()["sha"]

    def _create_tree(
        self,
        entries: list[dict[str, Any]],
        *,
        base_tree: Optional[str],
    ) -> str:
        payload: dict[str, Any] = {"tree": entries}
        if base_tree is not None:
            payload["base_tree"] = base_tree
        resp = self._request("POST", f"{self._repo_path}/git/trees", json=payload)
        return resp.json()["sha"]

    def _create_commit(
        self,
        message: str,
        tree_sha: str,
        *,
        parents: list[str],
    ) -> str:
        payload: dict[str, Any] = {
            "message": message,
            "tree": tree_sha,
            "parents": list(parents),
        }
        resp = self._request("POST", f"{self._repo_path}/git/commits", json=payload)
        return resp.json()["sha"]

    def get_branch_head_sha(self, branch: str) -> Optional[str]:
        resp = self._request(
            "GET",
            f"{self._repo_path}/git/refs/heads/{branch}",
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        # The refs endpoint returns an object for a single match; some
        # variations of the API return a list when the prefix matched
        # multiple refs. Defensive parsing handles both.
        if isinstance(body, list):
            for entry in body:
                if entry.get("ref") == f"refs/heads/{branch}":
                    return entry.get("object", {}).get("sha")
            return None
        obj = body.get("object") or {}
        sha = obj.get("sha")
        return sha if isinstance(sha, str) else None

    def delete_branch(self, name: str) -> None:
        # 404 is treated as success (idempotent), matching the in-memory client.
        resp = self._request(
            "DELETE",
            f"{self._repo_path}/git/refs/heads/{name}",
            allow_404=True,
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()

    def list_branches(self) -> list[dict[str, Any]]:
        """List branches in the repo, paginated.

        Returns a list of ``{"name": str, "sha": str, "protected": bool}``
        entries built from the REST ``GET /repos/{owner}/{repo}/branches``
        response. Pagination follows the ``Link: rel="next"`` header.
        """
        out: list[dict[str, Any]] = []
        path = f"{self._repo_path}/branches"
        params: Optional[dict[str, Any]] = {"per_page": 100}
        while True:
            resp = self._request("GET", path, params=params)
            page = resp.json() or []
            for b in page:
                if not isinstance(b, dict):
                    continue
                commit = b.get("commit") or {}
                out.append({
                    "name": b.get("name"),
                    "sha": commit.get("sha"),
                    "protected": bool(b.get("protected", False)),
                })
            next_url = _next_link(resp.headers.get("Link", ""))
            if not next_url:
                break
            path = next_url
            params = None
        return out

    # ------------------------------------------------------------------
    # PR API
    # ------------------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]:
        resp = self._request(
            "POST",
            f"{self._repo_path}/pulls",
            json={"title": title, "head": head, "base": base, "body": body},
        )
        return resp.json()

    def get_pull_request(self, number: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/pulls/{number}")
        return resp.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_link(link_header: str) -> Optional[str]:
    """Parse a ``Link`` header and return the URL with ``rel="next"``."""
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) < 2:
            continue
        url_part = section[0].strip()
        if not (url_part.startswith("<") and url_part.endswith(">")):
            continue
        rel = None
        for s in section[1:]:
            s = s.strip()
            if s.startswith("rel="):
                rel = s.split("=", 1)[1].strip().strip('"')
                break
        if rel == "next":
            return url_part[1:-1]
    return None


__all__ = ["RestGitHubClient"]

```

### .claude/skills/batch-job/templates/github/workflows/batch-job-handler.yml

```text
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
      github.event.comment.user.login == (vars.AGENT_LOGIN || 'jonathanmanton')
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - name: marker-start
        run: |
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d '{"body":"<!-- workflow-marker -->\n[handler-start] run=${{ github.run_id }} comment=${{ github.event.comment.id }}"}' \
            > /tmp/marker-start.json || true
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r .agent/scripts/requirements.txt
      - id: handler
        run: python .agent/scripts/handler.py 2>&1 | tee /tmp/handler.log
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          COMMENT_ID: ${{ github.event.comment.id }}
          WORKFLOW_RUN_ID: ${{ github.run_id }}
          AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}
      - name: marker-end
        if: always()
        run: |
          conclusion="${{ steps.handler.conclusion }}"
          # Trim and base64 just to embed cleanly; readers can decode
          tail_b64=$(tail -c 4000 /tmp/handler.log 2>/dev/null | base64 -w0 || echo "")
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d "{\"body\":\"<!-- workflow-marker -->\n[handler-end] run=${{ github.run_id }} comment=${{ github.event.comment.id }} conclusion=${conclusion}\n\n<details><summary>last 4KB of stdout/stderr (base64)</summary>\n\n\`\`\`\n${tail_b64}\n\`\`\`\n\n</details>\"}" \
            > /tmp/marker-end.json || true

```

### .claude/skills/composition-guide/README.md

```text
This is the `composition-guide` reference skill. SKILL.md-only.
Documentation for composing batch-job + task-dag + orchestrate-issue
manually. No install actions.

```

### .claude/skills/composition-guide/SKILL.md

````text
---
name: composition-guide
description: |
  Reference guide for composing batch-job, task-dag, and
  orchestrate-issue without using the all-in-one orchestrator. Use
  when you want to wire the agent-job protocol primitives manually,
  drive a custom primary-agent loop, or understand the patterns
  available. Documentation only — no install actions.
allowed-tools:
  - Read
---

# composition-guide

> I'm a reference skill; I don't install anything. If you want the
> protocol installed, invoke `batch-job`, `task-dag`,
> `orchestrate-issue`, or `onboarding`.

This skill documents how to **compose** the agent-job protocol
primitives (`batch-job`, `task-dag`) into custom primary-agent loops
for users who want finer control than the bundled `orchestrate-issue`
skill offers. It is documentation only: there are no templates, no
install logic, and no side effects.

Patterns described here mirror what `orchestrate-issue` does
internally, but exposed as building blocks you can reorder, omit, or
specialise. If you simply want the default end-to-end loop, invoke
`orchestrate-issue` instead.

## 1. When to use each skill

The agent-job package exposes four implementation skills plus this
reference. Pick the one that matches your level of involvement:

| Skill | Use when |
|---|---|
| `batch-job` | You need to dispatch a single workflow command (tests, build, deploy) against an existing branch + commit and wait for terminal status. One-shot. No issue claim, no PR, no merge. |
| `task-dag` | You own an issue end-to-end as a DAG node: claim it, plan subagents, merge their branches in plan order, schedule successors. Does **not** dispatch batch jobs itself. |
| `orchestrate-issue` | You want the entire primary-agent loop in one invocation: claim → plan → fan out → batch-job per subagent → merge → PR. Highest abstraction; least customisable. |
| `onboarding` | You want a guided interview to discover how the protocol should integrate with the target repo's existing workflow. Produces a recommendations doc; can optionally apply edits. |
| `composition-guide` (this) | You want the **primitives**, not the orchestrator. Read this to learn how to wire `batch-job` + `task-dag` yourself. |

### Decision tree

```
Do you have one issue to ship end-to-end with parallel subagents?
├── Yes → use orchestrate-issue
└── No
    ├── Do you have one branch+command to run? → use batch-job
    ├── Do you need to claim an issue but drive the loop yourself? → use task-dag
    ├── Are you onboarding a new repo to the protocol? → use onboarding
    └── Are you composing several primitives in a custom shape? → read this guide
```

### What this guide does NOT cover

- The protocol envelope schemas. See POC `SPEC.md` §9 (batch-job) and
  §10 (task-dag) for canonical wire-format detail.
- Installing templates. See each implementation skill's SKILL.md for
  self-install behavior.
- General Claude Code subagent dispatch. See the
  `parallel-subagent-fanout` skill in `software-factory` for the
  generic version of the fanout pattern below.

## 2. Pattern — single-subagent linear loop

The simplest composition. One primary agent, one issue, one branch,
one or more sequential batch-jobs. No fanout. No subagents.

### Shape

```
claim (task-dag)
  └── plan (task-dag)         # but you ignore subagent_layout
       └── for each step:
              edit code        # locally
              commit + push    # to feature branch
              batch-job        # run the relevant command
              ack received
       └── merge nothing       # there are no sub-branches
       └── open PR             # manually via mcp__github__create_pull_request
       └── (optional) schedule successors (task-dag)
```

### When to use

- The task is small enough that splitting into subagents would add
  more orchestration cost than it saves.
- The work is inherently serial (each step depends on the last).
- You want maximum visibility into each batch-job, one at a time.
- You're prototyping a new command and want to drive each invocation
  by hand.

### When NOT to use

- Tasks where files-touched are disjoint and could run in parallel.
- Long-running e2e suites where waiting serially burns wall clock.

### Variant: linear loop with multiple commands

You can dispatch successive batch-jobs against the same branch as
long as each step's commit_sha is the HEAD of the branch when the job
runs. Typical sequence: `lint` → `test` → `build` → `deploy`.

## 3. Pattern — parallel-subagent fanout

The pattern that `orchestrate-issue` implements internally. One
primary agent dispatches N subagents in parallel; each subagent owns
one sub-branch and runs its own batch-job; the primary collects,
merges in plan order, and opens the PR.

### Shape

```
claim (task-dag)
  └── plan (task-dag) → subagent_layout with N subtasks
       └── write .agent/runs/<run_id>/state.json
       └── create sub-branches: <feature>--sub-01, --sub-02, ...
       └── dispatch N subagents in a SINGLE message
             ├── each subagent gets isolation: "worktree"
             ├── each subagent invokes batch-job on its sub-branch
             └── each subagent reports back to the primary
       └── collect results, update state.json
       └── merge sub-branches into feature branch in PLAN ORDER
       └── open PR via mcp__github__create_pull_request
       └── (optional) schedule successors
```

### Critical rules

- **Single message dispatch.** The Claude Code harness only
  parallelises Agent calls made within one message. Spread the calls
  across messages and they will run serially.
- **Worktree isolation.** Pass `isolation: "worktree"` on every Agent
  call. Without it, concurrent subagents race on `git checkout` and
  contaminate each other's working trees.
- **Double-dash branch separator.** Use `feature--sub-01`, not
  `feature/sub-01`. Single slash collides with refspec parsing in
  some downstream tools (see POC SPEC.md §6).
- **Plan-order merge.** Merge in the order subtasks were planned,
  never in completion order. Completion order hides integration bugs
  whose surface is sensitive to merge sequence.
- **Disjoint files_touched.** The plan must guarantee subagents
  touch disjoint file paths. Overlap causes spurious merge conflicts
  and silently lost work.

### When to use

- N independent subtasks whose files_touched are disjoint.
- Wall-clock matters: parallelism cuts elapsed time by ~N.
- You can afford the dispatch overhead (Agent fanout has fixed cost).

### Wave limiting

If N is large, cap concurrency with `max_parallel` (typically 4). The
primary dispatches waves of `max_parallel` subagents, waits for the
wave to complete, then dispatches the next. See `orchestrate-issue`
Phase 5.

## 4. Pattern — pipelined long-running work

Many concurrent batch-jobs against one or more issues, with periodic
heartbeats and result reconciliation as jobs finish. Suitable for
e2e test suites, parallel deploys to multiple environments, or
fan-out builds across many platforms.

### Shape

```
for each environment / platform / target:
   dispatch batch-job (do NOT wait inline)
       └── record { comment_id, target } in a pending-jobs table
loop:
   for each pending job:
       poll its request comment
       if terminal:
            validate summary
            ack
            mark complete in pending-jobs
            record outcome
   call heartbeat() on the parent issue            # throttled
   sleep poll_interval
exit when pending-jobs is empty
```

### When to use

- Many independent jobs that all need to finish before the primary
  agent can proceed.
- Wall-clock dominates over per-job orchestration cost.
- Each job's outcome is independent — no inter-job dependencies.

### Critical rules

- **Heartbeat throttling.** Call `task-dag.heartbeat()` once per poll
  cycle, but the helper itself enforces `heartbeat_min_interval_seconds`.
  Don't write your own loop that pounds the API.
- **Tolerate trailers.** When re-reading comment bodies, use
  `json.JSONDecoder().raw_decode` rather than strict `json.loads` so
  the Claude Code MCP comment trailer doesn't cause spurious parse
  failures.
- **Restart safety.** Persist the pending-jobs table to
  `.agent/runs/<run_id>/state.json` after every state change. A
  restart should resume polling from the saved table, not redispatch.

### Variant: cross-issue pipeline

You can pipeline jobs across multiple issues by keeping per-issue
state in `.agent/runs/<run_id>/issues/<n>/state.json`. The
heartbeat call must target the specific issue that owns each job.

## 5. State management

Three layers of state live in the protocol; know which layer carries
which fact so you don't duplicate or contradict.

### Layer 1 — issue body (`agent-meta`)

Per-issue state owned by `task-dag`:

- `status` — `null` | `working` | `finished` | `abandoned`
- `agent_id` — current owner's identity
- `status_ts` — last heartbeat
- `feature_branch` — the branch this DAG node owns
- `instructions_inline` / `instructions_path` — work brief

Mutate via `mcp__github__issue_write`. Never mutate from inside
`batch-job` — that's `task-dag`'s job.

### Layer 2 — comment envelopes

Per-job state owned by `batch-job`:

- Request envelope (initial comment body): command, args, branch,
  commit_sha, subagent_id.
- Terminal state written by the runner (when the runner edits the
  comment): `run_status`, `summary`, `error_kind`.
- Ack envelope: `kind: "agent-ack"` follow-up comment OR inline edit
  to `agent_ack: "finished"`.

These envelopes form an append-only audit trail. Don't mutate the
comment body after ack.

### Layer 3 — run state (`.agent/runs/<run_id>/state.json`)

Per-run state for fanout / pipelined patterns. Owned by the primary
agent; not part of the wire protocol. Schema is flexible but commonly
includes:

```json
{
  "run_id": "20260514-055717",
  "issue_number": 42,
  "feature_branch": "agent/42-foo",
  "subtasks": [
    {"id": "sub-01", "branch": "agent/42-foo--sub-01",
     "status": "pending|dispatched|merged|failed",
     "request_comment_id": null, "ack_comment_id": null}
  ]
}
```

Commit and push state.json on the feature branch after each update so
a restart picks up exactly where you left off.

### Restart recovery

On restart:

1. Read `state.json` for the run.
2. For each subtask with `request_comment_id != null` and
   `ack_comment_id == null`, re-fetch the comment; if terminal, ack
   and update state.
3. For each subtask with `status == pending`, redispatch.
4. Resume the loop from the earliest incomplete phase.

Never assume a phase succeeded just because the last log line
mentions it. Always reconcile against the on-disk + on-GitHub state.

## 6. Common pitfalls

These are the failure modes seen most often when composing the
primitives. The orchestrator skill internalises avoidance of all of
them; if you compose by hand, watch for each.

| Pitfall | Symptom | Fix |
|---|---|---|
| Merging in completion order | Integration bugs that only appear when sub-02 lands before sub-01 | Always merge in plan order. Persist plan-order in state.json. |
| Single-slash branch separator | Refspec ambiguity, some tools strip the prefix | Use `feature--sub-01`, double-dash. See POC SPEC §6. |
| Dispatching subagents without `isolation: "worktree"` | Concurrent subagents corrupt each other's branches via shared CWD | Always pass `isolation: "worktree"` on Agent calls in fanout |
| Strict JSON parse on comment bodies | Spurious `ParseError` when the MCP trailer is appended | Use `json.JSONDecoder().raw_decode` to tolerate trailing prose |
| Dispatching subagents across multiple messages | Subagents run serially instead of in parallel | Place all Agent calls in **one** message |
| Forgetting to push state.json | Restart starts from scratch instead of resuming | Commit + push state.json after every meaningful state change |
| Calling `heartbeat()` from a hot poll loop | Rate-limit collisions | Use the throttled helper; let it skip if interval not elapsed |
| Writing `status: finished` before the PR opens | Issue closed without a real PR; lock-on-close runs prematurely | Only finalise `agent-meta` after `mcp__github__create_pull_request` returns success |
| Silent merge with `theirs` strategy | Lost edits from earlier subagents | Default `conflict_strategy: "fail"` and surface conflicts to the user |
| Re-using a subagent's branch across runs | Stale commits leak into a new run | Always create sub-branches fresh from the feature-branch tip per run |

## 7. Code snippets

The snippets below are illustrative, not runnable. They use a
pseudo-Python API that matches the shape of the skills' helpers; the
real call signatures are in each skill's SKILL.md.

### 7.1 Linear loop (Pattern 2)

```python
from agent_job import task_dag, batch_job

claimed = task_dag.claim(agent_id=AGENT_ID, agent_login=ME)
if not claimed:
    return {"reason": "no_work"}

issue, meta = claimed["issue"], claimed["meta"]
plan = task_dag.plan(issue_number=issue["number"], agent_login=ME)
brief = plan["brief"]

# Drive the work serially.
for step in derive_steps_from(brief):
    edit_files(step.files)
    sha = git_commit_and_push(meta["feature_branch"])
    result = batch_job.run(
        issue_number=issue["number"],
        command=step.command,
        args=step.args,
        branch=meta["feature_branch"],
        commit_sha=sha,
        subagent_id="primary",
        agent_id=AGENT_ID,
        heartbeat=task_dag.heartbeat_for(issue["number"]),
    )
    assert result["summary"]["status"] == "ok"

pr = mcp_github.create_pull_request(
    base=meta["base_branch"],
    head=meta["feature_branch"],
    title=f"#{issue['number']}: {issue['title']}",
    body=build_pr_body(results),
)
task_dag.finalise(issue["number"], status="finished")
```

### 7.2 Parallel fanout (Pattern 3)

```python
from agent_job import task_dag

claimed = task_dag.claim(agent_id=AGENT_ID, agent_login=ME)
plan = task_dag.plan(issue_number=claimed["issue"]["number"], agent_login=ME)
layout = plan["subagent_layout"]  # list of subtasks with disjoint files_touched

run_id = utc_now_compact()
state = init_state_json(run_id, claimed, layout)
write_and_push_state(state)

# Create sub-branches.
for sub in layout:
    git_create_branch(sub["branch"], from_ref=claimed["meta"]["feature_branch"])

# Dispatch ALL subagents in ONE message; each gets isolation: "worktree".
agent_calls = [
    AgentCall(
        subagent_type="general-purpose",
        isolation="worktree",
        prompt=render_brief(sub, run_id=run_id),
    )
    for sub in layout
]
results = dispatch_in_single_message(agent_calls)   # critical: one message

# Collect, persist, then merge in PLAN order (not completion order).
for sub, result in zip(layout, results):
    update_state(state, sub["id"], result)
write_and_push_state(state)

for sub in layout:                                  # plan order
    if state["subtasks"][sub["id"]]["status"] == "dispatched_ok":
        git_merge(into=claimed["meta"]["feature_branch"],
                  from_=sub["branch"], strategy="fail-on-conflict")
        git_push(claimed["meta"]["feature_branch"])

open_pr_and_finalise(claimed, state)
```

### 7.3 Pipelined long-running jobs (Pattern 4)

```python
from agent_job import task_dag, batch_job

# Fire off all jobs concurrently; do NOT wait inline.
pending = []
for target in TARGETS:
    comment_id = batch_job.submit_only(
        issue_number=ISSUE_N,
        command="deploy",
        args={"target": target},
        branch=BRANCH, commit_sha=SHA,
        subagent_id="primary", agent_id=AGENT_ID,
    )
    pending.append({"comment_id": comment_id, "target": target,
                    "status": "submitted"})

write_state({"run_id": RUN_ID, "pending": pending})

heartbeat = task_dag.heartbeat_for(ISSUE_N)         # throttled internally

while any(p["status"] == "submitted" for p in pending):
    for job in pending:
        if job["status"] != "submitted":
            continue
        envelope = batch_job.peek(job["comment_id"])
        if envelope["run_status"] in TERMINAL_STATES:
            batch_job.validate_and_ack(envelope)
            job["status"] = "complete"
            job["summary"] = envelope["summary"]
    write_state({"run_id": RUN_ID, "pending": pending})
    heartbeat()                                     # throttled
    sleep(POLL_INTERVAL)

reconcile_outcomes(pending)
```

### 7.4 Restart-safe resume (any pattern)

```python
state = read_state_or_none(RUN_ID)
if state is None:
    state = bootstrap_fresh_state()
    write_and_push_state(state)
else:
    # Reconcile: any subtask with request_comment_id but no
    # ack_comment_id may have completed while we were down.
    for sub in state["subtasks"]:
        if sub["request_comment_id"] and not sub["ack_comment_id"]:
            envelope = batch_job.peek(sub["request_comment_id"])
            if envelope["run_status"] in TERMINAL_STATES:
                batch_job.validate_and_ack(envelope)
                sub["ack_comment_id"] = envelope["ack_comment_id"]
                sub["status"] = "dispatched_ok"
    write_and_push_state(state)

# Continue from the earliest incomplete phase.
resume_from_state(state)
```

### 7.5 Tolerant comment-envelope parse

```python
import json

def parse_envelope(body: str) -> dict:
    """Parse a batch-job comment body, tolerating MCP trailer prose."""
    decoder = json.JSONDecoder()
    try:
        obj, _idx = decoder.raw_decode(body.lstrip())
    except json.JSONDecodeError as e:
        raise ParseErrorTerminal(
            f"could not decode envelope prefix: {e}"
        ) from e
    return obj
```

## 8. Cross-references

### Sibling skills in this package

- [`batch-job`](../batch-job/SKILL.md) — one-shot batch-job submission,
  poll, ack. The execution primitive used by Patterns 2-4.
- [`task-dag`](../task-dag/SKILL.md) — claim, plan, merge, schedule
  successors. The ownership primitive used by Patterns 2-3.
- [`orchestrate-issue`](../orchestrate-issue/SKILL.md) — end-to-end
  primary loop. Implements Pattern 3 (parallel fanout) as a single
  invocation.
- [`onboarding`](../onboarding/SKILL.md) — interview-based discovery of
  an existing repo's workflow; recommends how to integrate the
  protocol.

### Protocol-level references

- POC `SPEC.md` §9 — canonical batch-job wire protocol: request
  envelope, terminal states, ack modes, schemas.
- POC `SPEC.md` §10 — canonical task-dag skill spec: claim handshake,
  plan output, merge order, schedule_successors.
- POC `SPEC.md` §6 — branching model and double-dash separator
  convention.
- POC `SPEC.md` §4.1 — issue state machine.
- POC `SPEC.md` §10.4 — restart recovery semantics.

### External patterns

- `software-factory/.claude/skills/parallel-subagent-fanout/SKILL.md` —
  the generic parallel-subagent-fanout pattern. Pattern 3 above is the
  agent-job-protocol-specialised version.
- `software-factory/.claude/skills/subagent-prompting/SKILL.md` —
  9-section subagent brief template used in Phase 5 of fanout.

---

Version: 1.0.0
Protocol-version: 1
Last-synced-from-POC: 2026-05-14

````

### docs/skills/composition-guide/SPEC.md

````text
# SPEC — composition-guide skill

Status: design-stage
Audience: implementers of the skill in the new `pipeline-ai-sandbox` repo

## Purpose

Reference skill that documents how to **compose** `batch-job`,
`task-dag`, and `orchestrate-issue` for users who prefer the
primitives over the all-in-one orchestrator. The skill carries no
templates and no install logic — it is **documentation only**.

It exists because users who want fine control should be able to
discover composition patterns via the same skill-tool mechanism they
use for everything else.

## Trigger conditions

The skill matches when:

- "How do I compose the agent-job skills?"
- "Show me how to wire batch-job + task-dag manually"
- "I want to drive the primary loop myself without orchestrate-issue"
- "/composition-guide"

## Inputs

None. The skill renders documentation.

## Outputs

The skill's response is the entire content of `SKILL.md` rendered as
guidance. There are no file outputs.

## Procedure

The skill's SKILL.md contains the following sections:

1. **When to use each skill**
   - `batch-job` for one-shot job submission
   - `task-dag` for issue-as-DAG-node ownership
   - `orchestrate-issue` for end-to-end primary loop
   - `composition-guide` (this skill) for when you want the primitives

2. **Pattern: single-subagent linear loop**
   - Claim → plan → loop: edit code → commit → batch-job → ack → repeat → merge → PR
   - When to use: small tasks, single agent, no parallelism

3. **Pattern: parallel-subagent fanout**
   - Claim → plan → branch out → dispatch N subagents → each runs batch-job on its sub-branch → collect → merge in plan order → PR
   - When to use: independent subtasks, files-touched don't overlap
   - Mirrors the parallel-subagent-fanout pattern from
     `software-factory/.claude/skills/parallel-subagent-fanout/SKILL.md`,
     specialised to the agent-job protocol.

4. **Pattern: pipelined long-running work**
   - Dispatch many batch-jobs concurrently across one or more issues
   - Periodic heartbeats; reconcile results as they come in
   - When to use: e2e test suites, parallel deploys

5. **State management**
   - Where state lives (`.agent/runs/<run_id>/state.json` for fanout, agent-meta for issue state, comment envelopes for job state)
   - Restart recovery: re-read state, resume from earliest incomplete phase
   - Heartbeat throttling

6. **Common pitfalls**
   - Don't merge in completion order
   - Use double-dash branch separator
   - Always isolation=worktree when dispatching parallel subagents
   - MCP comment trailer tolerance (use `raw_decode`, not strict parse)

7. **Code snippets**
   - 3-5 short Python or pseudocode examples showing each pattern.

8. **Cross-references**
   - Link to each other skill's SKILL.md.
   - Link to POC's `SPEC.md` (§9 batch-job, §10 task-dag) for protocol-level detail.

## SKILL.md frontmatter

```yaml
---
name: composition-guide
description: |
  Reference guide for composing batch-job, task-dag, and
  orchestrate-issue without using the all-in-one orchestrator. Use
  when you want to wire the agent-job protocol primitives manually,
  drive a custom primary-agent loop, or understand the patterns
  available. Documentation only — no install actions.
allowed-tools:
  - Read
---
```

## Self-install logic

None. The skill has no installable artifacts.

It does emit a one-time message on first invocation: "I'm a reference
skill; I don't install anything. If you want the protocol installed,
invoke `batch-job`, `task-dag`, `orchestrate-issue`, or `onboarding`."

## Bundled templates

None. The skill is SKILL.md-only.

## Failure modes

The skill cannot fail beyond render errors — it only reads and emits
documentation.

## Tests

### In this POC

- Lint the rendered SKILL.md for broken cross-references (links to other skills must resolve to siblings in the package).

### In the new repo

- Verify each documented pattern is exercised by at least one test harness scenario.

## Anti-patterns

- **Do not** add install logic to this skill. It is a pure reference.
- **Do not** duplicate content that lives in other skills' SPECs — link instead.
- **Do not** silently update `composition-guide` content when other skills change; treat patterns as a stable contract.

## Dependencies

- No runtime dependencies.
- Conceptually depends on `batch-job`, `task-dag`, and
  `orchestrate-issue` existing in the same package.

````

### .claude/skills/onboarding/README.md

```text
This is the `onboarding` distributable skill. Entry point: SKILL.md.
Interview-driven adoption of the agent-job protocol. Resumable via
the dialog file on the agent-job-protocol/onboarding branch.

```

### .claude/skills/onboarding/SKILL.md

````text
---
name: onboarding
description: |
  Interview-based onboarding for adopting the agent-job dispatch
  protocol in an existing repo. Detects existing workflow conventions,
  asks the user about intent and integration preferences, produces a
  recommendations document, walks the user through proposed changes,
  and optionally applies them. Use when adopting the protocol in a
  new repo, or when revising integration choices in a repo that has
  already adopted it. Interruptible and resumable. On first
  invocation this skill self-installs by creating the
  `.agent/onboarding/` directory and the well-known branch
  `agent-job-protocol/onboarding`; it does not install protocol
  templates (those are the other skills' jobs).
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - mcp__github__*
---

# onboarding

Interview-driven adoption of the **agent-job dispatch protocol**.
This skill is the *guidance* layer — it neither installs nor runs the
protocol itself; it figures out how the protocol should fit into the
target repo's existing workflow and (optionally) applies the
agreed-upon edits.

## When this skill runs

This skill matches when **either** of the following is true:

- The user explicitly invokes it: "onboard this repo to the
  agent-job protocol", "set up the dispatch protocol here", "run the
  onboarding skill", or `/onboarding`.
- Another protocol skill (`batch-job`, `task-dag`, or
  `orchestrate-issue`) **AND** detects on its own invocation that
  the dialog file at `.agent/onboarding/dialog.md` is missing on the
  well-known branch `agent-job-protocol/onboarding` **AND** the user
  has not previously declined onboarding in the current session.

Under the second condition, the other skill *offers* onboarding via a
one-time message; this skill is not invoked without explicit user
consent.

## Inputs

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `mode` | enum | no | `"interactive"` | `"interactive"` or `"resume"` |
| `branch_name` | string | no | `agent-job-protocol/onboarding` | Well-known branch for onboarding artifacts |
| `dialog_path` | string | no | `.agent/onboarding/dialog.md` | Dialog file path on the well-known branch |
| `recommendations_path` | string | no | `.agent/onboarding/recommendations.md` | Recommendations doc path on the well-known branch |

## Outputs

- A committed **dialog file** at `dialog_path` on `branch_name`, written
  atomically after each answered question (interruptible, resumable).
- A committed **recommendations document** at `recommendations_path`
  on `branch_name`, generated from the dialog.
- Optionally, a set of **applied edits** to the repo on a separate
  branch, gated by explicit per-file user approval.
- A final **summary** to the user with onboarding state, what was
  applied, what was skipped, and how to re-invoke this skill or any
  of the protocol skills.

## Procedure

The skill runs in 7 phases (0 through 6). Every user-facing message
emitted while running carries a state block; see "State-clarity
discipline" below.

### Phase 0 — detect prior state

Check, on the current default branch:

1. Does `.agent/config.json` exist? → protocol is **installed**.
2. Does the branch `agent-job-protocol/onboarding` exist on origin? → onboarding has been **started** at some point.
3. On that branch, does `.agent/onboarding/dialog.md` exist? → onboarding **has run**.
4. On that branch, does `.agent/onboarding/recommendations.md` exist? → recommendations have been **produced**.
5. On the default branch, is a pointer line to the recommendations doc present in `AGENTS.md` or `CLAUDE.md`? → recommendations have been **applied**.

Report state to the user explicitly:

```
Onboarding status
  Protocol installed:      yes / no
  Onboarding started:      yes / no  (branch agent-job-protocol/onboarding)
  Dialog file present:     yes / no  (.agent/onboarding/dialog.md)
  Recommendations doc:     yes / no  (.agent/onboarding/recommendations.md)
  Recommendations applied: yes / no  (pointer line on default branch)
```

If a dialog file is found, jump to the resume model (see
"Resume model" below).

### Phase 1 — ask permission

Ask the user whether to onboard:

> "Would you like to onboard this repo to the agent-job dispatch
> protocol? You can decline; the protocol skills (`batch-job`,
> `task-dag`, `orchestrate-issue`) work standalone. Onboarding only
> helps tune how they fit your existing workflow."

If declined, write a session-transcript note ("onboarding declined;
user can re-invoke later") and exit cleanly. **No state is written
to the repo on decline.**

### Phase 2 — discovery scan

Scan the repo read-only for the following paths and patterns. Follow
one level of indirection for files referenced by `AGENTS.md` or
`CLAUDE.md`.

| Path / pattern | What we extract |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Existing conventions, referenced files |
| Files referenced by the above | One level of indirection |
| `README*` | Project purpose, audience |
| `SPEC*`, `PLAN*`, `HANDOFF*`, `ROADMAP*`, `TODO*` | Current direction |
| `.github/workflows/*.yml`, `*.yaml` | Existing GitHub Actions workflows |
| `.gitlab-ci.yml`, `.gitlab/*.yml` | GitLab CI |
| `.circleci/config.yml` | CircleCI |
| `Jenkinsfile` | Jenkins |
| `bitbucket-pipelines.yml` | Bitbucket Pipelines |
| `azure-pipelines.yml`, `.azure-pipelines.yml` | Azure Pipelines |
| `.claude/skills/*/SKILL.md` | Existing skills in the repo |

Summarise findings in 5-15 bullet points and show the summary to the
user before starting the interview.

### Phase 3 — interview

The interview is a tree of questions in **6 categories**, defined in
`templates/interview-questions.yml`. Answers persist to the dialog
file (atomic write + commit + push to the well-known branch) after
every answer. Re-invocation reads the dialog file and resumes from
the next unanswered question.

The six categories are:

1. **Statement of intent** — purpose, audience, near-term goal.
2. **Problems to solve** — what friction the protocol should address.
3. **Current workflow playback** — the agent's summary of the
   existing workflow, presented for the user to confirm or revise.
4. **Integration preferences** — adoption depth, branch naming,
   command registry, parallel fanout.
5. **Sensitive files** — docs other than `AGENTS.md`/`CLAUDE.md` that
   should not be modified.
6. **Confirmation** — recap of answers; user may revise any.

Do not suppress questions because they seem obvious. User answers
drive the recommendations.

### Phase 4 — write recommendations

Generate `recommendations.md` on the well-known branch from the
dialog file. Structure:

```markdown
# Onboarding recommendations — <repo>

## Statement of intent
<from interview>

## Problems addressed
<from interview>

## Files to add (no edits to existing files)
- .agent/config.json (from batch-job/task-dag template)
- .agent/scripts/... (full inventory)
- .github/workflows/lock-and-sweep.yml
- .github/workflows/batch-job-handler.yml
- .github/workflows/close-on-merge.yml
- .agent/schemas/...

## Files proposed for additive edits (pointer-only)
- AGENTS.md: add one line under a new "Agent-job protocol" section:
    > See .agent/onboarding/recommendations.md for protocol conventions.
- CLAUDE.md: identical pointer line.

## Files proposed for non-pointer edits
<list with diff preview for each; only present if discovery found
files that should be substantively modified — typically SPEC, README,
PLAN, HANDOFF. AGENTS.md/CLAUDE.md NEVER appear here.>

## Before/after workflow
- Today: <agent's summary of current dispatch model>
- After: <how the protocol changes dispatch>

## Next steps if accepted
1. The onboarding skill will apply the proposed edits with your
   explicit per-file approval.
2. Run `/orchestrate-issue` on any unclaimed agent-task issue to
   exercise the new flow.
3. Re-run `/onboarding` later to revise integration choices.
```

Use `lib/recommendations.py` (function `render_recommendations`) to
serialise the structure from the dialog data.

### Phase 5 — walkthrough and apply

For each proposed change in `recommendations.md`:

- Display a before/after diff (side-by-side or unified — agent's
  choice).
- Ask: "Apply this change? [yes / no / skip-all-AGENTS-edits / skip-all]"
- For `AGENTS.md` and `CLAUDE.md`: the **only** allowed edit is
  adding a single pointer line. The skill never proposes anything
  else here. Even the pointer-line edit requires explicit per-file
  approval.
- For `SPEC*`/`README*`/`PLAN*`/`HANDOFF*`/`ROADMAP*`/`TODO*`:
  substantive edits require walkthrough plus explicit approval.
- Apply approved changes one file at a time. After each apply, show
  the resulting file's relevant section.

Maintain a visible state block at every step (see "State-clarity
discipline" below).

### Phase 6 — finalise

- Merge the well-known branch's onboarding artifacts into the
  default branch via a PR (or commit directly if the user prefers
  and has permission).
- Post a final summary message: onboarding state, what was applied,
  what was skipped, how to re-invoke onboarding, and how to invoke
  each of the protocol skills.
- Done.

## Interview question categories

The canonical question tree lives in
`templates/interview-questions.yml` (machine-readable schema). The
six categories mirror Phase 3:

1. **Statement of intent** (`intent`) — purpose, audience, goal.
2. **Problems to solve** (`problems`) — friction inventory plus
   freeform pain points.
3. **Current workflow playback** (`current_workflow`) — playback
   accuracy check.
4. **Integration preferences** (`integration`) — depth, branch
   naming, commands, fanout.
5. **Sensitive files** (`sensitive_files`) — do-not-edit list.
6. **Confirmation** (`confirmation`) — final recap.

Question IDs are stable across versions so partial dialog files
remain resumable after schema additions. Adding a new question to
a category is backward-compatible; renaming an existing question ID
is a breaking change and requires bumping the YAML's `version` field.

## Well-known branch and dialog file conventions

- **Branch.** `agent-job-protocol/onboarding`. Created from the
  default branch if missing. Never deleted.
- **Dialog file.** `.agent/onboarding/dialog.md` on that branch.
- **Recommendations file.** `.agent/onboarding/recommendations.md`
  on that branch.

After Phase 6, the dialog file and recommendations file also exist
on the default branch under `.agent/onboarding/`. The well-known
branch is kept as a historical record (not deleted) so future
re-invocations can find the prior dialog and offer to revise.

## Resume model

When this skill is re-invoked and a dialog file already exists, it
presents the resume menu:

```
A prior onboarding session left a dialog file with 14/22 questions
answered. Last answer: "Branch naming overrides? — keep defaults"
on 2026-05-13.

Options:
  1. Continue from the next unanswered question
  2. Restart from the beginning (prior answers used as defaults)
  3. Show me the dialog file and let me edit it manually
  4. Abandon this onboarding run

What would you like to do?
```

The dialog file is the single source of truth for resumption state.
`lib/dialog.py` parses it back into structured Q/A pairs.

## Self-install logic

This skill is the **guidance** layer, not the protocol layer. It
**does not install protocol templates** — the protocol skills
(`batch-job`, `task-dag`, `orchestrate-issue`) install themselves on
first invocation.

What this skill installs:

| Target | Action if missing |
|---|---|
| `.agent/onboarding/` directory (on the well-known branch) | Create |
| Branch `agent-job-protocol/onboarding` | Create from default branch |

That is the entire self-install footprint. No workflow YAMLs, no
`.agent/config.json`, no scripts. The protocol skills handle their
own templates.

## State-clarity discipline

**Every user-facing message includes a state block.** This is
non-negotiable. The user must never have to ask "where are we?"

Example during the interview:

```
[onboarding • phase 3/6 • interview]
You said the repo's intent is to be a maintenance project for the
agent-job protocol skills. Next question: Who works on it (humans
only / agents only / both)?
```

Example during the apply phase:

```
[onboarding • phase 5/6 • apply]
Files queue:
  [done]    1/6: .agent/config.json (created)
  [done]    2/6: .agent/scripts/common.py (created)
  [pending] 3/6: AGENTS.md (proposed: add pointer line) ← awaiting your decision
  [queued]  4/6: README.md (proposed: add 1-paragraph section)
  [queued]  5/6: CLAUDE.md (proposed: add pointer line)
  [queued]  6/6: SPEC.md (proposed: add reference to .agent/onboarding/recommendations.md)
```

The skill always restates the current phase, what just happened, and
what is happening next — even when the user is a returning operator
on a session-resumed run.

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| User declines onboarding | Phase 1 | Exit cleanly; no state written |
| Discovery scan times out (very large repo) | Phase 2 | Show partial findings; ask user to continue |
| Network drops mid-interview | Phase 3 | Dialog file commit fails; surface to user; resume on next invocation |
| User rejects all edits | Phase 5 | Write recommendations only; report state; exit |
| Conflict applying pointer to `AGENTS.md` | Phase 5 | Show diff; ask user to resolve manually |
| Stale dialog from a prior protocol version | Phase 0 | Offer "revise integration" with prior answers as defaults |

## Anti-patterns

- **Do not** edit `AGENTS.md` or `CLAUDE.md` with anything other than
  a single pointer line. These files are sacred (cross-project
  conventions); the only legal additive edit is the pointer line, and
  even that requires explicit per-file approval.
- **Do not** apply edits without explicit per-file approval.
- **Do not** delete the dialog file between sessions.
- **Do not** assume the user remembers a prior session — always
  restate the current state at the top of every message.
- **Do not** suppress questions in the interview because they "seem
  obvious." User answers drive recommendations.
- **Do not** install protocol templates from within this skill —
  that is the job of `batch-job`, `task-dag`, and `orchestrate-issue`.

## Python entry points

The skill's runtime logic lives in `lib/`:

| Module | Purpose |
|---|---|
| `lib/detect.py` | `detect_state(repo_root)` — Phase 0 detection (5 booleans) |
| `lib/discovery.py` | `scan_repo(repo_root)` — Phase 2 discovery scan |
| `lib/dialog.py` | `load_dialog(path)` / `save_dialog(path, data)` — round-trip the dialog file |
| `lib/recommendations.py` | `render_recommendations(dialog)` — produce the recommendations.md content |

The interactive question-asking and per-file approval loops are
driven by the agent's tool calls (`AskUserQuestion`, `Read`, `Edit`,
`Write`), not by the Python helpers. The helpers are pure functions
over the dialog and discovery state.

## Templates bundled with this skill

```
templates/
  dialog-template.md           # blank dialog skeleton with section headers
  recommendations-template.md  # blank recommendations skeleton
  interview-questions.yml      # canonical question tree (stable schema)
```

The `interview-questions.yml` schema is stable so a future agent can
machine-read partial dialog files and resume them.

## Dependencies

- **Install time:** none.
- **Runtime:** a GitHub MCP server for branch and file operations.
- **Recommended (not required):** `batch-job`, `task-dag`,
  `orchestrate-issue` skills. The onboarding skill recommends but
  does not require them.

---
Version: 1.0.0
Protocol-version: 1
Last-synced-from-POC: 2026-05-14
---

````

### docs/skills/onboarding/SPEC.md

````text
# SPEC — onboarding skill

Status: design-stage
Audience: implementers of the skill in the new `pipeline-ai-sandbox` repo

## Purpose

Onboard a repo into the agent-job protocol via a **structured
interview**. The skill:

1. Detects whether the protocol has been adopted (`.agent/config.json` present?) and whether onboarding has been completed (dialog file present on the well-known branch?).
2. Reads the repo's existing workflow context: other skills, `AGENTS.md`/`CLAUDE.md` and any files they reference, `README*`, `SPEC*`, `PLAN*`, `HANDOFF*`, and CI/CD config (GitHub Actions, GitLab CI, CircleCI, Jenkinsfile, Bitbucket Pipelines, Azure Pipelines).
3. Asks the user whether to onboard. Accepts a decline.
4. If accepted, runs a structured interview persisted to a dialog file so a different agent session can resume.
5. Produces a **recommendations document** describing what to change in the repo.
6. Walks the user through suggested changes with before/after comparison.
7. **Offers to apply the changes itself**, respecting AGENTS.md/CLAUDE.md sacredness.
8. Reports state clearly at every step.

## Trigger conditions

The skill matches when:

- The user says: "onboard this repo to the agent-job protocol", "set up the dispatch protocol here", "run the onboarding skill", "/onboarding".
- Another protocol skill detects on its own invocation that the dialog file is missing on the well-known branch AND the user has not explicitly declined onboarding in this session. In that case the other skill offers onboarding but does not run it without user consent.

## Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `mode` | enum | no | `"interactive"` (default) or `"resume"` |
| `branch_name` | string | no | Defaults to `agent-job-protocol/onboarding` |
| `dialog_path` | string | no | Defaults to `.agent/onboarding/dialog.md` |
| `recommendations_path` | string | no | Defaults to `.agent/onboarding/recommendations.md` |

## Outputs

- A committed dialog file at `dialog_path` on `branch_name`.
- A committed recommendations document at `recommendations_path` on `branch_name`.
- Optionally, a set of applied edits to the repo (only with explicit per-file approval).
- A final summary to the user with state, what changed, and what is next.

## Procedure

### Phase 0 — detect prior state

Check (on the current default branch):

1. `.agent/config.json` exists? → protocol is **installed**.
2. Branch `agent-job-protocol/onboarding` exists on origin? → onboarding has been **started** at some point.
3. On that branch, does the dialog file exist? → onboarding **has run**.
4. On that branch, is the recommendations doc applied to default? → onboarding is **complete**.

Report state to the user explicitly:

```
Onboarding status
  Protocol installed:    yes / no
  Onboarding started:    yes / no  (branch agent-job-protocol/onboarding)
  Dialog file present:   yes / no  (.agent/onboarding/dialog.md)
  Recommendations doc:   yes / no  (.agent/onboarding/recommendations.md)
  Recommendations applied: yes / no  (presence of pointer in target docs)
```

### Phase 1 — ask permission

"Would you like to onboard this repo to the agent-job dispatch
protocol? You can decline; the protocol skills (`batch-job`,
`task-dag`, `orchestrate-issue`) work standalone. Onboarding only
helps tune how they fit your existing workflow."

If the user declines, exit cleanly. Write a small note to the
session transcript ("onboarding declined; user can re-invoke later").

### Phase 2 — discovery scan

If the user accepts, scan the repo (read-only) for:

| Path / pattern | What we extract |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Existing conventions, referenced files |
| Any file referenced by the above | Follow one level of indirection |
| `README*` | Project purpose, audience |
| `SPEC*`, `PLAN*`, `HANDOFF*`, `ROADMAP*`, `TODO*` | Current direction |
| `.github/workflows/*.yml`, `.github/workflows/*.yaml` | Existing GHA workflows |
| `.gitlab-ci.yml`, `.gitlab/*.yml` | GitLab CI |
| `.circleci/config.yml` | CircleCI |
| `Jenkinsfile` | Jenkins |
| `bitbucket-pipelines.yml` | Bitbucket Pipelines |
| `azure-pipelines.yml`, `.azure-pipelines.yml` | Azure |
| `.claude/skills/*/SKILL.md` | Existing skills in the repo |

The skill summarises what it found in 5-15 bullet points and shows the
summary to the user before starting the interview.

### Phase 3 — interview

The interview is a tree of questions. Answers persist to the dialog
file after every answer (atomic write + commit + push to the
well-known branch). Re-invocation reads the file and resumes.

Question categories:

1. **Statement of intent**
   - What does this repo do, in one sentence?
   - Who works on it (humans only / agents only / both)?
   - What is the goal for the next 1-3 months?

2. **Problems to solve**
   - What current friction does the user want the protocol to address?
     - Subagent coordination?
     - Secrets handling?
     - Parallel work fanout?
     - Long-running jobs?
   - Free-form: any existing pain points the user wants captured?

3. **Current workflow playback**
   - "Based on what we found, your current workflow looks like
     [agent's summary, 5-10 bullets]. Is this accurate?"
   - User can correct.

4. **Integration preferences**
   - Adoption depth: full (all 3 protocol skills + onboarding pointer in AGENTS.md) / partial (batch-job only) / spec-only (no install yet)?
   - Branch naming overrides? (default `agent/<issue>-<slug>`)
   - Command registry: which of `run-tests`, `build`, `deploy-staging`, etc., do they want enabled at start?
   - Subagent fanout: enable `orchestrate-issue` for parallel work, or stick to single-subagent loops?

5. **Sensitive files**
   - "Are there docs in the repo that are copied across projects and
     should not be modified by this onboarding (besides AGENTS.md and
     CLAUDE.md which are already protected)?" Add to a do-not-edit list.

6. **Confirmation**
   - Recap of answers; user can revise any.

### Phase 4 — write recommendations

Generate `recommendations.md` on the well-known branch. Structure:

```markdown
# Onboarding recommendations — <repo>

## Statement of intent
<from interview>

## Problems addressed
<from interview>

## Files to add (no edits to existing files)
- .agent/config.json (from batch-job/task-dag template)
- .agent/scripts/... (full inventory)
- .github/workflows/lock-and-sweep.yml
- .github/workflows/batch-job-handler.yml
- .github/workflows/close-on-merge.yml
- .agent/schemas/...

## Files proposed for additive edits (pointer-only)
- AGENTS.md: add one line under a new "Agent-job protocol" section:
    > See .agent/onboarding/recommendations.md for protocol conventions.
- CLAUDE.md: identical pointer line.

## Files proposed for non-pointer edits
<list with diff preview for each; only present if discovery found
files that should be substantively modified — typically SPEC, README,
PLAN, HANDOFF. AGENTS.md/CLAUDE.md NEVER appear here.>

## Before/after workflow
- Today: <agent's summary of current dispatch model>
- After: <how the protocol changes dispatch>

## Next steps if accepted
1. The onboarding skill will apply the proposed edits with your
   explicit per-file approval.
2. Run `/orchestrate-issue` on any unclaimed agent-task issue to
   exercise the new flow.
3. Re-run `/onboarding` later to revise integration choices.
```

### Phase 5 — walkthrough and apply

For each proposed change in `recommendations.md`:

- Display before/after side-by-side. (Use diff-style text output.)
- Ask: "Apply this change? [yes/no/skip-all-AGENTS-edits/skip-all]"
- For `AGENTS.md` and `CLAUDE.md`: the **only** allowed edit is adding
  a pointer line. The skill never proposes anything else here. Even
  the pointer-line edit requires explicit per-file approval.
- For SPEC/README/PLAN/HANDOFF/ROADMAP/TODO: substantive edits require
  walkthrough + explicit approval before applying.
- Apply approved changes one file at a time. After each apply, show
  the user the resulting file's relevant section.

The skill maintains a state block visible to the user at every step:

```
Onboarding progress
  Phase: 5 of 6 (apply edits)
  Files approved + applied: 4
  Files pending decision: 2
  Files skipped: 1
  Next action: review proposed edit to .agent/onboarding/recommendations.md
```

### Phase 6 — finalise

- Merge the well-known branch's onboarding artifacts into the default
  branch via a PR (or commit directly to default if the user has
  permission and prefers).
- Post a summary message: state, what was applied, what was skipped,
  how to re-invoke onboarding, how to invoke the other skills.
- Done.

## Well-known branch and dialog file

- Branch: `agent-job-protocol/onboarding` (configurable via input).
- Dialog file: `.agent/onboarding/dialog.md` on that branch.
- Recommendations: `.agent/onboarding/recommendations.md` on that branch.
- After Phase 6, recommendations and dialog also live on default
  branch under `.agent/onboarding/`. The well-known branch is kept as
  a historical record (not deleted).

If a future re-invocation detects an old dialog file and a previous
recommendations doc on the well-known branch, Phase 0 reports
"Recommendations applied" and offers two options: "Revise the
integration" (restart from Phase 3 with prior answers as defaults) or
"Exit".

## Resume model

When re-invoked and the dialog file already exists:

```
A prior onboarding session left a dialog file with 14/22 questions
answered. Last answer: "Branch naming overrides? — keep defaults"
on 2026-05-13.

Options:
  1. Continue from the next unanswered question
  2. Restart from the beginning (prior answers used as defaults)
  3. Show me the dialog file and let me edit it manually
  4. Abandon this onboarding run

What would you like to do?
```

## Self-install logic

This skill does **not** install protocol templates itself. It is the
**guidance** layer, not the protocol layer. The skills it recommends
(`batch-job`, `task-dag`, `orchestrate-issue`) install themselves on
first invocation.

What this skill does install:

| File or path | Action if missing |
|---|---|
| `.agent/onboarding/` directory | Create on the well-known branch |
| Branch `agent-job-protocol/onboarding` | Create from default branch |

## Bundled templates

```
templates/
  dialog-template.md           # blank dialog skeleton with section headers
  recommendations-template.md  # blank recommendations skeleton
  interview-questions.yml      # canonical question tree
```

The interview-questions.yml has a stable schema so a future agent can
machine-read partial dialog files and continue.

## SKILL.md frontmatter

```yaml
---
name: onboarding
description: |
  Interview-based onboarding for adopting the agent-job dispatch
  protocol in an existing repo. Detects existing workflow conventions,
  asks the user about intent and integration preferences, produces a
  recommendations document, walks the user through proposed changes,
  and optionally applies them. Use when adopting the protocol in a
  new repo, or when revising integration choices in a repo that has
  already adopted it. Interruptible and resumable.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - mcp__github__*
---
```

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| User declines onboarding | Phase 1 | Exit cleanly; no state written |
| Discovery scan times out (huge repo) | Phase 2 | Show partial findings; ask user to continue |
| Network drops mid-interview | Phase 3 | Dialog file commit fails; surface to user; resume on next invocation |
| User rejects all edits | Phase 5 | Write recommendations only; report state; exit |
| Conflict applying pointer to AGENTS.md | Phase 5 | Show diff, ask user to resolve manually |

## State-clarity discipline

**Every user-facing message includes a state block.** Example:

```
[onboarding • phase 3/6 • interview]
You said the repo's intent is to be a maintenance project for the
agent-job protocol skills. Next question: Who works on it? …
```

When applying edits:

```
[onboarding • phase 5/6 • apply]
Files queue:
  [done]    1/6: .agent/config.json (created)
  [done]    2/6: .agent/scripts/common.py (created)
  [pending] 3/6: AGENTS.md (proposed: add pointer line) ← awaiting your decision
  [queued]  4/6: README.md (proposed: add 1-paragraph section)
  [queued]  5/6: CLAUDE.md (proposed: add pointer line)
  [queued]  6/6: SPEC.md (proposed: add reference to .agent/onboarding/recommendations.md)
```

## Tests

### In this POC

- Schema validity of `interview-questions.yml`.
- Dialog-file round-trip: write a fixture, parse it back, verify all answers preserved.
- Discovery scan against fixture repos: assert the skill finds the right files.
- "Recommended edits" generation against fixtures: assert AGENTS.md is never proposed for non-pointer edits.

### In the new repo

- Drive a full interview via the test harness with scripted answers; verify dialog and recommendations docs are correctly written.
- Resume test: write a partial dialog; invoke onboarding; verify it picks up at the right question.
- Apply test: accept all edits; verify pointer lines are added correctly and substantive edits respect approval boundaries.

## Anti-patterns

- **Do not** edit AGENTS.md or CLAUDE.md with anything other than a single pointer line.
- **Do not** apply edits without explicit per-file approval.
- **Do not** delete the dialog file between sessions.
- **Do not** assume the user remembers the prior session — always restate state.
- **Do not** suppress questions in the interview because they "seem obvious." User answers drive recommendations.

## Dependencies

- None at install time.
- At runtime, depends on a GitHub MCP server for branch creation.
- Recommends `batch-job`, `task-dag`, `orchestrate-issue` skills but
  does not require them to be present.

````

### .claude/skills/onboarding/lib/__init__.py

```text
"""Helpers for the onboarding skill (detect / discovery / dialog / recommendations)."""

```

### .claude/skills/onboarding/lib/detect.py

```text
"""Phase 0 detection — does the onboarding skill have any prior state?

Reports five booleans that mirror the SKILL.md "Onboarding status"
block. The full implementation in the new repo uses the GitHub MCP
server to check the remote well-known branch
`agent-job-protocol/onboarding` for the dialog / recommendations
files. This stub only checks local filesystem presence so it can run
inside unit tests against fixture repos.
"""

from __future__ import annotations

import os
from typing import Dict


def detect_state(repo_root: str) -> Dict[str, bool]:
    """Return Phase 0 state booleans for the repo at ``repo_root``.

    Returns a dict with these keys:

    - ``protocol_installed`` — ``.agent/config.json`` is present.
    - ``onboarding_started`` — branch ``agent-job-protocol/onboarding``
      exists on origin. (Stub: cannot check remote; returns False
      unless a local marker file is found at
      ``.agent/onboarding/.branch-created``.)
    - ``dialog_present`` — ``.agent/onboarding/dialog.md`` exists.
    - ``recommendations_present`` — ``.agent/onboarding/recommendations.md`` exists.
    - ``recommendations_applied`` — a pointer line to
      ``.agent/onboarding/recommendations.md`` is present in
      ``AGENTS.md`` or ``CLAUDE.md``.

    The full implementation (run in the maintenance repo) replaces
    the local FS checks with GitHub MCP calls so detection works
    against the actual default branch and the well-known onboarding
    branch.
    """

    def _exists(rel: str) -> bool:
        return os.path.exists(os.path.join(repo_root, rel))

    pointer = ".agent/onboarding/recommendations.md"

    def _has_pointer(rel: str) -> bool:
        path = os.path.join(repo_root, rel)
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return pointer in fp.read()
        except OSError:
            return False

    return {
        "protocol_installed": _exists(".agent/config.json"),
        "onboarding_started": _exists(".agent/onboarding/.branch-created"),
        "dialog_present": _exists(".agent/onboarding/dialog.md"),
        "recommendations_present": _exists(".agent/onboarding/recommendations.md"),
        "recommendations_applied": _has_pointer("AGENTS.md") or _has_pointer("CLAUDE.md"),
    }

```

### .claude/skills/onboarding/lib/dialog.py

```text
"""Round-trip serialisation for the onboarding dialog file.

The dialog file is Markdown by design (humans read it directly during
resume), but every question has a stable id so a parser can pick it
back up. The schema lives in ``templates/interview-questions.yml``.

This module is the single point of truth for the dialog's on-disk
shape: ``load_dialog`` parses; ``save_dialog`` serialises; both
honour the convention that the file is atomically rewritten on
every answer (no append-only journaling).
"""

from __future__ import annotations

import datetime as _dt
import os
import re
from typing import Any, Dict, List, Optional


# A Q/A bullet looks like:   - **<question.id>** — _<text>_
# followed by indented sub-bullets that hold the answer.
_QA_LINE = re.compile(r"^- \*\*(?P<qid>[a-z_]+\.[a-z_]+)\*\* — _(?P<text>.+)_\s*$")
_ANSWER_LINE = re.compile(r"^\s*-\s*Answer(?:\s*\([^)]*\))?:\s*(?P<answer>.*)$")
_HEADER_KV = re.compile(r"^- (?P<key>[a-z_]+):\s*`?(?P<value>[^`]*)`?\s*$")


def load_dialog(path: str) -> Dict[str, Any]:
    """Parse a dialog file into a structured dict.

    Returns a dict shaped like::

        {
          "meta": {"run_id": "...", "started_at": "...", "last_updated": "...",
                   "protocol_version": 1, "questions_schema_version": 1},
          "answers": {
            "intent.purpose": "...",
            "intent.audience": "...",
            ...
          },
          "phases_done": ["phase_0", "phase_1", ...],
        }

    Unanswered questions are present in the file as placeholder text;
    their entries appear in ``answers`` with the literal placeholder
    string. The caller is responsible for distinguishing placeholders
    from real answers (typically by string-equal check against
    ``<placeholder>``).
    """
    if not os.path.exists(path):
        return {"meta": {}, "answers": {}, "phases_done": []}

    with open(path, "r", encoding="utf-8") as fp:
        text = fp.read()

    meta: Dict[str, Any] = {}
    answers: Dict[str, str] = {}
    phases_done: List[str] = []

    current_qid: Optional[str] = None
    lines = text.splitlines()

    # Header KV pairs (between the H1 and the first H2).
    for line in lines:
        m = _HEADER_KV.match(line)
        if m:
            meta[m.group("key")] = m.group("value")

    # Q/A bullets and their nested answer lines.
    for i, line in enumerate(lines):
        qa = _QA_LINE.match(line)
        if qa:
            current_qid = qa.group("qid")
            continue
        if current_qid:
            ans = _ANSWER_LINE.match(line)
            if ans:
                answers[current_qid] = ans.group("answer").strip().strip("`")
                current_qid = None

    # Status checklist.
    for line in lines:
        m = re.match(r"^- \[(?P<state>[ x])\] Phase (?P<n>\d) ", line)
        if m and m.group("state") == "x":
            phases_done.append(f"phase_{m.group('n')}")

    return {"meta": meta, "answers": answers, "phases_done": phases_done}


def save_dialog(path: str, data: Dict[str, Any]) -> None:
    """Atomically serialise ``data`` to the dialog file at ``path``.

    Atomic means: write to ``<path>.tmp`` then ``os.replace``. The
    caller is responsible for committing + pushing the result to the
    well-known branch.

    The full implementation will preserve the exact question ordering
    from ``templates/interview-questions.yml`` and include every
    question id (placeholder for unanswered ones) so the file is
    diff-friendly and re-parseable. This stub writes a minimal
    serialisation for tests.
    """
    meta = dict(data.get("meta") or {})
    meta.setdefault("last_updated", _dt.datetime.utcnow().isoformat() + "Z")
    answers = data.get("answers") or {}
    phases_done = set(data.get("phases_done") or [])

    out: List[str] = ["# Onboarding dialog", ""]
    for key in ("run_id", "started_at", "last_updated", "protocol_version", "questions_schema_version"):
        if key in meta:
            out.append(f"- {key}: `{meta[key]}`")
    out.append("")

    # One H2 per category, derived from the answers keys. The full
    # implementation orders sections by the canonical YAML; this stub
    # groups by the prefix before the dot.
    by_category: Dict[str, List[str]] = {}
    for qid in answers:
        cat = qid.split(".", 1)[0]
        by_category.setdefault(cat, []).append(qid)

    for cat, qids in by_category.items():
        out.append(f"## {cat}")
        out.append("")
        for qid in qids:
            out.append(f"- **{qid}** — _<text>_")
            out.append(f"  - Answer: {answers[qid]}")
        out.append("")

    out.append("## Status")
    out.append("")
    for n in range(7):
        mark = "x" if f"phase_{n}" in phases_done else " "
        out.append(f"- [{mark}] Phase {n}")
    out.append("")

    tmp = f"{path}.tmp"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fp:
        fp.write("\n".join(out))
    os.replace(tmp, path)

```

### .claude/skills/onboarding/lib/discovery.py

```text
"""Phase 2 discovery scan — read-only walk of known paths.

Produces a structured summary of what exists in the target repo so
the agent can show a discovery summary to the user before starting
the interview, and so `recommendations.py` can decide which files
warrant a non-pointer proposed edit.

The path table mirrors SPEC.md §"Phase 2 — discovery scan". The
full implementation in the new repo follows one level of indirection
for files referenced by AGENTS.md / CLAUDE.md; this stub records
their presence but does not parse them.
"""

from __future__ import annotations

import glob
import os
from typing import Dict, List


# The discovery patterns table. Each entry is (category, glob).
DISCOVERY_PATTERNS: List[tuple] = [
    ("conventions", "AGENTS.md"),
    ("conventions", "CLAUDE.md"),
    ("readme", "README*"),
    ("spec", "SPEC*"),
    ("plan", "PLAN*"),
    ("handoff", "HANDOFF*"),
    ("roadmap", "ROADMAP*"),
    ("todo", "TODO*"),
    ("ci.github", ".github/workflows/*.yml"),
    ("ci.github", ".github/workflows/*.yaml"),
    ("ci.gitlab", ".gitlab-ci.yml"),
    ("ci.gitlab", ".gitlab/*.yml"),
    ("ci.circle", ".circleci/config.yml"),
    ("ci.jenkins", "Jenkinsfile"),
    ("ci.bitbucket", "bitbucket-pipelines.yml"),
    ("ci.azure", "azure-pipelines.yml"),
    ("ci.azure", ".azure-pipelines.yml"),
    ("skills", ".claude/skills/*/SKILL.md"),
]


def scan_repo(repo_root: str) -> Dict[str, List[str]]:
    """Walk the discovery patterns and return a category -> [paths] map.

    Paths returned are repo-relative. The full implementation will
    additionally:

    - Follow one level of indirection for files referenced by
      AGENTS.md / CLAUDE.md (extract Markdown link targets, add them
      to the result under ``referenced``).
    - Parse YAML for CI files and extract job names / step names.
    - Truncate the result to 5-15 bullet points for user display
      while keeping the full structured map available for
      recommendations rendering.
    """
    found: Dict[str, List[str]] = {}
    for category, pattern in DISCOVERY_PATTERNS:
        matches = glob.glob(os.path.join(repo_root, pattern))
        rel_matches = sorted(
            os.path.relpath(m, repo_root) for m in matches if os.path.isfile(m)
        )
        if rel_matches:
            found.setdefault(category, []).extend(rel_matches)
    return found


def summarise(scan_result: Dict[str, List[str]]) -> List[str]:
    """Turn a scan result into 5-15 bullet points for user display.

    Stub returns one bullet per category with a count. The full
    implementation will produce richer summaries (e.g. "GitHub
    Actions: 3 workflows including ci.yml, release.yml, lint.yml").
    """
    bullets: List[str] = []
    for category, paths in sorted(scan_result.items()):
        bullets.append(f"{category}: {len(paths)} file(s) — {', '.join(paths[:3])}")
    return bullets

```

### .claude/skills/onboarding/lib/recommendations.py

```text
"""Render the recommendations Markdown from the dialog data.

The output structure mirrors SPEC.md §"Phase 4 — write
recommendations" and matches the template at
``templates/recommendations-template.md``. AGENTS.md and CLAUDE.md
NEVER appear in the "non-pointer edits" section — that is enforced
here, not just by policy.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable


_SACRED_FILES = frozenset({"AGENTS.md", "CLAUDE.md"})


def render_recommendations(dialog: Dict[str, Any], repo_name: str = "<repo>") -> str:
    """Produce the recommendations.md content as a string.

    ``dialog`` is the structured dict returned by
    ``lib.dialog.load_dialog``. ``repo_name`` is interpolated into the
    H1.

    The full implementation will:

    - Pull non-pointer-edit candidates from a discovery summary
      (passed separately), not from the dialog directly.
    - Diff each candidate against the current default branch and
      embed a short diff preview.
    - Hard-fail if a sacred file appears in the non-pointer list
      (defensive — that should never happen given the call sites).
    """
    answers: Dict[str, str] = dialog.get("answers") or {}

    def _get(qid: str, default: str = "_<not answered>_") -> str:
        return answers.get(qid, default)

    lines: list = []
    lines.append(f"# Onboarding recommendations — {repo_name}")
    lines.append("")
    lines.append("## Statement of intent")
    lines.append("")
    lines.append(f"- Purpose: {_get('intent.purpose')}")
    lines.append(f"- Audience: {_get('intent.audience')}")
    lines.append(f"- 1-3 month goal: {_get('intent.goal')}")
    lines.append("")

    lines.append("## Problems addressed")
    lines.append("")
    lines.append(f"- Friction addressed: {_get('problems.friction')}")
    lines.append(f"- Pain points captured: {_get('problems.freeform')}")
    lines.append("")

    lines.append("## Files to add (no edits to existing files)")
    lines.append("")
    for path in (
        ".agent/config.json (from batch-job/task-dag template)",
        ".agent/scripts/... (full inventory)",
        ".github/workflows/lock-and-sweep.yml",
        ".github/workflows/batch-job-handler.yml",
        ".github/workflows/close-on-merge.yml",
        ".agent/schemas/...",
    ):
        lines.append(f"- {path}")
    lines.append("")

    lines.append("## Files proposed for additive edits (pointer-only)")
    lines.append("")
    lines.append("- `AGENTS.md`: add one line under a new \"Agent-job protocol\" section:")
    lines.append("  > See `.agent/onboarding/recommendations.md` for protocol conventions.")
    lines.append("- `CLAUDE.md`: identical pointer line.")
    lines.append("")

    lines.append("## Files proposed for non-pointer edits")
    lines.append("")
    non_pointer = list(_filter_non_pointer(dialog.get("non_pointer_candidates") or []))
    if non_pointer:
        for path, rationale in non_pointer:
            lines.append(f"- `{path}` — {rationale}")
    else:
        lines.append("- _(none proposed by this run)_")
    lines.append("")

    lines.append("## Before/after workflow")
    lines.append("")
    lines.append(f"- Today: {_get('current_workflow.summary_accurate', '<agent summary>')}")
    lines.append(f"- After: see integration depth `{_get('integration.depth')}`")
    lines.append("")

    lines.append("## Next steps if accepted")
    lines.append("")
    lines.append("1. The onboarding skill will apply the proposed edits with your")
    lines.append("   explicit per-file approval.")
    lines.append("2. Run `/orchestrate-issue` on any unclaimed agent-task issue to")
    lines.append("   exercise the new flow.")
    lines.append("3. Re-run `/onboarding` later to revise integration choices.")
    lines.append("")

    return "\n".join(lines)


def _filter_non_pointer(candidates: Iterable) -> Iterable:
    """Strip sacred files from the non-pointer-edit candidate list.

    Defensive belt-and-braces: AGENTS.md / CLAUDE.md must never reach
    the non-pointer section. If a caller passes them in, drop them
    silently rather than render them.
    """
    for item in candidates:
        # Expect (path, rationale) tuples; tolerate plain strings too.
        if isinstance(item, tuple) and len(item) == 2:
            path, rationale = item
        else:
            path, rationale = str(item), ""
        if path in _SACRED_FILES:
            continue
        yield (path, rationale)

```

### .claude/skills/onboarding/templates/dialog-template.md

```text
# Onboarding dialog

<!--
This file is the persistent record of one onboarding interview.
The onboarding skill writes here after every answered question
(atomic write + commit + push to the well-known branch
`agent-job-protocol/onboarding`). The file is the single source of
truth for resuming an interrupted onboarding session.

Schema version: 1
-->

- run_id: `<fill-in-on-create>`
- started_at: `<fill-in-on-create>`
- last_updated: `<fill-in-on-each-write>`
- protocol_version: 1
- questions_schema_version: 1

## Statement of intent

<!-- Category id: intent. One bullet per question, in stable id order. -->

- **intent.purpose** — _What does this repo do, in one sentence?_
  - Answer: `<placeholder>`
- **intent.audience** — _Who works on it (humans only / agents only / both)?_
  - Answer: `<placeholder>`
- **intent.goal** — _What is the goal for the next 1-3 months?_
  - Answer: `<placeholder>`

## Problems to solve

<!-- Category id: problems. -->

- **problems.friction** — _What current friction do you want the protocol to address?_
  - Answer: `<placeholder>`
- **problems.freeform** — _Any existing pain points to capture?_
  - Answer: `<placeholder>`

## Current workflow playback

<!-- Category id: current_workflow. The agent fills in its summary above
     the answer line; the user accepts or revises. -->

- **current_workflow.summary_accurate** — _Based on what we found, your current workflow looks like ... Is this accurate?_
  - Agent summary: `<placeholder>`
  - Answer (yes / revise + revisions): `<placeholder>`
- **current_workflow.revisions** — _If not accurate, what should we revise in the summary?_
  - Answer: `<placeholder>`

## Integration preferences

<!-- Category id: integration. -->

- **integration.depth** — _Adoption depth?_
  - Answer: `<placeholder>`
- **integration.branch_naming** — _Branch naming overrides? (default agent/<issue>-<slug>)_
  - Answer: `<placeholder>`
- **integration.commands** — _Which commands to enable at start?_
  - Answer: `<placeholder>`
- **integration.fanout** — _Enable orchestrate-issue for parallel work?_
  - Answer: `<placeholder>`

## Sensitive files

<!-- Category id: sensitive_files. -->

- **sensitive_files.list** — _Are there docs that should not be modified (besides AGENTS.md/CLAUDE.md)?_
  - Answer: `<placeholder>`
- **sensitive_files.confirm_added** — _Confirm the do-not-edit list above is complete?_
  - Answer (yes / revise + revisions): `<placeholder>`

## Confirmation

<!-- Category id: confirmation. -->

- **confirmation.recap_ok** — _Recap of answers; revise any?_
  - Answer (yes / revise + revisions): `<placeholder>`

## Status

<!-- Phase completion checklist. The onboarding skill updates this as
     phases complete. Used by Phase 0 detection on re-invocation. -->

- [ ] Phase 0 — detect prior state
- [ ] Phase 1 — permission granted
- [ ] Phase 2 — discovery scan complete
- [ ] Phase 3 — interview complete
- [ ] Phase 4 — recommendations written
- [ ] Phase 5 — walkthrough and apply complete
- [ ] Phase 6 — finalised (merged to default)

```

### .claude/skills/onboarding/templates/interview-questions.yml

```text
# Canonical interview question tree for the onboarding skill.
#
# Stable schema. Question IDs do not change across versions. New
# questions append to a category; renames or removals require bumping
# `version`. Partial dialog files remain resumable across additive
# schema changes.
version: 1
categories:
  - id: intent
    title: "Statement of intent"
    questions:
      - id: intent.purpose
        text: "What does this repo do, in one sentence?"
        type: free_text
      - id: intent.audience
        text: "Who works on it (humans only / agents only / both)?"
        type: choice
        choices: ["humans only", "agents only", "both"]
      - id: intent.goal
        text: "What is the goal for the next 1-3 months?"
        type: free_text
  - id: problems
    title: "Problems to solve"
    questions:
      - id: problems.friction
        text: "What current friction do you want the protocol to address?"
        type: multi_choice
        choices: ["subagent coordination", "secrets handling", "parallel fanout", "long-running jobs", "other"]
      - id: problems.freeform
        text: "Any existing pain points to capture?"
        type: free_text
  - id: current_workflow
    title: "Current workflow playback"
    questions:
      - id: current_workflow.summary_accurate
        text: "Based on what we found, your current workflow looks like ... Is this accurate?"
        type: yes_no_revise
      - id: current_workflow.revisions
        text: "If not accurate, what should we revise in the summary?"
        type: free_text
  - id: integration
    title: "Integration preferences"
    questions:
      - id: integration.depth
        text: "Adoption depth?"
        type: choice
        choices: ["full", "partial (batch-job only)", "spec-only"]
      - id: integration.branch_naming
        text: "Branch naming overrides? (default agent/<issue>-<slug>)"
        type: free_text
      - id: integration.commands
        text: "Which commands to enable at start?"
        type: multi_choice
        choices: ["run-tests", "build", "deploy-staging", "echo"]
      - id: integration.fanout
        text: "Enable orchestrate-issue for parallel work?"
        type: yes_no
  - id: sensitive_files
    title: "Sensitive files"
    questions:
      - id: sensitive_files.list
        text: "Are there docs that should not be modified (besides AGENTS.md/CLAUDE.md)?"
        type: free_text
      - id: sensitive_files.confirm_added
        text: "Confirm the do-not-edit list above is complete?"
        type: yes_no_revise
  - id: confirmation
    title: "Confirmation"
    questions:
      - id: confirmation.recap_ok
        text: "Recap of answers; revise any?"
        type: yes_no_revise

```

### .claude/skills/onboarding/templates/recommendations-template.md

```text
# Onboarding recommendations — <repo>

<!--
This file is the agent's proposed integration of the agent-job
dispatch protocol into this repo. It is generated from the dialog
file by `lib/recommendations.py::render_recommendations`. The user
walks through each section in Phase 5 and approves or skips each
proposed change file-by-file.
-->

## Statement of intent

<!-- From the interview category `intent`. One paragraph + bullets. -->

- Purpose: `<from intent.purpose>`
- Audience: `<from intent.audience>`
- 1-3 month goal: `<from intent.goal>`

## Problems addressed

<!-- From the interview category `problems`. -->

- Friction addressed: `<from problems.friction>`
- Pain points captured: `<from problems.freeform>`

## Files to add (no edits to existing files)

<!-- The protocol skills install these themselves on first invocation.
     This list is informational so the user knows what the install
     footprint looks like. -->

- `.agent/config.json` (from batch-job/task-dag template)
- `.agent/scripts/...` (full inventory)
- `.github/workflows/lock-and-sweep.yml`
- `.github/workflows/batch-job-handler.yml`
- `.github/workflows/close-on-merge.yml`
- `.agent/schemas/...`

## Files proposed for additive edits (pointer-only)

<!-- The ONLY legal edit to AGENTS.md / CLAUDE.md is a single pointer
     line. Even this requires explicit per-file approval in Phase 5. -->

- `AGENTS.md`: add one line under a new "Agent-job protocol" section:
  > See `.agent/onboarding/recommendations.md` for protocol conventions.
- `CLAUDE.md`: identical pointer line.

## Files proposed for non-pointer edits

<!-- Only present if discovery found files that should be substantively
     modified — typically SPEC, README, PLAN, HANDOFF, ROADMAP, TODO.
     AGENTS.md and CLAUDE.md NEVER appear here.

     For each file: show the proposed diff and a one-sentence rationale. -->

- `<path>` — `<rationale>`
  - Diff preview: `<placeholder>`

## Before/after workflow

<!-- Two short paragraphs. -->

- **Today:** `<agent's summary of current dispatch model>`
- **After:** `<how the protocol changes dispatch>`

## Next steps if accepted

1. The onboarding skill will apply the proposed edits with your
   explicit per-file approval.
2. Run `/orchestrate-issue` on any unclaimed agent-task issue to
   exercise the new flow.
3. Re-run `/onboarding` later to revise integration choices.

```

### .claude/skills/orchestrate-issue/README.md

```text
This is the `orchestrate-issue` distributable skill. Entry point:
SKILL.md. Implementation spec: SPEC.md. Wraps batch-job + task-dag
into an end-to-end primary-agent loop with parallel subagent fanout.

```

### .claude/skills/orchestrate-issue/SKILL.md

````text
---
name: orchestrate-issue
description: |
  End-to-end primary-agent loop for one GitHub issue: claim, plan,
  fan out parallel subagents, run batch jobs, merge, open PR. Use
  when an agent needs to take a single issue from unclaimed to merged
  PR with parallel subagent execution. Self-installs the agent-job
  protocol templates on first invocation.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - mcp__github__*
---

# orchestrate-issue

End-to-end primary-agent loop for the agent-job protocol. This skill
takes a single GitHub issue from `status: null` (unclaimed) all the
way to a merged PR with a run report. It composes the `task-dag` and
`batch-job` primitives plus a parallel-subagent fanout pattern.

This is the **heavy adoption** skill. Users who prefer to compose the
primitives themselves should consult `composition-guide` and call
`task-dag` and `batch-job` directly.

The skill follows the parallel-subagent-fanout pattern from
software-factory, specialised to the agent-job protocol's branching
and acking model. Software-factory's skill is a reference pattern,
not an install-time dependency.

## Triggers

The skill matches when an agent is asked to:

- "Take this issue and finish it end-to-end"
- "Orchestrate the work on issue N"
- "Pick up the next unclaimed issue and ship it"
- "Run the full primary-agent loop"
- "Use the orchestrate-issue skill"

It does **not** match general "run tests" requests outside the
agent-job protocol — those route to `batch-job` directly.

## Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `issue_number` | int | no | If omitted, the skill scans for an unclaimed or stale issue |
| `agent_id` | string | no | Defaults to a generated UUID |
| `agent_login` | string | no | Resolved via `mcp__github__get_me` if omitted |
| `max_parallel` | int | no | Default 4. Cap on concurrent subagents per wave |
| `conflict_strategy` | enum | no | `fail` (default), `ours`, `theirs`, `manual` |
| `subagent_type` | string | no | Default `general-purpose`. Per the harness's Agent tool |
| `dry_run` | bool | no | Default False. Run Phases 0-3, stop before dispatch |

## Outputs

```json
{
  "issue_number": 42,
  "feature_branch": "agent/42-...",
  "subagent_branches": ["agent/42-...--sub-01", "..."],
  "pr_number": 123,
  "pr_url": "https://github.com/.../pull/123",
  "tests_delta": "+12",
  "run_report_path": ".agent/runs/<run_id>/report.md",
  "successors_scheduled": [],
  "elapsed_seconds": 1843
}
```

## Procedure (10 phases)

### Phase 0 — pre-flight

- Self-install protocol templates if missing (superset of `batch-job`
  + `task-dag` install logic; idempotent).
- Resolve `agent_login` via `mcp__github__get_me` if not provided.
- Generate `run_id` as `YYYYMMDD-HHMMSS` UTC.
- Detect any in-progress run for the same agent on the same feature
  branch — if found, jump to Phase Restart-Recovery.

### Phase 1 — claim

Delegate to `task-dag.claim` (Python helper at
`.agent/scripts/agent_lib/` plus the `task-dag` skill's `lib/`).
If no claimable issue is available and `issue_number` was not
provided, exit cleanly with `{"reason": "no_work"}`.

### Phase 2 — plan

Delegate to `task-dag.plan`. Convert the brief into a subagent layout:

```yaml
run_id: <run_id>
issue: <issue_number>
feature_branch: <feature_branch from agent-meta>
subtasks:
  - id: sub-01
    title: <short name>
    description: <one-sentence>
    files_touched: [<paths>]
    branch: <feature_branch>--sub-01
    command: <command to run via batch-job>
    args: { ... }
```

Subtasks must touch disjoint file paths. If the plan output suggests
overlap, the skill re-prompts for refinement. If refinement is
unavailable (unattended mode), fall back to serial single-subagent
execution.

### Phase 3 — write state.json

Write `.agent/runs/<run_id>/state.json`:

```json
{
  "run_id": "<run_id>",
  "issue_number": 42,
  "feature_branch": "agent/42-...",
  "subtasks": [
    {
      "id": "sub-01",
      "title": "...",
      "branch": "agent/42-...--sub-01",
      "status": "pending",
      "request_comment_id": null,
      "ack_comment_id": null,
      "subagent_pr": null,
      "tests_delta": null
    }
  ]
}
```

Commit and push `state.json` on the feature branch. This file is the
durability anchor for restart recovery.

### Phase 4 — create sub-branches

For each subtask, create `<feature_branch>--sub-<id>` from the current
feature-branch tip. Always use the **double-dash separator** (POC
SPEC §6). Never single-slash (`feature/sub-01`).

### Phase 5 — fanout (parallel)

Dispatch all subagents **in a single dispatcher message** using
multiple Agent tool calls. The harness only parallelises within one
message — splitting across messages serialises them.

Wave-limit by `max_parallel`:

- Wave 1: subagents `sub-01` … `sub-<max_parallel>`.
- Wait for all of wave 1 to complete.
- Wave 2: next batch.
- Continue until all dispatched.

Each Agent call uses `isolation: "worktree"` (critical — without it,
parallel subagents race on `git checkout` and contaminate each
other's branches).

Generate each subagent's brief from `templates/brief-template.md`
(this skill's internal template, not a target-repo template). The
brief is the 9-section subagent-prompting template, specialised for
the agent-job protocol. See `templates/brief-template.md` for the
exact section list and placeholder tokens.

### Phase 6 — collect

For each subagent's terminal report:

- Parse the deliverable (the subagent must include the structured
  fields enumerated in section 8 of the brief).
- Update `state.json`: set `status` to `dispatched_ok` or `failed`.
- Persist after each update (restart-safe).

If any subtask failed, the skill stops before merge and surfaces a
choice to the user: skip, retry, or abort. If running unattended
(overnight), the default is to **skip failed subtasks** and continue
with merge; the failures land in the run report.

### Phase 7 — merge in plan order

For each subtask with `status == dispatched_ok`, in plan order
(not completion order):

```bash
git checkout <feature_branch>
git merge --no-ff <feature_branch>--sub-<id>
```

Apply `conflict_strategy` on conflicts:

- `fail` (default) — surface to caller, halt merge phase.
- `ours` — keep the feature-branch side; record in run report.
- `theirs` — keep the subagent side; record in run report.
- `manual` — pause for user intervention.

Push the feature branch after each successful merge. Update
`state.json` to `merged` or `conflict` per subtask.

### Phase 8 — open PR

Open a PR from the feature branch to `base_branch` (read from
`agent-meta`). PR body includes:

- Run report summary table (one row per subtask)
- The `run_id`
- Links to all `batch-job` ack comments
- Any failed subtasks called out explicitly

On persistent PR-creation failure, write `.PENDING_PR.md` at the
feature-branch root with diagnostics, and exit with a typed error so
a human can recover.

### Phase 9 — finalise issue

Write `status: finished` into the issue's `agent-meta` block. Post a
final summary comment. Close the issue. The `close-on-merge.yml`
workflow then locks the issue when the PR merges (locking is
post-close, not at creation — POC SPEC §10.5).

### Phase 10 — schedule successors (optional)

If the plan or instructions defined successors, delegate to
`task-dag.schedule_successors`. Each successor is created with
`status: null` so any qualifying agent can claim it.

## Self-install

Superset of `batch-job` and `task-dag` install logic. Idempotent.
On invocation, the skill checks for the presence of:

| File or path | Action if missing |
|---|---|
| `.agent/config.json` | Copy from `templates/agent/config.json` |
| `.agent/scripts/common.py` | Copy from `templates/agent/scripts/common.py` |
| `.agent/scripts/rest_client.py` | Copy from `templates/agent/scripts/rest_client.py` |
| `.agent/scripts/handler.py` | Copy from `templates/agent/scripts/handler.py` |
| `.agent/scripts/requirements.txt` | Copy from `templates/agent/scripts/requirements.txt` |
| `.agent/scripts/lock_and_sweep.py` | Copy from `templates/agent/scripts/lock_and_sweep.py` |
| `.agent/scripts/close_on_merge.py` | Copy from `templates/agent/scripts/close_on_merge.py` |
| `.agent/scripts/agent_lib/` (directory) | Copy entire directory |
| `.agent/schemas/comment-envelope.schema.json` | Copy from `templates/agent/schemas/` |
| `.agent/schemas/comment-ack-envelope.schema.json` | Copy from `templates/agent/schemas/` |
| `.agent/schemas/log-manifest.schema.json` | Copy from `templates/agent/schemas/` |
| `.agent/schemas/issue-body.schema.json` | Copy from `templates/agent/schemas/` |
| `.agent/schemas/commands/` (directory) | Copy entire directory |
| `.agent/commands/` (directory) | Copy entire directory |
| `.github/workflows/batch-job-handler.yml` | Copy from `templates/github/workflows/` |
| `.github/workflows/lock-and-sweep.yml` | Copy from `templates/github/workflows/` |
| `.github/workflows/close-on-merge.yml` | Copy from `templates/github/workflows/` |
| `agent-task` label on the GitHub repo | Create via MCP (no schema match — REST POST) |
| `_agent_runs` orphan branch | Create empty orphan branch if missing |

Conflict handling on install:

1. If the target file is byte-identical to the bundled template — no-op.
2. If content differs — diff to the user, ask overwrite/skip/`.new`.
3. Skips are recorded in `.agent/installs/orchestrate-issue.log`.

`AGENTS.md` and `CLAUDE.md` are **never** in the installable file
list. Pointer-line edits to those files are the `onboarding` skill's
job, with explicit per-file user approval.

After install, the skill advertises the `onboarding` skill if the
well-known branch `agent-job-protocol/onboarding` does not exist.
Decline is fine — this skill works standalone.

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| No claimable issue | Phase 1 returns None | Exit cleanly with `{"reason": "no_work"}` |
| Plan produces overlapping subtasks | Phase 2 validation | Re-prompt; if unattended, fall back to serial single-subagent execution |
| Subagent fails | Phase 6 | Update state; skip in plan-order merge; record in run report |
| Merge conflict with strategy `fail` | Phase 7 | Stop; surface to user |
| PR creation fails | Phase 8 | Retry with backoff; on persistent failure write `.PENDING_PR.md` and exit with diagnostic |
| Restart mid-run | Restart detection in Phase 0 | Read `state.json`; resume from earliest incomplete phase |
| Heartbeat lost (parent issue stale) | `task-dag.heartbeat` raises | Surface immediately — claim has likely been swept |

## Restart recovery

The skill is restart-safe via `state.json`. On invocation, if a
`state.json` exists for an in-progress run on the feature branch and
the issue is still `working` under this `agent_id`:

- Resume from the earliest phase with incomplete state.
- Skip already-merged sub-branches.
- Skip already-acked `batch-job` comments.
- Re-collect subagent reports if their `request_comment_id` exists
  but `ack_comment_id` is null and the request comment is in terminal
  state.
- Continue Phase 5 only for subtasks whose `status` is still
  `pending` — never re-dispatch a subagent that already produced an
  ack.

## Anti-patterns

- **Do not** dispatch subagents across multiple messages. The harness
  only parallelises within a single message.
- **Do not** dispatch without `isolation: "worktree"`. Concurrent
  worktree-less subagents corrupt each other's branches.
- **Do not** merge in completion order. Always plan order.
- **Do not** open the PR before all in-plan-order merges succeed.
- **Do not** silently force-merge a conflict.
- **Do not** write `status: finished` to `agent-meta` until the PR
  is open.
- **Do not** invoke `batch-job` or `task-dag` via the Skill tool from
  inside this skill — call into their Python helpers instead (v1
  contract — too easy to recurse otherwise).
- **Do not** lock issues at creation; locking is post-close only.
- **Do not** use single-slash branch separators (`feature/sub-01`).
  Always double-dash (`feature--sub-01`).

## Dependencies

- Self-installs the protocol templates (superset of `batch-job` +
  `task-dag`).
- Internally calls into `batch-job` and `task-dag` logic (those
  skills' Python helpers, importable as a library — not Skill-tool
  invocations).
- Requires the harness's `Agent` tool for subagent dispatch.
- Requires a GitHub MCP server.

---
Version: 1.0.0
Protocol-version: 1
Last-synced-from-POC: 2026-05-14
---

````

### docs/skills/orchestrate-issue/SPEC.md

````text
# SPEC — orchestrate-issue skill

Status: design-stage
Audience: implementers of the skill in the new `pipeline-ai-sandbox` repo

## Purpose

Drive the **end-to-end primary-agent loop** for one issue:

1. Claim the issue (via `task-dag.claim`)
2. Plan subagents (via `task-dag.plan`)
3. Fan out parallel subagents — each owning one sub-branch
4. Each subagent runs `batch-job` against its branch
5. Merge subagent branches into the feature branch in plan order
6. Open the PR with run report
7. Optionally schedule successors

This is the "heavy adoption" skill: one invocation runs the whole
primary-agent's lifecycle for a single issue. Users who prefer the
primitives compose `task-dag` + `batch-job` themselves (see
`composition-guide`).

The skill implements the parallel-subagent-fanout pattern from
`software-factory/.claude/skills/parallel-subagent-fanout/SKILL.md`,
specialised to the agent-job protocol's branching and acking model.

## Trigger conditions

The skill matches when an agent is asked to:

- "Take this issue and finish it end-to-end"
- "Orchestrate the work on issue N"
- "Pick up the next unclaimed issue and ship it"
- "Run the full primary-agent loop"
- "Use the orchestrate-issue skill"

## Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `issue_number` | int | no | If omitted, the skill scans for an unclaimed or stale issue |
| `agent_id` | string | no | Defaults to a generated UUID |
| `agent_login` | string | no | Resolved via `mcp__github__get_me` if omitted |
| `max_parallel` | int | no | Default 4. Cap on concurrent subagents per wave |
| `conflict_strategy` | enum | no | `fail` (default), `ours`, `theirs`, `manual` |
| `subagent_type` | string | no | Default `general-purpose`. Per the harness's Agent tool |
| `dry_run` | bool | no | Default False. If True, run through plan + brief generation and stop before dispatching |

## Outputs

```json
{
  "issue_number": 42,
  "feature_branch": "agent/42-...",
  "subagent_branches": ["agent/42-...--sub-01", "..."],
  "pr_number": 123,
  "pr_url": "https://github.com/.../pull/123",
  "tests_delta": "+12",
  "run_report_path": ".agent/runs/<run_id>/report.md",
  "successors_scheduled": [],
  "elapsed_seconds": 1843
}
```

## Procedure

### Phase 0 — pre-flight

- Self-install protocol templates if missing (delegates to install
  logic shared with `batch-job` and `task-dag`).
- Resolve `agent_login` via `mcp__github__get_me` if not provided.
- Generate `run_id` as `YYYYMMDD-HHMMSS` UTC.

### Phase 1 — claim

Delegate to `task-dag.claim`. If no claimable issue is available and
`issue_number` was not provided, exit with `{"reason": "no_work"}`.

### Phase 2 — plan

Delegate to `task-dag.plan`. Convert the brief into a subagent layout:

```yaml
run_id: <run_id>
issue: <issue_number>
feature_branch: <feature_branch from agent-meta>
subtasks:
  - id: sub-01
    title: <short name>
    description: <one-sentence>
    files_touched: [<paths>]
    branch: <feature_branch>--sub-01
    command: <command to run via batch-job>
    args: { ... }
```

Subtasks must touch disjoint file paths. If the plan output suggests
overlap, the skill re-prompts for refinement.

### Phase 3 — write state.json

Write `.agent/runs/<run_id>/state.json`:

```json
{
  "run_id": "<run_id>",
  "issue_number": <n>,
  "feature_branch": "<>",
  "subtasks": [
    {
      "id": "sub-01",
      "title": "...",
      "branch": "...--sub-01",
      "status": "pending",
      "request_comment_id": null,
      "ack_comment_id": null,
      "subagent_pr": null,
      "tests_delta": null
    }
  ]
}
```

Commit and push the state file on the feature branch.

### Phase 4 — create sub-branches

For each subtask, create `<feature_branch>--sub-<id>` from the current
feature-branch tip. Double-dash separator (POC SPEC §6).

### Phase 5 — fanout (parallel)

Dispatch all subagents **in a single dispatcher message** using
multiple Agent tool calls. Wave-limit by `max_parallel`:

- Wave 1: subagents `sub-01` … `sub-<max_parallel>`
- Wait for all of wave 1 to complete
- Wave 2: next batch
- Continue until all dispatched

Each Agent call uses `isolation: "worktree"` (critical — without it,
parallel subagents race on `git checkout` and contaminate each other's
branches).

Each subagent's brief follows the subagent-prompting 9-section
template, specialised for the agent-job protocol:

1. **Identity + goal** — "You are sub-<id> for issue <n>. Your task: <description>."
2. **Context** — the issue's body, the spec path, the run_id.
3. **Repo and branch** — explicit "commit to <feature_branch>--sub-<id> ONLY".
4. **What to build** — 3-7 specific bullets derived from the subtask.
5. **Protocol contract** — "When done, invoke the `batch-job` skill with command `<>`, args `<>`, branch `<feature_branch>--sub-<id>`, commit_sha `<HEAD>`. Wait for terminal ack. Report back."
6. **Don'ts** — do not merge, do not switch branches, do not touch files outside your `files_touched` list.
7. **Validation** — assert local git state matches expected before reporting.
8. **Deliverable shape** — exact report format (sub-branch, batch-job comment id, batch-job summary, tests delta, issues).
9. **Traps** — double-dash separator, MCP comment-trailer tolerance, etc.

### Phase 6 — collect

For each subagent's report:

- Parse the deliverable.
- Update `state.json`: set `status` to `dispatched_ok` or `failed`.
- Persist after each update (restart-safe).

If any subtask failed, the skill stops before merge and surfaces a
choice to the user: skip, retry, or abort. If the skill is running
unattended (overnight), the default is to **skip failed subtasks**
and continue with merge; the failures land in the run report.

### Phase 7 — merge in plan order

For each subtask in plan order with `status == dispatched_ok`:

```bash
git checkout <feature_branch>
git merge --no-ff <feature_branch>--sub-<id>
```

Apply `conflict_strategy` on conflicts. Push the feature branch after
each successful merge. Update `state.json` to `merged` or `conflict`.

### Phase 8 — open PR

Open a PR from the feature branch to `base_branch` (read from
`agent-meta`). PR body includes:

- Run report summary table (one row per subtask)
- The run_id
- Links to all batch-job ack comments
- Any failed subtasks called out

### Phase 9 — finalise issue

Write `status: finished` into the `agent-meta` block. Post a final
comment summarising the work. Close the issue. (The
`close-on-merge.yml` workflow handles the lock when the PR merges.)

### Phase 10 — schedule successors (optional)

If the plan or instructions defined successors, create them via
`task-dag.schedule_successors`.

## Self-install logic

Superset of `batch-job` and `task-dag` install logic. Idempotent.
After install, advertises the onboarding skill if not yet run.

## Bundled templates

Same as `task-dag` (which is a superset of `batch-job`). No new
templates unique to this skill — it composes the others'.

The skill does carry one new file inside its own directory (not a
target-repo template):

```
templates/
  brief-template.md     # the 9-section subagent brief template
```

Used internally during Phase 5 to generate briefs.

## SKILL.md frontmatter

```yaml
---
name: orchestrate-issue
description: |
  End-to-end primary-agent loop for one GitHub issue: claim, plan,
  fan out parallel subagents, run batch jobs, merge, open PR. Use
  when an agent needs to take a single issue from unclaimed to merged
  PR with parallel subagent execution. Self-installs the agent-job
  protocol templates on first invocation.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - mcp__github__*
---
```

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| No claimable issue | Phase 1 returns None | Exit cleanly with `{"reason": "no_work"}` |
| Plan produces overlapping subtasks | Phase 2 validation | Re-prompt; if user-driven mode unavailable, fall back to serial single-subagent execution |
| Subagent fails | Phase 6 | Update state; skip in plan-order merge; record in run report |
| Merge conflict with strategy `fail` | Phase 7 | Stop; surface to user |
| PR creation fails | Phase 8 | Retry with backoff; on persistent failure write a `.PENDING_PR.md` and exit with diagnostic |
| Restart mid-run | Restart detection | Read `state.json`; resume from earliest incomplete phase |

## Restart recovery

The skill is restart-safe via `state.json`. On invocation, if a
`state.json` exists for an in-progress run on the feature branch and
the issue is still `working` under this `agent_id`:

- Resume from the earliest phase with incomplete state.
- Skip already-merged sub-branches.
- Skip already-acked batch-job comments.
- Re-collect subagent reports if their `request_comment_id` exists but `ack_comment_id` is null and the request comment is in terminal state.

## Tests

### In this POC

- Contract test (templates are byte-equivalent).
- Dry-run mode: run Phases 0-3 against a mock GitHub client, verify state.json is correctly shaped.
- Subagent brief generator: assert generated briefs follow the 9-section template against a fixture plan.

### In the new repo

- Full e2e: drive an orchestrate-issue invocation against a synthetic archetype in the test harness. Verify PR opens, all sub-branches merge, all batch-jobs complete, run report is written.
- Conflict-injection: deliberately create overlapping subtasks; assert the conflict_strategy options each produce the expected outcome.
- Restart test: kill the orchestrator mid-fanout; restart; verify completion.
- Wave-limit test: dispatch 9 subagents with max_parallel=4; assert two waves of 4 + one wave of 1.

## Anti-patterns

- **Do not** dispatch subagents across multiple messages. The harness only parallelises within a single message.
- **Do not** dispatch without `isolation: "worktree"`. Concurrent worktree-less subagents corrupt each other's branches.
- **Do not** merge in completion order. Always plan order.
- **Do not** open the PR before all in-plan-order merges succeed.
- **Do not** silently force-merge a conflict.
- **Do not** write `status: finished` to `agent-meta` until the PR is open.

## Dependencies

- Self-installs the protocol templates (superset of `batch-job` + `task-dag`).
- Internally calls into `batch-job` and `task-dag` logic (those skills' Python helpers, importable as a library).
- Requires the harness's `Agent` tool for subagent dispatch.
- Requires a GitHub MCP server.

````

### .claude/skills/orchestrate-issue/lib/__init__.py

```text
"""orchestrate-issue skill — Python helper package.

This package houses the orchestrator's docstring-level reference
implementation. The actual primary-agent loop is composed by
``SKILL.md`` invoking the Agent tool and the ``batch-job`` and
``task-dag`` skills' Python helpers (importable from
``.agent/scripts/agent_lib``).
"""

```

### .claude/skills/orchestrate-issue/lib/orchestrate.py

```text
"""orchestrate-issue — 10-phase primary-agent loop.

This module is a **docstring-level stub**. The actual orchestration is
performed by the SKILL.md procedure invoking the harness's Agent tool
and composing the ``batch-job`` and ``task-dag`` skills' Python helpers
(canonically installed at ``.agent/scripts/agent_lib``).

The function signatures below mirror the inputs and outputs documented
in ``SPEC.md``. They are present here so callers and tests have a
stable Python surface to import against; runtime behavior is delegated
to the SKILL.md flow plus the installed ``agent_lib`` and the sibling
``task-dag`` / ``batch-job`` ``lib/`` packages.

The 10 phases (see ``SKILL.md`` for full detail):

    0. pre-flight       — self-install, run_id, resume detection
    1. claim            — delegate to task-dag.claim
    2. plan             — delegate to task-dag.plan
    3. write state.json — durability anchor on the feature branch
    4. create sub-branches — double-dash separator (POC SPEC §6)
    5. fanout (parallel) — Agent tool, isolation=worktree, single message
    6. collect          — parse deliverables, update state.json
    7. merge in plan order — task-dag.merge_subagent_branches
    8. open PR          — feature_branch -> base_branch
    9. finalise issue   — write status=finished, close issue
   10. schedule successors — task-dag.schedule_successors (optional)

These functions are documented but not implemented at runtime — the
SKILL.md procedure is the canonical execution path. The
``parallel-subagent-fanout`` skill from software-factory is a pattern
reference, not an install-time dependency.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


def orchestrate_issue(
    issue_number: Optional[int] = None,
    agent_id: Optional[str] = None,
    agent_login: Optional[str] = None,
    max_parallel: int = 4,
    conflict_strategy: str = "fail",
    subagent_type: str = "general-purpose",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Drive the end-to-end primary-agent loop for one issue.

    Inputs
    ------
    issue_number : int, optional
        If omitted, the skill scans for an unclaimed or stale issue.
    agent_id : str, optional
        Defaults to a generated UUID.
    agent_login : str, optional
        Resolved via ``mcp__github__get_me`` when omitted.
    max_parallel : int
        Cap on concurrent subagents per wave. Default 4.
    conflict_strategy : str
        One of ``fail`` (default), ``ours``, ``theirs``, ``manual``.
    subagent_type : str
        Per the harness's Agent tool. Default ``general-purpose``.
    dry_run : bool
        If True, run Phases 0-3 and stop before dispatch.

    Returns
    -------
    dict
        Shape per ``SPEC.md`` Outputs::

            {
                "issue_number": int,
                "feature_branch": str,
                "subagent_branches": list[str],
                "pr_number": int,
                "pr_url": str,
                "tests_delta": str,
                "run_report_path": str,
                "successors_scheduled": list[int],
                "elapsed_seconds": int,
            }

    Notes
    -----
    Stub. Actual orchestration lives in ``SKILL.md`` plus the installed
    ``.agent/scripts/agent_lib`` package and the sibling ``task-dag``
    and ``batch-job`` ``lib/`` packages.
    """
    raise NotImplementedError(
        "orchestrate_issue is a docstring stub; see SKILL.md for the "
        "canonical 10-phase procedure."
    )


def phase_0_preflight(run_id: Optional[str] = None) -> dict[str, Any]:
    """Phase 0 — pre-flight checks and self-install.

    - Self-install protocol templates if missing (superset of
      batch-job + task-dag install logic; idempotent).
    - Resolve ``agent_login`` via ``mcp__github__get_me`` if absent.
    - Generate ``run_id`` as ``YYYYMMDD-HHMMSS`` UTC.
    - Detect any in-progress run for the same agent on the same
      feature branch and jump to restart recovery.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_1_claim(
    agent_id: str,
    agent_login: str,
    issue_number: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    """Phase 1 — claim the issue via task-dag.claim.

    Returns ``None`` if no claimable issue is available and
    ``issue_number`` was not provided; the caller surfaces
    ``{"reason": "no_work"}`` in that case.

    Stub. Delegates to the installed ``task-dag.claim`` Python helper.
    """
    raise NotImplementedError


def phase_2_plan(issue_number: int, agent_login: str) -> dict[str, Any]:
    """Phase 2 — plan subagents via task-dag.plan.

    Returns the subagent layout per the YAML shape in SPEC.md.
    Subtasks must touch disjoint file paths.

    Stub. Delegates to the installed ``task-dag.plan`` Python helper.
    """
    raise NotImplementedError


def phase_3_write_state(
    run_id: str,
    issue_number: int,
    feature_branch: str,
    subtasks: list[dict[str, Any]],
) -> str:
    """Phase 3 — write ``.agent/runs/<run_id>/state.json``.

    Commits and pushes the state file on the feature branch. Returns
    the absolute path to the written state.json.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_4_create_sub_branches(
    feature_branch: str,
    subtasks: list[dict[str, Any]],
) -> list[str]:
    """Phase 4 — create ``<feature_branch>--<sub_id>`` for each subtask.

    Double-dash separator (POC SPEC §6). Never single-slash.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_5_fanout(
    subtasks: list[dict[str, Any]],
    max_parallel: int,
    subagent_type: str,
    brief_template_path: str,
    heartbeat: Optional[Callable[[], None]] = None,
) -> list[dict[str, Any]]:
    """Phase 5 — dispatch subagents in waves via the Agent tool.

    All Agent calls in one wave go in a **single dispatcher message**;
    the harness only parallelises within one message. Each call uses
    ``isolation: "worktree"`` to prevent branch contamination.

    Briefs are rendered from ``templates/brief-template.md`` (the
    9-section subagent-prompting template specialised for the
    agent-job protocol).

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_6_collect(reports: list[dict[str, Any]], state_path: str) -> dict[str, Any]:
    """Phase 6 — parse subagent reports and update state.json.

    Sets each subtask's ``status`` to ``dispatched_ok`` or ``failed``.
    Persists after each update for restart-safety.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_7_merge(
    feature_branch: str,
    subagent_branches: list[str],
    conflict_strategy: str = "fail",
) -> dict[str, Any]:
    """Phase 7 — merge sub-branches in plan order (not completion order).

    Delegates to the installed ``task-dag.merge_subagent_branches``.
    Returns ``{"merged": [...], "conflicts": [...], "skipped": [...]}``.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_8_open_pr(
    feature_branch: str,
    base_branch: str,
    issue_number: int,
    run_report_path: str,
) -> dict[str, Any]:
    """Phase 8 — open the PR from feature_branch to base_branch.

    Returns ``{"pr_number": int, "pr_url": str}``. On persistent
    failure writes ``.PENDING_PR.md`` and raises a typed error.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_9_finalise_issue(issue_number: int, pr_url: str) -> None:
    """Phase 9 — write ``status: finished`` and close the issue.

    The ``close-on-merge.yml`` workflow handles the post-close lock
    when the PR merges.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


def phase_10_schedule_successors(
    successors: list[dict[str, Any]],
    base_branch: str,
) -> list[int]:
    """Phase 10 — create successor issues with ``status: null``.

    Delegates to the installed ``task-dag.schedule_successors``.

    Stub. See SKILL.md.
    """
    raise NotImplementedError


__all__ = [
    "orchestrate_issue",
    "phase_0_preflight",
    "phase_1_claim",
    "phase_2_plan",
    "phase_3_write_state",
    "phase_4_create_sub_branches",
    "phase_5_fanout",
    "phase_6_collect",
    "phase_7_merge",
    "phase_8_open_pr",
    "phase_9_finalise_issue",
    "phase_10_schedule_successors",
]

```

### .claude/skills/orchestrate-issue/templates/agent/commands/__init__.py

```text
"""Command handler modules. Each command is a sibling module exposing
``run(args, log_writer, workspace) -> dict`` returning the summary."""

```

### .claude/skills/orchestrate-issue/templates/agent/commands/bad_summary.py

```text
"""``bad-summary`` test command — intentionally returns invalid summary.

Used by harness scenario 07 (``07_summary_schema_violation.md``) to
exercise the handler's defense-in-depth ``summary_schema_violation``
path. The schema demands ``required_field`` in the completed summary,
but this handler returns ``{}`` so the validator must reject it.
"""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": "bad-summary about to return invalid summary",
    })
    # Intentionally missing the schema-required ``required_field``.
    return {}

```

### .claude/skills/orchestrate-issue/templates/agent/commands/build.py

```text
"""``build`` command stub. Pretends to build a target."""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    target = args.get("target", "default")
    release = bool(args.get("release", False))

    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "setup",
        "data": {"msg": "build started", "target": target, "release": release},
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": f"compiling {target}{' (release)' if release else ''}",
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "teardown",
        "data": {"msg": "build complete"},
    })

    artifact = f"build/out/{target}{'-release' if release else ''}.bin"
    return {
        "artifact_path": artifact,
        "size_bytes": 1024 * (4096 if release else 2048),
        "duration_seconds": 3.5 if release else 1.25,
    }

```

### .claude/skills/orchestrate-issue/templates/agent/commands/chatty.py

```text
"""``chatty`` test command — emits many log records to force chunk rotation.

Used by harness scenario 12 (``12_huge_log.md``). Args:

- ``lines`` (int, default 500): number of log records to emit.
- ``max_chunk_bytes_compressed`` (int, default 8192): rotation threshold
  applied to the LogWriter for this invocation only. The production
  default (524 288 bytes) remains untouched for non-test commands.

Rationale: live execution showed that triggering rotation at the full
production threshold required ~20 000 lines, which is timing-sensitive
and slow on real GitHub Actions runners. Lowering the per-invocation
threshold for the test command makes rotation fire reliably with a
modest line count, while production defaults are preserved because
chatty calls :py:meth:`LogWriter.set_max_chunk_bytes` itself rather
than mutating any shared config.

Each emitted record carries a high-entropy (per-line unique) payload so
that gzip cannot dedupe the stream down below the rotation threshold —
without this, 500 highly-repetitive lines compressed to <8 KB and never
rotated.
"""

from __future__ import annotations

import hashlib
from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ))
    from common import iso_now  # type: ignore[import-not-found]


def _entropy_payload(i: int, length: int = 192) -> str:
    """Build a high-entropy, per-line-unique string of ~``length`` chars.

    gzip compresses repeated text aggressively, so a constant pad would
    let 500 lines compress well below an 8 KiB rotation threshold. We
    derive a chain of SHA-256 hex digests seeded by ``i`` and concatenate
    them — this is effectively incompressible and grows linearly with
    line count.
    """
    out_parts: list[str] = []
    seed = f"chatty-line-{i:08d}".encode("utf-8")
    h = hashlib.sha256(seed).hexdigest()  # 64 hex chars
    out_parts.append(h)
    while sum(len(p) for p in out_parts) < length:
        h = hashlib.sha256(h.encode("utf-8")).hexdigest()
        out_parts.append(h)
    return "-".join(out_parts)[:length]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    # Override the rotation threshold up-front so every record we emit
    # is governed by the test-friendly size.
    max_chunk = int(args.get("max_chunk_bytes_compressed", 8192))
    log_writer.set_max_chunk_bytes(max_chunk)

    n = int(args.get("lines", 500))
    if n < 0:
        n = 0
    for i in range(n):
        log_writer.write({
            "ts": iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": f"line {i:08d} {_entropy_payload(i)}",
        })
    return {
        "lines_emitted": n,
        "message": f"chatty emitted {n} lines",
    }

```

### .claude/skills/orchestrate-issue/templates/agent/commands/echo.py

```text
"""``echo`` command: trivial demonstration handler.

Echoes its args back inside the summary. Useful for end-to-end POC
testing without depending on any synthetic test data.
"""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    message = str(args.get("message", "")) or "hello"
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": message,
    })
    return {
        "echoed_args": dict(args),
        "message": message,
    }

```

### .claude/skills/orchestrate-issue/templates/agent/commands/run_tests.py

```text
"""``run-tests`` command stub.

Pretends to run a suite and returns a fake-but-realistic summary that
conforms to ``commands/run-tests.schema.json``'s ``summary_completed``
shape. Streams a few records through ``log_writer`` so the manifest
contains real chunks.
"""

from __future__ import annotations

import random
from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    """Execute the (faked) test command.

    ``args`` is already validated against the command schema by the
    handler, so ``suite`` is guaranteed present.
    """
    suite = args["suite"]
    shard = args.get("shard")
    filter_ = args.get("filter")

    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "setup",
        "data": {
            "msg": "starting run-tests",
            "suite": suite,
            "shard": shard,
            "filter": filter_,
        },
    })

    # Deterministic-ish fake numbers based on suite size.
    base_counts = {"unit": 120, "integration": 40, "e2e": 12}
    total = base_counts.get(suite, 25)
    rng = random.Random(f"{suite}:{shard}:{filter_}")

    failed = rng.randint(0, max(1, total // 25))
    skipped = rng.randint(0, max(1, total // 30))
    passed = total - failed - skipped
    duration = round(rng.uniform(2.0, 12.0) + total * 0.1, 2)

    failed_tests: list[dict[str, str]] = []
    for i in range(failed):
        log_writer.write({
            "ts": iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": f"FAIL test_{suite}_{i}",
        })
        failed_tests.append({
            "name": f"test_{suite}_{i}",
            "message": "AssertionError: synthetic failure",
        })

    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": f"ran {total} {suite} tests in {duration}s",
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "teardown",
        "data": {"msg": "run-tests complete"},
    })

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_seconds": duration,
        "failed_tests": failed_tests,
    }

```

### .claude/skills/orchestrate-issue/templates/agent/config.json

```text
{
  "protocol_version": 1,
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
    "subagent_pattern": "<feature_branch>--sub-<subagent_id>"
  },
  "commands": ["run-tests", "build", "echo", "bad-summary", "chatty"]
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/commands/bad-summary.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/bad-summary.schema.json",
  "title": "bad-summary",
  "description": "Test command whose handler intentionally returns an invalid summary so the handler's summary_schema_violation path is exercised.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "additionalProperties": true
    },
    "summary_completed": {
      "type": "object",
      "required": ["required_field"],
      "properties": {
        "required_field": { "type": "string" }
      },
      "additionalProperties": true
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/commands/build.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/build.schema.json",
  "title": "build",
  "description": "Schema for the build command. Stub for the POC.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "target": { "type": "string", "minLength": 1 },
        "release": { "type": "boolean" }
      },
      "additionalProperties": false
    },
    "summary_completed": {
      "type": "object",
      "required": ["artifact_path", "size_bytes", "duration_seconds"],
      "properties": {
        "artifact_path": { "type": "string" },
        "size_bytes": { "type": "integer", "minimum": 0 },
        "duration_seconds": { "type": "number", "minimum": 0 }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/commands/chatty.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/chatty.schema.json",
  "title": "chatty",
  "description": "Test command that emits many log records to force chunk rotation.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "lines": { "type": "integer", "minimum": 0 },
        "max_chunk_bytes_compressed": { "type": "integer", "minimum": 1 }
      },
      "additionalProperties": false
    },
    "summary_completed": {
      "type": "object",
      "required": ["lines_emitted", "message"],
      "properties": {
        "lines_emitted": { "type": "integer", "minimum": 0 },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/commands/echo.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/echo.schema.json",
  "title": "echo",
  "description": "Schema for the echo command: trivial demonstration command that returns its args.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "message": { "type": "string" }
      },
      "additionalProperties": true
    },
    "summary_completed": {
      "type": "object",
      "required": ["echoed_args", "message"],
      "properties": {
        "echoed_args": { "type": "object" },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/commands/run-tests.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/run-tests.schema.json",
  "title": "run-tests",
  "description": "Schema for the run-tests command: validates args and the produced summary.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
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
        "duration_seconds": { "type": "number", "minimum": 0 },
        "failed_tests": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name"],
            "properties": {
              "name": { "type": "string" },
              "message": { "type": "string" }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/comment-ack-envelope.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/comment-ack-envelope.schema.json",
  "title": "comment envelope (agent-ack)",
  "description": "Follow-up comment that acknowledges a batch-job-request without editing it in place.",
  "type": "object",
  "required": ["protocol_version", "kind", "ack_for", "agent_acked_at"],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "kind": { "type": "string", "const": "agent-ack" },
    "ack_for": { "type": "integer", "minimum": 1 },
    "agent_acked_at": { "type": "string", "format": "date-time" },
    "agent_id": { "type": ["string", "null"] },
    "session_id": { "type": ["string", "null"] },
    "note": { "type": ["string", "null"] }
  },
  "additionalProperties": true
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/comment-envelope.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/comment-envelope.schema.json",
  "title": "comment envelope (batch-job-request)",
  "description": "Lifecycle-aware schema for comment-body envelopes. Supports request, post-run, and parse_error shapes.",
  "type": "object",
  "required": ["protocol_version", "kind"],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "kind": { "type": "string", "const": "batch-job-request" },
    "command": { "type": "string", "minLength": 1 },
    "args": { "type": "object" },
    "branch": { "type": "string", "minLength": 1 },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{40}$"
    },
    "subagent_id": { "type": "string", "minLength": 1 },
    "submitted_at": { "type": "string", "format": "date-time" },

    "run_status": {
      "type": ["string", "null"],
      "enum": [null, "running", "completed", "error", "parse_error"]
    },
    "run_started_at": { "type": ["string", "null"], "format": "date-time" },
    "run_finished_at": { "type": ["string", "null"], "format": "date-time" },
    "workflow_run_id": { "type": ["integer", "null"] },
    "checked_out_sha": {
      "type": ["string", "null"],
      "pattern": "^[0-9a-f]{40}$"
    },
    "summary": { "type": ["object", "null"] },
    "log_manifest_branch": { "type": ["string", "null"] },
    "log_manifest_path": { "type": ["string", "null"] },

    "agent_ack": {
      "type": ["string", "null"],
      "enum": [null, "finished"]
    },
    "agent_acked_at": { "type": ["string", "null"], "format": "date-time" },

    "error_kind": { "type": ["string", "null"] },
    "error_detail": { "type": ["string", "null"] },
    "original_body_b64": { "type": ["string", "null"] }
  },
  "allOf": [
    {
      "description": "If run_status is null/running/completed/error (i.e. a real request was submitted), the request fields must be present.",
      "if": {
        "properties": {
          "run_status": { "enum": [null, "running", "completed", "error"] }
        }
      },
      "then": {
        "required": ["command", "args", "branch", "commit_sha", "subagent_id", "submitted_at"]
      }
    },
    {
      "description": "If run_status is 'completed', summary and log manifest fields are required.",
      "if": {
        "properties": { "run_status": { "const": "completed" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id",
          "checked_out_sha",
          "summary",
          "log_manifest_branch",
          "log_manifest_path"
        ]
      }
    },
    {
      "description": "If run_status is 'error', error_kind and run timing must be present.",
      "if": {
        "properties": { "run_status": { "const": "error" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id",
          "error_kind"
        ]
      }
    },
    {
      "description": "If run_status is 'parse_error', original_body_b64 and error_kind must be present.",
      "if": {
        "properties": { "run_status": { "const": "parse_error" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "error_kind",
          "original_body_b64",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id"
        ]
      }
    }
  ],
  "additionalProperties": true
}

```

### .claude/skills/orchestrate-issue/templates/agent/schemas/issue-body.schema.json

````text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/issue-body.schema.json",
  "title": "agent-meta block (issue body)",
  "description": "Schema for the JSON object inside an issue body's fenced ```agent-meta block.",
  "type": "object",
  "required": [
    "protocol_version",
    "agent_id",
    "session_id",
    "status",
    "status_ts",
    "feature_branch",
    "base_branch",
    "parent_issue",
    "depends_on_prs",
    "instructions_path",
    "instructions_inline",
    "created_at"
  ],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "agent_id": { "type": ["string", "null"] },
    "session_id": { "type": ["string", "null"] },
    "status": {
      "type": ["string", "null"],
      "enum": [null, "working", "abandoned", "finished"]
    },
    "status_ts": {
      "type": ["string", "null"],
      "format": "date-time"
    },
    "feature_branch": { "type": "string", "minLength": 1 },
    "base_branch": { "type": "string", "minLength": 1 },
    "parent_issue": { "type": ["integer", "null"], "minimum": 1 },
    "depends_on_prs": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 }
    },
    "instructions_path": { "type": ["string", "null"] },
    "instructions_inline": { "type": ["string", "null"] },
    "created_at": { "type": "string", "format": "date-time" }
  },
  "anyOf": [
    { "properties": { "instructions_inline": { "type": "string", "minLength": 1 } }, "required": ["instructions_inline"] },
    { "properties": { "instructions_path": { "type": "string", "minLength": 1 } }, "required": ["instructions_path"] }
  ],
  "additionalProperties": true
}

````

### .claude/skills/orchestrate-issue/templates/agent/schemas/log-manifest.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/log-manifest.schema.json",
  "title": "log manifest",
  "description": "Schema for runs/<issue>/<comment>/manifest.json on the _agent_runs orphan branch.",
  "type": "object",
  "required": [
    "protocol_version",
    "schema",
    "command",
    "args",
    "checked_out_sha",
    "started_at",
    "finished_at",
    "exit_code",
    "chunks"
  ],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "schema": {
      "type": "object",
      "required": ["chunk_format", "fields"],
      "properties": {
        "chunk_format": { "type": "string", "const": "jsonl-gz" },
        "fields": { "type": "object" }
      }
    },
    "command": { "type": "string", "minLength": 1 },
    "args": { "type": "object" },
    "checked_out_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,64}$"
    },
    "started_at": { "type": "string", "format": "date-time" },
    "finished_at": { "type": "string", "format": "date-time" },
    "exit_code": { "type": "integer" },
    "chunks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "bytes", "lines"],
        "properties": {
          "path": { "type": "string", "minLength": 1 },
          "bytes": { "type": "integer", "minimum": 0 },
          "lines": { "type": "integer", "minimum": 0 }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": true
}

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/agent_lib/__init__.py

```text
"""Pure-Python helpers for the agent-mode harness.

This package is the agent-side counterpart to the workflow-side handler.

The dispatcher AI cannot pass MCP tools as Python callables, so the
"skill" lifecycle in agent mode is split into:

- Pure helpers (here): envelope construction, agent-meta marshalling,
  terminal-status parsing, summary path derivation, schema validation.
- Markdown playbooks (under ``harness/scenarios/``): tell the agent
  which MCP calls to make and in what order.

Pure helpers run inside the sandbox — invoked via ``python -m agent_lib
<sub> ...``; the printed JSON is consumed by the agent's tool-use
stream.

This module deliberately performs **no** I/O against GitHub.
"""

from __future__ import annotations

from .envelope import (
    EnvelopeArgsInvalid,
    make_ack_envelope,
    make_request_envelope,
)
from .meta import (
    abandon_meta,
    claim_meta,
    finish_meta,
    heartbeat_meta,
    make_initial_meta,
    parse_body,
    render_body,
    replace_meta_in_body,
)
from .poll import (
    is_request_acked,
    is_terminal,
    manifest_path_for,
    parse_ack_comment,
    parse_terminal_status,
    summary_path_for,
)


__all__ = [
    "EnvelopeArgsInvalid",
    "abandon_meta",
    "claim_meta",
    "finish_meta",
    "heartbeat_meta",
    "is_request_acked",
    "is_terminal",
    "make_ack_envelope",
    "make_initial_meta",
    "make_request_envelope",
    "manifest_path_for",
    "parse_ack_comment",
    "parse_body",
    "parse_terminal_status",
    "render_body",
    "replace_meta_in_body",
    "summary_path_for",
]

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/agent_lib/__main__.py

```text
"""Make ``python -m agent_lib`` invoke the CLI."""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/agent_lib/_common_loader.py

```text
"""Locate and load the central ``common.py`` module by file path.

The agent-mode helpers run from many entry points (CLI, tests,
imported by subagents). We deliberately keep the import shape as
robust as ``skills/batch-job/common.py`` so a stray ``common`` already
in ``sys.modules`` does not break us.
"""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def locate_repo_root(start: Path | None = None) -> Path:
    """Walk upwards from ``start`` looking for ``.agent/config.json``."""
    here = (start or Path(__file__)).resolve()
    candidates = [here] if here.is_dir() else [here.parent, *here.parents]
    for parent in candidates:
        if (parent / ".agent" / "config.json").exists():
            return parent
    raise RuntimeError("could not locate repo root (no .agent/config.json found)")


REPO_ROOT = locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_common() -> ModuleType:
    """Return the central agent-protocol ``common`` module, loaded once."""
    name = "agent_protocol_common"
    if name in sys.modules:
        return sys.modules[name]
    path = REPO_ROOT / ".agent" / "scripts" / "common.py"
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - import path
        raise RuntimeError(f"could not load common module from {path}")
    mod = module_from_spec(spec)
    sys.modules[name] = mod  # register before exec so dataclasses work
    spec.loader.exec_module(mod)
    return mod

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/agent_lib/cli.py

```text
"""Thin CLI wrapper around the pure helpers.

Designed to be invoked by the dispatcher agent via ``Bash`` calls of
the form::

    python -m agent_lib <subcommand> <positional args> [--option ...]

All subcommands print JSON to stdout (the parsed structure or the
markdown body) so the agent can pipe the result into a subsequent MCP
call. Validation failures exit with a non-zero status; the error
message goes to stderr as a single ``{"error": "..."}`` JSON object.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional

from . import (
    EnvelopeArgsInvalid,
    abandon_meta,
    claim_meta,
    finish_meta,
    heartbeat_meta,
    make_ack_envelope,
    make_initial_meta,
    make_request_envelope,
    parse_body,
    parse_terminal_status,
    render_body,
    summary_path_for,
)
from ._common_loader import REPO_ROOT, load_common
from .meta import replace_meta_in_body


_common = load_common()


def _die(msg: str, code: int = 1) -> None:
    sys.stderr.write(json.dumps({"error": msg}) + "\n")
    raise SystemExit(code)


def _loads(s: str, *, name: str) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError) as e:
        _die(f"{name}: invalid JSON: {e}")


def _print(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------

def cmd_make_request(ns: argparse.Namespace) -> int:
    args = _loads(ns.args_json, name="args")
    if not isinstance(args, dict):
        _die("args must be a JSON object")
    try:
        env = make_request_envelope(
            ns.command,
            args,
            ns.branch,
            ns.sha,
            ns.subagent_id,
            validate_args=not ns.no_validate,
        )
    except EnvelopeArgsInvalid as e:
        _die(str(e))
    except (TypeError, ValueError) as e:
        _die(str(e))
    _print(env)
    return 0


def cmd_make_ack(ns: argparse.Namespace) -> int:
    try:
        env = make_ack_envelope(
            ns.ack_for,
            agent_id=ns.agent_id,
            session_id=ns.session_id,
            note=ns.note,
        )
    except ValueError as e:
        _die(str(e))
    _print(env)
    return 0


def cmd_make_initial_meta(ns: argparse.Namespace) -> int:
    payload = _loads(ns.json_payload, name="payload")
    if not isinstance(payload, dict):
        _die("payload must be a JSON object")
    try:
        meta = make_initial_meta(**payload)
    except TypeError as e:
        _die(f"unsupported arguments: {e}")
    except ValueError as e:
        _die(str(e))
    body = render_body(meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_claim_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    try:
        new_meta = claim_meta(meta, ns.agent_id, ns.session_id)
    except ValueError as e:
        _die(str(e))
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_heartbeat_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = heartbeat_meta(meta)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_finish_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = finish_meta(meta)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_abandon_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = abandon_meta(meta, ns.reason)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_parse_comment(ns: argparse.Namespace) -> int:
    run_status, parsed = parse_terminal_status(ns.body)
    summary_path: Optional[str] = None
    log_manifest_path: Optional[str] = None
    if run_status is not None:
        log_manifest_path = parsed.get("log_manifest_path")
        if log_manifest_path:
            base = log_manifest_path.rsplit("/", 1)[0]
            summary_path = base + "/summary.json"
    out = {
        "run_status": run_status,
        "summary": parsed.get("summary"),
        "log_manifest_path": log_manifest_path,
        "summary_path": summary_path,
        "envelope": parsed,
    }
    _print(out)
    return 0


def cmd_parse_meta(ns: argparse.Namespace) -> int:
    meta = parse_body(ns.body)
    if meta is None:
        _print(None)
    else:
        _print(meta)
    return 0


def cmd_summary_path(ns: argparse.Namespace) -> int:
    try:
        path = summary_path_for(ns.issue, ns.comment)
    except ValueError as e:
        _die(str(e))
    _print({"summary_path": path})
    return 0


def cmd_replace_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    body = replace_meta_in_body(ns.body, meta)
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_validate_summary(ns: argparse.Namespace) -> int:
    summary = _loads(ns.summary_json, name="summary")
    try:
        schema = _common.load_schema(
            f"commands/{ns.command}.schema.json", REPO_ROOT
        )
    except FileNotFoundError as e:
        _die(f"no schema for command {ns.command}: {e}")
    key = "summary_completed" if ns.status == "completed" else "summary_error"
    sub = schema.get("properties", {}).get(key)
    if sub is None:
        _die(f"schema has no {key} sub-schema for {ns.command}")
    try:
        _common.validate(summary, sub)
    except Exception as e:  # noqa: BLE001
        _die(f"invalid: {e}")
    _print({"valid": True, "command": ns.command, "status": ns.status})
    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent_lib")
    sub = p.add_subparsers(dest="cmd", required=True)

    # make-request
    s = sub.add_parser("make-request", help="build a batch-job-request envelope")
    s.add_argument("args_json", help="JSON object: command args")
    s.add_argument("--command", required=True)
    s.add_argument("--branch", required=True)
    s.add_argument("--sha", required=True, help="commit_sha (40 hex chars)")
    s.add_argument("--subagent-id", required=True)
    s.add_argument("--no-validate", action="store_true",
                   help="skip args schema validation")
    s.set_defaults(func=cmd_make_request)

    # make-ack
    s = sub.add_parser(
        "make-ack",
        help="build a follow-up agent-ack comment envelope",
    )
    s.add_argument(
        "--ack-for", type=int, dest="ack_for", required=True,
        help="comment_id of the batch-job-request to ack",
    )
    s.add_argument("--agent-id", dest="agent_id", default=None)
    s.add_argument("--session-id", dest="session_id", default=None)
    s.add_argument("--note", default=None)
    s.set_defaults(func=cmd_make_ack)

    # make-initial-meta
    s = sub.add_parser("make-initial-meta",
                       help="build initial agent-meta block + body markdown")
    s.add_argument("json_payload",
                   help="JSON object of kwargs for make_initial_meta")
    s.add_argument("--prose", default="", help="prose to put before block")
    s.set_defaults(func=cmd_make_initial_meta)

    # claim-meta
    s = sub.add_parser("claim-meta",
                       help="produce new body markdown for a claim")
    s.add_argument("meta_json", help="existing meta JSON")
    s.add_argument("--agent-id", required=True)
    s.add_argument("--session-id", required=True)
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_claim_meta)

    # heartbeat-meta
    s = sub.add_parser("heartbeat-meta",
                       help="produce new body markdown with refreshed status_ts")
    s.add_argument("meta_json")
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_heartbeat_meta)

    # finish-meta
    s = sub.add_parser("finish-meta",
                       help="produce new body markdown with status=finished")
    s.add_argument("meta_json")
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_finish_meta)

    # abandon-meta
    s = sub.add_parser("abandon-meta",
                       help="produce new body markdown with status=abandoned")
    s.add_argument("meta_json")
    s.add_argument("--reason", required=True)
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_abandon_meta)

    # parse-comment
    s = sub.add_parser("parse-comment",
                       help="extract run_status / summary / paths from comment body")
    s.add_argument("body", help="raw comment body text")
    s.set_defaults(func=cmd_parse_comment)

    # parse-meta
    s = sub.add_parser("parse-meta",
                       help="parse the agent-meta block out of an issue body")
    s.add_argument("body", help="raw issue body markdown")
    s.set_defaults(func=cmd_parse_meta)

    # summary-path
    s = sub.add_parser("summary-path",
                       help="compute the summary.json path for issue/comment")
    s.add_argument("--issue", type=int, required=True)
    s.add_argument("--comment", type=int, required=True)
    s.set_defaults(func=cmd_summary_path)

    # replace-meta
    s = sub.add_parser("replace-meta",
                       help="replace the agent-meta block in an existing body")
    s.add_argument("body")
    s.add_argument("--meta-json", dest="meta_json", required=True)
    s.set_defaults(func=cmd_replace_meta)

    # validate-summary
    s = sub.add_parser("validate-summary",
                       help="validate a summary against the command schema")
    s.add_argument("summary_json")
    s.add_argument("--command", required=True)
    s.add_argument("--status", choices=("completed", "error"), required=True)
    s.set_defaults(func=cmd_validate_summary)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":  # pragma: no cover - dispatched by __main__.py
    raise SystemExit(main())

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/agent_lib/envelope.py

```text
"""Envelope construction helpers for the agent harness.

Pure functions that build a ``batch-job-request`` envelope dict and
optionally validate args against the command's args sub-schema.

No I/O is performed: schemas are loaded from disk via
:mod:`agent_protocol_common`, but no network is touched.
"""

from __future__ import annotations

from typing import Any, Optional

from ._common_loader import REPO_ROOT, load_common


_common = load_common()


class EnvelopeArgsInvalid(ValueError):
    """Raised when ``args`` fail to validate against the command schema."""

    def __init__(self, command: str, message: str) -> None:
        super().__init__(f"args invalid for command {command!r}: {message}")
        self.command = command
        self.message = message


def make_request_envelope(
    command: str,
    args: dict[str, Any],
    branch: str,
    commit_sha: str,
    subagent_id: str,
    *,
    validate_args: bool = True,
    submitted_at: Optional[str] = None,
) -> dict[str, Any]:
    """Construct an unsubmitted ``batch-job-request`` envelope.

    Mirrors :func:`skills.batch-job.submit.submit` minus the I/O. When
    ``validate_args`` is True (default), ``args`` is checked against the
    command's ``args`` sub-schema; an ``EnvelopeArgsInvalid`` is raised
    on failure.

    The ``submitted_at`` timestamp is filled with :func:`iso_now` when
    not provided by the caller.
    """
    if not isinstance(command, str) or not command:
        raise ValueError("command must be a non-empty string")
    if not isinstance(args, dict):
        raise TypeError("args must be a dict")
    if not isinstance(branch, str) or not branch:
        raise ValueError("branch must be a non-empty string")
    if not isinstance(commit_sha, str) or not commit_sha:
        raise ValueError("commit_sha must be a non-empty string")
    if not isinstance(subagent_id, str) or not subagent_id:
        raise ValueError("subagent_id must be a non-empty string")

    if validate_args:
        try:
            schema = _common.load_schema(
                f"commands/{command}.schema.json", REPO_ROOT
            )
        except FileNotFoundError as e:
            raise EnvelopeArgsInvalid(command, f"no schema file: {e}") from e
        args_schema = schema.get("properties", {}).get("args")
        if args_schema is not None:
            try:
                _common.validate(args, args_schema)
            except Exception as e:  # noqa: BLE001 - rewrap
                raise EnvelopeArgsInvalid(command, str(e)) from e

    return {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "command": command,
        "args": dict(args),
        "branch": branch,
        "commit_sha": commit_sha,
        "subagent_id": subagent_id,
        "submitted_at": submitted_at or _common.iso_now(),
        "run_status": None,
        "agent_ack": None,
    }


def make_ack_envelope(
    ack_for: int,
    *,
    agent_acked_at: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    note: Optional[str] = None,
) -> dict[str, Any]:
    """Construct an agent-ack follow-up comment envelope.

    ``ack_for`` is the comment_id of the original batch-job-request whose
    terminal envelope this comment acknowledges (SPEC §5.2). The
    handler treats agent-ack comments as informational; the
    working->finished gate (SPEC §4.1) accepts EITHER an in-place
    ``agent_ack: finished`` on the request comment OR a follow-up
    ``kind: agent-ack`` comment with ``ack_for`` matching the request.
    """
    if not isinstance(ack_for, int) or isinstance(ack_for, bool) or ack_for < 1:
        raise ValueError("ack_for must be a positive integer (comment_id)")
    env: dict[str, Any] = {
        "protocol_version": 1,
        "kind": "agent-ack",
        "ack_for": ack_for,
        "agent_acked_at": agent_acked_at or _common.iso_now(),
    }
    if agent_id is not None:
        env["agent_id"] = agent_id
    if session_id is not None:
        env["session_id"] = session_id
    if note is not None:
        env["note"] = note
    return env


__all__ = ["EnvelopeArgsInvalid", "make_request_envelope", "make_ack_envelope"]

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/agent_lib/meta.py

````text
"""Pure helpers that produce / mutate ``agent-meta`` blocks.

Each function takes either a meta dict (for transformations) or kwargs
(for ``make_initial_meta``) and returns either a new dict or the
markdown body string ready to be sent to ``mcp__github__issue_write``
as the ``body`` field.

No GitHub I/O is performed.
"""

from __future__ import annotations

from typing import Any, Optional

from ._common_loader import load_common


_common = load_common()


def _extract_prose(body: Optional[str]) -> str:
    """Return everything before the agent-meta fenced block, if any."""
    if not body:
        return ""
    marker = "```agent-meta"
    idx = body.find(marker)
    if idx == -1:
        return body
    return body[:idx].rstrip()


def make_initial_meta(
    *,
    feature_branch: str,
    base_branch: str = "main",
    instructions_inline: Optional[str] = None,
    instructions_path: Optional[str] = None,
    parent_issue: Optional[int] = None,
    depends_on_prs: Optional[list[int]] = None,
    protocol_version: int = 1,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a fresh agent-meta dict with ``status=None``.

    Either ``instructions_inline`` or ``instructions_path`` must be
    provided (matching the schema's ``anyOf``).
    """
    if not feature_branch:
        raise ValueError("feature_branch is required")
    if not instructions_inline and not instructions_path:
        raise ValueError(
            "either instructions_inline or instructions_path must be set"
        )
    meta = {
        "protocol_version": protocol_version,
        "agent_id": None,
        "session_id": None,
        "status": None,
        "status_ts": None,
        "feature_branch": feature_branch,
        "base_branch": base_branch,
        "parent_issue": parent_issue,
        "depends_on_prs": list(depends_on_prs or []),
        "instructions_path": instructions_path,
        "instructions_inline": instructions_inline,
        "created_at": _common.iso_now(),
    }
    if extra:
        for k, v in extra.items():
            meta[k] = v
    return meta


def claim_meta(
    meta: dict[str, Any],
    agent_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Mark the meta as claimed by ``agent_id``/``session_id``.

    Returns a new dict; the input is not mutated.
    """
    if not agent_id:
        raise ValueError("agent_id is required")
    if not session_id:
        raise ValueError("session_id is required")
    new_meta = dict(meta)
    new_meta["agent_id"] = agent_id
    new_meta["session_id"] = session_id
    new_meta["status"] = "working"
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def heartbeat_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Refresh ``status_ts`` to now. Returns a new dict."""
    new_meta = dict(meta)
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def finish_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Mark the meta as ``status="finished"``. Returns a new dict."""
    new_meta = dict(meta)
    new_meta["status"] = "finished"
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def abandon_meta(meta: dict[str, Any], reason: str) -> dict[str, Any]:
    """Mark the meta as ``abandoned`` with a recorded reason.

    The ``reason`` is stored under the ``abandon_reason`` key (additional
    properties are allowed by the issue-body schema).
    """
    new_meta = dict(meta)
    new_meta["status"] = "abandoned"
    new_meta["status_ts"] = _common.iso_now()
    new_meta["abandon_reason"] = reason
    return new_meta


def render_body(meta: dict[str, Any], prose: str = "") -> str:
    """Convenience: render an issue body with the given meta."""
    return _common.render_agent_meta(meta, prose=prose)


def parse_body(body: Optional[str]) -> Optional[dict[str, Any]]:
    """Convenience: parse an agent-meta block out of a body."""
    return _common.parse_agent_meta(body)


def replace_meta_in_body(
    body: Optional[str],
    new_meta: dict[str, Any],
) -> str:
    """Replace the agent-meta block in ``body`` with ``new_meta``.

    The prose before the block is preserved; if there was no block, the
    new meta is appended.
    """
    prose = _extract_prose(body)
    return _common.render_agent_meta(new_meta, prose=prose)


__all__ = [
    "make_initial_meta",
    "claim_meta",
    "heartbeat_meta",
    "finish_meta",
    "abandon_meta",
    "render_body",
    "parse_body",
    "replace_meta_in_body",
]

````

### .claude/skills/orchestrate-issue/templates/agent/scripts/agent_lib/poll.py

```text
"""Helpers for parsing terminal-status comments.

Polling itself is performed by the agent via repeated MCP calls; the
helpers here just classify a comment body and tell the agent what
``summary.json`` path to read once the comment has reached a terminal
state.
"""

from __future__ import annotations

import html
import json
from typing import Any, Optional

from ._common_loader import load_common


_common = load_common()


_TERMINAL_STATUSES = {"completed", "error", "parse_error"}


def parse_terminal_status(
    envelope_json: str,
) -> tuple[Optional[str], dict[str, Any]]:
    """Classify a comment body.

    Returns a tuple ``(run_status, parsed)``:
      - On JSON parse failure: returns ``(None, {})``.
      - On non-terminal envelope (run_status=None or "running"): returns
        ``(None, parsed)``.
      - On terminal envelope: returns ``(run_status, parsed)``.

    The caller is expected to use the parsed envelope to look up the
    summary path via :func:`summary_path_for` when terminal.
    """
    if not isinstance(envelope_json, str):
        raise TypeError("envelope_json must be a string")
    # MCP returns comment bodies HTML-escaped (&#34; for ", etc.) and
    # Claude Code's GitHub MCP additionally appends a trailer line like
    # ``\n---\n_Generated by [Claude Code](https://claude.ai/code)_`` to
    # every posted comment. We unescape (no-op on REST content) and then
    # use raw_decode to parse the longest JSON-object prefix at the
    # start of the body, tolerating any trailing prose.
    unescaped = html.unescape(envelope_json).lstrip()
    if not unescaped:
        return None, {}
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(unescaped)
    except (json.JSONDecodeError, ValueError):
        return None, {}
    if not isinstance(parsed, dict):
        return None, {}
    status = parsed.get("run_status")
    if status in _TERMINAL_STATUSES:
        return status, parsed
    return None, parsed


def summary_path_for(issue_number: int, comment_id: int) -> str:
    """Return the ``summary.json`` path under the ``_agent_runs`` branch."""
    if not isinstance(issue_number, int) or issue_number < 1:
        raise ValueError("issue_number must be a positive integer")
    if not isinstance(comment_id, int) or comment_id < 1:
        raise ValueError("comment_id must be a positive integer")
    return f"runs/{issue_number}/{comment_id}/summary.json"


def manifest_path_for(issue_number: int, comment_id: int) -> str:
    """Return the ``manifest.json`` path under the ``_agent_runs`` branch."""
    return f"runs/{issue_number}/{comment_id}/manifest.json"


def is_terminal(envelope: dict[str, Any]) -> bool:
    """True if the envelope's ``run_status`` is terminal."""
    return _common.is_terminal_run_status(envelope.get("run_status"))


def parse_ack_comment(body: str) -> Optional[dict[str, Any]]:
    """If body is an agent-ack envelope, return parsed dict; else None.

    Tolerates HTML-escaped bodies and trailing prose (matching the
    parse_terminal_status conventions).
    """
    if not isinstance(body, str):
        return None
    unescaped = html.unescape(body).lstrip()
    if not unescaped:
        return None
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(unescaped)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    if parsed.get("protocol_version") != 1 or parsed.get("kind") != "agent-ack":
        return None
    return parsed


def is_request_acked(
    request_envelope: dict[str, Any],
    request_comment_id: int,
    other_comment_bodies: list[str],
) -> bool:
    """Return True if the request is acked via either form (SPEC §4.1).

    EITHER ``request_envelope["agent_ack"] == "finished"`` (in-place form)
    OR there is at least one comment in ``other_comment_bodies`` that is
    a valid ``kind: agent-ack`` envelope with ``ack_for == request_comment_id``.
    """
    if request_envelope.get("agent_ack") == "finished":
        return True
    for body in other_comment_bodies:
        ack = parse_ack_comment(body)
        if ack and ack.get("ack_for") == request_comment_id:
            return True
    return False


__all__ = [
    "parse_terminal_status",
    "summary_path_for",
    "manifest_path_for",
    "is_terminal",
    "parse_ack_comment",
    "is_request_acked",
]

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/close_on_merge.py

```text
"""``close-on-merge`` script (§7.3).

Triggered on merged PRs. Reads the PR body for ``Closes #N``, verifies
the linked issue is in ``status: finished``, then closes the issue,
comments the merge SHA, and locks the issue. Locking happens here
(after the close + final comment) rather than at issue creation,
because GitHub refuses comments from ``GITHUB_TOKEN`` on locked
issues — locking earlier would prevent the batch-job-handler workflow
from writing its terminal envelope. Once the issue is closed and
finalised the lock acts as a tamper-prevention seal on the audit
record.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any, Optional

if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        iso_now,
        load_config,
        parse_agent_meta,
    )
else:
    from .common import GitHubClient, iso_now, load_config, parse_agent_meta


_CLOSES_RE = re.compile(
    r"\b(?:closes|closed|close|fixes|fixed|fix|resolves|resolved|resolve)\s+#(\d+)\b",
    re.IGNORECASE,
)


# Branches that must NEVER be deleted by close_on_merge, regardless of
# how the PR head ref or any sub-* match looks. ``main`` is the default
# branch; ``_agent_runs`` is the orphan audit-trail branch (SPEC §6).
_PROTECTED_BRANCHES = frozenset({"main", "_agent_runs"})


def parse_closes_refs(body: Optional[str]) -> list[int]:
    """Return list of issue numbers the PR claims to close."""
    if not body:
        return []
    return [int(m.group(1)) for m in _CLOSES_RE.finditer(body)]


def _safe_to_delete(name: Optional[str]) -> bool:
    """Return True if it's safe to delete this branch.

    Defensive: only branches that start with ``agent/`` are eligible —
    so even if a PR head somehow points at ``main`` or any other
    non-agent branch, we leave it alone.
    """
    if not name:
        return False
    if name in _PROTECTED_BRANCHES:
        return False
    if not name.startswith("agent/"):
        return False
    return True


def _delete_feature_and_subagent_branches(
    client: GitHubClient,
    feature_branch: Optional[str],
) -> list[str]:
    """Delete the feature branch and any ``<feature>--sub-*`` branches.

    Each deletion is wrapped in try/except so a missing or already-deleted
    branch (or any transient REST error) does not fail the workflow. The
    surviving deletions are still applied. Returns the names of branches
    we *attempted to* and successfully deleted (best-effort: the in-memory
    client is fully idempotent; the REST client treats 404 as success).
    """
    if not feature_branch:
        return []
    targets: list[str] = []
    if _safe_to_delete(feature_branch):
        targets.append(feature_branch)
    # Discover subagent branches under the feature.
    sub_prefix = f"{feature_branch}--sub-"
    try:
        branches = client.list_branches()
    except Exception:  # noqa: BLE001
        branches = []
    for b in branches:
        name = b.get("name") if isinstance(b, dict) else None
        if not name or name == feature_branch:
            continue
        if name.startswith(sub_prefix) and _safe_to_delete(name):
            targets.append(name)

    deleted: list[str] = []
    for name in targets:
        try:
            client.delete_branch(name)
            deleted.append(name)
        except Exception:  # noqa: BLE001
            # Swallow: missing/already-deleted branches must not fail the
            # workflow. Other deletions in the batch should still proceed.
            continue
    return deleted


def run(
    client: GitHubClient,
    pr_number: int,
    *,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Close issues referenced by a merged PR. Returns a result dict."""
    cfg = config or load_config()

    pr = client.get_pull_request(pr_number)
    if not pr.get("merged"):
        return {"action": "noop", "reason": "pr_not_merged"}

    head_ref = (pr.get("head") or {}).get("ref") if isinstance(pr.get("head"), dict) else None

    refs = parse_closes_refs(pr.get("body"))
    if not refs:
        deleted_branches = _delete_feature_and_subagent_branches(client, head_ref)
        return {
            "action": "noop",
            "reason": "no_closes_refs",
            "deleted_branches": deleted_branches,
        }

    closed: list[int] = []
    skipped: list[dict[str, Any]] = []

    for issue_number in refs:
        try:
            issue = client.get_issue(issue_number)
        except KeyError:
            skipped.append({"issue": issue_number, "reason": "missing"})
            continue

        meta = parse_agent_meta(issue.get("body"))
        if meta is None:
            skipped.append({"issue": issue_number, "reason": "no_agent_meta"})
            continue

        if meta.get("status") != "finished":
            skipped.append({
                "issue": issue_number,
                "reason": "not_finished",
                "status": meta.get("status"),
            })
            continue

        if issue.get("state") != "closed":
            client.update_issue(issue_number, state="closed")

        msg = (
            f"Issue closed by merge of #{pr_number} "
            f"(merge_sha={pr.get('merge_commit_sha')}). "
            f"Closed at {iso_now()}."
        )
        client.add_comment(issue_number, msg)
        # Lock the issue post-close as a tamper-prevention seal on the
        # audit record. We could not lock earlier without blocking the
        # batch-job-handler from writing terminal envelopes (GITHUB_TOKEN
        # cannot comment on locked issues).
        if not issue.get("locked"):
            client.lock_issue(issue_number)
        closed.append(issue_number)

    deleted_branches = _delete_feature_and_subagent_branches(client, head_ref)

    return {
        "action": "closed",
        "issues_closed": closed,
        "skipped": skipped,
        "deleted_branches": deleted_branches,
    }


def main() -> int:
    """``close-on-merge`` workflow entry point.

    Required environment variables:
      - ``PR_NUMBER``          the merged pull request number
      - ``GH_TOKEN`` / ``GITHUB_TOKEN``  REST API token
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug

    On success exits 0; on uncaught exception prints to stderr and
    exits 1. Tests call :func:`run` directly with an in-memory client.
    """
    required = ["PR_NUMBER", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    print(
        "close_on_merge: required env vars: " + ", ".join(required) + ".",
        file=sys.stderr,
    )
    pr_number = os.environ.get("PR_NUMBER")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    missing = [
        name for name, val in (
            ("PR_NUMBER", pr_number),
            ("GITHUB_TOKEN", token),
            ("GITHUB_REPOSITORY", repo_slug),
        ) if not val
    ]
    if missing:
        print(f"close_on_merge: missing env vars: {missing}", file=sys.stderr)
        return 1
    assert pr_number is not None and token is not None and repo_slug is not None
    if "/" not in repo_slug:
        print(
            f"close_on_merge: GITHUB_REPOSITORY must be 'owner/repo', got: {repo_slug!r}",
            file=sys.stderr,
        )
        return 1
    owner, repo = repo_slug.split("/", 1)
    print(
        f"close_on_merge: handling PR #{pr_number}",
        file=sys.stderr,
    )
    try:
        if __package__ in (None, ""):
            from rest_client import RestGitHubClient  # type: ignore[import-not-found]
        else:
            from .rest_client import RestGitHubClient
        client = RestGitHubClient(token=token, owner=owner, repo=repo)
        run(client, int(pr_number))
    except Exception as exc:  # noqa: BLE001
        import traceback as _tb
        print(f"close_on_merge: uncaught exception: {exc!r}", file=sys.stderr)
        _tb.print_exc()
        # Self-diagnostic: post a debug comment. Prefer the issue named in
        # ``Closes #N`` (best-effort PR body fetch); otherwise fall back
        # to the PR itself, since PRs are issues to GitHub's REST API.
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                if __package__ in (None, ""):
                    from handler import _post_debug_comment  # type: ignore[import-not-found]
                else:
                    from .handler import _post_debug_comment
                target_issue = int(pr_number)
                try:
                    import requests as _requests
                    pr_resp = _requests.get(
                        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                        timeout=15,
                    )
                    if pr_resp.status_code < 300:
                        refs = parse_closes_refs((pr_resp.json() or {}).get("body"))
                        if refs:
                            target_issue = refs[0]
                except Exception:  # noqa: BLE001
                    pass  # fall back to PR
                _post_debug_comment(
                    token=token,
                    owner=owner,
                    repo=repo,
                    issue_number=target_issue,
                    script="close_on_merge.py",
                    exc=exc,
                    extra_fields={"pr": pr_number},
                )
            except Exception as diag_exc:  # noqa: BLE001
                print(
                    f"close_on_merge: failed to post debug comment: {diag_exc!r}",
                    file=sys.stderr,
                )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/common.py

````text
"""Common helpers for the agent protocol POC.

Provides:
- ``GitHubClient`` Protocol/abstract definition of the operations the
  scripts need.
- ``InMemoryGitHubClient`` — fully working in-memory implementation
  used in tests and for local POC demonstrations.
- Envelope/agent-meta helpers (parse, render).
- ``LogWriter`` — a JSONL/gzip log writer that rotates by compressed
  size and produces a manifest.
- ``load_config`` and ``validate`` JSON-schema helpers.

The real GitHub REST integration is intentionally **not** implemented
here; for the POC we exercise behaviour through the in-memory client.
"""

from __future__ import annotations

import base64
import gzip
import html
import io
import json
import os
import re
import secrets
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Optional,
    Protocol,
    runtime_checkable,
)

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - jsonschema is in requirements
    Draft202012Validator = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Time and config helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    """Return the current UTC time as an ISO-8601 string with ``Z`` suffix."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config(path: str | os.PathLike[str] = ".agent/config.json") -> dict[str, Any]:
    """Load the central agent configuration JSON file."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(json_obj: Any, schema_obj: dict[str, Any]) -> None:
    """Validate a JSON object against a JSON schema (Draft 2020-12).

    Raises ``jsonschema.ValidationError`` on the first error encountered.
    """
    if Draft202012Validator is None:  # pragma: no cover
        raise RuntimeError("jsonschema is not installed; cannot validate")
    validator = Draft202012Validator(schema_obj)
    errors = sorted(validator.iter_errors(json_obj), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.absolute_path) or "<root>"
        raise ValueError(f"schema validation failed at {path}: {first.message}")


# ---------------------------------------------------------------------------
# agent-meta block parsing / rendering
# ---------------------------------------------------------------------------

_AGENT_META_RE = re.compile(
    r"```agent-meta\s*\n(?P<json>.*?)\n```",
    re.DOTALL,
)


def parse_agent_meta(body: Optional[str]) -> Optional[dict[str, Any]]:
    """Extract the JSON object inside the fenced ``agent-meta`` block.

    Returns ``None`` when:
    - the body is ``None`` or empty, OR
    - no ``agent-meta`` fenced block is present, OR
    - the block exists but its body is not valid JSON.

    The MCP server returns issue bodies with HTML-escaped entities
    (``&#34;`` for ``"``, etc.). We unescape the JSON region before
    parsing so the same parser works against MCP and REST responses.
    Workflow REST responses contain literal quotes so unescape is a
    no-op there.
    """
    if not body:
        return None
    m = _AGENT_META_RE.search(body)
    if not m:
        return None
    raw = html.unescape(m.group("json"))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def render_agent_meta(meta: dict[str, Any], prose: str = "") -> str:
    """Render an issue body markdown with the given ``agent-meta`` block.

    The prose is placed before the fenced block; a blank line separates
    them when both are non-empty.
    """
    block = "```agent-meta\n" + json.dumps(meta, indent=2) + "\n```"
    if prose:
        return f"{prose.rstrip()}\n\n{block}\n"
    return block + "\n"


# ---------------------------------------------------------------------------
# GitHub client abstraction
# ---------------------------------------------------------------------------

@runtime_checkable
class GitHubClient(Protocol):
    """Minimal protocol for the operations the agent scripts need.

    Implementations may use the REST API, an MCP relay, or the
    in-memory mock used for the POC. Errors are raised as exceptions.
    """

    # Issue operations -----------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]: ...
    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]: ...
    def lock_issue(self, number: int) -> None: ...
    def add_label(self, number: int, label: str) -> None: ...
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]: ...

    # Comment operations ---------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]: ...
    def get_comment(self, comment_id: int) -> dict[str, Any]: ...
    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]: ...
    def delete_comment(self, comment_id: int) -> None: ...
    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]: ...

    # File / branch operations --------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]: ...
    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]: ...
    def get_branch_head_sha(self, branch: str) -> Optional[str]: ...
    def delete_branch(self, name: str) -> None: ...
    def list_branches(self) -> list[dict[str, Any]]: ...

    # PR operations --------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]: ...
    def get_pull_request(self, number: int) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# In-memory GitHub client (POC + tests)
# ---------------------------------------------------------------------------

@dataclass
class _Commit:
    sha: str
    parent: Optional[str]
    message: str
    files: dict[str, bytes]  # path -> content


@dataclass
class _Branch:
    name: str
    head_sha: Optional[str]  # None means orphan/uninitialised


@dataclass
class _Comment:
    id: int
    issue_number: int
    user: str
    body: str
    created_at: str
    updated_at: str


@dataclass
class _Issue:
    number: int
    title: str
    body: str
    user: str
    state: str = "open"
    locked: bool = False
    labels: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=iso_now)
    updated_at: str = field(default_factory=iso_now)


@dataclass
class _PullRequest:
    number: int
    title: str
    head: str
    base: str
    body: str
    state: str = "open"
    merged: bool = False
    merge_commit_sha: Optional[str] = None
    user: str = "agent"
    created_at: str = field(default_factory=iso_now)


class InMemoryGitHubClient:
    """In-memory simulation of the subset of GitHub the protocol uses.

    Each call returns dict-shaped data resembling the REST API responses
    so that calling code is portable to a real REST client.
    """

    def __init__(self, default_user: str = "agent") -> None:
        self._lock = threading.RLock()
        self._issues: dict[int, _Issue] = {}
        self._comments: dict[int, _Comment] = {}
        self._comments_by_issue: dict[int, list[int]] = {}
        self._branches: dict[str, _Branch] = {}
        self._commits: dict[str, _Commit] = {}
        self._pulls: dict[int, _PullRequest] = {}
        self._next_issue_number = 1
        self._next_comment_id = 1_000_000
        self._next_pr_number = 5000
        self._default_user = default_user
        self._actor_stack: list[str] = [default_user]

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------
    def as_user(self, login: str) -> "_ActAs":
        """Context manager: switch the effective acting user temporarily."""
        return _ActAs(self, login)

    @property
    def current_user(self) -> str:
        return self._actor_stack[-1]

    def create_issue(
        self,
        title: str,
        body: str,
        user: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Test helper: create a fresh issue in the in-memory state."""
        with self._lock:
            number = self._next_issue_number
            self._next_issue_number += 1
            issue = _Issue(
                number=number,
                title=title,
                body=body,
                user=user or self.current_user,
                labels=list(labels or []),
            )
            self._issues[number] = issue
            self._comments_by_issue[number] = []
            return self._issue_to_dict(issue)

    def create_branch(self, name: str, from_branch: Optional[str] = None) -> str:
        """Create a branch (optionally branching from another). Returns sha."""
        with self._lock:
            if name in self._branches:
                raise ValueError(f"branch already exists: {name}")
            parent_sha: Optional[str] = None
            files: dict[str, bytes] = {}
            if from_branch is not None:
                src = self._branches.get(from_branch)
                if src is None:
                    raise ValueError(f"unknown source branch: {from_branch}")
                parent_sha = src.head_sha
                if parent_sha is not None:
                    files = dict(self._commits[parent_sha].files)
            sha = _new_sha()
            commit = _Commit(
                sha=sha,
                parent=parent_sha,
                message=f"create branch {name}",
                files=files,
            )
            self._commits[sha] = commit
            self._branches[name] = _Branch(name=name, head_sha=sha)
            return sha

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _issue_to_dict(self, issue: _Issue) -> dict[str, Any]:
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "user": {"login": issue.user},
            "state": issue.state,
            "locked": issue.locked,
            "labels": [{"name": n} for n in issue.labels],
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
        }

    def _comment_to_dict(self, c: _Comment) -> dict[str, Any]:
        return {
            "id": c.id,
            "issue_number": c.issue_number,
            "user": {"login": c.user},
            "body": c.body,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }

    # ------------------------------------------------------------------
    # Issue API
    # ------------------------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            return self._issue_to_dict(issue)

    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            if body is not None:
                issue.body = body
            if state is not None:
                if state not in ("open", "closed"):
                    raise ValueError(f"bad state: {state}")
                issue.state = state
            if labels is not None:
                issue.labels = list(labels)
            issue.updated_at = iso_now()
            return self._issue_to_dict(issue)

    def lock_issue(self, number: int) -> None:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            issue.locked = True
            issue.updated_at = iso_now()

    def add_label(self, number: int, label: str) -> None:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            if label not in issue.labels:
                issue.labels.append(label)
            issue.updated_at = iso_now()

    # ------------------------------------------------------------------
    # Comment API
    # ------------------------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]:
        with self._lock:
            ids = self._comments_by_issue.get(issue_number, [])
            return [self._comment_to_dict(self._comments[i]) for i in ids]

    def get_comment(self, comment_id: int) -> dict[str, Any]:
        with self._lock:
            c = self._comments.get(comment_id)
            if c is None:
                raise KeyError(f"no such comment: {comment_id}")
            return self._comment_to_dict(c)

    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        with self._lock:
            c = self._comments.get(comment_id)
            if c is None:
                raise KeyError(f"no such comment: {comment_id}")
            c.body = body
            c.updated_at = iso_now()
            return self._comment_to_dict(c)

    def delete_comment(self, comment_id: int) -> None:
        with self._lock:
            c = self._comments.pop(comment_id, None)
            if c is None:
                return
            self._comments_by_issue.get(c.issue_number, []).remove(comment_id)

    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        with self._lock:
            if issue_number not in self._issues:
                raise KeyError(f"no such issue: {issue_number}")
            cid = self._next_comment_id
            self._next_comment_id += 1
            now = iso_now()
            c = _Comment(
                id=cid,
                issue_number=issue_number,
                user=self.current_user,
                body=body,
                created_at=now,
                updated_at=now,
            )
            self._comments[cid] = c
            self._comments_by_issue.setdefault(issue_number, []).append(cid)
            return self._comment_to_dict(c)

    # ------------------------------------------------------------------
    # Files / branches / commits
    # ------------------------------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]:
        with self._lock:
            branch = self._branches.get(ref)
            if branch is None or branch.head_sha is None:
                return None
            commit = self._commits[branch.head_sha]
            data = commit.files.get(path)
            if data is None:
                return None
            # Returned as text (utf-8) or base64 if binary; we always return
            # decoded utf-8 if possible, else b64. Tests typically compare
            # bytes via separate helpers.
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(data).decode("ascii")

    def get_file_bytes(self, path: str, ref: str) -> Optional[bytes]:
        """Test convenience: raw bytes of a file at ref."""
        with self._lock:
            branch = self._branches.get(ref)
            if branch is None or branch.head_sha is None:
                return None
            commit = self._commits[branch.head_sha]
            return commit.files.get(path)

    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                # Auto-create as orphan branch (no parent)
                br = _Branch(name=branch, head_sha=None)
                self._branches[branch] = br
            parent = br.head_sha
            files = dict(self._commits[parent].files) if parent else {}
            files[path] = content_bytes
            sha = _new_sha()
            commit = _Commit(sha=sha, parent=parent, message=message, files=files)
            self._commits[sha] = commit
            br.head_sha = sha
            return {
                "path": path,
                "branch": branch,
                "commit": {"sha": sha, "message": message},
                "size": len(content_bytes),
            }

    def get_branch_head_sha(self, branch: str) -> Optional[str]:
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                return None
            return br.head_sha

    def delete_branch(self, name: str) -> None:
        """Delete a branch ref. Idempotent: missing branches are ignored.

        Note: commits are not garbage-collected from the in-memory store —
        only the branch ref is removed (mirrors GitHub's ref-delete semantics).
        """
        with self._lock:
            self._branches.pop(name, None)

    def list_branches(self) -> list[dict[str, Any]]:
        """List all branches as dicts ``{name, sha, protected}``.

        Mirrors a paginated REST ``GET /repos/{owner}/{repo}/branches``
        response shape. The in-memory client has no notion of branch
        protection, so ``protected`` is always ``False``.
        """
        with self._lock:
            return [
                {"name": b.name, "sha": b.head_sha, "protected": False}
                for b in self._branches.values()
            ]

    def commit_files(
        self,
        branch: str,
        files: dict[str, bytes],
        message: str,
    ) -> str:
        """Test helper: commit multiple files atomically. Returns new sha."""
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                br = _Branch(name=branch, head_sha=None)
                self._branches[branch] = br
            parent = br.head_sha
            current = dict(self._commits[parent].files) if parent else {}
            current.update(files)
            sha = _new_sha()
            self._commits[sha] = _Commit(
                sha=sha, parent=parent, message=message, files=current
            )
            br.head_sha = sha
            return sha

    # ------------------------------------------------------------------
    # PR API
    # ------------------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]:
        with self._lock:
            if head not in self._branches:
                raise ValueError(f"head branch does not exist: {head}")
            if base not in self._branches:
                raise ValueError(f"base branch does not exist: {base}")
            number = self._next_pr_number
            self._next_pr_number += 1
            pr = _PullRequest(
                number=number,
                title=title,
                head=head,
                base=base,
                body=body,
                user=self.current_user,
            )
            self._pulls[number] = pr
            return self._pr_to_dict(pr)

    def get_pull_request(self, number: int) -> dict[str, Any]:
        with self._lock:
            pr = self._pulls.get(number)
            if pr is None:
                raise KeyError(f"no such PR: {number}")
            return self._pr_to_dict(pr)

    def merge_pull_request(self, number: int) -> dict[str, Any]:
        """Test helper: simulate a merged PR."""
        with self._lock:
            pr = self._pulls.get(number)
            if pr is None:
                raise KeyError(f"no such PR: {number}")
            pr.state = "closed"
            pr.merged = True
            pr.merge_commit_sha = _new_sha()
            return self._pr_to_dict(pr)

    def _pr_to_dict(self, pr: _PullRequest) -> dict[str, Any]:
        return {
            "number": pr.number,
            "title": pr.title,
            "head": {"ref": pr.head},
            "base": {"ref": pr.base},
            "body": pr.body,
            "state": pr.state,
            "merged": pr.merged,
            "merge_commit_sha": pr.merge_commit_sha,
            "user": {"login": pr.user},
            "created_at": pr.created_at,
        }


class _ActAs:
    """Context manager to switch the in-memory client's acting user."""

    def __init__(self, client: InMemoryGitHubClient, login: str) -> None:
        self._client = client
        self._login = login

    def __enter__(self) -> InMemoryGitHubClient:
        self._client._actor_stack.append(self._login)
        return self._client

    def __exit__(self, exc_type, exc, tb) -> None:
        self._client._actor_stack.pop()


def _new_sha() -> str:
    """Generate a 40-character lowercase hex 'sha'."""
    return secrets.token_hex(20)


# ---------------------------------------------------------------------------
# Log sanitisation (SPEC §14)
# ---------------------------------------------------------------------------

# GitHub PAT/OAuth-style tokens.
_RE_GH_TOKEN = re.compile(r"gh[ps]_[A-Za-z0-9]{36,}")
# AWS access key id.
_RE_AWS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
# Bearer tokens in Authorization-style strings.
_RE_BEARER = re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")
# Generic key=value patterns where the key looks secret-shaped. We
# intentionally redact only the captured group so the rest of the
# string (including the key name and separator) survives for context.
_RE_GENERIC_SECRET = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password)[\"'\s:=]+([A-Za-z0-9_\-]{16,})"
)


def _sanitize_string(s: str) -> str:
    """Redact common secret patterns in a single string."""
    out = _RE_GH_TOKEN.sub("***", s)
    out = _RE_AWS_KEY.sub("***", out)
    out = _RE_BEARER.sub("Bearer ***", out)

    def _redact_group(m: re.Match[str]) -> str:
        whole = m.group(0)
        captured = m.group(1)
        # Replace just the captured secret value with ``***``.
        start, end = m.span(1)
        # m.span is relative to the whole input string, not to ``whole``.
        return whole[: start - m.start()] + "***" + whole[end - m.start():]

    out = _RE_GENERIC_SECRET.sub(_redact_group, out)
    return out


def sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copied record with common secret patterns redacted.

    Per SPEC §14: log content on a public repo is world-readable, so
    the handler should pass log records through a sanitiser that drops
    anything matching common secret patterns before writing chunks.

    The original ``record`` is NOT mutated.
    """

    def _walk(node: Any) -> Any:
        if isinstance(node, str):
            return _sanitize_string(node)
        if isinstance(node, dict):
            return {k: _walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(v) for v in node]
        if isinstance(node, tuple):
            return tuple(_walk(v) for v in node)
        return node

    return _walk(record)


# ---------------------------------------------------------------------------
# LogWriter
# ---------------------------------------------------------------------------

@dataclass
class _ChunkInfo:
    path: str
    bytes_: int
    lines: int
    data: bytes


class LogWriter:
    """Append JSONL records, gzip-rotate at a configured size threshold.

    Usage::

        lw = LogWriter(max_chunk_bytes_compressed=512_000)
        lw.write({"ts": iso_now(), "stream": "stdout", "phase": "exec",
                  "data": "hello"})
        ...
        chunks = lw.finalize()        # list[(path, bytes, dict)]
        manifest = lw.manifest(...)   # build manifest dict

    Records are passed through :func:`sanitize_record` before being
    serialised, unless the writer was constructed with
    ``sanitize=False``.
    """

    def __init__(
        self,
        max_chunk_bytes_compressed: int = 524_288,
        chunk_name_template: str = "log-{n:04d}.jsonl.gz",
        sanitize: bool = True,
    ) -> None:
        self._max = int(max_chunk_bytes_compressed)
        self._template = chunk_name_template
        self._sanitize = bool(sanitize)
        self._buf = io.BytesIO()
        self._gz = gzip.GzipFile(fileobj=self._buf, mode="wb", mtime=0)
        self._cur_lines = 0
        self._chunk_index = 1
        self._chunks: list[_ChunkInfo] = []
        self._closed = False

    # ------------------------------------------------------------------
    def set_max_chunk_bytes(self, max_chunk_bytes_compressed: int) -> None:
        """Update the rotation threshold mid-stream (use sparingly).

        Useful for test commands like chatty that want to force rotation
        at a smaller threshold than the production default.
        """
        if self._closed:
            raise RuntimeError("LogWriter is closed")
        n = int(max_chunk_bytes_compressed)
        if n < 1:
            raise ValueError("max_chunk_bytes_compressed must be >= 1")
        self._max = n

    # ------------------------------------------------------------------
    def _rotate_if_needed(self) -> None:
        # Flush current gzip stream to estimate compressed size.
        self._gz.flush()
        if self._buf.tell() >= self._max and self._cur_lines > 0:
            self._close_current_chunk()
            self._open_new_chunk()

    def _close_current_chunk(self) -> None:
        self._gz.close()
        data = self._buf.getvalue()
        path = self._template.format(n=self._chunk_index)
        self._chunks.append(
            _ChunkInfo(path=path, bytes_=len(data), lines=self._cur_lines, data=data)
        )
        self._chunk_index += 1

    def _open_new_chunk(self) -> None:
        self._buf = io.BytesIO()
        self._gz = gzip.GzipFile(fileobj=self._buf, mode="wb", mtime=0)
        self._cur_lines = 0

    # ------------------------------------------------------------------
    def write(self, record: dict[str, Any]) -> None:
        """Append one JSON record (one line) to the current chunk.

        When ``sanitize=True`` (default), the record is passed through
        :func:`sanitize_record` before serialisation.
        """
        if self._closed:
            raise RuntimeError("LogWriter is closed")
        payload = sanitize_record(record) if self._sanitize else record
        line = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        self._gz.write(line)
        self._cur_lines += 1
        # Rotate after writing so chunks contain at least one line.
        self._rotate_if_needed()

    def finalize(self) -> list[tuple[str, bytes, dict[str, int]]]:
        """Close the writer; return list of ``(path, gz_bytes, info)``.

        ``info`` contains keys ``bytes`` and ``lines``.
        """
        if self._closed:
            return [(c.path, c.data, {"bytes": c.bytes_, "lines": c.lines}) for c in self._chunks]
        # Close current chunk if it has any lines.
        if self._cur_lines > 0:
            self._close_current_chunk()
        else:
            # discard empty buffer
            try:
                self._gz.close()
            except Exception:
                pass
        self._closed = True
        return [(c.path, c.data, {"bytes": c.bytes_, "lines": c.lines}) for c in self._chunks]

    def manifest(
        self,
        *,
        command: str,
        args: dict[str, Any],
        checked_out_sha: str,
        started_at: str,
        finished_at: str,
        exit_code: int,
        protocol_version: int = 1,
        extra_schema_fields: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build a manifest dict matching ``log-manifest.schema.json``."""
        if not self._closed:
            self.finalize()
        fields = {
            "ts": {"type": "string", "description": "ISO 8601"},
            "stream": {"enum": ["stdout", "stderr", "meta"]},
            "phase": {"enum": ["setup", "exec", "teardown"]},
            "data": {"type": ["string", "object"]},
        }
        if extra_schema_fields:
            fields.update(extra_schema_fields)
        return {
            "protocol_version": protocol_version,
            "schema": {
                "chunk_format": "jsonl-gz",
                "fields": fields,
            },
            "command": command,
            "args": args,
            "checked_out_sha": checked_out_sha,
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "chunks": [
                {"path": c.path, "bytes": c.bytes_, "lines": c.lines}
                for c in self._chunks
            ],
        }

    # Convenience for tests / debugging
    def chunks(self) -> list[tuple[str, bytes, dict[str, int]]]:
        return self.finalize()


# ---------------------------------------------------------------------------
# Schema loading helpers
# ---------------------------------------------------------------------------

def schemas_root(repo_root: str | os.PathLike[str] = ".") -> Path:
    return Path(repo_root) / ".agent" / "schemas"


def load_schema(name: str, repo_root: str | os.PathLike[str] = ".") -> dict[str, Any]:
    """Load a schema by relative name (e.g. ``commands/run-tests.schema.json``)."""
    p = schemas_root(repo_root) / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def b64_encode(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("ascii")


def b64_decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def new_uuid() -> str:
    return str(uuid.uuid4())


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "task"


def is_terminal_run_status(status: Optional[str]) -> bool:
    return status in {"completed", "error", "parse_error"}


def has_protocol_markers(obj: Any) -> bool:
    """Return True if a parsed JSON object has ``protocol_version`` and ``kind``."""
    return (
        isinstance(obj, dict)
        and "protocol_version" in obj
        and "kind" in obj
    )


__all__ = [
    "GitHubClient",
    "InMemoryGitHubClient",
    "LogWriter",
    "iso_now",
    "load_config",
    "load_schema",
    "validate",
    "parse_agent_meta",
    "render_agent_meta",
    "b64_encode",
    "b64_decode",
    "new_uuid",
    "slugify",
    "is_terminal_run_status",
    "has_protocol_markers",
    "sanitize_record",
]

````

### .claude/skills/orchestrate-issue/templates/agent/scripts/handler.py

````text
"""``batch-job-handler`` script (§7.2).

Loads a comment from GitHub via the abstract :class:`GitHubClient`,
parses the JSON envelope, dispatches to a registered command handler,
writes structured logs into ``_agent_runs/runs/<issue>/<comment>/`` and
edits the comment with the terminal envelope.

Importable as ``run(client, issue_number, comment_id, ...)`` for tests.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Optional


def _parse_envelope_lenient(body: str) -> Optional[dict[str, Any]]:
    """Parse the longest JSON-object prefix at the start of ``body``.

    SPEC §5.2 says the comment body is a JSON object with no surrounding
    prose. We interpret "no surrounding prose" liberally to mean **JSON
    must start at the beginning of the body** (after any leading
    whitespace), but trailing prose is tolerated. This is necessary
    because some MCP servers (notably Claude Code's GitHub MCP)
    automatically append a trailer like
    ``\\n---\\n_Generated by [Claude Code](https://claude.ai/code)_``
    to every comment they post.

    Returns the parsed dict, or ``None`` if:
      - ``body`` is not a string, OR
      - the body (after stripping leading whitespace) does not start
        with a valid JSON object.
    """
    if not isinstance(body, str):
        return None
    stripped = body.lstrip()
    if not stripped:
        return None
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(stripped)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed

if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )
else:
    from .common import (
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    *,
    workflow_run_id: int = 0,
    workspace: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Process a single comment. Returns a summary dict for tests."""
    cfg = config or load_config(Path(repo_root) / ".agent" / "config.json")

    comment = client.get_comment(comment_id)
    raw_body = comment.get("body") or ""

    # Step 1: parse envelope ----------------------------------------------
    # Tolerate trailing prose (e.g. the trailer Claude Code's GitHub MCP
    # appends to every comment); see _parse_envelope_lenient.
    parsed: Optional[dict[str, Any]] = _parse_envelope_lenient(raw_body)

    if not has_protocol_markers(parsed):
        return {"action": "ignored", "reason": "no_protocol_markers"}

    assert isinstance(parsed, dict)  # for type checkers

    # Dispatch on envelope kind. Acks are informational follow-up comments;
    # the handler does not process them as batch jobs. They are surfaced
    # through the working->finished gate (SPEC §4.1). Without this dispatch
    # the schema validation step below would parse-error every agent-ack
    # comment because comment-envelope.schema.json says
    # ``kind: const "batch-job-request"``.
    kind = parsed.get("kind")
    if kind == "agent-ack":
        return {"action": "noop", "reason": "ack_comment", "kind": "agent-ack"}

    # Idempotency on already-terminal envelopes (webhook redelivery).
    if is_terminal_run_status(parsed.get("run_status")):
        return {"action": "noop", "reason": "already_terminal", "run_status": parsed["run_status"]}

    envelope_schema = load_schema("comment-envelope.schema.json", repo_root)

    started_at = iso_now()

    # SPEC §13: reject envelopes with unknown protocol_version BEFORE schema
    # validation. We already know parsed has both protocol_version and kind
    # markers (has_protocol_markers above).
    if parsed.get("protocol_version") != 1:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="unsupported_version",
            error_detail=(
                f"protocol_version {parsed.get('protocol_version')!r} is not supported"
            ),
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    # Validate base envelope shape.
    try:
        validate(parsed, envelope_schema)
    except Exception as e:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="schema_validation_failed",
            error_detail=str(e),
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    command = parsed.get("command")
    if not command or command not in cfg.get("commands", []):
        # SPEC §5.2.4 reserves parse_error for envelope-schema failures only.
        # An unknown command is a valid envelope referring to an unregistered
        # command — this is a terminal `error` with error_kind=unknown_command.
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="unknown_command",
            error_detail=f"command not in registry: {command!r}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    # Validate args via per-command schema.
    cmd_schema_path = f"commands/{command}.schema.json"
    try:
        cmd_schema = load_schema(cmd_schema_path, repo_root)
    except FileNotFoundError:
        # Command exists in the registry but the schema file is missing —
        # treat as a more specific terminal error so operators can tell
        # this case apart from a truly unknown command.
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="missing_schema",
            error_detail=f"no schema file for command {command}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    args_schema = cmd_schema.get("properties", {}).get("args")
    if args_schema:
        try:
            validate(parsed.get("args", {}), args_schema)
        except Exception as e:
            return _write_parse_error(
                client,
                comment_id,
                original_body=raw_body,
                error_kind="schema_validation_failed",
                error_detail=f"args: {e}",
                workflow_run_id=workflow_run_id,
                started_at=started_at,
            )

    # Step 3: branch+SHA check --------------------------------------------
    branch = parsed["branch"]
    expected_sha = parsed["commit_sha"]
    head_sha = client.get_branch_head_sha(branch)
    if head_sha is None:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"branch does not exist: {branch}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )
    if head_sha != expected_sha:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"HEAD={head_sha} != commit_sha={expected_sha}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    # Step 4: mark running ------------------------------------------------
    running_envelope = dict(parsed)
    running_envelope["run_status"] = "running"
    running_envelope["run_started_at"] = started_at
    running_envelope["workflow_run_id"] = workflow_run_id
    running_envelope["checked_out_sha"] = head_sha
    client.update_comment(comment_id, json.dumps(running_envelope, indent=2))

    # Step 5: dispatch ----------------------------------------------------
    log_writer = LogWriter(
        max_chunk_bytes_compressed=cfg.get("logs", {}).get("max_chunk_bytes_compressed", 524_288)
    )

    try:
        handler_fn = _load_command_handler(command)
        summary = handler_fn(parsed.get("args", {}) or {}, log_writer, workspace)
        run_status = "completed"
        error_kind: Optional[str] = None
        error_detail: Optional[str] = None
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log_writer.write({
            "ts": iso_now(),
            "stream": "stderr",
            "phase": "exec",
            "data": tb,
        })
        summary = {
            "error_kind": type(e).__name__,
            "error_detail": str(e),
        }
        run_status = "error"
        error_kind = type(e).__name__
        error_detail = str(e)

    finished_at = iso_now()

    # Step 6: validate summary against the command schema -----------------
    summary_schema_key = (
        "summary_completed" if run_status == "completed" else "summary_error"
    )
    summary_schema = cmd_schema.get("properties", {}).get(summary_schema_key)
    if summary_schema is not None:
        try:
            validate(summary, summary_schema)
        except Exception as e:
            run_status = "error"
            error_kind = "summary_schema_violation"
            error_detail = str(e)
            summary = {
                "error_kind": "summary_schema_violation",
                "error_detail": str(e),
            }
            log_writer.write({
                "ts": iso_now(),
                "stream": "stderr",
                "phase": "teardown",
                "data": f"summary schema violation: {e}",
            })

    # Step 7: write logs to _agent_runs ----------------------------------
    chunks = log_writer.finalize()
    manifest = log_writer.manifest(
        command=command,
        args=parsed.get("args", {}) or {},
        checked_out_sha=head_sha,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=0 if run_status == "completed" else 1,
    )

    # Validate the manifest against its schema (defense in depth).
    try:
        manifest_schema = load_schema("log-manifest.schema.json", repo_root)
        validate(manifest, manifest_schema)
    except Exception as e:  # pragma: no cover - manifest is built by us
        log_writer = None  # mark unused
        run_status = "error"
        error_kind = "manifest_schema_violation"
        error_detail = str(e)

    logs_branch = cfg.get("logs", {}).get("branch", "_agent_runs")
    log_dir = f"runs/{issue_number}/{comment_id}"

    summary_json = {
        "summary": summary,
        "run_status": run_status,
        "command": command,
        "args": parsed.get("args", {}) or {},
        "checked_out_sha": head_sha,
        "started_at": started_at,
        "finished_at": finished_at,
    }

    # Ensure the orphan branch exists by writing the manifest first
    # (put_file_contents auto-creates the branch as orphan if missing).
    _retry_put(client, f"{log_dir}/manifest.json",
               json.dumps(manifest, indent=2).encode("utf-8"),
               f"manifest for run {issue_number}/{comment_id}",
               logs_branch)
    for path, gz_bytes, _info in chunks:
        _retry_put(client, f"{log_dir}/{path}", gz_bytes,
                   f"log chunk for {issue_number}/{comment_id}", logs_branch)
    _retry_put(client, f"{log_dir}/summary.json",
               json.dumps(summary_json, indent=2).encode("utf-8"),
               f"summary for {issue_number}/{comment_id}", logs_branch)

    # Step 8: write terminal envelope ------------------------------------
    terminal = dict(running_envelope)
    terminal["run_status"] = run_status
    terminal["run_finished_at"] = finished_at
    terminal["summary"] = summary
    terminal["log_manifest_branch"] = logs_branch
    terminal["log_manifest_path"] = f"{log_dir}/manifest.json"
    if error_kind is not None:
        terminal["error_kind"] = error_kind
    if error_detail is not None:
        terminal["error_detail"] = error_detail

    client.update_comment(comment_id, json.dumps(terminal, indent=2))

    return {
        "action": "ran",
        "command": command,
        "run_status": run_status,
        "summary": summary,
        "log_manifest_path": f"{log_dir}/manifest.json",
        "chunks": [c[0] for c in chunks],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_command_handler(command: str):
    """Import ``.agent/commands/<command>.py`` and return its ``run``."""
    module_name = command.replace("-", "_")
    # Determine the path to the commands directory relative to this file.
    here = os.path.dirname(os.path.abspath(__file__))
    cmd_dir = os.path.normpath(os.path.join(here, os.pardir, "commands"))
    cmd_path = os.path.join(cmd_dir, f"{module_name}.py")
    if not os.path.isfile(cmd_path):
        raise ImportError(f"no command module at {cmd_path}")
    # Use a unique cached module name so dataclass etc. work correctly.
    sys_name = f"_agent_command_{module_name}"
    if sys_name in sys.modules:
        mod = sys.modules[sys_name]
    else:
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location(sys_name, cmd_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not build spec for {cmd_path}")
        mod = module_from_spec(spec)
        sys.modules[sys_name] = mod
        spec.loader.exec_module(mod)
    if not hasattr(mod, "run"):
        raise ImportError(f"command module {module_name} has no run()")
    return mod.run


def _retry_sleep(seconds: float) -> None:
    """Backoff sleep helper. Indirected so tests can stub it out."""
    import time as _time
    _time.sleep(seconds)


def _retry_put(
    client: GitHubClient,
    path: str,
    content: bytes,
    message: str,
    branch: str,
    *,
    retries: int = 6,
) -> None:
    """Put a file with retry + jittered exponential backoff.

    ``put_file_contents`` re-fetches the branch HEAD on each call, so
    each retry sees a fresh ``head_sha``. The backoff between attempts
    spreads out concurrent writers so they don't all collide in the
    same sub-millisecond race window — discovered live during scenario
    02 (multi-subagent), where three handlers writing to ``_agent_runs``
    collided and the (then) no-backoff retry loop exhausted all three
    attempts before any of them could settle.

    Backoff schedule (no-jitter base): 0.5s, 1s, 2s, 4s, 8s, 16s — caps
    at 30s. Each delay is multiplied by a random factor in [0.5, 1.5)
    to spread out concurrent writers further.
    """
    import random as _random

    last_exc: Optional[BaseException] = None
    for attempt in range(retries):
        try:
            client.put_file_contents(path, content, message, branch)
            return
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt + 1 >= retries:
                break
            base = min(0.5 * (2 ** attempt), 30.0)
            jitter = _random.uniform(0.5, 1.5)
            _retry_sleep(base * jitter)
    if last_exc is not None:
        raise last_exc


def _write_parse_error(
    client: GitHubClient,
    comment_id: int,
    *,
    original_body: str,
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    started_at: str,
) -> dict[str, Any]:
    """Replace the comment body with a ``parse_error`` envelope (§5.2.4)."""
    finished_at = iso_now()
    body = {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "run_status": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
        "original_body_b64": b64_encode(original_body),
        "run_started_at": started_at,
        "run_finished_at": finished_at,
        "workflow_run_id": workflow_run_id,
        "agent_ack": None,
    }
    client.update_comment(comment_id, json.dumps(body, indent=2))
    return {
        "action": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def _write_terminal_error(
    *,
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    envelope: dict[str, Any],
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    run_started_at: str,
    cfg: dict[str, Any],
    repo_root: str,
) -> dict[str, Any]:
    """Write a terminal ``error`` envelope (e.g. branch_sha_mismatch)."""
    finished_at = iso_now()
    terminal = dict(envelope)
    terminal["run_status"] = "error"
    terminal["run_started_at"] = run_started_at
    terminal["run_finished_at"] = finished_at
    terminal["workflow_run_id"] = workflow_run_id
    terminal["error_kind"] = error_kind
    terminal["error_detail"] = error_detail
    terminal["summary"] = {"error_kind": error_kind, "error_detail": error_detail}
    client.update_comment(comment_id, json.dumps(terminal, indent=2))
    return {
        "action": "error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def main() -> int:
    """``batch-job-handler`` workflow entry point.

    Required environment variables:
      - ``ISSUE_NUMBER``       issue carrying the request comment
      - ``COMMENT_ID``         comment id holding the envelope
      - ``GH_TOKEN`` / ``GITHUB_TOKEN``  REST API token
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug
    Optional:
      - ``GITHUB_RUN_ID`` / ``WORKFLOW_RUN_ID``  workflow run id echoed
        into the running envelope (default ``0``)
      - ``GITHUB_WORKSPACE``   checkout root passed to command handlers

    On success exits 0; on uncaught exception prints to stderr and
    exits 1. Tests call :func:`run` directly with an in-memory client.
    """
    required = ["ISSUE_NUMBER", "COMMENT_ID", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    print(
        "handler: required env vars: "
        + ", ".join(required)
        + ". Optional: GITHUB_RUN_ID, GITHUB_WORKSPACE.",
        file=sys.stderr,
    )
    issue_number = os.environ.get("ISSUE_NUMBER")
    comment_id = os.environ.get("COMMENT_ID")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    missing = [
        name for name, val in (
            ("ISSUE_NUMBER", issue_number),
            ("COMMENT_ID", comment_id),
            ("GITHUB_TOKEN", token),
            ("GITHUB_REPOSITORY", repo_slug),
        ) if not val
    ]
    if missing:
        print(f"handler: missing env vars: {missing}", file=sys.stderr)
        return 1
    assert issue_number is not None and comment_id is not None
    assert token is not None and repo_slug is not None
    if "/" not in repo_slug:
        print(
            f"handler: GITHUB_REPOSITORY must be 'owner/repo', got: {repo_slug!r}",
            file=sys.stderr,
        )
        return 1
    owner, repo = repo_slug.split("/", 1)
    workflow_run_id_str = (
        os.environ.get("GITHUB_RUN_ID") or os.environ.get("WORKFLOW_RUN_ID") or "0"
    )
    try:
        workflow_run_id = int(workflow_run_id_str)
    except ValueError:
        workflow_run_id = 0
    workspace = os.environ.get("GITHUB_WORKSPACE")
    print(
        "handler: dispatching issue "
        f"#{issue_number} comment {comment_id}",
        file=sys.stderr,
    )
    try:
        # Imported lazily so this script remains usable even if requests
        # is missing (e.g. when only run() is invoked from tests).
        if __package__ in (None, ""):
            from rest_client import RestGitHubClient  # type: ignore[import-not-found]
        else:
            from .rest_client import RestGitHubClient
        client = RestGitHubClient(token=token, owner=owner, repo=repo)
        run(
            client,
            int(issue_number),
            int(comment_id),
            workflow_run_id=workflow_run_id,
            workspace=workspace,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"handler: uncaught exception: {exc!r}", file=sys.stderr)
        traceback.print_exc()
        # Self-diagnostic: post a comment on the originating issue with the
        # traceback, so MCP-only operators (who can't read workflow logs)
        # can see what went wrong. Wrapped in its own try/except so a
        # failure here can't mask the original exit code.
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                _post_debug_comment(
                    token=token,
                    owner=owner,
                    repo=repo,
                    issue_number=int(issue_number),
                    script="handler.py",
                    exc=exc,
                    extra_fields={
                        "comment": comment_id,
                        "workflow run": workflow_run_id,
                    },
                )
            except Exception as diag_exc:  # noqa: BLE001
                print(
                    f"handler: failed to post debug comment: {diag_exc!r}",
                    file=sys.stderr,
                )
        return 1
    return 0


def _post_debug_comment(
    *,
    token: str,
    owner: str,
    repo: str,
    issue_number: int,
    script: str,
    exc: BaseException,
    extra_fields: Optional[dict[str, Any]] = None,
) -> None:
    """Post a self-diagnostic comment with traceback to the given issue.

    Uses ``requests.post`` directly to avoid depending on any code path
    that might itself be the source of the bug being diagnosed. Secrets
    are never echoed; the env-var summary only reports presence/absence.
    """
    import requests  # local import: keeps run() importable without requests

    # Summarise env vars without leaking secrets.
    secret_names = {"GH_TOKEN", "GITHUB_TOKEN"}
    relevant = [
        "ISSUE_NUMBER", "COMMENT_ID", "PR_NUMBER",
        "GH_TOKEN", "GITHUB_TOKEN", "GITHUB_REPOSITORY",
        "GITHUB_RUN_ID", "WORKFLOW_RUN_ID", "GITHUB_WORKSPACE",
        "AGENT_LOGIN", "AGENT_TASK_LABEL",
    ]
    env_lines = []
    for name in relevant:
        val = os.environ.get(name)
        if name in secret_names:
            env_lines.append(f"  - {name}: {'set' if val else 'unset'}")
        elif val is not None:
            env_lines.append(f"  - {name}: {val!r}")
        else:
            env_lines.append(f"  - {name}: unset")

    fields_lines = [f"- script: `{script}`", f"- issue: #{issue_number}"]
    for k, v in (extra_fields or {}).items():
        fields_lines.append(f"- {k}: {v}")
    fields_lines.append(f"- python: {sys.version.split()[0]}")

    debug_body = (
        "**handler self-diagnostic — uncaught exception**\n\n"
        + "\n".join(fields_lines)
        + "\n\n"
        + f"```\n{exc!r}\n```\n\n"
        + "<details><summary>Traceback</summary>\n\n"
        + f"```\n{traceback.format_exc()}```\n\n"
        + "</details>\n\n"
        + "<details><summary>Environment</summary>\n\n"
        + "\n".join(env_lines)
        + "\n\n</details>\n"
    )

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.post(url, headers=headers, json={"body": debug_body}, timeout=15)
    # Don't raise — caller wraps us anyway; but record non-2xx status.
    if resp.status_code >= 300:
        print(
            f"handler: debug comment POST returned {resp.status_code}: {resp.text[:200]!r}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(main())

````

### .claude/skills/orchestrate-issue/templates/agent/scripts/lock_and_sweep.py

```text
"""``lock-and-sweep`` script (§7.1).

Run on ``issues.opened``. Validates the issue belongs to the protocol
(creator is ``agent_login`` and body contains a parsable ``agent-meta``
block); applies the ``agent-task`` label; sweeps any non-agent comments
that snuck in before the label was applied.

Historically this script also locked the issue at creation time, but
GitHub refuses comments from ``GITHUB_TOKEN`` (the github-actions[bot]
identity) on locked issues — including the batch-job-handler's own
terminal envelope writes. Locking is therefore deferred to
``close_on_merge.py`` (post-merge), where the lock acts as an
audit-tamper-prevention seal rather than an injection guard. The
injection-guard role is filled by the batch-job-handler workflow's
label + author ``if:`` filter, which makes foreign comments inert.

``agent_login`` is sourced from the ``AGENT_LOGIN`` environment variable
(populated from a repo-level GitHub Actions variable so multi-user
deployments don't require workflow-YAML edits) or passed in explicitly
by tests. The static ``agent_login`` config key was removed in session 3
to drop the indirection.

Importable as a module: call :func:`run` directly with a
``GitHubClient`` for tests. The ``__main__`` entry point reads
environment variables (``ISSUE_NUMBER``, ``AGENT_LOGIN``) and is wired
up by the workflow file.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

# When run as a script the package isn't on sys.path; add repo root.
if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        load_config,
        parse_agent_meta,
    )
else:
    from .common import GitHubClient, load_config, parse_agent_meta


def run(
    client: GitHubClient,
    issue_number: int,
    agent_login: Optional[str] = None,
    agent_task_label: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Apply lock-and-sweep behaviour to an issue.

    ``agent_login`` resolution order: explicit argument → ``AGENT_LOGIN``
    environment variable → raise. There is no fallback to a static config
    key (removed in session 3).

    Returns a small dict describing what happened (useful for tests).
    """
    cfg = config or load_config()
    if agent_login is None:
        agent_login = os.environ.get("AGENT_LOGIN") or None
    if not agent_login:
        raise RuntimeError(
            "agent_login is required: pass it explicitly or set the "
            "AGENT_LOGIN environment variable (typically populated by the "
            "workflow from vars.AGENT_LOGIN)"
        )
    agent_task_label = (
        agent_task_label
        or cfg.get("labels", {}).get("agent_task", "agent-task")
    )

    issue = client.get_issue(issue_number)
    body = issue.get("body") or ""
    creator_login = (issue.get("user") or {}).get("login")

    meta = parse_agent_meta(body)
    if meta is None:
        return {"action": "noop", "reason": "no_agent_meta"}
    if creator_login != agent_login:
        return {"action": "noop", "reason": "creator_not_agent_login"}

    # 1. Apply label.
    client.add_label(issue_number, agent_task_label)

    # 2. Sweep non-agent comments that snuck in before the label was
    #    applied. We deliberately do NOT lock the issue here: a locked
    #    issue rejects comments from the GITHUB_TOKEN bot identity, and
    #    the batch-job-handler workflow needs to write its terminal
    #    envelope back as a comment. The lock is applied later by
    #    close_on_merge.py once the issue is finished.
    deleted = 0
    kept_unexpected = 0
    for c in client.list_comments(issue_number):
        author = (c.get("user") or {}).get("login")
        cid = c["id"]
        if author == agent_login:
            kept_unexpected += 1
            continue
        client.delete_comment(cid)
        deleted += 1

    return {
        "action": "labeled",
        "label_applied": agent_task_label,
        "deleted_comments": deleted,
        "kept_agent_comments": kept_unexpected,
    }


def main() -> int:
    """``lock-and-sweep`` workflow entry point.

    Required environment variables:
      - ``ISSUE_NUMBER``       the issue that just opened
      - ``GH_TOKEN`` / ``GITHUB_TOKEN``  REST API token
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug
      - ``AGENT_LOGIN``        bot login the protocol expects to author
                                envelopes (set from ``vars.AGENT_LOGIN``)
    Optional:
      - ``AGENT_TASK_LABEL``   override the label from ``.agent/config.json``

    On success exits 0; on uncaught exception prints to stderr and
    exits 1. Tests call :func:`run` directly with an in-memory client.
    """
    required = ["ISSUE_NUMBER", "GITHUB_TOKEN", "GITHUB_REPOSITORY", "AGENT_LOGIN"]
    print(
        "lock_and_sweep: required env vars: "
        + ", ".join(required)
        + ". Optional: AGENT_LOGIN, AGENT_TASK_LABEL.",
        file=sys.stderr,
    )
    issue_number = os.environ.get("ISSUE_NUMBER")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    agent_login = os.environ.get("AGENT_LOGIN") or None
    missing = [
        name for name, val in (
            ("ISSUE_NUMBER", issue_number),
            ("GITHUB_TOKEN", token),
            ("GITHUB_REPOSITORY", repo_slug),
            ("AGENT_LOGIN", agent_login),
        ) if not val
    ]
    if missing:
        print(f"lock_and_sweep: missing env vars: {missing}", file=sys.stderr)
        return 1
    assert issue_number is not None and token is not None and repo_slug is not None
    assert agent_login is not None
    if "/" not in repo_slug:
        print(
            f"lock_and_sweep: GITHUB_REPOSITORY must be 'owner/repo', got: {repo_slug!r}",
            file=sys.stderr,
        )
        return 1
    owner, repo = repo_slug.split("/", 1)
    print(
        f"lock_and_sweep: processing issue #{issue_number}",
        file=sys.stderr,
    )
    try:
        if __package__ in (None, ""):
            from rest_client import RestGitHubClient  # type: ignore[import-not-found]
        else:
            from .rest_client import RestGitHubClient
        client = RestGitHubClient(token=token, owner=owner, repo=repo)
        run(
            client,
            int(issue_number),
            agent_login=agent_login,
            agent_task_label=os.environ.get("AGENT_TASK_LABEL") or None,
        )
    except Exception as exc:  # noqa: BLE001
        import traceback as _tb
        print(f"lock_and_sweep: uncaught exception: {exc!r}", file=sys.stderr)
        _tb.print_exc()
        # Self-diagnostic: post a debug comment on the originating issue.
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                if __package__ in (None, ""):
                    from handler import _post_debug_comment  # type: ignore[import-not-found]
                else:
                    from .handler import _post_debug_comment
                _post_debug_comment(
                    token=token,
                    owner=owner,
                    repo=repo,
                    issue_number=int(issue_number),
                    script="lock_and_sweep.py",
                    exc=exc,
                    extra_fields={},
                )
            except Exception as diag_exc:  # noqa: BLE001
                print(
                    f"lock_and_sweep: failed to post debug comment: {diag_exc!r}",
                    file=sys.stderr,
                )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/requirements.txt

```text
jsonschema>=4.21.0
PyYAML>=6.0
requests>=2.31.0

```

### .claude/skills/orchestrate-issue/templates/agent/scripts/rest_client.py

```text
"""Live REST-backed implementation of the :class:`GitHubClient` Protocol.

This is the workflow side of the agent-job protocol: it is invoked from
GitHub Actions runners using ``GITHUB_TOKEN`` and talks to the
GitHub REST API.

The implementation focuses on the operations the workflow scripts need:

- Issues / labels / lock
- Comments (list, get, add, update, delete)
- Files (read, write — including orphan-branch creation for ``_agent_runs``)
- Branches (head SHA lookup, delete)
- Pull requests (create, get)

It also performs:

- Bearer-token auth with the standard GitHub headers.
- Bounded retry-with-backoff for 5xx and rate-limited 403 responses.
- The blob/tree/commit/ref dance required to commit to a fresh
  orphan branch (the Contents API cannot create branches).
"""

from __future__ import annotations

import base64
import time
from typing import Any, Optional

import requests


_DEFAULT_BASE_URL = "https://api.github.com"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 5
_BACKOFF_SECONDS = (1.0, 2.0, 4.0, 8.0, 16.0)


class RestGitHubClient:
    """REST implementation of the protocol used by the workflow scripts."""

    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        session: Optional[requests.Session] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        sleep: Any = time.sleep,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        if not owner or not repo:
            raise ValueError("owner and repo are required")
        self._token = token
        self._owner = owner
        self._repo = repo
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._sleep = sleep

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @property
    def _repo_path(self) -> str:
        return f"/repos/{self._owner}/{self._repo}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-job-protocol-poc",
        }

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self._base_url + path

    def _is_rate_limited(self, resp: requests.Response) -> bool:
        if resp.status_code != 403:
            return False
        # Primary rate limit signalled by remaining=0.
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining == "0":
            return True
        # Secondary rate limit / abuse detection signalled by Retry-After.
        if resp.headers.get("Retry-After"):
            return True
        # Some endpoints simply put it in the body.
        try:
            j = resp.json()
        except ValueError:
            return False
        msg = (j.get("message") or "").lower() if isinstance(j, dict) else ""
        return "rate limit" in msg or "abuse" in msg or "secondary rate" in msg

    def _rate_limit_sleep(self, resp: requests.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        reset = resp.headers.get("X-RateLimit-Reset")
        if reset:
            try:
                delta = float(reset) - time.time()
                if delta > 0:
                    # Cap the backoff so a clock-skew or far-future reset
                    # doesn't stall the runner forever.
                    return min(delta, 60.0)
            except ValueError:
                pass
        # Fall back to exponential backoff.
        return _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        allow_404: bool = False,
    ) -> requests.Response:
        """Perform an HTTP request with retry on 5xx and rate-limited 403.

        Retries up to ``_MAX_RETRIES`` times. 4xx (other than rate-limited
        403) raise immediately via ``raise_for_status``. When ``allow_404``
        is True, a 404 response is returned without raising.
        """
        url = self._url(path)
        last_resp: Optional[requests.Response] = None
        for attempt in range(_MAX_RETRIES):
            resp = self._session.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=params,
                timeout=self._timeout,
            )
            last_resp = resp
            if 200 <= resp.status_code < 300:
                return resp
            if resp.status_code == 404 and allow_404:
                return resp
            # Deterministic client errors: do NOT retry.
            if resp.status_code in (400, 401, 404, 405, 409, 410, 422):
                resp.raise_for_status()
                return resp  # unreachable; for mypy
            # Rate-limited 403: sleep then retry.
            if resp.status_code == 403 and self._is_rate_limited(resp):
                if attempt < _MAX_RETRIES - 1:
                    self._sleep(self._rate_limit_sleep(resp, attempt))
                    continue
                resp.raise_for_status()
                return resp
            # Other 4xx (e.g. plain 403 forbidden) — don't retry.
            if 400 <= resp.status_code < 500:
                resp.raise_for_status()
                return resp
            # 5xx — retry with exponential backoff.
            if attempt < _MAX_RETRIES - 1:
                self._sleep(_BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)])
                continue
            resp.raise_for_status()
            return resp
        assert last_resp is not None
        last_resp.raise_for_status()
        return last_resp  # unreachable

    # ------------------------------------------------------------------
    # Issue API
    # ------------------------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/issues/{number}")
        return resp.json()

    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        if labels is not None:
            payload["labels"] = list(labels)
        resp = self._request("PATCH", f"{self._repo_path}/issues/{number}", json=payload)
        return resp.json()

    def lock_issue(self, number: int) -> None:
        # PUT /repos/{owner}/{repo}/issues/{n}/lock returns 204 No Content.
        self._request("PUT", f"{self._repo_path}/issues/{number}/lock", json={})

    def add_label(self, number: int, label: str) -> None:
        self._request(
            "POST",
            f"{self._repo_path}/issues/{number}/labels",
            json={"labels": [label]},
        )

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = list(labels)
        resp = self._request("POST", f"{self._repo_path}/issues", json=payload)
        return resp.json()

    # ------------------------------------------------------------------
    # Comment API
    # ------------------------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]:
        # Paginate by following the Link header's ``rel="next"``.
        out: list[dict[str, Any]] = []
        path = f"{self._repo_path}/issues/{issue_number}/comments"
        params: Optional[dict[str, Any]] = {"per_page": 100}
        while True:
            resp = self._request("GET", path, params=params)
            page = resp.json() or []
            out.extend(page)
            next_url = _next_link(resp.headers.get("Link", ""))
            if not next_url:
                break
            path = next_url
            params = None  # the URL already contains the query string
        return out

    def get_comment(self, comment_id: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/issues/comments/{comment_id}")
        return resp.json()

    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        resp = self._request(
            "PATCH",
            f"{self._repo_path}/issues/comments/{comment_id}",
            json={"body": body},
        )
        return resp.json()

    def delete_comment(self, comment_id: int) -> None:
        self._request("DELETE", f"{self._repo_path}/issues/comments/{comment_id}")

    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        resp = self._request(
            "POST",
            f"{self._repo_path}/issues/{issue_number}/comments",
            json={"body": body},
        )
        return resp.json()

    # ------------------------------------------------------------------
    # File / branch operations
    # ------------------------------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]:
        """Return the file contents at ``ref`` (utf-8 text or base64).

        Returns ``None`` on 404. Mirrors :class:`InMemoryGitHubClient`:
        attempts utf-8 decoding; returns base64 on failure.
        """
        resp = self._request(
            "GET",
            f"{self._repo_path}/contents/{path}",
            params={"ref": ref},
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        if isinstance(body, list):
            # ``path`` resolved to a directory — treat like "no file".
            return None
        encoding = body.get("encoding")
        content = body.get("content") or ""
        if encoding == "base64":
            try:
                raw = base64.b64decode(content)
            except (ValueError, base64.binascii.Error):  # type: ignore[attr-defined]
                return content
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(raw).decode("ascii")
        # Unknown encoding: return as-is.
        return content if isinstance(content, str) else None

    def _get_file_sha(self, path: str, branch: str) -> Optional[str]:
        """Return the blob sha of ``path`` on ``branch`` if it exists."""
        resp = self._request(
            "GET",
            f"{self._repo_path}/contents/{path}",
            params={"ref": branch},
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        if isinstance(body, list):
            return None
        sha = body.get("sha")
        return sha if isinstance(sha, str) else None

    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        """Commit a file to ``branch``.

        If ``branch`` does not exist, create it as an orphan via the Git
        Database API (blob/tree/commit with empty parents/ref). If the
        branch exists, prefer the simple Contents API path; if that fails
        we fall back to the Git Database API for the next-commit case
        (blob/tree-with-base/commit-with-parent/patch-ref) so additional
        files on ``_agent_runs`` accumulate into the tree correctly.
        """
        head_sha = self.get_branch_head_sha(branch)
        if head_sha is None:
            return self._create_orphan_commit(path, content_bytes, message, branch)
        # Branch exists — use the Git Database API so the tree is
        # explicitly built from the previous commit, preserving existing
        # files (Contents API would also do this implicitly, but the GDB
        # path is what we tested for orphan-branch follow-ups).
        return self._append_commit(path, content_bytes, message, branch, head_sha)

    def _create_orphan_commit(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        blob_sha = self._create_blob(content_bytes)
        tree_sha = self._create_tree(
            [{"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}],
            base_tree=None,
        )
        commit_sha = self._create_commit(message, tree_sha, parents=[])
        # Create the ref; raises if it already exists.
        self._request(
            "POST",
            f"{self._repo_path}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": commit_sha},
        )
        return {
            "path": path,
            "branch": branch,
            "commit": {"sha": commit_sha, "message": message},
            "size": len(content_bytes),
        }

    def _append_commit(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
        parent_sha: str,
    ) -> dict[str, Any]:
        # Get the parent commit's tree sha.
        resp = self._request("GET", f"{self._repo_path}/git/commits/{parent_sha}")
        parent_tree_sha = resp.json()["tree"]["sha"]
        blob_sha = self._create_blob(content_bytes)
        tree_sha = self._create_tree(
            [{"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}],
            base_tree=parent_tree_sha,
        )
        commit_sha = self._create_commit(message, tree_sha, parents=[parent_sha])
        self._request(
            "PATCH",
            f"{self._repo_path}/git/refs/heads/{branch}",
            json={"sha": commit_sha},
        )
        return {
            "path": path,
            "branch": branch,
            "commit": {"sha": commit_sha, "message": message},
            "size": len(content_bytes),
        }

    def _create_blob(self, content_bytes: bytes) -> str:
        b64 = base64.b64encode(content_bytes).decode("ascii")
        resp = self._request(
            "POST",
            f"{self._repo_path}/git/blobs",
            json={"content": b64, "encoding": "base64"},
        )
        return resp.json()["sha"]

    def _create_tree(
        self,
        entries: list[dict[str, Any]],
        *,
        base_tree: Optional[str],
    ) -> str:
        payload: dict[str, Any] = {"tree": entries}
        if base_tree is not None:
            payload["base_tree"] = base_tree
        resp = self._request("POST", f"{self._repo_path}/git/trees", json=payload)
        return resp.json()["sha"]

    def _create_commit(
        self,
        message: str,
        tree_sha: str,
        *,
        parents: list[str],
    ) -> str:
        payload: dict[str, Any] = {
            "message": message,
            "tree": tree_sha,
            "parents": list(parents),
        }
        resp = self._request("POST", f"{self._repo_path}/git/commits", json=payload)
        return resp.json()["sha"]

    def get_branch_head_sha(self, branch: str) -> Optional[str]:
        resp = self._request(
            "GET",
            f"{self._repo_path}/git/refs/heads/{branch}",
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        # The refs endpoint returns an object for a single match; some
        # variations of the API return a list when the prefix matched
        # multiple refs. Defensive parsing handles both.
        if isinstance(body, list):
            for entry in body:
                if entry.get("ref") == f"refs/heads/{branch}":
                    return entry.get("object", {}).get("sha")
            return None
        obj = body.get("object") or {}
        sha = obj.get("sha")
        return sha if isinstance(sha, str) else None

    def delete_branch(self, name: str) -> None:
        # 404 is treated as success (idempotent), matching the in-memory client.
        resp = self._request(
            "DELETE",
            f"{self._repo_path}/git/refs/heads/{name}",
            allow_404=True,
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()

    def list_branches(self) -> list[dict[str, Any]]:
        """List branches in the repo, paginated.

        Returns a list of ``{"name": str, "sha": str, "protected": bool}``
        entries built from the REST ``GET /repos/{owner}/{repo}/branches``
        response. Pagination follows the ``Link: rel="next"`` header.
        """
        out: list[dict[str, Any]] = []
        path = f"{self._repo_path}/branches"
        params: Optional[dict[str, Any]] = {"per_page": 100}
        while True:
            resp = self._request("GET", path, params=params)
            page = resp.json() or []
            for b in page:
                if not isinstance(b, dict):
                    continue
                commit = b.get("commit") or {}
                out.append({
                    "name": b.get("name"),
                    "sha": commit.get("sha"),
                    "protected": bool(b.get("protected", False)),
                })
            next_url = _next_link(resp.headers.get("Link", ""))
            if not next_url:
                break
            path = next_url
            params = None
        return out

    # ------------------------------------------------------------------
    # PR API
    # ------------------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]:
        resp = self._request(
            "POST",
            f"{self._repo_path}/pulls",
            json={"title": title, "head": head, "base": base, "body": body},
        )
        return resp.json()

    def get_pull_request(self, number: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/pulls/{number}")
        return resp.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_link(link_header: str) -> Optional[str]:
    """Parse a ``Link`` header and return the URL with ``rel="next"``."""
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) < 2:
            continue
        url_part = section[0].strip()
        if not (url_part.startswith("<") and url_part.endswith(">")):
            continue
        rel = None
        for s in section[1:]:
            s = s.strip()
            if s.startswith("rel="):
                rel = s.split("=", 1)[1].strip().strip('"')
                break
        if rel == "next":
            return url_part[1:-1]
    return None


__all__ = ["RestGitHubClient"]

```

### .claude/skills/orchestrate-issue/templates/brief-template.md

````text
# Subagent brief — `<run_id>` / `<sub_id>`

> This template is consumed by the `orchestrate-issue` skill during
> Phase 5 (fanout). Tokens in angle brackets (`<placeholder>`) are
> substituted at dispatch time. Do not edit at the target-repo
> level — this file is internal to the skill.

## 1. Identity + goal

You are subagent `<sub_id>` for issue `<issue_number>` in run
`<run_id>`. Your task is to deliver one subtask of a multi-subagent
fanout managed by the `orchestrate-issue` skill.

Goal: `<one_sentence_goal>`.

## 2. Context

- Parent issue: `<issue_url>`
- Issue title: `<issue_title>`
- Issue body excerpt: `<issue_body_excerpt>`
- Spec or instructions: `<instructions_source>` (`inline` or path)
- Run ID: `<run_id>`
- Run state file: `.agent/runs/<run_id>/state.json`
- Plan brief (full): `<plan_brief_path>`

You have already-installed agent-job protocol templates in the
target repo. Do not modify `.agent/`, `.github/workflows/`, or any
other subagent's sub-branch.

## 3. Repo and branch

- Repo: `<repo_owner>/<repo_name>`
- Feature branch (the orchestrator's branch): `<feature_branch>`
- Your sub-branch (already created from feature tip): `<feature_branch>--<sub_id>`
- Commit and push **only** to `<feature_branch>--<sub_id>`. Do not
  switch branches. Do not push to `<feature_branch>`. Do not rebase.

The double-dash separator is mandatory (POC SPEC §6). Never write a
single-slash variant.

## 4. What to build

Subtask description: `<subtask_description>`.

Files you may touch (disjoint by plan construction):

- `<file_path_1>`
- `<file_path_2>`
- `<...>`

Concrete bullets (3-7 items):

- `<bullet_1>`
- `<bullet_2>`
- `<bullet_3>`
- `<bullet_n>`

## 5. Protocol contract

When your code changes are committed and pushed to
`<feature_branch>--<sub_id>`, invoke the `batch-job` skill with:

```yaml
issue_number: <issue_number>
command: <command_name>           # one of .agent/config.json :: commands
args: <command_args>              # validated against the command schema
branch: <feature_branch>--<sub_id>
commit_sha: <head_sha>            # full 40-char SHA of your branch tip
subagent_id: <sub_id>
agent_id: <agent_id>              # the orchestrator's agent_id; do not invent
ack_mode: follow_up               # MCP-only callers default
```

Wait for the **terminal ack** from `batch-job` (it returns the
envelope, summary, summary_json, ack_comment_id, log_manifest_path).
Only then are you allowed to return to the orchestrator.

If `batch-job` raises a typed exception (RunnerPickupTimeoutError,
RunningTimeoutError, BranchShaMismatchError, ParseErrorTerminal,
SummarySchemaViolation), capture it in your report — do not retry
on the same branch + SHA.

## 6. Don'ts

- Do **not** merge your sub-branch into `<feature_branch>`. The
  orchestrator merges in plan order in Phase 7.
- Do **not** switch to another sub-branch.
- Do **not** touch files outside the `files_touched` list above.
- Do **not** open the PR — that is Phase 8.
- Do **not** modify the issue's `agent-meta` block — that is the
  orchestrator's job.
- Do **not** invoke `task-dag` or `orchestrate-issue` — you are
  scoped to one subtask + one batch-job.
- Do **not** force-push or rewrite history on your sub-branch.

## 7. Validation

Before reporting back to the orchestrator, assert locally:

- `git rev-parse --abbrev-ref HEAD` equals `<feature_branch>--<sub_id>`.
- `git status` reports clean working tree.
- `git log <feature_branch>..HEAD --oneline` shows your commits only
  (no merges from other sub-branches).
- The `batch-job` ack envelope reported a terminal status.
- The summary JSON validates against the command's schema (the
  `batch-job` skill already enforces this; double-check the ack
  carried no schema-violation error).

## 8. Deliverable shape

Report back to the orchestrator with this exact structure:

```yaml
sub_id: <sub_id>
sub_branch: <feature_branch>--<sub_id>
head_sha: <40-char SHA>
batch_job_request_comment_id: <int>
batch_job_ack_comment_id: <int>
batch_job_terminal_status: <completed|failed|error>
summary_excerpt: <one-line summary from envelope>
summary_json_path: <path returned by batch-job>
log_manifest_path: <path returned by batch-job>
tests_delta: <"+N" / "-N" / "0" / "n/a">
files_changed: <int>
issues_encountered: <list or "none">
elapsed_seconds: <int>
deviations: <list or "none">
```

## 9. Traps

- **Double-dash separator.** Always `<feature_branch>--<sub_id>`,
  never `<feature_branch>/<sub_id>`. The lock-and-sweep workflow
  parses on `--`.
- **MCP comment-trailer tolerance.** Claude Code's MCP appends a
  trailer to comment bodies. `batch-job`'s envelope parser already
  tolerates it; do not strip it manually.
- **`agent_id` is the orchestrator's, not yours.** Subagents share
  the parent's `agent_id` so the issue heartbeat keeps working.
- **`isolation: "worktree"`.** You are running inside an isolated
  worktree. Treat the cwd as your sandbox; do not `cd` outside it.
- **Branch SHA verification.** `batch-job`'s `commit_sha` field must
  exactly match the runner's view of `git rev-parse <branch>`. Push
  before invoking `batch-job` — runners pull from origin.
- **Do not retry `BranchShaMismatchError` with the same SHA.** Push
  a fresh commit (even an empty `--allow-empty`) and call again.
- **Heartbeat.** `batch-job` accepts an optional `heartbeat`
  callable. Pass the one the orchestrator provided if any; do not
  invent your own — only the orchestrator may refresh `status_ts`
  on the parent issue.
- **Unattended mode.** If `dry_run` is True or the orchestrator
  flagged the run unattended, you must still complete the work but
  must not prompt for user input. Default-decide based on the
  contract; surface ambiguity in `deviations`.

````

### .claude/skills/orchestrate-issue/templates/github/workflows/batch-job-handler.yml

```text
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
      github.event.comment.user.login == (vars.AGENT_LOGIN || 'jonathanmanton')
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - name: marker-start
        run: |
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d '{"body":"<!-- workflow-marker -->\n[handler-start] run=${{ github.run_id }} comment=${{ github.event.comment.id }}"}' \
            > /tmp/marker-start.json || true
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r .agent/scripts/requirements.txt
      - id: handler
        run: python .agent/scripts/handler.py 2>&1 | tee /tmp/handler.log
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          COMMENT_ID: ${{ github.event.comment.id }}
          WORKFLOW_RUN_ID: ${{ github.run_id }}
          AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}
      - name: marker-end
        if: always()
        run: |
          conclusion="${{ steps.handler.conclusion }}"
          # Trim and base64 just to embed cleanly; readers can decode
          tail_b64=$(tail -c 4000 /tmp/handler.log 2>/dev/null | base64 -w0 || echo "")
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d "{\"body\":\"<!-- workflow-marker -->\n[handler-end] run=${{ github.run_id }} comment=${{ github.event.comment.id }} conclusion=${conclusion}\n\n<details><summary>last 4KB of stdout/stderr (base64)</summary>\n\n\`\`\`\n${tail_b64}\n\`\`\`\n\n</details>\"}" \
            > /tmp/marker-end.json || true

```

### .claude/skills/orchestrate-issue/templates/github/workflows/close-on-merge.yml

```text
name: close-on-merge
on:
  pull_request:
    types: [closed]
permissions:
  issues: write
  pull-requests: read
  contents: write
jobs:
  close:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r .agent/scripts/requirements.txt
      - run: python .agent/scripts/close_on_merge.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}

```

### .claude/skills/orchestrate-issue/templates/github/workflows/lock-and-sweep.yml

```text
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
        with:
          python-version: '3.12'
      - run: pip install -r .agent/scripts/requirements.txt
      - run: python .agent/scripts/lock_and_sweep.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}

```

### .claude/skills/task-dag/README.md

```text
This is the `task-dag` distributable skill. Entry point: SKILL.md.
Implementation spec: SPEC.md. Templates self-installed into the target
repo on first invocation. Composable with batch-job.

```

### .claude/skills/task-dag/SKILL.md

````text
---
name: task-dag
description: |
  Manage one agent-task GitHub issue as a DAG node: claim it, plan
  subagents, merge subagent branches, and schedule follow-up issues.
  Self-installs the protocol's workflow + script templates on first
  invocation. Use when an agent is taking ownership of a multi-step
  task represented by a GitHub issue.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__github__issue_read
  - mcp__github__issue_write
  - mcp__github__add_issue_comment
  - mcp__github__create_branch
  - mcp__github__list_issues
  - mcp__github__list_branches
  - mcp__github__create_or_update_file
---

# task-dag

Manage the lifecycle of one agent-task GitHub issue as a DAG node.
The skill exposes four primitives — **claim**, **plan**, **merge**, and
**schedule_successors** — plus a `heartbeat()` helper for the polling
loop. It is the agent-side primitive for issue ownership. It does
**not** dispatch batch jobs (that is the `batch-job` skill) and does
**not** spawn subagents (the calling harness or `orchestrate-issue`
handles that).

The full design contract lives in `SPEC.md` next to this file; the
canonical protocol behind both lives at POC `SPEC.md` §4.1 (state
machine), §6 (branching model), and §10 (task-dag skill).

## When to use this skill

This skill matches when an agent is asked to:

- "Claim an issue and start working on it"
- "Find an unclaimed agent-task issue"
- "Plan subagents for issue N"
- "Merge subagent branches into the feature branch"
- "Schedule follow-up issues for this DAG node"
- "Use the task-dag skill"

It does **not** match generic GitHub issue work outside the agent-job
protocol — there is no `agent-task` label, no `agent-meta` block in
the issue body, no `_agent_runs` branch.

## Operations

### `claim` — take ownership of an issue

| Input | Type | Notes |
|---|---|---|
| `agent_id` | string | UUID-recommended; this process's identity |
| `agent_login` | string | The bot account login (sourced via `mcp__github__get_me` if not provided) |
| `candidate_issues` | list[int] | Optional; if omitted, scan open issues with `agent-task` label |

Output: `{issue, meta, agent_id, session_id}` if claimed, else `None`.

Implementation: `lib/claim.py`.

### `plan` — produce the work brief

| Input | Type | Notes |
|---|---|---|
| `issue_number` | int | Required |
| `agent_login` | string | Used to filter comments |

Output: `{brief, source, subagent_layout}` where `source` is `inline`
or the resolved `instructions_path`.

Implementation: `lib/plan.py`.

### `merge_subagent_branches` — overlay sub-branches into the feature branch

| Input | Type | Notes |
|---|---|---|
| `feature_branch` | string | Required |
| `subagent_branches` | list[string] | Required, in plan order |
| `conflict_strategy` | enum | `fail` (default), `ours`, `theirs`, `manual` |

Output: `{merged: [...], conflicts: [...], skipped: [...]}`.

Implementation: `lib/merge.py`. **Branches merge in plan order, not in
completion order.** The default conflict strategy is `fail`; silent
auto-merges mask integration bugs.

### `schedule_successors` — open follow-up issues

| Input | Type | Notes |
|---|---|---|
| `successors` | list[dict] | Each dict has `title`, `body`, `depends_on_prs`, `parent_issue` |
| `base_branch` | string | Default branch the successors fork from |

Output: list of created issue numbers.

Implementation: `lib/schedule_successors.py`. Successors are created
with `status: null` so any qualifying agent — this one or a later one
— can claim them.

## Procedure

These behaviours map directly onto POC `SPEC.md` §4.1, §6, and §10.

### Claim handshake (CAS-by-re-read)

1. Scan candidates (provided list, or open issues with the
   `agent-task` label).
2. Filter to those whose `status` is `null` or `status == "working"`
   with `status_ts` older than `issue.stale_seconds` (default 7200).
3. For the first eligible issue, write `agent_id` (your own) and a
   fresh `status_ts` into the `agent-meta` block via
   `mcp__github__issue_write`.
4. Sleep 5 seconds.
5. Re-read the issue. If `agent_id` is still ours, the claim
   succeeded — return `{issue, meta, agent_id, session_id}`. If a
   different `agent_id` is in the body, **self-abandon silently** and
   return `None`. The losing party never rewrites the body.

### Heartbeat

`task-dag` exposes a `heartbeat()` helper called inside every
polling cycle (typically by the `batch-job` skill while it polls a
comment to terminal status). It:

1. Re-reads the issue body.
2. Asserts `agent_id` matches the running process. On mismatch, the
   primary self-abandons.
3. Writes a fresh `status_ts`.

Throttled to at most one write per `issue.heartbeat_min_interval_seconds`
(default 60) to avoid issue-edit rate limits during long batch jobs.

### Merge order

Subagent branches **must** be merged in the order the plan declared,
not in the order their batch jobs returned. Completion-order merges
silently reorder commits and hide subtle integration bugs. The
`conflict_strategy` parameter controls behaviour on conflict:

| value | effect |
|---|---|
| `fail` (default) | abort the merge run; surface the conflicting branch and paths to the caller |
| `ours` | resolve via `git merge -X ours`; record the override in the result |
| `theirs` | resolve via `git merge -X theirs`; record the override |
| `manual` | leave the conflict markers in place and yield to the caller |

### Successors

`schedule_successors` creates new issues with `status: null` and
the same `agent-task` label. Successor issues:

- Carry `parent_issue` set to the originating issue's number.
- Carry `depends_on_prs` listing PR numbers that must be merged
  before the successor begins.
- Are never given `status: "working"` at creation — successors are
  unclaimed by definition. Any qualifying agent (including this one
  later) may claim them.

## Self-install logic

On first invocation in a target repo, the skill checks for each of
the following files and installs anything missing from this skill's
`templates/` directory. Skills are idempotent — re-running the
install on an already-installed repo is a no-op.

This skill's template inventory is the **superset of `batch-job`'s
templates plus the DAG-orchestration extras**:

| File or path (in target repo) | Source in this skill |
|---|---|
| `.agent/config.json` | `templates/agent/config.json` |
| `.agent/scripts/common.py` | `templates/agent/scripts/common.py` |
| `.agent/scripts/rest_client.py` | `templates/agent/scripts/rest_client.py` |
| `.agent/scripts/handler.py` | `templates/agent/scripts/handler.py` |
| `.agent/scripts/requirements.txt` | `templates/agent/scripts/requirements.txt` |
| `.agent/scripts/lock_and_sweep.py` | `templates/agent/scripts/lock_and_sweep.py` |
| `.agent/scripts/close_on_merge.py` | `templates/agent/scripts/close_on_merge.py` |
| `.agent/scripts/agent_lib/__init__.py` | `templates/agent/scripts/agent_lib/__init__.py` |
| `.agent/scripts/agent_lib/__main__.py` | `templates/agent/scripts/agent_lib/__main__.py` |
| `.agent/scripts/agent_lib/_common_loader.py` | `templates/agent/scripts/agent_lib/_common_loader.py` |
| `.agent/scripts/agent_lib/cli.py` | `templates/agent/scripts/agent_lib/cli.py` |
| `.agent/scripts/agent_lib/envelope.py` | `templates/agent/scripts/agent_lib/envelope.py` |
| `.agent/scripts/agent_lib/meta.py` | `templates/agent/scripts/agent_lib/meta.py` |
| `.agent/scripts/agent_lib/poll.py` | `templates/agent/scripts/agent_lib/poll.py` |
| `.agent/schemas/comment-envelope.schema.json` | `templates/agent/schemas/comment-envelope.schema.json` |
| `.agent/schemas/comment-ack-envelope.schema.json` | `templates/agent/schemas/comment-ack-envelope.schema.json` |
| `.agent/schemas/log-manifest.schema.json` | `templates/agent/schemas/log-manifest.schema.json` |
| `.agent/schemas/issue-body.schema.json` | `templates/agent/schemas/issue-body.schema.json` |
| `.agent/schemas/commands/bad-summary.schema.json` | `templates/agent/schemas/commands/bad-summary.schema.json` |
| `.agent/schemas/commands/build.schema.json` | `templates/agent/schemas/commands/build.schema.json` |
| `.agent/schemas/commands/chatty.schema.json` | `templates/agent/schemas/commands/chatty.schema.json` |
| `.agent/schemas/commands/echo.schema.json` | `templates/agent/schemas/commands/echo.schema.json` |
| `.agent/schemas/commands/run-tests.schema.json` | `templates/agent/schemas/commands/run-tests.schema.json` |
| `.agent/commands/__init__.py` | `templates/agent/commands/__init__.py` |
| `.agent/commands/bad_summary.py` | `templates/agent/commands/bad_summary.py` |
| `.agent/commands/build.py` | `templates/agent/commands/build.py` |
| `.agent/commands/chatty.py` | `templates/agent/commands/chatty.py` |
| `.agent/commands/echo.py` | `templates/agent/commands/echo.py` |
| `.agent/commands/run_tests.py` | `templates/agent/commands/run_tests.py` |
| `.github/workflows/batch-job-handler.yml` | `templates/github/workflows/batch-job-handler.yml` |
| `.github/workflows/lock-and-sweep.yml` | `templates/github/workflows/lock-and-sweep.yml` |
| `.github/workflows/close-on-merge.yml` | `templates/github/workflows/close-on-merge.yml` |
| `_agent_runs` orphan branch | Created empty if missing (see below) |

### Install procedure

For each path above:

1. If the target file is absent, write the bundled template via
   `mcp__github__create_or_update_file`.
2. If the target file is present and byte-identical to the bundled
   template, no-op.
3. If the target file is present but content differs, diff against
   the bundled template and ask the user: overwrite, skip, or write
   to `<path>.new` for manual merge. Record the user's choice in
   `.agent/installs/task-dag.log`.

The skill considers the protocol "installed" once `.agent/config.json`
exists. The install marker is checked on every invocation.

### `_agent_runs` orphan branch

The batch-job-handler writes log manifests, chunks, and `summary.json`
to a dedicated branch named `_agent_runs`. The branch holds no source
tree — it is an audit log only. The skill creates this branch if
missing as part of its self-install sequence:

1. Use `mcp__github__list_branches` to check whether `_agent_runs`
   exists.
2. If absent, use `mcp__github__create_branch` from the repo's empty
   tree (an initial commit on an orphan branch). Some MCP servers do
   not expose orphan-branch creation directly — in that case, fall
   back to a Bash invocation in a clean checkout:

   ```bash
   git checkout --orphan _agent_runs
   git rm -rf .
   git commit --allow-empty -m "Initialize _agent_runs audit branch"
   git push origin _agent_runs
   ```

3. If the branch already exists but its tree is non-empty and the
   contents look like a regular source branch, **refuse to overwrite**;
   surface to the user with a clear message naming the conflicting
   files and the suspected accidental push.

The branch must exist before any batch-job-handler workflow can write
logs. The skill creates it once and never touches it again.

### Composition with `batch-job`

If `batch-job`'s templates are already present (it was installed
first), all overlapping files no-op. If `task-dag` installs first,
later invocation of `batch-job` finds them present and no-ops. The
two skills share the same template surface for their overlap; the
contract test asserts byte-equivalence across the shared paths.

### Onboarding hint

When `task-dag` self-installs into a repo whose
`agent-job-protocol/onboarding` branch is absent, it emits a one-time
message:

> Protocol installed. Onboarding has not been run in this repo. Run
> `/onboarding` for guided integration with your existing workflow,
> or skip — the skills work standalone.

The hint is recorded in `.agent/installs/task-dag.log` so it appears
only once per session.

## Crash recovery

A new agent process invoking `claim` will discover stale issues
(those whose `status_ts` is older than `issue.stale_seconds`) and
adopt them via the same handshake used for fresh claims. After
takeover the agent:

1. Reads the issue body and all comments.
2. Classifies each comment as in-flight (`run_status` non-terminal),
   terminal-unacked (`run_status` terminal, `agent_ack` null), or
   terminal-acked.
3. For terminal-unacked, reads the summary, integrates the outcome,
   then acks via the `batch-job` skill.
4. For in-flight, waits for terminal status subject to the runner-
   pickup and running deadlines; converts to abandoned if those
   deadlines have already elapsed.
5. If subagent branches exist but the feature-branch merge is
   partial, restarts from `merge_subagent_branches` (the implementation
   is idempotent — already-merged branches are skipped).

All recovery state lives on GitHub. No local agent state is required
for resumption; an empty workspace is sufficient. See POC `SPEC.md`
§10.4 for the canonical recovery contract.

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| No candidate issues | Empty list after filtering | Return `None`; caller decides next action |
| Claim race lost | Re-read shows different `agent_id` | Self-abandon silently; return `None` |
| Stale takeover collides | Two successors both wrote `agent_id` | Loser self-abandons on re-read |
| Instructions resolution fails | `instructions_path` returns 404 | Raise `InstructionsNotFoundError` to caller |
| Merge conflict | `git merge` returns non-zero | Apply `conflict_strategy`; surface to caller when `fail` |
| `_agent_runs` exists with non-audit content | `list_branches` + tree check | Refuse to overwrite; surface to user |
| Successor creation hits rate limit | MCP returns 403/429 | Retry with exponential backoff |
| Heartbeat finds `agent_id` mismatch | Re-read inside `heartbeat()` | Self-abandon; raise `LostOwnershipError` to the polling loop |
| Missing `agent-meta` in body | Parse fails after fetch | Treat as a non-protocol issue; skip during claim, raise during `plan` |

## Anti-patterns

- **Do not** lock issues at creation. `lock_and_sweep` applies the
  `agent-task` label only; locking happens at issue-close in
  `close_on_merge`. Locking earlier breaks the batch-job-handler's
  ability to write terminal envelopes.
- **Do not** use single-slash branch separators for subagent branches
  (`feature/sub-01`). Always double-dash: `feature--sub-01`. Single
  slashes collide with the ref namespace because the parent ref
  becomes a directory the moment a child ref exists.
- **Do not** merge in completion order. Always plan order. The plan
  is the source of truth for cross-subagent dependencies.
- **Do not** create successor issues with `status` set to anything
  other than `null`. Successors are unclaimed by definition; any
  qualifying agent may pick them up.
- **Do not** invoke the `batch-job` skill via the Skill tool from
  inside `task-dag`. Call into the Python helpers under
  `.agent/scripts/agent_lib/` instead. Cross-skill Skill-tool
  invocation is not supported in v1 (too easy to recurse).
- **Do not** rewrite the issue body after losing the claim race. The
  losing agent's only correct action is to walk away silently.

## Dependencies

- None at the skill level. Self-installs on first invocation.
- At runtime: a GitHub MCP server and a writable `_agent_runs`
  branch. Both are bootstrapped by the install procedure above.
- Composable with `batch-job` — `orchestrate-issue` wires them
  together; users can also wire them manually following the
  `composition-guide` skill.

---
Version: 1.0.0
Protocol-version: 1
Last-synced-from-POC: 2026-05-14
---

````

### docs/skills/task-dag/SPEC.md

````text
# SPEC — task-dag skill

Status: design-stage
Audience: implementers of the skill in the new `pipeline-ai-sandbox` repo

## Purpose

Manage the lifecycle of one agent-task issue as a DAG node:

- **claim** — pick an unclaimed or stale issue and take ownership via CAS-by-re-read
- **plan** — produce a work brief from `instructions_inline` or `instructions_path`
- **merge** — overlay subagent branches onto the feature branch
- **schedule_successors** — open follow-up issues with `status: null`

The skill is the agent-side primitive for issue ownership. It does
**not** dispatch batch jobs (that is `batch-job`) and does **not**
spawn subagents (that is the calling agent's harness-specific job, or
`orchestrate-issue`'s).

## Trigger conditions

The skill matches when an agent is asked to:

- "Claim an issue and start working on it"
- "Find an unclaimed agent-task issue"
- "Plan subagents for issue N"
- "Merge subagent branches into the feature branch"
- "Schedule follow-up issues for this DAG node"
- "Use the task-dag skill"

It does **not** match generic GitHub issue work outside the
agent-job protocol.

## Inputs and outputs

### claim

| Input | Type | Notes |
|---|---|---|
| `agent_id` | string | UUID-recommended; this process's identity |
| `agent_login` | string | The bot account login (sourced via `mcp__github__get_me` if not provided) |
| `candidate_issues` | list[int] | Optional; if omitted, scan open issues with `agent-task` label |

Output: `{issue, meta, agent_id, session_id}` if claimed, else `None`.

### plan

| Input | Type | Notes |
|---|---|---|
| `issue_number` | int | Required |
| `agent_login` | string | Used to filter comments |

Output: `{brief, source, subagent_layout}` where `source` is `inline`
or the resolved `instructions_path`.

### merge_subagent_branches

| Input | Type | Notes |
|---|---|---|
| `feature_branch` | string | Required |
| `subagent_branches` | list[string] | Required, in plan order |
| `conflict_strategy` | enum | `fail` (default), `ours`, `theirs`, `manual` |

Output: `{merged: [...], conflicts: [...], skipped: [...]}`.

### schedule_successors

| Input | Type | Notes |
|---|---|---|
| `successors` | list[dict] | Each dict has `title`, `body`, `depends_on_prs`, `parent_issue` |
| `base_branch` | string | Default branch the successors fork from |

Output: list of created issue numbers.

## Procedure

The procedures map directly onto SPEC §4.1 (state machine), §10 (skill
spec), and §6 (branching model) in the POC. Highlights:

- **Claim handshake**: CAS-by-re-read. Write `agent_id` + `status_ts`.
  Wait 5 seconds. Re-read. If `agent_id` is still ours, claim succeeded;
  otherwise self-abandon quietly.
- **Heartbeat**: `task-dag` exposes a `heartbeat()` helper. It re-reads
  the issue, asserts `agent_id` matches, refreshes `status_ts`.
  Throttled to `heartbeat_min_interval_seconds`.
- **Merge order**: subagent branches merge in **plan order**, not
  completion order. The conflict strategy is configurable but the
  default is `fail` — silent merges hide integration bugs.
- **Successors**: `status: null` issues are created so any qualifying
  agent (this one or a successor) can pick them up later.

## Self-install logic

Same template inventory as `batch-job`, plus:

| File or path | Action if missing |
|---|---|
| `.agent/scripts/lock_and_sweep.py` | Copy from `templates/agent/scripts/` |
| `.agent/scripts/close_on_merge.py` | Copy from `templates/agent/scripts/` |
| `.github/workflows/lock-and-sweep.yml` | Copy from `templates/github/workflows/` |
| `.github/workflows/close-on-merge.yml` | Copy from `templates/github/workflows/` |
| `_agent_runs` orphan branch | Create empty orphan branch if missing |

The `_agent_runs` branch must exist before any batch-job-handler can
write logs. The skill creates it on install via a sequence of
`mcp__github__create_branch` + an initial empty commit.

If templates from `batch-job` are already in place (skill was
installed by `batch-job` earlier), no-op. Skills are idempotent in
their install actions.

## Bundled templates

Superset of `batch-job`'s templates, plus:

```
templates/
  agent/
    scripts/
      lock_and_sweep.py
      close_on_merge.py
  github/
    workflows/
      lock-and-sweep.yml
      close-on-merge.yml
```

Contract-tested for byte-equivalence with the POC source.

## SKILL.md frontmatter

```yaml
---
name: task-dag
description: |
  Manage one agent-task GitHub issue as a DAG node: claim it, plan
  subagents, merge subagent branches, and schedule follow-up issues.
  Self-installs the protocol's workflow + script templates on first
  invocation. Use when an agent is taking ownership of a multi-step
  task represented by a GitHub issue.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__github__issue_read
  - mcp__github__issue_write
  - mcp__github__add_issue_comment
  - mcp__github__create_branch
  - mcp__github__list_issues
  - mcp__github__list_branches
  - mcp__github__create_or_update_file
---
```

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| No candidate issues | Empty list after filtering | Return `None`; caller decides |
| Claim race lost | Re-read shows different `agent_id` | Self-abandon; return `None` |
| Instructions resolution fails | `instructions_path` 404 | Raise `InstructionsNotFoundError` |
| Merge conflict | git returns non-zero | Apply `conflict_strategy`; surface to caller if `fail` |
| `_agent_runs` already exists with conflicting content | Branch listing | Refuse to overwrite; surface to user |
| Successor creation hits rate limit | MCP error | Retry with backoff |

## Tests

### In this POC

- Contract test for template parity.
- Schema validity for any new schemas.
- Dry-run claim against a mock GitHub client; assert handshake works.

### In the new repo

- Reuse the POC's `tests/unit/test_skill_task_dag.py` baseline (claim, plan, merge, schedule_successors).
- Real-GitHub e2e: drive a claim → plan → batch-job → merge → schedule loop against the new repo itself.
- Restart-recovery test: kill the agent mid-claim; verify a new agent picks up correctly per SPEC §10.4.

## Anti-patterns

- **Do not** lock issues at creation. The `lock_and_sweep` template
  intentionally does not lock. Locking is at issue-close only.
- **Do not** use single-slash branch separators (`feature/sub-01`).
  Always double-dash (`feature--sub-01`).
- **Do not** merge in completion order. Always plan order.
- **Do not** create successor issues with `status` set to anything
  other than `null`. Successors are unclaimed by definition.

## Dependencies

- None at skill level. Self-installs.
- At runtime, depends on a GitHub MCP server and a writable
  `_agent_runs` branch (which it creates if missing).
- Composable with `batch-job` — the `orchestrate-issue` skill wires
  them together; users can also wire them manually following
  `composition-guide`.

````

### .claude/skills/task-dag/lib/__init__.py

```text
"""Skill: task-dag — claim, plan, dispatch, merge, schedule successors."""

```

### .claude/skills/task-dag/lib/claim.py

````text
"""``task-dag/claim`` — pick up an unclaimed or stale issue.

Algorithm (§10):
1. Iterate open issues with the ``agent-task`` label.
2. Select one whose ``status`` is ``null``, OR whose ``status`` is
   ``working`` with a ``status_ts`` older than
   ``issue.stale_seconds``.
3. Write our agent-id and timestamp into the agent-meta block.
4. Re-read 5s later (or with a configurable verify delay) to confirm
   ownership.

The in-memory POC verifies immediately (verify_delay defaults to 0).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Optional

try:
    from .common import (
        GitHubClient,
        iso_now,
        load_config,
        new_uuid,
        parse_agent_meta,
        render_agent_meta,
        repo_root,
    )
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_taskdag_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_taskdag_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    iso_now = _mod.iso_now
    load_config = _mod.load_config
    new_uuid = _mod.new_uuid
    parse_agent_meta = _mod.parse_agent_meta
    render_agent_meta = _mod.render_agent_meta
    repo_root = _mod.repo_root


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _is_stale(meta: dict[str, Any], stale_seconds: float) -> bool:
    if meta.get("status") != "working":
        return False
    parsed = _parse_iso(meta.get("status_ts"))
    if parsed is None:
        return True  # missing timestamp counts as stale
    age = (datetime.now(tz=timezone.utc) - parsed).total_seconds()
    return age > stale_seconds


def select_candidate(
    issues: Iterable[dict[str, Any]],
    *,
    agent_task_label: str,
    stale_seconds: float,
) -> Optional[tuple[dict[str, Any], dict[str, Any]]]:
    """Return ``(issue, meta)`` for the first claimable issue."""
    null_first: list[tuple[dict[str, Any], dict[str, Any]]] = []
    stale: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for issue in issues:
        labels = {l["name"] for l in (issue.get("labels") or [])}
        if agent_task_label not in labels:
            continue
        meta = parse_agent_meta(issue.get("body"))
        if meta is None:
            continue
        status = meta.get("status")
        if status is None:
            null_first.append((issue, meta))
        elif _is_stale(meta, stale_seconds):
            stale.append((issue, meta))
    if null_first:
        return null_first[0]
    if stale:
        return stale[0]
    return None


def claim(
    client: GitHubClient,
    *,
    agent_id: Optional[str] = None,
    candidate_issues: Optional[list[dict[str, Any]]] = None,
    config: Optional[dict[str, Any]] = None,
    verify_delay: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Optional[dict[str, Any]]:
    """Claim one issue. Returns ``{issue, meta}`` on success, else None.

    ``candidate_issues`` allows callers to pass a pre-listed set; the
    in-memory client doesn't expose a generic list-issues call.
    """
    cfg = config or load_config(repo_root() / ".agent" / "config.json")
    agent_id = agent_id or new_uuid()
    agent_task_label = cfg.get("labels", {}).get("agent_task", "agent-task")
    stale_seconds = float(cfg.get("issue", {}).get("stale_seconds", 7200))

    if candidate_issues is None:
        # In a real client we'd call an issue-search; the in-memory
        # client only exposes get_issue. Skill callers typically pass
        # the candidate list explicitly.
        candidate_issues = []

    pick = select_candidate(
        candidate_issues,
        agent_task_label=agent_task_label,
        stale_seconds=stale_seconds,
    )
    if pick is None:
        return None

    issue, meta = pick
    number = issue["number"]
    session_id = new_uuid()

    new_meta = dict(meta)
    new_meta["agent_id"] = agent_id
    new_meta["session_id"] = session_id
    new_meta["status"] = "working"
    new_meta["status_ts"] = iso_now()

    new_body = render_agent_meta(new_meta, prose=_extract_prose(issue.get("body") or ""))
    client.update_issue(number, body=new_body)

    if verify_delay > 0:
        sleep(verify_delay)

    fresh = client.get_issue(number)
    fresh_meta = parse_agent_meta(fresh.get("body")) or {}
    if fresh_meta.get("agent_id") != agent_id:
        # We lost the race; abandon quietly.
        return None

    return {
        "issue": fresh,
        "meta": fresh_meta,
        "agent_id": agent_id,
        "session_id": session_id,
    }


def _extract_prose(body: str) -> str:
    """Return everything before the agent-meta fenced block, if any."""
    marker = "```agent-meta"
    idx = body.find(marker)
    if idx == -1:
        return body
    return body[:idx].rstrip()


def heartbeat(
    client: GitHubClient,
    *,
    issue_number: int,
    agent_id: str,
) -> bool:
    """Refresh ``status_ts`` if we still own the issue. Returns True if so."""
    issue = client.get_issue(issue_number)
    meta = parse_agent_meta(issue.get("body")) or {}
    if meta.get("agent_id") != agent_id:
        return False
    meta["status_ts"] = iso_now()
    new_body = render_agent_meta(meta, prose=_extract_prose(issue.get("body") or ""))
    client.update_issue(issue_number, body=new_body)
    return True


def abandon(
    client: GitHubClient,
    issue_number: int,
    reason: str,
) -> dict[str, Any]:
    """Mark an issue as ``abandoned`` (SPEC §4.1, §12).

    Sets ``status="abandoned"`` in the issue's agent-meta and posts a
    comment "Abandoning: <reason>". Returns the updated meta dict.

    Idempotent: if the issue is already abandoned, no second comment is
    posted and the meta is returned unchanged.
    """
    issue = client.get_issue(issue_number)
    meta = parse_agent_meta(issue.get("body")) or {}

    if meta.get("status") == "abandoned":
        return meta

    meta["status"] = "abandoned"
    meta["status_ts"] = iso_now()
    new_body = render_agent_meta(
        meta, prose=_extract_prose(issue.get("body") or "")
    )
    client.update_issue(issue_number, body=new_body)
    client.add_comment(issue_number, f"Abandoning: {reason}")
    return meta

````

### .claude/skills/task-dag/lib/common.py

```text
"""Shared helpers for the ``task-dag`` skill.

Loads the central :mod:`.agent.scripts.common` and re-exports the
symbols the skill scripts need.
"""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _locate_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".agent" / "config.json").exists():
            return parent
    raise RuntimeError("could not locate repo root")


REPO_ROOT = _locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_common():
    name = "agent_protocol_common"
    if name in sys.modules:
        return sys.modules[name]
    spec = spec_from_file_location(
        name,
        REPO_ROOT / ".agent" / "scripts" / "common.py",
    )
    assert spec is not None and spec.loader is not None
    mod = module_from_spec(spec)
    sys.modules[name] = mod  # register before exec so dataclass works
    spec.loader.exec_module(mod)
    return mod


_common = _load_common()

GitHubClient = _common.GitHubClient
InMemoryGitHubClient = _common.InMemoryGitHubClient
iso_now = _common.iso_now
load_config = _common.load_config
parse_agent_meta = _common.parse_agent_meta
render_agent_meta = _common.render_agent_meta
new_uuid = _common.new_uuid
slugify = _common.slugify
is_terminal_run_status = _common.is_terminal_run_status


def repo_root() -> Path:
    return REPO_ROOT


__all__ = [
    "GitHubClient",
    "InMemoryGitHubClient",
    "iso_now",
    "load_config",
    "parse_agent_meta",
    "render_agent_meta",
    "new_uuid",
    "slugify",
    "is_terminal_run_status",
    "repo_root",
]

```

### .claude/skills/task-dag/lib/merge.py

```text
"""``task-dag/merge`` — merge subagent branches into the feature branch.

In v1 we model "merge" as a fast-forward / files-overlay operation
against the in-memory client: each subagent branch's files are
applied on top of the feature branch. A real implementation would
shell out to git; this stub mirrors the spec's intent so tests can
exercise the orchestration logic.

Per SPEC §6 "Merge conflicts are the primary's responsibility": the
primary must have visibility into conflicts. We support three
strategies via ``conflict_strategy``:

- ``"fail"`` (default): raise :class:`MergeConflictError` BEFORE any
  branch is merged when conflicts are detected.
- ``"last-writer-wins"``: apply each subagent overlay in iteration
  order (existing behaviour); record the conflicting paths in
  ``result["conflicts"]``.
- ``"first-writer-wins"``: skip conflicting paths from later subagent
  branches; record the skipped paths in ``result["conflicts"]``.
"""

from __future__ import annotations

from typing import Any, Iterable, Literal, Optional

try:
    from .common import GitHubClient, iso_now
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_taskdag_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_taskdag_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    iso_now = _mod.iso_now


ConflictStrategy = Literal["fail", "last-writer-wins", "first-writer-wins"]


class MergeConflictError(RuntimeError):
    """Raised when conflict_strategy='fail' detects merge conflicts.

    The ``conflicts`` attribute holds the list of conflicting paths so
    callers can inspect / log them before retrying with a different
    strategy.
    """

    def __init__(self, conflicts: list[str]) -> None:
        super().__init__(
            f"merge conflicts on {len(conflicts)} path(s): {sorted(conflicts)}"
        )
        self.conflicts = list(conflicts)


def list_subagent_branches(
    branches: Iterable[str],
    feature_branch: str,
    *,
    pattern: str = "<feature_branch>/sub-",
) -> list[str]:
    prefix = pattern.replace("<feature_branch>", feature_branch)
    return sorted(b for b in branches if b.startswith(prefix))


def _detect_conflicts(
    client: GitHubClient,
    feature_branch: str,
    subagent_branches: list[str],
) -> list[str]:
    """Detect paths that conflict per SPEC §6.

    A path conflicts when:
      - Two or more subagent branches modify it with different content, AND
      - It also exists on the feature branch's pre-merge state with content
        different from at least one of those subagent versions.
    """
    feature_files = _files_at(client, feature_branch)

    # path -> list[bytes] (one entry per subagent branch that has this path)
    per_path_versions: dict[str, list[bytes]] = {}
    for sub in subagent_branches:
        files = _files_at(client, sub)
        if not files:
            continue
        for path, content in files.items():
            per_path_versions.setdefault(path, []).append(content)

    conflicts: list[str] = []
    for path, versions in per_path_versions.items():
        # At least two subagent branches touch this path...
        if len(versions) < 2:
            continue
        # ...with differing content.
        unique = {v for v in versions}
        if len(unique) < 2:
            continue
        # ...AND the feature branch already has the path with content
        # different from at least one of them.
        base = feature_files.get(path)
        if base is None:
            # Path didn't exist pre-merge; multiple subagents creating
            # divergent versions is still a conflict the primary must see.
            conflicts.append(path)
            continue
        if any(v != base for v in versions):
            conflicts.append(path)

    return conflicts


def merge_subagent_branches(
    client: GitHubClient,
    *,
    feature_branch: str,
    subagent_branches: list[str],
    delete_branches: bool = True,
    conflict_strategy: ConflictStrategy = "fail",
) -> dict[str, Any]:
    """Apply each subagent branch's tip files onto the feature branch.

    For the in-memory POC client this is implemented as a full overlay
    via :meth:`InMemoryGitHubClient.commit_files`; with a real client
    you'd open per-branch merge commits via the GitHub API.

    When ``delete_branches`` is True (default), each successfully-merged
    subagent branch is deleted via :meth:`GitHubClient.delete_branch`
    after the merge commit lands. Branches that were skipped (missing
    or empty) are not deleted.

    When ``conflict_strategy="fail"`` (default), conflicts are detected
    BEFORE any merge writes occur, and :class:`MergeConflictError` is
    raised — partial merges are never produced.

    The result dict always includes:
      - ``merged``: per-branch records of successful merges
      - ``skipped``: per-branch records of missing/empty branches
      - ``deleted``: list of subagent branches successfully deleted
      - ``delete_failed``: list of ``{branch, error}`` for failed deletes
      - ``conflicts``: list of conflicting paths (empty when no conflict)
    """
    if conflict_strategy not in ("fail", "last-writer-wins", "first-writer-wins"):
        raise ValueError(f"unknown conflict_strategy: {conflict_strategy!r}")

    conflicts = _detect_conflicts(client, feature_branch, subagent_branches)

    if conflicts and conflict_strategy == "fail":
        # Raise BEFORE any branch is merged.
        raise MergeConflictError(conflicts)

    merged: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    deleted: list[str] = []
    delete_failed: list[dict[str, Any]] = []

    # For first-writer-wins, track which conflicting paths have already
    # been claimed so later branches can skip them.
    conflict_set = set(conflicts)
    claimed_paths: set[str] = set()

    for sub in subagent_branches:
        sub_sha = client.get_branch_head_sha(sub)
        if sub_sha is None:
            skipped.append({"branch": sub, "reason": "missing_or_empty"})
            continue

        # Best-effort: use the in-memory commit_files helper if available.
        commit_files = getattr(client, "commit_files", None)
        if commit_files is None:
            # Real client: we'd POST a merge here. For the POC abstraction
            # we just record the intent.
            merged.append({
                "branch": sub,
                "sub_sha": sub_sha,
                "merged_at": iso_now(),
                "method": "abstract",
            })
        else:
            files = _files_at(client, sub)
            if conflict_strategy == "first-writer-wins" and conflict_set:
                # Drop any conflict path that has already been claimed by
                # an earlier branch in iteration order.
                files = {
                    p: c for p, c in files.items()
                    if not (p in conflict_set and p in claimed_paths)
                }
                # Mark paths this branch IS contributing as claimed.
                for p in list(files.keys()):
                    if p in conflict_set:
                        claimed_paths.add(p)
            new_sha = commit_files(
                feature_branch,
                files,
                f"Merge subagent branch {sub} into {feature_branch}",
            )
            merged.append({
                "branch": sub,
                "sub_sha": sub_sha,
                "merge_sha": new_sha,
                "merged_at": iso_now(),
                "method": "in_memory_overlay",
            })

        # After a successful merge, optionally delete the subagent branch.
        if delete_branches:
            try:
                client.delete_branch(sub)
                deleted.append(sub)
            except Exception as e:  # noqa: BLE001 - best-effort cleanup
                # Branch deletion is best-effort; failures don't roll back
                # an already-recorded merge. Record the failure so the
                # silent swallow becomes observable to callers.
                delete_failed.append({"branch": sub, "error": str(e)})

    return {
        "merged": merged,
        "skipped": skipped,
        "deleted": deleted,
        "delete_failed": delete_failed,
        "conflicts": conflicts,
    }


def _files_at(client: GitHubClient, branch: str) -> dict[str, bytes]:
    """For the in-memory client only: read all files at branch tip."""
    head = client.get_branch_head_sha(branch)
    if head is None:
        return {}
    # Reach into the in-memory commit graph if available.
    commits = getattr(client, "_commits", None)
    if commits is None:
        return {}
    commit = commits.get(head)
    if commit is None:
        return {}
    return dict(commit.files)

```

### .claude/skills/task-dag/lib/plan.py

```text
"""``task-dag/plan`` — load the work brief for a claimed issue.

Reads either ``instructions_inline`` from the agent-meta or fetches
``instructions_path`` via the GitHub client. Returns the brief plus
any pre-declared structure the spec leaves room for in v1.

Also exposes :func:`should_decline` which inspects ``depends_on_prs``
on an issue's agent-meta and reports whether the issue should be
declined (per SPEC §4.1, §12: failed required dependency leads to
``status="abandoned"``).
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

try:
    from .common import GitHubClient, parse_agent_meta
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_taskdag_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_taskdag_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    parse_agent_meta = _mod.parse_agent_meta


class PlanError(RuntimeError):
    """Raised when neither inline nor pathed instructions are available."""


def plan(
    client: GitHubClient,
    *,
    issue_number: int,
    base_branch: Optional[str] = None,
) -> dict[str, Any]:
    """Return ``{brief, source}`` for the issue's instructions."""
    issue = client.get_issue(issue_number)
    meta = parse_agent_meta(issue.get("body"))
    if meta is None:
        raise PlanError(f"issue #{issue_number} has no agent-meta")

    inline = meta.get("instructions_inline")
    path = meta.get("instructions_path")
    base = base_branch or meta.get("base_branch") or "main"

    if inline:
        return {
            "issue_number": issue_number,
            "brief": inline,
            "source": "inline",
            "base_branch": base,
            "feature_branch": meta.get("feature_branch"),
            "depends_on_prs": meta.get("depends_on_prs") or [],
        }

    if path:
        contents = client.get_file_contents(path, base)
        if contents is None:
            raise PlanError(
                f"instructions_path {path!r} not found on {base!r}"
            )
        return {
            "issue_number": issue_number,
            "brief": contents,
            "source": "path",
            "instructions_path": path,
            "base_branch": base,
            "feature_branch": meta.get("feature_branch"),
            "depends_on_prs": meta.get("depends_on_prs") or [],
        }

    raise PlanError(
        f"issue #{issue_number} has neither instructions_inline nor _path"
    )


def should_decline(
    client: GitHubClient,
    issue: dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """Per SPEC §4.1, §12: decide whether to decline (abandon) this issue.

    Inspects ``depends_on_prs`` on the issue's agent-meta. For each listed
    PR number:

    - If the PR is closed-without-merge (``state == "closed"`` and
      ``merged is False``) -> declines with reason
      ``"dependency_failed: PR #<N> closed without merge"``.
    - If the PR cannot be fetched (raises) -> declines with reason
      ``"dependency_missing: PR #<N>"``.

    Returns ``(False, None)`` when no listed PR is in a failure state.
    Returns ``(True, reason)`` on the first failure encountered.
    """
    meta = parse_agent_meta(issue.get("body")) or {}
    depends = meta.get("depends_on_prs") or []
    for n in depends:
        try:
            pr = client.get_pull_request(int(n))
        except Exception:  # noqa: BLE001 - any fetch failure -> dependency missing
            return True, f"dependency_missing: PR #{n}"

        state = pr.get("state")
        merged = bool(pr.get("merged"))
        if state == "closed" and not merged:
            return True, f"dependency_failed: PR #{n} closed without merge"

    return False, None

```

### .claude/skills/task-dag/lib/schedule_successors.py

```text
"""``task-dag/schedule_successors`` — create successor issues with status null.

The protocol expresses dependencies via ``depends_on_prs`` on each
successor's agent-meta block; the actual scheduling is expressed by
opening the issues with ``status: null`` so any qualifying agent can
claim them.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional

try:
    from .common import (
        GitHubClient,
        iso_now,
        new_uuid,
        render_agent_meta,
        slugify,
    )
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_taskdag_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_taskdag_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    iso_now = _mod.iso_now
    new_uuid = _mod.new_uuid
    render_agent_meta = _mod.render_agent_meta
    slugify = _mod.slugify


def schedule_successors(
    client: GitHubClient,
    *,
    successors: list[dict[str, Any]],
    base_branch: str = "main",
    parent_issue: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Open one issue per successor spec.

    Each successor dict has at minimum:

    - ``title`` (string)
    - ``instructions_inline`` OR ``instructions_path`` (string)
    - optional ``depends_on_prs`` (list[int])
    - optional ``feature_branch`` (string; defaults to slug-derived)
    """
    out: list[dict[str, Any]] = []

    # We can't reliably know the next issue number ahead of time; for
    # the in-memory client, ``create_issue`` is a test helper. Real
    # clients would use POST /issues.
    create_issue = getattr(client, "create_issue", None)
    if create_issue is None:
        raise RuntimeError(
            "client lacks create_issue(); a real REST client would POST /issues"
        )

    for spec in successors:
        title = spec["title"]
        slug = spec.get("slug") or slugify(title)
        # Without knowing the issue number yet, derive a placeholder
        # feature branch and tweak after creation.
        feature_branch = spec.get("feature_branch") or f"agent/<n>-{slug}"

        meta = {
            "protocol_version": 1,
            "agent_id": None,
            "session_id": None,
            "status": None,
            "status_ts": None,
            "feature_branch": feature_branch,
            "base_branch": spec.get("base_branch") or base_branch,
            "parent_issue": spec.get("parent_issue", parent_issue),
            "depends_on_prs": list(spec.get("depends_on_prs") or []),
            "instructions_path": spec.get("instructions_path"),
            "instructions_inline": spec.get("instructions_inline"),
            "created_at": iso_now(),
        }

        prose = spec.get("prose") or ""
        body = render_agent_meta(meta, prose=prose)

        issue = create_issue(title=title, body=body)
        # Substitute the real issue number into the feature branch placeholder.
        n = issue["number"]
        if "<n>" in feature_branch:
            meta["feature_branch"] = feature_branch.replace("<n>", str(n))
            new_body = render_agent_meta(meta, prose=prose)
            client.update_issue(n, body=new_body)
            issue = client.get_issue(n)
        out.append(issue)

    return out

```

### .claude/skills/task-dag/templates/agent/commands/__init__.py

```text
"""Command handler modules. Each command is a sibling module exposing
``run(args, log_writer, workspace) -> dict`` returning the summary."""

```

### .claude/skills/task-dag/templates/agent/commands/bad_summary.py

```text
"""``bad-summary`` test command — intentionally returns invalid summary.

Used by harness scenario 07 (``07_summary_schema_violation.md``) to
exercise the handler's defense-in-depth ``summary_schema_violation``
path. The schema demands ``required_field`` in the completed summary,
but this handler returns ``{}`` so the validator must reject it.
"""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": "bad-summary about to return invalid summary",
    })
    # Intentionally missing the schema-required ``required_field``.
    return {}

```

### .claude/skills/task-dag/templates/agent/commands/build.py

```text
"""``build`` command stub. Pretends to build a target."""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    target = args.get("target", "default")
    release = bool(args.get("release", False))

    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "setup",
        "data": {"msg": "build started", "target": target, "release": release},
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": f"compiling {target}{' (release)' if release else ''}",
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "teardown",
        "data": {"msg": "build complete"},
    })

    artifact = f"build/out/{target}{'-release' if release else ''}.bin"
    return {
        "artifact_path": artifact,
        "size_bytes": 1024 * (4096 if release else 2048),
        "duration_seconds": 3.5 if release else 1.25,
    }

```

### .claude/skills/task-dag/templates/agent/commands/chatty.py

```text
"""``chatty`` test command — emits many log records to force chunk rotation.

Used by harness scenario 12 (``12_huge_log.md``). Args:

- ``lines`` (int, default 500): number of log records to emit.
- ``max_chunk_bytes_compressed`` (int, default 8192): rotation threshold
  applied to the LogWriter for this invocation only. The production
  default (524 288 bytes) remains untouched for non-test commands.

Rationale: live execution showed that triggering rotation at the full
production threshold required ~20 000 lines, which is timing-sensitive
and slow on real GitHub Actions runners. Lowering the per-invocation
threshold for the test command makes rotation fire reliably with a
modest line count, while production defaults are preserved because
chatty calls :py:meth:`LogWriter.set_max_chunk_bytes` itself rather
than mutating any shared config.

Each emitted record carries a high-entropy (per-line unique) payload so
that gzip cannot dedupe the stream down below the rotation threshold —
without this, 500 highly-repetitive lines compressed to <8 KB and never
rotated.
"""

from __future__ import annotations

import hashlib
from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ))
    from common import iso_now  # type: ignore[import-not-found]


def _entropy_payload(i: int, length: int = 192) -> str:
    """Build a high-entropy, per-line-unique string of ~``length`` chars.

    gzip compresses repeated text aggressively, so a constant pad would
    let 500 lines compress well below an 8 KiB rotation threshold. We
    derive a chain of SHA-256 hex digests seeded by ``i`` and concatenate
    them — this is effectively incompressible and grows linearly with
    line count.
    """
    out_parts: list[str] = []
    seed = f"chatty-line-{i:08d}".encode("utf-8")
    h = hashlib.sha256(seed).hexdigest()  # 64 hex chars
    out_parts.append(h)
    while sum(len(p) for p in out_parts) < length:
        h = hashlib.sha256(h.encode("utf-8")).hexdigest()
        out_parts.append(h)
    return "-".join(out_parts)[:length]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    # Override the rotation threshold up-front so every record we emit
    # is governed by the test-friendly size.
    max_chunk = int(args.get("max_chunk_bytes_compressed", 8192))
    log_writer.set_max_chunk_bytes(max_chunk)

    n = int(args.get("lines", 500))
    if n < 0:
        n = 0
    for i in range(n):
        log_writer.write({
            "ts": iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": f"line {i:08d} {_entropy_payload(i)}",
        })
    return {
        "lines_emitted": n,
        "message": f"chatty emitted {n} lines",
    }

```

### .claude/skills/task-dag/templates/agent/commands/echo.py

```text
"""``echo`` command: trivial demonstration handler.

Echoes its args back inside the summary. Useful for end-to-end POC
testing without depending on any synthetic test data.
"""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    message = str(args.get("message", "")) or "hello"
    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": message,
    })
    return {
        "echoed_args": dict(args),
        "message": message,
    }

```

### .claude/skills/task-dag/templates/agent/commands/run_tests.py

```text
"""``run-tests`` command stub.

Pretends to run a suite and returns a fake-but-realistic summary that
conforms to ``commands/run-tests.schema.json``'s ``summary_completed``
shape. Streams a few records through ``log_writer`` so the manifest
contains real chunks.
"""

from __future__ import annotations

import random
from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    """Execute the (faked) test command.

    ``args`` is already validated against the command schema by the
    handler, so ``suite`` is guaranteed present.
    """
    suite = args["suite"]
    shard = args.get("shard")
    filter_ = args.get("filter")

    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "setup",
        "data": {
            "msg": "starting run-tests",
            "suite": suite,
            "shard": shard,
            "filter": filter_,
        },
    })

    # Deterministic-ish fake numbers based on suite size.
    base_counts = {"unit": 120, "integration": 40, "e2e": 12}
    total = base_counts.get(suite, 25)
    rng = random.Random(f"{suite}:{shard}:{filter_}")

    failed = rng.randint(0, max(1, total // 25))
    skipped = rng.randint(0, max(1, total // 30))
    passed = total - failed - skipped
    duration = round(rng.uniform(2.0, 12.0) + total * 0.1, 2)

    failed_tests: list[dict[str, str]] = []
    for i in range(failed):
        log_writer.write({
            "ts": iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": f"FAIL test_{suite}_{i}",
        })
        failed_tests.append({
            "name": f"test_{suite}_{i}",
            "message": "AssertionError: synthetic failure",
        })

    log_writer.write({
        "ts": iso_now(),
        "stream": "stdout",
        "phase": "exec",
        "data": f"ran {total} {suite} tests in {duration}s",
    })
    log_writer.write({
        "ts": iso_now(),
        "stream": "meta",
        "phase": "teardown",
        "data": {"msg": "run-tests complete"},
    })

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_seconds": duration,
        "failed_tests": failed_tests,
    }

```

### .claude/skills/task-dag/templates/agent/config.json

```text
{
  "protocol_version": 1,
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
    "subagent_pattern": "<feature_branch>--sub-<subagent_id>"
  },
  "commands": ["run-tests", "build", "echo", "bad-summary", "chatty"]
}

```

### .claude/skills/task-dag/templates/agent/schemas/commands/bad-summary.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/bad-summary.schema.json",
  "title": "bad-summary",
  "description": "Test command whose handler intentionally returns an invalid summary so the handler's summary_schema_violation path is exercised.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "additionalProperties": true
    },
    "summary_completed": {
      "type": "object",
      "required": ["required_field"],
      "properties": {
        "required_field": { "type": "string" }
      },
      "additionalProperties": true
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/task-dag/templates/agent/schemas/commands/build.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/build.schema.json",
  "title": "build",
  "description": "Schema for the build command. Stub for the POC.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "target": { "type": "string", "minLength": 1 },
        "release": { "type": "boolean" }
      },
      "additionalProperties": false
    },
    "summary_completed": {
      "type": "object",
      "required": ["artifact_path", "size_bytes", "duration_seconds"],
      "properties": {
        "artifact_path": { "type": "string" },
        "size_bytes": { "type": "integer", "minimum": 0 },
        "duration_seconds": { "type": "number", "minimum": 0 }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/task-dag/templates/agent/schemas/commands/chatty.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/chatty.schema.json",
  "title": "chatty",
  "description": "Test command that emits many log records to force chunk rotation.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "lines": { "type": "integer", "minimum": 0 },
        "max_chunk_bytes_compressed": { "type": "integer", "minimum": 1 }
      },
      "additionalProperties": false
    },
    "summary_completed": {
      "type": "object",
      "required": ["lines_emitted", "message"],
      "properties": {
        "lines_emitted": { "type": "integer", "minimum": 0 },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/task-dag/templates/agent/schemas/commands/echo.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/echo.schema.json",
  "title": "echo",
  "description": "Schema for the echo command: trivial demonstration command that returns its args.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
  "properties": {
    "args": {
      "type": "object",
      "properties": {
        "message": { "type": "string" }
      },
      "additionalProperties": true
    },
    "summary_completed": {
      "type": "object",
      "required": ["echoed_args", "message"],
      "properties": {
        "echoed_args": { "type": "object" },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/task-dag/templates/agent/schemas/commands/run-tests.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/commands/run-tests.schema.json",
  "title": "run-tests",
  "description": "Schema for the run-tests command: validates args and the produced summary.",
  "type": "object",
  "required": ["args", "summary_completed", "summary_error"],
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
        "duration_seconds": { "type": "number", "minimum": 0 },
        "failed_tests": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name"],
            "properties": {
              "name": { "type": "string" },
              "message": { "type": "string" }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },
    "summary_error": {
      "type": "object",
      "required": ["error_kind", "error_detail"],
      "properties": {
        "error_kind": { "type": "string" },
        "error_detail": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}

```

### .claude/skills/task-dag/templates/agent/schemas/comment-ack-envelope.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/comment-ack-envelope.schema.json",
  "title": "comment envelope (agent-ack)",
  "description": "Follow-up comment that acknowledges a batch-job-request without editing it in place.",
  "type": "object",
  "required": ["protocol_version", "kind", "ack_for", "agent_acked_at"],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "kind": { "type": "string", "const": "agent-ack" },
    "ack_for": { "type": "integer", "minimum": 1 },
    "agent_acked_at": { "type": "string", "format": "date-time" },
    "agent_id": { "type": ["string", "null"] },
    "session_id": { "type": ["string", "null"] },
    "note": { "type": ["string", "null"] }
  },
  "additionalProperties": true
}

```

### .claude/skills/task-dag/templates/agent/schemas/comment-envelope.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/comment-envelope.schema.json",
  "title": "comment envelope (batch-job-request)",
  "description": "Lifecycle-aware schema for comment-body envelopes. Supports request, post-run, and parse_error shapes.",
  "type": "object",
  "required": ["protocol_version", "kind"],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "kind": { "type": "string", "const": "batch-job-request" },
    "command": { "type": "string", "minLength": 1 },
    "args": { "type": "object" },
    "branch": { "type": "string", "minLength": 1 },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{40}$"
    },
    "subagent_id": { "type": "string", "minLength": 1 },
    "submitted_at": { "type": "string", "format": "date-time" },

    "run_status": {
      "type": ["string", "null"],
      "enum": [null, "running", "completed", "error", "parse_error"]
    },
    "run_started_at": { "type": ["string", "null"], "format": "date-time" },
    "run_finished_at": { "type": ["string", "null"], "format": "date-time" },
    "workflow_run_id": { "type": ["integer", "null"] },
    "checked_out_sha": {
      "type": ["string", "null"],
      "pattern": "^[0-9a-f]{40}$"
    },
    "summary": { "type": ["object", "null"] },
    "log_manifest_branch": { "type": ["string", "null"] },
    "log_manifest_path": { "type": ["string", "null"] },

    "agent_ack": {
      "type": ["string", "null"],
      "enum": [null, "finished"]
    },
    "agent_acked_at": { "type": ["string", "null"], "format": "date-time" },

    "error_kind": { "type": ["string", "null"] },
    "error_detail": { "type": ["string", "null"] },
    "original_body_b64": { "type": ["string", "null"] }
  },
  "allOf": [
    {
      "description": "If run_status is null/running/completed/error (i.e. a real request was submitted), the request fields must be present.",
      "if": {
        "properties": {
          "run_status": { "enum": [null, "running", "completed", "error"] }
        }
      },
      "then": {
        "required": ["command", "args", "branch", "commit_sha", "subagent_id", "submitted_at"]
      }
    },
    {
      "description": "If run_status is 'completed', summary and log manifest fields are required.",
      "if": {
        "properties": { "run_status": { "const": "completed" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id",
          "checked_out_sha",
          "summary",
          "log_manifest_branch",
          "log_manifest_path"
        ]
      }
    },
    {
      "description": "If run_status is 'error', error_kind and run timing must be present.",
      "if": {
        "properties": { "run_status": { "const": "error" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id",
          "error_kind"
        ]
      }
    },
    {
      "description": "If run_status is 'parse_error', original_body_b64 and error_kind must be present.",
      "if": {
        "properties": { "run_status": { "const": "parse_error" } },
        "required": ["run_status"]
      },
      "then": {
        "required": [
          "run_status",
          "error_kind",
          "original_body_b64",
          "run_started_at",
          "run_finished_at",
          "workflow_run_id"
        ]
      }
    }
  ],
  "additionalProperties": true
}

```

### .claude/skills/task-dag/templates/agent/schemas/issue-body.schema.json

````text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/issue-body.schema.json",
  "title": "agent-meta block (issue body)",
  "description": "Schema for the JSON object inside an issue body's fenced ```agent-meta block.",
  "type": "object",
  "required": [
    "protocol_version",
    "agent_id",
    "session_id",
    "status",
    "status_ts",
    "feature_branch",
    "base_branch",
    "parent_issue",
    "depends_on_prs",
    "instructions_path",
    "instructions_inline",
    "created_at"
  ],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "agent_id": { "type": ["string", "null"] },
    "session_id": { "type": ["string", "null"] },
    "status": {
      "type": ["string", "null"],
      "enum": [null, "working", "abandoned", "finished"]
    },
    "status_ts": {
      "type": ["string", "null"],
      "format": "date-time"
    },
    "feature_branch": { "type": "string", "minLength": 1 },
    "base_branch": { "type": "string", "minLength": 1 },
    "parent_issue": { "type": ["integer", "null"], "minimum": 1 },
    "depends_on_prs": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 }
    },
    "instructions_path": { "type": ["string", "null"] },
    "instructions_inline": { "type": ["string", "null"] },
    "created_at": { "type": "string", "format": "date-time" }
  },
  "anyOf": [
    { "properties": { "instructions_inline": { "type": "string", "minLength": 1 } }, "required": ["instructions_inline"] },
    { "properties": { "instructions_path": { "type": "string", "minLength": 1 } }, "required": ["instructions_path"] }
  ],
  "additionalProperties": true
}

````

### .claude/skills/task-dag/templates/agent/schemas/log-manifest.schema.json

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/log-manifest.schema.json",
  "title": "log manifest",
  "description": "Schema for runs/<issue>/<comment>/manifest.json on the _agent_runs orphan branch.",
  "type": "object",
  "required": [
    "protocol_version",
    "schema",
    "command",
    "args",
    "checked_out_sha",
    "started_at",
    "finished_at",
    "exit_code",
    "chunks"
  ],
  "properties": {
    "protocol_version": { "type": "integer", "const": 1 },
    "schema": {
      "type": "object",
      "required": ["chunk_format", "fields"],
      "properties": {
        "chunk_format": { "type": "string", "const": "jsonl-gz" },
        "fields": { "type": "object" }
      }
    },
    "command": { "type": "string", "minLength": 1 },
    "args": { "type": "object" },
    "checked_out_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,64}$"
    },
    "started_at": { "type": "string", "format": "date-time" },
    "finished_at": { "type": "string", "format": "date-time" },
    "exit_code": { "type": "integer" },
    "chunks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "bytes", "lines"],
        "properties": {
          "path": { "type": "string", "minLength": 1 },
          "bytes": { "type": "integer", "minimum": 0 },
          "lines": { "type": "integer", "minimum": 0 }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": true
}

```

### .claude/skills/task-dag/templates/agent/scripts/agent_lib/__init__.py

```text
"""Pure-Python helpers for the agent-mode harness.

This package is the agent-side counterpart to the workflow-side handler.

The dispatcher AI cannot pass MCP tools as Python callables, so the
"skill" lifecycle in agent mode is split into:

- Pure helpers (here): envelope construction, agent-meta marshalling,
  terminal-status parsing, summary path derivation, schema validation.
- Markdown playbooks (under ``harness/scenarios/``): tell the agent
  which MCP calls to make and in what order.

Pure helpers run inside the sandbox — invoked via ``python -m agent_lib
<sub> ...``; the printed JSON is consumed by the agent's tool-use
stream.

This module deliberately performs **no** I/O against GitHub.
"""

from __future__ import annotations

from .envelope import (
    EnvelopeArgsInvalid,
    make_ack_envelope,
    make_request_envelope,
)
from .meta import (
    abandon_meta,
    claim_meta,
    finish_meta,
    heartbeat_meta,
    make_initial_meta,
    parse_body,
    render_body,
    replace_meta_in_body,
)
from .poll import (
    is_request_acked,
    is_terminal,
    manifest_path_for,
    parse_ack_comment,
    parse_terminal_status,
    summary_path_for,
)


__all__ = [
    "EnvelopeArgsInvalid",
    "abandon_meta",
    "claim_meta",
    "finish_meta",
    "heartbeat_meta",
    "is_request_acked",
    "is_terminal",
    "make_ack_envelope",
    "make_initial_meta",
    "make_request_envelope",
    "manifest_path_for",
    "parse_ack_comment",
    "parse_body",
    "parse_terminal_status",
    "render_body",
    "replace_meta_in_body",
    "summary_path_for",
]

```

### .claude/skills/task-dag/templates/agent/scripts/agent_lib/__main__.py

```text
"""Make ``python -m agent_lib`` invoke the CLI."""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())

```

### .claude/skills/task-dag/templates/agent/scripts/agent_lib/_common_loader.py

```text
"""Locate and load the central ``common.py`` module by file path.

The agent-mode helpers run from many entry points (CLI, tests,
imported by subagents). We deliberately keep the import shape as
robust as ``skills/batch-job/common.py`` so a stray ``common`` already
in ``sys.modules`` does not break us.
"""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def locate_repo_root(start: Path | None = None) -> Path:
    """Walk upwards from ``start`` looking for ``.agent/config.json``."""
    here = (start or Path(__file__)).resolve()
    candidates = [here] if here.is_dir() else [here.parent, *here.parents]
    for parent in candidates:
        if (parent / ".agent" / "config.json").exists():
            return parent
    raise RuntimeError("could not locate repo root (no .agent/config.json found)")


REPO_ROOT = locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_common() -> ModuleType:
    """Return the central agent-protocol ``common`` module, loaded once."""
    name = "agent_protocol_common"
    if name in sys.modules:
        return sys.modules[name]
    path = REPO_ROOT / ".agent" / "scripts" / "common.py"
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - import path
        raise RuntimeError(f"could not load common module from {path}")
    mod = module_from_spec(spec)
    sys.modules[name] = mod  # register before exec so dataclasses work
    spec.loader.exec_module(mod)
    return mod

```

### .claude/skills/task-dag/templates/agent/scripts/agent_lib/cli.py

```text
"""Thin CLI wrapper around the pure helpers.

Designed to be invoked by the dispatcher agent via ``Bash`` calls of
the form::

    python -m agent_lib <subcommand> <positional args> [--option ...]

All subcommands print JSON to stdout (the parsed structure or the
markdown body) so the agent can pipe the result into a subsequent MCP
call. Validation failures exit with a non-zero status; the error
message goes to stderr as a single ``{"error": "..."}`` JSON object.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional

from . import (
    EnvelopeArgsInvalid,
    abandon_meta,
    claim_meta,
    finish_meta,
    heartbeat_meta,
    make_ack_envelope,
    make_initial_meta,
    make_request_envelope,
    parse_body,
    parse_terminal_status,
    render_body,
    summary_path_for,
)
from ._common_loader import REPO_ROOT, load_common
from .meta import replace_meta_in_body


_common = load_common()


def _die(msg: str, code: int = 1) -> None:
    sys.stderr.write(json.dumps({"error": msg}) + "\n")
    raise SystemExit(code)


def _loads(s: str, *, name: str) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError) as e:
        _die(f"{name}: invalid JSON: {e}")


def _print(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------

def cmd_make_request(ns: argparse.Namespace) -> int:
    args = _loads(ns.args_json, name="args")
    if not isinstance(args, dict):
        _die("args must be a JSON object")
    try:
        env = make_request_envelope(
            ns.command,
            args,
            ns.branch,
            ns.sha,
            ns.subagent_id,
            validate_args=not ns.no_validate,
        )
    except EnvelopeArgsInvalid as e:
        _die(str(e))
    except (TypeError, ValueError) as e:
        _die(str(e))
    _print(env)
    return 0


def cmd_make_ack(ns: argparse.Namespace) -> int:
    try:
        env = make_ack_envelope(
            ns.ack_for,
            agent_id=ns.agent_id,
            session_id=ns.session_id,
            note=ns.note,
        )
    except ValueError as e:
        _die(str(e))
    _print(env)
    return 0


def cmd_make_initial_meta(ns: argparse.Namespace) -> int:
    payload = _loads(ns.json_payload, name="payload")
    if not isinstance(payload, dict):
        _die("payload must be a JSON object")
    try:
        meta = make_initial_meta(**payload)
    except TypeError as e:
        _die(f"unsupported arguments: {e}")
    except ValueError as e:
        _die(str(e))
    body = render_body(meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_claim_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    try:
        new_meta = claim_meta(meta, ns.agent_id, ns.session_id)
    except ValueError as e:
        _die(str(e))
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_heartbeat_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = heartbeat_meta(meta)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_finish_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = finish_meta(meta)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_abandon_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    new_meta = abandon_meta(meta, ns.reason)
    body = render_body(new_meta, prose=ns.prose or "")
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_parse_comment(ns: argparse.Namespace) -> int:
    run_status, parsed = parse_terminal_status(ns.body)
    summary_path: Optional[str] = None
    log_manifest_path: Optional[str] = None
    if run_status is not None:
        log_manifest_path = parsed.get("log_manifest_path")
        if log_manifest_path:
            base = log_manifest_path.rsplit("/", 1)[0]
            summary_path = base + "/summary.json"
    out = {
        "run_status": run_status,
        "summary": parsed.get("summary"),
        "log_manifest_path": log_manifest_path,
        "summary_path": summary_path,
        "envelope": parsed,
    }
    _print(out)
    return 0


def cmd_parse_meta(ns: argparse.Namespace) -> int:
    meta = parse_body(ns.body)
    if meta is None:
        _print(None)
    else:
        _print(meta)
    return 0


def cmd_summary_path(ns: argparse.Namespace) -> int:
    try:
        path = summary_path_for(ns.issue, ns.comment)
    except ValueError as e:
        _die(str(e))
    _print({"summary_path": path})
    return 0


def cmd_replace_meta(ns: argparse.Namespace) -> int:
    meta = _loads(ns.meta_json, name="meta")
    if not isinstance(meta, dict):
        _die("meta must be a JSON object")
    body = replace_meta_in_body(ns.body, meta)
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


def cmd_validate_summary(ns: argparse.Namespace) -> int:
    summary = _loads(ns.summary_json, name="summary")
    try:
        schema = _common.load_schema(
            f"commands/{ns.command}.schema.json", REPO_ROOT
        )
    except FileNotFoundError as e:
        _die(f"no schema for command {ns.command}: {e}")
    key = "summary_completed" if ns.status == "completed" else "summary_error"
    sub = schema.get("properties", {}).get(key)
    if sub is None:
        _die(f"schema has no {key} sub-schema for {ns.command}")
    try:
        _common.validate(summary, sub)
    except Exception as e:  # noqa: BLE001
        _die(f"invalid: {e}")
    _print({"valid": True, "command": ns.command, "status": ns.status})
    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent_lib")
    sub = p.add_subparsers(dest="cmd", required=True)

    # make-request
    s = sub.add_parser("make-request", help="build a batch-job-request envelope")
    s.add_argument("args_json", help="JSON object: command args")
    s.add_argument("--command", required=True)
    s.add_argument("--branch", required=True)
    s.add_argument("--sha", required=True, help="commit_sha (40 hex chars)")
    s.add_argument("--subagent-id", required=True)
    s.add_argument("--no-validate", action="store_true",
                   help="skip args schema validation")
    s.set_defaults(func=cmd_make_request)

    # make-ack
    s = sub.add_parser(
        "make-ack",
        help="build a follow-up agent-ack comment envelope",
    )
    s.add_argument(
        "--ack-for", type=int, dest="ack_for", required=True,
        help="comment_id of the batch-job-request to ack",
    )
    s.add_argument("--agent-id", dest="agent_id", default=None)
    s.add_argument("--session-id", dest="session_id", default=None)
    s.add_argument("--note", default=None)
    s.set_defaults(func=cmd_make_ack)

    # make-initial-meta
    s = sub.add_parser("make-initial-meta",
                       help="build initial agent-meta block + body markdown")
    s.add_argument("json_payload",
                   help="JSON object of kwargs for make_initial_meta")
    s.add_argument("--prose", default="", help="prose to put before block")
    s.set_defaults(func=cmd_make_initial_meta)

    # claim-meta
    s = sub.add_parser("claim-meta",
                       help="produce new body markdown for a claim")
    s.add_argument("meta_json", help="existing meta JSON")
    s.add_argument("--agent-id", required=True)
    s.add_argument("--session-id", required=True)
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_claim_meta)

    # heartbeat-meta
    s = sub.add_parser("heartbeat-meta",
                       help="produce new body markdown with refreshed status_ts")
    s.add_argument("meta_json")
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_heartbeat_meta)

    # finish-meta
    s = sub.add_parser("finish-meta",
                       help="produce new body markdown with status=finished")
    s.add_argument("meta_json")
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_finish_meta)

    # abandon-meta
    s = sub.add_parser("abandon-meta",
                       help="produce new body markdown with status=abandoned")
    s.add_argument("meta_json")
    s.add_argument("--reason", required=True)
    s.add_argument("--prose", default="")
    s.set_defaults(func=cmd_abandon_meta)

    # parse-comment
    s = sub.add_parser("parse-comment",
                       help="extract run_status / summary / paths from comment body")
    s.add_argument("body", help="raw comment body text")
    s.set_defaults(func=cmd_parse_comment)

    # parse-meta
    s = sub.add_parser("parse-meta",
                       help="parse the agent-meta block out of an issue body")
    s.add_argument("body", help="raw issue body markdown")
    s.set_defaults(func=cmd_parse_meta)

    # summary-path
    s = sub.add_parser("summary-path",
                       help="compute the summary.json path for issue/comment")
    s.add_argument("--issue", type=int, required=True)
    s.add_argument("--comment", type=int, required=True)
    s.set_defaults(func=cmd_summary_path)

    # replace-meta
    s = sub.add_parser("replace-meta",
                       help="replace the agent-meta block in an existing body")
    s.add_argument("body")
    s.add_argument("--meta-json", dest="meta_json", required=True)
    s.set_defaults(func=cmd_replace_meta)

    # validate-summary
    s = sub.add_parser("validate-summary",
                       help="validate a summary against the command schema")
    s.add_argument("summary_json")
    s.add_argument("--command", required=True)
    s.add_argument("--status", choices=("completed", "error"), required=True)
    s.set_defaults(func=cmd_validate_summary)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":  # pragma: no cover - dispatched by __main__.py
    raise SystemExit(main())

```

### .claude/skills/task-dag/templates/agent/scripts/agent_lib/envelope.py

```text
"""Envelope construction helpers for the agent harness.

Pure functions that build a ``batch-job-request`` envelope dict and
optionally validate args against the command's args sub-schema.

No I/O is performed: schemas are loaded from disk via
:mod:`agent_protocol_common`, but no network is touched.
"""

from __future__ import annotations

from typing import Any, Optional

from ._common_loader import REPO_ROOT, load_common


_common = load_common()


class EnvelopeArgsInvalid(ValueError):
    """Raised when ``args`` fail to validate against the command schema."""

    def __init__(self, command: str, message: str) -> None:
        super().__init__(f"args invalid for command {command!r}: {message}")
        self.command = command
        self.message = message


def make_request_envelope(
    command: str,
    args: dict[str, Any],
    branch: str,
    commit_sha: str,
    subagent_id: str,
    *,
    validate_args: bool = True,
    submitted_at: Optional[str] = None,
) -> dict[str, Any]:
    """Construct an unsubmitted ``batch-job-request`` envelope.

    Mirrors :func:`skills.batch-job.submit.submit` minus the I/O. When
    ``validate_args`` is True (default), ``args`` is checked against the
    command's ``args`` sub-schema; an ``EnvelopeArgsInvalid`` is raised
    on failure.

    The ``submitted_at`` timestamp is filled with :func:`iso_now` when
    not provided by the caller.
    """
    if not isinstance(command, str) or not command:
        raise ValueError("command must be a non-empty string")
    if not isinstance(args, dict):
        raise TypeError("args must be a dict")
    if not isinstance(branch, str) or not branch:
        raise ValueError("branch must be a non-empty string")
    if not isinstance(commit_sha, str) or not commit_sha:
        raise ValueError("commit_sha must be a non-empty string")
    if not isinstance(subagent_id, str) or not subagent_id:
        raise ValueError("subagent_id must be a non-empty string")

    if validate_args:
        try:
            schema = _common.load_schema(
                f"commands/{command}.schema.json", REPO_ROOT
            )
        except FileNotFoundError as e:
            raise EnvelopeArgsInvalid(command, f"no schema file: {e}") from e
        args_schema = schema.get("properties", {}).get("args")
        if args_schema is not None:
            try:
                _common.validate(args, args_schema)
            except Exception as e:  # noqa: BLE001 - rewrap
                raise EnvelopeArgsInvalid(command, str(e)) from e

    return {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "command": command,
        "args": dict(args),
        "branch": branch,
        "commit_sha": commit_sha,
        "subagent_id": subagent_id,
        "submitted_at": submitted_at or _common.iso_now(),
        "run_status": None,
        "agent_ack": None,
    }


def make_ack_envelope(
    ack_for: int,
    *,
    agent_acked_at: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    note: Optional[str] = None,
) -> dict[str, Any]:
    """Construct an agent-ack follow-up comment envelope.

    ``ack_for`` is the comment_id of the original batch-job-request whose
    terminal envelope this comment acknowledges (SPEC §5.2). The
    handler treats agent-ack comments as informational; the
    working->finished gate (SPEC §4.1) accepts EITHER an in-place
    ``agent_ack: finished`` on the request comment OR a follow-up
    ``kind: agent-ack`` comment with ``ack_for`` matching the request.
    """
    if not isinstance(ack_for, int) or isinstance(ack_for, bool) or ack_for < 1:
        raise ValueError("ack_for must be a positive integer (comment_id)")
    env: dict[str, Any] = {
        "protocol_version": 1,
        "kind": "agent-ack",
        "ack_for": ack_for,
        "agent_acked_at": agent_acked_at or _common.iso_now(),
    }
    if agent_id is not None:
        env["agent_id"] = agent_id
    if session_id is not None:
        env["session_id"] = session_id
    if note is not None:
        env["note"] = note
    return env


__all__ = ["EnvelopeArgsInvalid", "make_request_envelope", "make_ack_envelope"]

```

### .claude/skills/task-dag/templates/agent/scripts/agent_lib/meta.py

````text
"""Pure helpers that produce / mutate ``agent-meta`` blocks.

Each function takes either a meta dict (for transformations) or kwargs
(for ``make_initial_meta``) and returns either a new dict or the
markdown body string ready to be sent to ``mcp__github__issue_write``
as the ``body`` field.

No GitHub I/O is performed.
"""

from __future__ import annotations

from typing import Any, Optional

from ._common_loader import load_common


_common = load_common()


def _extract_prose(body: Optional[str]) -> str:
    """Return everything before the agent-meta fenced block, if any."""
    if not body:
        return ""
    marker = "```agent-meta"
    idx = body.find(marker)
    if idx == -1:
        return body
    return body[:idx].rstrip()


def make_initial_meta(
    *,
    feature_branch: str,
    base_branch: str = "main",
    instructions_inline: Optional[str] = None,
    instructions_path: Optional[str] = None,
    parent_issue: Optional[int] = None,
    depends_on_prs: Optional[list[int]] = None,
    protocol_version: int = 1,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a fresh agent-meta dict with ``status=None``.

    Either ``instructions_inline`` or ``instructions_path`` must be
    provided (matching the schema's ``anyOf``).
    """
    if not feature_branch:
        raise ValueError("feature_branch is required")
    if not instructions_inline and not instructions_path:
        raise ValueError(
            "either instructions_inline or instructions_path must be set"
        )
    meta = {
        "protocol_version": protocol_version,
        "agent_id": None,
        "session_id": None,
        "status": None,
        "status_ts": None,
        "feature_branch": feature_branch,
        "base_branch": base_branch,
        "parent_issue": parent_issue,
        "depends_on_prs": list(depends_on_prs or []),
        "instructions_path": instructions_path,
        "instructions_inline": instructions_inline,
        "created_at": _common.iso_now(),
    }
    if extra:
        for k, v in extra.items():
            meta[k] = v
    return meta


def claim_meta(
    meta: dict[str, Any],
    agent_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Mark the meta as claimed by ``agent_id``/``session_id``.

    Returns a new dict; the input is not mutated.
    """
    if not agent_id:
        raise ValueError("agent_id is required")
    if not session_id:
        raise ValueError("session_id is required")
    new_meta = dict(meta)
    new_meta["agent_id"] = agent_id
    new_meta["session_id"] = session_id
    new_meta["status"] = "working"
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def heartbeat_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Refresh ``status_ts`` to now. Returns a new dict."""
    new_meta = dict(meta)
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def finish_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Mark the meta as ``status="finished"``. Returns a new dict."""
    new_meta = dict(meta)
    new_meta["status"] = "finished"
    new_meta["status_ts"] = _common.iso_now()
    return new_meta


def abandon_meta(meta: dict[str, Any], reason: str) -> dict[str, Any]:
    """Mark the meta as ``abandoned`` with a recorded reason.

    The ``reason`` is stored under the ``abandon_reason`` key (additional
    properties are allowed by the issue-body schema).
    """
    new_meta = dict(meta)
    new_meta["status"] = "abandoned"
    new_meta["status_ts"] = _common.iso_now()
    new_meta["abandon_reason"] = reason
    return new_meta


def render_body(meta: dict[str, Any], prose: str = "") -> str:
    """Convenience: render an issue body with the given meta."""
    return _common.render_agent_meta(meta, prose=prose)


def parse_body(body: Optional[str]) -> Optional[dict[str, Any]]:
    """Convenience: parse an agent-meta block out of a body."""
    return _common.parse_agent_meta(body)


def replace_meta_in_body(
    body: Optional[str],
    new_meta: dict[str, Any],
) -> str:
    """Replace the agent-meta block in ``body`` with ``new_meta``.

    The prose before the block is preserved; if there was no block, the
    new meta is appended.
    """
    prose = _extract_prose(body)
    return _common.render_agent_meta(new_meta, prose=prose)


__all__ = [
    "make_initial_meta",
    "claim_meta",
    "heartbeat_meta",
    "finish_meta",
    "abandon_meta",
    "render_body",
    "parse_body",
    "replace_meta_in_body",
]

````

### .claude/skills/task-dag/templates/agent/scripts/agent_lib/poll.py

```text
"""Helpers for parsing terminal-status comments.

Polling itself is performed by the agent via repeated MCP calls; the
helpers here just classify a comment body and tell the agent what
``summary.json`` path to read once the comment has reached a terminal
state.
"""

from __future__ import annotations

import html
import json
from typing import Any, Optional

from ._common_loader import load_common


_common = load_common()


_TERMINAL_STATUSES = {"completed", "error", "parse_error"}


def parse_terminal_status(
    envelope_json: str,
) -> tuple[Optional[str], dict[str, Any]]:
    """Classify a comment body.

    Returns a tuple ``(run_status, parsed)``:
      - On JSON parse failure: returns ``(None, {})``.
      - On non-terminal envelope (run_status=None or "running"): returns
        ``(None, parsed)``.
      - On terminal envelope: returns ``(run_status, parsed)``.

    The caller is expected to use the parsed envelope to look up the
    summary path via :func:`summary_path_for` when terminal.
    """
    if not isinstance(envelope_json, str):
        raise TypeError("envelope_json must be a string")
    # MCP returns comment bodies HTML-escaped (&#34; for ", etc.) and
    # Claude Code's GitHub MCP additionally appends a trailer line like
    # ``\n---\n_Generated by [Claude Code](https://claude.ai/code)_`` to
    # every posted comment. We unescape (no-op on REST content) and then
    # use raw_decode to parse the longest JSON-object prefix at the
    # start of the body, tolerating any trailing prose.
    unescaped = html.unescape(envelope_json).lstrip()
    if not unescaped:
        return None, {}
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(unescaped)
    except (json.JSONDecodeError, ValueError):
        return None, {}
    if not isinstance(parsed, dict):
        return None, {}
    status = parsed.get("run_status")
    if status in _TERMINAL_STATUSES:
        return status, parsed
    return None, parsed


def summary_path_for(issue_number: int, comment_id: int) -> str:
    """Return the ``summary.json`` path under the ``_agent_runs`` branch."""
    if not isinstance(issue_number, int) or issue_number < 1:
        raise ValueError("issue_number must be a positive integer")
    if not isinstance(comment_id, int) or comment_id < 1:
        raise ValueError("comment_id must be a positive integer")
    return f"runs/{issue_number}/{comment_id}/summary.json"


def manifest_path_for(issue_number: int, comment_id: int) -> str:
    """Return the ``manifest.json`` path under the ``_agent_runs`` branch."""
    return f"runs/{issue_number}/{comment_id}/manifest.json"


def is_terminal(envelope: dict[str, Any]) -> bool:
    """True if the envelope's ``run_status`` is terminal."""
    return _common.is_terminal_run_status(envelope.get("run_status"))


def parse_ack_comment(body: str) -> Optional[dict[str, Any]]:
    """If body is an agent-ack envelope, return parsed dict; else None.

    Tolerates HTML-escaped bodies and trailing prose (matching the
    parse_terminal_status conventions).
    """
    if not isinstance(body, str):
        return None
    unescaped = html.unescape(body).lstrip()
    if not unescaped:
        return None
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(unescaped)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    if parsed.get("protocol_version") != 1 or parsed.get("kind") != "agent-ack":
        return None
    return parsed


def is_request_acked(
    request_envelope: dict[str, Any],
    request_comment_id: int,
    other_comment_bodies: list[str],
) -> bool:
    """Return True if the request is acked via either form (SPEC §4.1).

    EITHER ``request_envelope["agent_ack"] == "finished"`` (in-place form)
    OR there is at least one comment in ``other_comment_bodies`` that is
    a valid ``kind: agent-ack`` envelope with ``ack_for == request_comment_id``.
    """
    if request_envelope.get("agent_ack") == "finished":
        return True
    for body in other_comment_bodies:
        ack = parse_ack_comment(body)
        if ack and ack.get("ack_for") == request_comment_id:
            return True
    return False


__all__ = [
    "parse_terminal_status",
    "summary_path_for",
    "manifest_path_for",
    "is_terminal",
    "parse_ack_comment",
    "is_request_acked",
]

```

### .claude/skills/task-dag/templates/agent/scripts/close_on_merge.py

```text
"""``close-on-merge`` script (§7.3).

Triggered on merged PRs. Reads the PR body for ``Closes #N``, verifies
the linked issue is in ``status: finished``, then closes the issue,
comments the merge SHA, and locks the issue. Locking happens here
(after the close + final comment) rather than at issue creation,
because GitHub refuses comments from ``GITHUB_TOKEN`` on locked
issues — locking earlier would prevent the batch-job-handler workflow
from writing its terminal envelope. Once the issue is closed and
finalised the lock acts as a tamper-prevention seal on the audit
record.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any, Optional

if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        iso_now,
        load_config,
        parse_agent_meta,
    )
else:
    from .common import GitHubClient, iso_now, load_config, parse_agent_meta


_CLOSES_RE = re.compile(
    r"\b(?:closes|closed|close|fixes|fixed|fix|resolves|resolved|resolve)\s+#(\d+)\b",
    re.IGNORECASE,
)


# Branches that must NEVER be deleted by close_on_merge, regardless of
# how the PR head ref or any sub-* match looks. ``main`` is the default
# branch; ``_agent_runs`` is the orphan audit-trail branch (SPEC §6).
_PROTECTED_BRANCHES = frozenset({"main", "_agent_runs"})


def parse_closes_refs(body: Optional[str]) -> list[int]:
    """Return list of issue numbers the PR claims to close."""
    if not body:
        return []
    return [int(m.group(1)) for m in _CLOSES_RE.finditer(body)]


def _safe_to_delete(name: Optional[str]) -> bool:
    """Return True if it's safe to delete this branch.

    Defensive: only branches that start with ``agent/`` are eligible —
    so even if a PR head somehow points at ``main`` or any other
    non-agent branch, we leave it alone.
    """
    if not name:
        return False
    if name in _PROTECTED_BRANCHES:
        return False
    if not name.startswith("agent/"):
        return False
    return True


def _delete_feature_and_subagent_branches(
    client: GitHubClient,
    feature_branch: Optional[str],
) -> list[str]:
    """Delete the feature branch and any ``<feature>--sub-*`` branches.

    Each deletion is wrapped in try/except so a missing or already-deleted
    branch (or any transient REST error) does not fail the workflow. The
    surviving deletions are still applied. Returns the names of branches
    we *attempted to* and successfully deleted (best-effort: the in-memory
    client is fully idempotent; the REST client treats 404 as success).
    """
    if not feature_branch:
        return []
    targets: list[str] = []
    if _safe_to_delete(feature_branch):
        targets.append(feature_branch)
    # Discover subagent branches under the feature.
    sub_prefix = f"{feature_branch}--sub-"
    try:
        branches = client.list_branches()
    except Exception:  # noqa: BLE001
        branches = []
    for b in branches:
        name = b.get("name") if isinstance(b, dict) else None
        if not name or name == feature_branch:
            continue
        if name.startswith(sub_prefix) and _safe_to_delete(name):
            targets.append(name)

    deleted: list[str] = []
    for name in targets:
        try:
            client.delete_branch(name)
            deleted.append(name)
        except Exception:  # noqa: BLE001
            # Swallow: missing/already-deleted branches must not fail the
            # workflow. Other deletions in the batch should still proceed.
            continue
    return deleted


def run(
    client: GitHubClient,
    pr_number: int,
    *,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Close issues referenced by a merged PR. Returns a result dict."""
    cfg = config or load_config()

    pr = client.get_pull_request(pr_number)
    if not pr.get("merged"):
        return {"action": "noop", "reason": "pr_not_merged"}

    head_ref = (pr.get("head") or {}).get("ref") if isinstance(pr.get("head"), dict) else None

    refs = parse_closes_refs(pr.get("body"))
    if not refs:
        deleted_branches = _delete_feature_and_subagent_branches(client, head_ref)
        return {
            "action": "noop",
            "reason": "no_closes_refs",
            "deleted_branches": deleted_branches,
        }

    closed: list[int] = []
    skipped: list[dict[str, Any]] = []

    for issue_number in refs:
        try:
            issue = client.get_issue(issue_number)
        except KeyError:
            skipped.append({"issue": issue_number, "reason": "missing"})
            continue

        meta = parse_agent_meta(issue.get("body"))
        if meta is None:
            skipped.append({"issue": issue_number, "reason": "no_agent_meta"})
            continue

        if meta.get("status") != "finished":
            skipped.append({
                "issue": issue_number,
                "reason": "not_finished",
                "status": meta.get("status"),
            })
            continue

        if issue.get("state") != "closed":
            client.update_issue(issue_number, state="closed")

        msg = (
            f"Issue closed by merge of #{pr_number} "
            f"(merge_sha={pr.get('merge_commit_sha')}). "
            f"Closed at {iso_now()}."
        )
        client.add_comment(issue_number, msg)
        # Lock the issue post-close as a tamper-prevention seal on the
        # audit record. We could not lock earlier without blocking the
        # batch-job-handler from writing terminal envelopes (GITHUB_TOKEN
        # cannot comment on locked issues).
        if not issue.get("locked"):
            client.lock_issue(issue_number)
        closed.append(issue_number)

    deleted_branches = _delete_feature_and_subagent_branches(client, head_ref)

    return {
        "action": "closed",
        "issues_closed": closed,
        "skipped": skipped,
        "deleted_branches": deleted_branches,
    }


def main() -> int:
    """``close-on-merge`` workflow entry point.

    Required environment variables:
      - ``PR_NUMBER``          the merged pull request number
      - ``GH_TOKEN`` / ``GITHUB_TOKEN``  REST API token
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug

    On success exits 0; on uncaught exception prints to stderr and
    exits 1. Tests call :func:`run` directly with an in-memory client.
    """
    required = ["PR_NUMBER", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    print(
        "close_on_merge: required env vars: " + ", ".join(required) + ".",
        file=sys.stderr,
    )
    pr_number = os.environ.get("PR_NUMBER")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    missing = [
        name for name, val in (
            ("PR_NUMBER", pr_number),
            ("GITHUB_TOKEN", token),
            ("GITHUB_REPOSITORY", repo_slug),
        ) if not val
    ]
    if missing:
        print(f"close_on_merge: missing env vars: {missing}", file=sys.stderr)
        return 1
    assert pr_number is not None and token is not None and repo_slug is not None
    if "/" not in repo_slug:
        print(
            f"close_on_merge: GITHUB_REPOSITORY must be 'owner/repo', got: {repo_slug!r}",
            file=sys.stderr,
        )
        return 1
    owner, repo = repo_slug.split("/", 1)
    print(
        f"close_on_merge: handling PR #{pr_number}",
        file=sys.stderr,
    )
    try:
        if __package__ in (None, ""):
            from rest_client import RestGitHubClient  # type: ignore[import-not-found]
        else:
            from .rest_client import RestGitHubClient
        client = RestGitHubClient(token=token, owner=owner, repo=repo)
        run(client, int(pr_number))
    except Exception as exc:  # noqa: BLE001
        import traceback as _tb
        print(f"close_on_merge: uncaught exception: {exc!r}", file=sys.stderr)
        _tb.print_exc()
        # Self-diagnostic: post a debug comment. Prefer the issue named in
        # ``Closes #N`` (best-effort PR body fetch); otherwise fall back
        # to the PR itself, since PRs are issues to GitHub's REST API.
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                if __package__ in (None, ""):
                    from handler import _post_debug_comment  # type: ignore[import-not-found]
                else:
                    from .handler import _post_debug_comment
                target_issue = int(pr_number)
                try:
                    import requests as _requests
                    pr_resp = _requests.get(
                        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                        timeout=15,
                    )
                    if pr_resp.status_code < 300:
                        refs = parse_closes_refs((pr_resp.json() or {}).get("body"))
                        if refs:
                            target_issue = refs[0]
                except Exception:  # noqa: BLE001
                    pass  # fall back to PR
                _post_debug_comment(
                    token=token,
                    owner=owner,
                    repo=repo,
                    issue_number=target_issue,
                    script="close_on_merge.py",
                    exc=exc,
                    extra_fields={"pr": pr_number},
                )
            except Exception as diag_exc:  # noqa: BLE001
                print(
                    f"close_on_merge: failed to post debug comment: {diag_exc!r}",
                    file=sys.stderr,
                )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### .claude/skills/task-dag/templates/agent/scripts/common.py

````text
"""Common helpers for the agent protocol POC.

Provides:
- ``GitHubClient`` Protocol/abstract definition of the operations the
  scripts need.
- ``InMemoryGitHubClient`` — fully working in-memory implementation
  used in tests and for local POC demonstrations.
- Envelope/agent-meta helpers (parse, render).
- ``LogWriter`` — a JSONL/gzip log writer that rotates by compressed
  size and produces a manifest.
- ``load_config`` and ``validate`` JSON-schema helpers.

The real GitHub REST integration is intentionally **not** implemented
here; for the POC we exercise behaviour through the in-memory client.
"""

from __future__ import annotations

import base64
import gzip
import html
import io
import json
import os
import re
import secrets
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Optional,
    Protocol,
    runtime_checkable,
)

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - jsonschema is in requirements
    Draft202012Validator = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Time and config helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    """Return the current UTC time as an ISO-8601 string with ``Z`` suffix."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config(path: str | os.PathLike[str] = ".agent/config.json") -> dict[str, Any]:
    """Load the central agent configuration JSON file."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(json_obj: Any, schema_obj: dict[str, Any]) -> None:
    """Validate a JSON object against a JSON schema (Draft 2020-12).

    Raises ``jsonschema.ValidationError`` on the first error encountered.
    """
    if Draft202012Validator is None:  # pragma: no cover
        raise RuntimeError("jsonschema is not installed; cannot validate")
    validator = Draft202012Validator(schema_obj)
    errors = sorted(validator.iter_errors(json_obj), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.absolute_path) or "<root>"
        raise ValueError(f"schema validation failed at {path}: {first.message}")


# ---------------------------------------------------------------------------
# agent-meta block parsing / rendering
# ---------------------------------------------------------------------------

_AGENT_META_RE = re.compile(
    r"```agent-meta\s*\n(?P<json>.*?)\n```",
    re.DOTALL,
)


def parse_agent_meta(body: Optional[str]) -> Optional[dict[str, Any]]:
    """Extract the JSON object inside the fenced ``agent-meta`` block.

    Returns ``None`` when:
    - the body is ``None`` or empty, OR
    - no ``agent-meta`` fenced block is present, OR
    - the block exists but its body is not valid JSON.

    The MCP server returns issue bodies with HTML-escaped entities
    (``&#34;`` for ``"``, etc.). We unescape the JSON region before
    parsing so the same parser works against MCP and REST responses.
    Workflow REST responses contain literal quotes so unescape is a
    no-op there.
    """
    if not body:
        return None
    m = _AGENT_META_RE.search(body)
    if not m:
        return None
    raw = html.unescape(m.group("json"))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def render_agent_meta(meta: dict[str, Any], prose: str = "") -> str:
    """Render an issue body markdown with the given ``agent-meta`` block.

    The prose is placed before the fenced block; a blank line separates
    them when both are non-empty.
    """
    block = "```agent-meta\n" + json.dumps(meta, indent=2) + "\n```"
    if prose:
        return f"{prose.rstrip()}\n\n{block}\n"
    return block + "\n"


# ---------------------------------------------------------------------------
# GitHub client abstraction
# ---------------------------------------------------------------------------

@runtime_checkable
class GitHubClient(Protocol):
    """Minimal protocol for the operations the agent scripts need.

    Implementations may use the REST API, an MCP relay, or the
    in-memory mock used for the POC. Errors are raised as exceptions.
    """

    # Issue operations -----------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]: ...
    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]: ...
    def lock_issue(self, number: int) -> None: ...
    def add_label(self, number: int, label: str) -> None: ...
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]: ...

    # Comment operations ---------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]: ...
    def get_comment(self, comment_id: int) -> dict[str, Any]: ...
    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]: ...
    def delete_comment(self, comment_id: int) -> None: ...
    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]: ...

    # File / branch operations --------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]: ...
    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]: ...
    def get_branch_head_sha(self, branch: str) -> Optional[str]: ...
    def delete_branch(self, name: str) -> None: ...
    def list_branches(self) -> list[dict[str, Any]]: ...

    # PR operations --------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]: ...
    def get_pull_request(self, number: int) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# In-memory GitHub client (POC + tests)
# ---------------------------------------------------------------------------

@dataclass
class _Commit:
    sha: str
    parent: Optional[str]
    message: str
    files: dict[str, bytes]  # path -> content


@dataclass
class _Branch:
    name: str
    head_sha: Optional[str]  # None means orphan/uninitialised


@dataclass
class _Comment:
    id: int
    issue_number: int
    user: str
    body: str
    created_at: str
    updated_at: str


@dataclass
class _Issue:
    number: int
    title: str
    body: str
    user: str
    state: str = "open"
    locked: bool = False
    labels: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=iso_now)
    updated_at: str = field(default_factory=iso_now)


@dataclass
class _PullRequest:
    number: int
    title: str
    head: str
    base: str
    body: str
    state: str = "open"
    merged: bool = False
    merge_commit_sha: Optional[str] = None
    user: str = "agent"
    created_at: str = field(default_factory=iso_now)


class InMemoryGitHubClient:
    """In-memory simulation of the subset of GitHub the protocol uses.

    Each call returns dict-shaped data resembling the REST API responses
    so that calling code is portable to a real REST client.
    """

    def __init__(self, default_user: str = "agent") -> None:
        self._lock = threading.RLock()
        self._issues: dict[int, _Issue] = {}
        self._comments: dict[int, _Comment] = {}
        self._comments_by_issue: dict[int, list[int]] = {}
        self._branches: dict[str, _Branch] = {}
        self._commits: dict[str, _Commit] = {}
        self._pulls: dict[int, _PullRequest] = {}
        self._next_issue_number = 1
        self._next_comment_id = 1_000_000
        self._next_pr_number = 5000
        self._default_user = default_user
        self._actor_stack: list[str] = [default_user]

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------
    def as_user(self, login: str) -> "_ActAs":
        """Context manager: switch the effective acting user temporarily."""
        return _ActAs(self, login)

    @property
    def current_user(self) -> str:
        return self._actor_stack[-1]

    def create_issue(
        self,
        title: str,
        body: str,
        user: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Test helper: create a fresh issue in the in-memory state."""
        with self._lock:
            number = self._next_issue_number
            self._next_issue_number += 1
            issue = _Issue(
                number=number,
                title=title,
                body=body,
                user=user or self.current_user,
                labels=list(labels or []),
            )
            self._issues[number] = issue
            self._comments_by_issue[number] = []
            return self._issue_to_dict(issue)

    def create_branch(self, name: str, from_branch: Optional[str] = None) -> str:
        """Create a branch (optionally branching from another). Returns sha."""
        with self._lock:
            if name in self._branches:
                raise ValueError(f"branch already exists: {name}")
            parent_sha: Optional[str] = None
            files: dict[str, bytes] = {}
            if from_branch is not None:
                src = self._branches.get(from_branch)
                if src is None:
                    raise ValueError(f"unknown source branch: {from_branch}")
                parent_sha = src.head_sha
                if parent_sha is not None:
                    files = dict(self._commits[parent_sha].files)
            sha = _new_sha()
            commit = _Commit(
                sha=sha,
                parent=parent_sha,
                message=f"create branch {name}",
                files=files,
            )
            self._commits[sha] = commit
            self._branches[name] = _Branch(name=name, head_sha=sha)
            return sha

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _issue_to_dict(self, issue: _Issue) -> dict[str, Any]:
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "user": {"login": issue.user},
            "state": issue.state,
            "locked": issue.locked,
            "labels": [{"name": n} for n in issue.labels],
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
        }

    def _comment_to_dict(self, c: _Comment) -> dict[str, Any]:
        return {
            "id": c.id,
            "issue_number": c.issue_number,
            "user": {"login": c.user},
            "body": c.body,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }

    # ------------------------------------------------------------------
    # Issue API
    # ------------------------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            return self._issue_to_dict(issue)

    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            if body is not None:
                issue.body = body
            if state is not None:
                if state not in ("open", "closed"):
                    raise ValueError(f"bad state: {state}")
                issue.state = state
            if labels is not None:
                issue.labels = list(labels)
            issue.updated_at = iso_now()
            return self._issue_to_dict(issue)

    def lock_issue(self, number: int) -> None:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            issue.locked = True
            issue.updated_at = iso_now()

    def add_label(self, number: int, label: str) -> None:
        with self._lock:
            issue = self._issues.get(number)
            if issue is None:
                raise KeyError(f"no such issue: {number}")
            if label not in issue.labels:
                issue.labels.append(label)
            issue.updated_at = iso_now()

    # ------------------------------------------------------------------
    # Comment API
    # ------------------------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]:
        with self._lock:
            ids = self._comments_by_issue.get(issue_number, [])
            return [self._comment_to_dict(self._comments[i]) for i in ids]

    def get_comment(self, comment_id: int) -> dict[str, Any]:
        with self._lock:
            c = self._comments.get(comment_id)
            if c is None:
                raise KeyError(f"no such comment: {comment_id}")
            return self._comment_to_dict(c)

    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        with self._lock:
            c = self._comments.get(comment_id)
            if c is None:
                raise KeyError(f"no such comment: {comment_id}")
            c.body = body
            c.updated_at = iso_now()
            return self._comment_to_dict(c)

    def delete_comment(self, comment_id: int) -> None:
        with self._lock:
            c = self._comments.pop(comment_id, None)
            if c is None:
                return
            self._comments_by_issue.get(c.issue_number, []).remove(comment_id)

    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        with self._lock:
            if issue_number not in self._issues:
                raise KeyError(f"no such issue: {issue_number}")
            cid = self._next_comment_id
            self._next_comment_id += 1
            now = iso_now()
            c = _Comment(
                id=cid,
                issue_number=issue_number,
                user=self.current_user,
                body=body,
                created_at=now,
                updated_at=now,
            )
            self._comments[cid] = c
            self._comments_by_issue.setdefault(issue_number, []).append(cid)
            return self._comment_to_dict(c)

    # ------------------------------------------------------------------
    # Files / branches / commits
    # ------------------------------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]:
        with self._lock:
            branch = self._branches.get(ref)
            if branch is None or branch.head_sha is None:
                return None
            commit = self._commits[branch.head_sha]
            data = commit.files.get(path)
            if data is None:
                return None
            # Returned as text (utf-8) or base64 if binary; we always return
            # decoded utf-8 if possible, else b64. Tests typically compare
            # bytes via separate helpers.
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(data).decode("ascii")

    def get_file_bytes(self, path: str, ref: str) -> Optional[bytes]:
        """Test convenience: raw bytes of a file at ref."""
        with self._lock:
            branch = self._branches.get(ref)
            if branch is None or branch.head_sha is None:
                return None
            commit = self._commits[branch.head_sha]
            return commit.files.get(path)

    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                # Auto-create as orphan branch (no parent)
                br = _Branch(name=branch, head_sha=None)
                self._branches[branch] = br
            parent = br.head_sha
            files = dict(self._commits[parent].files) if parent else {}
            files[path] = content_bytes
            sha = _new_sha()
            commit = _Commit(sha=sha, parent=parent, message=message, files=files)
            self._commits[sha] = commit
            br.head_sha = sha
            return {
                "path": path,
                "branch": branch,
                "commit": {"sha": sha, "message": message},
                "size": len(content_bytes),
            }

    def get_branch_head_sha(self, branch: str) -> Optional[str]:
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                return None
            return br.head_sha

    def delete_branch(self, name: str) -> None:
        """Delete a branch ref. Idempotent: missing branches are ignored.

        Note: commits are not garbage-collected from the in-memory store —
        only the branch ref is removed (mirrors GitHub's ref-delete semantics).
        """
        with self._lock:
            self._branches.pop(name, None)

    def list_branches(self) -> list[dict[str, Any]]:
        """List all branches as dicts ``{name, sha, protected}``.

        Mirrors a paginated REST ``GET /repos/{owner}/{repo}/branches``
        response shape. The in-memory client has no notion of branch
        protection, so ``protected`` is always ``False``.
        """
        with self._lock:
            return [
                {"name": b.name, "sha": b.head_sha, "protected": False}
                for b in self._branches.values()
            ]

    def commit_files(
        self,
        branch: str,
        files: dict[str, bytes],
        message: str,
    ) -> str:
        """Test helper: commit multiple files atomically. Returns new sha."""
        with self._lock:
            br = self._branches.get(branch)
            if br is None:
                br = _Branch(name=branch, head_sha=None)
                self._branches[branch] = br
            parent = br.head_sha
            current = dict(self._commits[parent].files) if parent else {}
            current.update(files)
            sha = _new_sha()
            self._commits[sha] = _Commit(
                sha=sha, parent=parent, message=message, files=current
            )
            br.head_sha = sha
            return sha

    # ------------------------------------------------------------------
    # PR API
    # ------------------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]:
        with self._lock:
            if head not in self._branches:
                raise ValueError(f"head branch does not exist: {head}")
            if base not in self._branches:
                raise ValueError(f"base branch does not exist: {base}")
            number = self._next_pr_number
            self._next_pr_number += 1
            pr = _PullRequest(
                number=number,
                title=title,
                head=head,
                base=base,
                body=body,
                user=self.current_user,
            )
            self._pulls[number] = pr
            return self._pr_to_dict(pr)

    def get_pull_request(self, number: int) -> dict[str, Any]:
        with self._lock:
            pr = self._pulls.get(number)
            if pr is None:
                raise KeyError(f"no such PR: {number}")
            return self._pr_to_dict(pr)

    def merge_pull_request(self, number: int) -> dict[str, Any]:
        """Test helper: simulate a merged PR."""
        with self._lock:
            pr = self._pulls.get(number)
            if pr is None:
                raise KeyError(f"no such PR: {number}")
            pr.state = "closed"
            pr.merged = True
            pr.merge_commit_sha = _new_sha()
            return self._pr_to_dict(pr)

    def _pr_to_dict(self, pr: _PullRequest) -> dict[str, Any]:
        return {
            "number": pr.number,
            "title": pr.title,
            "head": {"ref": pr.head},
            "base": {"ref": pr.base},
            "body": pr.body,
            "state": pr.state,
            "merged": pr.merged,
            "merge_commit_sha": pr.merge_commit_sha,
            "user": {"login": pr.user},
            "created_at": pr.created_at,
        }


class _ActAs:
    """Context manager to switch the in-memory client's acting user."""

    def __init__(self, client: InMemoryGitHubClient, login: str) -> None:
        self._client = client
        self._login = login

    def __enter__(self) -> InMemoryGitHubClient:
        self._client._actor_stack.append(self._login)
        return self._client

    def __exit__(self, exc_type, exc, tb) -> None:
        self._client._actor_stack.pop()


def _new_sha() -> str:
    """Generate a 40-character lowercase hex 'sha'."""
    return secrets.token_hex(20)


# ---------------------------------------------------------------------------
# Log sanitisation (SPEC §14)
# ---------------------------------------------------------------------------

# GitHub PAT/OAuth-style tokens.
_RE_GH_TOKEN = re.compile(r"gh[ps]_[A-Za-z0-9]{36,}")
# AWS access key id.
_RE_AWS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
# Bearer tokens in Authorization-style strings.
_RE_BEARER = re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")
# Generic key=value patterns where the key looks secret-shaped. We
# intentionally redact only the captured group so the rest of the
# string (including the key name and separator) survives for context.
_RE_GENERIC_SECRET = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password)[\"'\s:=]+([A-Za-z0-9_\-]{16,})"
)


def _sanitize_string(s: str) -> str:
    """Redact common secret patterns in a single string."""
    out = _RE_GH_TOKEN.sub("***", s)
    out = _RE_AWS_KEY.sub("***", out)
    out = _RE_BEARER.sub("Bearer ***", out)

    def _redact_group(m: re.Match[str]) -> str:
        whole = m.group(0)
        captured = m.group(1)
        # Replace just the captured secret value with ``***``.
        start, end = m.span(1)
        # m.span is relative to the whole input string, not to ``whole``.
        return whole[: start - m.start()] + "***" + whole[end - m.start():]

    out = _RE_GENERIC_SECRET.sub(_redact_group, out)
    return out


def sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copied record with common secret patterns redacted.

    Per SPEC §14: log content on a public repo is world-readable, so
    the handler should pass log records through a sanitiser that drops
    anything matching common secret patterns before writing chunks.

    The original ``record`` is NOT mutated.
    """

    def _walk(node: Any) -> Any:
        if isinstance(node, str):
            return _sanitize_string(node)
        if isinstance(node, dict):
            return {k: _walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(v) for v in node]
        if isinstance(node, tuple):
            return tuple(_walk(v) for v in node)
        return node

    return _walk(record)


# ---------------------------------------------------------------------------
# LogWriter
# ---------------------------------------------------------------------------

@dataclass
class _ChunkInfo:
    path: str
    bytes_: int
    lines: int
    data: bytes


class LogWriter:
    """Append JSONL records, gzip-rotate at a configured size threshold.

    Usage::

        lw = LogWriter(max_chunk_bytes_compressed=512_000)
        lw.write({"ts": iso_now(), "stream": "stdout", "phase": "exec",
                  "data": "hello"})
        ...
        chunks = lw.finalize()        # list[(path, bytes, dict)]
        manifest = lw.manifest(...)   # build manifest dict

    Records are passed through :func:`sanitize_record` before being
    serialised, unless the writer was constructed with
    ``sanitize=False``.
    """

    def __init__(
        self,
        max_chunk_bytes_compressed: int = 524_288,
        chunk_name_template: str = "log-{n:04d}.jsonl.gz",
        sanitize: bool = True,
    ) -> None:
        self._max = int(max_chunk_bytes_compressed)
        self._template = chunk_name_template
        self._sanitize = bool(sanitize)
        self._buf = io.BytesIO()
        self._gz = gzip.GzipFile(fileobj=self._buf, mode="wb", mtime=0)
        self._cur_lines = 0
        self._chunk_index = 1
        self._chunks: list[_ChunkInfo] = []
        self._closed = False

    # ------------------------------------------------------------------
    def set_max_chunk_bytes(self, max_chunk_bytes_compressed: int) -> None:
        """Update the rotation threshold mid-stream (use sparingly).

        Useful for test commands like chatty that want to force rotation
        at a smaller threshold than the production default.
        """
        if self._closed:
            raise RuntimeError("LogWriter is closed")
        n = int(max_chunk_bytes_compressed)
        if n < 1:
            raise ValueError("max_chunk_bytes_compressed must be >= 1")
        self._max = n

    # ------------------------------------------------------------------
    def _rotate_if_needed(self) -> None:
        # Flush current gzip stream to estimate compressed size.
        self._gz.flush()
        if self._buf.tell() >= self._max and self._cur_lines > 0:
            self._close_current_chunk()
            self._open_new_chunk()

    def _close_current_chunk(self) -> None:
        self._gz.close()
        data = self._buf.getvalue()
        path = self._template.format(n=self._chunk_index)
        self._chunks.append(
            _ChunkInfo(path=path, bytes_=len(data), lines=self._cur_lines, data=data)
        )
        self._chunk_index += 1

    def _open_new_chunk(self) -> None:
        self._buf = io.BytesIO()
        self._gz = gzip.GzipFile(fileobj=self._buf, mode="wb", mtime=0)
        self._cur_lines = 0

    # ------------------------------------------------------------------
    def write(self, record: dict[str, Any]) -> None:
        """Append one JSON record (one line) to the current chunk.

        When ``sanitize=True`` (default), the record is passed through
        :func:`sanitize_record` before serialisation.
        """
        if self._closed:
            raise RuntimeError("LogWriter is closed")
        payload = sanitize_record(record) if self._sanitize else record
        line = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        self._gz.write(line)
        self._cur_lines += 1
        # Rotate after writing so chunks contain at least one line.
        self._rotate_if_needed()

    def finalize(self) -> list[tuple[str, bytes, dict[str, int]]]:
        """Close the writer; return list of ``(path, gz_bytes, info)``.

        ``info`` contains keys ``bytes`` and ``lines``.
        """
        if self._closed:
            return [(c.path, c.data, {"bytes": c.bytes_, "lines": c.lines}) for c in self._chunks]
        # Close current chunk if it has any lines.
        if self._cur_lines > 0:
            self._close_current_chunk()
        else:
            # discard empty buffer
            try:
                self._gz.close()
            except Exception:
                pass
        self._closed = True
        return [(c.path, c.data, {"bytes": c.bytes_, "lines": c.lines}) for c in self._chunks]

    def manifest(
        self,
        *,
        command: str,
        args: dict[str, Any],
        checked_out_sha: str,
        started_at: str,
        finished_at: str,
        exit_code: int,
        protocol_version: int = 1,
        extra_schema_fields: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build a manifest dict matching ``log-manifest.schema.json``."""
        if not self._closed:
            self.finalize()
        fields = {
            "ts": {"type": "string", "description": "ISO 8601"},
            "stream": {"enum": ["stdout", "stderr", "meta"]},
            "phase": {"enum": ["setup", "exec", "teardown"]},
            "data": {"type": ["string", "object"]},
        }
        if extra_schema_fields:
            fields.update(extra_schema_fields)
        return {
            "protocol_version": protocol_version,
            "schema": {
                "chunk_format": "jsonl-gz",
                "fields": fields,
            },
            "command": command,
            "args": args,
            "checked_out_sha": checked_out_sha,
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "chunks": [
                {"path": c.path, "bytes": c.bytes_, "lines": c.lines}
                for c in self._chunks
            ],
        }

    # Convenience for tests / debugging
    def chunks(self) -> list[tuple[str, bytes, dict[str, int]]]:
        return self.finalize()


# ---------------------------------------------------------------------------
# Schema loading helpers
# ---------------------------------------------------------------------------

def schemas_root(repo_root: str | os.PathLike[str] = ".") -> Path:
    return Path(repo_root) / ".agent" / "schemas"


def load_schema(name: str, repo_root: str | os.PathLike[str] = ".") -> dict[str, Any]:
    """Load a schema by relative name (e.g. ``commands/run-tests.schema.json``)."""
    p = schemas_root(repo_root) / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def b64_encode(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("ascii")


def b64_decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def new_uuid() -> str:
    return str(uuid.uuid4())


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "task"


def is_terminal_run_status(status: Optional[str]) -> bool:
    return status in {"completed", "error", "parse_error"}


def has_protocol_markers(obj: Any) -> bool:
    """Return True if a parsed JSON object has ``protocol_version`` and ``kind``."""
    return (
        isinstance(obj, dict)
        and "protocol_version" in obj
        and "kind" in obj
    )


__all__ = [
    "GitHubClient",
    "InMemoryGitHubClient",
    "LogWriter",
    "iso_now",
    "load_config",
    "load_schema",
    "validate",
    "parse_agent_meta",
    "render_agent_meta",
    "b64_encode",
    "b64_decode",
    "new_uuid",
    "slugify",
    "is_terminal_run_status",
    "has_protocol_markers",
    "sanitize_record",
]

````

### .claude/skills/task-dag/templates/agent/scripts/handler.py

````text
"""``batch-job-handler`` script (§7.2).

Loads a comment from GitHub via the abstract :class:`GitHubClient`,
parses the JSON envelope, dispatches to a registered command handler,
writes structured logs into ``_agent_runs/runs/<issue>/<comment>/`` and
edits the comment with the terminal envelope.

Importable as ``run(client, issue_number, comment_id, ...)`` for tests.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Optional


def _parse_envelope_lenient(body: str) -> Optional[dict[str, Any]]:
    """Parse the longest JSON-object prefix at the start of ``body``.

    SPEC §5.2 says the comment body is a JSON object with no surrounding
    prose. We interpret "no surrounding prose" liberally to mean **JSON
    must start at the beginning of the body** (after any leading
    whitespace), but trailing prose is tolerated. This is necessary
    because some MCP servers (notably Claude Code's GitHub MCP)
    automatically append a trailer like
    ``\\n---\\n_Generated by [Claude Code](https://claude.ai/code)_``
    to every comment they post.

    Returns the parsed dict, or ``None`` if:
      - ``body`` is not a string, OR
      - the body (after stripping leading whitespace) does not start
        with a valid JSON object.
    """
    if not isinstance(body, str):
        return None
    stripped = body.lstrip()
    if not stripped:
        return None
    try:
        parsed, _idx = json.JSONDecoder().raw_decode(stripped)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed

if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )
else:
    from .common import (
        GitHubClient,
        LogWriter,
        b64_encode,
        has_protocol_markers,
        is_terminal_run_status,
        iso_now,
        load_config,
        load_schema,
        validate,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    *,
    workflow_run_id: int = 0,
    workspace: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Process a single comment. Returns a summary dict for tests."""
    cfg = config or load_config(Path(repo_root) / ".agent" / "config.json")

    comment = client.get_comment(comment_id)
    raw_body = comment.get("body") or ""

    # Step 1: parse envelope ----------------------------------------------
    # Tolerate trailing prose (e.g. the trailer Claude Code's GitHub MCP
    # appends to every comment); see _parse_envelope_lenient.
    parsed: Optional[dict[str, Any]] = _parse_envelope_lenient(raw_body)

    if not has_protocol_markers(parsed):
        return {"action": "ignored", "reason": "no_protocol_markers"}

    assert isinstance(parsed, dict)  # for type checkers

    # Dispatch on envelope kind. Acks are informational follow-up comments;
    # the handler does not process them as batch jobs. They are surfaced
    # through the working->finished gate (SPEC §4.1). Without this dispatch
    # the schema validation step below would parse-error every agent-ack
    # comment because comment-envelope.schema.json says
    # ``kind: const "batch-job-request"``.
    kind = parsed.get("kind")
    if kind == "agent-ack":
        return {"action": "noop", "reason": "ack_comment", "kind": "agent-ack"}

    # Idempotency on already-terminal envelopes (webhook redelivery).
    if is_terminal_run_status(parsed.get("run_status")):
        return {"action": "noop", "reason": "already_terminal", "run_status": parsed["run_status"]}

    envelope_schema = load_schema("comment-envelope.schema.json", repo_root)

    started_at = iso_now()

    # SPEC §13: reject envelopes with unknown protocol_version BEFORE schema
    # validation. We already know parsed has both protocol_version and kind
    # markers (has_protocol_markers above).
    if parsed.get("protocol_version") != 1:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="unsupported_version",
            error_detail=(
                f"protocol_version {parsed.get('protocol_version')!r} is not supported"
            ),
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    # Validate base envelope shape.
    try:
        validate(parsed, envelope_schema)
    except Exception as e:
        return _write_parse_error(
            client,
            comment_id,
            original_body=raw_body,
            error_kind="schema_validation_failed",
            error_detail=str(e),
            workflow_run_id=workflow_run_id,
            started_at=started_at,
        )

    command = parsed.get("command")
    if not command or command not in cfg.get("commands", []):
        # SPEC §5.2.4 reserves parse_error for envelope-schema failures only.
        # An unknown command is a valid envelope referring to an unregistered
        # command — this is a terminal `error` with error_kind=unknown_command.
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="unknown_command",
            error_detail=f"command not in registry: {command!r}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    # Validate args via per-command schema.
    cmd_schema_path = f"commands/{command}.schema.json"
    try:
        cmd_schema = load_schema(cmd_schema_path, repo_root)
    except FileNotFoundError:
        # Command exists in the registry but the schema file is missing —
        # treat as a more specific terminal error so operators can tell
        # this case apart from a truly unknown command.
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="missing_schema",
            error_detail=f"no schema file for command {command}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    args_schema = cmd_schema.get("properties", {}).get("args")
    if args_schema:
        try:
            validate(parsed.get("args", {}), args_schema)
        except Exception as e:
            return _write_parse_error(
                client,
                comment_id,
                original_body=raw_body,
                error_kind="schema_validation_failed",
                error_detail=f"args: {e}",
                workflow_run_id=workflow_run_id,
                started_at=started_at,
            )

    # Step 3: branch+SHA check --------------------------------------------
    branch = parsed["branch"]
    expected_sha = parsed["commit_sha"]
    head_sha = client.get_branch_head_sha(branch)
    if head_sha is None:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"branch does not exist: {branch}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )
    if head_sha != expected_sha:
        return _write_terminal_error(
            client=client,
            issue_number=issue_number,
            comment_id=comment_id,
            envelope=parsed,
            error_kind="branch_sha_mismatch",
            error_detail=f"HEAD={head_sha} != commit_sha={expected_sha}",
            workflow_run_id=workflow_run_id,
            run_started_at=started_at,
            cfg=cfg,
            repo_root=repo_root,
        )

    # Step 4: mark running ------------------------------------------------
    running_envelope = dict(parsed)
    running_envelope["run_status"] = "running"
    running_envelope["run_started_at"] = started_at
    running_envelope["workflow_run_id"] = workflow_run_id
    running_envelope["checked_out_sha"] = head_sha
    client.update_comment(comment_id, json.dumps(running_envelope, indent=2))

    # Step 5: dispatch ----------------------------------------------------
    log_writer = LogWriter(
        max_chunk_bytes_compressed=cfg.get("logs", {}).get("max_chunk_bytes_compressed", 524_288)
    )

    try:
        handler_fn = _load_command_handler(command)
        summary = handler_fn(parsed.get("args", {}) or {}, log_writer, workspace)
        run_status = "completed"
        error_kind: Optional[str] = None
        error_detail: Optional[str] = None
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log_writer.write({
            "ts": iso_now(),
            "stream": "stderr",
            "phase": "exec",
            "data": tb,
        })
        summary = {
            "error_kind": type(e).__name__,
            "error_detail": str(e),
        }
        run_status = "error"
        error_kind = type(e).__name__
        error_detail = str(e)

    finished_at = iso_now()

    # Step 6: validate summary against the command schema -----------------
    summary_schema_key = (
        "summary_completed" if run_status == "completed" else "summary_error"
    )
    summary_schema = cmd_schema.get("properties", {}).get(summary_schema_key)
    if summary_schema is not None:
        try:
            validate(summary, summary_schema)
        except Exception as e:
            run_status = "error"
            error_kind = "summary_schema_violation"
            error_detail = str(e)
            summary = {
                "error_kind": "summary_schema_violation",
                "error_detail": str(e),
            }
            log_writer.write({
                "ts": iso_now(),
                "stream": "stderr",
                "phase": "teardown",
                "data": f"summary schema violation: {e}",
            })

    # Step 7: write logs to _agent_runs ----------------------------------
    chunks = log_writer.finalize()
    manifest = log_writer.manifest(
        command=command,
        args=parsed.get("args", {}) or {},
        checked_out_sha=head_sha,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=0 if run_status == "completed" else 1,
    )

    # Validate the manifest against its schema (defense in depth).
    try:
        manifest_schema = load_schema("log-manifest.schema.json", repo_root)
        validate(manifest, manifest_schema)
    except Exception as e:  # pragma: no cover - manifest is built by us
        log_writer = None  # mark unused
        run_status = "error"
        error_kind = "manifest_schema_violation"
        error_detail = str(e)

    logs_branch = cfg.get("logs", {}).get("branch", "_agent_runs")
    log_dir = f"runs/{issue_number}/{comment_id}"

    summary_json = {
        "summary": summary,
        "run_status": run_status,
        "command": command,
        "args": parsed.get("args", {}) or {},
        "checked_out_sha": head_sha,
        "started_at": started_at,
        "finished_at": finished_at,
    }

    # Ensure the orphan branch exists by writing the manifest first
    # (put_file_contents auto-creates the branch as orphan if missing).
    _retry_put(client, f"{log_dir}/manifest.json",
               json.dumps(manifest, indent=2).encode("utf-8"),
               f"manifest for run {issue_number}/{comment_id}",
               logs_branch)
    for path, gz_bytes, _info in chunks:
        _retry_put(client, f"{log_dir}/{path}", gz_bytes,
                   f"log chunk for {issue_number}/{comment_id}", logs_branch)
    _retry_put(client, f"{log_dir}/summary.json",
               json.dumps(summary_json, indent=2).encode("utf-8"),
               f"summary for {issue_number}/{comment_id}", logs_branch)

    # Step 8: write terminal envelope ------------------------------------
    terminal = dict(running_envelope)
    terminal["run_status"] = run_status
    terminal["run_finished_at"] = finished_at
    terminal["summary"] = summary
    terminal["log_manifest_branch"] = logs_branch
    terminal["log_manifest_path"] = f"{log_dir}/manifest.json"
    if error_kind is not None:
        terminal["error_kind"] = error_kind
    if error_detail is not None:
        terminal["error_detail"] = error_detail

    client.update_comment(comment_id, json.dumps(terminal, indent=2))

    return {
        "action": "ran",
        "command": command,
        "run_status": run_status,
        "summary": summary,
        "log_manifest_path": f"{log_dir}/manifest.json",
        "chunks": [c[0] for c in chunks],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_command_handler(command: str):
    """Import ``.agent/commands/<command>.py`` and return its ``run``."""
    module_name = command.replace("-", "_")
    # Determine the path to the commands directory relative to this file.
    here = os.path.dirname(os.path.abspath(__file__))
    cmd_dir = os.path.normpath(os.path.join(here, os.pardir, "commands"))
    cmd_path = os.path.join(cmd_dir, f"{module_name}.py")
    if not os.path.isfile(cmd_path):
        raise ImportError(f"no command module at {cmd_path}")
    # Use a unique cached module name so dataclass etc. work correctly.
    sys_name = f"_agent_command_{module_name}"
    if sys_name in sys.modules:
        mod = sys.modules[sys_name]
    else:
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location(sys_name, cmd_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not build spec for {cmd_path}")
        mod = module_from_spec(spec)
        sys.modules[sys_name] = mod
        spec.loader.exec_module(mod)
    if not hasattr(mod, "run"):
        raise ImportError(f"command module {module_name} has no run()")
    return mod.run


def _retry_sleep(seconds: float) -> None:
    """Backoff sleep helper. Indirected so tests can stub it out."""
    import time as _time
    _time.sleep(seconds)


def _retry_put(
    client: GitHubClient,
    path: str,
    content: bytes,
    message: str,
    branch: str,
    *,
    retries: int = 6,
) -> None:
    """Put a file with retry + jittered exponential backoff.

    ``put_file_contents`` re-fetches the branch HEAD on each call, so
    each retry sees a fresh ``head_sha``. The backoff between attempts
    spreads out concurrent writers so they don't all collide in the
    same sub-millisecond race window — discovered live during scenario
    02 (multi-subagent), where three handlers writing to ``_agent_runs``
    collided and the (then) no-backoff retry loop exhausted all three
    attempts before any of them could settle.

    Backoff schedule (no-jitter base): 0.5s, 1s, 2s, 4s, 8s, 16s — caps
    at 30s. Each delay is multiplied by a random factor in [0.5, 1.5)
    to spread out concurrent writers further.
    """
    import random as _random

    last_exc: Optional[BaseException] = None
    for attempt in range(retries):
        try:
            client.put_file_contents(path, content, message, branch)
            return
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt + 1 >= retries:
                break
            base = min(0.5 * (2 ** attempt), 30.0)
            jitter = _random.uniform(0.5, 1.5)
            _retry_sleep(base * jitter)
    if last_exc is not None:
        raise last_exc


def _write_parse_error(
    client: GitHubClient,
    comment_id: int,
    *,
    original_body: str,
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    started_at: str,
) -> dict[str, Any]:
    """Replace the comment body with a ``parse_error`` envelope (§5.2.4)."""
    finished_at = iso_now()
    body = {
        "protocol_version": 1,
        "kind": "batch-job-request",
        "run_status": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
        "original_body_b64": b64_encode(original_body),
        "run_started_at": started_at,
        "run_finished_at": finished_at,
        "workflow_run_id": workflow_run_id,
        "agent_ack": None,
    }
    client.update_comment(comment_id, json.dumps(body, indent=2))
    return {
        "action": "parse_error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def _write_terminal_error(
    *,
    client: GitHubClient,
    issue_number: int,
    comment_id: int,
    envelope: dict[str, Any],
    error_kind: str,
    error_detail: str,
    workflow_run_id: int,
    run_started_at: str,
    cfg: dict[str, Any],
    repo_root: str,
) -> dict[str, Any]:
    """Write a terminal ``error`` envelope (e.g. branch_sha_mismatch)."""
    finished_at = iso_now()
    terminal = dict(envelope)
    terminal["run_status"] = "error"
    terminal["run_started_at"] = run_started_at
    terminal["run_finished_at"] = finished_at
    terminal["workflow_run_id"] = workflow_run_id
    terminal["error_kind"] = error_kind
    terminal["error_detail"] = error_detail
    terminal["summary"] = {"error_kind": error_kind, "error_detail": error_detail}
    client.update_comment(comment_id, json.dumps(terminal, indent=2))
    return {
        "action": "error",
        "error_kind": error_kind,
        "error_detail": error_detail,
    }


def main() -> int:
    """``batch-job-handler`` workflow entry point.

    Required environment variables:
      - ``ISSUE_NUMBER``       issue carrying the request comment
      - ``COMMENT_ID``         comment id holding the envelope
      - ``GH_TOKEN`` / ``GITHUB_TOKEN``  REST API token
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug
    Optional:
      - ``GITHUB_RUN_ID`` / ``WORKFLOW_RUN_ID``  workflow run id echoed
        into the running envelope (default ``0``)
      - ``GITHUB_WORKSPACE``   checkout root passed to command handlers

    On success exits 0; on uncaught exception prints to stderr and
    exits 1. Tests call :func:`run` directly with an in-memory client.
    """
    required = ["ISSUE_NUMBER", "COMMENT_ID", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    print(
        "handler: required env vars: "
        + ", ".join(required)
        + ". Optional: GITHUB_RUN_ID, GITHUB_WORKSPACE.",
        file=sys.stderr,
    )
    issue_number = os.environ.get("ISSUE_NUMBER")
    comment_id = os.environ.get("COMMENT_ID")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    missing = [
        name for name, val in (
            ("ISSUE_NUMBER", issue_number),
            ("COMMENT_ID", comment_id),
            ("GITHUB_TOKEN", token),
            ("GITHUB_REPOSITORY", repo_slug),
        ) if not val
    ]
    if missing:
        print(f"handler: missing env vars: {missing}", file=sys.stderr)
        return 1
    assert issue_number is not None and comment_id is not None
    assert token is not None and repo_slug is not None
    if "/" not in repo_slug:
        print(
            f"handler: GITHUB_REPOSITORY must be 'owner/repo', got: {repo_slug!r}",
            file=sys.stderr,
        )
        return 1
    owner, repo = repo_slug.split("/", 1)
    workflow_run_id_str = (
        os.environ.get("GITHUB_RUN_ID") or os.environ.get("WORKFLOW_RUN_ID") or "0"
    )
    try:
        workflow_run_id = int(workflow_run_id_str)
    except ValueError:
        workflow_run_id = 0
    workspace = os.environ.get("GITHUB_WORKSPACE")
    print(
        "handler: dispatching issue "
        f"#{issue_number} comment {comment_id}",
        file=sys.stderr,
    )
    try:
        # Imported lazily so this script remains usable even if requests
        # is missing (e.g. when only run() is invoked from tests).
        if __package__ in (None, ""):
            from rest_client import RestGitHubClient  # type: ignore[import-not-found]
        else:
            from .rest_client import RestGitHubClient
        client = RestGitHubClient(token=token, owner=owner, repo=repo)
        run(
            client,
            int(issue_number),
            int(comment_id),
            workflow_run_id=workflow_run_id,
            workspace=workspace,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"handler: uncaught exception: {exc!r}", file=sys.stderr)
        traceback.print_exc()
        # Self-diagnostic: post a comment on the originating issue with the
        # traceback, so MCP-only operators (who can't read workflow logs)
        # can see what went wrong. Wrapped in its own try/except so a
        # failure here can't mask the original exit code.
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                _post_debug_comment(
                    token=token,
                    owner=owner,
                    repo=repo,
                    issue_number=int(issue_number),
                    script="handler.py",
                    exc=exc,
                    extra_fields={
                        "comment": comment_id,
                        "workflow run": workflow_run_id,
                    },
                )
            except Exception as diag_exc:  # noqa: BLE001
                print(
                    f"handler: failed to post debug comment: {diag_exc!r}",
                    file=sys.stderr,
                )
        return 1
    return 0


def _post_debug_comment(
    *,
    token: str,
    owner: str,
    repo: str,
    issue_number: int,
    script: str,
    exc: BaseException,
    extra_fields: Optional[dict[str, Any]] = None,
) -> None:
    """Post a self-diagnostic comment with traceback to the given issue.

    Uses ``requests.post`` directly to avoid depending on any code path
    that might itself be the source of the bug being diagnosed. Secrets
    are never echoed; the env-var summary only reports presence/absence.
    """
    import requests  # local import: keeps run() importable without requests

    # Summarise env vars without leaking secrets.
    secret_names = {"GH_TOKEN", "GITHUB_TOKEN"}
    relevant = [
        "ISSUE_NUMBER", "COMMENT_ID", "PR_NUMBER",
        "GH_TOKEN", "GITHUB_TOKEN", "GITHUB_REPOSITORY",
        "GITHUB_RUN_ID", "WORKFLOW_RUN_ID", "GITHUB_WORKSPACE",
        "AGENT_LOGIN", "AGENT_TASK_LABEL",
    ]
    env_lines = []
    for name in relevant:
        val = os.environ.get(name)
        if name in secret_names:
            env_lines.append(f"  - {name}: {'set' if val else 'unset'}")
        elif val is not None:
            env_lines.append(f"  - {name}: {val!r}")
        else:
            env_lines.append(f"  - {name}: unset")

    fields_lines = [f"- script: `{script}`", f"- issue: #{issue_number}"]
    for k, v in (extra_fields or {}).items():
        fields_lines.append(f"- {k}: {v}")
    fields_lines.append(f"- python: {sys.version.split()[0]}")

    debug_body = (
        "**handler self-diagnostic — uncaught exception**\n\n"
        + "\n".join(fields_lines)
        + "\n\n"
        + f"```\n{exc!r}\n```\n\n"
        + "<details><summary>Traceback</summary>\n\n"
        + f"```\n{traceback.format_exc()}```\n\n"
        + "</details>\n\n"
        + "<details><summary>Environment</summary>\n\n"
        + "\n".join(env_lines)
        + "\n\n</details>\n"
    )

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.post(url, headers=headers, json={"body": debug_body}, timeout=15)
    # Don't raise — caller wraps us anyway; but record non-2xx status.
    if resp.status_code >= 300:
        print(
            f"handler: debug comment POST returned {resp.status_code}: {resp.text[:200]!r}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(main())

````

### .claude/skills/task-dag/templates/agent/scripts/lock_and_sweep.py

```text
"""``lock-and-sweep`` script (§7.1).

Run on ``issues.opened``. Validates the issue belongs to the protocol
(creator is ``agent_login`` and body contains a parsable ``agent-meta``
block); applies the ``agent-task`` label; sweeps any non-agent comments
that snuck in before the label was applied.

Historically this script also locked the issue at creation time, but
GitHub refuses comments from ``GITHUB_TOKEN`` (the github-actions[bot]
identity) on locked issues — including the batch-job-handler's own
terminal envelope writes. Locking is therefore deferred to
``close_on_merge.py`` (post-merge), where the lock acts as an
audit-tamper-prevention seal rather than an injection guard. The
injection-guard role is filled by the batch-job-handler workflow's
label + author ``if:`` filter, which makes foreign comments inert.

``agent_login`` is sourced from the ``AGENT_LOGIN`` environment variable
(populated from a repo-level GitHub Actions variable so multi-user
deployments don't require workflow-YAML edits) or passed in explicitly
by tests. The static ``agent_login`` config key was removed in session 3
to drop the indirection.

Importable as a module: call :func:`run` directly with a
``GitHubClient`` for tests. The ``__main__`` entry point reads
environment variables (``ISSUE_NUMBER``, ``AGENT_LOGIN``) and is wired
up by the workflow file.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

# When run as a script the package isn't on sys.path; add repo root.
if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from common import (  # type: ignore[import-not-found]
        GitHubClient,
        load_config,
        parse_agent_meta,
    )
else:
    from .common import GitHubClient, load_config, parse_agent_meta


def run(
    client: GitHubClient,
    issue_number: int,
    agent_login: Optional[str] = None,
    agent_task_label: Optional[str] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Apply lock-and-sweep behaviour to an issue.

    ``agent_login`` resolution order: explicit argument → ``AGENT_LOGIN``
    environment variable → raise. There is no fallback to a static config
    key (removed in session 3).

    Returns a small dict describing what happened (useful for tests).
    """
    cfg = config or load_config()
    if agent_login is None:
        agent_login = os.environ.get("AGENT_LOGIN") or None
    if not agent_login:
        raise RuntimeError(
            "agent_login is required: pass it explicitly or set the "
            "AGENT_LOGIN environment variable (typically populated by the "
            "workflow from vars.AGENT_LOGIN)"
        )
    agent_task_label = (
        agent_task_label
        or cfg.get("labels", {}).get("agent_task", "agent-task")
    )

    issue = client.get_issue(issue_number)
    body = issue.get("body") or ""
    creator_login = (issue.get("user") or {}).get("login")

    meta = parse_agent_meta(body)
    if meta is None:
        return {"action": "noop", "reason": "no_agent_meta"}
    if creator_login != agent_login:
        return {"action": "noop", "reason": "creator_not_agent_login"}

    # 1. Apply label.
    client.add_label(issue_number, agent_task_label)

    # 2. Sweep non-agent comments that snuck in before the label was
    #    applied. We deliberately do NOT lock the issue here: a locked
    #    issue rejects comments from the GITHUB_TOKEN bot identity, and
    #    the batch-job-handler workflow needs to write its terminal
    #    envelope back as a comment. The lock is applied later by
    #    close_on_merge.py once the issue is finished.
    deleted = 0
    kept_unexpected = 0
    for c in client.list_comments(issue_number):
        author = (c.get("user") or {}).get("login")
        cid = c["id"]
        if author == agent_login:
            kept_unexpected += 1
            continue
        client.delete_comment(cid)
        deleted += 1

    return {
        "action": "labeled",
        "label_applied": agent_task_label,
        "deleted_comments": deleted,
        "kept_agent_comments": kept_unexpected,
    }


def main() -> int:
    """``lock-and-sweep`` workflow entry point.

    Required environment variables:
      - ``ISSUE_NUMBER``       the issue that just opened
      - ``GH_TOKEN`` / ``GITHUB_TOKEN``  REST API token
      - ``GITHUB_REPOSITORY``  ``owner/repo`` slug
      - ``AGENT_LOGIN``        bot login the protocol expects to author
                                envelopes (set from ``vars.AGENT_LOGIN``)
    Optional:
      - ``AGENT_TASK_LABEL``   override the label from ``.agent/config.json``

    On success exits 0; on uncaught exception prints to stderr and
    exits 1. Tests call :func:`run` directly with an in-memory client.
    """
    required = ["ISSUE_NUMBER", "GITHUB_TOKEN", "GITHUB_REPOSITORY", "AGENT_LOGIN"]
    print(
        "lock_and_sweep: required env vars: "
        + ", ".join(required)
        + ". Optional: AGENT_LOGIN, AGENT_TASK_LABEL.",
        file=sys.stderr,
    )
    issue_number = os.environ.get("ISSUE_NUMBER")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    agent_login = os.environ.get("AGENT_LOGIN") or None
    missing = [
        name for name, val in (
            ("ISSUE_NUMBER", issue_number),
            ("GITHUB_TOKEN", token),
            ("GITHUB_REPOSITORY", repo_slug),
            ("AGENT_LOGIN", agent_login),
        ) if not val
    ]
    if missing:
        print(f"lock_and_sweep: missing env vars: {missing}", file=sys.stderr)
        return 1
    assert issue_number is not None and token is not None and repo_slug is not None
    assert agent_login is not None
    if "/" not in repo_slug:
        print(
            f"lock_and_sweep: GITHUB_REPOSITORY must be 'owner/repo', got: {repo_slug!r}",
            file=sys.stderr,
        )
        return 1
    owner, repo = repo_slug.split("/", 1)
    print(
        f"lock_and_sweep: processing issue #{issue_number}",
        file=sys.stderr,
    )
    try:
        if __package__ in (None, ""):
            from rest_client import RestGitHubClient  # type: ignore[import-not-found]
        else:
            from .rest_client import RestGitHubClient
        client = RestGitHubClient(token=token, owner=owner, repo=repo)
        run(
            client,
            int(issue_number),
            agent_login=agent_login,
            agent_task_label=os.environ.get("AGENT_TASK_LABEL") or None,
        )
    except Exception as exc:  # noqa: BLE001
        import traceback as _tb
        print(f"lock_and_sweep: uncaught exception: {exc!r}", file=sys.stderr)
        _tb.print_exc()
        # Self-diagnostic: post a debug comment on the originating issue.
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                if __package__ in (None, ""):
                    from handler import _post_debug_comment  # type: ignore[import-not-found]
                else:
                    from .handler import _post_debug_comment
                _post_debug_comment(
                    token=token,
                    owner=owner,
                    repo=repo,
                    issue_number=int(issue_number),
                    script="lock_and_sweep.py",
                    exc=exc,
                    extra_fields={},
                )
            except Exception as diag_exc:  # noqa: BLE001
                print(
                    f"lock_and_sweep: failed to post debug comment: {diag_exc!r}",
                    file=sys.stderr,
                )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### .claude/skills/task-dag/templates/agent/scripts/requirements.txt

```text
jsonschema>=4.21.0
PyYAML>=6.0
requests>=2.31.0

```

### .claude/skills/task-dag/templates/agent/scripts/rest_client.py

```text
"""Live REST-backed implementation of the :class:`GitHubClient` Protocol.

This is the workflow side of the agent-job protocol: it is invoked from
GitHub Actions runners using ``GITHUB_TOKEN`` and talks to the
GitHub REST API.

The implementation focuses on the operations the workflow scripts need:

- Issues / labels / lock
- Comments (list, get, add, update, delete)
- Files (read, write — including orphan-branch creation for ``_agent_runs``)
- Branches (head SHA lookup, delete)
- Pull requests (create, get)

It also performs:

- Bearer-token auth with the standard GitHub headers.
- Bounded retry-with-backoff for 5xx and rate-limited 403 responses.
- The blob/tree/commit/ref dance required to commit to a fresh
  orphan branch (the Contents API cannot create branches).
"""

from __future__ import annotations

import base64
import time
from typing import Any, Optional

import requests


_DEFAULT_BASE_URL = "https://api.github.com"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 5
_BACKOFF_SECONDS = (1.0, 2.0, 4.0, 8.0, 16.0)


class RestGitHubClient:
    """REST implementation of the protocol used by the workflow scripts."""

    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        session: Optional[requests.Session] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        sleep: Any = time.sleep,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        if not owner or not repo:
            raise ValueError("owner and repo are required")
        self._token = token
        self._owner = owner
        self._repo = repo
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._sleep = sleep

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @property
    def _repo_path(self) -> str:
        return f"/repos/{self._owner}/{self._repo}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-job-protocol-poc",
        }

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self._base_url + path

    def _is_rate_limited(self, resp: requests.Response) -> bool:
        if resp.status_code != 403:
            return False
        # Primary rate limit signalled by remaining=0.
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining == "0":
            return True
        # Secondary rate limit / abuse detection signalled by Retry-After.
        if resp.headers.get("Retry-After"):
            return True
        # Some endpoints simply put it in the body.
        try:
            j = resp.json()
        except ValueError:
            return False
        msg = (j.get("message") or "").lower() if isinstance(j, dict) else ""
        return "rate limit" in msg or "abuse" in msg or "secondary rate" in msg

    def _rate_limit_sleep(self, resp: requests.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        reset = resp.headers.get("X-RateLimit-Reset")
        if reset:
            try:
                delta = float(reset) - time.time()
                if delta > 0:
                    # Cap the backoff so a clock-skew or far-future reset
                    # doesn't stall the runner forever.
                    return min(delta, 60.0)
            except ValueError:
                pass
        # Fall back to exponential backoff.
        return _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        allow_404: bool = False,
    ) -> requests.Response:
        """Perform an HTTP request with retry on 5xx and rate-limited 403.

        Retries up to ``_MAX_RETRIES`` times. 4xx (other than rate-limited
        403) raise immediately via ``raise_for_status``. When ``allow_404``
        is True, a 404 response is returned without raising.
        """
        url = self._url(path)
        last_resp: Optional[requests.Response] = None
        for attempt in range(_MAX_RETRIES):
            resp = self._session.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=params,
                timeout=self._timeout,
            )
            last_resp = resp
            if 200 <= resp.status_code < 300:
                return resp
            if resp.status_code == 404 and allow_404:
                return resp
            # Deterministic client errors: do NOT retry.
            if resp.status_code in (400, 401, 404, 405, 409, 410, 422):
                resp.raise_for_status()
                return resp  # unreachable; for mypy
            # Rate-limited 403: sleep then retry.
            if resp.status_code == 403 and self._is_rate_limited(resp):
                if attempt < _MAX_RETRIES - 1:
                    self._sleep(self._rate_limit_sleep(resp, attempt))
                    continue
                resp.raise_for_status()
                return resp
            # Other 4xx (e.g. plain 403 forbidden) — don't retry.
            if 400 <= resp.status_code < 500:
                resp.raise_for_status()
                return resp
            # 5xx — retry with exponential backoff.
            if attempt < _MAX_RETRIES - 1:
                self._sleep(_BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)])
                continue
            resp.raise_for_status()
            return resp
        assert last_resp is not None
        last_resp.raise_for_status()
        return last_resp  # unreachable

    # ------------------------------------------------------------------
    # Issue API
    # ------------------------------------------------------------------
    def get_issue(self, number: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/issues/{number}")
        return resp.json()

    def update_issue(
        self,
        number: int,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        if labels is not None:
            payload["labels"] = list(labels)
        resp = self._request("PATCH", f"{self._repo_path}/issues/{number}", json=payload)
        return resp.json()

    def lock_issue(self, number: int) -> None:
        # PUT /repos/{owner}/{repo}/issues/{n}/lock returns 204 No Content.
        self._request("PUT", f"{self._repo_path}/issues/{number}/lock", json={})

    def add_label(self, number: int, label: str) -> None:
        self._request(
            "POST",
            f"{self._repo_path}/issues/{number}/labels",
            json={"labels": [label]},
        )

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = list(labels)
        resp = self._request("POST", f"{self._repo_path}/issues", json=payload)
        return resp.json()

    # ------------------------------------------------------------------
    # Comment API
    # ------------------------------------------------------------------
    def list_comments(self, issue_number: int) -> list[dict[str, Any]]:
        # Paginate by following the Link header's ``rel="next"``.
        out: list[dict[str, Any]] = []
        path = f"{self._repo_path}/issues/{issue_number}/comments"
        params: Optional[dict[str, Any]] = {"per_page": 100}
        while True:
            resp = self._request("GET", path, params=params)
            page = resp.json() or []
            out.extend(page)
            next_url = _next_link(resp.headers.get("Link", ""))
            if not next_url:
                break
            path = next_url
            params = None  # the URL already contains the query string
        return out

    def get_comment(self, comment_id: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/issues/comments/{comment_id}")
        return resp.json()

    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        resp = self._request(
            "PATCH",
            f"{self._repo_path}/issues/comments/{comment_id}",
            json={"body": body},
        )
        return resp.json()

    def delete_comment(self, comment_id: int) -> None:
        self._request("DELETE", f"{self._repo_path}/issues/comments/{comment_id}")

    def add_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        resp = self._request(
            "POST",
            f"{self._repo_path}/issues/{issue_number}/comments",
            json={"body": body},
        )
        return resp.json()

    # ------------------------------------------------------------------
    # File / branch operations
    # ------------------------------------------------------------------
    def get_file_contents(self, path: str, ref: str) -> Optional[str]:
        """Return the file contents at ``ref`` (utf-8 text or base64).

        Returns ``None`` on 404. Mirrors :class:`InMemoryGitHubClient`:
        attempts utf-8 decoding; returns base64 on failure.
        """
        resp = self._request(
            "GET",
            f"{self._repo_path}/contents/{path}",
            params={"ref": ref},
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        if isinstance(body, list):
            # ``path`` resolved to a directory — treat like "no file".
            return None
        encoding = body.get("encoding")
        content = body.get("content") or ""
        if encoding == "base64":
            try:
                raw = base64.b64decode(content)
            except (ValueError, base64.binascii.Error):  # type: ignore[attr-defined]
                return content
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(raw).decode("ascii")
        # Unknown encoding: return as-is.
        return content if isinstance(content, str) else None

    def _get_file_sha(self, path: str, branch: str) -> Optional[str]:
        """Return the blob sha of ``path`` on ``branch`` if it exists."""
        resp = self._request(
            "GET",
            f"{self._repo_path}/contents/{path}",
            params={"ref": branch},
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        if isinstance(body, list):
            return None
        sha = body.get("sha")
        return sha if isinstance(sha, str) else None

    def put_file_contents(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        """Commit a file to ``branch``.

        If ``branch`` does not exist, create it as an orphan via the Git
        Database API (blob/tree/commit with empty parents/ref). If the
        branch exists, prefer the simple Contents API path; if that fails
        we fall back to the Git Database API for the next-commit case
        (blob/tree-with-base/commit-with-parent/patch-ref) so additional
        files on ``_agent_runs`` accumulate into the tree correctly.
        """
        head_sha = self.get_branch_head_sha(branch)
        if head_sha is None:
            return self._create_orphan_commit(path, content_bytes, message, branch)
        # Branch exists — use the Git Database API so the tree is
        # explicitly built from the previous commit, preserving existing
        # files (Contents API would also do this implicitly, but the GDB
        # path is what we tested for orphan-branch follow-ups).
        return self._append_commit(path, content_bytes, message, branch, head_sha)

    def _create_orphan_commit(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        blob_sha = self._create_blob(content_bytes)
        tree_sha = self._create_tree(
            [{"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}],
            base_tree=None,
        )
        commit_sha = self._create_commit(message, tree_sha, parents=[])
        # Create the ref; raises if it already exists.
        self._request(
            "POST",
            f"{self._repo_path}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": commit_sha},
        )
        return {
            "path": path,
            "branch": branch,
            "commit": {"sha": commit_sha, "message": message},
            "size": len(content_bytes),
        }

    def _append_commit(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
        parent_sha: str,
    ) -> dict[str, Any]:
        # Get the parent commit's tree sha.
        resp = self._request("GET", f"{self._repo_path}/git/commits/{parent_sha}")
        parent_tree_sha = resp.json()["tree"]["sha"]
        blob_sha = self._create_blob(content_bytes)
        tree_sha = self._create_tree(
            [{"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}],
            base_tree=parent_tree_sha,
        )
        commit_sha = self._create_commit(message, tree_sha, parents=[parent_sha])
        self._request(
            "PATCH",
            f"{self._repo_path}/git/refs/heads/{branch}",
            json={"sha": commit_sha},
        )
        return {
            "path": path,
            "branch": branch,
            "commit": {"sha": commit_sha, "message": message},
            "size": len(content_bytes),
        }

    def _create_blob(self, content_bytes: bytes) -> str:
        b64 = base64.b64encode(content_bytes).decode("ascii")
        resp = self._request(
            "POST",
            f"{self._repo_path}/git/blobs",
            json={"content": b64, "encoding": "base64"},
        )
        return resp.json()["sha"]

    def _create_tree(
        self,
        entries: list[dict[str, Any]],
        *,
        base_tree: Optional[str],
    ) -> str:
        payload: dict[str, Any] = {"tree": entries}
        if base_tree is not None:
            payload["base_tree"] = base_tree
        resp = self._request("POST", f"{self._repo_path}/git/trees", json=payload)
        return resp.json()["sha"]

    def _create_commit(
        self,
        message: str,
        tree_sha: str,
        *,
        parents: list[str],
    ) -> str:
        payload: dict[str, Any] = {
            "message": message,
            "tree": tree_sha,
            "parents": list(parents),
        }
        resp = self._request("POST", f"{self._repo_path}/git/commits", json=payload)
        return resp.json()["sha"]

    def get_branch_head_sha(self, branch: str) -> Optional[str]:
        resp = self._request(
            "GET",
            f"{self._repo_path}/git/refs/heads/{branch}",
            allow_404=True,
        )
        if resp.status_code == 404:
            return None
        body = resp.json()
        # The refs endpoint returns an object for a single match; some
        # variations of the API return a list when the prefix matched
        # multiple refs. Defensive parsing handles both.
        if isinstance(body, list):
            for entry in body:
                if entry.get("ref") == f"refs/heads/{branch}":
                    return entry.get("object", {}).get("sha")
            return None
        obj = body.get("object") or {}
        sha = obj.get("sha")
        return sha if isinstance(sha, str) else None

    def delete_branch(self, name: str) -> None:
        # 404 is treated as success (idempotent), matching the in-memory client.
        resp = self._request(
            "DELETE",
            f"{self._repo_path}/git/refs/heads/{name}",
            allow_404=True,
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()

    def list_branches(self) -> list[dict[str, Any]]:
        """List branches in the repo, paginated.

        Returns a list of ``{"name": str, "sha": str, "protected": bool}``
        entries built from the REST ``GET /repos/{owner}/{repo}/branches``
        response. Pagination follows the ``Link: rel="next"`` header.
        """
        out: list[dict[str, Any]] = []
        path = f"{self._repo_path}/branches"
        params: Optional[dict[str, Any]] = {"per_page": 100}
        while True:
            resp = self._request("GET", path, params=params)
            page = resp.json() or []
            for b in page:
                if not isinstance(b, dict):
                    continue
                commit = b.get("commit") or {}
                out.append({
                    "name": b.get("name"),
                    "sha": commit.get("sha"),
                    "protected": bool(b.get("protected", False)),
                })
            next_url = _next_link(resp.headers.get("Link", ""))
            if not next_url:
                break
            path = next_url
            params = None
        return out

    # ------------------------------------------------------------------
    # PR API
    # ------------------------------------------------------------------
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]:
        resp = self._request(
            "POST",
            f"{self._repo_path}/pulls",
            json={"title": title, "head": head, "base": base, "body": body},
        )
        return resp.json()

    def get_pull_request(self, number: int) -> dict[str, Any]:
        resp = self._request("GET", f"{self._repo_path}/pulls/{number}")
        return resp.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_link(link_header: str) -> Optional[str]:
    """Parse a ``Link`` header and return the URL with ``rel="next"``."""
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) < 2:
            continue
        url_part = section[0].strip()
        if not (url_part.startswith("<") and url_part.endswith(">")):
            continue
        rel = None
        for s in section[1:]:
            s = s.strip()
            if s.startswith("rel="):
                rel = s.split("=", 1)[1].strip().strip('"')
                break
        if rel == "next":
            return url_part[1:-1]
    return None


__all__ = ["RestGitHubClient"]

```

### .claude/skills/task-dag/templates/github/workflows/batch-job-handler.yml

```text
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
      github.event.comment.user.login == (vars.AGENT_LOGIN || 'jonathanmanton')
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - name: marker-start
        run: |
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d '{"body":"<!-- workflow-marker -->\n[handler-start] run=${{ github.run_id }} comment=${{ github.event.comment.id }}"}' \
            > /tmp/marker-start.json || true
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r .agent/scripts/requirements.txt
      - id: handler
        run: python .agent/scripts/handler.py 2>&1 | tee /tmp/handler.log
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          COMMENT_ID: ${{ github.event.comment.id }}
          WORKFLOW_RUN_ID: ${{ github.run_id }}
          AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}
      - name: marker-end
        if: always()
        run: |
          conclusion="${{ steps.handler.conclusion }}"
          # Trim and base64 just to embed cleanly; readers can decode
          tail_b64=$(tail -c 4000 /tmp/handler.log 2>/dev/null | base64 -w0 || echo "")
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d "{\"body\":\"<!-- workflow-marker -->\n[handler-end] run=${{ github.run_id }} comment=${{ github.event.comment.id }} conclusion=${conclusion}\n\n<details><summary>last 4KB of stdout/stderr (base64)</summary>\n\n\`\`\`\n${tail_b64}\n\`\`\`\n\n</details>\"}" \
            > /tmp/marker-end.json || true

```

### .claude/skills/task-dag/templates/github/workflows/close-on-merge.yml

```text
name: close-on-merge
on:
  pull_request:
    types: [closed]
permissions:
  issues: write
  pull-requests: read
  contents: write
jobs:
  close:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r .agent/scripts/requirements.txt
      - run: python .agent/scripts/close_on_merge.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}

```

### .claude/skills/task-dag/templates/github/workflows/lock-and-sweep.yml

```text
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
        with:
          python-version: '3.12'
      - run: pip install -r .agent/scripts/requirements.txt
      - run: python .agent/scripts/lock_and_sweep.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          AGENT_LOGIN: ${{ vars.AGENT_LOGIN || 'jonathanmanton' }}

```

### test-harness/README.md

```text
# test-harness

This is the **test-harness DEVELOPMENT-ONLY skill**. Entry point:
[`SKILL.md`](./SKILL.md).

It drives the 5 distributable skills (`batch-job`, `task-dag`,
`orchestrate-issue`, `onboarding`, `composition-guide`) against
synthetic archetypes and the live new repo. **NOT for end-user
distribution.**

See also:

- [`SPEC.md`](./SPEC.md) — long-form design spec
- [`archetypes/`](./archetypes/) — 8 archetype fixture trees
- [`scenarios/`](./scenarios/) — 18 scenario YAML specs
- [`lib/`](./lib/) — Python helpers (`archetype_loader.py`,
  `scenario_runner.py`, `assertions.py`, `state.py`)
- [`runs/`](./runs/) — per-run state directory (gitkeep'd)

```

### test-harness/SKILL.md

````text
---
name: test-harness
description: |
  DEVELOPMENT-ONLY skill for validating the agent-job protocol skills
  against synthetic repo archetypes and live GitHub repos. Stepwise:
  setup/step/inspect/reset/run-all. Uses the running agent's GitHub
  MCP credentials. NOT for end-user distribution. Use in the
  pipeline-ai-sandbox maintenance repo only.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - mcp__github__*
---

# test-harness — development-only skill

> **WARNING — DEVELOPMENT-ONLY**
>
> This skill is bundled with the bootstrap so it lives in the new
> `pipeline-ai-sandbox` repo from day one, but it is **never** included
> in the end-user distribution build. Its sole purpose is to validate
> the 5 distributable skills (`batch-job`, `task-dag`,
> `orchestrate-issue`, `onboarding`, `composition-guide`) before they
> ship.

## Triggers

The skill matches when a maintainer in the `pipeline-ai-sandbox` repo
asks:

- "Run the test harness scenario `<id>`"
- "Test the onboarding skill against archetype `<name>`"
- "Drive an end-to-end orchestrate-issue against the test harness"
- "/test-harness setup", "/test-harness step", "/test-harness inspect",
  "/test-harness reset", "/test-harness run-all", "/test-harness report"
- "Run all test harness scenarios"

It does **not** match end-user invocations of the 5 distributable
skills.

## Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `command` | enum | yes | One of `setup`, `step`, `inspect`, `reset`, `run-all`, `report` |
| `scenario_id` | string | for `setup` | e.g. `onboarding-blank-repo` |
| `archetype` | string | for `setup` | Override the scenario's archetype; rare |
| `target` | enum | no | `synthetic-fixture` (default for unit scenarios) or `live-new-repo` |
| `phase_filter` | string | no | Restrict to phases whose name matches this token |
| `run_id` | string | no | Continue a prior run instead of creating a fresh one |

The `command` enum is the primary entry point. All other inputs are
contextual to the command being invoked.

## Outputs

- `harness/runs/<run_id>/state.json` — per-scenario run state. Written
  after every phase. Restart-safe.
- `harness/runs/<run_id>/report.md` — final scenario report, generated
  by the `report` command at the end of a run.
- `harness/runs/<run_id>/diagnostics/` — captured artifacts (raw logs,
  branch SHAs, comment ids, MCP responses). One file per phase.
- Console output with a **state block** at every step (see
  [State-block formatting](#state-block-formatting) below).

The `<run_id>` is a `YYYYMMDD-HHMMSS` timestamp generated at `setup`
time, or recovered from `run_id` on subsequent commands.

## Stepwise commands

| Command | Effect |
|---|---|
| `setup <scenario_id>` | Materialise the archetype; initialise run state; report phase 1 ready |
| `step` | Run the next pending phase; persist state; emit state block |
| `inspect` | Show current state, last phase output, next phase plan |
| `reset` | Tear down the current scenario (delete synthetic fixture, archive run logs, optionally delete live GitHub repo); ready for next scenario |
| `run-all` | Iterate `step` until all phases complete or the first failure; emit per-phase state blocks throughout |
| `report` | Render `harness/runs/<run_id>/report.md` to console |

Every command writes state before returning. If interrupted, the next
command re-reads state and resumes from the first `pending` (or
`in_progress`) phase.

## Real-GitHub interaction model

The harness uses the **running agent's own** GitHub MCP credentials.
No separate test account. No secrets. No PAT setup. The agent must
have the `mcp__github__*` tools enabled in its sandbox.

### `target: live-new-repo`

1. Harness creates a fresh GitHub repo under the agent's account via
   `mcp__github__create_repository`. Naming is deterministic and
   unique-per-run: `<agent-login>/<run_id>-<scenario_id>`. Parallel
   scenarios never collide.
2. Archetype files are pushed via `mcp__github__push_files`.
3. Scenario phases run against the live repo.
4. On `reset`, the harness either deletes the temporary repo or
   archives it under a `harness-runs-*` prefix for forensic
   preservation (controlled by scenario config).

### `target: synthetic-fixture`

1. Harness materialises the archetype tree into a local temporary
   directory under `harness/runs/<run_id>/fixture/`.
2. Skills that would call `mcp__github__*` are run against an
   in-process mock (the POC's `InMemoryGitHubClient`, adapted).
3. No live GitHub interaction. Faster, used for unit-style scenarios.

The default is `target: live-new-repo` for end-to-end scenarios; some
lighter scenarios default to `synthetic-fixture` and declare so in
their YAML. Either default can be overridden at `setup` time.

## State and restart safety

State is written after every phase to `harness/runs/<run_id>/state.json`:

```json
{
  "run_id": "20260514-051200",
  "scenario_id": "orchestrate-issue-parallel-fanout",
  "archetype": "python-gha-with-agents-md",
  "skill_under_test": "orchestrate-issue",
  "target": "live-new-repo",
  "github_repo": "<agent-login>/20260514-051200-orchestrate-issue-parallel-fanout",
  "phases": [
    {"name": "setup",  "status": "done",        "elapsed_s": 23},
    {"name": "claim",  "status": "in_progress", "started_at": "2026-05-14T05:12:43Z"},
    {"name": "fanout", "status": "pending"},
    {"name": "merge",  "status": "pending"},
    {"name": "verify", "status": "pending"}
  ],
  "diagnostics": {
    "issue_numbers": [1],
    "pr_numbers": [],
    "branches_created": ["agent/1-..."]
  }
}
```

A subsequent `step` invocation:

1. Reads `state.json`.
2. Finds the first `in_progress` phase (resume) or `pending` phase
   (advance).
3. Runs that phase, updates its `status` to `done` or `failed`.
4. Persists state.
5. Emits a state block.

A scenario interrupted mid-phase is safe to resume because phase
implementations are idempotent: re-running a `setup` phase on an
already-materialised fixture is a no-op; re-running an `invoke` phase
asserts post-state rather than mutating again.

## State-block formatting

Every command emits a state block to the console before returning:

```
[test-harness • scenario: onboarding-blank-repo • phase 2/4 (interview)]
  setup:     done    (archetype materialised at harness/runs/20260514-055717/)
  detect:    done    (protocol_installed=false, onboarding_started=false)
  interview: ready   (22 questions queued; scripted answers loaded)
  recommend: pending
  apply:     pending
Next: invoke onboarding skill in interview mode with scripted answers
```

The block is generated by `lib/state.py :: write_state_block_console`.
Fields:

- Header: `[test-harness • scenario: <id> • phase <i>/<n> (<name>)]`
- One row per phase: `<name>: <status> (<short detail>)`
- Footer: `Next: <human description of next action>`

Statuses: `pending`, `ready`, `in_progress`, `done`, `failed`,
`skipped`.

## Self-install logic

On first invocation in a session, the skill verifies:

1. The 5 distributable skills exist at `.claude/skills/<name>/`
   (where `<name>` is one of `batch-job`, `task-dag`,
   `orchestrate-issue`, `onboarding`, `composition-guide`).
2. The `harness/runs/` directory exists; creates it if not.
3. `mcp__github__get_me` returns a usable login (only required for
   `target: live-new-repo` scenarios).

If any check fails the harness aborts with a clear error that names
the missing artifact. The harness itself **does not** install
templates into the target repo — that is the responsibility of each
distributable skill on its own first invocation.

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Archetype not found | `setup` phase | Abort with the list of valid archetype names |
| Scenario YAML invalid | `setup` phase | Abort with a schema error citing the bad key |
| GitHub repo creation rate-limited | live-target `setup` | Backoff + retry up to 3 times; abort if still failing |
| Skill under test not installed | `invoke` phase | Surface as "missing dependency: `.claude/skills/<skill>/SKILL.md` not found"; abort |
| Phase assertion fails | any phase's verify step | Record failure in state; continue to the next phase or abort per scenario config |
| Live GitHub cleanup fails | `reset` phase | Log warning and leave artifacts on GitHub for forensics; do not raise |
| MCP token absent | first invocation | Abort with a clear "MCP github tools not available" message |

## Anti-patterns

- **Do not** ship this skill in the end-user distribution build. It
  exists only for development. The `bootstrap/distribution-exclude.txt`
  manifest in the bootstrap bundle MUST list `test-harness/` (and the
  build script enforces it).
- **Do not** run live scenarios against the user's production repo by
  accident. `target: live-new-repo` always creates a *fresh temporary*
  repo via `mcp__github__create_repository`; never reuse an existing
  repo for a scenario.
- **Do not** silently delete archetype fixtures; the harness should
  keep them for re-runs. Only `reset` removes a run's working
  directory, and only after archiving its logs.
- **Do not** assume scenarios are independent unless the scenario YAML
  explicitly marks it. The `multi-scenario-soak` scenario is a
  deliberate test for cross-contamination and must not be
  parallelised with itself.
- **Do not** call the 5 distributable skills via the Skill tool from
  inside a scenario phase. Use their Python helper entry points (the
  bundled `lib/` modules of each skill). Recursion is hard to debug.
- **Do not** edit AGENTS.md or CLAUDE.md from any harness scenario.
  Only the `onboarding` skill under test may propose pointer edits to
  those files, and only with explicit per-file approval.

## See also

- `SPEC.md` (same directory) — the long-form design spec
- `archetypes/<name>/manifest.json` — per-archetype metadata
- `scenarios/<id>.yml` — per-scenario phase specs
- `lib/archetype_loader.py`, `lib/scenario_runner.py`,
  `lib/assertions.py`, `lib/state.py` — Python helpers

---

Version: 0.1.0
Protocol-version: 1
Last-synced-from-POC: 2026-05-14

````

### docs/test-harness/SPEC.md

````text
# SPEC — test-harness (development-only)

Status: design-stage
Audience: implementers of the test harness in the new `pipeline-ai-sandbox` repo

This document specifies the **test harness skill** that lives in the
bootstrap bundle and the new `pipeline-ai-sandbox` repo. It is **not
part of the end-user distribution**. Its sole purpose is to validate
the 5 distributable skills before they ship.

## Purpose

Drive the 5 distributable skills (`batch-job`, `task-dag`,
`orchestrate-issue`, `onboarding`, `composition-guide`) against
synthetic repo archetypes — and against the new repo itself — using
real GitHub access via the running agent's MCP credentials.

The harness is **stepwise** — every test scenario can be paused,
inspected, and resumed via named keyword commands. It is **scenario-
based** — each archetype + skill combination is a discrete scenario
spec. And it is **agent-driven** — runs in a Claude Code sandbox (or
equivalent) using `mcp__github__*` tools, not a separate test account.

## Trigger conditions

The skill matches when:

- "Run the test harness scenario `<id>`"
- "Test the onboarding skill against archetype `<name>`"
- "Drive an end-to-end orchestrate-issue against the test harness"
- "/test-harness setup", "/test-harness step", "/test-harness reset"
- "Run all test harness scenarios"

## Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `command` | enum | yes | `setup`, `step`, `inspect`, `reset`, `run-all`, `report` |
| `scenario_id` | string | for setup | e.g. `onboarding-blank-repo`, `orchestrate-multi-subagent` |
| `archetype` | string | for setup | e.g. `python-gha-with-agents-md`, `node-circleci-no-agents-md` |
| `target` | enum | no | `synthetic-fixture` (default) or `live-new-repo` |
| `phase_filter` | string | no | Run only phase(s) matching this name |

## Outputs

- `harness/runs/<run_id>/state.json` — per-scenario run state (restart-safe)
- `harness/runs/<run_id>/report.md` — final scenario report
- `harness/runs/<run_id>/diagnostics/` — captured artifacts (logs, branch SHAs, comment ids)
- Console output formatted with state blocks at every step

## Archetypes

A catalog of synthetic repo states the harness can stand up before
running a scenario. Implemented as fixture directories that the
harness copies into a temporary location and initialises as a git
repo (and, for live-target scenarios, pushes to a fresh GitHub repo
under the agent's account).

| Archetype | Description |
|---|---|
| `blank-repo` | Empty repo; no AGENTS.md, no CI, no README beyond placeholder. Tests onboarding on a clean slate. |
| `python-gha-with-agents-md` | Python project; existing AGENTS.md and CLAUDE.md; GitHub Actions workflows; pytest. The "ideal adoption target" archetype. |
| `node-circleci-no-agents-md` | Node.js project; CircleCI config; no AGENTS.md. Tests discovery of non-GHA CI. |
| `monorepo-multi-language` | Multiple sub-projects; both GHA and a `Jenkinsfile`. Tests heterogeneous CI discovery. |
| `existing-skills-conflict` | Has a `.claude/skills/batch-job/` directory with a conflicting older version. Tests conflict-resolution prompts in skill self-install. |
| `partial-protocol` | Has `.agent/config.json` but no workflows. Tests skills that detect partial install. |
| `protocol-installed-not-onboarded` | Full protocol install, but no dialog file on well-known branch. Tests the "installed but not onboarded" detection. |
| `gitlab-only` | GitLab CI config; no GitHub Actions. Tests discovery + onboarding's recognition that GHA is required. |

Archetypes live at `test-harness/archetypes/<name>/` as a snapshot
tree. Each has a `manifest.json` listing files, expected discovery
outputs, and any baseline state.

## Scenarios

A scenario is a YAML spec at `test-harness/scenarios/<id>.yml`. Each
specifies:

- `archetype` — which archetype to start from
- `skill_under_test` — which of the 5 distributable skills to drive
- `phases` — ordered list of named phases, each with:
  - `name` — e.g. `setup`, `invoke`, `verify`
  - `inputs` — what the harness passes to the skill
  - `expected` — assertions to make after the phase completes

Example (`onboarding-blank-repo.yml`):

```yaml
scenario_id: onboarding-blank-repo
archetype: blank-repo
skill_under_test: onboarding
phases:
  - name: detect
    expected:
      protocol_installed: false
      onboarding_started: false
  - name: interview
    inputs:
      scripted_answers:
        intent: "tests the onboarding skill"
        problems: "validation"
        adoption: "full"
    expected:
      dialog_file_present: true
      questions_answered: 22
  - name: recommend
    expected:
      recommendations_file_present: true
      no_agents_md_edits_proposed: true
  - name: apply
    inputs:
      approve_all: true
    expected:
      pointer_added_to_agents_md: true
      protocol_templates_installed: true
```

Scenarios live at `test-harness/scenarios/<id>.yml`.

## Stepwise commands

The harness exposes these named commands. Each is an entry point in
the skill's SKILL.md.

| Command | Effect |
|---|---|
| `setup <scenario_id>` | Materialise the archetype; initialise state; report phase 1 ready |
| `step` | Run the next phase; report state |
| `inspect` | Show current state, last phase output, next phase plan |
| `reset` | Tear down current scenario (delete fixture, archive run logs); ready for next |
| `run-all` | Run every phase sequentially; report at end |
| `report` | Print the run report to console |

Every command output includes a state block:

```
[test-harness • scenario: onboarding-blank-repo • phase 2/4 (interview)]
  Setup:    done    (archetype materialised at /tmp/harness/<run_id>/)
  Interview: ready  (22 questions queued; scripted answers loaded)
  Recommend: pending
  Apply:     pending
Next: invoke onboarding skill in interview mode with scripted answers
```

## Real-GitHub interaction model

The harness uses the running agent's own GitHub MCP credentials.
**No separate test account.** No secrets configuration. No PAT setup.

For scenarios with `target: live-new-repo`:

1. The harness creates a temporary GitHub repo under the agent's
   account (via `mcp__github__create_repository`) with a deterministic
   name like `<run_id>-<scenario_id>`. Naming is unique per run so
   parallel scenarios don't collide.
2. The archetype's files are pushed to that repo.
3. The scenario runs against the live repo.
4. After the scenario, the harness optionally deletes the repo (or
   archives it under a `harness-runs` GitHub org/user prefix for
   forensic preservation if the scenario failed).

For scenarios with `target: synthetic-fixture`:

1. The harness initialises a local-only git repo with the archetype.
2. Skills that require GitHub interaction (`mcp__github__*`) use an
   in-process mock client (the POC's `InMemoryGitHubClient` adapted
   for the new repo).

The default for skill validation is `target: live-new-repo`. Some
unit-style scenarios (e.g. testing the onboarding interview state
machine) use `synthetic-fixture` for speed.

## State and restart safety

Every scenario writes state after every phase:

```json
{
  "run_id": "20260514-051200",
  "scenario_id": "orchestrate-multi-subagent",
  "archetype": "python-gha-with-agents-md",
  "target": "live-new-repo",
  "github_repo": "jonathanmanton/20260514-051200-orchestrate-multi-subagent",
  "phases": [
    {"name": "setup", "status": "done", "elapsed": 23},
    {"name": "invoke", "status": "in_progress", "started_at": "..."},
    {"name": "verify", "status": "pending"}
  ],
  "diagnostics": {
    "issue_numbers": [1],
    "pr_numbers": [],
    "branches_created": ["agent/1-..."]
  }
}
```

If interrupted, `step` re-reads state and resumes from the
`in_progress` or first `pending` phase.

## Scenario catalog (initial)

At least one scenario per (archetype, skill) combination plus
edge-case scenarios. Initial catalog:

1. `batch-job-happy-path` — submit echo command, get terminal ack
2. `batch-job-parse-error` — submit malformed envelope, get parse_error
3. `batch-job-branch-sha-mismatch` — submit with stale SHA, get error
4. `batch-job-runner-pickup-timeout` — submit against non-existent command
5. `task-dag-claim-and-plan` — claim an issue, generate a brief
6. `task-dag-stale-takeover` — second agent takes over an abandoned issue
7. `task-dag-merge-conflicts` — merge subagent branches with conflicts
8. `orchestrate-issue-single-subagent` — minimal orchestrate-issue run
9. `orchestrate-issue-parallel-fanout` — 3 parallel subagents merge in plan order
10. `orchestrate-issue-restart-recovery` — kill mid-fanout, restart
11. `onboarding-blank-repo` — full onboarding on an empty repo
12. `onboarding-existing-agents-md` — onboarding does NOT modify AGENTS.md beyond pointer
13. `onboarding-resume-mid-interview` — partial dialog file, resume from question 14
14. `onboarding-decline` — user declines; verify no state written
15. `onboarding-revise` — re-invoke after completion to change integration choices
16. `composition-guide-render` — verify SKILL.md renders cleanly with no broken links
17. `multi-scenario-soak` — drive 3 orchestrate-issue runs in parallel against 3 issues; verify no cross-contamination
18. `protocol-installed-not-onboarded` — verify each skill detects this state correctly

The full catalog grows in the new repo as scenarios are added.

## SKILL.md frontmatter

```yaml
---
name: test-harness
description: |
  DEVELOPMENT-ONLY skill for validating the agent-job protocol skills
  against synthetic repo archetypes and live GitHub repos. Stepwise:
  setup/step/inspect/reset/run-all. Uses the running agent's GitHub
  MCP credentials. NOT for end-user distribution. Use in the
  pipeline-ai-sandbox maintenance repo only.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - mcp__github__*
---
```

## Self-install logic

The harness has no in-repo template install (it lives entirely under
`test-harness/` in the new repo). On first invocation it does verify:

- The 5 distributable skills are present at `.claude/skills/<name>/`.
- The `harness/runs/` directory exists (creates if not).
- The agent's `mcp__github__get_me` returns a usable login.

If any of these fail, the harness aborts with a clear error.

## Bundled artifacts (inside the bootstrap bundle)

```
test-harness/
  SKILL.md
  SPEC.md                       (this file)
  archetypes/
    blank-repo/
      manifest.json
      <archetype files>
    python-gha-with-agents-md/
      ...
    [other archetypes]
  scenarios/
    onboarding-blank-repo.yml
    [other scenarios]
  lib/
    archetype_loader.py
    scenario_runner.py
    assertions.py
    state.py
  runs/.gitkeep
```

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Archetype not found | Setup phase | Abort with list of valid archetypes |
| Scenario YAML invalid | Setup phase | Abort with schema error |
| GitHub repo creation rate-limited | Live target setup | Backoff + retry; abort after 3 |
| Skill under test not installed | Invoke phase | Surface as "missing dependency"; abort |
| Phase assertion fails | Verify phase | Record failure in state; continue or abort per scenario config |
| Live GitHub cleanup fails | Reset phase | Log warning, leave artifacts for forensics |

## Tests of the harness itself

- Unit test each archetype's `manifest.json` against a schema.
- Unit test the scenario YAML schema.
- Lint check: every scenario references a valid archetype + skill.

## Anti-patterns

- **Do not** ship this skill in the end-user distribution. It exists for development only.
- **Do not** run live scenarios against the user's production repo by accident — `target: live-new-repo` always creates a fresh temporary repo.
- **Do not** silently delete archetype fixtures; the harness should keep them for re-runs.
- **Do not** assume scenarios are independent unless explicitly marked — parallel-soak scenarios test for non-independence.

## Dependencies

- The 5 distributable skills (the things being tested).
- A GitHub MCP server with `create_repository` permission (the
  default for a personal-account agent).
- Python 3.12 for the harness's `lib/` helpers.

````

### test-harness/archetypes/blank-repo/README.md

```text
# blank-repo

Placeholder README for the `blank-repo` archetype.

This archetype represents a brand-new GitHub repo with no AGENTS.md,
no CI, and no protocol install. The onboarding skill should be able
to discover the empty state and offer a from-scratch interview.

```

### test-harness/archetypes/blank-repo/manifest.json

```text
{
  "name": "blank-repo",
  "description": "Empty repo; no AGENTS.md, no CI, only a placeholder README. Used to test onboarding on a clean slate.",
  "expected_discovery": {
    "agents_md_present": false,
    "claude_md_present": false,
    "ci_system": "none",
    "language": "unknown",
    "protocol_installed": false,
    "onboarding_started": false
  },
  "files": [
    "README.md"
  ]
}

```

### test-harness/archetypes/existing-skills-conflict/.claude/skills/batch-job/SKILL.md

```text
# batch-job (old conflicting version)

```

### test-harness/archetypes/existing-skills-conflict/README.md

```text
# existing-skills-conflict

A repo that already has a stale `.claude/skills/batch-job/SKILL.md`.
Used to test the conflict-resolution prompts in batch-job's
self-install logic.

```

### test-harness/archetypes/existing-skills-conflict/manifest.json

```text
{
  "name": "existing-skills-conflict",
  "description": "Repo with a deliberately older/conflicting .claude/skills/batch-job/ directory. Tests conflict resolution in skill self-install.",
  "expected_discovery": {
    "agents_md_present": false,
    "claude_md_present": false,
    "ci_system": "none",
    "language": "unknown",
    "protocol_installed": false,
    "onboarding_started": false
  },
  "files": [
    "README.md",
    ".claude/skills/batch-job/SKILL.md"
  ]
}

```

### test-harness/archetypes/gitlab-only/.gitlab-ci.yml

```text
stages:
  - test

test:
  stage: test
  image: alpine:3.19
  script:
    - echo "placeholder gitlab-ci test"

```

### test-harness/archetypes/gitlab-only/README.md

```text
# gitlab-only

A repo with GitLab CI and no GitHub Actions. Used to test the
onboarding skill's recognition that the agent-job protocol requires
GitHub Actions and must surface a clear "GHA not present" message.

```

### test-harness/archetypes/gitlab-only/manifest.json

```text
{
  "name": "gitlab-only",
  "description": "GitLab CI config and no GitHub Actions. Tests onboarding's recognition that GHA is required for the protocol.",
  "expected_discovery": {
    "agents_md_present": false,
    "claude_md_present": false,
    "ci_system": "gitlab-ci",
    "language": "unknown",
    "protocol_installed": false,
    "onboarding_started": false
  },
  "files": [
    "README.md",
    ".gitlab-ci.yml"
  ]
}

```

### test-harness/archetypes/monorepo-multi-language/README.md

```text
# monorepo-multi-language

A monorepo fixture with multiple sub-projects:

- `api/` — has a Dockerfile and a per-subproject GitHub Actions workflow
- `worker/` — has a Jenkinsfile and a Gradle build

Used to test the onboarding skill's heterogeneous CI discovery.

```

### test-harness/archetypes/monorepo-multi-language/api/.github/workflows/api.yml

```text
name: api

on:
  push:
    paths: [api/**]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "placeholder api build"

```

### test-harness/archetypes/monorepo-multi-language/api/Dockerfile

```text
# placeholder Dockerfile for the api sub-project
FROM alpine:3.19
CMD ["echo", "placeholder api"]

```

### test-harness/archetypes/monorepo-multi-language/manifest.json

```text
{
  "name": "monorepo-multi-language",
  "description": "Monorepo with multiple sub-projects, GHA, and a Jenkinsfile. Tests heterogeneous CI discovery.",
  "expected_discovery": {
    "agents_md_present": false,
    "claude_md_present": false,
    "ci_system": "github-actions",
    "language": "mixed",
    "protocol_installed": false,
    "onboarding_started": false
  },
  "files": [
    "README.md",
    "api/Dockerfile",
    "api/.github/workflows/api.yml",
    "worker/Jenkinsfile",
    "worker/build.gradle"
  ]
}

```

### test-harness/archetypes/monorepo-multi-language/worker/Jenkinsfile

```text
pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        echo 'placeholder worker build'
      }
    }
  }
}

```

### test-harness/archetypes/monorepo-multi-language/worker/build.gradle

```text
// placeholder build.gradle for the worker sub-project
plugins {
    id 'java'
}

group = 'example'
version = '0.0.1'

```

### test-harness/archetypes/node-circleci-no-agents-md/.circleci/config.yml

```text
version: 2.1

jobs:
  build:
    docker:
      - image: cimg/node:20.10
    steps:
      - checkout
      - run: npm install
      - run: npm test

workflows:
  build-and-test:
    jobs:
      - build

```

### test-harness/archetypes/node-circleci-no-agents-md/README.md

```text
# node-circleci-no-agents-md

A Node.js project with CircleCI CI and no AGENTS.md. Used to test
the onboarding skill's discovery of non-GHA CI systems.

```

### test-harness/archetypes/node-circleci-no-agents-md/manifest.json

```text
{
  "name": "node-circleci-no-agents-md",
  "description": "Node.js project with CircleCI config and no AGENTS.md. Tests discovery of non-GHA CI.",
  "expected_discovery": {
    "agents_md_present": false,
    "claude_md_present": false,
    "ci_system": "circleci",
    "language": "node",
    "protocol_installed": false,
    "onboarding_started": false
  },
  "files": [
    "README.md",
    "package.json",
    ".circleci/config.yml"
  ]
}

```

### test-harness/archetypes/node-circleci-no-agents-md/package.json

```text
{
  "name": "node-circleci-fixture",
  "version": "0.0.1",
  "private": true,
  "description": "Fixture repo for the test-harness skill.",
  "scripts": {
    "test": "echo \"no tests yet\" && exit 0"
  }
}

```

### test-harness/archetypes/partial-protocol/.agent/config.json

```text
{"protocol_version": 1, "commands": {}}

```

### test-harness/archetypes/partial-protocol/README.md

```text
# partial-protocol

A repo that has `.agent/config.json` but no workflow YAMLs. Used to
test skill self-install logic that must detect a partial install and
either fail-fast or fill in the missing pieces.

```

### test-harness/archetypes/partial-protocol/manifest.json

```text
{
  "name": "partial-protocol",
  "description": "Has .agent/config.json but no workflow YAMLs. Tests skills that detect a partial install.",
  "expected_discovery": {
    "agents_md_present": false,
    "claude_md_present": false,
    "ci_system": "none",
    "language": "unknown",
    "protocol_installed": true,
    "onboarding_started": false
  },
  "files": [
    "README.md",
    ".agent/config.json"
  ]
}

```

### test-harness/archetypes/protocol-installed-not-onboarded/.agent/config.json

```text
{"protocol_version": 1, "commands": {}}

```

### test-harness/archetypes/protocol-installed-not-onboarded/.github/workflows/batch-job-handler.yml

```text
# placeholder

```

### test-harness/archetypes/protocol-installed-not-onboarded/README.md

```text
# protocol-installed-not-onboarded

A repo with a full protocol install but no onboarding dialog file
on the well-known branch. Used to verify each skill detects the
"installed but not onboarded" state correctly.

```

### test-harness/archetypes/protocol-installed-not-onboarded/manifest.json

```text
{
  "name": "protocol-installed-not-onboarded",
  "description": "Full protocol install (.agent/config.json + workflow handler) but no onboarding dialog file. Tests the 'installed but not onboarded' detection.",
  "expected_discovery": {
    "agents_md_present": false,
    "claude_md_present": false,
    "ci_system": "github-actions",
    "language": "python",
    "protocol_installed": true,
    "onboarding_started": false
  },
  "files": [
    "README.md",
    ".agent/config.json",
    ".github/workflows/batch-job-handler.yml",
    "tests/__init__.py"
  ]
}

```

### test-harness/archetypes/protocol-installed-not-onboarded/tests/__init__.py

```text

```

### test-harness/archetypes/python-gha-with-agents-md/.github/workflows/ci.yml

```text
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest
      - run: pytest -q

```

### test-harness/archetypes/python-gha-with-agents-md/AGENTS.md

```text
# AGENTS.md

Agent contributors: read this file and the linked policy docs before
making changes.

- Style: PEP 8.
- Tests: `pytest -q`.
- CI: GitHub Actions runs `pytest` on every push and pull request.

This is a small AGENTS.md used as a fixture for the test harness.

```

### test-harness/archetypes/python-gha-with-agents-md/CLAUDE.md

```text
# CLAUDE.md

Claude-specific guidance for this fixture repo. Read AGENTS.md first.

This is a small CLAUDE.md used as a fixture for the test harness.

```

### test-harness/archetypes/python-gha-with-agents-md/README.md

```text
# python-gha-with-agents-md

A Python project archetype with AGENTS.md, CLAUDE.md, and GitHub
Actions CI running pytest. Used to test the "ideal adoption target"
case for the protocol skills.

```

### test-harness/archetypes/python-gha-with-agents-md/manifest.json

```text
{
  "name": "python-gha-with-agents-md",
  "description": "Python project with AGENTS.md, CLAUDE.md, and a minimal GitHub Actions pytest workflow. The ideal adoption target.",
  "expected_discovery": {
    "agents_md_present": true,
    "claude_md_present": true,
    "ci_system": "github-actions",
    "language": "python",
    "protocol_installed": false,
    "onboarding_started": false
  },
  "files": [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".github/workflows/ci.yml",
    "pyproject.toml",
    "tests/__init__.py"
  ]
}

```

### test-harness/archetypes/python-gha-with-agents-md/pyproject.toml

```text
[project]
name = "python-gha-fixture"
version = "0.0.1"
description = "Fixture repo for the test-harness skill."
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]

```

### test-harness/archetypes/python-gha-with-agents-md/tests/__init__.py

```text

```

### test-harness/lib/__init__.py

```text
"""Helpers for the test-harness development-only skill."""

```

### test-harness/lib/archetype_loader.py

```text
"""Load and materialise archetype fixture trees for the test-harness.

An archetype is a directory under ``test-harness/archetypes/<name>/``
holding a ``manifest.json`` plus the actual fixture files listed in
``manifest["files"]``. The loader knows nothing about scenarios; it
only knows how to (a) read a manifest and (b) copy a tree.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


ARCHETYPES_DIR_NAME = "archetypes"


def _archetypes_root(harness_root: Path | None = None) -> Path:
    """Return the absolute path to the archetypes directory.

    ``harness_root`` defaults to the directory containing this file's
    parent (i.e. ``test-harness/``).
    """
    if harness_root is None:
        harness_root = Path(__file__).resolve().parent.parent
    return harness_root / ARCHETYPES_DIR_NAME


def load(name: str, harness_root: Path | None = None) -> dict[str, Any]:
    """Load the manifest for archetype ``name``.

    Returns the parsed manifest dict. Raises :class:`FileNotFoundError`
    if the archetype directory or its manifest is missing, and
    :class:`ValueError` if the manifest is missing required keys.

    Contract:
      - Manifest must have keys: ``name``, ``description``,
        ``expected_discovery``, ``files``.
      - ``manifest["name"]`` must equal ``name``.
    """
    root = _archetypes_root(harness_root)
    archetype_dir = root / name
    manifest_path = archetype_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"archetype manifest not found: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as fp:
        manifest = json.load(fp)
    required = {"name", "description", "expected_discovery", "files"}
    missing = required - set(manifest)
    if missing:
        raise ValueError(
            f"archetype {name!r} manifest missing required keys: {sorted(missing)}"
        )
    if manifest["name"] != name:
        raise ValueError(
            f"archetype manifest name {manifest['name']!r} does not match "
            f"directory name {name!r}"
        )
    return manifest


def list_archetypes(harness_root: Path | None = None) -> list[str]:
    """Return the sorted list of archetype names available on disk."""
    root = _archetypes_root(harness_root)
    if not root.is_dir():
        return []
    return sorted(
        p.name for p in root.iterdir()
        if p.is_dir() and (p / "manifest.json").is_file()
    )


def materialise(
    name: str,
    target_dir: Path,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Copy archetype ``name`` into ``target_dir``.

    The archetype's ``manifest.json`` is *not* copied — only the files
    listed in ``manifest["files"]``. The target directory is created
    if it does not exist. Existing files at the target paths are
    overwritten.

    Returns the manifest dict so callers can inspect
    ``expected_discovery`` without a second load.
    """
    manifest = load(name, harness_root=harness_root)
    src_root = _archetypes_root(harness_root) / name
    target_dir.mkdir(parents=True, exist_ok=True)
    for rel in manifest["files"]:
        src = src_root / rel
        dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.is_file():
            raise FileNotFoundError(
                f"archetype {name!r} declares {rel!r} but file is missing at {src}"
            )
        shutil.copy2(src, dst)
    return manifest


__all__ = ["load", "list_archetypes", "materialise"]

```

### test-harness/lib/assertions.py

```text
"""Pure assertions used by scenarios in the test-harness.

These mirror the spirit of ``harness/lib/asserts.py`` in the POC but
target the development-only harness's needs: archetype-shape
verification, dialog-file inspection, scenario phase post-conditions.

Each ``assert_*`` helper raises :class:`HarnessAssertionError` (a
subclass of :class:`AssertionError`) on failure so pytest treats it
as a regular assertion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class HarnessAssertionError(AssertionError):
    """Raised when a harness predicate fails."""


def assert_file_exists(path: Path) -> None:
    """Raise if ``path`` does not exist as a regular file."""
    if not path.is_file():
        raise HarnessAssertionError(f"expected file does not exist: {path}")


def assert_file_absent(path: Path) -> None:
    """Raise if ``path`` exists."""
    if path.exists():
        raise HarnessAssertionError(f"expected file to be absent: {path}")


def assert_yaml_parses(path: Path) -> Any:
    """Parse ``path`` as YAML; raise if it does not parse."""
    assert_file_exists(path)
    try:
        with path.open("r", encoding="utf-8") as fp:
            return yaml.safe_load(fp)
    except yaml.YAMLError as exc:
        raise HarnessAssertionError(f"YAML parse failed for {path}: {exc}") from exc


def assert_json_parses(path: Path) -> Any:
    """Parse ``path`` as JSON; raise if it does not parse."""
    assert_file_exists(path)
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError as exc:
        raise HarnessAssertionError(f"JSON parse failed for {path}: {exc}") from exc


def assert_dialog_questions_answered_count(
    dialog_path: Path,
    expected_count: int,
) -> None:
    """Assert the dialog file at ``dialog_path`` has exactly ``expected_count``
    answered questions.

    A "question" is identified by an ``H3 (###)`` heading; an "answered"
    question is one whose section contains at least one non-empty
    response body line. This is a deliberately loose definition — the
    real onboarding skill will provide a stricter parser; scenarios use
    this stub to verify rough counts.
    """
    assert_file_exists(dialog_path)
    text = dialog_path.read_text(encoding="utf-8")
    answered = 0
    in_section = False
    has_answer = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_section and has_answer:
                answered += 1
            in_section = True
            has_answer = False
            continue
        if in_section and stripped and not stripped.startswith("#"):
            has_answer = True
    if in_section and has_answer:
        answered += 1
    if answered != expected_count:
        raise HarnessAssertionError(
            f"dialog {dialog_path}: expected {expected_count} answered "
            f"questions, found {answered}"
        )


def assert_dialog_questions_answered_at_least(
    dialog_path: Path,
    minimum: int,
) -> None:
    """Like :func:`assert_dialog_questions_answered_count` but requires
    at least ``minimum`` answered questions."""
    assert_file_exists(dialog_path)
    text = dialog_path.read_text(encoding="utf-8")
    answered = 0
    in_section = False
    has_answer = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_section and has_answer:
                answered += 1
            in_section = True
            has_answer = False
            continue
        if in_section and stripped and not stripped.startswith("#"):
            has_answer = True
    if in_section and has_answer:
        answered += 1
    if answered < minimum:
        raise HarnessAssertionError(
            f"dialog {dialog_path}: expected at least {minimum} answered "
            f"questions, found {answered}"
        )


def assert_directory_contains(parent: Path, relative: str) -> None:
    """Assert ``parent / relative`` exists (file or directory)."""
    candidate = parent / relative
    if not candidate.exists():
        raise HarnessAssertionError(f"missing entry {relative!r} under {parent}")


def assert_keys_present(payload: dict[str, Any], keys: list[str]) -> None:
    """Assert every key in ``keys`` is present in ``payload``."""
    if not isinstance(payload, dict):
        raise HarnessAssertionError(f"expected dict, got {type(payload).__name__}")
    missing = [k for k in keys if k not in payload]
    if missing:
        raise HarnessAssertionError(f"missing keys {missing} in payload")


__all__ = [
    "HarnessAssertionError",
    "assert_dialog_questions_answered_at_least",
    "assert_dialog_questions_answered_count",
    "assert_directory_contains",
    "assert_file_absent",
    "assert_file_exists",
    "assert_json_parses",
    "assert_keys_present",
    "assert_yaml_parses",
]

```

### test-harness/lib/scenario_runner.py

```text
"""Drive a scenario through its phases, persisting state at each step.

The runner is intentionally minimal in this bootstrap copy: it knows
how to parse a scenario YAML, advance one phase, and inspect current
state. Actual phase implementations live in the new repo's harness
extensions (or are dispatched to the skill under test).
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import yaml

from . import state as _state


VALID_TARGETS = frozenset({"synthetic-fixture", "live-new-repo"})
VALID_SKILLS = frozenset(
    {
        "batch-job",
        "task-dag",
        "orchestrate-issue",
        "onboarding",
        "composition-guide",
    }
)


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_scenario(scenario_path: Path) -> dict[str, Any]:
    """Read and validate a scenario YAML.

    Validates:
      - ``scenario_id`` is a non-empty string
      - ``archetype`` is a non-empty string
      - ``skill_under_test`` is one of :data:`VALID_SKILLS`
      - ``target`` (if present) is one of :data:`VALID_TARGETS`
      - ``phases`` is a list of >=2 dicts with unique ``name``s
    """
    with scenario_path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"scenario {scenario_path} is not a YAML mapping")
    for key in ("scenario_id", "archetype", "skill_under_test", "phases"):
        if key not in data:
            raise ValueError(f"scenario {scenario_path} missing key {key!r}")
    if data["skill_under_test"] not in VALID_SKILLS:
        raise ValueError(
            f"scenario {scenario_path}: skill_under_test "
            f"{data['skill_under_test']!r} is not one of {sorted(VALID_SKILLS)}"
        )
    target = data.get("target", "synthetic-fixture")
    if target not in VALID_TARGETS:
        raise ValueError(
            f"scenario {scenario_path}: target {target!r} is not one of "
            f"{sorted(VALID_TARGETS)}"
        )
    phases = data["phases"]
    if not isinstance(phases, list) or len(phases) < 2:
        raise ValueError(
            f"scenario {scenario_path}: phases must be a list of >=2 items"
        )
    names = [p.get("name") for p in phases]
    if len(set(names)) != len(names):
        raise ValueError(
            f"scenario {scenario_path}: phase names must be unique; got {names}"
        )
    return data


def _initial_state(scenario: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Build the initial state dict for a fresh run of ``scenario``."""
    return {
        "run_id": run_id,
        "scenario_id": scenario["scenario_id"],
        "archetype": scenario["archetype"],
        "skill_under_test": scenario["skill_under_test"],
        "target": scenario.get("target", "synthetic-fixture"),
        "phases": [
            {"name": p["name"], "status": "pending"} for p in scenario["phases"]
        ],
        "diagnostics": {},
        "created_at": _utc_now_iso(),
    }


def run(scenario_path: Path, state_dir: Path, run_id: str) -> dict[str, Any]:
    """Initialise a fresh run of ``scenario_path`` under ``state_dir``.

    This is the ``setup`` entry point. It:
      1. Parses and validates the scenario YAML.
      2. Builds the initial state dict.
      3. Persists state.json.
      4. Returns the state dict.

    It does *not* execute any phases — callers invoke :func:`step` to
    advance.
    """
    scenario = _parse_scenario(scenario_path)
    initial = _initial_state(scenario, run_id)
    _state.save_state(state_dir, initial)
    return initial


def step(state_dir: Path) -> dict[str, Any]:
    """Advance the run in ``state_dir`` by one phase.

    Reads the current state, marks the first non-terminal phase as
    ``in_progress``, persists, then (in this stub) immediately marks
    it ``done`` and persists again. Real phase execution is delegated
    to the skill under test in the new repo; this stub exists so the
    Python package imports cleanly and the contract tests can run.

    Returns the updated state dict.
    """
    data = _state.load_state(state_dir)
    phases = data.get("phases", [])
    for phase in phases:
        if phase.get("status") in ("done", "skipped"):
            continue
        if phase.get("status") == "in_progress":
            phase["status"] = "done"
            phase["finished_at"] = _utc_now_iso()
            _state.save_state(state_dir, data)
            return data
        phase["status"] = "in_progress"
        phase["started_at"] = _utc_now_iso()
        _state.save_state(state_dir, data)
        phase["status"] = "done"
        phase["finished_at"] = _utc_now_iso()
        _state.save_state(state_dir, data)
        return data
    return data


def inspect(state_dir: Path) -> dict[str, Any]:
    """Return the current state dict from ``state_dir`` without mutating it."""
    return _state.load_state(state_dir)


__all__ = ["VALID_SKILLS", "VALID_TARGETS", "inspect", "run", "step"]

```

### test-harness/lib/state.py

```text
"""State persistence and console-block rendering for the test-harness.

State is a plain dict written to ``harness/runs/<run_id>/state.json``
after every phase. The shape is described in ``SKILL.md``. This module
performs the I/O and the human-facing state-block rendering only — it
does not interpret phases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATE_FILENAME = "state.json"

VALID_PHASE_STATUSES = frozenset(
    {"pending", "ready", "in_progress", "done", "failed", "skipped"}
)


def state_path(run_dir: Path) -> Path:
    """Return the canonical state.json path under ``run_dir``."""
    return run_dir / STATE_FILENAME


def load_state(run_dir: Path) -> dict[str, Any]:
    """Load and return the state dict for ``run_dir``.

    Raises :class:`FileNotFoundError` if the state file is missing.
    Raises :class:`ValueError` if the loaded payload is not a dict.
    """
    path = state_path(run_dir)
    if not path.is_file():
        raise FileNotFoundError(f"state file not found: {path}")
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"state at {path} is not a JSON object")
    return data


def save_state(run_dir: Path, data: dict[str, Any]) -> Path:
    """Write ``data`` to ``state.json`` under ``run_dir`` atomically.

    The run directory is created if missing. Writes go to a sibling
    ``state.json.tmp`` first then ``os.replace`` to the final path so
    a partial write never corrupts the persisted state.

    Returns the final state-file path.
    """
    if not isinstance(data, dict):
        raise TypeError("state data must be a dict")
    run_dir.mkdir(parents=True, exist_ok=True)
    final = state_path(run_dir)
    tmp = final.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=False)
        fp.write("\n")
    tmp.replace(final)
    return final


def _current_phase_index(state: dict[str, Any]) -> int:
    """Return 1-based index of the first phase that is not done/skipped.

    Returns ``len(phases)`` (1-based) if all phases are terminal.
    """
    phases = state.get("phases", [])
    for i, phase in enumerate(phases, start=1):
        if phase.get("status") not in ("done", "skipped"):
            return i
    return max(1, len(phases))


def write_state_block_console(state: dict[str, Any]) -> str:
    """Render the canonical state block for ``state``.

    Returns the rendered string (multi-line). The caller is
    responsible for actually printing it. The block format is:

      [test-harness * scenario: <id> * phase i/n (<name>)]
        <phase>: <status>  (<detail>)
        ...
      Next: <next-action>

    where "*" stands for a bullet character.
    """
    scenario_id = state.get("scenario_id", "<unknown>")
    phases = state.get("phases", [])
    total = max(1, len(phases))
    idx = _current_phase_index(state)
    current_name = phases[idx - 1]["name"] if phases else "<none>"

    bullet = "•"
    header = (
        f"[test-harness {bullet} scenario: {scenario_id} {bullet} "
        f"phase {idx}/{total} ({current_name})]"
    )
    lines = [header]
    width = max((len(p.get("name", "")) for p in phases), default=0)
    for phase in phases:
        name = phase.get("name", "<noname>")
        status = phase.get("status", "pending")
        detail = phase.get("detail", "")
        padded_name = f"{name}:".ljust(width + 2)
        if detail:
            lines.append(f"  {padded_name}{status:<10}({detail})")
        else:
            lines.append(f"  {padded_name}{status}")
    nxt = state.get("next_hint") or _default_next_hint(state, idx)
    lines.append(f"Next: {nxt}")
    return "\n".join(lines)


def _default_next_hint(state: dict[str, Any], idx: int) -> str:
    """Compute a reasonable Next: hint from state when none is stored."""
    phases = state.get("phases", [])
    if not phases:
        return "no phases declared; check scenario YAML"
    if idx > len(phases):
        return "scenario complete; run `report` to render report.md"
    current = phases[idx - 1]
    name = current.get("name", "<noname>")
    status = current.get("status", "pending")
    if status == "in_progress":
        return f"resume phase {name!r}"
    return f"run phase {name!r}"


__all__ = [
    "VALID_PHASE_STATUSES",
    "load_state",
    "save_state",
    "state_path",
    "write_state_block_console",
]

```

### test-harness/scenarios/batch-job-branch-sha-mismatch.yml

```text
scenario_id: batch-job-branch-sha-mismatch
archetype: python-gha-with-agents-md
skill_under_test: batch-job
target: synthetic-fixture
phases:
  - name: setup
    inputs:
      create_issue: true
      create_branch: true
    expected:
      issue_number_present: true
      branch_created: true

  - name: invoke
    inputs:
      command: echo
      args: {message: "stale"}
      commit_sha: "0000000000000000000000000000000000000000"
    expected:
      batch_job_comment_present: true

  - name: verify
    expected:
      envelope_run_status: error
      error_kind: sha_mismatch

```

### test-harness/scenarios/batch-job-happy-path.yml

```text
scenario_id: batch-job-happy-path
archetype: python-gha-with-agents-md
skill_under_test: batch-job
target: live-new-repo
phases:
  - name: setup
    inputs:
      create_issue: true
      issue_labels: [agent-task]
    expected:
      repo_created: true
      issue_number_present: true

  - name: invoke
    inputs:
      command: echo
      args:
        message: "hello from the harness"
    expected:
      batch_job_comment_present: true
      envelope_run_status: completed

  - name: verify
    expected:
      envelope_run_status: completed
      error_kind_absent: true
      summary_keys_present: [stdout]

```

### test-harness/scenarios/batch-job-parse-error.yml

```text
scenario_id: batch-job-parse-error
archetype: python-gha-with-agents-md
skill_under_test: batch-job
target: synthetic-fixture
phases:
  - name: setup
    inputs:
      create_issue: true
    expected:
      issue_number_present: true

  - name: invoke
    inputs:
      command: echo
      malformed_envelope: true
    expected:
      batch_job_comment_present: true

  - name: verify
    expected:
      envelope_run_status: parse_error
      error_kind: invalid_envelope

```

### test-harness/scenarios/batch-job-runner-pickup-timeout.yml

```text
scenario_id: batch-job-runner-pickup-timeout
archetype: python-gha-with-agents-md
skill_under_test: batch-job
target: synthetic-fixture
phases:
  - name: setup
    inputs:
      create_issue: true
    expected:
      issue_number_present: true

  - name: invoke
    inputs:
      command: nonexistent-command
      poll_timeout_s: 5
    expected:
      batch_job_comment_present: true

  - name: verify
    expected:
      envelope_run_status: error
      error_kind: pickup_timeout

```

### test-harness/scenarios/composition-guide-render.yml

```text
scenario_id: composition-guide-render
archetype: blank-repo
skill_under_test: composition-guide
target: synthetic-fixture
phases:
  - name: render
    inputs:
      source: .claude/skills/composition-guide/SKILL.md
    expected:
      markdown_renders: true
      frontmatter_parses: true

  - name: lint
    expected:
      no_broken_internal_links: true
      no_broken_external_links: true
      all_referenced_skills_exist:
        - batch-job
        - task-dag
        - orchestrate-issue
        - onboarding

```

### test-harness/scenarios/multi-scenario-soak.yml

```text
scenario_id: multi-scenario-soak
archetype: python-gha-with-agents-md
skill_under_test: orchestrate-issue
target: live-new-repo
phases:
  - name: setup
    inputs:
      create_issues: 3
      issue_bodies:
        - "instructions_inline: helper A"
        - "instructions_inline: helper B"
        - "instructions_inline: helper C"
    expected:
      issue_numbers_present_count: 3

  - name: fanout
    inputs:
      parallel_orchestrators: 3
      max_parallel_per_run: 2
    expected:
      orchestrators_running: 3
      no_shared_branch_names: true

  - name: merge
    expected:
      all_orchestrators_completed: true
      prs_opened_count: 3

  - name: verify
    expected:
      prs_merged_count: 3
      no_cross_contamination: true
      no_shared_run_dirs: true

```

### test-harness/scenarios/onboarding-blank-repo.yml

```text
scenario_id: onboarding-blank-repo
archetype: blank-repo
skill_under_test: onboarding
target: live-new-repo
phases:
  - name: detect
    expected:
      protocol_installed: false
      onboarding_started: false
      agents_md_present: false

  - name: interview
    inputs:
      scripted_answers:
        intent: "tests the onboarding skill"
        problems: "validation"
        adoption: "full"
    expected:
      dialog_file_present: true
      questions_answered: 22

  - name: recommend
    expected:
      recommendations_file_present: true
      no_agents_md_edits_proposed: true

  - name: apply
    inputs:
      approve_all: true
    expected:
      pointer_added_to_agents_md: true
      protocol_templates_installed: true

  - name: verify
    expected:
      meta_status: onboarded
      dialog_file_committed: true

```

### test-harness/scenarios/onboarding-decline.yml

```text
scenario_id: onboarding-decline
archetype: blank-repo
skill_under_test: onboarding
target: synthetic-fixture
phases:
  - name: detect
    expected:
      protocol_installed: false
      onboarding_started: false

  - name: interview
    inputs:
      scripted_answers:
        decline: true
    expected:
      decline_acknowledged: true

  - name: verify
    expected:
      dialog_file_present: false
      recommendations_file_present: false
      agents_md_present: false
      no_state_written: true

```

### test-harness/scenarios/onboarding-existing-agents-md.yml

```text
scenario_id: onboarding-existing-agents-md
archetype: python-gha-with-agents-md
skill_under_test: onboarding
target: synthetic-fixture
phases:
  - name: detect
    expected:
      protocol_installed: false
      onboarding_started: false
      agents_md_present: true
      claude_md_present: true

  - name: interview
    inputs:
      scripted_answers:
        intent: "augment existing AGENTS.md"
        problems: "reduce friction"
        adoption: "pointer-only"
    expected:
      dialog_file_present: true
      questions_answered_min: 12

  - name: recommend
    expected:
      recommendations_file_present: true
      no_agents_md_edits_proposed: true
      pointer_edit_proposed: true

  - name: apply
    inputs:
      approve_all: true
    expected:
      pointer_added_to_agents_md: true
      agents_md_body_unchanged: true

  - name: verify
    expected:
      meta_status: onboarded
      claude_md_body_unchanged: true

```

### test-harness/scenarios/onboarding-resume-mid-interview.yml

```text
scenario_id: onboarding-resume-mid-interview
archetype: blank-repo
skill_under_test: onboarding
target: synthetic-fixture
phases:
  - name: setup
    inputs:
      preexisting_dialog_questions_answered: 13
    expected:
      dialog_file_present: true
      questions_answered: 13

  - name: detect
    expected:
      onboarding_started: true
      resume_point_index: 14

  - name: interview
    inputs:
      mode: resume
      scripted_answers_from: 14
    expected:
      questions_answered: 22
      no_questions_re_asked: true

  - name: recommend
    expected:
      recommendations_file_present: true

  - name: verify
    expected:
      meta_status: onboarded

```

### test-harness/scenarios/onboarding-revise.yml

```text
scenario_id: onboarding-revise
archetype: python-gha-with-agents-md
skill_under_test: onboarding
target: synthetic-fixture
phases:
  - name: setup
    inputs:
      preexisting_dialog_complete: true
      preexisting_recommendations_applied: true
    expected:
      dialog_file_present: true
      recommendations_file_present: true

  - name: detect
    expected:
      protocol_installed: true
      onboarding_started: true
      revise_offered: true

  - name: interview
    inputs:
      mode: revise
      scripted_answers:
        change_integration: "switch from pointer-only to full"
    expected:
      dialog_revision_recorded: true

  - name: recommend
    expected:
      recommendations_diff_present: true

  - name: apply
    inputs:
      approve_all: true
    expected:
      revised_integration_applied: true

  - name: verify
    expected:
      meta_status: onboarded
      revision_count: 1

```

### test-harness/scenarios/orchestrate-issue-parallel-fanout.yml

```text
scenario_id: orchestrate-issue-parallel-fanout
archetype: python-gha-with-agents-md
skill_under_test: orchestrate-issue
target: live-new-repo
phases:
  - name: setup
    inputs:
      create_issue: true
      issue_body: "instructions_inline: implement three independent helpers"
    expected:
      issue_number_present: true

  - name: claim
    inputs:
      agent_id: "orchestrate-parallel-agent"
    expected:
      issue_locked: true

  - name: fanout
    inputs:
      max_parallel: 3
      planned_subagents: 3
    expected:
      subagents_dispatched: 3
      subagent_branches_created: 3

  - name: merge
    inputs:
      merge_order: plan
    expected:
      feature_branch_advanced: true
      pr_opened: true

  - name: verify
    expected:
      pr_merged: true
      meta_status: shipped
      no_cross_contamination: true

```

### test-harness/scenarios/orchestrate-issue-restart-recovery.yml

```text
scenario_id: orchestrate-issue-restart-recovery
archetype: python-gha-with-agents-md
skill_under_test: orchestrate-issue
target: live-new-repo
phases:
  - name: setup
    inputs:
      create_issue: true
      issue_body: "instructions_inline: implement two helpers"
    expected:
      issue_number_present: true

  - name: fanout
    inputs:
      max_parallel: 2
      planned_subagents: 2
      kill_after_dispatch: true
    expected:
      subagents_dispatched: 2
      orchestrator_killed_mid_fanout: true

  - name: restart
    inputs:
      resume_run_id: "<from-state>"
    expected:
      restart_acknowledged: true
      no_duplicate_dispatch: true

  - name: finalise
    expected:
      pr_opened: true

  - name: verify
    expected:
      pr_merged: true
      meta_status: shipped

```

### test-harness/scenarios/orchestrate-issue-single-subagent.yml

```text
scenario_id: orchestrate-issue-single-subagent
archetype: python-gha-with-agents-md
skill_under_test: orchestrate-issue
target: live-new-repo
phases:
  - name: setup
    inputs:
      create_issue: true
      issue_body: "instructions_inline: add a single trivial change"
    expected:
      issue_number_present: true

  - name: claim
    inputs:
      agent_id: "orchestrate-single-agent"
    expected:
      issue_locked: true

  - name: fanout
    inputs:
      max_parallel: 1
    expected:
      subagents_dispatched: 1

  - name: merge
    expected:
      feature_branch_advanced: true
      pr_opened: true

  - name: verify
    expected:
      pr_merged: true
      meta_status: shipped

```

### test-harness/scenarios/protocol-installed-not-onboarded.yml

```text
scenario_id: protocol-installed-not-onboarded
archetype: protocol-installed-not-onboarded
skill_under_test: onboarding
target: live-new-repo
phases:
  - name: detect
    expected:
      protocol_installed: true
      onboarding_started: false
      installed_but_not_onboarded: true

  - name: interview
    inputs:
      scripted_answers:
        intent: "complete the onboarding for an already-installed protocol"
        adoption: "full"
    expected:
      dialog_file_present: true
      questions_answered_min: 12

  - name: recommend
    expected:
      recommendations_file_present: true
      install_step_skipped: true

  - name: apply
    inputs:
      approve_all: true
    expected:
      pointer_added_to_agents_md: false
      onboarding_marker_set: true

  - name: verify
    expected:
      meta_status: onboarded
      protocol_install_unchanged: true

```

### test-harness/scenarios/task-dag-claim-and-plan.yml

```text
scenario_id: task-dag-claim-and-plan
archetype: python-gha-with-agents-md
skill_under_test: task-dag
target: live-new-repo
phases:
  - name: setup
    inputs:
      create_issue: true
      issue_body: "instructions_inline: write a hello world test"
    expected:
      issue_number_present: true

  - name: claim
    inputs:
      agent_id: "harness-agent-claim"
    expected:
      issue_locked: true
      issue_has_label: agent-task-claimed

  - name: plan
    expected:
      brief_present: true
      subagent_plan_count_min: 1

  - name: verify
    expected:
      meta_status: planned

```

### test-harness/scenarios/task-dag-merge-conflicts.yml

```text
scenario_id: task-dag-merge-conflicts
archetype: python-gha-with-agents-md
skill_under_test: task-dag
target: synthetic-fixture
phases:
  - name: setup
    inputs:
      create_issue: true
      create_subagent_branches:
        - id: sub-01
          touches: [shared.py]
        - id: sub-02
          touches: [shared.py]
    expected:
      issue_number_present: true
      subagent_branches_created: 2

  - name: merge
    inputs:
      conflict_strategy: fail
    expected:
      merge_attempted: true
      merge_failed: true
      conflict_paths_present: [shared.py]

  - name: verify
    expected:
      meta_status: merge_failed
      diagnostics_has_conflict_report: true

```

### test-harness/scenarios/task-dag-stale-takeover.yml

```text
scenario_id: task-dag-stale-takeover
archetype: python-gha-with-agents-md
skill_under_test: task-dag
target: synthetic-fixture
phases:
  - name: setup
    inputs:
      create_issue: true
      pre_lock_with_agent_id: "stale-agent-001"
      stale_age_minutes: 120
    expected:
      issue_number_present: true
      issue_locked: true

  - name: claim
    inputs:
      agent_id: "fresh-takeover-agent"
    expected:
      claim_succeeded: true
      previous_agent_evicted: true

  - name: verify
    expected:
      meta_status: claimed
      meta_agent_id: "fresh-takeover-agent"

```
