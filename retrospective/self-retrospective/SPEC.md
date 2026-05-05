# `self-retrospective` — implementation spec

A meta-skill that runs at the end of a long session to extract
durable lessons before they're lost.

## 1. Trigger conditions

**Direct user requests:**
- "Do a retrospective"
- "What did we learn?"
- "What skills could we extract?"
- "Lessons learned?"
- "Anything to add to AGENTS.md?"

**Proactive triggers** (skill should offer when):
- Session has spanned multiple distinct phases or pivots
- Session surfaced unexpected real-world findings (bugs, transport
  quirks, spec contradictions)
- Session used many subagents (≥5) or required novel orchestration
- Session has discovered workarounds for tool / sandbox limitations
- Session has run >2 hours of total agent time
- User says something that suggests session-wrapping ("OK we're
  done", "good work", "let's stop here")

**Negative triggers:**
- Routine sessions that just exercised a known pattern.
- Sessions where the user hasn't done substantive work yet.

## 2. Output structure (the spine)

The retrospective has three parts in this order. Each part is
mandatory; skipping one leaves significant value on the table.

### Part 1 — what happened (narrative)

**Phase-by-phase summary.** Each distinct phase of the session gets a
named heading and 1-3 paragraphs:

- What was the goal of this phase?
- What was the planned approach?
- What actually happened (especially deviations)?
- What was unplanned but mattered (operational mishaps, recoveries,
  surprises)?

**Metrics table** at the end of Part 1:

| Metric | Value |
|--------|-------|
| Subagents dispatched | N (by category if useful) |
| PRs opened / merged | M / K |
| Real-world bugs discovered + fixed | B |
| Tests added (before / after) | X / Y |
| Spec amendments | S |
| Scenarios driven / skipped | D / Sk |
| Files touched at major refactors | F |

### Part 2 — skills to extract

For each skill candidate, use the uniform template:

```markdown
### Skill N: `<skill-id>` — <one-line summary>

**Purpose.** <One sentence: what problem this skill solves.>

**Trigger.** <When this skill should activate.>

**Core content.** <Numbered list of 5-10 substantive teachings.>

**Anti-patterns.** <What NOT to do — based on session misses.>

**Example/template.** <Concrete code or text where useful.>
```

Aim for 200-500 words per skill. Detailed enough that later building
from each spec is straightforward; not so detailed that the
retrospective becomes the implementation.

### Part 3 — AGENTS.md / repo conventions

One-line rules, each grounded in something that went wrong (or
nearly did). Format:

```markdown
N. **<Rule name>.**  
   "<The rule, phrased as a do/don't statement, ready to drop into
   AGENTS.md verbatim.>"
```

Aim for 5-15 rules. More than 15 is usually noise.

### Final summary table

After all three parts, a sortable table:

| Skill | Priority | Approx scope |
|-------|----------|--------------|
| ... | high/med/low | ... |

This is the user's pick-list for what to build next.

## 3. The scan checklist (what to harvest)

When walking the session for material, look for:

### 3.1 Bugs you fixed
Each bug is candidate content for either a skill (if generalizable)
or an AGENTS.md rule (if project/runtime-specific).

Distinguish three kinds:
- **Implementation defects** — your code did the wrong thing.
- **Spec defects** — the design itself was broken.
- **Transport / environment quirks** — the runtime surprised you
  (escaping, identity, permissions, naming).

### 3.2 Workarounds you invented
When a tool didn't do what you needed and you went around it, that
workaround is reusable. Examples from this session:
- Self-diagnostic comments when CI logs are auth-walled.
- Driving branch deletion through close_on_merge when `git push --delete` is blocked.
- Polling loops in `run_in_background` when `sleep 45` is blocked.

### 3.3 Recurring micro-patterns
Anything you typed >2 times. If it's worth typing twice, it's worth
templating.

### 3.4 Operational mishaps
**Especially valuable.** Each near-miss becomes a "don't do X" rule.
Examples:
- Force-pushed feature branch back to main → PR auto-closed.
- Subagent ran out of usage mid-task → recovery from local commit.
- Marker comments didn't appear → workflow YAML wasn't on main yet.

### 3.5 Subagent prompts that worked vs didn't
Meta-lesson on briefing future subagents.

### 3.6 Scope decisions
What you skipped and *why*. The "why" is the lesson.

### 3.7 Discoveries about the runtime
Auth boundaries, identity quirks, rate limits, naming collisions —
hard-won and should be captured.

## 4. What NOT to include

- Step-by-step replay of routine work.
- Self-evaluation / praise.
- Speculation about features the system "should" have.
- Code (beyond illustrative snippets — the skill files hold code).
- Internal subagent transcripts (just summaries).

## 5. Output deliverable

By default the skill produces:

- A **markdown document** with the three-part structure and the
  summary table.
- Optionally: a **directory tree** like the one this session
  produced (`retrospective/<skill-name>/{README,SPEC}.md` plus
  excerpts), if the user wants a full implementation-grade package.

The skill should ASK which output the user wants:

> "Do you want a chat-only retrospective, or should I write a full
> `retrospective/` directory with per-skill packages?"

## 6. Tone

- **Honest about misses.** A retrospective with no "I would do this
  differently" entries is incomplete. Specific examples:
  - "I lost a commit by force-pushing PR #6's branch to main before
    the PR was merged. Recovered from local reflog. Lesson: never
    force-push between PR open and PR merge."
  - "Subagent debugging session was wasteful for the first 30 minutes
    because I asked it to find 'the bug' rather than enumerating
    hypotheses. Hypothesis enumeration in subagent briefs reduces
    debug time substantially."
- **Concrete about scope.** List what's in, what's out, why.
- **Suggest, don't prescribe.** The user picks what survives.

## 7. Anti-patterns

- **Implementing while retrospecting.** A retrospective with code
  changes attached is the wrong response. Wait for explicit "now
  build it."
- **One giant unstructured document.** The Part 1/2/3 split makes it
  skimmable and selectively actionable.
- **Generic advice.** "Write good prompts" is useless. Always ground
  rules in specific session events.
- **Forgetting Part 3.** Repo conventions are often the highest-ROI
  output. Skipping them squanders much of the session's value.
- **Capping at "what went well."** The misses ARE the lessons.

## 8. Skill invocation

```
/retrospective                           # the default
/retrospective --no-skills               # skip Part 2 (just narrative + AGENTS.md)
/retrospective --output-dir ./retro/     # produce a full directory tree
/retrospective --since "2025-01-15"      # only material since this point in session
```

## 9. Test plan (when built)

Hard to unit-test a meta-skill. Ideal validation:

- Run on a known session transcript (e.g., this one).
- Verify output covers all three parts.
- Verify each skill candidate has the uniform shape.
- Verify each AGENTS.md rule is grounded in a session event.

## 10. Living document

Like all skills here, this should evolve. New scan-checklist items
get added as new kinds of valuable lessons surface in future
sessions.

## 11. Meta-note

This SPEC.md is itself an output of `self-retrospective` being
applied to this session. The retrospective in chat → user requested
"create the directory" → here we are.

If a future agent wants to build this skill, the input it should
study is **`ITERATION_REPORT.md` plus this entire `retrospective/`
directory**. They demonstrate the format, the depth, and the kind of
material the skill should produce.
