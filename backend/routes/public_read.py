"""Server-side public_read_v1 surface. No DSN leakage."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from public_read.contract import CONTRACT_FAMILIES, CONTRACT_VERSION, FamilyRead
from public_read.flags import get_public_read_mode, is_kill_switch_on
from public_read.isolation import get_backpressure
from public_read.serve import serve_family

router = APIRouter(prefix="/public-read", tags=["public-read"])

_FAMILY_ALIAS = {
    "tender": "tenders",
    "licitacoes": "tenders",
    "contract": "contracts",
    "contratos": "contracts",
    "company": "suppliers",
    "empresa": "suppliers",
    "fornecedor": "suppliers",
    "supplier": "suppliers",
    "organ": "organs",
    "orgao": "organs",
    "municipality": "municipalities",
    "municipio": "municipalities",
    "entity": "entities",
}


@router.get("/health", response_model=dict)
async def public_read_health() -> dict:
    pressure = get_backpressure().snapshot()
    return {
        "contract_version": CONTRACT_VERSION,
        "mode": get_public_read_mode().value,
        "kill_switch": is_kill_switch_on(),
        "families": list(CONTRACT_FAMILIES),
        "isolation": pressure,
    }


@router.get("/{family}/{public_id}", response_model=FamilyRead)
async def public_read_family(family: str, public_id: str) -> FamilyRead:
    mapped = _FAMILY_ALIAS.get(family, family)
    if mapped not in {
        "tenders",
        "contracts",
        "entities",
        "suppliers",
        "organs",
        "municipalities",
    }:
        raise HTTPException(status_code=404, detail="unknown_family")
    if len(public_id) > 128:
        raise HTTPException(status_code=422, detail="public_id_too_long")
    return serve_family(mapped, public_id)
