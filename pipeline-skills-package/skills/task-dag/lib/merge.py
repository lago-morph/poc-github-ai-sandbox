"""``task-dag/merge`` — merge subagent branches into the feature branch.

In v1 we model "merge" as a fast-forward / files-overlay operation
against the in-memory client: each subagent branch's files are
applied on top of the feature branch. A real implementation would
shell out to git; this stub mirrors the spec's intent so tests can
exercise the orchestration logic.

Per SPEC §6 "Merge conflicts are the primary's responsibility": the
primary must have visibility into conflicts. We support three
strategies via ``conflict_strategy``:

- ``"fail"`` (default): raise :class:`MergeConflictError` BEFORE any
  branch is merged when conflicts are detected.
- ``"last-writer-wins"``: apply each subagent overlay in iteration
  order (existing behaviour); record the conflicting paths in
  ``result["conflicts"]``.
- ``"first-writer-wins"``: skip conflicting paths from later subagent
  branches; record the skipped paths in ``result["conflicts"]``.
"""

from __future__ import annotations

from typing import Any, Iterable, Literal, Optional

try:
    from .common import GitHubClient, iso_now
except ImportError:
    import importlib.util as _ilu, os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _spec = _ilu.spec_from_file_location(
        "skills_taskdag_common", _os.path.join(_here, "common.py")
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["skills_taskdag_common"] = _mod
    _spec.loader.exec_module(_mod)
    GitHubClient = _mod.GitHubClient
    iso_now = _mod.iso_now


ConflictStrategy = Literal["fail", "last-writer-wins", "first-writer-wins"]


class MergeConflictError(RuntimeError):
    """Raised when conflict_strategy='fail' detects merge conflicts.

    The ``conflicts`` attribute holds the list of conflicting paths so
    callers can inspect / log them before retrying with a different
    strategy.
    """

    def __init__(self, conflicts: list[str]) -> None:
        super().__init__(
            f"merge conflicts on {len(conflicts)} path(s): {sorted(conflicts)}"
        )
        self.conflicts = list(conflicts)


def list_subagent_branches(
    branches: Iterable[str],
    feature_branch: str,
    *,
    pattern: str = "<feature_branch>/sub-",
) -> list[str]:
    prefix = pattern.replace("<feature_branch>", feature_branch)
    return sorted(b for b in branches if b.startswith(prefix))


def _detect_conflicts(
    client: GitHubClient,
    feature_branch: str,
    subagent_branches: list[str],
) -> list[str]:
    """Detect paths that conflict per SPEC §6.

    A path conflicts when:
      - Two or more subagent branches modify it with different content, AND
      - It also exists on the feature branch's pre-merge state with content
        different from at least one of those subagent versions.
    """
    feature_files = _files_at(client, feature_branch)

    # path -> list[bytes] (one entry per subagent branch that has this path)
    per_path_versions: dict[str, list[bytes]] = {}
    for sub in subagent_branches:
        files = _files_at(client, sub)
        if not files:
            continue
        for path, content in files.items():
            per_path_versions.setdefault(path, []).append(content)

    conflicts: list[str] = []
    for path, versions in per_path_versions.items():
        # At least two subagent branches touch this path...
        if len(versions) < 2:
            continue
        # ...with differing content.
        unique = {v for v in versions}
        if len(unique) < 2:
            continue
        # ...AND the feature branch already has the path with content
        # different from at least one of them.
        base = feature_files.get(path)
        if base is None:
            # Path didn't exist pre-merge; multiple subagents creating
            # divergent versions is still a conflict the primary must see.
            conflicts.append(path)
            continue
        if any(v != base for v in versions):
            conflicts.append(path)

    return conflicts


def merge_subagent_branches(
    client: GitHubClient,
    *,
    feature_branch: str,
    subagent_branches: list[str],
    delete_branches: bool = True,
    conflict_strategy: ConflictStrategy = "fail",
) -> dict[str, Any]:
    """Apply each subagent branch's tip files onto the feature branch.

    For the in-memory POC client this is implemented as a full overlay
    via :meth:`InMemoryGitHubClient.commit_files`; with a real client
    you'd open per-branch merge commits via the GitHub API.

    When ``delete_branches`` is True (default), each successfully-merged
    subagent branch is deleted via :meth:`GitHubClient.delete_branch`
    after the merge commit lands. Branches that were skipped (missing
    or empty) are not deleted.

    When ``conflict_strategy="fail"`` (default), conflicts are detected
    BEFORE any merge writes occur, and :class:`MergeConflictError` is
    raised — partial merges are never produced.

    The result dict always includes:
      - ``merged``: per-branch records of successful merges
      - ``skipped``: per-branch records of missing/empty branches
      - ``deleted``: list of subagent branches successfully deleted
      - ``delete_failed``: list of ``{branch, error}`` for failed deletes
      - ``conflicts``: list of conflicting paths (empty when no conflict)
    """
    if conflict_strategy not in ("fail", "last-writer-wins", "first-writer-wins"):
        raise ValueError(f"unknown conflict_strategy: {conflict_strategy!r}")

    conflicts = _detect_conflicts(client, feature_branch, subagent_branches)

    if conflicts and conflict_strategy == "fail":
        # Raise BEFORE any branch is merged.
        raise MergeConflictError(conflicts)

    merged: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    deleted: list[str] = []
    delete_failed: list[dict[str, Any]] = []

    # For first-writer-wins, track which conflicting paths have already
    # been claimed so later branches can skip them.
    conflict_set = set(conflicts)
    claimed_paths: set[str] = set()

    for sub in subagent_branches:
        sub_sha = client.get_branch_head_sha(sub)
        if sub_sha is None:
            skipped.append({"branch": sub, "reason": "missing_or_empty"})
            continue

        # Best-effort: use the in-memory commit_files helper if available.
        commit_files = getattr(client, "commit_files", None)
        if commit_files is None:
            # Real client: we'd POST a merge here. For the POC abstraction
            # we just record the intent.
            merged.append({
                "branch": sub,
                "sub_sha": sub_sha,
                "merged_at": iso_now(),
                "method": "abstract",
            })
        else:
            files = _files_at(client, sub)
            if conflict_strategy == "first-writer-wins" and conflict_set:
                # Drop any conflict path that has already been claimed by
                # an earlier branch in iteration order.
                files = {
                    p: c for p, c in files.items()
                    if not (p in conflict_set and p in claimed_paths)
                }
                # Mark paths this branch IS contributing as claimed.
                for p in list(files.keys()):
                    if p in conflict_set:
                        claimed_paths.add(p)
            new_sha = commit_files(
                feature_branch,
                files,
                f"Merge subagent branch {sub} into {feature_branch}",
            )
            merged.append({
                "branch": sub,
                "sub_sha": sub_sha,
                "merge_sha": new_sha,
                "merged_at": iso_now(),
                "method": "in_memory_overlay",
            })

        # After a successful merge, optionally delete the subagent branch.
        if delete_branches:
            try:
                client.delete_branch(sub)
                deleted.append(sub)
            except Exception as e:  # noqa: BLE001 - best-effort cleanup
                # Branch deletion is best-effort; failures don't roll back
                # an already-recorded merge. Record the failure so the
                # silent swallow becomes observable to callers.
                delete_failed.append({"branch": sub, "error": str(e)})

    return {
        "merged": merged,
        "skipped": skipped,
        "deleted": deleted,
        "delete_failed": delete_failed,
        "conflicts": conflicts,
    }


def _files_at(client: GitHubClient, branch: str) -> dict[str, bytes]:
    """For the in-memory client only: read all files at branch tip."""
    head = client.get_branch_head_sha(branch)
    if head is None:
        return {}
    # Reach into the in-memory commit graph if available.
    commits = getattr(client, "_commits", None)
    if commits is None:
        return {}
    commit = commits.get(head)
    if commit is None:
        return {}
    return dict(commit.files)
