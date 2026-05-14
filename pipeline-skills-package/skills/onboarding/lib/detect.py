"""Phase 0 detection — does the onboarding skill have any prior state?

Reports five booleans that mirror the SKILL.md "Onboarding status"
block. The full implementation in the new repo uses the GitHub MCP
server to check the remote well-known branch
`agent-job-protocol/onboarding` for the dialog / recommendations
files. This stub only checks local filesystem presence so it can run
inside unit tests against fixture repos.
"""

from __future__ import annotations

import os
from typing import Dict


def detect_state(repo_root: str) -> Dict[str, bool]:
    """Return Phase 0 state booleans for the repo at ``repo_root``.

    Returns a dict with these keys:

    - ``protocol_installed`` — ``.agent/config.json`` is present.
    - ``onboarding_started`` — branch ``agent-job-protocol/onboarding``
      exists on origin. (Stub: cannot check remote; returns False
      unless a local marker file is found at
      ``.agent/onboarding/.branch-created``.)
    - ``dialog_present`` — ``.agent/onboarding/dialog.md`` exists.
    - ``recommendations_present`` — ``.agent/onboarding/recommendations.md`` exists.
    - ``recommendations_applied`` — a pointer line to
      ``.agent/onboarding/recommendations.md`` is present in
      ``AGENTS.md`` or ``CLAUDE.md``.

    The full implementation (run in the maintenance repo) replaces
    the local FS checks with GitHub MCP calls so detection works
    against the actual default branch and the well-known onboarding
    branch.
    """

    def _exists(rel: str) -> bool:
        return os.path.exists(os.path.join(repo_root, rel))

    pointer = ".agent/onboarding/recommendations.md"

    def _has_pointer(rel: str) -> bool:
        path = os.path.join(repo_root, rel)
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return pointer in fp.read()
        except OSError:
            return False

    return {
        "protocol_installed": _exists(".agent/config.json"),
        "onboarding_started": _exists(".agent/onboarding/.branch-created"),
        "dialog_present": _exists(".agent/onboarding/dialog.md"),
        "recommendations_present": _exists(".agent/onboarding/recommendations.md"),
        "recommendations_applied": _has_pointer("AGENTS.md") or _has_pointer("CLAUDE.md"),
    }
