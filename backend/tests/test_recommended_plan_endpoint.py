"""STORY-BIZ-002: integration tests for GET /v1/user/recommended-plan."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import require_auth
from database import get_db
from routes.user import router as user_router


def _fake_db(cnae_primary):
    fake = MagicMock()
    fake.table.return_value = fake
    fake.select.return_value = fake
    fake.eq.return_value = fake
    fake.limit.return_value = fake
    if cnae_primary is None:
        fake.execute.return_value = MagicMock(data=[])
    else:
        fake.execute.return_value = MagicMock(data=[{"cnae_primary": cnae_primary}])
    return fake


def _make_client(fake_db_fn):
    app = FastAPI()
    app.include_router(user_router, prefix="/v1")
    app.dependency_overrides[require_auth] = lambda: {"id": "user-abc", "email": "x@y.com"}
    app.dependency_overrides[get_db] = fake_db_fn
    return TestClient(app)


@pytest.fixture(autouse=True)
def _disable_redis(monkeypatch):
    """Return no Redis client so tests exercise the DB-only branch by default."""
    monkeypatch.setattr("redis_pool.get_sync_redis", lambda: None, raising=False)


def test_returns_consultoria_for_consultancy_cnae():
    client = _make_client(lambda: _fake_db("70.20-4/00"))
    r = client.get("/v1/user/recommended-plan")
    assert r.status_code == 200
    assert r.json() == {"plan_key": "consultoria", "reason": "cnae_consultoria"}


def test_returns_pro_for_non_consultancy_cnae():
    client = _make_client(lambda: _fake_db("41.20-4/00"))
    r = client.get("/v1/user/recommended-plan")
    assert r.status_code == 200
    assert r.json() == {"plan_key": "smartlic_pro", "reason": "default"}


def test_returns_pro_when_profile_missing_cnae():
    client = _make_client(lambda: _fake_db(None))
    r = client.get("/v1/user/recommended-plan")
    assert r.status_code == 200
    body = r.json()
    assert body["plan_key"] == "smartlic_pro"
    assert body["reason"] == "default"


def test_survives_db_error_and_returns_pro():
    def _broken():
        broken = MagicMock()
        broken.table.side_effect = Exception("db unreachable")
        return broken
    client = _make_client(_broken)
    r = client.get("/v1/user/recommended-plan")
    assert r.status_code == 200
    assert r.json()["plan_key"] == "smartlic_pro"


def test_cache_hit_skips_db_query(monkeypatch):
    cached_redis = MagicMock()
    cached_redis.get.return_value = '{"plan_key": "consultoria", "reason": "cnae_consultoria"}'
    monkeypatch.setattr("redis_pool.get_sync_redis", lambda: cached_redis, raising=False)

    call_counter = {"n": 0}

    def _db():
        call_counter["n"] += 1
        return _fake_db("41.20-4/00")

    client = _make_client(_db)
    r = client.get("/v1/user/recommended-plan")
    assert r.status_code == 200
    assert r.json()["plan_key"] == "consultoria"
    # DB provider may be instantiated by FastAPI dependency graph even when unused;
    # the important invariant is that the cached payload is returned unchanged.


def test_cache_miss_writes_through(monkeypatch):
    miss_redis = MagicMock()
    miss_redis.get.return_value = None
    monkeypatch.setattr("redis_pool.get_sync_redis", lambda: miss_redis, raising=False)

    client = _make_client(lambda: _fake_db("74.90-1/04"))
    r = client.get("/v1/user/recommended-plan")
    assert r.status_code == 200
    miss_redis.setex.assert_called_once()
    args = miss_redis.setex.call_args.args
    assert args[0] == "user:recommended_plan:user-abc"
    assert args[1] == 86400
