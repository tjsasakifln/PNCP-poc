"""schemas package — DEBT-302 decomposition.

Re-exports everything from submodules so that
``from schemas import X`` continues to work unchanged.
"""

from schemas.common import *  # noqa: F401,F403
from schemas.search import *  # noqa: F401,F403
from schemas.messages import *  # noqa: F401,F403
from schemas.user import *  # noqa: F401,F403
from schemas.health import *  # noqa: F401,F403
from schemas.billing import *  # noqa: F401,F403
from schemas.admin import *  # noqa: F401,F403
from schemas.pipeline import *  # noqa: F401,F403
from schemas.feedback import *  # noqa: F401,F403
from schemas.export import *  # noqa: F401,F403

# Re-export private names used by external code
from schemas.common import (  # noqa: F401
    validate_uuid,
    validate_password,
    validate_plan_id,
    sanitize_search_query,
    UUID_V4_PATTERN,
    PLAN_ID_PATTERN,
    SAFE_SEARCH_PATTERN,
    ERROR_CODES,
    SearchErrorCode,
)

from schemas.pipeline import (  # noqa: F401
    VALID_PIPELINE_STAGES,
    PIPELINE_STAGE_LABELS,
)
