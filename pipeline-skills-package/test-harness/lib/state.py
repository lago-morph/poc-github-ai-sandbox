"""State persistence and console-block rendering for the test-harness.

State is a plain dict written to ``harness/runs/<run_id>/state.json``
after every phase. The shape is described in ``SKILL.md``. This module
performs the I/O and the human-facing state-block rendering only — it
does not interpret phases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATE_FILENAME = "state.json"

VALID_PHASE_STATUSES = frozenset(
    {"pending", "ready", "in_progress", "done", "failed", "skipped"}
)


def state_path(run_dir: Path) -> Path:
    """Return the canonical state.json path under ``run_dir``."""
    return run_dir / STATE_FILENAME


def load_state(run_dir: Path) -> dict[str, Any]:
    """Load and return the state dict for ``run_dir``.

    Raises :class:`FileNotFoundError` if the state file is missing.
    Raises :class:`ValueError` if the loaded payload is not a dict.
    """
    path = state_path(run_dir)
    if not path.is_file():
        raise FileNotFoundError(f"state file not found: {path}")
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"state at {path} is not a JSON object")
    return data


def save_state(run_dir: Path, data: dict[str, Any]) -> Path:
    """Write ``data`` to ``state.json`` under ``run_dir`` atomically.

    The run directory is created if missing. Writes go to a sibling
    ``state.json.tmp`` first then ``os.replace`` to the final path so
    a partial write never corrupts the persisted state.

    Returns the final state-file path.
    """
    if not isinstance(data, dict):
        raise TypeError("state data must be a dict")
    run_dir.mkdir(parents=True, exist_ok=True)
    final = state_path(run_dir)
    tmp = final.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=False)
        fp.write("\n")
    tmp.replace(final)
    return final


def _current_phase_index(state: dict[str, Any]) -> int:
    """Return 1-based index of the first phase that is not done/skipped.

    Returns ``len(phases)`` (1-based) if all phases are terminal.
    """
    phases = state.get("phases", [])
    for i, phase in enumerate(phases, start=1):
        if phase.get("status") not in ("done", "skipped"):
            return i
    return max(1, len(phases))


def write_state_block_console(state: dict[str, Any]) -> str:
    """Render the canonical state block for ``state``.

    Returns the rendered string (multi-line). The caller is
    responsible for actually printing it. The block format is:

      [test-harness * scenario: <id> * phase i/n (<name>)]
        <phase>: <status>  (<detail>)
        ...
      Next: <next-action>

    where "*" stands for a bullet character.
    """
    scenario_id = state.get("scenario_id", "<unknown>")
    phases = state.get("phases", [])
    total = max(1, len(phases))
    idx = _current_phase_index(state)
    current_name = phases[idx - 1]["name"] if phases else "<none>"

    bullet = "•"
    header = (
        f"[test-harness {bullet} scenario: {scenario_id} {bullet} "
        f"phase {idx}/{total} ({current_name})]"
    )
    lines = [header]
    width = max((len(p.get("name", "")) for p in phases), default=0)
    for phase in phases:
        name = phase.get("name", "<noname>")
        status = phase.get("status", "pending")
        detail = phase.get("detail", "")
        padded_name = f"{name}:".ljust(width + 2)
        if detail:
            lines.append(f"  {padded_name}{status:<10}({detail})")
        else:
            lines.append(f"  {padded_name}{status}")
    nxt = state.get("next_hint") or _default_next_hint(state, idx)
    lines.append(f"Next: {nxt}")
    return "\n".join(lines)


def _default_next_hint(state: dict[str, Any], idx: int) -> str:
    """Compute a reasonable Next: hint from state when none is stored."""
    phases = state.get("phases", [])
    if not phases:
        return "no phases declared; check scenario YAML"
    if idx > len(phases):
        return "scenario complete; run `report` to render report.md"
    current = phases[idx - 1]
    name = current.get("name", "<noname>")
    status = current.get("status", "pending")
    if status == "in_progress":
        return f"resume phase {name!r}"
    return f"run phase {name!r}"


__all__ = [
    "VALID_PHASE_STATUSES",
    "load_state",
    "save_state",
    "state_path",
    "write_state_block_console",
]
