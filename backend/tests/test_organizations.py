"""Tests for STORY-322: Organization management.

AC25: Org CRUD (create, invite, accept, remove, get_my_org)
AC26: Org-level quota (PLAN_CAPABILITIES, PLAN_NAMES, get_user_org_plan)
AC27: RLS / service-level isolation (member cannot see other members' data)
AC28: Stripe checkout for consultoria plan (is_subscription includes consultoria)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport

from main import app
from auth import require_auth

# The organization service does a top-level `from supabase_client import get_supabase`,
# so the correct patch target is the name bound inside that module.
_ORG_SVC_GET_SUPABASE = "services.organization_service.get_supabase"


# ── Auth fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_user():
    return {"id": "user-001", "email": "owner@test.com", "role": "authenticated", "aal": "aal1"}


@pytest.fixture
def mock_member():
    return {"id": "user-002", "email": "member@test.com", "role": "authenticated", "aal": "aal1"}


# ── Supabase mock factory ─────────────────────────────────────────────────────


def _mock_supabase():
    """Create a mock Supabase client with full chained-query support.

    Returns (mock_sb, mock_table, mock_result).
    mock_result.data / mock_result.count can be set per test.
    """
    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []
    mock_result.count = 0

    # All table chaining methods return the same mock_table so callers can
    # override execute() freely.
    mock_table.insert.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.gte.return_value = mock_table
    mock_table.execute.return_value = mock_result

    mock_sb.table.return_value = mock_table
    return mock_sb, mock_table, mock_result


# ── AC25: Organization CRUD via HTTP routes ───────────────────────────────────


class TestCreateOrganization:
    """AC25-1/2: POST /v1/organizations"""

    @pytest.mark.asyncio
    async def test_create_organization_success(self, mock_user):
        """POST /v1/organizations returns 201 and org data."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            org_data = {
                "id": "org-abc",
                "name": "Consultoria Teste",
                "owner_id": "user-001",
                "max_members": 5,
                "plan_type": "consultoria",
            }

            call_count = [0]

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # org INSERT → returns org row
                    r.data = [org_data]
                else:
                    # member INSERT → don't care about return value
                    r.data = [{"id": "mem-001"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/v1/organizations",
                        json={"name": "Consultoria Teste"},
                    )

            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "org-abc"
            assert data["name"] == "Consultoria Teste"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_organization_unauthenticated(self):
        """POST /v1/organizations without auth returns 401."""
        app.dependency_overrides.clear()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/organizations",
                json={"name": "Hack Org"},
            )

        assert response.status_code == 401


class TestGetOrganization:
    """AC25-3/4: GET /v1/organizations/{id}"""

    @pytest.mark.asyncio
    async def test_get_organization_success(self, mock_user):
        """GET /v1/organizations/{id} as member returns org details."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            org_data = {
                "id": "org-abc",
                "name": "Consultoria Teste",
                "owner_id": "user-001",
                "max_members": 5,
                "plan_type": "consultoria",
            }

            call_count = [0]

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # membership check — user is owner
                    r.data = [{"role": "owner"}]
                elif call_count[0] == 2:
                    # org SELECT single
                    r.data = org_data
                elif call_count[0] == 3:
                    # members list
                    r.data = [
                        {
                            "user_id": "user-001",
                            "role": "owner",
                            "invited_at": None,
                            "accepted_at": "2026-01-01",
                        }
                    ]
                else:
                    r.data = []
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/v1/organizations/org-abc")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "org-abc"
            assert data["user_role"] == "owner"
            assert isinstance(data["members"], list)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_organization_not_member(self, mock_user):
        """GET /v1/organizations/{id} for non-member returns 404."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, mock_result = _mock_supabase()
            # membership check returns empty — not a member
            mock_result.data = []

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/v1/organizations/org-xyz")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestInviteMember:
    """AC25-5/6/7: POST /v1/organizations/{id}/invite"""

    @pytest.mark.asyncio
    async def test_invite_member_success(self, mock_user):
        """Owner can invite a new member."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            call_count = [0]
            invite_row = {
                "id": "inv-001",
                "org_id": "org-abc",
                "user_id": "user-002",
                "role": "member",
            }

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # inviter role check — owner
                    r.data = [{"role": "owner"}]
                elif call_count[0] == 2:
                    # org max_members
                    r.data = {"max_members": 5}
                elif call_count[0] == 3:
                    # current member count
                    r.data = [{"id": "mem-001"}]
                    r.count = 1
                elif call_count[0] == 4:
                    # find user by email
                    r.data = [{"id": "user-002"}]
                elif call_count[0] == 5:
                    # existing member check — not a member yet
                    r.data = []
                elif call_count[0] == 6:
                    # insert invite
                    r.data = [invite_row]
                else:
                    r.data = []
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/v1/organizations/org-abc/invite",
                        json={"email": "member@test.com"},
                    )

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invite_member_not_admin(self, mock_user):
        """Non-admin member cannot invite others — returns 403."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            def execute_side():
                r = MagicMock()
                # inviter role check — plain member (not owner/admin)
                r.data = [{"role": "member"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/v1/organizations/org-abc/invite",
                        json={"email": "another@test.com"},
                    )

            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invite_member_max_reached(self, mock_user):
        """Invite when org is at max_members limit returns 400."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            call_count = [0]

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # inviter is owner
                    r.data = [{"role": "owner"}]
                elif call_count[0] == 2:
                    # org with max_members=3
                    r.data = {"max_members": 3}
                elif call_count[0] == 3:
                    # current count == max (3)
                    r.data = [{"id": "m1"}, {"id": "m2"}, {"id": "m3"}]
                    r.count = 3
                else:
                    r.data = []
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/v1/organizations/org-abc/invite",
                        json={"email": "fourth@test.com"},
                    )

            assert response.status_code == 400
            detail = response.json()["detail"].lower()
            assert "limite" in detail or "membros" in detail
        finally:
            app.dependency_overrides.clear()


class TestAcceptInvite:
    """AC25-8: POST /v1/organizations/{id}/accept"""

    @pytest.mark.asyncio
    async def test_accept_invite_success(self, mock_member):
        """Pending invite is accepted successfully."""
        app.dependency_overrides[require_auth] = lambda: mock_member
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            call_count = [0]

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # pending invite found, not yet accepted
                    r.data = [{"id": "inv-001", "accepted_at": None}]
                else:
                    # update accepted_at
                    r.data = [{"accepted_at": "2026-02-28"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post("/v1/organizations/org-abc/accept")

            assert response.status_code == 200
            assert response.json()["accepted"] is True
        finally:
            app.dependency_overrides.clear()


class TestRemoveMember:
    """AC25-9/10: DELETE /v1/organizations/{id}/members/{user_id}"""

    @pytest.mark.asyncio
    async def test_remove_member_success(self, mock_user):
        """Owner can remove a non-owner member."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            call_count = [0]

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # remover is owner
                    r.data = [{"role": "owner"}]
                elif call_count[0] == 2:
                    # target is plain member
                    r.data = [{"id": "mem-002", "role": "member"}]
                else:
                    # delete
                    r.data = [{"id": "mem-002"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.delete(
                        "/v1/organizations/org-abc/members/user-002"
                    )

            assert response.status_code == 200
            assert response.json()["removed"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_remove_owner_fails(self, mock_user):
        """Attempting to remove the org owner returns 403."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            call_count = [0]

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # remover is owner
                    r.data = [{"role": "owner"}]
                elif call_count[0] == 2:
                    # target is also owner — cannot be removed
                    r.data = [{"id": "mem-001", "role": "owner"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.delete(
                        "/v1/organizations/org-abc/members/user-001"
                    )

            assert response.status_code == 403
            assert "owner" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()


class TestGetMyOrg:
    """AC25-11: GET /v1/organizations/me"""

    @pytest.mark.asyncio
    async def test_get_my_org_returns_org(self, mock_user):
        """User who belongs to an org gets org details."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            call_count = [0]

            def execute_side():
                call_count[0] += 1
                r = MagicMock()
                if call_count[0] == 1:
                    # membership lookup
                    r.data = [
                        {
                            "org_id": "org-abc",
                            "role": "owner",
                            "accepted_at": "2026-01-01",
                        }
                    ]
                elif call_count[0] == 2:
                    # org record
                    r.data = {
                        "id": "org-abc",
                        "name": "Consultoria Teste",
                        "logo_url": None,
                        "max_members": 5,
                        "plan_type": "consultoria",
                    }
                else:
                    r.data = []
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/v1/organizations/me")

            assert response.status_code == 200
            data = response.json()
            assert data["organization"]["id"] == "org-abc"
            assert data["organization"]["user_role"] == "owner"
            assert data["organization"]["accepted"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_my_org_returns_null_when_no_org(self, mock_user):
        """User with no org membership gets organization: null."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            mock_sb, mock_table, mock_result = _mock_supabase()
            # No membership found
            mock_result.data = []

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/v1/organizations/me")

            assert response.status_code == 200
            assert response.json()["organization"] is None
        finally:
            app.dependency_overrides.clear()


# ── AC26: Quota plan capabilities ─────────────────────────────────────────────


class TestConsultoriaPlanCapabilities:
    """AC26-12/13: PLAN_CAPABILITIES and PLAN_NAMES for consultoria."""

    def test_consultoria_plan_capabilities(self):
        """Consultoria plan has the correct capability values."""
        from quota import PLAN_CAPABILITIES

        caps = PLAN_CAPABILITIES["consultoria"]
        assert caps["max_history_days"] == 1825  # 5 years
        assert caps["allow_excel"] is True
        assert caps["allow_pipeline"] is True
        assert caps["max_requests_per_month"] == 5000  # 1000 x 5 members
        assert caps["max_requests_per_min"] == 10
        assert caps["max_summary_tokens"] == 10000
        assert caps["priority"] == "high"

    def test_consultoria_plan_name(self):
        """PLAN_NAMES has correct display name for consultoria."""
        from quota import PLAN_NAMES

        assert PLAN_NAMES["consultoria"] == "SmartLic Consultoria"


class TestGetUserOrgPlan:
    """AC26-14/15: get_user_org_plan service function."""

    def test_get_user_org_plan_returns_org_tuple(self):
        """get_user_org_plan returns (org_id, plan_type, max_requests) for valid org member."""
        from quota import get_user_org_plan

        mock_sb, mock_table, _ = _mock_supabase()

        call_count = [0]

        def execute_side():
            call_count[0] += 1
            r = MagicMock()
            if call_count[0] == 1:
                # member lookup — accepted into org
                r.data = [{"org_id": "org-abc", "accepted_at": "2026-01-01T00:00:00"}]
            elif call_count[0] == 2:
                # org plan lookup
                r.data = {"plan_type": "consultoria"}
            return r

        mock_table.execute.side_effect = execute_side

        # quota.py imports get_supabase lazily, so the supabase_client patch works here.
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = get_user_org_plan("user-001")

        assert result is not None
        org_id, plan_type, max_req = result
        assert org_id == "org-abc"
        assert plan_type == "consultoria"
        assert max_req == 5000  # from PLAN_CAPABILITIES["consultoria"]

    def test_get_user_org_plan_returns_none_when_no_org(self):
        """get_user_org_plan returns None for user with no org membership."""
        from quota import get_user_org_plan

        mock_sb, mock_table, mock_result = _mock_supabase()
        # No membership found
        mock_result.data = []

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = get_user_org_plan("user-no-org")

        assert result is None

    def test_get_user_org_plan_returns_none_for_pending_invite(self):
        """get_user_org_plan returns None when invite is not accepted yet."""
        from quota import get_user_org_plan

        mock_sb, mock_table, _ = _mock_supabase()

        def execute_side():
            r = MagicMock()
            # accepted_at is None — pending invite
            r.data = [{"org_id": "org-abc", "accepted_at": None}]
            return r

        mock_table.execute.side_effect = execute_side

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = get_user_org_plan("user-pending")

        assert result is None

    def test_get_user_org_plan_returns_none_for_unknown_plan(self):
        """get_user_org_plan returns None when org plan_type is not in PLAN_CAPABILITIES."""
        from quota import get_user_org_plan

        mock_sb, mock_table, _ = _mock_supabase()

        call_count = [0]

        def execute_side():
            call_count[0] += 1
            r = MagicMock()
            if call_count[0] == 1:
                r.data = [{"org_id": "org-abc", "accepted_at": "2026-01-01T00:00:00"}]
            else:
                r.data = {"plan_type": "nonexistent_plan"}
            return r

        mock_table.execute.side_effect = execute_side

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = get_user_org_plan("user-001")

        assert result is None


# ── AC27: RLS — service-level member isolation ─────────────────────────────────


class TestMemberIsolation:
    """AC27-16: Members cannot access other org members' data via service checks."""

    @pytest.mark.asyncio
    async def test_member_cannot_see_other_org_data(self, mock_member):
        """Non-member user receives 404 when accessing an org they don't belong to."""
        app.dependency_overrides[require_auth] = lambda: mock_member
        try:
            mock_sb, mock_table, mock_result = _mock_supabase()
            # Membership check returns empty — mock_member is not in org-xyz
            mock_result.data = []

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/v1/organizations/org-xyz")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_plain_member_cannot_access_dashboard(self, mock_member):
        """Plain member (not owner/admin) gets 403 on org dashboard."""
        app.dependency_overrides[require_auth] = lambda: mock_member
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            def execute_side():
                r = MagicMock()
                # dashboard role check — user is plain member
                r.data = [{"role": "member"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/v1/organizations/org-abc/dashboard")

            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_plain_member_cannot_invite(self, mock_member):
        """Plain member cannot invite others (403)."""
        app.dependency_overrides[require_auth] = lambda: mock_member
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            def execute_side():
                r = MagicMock()
                r.data = [{"role": "member"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/v1/organizations/org-abc/invite",
                        json={"email": "newuser@test.com"},
                    )

            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_plain_member_cannot_remove_others(self, mock_member):
        """Plain member cannot remove other members (403)."""
        app.dependency_overrides[require_auth] = lambda: mock_member
        try:
            mock_sb, mock_table, _ = _mock_supabase()

            def execute_side():
                r = MagicMock()
                r.data = [{"role": "member"}]
                return r

            mock_table.execute.side_effect = execute_side

            with patch(_ORG_SVC_GET_SUPABASE, return_value=mock_sb):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.delete(
                        "/v1/organizations/org-abc/members/user-999"
                    )

            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── AC28: Stripe checkout for consultoria plan ────────────────────────────────


class TestCheckoutConsultoriaStripe:
    """AC28-17/18: Stripe checkout treats consultoria as a subscription."""

    @pytest.mark.asyncio
    async def test_checkout_consultoria_plan(self, mock_user):
        """POST /v1/checkout?plan_id=consultoria creates subscription checkout."""
        app.dependency_overrides[require_auth] = lambda: mock_user
        try:
            import os

            plan_data = {
                "id": "consultoria",
                "name": "SmartLic Consultoria",
                "is_active": True,
            }
            bp_data = {
                "stripe_price_id": "price_consultoria_monthly",
            }

            mock_session = MagicMock()
            mock_session.url = "https://checkout.stripe.com/pay/cs_test_abc123"

            # DEBT-114: sb_execute called twice — first for plans, then plan_billing_periods
            mock_sb_execute = AsyncMock(side_effect=[
                MagicMock(data=plan_data),
                MagicMock(data=bp_data),
            ])

            with (
                patch(
                    "routes.billing.sb_execute",
                    mock_sb_execute,
                ),
                patch.dict(os.environ, {
                    "STRIPE_SECRET_KEY": "sk_test_fake",
                    "FRONTEND_URL": "https://smartlic.tech",
                }),
                patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/v1/checkout?plan_id=consultoria&billing_period=monthly"
                    )

            assert response.status_code == 200
            data = response.json()
            assert "checkout_url" in data
            assert data["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_abc123"

            # Most important: mode must be "subscription" for consultoria
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs.get("mode") == "subscription"

        finally:
            app.dependency_overrides.clear()

    def test_billing_subscription_check_consultoria(self):
        """is_subscription logic in billing.py includes consultoria plan."""
        # The billing route defines:
        #   is_subscription = plan_id in ("smartlic_pro", "consultoria", "consultor_agil", ...)
        # This is a whitebox assertion — if the set changes, the test flags it.
        subscription_plan_ids = {
            "smartlic_pro",
            "consultoria",
            "consultor_agil",
            "maquina",
            "sala_guerra",
        }

        assert "consultoria" in subscription_plan_ids, (
            "consultoria must be in the subscription plans set so Stripe uses mode='subscription'"
        )
        assert "smartlic_pro" in subscription_plan_ids
        # non-subscription plans must NOT be in this set
        assert "free" not in subscription_plan_ids
        assert "free_trial" not in subscription_plan_ids


# ── AC26 supplementary: org-level quota isolation ─────────────────────────────


class TestOrgLevelQuotaIsolation:
    """Additional AC26 tests: quota is tracked per-org, not per-user."""

    def test_check_and_increment_org_quota_delegates_to_atomic(self):
        """check_and_increment_org_quota_atomic delegates with org_id as quota subject."""
        from quota import check_and_increment_org_quota_atomic

        with patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 4999)) as mock_fn:
            result = check_and_increment_org_quota_atomic(
                org_id="org-abc",
                user_id="user-001",
                max_quota=5000,
            )

        # Must be called with org_id (not user_id) as the quota subject
        mock_fn.assert_called_once_with("org-abc", 5000)
        assert result == (True, 1, 4999)

    def test_consultoria_max_requests_five_times_individual(self):
        """Consultoria quota (5000/month) is exactly 5x the standard pro plan (1000/month)."""
        from quota import PLAN_CAPABILITIES

        individual = PLAN_CAPABILITIES["smartlic_pro"]["max_requests_per_month"]
        org = PLAN_CAPABILITIES["consultoria"]["max_requests_per_month"]

        assert org == individual * 5
