"""#2111 onda 1 — freeze de jornada comercial SaaS.

Default: SAAS_COMMERCE_ENABLED=false. Novos checkouts, trials, upgrades e
assinaturas retornam 410. Webhooks, cancelamento e dados históricos ficam
intactos até as ondas 3–4.
"""

from __future__ import annotations

from fastapi import HTTPException

SAAS_COMMERCE_FROZEN_CODE = "SAAS_COMMERCE_FROZEN"
SAAS_COMMERCE_NEXT = "/consultoria-b2g"

FROZEN_DETAIL: dict[str, str] = {
    "error_code": SAAS_COMMERCE_FROZEN_CODE,
    "message": (
        "Novas assinaturas, trials e checkouts estão encerrados. "
        "O SmartLic é o braço público de inbound da CONFENGE."
    ),
    "next": SAAS_COMMERCE_NEXT,
    "issue": "2111",
}


def is_saas_commerce_enabled() -> bool:
    """Runtime-resolved. Registry default is false (ADR-STRAT-001 / #2111)."""
    from config.features import get_feature_flag

    return bool(get_feature_flag("SAAS_COMMERCE_ENABLED"))


def require_saas_commerce() -> None:
    """FastAPI dependency: block new commercial journeys unless explicitly re-enabled."""
    if not is_saas_commerce_enabled():
        raise HTTPException(status_code=410, detail=FROZEN_DETAIL)
