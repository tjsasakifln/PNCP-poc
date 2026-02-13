"""Tests for routes.messages — InMail messaging endpoints.

STORY-224 Track 4 (AC24): Message/conversation route coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from admin import require_admin
from routes.messages import router


MOCK_USER = {"id": "user-123-uuid", "email": "test@example.com", "role": "authenticated"}
MOCK_ADMIN = {"id": "admin-999-uuid", "email": "admin@example.com", "role": "authenticated"}
CONV_ID = "a1b2c3d4-e5f6-4890-abcd-ef1234567890"


def _create_client(user=None, admin_user=None):
    """Create test client with auth overrides.

    Args:
        user: User dict for require_auth override (defaults to MOCK_USER).
        admin_user: If set, also override require_admin with this user dict.
    """
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: (user or MOCK_USER)
    if admin_user is not None:
        app.dependency_overrides[require_admin] = lambda: admin_user
    return TestClient(app)


def _mock_sb():
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.update.return_value = sb
    sb.eq.return_value = sb
    sb.in_.return_value = sb
    sb.order.return_value = sb
    sb.range.return_value = sb
    sb.limit.return_value = sb
    sb.single.return_value = sb
    result = Mock(data=[], count=0)
    sb.execute.return_value = result
    # RPC chain
    rpc_mock = Mock()
    rpc_mock.execute.return_value = Mock(data=[])
    sb.rpc.return_value = rpc_mock
    return sb


# ============================================================================
# POST /api/messages/conversations — create conversation
# ============================================================================

class TestCreateConversation:

    @patch("routes.messages._get_sb")
    def test_create_conversation_success(self, mock_get_sb):
        sb = _mock_sb()
        # First execute: insert conversation
        conv_data = {"id": CONV_ID, "status": "aberto"}
        # Second execute: insert message
        sb.execute.side_effect = [
            Mock(data=[conv_data]),  # conv insert
            Mock(data=[{"id": "msg-1"}]),  # msg insert
        ]
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/api/messages/conversations", json={
            "subject": "Help with search",
            "category": "suporte",
            "body": "I need help finding procurements in SP.",
        })

        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == CONV_ID
        assert body["status"] == "aberto"

    @patch("routes.messages._get_sb")
    def test_create_conversation_db_failure(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])  # No data = failure
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/api/messages/conversations", json={
            "subject": "Help",
            "category": "suporte",
            "body": "Problem description",
        })

        assert resp.status_code == 500

    def test_create_conversation_missing_fields(self):
        client = _create_client()
        resp = client.post("/api/messages/conversations", json={})
        assert resp.status_code == 422


# ============================================================================
# GET /api/messages/conversations — list conversations
# ============================================================================

class TestListConversations:

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_list_conversations_empty(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        rpc_mock = Mock()
        rpc_mock.execute.return_value = Mock(data=[])
        sb.rpc.return_value = rpc_mock
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/api/messages/conversations")

        assert resp.status_code == 200
        body = resp.json()
        assert body["conversations"] == []
        assert body["total"] == 0

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_list_conversations_with_data(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        rpc_row = {
            "id": CONV_ID,
            "user_id": "user-123-uuid",
            "user_email": None,
            "subject": "Test",
            "category": "suporte",
            "status": "aberto",
            "last_message_at": "2026-02-01T10:00:00+00:00",
            "created_at": "2026-02-01T09:00:00+00:00",
            "unread_count": 2,
            "total_count": 1,
        }
        rpc_mock = Mock()
        rpc_mock.execute.return_value = Mock(data=[rpc_row])
        sb.rpc.return_value = rpc_mock
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/api/messages/conversations")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["conversations"]) == 1
        assert body["conversations"][0]["id"] == CONV_ID
        assert body["total"] == 1

    @patch("routes.messages._is_admin", return_value=True)
    @patch("routes.messages._get_sb")
    def test_list_conversations_admin_sees_email(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        rpc_row = {
            "id": CONV_ID,
            "user_id": "user-123-uuid",
            "user_email": "test@example.com",
            "subject": "Test",
            "category": "suporte",
            "status": "aberto",
            "last_message_at": "2026-02-01T10:00:00+00:00",
            "created_at": "2026-02-01T09:00:00+00:00",
            "unread_count": 0,
            "total_count": 1,
        }
        rpc_mock = Mock()
        rpc_mock.execute.return_value = Mock(data=[rpc_row])
        sb.rpc.return_value = rpc_mock
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/api/messages/conversations")

        assert resp.status_code == 200
        assert resp.json()["conversations"][0]["user_email"] == "test@example.com"


# ============================================================================
# GET /api/messages/conversations/{id} — get conversation thread
# ============================================================================

class TestGetConversation:

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_get_conversation_success(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        conv_data = {
            "id": CONV_ID,
            "user_id": "user-123-uuid",
            "subject": "Help",
            "category": "suporte",
            "status": "aberto",
            "last_message_at": "2026-02-01T10:00:00+00:00",
            "created_at": "2026-02-01T09:00:00+00:00",
            "profiles": {"email": "test@example.com"},
        }
        msg_data = [
            {
                "id": "msg-1",
                "sender_id": "user-123-uuid",
                "body": "Hello",
                "is_admin_reply": False,
                "read_by_user": True,
                "read_by_admin": False,
                "created_at": "2026-02-01T09:00:00+00:00",
                "profiles": {"email": "test@example.com"},
            },
        ]
        # Chain: conv select -> single -> execute, msgs select -> order -> execute, update -> execute
        sb.execute.side_effect = [
            Mock(data=conv_data),   # conv fetch (single)
            Mock(data=msg_data),    # messages fetch
            Mock(data=[]),          # mark read update
        ]
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get(f"/api/messages/conversations/{CONV_ID}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == CONV_ID
        assert len(body["messages"]) == 1
        assert body["messages"][0]["body"] == "Hello"

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_get_conversation_not_found(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=None)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get(f"/api/messages/conversations/{CONV_ID}")

        assert resp.status_code == 404

    def test_get_conversation_invalid_uuid(self):
        client = _create_client()
        resp = client.get("/api/messages/conversations/not-a-uuid")
        assert resp.status_code == 400

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_get_conversation_access_denied(self, mock_get_sb, mock_is_admin):
        """Non-admin user cannot view another user's conversation."""
        sb = _mock_sb()
        conv_data = {
            "id": CONV_ID,
            "user_id": "other-user-uuid",  # Different user
            "subject": "Private",
            "category": "suporte",
            "status": "aberto",
            "last_message_at": "2026-02-01T10:00:00+00:00",
            "created_at": "2026-02-01T09:00:00+00:00",
            "profiles": {},
        }
        sb.execute.return_value = Mock(data=conv_data)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get(f"/api/messages/conversations/{CONV_ID}")

        assert resp.status_code == 403


# ============================================================================
# POST /api/messages/conversations/{id}/reply
# ============================================================================

class TestReplyToConversation:

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_user_reply_success(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        conv_data = {
            "id": CONV_ID,
            "user_id": "user-123-uuid",
            "status": "respondido",
        }
        sb.execute.side_effect = [
            Mock(data=conv_data),   # conv fetch
            Mock(data=[{"id": "msg-new"}]),  # msg insert
            Mock(data=[]),          # status update
        ]
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post(f"/api/messages/conversations/{CONV_ID}/reply", json={
            "body": "Thanks for your help!",
        })

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "aberto"  # User reply sets status to "aberto"

    @patch("routes.messages._is_admin", return_value=True)
    @patch("routes.messages._get_sb")
    def test_admin_reply_sets_respondido(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        conv_data = {
            "id": CONV_ID,
            "user_id": "user-123-uuid",
            "status": "aberto",
        }
        sb.execute.side_effect = [
            Mock(data=conv_data),   # conv fetch
            Mock(data=[{"id": "msg-new"}]),  # msg insert
            Mock(data=[]),          # status update
        ]
        mock_get_sb.return_value = sb
        client = _create_client(user=MOCK_ADMIN)

        resp = client.post(f"/api/messages/conversations/{CONV_ID}/reply", json={
            "body": "We are looking into this.",
        })

        assert resp.status_code == 201
        assert resp.json()["status"] == "respondido"

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_reply_conversation_not_found(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=None)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post(f"/api/messages/conversations/{CONV_ID}/reply", json={
            "body": "Hello?",
        })

        assert resp.status_code == 404

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_reply_access_denied(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        conv_data = {"id": CONV_ID, "user_id": "other-user-uuid", "status": "aberto"}
        sb.execute.return_value = Mock(data=conv_data)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post(f"/api/messages/conversations/{CONV_ID}/reply", json={
            "body": "Trying to sneak in.",
        })

        assert resp.status_code == 403

    def test_reply_invalid_uuid(self):
        client = _create_client()
        resp = client.post("/api/messages/conversations/not-a-uuid/reply", json={
            "body": "Test",
        })
        assert resp.status_code == 400


# ============================================================================
# PATCH /api/messages/conversations/{id}/status — admin only
# ============================================================================

class TestUpdateConversationStatus:

    @patch("routes.messages._get_sb")
    def test_admin_update_status_resolvido(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[{"id": CONV_ID, "status": "resolvido"}])
        mock_get_sb.return_value = sb
        client = _create_client(admin_user=MOCK_ADMIN)

        resp = client.patch(f"/api/messages/conversations/{CONV_ID}/status", json={
            "status": "resolvido",
        })

        assert resp.status_code == 200
        assert resp.json()["status"] == "resolvido"

    @patch("routes.messages._get_sb")
    def test_update_status_not_found(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])
        mock_get_sb.return_value = sb
        client = _create_client(admin_user=MOCK_ADMIN)

        resp = client.patch(f"/api/messages/conversations/{CONV_ID}/status", json={
            "status": "resolvido",
        })

        assert resp.status_code == 404

    def test_update_status_invalid_uuid(self):
        client = _create_client(admin_user=MOCK_ADMIN)
        resp = client.patch("/api/messages/conversations/not-a-uuid/status", json={
            "status": "resolvido",
        })
        assert resp.status_code == 400

    def test_update_status_non_admin_rejected(self):
        """Without require_admin override, non-admin should be rejected."""
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[require_auth] = lambda: MOCK_USER
        # Do NOT override require_admin — it will try real auth and fail
        # Since require_admin depends on require_auth, we mock require_admin to raise
        async def reject_admin(user=None):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Acesso restrito a administradores")

        app.dependency_overrides[require_admin] = reject_admin
        client = TestClient(app)

        resp = client.patch(f"/api/messages/conversations/{CONV_ID}/status", json={
            "status": "resolvido",
        })

        assert resp.status_code == 403


# ============================================================================
# GET /api/messages/unread-count
# ============================================================================

class TestUnreadCount:

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_user_unread_count(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        # First call: get user's conversation IDs
        # Second call: count unread admin replies
        sb.execute.side_effect = [
            Mock(data=[{"id": CONV_ID}]),  # user's conversations
            Mock(count=3),                  # unread messages
        ]
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/api/messages/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 3

    @patch("routes.messages._is_admin", return_value=False)
    @patch("routes.messages._get_sb")
    def test_user_no_conversations_zero_unread(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])  # No conversations
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/api/messages/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0

    @patch("routes.messages._is_admin", return_value=True)
    @patch("routes.messages._get_sb")
    def test_admin_unread_count(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        sb.execute.return_value = Mock(count=7)  # 7 unread user messages
        mock_get_sb.return_value = sb
        client = _create_client(user=MOCK_ADMIN)

        resp = client.get("/api/messages/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 7

    @patch("routes.messages._is_admin", return_value=True)
    @patch("routes.messages._get_sb")
    def test_admin_zero_unread(self, mock_get_sb, mock_is_admin):
        sb = _mock_sb()
        sb.execute.return_value = Mock(count=0)
        mock_get_sb.return_value = sb
        client = _create_client(user=MOCK_ADMIN)

        resp = client.get("/api/messages/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0
