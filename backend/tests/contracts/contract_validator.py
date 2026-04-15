"""Contract validator — schema extraction, validation, and diffing.

This module provides three primary helpers used by contract tests:

- ``validate_shape``: validate a sample against a JSON schema and return a
  human-readable diff when the sample violates the schema.
- ``extract_schema_from_samples``: auto-generate a permissive JSON schema
  from a set of real/recorded samples. Used to (re-)baseline schemas.
- ``diff_shapes``: structural diff between two JSON schemas describing what
  changed (fields added/removed/type-changed).

Design choices:

- Schemas are permissive by design: ``additionalProperties`` is allowed
  (APIs add new fields all the time — we don't want to fail on additions).
- Required fields are the intersection of fields present across samples —
  i.e. a field is only treated as required if it is present in ALL samples.
- Types are expressed as a JSON Schema ``type`` string or a list of types
  when the field is nullable or inconsistent across samples (e.g. ``[int, null]``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import jsonschema
from jsonschema import Draft202012Validator


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Result of a ``validate_shape`` call."""

    valid: bool
    errors: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return self.valid


# ---------------------------------------------------------------------------
# Shape validation
# ---------------------------------------------------------------------------


def validate_shape(sample: Any, schema: dict) -> ValidationResult:
    """Validate ``sample`` against ``schema`` with human-readable diff on failure.

    Returns ``ValidationResult(valid=True)`` when the sample matches the schema.
    Otherwise returns the list of errors with JSON paths and expected vs actual
    types — enough for a human to understand the breaking change at a glance.
    """

    validator = Draft202012Validator(schema)
    raw_errors = sorted(validator.iter_errors(sample), key=lambda e: list(e.absolute_path))
    if not raw_errors:
        return ValidationResult(valid=True, errors=[])

    messages: list[str] = []
    for err in raw_errors:
        path = _format_path(err.absolute_path)
        messages.append(_format_error(err, path))
    return ValidationResult(valid=False, errors=messages)


def _format_path(path_iter: Iterable[Any]) -> str:
    parts: list[str] = []
    for part in path_iter:
        if isinstance(part, int):
            parts.append(f"[{part}]")
        else:
            parts.append(f".{part}")
    joined = "".join(parts) or "<root>"
    if joined.startswith("."):
        joined = joined[1:] or "<root>"
    return joined


def _format_error(err: jsonschema.ValidationError, path: str) -> str:
    validator = err.validator
    if validator == "required":
        missing = err.message.split("'")[1] if "'" in err.message else err.message
        return f"MISSING_REQUIRED at {path}: field '{missing}' not present"
    if validator == "type":
        expected = err.schema.get("type")
        actual = type(err.instance).__name__
        return f"TYPE_MISMATCH at {path}: expected {expected}, got {actual} ({err.instance!r})"
    return f"VALIDATION_ERROR at {path}: {err.message}"


# ---------------------------------------------------------------------------
# Schema extraction
# ---------------------------------------------------------------------------


_JSON_TYPE_BY_PY: dict[type, str] = {
    dict: "object",
    list: "array",
    str: "string",
    bool: "boolean",
    int: "integer",
    float: "number",
    type(None): "null",
}


def _json_type(value: Any) -> str:
    # Order matters: bool before int (bool is subclass of int in Python).
    if isinstance(value, bool):
        return "boolean"
    for py_type, json_type in _JSON_TYPE_BY_PY.items():
        if isinstance(value, py_type):
            return json_type
    return "string"  # safe fallback


def extract_schema_from_samples(samples: Sequence[Any], title: str | None = None) -> dict:
    """Build a permissive JSON schema from a list of real samples.

    - Field is ``required`` iff present in ALL samples.
    - Field type is the union of observed types (``["integer", "null"]`` etc.).
    - Objects allow ``additionalProperties`` (permissive by design).
    - Arrays use the union schema of observed items.
    """

    if not samples:
        raise ValueError("extract_schema_from_samples requires at least one sample")

    schema = _merge_schemas([_infer_schema(s) for s in samples])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    if title:
        schema["title"] = title
    return schema


def _infer_schema(value: Any) -> dict:
    t = _json_type(value)
    if t == "object":
        props: dict[str, dict] = {}
        for k, v in value.items():
            props[k] = _infer_schema(v)
        return {
            "type": "object",
            "properties": props,
            "required": sorted(value.keys()),
            "additionalProperties": True,
        }
    if t == "array":
        if not value:
            return {"type": "array", "items": {}}
        item_schemas = [_infer_schema(v) for v in value]
        return {"type": "array", "items": _merge_schemas(item_schemas)}
    return {"type": t}


def _merge_schemas(schemas: list[dict]) -> dict:
    """Merge a list of inferred schemas into a single permissive schema."""

    if len(schemas) == 1:
        return schemas[0]

    types: list[str] = []
    for s in schemas:
        st = s.get("type")
        if isinstance(st, list):
            for tt in st:
                if tt not in types:
                    types.append(tt)
        elif st and st not in types:
            types.append(st)

    # Object merge
    if types == ["object"] or all(s.get("type") == "object" for s in schemas):
        all_props: dict[str, list[dict]] = {}
        required_sets: list[set[str]] = []
        for s in schemas:
            required_sets.append(set(s.get("required", [])))
            for k, v in (s.get("properties") or {}).items():
                all_props.setdefault(k, []).append(v)
        merged_props = {k: _merge_schemas(v) for k, v in all_props.items()}
        required = sorted(set.intersection(*required_sets)) if required_sets else []
        return {
            "type": "object",
            "properties": merged_props,
            "required": required,
            "additionalProperties": True,
        }

    # Array merge
    if types == ["array"] or all(s.get("type") == "array" for s in schemas):
        item_schemas = [s.get("items") for s in schemas if s.get("items")]
        item_schemas = [i for i in item_schemas if i]
        merged_items = _merge_schemas(item_schemas) if item_schemas else {}
        return {"type": "array", "items": merged_items}

    # Scalar / mixed — express as union of types.
    type_value: Any = types[0] if len(types) == 1 else types
    return {"type": type_value}


# ---------------------------------------------------------------------------
# Schema diff
# ---------------------------------------------------------------------------


def diff_shapes(schema_a: dict, schema_b: dict, path: str = "<root>") -> list[str]:
    """Return a human-readable diff between two JSON schemas.

    Reports added fields, removed fields, type changes, and required-set
    changes. Primarily used for debugging and for re-baselining workflows.
    """

    diffs: list[str] = []

    type_a = schema_a.get("type")
    type_b = schema_b.get("type")
    if type_a != type_b:
        diffs.append(f"TYPE_CHANGED at {path}: {type_a!r} -> {type_b!r}")

    if type_a == "object" and type_b == "object":
        props_a = schema_a.get("properties", {}) or {}
        props_b = schema_b.get("properties", {}) or {}
        req_a = set(schema_a.get("required", []) or [])
        req_b = set(schema_b.get("required", []) or [])

        added = sorted(set(props_b) - set(props_a))
        removed = sorted(set(props_a) - set(props_b))
        for name in added:
            diffs.append(f"FIELD_ADDED at {path}.{name}")
        for name in removed:
            diffs.append(f"FIELD_REMOVED at {path}.{name}")

        became_required = sorted(req_b - req_a - set(added))
        became_optional = sorted(req_a - req_b - set(removed))
        for name in became_required:
            diffs.append(f"REQUIRED_ADDED at {path}.{name}")
        for name in became_optional:
            diffs.append(f"REQUIRED_REMOVED at {path}.{name}")

        for name in sorted(set(props_a) & set(props_b)):
            diffs.extend(diff_shapes(props_a[name], props_b[name], f"{path}.{name}"))

    elif type_a == "array" and type_b == "array":
        items_a = schema_a.get("items") or {}
        items_b = schema_b.get("items") or {}
        diffs.extend(diff_shapes(items_a, items_b, f"{path}[]"))

    return diffs


# ---------------------------------------------------------------------------
# Snapshot IO helpers
# ---------------------------------------------------------------------------


SNAPSHOT_ROOT = Path(__file__).parent / "snapshots"
SCHEMA_ROOT = Path(__file__).parent / "schemas"


def load_snapshot(relative_path: str) -> dict:
    """Load a JSON snapshot relative to ``tests/contracts/snapshots/``."""

    path = SNAPSHOT_ROOT / relative_path
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schema(name: str) -> dict:
    """Load a committed JSON schema by file name (from ``schemas/``)."""

    path = SCHEMA_ROOT / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_schema(name: str, schema: dict) -> Path:
    """Persist a schema under ``schemas/<name>`` (used by re-baselining)."""

    path = SCHEMA_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    return path


__all__ = [
    "ValidationResult",
    "validate_shape",
    "extract_schema_from_samples",
    "diff_shapes",
    "load_snapshot",
    "load_schema",
    "write_schema",
]
