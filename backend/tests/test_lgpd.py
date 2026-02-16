"""Comprehensive tests for STORY-213 LGPD compliance endpoints.

Tests cover:
- DELETE /me - Account deletion endpoint (AC26, AC28)
- GET /me/export - Data export endpoint (AC27)
"""

from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from auth import require_auth
from database import get_db


client = TestClient(app)


def override_require_auth(user_id: str = "test-user-123"):
    """Create a dependency override for require_auth."""
    async def _override():
        return {"id": user_id, "email": "test@example.com"}
    return _override


def setup_auth_override(user_id="test-user-123"):
    """Setup auth override and return cleanup function."""
    app.dependency_overrides[require_auth] = override_require_auth(user_id)
    def cleanup():
        app.dependency_overrides.clear()
    return cleanup


class TestDeleteAccountEndpoint:
    """Test DELETE /me endpoint (AC26, AC28) - Account deletion."""

    @patch("stripe.Subscription.cancel")
    def test_successful_account_deletion_with_stripe_subscription(
        self, mock_stripe_cancel
    ):
        """Should delete account successfully and cancel Stripe subscription."""
        cleanup = setup_auth_override("user-with-subscription")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock Stripe subscription check
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.execute.return_value = Mock(
                data=[{"stripe_subscription_id": "sub_test123", "is_active": True}]
            )

            # Mock table deletions
            mock_sb.delete.return_value = mock_sb

            # Mock auth user deletion
            mock_sb.auth.admin.delete_user = Mock()

            response = client.delete("/me")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Conta excluída com sucesso."

            # Verify Stripe subscription was cancelled
            mock_stripe_cancel.assert_called_once_with("sub_test123")

            # Verify all tables were deleted from
            expected_tables = [
                "search_sessions",
                "monthly_quota",
                "user_subscriptions",
                "user_oauth_tokens",
                "messages",
                "profiles"
            ]
            # Check that table() was called for each expected table
            table_calls = [call[0][0] for call in mock_sb.table.call_args_list]
            for table in expected_tables:
                assert table in table_calls

            # Verify auth user was deleted
            mock_sb.auth.admin.delete_user.assert_called_once_with("user-with-subscription")

        finally:
            cleanup()

    def test_successful_account_deletion_without_stripe_subscription(
        self
    ):
        """Should delete account successfully when no Stripe subscription exists."""
        cleanup = setup_auth_override("user-without-subscription")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock empty Stripe subscription check
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])

            # Mock table deletions
            mock_sb.delete.return_value = mock_sb

            # Mock auth user deletion
            mock_sb.auth.admin.delete_user = Mock()

            response = client.delete("/me")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Conta excluída com sucesso."

            # Verify auth user was deleted
            mock_sb.auth.admin.delete_user.assert_called_once_with("user-without-subscription")

        finally:
            cleanup()

    @patch("stripe.Subscription.cancel")
    def test_continues_deletion_if_stripe_cancel_fails(
        self, mock_stripe_cancel
    ):
        """Should continue account deletion even if Stripe cancellation fails."""
        cleanup = setup_auth_override("user-stripe-error")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock Stripe subscription check
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.execute.return_value = Mock(
                data=[{"stripe_subscription_id": "sub_invalid", "is_active": True}]
            )

            # Mock Stripe cancel failure
            import stripe as stripe_lib
            mock_stripe_cancel.side_effect = stripe_lib.InvalidRequestError(
                message="Subscription not found",
                param="subscription"
            )

            # Mock table deletions
            mock_sb.delete.return_value = mock_sb

            # Mock auth user deletion
            mock_sb.auth.admin.delete_user = Mock()

            response = client.delete("/me")

            # Should still succeed
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify deletion continued despite Stripe error
            mock_sb.auth.admin.delete_user.assert_called_once()

        finally:
            cleanup()

    def test_deletion_fails_with_500_on_search_sessions_error(
        self
    ):
        """Should return 500 if deletion from search_sessions fails."""
        cleanup = setup_auth_override("user-db-error")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock empty subscription check
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb

            # First execute is for subscription check (empty)
            # Subsequent executes fail
            mock_sb.execute.side_effect = [
                Mock(data=[]),  # Empty subscription check
                Exception("Database connection lost")  # First table deletion fails
            ]

            mock_sb.delete.return_value = mock_sb

            response = client.delete("/me")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "search_sessions" in data["detail"]

        finally:
            cleanup()

    def test_deletion_fails_with_500_on_profile_error(
        self
    ):
        """Should return 500 if profile deletion fails."""
        cleanup = setup_auth_override("user-profile-error")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock table operations
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.delete.return_value = mock_sb

            # Subscription check succeeds (empty), first 5 table deletions succeed,
            # but profile deletion (6th table) fails
            mock_sb.execute.side_effect = [
                Mock(data=[]),  # Subscription check
                Mock(data=[]),  # search_sessions
                Mock(data=[]),  # monthly_quota
                Mock(data=[]),  # user_subscriptions
                Mock(data=[]),  # user_oauth_tokens
                Mock(data=[]),  # messages
                Exception("Profile deletion failed")  # profiles
            ]

            response = client.delete("/me")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "perfil" in data["detail"]  # Portuguese error message

        finally:
            cleanup()

    def test_deletion_fails_with_500_on_auth_user_error(
        self
    ):
        """Should return 500 if auth user deletion fails."""
        cleanup = setup_auth_override("user-auth-error")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock table operations
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.delete.return_value = mock_sb

            # All table deletions succeed
            mock_sb.execute.return_value = Mock(data=[])

            # Auth user deletion fails
            mock_sb.auth.admin.delete_user.side_effect = Exception("Auth API error")

            response = client.delete("/me")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "autenticação" in data["detail"]  # Portuguese error message

        finally:
            cleanup()

    def test_unauthorized_deletion_without_auth(self):
        """Should return 401/403 when no authentication provided."""
        # No auth override
        response = client.delete("/me")

        # Should be unauthorized
        assert response.status_code in [401, 403]

    @patch("stripe.Subscription.cancel")
    def test_deletion_cascades_all_user_data(
        self, mock_stripe_cancel
    ):
        """Should cascade delete from ALL expected tables."""
        cleanup = setup_auth_override("user-cascade-test")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock operations
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.delete.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])
            mock_sb.auth.admin.delete_user = Mock()

            response = client.delete("/me")

            assert response.status_code == 200

            # Verify cascade order and tables
            table_calls = [call[0][0] for call in mock_sb.table.call_args_list]

            # Check all expected tables are present
            expected_in_order = [
                "user_subscriptions",  # For Stripe check
                "search_sessions",
                "monthly_quota",
                "user_subscriptions",
                "user_oauth_tokens",
                "messages",
                "profiles"
            ]

            for table in expected_in_order:
                assert table in table_calls, f"Table {table} should be deleted"

        finally:
            cleanup()


class TestExportUserDataEndpoint:
    """Test GET /me/export endpoint (AC27) - Data portability."""

    def test_successful_data_export_with_all_data(
        self
    ):
        """Should export all user data in JSON format."""
        cleanup = setup_auth_override("user-full-data")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock table operations
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb

            # Mock data for each table
            profile_data = {
                "id": "user-full-data",
                "email": "test@example.com",
                "plan_type": "consultor_agil"
            }

            search_sessions_data = [
                {
                    "id": "session1",
                    "user_id": "user-full-data",
                    "created_at": "2026-02-01T10:00:00Z"
                }
            ]

            subscriptions_data = [
                {
                    "id": "sub1",
                    "user_id": "user-full-data",
                    "plan_type": "consultor_agil"
                }
            ]

            messages_data = [
                {
                    "id": "msg1",
                    "user_id": "user-full-data",
                    "content": "Test message"
                }
            ]

            quota_data = [
                {
                    "id": "quota1",
                    "user_id": "user-full-data",
                    "requests_this_month": 10
                }
            ]

            # Return different data for each table
            mock_sb.execute.side_effect = [
                Mock(data=[profile_data]),        # profiles
                Mock(data=search_sessions_data),  # search_sessions
                Mock(data=subscriptions_data),    # user_subscriptions
                Mock(data=messages_data),         # messages
                Mock(data=quota_data)             # monthly_quota
            ]

            response = client.get("/me/export")

            assert response.status_code == 200

            # Check Content-Disposition header
            assert "Content-Disposition" in response.headers
            assert "attachment" in response.headers["Content-Disposition"]
            assert "smartlic_dados_" in response.headers["Content-Disposition"]
            assert ".json" in response.headers["Content-Disposition"]

            # Check JSON content
            data = response.json()
            assert "exported_at" in data
            assert data["user_id"] == "user-full-data"
            assert data["profile"] == profile_data
            assert data["search_history"] == search_sessions_data
            assert data["subscriptions"] == subscriptions_data
            assert data["messages"] == messages_data
            assert data["quota_history"] == quota_data

        finally:
            cleanup()

    def test_export_filename_format(
        self
    ):
        """Should generate filename in format: smartlic_dados_{prefix}_{date}.json"""
        cleanup = setup_auth_override("user-filename-test")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock all table queries to return empty data
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])

            response = client.get("/me/export")

            assert response.status_code == 200

            # Check filename format
            content_disposition = response.headers["Content-Disposition"]
            assert 'filename="smartlic_dados_user-fil_' in content_disposition
            assert '.json"' in content_disposition

            # Verify date format (YYYY-MM-DD)
            import re
            match = re.search(r'smartlic_dados_[\w-]+_(\d{4}-\d{2}-\d{2})\.json', content_disposition)
            assert match is not None, "Filename should contain date in YYYY-MM-DD format"

        finally:
            cleanup()

    def test_export_with_empty_data(
        self
    ):
        """Should handle export when user has no data in tables."""
        cleanup = setup_auth_override("user-empty-data")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock all table queries to return empty data
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])

            response = client.get("/me/export")

            assert response.status_code == 200

            data = response.json()
            assert data["user_id"] == "user-empty-data"
            assert data["profile"] is None
            assert data["search_history"] == []
            assert data["subscriptions"] == []
            assert data["messages"] == []
            assert data["quota_history"] == []

        finally:
            cleanup()

    def test_export_handles_partial_table_failures(
        self
    ):
        """Should include empty arrays for tables that fail to load."""
        cleanup = setup_auth_override("user-partial-fail")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock table operations
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb

            # Profile succeeds, search_sessions fails, rest succeed
            mock_sb.execute.side_effect = [
                Mock(data=[{"id": "user-partial-fail"}]),  # profiles
                Exception("Database timeout"),              # search_sessions
                Mock(data=[]),                              # user_subscriptions
                Mock(data=[]),                              # messages
                Mock(data=[])                               # monthly_quota
            ]

            response = client.get("/me/export")

            assert response.status_code == 200

            data = response.json()
            assert data["profile"] is not None
            assert data["search_history"] == []  # Failed, should be empty array
            assert data["subscriptions"] == []
            assert data["messages"] == []
            assert data["quota_history"] == []

        finally:
            cleanup()

    def test_export_includes_all_expected_tables(
        self
    ):
        """Should query all expected tables: profile, search_sessions, subscriptions, messages, quota."""
        cleanup = setup_auth_override("user-table-check")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock operations
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])

            response = client.get("/me/export")

            assert response.status_code == 200

            # Check which tables were queried
            table_calls = [call[0][0] for call in mock_sb.table.call_args_list]

            expected_tables = [
                "profiles",
                "search_sessions",
                "user_subscriptions",
                "messages",
                "monthly_quota"
            ]

            for table in expected_tables:
                assert table in table_calls, f"Should query {table}"

        finally:
            cleanup()

    def test_export_response_has_correct_media_type(
        self
    ):
        """Should return application/json media type."""
        cleanup = setup_auth_override("user-media-type")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock all queries
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])

            response = client.get("/me/export")

            assert response.status_code == 200
            assert response.headers["Content-Type"] == "application/json"

        finally:
            cleanup()

    def test_unauthorized_export_without_auth(self):
        """Should return 401/403 when no authentication provided."""
        # No auth override
        response = client.get("/me/export")

        # Should be unauthorized
        assert response.status_code in [401, 403]

    def test_export_data_includes_timestamp(
        self
    ):
        """Should include exported_at timestamp in ISO format."""
        cleanup = setup_auth_override("user-timestamp")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock all queries
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])

            response = client.get("/me/export")

            assert response.status_code == 200

            data = response.json()
            assert "exported_at" in data

            # Verify it's a valid ISO timestamp
            exported_at = datetime.fromisoformat(data["exported_at"].replace("Z", "+00:00"))
            assert isinstance(exported_at, datetime)

        finally:
            cleanup()

    def test_export_search_history_ordered_by_created_at_desc(
        self
    ):
        """Should order search history, subscriptions, and messages by created_at descending."""
        cleanup = setup_auth_override("user-order-test")
        try:
            # Mock Supabase client
            mock_sb = MagicMock()
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock operations
            mock_sb.table.return_value = mock_sb
            mock_sb.select.return_value = mock_sb
            mock_sb.eq.return_value = mock_sb
            mock_sb.order.return_value = mock_sb
            mock_sb.execute.return_value = Mock(data=[])

            response = client.get("/me/export")

            assert response.status_code == 200

            # Check that order() was called with correct parameters
            order_calls = [call for call in mock_sb.order.call_args_list]

            # Should be called for search_sessions, user_subscriptions, messages (3 tables)
            # monthly_quota does NOT have order() in implementation
            assert len(order_calls) == 3

            # Each should order by created_at, desc=True
            for call in order_calls:
                args, kwargs = call
                assert args[0] == "created_at"
                assert kwargs.get("desc") is True

        finally:
            cleanup()
