"""HARDEN-001 / DEBT-103 AC1: Verify OpenAI client uses timeout=5s and max_retries=1."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_client():
    """Reset the lazily-initialized OpenAI client between tests.

    STORY-CIG-BE-llm-arbiter-internals: `_client` moved to
    `llm_arbiter.classification` submodule after package refactor (TD-009).
    """
    from llm_arbiter import classification
    original = classification._client
    classification._client = None
    yield
    classification._client = original


class TestOpenAIClientTimeout:
    """AC1-AC4: Verify timeout, max_retries, and env-var configurability."""

    @patch("llm_arbiter.classification.OpenAI")
    def test_default_timeout_5s(self, mock_openai_cls):
        """DEBT-103 AC1: OpenAI() initialized with timeout=5 (was 15)."""
        import llm_arbiter
        llm_arbiter._get_client()
        mock_openai_cls.assert_called_once()
        kwargs = mock_openai_cls.call_args[1]
        assert kwargs["timeout"] == 5.0

    @patch("llm_arbiter.classification.OpenAI")
    def test_max_retries_1(self, mock_openai_cls):
        """AC2: max_retries=1 (reduced from SDK default of 2)."""
        import llm_arbiter
        llm_arbiter._get_client()
        kwargs = mock_openai_cls.call_args[1]
        assert kwargs["max_retries"] == 1

    def test_timeout_configurable_via_env(self):
        """AC3: Timeout configurable via LLM_TIMEOUT_S env var."""
        import importlib

        import config.features as _features
        import llm_arbiter
        from llm_arbiter import classification

        with patch.dict("os.environ", {"LLM_TIMEOUT_S": "30", "OPENAI_API_KEY": "test-key"}):
            # Reload config.features so LLM_TIMEOUT_S picks up env change,
            # reload classification so its cached `_LLM_TIMEOUT` uses the new value,
            # then reload the llm_arbiter facade so its re-exported bindings
            # (_arbiter_cache, _ARBITER_CACHE_MAX, _client, etc.) stay in sync
            # with the freshly-reloaded classification module. Without this,
            # downstream tests that access `llm_arbiter._arbiter_cache` would
            # operate on a stale OrderedDict detached from classification.
            importlib.reload(_features)
            importlib.reload(classification)
            importlib.reload(llm_arbiter)
            classification._client = None
            with patch("llm_arbiter.classification.OpenAI") as mock_openai_cls:
                classification._get_client()
                kwargs = mock_openai_cls.call_args[1]
                assert kwargs["timeout"] == 30.0
        # Restore modules to defaults (order matters: features → classification → facade)
        importlib.reload(_features)
        importlib.reload(classification)
        importlib.reload(llm_arbiter)

    @patch("llm_arbiter.classification.OpenAI")
    def test_client_lazy_singleton(self, mock_openai_cls):
        """Client is created once (singleton) on first call."""
        import llm_arbiter
        llm_arbiter._get_client()
        llm_arbiter._get_client()
        assert mock_openai_cls.call_count == 1
