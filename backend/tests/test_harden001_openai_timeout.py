"""HARDEN-001 / DEBT-103 AC1: Verify OpenAI client uses timeout=5s and max_retries=1."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_client():
    """Reset the lazily-initialized OpenAI client between tests."""
    import llm_arbiter
    original = llm_arbiter._client
    llm_arbiter._client = None
    yield
    llm_arbiter._client = original


class TestOpenAIClientTimeout:
    """AC1-AC4: Verify timeout, max_retries, and env-var configurability."""

    @patch("llm_arbiter.OpenAI")
    def test_default_timeout_5s(self, mock_openai_cls):
        """DEBT-103 AC1: OpenAI() initialized with timeout=5 (was 15)."""
        import llm_arbiter
        llm_arbiter._get_client()
        mock_openai_cls.assert_called_once()
        kwargs = mock_openai_cls.call_args[1]
        assert kwargs["timeout"] == 5.0

    @patch("llm_arbiter.OpenAI")
    def test_max_retries_1(self, mock_openai_cls):
        """AC2: max_retries=1 (reduced from SDK default of 2)."""
        import llm_arbiter
        llm_arbiter._get_client()
        kwargs = mock_openai_cls.call_args[1]
        assert kwargs["max_retries"] == 1

    def test_timeout_configurable_via_env(self):
        """AC3: Timeout configurable via LLM_TIMEOUT_S env var."""
        import llm_arbiter
        with patch.dict("os.environ", {"LLM_TIMEOUT_S": "30", "OPENAI_API_KEY": "test-key"}):
            import importlib
            importlib.reload(llm_arbiter)
            llm_arbiter._client = None
            with patch("llm_arbiter.OpenAI") as mock_openai_cls:
                llm_arbiter._get_client()
                kwargs = mock_openai_cls.call_args[1]
                assert kwargs["timeout"] == 30.0
            # Restore module to default
            importlib.reload(llm_arbiter)

    @patch("llm_arbiter.OpenAI")
    def test_client_lazy_singleton(self, mock_openai_cls):
        """Client is created once (singleton) on first call."""
        import llm_arbiter
        llm_arbiter._get_client()
        llm_arbiter._get_client()
        assert mock_openai_cls.call_count == 1
