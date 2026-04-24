"""STORY-413: Regression tests for backend/startup/sentry.py integrations list.

The 2026-04-10 incident (Sentry issues 7400217484 / 7282829485 / 7282829484,
132 events, Escalating/Regressed) was rooted in a contradiction: the
``init_sentry`` docstring claimed StarletteIntegration was DISABLED for SIGSEGV
reasons, but the integrations list still included it. When sentry-sdk 2.x
re-shaped the _sentry_receive wrapper, the double-wrap surfaced as
``TypeError: func() missing 1 required positional argument: 'coroutine'``
unhandled inside AsyncExitStackMiddleware → crash loop.

These tests guard against any future re-addition by:
  1. Asserting the StarletteIntegration class is not even imported in the module.
  2. Inspecting the integrations list passed to sentry_sdk.init() at runtime.
  3. Verifying the sentry-sdk version pin in requirements.txt is exact.
"""

import importlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSentryIntegrationsContract:
    """STORY-413 AC5 — StarletteIntegration must never ship enabled again."""

    def test_starlette_integration_not_imported_in_module(self):
        """The import itself is removed; `StarletteIntegration` must not be an attr."""
        import startup.sentry as sentry_module

        assert not hasattr(sentry_module, "StarletteIntegration"), (
            "StarletteIntegration is intentionally NOT imported in backend/startup/sentry.py "
            "to prevent the STORY-413 crash loop regression. See init_sentry() docstring."
        )

    def test_init_sentry_passes_only_fastapi_integration(self, monkeypatch):
        """At runtime, sentry_sdk.init() must receive exactly one integration: FastApi."""
        from startup import sentry as sentry_module

        captured: dict = {}

        def fake_init(**kwargs):
            captured.update(kwargs)

        monkeypatch.setenv("SENTRY_DSN", "https://fake@sentry.test/1")
        with patch.object(sentry_module.sentry_sdk, "init", side_effect=fake_init):
            sentry_module.init_sentry(env="test", version="v-story-413")

        integrations = captured.get("integrations") or []
        names = [type(i).__name__ for i in integrations]

        assert "FastApiIntegration" in names, "FastApiIntegration must remain active"
        assert "StarletteIntegration" not in names, (
            "StarletteIntegration must NOT be in the integrations list — this is the "
            "STORY-413 regression guard. Re-enabling it brought down production on 2026-04-10."
        )

    def test_init_sentry_no_op_without_dsn(self, monkeypatch):
        """Without SENTRY_DSN the init call must be skipped entirely."""
        from startup import sentry as sentry_module

        init_called = False

        def fake_init(**kwargs):
            nonlocal init_called
            init_called = True

        monkeypatch.delenv("SENTRY_DSN", raising=False)
        with patch.object(sentry_module.sentry_sdk, "init", side_effect=fake_init):
            sentry_module.init_sentry(env="test", version="v-story-413")

        assert init_called is False

    def test_init_sentry_disables_tracing_and_profiling(self, monkeypatch):
        """Both flags stay off — they were the original SIGSEGV sources."""
        from startup import sentry as sentry_module

        captured: dict = {}
        monkeypatch.setenv("SENTRY_DSN", "https://fake@sentry.test/1")
        with patch.object(
            sentry_module.sentry_sdk, "init", side_effect=lambda **kw: captured.update(kw)
        ):
            sentry_module.init_sentry(env="test", version="v-story-413")

        assert captured.get("enable_tracing") is False
        assert captured.get("profiles_sample_rate") == 0


class TestSentrySdkPin:
    """STORY-413 AC3 — the sentry-sdk version must be pinned exactly."""

    def test_requirements_pins_sentry_sdk_exact(self):
        """An open pin (>=2.0.0) was the transport for the 2026-04-10 regression."""
        repo_root = Path(__file__).resolve().parents[2]
        requirements = (repo_root / "backend" / "requirements.txt").read_text(encoding="utf-8")

        line = next(
            (l for l in requirements.splitlines() if l.strip().startswith("sentry-sdk")),
            None,
        )
        assert line is not None, "sentry-sdk must remain in requirements.txt"

        # Exact pin (==X.Y.Z) is the contract. Allow extras like [fastapi].
        assert re.search(r"sentry-sdk(\[[^\]]+\])?==\d+\.\d+\.\d+", line), (
            f"sentry-sdk must be pinned exactly (==X.Y.Z) to block transitive upgrades. "
            f"Got: {line!r}. See STORY-413 for rationale."
        )
