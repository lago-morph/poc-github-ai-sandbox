"""test_schema_validity — bundled JSON schemas are Draft 2020-12 valid."""

from __future__ import annotations

import json

import pytest
from jsonschema import Draft202012Validator

from .conftest import PACKAGE_ROOT, SKILLS_WITH_TEMPLATES


def _schema_paths():
    out = []
    for skill in SKILLS_WITH_TEMPLATES:
        schemas_root = PACKAGE_ROOT / "skills" / skill / "templates" / "agent" / "schemas"
        if not schemas_root.is_dir():
            continue
        for p in sorted(schemas_root.rglob("*.schema.json")):
            out.append(p)
    return out


SCHEMA_PATHS = _schema_paths()


@pytest.mark.parametrize("schema_path", SCHEMA_PATHS, ids=lambda p: p.relative_to(PACKAGE_ROOT).as_posix())
def test_schema_parses_as_json(schema_path):
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


@pytest.mark.parametrize("schema_path", SCHEMA_PATHS, ids=lambda p: p.relative_to(PACKAGE_ROOT).as_posix())
def test_schema_is_draft_2020_12(schema_path):
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    assert data.get("$schema") == "https://json-schema.org/draft/2020-12/schema", (
        f"Schema {schema_path} has $schema={data.get('$schema')!r}; expected draft 2020-12"
    )


@pytest.mark.parametrize("schema_path", SCHEMA_PATHS, ids=lambda p: p.relative_to(PACKAGE_ROOT).as_posix())
def test_schema_validates_against_meta_schema(schema_path):
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(data)


def test_we_actually_found_schemas():
    assert len(SCHEMA_PATHS) > 0, "Expected at least one bundled schema"
