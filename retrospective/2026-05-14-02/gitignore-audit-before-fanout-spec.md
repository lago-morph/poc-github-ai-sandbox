# Spec: `gitignore-audit-before-fanout`

## Intent

Before a dispatcher fans out parallel subagents whose deliverables will
land at new top-level paths in the repo, audit the repo's `.gitignore`
(and any nested `.gitignore` files) for rules that could silently swallow
those paths — broad un-rooted directory names like `lib/`, `dist/`,
`build/`, `output/` are the usual culprits.

The session this skill was born from dispatched 6 subagents to build a
new family of distributable skill packages, each of which bundled a
`lib/` directory under `pipeline-skills-package/skills/<name>/`. The
repo's `.gitignore` had a single-line `lib/` rule (a stale
Python-cookiecutter convention) with one negation (`!harness/lib/`) for
a different POC use-case. The rule matched the new `lib/` dirs and
silently dropped them from `git add -A`.

Three of the six subagents (sub-02, sub-03, sub-06) independently
discovered this and invented the same workaround: a nested `.gitignore`
inside their skill dir with `!lib/` `!lib/**` to override the parent.
The other three (sub-01, sub-04, sub-05) used `git add -f` instead.

Result: two parallel mechanisms for the same problem, plus a cleanup
commit after merge to remove the redundant nested ignores. ~10 minutes
of avoidable rework + a confusing merge state. Auditing `.gitignore`
once at session start would have prevented all of it.

## Trigger

### Direct triggers — activate immediately

- "Audit `.gitignore` before we fan out"
- "Will my subagents' new paths be tracked?"
- "Check that `<path>/<lib|dist|build|output|...>` won't be ignored"
- `/gitignore-audit`

### Proactive triggers — offer the skill without being asked

Offer when **any** of these apply:

- The dispatcher is about to dispatch ≥2 subagents in parallel.
- The dispatcher's plan adds files at new top-level directories whose
  names match the broad Python/Node/Java conventions
  (`lib/`, `dist/`, `build/`, `target/`, `out/`, `output/`, `bin/`,
  `obj/`, `node_modules/` — though the last is usually intentional).
- The dispatcher's plan adds files under a path that is itself nested
  inside a directory that might be ignored
  (`<some-package>/<lib|dist|...>/`).

### Negative triggers — skip the skill

- The work touches only existing tracked files.
- The repo has no `.gitignore` at all.
- The dispatcher already passed an `--audited` or similar flag.

## Inputs

- The plan's list of "files to be created" or "directories to be
  populated." If not enumerated, the dispatcher can derive it from each
  subagent's brief (look for `templates/`, `lib/`, `bin/`, `build/`,
  `dist/`, `output/` mentions).
- Optional: an `--include-nested` flag to walk all `.gitignore` files in
  the tree, not just the root.

## Outputs

A short report (typed inline; not a file) of shape:

```
.gitignore audit — <count> potential collisions

Rules that could swallow your planned paths:

  .gitignore:13  `lib/`
    swallows:    pipeline-skills-package/skills/batch-job/lib/
                 pipeline-skills-package/skills/task-dag/lib/
                 pipeline-skills-package/skills/orchestrate-issue/lib/
                 pipeline-skills-package/skills/onboarding/lib/
                 pipeline-skills-package/test-harness/lib/
    existing exceptions: !harness/lib/
    fix options:
      1. Replace `lib/` with rooted `/lib/`           (preferred)
      2. Add `!pipeline-skills-package/**/lib/`        (per-subtree)
      3. Tell every subagent to use `git add -f`      (band-aid)

Status: STOP. Fix .gitignore before dispatching, then re-audit.
```

If zero collisions found, output `.gitignore audit — clean. <N> rules checked against <M> planned paths.`

## Workflow

1. **Enumerate planned paths.** Read each subagent's brief (or the
   plan's "Output" / "Files this skill creates" sections). Collect each
   file or directory that will be created.

2. **Read every `.gitignore` in the repo.** Default scope: root-level
   `.gitignore` only. With `--include-nested`: walk and read all
   `.gitignore` files. Capture each rule's source file + line number.

3. **For each planned path, check every rule.** A rule "swallows" a
   path if a hypothetical `git add <planned_path>` would be silently
   ignored. The safest test is to use `git check-ignore -v <path>`
   itself — but the path may not exist yet, so create a `tmp_path`
   with the structure mocked, run `git check-ignore` in a temporary
   `git init` clone of the relevant `.gitignore` chain, OR write a
   minimal Python rule-matcher that handles `<name>/`, `*<glob>`,
   `**/<name>`, and `!<negation>`.

4. **Group collisions by rule.** A single rule like `lib/` usually
   matches many planned paths.

5. **For each collision group, propose three fix options ranked by
   safety.** The preferred fix is to narrow the rule (root it with `/`,
   tighten the glob, or add a specific negation). The fallback is to
   tell subagents to use `git add -f`. The last resort is to ignore
   the collision and clean up post-merge.

6. **If at least one collision is found, return STATUS = STOP.** The
   dispatcher must fix the `.gitignore` and re-audit before dispatching.

7. **If zero collisions, return STATUS = CLEAR + a one-line summary.**

## Concrete examples

### Example 1: the originating session

Plan: dispatch 6 subagents each writing files under
`pipeline-skills-package/skills/<name>/lib/` (and `test-harness/lib/`
for one).

Skill input — derived planned paths:

```
pipeline-skills-package/skills/batch-job/lib/__init__.py
pipeline-skills-package/skills/batch-job/lib/common.py
pipeline-skills-package/skills/batch-job/lib/poll.py
pipeline-skills-package/skills/batch-job/lib/submit.py
pipeline-skills-package/skills/task-dag/lib/{...}
pipeline-skills-package/skills/orchestrate-issue/lib/{...}
pipeline-skills-package/skills/onboarding/lib/{...}
pipeline-skills-package/test-harness/lib/{...}
```

Skill output:

```
.gitignore audit — 1 potential collision

Rules that could swallow your planned paths:

  .gitignore:13  `lib/`
    swallows:    pipeline-skills-package/skills/batch-job/lib/
                 pipeline-skills-package/skills/task-dag/lib/
                 pipeline-skills-package/skills/orchestrate-issue/lib/
                 pipeline-skills-package/skills/onboarding/lib/
                 pipeline-skills-package/test-harness/lib/
    existing exceptions: !harness/lib/
    fix options:
      1. Replace `lib/` with rooted `/lib/`           (preferred)
      2. Add `!pipeline-skills-package/**/lib/`        (per-subtree)
      3. Tell every subagent to use `git add -f`      (band-aid)

Status: STOP. Fix .gitignore before dispatching, then re-audit.
```

Outcome had it been run: dispatcher fixes the rule once
(`git mv lib/ → /lib/` in the gitignore), re-audits → CLEAR, dispatches.
No nested-`.gitignore` workarounds, no cleanup commit.

### Example 2: dispatching test files under `tests/distribution/`

Plan: write 15 contract test files at `tests/distribution/test_*.py`
and fixtures.

Skill input — derived planned paths:

```
tests/distribution/__init__.py
tests/distribution/conftest.py
tests/distribution/test_template_parity.py
... 13 more test files ...
tests/distribution/fixtures/fake_repos/blank-repo/README.md
```

Audit checks against root `.gitignore` rules:

- `dist/` matches the `dist` segment in `tests/distribution/` because
  the bare-name form matches at any depth. **Hit.**
- `__pycache__/` does not match `__init__.py`. Pass.

Skill output:

```
.gitignore audit — 1 potential collision

Rules that could swallow your planned paths:

  .gitignore:14  `dist/`
    swallows: tests/distribution/  (because bare `dist/` matches a
              directory at any depth named `dist`)
    NOTE: this is a NEAR miss — `dist/` matches dirs named `dist`,
          not `distribution`. Modern git versions match by exact
          path component. Verify with `git check-ignore -v <path>`.
    fix options:
      1. Replace `dist/` with rooted `/dist/`         (preferred)
      2. Rename your dir to `tests/dist_tests/`        (avoid)

Status: WARN. The pattern *may* match depending on git version. Verify
with `git check-ignore -v tests/distribution/conftest.py` before
dispatching.
```

The dispatcher runs `git check-ignore -v` on a representative planned
path to disambiguate. (In practice, the originating session hit this
near-miss and confirmed `dist/` does NOT match `tests/distribution/`
because git uses path-component matching.)

## Anti-patterns

- **Trusting that the dispatcher remembers all the planned paths.** A
  6-subagent fanout has dozens of new paths; pull them from the briefs
  programmatically.
- **Skipping nested `.gitignore` files when `--include-nested` is set.**
  A nested `.gitignore` can re-introduce a rule that the root suppressed,
  or vice versa.
- **Running this skill AFTER subagents have already started.** The whole
  point is pre-flight. Running it post-fanout finds the same collisions
  the subagents already worked around — too late.
- **Suggesting `git add -f` as the preferred fix.** Force-adding bypasses
  the symptom but leaves the bad rule in place. Narrow the rule instead.

## Acceptance criteria

1. Given a plan that adds files under a path matched by a broad
   `.gitignore` rule, the skill emits a STOP report naming the rule's
   source file + line + the matched paths.
2. Given a plan with no `.gitignore` collisions, the skill emits a CLEAR
   report listing the rule count and planned-path count it checked.
3. The skill's fix-option list always includes a preferred narrowing
   (rooted / negation), a fallback structural fix (rename / move), and
   the `git add -f` band-aid in last place — and never reverses that
   ranking.
4. `git check-ignore -v` is used to disambiguate near-misses (e.g.,
   `dist/` against `tests/distribution/`) before declaring a hit.
5. The skill runs in under 5 seconds against a typical repo with a 200-
   line `.gitignore` and 50 planned paths.

## Files this skill creates / modifies

- **No files created.** Output is a typed report.
- **The dispatcher** modifies `.gitignore` (and possibly nested ones)
  in response to the report — those edits are out of scope for this
  skill itself.

## Optional: implementation sketch

```python
# .claude/skills/gitignore-audit-before-fanout/lib/audit.py
import re
import subprocess
from pathlib import Path

def audit(repo_root: Path, planned_paths: list[str]) -> dict:
    gitignores = list(repo_root.rglob(".gitignore"))
    collisions = []
    for planned in planned_paths:
        # Use git check-ignore to authoritatively check
        result = subprocess.run(
            ["git", "check-ignore", "-v", planned],
            cwd=repo_root, capture_output=True, text=True,
        )
        if result.returncode == 0:
            # Output format: <gitignore_path>:<line>:<pattern>\t<planned>
            collisions.append({
                "planned": planned,
                "rule_source": result.stdout.strip(),
            })
    return {
        "status": "STOP" if collisions else "CLEAR",
        "collisions": collisions,
        "checked_paths": len(planned_paths),
        "checked_gitignores": len(gitignores),
    }
```

This is a sketch; the real skill should also propose narrowed fixes,
which requires parsing the rule patterns and proposing rooted variants.
