"""GTM-FIX-024 T6: Parametrized adapter conformance tests.

Verifies that ALL source adapters (both SourceAdapter subclasses and
duck-typed adapters like PNCPLegacyAdapter) implement the required
interface expected by ConsolidationService.
"""

import asyncio
import inspect
from typing import Set

import pytest

from clients.base import SourceAdapter, SourceMetadata, SourceStatus
from clients.portal_compras_client import PortalComprasAdapter
from clients.compras_gov_client import ComprasGovAdapter
from pncp_client import PNCPLegacyAdapter


# ============ Adapter Factory Fixtures ============


def _make_pncp_adapter():
    return PNCPLegacyAdapter(ufs=["SP"])


def _make_portal_adapter():
    return PortalComprasAdapter(timeout=10)


def _make_compras_gov_adapter():
    return ComprasGovAdapter(timeout=10)


ADAPTER_FACTORIES = {
    "PNCPLegacyAdapter": _make_pncp_adapter,
    "PortalComprasAdapter": _make_portal_adapter,
    "ComprasGovAdapter": _make_compras_gov_adapter,
}


@pytest.fixture(params=list(ADAPTER_FACTORIES.keys()))
def adapter(request):
    """Parametrized fixture that yields each adapter instance."""
    factory = ADAPTER_FACTORIES[request.param]
    return factory()


# ============ Contract: Required Properties ============


class TestAdapterContractProperties:
    """Every adapter must have code, name, and metadata properties."""

    def test_has_code_property(self, adapter):
        assert hasattr(adapter, "code"), f"{type(adapter).__name__} missing 'code'"
        code = adapter.code
        assert isinstance(code, str)
        assert len(code) > 0

    def test_has_name_property(self, adapter):
        assert hasattr(adapter, "name"), f"{type(adapter).__name__} missing 'name'"
        name = adapter.name
        assert isinstance(name, str)
        assert len(name) > 0

    def test_has_metadata_property(self, adapter):
        assert hasattr(adapter, "metadata"), f"{type(adapter).__name__} missing 'metadata'"
        meta = adapter.metadata
        assert isinstance(meta, SourceMetadata)
        assert meta.name
        assert meta.code
        assert meta.base_url
        assert meta.priority >= 0

    def test_code_matches_metadata(self, adapter):
        assert adapter.code == adapter.metadata.code

    def test_name_matches_metadata(self, adapter):
        assert adapter.name == adapter.metadata.name


# ============ Contract: Required Methods ============


class TestAdapterContractMethods:
    """Every adapter must have fetch, health_check, close, normalize methods."""

    def test_has_fetch_method(self, adapter):
        assert hasattr(adapter, "fetch"), f"{type(adapter).__name__} missing 'fetch'"
        assert callable(adapter.fetch)

    def test_has_health_check_method(self, adapter):
        assert hasattr(adapter, "health_check"), f"{type(adapter).__name__} missing 'health_check'"
        assert callable(adapter.health_check)

    def test_has_close_method(self, adapter):
        assert hasattr(adapter, "close"), f"{type(adapter).__name__} missing 'close'"
        assert callable(adapter.close)

    def test_has_normalize_method(self, adapter):
        assert hasattr(adapter, "normalize"), f"{type(adapter).__name__} missing 'normalize'"
        assert callable(adapter.normalize)

    def test_fetch_is_async(self, adapter):
        assert asyncio.iscoroutinefunction(adapter.fetch) or inspect.isasyncgenfunction(adapter.fetch)

    def test_health_check_is_async(self, adapter):
        assert asyncio.iscoroutinefunction(adapter.health_check)

    def test_close_is_async(self, adapter):
        assert asyncio.iscoroutinefunction(adapter.close)


# ============ Contract: Truncation Tracking ============


class TestAdapterTruncationTracking:
    """GTM-FIX-004: PNCP and PCP adapters should expose truncation state."""

    @pytest.mark.parametrize("adapter_name", ["PNCPLegacyAdapter", "PortalComprasAdapter"])
    def test_has_was_truncated(self, adapter_name):
        adapter = ADAPTER_FACTORIES[adapter_name]()
        assert hasattr(adapter, "was_truncated")
        assert adapter.was_truncated is False


# ============ ConsolidationService Contract Validation ============


class TestConsolidationContractValidation:
    """GTM-FIX-024 T5: ConsolidationService rejects non-conforming adapters."""

    def test_rejects_adapter_missing_code(self):
        from consolidation import ConsolidationService

        class BadAdapter:
            metadata = SourceMetadata(name="Bad", code="BAD", base_url="http://x")
            async def fetch(self, *a, **kw): yield  # noqa
            async def health_check(self): return SourceStatus.AVAILABLE
            async def close(self): pass

        with pytest.raises(TypeError, match="missing required attributes.*code"):
            ConsolidationService(adapters={"BAD": BadAdapter()})

    def test_rejects_adapter_missing_fetch(self):
        from consolidation import ConsolidationService

        class BadAdapter:
            code = "BAD"
            metadata = SourceMetadata(name="Bad", code="BAD", base_url="http://x")
            async def health_check(self): return SourceStatus.AVAILABLE
            async def close(self): pass

        with pytest.raises(TypeError, match="missing required attributes.*fetch"):
            ConsolidationService(adapters={"BAD": BadAdapter()})

    def test_accepts_conforming_adapters(self):
        from consolidation import ConsolidationService

        adapter = _make_pncp_adapter()
        svc = ConsolidationService(adapters={"PNCP": adapter})
        assert svc is not None

    def test_accepts_all_real_adapters(self):
        from consolidation import ConsolidationService

        adapters = {name: factory() for name, factory in ADAPTER_FACTORIES.items()}
        svc = ConsolidationService(adapters=adapters)
        assert svc is not None

    def test_rejects_bad_fallback_adapter(self):
        from consolidation import ConsolidationService

        adapter = _make_pncp_adapter()

        class BadFallback:
            pass

        with pytest.raises(TypeError, match="Fallback adapter"):
            ConsolidationService(
                adapters={"PNCP": adapter},
                fallback_adapter=BadFallback(),
            )
