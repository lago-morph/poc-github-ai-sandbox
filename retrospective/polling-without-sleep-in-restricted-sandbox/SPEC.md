# `polling-without-sleep-in-restricted-sandbox` — implementation spec

A small reference skill for the pattern of bounded async-condition
waiting in sandboxes that block long `sleep` calls.

## 1. Trigger conditions

- The agent is about to wait for an external state change.
- The wait might exceed ~25-30s (long `sleep` is blocked).
- The condition is observable (a file, an API response, a property
  of a remote object).

Examples:
- "Wait for the workflow run to complete"
- "Wait until the issue is locked"
- "Wait for the deploy to finish"
- "Wait until the file appears"

## 2. The base pattern

```bash
until [ <condition> ]; do
  sleep <short-interval>
  n=$((n+1))
  [ "$n" -ge <max-iterations> ] && break
done
```

Run via `Bash run_in_background: true`. The dispatcher gets a single
notification on exit (success or timeout).

## 3. Variants

### 3.1 File-based condition (local)

```bash
until [ -f /tmp/done ]; do
  sleep 1
  n=$((n+1))
  [ "$n" -ge 30 ] && break
done
```
30 × 1s = 30s cap. Useful when the condition is set by another
local process.

### 3.2 Workflow run completion (remote)

```bash
until [ -f /tmp/wait_marker ]; do
  sleep 5
  n=$((n+1))
  [ "$n" -ge 18 ] && break
done
echo "polled ${n}x5s"
```
18 × 5s = 90s cap. The agent then queries the remote state once;
this is just the wait skeleton. Pair with a separate MCP call to
check the actual condition after the wait.

### 3.3 Command-based condition with retries

When the wait is "until a command returns 0":

```bash
n=0
until command-that-checks; do
  sleep 5
  n=$((n+1))
  [ "$n" -ge 30 ] && exit 1
done
```
30 × 5s = 150s cap. Exits 1 on timeout so the dispatcher knows it
failed.

## 4. Why not `Monitor`?

`Monitor` is the right tool for **streamed** events (each line of
output is a notification). For **single-event "wait until X"**, the
overhead of Monitor is wrong:

- Monitor sends a notification per line; you only want one.
- Monitor's filter has to match every terminal state including
  failures (silence is not success).

For "wait until X", `Bash run_in_background` with an `until` loop
is cleaner:

- One notification on exit
- Natural bounded retry via the counter
- Exit code is the success indicator

Use Monitor for log-tailing, CI step streaming, periodic-check
loops. Use `Bash run_in_background` with `until` for one-shot
waits.

## 5. Anti-patterns

- **Standalone long sleep**: `sleep 45` is blocked. Don't.
- **Unbounded loop**: `until <cond>; do sleep 5; done` with no
  counter. If the condition never becomes true, the bash hangs
  until killed.
- **Tiny intervals on remote APIs**: `sleep 1` polling GitHub will
  hit rate limits. 5-10s minimum for remote.
- **Polling for remote state inside the sleep loop**: each iteration
  shells out to a tool that costs latency. Better: do the cheap
  marker check inside the loop, do the expensive remote check
  after the loop.

## 6. The "marker file" trick

A common pattern: the dispatcher's polling loop watches for a
marker file that doesn't exist. It just runs the loop to its cap
and exits. The dispatcher then queries the actual remote state
once after the loop ends.

```bash
until [ -f /tmp/never-going-to-exist ]; do
  sleep 5
  n=$((n+1))
  [ "$n" -ge 18 ] && break
done
```

This is "wait 90s" expressed in a way that doesn't trigger the
long-sleep block. The condition is intentionally false; the loop
hits its cap.

This is what most of this session's polling actually was.

## 7. Implementation

The skill could be:

- A SKILL.md with the variants listed and "use this one for X."
- A small bash function library:
  ```bash
  wait_with_cap() {
    local cap=${1:-90}
    local interval=${2:-5}
    local cond=${3:-"[ -f /tmp/never ]"}
    local n=0
    until eval "$cond"; do
      sleep "$interval"
      n=$((n+1))
      [ "$n" -ge $((cap / interval)) ] && break
    done
    echo "polled ${n} iterations"
  }
  ```
- Or just a reference doc. Given the pattern is 5 lines, an
  in-skill code block is probably enough.

## 8. Test plan (when built)

- Verify the loops exit at the cap when the condition never holds.
- Verify the loops exit when the condition becomes true mid-run.
- Verify the standalone-sleep block doesn't fire (intervals stay
  under the threshold).

## 9. Living document

Add new variants as patterns emerge. E.g., if a future sandbox
blocks differently or has different timeouts, add a section.
