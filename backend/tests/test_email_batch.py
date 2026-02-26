"""Tests for STORY-278 AC4: Batch email sending via Resend.

Tests send_batch_email() function in email_service.py.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSendBatchEmail:
    """Test batch email sending."""

    @patch("email_service._is_configured", return_value=True)
    def test_sends_batch_successfully(self, mock_configured):
        mock_resend = MagicMock()
        mock_resend.Batch.send.return_value = [
            {"id": "email-1"},
            {"id": "email-2"},
        ]

        with patch.dict("sys.modules", {"resend": mock_resend}):
            from email_service import send_batch_email

            messages = [
                {"to": "a@test.com", "subject": "Test 1", "html": "<p>Body 1</p>"},
                {"to": "b@test.com", "subject": "Test 2", "html": "<p>Body 2</p>"},
            ]

            result = send_batch_email(messages)

        assert result is not None
        assert len(result) == 2

    def test_returns_none_when_not_configured(self):
        with patch("email_service._is_configured", return_value=False):
            from email_service import send_batch_email

            result = send_batch_email([
                {"to": "test@test.com", "subject": "Test", "html": "<p>Body</p>"},
            ])

        assert result is None

    @patch("email_service._is_configured", return_value=True)
    def test_returns_empty_for_empty_messages(self, mock_configured):
        from email_service import send_batch_email
        result = send_batch_email([])
        assert result == []

    @patch("email_service._is_configured", return_value=True)
    @patch("email_service.MAX_RETRIES", 1)
    def test_returns_none_on_api_failure(self, mock_configured):
        mock_resend = MagicMock()
        mock_resend.Batch.send.side_effect = Exception("API Error")
        mock_resend.api_key = None

        with patch.dict("sys.modules", {"resend": mock_resend}):
            from email_service import send_batch_email

            messages = [
                {"to": "test@test.com", "subject": "Test", "html": "<p>Body</p>"},
            ]

            result = send_batch_email(messages)

        assert result is None

    @patch("email_service._is_configured", return_value=True)
    def test_includes_tags_when_provided(self, mock_configured):
        mock_resend = MagicMock()
        mock_resend.Batch.send.return_value = [{"id": "email-1"}]

        with patch.dict("sys.modules", {"resend": mock_resend}):
            from email_service import send_batch_email

            messages = [
                {
                    "to": "test@test.com",
                    "subject": "Test",
                    "html": "<p>Body</p>",
                    "tags": [{"name": "category", "value": "digest"}],
                },
            ]

            send_batch_email(messages)

        call_args = mock_resend.Batch.send.call_args[0][0]
        assert call_args[0]["tags"] == [{"name": "category", "value": "digest"}]

    @patch("email_service._is_configured", return_value=True)
    def test_handles_single_result_not_list(self, mock_configured):
        mock_resend = MagicMock()
        # Resend may return a single object instead of list
        mock_resend.Batch.send.return_value = {"id": "batch-1"}

        with patch.dict("sys.modules", {"resend": mock_resend}):
            from email_service import send_batch_email

            messages = [
                {"to": "test@test.com", "subject": "Test", "html": "<p>Body</p>"},
            ]

            result = send_batch_email(messages)

        assert result is not None
        assert len(result) == 1

    @patch("email_service._is_configured", return_value=True)
    def test_handles_to_as_list(self, mock_configured):
        mock_resend = MagicMock()
        mock_resend.Batch.send.return_value = [{"id": "email-1"}]

        with patch.dict("sys.modules", {"resend": mock_resend}):
            from email_service import send_batch_email

            messages = [
                {"to": ["a@test.com", "b@test.com"], "subject": "Test", "html": "<p>Body</p>"},
            ]

            send_batch_email(messages)

        call_args = mock_resend.Batch.send.call_args[0][0]
        assert call_args[0]["to"] == ["a@test.com", "b@test.com"]
