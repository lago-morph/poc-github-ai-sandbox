"""``chatty`` test command — emits many log records to force chunk rotation.

Used by harness scenario 12 (``12_huge_log.md``). Args:

- ``lines`` (int, default 20000): number of log records to emit.

The default is large enough that the LogWriter's compressed-chunk
rotation kicks in at the configured ``max_chunk_bytes_compressed``
(524 288 bytes) and produces multiple chunks.
"""

from __future__ import annotations

from typing import Any

try:
    from ..scripts.common import iso_now  # type: ignore[import-not-found]
except (ImportError, ValueError):
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ))
    from common import iso_now  # type: ignore[import-not-found]


def run(args: dict[str, Any], log_writer, workspace) -> dict[str, Any]:
    n = int(args.get("lines", 20000))
    if n < 0:
        n = 0
    # Pad each line so the gzip-compressed stream actually grows fast
    # enough to rotate. ~120 chars of mixed-entropy text per record.
    pad = (
        "padding-payload-mixed-entropy-"
        "abc123-def456-ghi789-jkl012-mno345-pqr678-stu901-vwx234-yz0-"
    )
    for i in range(n):
        log_writer.write({
            "ts": iso_now(),
            "stream": "stdout",
            "phase": "exec",
            "data": f"line {i:08d} {pad}",
        })
    return {
        "lines_emitted": n,
        "message": f"chatty emitted {n} lines",
    }
