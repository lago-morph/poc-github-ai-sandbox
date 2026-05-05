# Output template — DECISION.md

When you finish the conversation, write the synthesis to
`proposals/bitbucket-adapter/DECISION.md` using this structure.
Keep it short — under 500 words is ideal. A future implementation
agent will read this in five minutes and produce a proper
implementation brief from it.

```markdown
# Bitbucket adapter — decision

Decided: <date>, by: <user-handle>, agent session: <session-id>

## Chosen alternative

**Alternative <X>** from `ALTERNATIVES.md`, with the following
adjustments: <list any hybrid choices, or "none">.

One-line rationale: <why this beat the other alternatives>.

## POC deltas (informing this decision)

### Confirmed in POC
- ...

### Diverges from SPEC.md
- ...

### Open / unverified
- ...

## Substrate

- Task record: <Jira issue type X | Bitbucket PR | Confluence page | ...>
- Job record: <Jira sub-task type X | Bitbucket PR comment | ...>
- Logs: <_agent_runs branch | Jira attachments | Confluence pages | ...>
- Brief: <Jira Description | Confluence page | repo file | ...>
- Dashboard: <Jira Kanban | Confluence space | ...>

## Trigger

How a job submission causes Pipelines to run:
<Jira Automation rule | Bitbucket webhook → relay → Pipelines API | ...>

If a relay is needed, where it's hosted and who owns it:
<Cloudflare Worker / Lambda / Forge function / etc.>

## Atlassian product needs

- [ ] Bitbucket Cloud (Free / Standard / Premium)
- [ ] Jira Software Cloud (Free / Standard / Premium)
- [ ] Confluence Cloud (Free / Standard / Premium)
- [ ] Atlassian Rovo MCP (yes / no / partially)

User-cap accounting:
- Humans: <n>
- Agent service accounts: <n>
- Total per product: <n> (vs. Free cap)

## Atlassian admin prerequisites

The following must be configured before implementation can start:

- [ ] Project: <name, key, type>
- [ ] Issue types: <list>
- [ ] Custom fields: <list, with types>
- [ ] Workflow(s): <Task / Job, with statuses and transitions>
- [ ] Permission scheme: <who-can-write-what>
- [ ] Automation rules: <list>
- [ ] Confluence space + templates (if applicable): <list>
- [ ] Bitbucket-Jira link (Smart Commits): yes/no
- [ ] Pipelines enabled, repo variables: <list>
- [ ] Webhooks (if Alternative A or B): <event types, target URL>

## Custom MCP scope

What we own:
- [ ] Bitbucket MCP — wraps Bitbucket REST. Tools: <list>.
      Source: <new build | fork of aashari/... | Rovo passthrough>
- [ ] Jira MCP — wraps Jira REST. Tools: <list>.
- [ ] Confluence MCP — wraps Confluence REST. Tools: <list>. (omit if
      not in scope)

What we depend on:
- [ ] Atlassian Rovo MCP for: <list of operations>

## TaskBackend driver mapping

Outline how each method on the neutral `TaskBackend` Protocol (see
`proposals/agent-api-refactor/INTERFACE.md`) is implemented in the
chosen alternative. One bullet per Protocol method; one line each.

- `find_claimable_tasks` → <JQL: project = AG AND status in (Open, Stale)>
- `read_task(task_id)` → <Jira REST GET /issue/{key}>
- `submit_job(...)` → <Jira REST POST /issue (sub-task) with custom fields>
- `read_job(job_id)` → <Jira REST GET /issue/{key}>
- `ack_job(job_id)` → <Jira REST PUT /issue/{key} setting custom field>
- `read_brief(task)` → <Confluence REST GET /content/{id}/expand=body.atlas_doc_format>
- ...

If a Protocol method has no clean mapping, call it out as a
"capability gap" — implementation will need to either add the gap to
the Protocol or surface it via `capabilities()`.

## Capabilities advertised

Which `Capability` flags from `INTERFACE.md` does this driver
advertise?

- [ ] `native_heartbeat`
- [ ] `field_history`
- [ ] `smart_commits`
- [ ] `permission_split`

## Open questions deferred to implementation

These came up but were not resolved in this session. The
implementation pass should resolve before merging.

- ...

## Estimated effort

- MCP server(s): <person-days>
- Driver implementation: <person-days>
- Atlassian admin configuration: <person-hours>
- Tests: <person-days>

## What this does NOT include

- The agent-API refactor (separate package: `proposals/agent-api-refactor/`).
  This decision assumes the refactor has landed.
- Migration of GitHub-side tasks (out of scope unless explicitly added).
- Production hardening of the trigger relay (if applicable).
```

## Length guidance

Aim for ~300–500 words filling in this template. If you find yourself
exceeding 1000 words, you are over-specifying — push detail into the
implementation brief that comes later.

## Where to commit it

`proposals/bitbucket-adapter/DECISION.md` on the same branch as the
package. Open a PR if not already on one.
