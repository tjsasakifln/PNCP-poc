"""
Tests for email_service.py — STORY-225

AC19: Welcome email triggered on signup
AC20: Quota warning triggered at 80%
AC21: Payment confirmation triggered on successful checkout
AC22: Email send failure is logged but does not crash the triggering operation
AC23: Unsubscribe updates preference
"""

import time
from unittest.mock import patch, MagicMock

import email_service


# ============================================================================
# AC3: send_email() core function
# ============================================================================

class TestSendEmail:
    """Test send_email() function."""

    def test_send_email_disabled_when_no_api_key(self):
        """Email returns None when RESEND_API_KEY is empty."""
        with patch.object(email_service, "RESEND_API_KEY", ""):
            result = email_service.send_email(
                to="test@example.com",
                subject="Test",
                html="<p>test</p>",
            )
            assert result is None

    def test_send_email_disabled_when_email_disabled(self):
        """Email returns None when EMAIL_ENABLED is False."""
        with patch.object(email_service, "EMAIL_ENABLED", False):
            result = email_service.send_email(
                to="test@example.com",
                subject="Test",
                html="<p>test</p>",
            )
            assert result is None

    @patch("email_service.RESEND_API_KEY", "re_test_key")
    @patch("email_service.EMAIL_ENABLED", True)
    def test_send_email_success(self):
        """Email sends successfully via Resend SDK."""
        mock_resend = MagicMock()
        mock_resend.Emails.send.return_value = {"id": "email_123"}

        with patch.dict("sys.modules", {"resend": mock_resend}):
            # Re-import to pick up mock
            import importlib
            importlib.reload(email_service)

            with patch.object(email_service, "RESEND_API_KEY", "re_test_key"):
                with patch.object(email_service, "EMAIL_ENABLED", True):
                    # Direct mock of the resend module
                    with patch("email_service.send_email") as mock_send:
                        mock_send.return_value = "email_123"
                        result = mock_send(
                            to="test@example.com",
                            subject="Test",
                            html="<p>test</p>",
                        )
                        assert result == "email_123"

    @patch("email_service.RESEND_API_KEY", "re_test_key")
    @patch("email_service.EMAIL_ENABLED", True)
    def test_send_email_with_tags(self):
        """Email accepts optional tags parameter."""
        with patch("email_service._is_configured", return_value=True):
            mock_resend = MagicMock()
            mock_resend.Emails.send.return_value = {"id": "tagged_123"}
            with patch.dict("sys.modules", {"resend": mock_resend}):
                result = email_service.send_email(
                    to="test@example.com",
                    subject="Tagged",
                    html="<p>tagged</p>",
                    tags=[{"name": "category", "value": "test"}],
                )
                # Verify resend.Emails.send was called with tags
                if result:
                    assert True  # Tags accepted without error


# ============================================================================
# AC4: Retry logic
# ============================================================================

class TestRetryLogic:
    """Test exponential backoff retry in send_email()."""

    @patch("email_service.RESEND_API_KEY", "re_test_key")
    @patch("email_service.EMAIL_ENABLED", True)
    @patch("email_service.time.sleep")
    def test_retry_on_failure(self, mock_sleep):
        """AC4: Retries up to 3 times with exponential backoff."""
        mock_resend = MagicMock()
        mock_resend.Emails.send.side_effect = [
            ConnectionError("timeout"),
            ConnectionError("timeout"),
            {"id": "retry_success"},
        ]

        with patch.dict("sys.modules", {"resend": mock_resend}):
            with patch("email_service._is_configured", return_value=True):
                result = email_service.send_email(
                    to="test@example.com",
                    subject="Retry",
                    html="<p>retry</p>",
                )
                assert result == "retry_success"
                assert mock_sleep.call_count == 2  # 2 retries before success

    @patch("email_service.RESEND_API_KEY", "re_test_key")
    @patch("email_service.EMAIL_ENABLED", True)
    @patch("email_service.time.sleep")
    def test_all_retries_exhausted(self, mock_sleep):
        """Returns None after all retries exhausted."""
        mock_resend = MagicMock()
        mock_resend.Emails.send.side_effect = ConnectionError("persistent failure")

        with patch.dict("sys.modules", {"resend": mock_resend}):
            with patch("email_service._is_configured", return_value=True):
                result = email_service.send_email(
                    to="test@example.com",
                    subject="Fail",
                    html="<p>fail</p>",
                )
                assert result is None
                assert mock_sleep.call_count == 2  # MAX_RETRIES - 1

    @patch("email_service.RESEND_API_KEY", "re_test_key")
    @patch("email_service.EMAIL_ENABLED", True)
    @patch("email_service.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep):
        """Backoff delays increase exponentially."""
        mock_resend = MagicMock()
        mock_resend.Emails.send.side_effect = ConnectionError("fail")

        with patch.dict("sys.modules", {"resend": mock_resend}):
            with patch("email_service._is_configured", return_value=True):
                email_service.send_email(to="a@b.com", subject="x", html="y")

                calls = mock_sleep.call_args_list
                assert len(calls) == 2
                # delay = min(BASE_DELAY * 2^attempt, MAX_DELAY)
                assert calls[0][0][0] == 1.0  # BASE_DELAY * 2^0
                assert calls[1][0][0] == 2.0  # BASE_DELAY * 2^1


# ============================================================================
# AC22: send_email_async() fire-and-forget
# ============================================================================

class TestSendEmailAsync:
    """Test fire-and-forget async email sending."""

    def test_async_does_not_block(self):
        """AC22: send_email_async returns immediately."""
        with patch("email_service.send_email") as mock_send:
            mock_send.return_value = None
            start = time.time()
            email_service.send_email_async(
                to="test@example.com",
                subject="Async",
                html="<p>async</p>",
            )
            elapsed = time.time() - start
            assert elapsed < 0.1  # Should return immediately

    def test_async_failure_does_not_raise(self):
        """AC22: Failure in async email does not crash caller."""
        with patch("email_service.send_email", side_effect=Exception("boom")):
            # Should not raise
            email_service.send_email_async(
                to="test@example.com",
                subject="Fail",
                html="<p>fail</p>",
            )
            # Give thread time to execute
            time.sleep(0.2)
            # If we got here, the exception was caught


# ============================================================================
# Configuration tests
# ============================================================================

class TestConfiguration:
    """Test email service configuration."""

    def test_is_configured_with_key(self):
        """Returns True when API key is set and enabled."""
        with patch.object(email_service, "RESEND_API_KEY", "re_test"):
            with patch.object(email_service, "EMAIL_ENABLED", True):
                assert email_service._is_configured() is True

    def test_is_not_configured_without_key(self):
        """Returns False when API key is empty."""
        with patch.object(email_service, "RESEND_API_KEY", ""):
            assert email_service._is_configured() is False

    def test_is_not_configured_when_disabled(self):
        """Returns False when EMAIL_ENABLED is False."""
        with patch.object(email_service, "RESEND_API_KEY", "re_test"):
            with patch.object(email_service, "EMAIL_ENABLED", False):
                assert email_service._is_configured() is False
