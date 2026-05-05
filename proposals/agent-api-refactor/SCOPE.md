# Scope

This refactor must operate within these file boundaries to avoid
conflicting with the parallel GitHub POC implementation effort.

## In scope (you may modify)

- `skills/batch-job/submit.py`
- `skills/batch-job/poll.py`
- `skills/batch-job/common.py`
- `skills/batch-job/SKILL.md`
- `skills/batch-job/__init__.py`
- `skills/task-dag/claim.py`
- `skills/task-dag/plan.py`
- `skills/task-dag/merge.py`
- `skills/task-dag/schedule_successors.py`
- `skills/task-dag/common.py`
- `skills/task-dag/SKILL.md`
- `skills/task-dag/__init__.py`
- Tests under `tests/unit/` and `tests/e2e/` that exercise the skills
  (update imports/calls; do not weaken assertions). Note: tests that
  exercise the workflow handlers directly are part of POC work; if a
  test does both, prefer to leave it alone and surface the dependency
  in the PR description.
- `tests/conftest.py` only if needed to register a `TaskBackend`
  fixture; if so, add to it, do not rewrite it.

## In scope (you may create)

- A new file for the `TaskBackend` Protocol and shared neutral
  dataclasses. Suggested location: `skills/backend.py` (a top-level
  skill helper, not nested under either of the two skills, so both
  skills can import from it).
- A new file for the `GithubDriver`. Suggested location:
  `skills/drivers/github.py` (with a `skills/drivers/__init__.py`).
- New tests under `tests/unit/` exercising the driver and the neutral
  interface directly.

## Out of scope (do NOT modify)

These are owned by the parallel GitHub POC implementation effort. Any
edits here will conflict.

- `.agent/config.json`
- `.agent/schemas/**`
- `.agent/scripts/handler.py`
- `.agent/scripts/lock_and_sweep.py`
- `.agent/scripts/close_on_merge.py`
- `.agent/scripts/common.py`  ← important: do NOT add the new Protocol
  here. The new Protocol lives under `skills/`.
- `.agent/scripts/requirements.txt`
- `.agent/commands/**`
- `.github/workflows/*.yml`
- `harness/**`
- `SPEC.md`
- `README.md`
- `ITERATION_REPORT.md`
- `pytest.ini`

## Test scope

Run `pytest` from the repo root. Acceptance criterion is "all tests
that pass on the current `HEAD` still pass." If a test is currently
failing on `HEAD` (POC-in-progress), do not try to fix it as part of
this refactor — note it in the PR description and leave it.

## When the boundary is unclear

Default to *not* editing. If a needed change touches an out-of-scope
file, leave a note in the PR description with:

- the file in question,
- why a change is required,
- what the minimal change would be,

and stop. The user will reconcile it with the parallel POC effort.
