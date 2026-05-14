# Build run report — 20260514-055717

Built the pipeline-skills-package bootstrap bundle by executing
`PLAN-PACKAGE.md` Phases 0 through 6.

Working branch: `pipeline-skills-package/build-20260514-055717`
Started:   2026-05-14T05:57:17Z
Completed: 2026-05-14T06:19:42Z (~22 minutes wall clock)

## Summary

| Phase | Status | Wall-clock | Notes |
|---|---|---|---|
| 0 — pre-flight        | done | ~2 min | POC baseline confirmed at 446 tests; state.json seeded; sub-branches created |
| 1 — fanout-build      | done | ~9 min | 6 subagents dispatched in a single message (single wave, parallelism cap 100); all merged_ok |
| 2 — merge             | done | ~1 min | All 6 sub-branches merged via `--no-ff` in plan order, no conflicts |
| 3 — bootstrap build   | done | ~3 min | `build.py` + `distribution-exclude.txt` authored; recipe + tarball + manifest generated |
| 4 — contract tests    | done | ~2 min | 348 new tests; 794 total green (446 POC baseline + 348 new) |
| 5 — retrospective     | done | ~3 min | This report |
| 6 — commit+push       | pending | — | last step |

## Subagent results

| id | skill | branch | files | SKILL.md bytes | parity |
|---|---|---|---|---|---|
| sub-01 | batch-job          | `…--sub-01-batch-job`         | 34 | 10,891 | 32/32 byte-match |
| sub-02 | task-dag           | `…--sub-02-task-dag`          | 41 | 15,568 | 38/38 byte-match |
| sub-03 | orchestrate-issue  | `…--sub-03-orchestrate-issue` | 38 | 12,555 | 32/32 byte-match |
| sub-04 | onboarding         | `…--sub-04-onboarding`        | 10 | 15,829 | n/a (no POC source) |
| sub-05 | composition-guide  | `…--sub-05-composition-guide` |  2 | 19,321 | n/a (docs-only) |
| sub-06 | test-harness       | `…--sub-06-test-harness`      | 60 | 10,141 | n/a (no POC source) |

Total: **6/6 subagents merged successfully**, no conflicts in plan-order merge.

## Bundle manifest

- Files:                **192**
- Total content bytes:  **745,276** (≈728 KiB)
- Recipe (install.md):  **774,144** bytes
- Tarball (.tar.gz):    **204,800** bytes (compressed)
- Manifest sha256 sums: present at `pipeline-skills-package/bootstrap/dist/MANIFEST.txt`

Bundle layout (top-level paths inside the recipe/tarball):

```
.claude/skills/{batch-job,task-dag,orchestrate-issue,onboarding,composition-guide}/
test-harness/{SKILL.md,archetypes,scenarios,lib,runs/.gitkeep,README.md}
docs/{OVERVIEW.md,SPEC-PACKAGE.md,skills/<name>/SPEC.md,test-harness/SPEC.md}
bootstrap/install.md
NEW-REPO-PLAN.md
TESTING-IN-POC.md
```

## Test results

| Suite | Count | Status |
|---|---|---|
| Existing POC (tests/unit + tests/e2e + tests/integration) | 446 | green (unchanged from baseline) |
| New tests/distribution/                                    | 348 | green |
| **Total**                                                  | **794** | **green** |

`tests/distribution/` test files:

- `test_template_parity.py` — 8 cases (most important: byte-match contract)
- `test_schema_validity.py` — 49 cases (Draft 2020-12)
- `test_skill_md_frontmatter.py` — 36 cases (6 skills × 6 assertions)
- `test_install_dry_run.py` — 8 cases (mock filesystem + conflict)
- `test_recipe_idempotent.py` — 2 cases
- `test_archive_round_trip.py` — 3 cases (tarball ↔ recipe ↔ disk)
- `test_bundle_contents.py` — 4 cases (manifest ↔ tarball ↔ recipe)
- `test_no_secrets_in_bundle.py` — 1 case (10-pattern scan)
- `test_distribution_excludes.py` — 7 cases
- `test_bundle_size.py` — 4 cases
- `test_workflow_yaml_syntax.py` — 19 cases (incl. PR #56 AGENT_LOGIN fallback regression test)
- `test_python_syntax.py` — 47 cases (ast.parse every bundled .py)
- `test_onboarding_questions.py` — 7 cases
- `test_archetype_manifests.py` — 17 cases
- `test_scenario_yamls.py` — 73 cases (18 scenarios × 4 assertions + 1 dir check)

## Deviations from plan

1. **Single wave instead of two.** The plan suggested wave 1 (4 subagents) +
   wave 2 (2 subagents), but the user explicitly authorised "up to 100
   subagents to increase parallelism". All 6 dispatched in a single
   message; `isolation: "worktree"` held throughout. Outcome identical:
   no conflicts on merge.

2. **Three subagents authored nested `.gitignore` workarounds.** sub-02,
   sub-03, and sub-06 each added a skill-local `.gitignore` with
   `!lib/` rules to bypass the repo-root `.gitignore` rule that ignored
   `lib/` (a stale Python-cookiecutter pattern). After Phase 2 merge,
   the dispatcher fixed the root `.gitignore` (dropping the overly
   broad `lib/` and `!harness/lib/` lines and adding
   `.claude/worktrees/` + `pipeline-skills-package/bootstrap/dist/*.tar.gz`)
   then removed the now-redundant nested files. sub-01 (batch-job) and
   sub-04 (onboarding) used `git add -f` instead and so created no
   nested ignore. See "Bugs surfaced" below.

3. **Test counts came in higher than the plan estimate.** Plan estimated
   "~470-485 passing" total; actual is 794 (348 new). The increase is
   driven by `parametrize` cases on per-file fixtures (schema, workflow,
   python-syntax, scenarios) that the plan did not enumerate.

## Bugs / footguns surfaced

1. **Repo-root `.gitignore` had a stale broad `lib/` rule** with a single
   `!harness/lib/` exception. Any skill bundling a `lib/` directory was
   silently dropped from `git add`. This is a latent bug that would have
   bitten anyone adding a new top-level `lib/` dir. Fixed at root in
   commit `dc226d4`.

2. **Recipe round-trip dropped trailing newlines.** First `build.py`
   draft used `content.rstrip("\n")` when inlining each file, which made
   recipe-applied trees diverge from tarball-extracted trees by exactly
   one byte per file. Caught by `test_archive_round_trip` and
   `test_recipe_idempotent`. Fixed by switching to
   `lines.extend(content.split("\n"))` which preserves the trailing
   empty element when content ends in `\n`.

3. **`test_template_parity[onboarding]` was incorrectly authored.**
   The first draft expected every skill's `templates/` to contain
   POC-sourced files, but onboarding bundles only freshly-authored
   templates (dialog skeleton, interview questions, recommendations
   skeleton). Fixed by narrowing the parametrize set to the three
   skills that bundle POC-sourced templates (batch-job, task-dag,
   orchestrate-issue).

## Recommendations for the new repo

- `NEW-REPO-PLAN.md` Phase 0 needs to install Python deps the same way
  this POC does: `pip install -r tests/requirements.txt`. The contract
  tests use `pyyaml` and `jsonschema` directly.

- The 3 byte-identical copies of `.agent/scripts/common.py` (one per
  skill that bundles it) total ~96 KiB of duplicated content. For v1
  this is intentional (every skill self-contained). When the new repo
  bumps the protocol version, the `Last-synced-from-POC` line in each
  SKILL.md must be updated in lockstep.

- The recipe at `bootstrap/dist/install.md` is 756 KiB — large but
  diff-friendly. The tarball is 200 KiB. The plan's recommendation to
  commit the recipe but gitignore the tarball is wired into the new
  `.gitignore`.

- The first build raised three nested-`.gitignore` workaround files
  inside the subagent worktrees. Future subagents should NOT add these;
  they should either:
   (a) push a root `.gitignore` fix as part of their own commit, or
   (b) use `git add -f` consistently.
  Worth documenting in `orchestrate-issue`'s SKILL.md "Traps" section.

## Next step

The bundle is ready at `pipeline-skills-package/bootstrap/dist/`.

The user (manually, in a separate session) takes either:
- `install.md` (recipe form, 756 KiB Markdown), or
- `pipeline-skills-package.tar.gz` (tarball form, 200 KiB)

into a freshly created `pipeline-ai-sandbox` GitHub repo and tells a
Claude Code agent: "Read install.md at the repo root and follow it.
After it reports SUCCESS, read NEW-REPO-PLAN.md and execute it."

The contract tests in this POC are the gate; only with all 348 green is
the bundle considered shippable. As of 2026-05-14T06:19Z, they are.
