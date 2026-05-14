"""Drive a scenario through its phases, persisting state at each step.

The runner is intentionally minimal in this bootstrap copy: it knows
how to parse a scenario YAML, advance one phase, and inspect current
state. Actual phase implementations live in the new repo's harness
extensions (or are dispatched to the skill under test).
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import yaml

from . import state as _state


VALID_TARGETS = frozenset({"synthetic-fixture", "live-new-repo"})
VALID_SKILLS = frozenset(
    {
        "batch-job",
        "task-dag",
        "orchestrate-issue",
        "onboarding",
        "composition-guide",
    }
)


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_scenario(scenario_path: Path) -> dict[str, Any]:
    """Read and validate a scenario YAML.

    Validates:
      - ``scenario_id`` is a non-empty string
      - ``archetype`` is a non-empty string
      - ``skill_under_test`` is one of :data:`VALID_SKILLS`
      - ``target`` (if present) is one of :data:`VALID_TARGETS`
      - ``phases`` is a list of >=2 dicts with unique ``name``s
    """
    with scenario_path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"scenario {scenario_path} is not a YAML mapping")
    for key in ("scenario_id", "archetype", "skill_under_test", "phases"):
        if key not in data:
            raise ValueError(f"scenario {scenario_path} missing key {key!r}")
    if data["skill_under_test"] not in VALID_SKILLS:
        raise ValueError(
            f"scenario {scenario_path}: skill_under_test "
            f"{data['skill_under_test']!r} is not one of {sorted(VALID_SKILLS)}"
        )
    target = data.get("target", "synthetic-fixture")
    if target not in VALID_TARGETS:
        raise ValueError(
            f"scenario {scenario_path}: target {target!r} is not one of "
            f"{sorted(VALID_TARGETS)}"
        )
    phases = data["phases"]
    if not isinstance(phases, list) or len(phases) < 2:
        raise ValueError(
            f"scenario {scenario_path}: phases must be a list of >=2 items"
        )
    names = [p.get("name") for p in phases]
    if len(set(names)) != len(names):
        raise ValueError(
            f"scenario {scenario_path}: phase names must be unique; got {names}"
        )
    return data


def _initial_state(scenario: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Build the initial state dict for a fresh run of ``scenario``."""
    return {
        "run_id": run_id,
        "scenario_id": scenario["scenario_id"],
        "archetype": scenario["archetype"],
        "skill_under_test": scenario["skill_under_test"],
        "target": scenario.get("target", "synthetic-fixture"),
        "phases": [
            {"name": p["name"], "status": "pending"} for p in scenario["phases"]
        ],
        "diagnostics": {},
        "created_at": _utc_now_iso(),
    }


def run(scenario_path: Path, state_dir: Path, run_id: str) -> dict[str, Any]:
    """Initialise a fresh run of ``scenario_path`` under ``state_dir``.

    This is the ``setup`` entry point. It:
      1. Parses and validates the scenario YAML.
      2. Builds the initial state dict.
      3. Persists state.json.
      4. Returns the state dict.

    It does *not* execute any phases — callers invoke :func:`step` to
    advance.
    """
    scenario = _parse_scenario(scenario_path)
    initial = _initial_state(scenario, run_id)
    _state.save_state(state_dir, initial)
    return initial


def step(state_dir: Path) -> dict[str, Any]:
    """Advance the run in ``state_dir`` by one phase.

    Reads the current state, marks the first non-terminal phase as
    ``in_progress``, persists, then (in this stub) immediately marks
    it ``done`` and persists again. Real phase execution is delegated
    to the skill under test in the new repo; this stub exists so the
    Python package imports cleanly and the contract tests can run.

    Returns the updated state dict.
    """
    data = _state.load_state(state_dir)
    phases = data.get("phases", [])
    for phase in phases:
        if phase.get("status") in ("done", "skipped"):
            continue
        if phase.get("status") == "in_progress":
            phase["status"] = "done"
            phase["finished_at"] = _utc_now_iso()
            _state.save_state(state_dir, data)
            return data
        phase["status"] = "in_progress"
        phase["started_at"] = _utc_now_iso()
        _state.save_state(state_dir, data)
        phase["status"] = "done"
        phase["finished_at"] = _utc_now_iso()
        _state.save_state(state_dir, data)
        return data
    return data


def inspect(state_dir: Path) -> dict[str, Any]:
    """Return the current state dict from ``state_dir`` without mutating it."""
    return _state.load_state(state_dir)


__all__ = ["VALID_SKILLS", "VALID_TARGETS", "inspect", "run", "step"]
