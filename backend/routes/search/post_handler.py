"""STORY-3.1 (EPIC-TD-2026Q2 / TD-SYS-005): POST /buscar handler — shim.

The actual ``buscar_licitacoes`` definition lives in :mod:`routes.search`
(the package's ``__init__``). Keeping it there is required so unittest.mock
patches like ``@patch("routes.search.SearchPipeline")`` still substitute the
references the handler resolves at call time.

This submodule is kept as a thin shim so the ``routes/search/`` package
still ships the documented module list (``__init__``, ``post_handler``,
``sse``, ``state``, ``status``, ``retry``) — and so any code that already
imports from ``routes.search.post_handler`` keeps working.
"""

from routes.search import (  # noqa: F401
    buscar_licitacoes,
    get_correlation_id,
    _build_error_detail,
    _build_pncp_link,
    _calcular_urgencia,
    _calcular_dias_restantes,
    _convert_to_licitacao_items,
    logger,
    router,
)
