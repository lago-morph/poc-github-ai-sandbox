"""test_skill_md_frontmatter — every SKILL.md has required frontmatter."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from .conftest import DISTRIBUTABLE_SKILLS, PACKAGE_ROOT

ALL_SKILL_MDS = [
    *[PACKAGE_ROOT / "skills" / name / "SKILL.md" for name in DISTRIBUTABLE_SKILLS],
    PACKAGE_ROOT / "test-harness" / "SKILL.md",
]


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise AssertionError("SKILL.md does not start with `---` frontmatter delimiter")
    end = text.find("\n---", 3)
    if end == -1:
        raise AssertionError("SKILL.md frontmatter is unterminated")
    fm_text = text[3:end]
    body = text[end + 4 :]
    data = yaml.safe_load(fm_text)
    if not isinstance(data, dict):
        raise AssertionError("SKILL.md frontmatter is not a YAML mapping")
    return data, body


@pytest.mark.parametrize("skill_md", ALL_SKILL_MDS, ids=lambda p: p.parent.name)
def test_skill_md_exists_and_starts_with_frontmatter(skill_md: Path):
    assert skill_md.is_file(), f"missing SKILL.md: {skill_md}"
    text = skill_md.read_text(encoding="utf-8")
    fm, _body = _split_frontmatter(text)
    assert isinstance(fm, dict)


@pytest.mark.parametrize("skill_md", ALL_SKILL_MDS, ids=lambda p: p.parent.name)
def test_required_keys_present(skill_md: Path):
    fm, _ = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
    for key in ("name", "description", "allowed-tools"):
        assert key in fm, f"{skill_md} frontmatter missing key: {key!r}"


@pytest.mark.parametrize("skill_md", ALL_SKILL_MDS, ids=lambda p: p.parent.name)
def test_name_matches_directory(skill_md: Path):
    fm, _ = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
    assert fm["name"] == skill_md.parent.name


@pytest.mark.parametrize("skill_md", ALL_SKILL_MDS, ids=lambda p: p.parent.name)
def test_description_is_nonempty_string(skill_md: Path):
    fm, _ = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
    desc = fm["description"]
    assert isinstance(desc, str)
    assert desc.strip(), "description is empty"


@pytest.mark.parametrize("skill_md", ALL_SKILL_MDS, ids=lambda p: p.parent.name)
def test_allowed_tools_is_list_of_strings(skill_md: Path):
    fm, _ = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
    tools = fm["allowed-tools"]
    assert isinstance(tools, list)
    assert tools, "allowed-tools is empty"
    for t in tools:
        assert isinstance(t, str)
