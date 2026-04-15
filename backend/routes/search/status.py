"""STORY-3.1 (EPIC-TD-2026Q2): Search status / results / timeline / regenerate-excel.

Thin re-export of routes.search_status for the package-style import path.
The flat module remains the canonical implementation; retry/cancel endpoints
are surfaced from .retry instead.
"""

from routes.search_status import (  # noqa: F401
    _verify_search_ownership,
    search_status_endpoint,
    search_timeline_endpoint,
    get_search_results,
    get_search_results_v1,
    get_zero_match_results_endpoint,
    regenerate_excel_endpoint,
    router,
)
