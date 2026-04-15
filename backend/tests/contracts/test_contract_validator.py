"""Unit tests for the contract_validator helper module."""

from __future__ import annotations

import pytest

from .contract_validator import (
    diff_shapes,
    extract_schema_from_samples,
    validate_shape,
)


@pytest.mark.contract
class TestExtractSchema:
    def test_single_sample_produces_schema(self):
        schema = extract_schema_from_samples([{"a": 1, "b": "x"}])
        assert schema["type"] == "object"
        assert "a" in schema["properties"]
        assert "b" in schema["properties"]
        assert schema["properties"]["a"]["type"] == "integer"
        assert schema["properties"]["b"]["type"] == "string"
        assert set(schema["required"]) == {"a", "b"}

    def test_required_is_intersection_across_samples(self):
        schema = extract_schema_from_samples([
            {"a": 1, "b": "x"},
            {"a": 2},  # missing b → b NOT required
        ])
        assert "a" in schema["required"]
        assert "b" not in schema["required"]
        assert "b" in schema["properties"]

    def test_null_values_produce_union_type(self):
        schema = extract_schema_from_samples([
            {"a": 1},
            {"a": None},
        ])
        t = schema["properties"]["a"]["type"]
        assert t == ["integer", "null"] or t == ["null", "integer"]

    def test_empty_samples_raises(self):
        with pytest.raises(ValueError):
            extract_schema_from_samples([])

    def test_nested_objects_and_arrays(self):
        schema = extract_schema_from_samples([
            {"items": [{"price": 10}, {"price": 20}], "meta": {"page": 1}},
        ])
        items = schema["properties"]["items"]
        assert items["type"] == "array"
        assert items["items"]["type"] == "object"
        assert "price" in items["items"]["required"]
        assert schema["properties"]["meta"]["type"] == "object"


@pytest.mark.contract
class TestValidateShape:
    def test_valid_sample_returns_ok(self):
        schema = extract_schema_from_samples([{"a": 1}])
        r = validate_shape({"a": 2}, schema)
        assert r.valid
        assert r.errors == []

    def test_missing_required_field_is_reported(self):
        schema = extract_schema_from_samples([{"a": 1, "b": 2}])
        r = validate_shape({"a": 1}, schema)
        assert not r.valid
        assert any("MISSING_REQUIRED" in e and "'b'" in e for e in r.errors)

    def test_wrong_type_is_reported_with_path(self):
        schema = extract_schema_from_samples([{"a": 1}])
        r = validate_shape({"a": "not-an-int"}, schema)
        assert not r.valid
        assert any("TYPE_MISMATCH" in e for e in r.errors)

    def test_additional_properties_are_permitted(self):
        schema = extract_schema_from_samples([{"a": 1}])
        # New field appearing — should NOT break contract.
        r = validate_shape({"a": 1, "new_field": "added-by-api"}, schema)
        assert r.valid


@pytest.mark.contract
class TestDiffShapes:
    def test_identical_schemas_no_diff(self):
        s = extract_schema_from_samples([{"a": 1, "b": "x"}])
        assert diff_shapes(s, s) == []

    def test_added_field_is_detected(self):
        a = extract_schema_from_samples([{"a": 1}])
        b = extract_schema_from_samples([{"a": 1, "new": 2}])
        diffs = diff_shapes(a, b)
        assert any("FIELD_ADDED" in d and "new" in d for d in diffs)

    def test_removed_field_is_detected(self):
        a = extract_schema_from_samples([{"a": 1, "old": 1}])
        b = extract_schema_from_samples([{"a": 1}])
        diffs = diff_shapes(a, b)
        assert any("FIELD_REMOVED" in d and "old" in d for d in diffs)

    def test_type_change_is_detected(self):
        a = extract_schema_from_samples([{"a": 1}])  # integer
        b = extract_schema_from_samples([{"a": "1"}])  # string
        diffs = diff_shapes(a, b)
        assert any("TYPE_CHANGED" in d for d in diffs)
