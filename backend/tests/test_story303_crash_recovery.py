"""
STORY-303: Backend Crash Recovery & Startup Resilience — Tests

AC17: Gunicorn starts without --preload and workers respond to health check
AC18: cryptography import works in worker process (JWT decode, HTTPS)
AC15-AC16: worker_exit logs SIGSEGV, OOM, and non-zero exit codes
AC5: when_ready hook logs readiness
AC1: start.sh defaults GUNICORN_PRELOAD=false
AC10: cryptography pinned to exact version
AC6: railway.toml health check grace period >= 30s
"""

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _restore_gunicorn_conf_logger_propagation():
    """Restore `gunicorn.conf` logger propagation for caplog compatibility.

    BTS-011 cluster 1: `test_crit042_gunicorn_logging.py` applies
    `logging.config.dictConfig(gunicorn_conf.logconfig_dict)` which globally
    sets `propagate=False` on the `gunicorn.conf` logger (by design, so that
    gunicorn doesn't double-emit). That state persists across test files
    (Python's logging module has process-global state). When pytest discovers
    test_story303 after test_crit042, caplog receives no records because
    messages never propagate to the root handler that caplog installs.

    This fixture runs before every test in this module and forces propagation
    back on, so `caplog.at_level(..., logger="gunicorn.conf")` works as
    pytest documents. It restores the prior value after each test so we don't
    affect subsequent tests' expectations.
    """
    gc_logger = logging.getLogger("gunicorn.conf")
    prev_propagate = gc_logger.propagate
    prev_level = gc_logger.level
    gc_logger.propagate = True
    gc_logger.setLevel(logging.DEBUG)
    try:
        yield
    finally:
        gc_logger.propagate = prev_propagate
        gc_logger.setLevel(prev_level)


# ---------------------------------------------------------------------------
# AC1: start.sh — GUNICORN_PRELOAD defaults to false
# ---------------------------------------------------------------------------


class TestStartShPreloadDefault:
    """AC1: start.sh must default GUNICORN_PRELOAD to false."""

    def test_ac1_start_sh_defaults_preload_false(self):
        """start.sh contains GUNICORN_PRELOAD:-false as default."""
        import os

        start_sh_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "start.sh"
        )
        with open(start_sh_path) as f:
            content = f.read()

        assert "GUNICORN_PRELOAD:-false" in content, (
            "start.sh must default GUNICORN_PRELOAD to false (STORY-303 AC1)"
        )

    def test_ac1_start_sh_no_preload_true_default(self):
        """start.sh must NOT default GUNICORN_PRELOAD to true."""
        import os

        start_sh_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "start.sh"
        )
        with open(start_sh_path) as f:
            content = f.read()

        assert "GUNICORN_PRELOAD:-true" not in content, (
            "start.sh must not have GUNICORN_PRELOAD:-true (STORY-303 AC1)"
        )

    def test_ac1_start_sh_preload_warning_when_enabled(self):
        """start.sh warns about fork-safety when --preload is explicitly enabled."""
        import os

        start_sh_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "start.sh"
        )
        with open(start_sh_path) as f:
            content = f.read()

        assert "verify cryptography fork-safety" in content, (
            "start.sh must warn about fork-safety when preload is enabled"
        )


# ---------------------------------------------------------------------------
# AC10-AC11: requirements.txt — cryptography pinned to exact version
# ---------------------------------------------------------------------------


class TestRequirementsCryptographyPin:
    """AC10-AC11: cryptography must be pinned to an exact version."""

    def test_ac10_cryptography_pinned_exact(self):
        """requirements.txt pins cryptography to a single 46.x release line.

        CIG-BE-story-drift-cryptography-pin: STORY-303 AC10 originally required
        ``cryptography==46.0.5`` (exact pin). After CVE-2026-26007 + CVE-2026-34073
        fixes (DEBT-SYS-002), the constraint was widened to
        ``cryptography>=46.0.6,<47.0.0`` — the upper bound on the major release
        preserves fork-safety (47.x has not been validated) while still letting
        the security floor advance with patch releases. AC10 is satisfied as
        long as the constraint stays bounded inside the 46.x line.
        """
        import os
        import re

        req_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "requirements.txt"
        )
        with open(req_path) as f:
            content = f.read()

        # Accept either exact pin (==46.x.y) or the bounded range used post-DEBT-SYS-002.
        exact = re.search(r"cryptography==46\.\d+\.\d+", content) is not None
        bounded = re.search(
            r"cryptography>=46\.\d+\.\d+,<47\.0\.0", content
        ) is not None
        assert exact or bounded, (
            "requirements.txt must pin cryptography to the 46.x line "
            "(==46.x.y exact OR >=46.x.y,<47.0.0 bounded)"
        )

    def test_ac10_no_cryptography_greater_than(self):
        """requirements.txt cryptography pin must be bounded to the 46.x line.

        Same rationale as ``test_ac10_cryptography_pinned_exact``: a bare ``>=``
        without an upper bound would break fork-safety, but the
        ``>=46.0.6,<47.0.0`` range introduced post-DEBT-SYS-002 keeps the upper
        bound and is therefore acceptable.
        """
        import os

        req_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "requirements.txt"
        )
        with open(req_path) as f:
            lines = f.readlines()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("cryptography") and not stripped.startswith("#"):
                if ">=" in stripped:
                    assert "<47.0.0" in stripped, (
                        f"cryptography must keep the <47.0.0 upper bound "
                        f"(found: {stripped}). Unbounded >= breaks fork-safety."
                    )

    def test_ac11_cryptography_has_fork_safety_comment(self):
        """requirements.txt has a comment about fork-safety testing on upgrade."""
        import os

        req_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "requirements.txt"
        )
        with open(req_path) as f:
            content = f.read()

        assert "fork-safe" in content.lower(), (
            "requirements.txt must document fork-safety testing requirement (STORY-303 AC11)"
        )


# ---------------------------------------------------------------------------
# AC5: when_ready hook
# ---------------------------------------------------------------------------


class TestWhenReadyHook:
    """AC5: when_ready hook logs readiness after workers spawned."""

    def test_ac5_when_ready_exists(self):
        """gunicorn_conf.py exports when_ready hook."""
        import gunicorn_conf

        assert hasattr(gunicorn_conf, "when_ready"), (
            "gunicorn_conf.py must define when_ready hook (STORY-303 AC5)"
        )
        assert callable(gunicorn_conf.when_ready)

    def test_ac5_when_ready_logs_info(self, caplog):
        """when_ready logs at INFO level with worker count and preload status."""
        import gunicorn_conf

        # Mock server object
        mock_cfg = SimpleNamespace(preload_app=False)
        mock_server = SimpleNamespace(pid=1234, num_workers=2, cfg=mock_cfg)

        with caplog.at_level(logging.INFO, logger="gunicorn.conf"):
            gunicorn_conf.when_ready(mock_server)

        assert any("All workers ready" in r.message for r in caplog.records), (
            "when_ready must log 'All workers ready'"
        )
        assert any("preload=OFF" in r.message for r in caplog.records), (
            "when_ready must log preload status"
        )

    def test_ac5_when_ready_shows_preload_on(self, caplog):
        """when_ready correctly reports preload=ON when enabled."""
        import gunicorn_conf

        mock_cfg = SimpleNamespace(preload_app=True)
        mock_server = SimpleNamespace(pid=5678, num_workers=4, cfg=mock_cfg)

        with caplog.at_level(logging.INFO, logger="gunicorn.conf"):
            gunicorn_conf.when_ready(mock_server)

        assert any("preload=ON" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# AC15: worker_exit — SIGSEGV (exit code -11) logging
# ---------------------------------------------------------------------------


class TestWorkerExitSigsegv:
    """AC15: worker_exit handles SIGSEGV (exit code -11) with CRITICAL + Sentry."""

    def test_ac15_sigsegv_logged_critical(self, caplog):
        """SIGSEGV (exit code -11) logged at CRITICAL severity."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=9999, exitcode=-11)

        with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
            with patch.dict("sys.modules", {"sentry_sdk": MagicMock()}):
                gunicorn_conf.worker_exit(mock_server, mock_worker)

        critical_records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
        assert len(critical_records) >= 1, "SIGSEGV must produce CRITICAL log"
        assert any("SIGSEGV" in r.message for r in critical_records)
        assert any("exit_code=-11" in r.message for r in critical_records)

    def test_ac15_sigsegv_mentions_fork_safety(self, caplog):
        """SIGSEGV log message mentions cryptography fork-safety check."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=1111, exitcode=-11)

        with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
            with patch.dict("sys.modules", {"sentry_sdk": MagicMock()}):
                gunicorn_conf.worker_exit(mock_server, mock_worker)

        assert any("fork-safety" in r.message for r in caplog.records)
        assert any("GUNICORN_PRELOAD=false" in r.message for r in caplog.records)

    def test_ac15_sigsegv_captures_sentry(self):
        """SIGSEGV triggers Sentry capture with crash_type=SIGSEGV tag."""
        import gunicorn_conf

        mock_sentry = MagicMock()
        mock_scope = MagicMock()
        mock_sentry.new_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_sentry.new_scope.return_value.__exit__ = MagicMock(return_value=False)

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=2222, exitcode=-11)

        with patch.dict("sys.modules", {"sentry_sdk": mock_sentry}):
            gunicorn_conf.worker_exit(mock_server, mock_worker)

        mock_scope.set_tag.assert_any_call("crash_type", "SIGSEGV")
        mock_scope.set_level.assert_called_with("fatal")
        mock_sentry.capture_message.assert_called_once()
        assert "SIGSEGV" in mock_sentry.capture_message.call_args[0][0]


# ---------------------------------------------------------------------------
# AC16: worker_exit — ALL non-zero exit codes logged
# ---------------------------------------------------------------------------


class TestWorkerExitAllNonZero:
    """AC16: Every non-zero exit code is logged (not silently ignored)."""

    def test_ac16_oom_kill_logged_critical(self, caplog):
        """OOM kill (exit code -9) logged at CRITICAL."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=3333, exitcode=-9)

        with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
            with patch.dict("sys.modules", {"sentry_sdk": MagicMock()}):
                gunicorn_conf.worker_exit(mock_server, mock_worker)

        critical_records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
        assert any("OOM" in r.message for r in critical_records)

    def test_ac16_clean_exit_logged_info(self, caplog):
        """Clean exit (code 0) logged at INFO."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=4444, exitcode=0)

        with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
            gunicorn_conf.worker_exit(mock_server, mock_worker)

        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert any("recycled cleanly" in r.message for r in info_records)

    def test_ac16_unexpected_exit_logged_warning(self, caplog):
        """Unexpected non-zero exit (e.g., code 1) logged at WARNING."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=5555, exitcode=1)

        with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
            with patch.dict("sys.modules", {"sentry_sdk": MagicMock()}):
                gunicorn_conf.worker_exit(mock_server, mock_worker)

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("unexpectedly" in r.message for r in warning_records)

    def test_ac16_sigterm_exit_logged(self, caplog):
        """SIGTERM (exit code -15) logged at WARNING with Sentry capture."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=6666, exitcode=-15)

        with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
            with patch.dict("sys.modules", {"sentry_sdk": MagicMock()}):
                gunicorn_conf.worker_exit(mock_server, mock_worker)

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("exit_code=-15" in r.message for r in warning_records)

    def test_ac16_unknown_exitcode_handled(self, caplog):
        """Worker without exitcode attribute doesn't crash."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=7777)  # no exitcode attribute

        with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
            with patch.dict("sys.modules", {"sentry_sdk": MagicMock()}):
                gunicorn_conf.worker_exit(mock_server, mock_worker)

        # "unknown" exit code should still produce a log
        assert any("unknown" in r.message for r in caplog.records)

    def test_ac16_sentry_failure_does_not_crash(self, caplog):
        """Sentry import failure doesn't crash worker_exit."""
        import gunicorn_conf

        mock_server = SimpleNamespace()
        mock_worker = SimpleNamespace(pid=8888, exitcode=-11)

        # Remove sentry_sdk from modules to simulate import failure
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            # Should not raise
            with caplog.at_level(logging.DEBUG, logger="gunicorn.conf"):
                gunicorn_conf.worker_exit(mock_server, mock_worker)

        # SIGSEGV still logged despite Sentry failure
        assert any("SIGSEGV" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# AC6: railway.toml — health check grace period >= 30s
# ---------------------------------------------------------------------------


class TestRailwayTomlGracePeriod:
    """AC6: railway.toml healthcheckTimeout >= 30s."""

    def test_ac6_healthcheck_timeout_gte_30(self):
        """railway.toml healthcheckTimeout must be >= 30 seconds."""
        import os
        import re

        toml_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "railway.toml"
        )
        with open(toml_path) as f:
            content = f.read()

        match = re.search(r"healthcheckTimeout\s*=\s*(\d+)", content)
        assert match is not None, "railway.toml must define healthcheckTimeout"

        timeout = int(match.group(1))
        assert timeout >= 30, (
            f"healthcheckTimeout={timeout} must be >= 30 (STORY-303 AC6)"
        )

    def test_ac6_healthcheck_path_is_health_live(self):
        """railway.toml health check path must be /health/live.

        Stage-2 incident fix 2026-04-27 (PR #529): switched from /health (probes 5
        external APIs, slow under load) and /health/ready (probes Redis+Supabase,
        fails 503 when wedged) to /health/live (pure-async, no IO, ALWAYS 200 if
        worker is alive). Under sustained Googlebot crawl the previous probe
        couldn't respond → Railway healthcheck timed out 11/11 retries → new
        container never promoted → wedge perpetuated.
        """
        import os

        toml_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "railway.toml"
        )
        with open(toml_path) as f:
            content = f.read()

        assert "/health/live" in content, (
            "railway.toml must check /health/live (pure-async liveness probe; "
            "incident hotfix PR #529 Stage 2)"
        )


# ---------------------------------------------------------------------------
# AC18: cryptography import works in current process
# ---------------------------------------------------------------------------


class TestCryptographyImport:
    """AC18: cryptography works without --preload (in-process import)."""

    def test_ac18_cryptography_imports_successfully(self):
        """cryptography can be imported in the current process."""
        try:
            import cryptography
            assert cryptography.__version__ is not None
        except ImportError:
            pytest.skip("cryptography not installed in test environment")

    def test_ac18_jwt_decode_works(self):
        """PyJWT with cryptography backend can create/verify tokens."""
        try:
            import jwt
        except ImportError:
            pytest.skip("PyJWT not installed in test environment")

        # Use 32-byte key to satisfy RFC 7518 Section 3.2 minimum for HS256
        payload = {"sub": "test", "exp": 9999999999}
        secret = "test-secret-key-that-is-32-bytes"

        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        assert decoded["sub"] == "test"

    def test_ac18_cryptography_hazmat_accessible(self):
        """cryptography.hazmat (C bindings) can be imported."""
        try:
            from cryptography.hazmat.primitives import hashes
            # Verify the C bindings are actually loaded
            digest = hashes.SHA256()
            assert digest.digest_size == 32
        except ImportError:
            pytest.skip("cryptography not installed in test environment")


# ---------------------------------------------------------------------------
# AC17: Integration — gunicorn_conf.py hooks are importable and callable
# ---------------------------------------------------------------------------


class TestGunicornConfIntegration:
    """AC17: All gunicorn_conf hooks are importable and callable."""

    def test_ac17_all_hooks_importable(self):
        """All 4 hooks can be imported from gunicorn_conf."""
        from gunicorn_conf import (
            post_worker_init,
            when_ready,
            worker_abort,
            worker_exit,
        )

        assert callable(when_ready)
        assert callable(post_worker_init)
        assert callable(worker_abort)
        assert callable(worker_exit)

    def test_ac17_when_ready_no_crash_with_minimal_server(self):
        """when_ready doesn't crash with minimal server object."""
        from gunicorn_conf import when_ready

        mock_cfg = SimpleNamespace(preload_app=False)
        mock_server = SimpleNamespace(pid=1, num_workers=1, cfg=mock_cfg)
        when_ready(mock_server)  # Should not raise

    def test_ac17_worker_exit_no_crash_with_all_codes(self):
        """worker_exit handles all signal codes without crashing."""
        from gunicorn_conf import worker_exit

        mock_server = SimpleNamespace()
        test_codes = [-11, -9, -15, -6, 0, 1, 2, 137]

        for code in test_codes:
            mock_worker = SimpleNamespace(pid=100, exitcode=code)
            with patch.dict("sys.modules", {"sentry_sdk": MagicMock()}):
                worker_exit(mock_server, mock_worker)  # Should not raise

    def test_ac17_post_worker_init_graceful_on_missing_module(self, caplog):
        """post_worker_init handles missing worker_lifecycle gracefully."""
        from gunicorn_conf import post_worker_init

        mock_worker = SimpleNamespace(pid=100)

        # Temporarily break the import
        with patch.dict("sys.modules", {"worker_lifecycle": None}):
            with caplog.at_level(logging.WARNING, logger="gunicorn.conf"):
                post_worker_init(mock_worker)

        # Should log warning, not crash
        assert any("Failed to install" in r.message for r in caplog.records)
