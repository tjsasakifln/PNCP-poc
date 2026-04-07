"""Tests for A/B testing service — deterministic variant assignment."""

import json
from unittest.mock import patch

import pytest


class TestGetVariant:
    """Test deterministic variant assignment."""

    def test_same_user_same_experiment_returns_same_variant(self):
        from services.ab_testing import get_variant

        experiments = {"cta_copy": {"variants": ["control", "variant_a"]}}
        with patch("services.ab_testing._get_active_experiments", return_value=experiments):
            v1 = get_variant("user-123", "cta_copy")
            v2 = get_variant("user-123", "cta_copy")
            assert v1 == v2
            assert v1 in ["control", "variant_a"]

    def test_different_users_get_distributed(self):
        from services.ab_testing import get_variant

        experiments = {"pricing": {"variants": ["control", "variant_a"]}}
        with patch("services.ab_testing._get_active_experiments", return_value=experiments):
            variants = set()
            for i in range(100):
                v = get_variant(f"user-{i}", "pricing")
                variants.add(v)
            assert len(variants) == 2  # both variants assigned across 100 users

    def test_empty_user_id_returns_none(self):
        from services.ab_testing import get_variant

        assert get_variant("", "cta_copy") is None

    def test_empty_experiment_returns_none(self):
        from services.ab_testing import get_variant

        assert get_variant("user-123", "") is None

    def test_inactive_experiment_returns_none(self):
        from services.ab_testing import get_variant

        with patch("services.ab_testing._get_active_experiments", return_value={}):
            assert get_variant("user-123", "nonexistent") is None

    def test_explicit_variants_override_config(self):
        from services.ab_testing import get_variant

        with patch("services.ab_testing._get_active_experiments", return_value={}):
            v = get_variant("user-123", "test", variants=["a", "b", "c"])
            assert v in ["a", "b", "c"]

    def test_three_variants_distribution(self):
        from services.ab_testing import get_variant

        experiments = {"test": {"variants": ["a", "b", "c"]}}
        with patch("services.ab_testing._get_active_experiments", return_value=experiments):
            variants = set()
            for i in range(200):
                v = get_variant(f"user-{i}", "test")
                variants.add(v)
            assert len(variants) == 3


class TestGetUserExperiments:
    """Test fetching all active experiments for a user."""

    def test_returns_all_active_experiments(self):
        from services.ab_testing import get_user_experiments

        experiments = {
            "cta_copy": {"variants": ["control", "variant_a"]},
            "pricing": {"variants": ["show_monthly", "show_annual"]},
        }
        with patch("services.ab_testing._get_active_experiments", return_value=experiments):
            result = get_user_experiments("user-123")
            assert len(result) == 2
            assert "cta_copy" in result
            assert "pricing" in result
            assert result["cta_copy"] in ["control", "variant_a"]
            assert result["pricing"] in ["show_monthly", "show_annual"]

    def test_empty_user_id_returns_empty(self):
        from services.ab_testing import get_user_experiments

        assert get_user_experiments("") == {}

    def test_no_active_experiments_returns_empty(self):
        from services.ab_testing import get_user_experiments

        with patch("services.ab_testing._get_active_experiments", return_value={}):
            assert get_user_experiments("user-123") == {}


class TestGetActiveExperiments:
    """Test experiment config loading from env."""

    def test_disabled_flag_returns_empty(self):
        from services.ab_testing import _get_active_experiments

        with patch("services.ab_testing.get_feature_flag", return_value=False):
            assert _get_active_experiments() == {}

    def test_valid_json_returns_experiments(self):
        from services.ab_testing import _get_active_experiments

        experiments = {"test": {"variants": ["a", "b"]}}
        with (
            patch("services.ab_testing.get_feature_flag", return_value=True),
            patch.dict("os.environ", {"AB_ACTIVE_EXPERIMENTS": json.dumps(experiments)}),
        ):
            result = _get_active_experiments()
            assert result == experiments

    def test_invalid_json_returns_empty(self):
        from services.ab_testing import _get_active_experiments

        with (
            patch("services.ab_testing.get_feature_flag", return_value=True),
            patch.dict("os.environ", {"AB_ACTIVE_EXPERIMENTS": "not-json"}),
        ):
            result = _get_active_experiments()
            assert result == {}
