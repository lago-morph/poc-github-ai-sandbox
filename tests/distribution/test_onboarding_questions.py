"""test_onboarding_questions — interview-questions.yml schema + completeness."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from .conftest import PACKAGE_ROOT


QUESTIONS_PATH = (
    PACKAGE_ROOT / "skills" / "onboarding" / "templates" / "interview-questions.yml"
)

EXPECTED_CATEGORY_IDS = {
    "intent",
    "problems",
    "current_workflow",
    "integration",
    "sensitive_files",
    "confirmation",
}


@pytest.fixture(scope="module")
def questions_data():
    text = QUESTIONS_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def test_questions_file_exists():
    assert QUESTIONS_PATH.is_file()


def test_questions_yaml_top_level_keys(questions_data):
    assert isinstance(questions_data, dict)
    assert "categories" in questions_data
    assert isinstance(questions_data["categories"], list)


def test_questions_six_categories(questions_data):
    cats = questions_data["categories"]
    assert len(cats) == 6, f"expected exactly 6 categories, got {len(cats)}"


def test_questions_expected_category_ids(questions_data):
    cat_ids = {c["id"] for c in questions_data["categories"]}
    assert cat_ids == EXPECTED_CATEGORY_IDS, (
        f"unexpected category set: {cat_ids - EXPECTED_CATEGORY_IDS} extra, "
        f"{EXPECTED_CATEGORY_IDS - cat_ids} missing"
    )


def test_questions_each_has_required_keys(questions_data):
    for cat in questions_data["categories"]:
        for q in cat.get("questions", []):
            for key in ("id", "text", "type"):
                assert key in q, f"question in category {cat['id']} missing {key!r}: {q}"


def test_questions_no_duplicate_ids(questions_data):
    seen: list[str] = []
    for cat in questions_data["categories"]:
        for q in cat.get("questions", []):
            assert q["id"] not in seen, f"duplicate question id: {q['id']}"
            seen.append(q["id"])
    assert len(seen) >= 12, f"expected at least 12 questions, got {len(seen)}"


def test_questions_choice_types_have_choices(questions_data):
    choice_types = {"choice", "multi_choice"}
    for cat in questions_data["categories"]:
        for q in cat.get("questions", []):
            if q["type"] in choice_types:
                assert "choices" in q, f"{q['id']} has type={q['type']} but no choices"
                assert isinstance(q["choices"], list) and q["choices"]
