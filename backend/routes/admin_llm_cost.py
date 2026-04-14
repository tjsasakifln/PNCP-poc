"""STORY-2.11 (EPIC-TD-2026Q2 P0): LLM monthly budget admin endpoint.

GET /v1/admin/llm-cost — admin-only JSON snapshot do gasto LLM do mês:
    - month_to_date_usd
    - budget_usd
    - pct_used
    - projected_end_of_month_usd
    - month (chave Redis usada)
    - exceeded (bool — flag de hard-reject está ativa?)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from admin import require_admin
from llm_budget import get_cost_snapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/llm-cost")
async def admin_llm_cost(user: dict = Depends(require_admin)) -> dict[str, Any]:
    """Return LLM cost snapshot para o mês corrente (admin-only).

    Response shape::

        {
            "month_to_date_usd": 42.1234,
            "budget_usd": 100.0,
            "pct_used": 42.12,
            "projected_end_of_month_usd": 78.55,
            "month": "llm_cost_month_2026_04",
            "exceeded": false
        }

    Em caso de Redis indisponível, retorna zeros (graceful degradation).
    """
    return await get_cost_snapshot()
