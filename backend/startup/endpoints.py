"""startup/endpoints.py — Root-level endpoint definitions (DEBT-107).

Endpoints that live directly on the app (not inside a router):
  GET /             — API root / navigation
  GET /v1/setores   — Sector list for frontend dropdown
  GET /debug/pncp-test — Admin diagnostic for PNCP API connectivity (admin only)
"""

import os

from fastapi import Depends, FastAPI

from schemas import RootResponse, SetoresResponse, DebugPNCPResponse
from sectors import list_sectors

APP_VERSION = os.getenv("APP_VERSION", "dev")


def register_endpoints(app: FastAPI) -> None:
    """Attach root endpoints to *app* (excluding /debug/pncp-test, see module docstring)."""

    @app.get("/", response_model=RootResponse)
    async def root():
        """API root — navigation and version info."""
        return {
            "name": "SmartLic API",
            "version": APP_VERSION,
            "api_version": "v1",
            "description": "API para busca e análise de licitações em fontes oficiais",
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "openapi": "/openapi.json",
                "v1_api": "/v1",
            },
            "versioning": {
                "current": "v1",
                "supported": ["v1"],
                "deprecated": [],
                "note": "All endpoints at /v1/<endpoint>. Legacy root paths removed (TD-004).",
            },
            "status": "operational",
        }

    @app.get("/v1/setores", response_model=SetoresResponse)
    async def listar_setores():
        """Return available procurement sectors for frontend dropdown."""
        return {"setores": list_sectors()}

    # STORY-210 AC9: Admin-only debug endpoint
    from admin import require_admin as _require_admin

    @app.get("/debug/pncp-test", response_model=DebugPNCPResponse)
    async def debug_pncp_test(admin: dict = Depends(_require_admin)):
        """Diagnostic: test if PNCP API is reachable from this server. Admin only."""
        import time as t
        from datetime import date, timedelta
        from pncp_client import PNCPClient

        start = t.time()
        try:
            client = PNCPClient()
            hoje = date.today()
            tres_dias = hoje - timedelta(days=3)
            response = client.fetch_page(
                data_inicial=tres_dias.strftime("%Y-%m-%d"),
                data_final=hoje.strftime("%Y-%m-%d"),
                modalidade=6,
                pagina=1,
                tamanho=10,
            )
            elapsed = int((t.time() - start) * 1000)
            return {
                "success": True,
                "total_registros": response.get("totalRegistros", 0),
                "items_returned": len(response.get("data", [])),
                "elapsed_ms": elapsed,
            }
        except Exception as e:
            elapsed = int((t.time() - start) * 1000)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "elapsed_ms": elapsed,
            }
