"""
STORY-278 AC2: Digest Service — builds per-user opportunity digest.

Queries search_results_cache filtered by user's profile_context (setor + UFs),
returns top N opportunities sorted by viability_score.

Usage:
    from services.digest_service import build_digest_for_user

    opportunities = await build_digest_for_user(user_id, max_items=10)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from supabase_client import sb_execute

logger = logging.getLogger(__name__)


async def _get_user_profile_context(user_id: str, db) -> Optional[dict]:
    """Fetch user's profile_context from profiles table.

    Returns:
        Dict with context_data keys (setor_id, ufs_atuacao, etc.) or None.
    """
    try:
        result = await sb_execute(
            db.table("profiles").select(
                "context_data"
            ).eq("id", user_id).single()
        )
        return (result.data or {}).get("context_data") or {}
    except Exception as e:
        logger.warning(f"Failed to get profile context for digest: user_id={user_id[:8]}, error={e}")
        return None


async def _get_alert_preferences(user_id: str, db) -> Optional[dict]:
    """Fetch user's alert preferences.

    Returns:
        Dict with frequency, enabled, last_digest_sent_at or None.
    """
    try:
        result = await sb_execute(
            db.table("alert_preferences").select(
                "frequency, enabled, last_digest_sent_at"
            ).eq("user_id", user_id).single()
        )
        return result.data
    except Exception:
        return None


def _is_digest_due(prefs: dict) -> bool:
    """Check if user is due for a digest based on frequency and last sent time.

    Args:
        prefs: Alert preferences dict with frequency and last_digest_sent_at.

    Returns:
        True if digest should be sent now.
    """
    if not prefs.get("enabled", True):
        return False

    frequency = prefs.get("frequency", "daily")
    if frequency not in ("daily", "twice_weekly", "weekly"):
        return False

    last_sent_str = prefs.get("last_digest_sent_at")
    if not last_sent_str:
        return True  # Never sent — always due

    try:
        if isinstance(last_sent_str, str):
            # Handle ISO format with timezone
            last_sent = datetime.fromisoformat(last_sent_str.replace("Z", "+00:00"))
        else:
            last_sent = last_sent_str
    except (ValueError, TypeError):
        return True  # Can't parse — send anyway

    now = datetime.now(timezone.utc)
    elapsed = now - last_sent

    if frequency == "daily":
        return elapsed >= timedelta(hours=20)  # 20h buffer to avoid timezone edge cases
    elif frequency == "twice_weekly":
        return elapsed >= timedelta(days=3)  # ~2x per week = every 3-4 days
    elif frequency == "weekly":
        return elapsed >= timedelta(days=6)  # 6-day buffer
    else:
        return False


async def _query_recent_opportunities(
    db,
    setor_id: str | None,
    ufs: list[str] | None,
    since: datetime | None,
    max_items: int = 10,
) -> list[dict]:
    """Query search_results_cache for recent opportunities matching user profile.

    Args:
        db: Supabase client.
        setor_id: User's sector ID filter.
        ufs: User's UFs filter.
        since: Only include results newer than this timestamp.
        max_items: Max opportunities to return.

    Returns:
        List of opportunity dicts.
    """
    try:
        query = db.table("search_results_cache").select(
            "results, search_params, created_at"
        ).order("created_at", desc=True).limit(50)

        if since:
            query = query.gte("created_at", since.isoformat())

        result = await sb_execute(query)

        if not result.data:
            return []

        # Flatten all results and filter by setor/UFs
        all_opps = []
        seen_ids = set()

        for row in result.data:
            results = row.get("results") or []
            params = row.get("search_params") or {}

            # Filter by setor if user has one
            if setor_id and params.get("setor_id") and params["setor_id"] != setor_id:
                continue

            for item in results:
                if not isinstance(item, dict):
                    continue

                # Dedup by PNCP ID or object hash
                item_id = item.get("id") or item.get("numeroControlePNCP") or id(item)
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                # Filter by UF if user has UF preference
                item_uf = item.get("uf") or item.get("unidadeFederativa", "")
                if ufs and item_uf and item_uf not in ufs:
                    continue

                all_opps.append({
                    "titulo": item.get("objetoCompra") or item.get("titulo") or "Sem titulo",
                    "orgao": item.get("nomeOrgao") or item.get("orgao") or "Nao informado",
                    "valor_estimado": float(item.get("valorTotalEstimado") or 0),
                    "uf": item_uf,
                    "viability_score": item.get("viability_score"),
                    "data_publicacao": item.get("dataPublicacaoPncp") or item.get("data_publicacao"),
                })

        # Sort: viability_score DESC (None at end), then valor_estimado DESC
        all_opps.sort(
            key=lambda x: (
                x.get("viability_score") or 0.0,
                x.get("valor_estimado") or 0.0,
            ),
            reverse=True,
        )

        return all_opps[:max_items]

    except Exception as e:
        logger.error(f"Failed to query opportunities for digest: {e}")
        return []


async def build_digest_for_user(
    user_id: str,
    db=None,
    max_items: int = 10,
) -> dict | None:
    """Build a digest payload for a single user.

    STORY-278 AC2: Main entry point for digest generation.

    Args:
        user_id: User UUID.
        db: Supabase client (fetched if None).
        max_items: Max opportunities per digest email.

    Returns:
        Dict with keys: user_name, opportunities, stats, email.
        None if user is not due for digest or has no profile.
    """
    if db is None:
        from supabase_client import get_supabase
        db = get_supabase()

    # Check alert preferences
    prefs = await _get_alert_preferences(user_id, db)
    if prefs and not _is_digest_due(prefs):
        return None

    # Get profile context
    profile_ctx = await _get_user_profile_context(user_id, db)
    if profile_ctx is None:
        return None

    setor_id = profile_ctx.get("setor_id")
    ufs = profile_ctx.get("ufs_atuacao")

    # Determine time window
    last_sent_str = (prefs or {}).get("last_digest_sent_at")
    if last_sent_str:
        try:
            since = datetime.fromisoformat(
                last_sent_str.replace("Z", "+00:00") if isinstance(last_sent_str, str) else str(last_sent_str)
            )
        except (ValueError, TypeError):
            since = datetime.now(timezone.utc) - timedelta(days=1)
    else:
        since = datetime.now(timezone.utc) - timedelta(days=1)

    # Query opportunities
    opportunities = await _query_recent_opportunities(
        db=db,
        setor_id=setor_id,
        ufs=ufs,
        since=since,
        max_items=max_items,
    )

    # Get user email and name
    try:
        user_data = db.auth.admin.get_user_by_id(user_id)
        email = user_data.user.email if user_data and user_data.user else None
        user_name = email.split("@")[0] if email else "Usuario"
    except Exception:
        email = None
        user_name = "Usuario"

    if not email:
        logger.debug(f"No email found for user {user_id[:8]} — skipping digest")
        return None

    # Calculate stats
    total_valor = sum(opp.get("valor_estimado", 0) for opp in opportunities)
    setor_nome = setor_id or "seu setor"

    # Map sector IDs to friendly names (subset)
    _SECTOR_NAMES = {
        "vestuario": "Vestuario e Uniformes",
        "alimentos": "Alimentos",
        "informatica": "TI e Hardware",
        "software": "Software e Sistemas",
        "engenharia": "Engenharia",
        "saude": "Saude",
        "facilities": "Facilities",
        "mobiliario": "Mobiliario",
    }
    setor_nome = _SECTOR_NAMES.get(setor_id, setor_id or "seu setor")

    return {
        "user_id": user_id,
        "user_name": user_name,
        "email": email,
        "opportunities": opportunities,
        "stats": {
            "total_novas": len(opportunities),
            "setor_nome": setor_nome,
            "total_valor": total_valor,
        },
    }


async def get_digest_eligible_users(db=None) -> list[dict]:
    """Query all users eligible for digest right now.

    Returns list of dicts with user_id, frequency, last_digest_sent_at.
    """
    if db is None:
        from supabase_client import get_supabase
        db = get_supabase()

    try:
        result = await sb_execute(
            db.table("alert_preferences").select(
                "user_id, frequency, enabled, last_digest_sent_at"
            ).eq("enabled", True).neq("frequency", "off")
        )

        if not result.data:
            return []

        # Filter by schedule
        eligible = []
        for prefs in result.data:
            if _is_digest_due(prefs):
                eligible.append(prefs)

        return eligible
    except Exception as e:
        logger.error(f"Failed to query eligible digest users: {e}")
        return []


async def mark_digest_sent(user_id: str, db=None) -> None:
    """Update last_digest_sent_at after successful send."""
    if db is None:
        from supabase_client import get_supabase
        db = get_supabase()

    try:
        now = datetime.now(timezone.utc)
        await sb_execute(
            db.table("alert_preferences").update({
                "last_digest_sent_at": now.isoformat(),
            }).eq("user_id", user_id)
        )
    except Exception as e:
        logger.warning(f"Failed to update last_digest_sent_at for {user_id[:8]}: {e}")
