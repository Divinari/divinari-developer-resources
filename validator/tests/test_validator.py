# SPDX-License-Identifier: Apache-2.0
"""Automated tests for Divinari clean-room schemas and validator CLI."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validator"))

import divinari_validate  # noqa: E402

SCHEMA_PAIRS = [
    ("schemas/language-metadata.schema.json", "examples/valid-language-metadata-tl.json"),
    ("schemas/lexicon-entry.schema.json", "examples/valid-lexicon-tl.json"),
    ("schemas/example-sentence.schema.json", "examples/valid-example-sentence-tl.json"),
    ("schemas/writing-system.schema.json", "examples/valid-writing-system-baybayin.json"),
    ("schemas/curriculum-unit.schema.json", "examples/valid-curriculum-unit.json"),
    ("schemas/heritage-contribution.schema.json", "examples/valid-heritage-contribution.json"),
    ("schemas/scripture-bundle.schema.json", "examples/valid-scripture-kjv-excerpt.json"),
]


def test_all_valid_examples_pass() -> None:
    for schema_rel, example_rel in SCHEMA_PAIRS:
        errs = divinari_validate.validate_file(ROOT / example_rel, ROOT / schema_rel)
        assert errs == [], f"{example_rel} unexpectedly failed: {errs}"


def test_invalid_numbered_placeholder_rejected() -> None:
    errs = divinari_validate.validate_file(
        ROOT / "examples/invalid-fixtures/invalid-numbered-placeholder.json",
        ROOT / "schemas/lexicon-entry.schema.json",
    )
    assert any("synthetic numeric suffix" in e or "commercial trade instrument" in e for e in errs), errs


def test_invalid_bad_license_rejected() -> None:
    errs = divinari_validate.validate_file(
        ROOT / "examples/invalid-fixtures/invalid-bad-license.json",
        ROOT / "schemas/lexicon-entry.schema.json",
    )
    assert any("license" in e.lower() for e in errs), errs


def test_invalid_duplicate_concept_rejected() -> None:
    errs = divinari_validate.validate_file(
        ROOT / "examples/invalid-fixtures/invalid-duplicate-key.json",
        ROOT / "schemas/lexicon-entry.schema.json",
    )
    assert any("duplicate" in e.lower() for e in errs), errs


def test_invalid_token_span_rejected() -> None:
    errs = divinari_validate.validate_file(
        ROOT / "examples/invalid-fixtures/invalid-bad-token-span.json",
        ROOT / "schemas/example-sentence.schema.json",
    )
    assert any("surface" in e.lower() or "slice" in e.lower() for e in errs), errs
