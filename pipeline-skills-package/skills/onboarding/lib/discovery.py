"""Phase 2 discovery scan — read-only walk of known paths.

Produces a structured summary of what exists in the target repo so
the agent can show a discovery summary to the user before starting
the interview, and so `recommendations.py` can decide which files
warrant a non-pointer proposed edit.

The path table mirrors SPEC.md §"Phase 2 — discovery scan". The
full implementation in the new repo follows one level of indirection
for files referenced by AGENTS.md / CLAUDE.md; this stub records
their presence but does not parse them.
"""

from __future__ import annotations

import glob
import os
from typing import Dict, List


# The discovery patterns table. Each entry is (category, glob).
DISCOVERY_PATTERNS: List[tuple] = [
    ("conventions", "AGENTS.md"),
    ("conventions", "CLAUDE.md"),
    ("readme", "README*"),
    ("spec", "SPEC*"),
    ("plan", "PLAN*"),
    ("handoff", "HANDOFF*"),
    ("roadmap", "ROADMAP*"),
    ("todo", "TODO*"),
    ("ci.github", ".github/workflows/*.yml"),
    ("ci.github", ".github/workflows/*.yaml"),
    ("ci.gitlab", ".gitlab-ci.yml"),
    ("ci.gitlab", ".gitlab/*.yml"),
    ("ci.circle", ".circleci/config.yml"),
    ("ci.jenkins", "Jenkinsfile"),
    ("ci.bitbucket", "bitbucket-pipelines.yml"),
    ("ci.azure", "azure-pipelines.yml"),
    ("ci.azure", ".azure-pipelines.yml"),
    ("skills", ".claude/skills/*/SKILL.md"),
]


def scan_repo(repo_root: str) -> Dict[str, List[str]]:
    """Walk the discovery patterns and return a category -> [paths] map.

    Paths returned are repo-relative. The full implementation will
    additionally:

    - Follow one level of indirection for files referenced by
      AGENTS.md / CLAUDE.md (extract Markdown link targets, add them
      to the result under ``referenced``).
    - Parse YAML for CI files and extract job names / step names.
    - Truncate the result to 5-15 bullet points for user display
      while keeping the full structured map available for
      recommendations rendering.
    """
    found: Dict[str, List[str]] = {}
    for category, pattern in DISCOVERY_PATTERNS:
        matches = glob.glob(os.path.join(repo_root, pattern))
        rel_matches = sorted(
            os.path.relpath(m, repo_root) for m in matches if os.path.isfile(m)
        )
        if rel_matches:
            found.setdefault(category, []).extend(rel_matches)
    return found


def summarise(scan_result: Dict[str, List[str]]) -> List[str]:
    """Turn a scan result into 5-15 bullet points for user display.

    Stub returns one bullet per category with a count. The full
    implementation will produce richer summaries (e.g. "GitHub
    Actions: 3 workflows including ci.yml, release.yml, lint.yml").
    """
    bullets: List[str] = []
    for category, paths in sorted(scan_result.items()):
        bullets.append(f"{category}: {len(paths)} file(s) — {', '.join(paths[:3])}")
    return bullets
