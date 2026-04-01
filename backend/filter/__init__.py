"""filter package -- DEBT-201 decomposition.

Re-exports everything from sub-modules so that ``from filter import X``
continues to work (facade pattern).

Architecture:
  - filter/pipeline.py: Main orchestrator (aplicar_todos_filtros)
  - filter/keywords.py: Keyword matching engine (match_keywords, normalize_text, etc.)
  - filter/density.py: Proximity/co-occurrence checks
  - filter/status.py: Status inference + prazo aberto filter
  - filter/uf.py: UF filtering
  - filter/value.py: Value range filtering
  - filter/stats.py: Filter statistics tracking
  - filter/utils.py: Shared filter utilities
"""

# Sub-modules (decomposed filter package)
from filter.keywords import *  # noqa: F401,F403
from filter.density import *  # noqa: F401,F403
from filter.stats import *  # noqa: F401,F403
from filter.status import *  # noqa: F401,F403
from filter.uf import *  # noqa: F401,F403
from filter.utils import *  # noqa: F401,F403
from filter.value import *  # noqa: F401,F403

# Main orchestrator (DEBT-201: extracted from core.py to pipeline.py)
from filter.pipeline import aplicar_todos_filtros  # noqa: F401

# Private names used by tests/other modules
from filter.keywords import _strip_org_context, _strip_org_context_with_detail, _get_tracker  # noqa: F401
from filter.keywords import (  # noqa: F401
    GLOBAL_EXCLUSION_OVERRIDES,
    GLOBAL_EXCLUSIONS,
    GLOBAL_EXCLUSIONS_NORMALIZED,
    _INFRA_EXEMPT_SECTORS,
    _MEDICAL_EXEMPT_SECTORS,
    _ADMIN_EXEMPT_SECTORS,
    RED_FLAGS_PER_SECTOR,
)

# _filter_stats_tracker: lazy singleton, lives in keywords.py (same as _get_tracker)
_filter_stats_tracker = None  # noqa: F401 — kept for backward compat (tests import this name)
