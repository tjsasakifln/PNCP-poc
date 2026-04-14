"""STORY-2.12 (TD-DB-015) AC4:
validate the transformer + loader defensive fallback for NULL data_*.

Design:
  The transformer fills data_publicacao with (now UTC - 1 day) when the
  PNCP payload returns NULL/empty dataPublicacaoPncp, and falls back to
  that same value for data_abertura when dataAberturaProposta is also
  missing. data_encerramento is left NULL (intentional — marks 'open
  indefinitely' for p_modo='abertas').

  The loader re-asserts the same invariant in case a caller bypassed the
  transformer (defence in depth).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ingestion.transformer import transform_pncp_item
from ingestion.loader import _apply_date_fallbacks


def _base_raw(pncp_id: str = "X-0001") -> dict:
    return {
        "numeroControlePNCP": pncp_id,
        "objetoCompra": "teste",
        "valorTotalEstimado": 100,
        "situacaoCompraNome": "Aberta",
    }


class TestTransformerFallback:
    def test_null_dataPublicacaoPncp_gets_fallback(self):
        raw = _base_raw()
        # dataPublicacaoPncp absent -> fallback kicks in
        result = transform_pncp_item(raw, source="pncp")
        assert result["data_publicacao"] is not None
        # Fallback must be an ISO datetime string roughly 1 day old
        fallback = datetime.fromisoformat(result["data_publicacao"])
        age = datetime.now(timezone.utc) - fallback
        assert timedelta(hours=12) < age < timedelta(hours=48), (
            f"fallback timestamp {fallback} not ~1 day old (age={age})"
        )

    def test_empty_string_dataPublicacaoPncp_gets_fallback(self):
        raw = _base_raw() | {"dataPublicacaoPncp": ""}
        result = transform_pncp_item(raw, source="pncp")
        assert result["data_publicacao"], "empty string must be replaced"

    def test_valid_date_preserved(self):
        raw = _base_raw() | {"dataPublicacaoPncp": "2026-03-01T10:00:00+00:00"}
        result = transform_pncp_item(raw, source="pncp")
        assert result["data_publicacao"] == "2026-03-01T10:00:00+00:00"

    def test_data_abertura_defaults_to_data_publicacao(self):
        raw = _base_raw() | {"dataPublicacaoPncp": "2026-03-01T10:00:00+00:00"}
        # dataAberturaProposta absent -> uses data_publicacao
        result = transform_pncp_item(raw, source="pncp")
        assert result["data_abertura"] == result["data_publicacao"]

    def test_data_abertura_preserved_when_present(self):
        raw = _base_raw() | {
            "dataPublicacaoPncp": "2026-03-01T10:00:00+00:00",
            "dataAberturaProposta": "2026-03-05T12:00:00+00:00",
        }
        result = transform_pncp_item(raw, source="pncp")
        assert result["data_abertura"] == "2026-03-05T12:00:00+00:00"

    def test_data_encerramento_stays_null_on_missing(self):
        """Intentional — NULL means 'open indefinitely' for p_modo='abertas'."""
        raw = _base_raw()
        result = transform_pncp_item(raw, source="pncp")
        assert result["data_encerramento"] is None


class TestLoaderFallback:
    def test_apply_date_fallbacks_fills_nulls(self):
        records = [
            {"pncp_id": "1", "data_publicacao": None, "data_abertura": None},
            {"pncp_id": "2", "data_publicacao": "", "data_abertura": "2026-01-01"},
        ]
        out = _apply_date_fallbacks(records)
        # Both are patched (None and "" both falsy)
        assert out[0]["data_publicacao"] is not None
        assert out[0]["data_abertura"] == out[0]["data_publicacao"]
        assert out[1]["data_publicacao"] != ""
        # Existing data_abertura preserved
        assert out[1]["data_abertura"] == "2026-01-01"

    def test_apply_date_fallbacks_preserves_nonnull_values(self):
        records = [
            {
                "pncp_id": "1",
                "data_publicacao": "2026-03-01T10:00:00+00:00",
                "data_abertura": "2026-03-02T10:00:00+00:00",
            }
        ]
        out = _apply_date_fallbacks(records)
        assert out[0]["data_publicacao"] == "2026-03-01T10:00:00+00:00"
        assert out[0]["data_abertura"] == "2026-03-02T10:00:00+00:00"
