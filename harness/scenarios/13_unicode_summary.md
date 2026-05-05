# Scenario 13 — unicode args round-trip through gzip + JSON

## Objective
Submit an `echo` request whose `args.message` contains multi-byte
unicode (CJK + emoji + combining characters) and verify the terminal
envelope's `summary.message` and `summary.json` artifact preserve the
exact string after gzip compression and JSON serialisation.

## Prereqs
- Same as scenario 01.

## Setup
1. `run_id = new_run_id()`; `feature = feature_branch(13, run_id)`.
2. Create `feature` from `main`. Capture HEAD.
3. Create + label (do NOT lock — locking moved to close_on_merge per SPEC §3) issue (`harness-scenario-13`); claim meta.

## Agent steps
1. `MESSAGE = "Hello 世界 🌍 éclair café Ω βγ ✓"`.
2. Build envelope::

       python -m agent_lib make-request "$(jq -nc \
         --arg m "$MESSAGE" '{message:$m}')" \
         --command echo \
         --branch <feature> --sha <feature_head> \
         --subagent-id alpha

   In the live harness, the dispatcher constructs the JSON in-process
   to avoid shell-quoting drift.
3. Post envelope as comment.
4. Poll until `completed`.
5. Read `runs/N/C/summary.json`. The dispatcher's harness code parses
   it and asserts `summary["message"] == MESSAGE`.
6. `finish-meta`, open + merge PR.

## Workflow expectations
- LogWriter records the unicode payload (sanitiser is regex-based on
  ASCII patterns, so unicode passes through untouched).
- Manifest and summary JSON are emitted with `ensure_ascii=False` is
  not required (Python's default `json.dumps` escapes non-ASCII into
  `\uXXXX`, which still round-trips).

## Assertions
- `assert_envelope_terminal(envelope, "completed")`.
- `summary["message"] == MESSAGE` (exact equality).
- `summary["echoed_args"]["message"] == MESSAGE`.
- `assert_pr_merged(pr)`.

## Forensic artifacts
- Issue `N`, one terminal comment, log + summary artifacts, one PR.
