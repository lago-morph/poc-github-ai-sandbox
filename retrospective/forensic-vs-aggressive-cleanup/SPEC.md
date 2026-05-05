# `forensic-vs-aggressive-cleanup` — implementation spec

A skill that codifies cleanup policy for systems producing real-world
artifacts (branches, issues, comments, log files).

## 1. Trigger conditions

- Setting up a new system that creates persistent remote artifacts.
- A user request like "clean up the old branches" / "we have too many
  issues" / "tidy this up."
- After a long live-execution session that accumulated artifacts.

## 2. Two modes

### 2.1 Pure forensic
- Nothing is auto-cleaned.
- All artifacts persist for inspection.
- The user (or a separate cleanup pass) decides when to clean up.
- Best for: research, exploration, debugging, demos that must be
  inspectable later.

### 2.2 Aggressive-on-success, forensic-on-failure
- Successful scenarios auto-clean their artifacts.
- Failed scenarios leave everything for forensics.
- Best for: production-ish systems with high run volume.
- Requires: the system can tell success from failure (status
  field, exit code, labelled outcome).

Pick one as the default. This session was pure forensic; many
production systems should be aggressive-on-success.

## 3. Mandatory conventions (regardless of mode)

### 3.1 Labelled / namespaced artifacts

Every artifact gets a unique run id and a scenario label (or
equivalent):

- Issues: label `harness-scenario-NN` and a unique title prefix
- Branches: `agent/<scenario>-<run_id>` and `<feature>--sub-<id>`
- Files in orphan log branches: `runs/<issue>/<comment>/...`

These conventions enable later greppable cleanup ("delete all
branches starting with `agent/harness-`").

### 3.2 Defensive namespace gates

The auto-cleanup logic MUST never touch:

- `main` (or whatever the default branch is)
- Orphan log branches (e.g., `_agent_runs`)
- Anything outside an explicit agent namespace prefix
- Branches whose name doesn't match the system's pattern

When in doubt, refuse. The cost of cleaning up too aggressively is
high (lost work); the cost of leaving stale artifacts is low.

### 3.3 Cleanup as a system primitive

Bake cleanup into the **system itself**, not as a separate script:

- Branch deletion → in `close_on_merge.py` after PR merge
- Issue closure → already handled by the protocol's finished state
- File expiry on log branches → optional, almost always deferred

Why: a separate cleanup script can be forgotten, can race with
production work, and inevitably gets out of sync with the schema.
Making cleanup an integral part of the workflow's "PR merged" event
guarantees it stays in sync.

## 4. The auto-delete-on-merge pattern (from this session)

In `close_on_merge.py`:

```python
def _safe_to_delete(branch_name: str) -> bool:
    """Defensive gate. Never delete protected refs."""
    PROTECTED = {"main", "master", "_agent_runs"}
    if branch_name in PROTECTED:
        return False
    if not branch_name.startswith("agent/"):
        return False  # only operate within the agent namespace
    return True


def _delete_feature_and_subagent_branches(client, feature_branch):
    deleted = []
    failed = []
    
    if _safe_to_delete(feature_branch):
        try:
            client.delete_branch(feature_branch)
            deleted.append(feature_branch)
        except Exception as e:
            failed.append({"branch": feature_branch, "error": str(e)})
    
    # Also sweep subagent branches under the feature
    prefix = f"{feature_branch}--sub-"
    for branch in client.list_branches():
        name = branch["name"]
        if name.startswith(prefix) and _safe_to_delete(name):
            try:
                client.delete_branch(name)
                deleted.append(name)
            except Exception as e:
                failed.append({"branch": name, "error": str(e)})
    
    return {"deleted": deleted, "failed": failed}
```

Key properties:
- Idempotent (deleting a missing branch is a no-op via try/except)
- Non-fatal on partial failure (records to `failed` list, continues)
- Never touches protected refs
- Sweeps the whole `<feature>--sub-*` family in one call

## 5. The cleanup-after-the-fact pattern

When the user wants to clean up artifacts that pre-date the
auto-cleanup logic (or when the system was in forensic mode and
they're switching), provide a separate one-shot tool:

```python
def cleanup_pass(client, *, prefix: str, dry_run: bool = True):
    """Delete all branches under a namespace prefix.
    
    Defensive: respects _safe_to_delete().
    """
    todo = [
        b["name"] for b in client.list_branches()
        if b["name"].startswith(prefix) and _safe_to_delete(b["name"])
    ]
    if dry_run:
        print(f"would delete {len(todo)} branches:")
        for n in todo:
            print(f"  {n}")
        return
    
    for name in todo:
        try:
            client.delete_branch(name)
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ {name}: {e}")
```

Default to `dry_run=True`. The user's first invocation should print
the list; only after they confirm should the actual deletion run.

## 6. The "git push --delete is blocked" workaround (sandbox-specific)

In some sandbox environments, `git push --delete <branch>` is
blocked at the proxy level (returns 403). When that happens:

- **Option A**: drive deletion through the system's own
  auto-cleanup workflow. Push an empty commit to each branch, open
  a PR, squash-merge. The merge handler does the actual delete via
  REST.
- **Option B**: use `mcp__github__delete_branch` if the MCP server
  exposes it (or the equivalent REST call).
- **Option C**: build a one-shot cleanup workflow gated on a
  specific commit-message marker, run once, then remove.

Document which is appropriate for the project's sandbox.

## 7. Branch retention rules

| Artifact | Retention |
|----------|-----------|
| Code commits to `main` | Permanent |
| Issues / comments | Permanent unless explicitly closed |
| Feature branches (merged) | Auto-delete on PR merge |
| Subagent branches | Auto-delete with feature on PR merge |
| Orphan log branches (e.g., `_agent_runs`) | **PERMANENT — never auto-delete** |
| Debug branches | Cleanup after debug is over (one-shot) |
| Workflow run history | Out of agent's control; GitHub default 90 days |

## 8. Decision criteria for a new project

When setting up a new system, ask:

1. **Will artifacts accumulate?** If yes, auto-cleanup is
   non-negotiable.
2. **Are failures common and worth inspecting?** If yes,
   forensic-on-failure rather than always-aggressive.
3. **Are there forensic-permanent artifacts (audit logs)?** If yes,
   they need a separate namespace that's explicitly excluded from
   cleanup.
4. **Is there sandbox/proxy weirdness?** Validate `git push --delete`
   works before relying on it.

## 9. Anti-patterns

- **A separate cleanup script that has to be remembered.** Bake into
  the system.
- **Aggressive cleanup on failure.** Failed runs are forensic gold.
- **Deleting orphan log branches.** They're the audit record.
- **No namespace gates.** One day someone names a branch `main2`
  and gets it auto-deleted.
- **Pure-permissive cleanup.** "Delete everything matching `agent/`"
  without `_safe_to_delete()` checks — too easy to widen the pattern
  and lose something important.

## 10. Test plan (when built)

- Unit: `_safe_to_delete()` for every protected ref.
- Unit: cleanup respects mode (forensic vs aggressive).
- Integration: cleanup pass on a scratch repo with mixed branches
  produces correct dry-run output.
- Live (rare): full cleanup of N artifacts produces N deletes + 0
  collateral.

## 11. Integration with other skills

- `parallel-subagent-fanout` ships its sub-branches expecting
  cleanup-on-merge. This skill's pattern handles them.
- `agent-dispatch-loop` ships per-iteration feature branches; same.
- `live-debug-from-mcp-only` adds debug branches that need a
  separate cleanup; this skill's "cleanup-after-the-fact" pattern
  applies.
