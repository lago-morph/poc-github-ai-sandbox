"""test_scenario_yamls — test-harness scenarios have valid spec."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from .conftest import DISTRIBUTABLE_SKILLS, PACKAGE_ROOT


SCENARIOS_ROOT = PACKAGE_ROOT / "test-harness" / "scenarios"
ARCHETYPES_ROOT = PACKAGE_ROOT / "test-harness" / "archetypes"


def _scenario_paths():
    if not SCENARIOS_ROOT.is_dir():
        return []
    return sorted(SCENARIOS_ROOT.glob("*.yml"))


def _valid_archetypes() -> set[str]:
    if not ARCHETYPES_ROOT.is_dir():
        return set()
    return {p.name for p in ARCHETYPES_ROOT.iterdir() if p.is_dir()}


def test_scenarios_dir_exists():
    assert SCENARIOS_ROOT.is_dir()


def test_eighteen_scenarios_present():
    paths = _scenario_paths()
    assert len(paths) == 18, f"expected 18 scenarios, got {len(paths)}"


@pytest.mark.parametrize("scenario_path", _scenario_paths(), ids=lambda p: p.name)
def test_scenario_parses(scenario_path: Path):
    data = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    for key in ("scenario_id", "archetype", "skill_under_test", "phases"):
        assert key in data, f"{scenario_path} missing key {key!r}"


@pytest.mark.parametrize("scenario_path", _scenario_paths(), ids=lambda p: p.name)
def test_scenario_archetype_resolves(scenario_path: Path):
    data = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    valid = _valid_archetypes()
    assert data["archetype"] in valid, (
        f"{scenario_path.name}: archetype {data['archetype']!r} is not one of {sorted(valid)}"
    )


@pytest.mark.parametrize("scenario_path", _scenario_paths(), ids=lambda p: p.name)
def test_scenario_skill_under_test_is_valid(scenario_path: Path):
    data = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    assert data["skill_under_test"] in DISTRIBUTABLE_SKILLS, (
        f"{scenario_path.name}: skill_under_test {data['skill_under_test']!r} "
        f"not one of {DISTRIBUTABLE_SKILLS}"
    )


@pytest.mark.parametrize("scenario_path", _scenario_paths(), ids=lambda p: p.name)
def test_scenario_has_at_least_two_phases_with_unique_names(scenario_path: Path):
    data = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    phases = data["phases"]
    assert isinstance(phases, list) and len(phases) >= 2, (
        f"{scenario_path.name}: scenario must have at least 2 phases"
    )
    names = [p["name"] for p in phases]
    assert len(names) == len(set(names)), (
        f"{scenario_path.name}: duplicate phase names {names}"
    )
