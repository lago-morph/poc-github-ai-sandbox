# proposals/

Two independent agent-session packages. Each is a self-contained brief that
you hand to a fresh Claude Code (or equivalent) session. They do NOT depend
on each other and can be run in either order.

## Package 1: `agent-api-refactor/`

**What it does.** Refactors the agent-facing skill API (in `skills/`) so the
backend (today: GitHub MCP; tomorrow: Bitbucket / Jira / Confluence) can be
swapped without changing any agent code, prompt, or skill documentation.

**When to run.** Any time. Designed to be safe to run in parallel with the
in-progress GitHub POC implementation work — its scope is the skill layer
and a new driver abstraction; it deliberately does not touch the workflow
scripts or YAML files that the POC owns.

**How to use.** Open a fresh agent session in the repo and tell it:

> Read `proposals/agent-api-refactor/README.md` and complete the refactor
> described there. Stay strictly within the scope listed in `SCOPE.md`.

The package is self-contained; the agent will follow it through to a PR.

## Package 2: `bitbucket-adapter/`

**What it does.** Drives a back-and-forth conversation with you to decide
*which* Bitbucket-shaped backend to build, then synthesises the decision
into a concrete adapter design. It is intentionally a decision-support
package, not an implementation brief.

**When to run.** After the GitHub POC has settled enough that its lessons
are usable input. This package's first instruction to the agent is to
review the as-built POC before consulting the alternatives, so any
divergence from the original SPEC informs the Bitbucket design.

**How to use.** Open a fresh agent session in the repo and tell it:

> Read `proposals/bitbucket-adapter/README.md` and walk me through the
> decision conversation it describes. Do not start implementing; we are
> only deciding.

The package guides the agent to:
1. Review the as-built GitHub POC and note any deltas from `SPEC.md`.
2. Read the consolidated background research (so you don't redo it).
3. Walk through the alternative designs.
4. Ask you the decision questions in a structured order.
5. Produce a final adapter-design document for a future implementation
   session.

## Why two packages

These two efforts are orthogonal:

- The refactor is mechanical: rename the skill API, introduce a driver
  Protocol, supply one driver (GitHub) so nothing breaks.
- The Bitbucket decision is strategic: which substrate, which products,
  which trade-offs.

Doing them together would couple decisions that don't need coupling.
Doing the refactor first means the Bitbucket adapter is "just a second
driver" when its time comes.
