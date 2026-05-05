# Agent API refactor — backend-neutral skill layer

You are a fresh agent session. Read this file end-to-end before doing
anything. Then read `SCOPE.md`, `INTERFACE.md`, and `RENAME-MAP.md` in
that order. The work is contained.

## Goal

Make the agent-facing skill API (in `skills/`) backend-neutral so the
substrate (today GitHub; later Bitbucket+Jira+Confluence or others) can
be swapped without changing any agent code, prompt, or skill `SKILL.md`
documentation.

After this refactor, an agent that uses the skills should never see:

- the words `issue`, `comment`, `envelope`, `agent-meta`, `_agent_runs`,
  `Closes #N`, or `lock` in any skill API parameter, return value, or
  documentation;
- any GitHub-specific identifier types (issue numbers as int, comment
  IDs as int — both become opaque strings);
- any platform-specific file or branch path conventions that the skills
  could otherwise hide.

The implementation behind today's GitHub-only POC must keep working
unchanged: a `GithubDriver` adapter wraps the existing `GitHubClient`
Protocol so all current tests still pass.

## Why this is being done now (and what is in flight)

A separate, **parallel** implementation effort is iterating on the live
GitHub POC: that work owns the workflow scripts (`.agent/scripts/*.py`),
the YAML workflows under `.github/workflows/`, and the harness
(`harness/`). To avoid step-on-toes conflicts, this refactor is
**strictly scoped to the skill layer plus a new driver abstraction**.
See `SCOPE.md` for the exact include/exclude file list.

This refactor is independent of the eventual Bitbucket adapter design.
The decision *which* second backend to build is captured in the sibling
package `proposals/bitbucket-adapter/` and is deliberately not part of
this work. Your output here just needs to make a second driver tractable
later — it does not need to ship one.

## Deliverable

A single PR against the same feature branch (or a new sub-branch off
it — your choice; if creating a sub-branch, branch off the current HEAD
of `claude/bitbucket-mcp-assessment-5tlr9` and target the same branch in
the PR) that:

1. Introduces a backend-neutral `TaskBackend` Protocol (location and
   shape specified in `INTERFACE.md`).
2. Refactors the two skills (`skills/batch-job/`, `skills/task-dag/`) to
   take a `TaskBackend` rather than a `GitHubClient` and to use the
   neutral API methods (per `RENAME-MAP.md`).
3. Ships exactly one driver: `GithubDriver`, which adapts the existing
   `InMemoryGitHubClient` (and any future REST `GitHubClient`) to the
   new `TaskBackend` Protocol. The driver is the *only* place that
   knows about issues, comments, agent-meta, locks, etc.
4. Keeps all existing tests passing. Update test imports/calls but do
   not weaken any assertion. Where a test was effectively asserting
   "GitHub-shaped behaviour," prefer to keep that assertion against the
   driver's GitHub-specific layer rather than the skill's neutral layer.
5. Updates the two `SKILL.md` files (`skills/batch-job/SKILL.md`,
   `skills/task-dag/SKILL.md`) so they describe the neutral interface.
   No GitHub words.
6. Does NOT modify any file listed under "Out of scope" in `SCOPE.md`.

## Acceptance criteria

- [ ] `TaskBackend` Protocol exists and is the only type the skills
      reference for backend operations.
- [ ] `GithubDriver` exists and implements `TaskBackend` by delegating
      to a `GitHubClient`. The existing `GitHubClient` Protocol and
      `InMemoryGitHubClient` are unchanged.
- [ ] `skills/batch-job/SKILL.md` and `skills/task-dag/SKILL.md` contain
      no GitHub-specific terminology. (Grep for `issue`, `comment`,
      `envelope`, `agent-meta`, `_agent_runs`, `lock`.)
- [ ] All tests under `tests/` pass.
- [ ] The skill API uses opaque-string `task_id` and `job_id`. Where a
      caller previously passed `issue_number=42`, they now pass
      `task_id="42"` (driver-internal coercion to int is fine).
- [ ] `poll()` returns a `JobResult` dataclass / TypedDict with neutral
      field names (per `INTERFACE.md`), not a raw `envelope` dict.
- [ ] An escape hatch exists: `backend.raw_client()` returns the
      underlying `GitHubClient` so operator scripts can drop down. This
      hatch is not used inside any skill.
- [ ] PR description summarises the rename map and links to the three
      docs in this package.

## Working procedure

1. Read `SPEC.md` sections 9 (`batch-job` skill) and 10 (`task-dag`
   skill) to understand the agent-facing contract today.
2. Read `skills/batch-job/{submit.py,poll.py,common.py,SKILL.md}` and
   `skills/task-dag/{claim.py,plan.py,merge.py,schedule_successors.py,common.py,SKILL.md}`.
3. Read the `GitHubClient` Protocol in `.agent/scripts/common.py:128`
   and the `InMemoryGitHubClient` below it for the current shape.
4. Plan the rename and the driver split following `INTERFACE.md` and
   `RENAME-MAP.md`. Do not deviate from the proposed interface without
   first leaving a note in the PR description explaining why.
5. Implement, then run `pytest` from the repo root to confirm tests
   pass. (See `pytest.ini`.)
6. Update both `SKILL.md` files.
7. Commit in logical chunks (suggest: introduce Protocol; introduce
   driver; refactor batch-job; refactor task-dag; update docs; update
   tests). Open a PR.

## What you should NOT do

- Don't attempt a Bitbucket / Jira / Confluence driver. That decision
  is being held in `proposals/bitbucket-adapter/`. The refactor's goal
  is just to make a future second driver mechanical.
- Don't modify the workflow YAML, `.agent/scripts/*.py`, `.agent/config.json`,
  or the harness. The parallel POC owns those. (See `SCOPE.md`.)
- Don't rename `GitHubClient` or `InMemoryGitHubClient`. Add the new
  Protocol alongside them. The driver is the *only* new abstraction.
- Don't introduce extra capabilities (search, queries, hooks) beyond
  what the skills already exercise. Keep the surface tight; richer
  abstractions can be added later when a second driver actually arrives.
- Don't assume any specific Bitbucket / Jira shape. The neutral
  Protocol is platform-shaped only insofar as it covers the operations
  the existing skills already need.
