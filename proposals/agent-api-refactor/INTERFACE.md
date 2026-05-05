# Neutral interface

This file specifies the target shape. Treat it as authoritative; deviate
only with a note in the PR description.

## Design rule

The skill API is the *agent's* contract. It must contain no GitHub /
Bitbucket / Jira / Confluence words. The driver is the *operator's*
contract — it knows the platform.

## Neutral types

```python
# skills/backend.py

from dataclasses import dataclass
from typing import Any, Optional, Protocol, Literal, runtime_checkable

TaskHandle = str   # opaque to callers; drivers may encode (e.g., "42" or "AGENT-42")
JobHandle  = str   # opaque to callers
PRHandle   = str   # opaque to callers (e.g., "123" or "PR-123")


JobStatus = Literal["queued", "running", "completed", "errored", "parse_error"]
TaskStatus = Literal["open", "working", "stale", "abandoned", "finished"]


@dataclass
class Task:
    id: TaskHandle
    status: TaskStatus
    agent_id: Optional[str]
    session_id: Optional[str]
    feature_branch: Optional[str]
    base_branch: Optional[str]
    parent_task: Optional[TaskHandle]
    depends_on: list[str]            # opaque PR/task identifiers
    brief: Optional[str]             # short brief; long-form may live elsewhere
    brief_ref: Optional[str]         # opaque pointer the driver can resolve
    updated_ts: Optional[str]
    raw: Optional[dict[str, Any]] = None   # driver may stash escape-hatch data


@dataclass
class Job:
    id: JobHandle
    task: TaskHandle
    command: str
    args: dict[str, Any]
    branch: str
    commit_sha: str
    subagent_id: str
    status: JobStatus
    started_ts: Optional[str]
    finished_ts: Optional[str]
    summary: Optional[dict[str, Any]]
    summary_ref: Optional[str]       # opaque pointer to large summary blob
    ack_required: bool               # True until the agent has ack'd
    raw: Optional[dict[str, Any]] = None


@dataclass
class JobResult:
    job: Job
    summary: dict[str, Any]
    summary_blob: Optional[dict[str, Any]]   # parsed large summary if available


@dataclass
class PR:
    id: PRHandle
    head: str
    base: str
    state: str               # "open" | "merged" | "closed"


# Optional: capability flags drivers can advertise
Capability = Literal[
    "native_heartbeat",       # backend tracks updated_ts natively
    "field_history",          # backend audits per-field changes
    "smart_commits",          # PR merge can transition tasks via commit message
    "permission_split",       # backend can enforce per-field write permissions
]
```

## TaskBackend Protocol

```python
@runtime_checkable
class TaskBackend(Protocol):
    """The neutral interface the skills speak.

    Method names use protocol terms (task, job, brief, summary), never
    platform terms (issue, comment, envelope, agent-meta).
    """

    # Capability advertisement
    def capabilities(self) -> set[Capability]: ...

    # Tasks
    def find_claimable_tasks(self) -> list[Task]: ...
    def read_task(self, task_id: TaskHandle) -> Task: ...
    def write_task_fields(self, task_id: TaskHandle, **fields: Any) -> Task: ...
    def transition_task_status(
        self, task_id: TaskHandle, to: TaskStatus
    ) -> Task: ...
    def create_task(
        self,
        *,
        title: str,
        brief: str,
        labels: Optional[list[str]] = None,
        parent_task: Optional[TaskHandle] = None,
        depends_on: Optional[list[str]] = None,
    ) -> Task: ...
    def heartbeat_task(self, task_id: TaskHandle, agent_id: str) -> bool: ...

    # Brief resolution
    def read_brief(self, task: Task) -> str: ...

    # Jobs
    def submit_job(
        self,
        *,
        task_id: TaskHandle,
        command: str,
        args: dict[str, Any],
        branch: str,
        commit_sha: str,
        subagent_id: str,
    ) -> Job: ...
    def read_job(self, job_id: JobHandle) -> Job: ...
    def ack_job(self, job_id: JobHandle) -> Job: ...

    # Files / branches (used by merge.py and by callers fetching summaries)
    def read_file(self, ref: str, path: str) -> Optional[bytes]: ...
    def commit_file(
        self, *, branch: str, path: str, content: bytes, message: str
    ) -> None: ...
    def get_branch_head(self, branch: str) -> Optional[str]: ...
    def delete_branch(self, name: str) -> None: ...

    # PRs
    def create_pr(
        self,
        *,
        head: str,
        base: str,
        title: str,
        body: str,
        links_to_task: Optional[TaskHandle] = None,
    ) -> PR: ...
    def read_pr(self, pr_id: PRHandle) -> PR: ...

    # Large-summary resolution (driver decides where it lives)
    def read_summary_blob(self, job: Job) -> Optional[dict[str, Any]]: ...

    # Escape hatch (NOT used by skills; for operator scripts)
    def raw_client(self) -> Any: ...
```

## Skill API after refactor

```python
# skills/task-dag

def claim_task(backend: TaskBackend, *, agent_id: Optional[str] = None) -> Optional[Task]: ...
def heartbeat(backend: TaskBackend, *, task_id: TaskHandle, agent_id: str) -> bool: ...
def get_brief(backend: TaskBackend, task: Task) -> str: ...
def abandon(backend: TaskBackend, task_id: TaskHandle, reason: str) -> None: ...
def merge_subagent_branches(
    backend: TaskBackend, *, feature_branch: str, subagent_branches: list[str]
) -> None: ...
def open_pr(
    backend: TaskBackend,
    *,
    head: str, base: str, title: str, body: str,
    links_to_task: TaskHandle,
) -> PR: ...
def schedule_successors(
    backend: TaskBackend, *, successors: list[dict], base_branch: str
) -> list[Task]: ...

# skills/batch-job

def submit(
    backend: TaskBackend,
    *,
    task_id: TaskHandle,
    command: str,
    args: dict[str, Any],
    branch: str,
    commit_sha: str,
    subagent_id: str,
    agent_id: Optional[str] = None,
) -> Job: ...

def poll(
    backend: TaskBackend,
    *,
    job_id: JobHandle,
    command: str,
    sleep: Callable[[float], None] = time.sleep,
    now:   Callable[[], float] = time.monotonic,
    ack: bool = True,
    heartbeat: Optional[Callable[[], None]] = None,
) -> JobResult: ...
```

## GithubDriver

```python
# skills/drivers/github.py

class GithubDriver:
    """Adapts an existing GitHubClient to the neutral TaskBackend Protocol.

    All GitHub-specific logic lives here:

    - parses/renders the agent-meta fenced JSON block in issue bodies
      (delegates to existing helpers in .agent/scripts/common.py)
    - maps Task fields to/from agent-meta keys
    - converts issue numbers / comment IDs to/from opaque string handles
    - knows _agent_runs is the log branch
    - knows runner-failure label semantics
    - knows that ack means writing agent_ack="finished" into the comment
    - read_brief: returns instructions_inline if present, else fetches
      instructions_path from the repo
    - read_summary_blob: fetches summary.json from _agent_runs
    """

    def __init__(self, client: GitHubClient, *, config: Optional[dict] = None) -> None: ...

    def capabilities(self) -> set[Capability]:
        # GitHub today has none of the listed capabilities.
        return set()

    # ... full Protocol implementation ...

    def raw_client(self) -> GitHubClient:
        return self._client
```

## Things the driver hides — explicit list

These are platform details that must NEVER appear in skill code or
`SKILL.md`:

| Hidden detail | Where it lives |
|---|---|
| `issue_number` / `comment_id` ints | inside `GithubDriver`; agent sees opaque str handles |
| `agent-meta` fenced block parse/render | inside `GithubDriver` |
| HTML-unescape of escaped JSON | inside `GithubDriver` |
| MCP-trailer-tolerant JSON parsing | inside `GithubDriver` |
| `agent-task` label | inside `GithubDriver` |
| `_agent_runs` branch | inside `GithubDriver` |
| `Closes #N` text in PR body | inside `GithubDriver` (handled via `links_to_task`) |
| Lock semantics | inside `GithubDriver` (and not exposed at all today) |
| Runner-failure issue creation | inside `GithubDriver` |

## Capability flags — usage rule

Skills MAY take fast paths when a capability is present, but MUST work
correctly when it is absent. Example:

```python
def heartbeat(backend, *, task_id, agent_id):
    if "native_heartbeat" in backend.capabilities():
        return True   # backend tracks updated_ts natively; nothing to do
    return backend.heartbeat_task(task_id, agent_id)
```

This pattern is how Atlassian-shaped backends elide the explicit
heartbeat without changing skill behaviour.

## Versioning

Add `BACKEND_PROTOCOL_VERSION = 1` as a module-level constant in
`skills/backend.py`. The `TaskBackend` Protocol may grow methods over
time; consumers can check the version. Do not over-design this for the
first cut — the constant alone is enough.
