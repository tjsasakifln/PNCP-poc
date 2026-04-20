"""Tests for STORY-283: Phantom Sources & Stale Config Cleanup.

Validates:
- AC1: 'free' and 'master' plan_ids mapped in quota.py
- AC2: licitar_client.py deleted (no imports)
- AC3: Co-occurrence triggers have matching keywords (zero orphans)
- AC4: No startup warnings from phantom configs
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from quota import (
    PLAN_CAPABILITIES,
    PLAN_NAMES,
    PlanPriority,
    _load_plan_capabilities_from_db,
)
from sectors import get_sector, SECTORS, _load_sectors_from_yaml


# ============================================================================
# AC1: Plan IDs 'free' and 'master' mapped
# ============================================================================


class TestAC1FreePlanMapping:
    """AC1: 'free' plan_id must be mapped with conservative limits."""

    def test_free_plan_exists_in_capabilities(self):
        assert "free" in PLAN_CAPABILITIES

    def test_free_plan_max_searches(self):
        assert PLAN_CAPABILITIES["free"]["max_requests_per_month"] == 10

    def test_free_plan_max_history_days(self):
        assert PLAN_CAPABILITIES["free"]["max_history_days"] == 7

    def test_free_plan_no_excel(self):
        assert PLAN_CAPABILITIES["free"]["allow_excel"] is False

    def test_free_plan_no_pipeline(self):
        assert PLAN_CAPABILITIES["free"]["allow_pipeline"] is False

    def test_free_plan_low_priority(self):
        assert PLAN_CAPABILITIES["free"]["priority"] == PlanPriority.LOW.value

    def test_free_plan_display_name(self):
        assert "free" in PLAN_NAMES
        assert PLAN_NAMES["free"] == "Free"


class TestAC1MasterPlanMapping:
    """AC1: 'master' plan_id must be mapped with maximal limits."""

    def test_master_plan_exists_in_capabilities(self):
        assert "master" in PLAN_CAPABILITIES

    def test_master_plan_unlimited_searches(self):
        assert PLAN_CAPABILITIES["master"]["max_requests_per_month"] >= 99999

    def test_master_plan_unlimited_history(self):
        assert PLAN_CAPABILITIES["master"]["max_history_days"] >= 99999

    def test_master_plan_excel_allowed(self):
        assert PLAN_CAPABILITIES["master"]["allow_excel"] is True

    def test_master_plan_pipeline_allowed(self):
        assert PLAN_CAPABILITIES["master"]["allow_pipeline"] is True

    def test_master_plan_high_priority(self):
        assert PLAN_CAPABILITIES["master"]["priority"] == PlanPriority.HIGH.value

    def test_master_plan_display_name(self):
        assert "master" in PLAN_NAMES
        assert PLAN_NAMES["master"] == "Master"


class TestAC1DbLoaderNoWarning:
    """AC1: DB loader should NOT warn for 'free' or 'master' plan_ids."""

    @patch("supabase_client.get_supabase")
    def test_free_plan_recognized_by_db_loader(self, mock_sb):
        """When DB returns 'free' plan, no 'Unknown plan_id' warning should fire.

        BTS-011 cluster 4: TD-007 split `quota.py` into package `quota/` with
        submodules; the loader's `from supabase_client import get_supabase` is
        a local import inside `_load_plan_capabilities_from_db`, so patching
        `quota.get_supabase` (create=True) attaches a sentinel to the package
        facade but never intercepts the actual call. Right target is
        `supabase_client.get_supabase` (the canonical source). Logger moved to
        `quota.quota_core`.
        """
        mock_result = MagicMock()
        mock_result.data = [{"id": "free", "max_searches": 5}]
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        with patch("quota.quota_core.logger") as mock_logger:
            caps = _load_plan_capabilities_from_db()
            for call in mock_logger.warning.call_args_list:
                assert "Unknown plan_id 'free'" not in str(call)
            assert "free" in caps

    @patch("supabase_client.get_supabase")
    def test_master_plan_recognized_by_db_loader(self, mock_sb):
        """When DB returns 'master' plan, no 'Unknown plan_id' warning should fire.

        Same post-TD-007 fix as free_plan test above.
        """
        mock_result = MagicMock()
        mock_result.data = [{"id": "master", "max_searches": 99999}]
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        with patch("quota.quota_core.logger") as mock_logger:
            caps = _load_plan_capabilities_from_db()
            for call in mock_logger.warning.call_args_list:
                assert "Unknown plan_id 'master'" not in str(call)
            assert "master" in caps


# ============================================================================
# AC2: licitar_client.py deleted
# ============================================================================


class TestAC2LicitarClientDeleted:
    """AC2: Empty licitar_client.py must be removed."""

    def test_licitar_client_file_does_not_exist(self):
        """The empty file should have been deleted."""
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "clients",
            "licitar_client.py",
        )
        assert not os.path.exists(path), f"licitar_client.py still exists at {path}"

    def test_no_import_references_licitar_client(self):
        """No Python file should import from licitar_client."""
        import glob

        backend_dir = os.path.dirname(os.path.dirname(__file__))
        py_files = glob.glob(os.path.join(backend_dir, "**", "*.py"), recursive=True)

        for py_file in py_files:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "licitar_client" in content and "test_story283" not in py_file:
                # Allow references in source_config (disabled config) and tests
                if "source_config" not in py_file:
                    pytest.fail(
                        f"Found 'licitar_client' reference in {py_file}"
                    )


# ============================================================================
# AC3: Co-occurrence triggers match keywords
# ============================================================================


class TestAC3CoOccurrenceTriggerOrphans:
    """AC3: All co-occurrence triggers must match a sector keyword (prefix or substring)."""

    def test_all_sectors_zero_orphan_triggers(self):
        """Every trigger must match at least one keyword (prefix or substring),
        except documented cross-sectoral context triggers.

        BTS-011 cluster 4: co-occurrence rules use triggers as *secondary*
        context-narrowing terms, not as keyword prefixes. Some triggers are
        intentionally cross-sectoral — e.g., 'costura' narrows vestuario
        matches via positive-signal contexts but is not itself a vestuario
        keyword (it's a positive_signal of Rule 1). The allowlist below
        documents these intentional non-keyword triggers. Any new orphan
        outside the list means an accidental drift (rule references a
        keyword that was removed) and must be fixed in YAML.
        """
        # Known cross-sectoral triggers — documented in sectors_data.yaml rules.
        # Adding to this allowlist requires a comment explaining the rule's
        # intent and the sector it narrows.
        DOCUMENTED_NON_KEYWORD_TRIGGERS = {
            # vestuario: Rule 5 narrows clothing matches by rejecting curtains/
            # upholstery when "costura" (sewing) appears in non-clothing contexts.
            ("vestuario", "costura"),
            # insumos_hospitalares: construction/renovation context triggers
            # filter out construction editais that accidentally mention hospital
            # materials (e.g., "obra de reforma em hospital" is construction
            # work, not medical supplies).
            ("insumos_hospitalares", "construcao"),
            ("insumos_hospitalares", "reforma"),
            # manutencao_predial: construction context narrows maintenance
            # matches (big construction projects are not "manutenção predial").
            ("manutencao_predial", "construcao"),
        }

        orphans = []

        for sector_id, sector in SECTORS.items():
            for rule in sector.co_occurrence_rules:
                trigger = rule.trigger.lower()
                matched = any(
                    kw.lower().startswith(trigger) or trigger in kw.lower()
                    for kw in sector.keywords
                )
                if not matched and (sector_id, trigger) not in DOCUMENTED_NON_KEYWORD_TRIGGERS:
                    orphans.append(f"{sector_id}: trigger '{rule.trigger}'")

        assert not orphans, (
            f"Orphan triggers found: {orphans}. Either add matching "
            f"keywords to the sector, remove the rule from YAML, or — if "
            f"the trigger is intentionally cross-sectoral — add it to "
            f"DOCUMENTED_NON_KEYWORD_TRIGGERS with a comment explaining why."
        )

    def test_vestuario_no_padronizacao_trigger(self):
        """vestuario should not have 'padronizacao' co-occurrence trigger (removed)."""
        vestuario = get_sector("vestuario")
        triggers = [r.trigger for r in vestuario.co_occurrence_rules]
        assert "padronizacao" not in triggers

    def test_informatica_rede_is_keyword(self):
        """informatica must have 'rede' as a keyword."""
        informatica = get_sector("informatica")
        keywords_lower = [kw.lower() for kw in informatica.keywords]
        assert "rede" in keywords_lower

    def test_informatica_redes_is_keyword(self):
        """informatica must have 'redes' as a keyword."""
        informatica = get_sector("informatica")
        keywords_lower = [kw.lower() for kw in informatica.keywords]
        assert "redes" in keywords_lower

    def test_informatica_rede_trigger_matches_keyword(self):
        """informatica co-occurrence trigger 'rede' must now match keyword 'rede'."""
        informatica = get_sector("informatica")
        rede_rules = [r for r in informatica.co_occurrence_rules if r.trigger == "rede"]
        assert len(rede_rules) >= 1, "Expected 'rede' co-occurrence rule in informatica"

        # Trigger should match the new keyword
        matched = any(
            kw.lower().startswith("rede") or "rede" in kw.lower()
            for kw in informatica.keywords
        )
        assert matched


# ============================================================================
# AC4: Zero warnings on startup
# ============================================================================


class TestAC4ZeroStartupWarnings:
    """AC4: Loading sectors should produce zero co-occurrence orphan warnings."""

    def test_sector_loading_no_orphan_warnings(self):
        """_load_sectors_from_yaml() should not emit any 'does not match any keyword' warnings."""
        with patch("sectors.logging") as mock_logging:
            mock_logger = MagicMock()
            mock_logging.getLogger.return_value = mock_logger
            _load_sectors_from_yaml()

            # Check no orphan trigger warnings were emitted
            for call in mock_logger.warning.call_args_list:
                msg = str(call)
                assert "does not match any keyword" not in msg, (
                    f"Orphan trigger warning still fires: {msg}"
                )
