"""HARDEN-010: ComprasGov v3 feature flag disable tests.

Validates that COMPRASGOV_ENABLED=false (default) causes ComprasGov
to be skipped in consolidation, logged at startup, and easily re-enabled.
"""

import logging
from unittest.mock import patch



# ---------------------------------------------------------------------------
# AC1: Feature flag exists in config.py with default=false
# ---------------------------------------------------------------------------
class TestAC1FeatureFlag:
    def test_default_is_false(self):
        """COMPRASGOV_ENABLED defaults to false."""
        from config import COMPRASGOV_ENABLED
        assert COMPRASGOV_ENABLED is False

    @patch.dict("os.environ", {"COMPRASGOV_ENABLED": "true"})
    def test_env_var_enables(self):
        """Setting COMPRASGOV_ENABLED=true enables the flag."""
        import importlib
        import config
        importlib.reload(config)
        try:
            assert config.COMPRASGOV_ENABLED is True
        finally:
            importlib.reload(config)

    def test_registered_in_feature_flag_registry(self):
        """Flag is in _FEATURE_FLAG_REGISTRY for runtime toggles."""
        from config import _FEATURE_FLAG_REGISTRY
        assert "COMPRASGOV_ENABLED" in _FEATURE_FLAG_REGISTRY
        env_var, default = _FEATURE_FLAG_REGISTRY["COMPRASGOV_ENABLED"]
        assert env_var == "COMPRASGOV_ENABLED"
        assert default == "false"


# ---------------------------------------------------------------------------
# AC2: Consolidation skips ComprasGov when disabled
# ---------------------------------------------------------------------------
class TestAC2ConsolidationSkip:
    @patch("config.COMPRASGOV_ENABLED", False)
    def test_source_config_disabled_when_flag_false(self):
        """source_config.compras_gov.enabled=False when COMPRASGOV_ENABLED=false."""
        from source_config.sources import SourceConfig
        config = SourceConfig.from_env()
        assert config.compras_gov.enabled is False
        assert "ComprasGov" not in config.get_enabled_sources()

    @patch("config.COMPRASGOV_ENABLED", True)
    def test_source_config_enabled_when_flag_true(self):
        """source_config.compras_gov.enabled=True when COMPRASGOV_ENABLED=true."""
        from source_config.sources import SourceConfig
        config = SourceConfig.from_env()
        assert config.compras_gov.enabled is True
        assert "ComprasGov" in config.get_enabled_sources()


# ---------------------------------------------------------------------------
# AC3: Startup warning log when disabled
# ---------------------------------------------------------------------------
class TestAC3StartupWarning:
    @patch("config.COMPRASGOV_ENABLED", False)
    def test_logs_warning_when_disabled(self, caplog):
        """log_feature_flags() emits WARNING when ComprasGov is disabled."""
        from config import log_feature_flags
        with caplog.at_level(logging.WARNING, logger="config"):
            log_feature_flags()
        assert any(
            "ComprasGov v3 source is DISABLED" in msg
            for msg in caplog.messages
        )

    @patch("config.COMPRASGOV_ENABLED", True)
    def test_no_warning_when_enabled(self, caplog):
        """log_feature_flags() does NOT warn when ComprasGov is enabled."""
        from config import log_feature_flags
        with caplog.at_level(logging.WARNING, logger="config"):
            log_feature_flags()
        assert not any(
            "ComprasGov v3 source is DISABLED" in msg
            for msg in caplog.messages
        )


# ---------------------------------------------------------------------------
# AC4: Easy to re-enable via env var
# ---------------------------------------------------------------------------
class TestAC4ReEnable:
    @patch.dict("os.environ", {"COMPRASGOV_ENABLED": "true"})
    def test_reenable_via_env_var(self):
        """Setting COMPRASGOV_ENABLED=true re-enables ComprasGov."""
        import importlib
        import config
        importlib.reload(config)
        try:
            assert config.COMPRASGOV_ENABLED is True
            from source_config.sources import SourceConfig
            sc = SourceConfig.from_env()
            assert sc.compras_gov.enabled is True
        finally:
            importlib.reload(config)


# ---------------------------------------------------------------------------
# AC5: Integration — search pipeline skips ComprasGov when disabled
# ---------------------------------------------------------------------------
class TestAC5PipelineSkip:
    @patch("config.COMPRASGOV_ENABLED", False)
    def test_comprasgov_not_in_enabled_sources_default(self):
        """With default config, ComprasGov is not in enabled sources list."""
        from source_config.sources import SourceConfig
        config = SourceConfig.from_env()
        enabled = config.get_enabled_sources()
        assert "ComprasGov" not in enabled
        # PNCP and Portal should still be enabled
        assert "PNCP" in enabled
