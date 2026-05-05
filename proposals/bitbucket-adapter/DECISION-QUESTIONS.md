# Decision questions

Walk these in order. Each cluster eliminates one or more alternatives.
Ask one cluster at a time, reflect the user's answer, then move on.

After each cluster, state which alternatives in `ALTERNATIVES.md` are
still in the running and which are eliminated. The user should be able
to track the funnel.

---

## Cluster 1 — Atlassian product baseline

**Why it matters.** This eliminates the largest swathes of alternatives
in one go.

Ask:

1. Which Atlassian Cloud products do you currently subscribe to (or
   are willing to subscribe to on a Free plan)? Options: Bitbucket,
   Jira Software, Confluence, Atlassian Rovo MCP server.
2. Are all those products on the same Atlassian organisation, or
   separate?
3. Approximately how many people will be in each product (humans +
   agent service accounts), to confirm Free-tier user-cap fit?

**Elimination logic.**

- "Bitbucket only" → only Alternative A is viable.
- "Bitbucket + Jira" (no Confluence) → eliminate D, E. B and C remain.
- "Bitbucket + Jira + Confluence" → all five remain; favour C/D/E.
- "Already paying for all three" → cost objections to D/E disappear.

---

## Cluster 2 — Task-without-code-yet

**Why it matters.** This is the single biggest discriminator between
Alternative A and everything else.

Ask:

1. Should agents be able to claim a task that has no code branch /
   commit yet — i.e., a fresh "research and decide" task? Or is every
   task always rooted in an existing PR?
2. Do you want humans (or other agents) to be able to schedule tasks
   ahead of time as a backlog?

**Elimination logic.**

- "Yes, tasks-without-code is a hard requirement" → eliminate A.
- "No, every task has a PR from the start" → A is fine, but only A;
  everything else still works.

---

## Cluster 3 — Job-record substrate

**Why it matters.** This decides whether the protocol's
"comment-as-job-record" pattern survives or is replaced by Jira sub-
tasks.

Ask:

1. How many jobs per task do you typically expect? (1–3, 5–10, 20+?)
2. Do you want jobs to have their own typed lifecycle (status,
   started_at, finished_at, summary) visible in a UI without clicking
   in?
3. Do you want the operator to be able to query "all running jobs
   across all tasks" easily?

**Elimination logic.**

- "Many jobs, want native lifecycle, want cross-task queries" →
  Jira-sub-tasks-as-jobs is strongly favoured. Lean toward C, D, or E.
- "Few jobs, comment-as-record is fine" → B is acceptable; saves the
  cost of configuring Jira sub-task workflows.

---

## Cluster 4 — Brief substrate

**Why it matters.** Decides whether Confluence enters the picture for
documents.

Ask:

1. How long are typical task briefs? (One paragraph, one page, ten
   pages?)
2. Do humans collaborate on briefs before agents start work? (Inline
   comments, edits, reviews?)
3. Do briefs need rich content (diagrams, tables, embedded media,
   cross-references)?

**Elimination logic.**

- "Short, one-and-done briefs" → Jira Description is fine; eliminate
  D's Confluence-for-briefs strength; D loses some of its appeal.
- "Long, collaborative, rich" → Confluence becomes high-value;
  Alternative D or E is favoured.

---

## Cluster 5 — Pipelines trigger architecture

**Why it matters.** Decides whether you must host an external relay
or can use Atlassian-native machinery.

Ask:

1. Do you have a place to host a small webhook receiver (Cloudflare
   Worker, AWS Lambda, Forge function)? Or do you want to avoid that?
2. Are you OK with Jira Automation rules running ~500 invocations per
   month per site on Free, or do you expect higher volume?

**Elimination logic.**

- "Want to avoid external infra" → favour C, D, E (Jira Automation as
  the relay).
- "External relay is fine" → A and B remain viable; relay is small.
- "High volume" → may need to upgrade Jira plan or batch automations.

---

## Cluster 6 — Run logs and artifacts

**Why it matters.** Decides whether the `_agent_runs` orphan branch
survives.

Ask:

1. Approximately how large are typical run logs? (KB, MB, hundreds of
   MB?)
2. Do you want logs to be human-browsable in a UI without git tooling?
3. Are you OK with logs living on Bitbucket forever (public-repo
   exposure considerations)?

**Elimination logic.**

- "Logs are small, want UI browsability" → favour Jira attachments
  (C2) or Confluence pages (D, E).
- "Logs are large or run-frequent" → keep `_agent_runs` (C1, A, B).
- "Logs may contain sensitive data" → confirm sanitiser is in place
  regardless of substrate.

---

## Cluster 7 — Dashboard expectations

**Why it matters.** Decides whether Confluence's auto-dashboard is
worth the setup cost.

Ask:

1. Who is the primary audience for the dashboard — agent operators,
   project managers, both?
2. Do they want a single view that aggregates tasks, jobs, runs, and
   open PRs across the whole agent activity?
3. Are you willing to set up a Confluence space with the Page
   Properties Report macro, or would you rather a Jira board be enough?

**Elimination logic.**

- "Just need a Jira board" → eliminate D's Confluence dashboard
  advantage; B/C remain favoured.
- "Want a rich human-facing operator view" → D or E.

---

## Cluster 8 — Agent task creation

**Why it matters.** Decides between Alternative E (humans-create only)
and the others (agent-can-create).

Ask:

1. Should agents be able to schedule successor tasks (e.g.,
   "spec → implement → test" handoff)?
2. Or should every task originate from a human posting a brief?

**Elimination logic.**

- "Agents schedule successors" → eliminate E (or accept a hybrid
  where agents have a constrained scheduling permission).
- "Humans only" → E is viable and clean.

---

## Cluster 9 — Custom MCP vs. Atlassian Rovo MCP

**Why it matters.** Decides how much MCP code we own vs. consume.

Ask:

1. Are you willing to depend on Atlassian Rovo MCP (official, GA, but
   today missing Bitbucket Issues coverage and possibly other gaps),
   or do you want full control via a custom MCP server we own?
2. Are you sensitive to the "API token only" auth on Rovo Bitbucket
   tools (no OAuth yet), or is that fine for service accounts?
3. Are you willing to fork an OSS Bitbucket MCP (e.g.
   `aashari/mcp-server-atlassian-bitbucket`) as a starting point?

**Elimination logic.**

- "Use Rovo if it covers it" → check coverage gaps in the chosen
  alternative; possibly hybrid (Rovo for what it covers, custom for
  the rest).
- "Custom MCP, full control" → plan implementation scope.
- "Fork OSS MCP" → write up the diff against the chosen alternative.

---

## Cluster 10 — Configuration reproducibility

**Why it matters.** Decides whether the Atlassian admin clickwork is
acceptable or needs to be Jira-as-Code.

Ask:

1. Will the Jira project / workflow / fields / permission scheme be
   set up once, or do you expect to reproduce it across environments
   (dev, staging, prod sites)?
2. Is the team willing to maintain Jira-as-Code (REST-driven config
   export/import) if reproducibility matters?

**Elimination logic.**

- "Set up once, never again" → admin UI clickwork is fine.
- "Reproducible across sites" → add Jira-as-Code as a sub-deliverable
  of the chosen alternative.

---

## Cluster 11 — Migration affordances

**Why it matters.** What if the user later wants to swap backends
again, or run two backends simultaneously during transition?

Ask:

1. Do you want the GitHub backend to remain operable in parallel, or
   is the Bitbucket adapter a replacement?
2. Are existing GitHub-side tasks/jobs in scope for migration, or is
   this a fresh start?
3. Should the Bitbucket adapter respect the same `protocol_version`
   bumps as GitHub, or is it allowed to diverge?

**Elimination logic.**

- "Parallel operation" → make sure the agent-API refactor lands
  first (it does, in the sibling package); driver selection by config.
- "Replacement" → simpler, but inform the user of the cutover plan.

---

## Cluster 12 — POC delta cross-check

**Why it matters.** Some POC discoveries change which alternative is
safe.

For each POC delta surfaced in Step 1 (`POC-REVIEW.md`), ask:

1. Did this delta come from a GitHub-specific limitation, or a more
   general substrate concern?
2. Does the chosen alternative inherit or eliminate this concern?

If a chosen alternative inherits a known POC failure mode without
mitigation, name it explicitly in `DECISION.md`.

---

## After Cluster 12

By this point you should have one alternative standing (possibly with
hybrid notes). Confirm the user's choice with a short recap:

- "We're going with Alternative {X}, with {hybrid adjustments}."
- "These were the eliminations and why."
- "These open questions are deferred to implementation: {...}."
- "These admin prerequisites are needed before implementation can
  start: {...}."

Then write `DECISION.md` per `OUTPUT-TEMPLATE.md`.
