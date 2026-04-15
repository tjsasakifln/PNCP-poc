"""STORY-3.1 (EPIC-TD-2026Q2): SSE progress stream submodule.

Thin re-export of routes.search_sse for the new routes/search/ package.

The flat module routes/search_sse.py remains the canonical implementation so
existing test patches like ``@patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL")``
keep working untouched. New code may import from ``routes.search.sse`` for the
package-style API.
"""

from routes.search_sse import (  # noqa: F401
    _SSE_HEARTBEAT_INTERVAL,
    _SSE_WAIT_HEARTBEAT_EVERY,
    _SSE_TRACKER_WAIT_TIMEOUT_S,
    _SSE_POLL_INTERVAL,
    _SSE_POLLS_PER_HEARTBEAT,
    buscar_progress_stream,
    router,
)
