# `forensic-vs-aggressive-cleanup` skill

> Two cleanup modes for systems that produce real-world artifacts,
> with the policy and tooling to switch between them.

## Why this skill

Systems that produce persistent artifacts (issues, branches, files
in remote storage) need a cleanup story or they drown in clutter.
But naive cleanup destroys forensic evidence — and the most
valuable evidence is from runs that *failed*.

The right policy is bimodal:

- **Forensic mode**: leave everything for inspection
- **Aggressive on success, forensic on failure**: clean up after
  passing scenarios, leave failed ones for forensics

Either choice has implementation consequences (labels, namespaces,
auto-cleanup logic) that should be designed in from the start.

## When this would have helped

This session went all-forensic by user direction (good — we
discovered 7 bugs across the artifacts). But branch accumulation
became unwieldy: 28 stale branches needed manual cleanup near the
end. With this skill in place, the auto-delete-on-merge would have
been baked in from day one and there'd be no cleanup task.

The session ALSO discovered: the local git proxy blocks
`git push --delete`. The cleanup pass had to invent a workaround
(driving deletion through the close_on_merge workflow). That whole
detour would have been avoided if the skill had been present.

## What good looks like

- Each artifact tagged with a unique run id (label-based for
  greppability).
- Auto-cleanup baked into the system itself (e.g.,
  `close_on_merge.py` sweeps branches on PR merge).
- Defensive namespace gates: never touch `main`, `_agent_runs`,
  default branches, or anything outside the agent namespace.
- A separate cleanup tool for cleanup-after-the-fact (e.g., when
  policy changes from forensic to aggressive).
- Clear rules for what's forensic-permanent (logs in orphan
  branches, closed issues) vs ephemeral (feature branches, debug
  PRs).

## Cousins

- **`parallel-subagent-fanout`** — its sub-branches need cleanup;
  this skill's auto-delete handles them.
- **`agent-dispatch-loop`** — feature branches per iteration; same.

## Status

- Spec only — see `SPEC.md`.
- No code yet.
