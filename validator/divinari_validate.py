# SPDX-License-Identifier: Apache-2.0
"""Standalone clean-room validator CLI for Divinari public open-data schemas & contribution rules."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import unicodedata
from typing import Any

try:
    from jsonschema import Draft202012Validator  # type: ignore
except ImportError:  # pragma: no cover - stdlib fallback handles local zero-dep runs
    Draft202012Validator = None

DISALLOWED_LICENSE_VALUES = {"CC-BY-SA", "CC-BY-SA-4.0", "ALL RIGHTS RESERVED", "UNKNOWN", "PROPRIETARY"}
FORBIDDEN_CITATION_TERMS = ("edge-tts", "google tts", "lai ", "pbs 1978+", "kwf commercial")
SYNTHETIC_SUFFIX_RE = re.compile(r"(?:[-_]\d+|\(\d+\))$", re.IGNORECASE)
SYNTHETIC_TEXT_PATTERNS = [
    re.compile(r"\(nuance\s+\d+\)", re.IGNORECASE),
    re.compile(r"plays a vital role in", re.IGNORECASE),
    re.compile(r"^Definition in .+ for\b", re.IGNORECASE),
    re.compile(r"^Sample sentence (?:with|containing)\b", re.IGNORECASE),
    re.compile(r"^commercial trade instrument", re.IGNORECASE),
    re.compile(r"^Lexical entry for\b", re.IGNORECASE),
]


def _check_type(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_check_type(value, t) for t in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, (int, float)) and not isinstance(value, bool))
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _validate_with_stdlib_schema(data: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Strict subset Draft 2020-12 JSON Schema validator used when jsonschema is unavailable."""
    errors: list[str] = []
    if "type" in schema and not _check_type(data, schema["type"]):
        return [f"{path}: expected type {schema['type']}, got {type(data).__name__}"]
    if "const" in schema and data != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {data!r}")
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: value {data!r} not in allowed enum {schema['enum']}")

    if isinstance(data, str):
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"{path}: string length {len(data)} < minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], data):
            errors.append(f"{path}: string {data!r} does not match pattern {schema['pattern']}")

    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{path}: {data} < minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{path}: {data} > maximum {schema['maximum']}")

    if isinstance(data, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"{path}: missing required key {req!r}")
        if schema.get("additionalProperties") is False:
            for k in data:
                if k not in props:
                    errors.append(f"{path}: unexpected additional property {k!r}")
        for k, v in data.items():
            if k in props:
                errors.extend(_validate_with_stdlib_schema(v, props[k], f"{path}.{k}"))

    if isinstance(data, list):
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(f"{path}: array length {len(data)} < minItems {schema['minItems']}")
        if "items" in schema:
            for idx, item in enumerate(data):
                errors.extend(_validate_with_stdlib_schema(item, schema["items"], f"{path}[{idx}]"))
    return errors


def check_syntax_and_encoding(file_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if file_path.suffix.lower() in {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".sqlite", ".db", ".enc"}:
        return [f"{file_path}: forbidden binary audio/database/encrypted file extension"]
    raw = file_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{file_path}: contains UTF-8 BOM")
    if b"\r\n" in raw:
        errors.append(f"{file_path}: contains CRLF line endings")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"{file_path}: invalid UTF-8 ({exc})"]
    if text != unicodedata.normalize("NFC", text):
        errors.append(f"{file_path}: not Unicode NFC normalized")
    if text and not text.endswith("\n"):
        errors.append(f"{file_path}: missing trailing newline")
    if file_path.suffix.lower() == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{file_path}: invalid JSON ({exc})")
    return errors


def check_formatting(file_path: pathlib.Path) -> list[str]:
    if file_path.suffix.lower() != ".json":
        return []
    text = file_path.read_text(encoding="utf-8")
    obj = json.loads(text)
    expected = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if text != expected:
        return [f"{file_path}: JSON is not formatted with 2-space indentation and LF trailing newline"]
    return []


def check_schema(data: Any, schema: dict[str, Any]) -> list[str]:
    if Draft202012Validator is not None:
        v = Draft202012Validator(schema)
        return [f"{'/'.join(str(p) for p in err.path) or '$'}: {err.message}" for err in v.iter_errors(data)]
    return _validate_with_stdlib_schema(data, schema)


def _check_tokens(sentence_text: str, tokens: list[dict[str, Any]], label: str, errors: list[str]) -> None:
    for idx, tok in enumerate(tokens):
        start = tok.get("char_start")
        end = tok.get("char_end")
        surf = tok.get("surface", "")
        if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(sentence_text)):
            errors.append(f"{label} token[{idx}] bounds [{start}, {end}) out of range for length {len(sentence_text)}")
            continue
        actual = sentence_text[start:end]
        if actual != surf:
            errors.append(f"{label} token[{idx}] slice {actual!r} != surface {surf!r}")


def check_duplicates_and_spans(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    lang = data.get("language_code", "")
    seen_concepts: set[tuple[str, str]] = set()
    seen_senses: set[tuple[str, str, str, str]] = set()

    for idx, entry in enumerate(data.get("entries", [])):
        ck = entry.get("concept_key", "")
        sk = entry.get("sense_key", "")
        pos = entry.get("part_of_speech", "")
        norm = entry.get("normalized_term", "")
        if (lang, ck) in seen_concepts:
            errors.append(f"entries[{idx}]: duplicate (language_code, concept_key) = ({lang}, {ck})")
        seen_concepts.add((lang, ck))
        sense_tuple = (lang, norm, pos, sk)
        if sense_tuple in seen_senses:
            errors.append(f"entries[{idx}]: duplicate (language_code, normalized_term, pos, sense_key) = {sense_tuple}")
        seen_senses.add(sense_tuple)

        for ex_idx, ex in enumerate(entry.get("examples", [])):
            _check_tokens(ex.get("sentence_text", ""), ex.get("tokens", []), f"entries[{idx}].examples[{ex_idx}]", errors)

    seen_sentences: set[str] = set()
    for idx, sent in enumerate(data.get("sentences", [])):
        sid = sent.get("sentence_id", "")
        if sid in seen_sentences:
            errors.append(f"sentences[{idx}]: duplicate sentence_id {sid!r}")
        seen_sentences.add(sid)
        _check_tokens(sent.get("sentence_text", ""), sent.get("tokens", []), f"sentences[{idx}]", errors)
    return errors


def check_provenance_and_license(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    lic = str(data.get("license", "")).strip()
    if not lic and isinstance(data.get("licenseInfo"), dict):
        lic = str(data["licenseInfo"].get("license", "")).strip()
    if lic.upper() in DISALLOWED_LICENSE_VALUES:
        errors.append(f"Disallowed or incompatible license: {lic!r}")

    citation = " ".join(
        [
            str(data.get("source_citation", "")),
            str(data.get("licenseInfo", {}).get("verified_edition", "")),
            str(data.get("licenseInfo", {}).get("publisher", "")),
            str(data.get("licenseInfo", {}).get("digital_source", "")),
        ]
    ).lower()
    for term in FORBIDDEN_CITATION_TERMS:
        if term in citation:
            errors.append(f"Forbidden provenance/TTS citation term detected: {term!r}")
    return errors


def _scan_synthetic_strings(obj: Any, path: str, errors: list[str]) -> None:
    if isinstance(obj, dict):
        for key in ("term", "normalized_term"):
            val = obj.get(key)
            if isinstance(val, str) and SYNTHETIC_SUFFIX_RE.search(val.strip()):
                errors.append(f"{path}.{key}: synthetic numeric suffix detected in {val!r}")
        for k, v in obj.items():
            _scan_synthetic_strings(v, f"{path}.{k}", errors)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_synthetic_strings(item, f"{path}[{idx}]", errors)
    elif isinstance(obj, str):
        for pat in SYNTHETIC_TEXT_PATTERNS:
            if pat.search(obj.strip()):
                errors.append(f"{path}: synthetic/boilerplate pattern {pat.pattern!r} matched {obj!r}")


def check_anti_synthetic(data: Any) -> list[str]:
    errors: list[str] = []
    _scan_synthetic_strings(data, "$", errors)
    return errors


def validate_file(file_path: pathlib.Path, schema_path: pathlib.Path | None = None, checks: list[str] | None = None) -> list[str]:
    active = set(checks or ["all"])
    errors: list[str] = []
    if active & {"all", "syntax-and-encoding"}:
        errors.extend(check_syntax_and_encoding(file_path))
    if file_path.suffix.lower() != ".json" or any("invalid JSON" in e for e in errors):
        return errors
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if (active & {"all", "schema"}) and schema_path is not None:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors.extend(check_schema(data, schema))
    if isinstance(data, dict):
        if active & {"all", "duplicates-and-spans"}:
            errors.extend(check_duplicates_and_spans(data))
        if active & {"all", "provenance-and-license"}:
            errors.extend(check_provenance_and_license(data))
    if active & {"all", "anti-synthetic"}:
        errors.extend(check_anti_synthetic(data))
    if active & {"all", "formatting"}:
        errors.extend(check_formatting(file_path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Divinari public open-data validator CLI")
    parser.add_argument("target", help="JSON contribution file to validate")
    parser.add_argument("--schema", help="Path to Draft 2020-12 JSON Schema file")
    parser.add_argument(
        "--check",
        default="all",
        choices=[
            "all",
            "syntax-and-encoding",
            "schema",
            "duplicates-and-spans",
            "provenance-and-license",
            "anti-synthetic",
            "formatting",
        ],
    )
    args = parser.parse_args()
    errs = validate_file(
        pathlib.Path(args.target),
        pathlib.Path(args.schema) if args.schema else None,
        [args.check],
    )
    if errs:
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"OK: {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
