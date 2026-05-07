# Skill: `yaml-literal-fallback`

## Why this skill matters

GitHub Actions repo variables (`vars.X`) require admin setup. A
deployment to a fresh repo where the admin hasn't set the variable
will silently break: workflow `if:` clauses comparing
`comment.user.login == vars.AGENT_LOGIN` evaluate to
`comment.user.login == null` = false, and the workflow never fires
on any comment.

The fix is a one-line YAML expression: `${{ vars.X || 'literal' }}`.
Both expressions evaluate at workflow start. When `vars.X` is set,
it wins. When it's empty, the literal kicks in. New deployments still
override (just set the variable); the literal is a safety net for the
canonical / reference deployment.

This pattern is small but easy to lose during refactors. It's worth
a skill because:
1. The failure mode is silent (the workflow run just doesn't happen).
2. The fix has to land in TWO places (`if:` clause + `env:` block).
3. Without unit tests pinning the literal in the YAML, a
   well-intentioned cleanup will remove it and re-introduce the
   silent-break failure mode.

## When it would have helped

**Session 3, scenario 01 first attempt (issue #55):** PR #54 had
just merged the session-3 changes, including removal of the static
`agent_login` config key. The workflow YAMLs used
`${{ vars.AGENT_LOGIN }}` everywhere — but the canonical repo had
no such repo variable set. Lock-and-sweep workflow ran, env var was
empty, script exited 1 silently. No `agent-task` label applied. No
diagnostic comment (return-code-1 path doesn't trigger the
self-diagnostic).

**Fix (PR #56):** added `${{ vars.AGENT_LOGIN || 'jonathanmanton' }}`
to all three workflow YAMLs (one in the `if:` clause, three in `env:`
blocks). Pinned in `tests/unit/test_workflow_yamls.py` (4 new tests).
Re-ran scenario 01 in a fresh issue (#57) — labeled within 30s, full
lifecycle completed in 3 minutes.

Without this skill: every fresh deployment of this protocol would
silently break until an admin happened to set `vars.AGENT_LOGIN`.
The new-user experience would be "doesn't work, no error message".

## What "good looks like"

- Every YAML expression that reads `vars.X` (or `env.Y`, or
  `secrets.Z` where a literal default makes sense) uses the
  `${{ ... || 'literal' }}` form.
- The literal matches the canonical repo's known-good value.
- Unit tests pin the literal pattern in each YAML file (text-level
  assertions are sufficient — no need to parse YAML).
- HANDOFF.md / AGENTS.md include a "don't remove this fallback"
  rule so future cleanup doesn't accidentally regress it.

## Cousin skills

- `retrospective/agents-md-template` (session 2) — the umbrella
  pattern for capturing one-liner deployment rules in `AGENTS.md`.
- [`live-test-after-substantive-merge`](../live-test-after-substantive-merge/) — how to surface this kind of bug.

## Status

**Spec only — no code yet.** The fallback pattern is implemented in
the three workflow YAMLs in this repo and pinned in
`tests/unit/test_workflow_yamls.py`. The skill generalizes the
pattern.
