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

The skill supports **two deliverable modes**. Pick based on user
intent — and ASK if it's not obvious.

### 5.1 Mode A — chat-only retrospective (the default)

A markdown document delivered inline in the chat, with the three-part
structure and the final summary table. Best when:

- The user wants to **review** the lessons before deciding what to
  do with them.
- The session was short or the lessons are few.
- The user explicitly asks for "a retrospective" without mentioning
  files or branches.

Cap output at ~5000 words. If more is needed, recommend mode B.

### 5.2 Mode B — package mode (the implementation-grade deliverable)

A **filesystem package** committed to a feature branch and pushed,
ready for future skill-build tasks to consume. Best when:

- The user says things like "create a feature branch", "package these
  for later", "create specs and READMEs", "I want to capture this
  for later implementation."
- The session was long and lessons are many (5+ skills).
- The user wants to dispatch each skill build as a separate task
  later.

#### Recipe for mode B (the explicit steps)

1. **Create a feature branch.**
   ```bash
   git checkout -b feat/retrospective-skill-specs
   ```
   (or similar). Don't reuse the working branch — this is a clean
   deliverable, separate from in-flight work.

2. **Create the directory tree.** At the repo root:
   ```
   retrospective/
     README.md                            # top-level index
     <skill-name-1>/
       README.md                          # human motivation
       SPEC.md                            # implementation-grade detail
       excerpts.jsonl                     # session evidence (optional)
       examples/                          # concrete templates (optional)
     <skill-name-2>/
       ...
     agents-md-template/                  # special: spec for AGENTS.md edits
       README.md
       SPEC.md
   ```

3. **Top-level `retrospective/README.md`** has:
   - Why the directory exists (paragraph or two — capture the
     "long sessions accumulate value, harvest before compacted"
     intent)
   - The skill-index table (priority + one-line summary per skill,
     with links)
   - A "How to consume this package" section telling future tasks
     how to use the spec to build the skill

4. **For each skill, the per-subdirectory contents:**

   **`README.md`** (human-readable motivation — this is the
   stakeholder-facing doc):
   - **Why this skill matters** — the pain it removes, ideally with
     concrete numbers ("saved ~2 hours of debug time")
   - **When this would have helped (in this session)** — at least
     one concrete example from the session where the skill would
     have been valuable. Reference specific PRs, scenarios,
     subagent dispatches.
   - **What good looks like** — narrative description of the skill
     in action ("user says X, skill outputs Y")
   - **Cousins** — other skills it composes with
   - **Status** — "Spec only — see SPEC.md. No code yet."

   **`SPEC.md`** (implementation-grade detail — the input for a
   future builder agent):
   - **Trigger conditions** (when the skill activates) with
     positive triggers AND negative triggers (when NOT to fire)
   - **Inputs** (parameters, defaults, configuration)
   - **Outputs** (what the skill produces)
   - **Workflow steps** or **core content** (the substance)
   - **Templates** for any prompts, briefs, or generated artifacts
   - **Anti-patterns** (what NOT to do, ideally with session
     examples of the anti-pattern surfacing)
   - **Implementation notes** for the builder (suggested file
     layout, dependencies, integration points)
   - **Test plan** (how to validate the skill works, when built)
   - **Living document** note (skills evolve as new patterns
     emerge)
   - **References** (back to ITERATION_REPORT.md or the session's
     evidence)

   **`excerpts.jsonl`** (when valuable):
   - JSONL format — one record per line.
   - Each record has at minimum: `id`, `kind`, `phase`,
     `demonstration`, plus skill-specific fields like `evidence_raw`,
     `fix`, `lesson`.
   - Include the actual error messages, the actual fix code, the
     actual user quote that motivated the skill — not paraphrases.
   - The SPEC.md should mention the `excerpts.jsonl` exists, what
     it contains, and how a future builder should use it (usually:
     "test the skill against these recorded scenarios").

   **`examples/`** (when valuable):
   - Concrete templates: good-vs-bad prompts, sample YAML snippets,
     reference output formats.
   - Each example file has its own narrative explaining why it's
     a good (or bad) example.

5. **`agents-md-template/` is special.** It's not a skill spec; it's
   a spec for repo-level convention additions. Its SPEC.md
   enumerates rules (with do/don't, "why" grounded in failure, and
   "see also" links to skills). Its README explains why these
   conventions are high-leverage.

6. **Tone for both README and SPEC:**
   - **Lots of intent.** "This is why this is important" — make the
     case for the skill at every level. "This is when this would
     have helped" — concrete situations from the session. "Doing
     this will help in this way" — explicit value statements.
   - Honest about the reasons. If the skill exists because you
     wasted 90 minutes debugging something, say so. The pain is
     the motivation.
   - Future-builder-friendly. Imagine a fresh subagent receiving
     just `SPEC.md` as their brief. Can they build the skill? If
     not, the spec is too thin.

7. **DO NOT implement the skills in this branch.** The package is
   a *deliverable for later tasks*. Mixing the spec branch with
   actual skill code creates merge headaches and conflates two
   purposes. State explicitly in each skill's README: "Spec only.
   No code yet."

8. **Commit and push.** One commit, descriptive message:
   ```
   docs: retrospective skill specs — N skills + AGENTS.md template

   Captures session-wide lessons as self-contained spec packages.
   Each skill has README (motivation) + SPEC (impl detail) +
   excerpts/examples where useful.

   Skills (priority order):
   - <skill-1> (high)
   - <skill-2> (high)
   ...

   No skills implemented in this branch. Each SPEC.md is self-
   contained enough to dispatch a future build task with that
   file as the brief.
   ```

9. **Open a PR.** Body summarizes the index table, what's in /
   what's not in. Don't merge unless the user requests it — the
   user's review of the package is part of the value.

#### Quality bar for mode B

A "good" package is one where:

- Each `SPEC.md` is detailed enough that a future builder agent,
  given just that file as a brief, can produce the skill without
  needing the original session.
- Each `README.md` makes the case clearly enough that a stakeholder
  can decide whether to fund the build without reading the SPEC.
- The session's specific failures, fixes, and quotes appear in
  `excerpts.jsonl` files — preserved verbatim, not paraphrased.
- Cross-references between skills work (see-also links resolve to
  real files in the package).
- The top-level `README.md` index lets a future planner pick which
  skills to build first based on priority + scope.

Total target size: 25-50 files, 3000-6000 lines of markdown,
depending on how rich the session was.

#### When NOT to use mode B

- Routine sessions with 1-2 lessons. A chat-only summary is
  sufficient.
- User explicitly wants the lessons in chat.
- User explicitly wants implementation, not specs.

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
