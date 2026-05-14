# RESUME — handoff prompt for continuing this work

Status: durable handoff document.
Audience: future-you (or another agent) picking this work back up.

## What this is

A copy-pasteable prompt + context for the next Claude Code session
that should continue building the `pipeline-skills-package` bootstrap
bundle. The prompt is self-contained — paste it into a new session
and the agent has enough context to start.

## State of the work

As of the planning session that produced this directory
(`pipeline-skills-package/`):

- **All design specs are written.** `OVERVIEW.md`, `SPEC-PACKAGE.md`,
  per-skill SPECs, `test-harness/SPEC.md`, `PLAN-PACKAGE.md`,
  `TESTING-IN-POC.md`, `NEW-REPO-PLAN.md`, `bootstrap/install.md`,
  and this file are all in place.
- **No implementation has happened.** The skill packages contain only
  `SPEC.md` files. No `SKILL.md`, no `templates/`, no `lib/`, no
  archetypes, no scenarios, no runners.
- **The bootstrap build script does not yet exist.**
  `bootstrap/build.py` is referenced in the specs but has not been
  written.
- **No contract tests under `tests/distribution/` exist yet.**

## Where to continue

The natural next step is to execute `PLAN-PACKAGE.md` Phase 0 through
Phase 6. That plan is designed for **overnight, unattended, parallel
execution**.

## Prompt to give a new agent session

Copy and paste this into a fresh Claude Code session in the
`poc-github-ai-sandbox` repo (branch
`claude/assess-project-status-YBFY9`, or wherever this work has been
merged to):

```
Continue building the pipeline-skills-package bootstrap bundle.

State: all design specs are in pipeline-skills-package/ as of the
last commit on this branch. The implementation has not been started.

Your task: execute PLAN-PACKAGE.md from Phase 0 through Phase 6.
Run unattended (overnight) if I'm not present; otherwise run
interactively.

Read in this order:
  1. pipeline-skills-package/OVERVIEW.md          (3 min)
  2. pipeline-skills-package/SPEC-PACKAGE.md       (5 min)
  3. pipeline-skills-package/PLAN-PACKAGE.md       (10 min — this is your plan)
  4. pipeline-skills-package/TESTING-IN-POC.md     (5 min — Phase 4 spec)
  5. pipeline-skills-package/skills/<each>/SPEC.md (each ~5 min; needed before dispatching subagents in Phase 1)
  6. pipeline-skills-package/test-harness/SPEC.md  (skim — sub-06's reference)
  7. pipeline-skills-package/bootstrap/install.md  (skim — what the build produces)

Constraints (re-read these before each phase):
  - Do NOT modify the POC's .agent/, .github/workflows/, _agent_runs,
    existing tests/unit/, tests/e2e/, existing skills/batch-job/, or
    existing skills/task-dag/.
  - All new work stays under pipeline-skills-package/ plus tests/distribution/.
  - The contract test test_template_parity.py must pass — bundled
    templates byte-match POC source.
  - Subagent dispatches use isolation: "worktree" without exception.
  - Multi-subagent waves dispatch in a single message.
  - Conflicts in plan-order merge → abort, surface to me. Don't auto-resolve.

If you want unattended mode, set UNATTENDED=1 in state.json before
starting Phase 1 — that flag means failed subtasks get skipped and
recorded in the report rather than blocking the run.

When you finish all phases, the bundle will be at
pipeline-skills-package/bootstrap/dist/, the contract tests will be
green, and a run report will be at
pipeline-skills-package/runs/<run_id>/report.md.

The step after that (which I'll do later, manually) is to take the
bundle to a fresh pipeline-ai-sandbox repo and execute
NEW-REPO-PLAN.md there.
```

## Alternative entry points

### If you only want to build one skill at a time

Use the per-skill SPEC as a brief for a single subagent. Don't run
the full `PLAN-PACKAGE.md`. Useful when iterating on one skill before
committing to the full bundle.

```
Pick one skill from pipeline-skills-package/skills/<name>/SPEC.md.
Build only that skill's package per the SPEC. Don't touch other
skills' directories. Verify against tests/distribution/ contract
tests for that one skill.
```

### If the bundle is built and you want to ship to the new repo

```
The bundle is at pipeline-skills-package/bootstrap/dist/. Take
either install.md (recipe form) or pipeline-skills-package.tar.gz
(tarball form). Create a fresh GitHub repo named
pipeline-ai-sandbox. Clone it locally. Copy the bundle file in.

Tell a Claude Code agent in the new repo:
  "Read install.md at the repo root and follow it. After it
  reports SUCCESS, read NEW-REPO-PLAN.md and execute it."
```

### If the bundle in the new repo is partially set up

`NEW-REPO-PLAN.md`'s restart recovery section explains how to
resume. The same `runs/<run_id>/state.json` pattern applies.

## Glossary

- **POC repo**: `lago-morph/poc-github-ai-sandbox`. Where the protocol
  was prototyped. Stays preserved.
- **The package**: `pipeline-skills-package/` inside the POC repo.
  Everything new lives here.
- **The bundle**: the recipe + tarball at
  `pipeline-skills-package/bootstrap/dist/`. What gets copied into
  the new repo.
- **The new repo**: `<agent-account>/pipeline-ai-sandbox`. The
  maintenance project for ongoing skill development.
- **The 5 distributable skills**: batch-job, task-dag,
  orchestrate-issue, onboarding, composition-guide.
- **The test harness**: development-only skill that drives the 5
  distributable skills against synthetic + live scenarios. Bundled
  with the bootstrap, lives only in the new repo.

## Useful commands

| What | Command |
|---|---|
| Run full POC test suite | `python -m pytest tests/ -q --tb=short` |
| Run only distribution tests | `python -m pytest tests/distribution/ -v` |
| Verify template parity | `python -m pytest tests/distribution/test_template_parity.py -v` |
| See what changed since main | `git diff main --stat` |
| Resume the build plan | `cat pipeline-skills-package/runs/<run_id>/state.json` then read PLAN-PACKAGE.md "Restart recovery" |

## Provenance

This file was written in the same planning session that produced
the per-skill SPECs and the two plans. The state captured here is
accurate as of that session's last commit. Future sessions should
update this file if the state changes.
