"""STORY-2.11 (EPIC-TD-2026Q2 P0): Tests for budget-exceeded rejection in llm_arbiter.

Covers:
- classify_contract_primary_match retorna PENDING_REVIEW sem chamar OpenAI
  quando ``is_budget_exceeded_sync()`` retorna True
- Metric ``LLM_BUDGET_REJECTIONS`` é incrementado
- Budget NOT exceeded → fluxo normal (OpenAI é chamado)
- Admin endpoint GET /v1/admin/llm-cost retorna snapshot
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Arbiter reject path
# ---------------------------------------------------------------------------


def test_arbiter_rejects_when_budget_exceeded(monkeypatch):
    """Com budget flag=True, classify retorna PENDING_REVIEW sem OpenAI call."""
    monkeypatch.setenv("LLM_ARBITER_ENABLED", "true")

    # Importa depois de setar env
    from llm_arbiter.classification import classify_contract_primary_match
    import llm_arbiter as _lm

    # Force LLM_ENABLED True via facade
    monkeypatch.setattr(_lm, "LLM_ENABLED", True, raising=False)

    # Clear cache para garantir que não bate em cache
    from llm_arbiter.classification import _arbiter_cache
    _arbiter_cache.clear()

    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(
        side_effect=AssertionError("OpenAI NÃO deveria ser chamada com budget exceeded")
    )

    with patch(
        "llm_budget.is_budget_exceeded_sync", return_value=True
    ), patch("llm_arbiter._get_client", return_value=mock_client), patch(
        "llm_arbiter.classification._arbiter_cache_get_redis", return_value=None
    ):
        result = classify_contract_primary_match(
            objeto="Obra de engenharia civil",
            valor=150000.0,
            setor_name="engenharia_civil",
            prompt_level="standard",
            setor_id="engenharia_civil",
            search_id="test-budget-1",
        )

    assert result["is_primary"] is False
    assert result["confidence"] == 0
    assert result["rejection_reason"] == "llm_budget_exceeded"
    assert result.get("pending_review") is True
    assert result.get("_classification_source") == "budget_cap"
    # Garante que OpenAI não foi invocada
    mock_client.chat.completions.create.assert_not_called()


def test_arbiter_rejects_increments_rejection_metric(monkeypatch):
    monkeypatch.setenv("LLM_ARBITER_ENABLED", "true")

    from llm_arbiter.classification import classify_contract_primary_match, _arbiter_cache
    import llm_arbiter as _lm

    monkeypatch.setattr(_lm, "LLM_ENABLED", True, raising=False)
    _arbiter_cache.clear()

    mock_counter = MagicMock()
    mock_labels = MagicMock()
    mock_counter.labels.return_value = mock_labels

    with patch("llm_budget.is_budget_exceeded_sync", return_value=True), patch(
        "metrics.LLM_BUDGET_REJECTIONS", mock_counter
    ), patch(
        "llm_arbiter.classification._arbiter_cache_get_redis", return_value=None
    ):
        classify_contract_primary_match(
            objeto="obra nova",
            valor=10000.0,
            setor_name="engenharia_civil",
            prompt_level="standard",
            setor_id="engenharia_civil",
            search_id="test-budget-metric",
        )

    mock_counter.labels.assert_called_with(caller="arbiter")
    mock_labels.inc.assert_called_once()


def test_arbiter_proceeds_when_budget_not_exceeded(monkeypatch):
    """Budget OK → fluxo normal, OpenAI é chamada."""
    monkeypatch.setenv("LLM_ARBITER_ENABLED", "true")

    from llm_arbiter.classification import classify_contract_primary_match, _arbiter_cache
    import llm_arbiter as _lm

    monkeypatch.setattr(_lm, "LLM_ENABLED", True, raising=False)
    _arbiter_cache.clear()

    # Mock OpenAI retornando SIM estruturado
    fake_response = MagicMock()
    fake_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"classe": "SIM", "confianca": 90, "evidencias": ["obra"], "motivo_exclusao": null, "precisa_mais_dados": false}'
            )
        )
    ]
    fake_response.usage = MagicMock(prompt_tokens=50, completion_tokens=20)

    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(return_value=fake_response)

    with patch("llm_budget.is_budget_exceeded_sync", return_value=False), patch(
        "llm_arbiter._get_client", return_value=mock_client
    ), patch(
        "llm_arbiter.classification._arbiter_cache_get_redis", return_value=None
    ), patch(
        "llm_arbiter.classification._arbiter_cache_set_redis"
    ):
        result = classify_contract_primary_match(
            objeto="obra de engenharia civil",
            valor=50000.0,
            setor_name="engenharia_civil",
            prompt_level="standard",
            setor_id="engenharia_civil",
            search_id="test-ok",
        )

    # OpenAI chamada com sucesso
    mock_client.chat.completions.create.assert_called_once()
    assert result["is_primary"] is True


# ---------------------------------------------------------------------------
# Admin endpoint GET /v1/admin/llm-cost
# ---------------------------------------------------------------------------


def test_admin_llm_cost_endpoint_returns_snapshot(monkeypatch):
    from main import app
    from admin import require_admin
    from auth import require_auth

    admin_user = {
        "id": "admin-001",
        "email": "admin@smartlic.tech",
        "role": "admin",
    }
    app.dependency_overrides[require_auth] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user

    fake_snap = {
        "month_to_date_usd": 12.34,
        "budget_usd": 100.0,
        "pct_used": 12.34,
        "projected_end_of_month_usd": 50.0,
        "month": "llm_cost_month_2026_04",
        "exceeded": False,
    }

    try:
        with patch(
            "routes.admin_llm_cost.get_cost_snapshot",
            AsyncMock(return_value=fake_snap),
        ):
            client = TestClient(app)
            r = client.get("/v1/admin/llm-cost")

        assert r.status_code == 200
        data = r.json()
        assert data["month_to_date_usd"] == 12.34
        assert data["budget_usd"] == 100.0
        assert data["exceeded"] is False
        assert "month" in data
    finally:
        app.dependency_overrides.pop(require_auth, None)
        app.dependency_overrides.pop(require_admin, None)


def test_admin_llm_cost_endpoint_requires_admin():
    from main import app
    from admin import require_admin
    from auth import require_auth

    # Sem overrides — deve bloquear
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)

    client = TestClient(app)
    r = client.get("/v1/admin/llm-cost")
    # Esperamos 401 ou 403 (sem auth)
    assert r.status_code in (401, 403)
