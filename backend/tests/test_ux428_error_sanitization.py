"""UX-428: Tests for error sanitization in SSE progress events.

Ensures that technical error strings (HTTP status codes, env var names,
authentication details) are never exposed to the end user via SSE events
or frontend badge tooltips.
"""

import pytest

from progress import _sanitize_source_error


# ---------------------------------------------------------------------------
# Unit tests: _sanitize_source_error
# ---------------------------------------------------------------------------


class TestSanitizeSourceError:
    """AC3: Backend sanitization maps technical errors → friendly messages."""

    def test_401_http_status_returns_unavailable(self):
        result = _sanitize_source_error("HTTP 401: Authentication failed", "LICITAJA")
        assert result == "LICITAJA indisponível"

    def test_env_var_name_in_error_returns_unavailable(self):
        result = _sanitize_source_error("check LICITAJA_API_KEY env var", "LICITAJA")
        assert result == "LICITAJA indisponível"

    def test_source_auth_error_with_brackets_returns_unavailable(self):
        result = _sanitize_source_error("[LICITAJA] HTTP 401: SourceAuthError", "LICITAJA")
        assert result == "LICITAJA indisponível"

    def test_authentication_word_case_insensitive_returns_unavailable(self):
        result = _sanitize_source_error("Authentication Required", "LICITAJA")
        assert result == "LICITAJA indisponível"

    def test_403_forbidden_returns_unavailable(self):
        result = _sanitize_source_error("HTTP 403: Forbidden", "LICITAJA")
        assert result == "LICITAJA indisponível"

    def test_forbidden_word_returns_unavailable(self):
        result = _sanitize_source_error("Access Forbidden for this resource", "LICITAJA")
        assert result == "LICITAJA indisponível"

    def test_429_rate_limit_returns_overloaded(self):
        result = _sanitize_source_error("Rate limit exceeded: 429", "LICITAJA")
        assert result == "LICITAJA sobrecarregado"

    def test_rate_limit_string_returns_overloaded(self):
        result = _sanitize_source_error("rate limit exceeded, retry after 60s", "LICITAJA")
        assert result == "LICITAJA sobrecarregado"

    def test_timeout_error_returns_timeout_message(self):
        result = _sanitize_source_error("timeout after 30s", "LICITAJA")
        assert result == "LICITAJA não respondeu a tempo"

    def test_timeout_uppercase_returns_timeout_message(self):
        result = _sanitize_source_error("Timeout connecting to API endpoint", "LICITAJA")
        assert result == "LICITAJA não respondeu a tempo"

    def test_connection_refused_returns_generic(self):
        result = _sanitize_source_error("Connection refused", "LICITAJA")
        assert result == "LICITAJA: erro temporário"

    def test_generic_http_500_returns_generic(self):
        result = _sanitize_source_error("HTTP 500: Internal Server Error", "LICITAJA")
        assert result == "LICITAJA: erro temporário"

    def test_empty_error_returns_generic(self):
        result = _sanitize_source_error("", "LICITAJA")
        assert result == "LICITAJA: erro temporário"

    def test_source_name_in_result(self):
        """Source name must always appear in the returned string."""
        for error in ["HTTP 401: Auth", "rate limit", "timeout", "Connection error"]:
            result = _sanitize_source_error(error, "PNCP")
            assert "PNCP" in result, f"Source name missing for error: {error!r}"

    def test_api_key_substring_returns_unavailable(self):
        result = _sanitize_source_error("Missing api_key in headers", "BLL")
        assert result == "BLL indisponível"

    def test_api_key_space_variant_returns_unavailable(self):
        result = _sanitize_source_error("invalid API key provided", "BLL")
        assert result == "BLL indisponível"


# ---------------------------------------------------------------------------
# Integration test: emit_source_error produces sanitized SSE event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_source_error_sanitizes_detail():
    """AC3 integration: emit_source_error must not expose raw technical errors in detail."""
    from unittest.mock import AsyncMock, patch

    from progress import ProgressTracker

    tracker = ProgressTracker.__new__(ProgressTracker)
    tracker.search_id = "test-search-id"
    tracker._emit_event = AsyncMock()

    await tracker.emit_source_error(
        source="LICITAJA",
        error="HTTP 401: Authentication failed — check LICITAJA_API_KEY",
        duration_ms=1234,
    )

    tracker._emit_event.assert_called_once()
    emitted_event = tracker._emit_event.call_args[0][0]
    detail = emitted_event.detail

    assert "401" not in detail["error"], "Raw HTTP status exposed in detail"
    assert "LICITAJA_API_KEY" not in detail["error"], "Env var name exposed in detail"
    assert "LICITAJA" in detail["error"]
    assert detail["source"] == "LICITAJA"
    assert detail["duration_ms"] == 1234
    assert "401" not in emitted_event.message
    assert "LICITAJA_API_KEY" not in emitted_event.message


@pytest.mark.asyncio
async def test_emit_source_error_sanitizes_rate_limit():
    """emit_source_error sanitizes rate limit errors too."""
    from progress import ProgressTracker

    tracker = ProgressTracker.__new__(ProgressTracker)
    tracker.search_id = "test-429"
    from unittest.mock import AsyncMock
    tracker._emit_event = AsyncMock()

    await tracker.emit_source_error(
        source="PORTAL_COMPRAS",
        error="HTTP 429: Too Many Requests — rate limit exceeded",
        duration_ms=500,
    )

    event = tracker._emit_event.call_args[0][0]
    assert "429" not in event.detail["error"]
    assert "sobrecarregado" in event.detail["error"]
