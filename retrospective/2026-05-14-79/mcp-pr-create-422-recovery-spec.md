# Spec: `mcp-pr-create-422-recovery`

## Intent

The GitHub MCP `create_pull_request` tool can return `422 Validation Failed` in two completely different cases that the response body does not distinguish well:

1. **The PR was not created** — head branch invalid, target conflict, malformed input.
2. **The PR was created but the response also includes a follow-up validation failure** — this happened in this session for PR #79: the call returned `422 Validation Failed [{Resource:PullRequest Field:head Code:invalid Message:}]` but the PR was on GitHub, and got merged before the agent realized.

A naive retry on the 422 sometimes succeeds (case 1 was real and the second attempt actually creates the PR) and sometimes returns "No commits between main and the branch" (case 2 — the PR exists, you can't create another). Without verifying state between attempts, the agent gets confused.

The cost of unverified retries: in this session, the second attempt returned a different error (`No commits between main and branch`) because by then the PR had been merged by the user and the branch had been merged into main, so there were genuinely no commits left. The agent assumed something was wrong with the branch and started inspecting `git ls-remote` (which itself had a quirk — see the local-proxy notes in `AGENTS-suggestions.md`). Eventually checking `list_branches` revealed the truth.

This skill enforces a verify-then-act loop around `create_pull_request`.

## Trigger

Activate when:

- About to call `mcp__github__create_pull_request`.
- A prior call returned 422 and the agent is about to retry.
- A prior call returned a success response but the PR cannot be found (rare; safety net).

**Direct triggers**:
- "Open a PR for this branch"
- "Create a pull request from <branch> to <base>"

**Negative triggers**:
- The user has already explicitly verified the PR's state.
- A different tool is being used (`gh pr create`, web UI).

## Inputs

- `owner`, `repo`, `head`, `base`, `title`, `body` (the standard create-PR inputs).
- An optional `expected_commits_min` (default 1) — the minimum number of commits between `base` and `head` that the call expects.

## Outputs

- Either the PR number + URL (success path).
- Or a typed error explaining which case applies: `branch_invalid`, `pr_already_exists`, `no_commits_between`, `unknown_422`.

## Workflow

1. **Pre-flight**: Before calling `create_pull_request`, run `mcp__github__list_branches` and confirm `head` is present at the expected SHA. If absent or at the wrong SHA, push first.
2. **Pre-flight commit count**: Compare `head` SHA to `base` SHA. If they're equal, surface `no_commits_between` before calling the API.
3. **Call `create_pull_request`**.
4. **On success response**: extract the PR URL and number. Done.
5. **On `422` error**:
   a. Wait briefly (~2s) to allow GitHub state propagation.
   b. Call `mcp__github__list_pull_requests` with `head: <owner>:<branch>` to check if a PR was created.
   c. If a PR exists with this head branch and matching base, that PR is the result. Return it. Surface a note: "create_pull_request returned 422 but the PR was created."
   d. If no PR exists, call `list_commits sha=<branch>` to verify the branch state on GitHub.
   e. If commit count between base and head is zero, return `no_commits_between` with a remediation hint (push more commits or rebase).
   f. Otherwise, try once more with the same input. If that also fails, return `unknown_422` with full error context.
6. **Never retry the same call more than twice.** Two attempts is the cap. After that, surface to the user.

## Concrete examples

### Example 1: 422 returned but PR was created

Agent calls `create_pull_request(head=claude/install-tooling-skills, base=main)`. Response: `422 Validation Failed [{Resource:PullRequest Field:head Code:invalid Message:}]`.

Skill action: wait 2s, call `list_pull_requests(head=lago-morph:claude/install-tooling-skills)`. Response: 1 PR found, number 79, state: open. Skill returns: "PR #79 was created despite the 422 response."

Agent moves on to subscribe / report; the user merges PR #79 a few minutes later.

### Example 2: 422 because the branch has no commits

Agent has a fresh branch `feature/x` at the same SHA as `main`. Calls `create_pull_request(head=feature/x, base=main)`. Response: `422 Validation Failed [{Resource:PullRequest Field: Code:custom Message:No commits between main and feature/x}]`.

Skill action: skip the API retry. Call `list_commits sha=feature/x` and compare to `main`. Confirms 0 commits. Return `no_commits_between` with remediation: "the branch has no commits beyond `main` — either there's nothing to merge, or your local commits haven't been pushed to origin yet."

## Anti-patterns

- **Re-running `create_pull_request` immediately on 422 without verification.** The second attempt either succeeds spuriously or fails for a different reason, masking the original cause.
- **Trusting only the API response.** GitHub's REST 422 body sometimes includes the validation field, sometimes doesn't. Always verify against `list_pull_requests` and `list_branches`.
- **Skipping the pre-flight branch+SHA check.** A `git push` from a sandbox can race with PR creation; if the branch isn't on origin at the expected SHA when `create_pull_request` runs, the result is unpredictable.
- **Polling `list_pull_requests` in a tight loop after a 422.** One check after a brief delay is enough. Tight polling exhausts rate limits and rarely changes the answer.

## Acceptance criteria

1. After a 422 response, the skill verifies PR existence before any retry.
2. The skill returns a typed error (`branch_invalid` / `pr_already_exists` / `no_commits_between` / `unknown_422`) rather than just bubbling up the raw API error.
3. Retries are capped at one (total two attempts including the original).
4. Pre-flight catches the zero-commits case before the API call, avoiding unnecessary 422 noise.
5. The skill correctly handles the "422-but-PR-was-created" case observed in PR #79.

## Files this skill creates / modifies

- None on disk. The skill is a wrapper around MCP calls.
- Optionally writes a `pr-create-attempts.log` to the session's working directory if `--log` is passed, capturing each attempt's input + response.
