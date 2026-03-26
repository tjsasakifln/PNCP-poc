"""Tests for partial accumulation on modality timeout.

Validates that when _fetch_single_modality is interrupted by asyncio.wait_for
timeout, items accumulated before the cancellation point are preserved and
returned instead of being discarded.
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from pncp_client import AsyncPNCPClient, ModalityFetchState, _circuit_breaker


@pytest.fixture(autouse=True)
def _reset_circuit_breaker():
    """Reset circuit breaker state before and after each test."""
    _circuit_breaker.consecutive_failures = 0
    _circuit_breaker.degraded_until = None
    yield
    _circuit_breaker.consecutive_failures = 0
    _circuit_breaker.degraded_until = None


class TestModalityFetchState:
    """Unit tests for the ModalityFetchState dataclass."""

    def test_default_state(self):
        state = ModalityFetchState()
        assert state.items == []
        assert state.seen_ids == set()
        assert state.pages_fetched == 0
        assert state.was_truncated is False
        assert state.timed_out is False

    def test_state_mutation(self):
        state = ModalityFetchState()
        state.items.append({"id": "1"})
        state.seen_ids.add("1")
        state.pages_fetched = 3
        state.was_truncated = True
        state.timed_out = True
        assert len(state.items) == 1
        assert "1" in state.seen_ids
        assert state.pages_fetched == 3

    def test_state_isolation(self):
        """Two state instances do not share mutable fields."""
        s1 = ModalityFetchState()
        s2 = ModalityFetchState()
        s1.items.append({"id": "a"})
        s1.seen_ids.add("a")
        assert len(s2.items) == 0
        assert len(s2.seen_ids) == 0


class TestPartialAccumulation:
    """Core partial accumulation tests."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_timeout_returns_partial_items_not_empty(self):
        """When modality times out after fetching N pages, return those N pages
        instead of []. This is THE critical test."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            call_count = 0

            async def mock_fetch_page(**kwargs):
                nonlocal call_count
                call_count += 1
                pg = kwargs.get("pagina", 1)
                if pg <= 3:
                    return {
                        "data": [{"numeroControlePNCP": f"item-{pg}", "uf": "SP",
                                  "objetoCompra": f"Test item {pg}"}],
                        "paginasRestantes": 100 - pg,
                        "totalRegistros": 5000,
                    }
                # Page 4+: slow, causes timeout
                await asyncio.sleep(100)
                return {"data": [], "paginasRestantes": 0, "totalRegistros": 0}

            client._fetch_page_async = mock_fetch_page

            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 1.0):
                with patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                    items, was_truncated = await client._fetch_modality_with_timeout(
                        uf="SP",
                        data_inicial="2026-01-01",
                        data_final="2026-01-15",
                        modalidade=6,
                    )

            # CRITICAL: items are NOT empty — partial accumulation works
            assert len(items) >= 2, f"Expected partial items, got {len(items)}"
            assert was_truncated is True
            # Verify items are from early pages
            item_ids = {item.get("numeroControlePNCP", "") for item in items}
            assert "item-1" in item_ids

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_timeout_with_zero_items_still_retries(self):
        """When timeout fires before any page completes, retry is attempted."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            attempt_count = 0

            async def mock_fetch_page(**kwargs):
                nonlocal attempt_count
                attempt_count += 1
                # Always slow — no pages complete before timeout
                await asyncio.sleep(100)
                return {"data": [], "paginasRestantes": 0}

            client._fetch_page_async = mock_fetch_page

            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.05):
                with patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                    items, was_truncated = await client._fetch_modality_with_timeout(
                        uf="SP",
                        data_inicial="2026-01-01",
                        data_final="2026-01-15",
                        modalidade=6,
                    )

            # 0 items: should have retried (2 total attempts)
            assert len(items) == 0
            assert was_truncated is False
            assert attempt_count >= 2, "Should retry when 0 items on first timeout"

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_partial_items_skip_retry(self):
        """When timeout fires WITH partial items, do NOT retry — return immediately."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            fetch_calls = 0

            async def mock_fetch_page(**kwargs):
                nonlocal fetch_calls
                fetch_calls += 1
                pg = kwargs.get("pagina", 1)
                if pg == 1:
                    return {
                        "data": [{"numeroControlePNCP": "partial-1", "uf": "SP"}],
                        "paginasRestantes": 50,
                        "totalRegistros": 2500,
                    }
                # Page 2+: slow
                await asyncio.sleep(100)
                return {"data": [], "paginasRestantes": 0}

            client._fetch_page_async = mock_fetch_page

            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.5):
                with patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                    items, was_truncated = await client._fetch_modality_with_timeout(
                        uf="SP",
                        data_inicial="2026-01-01",
                        data_final="2026-01-15",
                        modalidade=6,
                    )

            assert len(items) >= 1
            assert was_truncated is True
            # Page 1 succeeded on first attempt + page 2 started (then timeout)
            # Should NOT have made a second attempt at page 1
            assert fetch_calls <= 3, "Should not retry when partial items exist"

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_successful_fetch_unchanged(self):
        """Normal successful fetch behavior is not affected by the change."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_page(**kwargs):
                return {
                    "data": [{"numeroControlePNCP": f"ok-{kwargs.get('pagina', 1)}", "uf": "SP"}],
                    "paginasRestantes": 0,
                    "totalRegistros": 1,
                }

            client._fetch_page_async = mock_fetch_page

            items, was_truncated = await client._fetch_modality_with_timeout(
                uf="SP",
                data_inicial="2026-01-01",
                data_final="2026-01-15",
                modalidade=6,
            )

            assert len(items) == 1
            assert was_truncated is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_single_modality_backward_compatible(self):
        """_fetch_single_modality works without state parameter (backward compat)."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_page(**kwargs):
                return {
                    "data": [{"numeroControlePNCP": "compat-1", "uf": "RJ"}],
                    "paginasRestantes": 0,
                    "totalRegistros": 1,
                }

            client._fetch_page_async = mock_fetch_page

            # Call WITHOUT state parameter — should work identically to before
            items, was_truncated = await client._fetch_single_modality(
                uf="RJ",
                data_inicial="2026-01-01",
                data_final="2026-01-15",
                modalidade=5,
            )

            assert len(items) == 1
            assert items[0].get("numeroControlePNCP") == "compat-1"
            assert was_truncated is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_single_modality_with_shared_state(self):
        """_fetch_single_modality writes to shared state when provided."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_page(**kwargs):
                pg = kwargs.get("pagina", 1)
                return {
                    "data": [{"numeroControlePNCP": f"shared-{pg}", "uf": "MG"}],
                    "paginasRestantes": max(0, 3 - pg),
                    "totalRegistros": 3,
                }

            client._fetch_page_async = mock_fetch_page

            state = ModalityFetchState()
            items, was_truncated = await client._fetch_single_modality(
                uf="MG",
                data_inicial="2026-01-01",
                data_final="2026-01-15",
                modalidade=4,
                state=state,
            )

            # Items should be in both the return value AND the shared state
            assert len(items) == 3
            assert len(state.items) == 3
            assert state.pages_fetched == 3
            assert items is state.items  # same reference


class TestPartialAccumulationIntegration:
    """Integration: partial accumulation through _fetch_uf_all_pages."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_one_modality_partial_others_complete(self):
        """Mod 6 times out with partial, mods 4,5 complete normally.
        Validates correct merge of partial + complete results."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_page(**kwargs):
                mod = kwargs.get("modalidade", 0)
                pg = kwargs.get("pagina", 1)

                if mod == 6 and pg >= 3:
                    # Mod 6 page 3+: slow → triggers timeout
                    await asyncio.sleep(100)
                    return {"data": [], "paginasRestantes": 0}

                return {
                    "data": [{"numeroControlePNCP": f"SP-{mod}-p{pg}", "uf": "SP"}],
                    "paginasRestantes": max(0, 2 - pg) if mod != 6 else 50,
                    "totalRegistros": 100 if mod == 6 else 3,
                }

            client._fetch_page_async = mock_fetch_page

            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.5):
                with patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                    items, was_truncated = await client._fetch_uf_all_pages(
                        uf="SP",
                        data_inicial="2026-01-01",
                        data_final="2026-01-15",
                        modalidades=[4, 5, 6],
                    )

            # Mod 4: 3 items (p1+p2+p3, complete)
            # Mod 5: 3 items (p1+p2+p3, complete)
            # Mod 6: 2 items (p1+p2 partial, p3 timed out)
            assert len(items) >= 6, f"Expected >=6 items (2 complete + partial), got {len(items)}"
            assert was_truncated is True

            # Verify items from all modalities are present
            item_ids = {item.get("codigoCompra", item.get("numeroControlePNCP", "")) for item in items}
            assert "SP-4-p1" in item_ids, "Mod 4 items should be present"
            assert "SP-5-p1" in item_ids, "Mod 5 items should be present"
            assert "SP-6-p1" in item_ids, "Mod 6 partial items should be present"
