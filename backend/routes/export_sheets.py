"""
Google Sheets export routes.

Endpoints:
- POST /api/export/google-sheets - Export results to Google Sheets
- GET /api/export/google-sheets/history - Get user's export history

STORY-180: Google Sheets Export
"""

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import require_auth
from oauth import get_user_google_token
from google_sheets import GoogleSheetsExporter
from schemas import (
    GoogleSheetsExportRequest,
    GoogleSheetsExportResponse,
    GoogleSheetsExportHistory,
    GoogleSheetsExportHistoryResponse
)
from supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["export"])


# ============================================================================
# Export Endpoints
# ============================================================================

@router.post("/google-sheets", response_model=GoogleSheetsExportResponse)
async def export_to_google_sheets(
    request: GoogleSheetsExportRequest,
    user: dict = Depends(require_auth)
) -> GoogleSheetsExportResponse:
    """
    Export search results to Google Sheets.

    Creates a new Google Sheets spreadsheet or updates an existing one
    with search results. Applies professional formatting (green header,
    currency symbols, hyperlinks).

    Request Body:
        {
            "licitacoes": [...],
            "title": "SmartLic - Uniformes - 09/02/2026",
            "mode": "create" | "update",
            "spreadsheet_id": "optional for update mode"
        }

    Returns:
        {
            "success": true,
            "spreadsheet_id": "...",
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
            "total_rows": 142,
            "updated_at": "2026-02-09T15:30:00Z"  // only for update mode
        }

    Errors:
        401 Unauthorized: User hasn't authorized Google Sheets
        403 Forbidden: Token revoked or insufficient permissions
        429 Too Many Requests: Google API quota exceeded
        500 Internal Server Error: Google API error

    Example:
        POST /api/export/google-sheets
        {
            "licitacoes": [...],
            "title": "SmartLic - Uniformes - SP, RJ",
            "mode": "create"
        }
    """
    try:
        logger.info(
            f"Google Sheets export requested by user {user['id'][:8]}: "
            f"{len(request.licitacoes)} rows, mode={request.mode}"
        )

        # 1. Get user's Google access token (with auto-refresh)
        access_token = await get_user_google_token(user["id"])

        if not access_token:
            logger.warning(f"No Google OAuth token for user {user['id'][:8]}")
            raise HTTPException(
                status_code=401,
                detail="Google Sheets não autorizado. Por favor, conecte sua conta Google."
            )

        # 2. Create exporter with user's token
        exporter = GoogleSheetsExporter(access_token)

        # 3. Execute export (create or update)
        if request.mode == "create":
            result = await exporter.create_spreadsheet(
                licitacoes=request.licitacoes,
                title=request.title
            )
        else:  # update
            result = await exporter.update_spreadsheet(
                spreadsheet_id=request.spreadsheet_id,
                licitacoes=request.licitacoes
            )

        # 4. Save export history to database
        await _save_export_history(
            user_id=user["id"],
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            search_params={
                "title": request.title,
                "mode": request.mode,
                "total_rows": result["total_rows"]
            },
            total_rows=result["total_rows"]
        )

        logger.info(
            f"Google Sheets export completed: {result['spreadsheet_id']} "
            f"({result['total_rows']} rows)"
        )

        return GoogleSheetsExportResponse(
            success=True,
            **result
        )

    except HTTPException:
        # Re-raise FastAPI exceptions (401, 403, 429, 500)
        raise

    except Exception as e:
        logger.error(f"Unexpected export error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao exportar para Google Sheets: {str(e)}"
        )


@router.get("/google-sheets/history", response_model=GoogleSheetsExportHistoryResponse)
async def get_export_history(
    limit: int = 50,
    user: dict = Depends(require_auth)
) -> GoogleSheetsExportHistoryResponse:
    """
    Get user's Google Sheets export history.

    Returns list of all exports with spreadsheet URLs and search parameters.
    Useful for "re-open last export" and usage analytics.

    Query Parameters:
        limit: Maximum number of exports to return (default: 50, max: 100)

    Returns:
        {
            "exports": [
                {
                    "id": "uuid",
                    "spreadsheet_id": "...",
                    "spreadsheet_url": "https://docs.google.com/...",
                    "search_params": {"ufs": ["SP"], "setor": "Uniformes"},
                    "total_rows": 142,
                    "created_at": "2026-02-09T15:30:00Z",
                    "last_updated_at": "2026-02-09T15:30:00Z"
                }
            ],
            "total": 1
        }

    Example:
        GET /api/export/google-sheets/history?limit=20
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100

        # Query export history
        sb = get_supabase()

        result = sb.table("google_sheets_exports")\
            .select("*")\
            .eq("user_id", user["id"])\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        # Map to response model
        exports = [
            GoogleSheetsExportHistory(
                id=export["id"],
                spreadsheet_id=export["spreadsheet_id"],
                spreadsheet_url=export["spreadsheet_url"],
                search_params=export["search_params"],
                total_rows=export["total_rows"],
                created_at=export["created_at"],
                last_updated_at=export["last_updated_at"]
            )
            for export in result.data
        ]

        logger.info(f"Fetched {len(exports)} exports for user {user['id'][:8]}")

        return GoogleSheetsExportHistoryResponse(
            exports=exports,
            total=len(exports)
        )

    except Exception as e:
        logger.error(f"Failed to fetch export history: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch export history. Try again."
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def _save_export_history(
    user_id: str,
    spreadsheet_id: str,
    spreadsheet_url: str,
    search_params: dict,
    total_rows: int
) -> None:
    """
    Save export to history table.

    Args:
        user_id: Supabase user UUID
        spreadsheet_id: Google Sheets ID
        spreadsheet_url: Full shareable URL
        search_params: Search parameters snapshot
        total_rows: Number of rows exported

    Raises:
        Exception: Database error (logged but not raised to avoid breaking export)
    """
    try:
        sb = get_supabase()

        sb.table("google_sheets_exports").insert({
            "user_id": user_id,
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": spreadsheet_url,
            "search_params": search_params,
            "total_rows": total_rows,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated_at": datetime.now(timezone.utc).isoformat()
        }).execute()

        logger.debug(f"Saved export history for spreadsheet {spreadsheet_id}")

    except Exception as e:
        # Log error but don't fail export
        logger.error(f"Failed to save export history: {type(e).__name__}")
