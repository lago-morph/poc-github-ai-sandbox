# Adapter alternatives

Five candidate shapes, A through E, ordered from "most like the
current GitHub design" to "most distinct from it." Pick exactly one as
the chosen alternative in `DECISION.md`, possibly with named hybrid
adjustments. Each alternative is independently viable on the free tier.

For each, this file documents:

- **Substrate.** Where the task record and job record live.
- **Trigger.** How an agent-submitted job causes Pipelines to run.
- **Logs and summary.** Where job artifacts go.
- **Brief substrate.** Where long-form instructions live.
- **Dashboard.** What the human operator sees.
- **Custom MCP scope.** How much MCP code we have to build/own.
- **Atlassian product needs.** Which products you must subscribe to.
- **Atlassian admin needs.** What configuration the admin must do.
- **Awkward parts.** Where the design has tension.
- **What gets simpler vs. the GitHub POC.** Workaround eliminations.

---

## Alternative A — Bitbucket-only, PR-as-task

Closest to "drop in Bitbucket where GitHub was, change as little as
possible," constrained by Bitbucket Issues sunsetting in August.

- **Substrate.** Pull request as the task record. PR description holds
  a typed-fields preamble (markdown table or fenced JSON, same trade-
  offs as today's `agent-meta`). Job record: PR comment.
- **Trigger.** Webhook → tiny relay → POST `/2.0/repositories/{ws}/{repo}/pipelines/`
  with `target.selector.type=custom`, `target.selector.pattern=batch-job-handler`,
  variables = `{PR_NUMBER, COMMENT_ID, BRANCH, SHA, COMMAND, ARGS}`.
  Relay can be a Cloudflare Worker / AWS Lambda / Forge function.
- **Logs and summary.** `_agent_runs` orphan branch, identical to
  GitHub. Bitbucket `POST /src` writes, same chunked-gzip JSONL design.
- **Brief substrate.** Markdown file at `prompts/<branch-name>.md` on
  the feature branch (or default branch); URL referenced from PR
  description. Or PR description body itself if short.
- **Dashboard.** Bitbucket native PR list with filters; no rich
  cross-task view.
- **Custom MCP scope.** Bitbucket-only MCP, ~10 tools (PR CRUD,
  comment CRUD, file read/write, branch ops, pipeline trigger). Could
  fork `aashari/mcp-server-atlassian-bitbucket` and extend.
- **Atlassian product needs.** Bitbucket Cloud only.
- **Atlassian admin needs.** Pipelines enabled; one repo variable for
  the agent's API token; webhook configured to point at the relay.
- **Awkward parts.**
  - Loses the "task without code yet" affordance — must commit *some*
    initial branch state to open a PR.
  - PR description is a poor fit for long-form briefs (Bitbucket
    markdown rendering is limited; large descriptions are hard to
    read).
  - PR comments lack a true "edit-in-place" event; if the relay
    listens to `pullrequest:comment_updated` as well, you get
    re-triggering risk.
  - Webhook relay is a third party (or Forge) you have to host and
    monitor.
- **What gets simpler vs. GitHub POC.** Almost nothing. This is a
  port. The structural workarounds (`agent-meta` block, two-field
  comment convention, lock-at-close) all carry over near-identically.

---

## Alternative B — Bitbucket + Jira; Jira holds tasks, Bitbucket holds jobs

Hybrid: Jira issue as the durable task record, Bitbucket PR comments
as the job record. The "task without code yet" state lives naturally
in Jira; commits and PRs follow.

- **Substrate.** Jira issue (project `AGENT`, type `Agent Task`) for
  the task. Bitbucket PR comment for each job.
- **Trigger.** Bitbucket `pullrequest:comment_created` webhook → relay
  → Pipelines API. Same relay shape as Alternative A.
- **Logs and summary.** `_agent_runs` orphan branch on Bitbucket.
- **Brief substrate.** Jira issue Description field for short briefs;
  optional Confluence page (linked from the issue) for long-form.
- **Dashboard.** Jira Kanban board on the Agent project. Native, zero
  code.
- **Custom MCP scope.** Bitbucket MCP (~10 tools) + Jira MCP (~10
  tools — issue CRUD, JQL, transitions, comments, fields, links).
  Plus optional Confluence MCP (~6 tools) if briefs go there.
- **Atlassian product needs.** Bitbucket Cloud + Jira Software Cloud
  (Free OK).
- **Atlassian admin needs.** Jira project with custom issue type,
  custom fields, workflow, permission scheme. Bitbucket-Jira link
  configured (Smart Commits). Pipelines enabled.
- **Awkward parts.**
  - Mixed substrate: cross-product debugging means looking at both
    Jira and Bitbucket UIs.
  - Job records on Bitbucket lack Jira's rich state machine; you
    re-implement the comment-edit-in-place pattern from the GitHub
    POC, and inherit its workarounds.
  - Heartbeat / takeover semantics live on Jira (good) but jobs live
    on Bitbucket (uses comment edit-in-place); the protocol straddles
    two state shapes.
- **What gets simpler vs. GitHub POC.**
  - Task-side: no `agent-meta` block; typed fields; native workflow;
    JQL-based claiming; native audit log; native staleness detection
    via Jira Automation.
  - Workflow `lock-and-sweep` and `close-on-merge` workflows can be
    deleted (replaced by Jira workflow + Smart Commits).
  - `runner-failure` queue becomes an Automation rule.
  - Job-side: still has the comment-as-record pattern with all its
    workarounds.

---

## Alternative C — Bitbucket + Jira; Jira holds tasks AND jobs

Jira sub-tasks as the job record. Bitbucket is purely code+pipelines.
The protocol's "comment-as-job-record" idiom dies; jobs are first-class
Jira sub-tasks with typed fields and their own lifecycle.

- **Substrate.** Jira issue (`Agent Task`) for the task. Jira sub-task
  (`Agent Job`) for each job, parented to the task.
- **Trigger.** Jira Automation rule on Job sub-task creation: "Send
  web request → POST `/pipelines/` with selector + variables." Native
  to Jira; no external relay.
- **Logs and summary.** Two options:
  - **C1: keep `_agent_runs`** orphan branch (mechanically identical
    to today). Pipelines writes; agent reads via Bitbucket MCP.
  - **C2: Jira attachments** on the Job sub-task for small artifacts.
    `_agent_runs` only for runs that exceed Jira's 10 MB attachment
    cap. Fewer dependencies on cross-product reads.
- **Brief substrate.** Jira issue Description, possibly with a
  Confluence-page link.
- **Dashboard.** Jira Kanban board; sub-tasks roll up to parent.
- **Custom MCP scope.** Bitbucket MCP (~10 tools, but no
  comment-CRUD-at-scale needed) + Jira MCP (~12 tools: issue, sub-task,
  fields, transitions, JQL, attachments, links, properties).
- **Atlassian product needs.** Bitbucket Cloud + Jira Software Cloud.
- **Atlassian admin needs.** Two custom issue types (Task, Job), each
  with its own workflow; field configuration scheme per Job sub-type
  (one per command); Automation rule for Pipelines trigger; Permission
  scheme separating bot writes from automation writes.
- **Awkward parts.**
  - Jira Automation Free-tier monthly run cap (~500/site) constrains
    high-throughput agents. Each Job creation, transition, stale
    sweep is a run. Mitigation: paid tier (~$10/user/mo), or batch
    Automation rules.
  - Custom field configuration per command is admin-UI clickwork;
    less reproducible than YAML schemas. Mitigation: Jira-as-Code
    tooling (Atlassian's REST APIs support full configuration export
    /import) or just commit screenshots.
- **What gets simpler vs. GitHub POC.**
  - Drops `agent-meta`, HTML-unescape, MCP-trailer tolerance,
    `lock-and-sweep`, `close-on-merge`, `status_ts` heartbeat, the
    two-field comment convention, the `agent-task` label as ACL.
  - Job lifecycle becomes a Jira workflow with native transitions
    instead of `run_status`/`agent_ack` JSON dance.
  - Half of `.agent/scripts/` and the bulk of skill code shrinks.

This is the Atlassian-native sweet spot if you have Jira already.

---

## Alternative D — Bitbucket + Jira + Confluence

C, plus Confluence as the document substrate for briefs and run logs.

- **Substrate.** Jira issue (Task), Jira sub-task (Job).
- **Trigger.** Jira Automation rule.
- **Logs and summary.** Confluence pages — one per Job sub-task in an
  `Agent Runs` space. Manifest fields are page properties; chunks are
  attachments or code-block sections; summary is rendered as a panel.
  The **Page Properties Report macro** auto-generates the dashboard.
- **Brief substrate.** Confluence page per Task. The Jira Task carries
  only a summary line plus a "Brief" link field.
- **Dashboard.** Confluence space with embedded Jira board + auto-
  generated page-properties table + (optionally) Confluence Database
  for failures, Whiteboard for DAG visualisation.
- **Custom MCP scope.** Bitbucket (~10) + Jira (~12) + Confluence (~6:
  page CRUD, page properties, attachments, Smart-Link resolve). Or
  adopt Atlassian Rovo MCP (covers all three) and add only the gaps
  (Bitbucket Issues isn't there — but we don't need it; Jira Issues
  custom-fields-write coverage may have gaps).
- **Atlassian product needs.** Bitbucket Cloud + Jira Software Cloud +
  Confluence Cloud. All on one Atlassian organisation.
- **Atlassian admin needs.** Everything from C, plus: Confluence space,
  page templates, Page Properties Report macro setup, optional
  Confluence Database setup.
- **Awkward parts.**
  - Most moving parts of any alternative; biggest setup burden.
  - Three free-tier user caps to keep an eye on (Jira, Bitbucket,
    Confluence).
  - Confluence page writes from the agent require the Confluence MCP
    or REST; large-log writes via REST need attachment-multipart
    handling.
- **What gets simpler vs. GitHub POC.** All of C's wins, plus:
  - `_agent_runs` orphan branch goes away entirely (or is reduced to
    only the very-large-log fallback case).
  - Dashboard is Confluence Page Properties Report — auto-generated,
    no code.
  - Long-form briefs stop being squeezed into issue body.
  - Three-substrate audit trail (Jira issue history + Confluence page
    history + Bitbucket commit history) is stronger than GitHub's
    single audit thread.

This is the strongest design if "use what Atlassian gives you" is the
goal and the user has all three products.

---

## Alternative E — Out-of-the-box: brief-as-contract, agent never creates tasks

Same substrate as C or D, but with a different agent-side contract.

- **Substrate.** Confluence page using a fixed front-matter template is
  the canonical "task." A "Run" button on the page (Smart Link / button
  macro / Forge function) creates the Jira Task and the first Job
  sub-task. The agent **never creates tasks** — it claims tasks
  pre-staged by humans, executes them, opens PRs.
- **Trigger.** Jira Automation rule (as in C / D).
- **Logs and summary.** Confluence pages (as in D) or Jira attachments
  (as in C2). Pick at decision time.
- **Brief substrate.** The Confluence page IS the brief; nothing else
  is needed.
- **Dashboard.** Confluence space with the page-properties macro plus
  embedded Jira board.
- **Custom MCP scope.** Same as D, minus task-creation tools (the
  agent doesn't need to write to Jira's create-issue API). Slightly
  smaller surface.
- **Atlassian product needs.** Bitbucket Cloud + Jira Software Cloud +
  Confluence Cloud.
- **Atlassian admin needs.** Everything from D, plus the Forge-function
  / button-macro that creates Jira issues from a Confluence page.
- **Awkward parts.**
  - Asymmetric: humans-create, agents-only-claim. Closes the
    schedule_successors flow unless the agent is granted task-creation
    permissions selectively.
  - Adds a Forge function or equivalent — small but real.
- **What gets simpler vs. GitHub POC.** Everything in D, plus:
  - The agent's task-creation API can be removed; the skill API
    shrinks.
  - "Briefs are documents" is a clean human story; humans can
    collaborate on briefs in Confluence (versioning, inline comments)
    before the agent picks them up.
  - Inline Confluence comments on the brief give a clean
    clarification channel.

---

## At-a-glance comparison

| Dimension | A | B | C | D | E |
|---|---|---|---|---|---|
| Substrate complexity | low | medium | medium | high | high |
| Atlassian admin burden | low | medium | medium-high | high | high |
| Custom MCP code | small | medium | medium | larger | larger |
| Free-tier fit (1–2 ppl + agents) | OK | OK | OK | OK | OK |
| Eliminates `agent-meta` workaround? | no | yes (task) | yes | yes | yes |
| Eliminates comment-as-job workaround? | no | no | yes | yes | yes |
| Eliminates `_agent_runs` orphan branch? | no | no | partial (C2) | yes (D) | yes |
| Native dashboard? | weak | yes (Jira board) | yes | yes (Confluence) | yes |
| Pipelines trigger needs external relay? | yes | yes | no (Jira Automation) | no | no |
| Agent harness changes (with refactor)? | none | none | none | none | none |
| "Task without code yet" state? | no | yes | yes | yes | yes |
| Bitbucket Issues exposure? | no | no | no | no | no |

## How to use this in the conversation

When walking the decision questions in `DECISION-QUESTIONS.md`, treat
these alternatives as a forest you eliminate down to one tree. Each
question typically eliminates 1–2 alternatives. Track elimination as
you go, and confirm with the user.
