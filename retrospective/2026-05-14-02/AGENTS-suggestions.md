# AGENTS.md suggestions — 2026-05-14-02

These are proposed additions to the project's agents file
(`AGENTS.md` at the repo root). Each section contains:

1. **Proposed addition** — the exact text to paste.
2. **Why this earns its place in your agents file** — the argument
   for doing it, grounded in something that happened in the session.

Decide each on its own merits. Skip ones that don't apply to your
operating posture; copy-paste the ones that do.

---

## Suggestion 1: Audit `.gitignore` before parallel fanout

### Proposed addition

> **Audit `.gitignore` before dispatching parallel subagents that will write to new top-level paths.**
> Before fanning out N ≥ 2 subagents whose deliverables land at new top-level directories (especially names like `lib/`, `dist/`, `build/`, `output/`), run `git check-ignore -v <representative-planned-path>` once per distinct new top-level dir. If anything reports a match, narrow the offending rule (prefer rooted `/dir/` or a specific negation) BEFORE dispatching — do NOT push the workaround onto subagents.
>
> *Grounded in: 2026-05-14 build run — three of six parallel subagents independently invented a nested `.gitignore` with `!lib/` rules to defeat a repo-root `lib/` rule, while two others used `git add -f`. Two parallel mechanisms for the same problem and a cleanup commit after merge.*

### Why this earns its place in your agents file

When a single shared blocker exists at the dispatcher level, parallel subagents will each rediscover and route around it differently — there's no coordination channel. The 2026-05-14 fanout produced two distinct workaround patterns (nested-gitignore-negation vs `git add -f`) plus one cleanup commit after merge to remove the redundant nested files. Total cost: ~10 minutes of avoidable rework + a confusing merge state where three sibling skill dirs had identical-looking `.gitignore` files that did nothing once the root was fixed.

The pre-flight check is a single `git check-ignore -v` per distinct new top-level dir — typically 1-5 invocations for a 6-subagent fanout. That's seconds of dispatcher time to spend in exchange for not coordinating workarounds across N agents who can't see each other.

---

## Suggestion 2: Prefer rooted `/dir/` over bare `dir/` in `.gitignore`

### Proposed addition

> **Prefer rooted `/dir/` over bare `dir/` for Python build-output gitignore rules.**
> The Python convention `dist/`, `build/`, `lib/` (cookiecutter-style) excludes a directory of that name *at any depth* in the tree. This silently swallows new packages that bundle their own `lib/` or build outputs. Always root these with a leading `/` (`/dist/`, `/build/`, `/lib/`) unless you actively want depth-anywhere matching.
>
> *Grounded in: 2026-05-14 build run — bare `dist/` rule made `pipeline-skills-package/bootstrap/dist/install.md` and `MANIFEST.txt` invisible to `git add`, requiring a rule rewrite + `git check-ignore` verification mid-Phase-6.*

### Why this earns its place in your agents file

Bare-name gitignore rules are a footgun specific to the Python-cookiecutter convention. They look harmless for years until a new sub-package adds a directory of the same name. Then they hide files silently — `git status` shows nothing, the commit appears clean, and the absence is only caught later when CI or contract tests fail.

The fix is one character (a leading `/`). The cost of not having the rule is intermittent silent file loss in any project that grows new top-level packages, sometimes years after the gitignore was last touched. Make the cheap change once.

---

## Suggestion 3: When MAX_PARALLEL ≥ N, dispatch all subagents in one message

### Proposed addition

> **Dispatch all N parallel subagents in a SINGLE message when MAX_PARALLEL ≥ N.**
> Two-wave dispatch (e.g. 4 + 2) is only required when the harness caps concurrent agents below N. Otherwise the single-message form is identical in safety, simpler to track, and produces results faster (no wait-for-wave-1-before-launching-wave-2 latency). Subagents in the same message do not share state — only the dispatcher does — so isolation is unaffected.
>
> *Grounded in: 2026-05-14 build run — PLAN-PACKAGE.md prescribed 4+2 waves, but user authorised parallelism ≥ 100. All 6 dispatched in one message; all 6 returned within 12 minutes wall clock; zero conflicts on merge.*

### Why this earns its place in your agents file

Wave-dispatch was a fall-back pattern for early Claude Code where parallelism was capped at 4. Modern harnesses with explicit `MAX_PARALLEL` settings remove the need for that pattern when N ≤ the cap. Defaulting to one-message dispatch is simpler — one batch of results to collect, one update to state.json after — and faster — total wall clock is max(per-subagent times) rather than max(wave 1) + max(wave 2).

The only reason to keep wave-dispatch in the rotation is if the failure-mode of wave 1 should influence wave 2's brief content. For a homogeneous fanout where each subagent owns disjoint paths, that condition doesn't apply.

---

## Suggestion 4: Subagent briefs must specify what to do about cross-cutting blockers

### Proposed addition

> **When dispatching parallel subagents, anticipate cross-cutting blockers and prescribe a single resolution.**
> If you know that ALL N subagents will hit the same environmental issue (a gitignore rule, a missing dependency, a confusing error message, a sandbox limit), explicitly tell every subagent in the brief: "When you hit X, do Y." If you didn't see it coming, immediately update the in-progress fanout's coordination channel (state.json + a follow-up dispatcher message) the moment the first subagent reports it.
>
> *Grounded in: 2026-05-14 build run — three subagents independently invented a nested-gitignore workaround for a repo-root `lib/` rule; two others used `git add -f`. The dispatcher had not predicted the issue and did not tell anyone how to handle it.*

### Why this earns its place in your agents file

Parallel subagents are smart enough to route around blockers, but each one will choose its own workaround. The cost is N inconsistent mechanisms for one problem. The cure is a single sentence in the brief — and if the dispatcher only learns of the issue mid-fanout, a single coordination update is still cheaper than letting the inconsistency propagate.

This rule is the prophylactic of Suggestion 1 (audit gitignore before): Suggestion 1 prevents the issue; this rule constrains the response if it slips through.

---

## Suggestion 5: Recipe-style text encoders must round-trip a file's exact bytes

### Proposed addition

> **A text-content encoder that inlines file contents into a recipe / manifest format MUST preserve trailing newlines.**
> Don't `content.rstrip("\n")` when emitting content into a fenced block. Use `lines.extend(content.split("\n"))` (which keeps an empty trailing element when content ends in `\n`) so the parser can reconstruct the original bytes. Verify with a round-trip test: encode → decode → compare to original bytewise.
>
> *Grounded in: 2026-05-14 build run — `bootstrap/build.py` first draft used `rstrip("\n")` when inlining each file; `test_archive_round_trip` caught 190 file mismatches between tarball-extracted and recipe-applied trees, each off by exactly one byte (the missing newline).*

### Why this earns its place in your agents file

Trailing newlines are a famously easy thing to drop without noticing. They don't change rendering, don't break parsing, don't show in most diffs — but they make sha256 sums differ. For any pipeline that round-trips files through a recipe or manifest format and later compares against the originals, a one-byte-per-file drift is the difference between green and red.

The cost of the rule is one habit-of-mind. The cost of not having it is rediscovering the bug every time someone writes a new encoder.

---

## Suggestion 6: Test parametrize sets must reflect the data actually under test

### Proposed addition

> **When you `@pytest.mark.parametrize` over a set of items, double-check that every item in the set has the data the test expects.**
> A test like `for x in PARAMS: assert checked > 0` will fail when one of the PARAMS contributes zero checked items — not because the code is wrong, but because the parametrize set is too wide. Either narrow the set, or change the assertion to `assert checked >= 0` with a separate test asserting at least one PARAM has data.
>
> *Grounded in: 2026-05-14 build run — `test_template_parity[onboarding]` failed because onboarding bundles only freshly-authored templates (no POC-source byte-match to check), but the test was parametrized over all 4 template-bundling skills with a `checked > 0` assertion. Fix was to narrow the parametrize set to the 3 skills that bundle POC-sourced templates.*

### Why this earns its place in your agents file

Parametrize-set-too-wide is a subtle test-authoring bug that looks like a production-code defect when CI fires red. The first reaction is "what's wrong with onboarding's templates?" — but the answer is "the test asked the wrong question." Cost of the rule: a moment of thought when authoring parametrize sets. Cost of skipping it: a confusing red CI signal that lies about which subsystem is broken.

---

## Suggestion 7: Read the existing AGENTS.md before adding to it

### Proposed addition

> **Before adding a new convention to `AGENTS.md`, grep it for existing rules that overlap. Update or extend, do not duplicate.**
> The agents file is a living artifact; conventions accrete over months. New rules added blindly create two parallel versions of the same lesson, which is worse than no rule at all (now there's a contradiction). Always `grep -i` for the new rule's keywords first.
>
> *Grounded in: 2026-05-14 retro authoring — without checking, the retro could have proposed "Always use isolation: worktree for parallel subagents", which is already covered by `AGENTS.md`'s `### Subagent dispatch` section. The pre-write grep caught the duplication; otherwise this file would have shipped a redundant rule.*

### Why this earns its place in your agents file

This is a meta-rule about how to grow the agents file safely. A 264-line AGENTS.md (which this repo's is, today) is long enough that no one remembers all of it. New conventions are easy to add by accident. The cure is one `grep` before each addition.

The marginal cost is seconds. The marginal benefit is preserving the agents file's signal-to-noise ratio over time.
