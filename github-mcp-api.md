# GitHub MCP Server — API Reference

Source: https://github.com/github/github-mcp-server

Tools are grouped by **toolset**. Toolsets can be enabled/disabled at server start via `--toolsets` or `GITHUB_TOOLSETS`. Default toolsets when none specified: `context`, `repos`, `issues`, `pull_requests`, `users`.

## Conventions

- Params: `name (type, R|O)` — R=required, O=optional. Types: `str`, `int`, `bool`, `str[]`, `obj`, `obj[]`.
- Common params (omitted from descriptions when self-evident):
  - `owner` (str): repo owner login (user or org)
  - `repo` (str): repo name
  - `page` (int), `perPage`/`per_page` (int): pagination (max ~100)
  - `after`/`before` (str): cursor pagination (GraphQL-backed tools)
- Some tools dispatch on a `method` param — valid values are listed in the tool's notes.
- Tool naming: snake_case. Some related operations are consolidated under `*_read` / `*_write` / `*_get` / `*_list` dispatchers.

---

## Toolset: context

User/auth context.

| Tool | Description |
|------|-------------|
| `get_me` | Authenticated user profile. No params. |
| `get_teams` | List teams for a user. Params: `user` (str, O). |
| `get_team_members` | List team members. Params: `org` (str, R), `team_slug` (str, R). |

---

## Toolset: actions

GitHub Actions workflows, runs, jobs, artifacts, logs.

### `actions_list`
List Actions resources.
- `method` (str, R): one of `list_workflows`, `list_workflow_runs`, `list_workflow_jobs`, `list_workflow_run_artifacts`
- `owner`, `repo` (R)
- `resource_id` (str, O): workflow id/filename for runs; run id for jobs/artifacts
- `workflow_runs_filter` (obj, O): filter by `actor`, `branch`, `event`, `status`
- `workflow_jobs_filter` (obj, O): `latest` or `all`
- `page`, `per_page` (O)

### `actions_get`
Get a specific Actions resource.
- `method` (str, R): `get_workflow`, `get_workflow_run`, `get_workflow_job`, `download_workflow_run_artifact`, `get_workflow_run_usage`, `get_workflow_run_logs_url`
- `owner`, `repo`, `resource_id` (R)

### `actions_run_trigger`
Run, rerun, cancel, or clear logs for workflows/runs.
- `method` (str, R): `run_workflow`, `rerun_workflow_run`, `rerun_failed_jobs`, `cancel_workflow_run`, `delete_workflow_run_logs`
- `owner`, `repo` (R)
- `workflow_id` (str, conditional): required for `run_workflow`
- `ref` (str, conditional): required for `run_workflow`
- `inputs` (obj, O): workflow inputs
- `run_id` (int, conditional): required for all methods except `run_workflow`

### `get_job_logs`
Retrieve workflow job logs.
- `owner`, `repo` (R)
- `job_id` (int, conditional): required unless `failed_only=true`
- `run_id` (int, conditional): required when `failed_only=true`
- `failed_only` (bool, O): logs for all failed jobs in a run
- `return_content` (bool, O): return content instead of URLs
- `tail_lines` (int, O): lines from end (default 500)

---

## Toolset: code_security

Code scanning alerts.

### `get_code_scanning_alert`
- `owner`, `repo`, `alertNumber` (int) — all R

### `list_code_scanning_alerts`
- `owner`, `repo` (R)
- `ref` (str, O), `severity` (str, O), `state` (str, O), `tool_name` (str, O)

---

## Toolset: copilot

### `assign_copilot_to_issue`
Assign Copilot coding agent to an issue.
- `owner`, `repo`, `issue_number` (int) — R
- `base_ref` (str, O): starting git ref
- `custom_instructions` (str, O)

### `request_copilot_review`
Request Copilot review on a PR.
- `owner`, `repo`, `pullNumber` (int) — R

---

## Toolset: dependabot

### `get_dependabot_alert`
- `owner`, `repo`, `alertNumber` (int) — R

### `list_dependabot_alerts`
- `owner`, `repo` (R)
- `severity` (str, O), `state` (str, O)

---

## Toolset: discussions

GraphQL-backed.

### `list_discussions`
- `owner` (R); `repo` (str, O — omit for org-level)
- `category` (str, O), `orderBy` (str, O), `direction` (str, O)
- `after` (str, O), `perPage` (int, O)

### `list_discussion_categories`
- `owner` (R); `repo` (O)

### `get_discussion`
- `owner`, `repo`, `discussionNumber` (int) — R

### `get_discussion_comments`
- `owner`, `repo`, `discussionNumber` (R)
- `after` (str, O), `perPage` (int, O)

---

## Toolset: gists

### `list_gists`
- `username` (str, O), `since` (str, O — ISO 8601), `page` (O), `perPage` (O)

### `get_gist`
- `gist_id` (str, R)

### `create_gist`
- `filename` (str, R), `content` (str, R)
- `description` (str, O), `public` (bool, O)

### `update_gist`
- `gist_id`, `filename`, `content` (R)
- `description` (str, O)

---

## Toolset: git

### `get_repository_tree`
File/directory structure at a ref or SHA.
- `owner`, `repo` (R)
- `tree_sha` (str, O): SHA, branch, or tag — defaults to default branch
- `recursive` (bool, O): default false
- `path_filter` (str, O): path prefix (e.g. `src/`)

---

## Toolset: issues

### `issue_read`
Read issue data.
- `method` (str, R): `get`, `get_comments`, `get_sub_issues`, `get_labels`
- `owner`, `repo`, `issue_number` (int) — R
- `page`, `perPage` (O)

### `issue_write`
Create or update an issue.
- `method` (str, R): `create`, `update`
- `owner`, `repo` (R)
- `issue_number` (int, conditional): required for `update`
- `title` (str, O), `body` (str, O)
- `assignees` (str[], O), `labels` (str[], O)
- `milestone` (int, O), `type` (str, O)
- `state` (str, O): `open`, `closed`
- `state_reason` (str, O): e.g. `completed`, `not_planned`, `reopened`, `duplicate`
- `duplicate_of` (int, O): issue # when `state_reason=duplicate`

### `list_issues`
- `owner`, `repo` (R)
- `state` (str, O), `labels` (str[], O), `since` (str, O — ISO 8601)
- `orderBy` (str, O), `direction` (str, O)
- `after` (str, O), `perPage` (int, O)

### `search_issues`
- `query` (str, R): GitHub search syntax
- `owner` (str, O), `repo` (str, O): scope to repo
- `sort` (str, O), `order` (str, O), `page` (O), `perPage` (O)

### `add_issue_comment`
- `owner`, `repo`, `issue_number`, `body` (str) — R

### `sub_issue_write`
Manage sub-issue relationships.
- `method` (str, R): `add`, `remove`, `reprioritize`
- `owner`, `repo`, `issue_number`, `sub_issue_id` (int) — R
- `replace_parent` (bool, O): for `add`
- `after_id` (int, O), `before_id` (int, O): for `reprioritize`

### `list_issue_types`
- `owner` (str, R): organization login

---

## Toolset: labels

### `list_label`
- `owner`, `repo` (R)

### `get_label`
- `owner`, `repo`, `name` (str) — R

### `label_write`
- `method` (str, R): `create`, `update`, `delete`
- `owner`, `repo`, `name` — R
- `color` (str, O): hex without `#`
- `description` (str, O)
- `new_name` (str, O): for `update`

---

## Toolset: notifications

### `list_notifications`
- `filter` (str, O): e.g. `default`, `include_read_notifications`, `only_participating`
- `since` (str, O), `before` (str, O)
- `owner` (str, O), `repo` (str, O): scope
- `page`, `perPage` (O)

### `get_notification_details`
- `notificationID` (str, R)

### `dismiss_notification`
- `threadID` (str, R), `state` (str, R): `read` or `done`

### `mark_all_notifications_read`
- `lastReadAt` (str, O — ISO 8601)
- `owner` (O), `repo` (O): scope to a repo

### `manage_notification_subscription`
Watch/ignore/delete a thread subscription.
- `notificationID` (str, R), `action` (str, R): `ignore`, `watch`, `delete`

### `manage_repository_notification_subscription`
Watch/ignore/delete a repo subscription.
- `owner`, `repo`, `action` — R; `action`: `ignore`, `watch`, `delete`

---

## Toolset: orgs

### `search_orgs`
- `query` (str, R)
- `sort` (str, O), `order` (str, O), `page` (O), `perPage` (O)

---

## Toolset: projects

GitHub Projects (v2). All methods take `owner_type` (str, O) of `user` or `org`.

### `projects_get`
Get project resources.
- `method` (str, R): operations include `get_project`, `get_project_field`, `get_project_item`, `get_status_update`, etc.
- `owner` (str, O), `owner_type` (O)
- `project_number` (int, O)
- `field_id` (int, O), `item_id` (int, O), `status_update_id` (str, O)
- `fields` (str[], O): field IDs to include

### `projects_list`
List project resources.
- `method` (str, R): listing operations (e.g. `list_projects`, `list_project_fields`, `list_project_items`, `list_status_updates`)
- `owner` (str, R), `owner_type` (O)
- `project_number` (int, O)
- `query` (str, O), `fields` (str[], O)
- `after`/`before` (str, O), `per_page` (int, O)

### `projects_write`
Modify project items, fields, status updates.
- `method` (str, R): create/update/delete operations
- `owner`, `project_number` — R; `owner_type` (O)
- `item_id` (int, O), `item_type` (str, O): `issue` or `pull_request`
- `item_owner` (str, O), `item_repo` (str, O)
- `issue_number` (int, O), `pull_request_number` (int, O)
- `updated_field` (obj, O): field update payload
- `body` (str, O), `start_date` (str, O), `target_date` (str, O), `status` (str, O)

---

## Toolset: pull_requests

### `create_pull_request`
- `owner`, `repo`, `title`, `head`, `base` — R
- `body` (str, O), `draft` (bool, O), `maintainer_can_modify` (bool, O)

### `list_pull_requests`
- `owner`, `repo` (R)
- `state` (str, O): `open`, `closed`, `all`
- `head` (str, O), `base` (str, O)
- `sort` (str, O), `direction` (str, O)
- `page`, `perPage` (O)

### `search_pull_requests`
- `query` (str, R)
- `owner` (O), `repo` (O), `sort` (O), `order` (O), `page` (O), `perPage` (O)

### `pull_request_read`
Read PR data.
- `method` (str, R): `get`, `get_diff`, `get_status`, `get_files`, `get_review_comments`, `get_reviews`, `get_comments`, `get_check_runs`
- `owner`, `repo`, `pullNumber` (int) — R
- `page`, `perPage` (O)

### `update_pull_request`
- `owner`, `repo`, `pullNumber` — R
- `title` (str, O), `body` (str, O), `state` (str, O)
- `base` (str, O), `draft` (bool, O), `maintainer_can_modify` (bool, O)
- `reviewers` (str[], O)

### `merge_pull_request`
- `owner`, `repo`, `pullNumber` — R
- `merge_method` (str, O): `merge`, `squash`, `rebase`
- `commit_title` (str, O), `commit_message` (str, O)

### `update_pull_request_branch`
Update PR branch with base.
- `owner`, `repo`, `pullNumber` — R
- `expectedHeadSha` (str, O)

### `pull_request_review_write`
Manage reviews and review threads.
- `method` (str, R): `create` (pending review), `submit`, `delete`, `resolve_thread`, `unresolve_thread`
- `owner`, `repo`, `pullNumber` — R
- `body` (str, O): review body
- `commitID` (str, O): SHA for the review
- `event` (str, O): `APPROVE`, `REQUEST_CHANGES`, `COMMENT` (for `submit`)
- `threadId` (str, O): node ID (for resolve/unresolve)

### `add_comment_to_pending_review`
Append a file comment to the current pending review.
- `owner`, `repo`, `pullNumber`, `path`, `body`, `subjectType` (str) — R
- `subjectType`: `LINE` or `FILE`
- `line` (int, O), `side` (str, O): `LEFT`/`RIGHT`
- `startLine` (int, O), `startSide` (str, O): for multi-line comments

### `add_reply_to_pull_request_comment`
Reply to an existing PR review comment.
- `owner`, `repo`, `pullNumber`, `commentId` (int), `body` — R

---

## Toolset: repos

### `create_repository`
- `name` (str, R)
- `organization` (str, O), `description` (str, O)
- `private` (bool, O), `autoInit` (bool, O)

### `fork_repository`
- `owner`, `repo` (R)
- `organization` (str, O): destination org

### `search_repositories`
- `query` (str, R)
- `sort` (O), `order` (O), `page` (O), `perPage` (O)
- `minimal_output` (bool, O): trimmed payload

### `search_code`
- `query` (str, R)
- `sort` (O), `order` (O), `page` (O), `perPage` (O)

### `list_branches`
- `owner`, `repo` (R), `page` (O), `perPage` (O)

### `create_branch`
- `owner`, `repo`, `branch` (str) — R
- `from_branch` (str, O): defaults to default branch

### `list_commits`
- `owner`, `repo` (R)
- `sha` (str, O): branch, tag, or SHA
- `path` (str, O): filter by file path
- `author` (str, O): username or email
- `since` (str, O — ISO 8601), `until` (str, O — ISO 8601)
- `page`, `perPage` (O)

### `get_commit`
- `owner`, `repo`, `sha` — R
- `include_diff` (bool, O), `page` (O), `perPage` (O)

### `get_file_contents`
- `owner`, `repo` (R)
- `path` (str, O): file or dir; omit for repo root
- `ref` (str, O): branch/tag
- `sha` (str, O): commit SHA

### `create_or_update_file`
- `owner`, `repo`, `path`, `content` (str), `message`, `branch` — R
- `sha` (str, O): required when updating an existing file

### `delete_file`
- `owner`, `repo`, `path`, `message`, `branch` — R

### `push_files`
Push multiple files in a single commit.
- `owner`, `repo`, `branch`, `message` — R
- `files` (obj[], R): items shaped `{ path: str, content: str }`

### `list_tags`
- `owner`, `repo` (R), `page` (O), `perPage` (O)

### `get_tag`
- `owner`, `repo`, `tag` (str) — R

### `list_releases`
- `owner`, `repo` (R), `page` (O), `perPage` (O)

### `get_latest_release`
- `owner`, `repo` (R)

### `get_release_by_tag`
- `owner`, `repo`, `tag` — R

---

## Toolset: secret_protection

### `get_secret_scanning_alert`
- `owner`, `repo`, `alertNumber` (int) — R

### `list_secret_scanning_alerts`
- `owner`, `repo` (R)
- `state` (str, O), `secret_type` (str, O), `resolution` (str, O)

---

## Toolset: security_advisories

### `get_global_security_advisory`
- `ghsaId` (str, R): `GHSA-xxxx-xxxx-xxxx`

### `list_global_security_advisories`
- `ghsaId` (O), `cveId` (O), `cwes` (str[], O)
- `type` (str, O), `severity` (str, O), `ecosystem` (str, O)
- `affects` (str, O): affected package(s)
- `isWithdrawn` (bool, O)
- `published` (str, O), `updated` (str, O), `modified` (str, O)

### `list_repository_security_advisories`
- `owner`, `repo` (R)
- `state` (str, O), `sort` (str, O), `direction` (str, O)

### `list_org_repository_security_advisories`
- `org` (str, R)
- `state` (str, O), `sort` (str, O), `direction` (str, O)

---

## Toolset: stargazers

### `list_starred_repositories`
- `username` (str, O — defaults to authenticated user)
- `sort` (str, O), `direction` (str, O), `page` (O), `perPage` (O)

### `star_repository`
- `owner`, `repo` (R)

### `unstar_repository`
- `owner`, `repo` (R)

---

## Toolset: users

### `search_users`
- `query` (str, R)
- `sort` (O), `order` (O), `page` (O), `perPage` (O)

---

## Quick lookup index

| Need | Tool |
|------|------|
| Who am I | `get_me` |
| Read file | `get_file_contents` |
| Write file | `create_or_update_file` |
| Bulk file commit | `push_files` |
| Repo tree | `get_repository_tree` |
| Make branch | `create_branch` |
| Open PR | `create_pull_request` |
| PR diff | `pull_request_read` (`method=get_diff`) |
| PR files | `pull_request_read` (`method=get_files`) |
| PR CI status | `pull_request_read` (`method=get_status` or `get_check_runs`) |
| Submit review | `pull_request_review_write` (`method=create`→`submit`) |
| Inline review comment | `add_comment_to_pending_review` |
| Reply to review comment | `add_reply_to_pull_request_comment` |
| Merge PR | `merge_pull_request` |
| Open issue | `issue_write` (`method=create`) |
| Close issue | `issue_write` (`method=update`, `state=closed`) |
| Comment on issue/PR | `add_issue_comment` |
| Search issues/PRs | `search_issues` / `search_pull_requests` |
| Search code | `search_code` |
| Run workflow | `actions_run_trigger` (`method=run_workflow`) |
| Get job logs | `get_job_logs` |
| List notifications | `list_notifications` |
| Code scan alert | `get_code_scanning_alert` |
| Secret scan alert | `get_secret_scanning_alert` |
| Dependabot alert | `get_dependabot_alert` |
