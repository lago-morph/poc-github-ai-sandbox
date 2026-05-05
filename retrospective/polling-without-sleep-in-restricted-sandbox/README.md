# `polling-without-sleep-in-restricted-sandbox` skill

> A small but recurring pattern: how to wait for an external state
> change when the sandbox blocks long `sleep` calls.

## Why this skill

This Claude Code sandbox blocks any `sleep` ≥ ~30 seconds:

```
> sleep 45
Blocked: standalone sleep 45. To wait for a condition, use Monitor
with an until-loop (e.g. `until <check>; do sleep 2; done`)...
```

Every time I needed to wait for a workflow to complete (90s+
typically), I had to re-derive the workaround. Encoding the pattern
once saves the re-derivation each time.

## When this would have helped

This session had ~15 instances of "wait for workflow to complete"
or "wait for asynchronous external state change." Each one used the
same pattern, typed slightly differently each time. A skill removes
the re-typing AND the small-but-real chance of getting it wrong
(e.g., setting the cap too low and missing a slow run).

## The pattern

```bash
until [ -f /tmp/done ]; do
  sleep 5
  n=$((n+1))
  [ "$n" -ge 18 ] && break
done
echo "polled ${n}x5s"
```

- Each iteration: 5s sleep (under the standalone-sleep block).
- Bounded retries via `n` counter prevent infinite loops.
- The condition (`[ -f /tmp/done ]`) is a placeholder for whatever
  you're actually waiting for.
- Run via `Bash run_in_background: true` so the dispatcher gets a
  notification on exit.

## What good looks like

A skill that, when triggered, generates the right pattern with the
right cap based on what's being waited for:

| Wait for... | Cap | Interval |
|-------------|-----|----------|
| Workflow run pickup | 60s | 5s |
| Workflow run completion | 5min | 10s |
| External API state change | varies | 30s |
| Local file appearance | 30s | 1s |

## Status

- Spec only — see `SPEC.md`.
- No code yet (the pattern is ~5 lines so a skill might just be a
  reference doc).
