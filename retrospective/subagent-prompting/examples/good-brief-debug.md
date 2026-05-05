# Good brief example: workflow-debug subagent

This brief enumerated 7 hypotheses for an unknown bug and gave the
subagent explicit "pivot if stuck" instructions. It found the root
cause (lock-vs-bot) in ~13 minutes — substantially faster than I would
have found it solo.

## Why this worked

- **Hypotheses listed**, not just "find the bug." Subagent didn't
  spelunk randomly.
- **Concrete diagnostic steps**, with specific files to verify.
- **Pivot signal**: "If you're stuck after 30 minutes, propose a
  pivot." Bounded the worst-case time.
- **Token discovery hint**: told the subagent to check env vars for
  a usable token, in case the workflow path was a dead end.
- **Constraint on side effects**: "don't post more than ~10 new
  comments on issue #11."

## Original brief (excerpts)

> You're debugging why GitHub Actions workflows for the
> agent-job-protocol POC at `/home/user/poc-github-ai-sandbox` aren't
> executing the diagnostic markers we added.
>
> ## Symptoms
> [5 bullet points listing concrete observed state]
>
> ## Your tools
> - All `mcp__github__*` MCP tools (full surface — search GitHub via
>   `ToolSearch` for `select:...` to load specific tool schemas).
> - `WebFetch` for public GitHub pages.
> - Bash for local repo work, `git` operations, running tests, editing files.
> - You CANNOT use `gh` CLI or REST directly (no token).
>
> ## Hypotheses to investigate (any of which could be the bug)
> 1. The `if:` clause is silently false — maybe `github.event.issue.locked`
>    is not present in `issue_comment` payloads (try removing one
>    condition at a time).
> 2. The workflow file on `main` isn't what we think it is...
> 3. Permissions issue: maybe `secrets.GITHUB_TOKEN` doesn't have
>    permission to post comments...
> 4. GitHub Actions has a delay we haven't accounted for.
> 5. Webhook isn't firing for comments at all...
> 6. YAML parse error in the workflow.
> 7. Repo has Actions disabled, or has reached a billing limit, or is paused.
>
> ## Concrete diagnostic steps to take
> 1. [specific steps with file paths and tool calls]
> ...
>
> ## IMPORTANT — don't loop forever
> Try diagnostics with ~30 minutes of effort cap. If you're stuck after
> that, propose a PIVOT. A reasonable pivot would be: skip the workflow
> side entirely and **simulate the workflow handler** by running
> `python .agent/scripts/handler.py` LOCALLY...
>
> ## When done
> Report back EXACTLY:
> 1. Root cause if found, with evidence.
> 2. Steps you took.
> 3. Any PRs you opened (numbers) and whether you merged them.
> 4. Final test count (after any changes).
> 5. Recommendation for next step: continue debug, accept the
>    workaround, or pivot.

## What the subagent produced

In ~13 minutes:
- Created two diagnostic PRs (#15 and #16)
- Discovered the root cause (lock blocks GITHUB_TOKEN writes)
- Reported with evidence (the actual error message from the failing
  github-script step)
- Recommended a fix (drop the lock at issue creation)

## Pattern to extract for the skill

For debug tasks, always include:
1. Numbered hypotheses
2. Concrete diagnostic steps (don't make the subagent invent them)
3. Time cap with explicit pivot suggestion
4. Side-effect budget ("at most N new comments / branches / PRs")
5. Structured report format
