"""Tests for the referral program (SEO-PLAYBOOK Frente 2).

Covers:
- GET  /v1/referral/code   — code generation / idempotent reuse
- GET  /v1/referral/stats  — aggregate statistics
- POST /v1/referral/redeem — signup redemption flow
"""

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from main import app
from auth import require_auth


USER_ID = "user-ref-1"
OTHER_USER_ID = "user-ref-2"


def _override_auth(user_id: str = USER_ID):
    async def _dep():
        return {"id": user_id, "email": f"{user_id}@example.com"}
    return _dep


@pytest.fixture
def auth_as_user():
    app.dependency_overrides[require_auth] = _override_auth(USER_ID)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def auth_as_other():
    app.dependency_overrides[require_auth] = _override_auth(OTHER_USER_ID)
    yield
    app.dependency_overrides.clear()


class _FakeTable:
    """Tiny fluent fake for supabase table queries used by routes/referral.py."""

    def __init__(self, store):
        self._store = store
        self._filters = []
        self._order = None
        self._limit = None
        self._op = None  # ("select", cols) | ("insert", row) | ("update", row)
        self._row = None

    # Chain methods
    def select(self, *_args, **_kwargs):
        self._op = ("select", None)
        return self

    def insert(self, row):
        self._op = ("insert", row)
        return self

    def update(self, row):
        self._op = ("update", row)
        return self

    def eq(self, col, val):
        self._filters.append((col, val))
        return self

    def is_(self, col, val):
        # treat "null" literal same as None
        self._filters.append((col, None if val == "null" else val))
        return self

    def order(self, *_a, **_kw):
        return self

    def limit(self, n):
        self._limit = n
        return self

    def execute(self):
        if self._op[0] == "insert":
            row = dict(self._op[1])
            row.setdefault("id", f"row-{len(self._store) + 1}")
            row.setdefault("status", "pending")
            row.setdefault("referred_user_id", None)
            self._store.append(row)
            return MagicMock(data=[row])

        if self._op[0] == "select":
            rows = self._store
            for col, val in self._filters:
                rows = [r for r in rows if r.get(col) == val]
            if self._limit:
                rows = rows[: self._limit]
            return MagicMock(data=list(rows), count=len(rows))

        if self._op[0] == "update":
            updates = self._op[1]
            rows = self._store
            matched = []
            for col, val in self._filters:
                rows = [r for r in rows if r.get(col) == val]
            for r in rows:
                r.update(updates)
                matched.append(r)
            return MagicMock(data=matched)

        return MagicMock(data=[])


class FakeSupabase:
    def __init__(self):
        self.referrals = []

    def table(self, name):
        assert name == "referrals", f"unexpected table {name}"
        return _FakeTable(self.referrals)


@pytest.fixture
def fake_sb():
    sb = FakeSupabase()
    with patch("supabase_client.get_supabase", return_value=sb), \
         patch("routes.referral._maybe_send_welcome_email"):
        yield sb


@pytest.mark.asyncio
async def test_get_code_creates_new_code_on_first_call(auth_as_user, fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/v1/referral/code")
    assert r.status_code == 200
    data = r.json()
    assert len(data["code"]) == 8
    assert data["code"].isalnum() and data["code"].upper() == data["code"]
    assert data["share_url"].endswith(f"?ref={data['code']}")
    assert len(fake_sb.referrals) == 1
    assert fake_sb.referrals[0]["referrer_user_id"] == USER_ID


@pytest.mark.asyncio
async def test_get_code_is_idempotent(auth_as_user, fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/v1/referral/code")
        r2 = await client.get("/v1/referral/code")
    assert r1.json()["code"] == r2.json()["code"]
    assert len(fake_sb.referrals) == 1


@pytest.mark.asyncio
async def test_stats_returns_zero_counts_for_new_user(auth_as_user, fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/v1/referral/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_signups"] == 0
    assert data["total_converted"] == 0
    assert data["credits_earned_months"] == 0
    assert len(data["code"]) == 8


@pytest.mark.asyncio
async def test_stats_counts_by_status(auth_as_user, fake_sb):
    # Seed a code for the user
    fake_sb.referrals.extend(
        [
            {
                "id": "r1",
                "referrer_user_id": USER_ID,
                "referred_user_id": None,
                "code": "AAAA1111",
                "status": "pending",
            },
            {
                "id": "r2",
                "referrer_user_id": USER_ID,
                "referred_user_id": "u-x",
                "code": "BBBB2222",
                "status": "signed_up",
            },
            {
                "id": "r3",
                "referrer_user_id": USER_ID,
                "referred_user_id": "u-y",
                "code": "CCCC3333",
                "status": "converted",
            },
            {
                "id": "r4",
                "referrer_user_id": USER_ID,
                "referred_user_id": "u-z",
                "code": "DDDD4444",
                "status": "credited",
            },
        ]
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/v1/referral/stats")
    data = r.json()
    assert data["total_signups"] == 3  # signed_up + converted + credited
    assert data["total_converted"] == 2  # converted + credited
    assert data["credits_earned_months"] == 1


@pytest.mark.asyncio
async def test_redeem_marks_row_signed_up(auth_as_other, fake_sb):
    # Referrer owns the code; the "other" user will redeem it
    fake_sb.referrals.append(
        {
            "id": "r1",
            "referrer_user_id": USER_ID,
            "referred_user_id": None,
            "code": "ZZZZ9999",
            "status": "pending",
        }
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/referral/redeem",
            json={"code": "ZZZZ9999", "referred_user_id": OTHER_USER_ID},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "signed_up"
    row = fake_sb.referrals[0]
    assert row["status"] == "signed_up"
    assert row["referred_user_id"] == OTHER_USER_ID


@pytest.mark.asyncio
async def test_redeem_unknown_code_is_ignored(auth_as_other, fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/referral/redeem",
            json={"code": "NOPE0000", "referred_user_id": OTHER_USER_ID},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


@pytest.mark.asyncio
async def test_redeem_rejects_identity_mismatch(auth_as_user, fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/referral/redeem",
            json={"code": "ZZZZ9999", "referred_user_id": "someone-else"},
        )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_redeem_self_referral_ignored(auth_as_user, fake_sb):
    fake_sb.referrals.append(
        {
            "id": "r1",
            "referrer_user_id": USER_ID,
            "referred_user_id": None,
            "code": "SELF0000",
            "status": "pending",
        }
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/referral/redeem",
            json={"code": "SELF0000", "referred_user_id": USER_ID},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"
    assert fake_sb.referrals[0]["status"] == "pending"
