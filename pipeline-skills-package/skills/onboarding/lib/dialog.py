"""Round-trip serialisation for the onboarding dialog file.

The dialog file is Markdown by design (humans read it directly during
resume), but every question has a stable id so a parser can pick it
back up. The schema lives in ``templates/interview-questions.yml``.

This module is the single point of truth for the dialog's on-disk
shape: ``load_dialog`` parses; ``save_dialog`` serialises; both
honour the convention that the file is atomically rewritten on
every answer (no append-only journaling).
"""

from __future__ import annotations

import datetime as _dt
import os
import re
from typing import Any, Dict, List, Optional


# A Q/A bullet looks like:   - **<question.id>** — _<text>_
# followed by indented sub-bullets that hold the answer.
_QA_LINE = re.compile(r"^- \*\*(?P<qid>[a-z_]+\.[a-z_]+)\*\* — _(?P<text>.+)_\s*$")
_ANSWER_LINE = re.compile(r"^\s*-\s*Answer(?:\s*\([^)]*\))?:\s*(?P<answer>.*)$")
_HEADER_KV = re.compile(r"^- (?P<key>[a-z_]+):\s*`?(?P<value>[^`]*)`?\s*$")


def load_dialog(path: str) -> Dict[str, Any]:
    """Parse a dialog file into a structured dict.

    Returns a dict shaped like::

        {
          "meta": {"run_id": "...", "started_at": "...", "last_updated": "...",
                   "protocol_version": 1, "questions_schema_version": 1},
          "answers": {
            "intent.purpose": "...",
            "intent.audience": "...",
            ...
          },
          "phases_done": ["phase_0", "phase_1", ...],
        }

    Unanswered questions are present in the file as placeholder text;
    their entries appear in ``answers`` with the literal placeholder
    string. The caller is responsible for distinguishing placeholders
    from real answers (typically by string-equal check against
    ``<placeholder>``).
    """
    if not os.path.exists(path):
        return {"meta": {}, "answers": {}, "phases_done": []}

    with open(path, "r", encoding="utf-8") as fp:
        text = fp.read()

    meta: Dict[str, Any] = {}
    answers: Dict[str, str] = {}
    phases_done: List[str] = []

    current_qid: Optional[str] = None
    lines = text.splitlines()

    # Header KV pairs (between the H1 and the first H2).
    for line in lines:
        m = _HEADER_KV.match(line)
        if m:
            meta[m.group("key")] = m.group("value")

    # Q/A bullets and their nested answer lines.
    for i, line in enumerate(lines):
        qa = _QA_LINE.match(line)
        if qa:
            current_qid = qa.group("qid")
            continue
        if current_qid:
            ans = _ANSWER_LINE.match(line)
            if ans:
                answers[current_qid] = ans.group("answer").strip().strip("`")
                current_qid = None

    # Status checklist.
    for line in lines:
        m = re.match(r"^- \[(?P<state>[ x])\] Phase (?P<n>\d) ", line)
        if m and m.group("state") == "x":
            phases_done.append(f"phase_{m.group('n')}")

    return {"meta": meta, "answers": answers, "phases_done": phases_done}


def save_dialog(path: str, data: Dict[str, Any]) -> None:
    """Atomically serialise ``data`` to the dialog file at ``path``.

    Atomic means: write to ``<path>.tmp`` then ``os.replace``. The
    caller is responsible for committing + pushing the result to the
    well-known branch.

    The full implementation will preserve the exact question ordering
    from ``templates/interview-questions.yml`` and include every
    question id (placeholder for unanswered ones) so the file is
    diff-friendly and re-parseable. This stub writes a minimal
    serialisation for tests.
    """
    meta = dict(data.get("meta") or {})
    meta.setdefault("last_updated", _dt.datetime.utcnow().isoformat() + "Z")
    answers = data.get("answers") or {}
    phases_done = set(data.get("phases_done") or [])

    out: List[str] = ["# Onboarding dialog", ""]
    for key in ("run_id", "started_at", "last_updated", "protocol_version", "questions_schema_version"):
        if key in meta:
            out.append(f"- {key}: `{meta[key]}`")
    out.append("")

    # One H2 per category, derived from the answers keys. The full
    # implementation orders sections by the canonical YAML; this stub
    # groups by the prefix before the dot.
    by_category: Dict[str, List[str]] = {}
    for qid in answers:
        cat = qid.split(".", 1)[0]
        by_category.setdefault(cat, []).append(qid)

    for cat, qids in by_category.items():
        out.append(f"## {cat}")
        out.append("")
        for qid in qids:
            out.append(f"- **{qid}** — _<text>_")
            out.append(f"  - Answer: {answers[qid]}")
        out.append("")

    out.append("## Status")
    out.append("")
    for n in range(7):
        mark = "x" if f"phase_{n}" in phases_done else " "
        out.append(f"- [{mark}] Phase {n}")
    out.append("")

    tmp = f"{path}.tmp"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fp:
        fp.write("\n".join(out))
    os.replace(tmp, path)
