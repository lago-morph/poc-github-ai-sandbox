"""``task-dag/merge`` — merge subagent branches into the feature branch.

In v1 we model "merge" as a fast-forward / files-overlay operation
against the in-memory client: each subagent branch's files are
applied on top of the feature branch. A real implementation would
shell out to git; this stub mirrors the spec's intent so tests can
exercise the orchestration logic.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

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


def list_subagent_branches(
    branches: Iterable[str],
    feature_branch: str,
    *,
    pattern: str = "<feature_branch>/sub-",
) -> list[str]:
    prefix = pattern.replace("<feature_branch>", feature_branch)
    return sorted(b for b in branches if b.startswith(prefix))


def merge_subagent_branches(
    client: GitHubClient,
    *,
    feature_branch: str,
    subagent_branches: list[str],
    delete_branches: bool = True,
) -> dict[str, Any]:
    """Apply each subagent branch's tip files onto the feature branch.

    For the in-memory POC client this is implemented as a full overlay
    via :meth:`InMemoryGitHubClient.commit_files`; with a real client
    you'd open per-branch merge commits via the GitHub API.

    When ``delete_branches`` is True (default), each successfully-merged
    subagent branch is deleted via :meth:`GitHubClient.delete_branch`
    after the merge commit lands. Branches that were skipped (missing
    or empty) are not deleted.
    """
    merged: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    deleted: list[str] = []

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
            # Pull the file map directly from the in-memory commit graph.
            files = _files_at(client, sub)
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
            except Exception:  # noqa: BLE001 - best-effort cleanup
                # Branch deletion is best-effort; failures don't roll back
                # an already-recorded merge. Real clients may surface 422
                # ("not found") which we treat as already-deleted.
                pass

    return {"merged": merged, "skipped": skipped, "deleted": deleted}


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
