# `live-debug-from-mcp-only` skill

> Debugging GitHub Actions failures when you only have MCP tools and
> can't read workflow logs. The marker-comment + self-diagnostic
> patterns developed live in this session.

## Why this skill

GitHub Actions workflow logs require auth to view. Even on **public**
repos, the log archive endpoint and the per-run detail page hit a
sign-in wall. WebFetch returns "Sign in to view logs" or "Sorry,
something went wrong."

An MCP-only agent has no way to see why a workflow failed. The
default behavior — workflow run shows red X, exit code 1, no further
info — is a debugging dead end.

This skill encodes the workarounds that got us from "completely
opaque" to "actionable diagnostic data" in this session.

## When this would have helped

In this session: PRs #13–#16 all silently failed because of the
lock-vs-bot bug. The handler workflow ran, exited 1, but I couldn't
see why. Three rounds of failed comment-posts wasted ~90 minutes
before the diagnostic patterns surfaced enough info to find the root
cause.

If this skill had existed at the start, the patterns would have been
in the workflow YAML by default, and the debug session would have
been ~10 minutes instead of 90.

## What good looks like

The patterns:

1. **Workflow markers**: first step in the YAML posts a "started"
   comment via curl; final step (`if: always()`) posts an "ended"
   comment with the conclusion + last 4KB of stdout/stderr base64-
   encoded.
2. **Self-diagnostic from the script**: on uncaught exception, the
   Python script `requests.post`s a comment with the full traceback.
3. **Embedded log tail**: the marker comment includes the last 4KB
   as base64 so an MCP-only agent can decode it locally.

All readable via `mcp__github__issue_read get_comments`.

## Cousins

- **`github-mcp-tips`** — the broader tips list; this skill is a
  focused subskill.
- **`spec-vs-implementation-gap-discovery`** — most of the bugs this
  diagnostic system surfaces are spec gaps, not impl bugs.

## Status

- Spec only — see `SPEC.md`.
- Templates in `templates/` (workflow YAML snippets, Python
  diagnostic helper).
- No code yet.
