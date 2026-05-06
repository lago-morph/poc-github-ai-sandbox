# Scenario 10 — crash_recovery

Primary-1 (f3af3edd) claimed, posted echo, "crashed" (stopped responding).
Primary-2 (de94f35d) detected stale status_ts (1970-01-01),
took over with new agent_id, acked the inherited comment via the
follow-up agent-ack form, and finished the issue.
