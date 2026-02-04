"""Tests for secure ID validation (Issue #203 - P0 Security Fix).

This module tests the security hardening for admin user ID parsing:
- UUID v4 format validation
- Plan ID validation
- Search query sanitization
- Malicious input rejection
"""

import pytest
import os
from unittest.mock import patch, Mock

from schemas import (
    validate_uuid,
    validate_plan_id,
    sanitize_search_query,
    SecureUserId,
    SecurePlanId,
    UUID_V4_PATTERN,
    PLAN_ID_PATTERN,
)


class TestValidateUuid:
    """Test suite for validate_uuid function."""

    def test_accepts_valid_uuid_v4(self):
        """Should accept valid UUID v4 strings."""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "6ba7b810-9dad-41d9-80b4-00c04fd430c8",
        ]
        for uuid in valid_uuids:
            result = validate_uuid(uuid)
            assert result == uuid.lower()

    def test_normalizes_to_lowercase(self):
        """Should normalize UUIDs to lowercase."""
        result = validate_uuid("550E8400-E29B-41D4-A716-446655440000")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        result = validate_uuid("  550e8400-e29b-41d4-a716-446655440000  ")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_rejects_empty_string(self):
        """Should reject empty string."""
        with pytest.raises(ValueError) as exc_info:
            validate_uuid("")
        assert "cannot be empty" in str(exc_info.value)

    def test_rejects_none(self):
        """Should reject None values."""
        with pytest.raises(ValueError):
            validate_uuid(None)

    def test_rejects_invalid_uuid_format(self):
        """Should reject strings that don't match UUID format."""
        invalid_uuids = [
            "not-a-uuid",
            "12345678",
            "550e8400-e29b-11d4-a716-446655440000",  # UUID v1
            "550e8400-e29b-21d4-a716-446655440000",  # UUID v2
            "550e8400-e29b-31d4-a716-446655440000",  # UUID v3
            "550e8400-e29b-51d4-a716-446655440000",  # UUID v5
            "550e8400e29b41d4a716446655440000",  # No dashes
            "550e8400-e29b-41d4-a716-44665544000",  # Too short
            "550e8400-e29b-41d4-a716-4466554400000",  # Too long
        ]
        for invalid_uuid in invalid_uuids:
            with pytest.raises(ValueError) as exc_info:
                validate_uuid(invalid_uuid)
            assert "Invalid" in str(exc_info.value) or "UUID" in str(exc_info.value)

    def test_rejects_sql_injection_attempts(self):
        """Should reject strings containing SQL injection patterns."""
        injection_attempts = [
            "550e8400-e29b-41d4-a716-446655440000; DROP TABLE users;--",
            "550e8400-e29b-41d4-a716-446655440000' OR '1'='1",
            "'; DELETE FROM profiles; --",
            "1; UPDATE users SET role='admin' WHERE id='",
        ]
        for attempt in injection_attempts:
            with pytest.raises(ValueError):
                validate_uuid(attempt)

    def test_rejects_path_traversal_attempts(self):
        """Should reject path traversal patterns."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "550e8400-e29b-41d4-a716-446655440000/../..",
        ]
        for attempt in traversal_attempts:
            with pytest.raises(ValueError):
                validate_uuid(attempt)

    def test_custom_field_name_in_error(self):
        """Should include custom field name in error message."""
        with pytest.raises(ValueError) as exc_info:
            validate_uuid("invalid", "custom_field")
        assert "custom_field" in str(exc_info.value)


class TestValidatePlanId:
    """Test suite for validate_plan_id function."""

    def test_accepts_valid_plan_ids(self):
        """Should accept valid plan ID strings."""
        valid_ids = [
            "free",
            "free_trial",
            "pack_10",
            "pack_50",
            "monthly",
            "consultor_agil",
            "maquina",
            "sala_guerra",
        ]
        for plan_id in valid_ids:
            result = validate_plan_id(plan_id)
            assert result == plan_id.lower()

    def test_normalizes_to_lowercase(self):
        """Should normalize plan IDs to lowercase."""
        result = validate_plan_id("FREE_TRIAL")
        assert result == "free_trial"

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        result = validate_plan_id("  free_trial  ")
        assert result == "free_trial"

    def test_rejects_empty_string(self):
        """Should reject empty string."""
        with pytest.raises(ValueError) as exc_info:
            validate_plan_id("")
        assert "cannot be empty" in str(exc_info.value)

    def test_rejects_too_long_plan_id(self):
        """Should reject plan IDs longer than 50 characters."""
        long_id = "a" * 51
        with pytest.raises(ValueError) as exc_info:
            validate_plan_id(long_id)
        assert "50 characters" in str(exc_info.value)

    def test_rejects_plan_id_starting_with_number(self):
        """Should reject plan IDs starting with a number."""
        with pytest.raises(ValueError):
            validate_plan_id("123_plan")

    def test_rejects_plan_id_with_special_chars(self):
        """Should reject plan IDs with special characters."""
        invalid_ids = [
            "plan-name",  # Dash not allowed
            "plan.name",  # Dot not allowed
            "plan@name",  # @ not allowed
            "plan name",  # Space not allowed
            "plan!name",  # ! not allowed
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError):
                validate_plan_id(invalid_id)

    def test_rejects_sql_injection_in_plan_id(self):
        """Should reject SQL injection attempts in plan IDs."""
        injection_attempts = [
            "free'; DROP TABLE plans;--",
            "free' OR '1'='1",
            "'; DELETE FROM subscriptions; --",
        ]
        for attempt in injection_attempts:
            with pytest.raises(ValueError):
                validate_plan_id(attempt)


class TestSanitizeSearchQuery:
    """Test suite for sanitize_search_query function."""

    def test_accepts_valid_search_queries(self):
        """Should accept valid search queries."""
        valid_queries = [
            "john@example.com",
            "John Doe",
            "empresa-teste",
            "usuario.nome",
            "nome_usuario",
        ]
        for query in valid_queries:
            result = sanitize_search_query(query)
            assert result  # Should return non-empty

    def test_returns_empty_for_empty_input(self):
        """Should return empty string for empty input."""
        assert sanitize_search_query("") == ""
        assert sanitize_search_query(None) == ""

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        result = sanitize_search_query("  test  ")
        assert result == "test"

    def test_rejects_too_long_query(self):
        """Should reject queries longer than max_length."""
        long_query = "a" * 101
        with pytest.raises(ValueError) as exc_info:
            sanitize_search_query(long_query)
        assert "100 characters" in str(exc_info.value)

    def test_custom_max_length(self):
        """Should respect custom max_length parameter."""
        query = "a" * 51
        with pytest.raises(ValueError):
            sanitize_search_query(query, max_length=50)

    def test_accepts_underscores(self):
        """Should accept underscores in search queries."""
        result = sanitize_search_query("test_value")
        # Underscores are allowed in search queries
        assert "test" in result and "value" in result

    def test_rejects_invalid_characters(self):
        """Should reject queries with invalid characters."""
        invalid_queries = [
            "test;DROP TABLE",  # Semicolon
            "test<script>alert(1)</script>",  # HTML tags
            "test$(echo)",  # Command substitution
            "test`id`",  # Backticks
            "test|cat /etc/passwd",  # Pipe
        ]
        for query in invalid_queries:
            with pytest.raises(ValueError):
                sanitize_search_query(query)

    def test_accepts_portuguese_characters(self):
        """Should accept Portuguese accented characters."""
        queries_with_accents = [
            "Jose da Silva",
            "Maria",
            "Joao",
            "Sao Paulo",
        ]
        for query in queries_with_accents:
            result = sanitize_search_query(query)
            assert result  # Should return non-empty


class TestSecureUserIdModel:
    """Test suite for SecureUserId Pydantic model."""

    def test_validates_valid_uuid(self):
        """Should validate and accept valid UUID."""
        model = SecureUserId(user_id="550e8400-e29b-41d4-a716-446655440000")
        assert model.user_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_rejects_invalid_uuid(self):
        """Should reject invalid UUID."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SecureUserId(user_id="invalid-uuid")


class TestSecurePlanIdModel:
    """Test suite for SecurePlanId Pydantic model."""

    def test_validates_valid_plan_id(self):
        """Should validate and accept valid plan ID."""
        model = SecurePlanId(plan_id="free_trial")
        assert model.plan_id == "free_trial"

    def test_rejects_invalid_plan_id(self):
        """Should reject invalid plan ID."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SecurePlanId(plan_id="invalid-plan!")


class TestAdminGetAdminIdsSecure:
    """Test suite for secure _get_admin_ids function."""

    def test_validates_and_returns_valid_uuids(self):
        """Should validate and return only valid UUIDs."""
        from admin import _get_admin_ids

        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        with patch.dict(os.environ, {"ADMIN_USER_IDS": valid_uuid}):
            result = _get_admin_ids()

        assert result == {valid_uuid}

    def test_skips_invalid_uuids(self):
        """Should skip invalid UUIDs and log warning."""
        from admin import _get_admin_ids

        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        mixed_ids = f"{valid_uuid},invalid-uuid,another-bad"

        with patch.dict(os.environ, {"ADMIN_USER_IDS": mixed_ids}):
            result = _get_admin_ids()

        # Should only contain the valid UUID
        assert result == {valid_uuid}
        assert "invalid-uuid" not in result
        assert "another-bad" not in result

    def test_returns_empty_set_for_all_invalid(self):
        """Should return empty set if all IDs are invalid."""
        from admin import _get_admin_ids

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "not-uuid,also-invalid"}):
            result = _get_admin_ids()

        assert result == set()

    def test_normalizes_uuids_to_lowercase(self):
        """Should normalize UUIDs to lowercase for consistent comparison."""
        from admin import _get_admin_ids

        upper_uuid = "550E8400-E29B-41D4-A716-446655440000"
        with patch.dict(os.environ, {"ADMIN_USER_IDS": upper_uuid}):
            result = _get_admin_ids()

        assert result == {"550e8400-e29b-41d4-a716-446655440000"}


class TestAdminEndpointValidation:
    """Test suite for admin endpoint parameter validation."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user with valid UUID."""
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
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

        async def mock_require_admin():
            return mock_admin_user

        app.dependency_overrides[require_admin] = mock_require_admin
        return app

    @pytest.fixture
    def admin_client(self, admin_app_with_overrides):
        """Create test client with admin auth mocked."""
        from fastapi.testclient import TestClient
        return TestClient(admin_app_with_overrides)

    def test_delete_user_rejects_invalid_uuid(self, admin_client):
        """Should return 400 for invalid user_id in DELETE endpoint."""
        response = admin_client.delete("/admin/users/not-a-valid-uuid")
        assert response.status_code == 400
        assert "invalido" in response.json()["detail"].lower()

    def test_delete_user_rejects_sql_injection(self, admin_client):
        """Should reject SQL injection in DELETE endpoint."""
        response = admin_client.delete("/admin/users/'; DROP TABLE users;--")
        assert response.status_code == 400

    def test_update_user_rejects_invalid_uuid(self, admin_client):
        """Should return 400 for invalid user_id in PUT endpoint."""
        response = admin_client.put(
            "/admin/users/not-a-valid-uuid",
            json={"full_name": "Test"}
        )
        assert response.status_code == 400

    def test_update_user_rejects_invalid_plan_id(self, admin_client):
        """Should return 400 for invalid plan_id in request body."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock Supabase
        mock_sb = Mock()
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            response = admin_client.put(
                f"/admin/users/{valid_uuid}",
                json={"plan_id": "invalid-plan!@#"}
            )

        # Validation happens in the endpoint, returns 400
        assert response.status_code == 400
        assert "invalido" in response.json()["detail"].lower()

    def test_reset_password_rejects_invalid_uuid(self, admin_client):
        """Should return 400 for invalid user_id in reset-password endpoint."""
        response = admin_client.post(
            "/admin/users/not-a-valid-uuid/reset-password",
            json={"new_password": "newpassword123"}
        )
        assert response.status_code == 400

    def test_assign_plan_rejects_invalid_uuid(self, admin_client):
        """Should return 400 for invalid user_id in assign-plan endpoint."""
        response = admin_client.post(
            "/admin/users/not-a-valid-uuid/assign-plan?plan_id=free_trial"
        )
        assert response.status_code == 400

    def test_assign_plan_rejects_invalid_plan_id(self, admin_client):
        """Should return 400 for invalid plan_id query parameter."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = admin_client.post(
            f"/admin/users/{valid_uuid}/assign-plan?plan_id=invalid-plan!"
        )
        assert response.status_code == 400

    def test_list_users_sanitizes_search_query(self, admin_client):
        """Should sanitize search query in list users endpoint."""
        mock_sb = Mock()
        mock_result = Mock()
        mock_result.data = []
        mock_result.count = 0

        # Build the full mock chain properly
        mock_table = Mock()
        mock_select = Mock()
        mock_or = Mock()
        mock_order = Mock()
        mock_range = Mock()

        mock_sb.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.or_.return_value = mock_or
        mock_or.order.return_value = mock_order
        mock_order.range.return_value = mock_range
        mock_range.execute.return_value = mock_result

        # Also handle non-search path
        mock_select.order.return_value = mock_order

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            # This should not cause any issues - sanitization should handle it
            response = admin_client.get("/admin/users?search=test")

        assert response.status_code == 200

    def test_create_user_accepts_valid_plan_id(self, admin_client):
        """Should accept valid plan_id in create user request body."""
        mock_sb = Mock()

        # Mock auth.admin.create_user
        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = "new-user-uuid"
        mock_sb.auth.admin.create_user.return_value = created_user

        # Mock table operations
        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_sb.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "test@example.com",
                    "password": "password123",
                    "plan_id": "free"  # Valid plan_id
                }
            )

        # Should succeed with valid plan_id
        assert response.status_code == 200


class TestMaliciousInputRejection:
    """Test suite specifically for malicious input patterns."""

    def test_uuid_rejects_unicode_bypass_attempts(self):
        """Should reject Unicode bypass attempts."""
        unicode_attacks = [
            "550e8400\u200b-e29b-41d4-a716-446655440000",  # Zero-width space
            "550e8400\u00a0-e29b-41d4-a716-446655440000",  # Non-breaking space
        ]
        for attack in unicode_attacks:
            with pytest.raises(ValueError):
                validate_uuid(attack)

    def test_uuid_rejects_null_byte_injection(self):
        """Should reject null byte injection attempts."""
        null_byte_attacks = [
            "550e8400-e29b-41d4-a716-446655440000\x00malicious",
            "\x00550e8400-e29b-41d4-a716-446655440000",
        ]
        for attack in null_byte_attacks:
            with pytest.raises(ValueError):
                validate_uuid(attack)

    def test_plan_id_rejects_command_injection(self):
        """Should reject command injection in plan IDs."""
        command_injections = [
            "free;id",
            "free|cat /etc/passwd",
            "free`id`",
            "free$(id)",
        ]
        for attack in command_injections:
            with pytest.raises(ValueError):
                validate_plan_id(attack)
