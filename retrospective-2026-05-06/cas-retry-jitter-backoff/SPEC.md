# SPEC: `cas-retry-jitter-backoff`

## Trigger conditions

### Direct triggers — activate immediately

- "Add retry to this CAS call."
- "Why does this fail under load?"
- "412 / 422 / 409 keeps coming up."
- Any code review where a retry loop is being added or modified.

### Proactive triggers — offer the skill without being asked

Offer when reviewing any code that:

- Calls an HTTP API that returns 412 Precondition Failed, 422 Unprocessable Entity, or 409 Conflict.
- Does optimistic concurrency control (etags, version numbers, `If-Match`, GitHub PATCH-ref).
- Implements a retry loop on `Exception` without explicit backoff.
- Will run in N>1 concurrent execution contexts (Actions runners, Lambda, Cloud Run, K8s pods).

Do NOT offer for:
- Single-writer CAS (no competition exists).
- Non-CAS retries (e.g., transient network errors with no version semantics) — those want different backoff schedules.

## Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `retries` | `6` | Maximum number of attempts (NOT just retries — the first attempt counts). |
| `base_seconds` | `0.5` | Exponential base. Schedule: `base * 2^attempt`. |
| `max_seconds` | `30.0` | Cap on per-attempt sleep. Beyond this the schedule plateaus. |
| `jitter` | `(0.5, 1.5)` | Multiplier range applied to each delay. |
| `sleep_fn` | `_retry_sleep` (module-level) | Indirection so tests can stub. |
| `should_retry` | `lambda e: True` | Predicate: which exceptions trigger a retry. Default = all. |

## Outputs

- On success: returns whatever the wrapped function returned. No exception.
- On exhausted retries: re-raises the last exception. The caller distinguishes "transient and gave up" from "permanent" by re-inspecting the exception type / status code.
- Side effect: emitted log line per retry with `(attempt, delay, exception_repr)`. Helps post-mortem diagnosis.

## Workflow steps

The skill's "execution" is actually a code template. Follow these
implementation steps when adding a retry loop to a new CAS-protected
operation.

1. **Identify the CAS primitive.** What HTTP method + path / RPC / function call is the actual CAS step? In this repo it's
   `PATCH /repos/{owner}/{repo}/git/refs/{ref}` with `{"sha": ...}`.

2. **Identify the read-side state that must be refreshed on each
   retry.** The CAS expects a `parent_sha`, `expected_etag`,
   `version`, etc. The retry MUST re-fetch this between attempts —
   otherwise it just re-attempts with the same stale value.

3. **Wrap the CAS call in a function that re-fetches.** In this repo,
   `put_file_contents()` re-fetches `head_sha` at the top. The retry
   loop calls `put_file_contents()`, NOT a lower-level helper that
   bypasses the refresh.

4. **Define the sleep helper at module scope.**
   ```python
   def _retry_sleep(seconds: float) -> None:
       import time as _time
       _time.sleep(seconds)
   ```
   Indirecting through a named function lets tests `monkeypatch.setattr(module, '_retry_sleep', recorder)` without affecting any other `time.sleep` use.

5. **Implement the retry loop.**
   ```python
   def _retry_put(client, path, content, msg, branch, *, retries=6):
       import random as _random
       last_exc = None
       for attempt in range(retries):
           try:
               client.put_file_contents(path, content, msg, branch)
               return
           except Exception as e:  # noqa: BLE001
               last_exc = e
               if attempt + 1 >= retries:
                   break
               base = min(0.5 * (2 ** attempt), 30.0)
               jitter = _random.uniform(0.5, 1.5)
               _retry_sleep(base * jitter)
       if last_exc is not None:
           raise last_exc
   ```

6. **Pin the contract in unit tests.** At minimum:
   - "succeeds after N transient failures"
   - "raises after exhausting retries"
   - "calls the underlying function each attempt" (regression for someone refactoring head_sha refresh out of the loop)
   - "sleeps strictly positive and non-decreasing between attempts"
   - "default retries ≥ 5"

## Templates

### Test template (Python + pytest)

```python
def test_retry_put_succeeds_after_transient_failures(monkeypatch):
    monkeypatch.setattr(handler, "_retry_sleep", lambda _t: None)
    calls = {"n": 0}
    class _Stub:
        def put_file_contents(self, path, content, msg, branch):
            calls["n"] += 1
            if calls["n"] < 3:
                raise RuntimeError(f"transient (attempt {calls['n']})")
            return {"path": path, "branch": branch}
    handler._retry_put(_Stub(), "x.json", b"{}", "msg", "_agent_runs", retries=5)
    assert calls["n"] == 3


def test_retry_put_sleeps_with_backoff(monkeypatch):
    sleeps = []
    monkeypatch.setattr(handler, "_retry_sleep", sleeps.append)
    class _FailUntilThird:
        def __init__(self): self.n = 0
        def put_file_contents(self, *a, **kw):
            self.n += 1
            if self.n < 3: raise RuntimeError("transient")
            return {}
    handler._retry_put(_FailUntilThird(), "z.json", b"{}", "m", "_agent_runs", retries=5)
    assert len(sleeps) >= 2
    assert all(s > 0 for s in sleeps)
    assert sleeps == sorted(sleeps)  # non-decreasing
```

### Backoff schedule (spec'd, not implementation)

| Attempt | Base delay (s) | After jitter range (s) |
|---------|----------------|------------------------|
| 0 | 0.5 | 0.25 – 0.75 |
| 1 | 1.0 | 0.5 – 1.5 |
| 2 | 2.0 | 1.0 – 3.0 |
| 3 | 4.0 | 2.0 – 6.0 |
| 4 | 8.0 | 4.0 – 12.0 |
| 5 | 16.0 | 8.0 – 24.0 |
| 6+ | 30.0 (capped) | 15.0 – 45.0 |

## Anti-patterns

- **No backoff at all.** Three concurrent writers retrying without
  delay = three writers continuing to collide forever, or until
  default retry exhausts (~milliseconds). Functionally no retry.
- **No jitter.** Without jitter, two writers that started together
  will wake up together, retry together, fail together. Synchronized
  herd. Jitter spreads them.
- **No max cap on the backoff.** Exponential without a cap will hit
  delays of minutes-to-hours on persistent contention. Workflow
  timeouts will hit before the retry succeeds.
- **Caching the read-side state across retries.** If `head_sha` is
  fetched once and reused across attempts, the retry uses a known-bad
  value. Refresh on every attempt.
- **Setting `force=true` on the underlying API call.** This bypasses
  the version check; concurrent writes silently overwrite each
  other. CAS exists for a reason.
- **Retrying on every Exception type.** Defensive but loses signal.
  At minimum, log the exception each retry; ideally narrow `should_retry`
  to known-transient errors. (For HTTP, status codes 5xx + 408 + 425 +
  429; for CAS specifically, 409/412/422.)
- **Bumping `retries` to 100 without backoff.** Doesn't help; the
  competitors keep racing too.

## Implementation notes

- **Indirected sleep is non-negotiable.** Tests cannot rely on
  `time.sleep(0.5)` in CI — even at the lower bound, six retries
  add up to seconds of test runtime, multiplied across the suite
  becomes noticeable. The `_retry_sleep` indirection lets tests
  use `monkeypatch.setattr` to record sleep durations without
  actually sleeping.
- **Per-call retry budget.** This skill's contract is per-CAS-call.
  Higher-level retry budgets (per-job, per-comment) live elsewhere.
- **Logging.** Every retry should emit a structured log line with
  `attempt`, `delay`, `error_kind`, `error_detail`. Useful for
  post-mortem diagnosis and capacity planning.
- **Generalization.** This skill is implementation-language-neutral.
  Translate the loop and template tests; the contract stays.

## Test plan

- Unit tests for the contract (5 tests minimum, see template above).
- Property-based test (optional): for any K transient failures < retries, the loop succeeds; for K ≥ retries, the loop raises.
- Stress test (optional): run N=10 concurrent `_retry_put` calls against an in-memory mock that races; assert all succeed within retries × max_seconds budget.
- Live regression: any time a new CAS-protected primitive is added, drive a multi-writer scenario (this repo: scenario 02) and verify no 422/412/409 escapes.

## Living document

Amend this spec when:
- A new failure mode requires a different backoff schedule.
- The underlying API's CAS contract changes (e.g., GitHub starts returning 409 instead of 422 for non-fast-forward).
- The unit-test idioms in this repo evolve (e.g., conftest gains a `retry_sleep_recorder` fixture).

Provenance: PR #68 — `_retry_put` jittered exponential backoff. Live
discovery in scenario 02 (issue #67), beta subagent crashed with 422 on
`_agent_runs` PATCH-ref. Fix verified by re-running scenario 02 (issue #69)
to clean completion.
