# Spec: `clarify-before-bulk-design`

## Intent

Before producing a multi-document design package (specs + plans that cross-reference each other), gather decisions from the user with structured questions rather than guessing. Multi-doc design has a high consistency cost — every cross-reference depends on a shared model in the agent's head. If that model has the wrong default on any key axis, all the cross-referenced docs need to be rewritten together. The marginal cost of asking 3-4 multiple-choice questions up front (60 seconds of user time) is dwarfed by the cost of rewriting 8 inter-referential documents.

In this session, four sequential `AskUserQuestion` calls were used:

1. Skill structure (4 options for how the onboarding skill relates to install).
2. Resume model (3 options for handling interrupted onboarding).
3. Adoption marker (4 options for "what signals already-onboarded").
4. Output scope (4 options, multi-select, for what onboarding may edit).

Each answer foreclosed a substantial design branch. None of the chosen options would have been my default. Writing the specs first and revising on rejection would have meant ~3000 lines of rework.

The user's preferred option was picked as `(Recommended)` in 3 of 4 cases — meaning the recommendation was right but the question still produced value because (a) it surfaced the user's preference explicitly rather than relying on assumption, and (b) the question itself documented why one option was preferred.

## Trigger

Activate when **all** of the following hold:

- The next deliverable is **multiple inter-referential design documents** (3+ files that cite each other).
- At least one **structural** decision has 2+ defensible answers (not just polish choices).
- The user has not explicitly said "just write what you think makes sense, I'll revise."

**Direct triggers**:
- "Design specs for X, Y, Z"
- "Build a package that includes A, B, C"
- "Write the plan AND the SPECs for ..."
- "Set up the whole thing"

**Proactive triggers**:
- A planning conversation has surfaced more than one axis of decision (e.g. "where does it install?" + "how does it self-bootstrap?" + "what's the trigger pattern?").
- The agent is about to write a `SPEC.md` and a `PLAN.md` in the same session.

**Negative triggers**:
- Single-file deliverable.
- User explicitly said "I'll review, don't ask me."
- Time-critical task where waiting for user input is the bottleneck.
- The agent has already asked 3-4 questions in the same conversation — diminishing returns; switch to writing and revising.

## Inputs

- The user's most recent request.
- The list of design axes the agent has identified.
- (Internal) The agent's best guess at the answer for each axis — this becomes the `Recommended` option.

## Outputs

- A series of `AskUserQuestion` calls, no more than 4 per round.
- A clear restatement of the user's combined answers before writing.
- A "I'm ready to start writing — confirm?" gate.

## Workflow

1. **Identify the design axes.** Walk through the planned deliverables and find every decision the agent would otherwise default on. Examples: where does it install, how does it trigger, what's the conflict policy, what's the file format, what's the well-known branch name.
2. **Filter to structural axes.** Polish decisions (typography, doc tone) don't qualify. Only axes where a different answer would meaningfully change the design.
3. **Per axis, draft 2-4 options.** Include the agent's best guess, labeled `(Recommended)`. Each option has a description that names the trade-off.
4. **Group into batches of up to 4 questions.** Use `AskUserQuestion`'s native multi-question form. Don't ask one at a time when several are independent.
5. **Restate the answers.** After each `AskUserQuestion` round, summarize the user's decisions in 3-7 sentences so they can catch a misinterpretation cheaply.
6. **Gate before writing.** Ask: "Ready to start writing the docs, or anything else to lock in first?"
7. **Cap rounds.** No more than 3 `AskUserQuestion` rounds in a session. Beyond that, the marginal value drops and the user starts feeling interrogated.

## Concrete examples

### Example 1: design package for a skill bundle

User: "Spec out a skill package that bundles X, Y, Z plus an onboarding skill."

Agent identifies 4 axes: install location, archive form, test-harness GitHub interaction, template relationship to source. Asks all 4 in one `AskUserQuestion` call with 4 questions:

```
Q1: Where should skills install? (project / user / both)
Q2: What form should the archive take? (recipe / tarball / both)
Q3: How should test harness interact with GitHub? (mock / live account / hybrid)
Q4: How should templates relate to source? (copy with contract test / independent / invert)
```

User picks (project / both / live with own credentials [via "Other"] / copy with contract test). Agent restates, gates, then writes 13 documents with consistent answers throughout. Zero rewrites required.

### Example 2: not triggering — single-file ask

User: "Write a SPEC.md for the batch-job skill."

One file. No multi-doc consistency cost. Skill does **not** activate; agent writes the spec directly. Any structural ambiguity surfaces as a "question for you:" line in the chat reply.

## Anti-patterns

- **Asking polish questions.** "Should the doc start with a header or a quote block?" wastes the user's attention. Reserve `AskUserQuestion` for decisions that change architecture.
- **One question per call.** `AskUserQuestion` supports 1-4 questions per call. Group related axes; minimize round-trip count.
- **Forgetting to restate.** A multi-question round can produce non-obvious combined answers. Restate the combined decision in 3-7 sentences before writing.
- **Over-asking.** After 3 rounds the user fatigues. If more decisions remain, write a draft with assumptions clearly flagged and let the user revise.
- **Asking without a recommendation.** The `(Recommended)` option is high-signal — it tells the user what the agent thinks AND gives a defensible default. Always include one if a defensible default exists.
- **Asking architectural questions after writing has started.** The point is to ask BEFORE the rewriting cost accrues.

## Acceptance criteria

1. The agent asks at least one structured question before writing 3+ inter-referential docs.
2. Each `AskUserQuestion` call groups 2-4 related axes, not 1.
3. Each option includes a description that names a trade-off, not just a label.
4. The agent restates combined answers in <8 sentences before starting to write.
5. The agent does not exceed 3 rounds of `AskUserQuestion` in one session.
6. At least one option per question is marked `(Recommended)` when a defensible default exists.

## Files this skill creates / modifies

- None on disk. The skill governs interaction shape.
- Optionally writes a `design-decisions.md` capturing the Q&A trace if `--log-decisions` is passed — useful for resumption and for tying answers back to written specs.
