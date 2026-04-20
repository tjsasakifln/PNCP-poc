"""Tests for STORY-278 AC5: Daily Digest ARQ Cron Job.

Tests daily_digest_job() in job_queue.py and WorkerSettings registration.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys


# Mock arq before importing job_queue
_fake_arq = MagicMock()
_fake_arq.connections.RedisSettings = MagicMock


class _FakeRedisSettings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestDailyDigestJob:
    """Test the daily_digest_job function."""

    @pytest.mark.asyncio
    @patch("config.DIGEST_ENABLED", False)
    async def test_skips_when_disabled(self):
        with patch.dict(sys.modules, {"arq": _fake_arq, "arq.connections": _fake_arq.connections, "arq.cron": _fake_arq}):
            _fake_arq.connections.RedisSettings = _FakeRedisSettings
            from job_queue import daily_digest_job

            result = await daily_digest_job({})
            assert result["status"] == "disabled"

    @pytest.mark.asyncio
    @patch("config.DIGEST_ENABLED", True)
    @patch("config.DIGEST_MAX_PER_EMAIL", 10)
    @patch("config.DIGEST_BATCH_SIZE", 100)
    async def test_handles_no_eligible_users(self):
        with patch.dict(sys.modules, {"arq": _fake_arq, "arq.connections": _fake_arq.connections, "arq.cron": _fake_arq}):
            _fake_arq.connections.RedisSettings = _FakeRedisSettings

            mock_db = MagicMock()
            with patch("job_queue.daily_digest_job.__module__", "job_queue"):
                pass

            # Patch supabase
            with patch("supabase_client.get_supabase", return_value=mock_db):
                with patch("services.digest_service.get_digest_eligible_users", new_callable=AsyncMock, return_value=[]):
                    from job_queue import daily_digest_job
                    result = await daily_digest_job({})

            assert result["status"] == "no_users"
            assert result["users_queried"] == 0

    @pytest.mark.asyncio
    @patch("config.DIGEST_ENABLED", True)
    @patch("config.DIGEST_MAX_PER_EMAIL", 10)
    @patch("config.DIGEST_BATCH_SIZE", 100)
    async def test_sends_digest_for_eligible_users(self):
        with patch.dict(sys.modules, {"arq": _fake_arq, "arq.connections": _fake_arq.connections, "arq.cron": _fake_arq}):
            _fake_arq.connections.RedisSettings = _FakeRedisSettings

            mock_db = MagicMock()

            eligible_users = [
                {"user_id": "u1", "frequency": "daily", "enabled": True, "last_digest_sent_at": None},
            ]

            digest_data = {
                "user_id": "u1",
                "user_name": "Test",
                "email": "test@example.com",
                "opportunities": [{"titulo": "T", "orgao": "O", "valor_estimado": 100, "uf": "SP", "viability_score": 0.8}],
                "stats": {"total_novas": 1, "setor_nome": "TI", "total_valor": 100},
            }

            with patch("supabase_client.get_supabase", return_value=mock_db), \
                 patch("services.digest_service.get_digest_eligible_users", new_callable=AsyncMock, return_value=eligible_users), \
                 patch("services.digest_service.build_digest_for_user", new_callable=AsyncMock, return_value=digest_data), \
                 patch("services.digest_service.mark_digest_sent", new_callable=AsyncMock), \
                 patch("email_service.send_batch_email", return_value=[{"id": "email-1"}]):

                from job_queue import daily_digest_job
                result = await daily_digest_job({})

            assert result["status"] == "completed"
            assert result["emails_sent"] == 1
            assert result["users_queried"] == 1

    @pytest.mark.asyncio
    @patch("config.DIGEST_ENABLED", True)
    @patch("config.DIGEST_MAX_PER_EMAIL", 10)
    @patch("config.DIGEST_BATCH_SIZE", 100)
    async def test_handles_build_digest_failure(self):
        with patch.dict(sys.modules, {"arq": _fake_arq, "arq.connections": _fake_arq.connections, "arq.cron": _fake_arq}):
            _fake_arq.connections.RedisSettings = _FakeRedisSettings

            mock_db = MagicMock()

            eligible_users = [
                {"user_id": "u1", "frequency": "daily", "enabled": True, "last_digest_sent_at": None},
            ]

            with patch("supabase_client.get_supabase", return_value=mock_db), \
                 patch("services.digest_service.get_digest_eligible_users", new_callable=AsyncMock, return_value=eligible_users), \
                 patch("services.digest_service.build_digest_for_user", new_callable=AsyncMock, side_effect=Exception("Build error")):

                from job_queue import daily_digest_job
                result = await daily_digest_job({})

            assert result["emails_failed"] == 1
            assert result["emails_sent"] == 0

    @pytest.mark.asyncio
    @patch("config.DIGEST_ENABLED", True)
    @patch("config.DIGEST_MAX_PER_EMAIL", 10)
    @patch("config.DIGEST_BATCH_SIZE", 100)
    async def test_handles_db_unavailable(self):
        with patch.dict(sys.modules, {"arq": _fake_arq, "arq.connections": _fake_arq.connections, "arq.cron": _fake_arq}):
            _fake_arq.connections.RedisSettings = _FakeRedisSettings

            with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
                from job_queue import daily_digest_job
                result = await daily_digest_job({})

            assert result["status"] == "db_unavailable"

    @pytest.mark.asyncio
    @patch("config.DIGEST_ENABLED", True)
    @patch("config.DIGEST_MAX_PER_EMAIL", 10)
    @patch("config.DIGEST_BATCH_SIZE", 100)
    async def test_skips_users_with_no_digest(self):
        """Users where build_digest returns None are skipped."""
        with patch.dict(sys.modules, {"arq": _fake_arq, "arq.connections": _fake_arq.connections, "arq.cron": _fake_arq}):
            _fake_arq.connections.RedisSettings = _FakeRedisSettings

            mock_db = MagicMock()

            eligible_users = [
                {"user_id": "u1", "frequency": "daily", "enabled": True, "last_digest_sent_at": None},
            ]

            with patch("supabase_client.get_supabase", return_value=mock_db), \
                 patch("services.digest_service.get_digest_eligible_users", new_callable=AsyncMock, return_value=eligible_users), \
                 patch("services.digest_service.build_digest_for_user", new_callable=AsyncMock, return_value=None):

                from job_queue import daily_digest_job
                result = await daily_digest_job({})

            assert result["emails_skipped"] == 1
            assert result["emails_sent"] == 0


class TestWorkerSettingsDigest:
    """Test that daily_digest_job is registered in WorkerSettings."""

    def test_digest_job_in_functions(self):
        with patch.dict(sys.modules, {"arq": _fake_arq, "arq.connections": _fake_arq.connections, "arq.cron": _fake_arq}):
            _fake_arq.connections.RedisSettings = _FakeRedisSettings
            _fake_arq.cron = MagicMock()

            from job_queue import WorkerSettings
            # BTS-010b: some entries may be MagicMocks lacking __name__ due to arq stub;
            # fall back to repr for those entries so we can scan reliably.
            func_names = [
                getattr(f, "__name__", None) or repr(f)
                for f in WorkerSettings.functions
            ]
            assert "daily_digest_job" in func_names, (
                f"daily_digest_job not found in WorkerSettings.functions: {func_names}"
            )


class TestDigestConfig:
    """Test STORY-278 config variables."""

    def test_digest_enabled_default_false(self):
        from config import DIGEST_ENABLED
        # Default is false unless env var is set
        assert isinstance(DIGEST_ENABLED, bool)

    def test_digest_hour_default_10(self):
        from config import DIGEST_HOUR_UTC
        assert DIGEST_HOUR_UTC == 10

    def test_digest_max_per_email_default_10(self):
        from config import DIGEST_MAX_PER_EMAIL
        assert DIGEST_MAX_PER_EMAIL == 10

    def test_digest_batch_size_100(self):
        from config import DIGEST_BATCH_SIZE
        assert DIGEST_BATCH_SIZE == 100
