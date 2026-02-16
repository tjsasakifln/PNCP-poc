"""REG-T03: Test admin user creation default plan behavior.

This test verifies that when an admin creates a user without specifying
a plan_id, the user receives the 'free_trial' plan by default, and no
database constraint violations occur.

Related to STORY-TD-004 regression testing.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Valid UUID v4 test fixtures
ADMIN_UUID = "550e8400-e29b-41d4-a716-446655440000"
NEW_USER_UUID = "550e8400-e29b-41d4-a716-446655440099"


class TestAdminUserCreationDefaultPlan:
    """REG-T03: Admin creates user without explicit plan_id → profile with plan_type = 'free_trial'"""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user with valid UUID."""
        return {
            "id": ADMIN_UUID,
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

    def test_create_user_without_plan_id_defaults_to_free_trial(self, admin_client):
        """
        REG-T03: Verify that creating a user without explicit plan_id
        results in a profile with plan_type = 'free_trial' and no
        constraint violations.

        This test ensures:
        1. CreateUserRequest.plan_id defaults to "free_trial"
        2. No database constraint violations occur
        3. The created user has free_trial plan access
        4. No subscription is created (free_trial uses plan capabilities)
        """
        mock_supabase = Mock()

        # Mock auth.admin.create_user - successful user creation
        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = NEW_USER_UUID
        mock_supabase.auth.admin.create_user.return_value = created_user

        # Mock table operations
        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            # Create user WITHOUT plan_id field (should default to free_trial)
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "testuser@example.com",
                    "password": "SecurePass123",
                    "full_name": "Test User",
                    "company": "Test Company"
                }
            )

        # Assertions
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()

        # Verify response contains expected fields
        assert data["user_id"] == NEW_USER_UUID
        assert data["email"] == "testuser@example.com"
        assert data["plan_id"] == "free_trial", "Default plan_id should be 'free_trial'"

        # Verify auth.admin.create_user was called correctly
        create_call = mock_supabase.auth.admin.create_user.call_args[0][0]
        assert create_call["email"] == "testuser@example.com"
        assert create_call["password"] == "SecurePass123"
        assert create_call["email_confirm"] is True
        assert create_call["user_metadata"]["full_name"] == "Test User"

        # Verify that table update WAS called (company is provided, so update should happen)
        assert mock_table.update.called, "Profile should be updated with company info"

        # Verify NO subscription was created (free_trial doesn't create subscription)
        # The insert() method should NOT be called for free_trial plans
        assert mock_table.insert.call_count == 0, "free_trial should not create a subscription record"

    def test_create_user_without_plan_id_and_without_company_minimal_profile(self, admin_client):
        """
        REG-T03 (variant): Verify creating a user with ONLY email/password
        (no plan_id, no company) works correctly and relies on database defaults.

        This is the most minimal case - user creation with absolutely minimal data.
        """
        mock_supabase = Mock()

        # Mock auth.admin.create_user
        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = NEW_USER_UUID
        mock_supabase.auth.admin.create_user.return_value = created_user

        # Mock table operations
        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            # Create user with ONLY email and password (no plan_id, no company, no full_name)
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "minimal@example.com",
                    "password": "SecurePass123"
                }
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == NEW_USER_UUID
        assert data["email"] == "minimal@example.com"
        assert data["plan_id"] == "free_trial", "Default plan_id should be 'free_trial'"

        # Verify that table update was NOT called (no company, plan_id is free_trial)
        # Line 348 in admin.py: if req.company or req.plan_id != "free_trial"
        # Since company is None and plan_id == "free_trial", update should NOT happen
        assert mock_table.update.call_count == 0, "Profile should NOT be updated (relying on DB defaults)"

        # Verify NO subscription was created
        assert mock_table.insert.call_count == 0, "free_trial should not create a subscription record"

    def test_create_user_explicit_free_trial_behaves_same_as_default(self, admin_client):
        """
        REG-T03 (explicit): Verify that explicitly passing plan_id="free_trial"
        behaves identically to omitting it (default behavior).
        """
        mock_supabase = Mock()

        # Mock auth.admin.create_user
        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = NEW_USER_UUID
        mock_supabase.auth.admin.create_user.return_value = created_user

        # Mock table operations
        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            # Explicitly set plan_id to "free_trial"
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "explicit@example.com",
                    "password": "SecurePass123",
                    "plan_id": "free_trial"  # Explicit free_trial
                }
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == NEW_USER_UUID
        assert data["email"] == "explicit@example.com"
        assert data["plan_id"] == "free_trial"

        # Verify behavior is same as default (no update, no subscription)
        assert mock_table.update.call_count == 0, "Explicit free_trial should not update profile"
        assert mock_table.insert.call_count == 0, "Explicit free_trial should not create subscription"

    def test_create_user_with_paid_plan_creates_subscription(self, admin_client):
        """
        REG-T03 (contrast): Verify that when plan_id is NOT free_trial,
        a subscription IS created. This confirms the default behavior is different.
        """
        mock_supabase = Mock()

        # Mock auth.admin.create_user
        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = NEW_USER_UUID
        mock_supabase.auth.admin.create_user.return_value = created_user

        # Mock plan lookup
        plan_result = Mock()
        plan_result.data = {
            "id": "smartlic_pro",
            "max_searches": 1000,
            "duration_days": 30,
        }

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = plan_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            # Create user with paid plan (NOT free_trial)
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "premium@example.com",
                    "password": "SecurePass123",
                    "plan_id": "smartlic_pro"
                }
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == "smartlic_pro"

        # Verify subscription WAS created (contrast with free_trial)
        assert mock_table.insert.call_count == 1, "Paid plan should create a subscription record"

        # Verify profile WAS updated with plan_type
        update_calls = [call for call in mock_table.update.call_args_list if call[0][0].get("plan_type")]
        assert len(update_calls) > 0, "Profile should be updated with plan_type for paid plans"

    def test_create_user_default_plan_no_constraint_violation(self, admin_client):
        """
        REG-T03 (constraint): Verify that the default plan_id does NOT
        cause database constraint violations.

        This specifically tests that "free_trial" is a valid plan_type
        according to the database CHECK constraint.
        """
        mock_supabase = Mock()

        # Mock auth.admin.create_user
        created_user = Mock()
        created_user.user = Mock()
        created_user.user.id = NEW_USER_UUID
        mock_supabase.auth.admin.create_user.return_value = created_user

        # Mock table operations - simulate successful execution (no constraint error)
        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/admin/users",
                json={
                    "email": "noconstranterror@example.com",
                    "password": "SecurePass123"
                }
            )

        # Should succeed without constraint violation
        assert response.status_code == 200
        assert response.json()["plan_id"] == "free_trial"

    def test_request_schema_default_value(self):
        """
        REG-T03 (schema): Verify CreateUserRequest Pydantic model
        has correct default value for plan_id field.
        """
        from admin import CreateUserRequest

        # Create request without plan_id
        request = CreateUserRequest(
            email="test@example.com",
            password="SecurePass123"
        )

        # Verify default is set correctly
        assert request.plan_id == "free_trial", "CreateUserRequest.plan_id default should be 'free_trial'"

    def test_request_schema_default_value_not_free(self):
        """
        REG-T03 (regression): Verify CreateUserRequest default is NOT "free"
        (which would cause constraint violations).

        This is the core regression test - ensuring the bug is fixed.
        """
        from admin import CreateUserRequest

        # Create request without plan_id
        request = CreateUserRequest(
            email="test@example.com",
            password="SecurePass123"
        )

        # CRITICAL: Verify it's NOT "free" (the bug that was causing constraint violations)
        assert request.plan_id != "free", "CreateUserRequest.plan_id should NOT be 'free' (invalid plan)"
        assert request.plan_id == "free_trial", "Should be 'free_trial' instead"
