"""Tests for STORY-224 Track 3: Authorization module tests.

Tests admin and master access control, role checking with retry logic, and environment-based admin overrides.

Covers:
- AC19: require_admin rejects non-admin users (403)
- AC20: require_admin accepts users in ADMIN_USER_IDS env var
- AC21: _check_user_roles() retry logic (1 retry, 0.3s delay)

Related Files:
- backend/authorization.py: _get_admin_ids, _check_user_roles, _is_admin, _has_master_access, _get_master_quota_info
"""

import os
import time
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException


class TestGetAdminIds:
    """Test _get_admin_ids() parsing and normalization."""

    def test_empty_env_returns_empty_set(self, monkeypatch):
        """Empty ADMIN_USER_IDS returns empty set."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from authorization import _get_admin_ids

        result = _get_admin_ids()

        assert result == set()

    def test_single_id(self, monkeypatch):
        """Single admin ID is parsed correctly."""
        monkeypatch.setenv("ADMIN_USER_IDS", "admin-user-123")
        from authorization import _get_admin_ids

        result = _get_admin_ids()

        assert result == {"admin-user-123"}

    def test_multiple_ids(self, monkeypatch):
        """Multiple comma-separated IDs are parsed."""
        monkeypatch.setenv("ADMIN_USER_IDS", "admin-1,admin-2,admin-3")
        from authorization import _get_admin_ids

        result = _get_admin_ids()

        assert result == {"admin-1", "admin-2", "admin-3"}

    def test_whitespace_handling(self, monkeypatch):
        """Whitespace around IDs is stripped."""
        monkeypatch.setenv("ADMIN_USER_IDS", "  admin-1  ,  admin-2  ,  admin-3  ")
        from authorization import _get_admin_ids

        result = _get_admin_ids()

        assert result == {"admin-1", "admin-2", "admin-3"}

    def test_case_normalization(self, monkeypatch):
        """IDs are normalized to lowercase."""
        monkeypatch.setenv("ADMIN_USER_IDS", "Admin-User-ABC,ADMIN-USER-XYZ")
        from authorization import _get_admin_ids

        result = _get_admin_ids()

        assert result == {"admin-user-abc", "admin-user-xyz"}

    def test_empty_items_ignored(self, monkeypatch):
        """Empty items from multiple commas are ignored."""
        monkeypatch.setenv("ADMIN_USER_IDS", "admin-1,,,admin-2,,")
        from authorization import _get_admin_ids

        result = _get_admin_ids()

        assert result == {"admin-1", "admin-2"}

    def test_missing_env_var(self, monkeypatch):
        """Missing ADMIN_USER_IDS env var returns empty set."""
        monkeypatch.delenv("ADMIN_USER_IDS", raising=False)
        from authorization import _get_admin_ids

        result = _get_admin_ids()

        assert result == set()


class TestCheckUserRoles:
    """Test _check_user_roles() with Supabase integration."""

    @pytest.mark.asyncio
    async def test_admin_user(self):
        """User with is_admin=true returns (True, True)."""
        from authorization import _check_user_roles

        mock_response = Mock()
        mock_response.data = {"is_admin": True, "plan_type": "free_trial"}

        mock_execute = Mock(return_value=mock_response)
        mock_single = Mock(return_value=Mock(execute=mock_execute))
        mock_eq = Mock(return_value=Mock(single=mock_single))
        mock_select = Mock(return_value=Mock(eq=mock_eq))
        mock_table = Mock(return_value=Mock(select=mock_select))

        mock_sb = Mock(table=mock_table)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            is_admin, is_master = await _check_user_roles("admin-user-id")

        assert is_admin is True
        assert is_master is True  # Admin implies master

    @pytest.mark.asyncio
    async def test_master_user(self):
        """User with plan_type='master' returns (False, True)."""
        from authorization import _check_user_roles

        mock_response = Mock()
        mock_response.data = {"is_admin": False, "plan_type": "master"}

        mock_execute = Mock(return_value=mock_response)
        mock_single = Mock(return_value=Mock(execute=mock_execute))
        mock_eq = Mock(return_value=Mock(single=mock_single))
        mock_select = Mock(return_value=Mock(eq=mock_eq))
        mock_table = Mock(return_value=Mock(select=mock_select))

        mock_sb = Mock(table=mock_table)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            is_admin, is_master = await _check_user_roles("master-user-id")

        assert is_admin is False
        assert is_master is True

    @pytest.mark.asyncio
    async def test_regular_user(self):
        """Regular user (is_admin=false, plan_type!='master') returns (False, False)."""
        from authorization import _check_user_roles

        mock_response = Mock()
        mock_response.data = {"is_admin": False, "plan_type": "free_trial"}

        mock_execute = Mock(return_value=mock_response)
        mock_single = Mock(return_value=Mock(execute=mock_execute))
        mock_eq = Mock(return_value=Mock(single=mock_single))
        mock_select = Mock(return_value=Mock(eq=mock_eq))
        mock_table = Mock(return_value=Mock(select=mock_select))

        mock_sb = Mock(table=mock_table)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            is_admin, is_master = await _check_user_roles("regular-user-id")

        assert is_admin is False
        assert is_master is False

    @pytest.mark.asyncio
    async def test_profile_not_found(self):
        """Profile not found (data=None) returns (False, False)."""
        from authorization import _check_user_roles

        mock_response = Mock()
        mock_response.data = None

        mock_execute = Mock(return_value=mock_response)
        mock_single = Mock(return_value=Mock(execute=mock_execute))
        mock_eq = Mock(return_value=Mock(single=mock_single))
        mock_select = Mock(return_value=Mock(eq=mock_eq))
        mock_table = Mock(return_value=Mock(select=mock_select))

        mock_sb = Mock(table=mock_table)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            is_admin, is_master = await _check_user_roles("nonexistent-user")

        assert is_admin is False
        assert is_master is False

    @pytest.mark.asyncio
    async def test_is_admin_column_missing_fallback(self):
        """If is_admin column doesn't exist, fallback to plan_type only."""
        from authorization import _check_user_roles

        # First attempt: is_admin column missing (raises exception)
        # Second attempt: fallback to just plan_type (succeeds)
        mock_response_fallback = Mock()
        mock_response_fallback.data = {"plan_type": "master"}

        mock_execute_fallback = Mock(return_value=mock_response_fallback)
        mock_single_fallback = Mock(return_value=Mock(execute=mock_execute_fallback))
        mock_eq_fallback = Mock(return_value=Mock(single=mock_single_fallback))
        mock_select_fallback = Mock(return_value=Mock(eq=mock_eq_fallback))

        # First select() with is_admin raises
        # Second select() without is_admin succeeds
        call_count = {"count": 0}

        def mock_select_side_effect(*args):
            call_count["count"] += 1
            if call_count["count"] == 1:
                # First call: is_admin + plan_type
                raise Exception("Column is_admin does not exist")
            else:
                # Second call: plan_type only
                return Mock(eq=mock_eq_fallback)

        mock_table = Mock(return_value=Mock(select=Mock(side_effect=mock_select_side_effect)))
        mock_sb = Mock(table=mock_table)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            is_admin, is_master = await _check_user_roles("user-id")

        # Should fallback to plan_type only
        assert is_admin is False
        assert is_master is True

    @pytest.mark.asyncio
    async def test_retry_on_first_failure(self):
        """AC21: Retry logic - first failure triggers 0.3s delay + retry."""
        from authorization import _check_user_roles

        # First call: raises exception AFTER the inner try/except (e.g., at profile.data access)
        # Second call: succeeds
        mock_response_success = Mock()
        mock_response_success.data = {"is_admin": False, "plan_type": "free_trial"}

        attempts = []

        def mock_get_supabase_side_effect():
            attempts.append(1)
            if len(attempts) == 1:
                # First attempt - fail at get_supabase() level (outer exception)
                raise Exception("Transient database connection error")
            else:
                # Second attempt - succeed
                mock_execute = Mock(return_value=mock_response_success)
                mock_single = Mock(return_value=Mock(execute=mock_execute))
                mock_eq = Mock(return_value=Mock(single=mock_single))
                mock_select = Mock(return_value=Mock(eq=mock_eq))
                mock_table = Mock(return_value=Mock(select=mock_select))
                return Mock(table=mock_table)

        start_time = time.time()

        with patch("supabase_client.get_supabase", side_effect=mock_get_supabase_side_effect):
            is_admin, is_master = await _check_user_roles("retry-user-id")

        elapsed = time.time() - start_time

        # Should have retried after ~0.3s
        assert elapsed >= 0.25  # Allow some tolerance
        assert len(attempts) == 2  # Two attempts
        assert is_admin is False
        assert is_master is False

    @pytest.mark.asyncio
    async def test_failure_after_two_attempts(self):
        """AC21: After 2 failed attempts, returns (False, False)."""
        from authorization import _check_user_roles

        attempts = []

        def mock_get_supabase_side_effect():
            attempts.append(1)
            # Always fail
            raise Exception("Persistent database connection error")

        with patch("supabase_client.get_supabase", side_effect=mock_get_supabase_side_effect):
            is_admin, is_master = await _check_user_roles("failure-user-id")

        # Should return (False, False) after 2 attempts
        assert is_admin is False
        assert is_master is False
        assert len(attempts) == 2

    @pytest.mark.asyncio
    async def test_admin_with_master_plan_type(self):
        """Admin with plan_type='master' still returns (True, True)."""
        from authorization import _check_user_roles

        mock_response = Mock()
        mock_response.data = {"is_admin": True, "plan_type": "master"}

        mock_execute = Mock(return_value=mock_response)
        mock_single = Mock(return_value=Mock(execute=mock_execute))
        mock_eq = Mock(return_value=Mock(single=mock_single))
        mock_select = Mock(return_value=Mock(eq=mock_eq))
        mock_table = Mock(return_value=Mock(select=mock_select))
        mock_sb = Mock(table=mock_table)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            is_admin, is_master = await _check_user_roles("admin-master-user")

        assert is_admin is True
        assert is_master is True


class TestIsAdmin:
    """Test _is_admin() fast path and Supabase fallback."""

    @pytest.mark.asyncio
    async def test_via_env_var_fast_path(self, monkeypatch):
        """AC20: User in ADMIN_USER_IDS env var returns True (no DB call)."""
        monkeypatch.setenv("ADMIN_USER_IDS", "env-admin-1,env-admin-2")
        from authorization import _is_admin

        with patch("authorization._check_user_roles") as mock_check:
            result = await _is_admin("env-admin-1")

        assert result is True
        # Should NOT have called Supabase
        mock_check.assert_not_called()

    @pytest.mark.asyncio
    async def test_via_env_var_case_insensitive(self, monkeypatch):
        """Env var match is case-insensitive."""
        monkeypatch.setenv("ADMIN_USER_IDS", "Admin-User-ABC")
        from authorization import _is_admin

        with patch("authorization._check_user_roles") as mock_check:
            result = await _is_admin("ADMIN-USER-ABC")

        assert result is True
        mock_check.assert_not_called()

    @pytest.mark.asyncio
    async def test_via_supabase(self, monkeypatch):
        """User not in env var but is_admin=true in Supabase returns True."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from authorization import _is_admin

        with patch("authorization._check_user_roles", return_value=(True, True)):
            result = await _is_admin("db-admin-user")

        assert result is True

    @pytest.mark.asyncio
    async def test_not_admin(self, monkeypatch):
        """User not in env var and is_admin=false in Supabase returns False."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from authorization import _is_admin

        with patch("authorization._check_user_roles", return_value=(False, False)):
            result = await _is_admin("regular-user")

        assert result is False


class TestHasMasterAccess:
    """Test _has_master_access() for admin/master privilege checking."""

    @pytest.mark.asyncio
    async def test_via_env_admin(self, monkeypatch):
        """User in ADMIN_USER_IDS has master access (no DB call)."""
        monkeypatch.setenv("ADMIN_USER_IDS", "env-admin")
        from authorization import _has_master_access

        with patch("authorization._check_user_roles") as mock_check:
            result = await _has_master_access("env-admin")

        assert result is True
        mock_check.assert_not_called()

    @pytest.mark.asyncio
    async def test_via_db_admin(self, monkeypatch):
        """User with is_admin=true in Supabase has master access."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from authorization import _has_master_access

        with patch("authorization._check_user_roles", return_value=(True, True)):
            result = await _has_master_access("db-admin")

        assert result is True

    @pytest.mark.asyncio
    async def test_via_db_master_plan_type(self, monkeypatch):
        """User with plan_type='master' has master access."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from authorization import _has_master_access

        with patch("authorization._check_user_roles", return_value=(False, True)):
            result = await _has_master_access("master-plan-user")

        assert result is True

    @pytest.mark.asyncio
    async def test_regular_user(self, monkeypatch):
        """Regular user (not admin, not master) returns False."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from authorization import _has_master_access

        with patch("authorization._check_user_roles", return_value=(False, False)):
            result = await _has_master_access("regular-user")

        assert result is False


class TestGetMasterQuotaInfo:
    """Test _get_master_quota_info() returns sala_guerra plan."""

    def test_admin_label(self):
        """Admin user gets 'Sala de Guerra (Admin)' label."""
        from authorization import _get_master_quota_info

        quota_info = _get_master_quota_info(is_admin=True)

        assert quota_info.allowed is True
        assert quota_info.plan_id == "sala_guerra"
        assert quota_info.plan_name == "Sala de Guerra (Admin)"
        assert quota_info.quota_remaining == 999999

    def test_master_label(self):
        """Master user gets 'Sala de Guerra (Master)' label."""
        from authorization import _get_master_quota_info

        quota_info = _get_master_quota_info(is_admin=False)

        assert quota_info.allowed is True
        assert quota_info.plan_id == "sala_guerra"
        assert quota_info.plan_name == "Sala de Guerra (Master)"
        assert quota_info.quota_remaining == 999999

    def test_returns_correct_plan_id(self):
        """Returns sala_guerra plan_id (highest tier)."""
        from authorization import _get_master_quota_info

        quota_info = _get_master_quota_info(is_admin=False)

        assert quota_info.plan_id == "sala_guerra"

    def test_unlimited_quota(self):
        """Master quota is effectively unlimited."""
        from authorization import _get_master_quota_info

        quota_info = _get_master_quota_info(is_admin=True)

        assert quota_info.quota_used == 0
        assert quota_info.quota_remaining == 999999

    def test_capabilities_included(self):
        """Returns sala_guerra capabilities."""
        from authorization import _get_master_quota_info

        quota_info = _get_master_quota_info(is_admin=True)

        assert quota_info.capabilities is not None
        # sala_guerra has the most permissive capabilities (dict format)
        assert "allow_excel" in quota_info.capabilities
        assert quota_info.capabilities["allow_excel"] is True


class TestRequireAdmin:
    """Test require_admin dependency (AC19, AC20)."""

    @pytest.mark.asyncio
    async def test_rejects_non_admin_with_403(self, monkeypatch):
        """AC19: require_admin raises 403 for non-admin users."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from admin import require_admin

        mock_user = {"id": "regular-user", "email": "user@example.com"}

        with patch("admin._is_admin_from_supabase", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(user=mock_user)

        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail.lower() or "forbidden" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_accepts_user_in_env_var(self, monkeypatch):
        """AC20: require_admin accepts users in ADMIN_USER_IDS env var."""
        # Use valid UUID v4 format (admin.py validates this)
        admin_uuid = "550e8400-e29b-41d4-a716-446655440000"
        monkeypatch.setenv("ADMIN_USER_IDS", admin_uuid)
        from admin import require_admin

        mock_user = {"id": admin_uuid, "email": "admin@example.com"}

        # No patch needed - env var fast path doesn't call Supabase
        result = await require_admin(user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_accepts_db_admin(self, monkeypatch):
        """require_admin accepts user with is_admin=true in Supabase."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from admin import require_admin

        mock_user = {"id": "db-admin", "email": "dbadmin@example.com"}

        with patch("admin._is_admin_from_supabase", return_value=True):
            result = await require_admin(user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_rejects_unauthenticated_user(self, monkeypatch):
        """require_admin raises AttributeError when user is None (because require_auth dependency should handle this)."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from admin import require_admin

        # require_admin expects user from require_auth dependency
        # If user is None, it will raise AttributeError trying to call user.get()
        # In real usage, require_auth dependency raises 401 before require_admin runs
        with pytest.raises(AttributeError):
            await require_admin(user=None)

    @pytest.mark.asyncio
    async def test_error_message_is_clear(self, monkeypatch):
        """require_admin error message mentions admin access required."""
        monkeypatch.setenv("ADMIN_USER_IDS", "")
        from admin import require_admin

        mock_user = {"id": "regular-user"}

        with patch("admin._is_admin_from_supabase", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(user=mock_user)

        detail = exc_info.value.detail.lower()
        assert "admin" in detail or "forbidden" in detail or "acesso negado" in detail or "restrito" in detail
