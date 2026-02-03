"""Tests for admin endpoints module (admin.py).

Tests user management CRUD operations, admin authorization, and plan assignment.
Uses mocked Supabase client to avoid external API calls.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestGetAdminIds:
    """Test suite for _get_admin_ids helper function."""

    def test_returns_empty_set_when_env_not_set(self):
        """Should return empty set when ADMIN_USER_IDS is not set."""
        from admin import _get_admin_ids

        with patch.dict(os.environ, {}, clear=True):
            # Ensure ADMIN_USER_IDS is not in environ
            os.environ.pop("ADMIN_USER_IDS", None)
            result = _get_admin_ids()

        assert result == set()

    def test_returns_empty_set_when_env_is_empty(self):
        """Should return empty set when ADMIN_USER_IDS is empty string."""
        from admin import _get_admin_ids

        with patch.dict(os.environ, {"ADMIN_USER_IDS": ""}):
            result = _get_admin_ids()

        assert result == set()

    def test_parses_single_admin_id(self):
        """Should parse single admin ID correctly."""
        from admin import _get_admin_ids

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "admin-uuid-123"}):
            result = _get_admin_ids()

        assert result == {"admin-uuid-123"}

    def test_parses_multiple_admin_ids(self):
        """Should parse multiple comma-separated admin IDs."""
        from admin import _get_admin_ids

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "admin-1,admin-2,admin-3"}):
            result = _get_admin_ids()

        assert result == {"admin-1", "admin-2", "admin-3"}

    def test_strips_whitespace_from_ids(self):
        """Should strip whitespace from admin IDs."""
        from admin import _get_admin_ids

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "  admin-1 , admin-2  , admin-3  "}):
            result = _get_admin_ids()

        assert result == {"admin-1", "admin-2", "admin-3"}

    def test_ignores_empty_entries(self):
        """Should ignore empty entries from extra commas."""
        from admin import _get_admin_ids

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "admin-1,,admin-2,,,admin-3,"}):
            result = _get_admin_ids()

        assert result == {"admin-1", "admin-2", "admin-3"}


class TestRequireAdmin:
    """Test suite for require_admin dependency."""

    @pytest.mark.asyncio
    async def test_allows_valid_admin_user(self):
        """Should allow user whose ID is in ADMIN_USER_IDS."""
        from admin import require_admin

        admin_user = {
            "id": "admin-uuid-123",
            "email": "admin@example.com",
            "role": "authenticated",
        }

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "admin-uuid-123,other-admin"}):
            result = await require_admin(user=admin_user)

        assert result == admin_user

    @pytest.mark.asyncio
    async def test_rejects_non_admin_user(self):
        """Should raise 403 for user not in ADMIN_USER_IDS."""
        from admin import require_admin

        regular_user = {
            "id": "regular-user-456",
            "email": "user@example.com",
            "role": "authenticated",
        }

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "admin-uuid-123"}):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(user=regular_user)

        assert exc_info.value.status_code == 403
        assert "administradores" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rejects_when_no_admins_configured(self):
        """Should reject all users when ADMIN_USER_IDS is not set."""
        from admin import require_admin

        user = {
            "id": "any-user",
            "email": "any@example.com",
            "role": "authenticated",
        }

        with patch.dict(os.environ, {"ADMIN_USER_IDS": ""}):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(user=user)

        assert exc_info.value.status_code == 403


class TestAdminEndpointsBase:
    """Base class for admin endpoint tests with common fixtures."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        return {
            "id": "admin-123",
            "email": "admin@example.com",
            "role": "authenticated",
        }

    @pytest.fixture
    def admin_app_with_overrides(self, mock_admin_user):
        """Create FastAPI app with admin router and dependency overrides."""
        from fastapi import FastAPI
        from admin import router, require_admin

        app = FastAPI()
        app.include_router(router)

        # Override the require_admin dependency
        async def mock_require_admin():
            return mock_admin_user

        app.dependency_overrides[require_admin] = mock_require_admin

        return app

    @pytest.fixture
    def admin_client(self, admin_app_with_overrides):
        """Create test client with admin auth mocked."""
        return TestClient(admin_app_with_overrides)


class TestListUsersEndpoint(TestAdminEndpointsBase):
    """Test suite for GET /admin/users endpoint."""

    @pytest.fixture
    def admin_app_no_override(self):
        """Create FastAPI app without auth override for testing 401."""
        from fastapi import FastAPI
        from admin import router

        app = FastAPI()
        app.include_router(router)
        return app

    def test_list_users_requires_admin(self, admin_app_no_override):
        """Should return 401 without authentication."""
        client = TestClient(admin_app_no_override)
        response = client.get("/admin/users")

        assert response.status_code == 401

    def test_list_users_returns_paginated_results(self, admin_client):
        """Should return paginated user list."""
        mock_supabase = Mock()

        users_result = Mock()
        users_result.data = [
            {"id": "user-1", "email": "user1@example.com", "full_name": "User One", "user_subscriptions": []},
            {"id": "user-2", "email": "user2@example.com", "full_name": "User Two", "user_subscriptions": []},
        ]
        users_result.count = 2

        mock_table = Mock()
        mock_table.select.return_value.order.return_value.range.return_value.execute.return_value = users_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.get("/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["users"]) == 2

    def test_list_users_respects_limit_and_offset(self, admin_client):
        """Should respect limit and offset query parameters."""
        mock_supabase = Mock()

        users_result = Mock()
        users_result.data = [{"id": "user-3", "email": "user3@example.com", "user_subscriptions": []}]
        users_result.count = 100

        mock_table = Mock()
        mock_table.select.return_value.order.return_value.range.return_value.execute.return_value = users_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.get("/admin/users?limit=10&offset=50")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 50

    def test_list_users_with_search_filter(self, admin_client):
        """Should filter users by search term."""
        mock_supabase = Mock()

        users_result = Mock()
        users_result.data = [{"id": "user-match", "email": "john@example.com", "user_subscriptions": []}]
        users_result.count = 1

        mock_table = Mock()
        mock_table.select.return_value.or_.return_value.order.return_value.range.return_value.execute.return_value = users_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.get("/admin/users?search=john")

        assert response.status_code == 200


class TestCreateUserEndpoint(TestAdminEndpointsBase):
    """Test suite for POST /admin/users endpoint."""

    def test_create_user_success(self, admin_client):
        """Should create new user successfully."""
        mock_supabase = Mock()

        # Mock auth.admin.create_user
        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = "new-user-uuid"
        mock_supabase.auth.admin.create_user.return_value = created_user

        # Mock table operations
        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "newuser@example.com",
                    "password": "securepassword123",
                    "full_name": "New User",
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "new-user-uuid"
        assert data["email"] == "newuser@example.com"

    def test_create_user_with_plan(self, admin_client):
        """Should create user with specified plan."""
        mock_supabase = Mock()

        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = "user-with-plan"
        mock_supabase.auth.admin.create_user.return_value = created_user

        # Mock plan lookup
        plan_result = Mock()
        plan_result.data = {
            "id": "pack_10",
            "max_searches": 10,
            "duration_days": None,
        }

        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result
        mock_table.insert.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "premium@example.com",
                    "password": "securepassword123",
                    "plan_id": "pack_10",
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == "pack_10"

    def test_create_user_validation_password_too_short(self, admin_client):
        """Should reject password shorter than 6 characters."""
        response = admin_client.post(
            "/admin/users",
            json={
                "email": "user@example.com",
                "password": "12345",  # Too short
            }
        )

        assert response.status_code == 422

    def test_create_user_supabase_error(self, admin_client):
        """Should return 400 when Supabase fails to create user."""
        mock_supabase = Mock()
        mock_supabase.auth.admin.create_user.side_effect = Exception("Email already exists")

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "duplicate@example.com",
                    "password": "securepassword123",
                }
            )

        assert response.status_code == 400
        assert "erro" in response.json()["detail"].lower()


class TestDeleteUserEndpoint(TestAdminEndpointsBase):
    """Test suite for DELETE /admin/users/{user_id} endpoint."""

    def test_delete_user_success(self, admin_client):
        """Should delete user successfully."""
        mock_supabase = Mock()

        # Mock profile lookup
        profile_result = Mock()
        profile_result.data = {"email": "deleted@example.com"}

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        mock_supabase.table.return_value = mock_table
        mock_supabase.auth.admin.delete_user.return_value = None

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.delete("/admin/users/user-to-delete")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["user_id"] == "user-to-delete"

    def test_delete_user_not_found(self, admin_client):
        """Should return 404 when user not found."""
        mock_supabase = Mock()

        profile_result = Mock()
        profile_result.data = None  # User not found

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.delete("/admin/users/nonexistent-user")

        assert response.status_code == 404
        assert "nao encontrado" in response.json()["detail"].lower()

    def test_delete_user_supabase_error(self, admin_client):
        """Should return 500 when Supabase delete fails."""
        mock_supabase = Mock()

        profile_result = Mock()
        profile_result.data = {"email": "user@example.com"}

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        mock_supabase.table.return_value = mock_table
        mock_supabase.auth.admin.delete_user.side_effect = Exception("Delete failed")

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.delete("/admin/users/user-id")

        assert response.status_code == 500


class TestUpdateUserEndpoint(TestAdminEndpointsBase):
    """Test suite for PUT /admin/users/{user_id} endpoint."""

    def test_update_user_profile(self, admin_client):
        """Should update user profile fields."""
        mock_supabase = Mock()

        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.put(
                "/admin/users/user-123",
                json={
                    "full_name": "Updated Name",
                    "company": "New Company",
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["updated"] is True
        assert data["user_id"] == "user-123"

    def test_update_user_with_plan_change(self, admin_client):
        """Should update user plan when plan_id is provided."""
        mock_supabase = Mock()

        # Mock plan lookup
        plan_result = Mock()
        plan_result.data = {
            "id": "monthly",
            "max_searches": None,
            "duration_days": 30,
        }

        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result
        mock_table.insert.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.put(
                "/admin/users/user-123",
                json={"plan_id": "monthly"}
            )

        assert response.status_code == 200


class TestResetPasswordEndpoint(TestAdminEndpointsBase):
    """Test suite for POST /admin/users/{user_id}/reset-password endpoint."""

    def test_reset_password_success(self, admin_client):
        """Should reset user password successfully."""
        mock_supabase = Mock()
        mock_supabase.auth.admin.update_user_by_id.return_value = None

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users/user-123/reset-password",
                json={"new_password": "newSecurePassword123"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == "user-123"

    def test_reset_password_too_short(self, admin_client):
        """Should reject password shorter than 6 characters."""
        response = admin_client.post(
            "/admin/users/user-123/reset-password",
            json={"new_password": "12345"}  # Too short
        )

        assert response.status_code == 400
        assert "6 caracteres" in response.json()["detail"]

    def test_reset_password_supabase_error(self, admin_client):
        """Should return 500 when Supabase update fails."""
        mock_supabase = Mock()
        mock_supabase.auth.admin.update_user_by_id.side_effect = Exception("Update failed")

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users/user-123/reset-password",
                json={"new_password": "validPassword123"}
            )

        assert response.status_code == 500


class TestAssignPlanEndpoint(TestAdminEndpointsBase):
    """Test suite for POST /admin/users/{user_id}/assign-plan endpoint."""

    def test_assign_plan_success(self, admin_client):
        """Should assign plan to user successfully."""
        mock_supabase = Mock()

        # Mock plan lookup
        plan_result = Mock()
        plan_result.data = {
            "id": "pack_10",
            "max_searches": 10,
            "duration_days": None,
        }

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users/user-123/assign-plan?plan_id=pack_10"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["assigned"] is True
        assert data["user_id"] == "user-123"
        assert data["plan_id"] == "pack_10"

    def test_assign_plan_not_found(self, admin_client):
        """Should return 404 when plan not found."""
        mock_supabase = Mock()

        # Mock plan lookup - not found
        plan_result = Mock()
        plan_result.data = None

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users/user-123/assign-plan?plan_id=invalid_plan"
            )

        assert response.status_code == 404
        assert "nao encontrado" in response.json()["detail"].lower()


class TestAssignPlanFunction:
    """Test suite for _assign_plan helper function."""

    def test_assign_plan_deactivates_previous_subscription(self):
        """Should deactivate previous active subscriptions."""
        from admin import _assign_plan

        mock_supabase = Mock()

        plan_result = Mock()
        plan_result.data = {
            "id": "pack_10",
            "max_searches": 10,
            "duration_days": None,
        }

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result
        mock_update = Mock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        _assign_plan(mock_supabase, "user-123", "pack_10")

        # Verify deactivation was called
        mock_table.update.assert_called_with({"is_active": False})

    def test_assign_plan_creates_subscription_with_credits(self):
        """Should create subscription with correct credits for pack plans."""
        from admin import _assign_plan

        mock_supabase = Mock()

        plan_result = Mock()
        plan_result.data = {
            "id": "pack_10",
            "max_searches": 10,
            "duration_days": None,
        }

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()

        insert_mock = Mock()
        mock_table.insert.return_value = insert_mock
        insert_mock.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        _assign_plan(mock_supabase, "user-123", "pack_10")

        # Verify insert was called with correct data
        insert_call = mock_table.insert.call_args[0][0]
        assert insert_call["user_id"] == "user-123"
        assert insert_call["plan_id"] == "pack_10"
        assert insert_call["credits_remaining"] == 10
        assert insert_call["is_active"] is True
        assert insert_call["expires_at"] is None

    def test_assign_plan_creates_subscription_with_expiry(self):
        """Should create subscription with expiry date for time-based plans."""
        from admin import _assign_plan
        from datetime import datetime, timezone, timedelta

        mock_supabase = Mock()

        plan_result = Mock()
        plan_result.data = {
            "id": "monthly",
            "max_searches": None,  # Unlimited
            "duration_days": 30,
        }

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()

        insert_mock = Mock()
        mock_table.insert.return_value = insert_mock
        insert_mock.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        _assign_plan(mock_supabase, "user-123", "monthly")

        # Verify insert was called with expiry date
        insert_call = mock_table.insert.call_args[0][0]
        assert insert_call["credits_remaining"] is None  # Unlimited
        assert insert_call["expires_at"] is not None

        # Verify expiry is approximately 30 days from now
        expires_at = datetime.fromisoformat(insert_call["expires_at"].replace("Z", "+00:00"))
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        delta = abs((expires_at - expected_expiry).total_seconds())
        assert delta < 60  # Within 1 minute


class TestAdminLogging(TestAdminEndpointsBase):
    """Test suite for admin operation logging."""

    def test_create_user_logs_action(self, admin_client, caplog):
        """Should log admin user creation action."""
        import logging

        mock_supabase = Mock()

        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = "new-user"
        mock_supabase.auth.admin.create_user.return_value = created_user

        mock_table = Mock()
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with caplog.at_level(logging.INFO):
                admin_client.post(
                    "/admin/users",
                    json={"email": "new@example.com", "password": "password123"}
                )

        assert any("created user" in record.message.lower() for record in caplog.records)
        assert any("admin-123" in record.message for record in caplog.records)

    def test_delete_user_logs_action(self, admin_client, caplog):
        """Should log admin user deletion action."""
        import logging

        mock_supabase = Mock()

        profile_result = Mock()
        profile_result.data = {"email": "deleted@example.com"}

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        mock_supabase.table.return_value = mock_table
        mock_supabase.auth.admin.delete_user.return_value = None

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with caplog.at_level(logging.INFO):
                admin_client.delete("/admin/users/user-to-delete")

        assert any("deleted user" in record.message.lower() for record in caplog.records)
