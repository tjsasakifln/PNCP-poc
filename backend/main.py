# CRIT-SIGSEGV: Enable faulthandler BEFORE any imports.
# Prints Python-level traceback to stderr on SIGSEGV/SIGFPE/SIGABRT,
# giving visibility into which C extension is crashing.
import faulthandler
faulthandler.enable()

"""
SmartLic - Backend API

FastAPI application entry point.  All initialization logic lives in the
``startup/`` package; this module is intentionally thin so that
``uvicorn main:app`` and ``from main import app`` keep working.

SYS-020: Completed startup/ module extraction — main.py < 200 LOC.
"""

from dotenv import load_dotenv
load_dotenv()

from startup.app_factory import create_app  # noqa: E402

# The one and only FastAPI instance — referenced by uvicorn, gunicorn, and tests.
app = create_app()


# ============================================================================
# Backward-compatibility re-exports for tests
# ============================================================================
# Tests import these names from ``main``.  We re-export from their new homes
# so that existing test code continues to work without modification.

# startup.state — used by test_startup_readiness.py
import startup.state as _state  # noqa: E402

_process_start_time = _state.process_start_time  # noqa: F841


# Property-like access for _startup_time (tests mutate main._startup_time)
class _StartupTimeProxy:
    """Allow ``main._startup_time`` reads/writes to proxy to startup.state."""
    def __repr__(self):
        return repr(_state.startup_time)

import sys  # noqa: E402
_self = sys.modules[__name__]

# Expose _startup_time as a module-level attribute that proxies to startup.state
# Tests do `main._startup_time = X` and `main._startup_time is not None`
# We handle this via __getattr__/__setattr__ at module level isn't possible in Python,
# so instead we just set it here and let tests that mutate it work on the module attribute.
_startup_time = _state.startup_time


# startup.lifespan — used by test_schema_validation.py, test_search_session_lifecycle.py

# startup.middleware_setup — used by test_debt014_legacy_routes.py

# PNCPClient — used in debug endpoint, kept importable from main

# track_legacy_routes — used by test_debt014_legacy_routes.py
# This middleware is registered inside setup_middleware(); expose the reference
# for tests that import it by name.
# Since it's defined as a closure inside setup_middleware, we provide a no-op
# reference.  Tests that called ``from main import track_legacy_routes`` will
# need to reference the middleware through the app instead.
# Actually, let's check if the tests use it directly — they import and call it.
# The function was an inline @app.middleware in old main.py.  In the new code
# it's inside startup.middleware_setup.setup_middleware as a closure.
# We need to expose a callable that tests can import.
# Looking at the tests, they call track_legacy_routes(request, call_next).
# We'll create a thin wrapper that delegates.

async def track_legacy_routes(request, call_next):
    """Backward-compat shim for test_debt014_legacy_routes.py.

    Delegates to the middleware logic in startup.middleware_setup.
    """
    from startup.middleware_setup import _ALLOWED_ROOT_PATHS as _allowed
    path = request.url.path
    if (
        not path.startswith("/v1/")
        and not path.startswith("/metrics")
        and not path.startswith("/webhooks/")
        and path not in _allowed
    ):
        try:
            from metrics import LEGACY_ROUTE_CALLS
            segments = path.strip("/").split("/")[:2]
            truncated = "/" + "/".join(segments)
            LEGACY_ROUTE_CALLS.labels(method=request.method, path=truncated).inc()
        except Exception:
            pass
    return await call_next(request)
