# AGENTS.md suggestions — 2026-05-14-79

These are proposed additions to the project's agents file (typically
`AGENTS.md` at the repo root). Each section contains:

1. **Proposed addition** — the exact text to paste.
2. **Why this earns its place in your agents file** — the argument for
   doing it, grounded in something that happened (or nearly happened).

Decide each on its own merits. Skip ones that don't apply to your
operating posture; copy-paste the ones that do.

---

## Suggestion 1: Don't use WebFetch for verbatim file content

### Proposed addition

> **Don't use WebFetch when verbatim content matters.** WebFetch routes responses through a small AI processing model that summarizes content regardless of prompt wording. For exact-bytes use cases (copying a skill from another repo, reading a spec file you'll quote, downloading a config) use `curl https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>` for single files, or `git clone --depth 1` for multi-file directories. Verify with `sha256sum` if the content's integrity matters downstream.
>
> *Grounded in: this session's WebFetch attempts to read `subagent-prompting/SKILL.md` and `self-retrospective/SKILL.md` from raw.githubusercontent.com, which returned 200-300-word summaries despite a prompt explicitly demanding verbatim output.*

### Why this earns its place in your agents file

A WebFetch summary is roughly 70% lossy compression of the source. If an agent uses that summary as the basis for design work (specs, plans, code generation), all downstream artifacts inherit the lossiness. In this session, the agent caught the summarization after two attempts and switched to `git clone`, but the close-call mattered: the eventual design referenced specific patterns in `parallel-subagent-fanout/SKILL.md` (which fetched verbatim) and those references would have been wrong if any of the other two had served as the source.

Marginal cost of adoption: one extra Bash command, ~2 seconds. Cost of not having the rule: undetected design corruption from a "successful-looking" tool response. Asymmetric — adopt the rule.

---

## Suggestion 2: Treat MCP `create_pull_request` 422 errors as ambiguous

### Proposed addition

> **Verify before retrying a 422 from `mcp__github__create_pull_request`.** A 422 response sometimes means the PR was not created (bad input), sometimes means the PR WAS created but the response also carried a validation note. Before retrying, wait briefly (~2s) then call `mcp__github__list_pull_requests` with `head: <owner>:<branch>` to check if the PR exists. If it does, use it. If it doesn't, verify the branch is on origin at the expected SHA via `list_branches` before retrying. Cap retries at one.
>
> *Grounded in: this session's PR #79 creation returned `422 Validation Failed [{Resource:PullRequest Field:head Code:invalid Message:}]` but the PR was created and merged. A naive retry would have hit a different 422 ("No commits between main and branch") and led to misdiagnosis.*

### Why this earns its place in your agents file

The asymmetric cost is the same shape as the WebFetch case: an unverified retry can succeed spuriously (PR exists, second call returns its own ambiguous error), or fail for a misleading reason ("no commits between" when the branch was already merged), or succeed by creating a duplicate PR if the API state had time to catch up. Each of these wastes minutes of agent time on misdiagnosis.

Marginal cost of adoption: one extra MCP call per retry. Cost of not having it: 5-15 minutes of confused debugging per occurrence, plus possibly a duplicate PR that the user has to close.

---

## Suggestion 3: Use `AskUserQuestion` before bulk multi-document design work

### Proposed addition

> **Before producing 3+ inter-referential design documents, ask the user 2-4 structured `AskUserQuestion` questions about the structural axes you can't infer.** Group related axes in one call (up to 4 questions per `AskUserQuestion` invocation). Each option must name a trade-off, not just a label. Include `(Recommended)` for defensible defaults. Cap rounds at 3 per session. Restate combined answers before writing.
>
> *Grounded in: this session's design of `pipeline-skills-package/` (13 inter-referential docs) was preceded by 4 `AskUserQuestion` calls. Three of four `(Recommended)` defaults were chosen; one was overridden. The override changed install structure for all skills — a guess would have triggered ~3000 lines of rework.*

### Why this earns its place in your agents file

Multi-doc design has a high consistency cost: every cross-reference depends on a shared model in the agent's head. The marginal cost of 60 seconds of user time up front is dwarfed by the cost of rewriting 8+ docs to match the user's actual preference. The `(Recommended)` annotation is doubly useful: it tells the user what the agent thinks AND gives the user a low-friction confirmation path when the recommendation is right.

Marginal cost of adoption: one `AskUserQuestion` call per architectural axis. Cost of not having it: rewrites measured in thousands of lines, plus the time and trust cost of revealing late that the agent didn't ask.

---

## Suggestion 4: Distinguish "skills FROM retrospectives" from "skills FOR a process"

### Proposed addition

> **When the user asks for "skills to make this repeatable", clarify whether they mean (a) operational skills that drive a process, or (b) lesson-skills harvested from retrospectives.** These are different artifacts with different audiences. Process skills are user-facing (`SKILL.md` with trigger phrases for `Skill` tool routing). Lesson skills are spec-only artifacts under `retrospective/` that document a pattern for later implementation. Ask which is meant before producing either.
>
> *Grounded in: this session opened with a misinterpretation — when the user asked "is it useful to create the skills to make this process repeatable?", the initial answer treated existing retrospective specs as the topic. The user corrected: they meant skills that operate the protocol as an execution engine.*

### Why this earns its place in your agents file

The two artifact types have similar names ("skill") and overlap conceptually but produce wildly different deliverables. Mis-identifying the user's intent costs the rest of the session: any subsequent specs / plans are misdirected. The fix is one clarifying question worth 30 seconds.

Marginal cost of adoption: one clarifying sentence in the first reply. Cost of not having it: in this session, the misinterpretation lasted one message before correction — but the lost time was non-trivial, and in less careful conversations the wrong direction can persist for multiple replies before catching.

---

## Suggestion 5: Treat the POC as preserved; derived work goes under one subdirectory

### Proposed addition

> **The POC (`poc-github-ai-sandbox`) is a historical reference. New work that derives from it goes under a single named subdirectory at the repo root (e.g. `pipeline-skills-package/`). Don't modify POC operational files (`.agent/`, `.github/workflows/`, `_agent_runs`, existing `tests/`, existing `skills/`). The boundary between POC and derived work must be obvious at a glance.**
>
> *Grounded in: this session created `pipeline-skills-package/` with 13 new design docs. POC's 446-test baseline stayed green because nothing under the POC tree was touched.*

### Why this earns its place in your agents file

Without this rule, derived work tends to leak into POC paths: a "small fix" to a workflow YAML, a "synced" copy of a script, a "convenience" addition to an existing test file. Each one weakens the POC's role as a reliable historical reference. The rule keeps the boundary clean: anyone reading the repo can tell at a glance what's POC vs what's the next phase.

Marginal cost of adoption: minor friction when the agent wants to "just fix this one thing." Cost of not having it: the POC stops being a reliable baseline, and `git diff main` becomes hard to read.

---

## Suggestion 6: AGENTS.md and CLAUDE.md are sacred — never edit beyond a pointer line

### Proposed addition

> **Onboarding skills, scaffolding flows, and template installers must never edit `AGENTS.md` or `CLAUDE.md` beyond adding a single pointer line that references another file. Even the pointer line requires explicit per-file user approval. People copy these files between projects; in-place edits break that copy-flow.**
>
> *Grounded in: this session's `pipeline-skills-package/skills/onboarding/SPEC.md` codifies this rule. The user explicitly stated "Some people copy their agents.md or Claude.md from project to project, so try very hard to install the skills into the project without changing those two files if possible."*

### Why this earns its place in your agents file

`AGENTS.md` and `CLAUDE.md` are personal artifacts — users tune them and carry them across projects. A skill that helpfully appends 50 lines of project-specific guidance breaks every future copy-paste. The rule limits the damage to a single pointer line, which the user can audit before approving.

Marginal cost of adoption: skill authors must put project-specific content in a separate file rather than inline. Cost of not having it: every per-project skill author adds their own block, and the user's portable agents file fragments into project-specific accretion.

---

## Suggestion 7: Local git proxy can lag the GitHub state — verify via MCP when in doubt

### Proposed addition

> **When the local git proxy returns unexpected output (e.g. `git ls-remote` empty after a successful push, or `git pull` reporting nothing new despite known upstream changes), verify the actual GitHub state via `mcp__github__list_branches` and `mcp__github__list_commits` before acting on the local view. The proxy can be eventually consistent rather than strongly consistent.**
>
> *Grounded in: this session's PR #79 troubleshooting. Local `git ls-remote origin claude/install-tooling-skills` returned empty, but the branch was on origin (confirmed via `mcp__github__list_branches`). And `origin/main` locally was at `8c8b123` while GitHub's actual main was at `077ce13` — the proxy had not propagated the merge yet.*

### Why this earns its place in your agents file

The local git proxy in this sandbox environment is fast but not strongly consistent with GitHub. A `git push` may complete locally before the remote registers; subsequent local reads see the old state. Treating the local view as authoritative leads to misdiagnosis. MCP calls go directly to GitHub's API and reflect current state. When the two disagree, MCP wins.

Marginal cost of adoption: one or two extra MCP calls per ambiguous moment. Cost of not having it: minutes of debugging based on stale local state, eventually resolved by `git fetch` — but only if the agent thought to fetch.

---

## Suggestion 8: Plans designed for parallel execution must use the parallel-subagent-fanout pattern explicitly

### Proposed addition

> **Multi-step plans intended for parallel / unattended execution must follow the `parallel-subagent-fanout` skill's pattern: state.json at `runs/<run_id>/state.json` for restart safety, single-message wave dispatch, `isolation: "worktree"` on every Agent call, plan-order merge (never completion order), explicit MAX_PARALLEL cap. Don't invent ad-hoc parallel-execution structure for plans the protocol already covers.**
>
> *Grounded in: this session's `PLAN-PACKAGE.md` and `NEW-REPO-PLAN.md` both adopt the parallel-subagent-fanout pattern wholesale, with explicit references to the skill in `software-factory`.*

### Why this earns its place in your agents file

Parallel agent dispatch has subtle traps (worktree contamination, merge-order non-determinism, restart-incoherent state). The `parallel-subagent-fanout` skill encodes the right patterns. Re-deriving them from scratch per plan loses correctness. Citing the skill explicitly forces the plan to align.

Marginal cost of adoption: a few sentences in each parallel-execution plan. Cost of not having it: each plan slowly drifts away from the canonical pattern, and concurrent-execution bugs accumulate.
