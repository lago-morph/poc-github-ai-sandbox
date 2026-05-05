# Background research (May 2026)

Consolidated findings from earlier sessions. Treat these as inputs you
do not need to re-derive. Verify the most volatile facts (sunset dates,
free-tier limits, MCP feature coverage) at the start of your session;
if anything has shifted, note it in the POC deltas section of your
final document.

## What this repo's POC does, in one paragraph

A portable, restart-safe protocol that lets an AI agent — running in
any sandbox — submit batch jobs to GitHub Actions runners, using only
a GitHub MCP server as transport. State lives entirely in GitHub
Issues and Comments. The agent posts a structured comment on a labeled
issue; a workflow on the default branch picks it up, runs the job in a
runner that has access to repo-level secrets, writes logs and a
summary back to a `_agent_runs` orphan branch, and edits the comment
with terminal status. The agent polls the comment, reads the summary,
acks. The protocol is harness-agnostic: any agent CLI with GitHub MCP
tool access can drive it.

The full design lives in `SPEC.md`; the live POC runs are documented
in `harness/runs/`.

## What the agent needs from a backend (per the SPEC)

These are the operations the agent-side skills must perform. They are
the minimum surface a Bitbucket adapter has to cover, regardless of
which substrate it uses for tasks/jobs.

| Operation | Used by |
|---|---|
| Read task record | `claim`, `submit` preflight, `poll` heartbeat |
| Update task fields (status, agent_id, status_ts) | `claim` (handshake), `heartbeat` |
| Create task (e.g. successors, runner-failure) | `schedule_successors`, `poll` (on timeout) |
| Find claimable tasks (open, unowned, or stale) | `claim` |
| Submit a job (request envelope or equivalent) | `submit` |
| Read a job (status + summary) | `poll` |
| Edit a job (ack) | `poll` final step |
| Read a brief (long-form instructions) | `plan` |
| Read file at branch+path | `poll` (summary.json), `merge` |
| Commit file to branch | workflow-side log writes; `merge` |
| Branch ops (head SHA, delete) | `merge` |
| Create PR; link PR to task | `task-dag` PR-opening step |
| Read PR (state, merged) | downstream consumers |

## Bitbucket landscape (as of May 2026)

Three load-bearing facts, in order of severity:

1. **Bitbucket Cloud Issues are being removed on 20 Aug 2026.** Atlassian
   announced sunset of Issues *and* Wikis. As of April 2026 they're
   already disabled for new opt-ins; the entire feature disappears in
   ~3 months. Atlassian recommends migrating to Jira.
   ([sunset announcement](https://community.atlassian.com/forums/Bitbucket-articles/Announcing-sunset-of-Bitbucket-Issues-and-Wikis/ba-p/3193882))

2. **Atlassian Rovo MCP server (official) supports Bitbucket Cloud** as
   of April 2026. Coverage is **repos / PRs / pipelines** — no
   Bitbucket Issues coverage that we could find documented. Tools are
   exposed under broad names like `read_bitbucket` / `write_bitbucket`
   covering: list workspaces/repos, browse branches, read files,
   create commits, open PRs, get diffs, comment on PRs, approve,
   merge, check pipeline results. Auth is API-token-only for now (OAuth
   coming).
   ([Rovo MCP + Bitbucket](https://www.atlassian.com/blog/bitbucket/the-atlassian-rovo-mcp-server-now-supports-bitbucket-cloud),
   [supported tools](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/))

3. **Bitbucket Pipelines does not natively trigger on a comment event.**
   Native triggers are: push, pull-request, schedule, manual. The
   `issue:comment_created` and `pullrequest:comment_created` webhook
   *events* exist, but they are *outbound* webhooks that POST a payload
   to a URL of your choosing — Pipelines is not a built-in subscriber.
   To turn a comment into a pipeline run you need a small relay (a
   tiny webhook-receiver service, an Atlassian Forge app, AWS Lambda,
   or a Jira Automation rule that wraps the call).
   ([event payloads](https://support.atlassian.com/bitbucket-cloud/docs/event-payloads/),
   [Pipelines REST](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pipelines/))

Lesser facts that still matter:

- **No "lock issue" primitive** in Bitbucket Cloud (closest analogues:
  `archive` on issues, `state: closed` on PRs). The injection-guard
  role is filled by the workflow's `if:` filter in this protocol, so
  this is not blocking.
- **Pipelines step max-time is 720 minutes** (default 120). Comparable
  to GitHub Actions' 360-min hosted job cap.
  ([step options](https://support.atlassian.com/bitbucket-cloud/docs/step-options/))
- **Issue tracker REST API exists** until Aug 2026.
  ([API group](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-issue-tracker/))
- **OSS community MCP server** [`aashari/mcp-server-atlassian-bitbucket`](https://github.com/aashari/mcp-server-atlassian-bitbucket)
  covers most of the Bitbucket surface and is forkable.

## Jira capabilities relevant to this protocol

Each row is a primitive Jira gives you that would otherwise be a
workaround in the Bitbucket-only or GitHub-only design.

| Need | Jira primitive | Replaces |
|---|---|---|
| Task record with typed metadata | Issue + custom fields | `agent-meta` JSON block in body |
| Job record per dispatch | **Sub-task** under a Task | Comment-as-job-record |
| Task lifecycle | **Workflow** + Status field (state machine) | `null/working/abandoned/finished` JSON status |
| Job lifecycle | Sub-task workflow | `run_status` field convention |
| `agent_id`, `feature_branch`, etc. | Custom fields | Convention-only fields in JSON |
| `depends_on_prs` | **Issue links** ("is blocked by") | Hand-maintained array |
| `Closes #N` on PR | **Smart Commits** (`PROJ-42 #close`) | `close-on-merge.py` parser |
| Two-writer split | **Permission scheme** + per-field perms | `run_status` vs `agent_ack` convention |
| Stale takeover | **Automation rule** ("status=Running and updated > 2h → Stale") | `status_ts` heartbeat |
| `runner-failure` queue | Automation rule auto-creates a Bug task | Skill-side issue creation |
| Lock at close | Workflow post-function removes Edit perm | `lock-and-sweep` + `close-on-merge` |
| Per-command arg schemas | **Field configuration scheme** per sub-task type | `commands/*.schema.json` + Python validation |
| Audit trail | **Issue change log** + transition history | Comment-edit history |
| Foreign-comment sweep | Permission scheme refuses non-bot writes outright | Workflow `if:` filter |
| Listing claimable tasks | **JQL** | Body parsing + label filter |
| Heartbeat | Native `updated` timestamp | Custom `status_ts` field |
| Comment trigger to Pipelines | **Jira Automation** "Send web request" action | Custom Lambda relay |

## Confluence capabilities relevant to this protocol

| Need | Confluence primitive |
|---|---|
| Long-form briefs | Pages with rich content + version history |
| Run-log artifact | Pages with attachments / code blocks; one per run |
| Auto-dashboard | Page Properties Report macro (no code) |
| DAG visualisation | Whiteboards with Smart Links to Jira issues |
| Failure queue | Confluence Database (typed rows + views) |
| Cross-product audit | Smart Links between Jira issues and Confluence pages |

## Free-tier feasibility

| Product | Free tier | Fit for 1–2 humans + service accounts |
|---|---|---|
| Jira Software Cloud | 10 users, 2 GB storage, ~500 Automation runs/site/month | OK; Automation runs can be the first wall |
| Bitbucket Cloud | 5 users, 50 Pipelines build minutes/month, 1 GB Git LFS | Pipeline minutes are tight; mitigate with self-hosted runner (free) |
| Confluence Cloud | 10 users, 2 GB storage | Fine |
| All three on one Atlassian Cloud organisation | One billing surface, one identity provider | Fine |

Service accounts count as users in all three caps.

## What goes away when the substrate moves

The current GitHub-comment-as-job-record substrate forces these
workarounds. Most disappear under any Atlassian-shaped backend:

- `agent-meta` fenced JSON block in issue body (would be typed fields)
- HTML-unescape on body parse (no longer JSON in a body)
- MCP-trailer-tolerant JSON parser (no longer JSON in a body)
- Lock-at-close vs lock-at-creation correction (real permission scheme)
- `if: contains(labels, agent-task) && comment.user.login == ...` filter
  (real ACL)
- `run_status` vs `agent_ack` two-field convention (server-enforced
  per-field perms)
- `status_ts` heartbeat polling loop (native `updated`)
- `_agent_runs` orphan branch (Confluence pages or Jira attachments)
- `Closes #N` parser in close-on-merge (Smart Commits)
- `runner-failure` issue auto-creation in skill code (Automation rule)
- `agent-task` label as ACL primitive (real Permission Scheme)
- Polling with backoff (JQL queries; or, if subscribed via Jira
  webhooks, push)

## What gets harder or weirder

- The agent now needs at least two MCP servers (Jira, Bitbucket), plus
  optionally Confluence. More tool surface.
- Bitbucket Pipelines triggers are still not native to Jira-issue
  events; need Jira Automation "Send web request" or a relay.
- Free-tier Automation-run quotas could throttle.
- Atlassian APIs are spread across multiple products; custom MCP scope
  grows.
- Jira issue types come with mandatory fields you don't want; need a
  cleaned-up issue type with a screen scheme. Configuration is in
  Atlassian admin UI; less reproducible than YAML in a repo (mitigate
  with Jira-as-Code if the user cares).
- Permission schemes are per-project, configured in admin UI.

## Sources

- [Atlassian Rovo MCP Server now supports Bitbucket Cloud (Apr 2026)](https://www.atlassian.com/blog/bitbucket/the-atlassian-rovo-mcp-server-now-supports-bitbucket-cloud)
- [Atlassian Rovo MCP — Supported tools](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/)
- [Announcing sunset of Bitbucket Issues and Wikis (Aug 20, 2026)](https://community.atlassian.com/forums/Bitbucket-articles/Announcing-sunset-of-Bitbucket-Issues-and-Wikis/ba-p/3193882)
- [Bitbucket Cloud event payloads (incl. `issue:comment_created`, `pullrequest:comment_created`)](https://support.atlassian.com/bitbucket-cloud/docs/event-payloads/)
- [Bitbucket Cloud Pipelines REST API (custom trigger)](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pipelines/)
- [Bitbucket Pipelines step `max-time` (up to 720 min)](https://support.atlassian.com/bitbucket-cloud/docs/step-options/)
- [Bitbucket Cloud Issue tracker REST API](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-issue-tracker/)
- [Community OSS Bitbucket MCP server (`aashari/mcp-server-atlassian-bitbucket`)](https://github.com/aashari/mcp-server-atlassian-bitbucket)
