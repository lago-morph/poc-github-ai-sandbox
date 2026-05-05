# Bad brief example: lock-vs-bot fix (overscoped)

This brief is what happens when too much is packed into one
dispatch. The subagent ran out of usage mid-task. Recovery worked
because the subagent had committed locally before stopping, but the
ideal would have been not to overscope in the first place.

## What was overscoped

The brief asked the subagent to do, in one task:

1. Update `.agent/config.json` agent_login
2. Update `batch-job-handler.yml` if-clause
3. Modify `lock_and_sweep.py` to stop locking
4. Modify `close_on_merge.py` to lock at close
5. Update **8** harness scenario markdown files
6. Update `harness/lib/asserts.py`
7. Add a "Real-world correction" paragraph to **§3, §4.1, §7.1, §7.3**
   of SPEC.md
8. Update **3** test files
9. Update e2e tests
10. Run the full test suite and confirm count
11. Commit, push, open a PR

That's ~15-20 file changes spanning 4 different layers of the
project.

## Why this is too much

- The subagent has to keep all 11 deliverables in working memory.
- Some are small (config update); some are large (8 scenario docs,
  spec amendments to 4 sections).
- Mid-task context exhaustion is a real risk on a brief this long.
- Recovery is harder because changes span many files; partial state
  is hard to reason about.

## How to split it

Three tighter briefs would have worked:

### Brief A: code change
- config.json + batch-job-handler.yml + lock_and_sweep.py +
  close_on_merge.py + tests for those
- Focused, ~6 files, clean PR

### Brief B: scenario doc updates
- The 8 harness scenario docs + asserts.py
- Pattern: find-and-replace "lock + label" → "label only", add
  comment about close_on_merge's new lock role
- Focused, ~9 files, doc-only PR

### Brief C: SPEC.md amendments
- The 4 §-amendment paragraphs
- Single file, dispatcher could even do this inline since it's pure
  text editing

Each one is ~10-20 minutes for a subagent. Sequential dispatch
total: ~45 minutes, but each has a clean checkpoint.

## What actually happened

The subagent committed locally (smart!) then ran out of usage. The
dispatcher (me) picked up:

- The local commit was complete enough to push
- Pushed and PR'd from the dispatcher's clone
- Verified all 380 tests still passed

Recovery worked, but only because the subagent had committed early.
This is now part of the `subagent-prompting` skill: "If you commit
local changes, the dispatcher can pick up local-but-unpushed work."

## The lesson

**Brief size scales work, not capability.** Subagents can do large
work — but each unit of brief complexity adds:

- Memory pressure on the subagent
- More places where the subagent could deviate
- Harder recovery if anything goes wrong

When in doubt, split. Three sequential briefs at ~600 words each
beat one ~2000-word brief.

## Heuristic for future briefs

If a brief includes:
- More than ~8 distinct deliverables, OR
- Changes to >10 files, OR
- Changes spanning >3 architectural layers (config, code, tests,
  docs, spec)

Split it. Two or three smaller briefs almost always finish faster
than one big one, and have cleaner failure modes.
