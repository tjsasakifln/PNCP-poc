"""filter package -- DEBT-301 decomposition.

Re-exports everything from sub-modules and core orchestrator
so that ``from filter import X`` continues to work.

Architecture:
  - filter/core.py: Main orchestrator (aplicar_todos_filtros) + legacy monolith
  - filter_basic.py: Basic filter helpers (status, esfera, proximity, red flags)
  - filter_keywords.py: Keyword matching engine (match_keywords, normalize_text, etc.)
  - filter_density.py: Term density scoring
  - filter_llm.py: LLM zero-match classification
  - filter_recovery.py: Zero-results recovery (relaxation, LLM recovery)
  - filter_stats.py: Filter statistics tracking
  - filter_status.py: Status inference
  - filter_uf.py: UF filtering
  - filter_utils.py: Shared filter utilities
  - filter_value.py: Value range filtering
"""

# Sub-modules (decomposed filter_*.py files)
from filter.basic import *  # noqa: F401,F403
from filter.keywords import *  # noqa: F401,F403
from filter.density import *  # noqa: F401,F403
from filter.llm import *  # noqa: F401,F403
from filter.recovery import *  # noqa: F401,F403
from filter.stats import *  # noqa: F401,F403
from filter.status import *  # noqa: F401,F403
from filter.uf import *  # noqa: F401,F403
from filter.utils import *  # noqa: F401,F403
from filter.value import *  # noqa: F401,F403

# Main orchestrator (still in core.py -- 1632-line function)
from filter.core import aplicar_todos_filtros  # noqa: F401

# Private names used by tests/other modules
from filter.keywords import _strip_org_context, _strip_org_context_with_detail, _get_tracker  # noqa: F401
from filter.core import _filter_stats_tracker  # noqa: F401
from filter.core import (  # noqa: F401
    GLOBAL_EXCLUSION_OVERRIDES,
    GLOBAL_EXCLUSIONS,
    GLOBAL_EXCLUSIONS_NORMALIZED,
    _INFRA_EXEMPT_SECTORS,
    _MEDICAL_EXEMPT_SECTORS,
    _ADMIN_EXEMPT_SECTORS,
    RED_FLAGS_PER_SECTOR,
)
