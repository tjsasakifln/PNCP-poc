"""#2111 onda 1 — freeze of new SaaS commerce journeys.

Production default: SAAS_COMMERCE_ENABLED=false → 410 Gone.
These tests are marked saas_freeze so conftest does NOT re-enable commerce.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from saas_commerce import (
    FROZEN_DETAIL,
    SAAS_COMMERCE_FROZEN_CODE,
    is_saas_commerce_enabled,
    require_saas_commerce,
)

pytestmark = pytest.mark.saas_freeze


def test_flag_defaults_off_under_freeze_marker():
    assert is_saas_commerce_enabled() is False


def test_require_saas_commerce_raises_410():
    with pytest.raises(HTTPException) as exc:
        require_saas_commerce()
    assert exc.value.status_code == 410
    assert exc.value.detail["error_code"] == SAAS_COMMERCE_FROZEN_CODE
    assert exc.value.detail["next"] == "/consultoria-b2g"
    assert "CONFENGE" in exc.value.detail["message"]


def test_require_saas_commerce_allows_when_enabled(monkeypatch):
    from config import features as feat

    monkeypatch.setenv("SAAS_COMMERCE_ENABLED", "true")
    feat._feature_flag_cache.clear()
    feat._runtime_overrides.clear()
    assert is_saas_commerce_enabled() is True
    require_saas_commerce()  # does not raise


def _checkout_client() -> TestClient:
    from auth import require_auth
    from routes.checkout import checkout_rate_limit, router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: {
        "id": "user-freeze",
        "email": "freeze@example.com",
        "role": "authenticated",
    }
    app.dependency_overrides[checkout_rate_limit] = lambda: None
    return TestClient(app)


def test_one_time_checkout_returns_410():
    client = _checkout_client()
    res = client.post("/api/checkout/one-time", json={"sku": "relatorio-oportunidade"})
    assert res.status_code == 410
    body = res.json()["detail"]
    assert body["error_code"] == SAAS_COMMERCE_FROZEN_CODE
    assert body == FROZEN_DETAIL


def test_api_subscription_checkout_returns_410():
    client = _checkout_client()
    res = client.post(
        "/api/checkout/api-subscription",
        json={"tier": "starter"},
    )
    assert res.status_code == 410


def test_plan_checkout_returns_410():
    from auth import require_auth
    from database import get_db
    from routes.billing import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: {"id": "u", "email": "a@b.c"}
    app.dependency_overrides[get_db] = lambda: None
    client = TestClient(app)
    res = client.post("/checkout?plan_id=pro")
    assert res.status_code == 410


def test_signup_shaped_route_returns_410():
    """Signup/trial uses the same dependency; isolate it from rate-limit factories."""
    app = FastAPI()

    @app.post("/auth/signup")
    def _signup(_frozen=None):
        require_saas_commerce()
        return {"ok": True}

    res = TestClient(app).post("/auth/signup")
    assert res.status_code == 410
    assert res.json()["detail"]["error_code"] == SAAS_COMMERCE_FROZEN_CODE


def test_flag_registered_default_false():
    from config.features import _FEATURE_FLAG_REGISTRY

    env_var, default = _FEATURE_FLAG_REGISTRY["SAAS_COMMERCE_ENABLED"]
    assert env_var == "SAAS_COMMERCE_ENABLED"
    assert default == "false"
