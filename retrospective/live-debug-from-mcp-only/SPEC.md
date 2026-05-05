# `live-debug-from-mcp-only` — implementation spec

A focused skill for the specific scenario "my workflow failed and I
can't read the logs from MCP."

## 1. Trigger conditions

- A workflow YAML triggered, the run failed (exit 1 or other)
- The agent's only access is MCP tools (no PAT, no `gh` CLI)
- WebFetch on `/actions/runs/<id>` hits the auth wall

Soft trigger:
- Setting up any new workflow that the agent will need to debug
  (proactively bake in the diagnostic patterns from the start)

## 2. Three patterns (defense in depth)

The patterns layer. Use all three for maximum visibility.

### Pattern 1 — Workflow markers (in YAML)

Add a first step that posts a "handler started" comment, and a
final `if: always()` step that posts a "handler ended" comment with
the conclusion + last 4KB of stdout/stderr base64-encoded.

This runs **regardless** of whether the python step succeeds or
fails, so the agent always sees a marker.

```yaml
jobs:
  handle:
    if: |
      <existing if filters>
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - name: marker-start
        run: |
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d '{"body":"<!-- workflow-marker -->\n[handler-start] run=${{ github.run_id }} comment=${{ github.event.comment.id }}"}' \
            > /tmp/marker-start.json || true
      
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r .agent/scripts/requirements.txt
      
      - id: handler
        run: python .agent/scripts/handler.py 2>&1 | tee /tmp/handler.log
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          COMMENT_ID: ${{ github.event.comment.id }}
          WORKFLOW_RUN_ID: ${{ github.run_id }}
      
      - name: marker-end
        if: always()
        run: |
          conclusion="${{ steps.handler.conclusion }}"
          tail_b64=$(tail -c 4000 /tmp/handler.log 2>/dev/null | base64 -w0 || echo "")
          curl -sS -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments" \
            -d "{\"body\":\"<!-- workflow-marker -->\n[handler-end] run=${{ github.run_id }} comment=${{ github.event.comment.id }} conclusion=${conclusion}\n\n<details><summary>last 4KB of stdout/stderr (base64)</summary>\n\n\`\`\`\n${tail_b64}\n\`\`\`\n\n</details>\"}" \
            > /tmp/marker-end.json || true
```

Key notes:
- `|| true` on each curl so a failed marker doesn't crash the job.
- `tee /tmp/handler.log` captures both stdout and stderr.
- Base64-encoding tames newlines in the JSON payload.
- `if: always()` guarantees the end-marker even on python crash.

Decode the base64 locally:
```bash
echo "<base64 here>" | base64 -d
```

### Pattern 2 — Self-diagnostic from the script

In Python, wrap `main()`'s try/except. On uncaught exception, post a
comment with `traceback.format_exc()` to the originating issue.

```python
import os, sys, traceback, requests

def _post_debug_comment(*, token, owner, repo, issue_number,
                       script, exc, extra_fields=None):
    """Post a traceback comment to the originating issue."""
    body = (
        f"**{script} crashed**\n\n"
        f"- issue: #{issue_number}\n"
    )
    for k, v in (extra_fields or {}).items():
        body += f"- {k}: {v}\n"
    body += (
        f"- python: {sys.version.split()[0]}\n\n"
        f"```\n{exc!r}\n```\n\n"
        f"<details><summary>Traceback</summary>\n\n"
        f"```\n{traceback.format_exc()}```\n\n"
        f"</details>\n"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    requests.post(url, headers=headers, json={"body": body}, timeout=15)


def main() -> int:
    # ... env validation, build client, etc.
    try:
        run(client, ...)
        return 0
    except Exception as exc:
        traceback.print_exc()
        if os.environ.get("HANDLER_DEBUG_COMMENT", "1") == "1":
            try:
                _post_debug_comment(
                    token=token, owner=owner, repo=repo,
                    issue_number=int(issue_number),
                    script="handler.py",
                    exc=exc,
                    extra_fields={"comment": comment_id, "run": workflow_run_id},
                )
            except Exception as diag_exc:
                print(f"failed to post debug comment: {diag_exc!r}", file=sys.stderr)
        return 1
```

Important details:
- Wrap the diagnostic post in its own try/except. A failure to
  diagnose must not mask the original exit code.
- Use direct `requests.post`, not your domain client. The bug might
  be in the domain client.
- Opt-out via env var (`HANDLER_DEBUG_COMMENT=0`) for tests that
  don't want noise.
- Don't include the GH_TOKEN value in the diagnostic body. List
  env vars as "set" / "unset" only.

### Pattern 3 — Decoder helper for the agent

The agent reads marker comments via MCP. Provide a small helper to
extract the embedded base64 tail.

```python
import base64, html, re

def extract_marker_log(comment_body: str) -> str | None:
    """Extract the embedded log from a marker-end comment."""
    body = html.unescape(comment_body)
    m = re.search(
        r"<details><summary>last 4KB[^<]*</summary>.*?```\n([A-Za-z0-9+/=]+)\n```",
        body, re.DOTALL,
    )
    if not m:
        return None
    try:
        return base64.b64decode(m.group(1)).decode("utf-8", errors="replace")
    except Exception:
        return None
```

Used by the agent like:
```python
comments = mcp.issue_read("get_comments", issue_number=N)
for c in comments:
    if c["user"]["login"] == "github-actions[bot]" and "[handler-end]" in c["body"]:
        log = extract_marker_log(c["body"])
        if log:
            print(log)  # full last-4KB of handler stdout
```

## 3. Pivot signals

Use the diagnostic data to identify common root causes:

- **Marker-start posted, marker-end not posted, no traceback comment**:
  - Job timed out (60-min default for `ubuntu-latest`)
  - Or the runner was killed (rate limit, billing)
  
- **Marker-start posted, marker-end posted with conclusion=success, but original-comment unchanged**:
  - Handler exited 0 but didn't do its work
  - Likely an early-return on guard condition (e.g., `if`-clause logic)
  - **OR**: the handler tried to write back but got 403
  
- **Marker-start posted, marker-end posted with conclusion=failure, base64 contains a Python traceback**:
  - Decode the base64; that's your bug
  
- **No markers at all**:
  - Job-level `if:` evaluated false → workflow didn't run
  - Check `github.event.issue.locked`, label presence, comment author
  
- **`Unable to create comment because issue is locked` in the base64**:
  - The lock-vs-bot bug from this session
  - Workflow has lock guard in `if:`, but locked issues refuse bot comments
  - Move locking to issue close, not creation

## 4. What this skill cannot do

- Stream logs while a job is running (post-hoc only)
- Read older runs' logs (markers are ephemeral; only THIS run's
  comments)
- Diagnose `setup-python` or `pip install` failures (markers fire
  after those steps)
  - **Workaround**: also add `marker-pre-checkout` as the very first
    step, before `actions/checkout@v4`. Then if the start-marker
    fires but checkout-marker doesn't, you know checkout failed.

## 5. Anti-patterns

- **`|| true` on the marker step is REQUIRED.** Without it, a failed
  marker (e.g., the lock-vs-bot 403) fails the whole job AND eats
  the diagnostic.
- **Don't include `GH_TOKEN` value in any comment.** "set" / "unset"
  only. Tokens leak permanently.
- **Don't use the domain client for the diagnostic.** Bug may be
  there.
- **Don't make the diagnostic mandatory.** Opt-out env var.

## 6. Implementation notes

The skill ships:
- A YAML snippet template for marker-start / marker-end
- A Python helper (`debug_post_comment.py`) for self-diagnostic
- A decoder helper (`extract_marker_log.py`) for the agent side

The skill should add these to a project as a `--with-diagnostics`
flag at `lock-and-sweep` / `batch-job-handler` setup time, OR offer
to retrofit them when activated mid-debug.

## 7. Test plan (when built)

- Snapshot test: marker YAML produces well-formed JSON for the curl
- Unit: `extract_marker_log` round-trips a known base64
- Integration: a test workflow with a `python -c "raise Exception('x')"`
  step produces both an end-marker AND a traceback comment

## 8. References

- The session's PR #14 (debug markers) and PR #13 (self-diagnostic)
- `github-mcp-tips/excerpts.jsonl` for the live evidence
- `ITERATION_REPORT.md` Phase 4 section for the full discovery story
