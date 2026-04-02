"""
STORY-301 AC5/AC6/AC8: Alert Service — cron job logic for executing email alerts.

For each active alert:
1. Check rate limit (max 1 email/day per alert) — AC8
2. Execute search against cached results (lightweight, no external API calls)
3. Dedup against alert_sent_items — AC6
4. Send email if new items found — AC5
5. Track sent items for future dedup

Usage (from ARQ worker or cron endpoint):
    from services.alert_service import run_all_alerts
    results = await run_all_alerts()
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from supabase_client import get_supabase, sb_execute

logger = logging.getLogger(__name__)

# Sector ID -> friendly display name mapping (matches sectors_data.yaml)
_SECTOR_NAMES = {
    "vestuario": "Vestuario e Uniformes",
    "alimentos": "Alimentos e Merenda",
    "informatica": "Hardware e Equipamentos de TI",
    "mobiliario": "Mobiliario",
    "papelaria": "Papelaria e Material de Escritorio",
    "engenharia": "Engenharia, Projetos e Obras",
    "software": "Software e Sistemas",
    "facilities": "Facilities e Manutencao",
    "saude": "Saude",
    "vigilancia": "Vigilancia e Seguranca Patrimonial",
    "transporte_servicos": "Transporte de Pessoas e Cargas",
    "frota_veicular": "Frota e Veiculos",
    "manutencao_predial": "Manutencao e Conservacao Predial",
    "engenharia_rodoviaria": "Engenharia Rodoviaria e Infraestrutura Viaria",
    "materiais_eletricos": "Materiais Eletricos e Instalacoes",
    "materiais_hidraulicos": "Materiais Hidraulicos e Saneamento",
}


async def get_active_alerts(db=None) -> list[dict]:
    """Get all active alerts with user info.

    Queries the alerts table for active=true, then enriches each alert
    with profile data (email, full_name) needed for email sending.

    Args:
        db: Supabase client (fetched if None).

    Returns:
        List of dicts with keys: id, user_id, name, filters, email, full_name.
        Empty list on error.
    """
    if db is None:
        db = get_supabase()

    try:
        result = await sb_execute(
            db.table("alerts")
            .select("id, user_id, name, filters, active, created_at")
            .eq("active", True)
        )

        if not result.data:
            logger.debug("No active alerts found")
            return []

        # Enrich with profile data
        enriched = []
        for alert in result.data:
            user_id = alert.get("user_id")
            if not user_id:
                continue

            profile = await _get_user_profile(user_id, db)
            if not profile or not profile.get("email"):
                logger.debug(
                    "Skipping alert %s — no email for user %s",
                    alert["id"][:8],
                    user_id[:8],
                )
                continue

            enriched.append({
                "id": alert["id"],
                "user_id": user_id,
                "name": alert.get("name", ""),
                "filters": alert.get("filters") or {},
                "email": profile["email"],
                "full_name": profile.get("full_name") or profile["email"].split("@")[0],
            })

        logger.info("Found %d active alerts with valid profiles", len(enriched))
        return enriched

    except Exception as e:
        logger.error("Failed to get active alerts: %s", e)
        return []


async def _get_user_profile(user_id: str, db) -> Optional[dict]:
    """Fetch user email and full_name from profiles table.

    Args:
        user_id: User UUID.
        db: Supabase client.

    Returns:
        Dict with email, full_name or None on failure.
    """
    try:
        result = await sb_execute(
            db.table("profiles")
            .select("email, full_name")
            .eq("id", user_id)
            .single()
        )
        return result.data
    except Exception as e:
        logger.warning(
            "Failed to get profile for user %s: %s", user_id[:8], e
        )
        return None


async def execute_alert_search(alert_filters: dict, db=None) -> list[dict]:
    """Simplified search for alert execution.

    Rather than hitting external PNCP/PCP APIs (too heavy for a cron job),
    queries the search_results_cache table for recent results matching
    the alert's filter criteria (setor, UFs, keywords, value range).

    This leverages the fact that SmartLic continuously caches search results
    from active users and background warming jobs.

    Args:
        alert_filters: Dict from alerts.filters JSONB column with keys:
            setor (str), ufs (list[str]), keywords (list[str]),
            valor_min (float), valor_max (float).
        db: Supabase client (fetched if None).

    Returns:
        List of opportunity dicts with normalized keys:
            id, titulo, orgao, valor_estimado, uf, modalidade,
            link_pncp, viability_score.
    """
    if db is None:
        db = get_supabase()

    setor = alert_filters.get("setor", "")
    ufs = alert_filters.get("ufs") or []
    keywords = alert_filters.get("keywords") or []
    valor_min = float(alert_filters.get("valor_min", 0))
    valor_max = float(alert_filters.get("valor_max", 0))

    # Query recent cache entries (last 24h)
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    try:
        query = (
            db.table("search_results_cache")
            .select("results, search_params, created_at")
            .gte("created_at", since.isoformat())
            .order("created_at", desc=True)
            .limit(100)
        )

        result = await sb_execute(query)

        if not result.data:
            logger.debug("No cached results found in last 24h for alert search")
            return []

        # Flatten and filter results
        all_opps: list[dict] = []
        seen_ids: set[str] = set()

        for row in result.data:
            results = row.get("results") or []
            params = row.get("search_params") or {}

            # Filter by setor if alert has a setor filter
            if setor and params.get("setor_id") and params["setor_id"] != setor:
                continue

            for item in results:
                if not isinstance(item, dict):
                    continue

                # Dedup by item ID
                item_id = (
                    item.get("id")
                    or item.get("numeroControlePNCP")
                    or item.get("pncp_id")
                    or ""
                )
                if not item_id:
                    continue
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                # Extract and normalize fields
                item_uf = item.get("uf") or item.get("unidadeFederativa", "")
                item_valor = float(
                    item.get("valorTotalEstimado")
                    or item.get("valor_estimado")
                    or 0
                )
                item_titulo = (
                    item.get("objetoCompra")
                    or item.get("titulo")
                    or "Sem titulo"
                )
                item_modalidade = item.get("modalidade") or item.get(
                    "modalidadeNome", ""
                )
                item_link = item.get("link_pncp") or item.get("linkPncp", "")
                item_orgao = (
                    item.get("nomeOrgao")
                    or item.get("orgao")
                    or "Nao informado"
                )

                # Apply UF filter
                if ufs and item_uf and item_uf not in ufs:
                    continue

                # Apply value range filter
                if valor_min > 0 and item_valor > 0 and item_valor < valor_min:
                    continue
                if valor_max > 0 and item_valor > 0 and item_valor > valor_max:
                    continue

                # Apply keyword filter (case-insensitive substring match)
                if keywords:
                    titulo_lower = item_titulo.lower()
                    orgao_lower = item_orgao.lower()
                    text_to_search = f"{titulo_lower} {orgao_lower}"
                    matched = any(
                        kw.lower() in text_to_search for kw in keywords
                    )
                    if not matched:
                        continue

                all_opps.append({
                    "id": item_id,
                    "titulo": item_titulo,
                    "orgao": item_orgao,
                    "valor_estimado": item_valor,
                    "uf": item_uf,
                    "modalidade": item_modalidade,
                    "link_pncp": item_link,
                    "viability_score": item.get("viability_score"),
                })

        # Sort: viability_score DESC (None at end), then valor_estimado DESC
        all_opps.sort(
            key=lambda x: (
                x.get("viability_score") or 0.0,
                x.get("valor_estimado") or 0.0,
            ),
            reverse=True,
        )

        logger.info(
            "Alert search found %d matching items from cache (setor=%s, ufs=%s)",
            len(all_opps),
            setor or "any",
            ufs or "any",
        )
        return all_opps

    except Exception as e:
        logger.error("Failed to execute alert search: %s", e)
        return []


async def get_sent_item_ids(alert_id: str, db=None) -> set[str]:
    """Get set of item IDs already sent for this alert.

    AC6: Queries alert_sent_items to find items already emailed,
    preventing duplicate notifications.

    Args:
        alert_id: UUID of the alert.
        db: Supabase client (fetched if None).

    Returns:
        Set of item_id strings that have already been sent.
    """
    if db is None:
        db = get_supabase()

    try:
        result = await sb_execute(
            db.table("alert_sent_items")
            .select("item_id")
            .eq("alert_id", alert_id)
        )

        if not result.data:
            return set()

        return {row["item_id"] for row in result.data if row.get("item_id")}

    except Exception as e:
        logger.warning(
            "Failed to get sent items for alert %s: %s", alert_id[:8], e
        )
        return set()


def dedup_results(results: list[dict], sent_ids: set[str]) -> list[dict]:
    """Filter out already-sent items from search results.

    AC6: Compares result IDs against the sent_ids set to ensure
    users never receive duplicate notifications for the same opportunity.

    Args:
        results: List of opportunity dicts (must have "id" key).
        sent_ids: Set of item IDs already sent.

    Returns:
        Filtered list containing only items not in sent_ids.
    """
    if not sent_ids:
        return results

    deduped = []
    for item in results:
        item_id = item.get("id", "")
        if item_id and item_id not in sent_ids:
            deduped.append(item)

    logger.debug(
        "Dedup: %d items in, %d after removing %d already-sent",
        len(results),
        len(deduped),
        len(results) - len(deduped),
    )
    return deduped


async def track_sent_items(
    alert_id: str, item_ids: list[str], db=None
) -> None:
    """Record items as sent to prevent future duplicates.

    AC6: Inserts rows into alert_sent_items for each item_id.
    Uses ON CONFLICT DO NOTHING to handle race conditions gracefully
    (the unique index idx_alert_sent_items_dedup enforces alert_id+item_id).

    Args:
        alert_id: UUID of the alert.
        item_ids: List of item ID strings to record.
        db: Supabase client (fetched if None).
    """
    if not item_ids:
        return

    if db is None:
        db = get_supabase()

    now = datetime.now(timezone.utc).isoformat()

    try:
        # Batch insert — Supabase upsert with ignoreDuplicates handles conflicts
        rows = [
            {"alert_id": alert_id, "item_id": iid, "sent_at": now}
            for iid in item_ids
        ]
        await sb_execute(
            db.table("alert_sent_items").upsert(
                rows, on_conflict="alert_id,item_id"
            )
        )
        logger.debug(
            "Tracked %d sent items for alert %s", len(item_ids), alert_id[:8]
        )
    except Exception as e:
        logger.warning(
            "Failed to track sent items for alert %s: %s", alert_id[:8], e
        )


async def check_rate_limit(alert_id: str, db=None) -> bool:
    """Check if alert has already been sent today.

    AC8: Max 1 email per day per alert. Checks alert_sent_items for any
    items sent in the last 20 hours (same 20h buffer as digest_service.py
    to avoid timezone edge cases).

    Args:
        alert_id: UUID of the alert.
        db: Supabase client (fetched if None).

    Returns:
        True if the alert is rate-limited (should NOT send).
        False if it is safe to send.
    """
    if db is None:
        db = get_supabase()

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=20)).isoformat()

    try:
        result = await sb_execute(
            db.table("alert_sent_items")
            .select("id", count="exact")
            .eq("alert_id", alert_id)
            .gte("sent_at", cutoff)
            .limit(1)
        )

        count = result.count if hasattr(result, "count") and result.count is not None else len(result.data or [])
        is_limited = count > 0

        if is_limited:
            logger.debug(
                "Alert %s rate-limited — already sent within last 20h",
                alert_id[:8],
            )

        return is_limited

    except Exception as e:
        logger.warning(
            "Rate limit check failed for alert %s: %s — allowing send",
            alert_id[:8],
            e,
        )
        # Fail open: allow the send rather than silently suppressing alerts
        return False


async def process_single_alert(alert: dict, db=None) -> dict:
    """Process a single alert: search, dedup, return payload for sending.

    AC5: Core cron job logic for one alert.

    Args:
        alert: Dict from get_active_alerts() with keys:
            id, user_id, name, filters, email, full_name.
        db: Supabase client (fetched if None).

    Returns:
        Dict with keys:
            alert_id, user_id, email, full_name, alert_name,
            opportunities (deduped list), total_count, skipped (bool),
            skip_reason (str or None).
    """
    if db is None:
        db = get_supabase()

    alert_id = alert["id"]
    result_payload = {
        "alert_id": alert_id,
        "user_id": alert["user_id"],
        "email": alert["email"],
        "full_name": alert["full_name"],
        "alert_name": alert.get("name") or _resolve_alert_name(alert.get("filters", {})),
        "opportunities": [],
        "total_count": 0,
        "skipped": False,
        "skip_reason": None,
    }

    # AC8: Rate limit check
    if await check_rate_limit(alert_id, db):
        result_payload["skipped"] = True
        result_payload["skip_reason"] = "rate_limited"
        return result_payload

    # Execute search against cache
    raw_results = await execute_alert_search(alert.get("filters", {}), db)

    if not raw_results:
        result_payload["skipped"] = True
        result_payload["skip_reason"] = "no_results"
        return result_payload

    # AC6: Dedup against previously sent items
    sent_ids = await get_sent_item_ids(alert_id, db)
    new_results = dedup_results(raw_results, sent_ids)

    if not new_results:
        result_payload["skipped"] = True
        result_payload["skip_reason"] = "all_already_sent"
        return result_payload

    result_payload["opportunities"] = new_results
    result_payload["total_count"] = len(new_results)

    return result_payload


async def finalize_alert_send(
    alert_id: str, item_ids: list[str], db=None
) -> None:
    """Record that an alert email was successfully sent.

    Call this AFTER the email is confirmed sent to track items
    for dedup and update the send timestamp.

    Args:
        alert_id: UUID of the alert.
        item_ids: List of item IDs included in the sent email.
        db: Supabase client (fetched if None).
    """
    if db is None:
        db = get_supabase()

    await track_sent_items(alert_id, item_ids, db)


def _resolve_alert_name(filters: dict) -> str:
    """Derive a display name from alert filters when alert.name is empty.

    Falls back to sector name, then "suas licitacoes".

    Args:
        filters: The alert's filters JSONB dict.

    Returns:
        Human-readable alert name string.
    """
    setor = filters.get("setor", "")
    if setor and setor in _SECTOR_NAMES:
        return _SECTOR_NAMES[setor]
    if setor:
        return setor
    return "suas licitacoes"


async def run_all_alerts(db=None) -> dict:
    """Execute all active alerts — main entry point for cron job.

    AC5: For each active alert:
    1. Check rate limit (AC8)
    2. Search cached results
    3. Dedup (AC6)
    4. Return payloads ready for email sending

    The caller (ARQ worker or cron endpoint) is responsible for
    actually sending the emails using the returned payloads and
    calling finalize_alert_send() after each successful send.

    Args:
        db: Supabase client (fetched if None).

    Returns:
        Dict with keys:
            total_alerts (int): Total active alerts processed.
            sent (int): Alerts with new items to send.
            skipped (int): Alerts skipped (rate limited, no results, etc.).
            errors (int): Alerts that failed processing.
            payloads (list[dict]): List of result dicts from process_single_alert
                for alerts that have new items (skipped=False).
    """
    if db is None:
        db = get_supabase()

    summary = {
        "total_alerts": 0,
        "sent": 0,
        "skipped": 0,
        "errors": 0,
        "payloads": [],
    }

    alerts = await get_active_alerts(db)
    summary["total_alerts"] = len(alerts)

    if not alerts:
        logger.info("No active alerts to process")
        return summary

    for alert in alerts:
        try:
            payload = await process_single_alert(alert, db)

            if payload.get("skipped"):
                summary["skipped"] += 1
                logger.debug(
                    "Alert %s skipped: %s",
                    alert["id"][:8],
                    payload.get("skip_reason"),
                )
            else:
                summary["sent"] += 1
                summary["payloads"].append(payload)
                logger.info(
                    "Alert %s ready: %d new items for %s",
                    alert["id"][:8],
                    payload["total_count"],
                    alert["email"],
                )

        except Exception as e:
            summary["errors"] += 1
            logger.error(
                "Failed to process alert %s: %s", alert["id"][:8], e
            )

    logger.info(
        "Alert run complete: %d total, %d to send, %d skipped, %d errors",
        summary["total_alerts"],
        summary["sent"],
        summary["skipped"],
        summary["errors"],
    )

    return summary


async def cleanup_old_sent_items(days: int = 90, db=None) -> int:
    """Remove old alert_sent_items records to prevent table bloat.

    Should be called periodically (e.g., weekly) from a maintenance job.

    Args:
        days: Delete records older than this many days.
        db: Supabase client (fetched if None).

    Returns:
        Number of records deleted (approximate).
    """
    if db is None:
        db = get_supabase()

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        result = await sb_execute(
            db.table("alert_sent_items")
            .delete()
            .lt("sent_at", cutoff)
        )
        count = len(result.data) if result.data else 0
        logger.info("Cleaned up %d old alert_sent_items (older than %d days)", count, days)
        return count
    except Exception as e:
        logger.error("Failed to cleanup old alert_sent_items: %s", e)
        return 0
