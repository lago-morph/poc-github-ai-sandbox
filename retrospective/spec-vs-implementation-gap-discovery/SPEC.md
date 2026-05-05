# `spec-vs-implementation-gap-discovery` — implementation spec

A skill that codifies the discipline of running live scenarios after
unit tests pass, and the patterns for finding spec/transport bugs
that mocks can't surface.

## 1. Trigger conditions

- After unit tests pass on a project that interacts with external
  systems (APIs, transports, runtime environments).
- When a user says something like "but does this actually work?" or
  "let's try it for real" or "use it the way it was intended."
- Periodically during a project — every few iterations of
  `agent-dispatch-loop`, regardless of coverage %.

Negative triggers:
- Pure-Python utility libraries with no external dependencies.
- Projects already in production (continuous monitoring is a
  different pattern).

## 2. Two kinds of bugs

| Kind | Example from this session | Caught by |
|------|---------------------------|-----------|
| **Implementation defect** | Off-by-one in chunk rotation | Unit tests |
| **Spec defect** | Lock-vs-bot contradiction | Live execution only |
| **Transport quirk** | MCP HTML-escapes bodies | Live execution only |
| **Identity asymmetry** | `GITHUB_TOKEN` ≠ collaborator on locked issue | Live execution only |
| **Naming collision** | `agent/foo` and `agent/foo/bar` can't coexist | Live execution only |

The mock client in unit tests is, by definition, **a model of the
spec**. It can never disagree with the spec. So spec bugs are
invisible to it.

## 3. The live-execution phase

After unit tests are green, schedule a live phase with these
properties:

### 3.1 Scenario design
Pick scenarios that exercise distinct architectural paths, not
permutations of the same path. Examples from this session:

| Scenario | Architecturally distinct? |
|----------|--------------------------|
| Happy single subagent | ✅ Full lifecycle |
| Multi-subagent fan-out | ✅ Concurrency + merge |
| Parse error | ✅ Validation failure path |
| SHA mismatch | ✅ Pre-flight rejection |
| Unsupported version | ✅ Pre-validation check |
| Unknown command | ✅ Registry rejection |
| Summary schema violation | ✅ Post-run validation |
| Huge log | ✅ Chunk rotation |
| Unicode | ✅ Encoding round-trip |

NOT distinct (don't add to the live list — covered by units):
- "Echo with different message string" — same path as scenario 1
- "Three different valid commands" — same path as scenario 1 with
  different inputs

### 3.2 Pre-conditions
For each scenario, document:
- Initial real-system state needed (issues, branches, config)
- What the agent + workflow are expected to do
- Expected final state (in the real system, not in a mock)

### 3.3 Assertions against real state
Read state from the real system after the scenario runs and verify:
- Workflow ran (visible in Actions UI / runs API)
- Comment terminal envelope present + correct fields
- Log artifacts on the orphan branch (with correct paths)
- Issue state (closed? locked? labels?)
- PR opened/merged (if applicable)

Use `mcp__github__*` tools (or the project's equivalent) to verify.

### 3.4 Forensic preservation
- Tag every scenario run with a unique id.
- Leave artifacts in place by default (forensic mode).
- Failed scenarios stay open for inspection.

See `forensic-vs-aggressive-cleanup` for the full pattern.

## 4. The discovery loop

When a live scenario fails:

1. **Diagnose at the boundary**, not the internals. Most live
   failures are at the agent ↔ external system boundary, not in
   pure logic.
2. **Trust the spec less** than you would normally. Your first
   suspicion should be "the spec is wrong here," not "my code is
   wrong."
3. **Capture the surprise immediately**. Even before fixing, write
   down what surprised you.
4. **Annotate the spec inline** when the discovery is permanent:

```markdown
## §3. Identities and access control

[original spec text]

**Real-world correction (discovered during live POC runs).** The
original draft locked agent issues at creation. In practice, GitHub
refuses comments from `GITHUB_TOKEN` on locked issues — including
the workflow's own terminal envelope writes. The handler is
therefore unable to produce its required output if the issue is
locked during processing. The corrected design: ...
```

5. **Add a regression test** that captures the discovery (mock-
   based, since the real system is hard to retest cheaply).

## 5. Discovery checklist

When investigating a live failure, walk through these questions in
order:

### 5.1 Identity
- Who is the agent authenticated as?
- Who does the workflow's `GITHUB_TOKEN` represent?
- Are they the same? (Often not — agent is a user, token is a bot.)
- Does the system's auth/permission model account for both?

### 5.2 Permissions
- What permissions does the workflow have?
- Are there operations that the bot identity can't do regardless
  of permissions? (Locked issues, archived repos, etc.)
- Are there operations only the user can do?

### 5.3 Encoding / serialization
- Is content escaped on the way out?
- Is content modified on the way in (auto-trailers)?
- Are there encoding round-trips that lose information?

### 5.4 Naming
- Are there reserved names or namespaces?
- Do collisions exist (filesystem refs, ID conflicts)?
- Is your naming pattern legal in the target system?

### 5.5 Timing
- What's the latency between trigger and execution?
- Are there queue delays under load?
- Are there rate limits?

### 5.6 Defaults
- Are your defaults appropriate for production?
- Did your test command parameters reflect realistic load?

## 6. Annotating discoveries

Use a uniform format for spec annotations:

```markdown
**Real-world correction (discovered <date> via <how>).** <One-sentence
description of what was wrong>. <One-sentence statement of the new
design>. <Optional: brief rationale for why this works around the
constraint.>
```

Place inline at the section where the original (now-incorrect)
guidance lived. Don't move the original; correct it explicitly.

## 7. The "scenarios skipped" rule

When defining the live-execution scope, **scope reduction is fine but
must be explained**. A scenario should only be skipped if:

- It exercises the same architectural path as one already run, OR
- It requires orchestration that's impractical (e.g., race timing
  the agent can't induce), OR
- It's covered by unit tests AND the unit-test path matches the live
  path (no transport mismatch)

Document the reason for each skip:

```markdown
| Scenario | Status | Reason |
|----------|--------|--------|
| 08 merge_conflict | Skipped | Pattern same as scenario 02 + unit-tested in test_merge_conflict_*; live demo would re-confirm |
| 10 crash_recovery | Skipped | Requires inducing workflow crash; MCP can't trigger that |
```

This makes the live-execution coverage auditable.

## 8. Anti-patterns

- **Treating "unit tests pass" as "ready to ship."** They prove the
  impl matches your understanding of the spec. The spec might be
  wrong.
- **Running scenarios that are unit-test permutations.** Wastes
  time without finding new bugs. Pick distinct paths.
- **Auto-cleaning failed scenarios.** Failed runs are forensic gold.
- **Investigating internals first when a live test fails.** The bug
  is almost always at the boundary.
- **Not annotating the spec.** Discoveries that don't make it back
  into the spec are lost when the next round starts from the
  unmodified spec.
- **Treating a discovery as a one-off.** Every discovery is a
  candidate skill or AGENTS.md rule.

## 9. Output deliverables

After the live-execution phase, the project should have:

- A scenario log (this session's `harness/RUNS.md` is an example).
- Spec amendments inline in the spec doc.
- Regression tests for each discovered bug.
- An entry in the project's "lessons" or AGENTS.md doc.
- A list of artifacts left for forensic inspection.

## 10. Test plan (for the skill itself, when built)

The skill's value is mostly procedural / prompt-shaped. To test:

- Verify the skill triggers on the right cues.
- Verify the skill produces a scenario list with distinct paths.
- Verify discovered bugs lead to spec annotations + regression tests.
- Hard to truly unit-test; best validation is real use.

## 11. References

- `ITERATION_REPORT.md` Phase 4 section — narrative of how the 7
  bugs were discovered.
- `github-mcp-tips/excerpts.jsonl` — the actual evidence per bug.
- `harness/RUNS.md` — the scenario log format.
- `harness/scenarios/*.md` — scenario spec format.
