"""jobs.queue.jobs — All ARQ job function implementations."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


async def llm_summary_job(ctx: dict, search_id: str, licitacoes: list, sector_name: str, termos_busca: str | None = None, **kwargs) -> dict:
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))

    from llm import gerar_resumo, gerar_resumo_fallback
    from progress import get_tracker
    from jobs.queue.result_store import persist_job_result

    logger.info(f"[LLM Job] search_id={search_id}, bids={len(licitacoes)}, sector={sector_name}")
    _setor_id = kwargs.get("setor_id")
    try:
        resumo = gerar_resumo(licitacoes, sector_name=sector_name, termos_busca=termos_busca, setor_id=_setor_id)
    except Exception as e:
        logger.warning(f"[LLM Job] LLM failed ({type(e).__name__}), using fallback: {e}")
        resumo = gerar_resumo_fallback(licitacoes, sector_name=sector_name, termos_busca=termos_busca)

    resumo.total_oportunidades = len(licitacoes)
    resumo.valor_total = sum(lic.get("valorTotalEstimado", 0) or 0 for lic in licitacoes)
    from llm import _ground_truth_summary, recompute_temporal_alerts
    _ground_truth_summary(resumo)
    recompute_temporal_alerts(resumo, licitacoes)

    result_data = resumo.model_dump()
    await persist_job_result(search_id, "resumo_json", result_data)
    tracker = await get_tracker(search_id)
    if tracker:
        await tracker.emit("llm_ready", 85, "Resumo pronto", resumo=result_data)
    return result_data


async def excel_generation_job(ctx: dict, search_id: str, licitacoes: list, allow_excel: bool, **kwargs) -> dict:
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))

    from excel import create_excel
    from storage import upload_excel
    from progress import get_tracker
    from jobs.queue.result_store import persist_job_result, _update_results_excel_url

    logger.info(f"[Excel Job] search_id={search_id}, bids={len(licitacoes)}, allow={allow_excel}")

    if not allow_excel:
        result = {"excel_status": "skipped", "download_url": None}
        await persist_job_result(search_id, "excel_result", result)
        return result

    download_url = None
    try:
        excel_buffer = create_excel(licitacoes)
        storage_result = upload_excel(excel_buffer.read(), search_id)
        if storage_result:
            download_url = storage_result["signed_url"]
        else:
            logger.error("[Excel Job] Storage upload returned None")
    except Exception as e:
        logger.error(f"[Excel Job] Generation/upload failed: {e}", exc_info=True)

    excel_status = "ready" if download_url else "failed"
    result = {"excel_status": excel_status, "download_url": download_url}
    await persist_job_result(search_id, "excel_result", result)
    if download_url:
        await _update_results_excel_url(search_id, download_url)

    tracker = await get_tracker(search_id)
    if tracker:
        if download_url:
            await tracker.emit("excel_ready", 98, "Planilha pronta para download", download_url=download_url)
        else:
            await tracker.emit("excel_ready", 98, "Erro ao gerar planilha. Tente novamente.", excel_status="failed")
    return result


async def bid_analysis_job(ctx: dict, search_id: str, licitacoes: list, user_profile: dict | None = None, sector_name: str = "", **kwargs) -> dict:
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))
    from bid_analyzer import batch_analyze_bids
    from progress import get_tracker
    from jobs.queue.result_store import persist_job_result

    logger.info(f"[BidAnalysis Job] search_id={search_id}, bids={len(licitacoes)}, sector={sector_name}")
    try:
        result_data = [r.model_dump() for r in batch_analyze_bids(bids=licitacoes, user_profile=user_profile, sector_name=sector_name)]
    except Exception as e:
        logger.warning(f"[BidAnalysis Job] Failed ({type(e).__name__}): {e}")
        result_data = []

    await persist_job_result(search_id, "bid_analysis", result_data)
    tracker = await get_tracker(search_id)
    if tracker:
        await tracker.emit("bid_analysis_ready", 90, "Análise de editais pronta", bid_analysis=result_data)
    return {"status": "completed", "count": len(result_data)}


async def daily_digest_job(ctx: dict) -> dict:
    import uuid as _uuid
    from config import DIGEST_ENABLED, DIGEST_MAX_PER_EMAIL, DIGEST_BATCH_SIZE
    from metrics import DIGEST_EMAILS_SENT, DIGEST_JOB_DURATION

    cycle_id = str(_uuid.uuid4())[:8]
    start = time.monotonic()

    if not DIGEST_ENABLED:
        return {"status": "disabled", "cycle_id": cycle_id}

    stats = {"cycle_id": cycle_id, "users_queried": 0, "emails_sent": 0, "emails_failed": 0, "emails_skipped": 0}

    try:
        from supabase_client import get_supabase
        db = get_supabase()
    except Exception as e:
        logger.error(f"[Digest {cycle_id}] Supabase unavailable: {e}")
        return {"status": "db_unavailable", **stats}

    try:
        from services.digest_service import get_digest_eligible_users, build_digest_for_user, mark_digest_sent
        from templates.emails.digest import render_daily_digest_email
        from email_service import send_batch_email

        eligible = await get_digest_eligible_users(db)
        stats["users_queried"] = len(eligible)
        if not eligible:
            DIGEST_JOB_DURATION.observe(time.monotonic() - start)
            return {"status": "no_users", **stats}

        batch_messages = []
        user_ids_in_batch = []

        for user_prefs in eligible:
            user_id = user_prefs["user_id"]
            try:
                digest = await build_digest_for_user(user_id=user_id, db=db, max_items=DIGEST_MAX_PER_EMAIL)
                if not digest or not digest.get("email"):
                    stats["emails_skipped"] += 1
                    DIGEST_EMAILS_SENT.labels(status="skipped").inc()
                    continue
                html = render_daily_digest_email(user_name=digest["user_name"], opportunities=digest["opportunities"], stats=digest["stats"])
                batch_messages.append({"to": digest["email"], "subject": f"{digest['stats']['total_novas']} oportunidades no seu setor — SmartLic", "html": html, "tags": [{"name": "category", "value": "digest"}, {"name": "cycle_id", "value": cycle_id}]})
                user_ids_in_batch.append(user_id)
            except Exception as e:
                stats["emails_failed"] += 1
                DIGEST_EMAILS_SENT.labels(status="failed").inc()
                logger.warning(f"[Digest {cycle_id}] Failed to build digest for {user_id[:8]}: {e}")

        if not batch_messages:
            DIGEST_JOB_DURATION.observe(time.monotonic() - start)
            return {"status": "no_messages", **stats}

        for batch_start in range(0, len(batch_messages), DIGEST_BATCH_SIZE):
            batch_end = min(batch_start + DIGEST_BATCH_SIZE, len(batch_messages))
            batch_slice = batch_messages[batch_start:batch_end]
            batch_user_ids = user_ids_in_batch[batch_start:batch_end]
            result = send_batch_email(batch_slice, idempotency_key=f"digest-{cycle_id}-{batch_start}")
            if result is not None:
                stats["emails_sent"] += len(batch_slice)
                DIGEST_EMAILS_SENT.labels(status="success").inc(len(batch_slice))
                for uid in batch_user_ids:
                    await mark_digest_sent(uid, db)
            else:
                stats["emails_failed"] += len(batch_slice)
                DIGEST_EMAILS_SENT.labels(status="failed").inc(len(batch_slice))

    except Exception as e:
        logger.error(f"[Digest {cycle_id}] Unexpected error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), **stats}

    duration_s = time.monotonic() - start
    stats["duration_ms"] = int(duration_s * 1000)
    DIGEST_JOB_DURATION.observe(duration_s)
    logger.info(json.dumps({"event": "digest_sent", **stats}))
    return {"status": "completed", **stats}


async def email_alerts_job(ctx: dict) -> dict:
    import uuid as _uuid
    from config import ALERTS_ENABLED, ALERTS_MAX_PER_EMAIL

    cycle_id = str(_uuid.uuid4())[:8]
    start = time.monotonic()

    if not ALERTS_ENABLED:
        return {"status": "disabled", "cycle_id": cycle_id}

    stats = {"cycle_id": cycle_id, "total_alerts": 0, "emails_sent": 0, "emails_failed": 0, "emails_skipped": 0}

    try:
        from supabase_client import get_supabase
        db = get_supabase()
    except Exception as e:
        return {"status": "db_unavailable", **stats}

    try:
        from services.alert_service import run_all_alerts, finalize_alert_send
        from templates.emails.alert_digest import render_alert_digest_email, get_alert_digest_subject
        from routes.alerts import get_alert_unsubscribe_url
        from email_service import send_email

        summary = await run_all_alerts(db)
        stats["total_alerts"] = summary["total_alerts"]
        stats["emails_skipped"] = summary["skipped"]

        if not summary["payloads"]:
            return {"status": "no_messages", **stats}

        for payload in summary["payloads"]:
            alert_id = payload["alert_id"]
            opps = payload["opportunities"][:ALERTS_MAX_PER_EMAIL]
            try:
                unsubscribe_url = get_alert_unsubscribe_url(alert_id)
                html = render_alert_digest_email(user_name=payload["full_name"], alert_name=payload["alert_name"], opportunities=opps, total_count=payload["total_count"], unsubscribe_url=unsubscribe_url)
                subject = get_alert_digest_subject(payload["total_count"], payload["alert_name"])
                result = send_email(to=payload["email"], subject=subject, html=html, tags=[{"name": "category", "value": "alert"}, {"name": "alert_id", "value": alert_id[:8]}, {"name": "cycle_id", "value": cycle_id}])
                if result:
                    stats["emails_sent"] += 1
                    await finalize_alert_send(alert_id, [o["id"] for o in opps if o.get("id")], db)
                else:
                    stats["emails_failed"] += 1
            except Exception as e:
                stats["emails_failed"] += 1
                logger.error(f"[Alerts {cycle_id}] Error sending alert {alert_id[:8]}: {e}")

    except Exception as e:
        logger.error(f"[Alerts {cycle_id}] Unexpected error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), **stats}

    stats["duration_ms"] = int((time.monotonic() - start) * 1000)
    logger.info(json.dumps({"event": "alerts_sent", **stats}))
    return {"status": "completed", **stats}


async def reclassify_pending_bids_job(ctx: dict, search_id: str, sector_name: str = "", sector_id: str = "", attempt: int = 1, **kwargs) -> dict:
    from config import PENDING_REVIEW_MAX_RETRIES, PENDING_REVIEW_RETRY_DELAY
    from redis_pool import get_redis_pool
    from jobs.queue.result_store import _PENDING_REVIEW_KEY_PREFIX
    from job_queue import get_arq_pool

    logger.info(f"STORY-354: reclassify_pending_bids_job start (search_id={search_id}, attempt={attempt})")
    redis = await get_redis_pool()
    if redis is None:
        return {"status": "error", "reason": "redis_unavailable"}

    key = f"{_PENDING_REVIEW_KEY_PREFIX}{search_id}"
    try:
        raw = await redis.get(key)
        if not raw:
            return {"status": "skipped", "reason": "no_pending_bids"}
        data = json.loads(raw)
        bids = data["bids"]
    except Exception as e:
        logger.error(f"STORY-354: Failed to load pending bids: {e}")
        return {"status": "error", "reason": str(e)}

    if not bids:
        return {"status": "skipped", "reason": "empty_bids"}

    from llm_arbiter import classify_contract_primary_match
    from concurrent.futures import ThreadPoolExecutor, as_completed

    accepted = rejected = still_pending = 0

    def _classify_one(bid: dict) -> tuple:
        objeto = bid.get("objetoCompra", "")
        valor = float(bid.get("valorTotalEstimado") or bid.get("valorTotalHomologado") or 0)
        result = classify_contract_primary_match(objeto=objeto, valor=valor, setor_name=sector_name or None, prompt_level="zero_match", setor_id=sector_id or None, search_id=search_id)
        return bid, result

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            for future in as_completed({executor.submit(_classify_one, bid): bid for bid in bids}):
                try:
                    bid, result = future.result()
                    if isinstance(result, dict) and result.get("pending_review"):
                        still_pending += 1
                    elif isinstance(result, dict) and result.get("is_primary"):
                        accepted += 1
                    else:
                        rejected += 1
                except Exception:
                    still_pending += 1
    except Exception as e:
        logger.error(f"STORY-354: Reclassification failed entirely: {e}")
        if attempt < PENDING_REVIEW_MAX_RETRIES:
            try:
                pool = await get_arq_pool()
                if pool:
                    await pool.enqueue_job("reclassify_pending_bids_job", search_id=search_id, sector_name=sector_name, sector_id=sector_id, attempt=attempt + 1, _defer_by=PENDING_REVIEW_RETRY_DELAY)
            except Exception as enq_err:
                logger.error(f"STORY-354: Failed to enqueue retry: {enq_err}")
        return {"status": "error", "reason": str(e)}

    logger.info(f"STORY-354: Reclassification complete: {accepted} accepted, {rejected} rejected, {still_pending} still pending (search_id={search_id})")

    if accepted + rejected > 0:
        from progress import get_tracker
        tracker = await get_tracker(search_id)
        if tracker:
            await tracker.emit_pending_review_complete(reclassified_count=accepted + rejected, accepted_count=accepted, rejected_count=rejected)

    if still_pending == 0:
        try:
            await redis.delete(key)
        except Exception:
            pass
    elif attempt < PENDING_REVIEW_MAX_RETRIES:
        try:
            pool = await get_arq_pool()
            if pool:
                await pool.enqueue_job("reclassify_pending_bids_job", search_id=search_id, sector_name=sector_name, sector_id=sector_id, attempt=attempt + 1, _defer_by=PENDING_REVIEW_RETRY_DELAY)
        except Exception as enq_err:
            logger.error(f"STORY-354: Failed to enqueue retry: {enq_err}")

    return {"status": "completed", "total": accepted + rejected + still_pending, "accepted": accepted, "rejected": rejected, "still_pending": still_pending}


async def classify_zero_match_job(ctx: dict, search_id: str, candidates: list[dict], setor: str, sector_name: str, custom_terms: list[str] | None = None, enqueued_at: float = 0, **kwargs) -> dict:
    from config import MAX_ZERO_MATCH_ITEMS, ZERO_MATCH_JOB_TIMEOUT_S, LLM_ZERO_MATCH_BATCH_SIZE, FILTER_ZERO_MATCH_BUDGET_S, LLM_FALLBACK_PENDING_ENABLED
    from metrics import ZERO_MATCH_JOB_DURATION, ZERO_MATCH_JOB_STATUS, ZERO_MATCH_JOB_QUEUE_TIME
    from progress import get_tracker
    from jobs.queue.result_store import store_zero_match_results

    job_start = time.time()
    if enqueued_at > 0:
        ZERO_MATCH_JOB_QUEUE_TIME.observe(job_start - enqueued_at)

    total_candidates = len(candidates)
    will_classify = min(total_candidates, MAX_ZERO_MATCH_ITEMS)
    logger.info(f"CRIT-059: classify_zero_match_job start (search_id={search_id}, candidates={total_candidates}, will_classify={will_classify})")

    tracker = await get_tracker(search_id)
    if tracker:
        await tracker.emit("zero_match_started", -1, f"Analisando {will_classify} oportunidades adicionais com IA...", candidates=total_candidates, will_classify=will_classify)

    from llm_arbiter import _classify_zero_match_batch as _classify_batch
    approved: list[dict] = []
    rejected_count = pending_count = classified = 0
    budget_start = time.time()
    pool_to_classify = candidates[:will_classify]

    try:
        batch_items = []
        for lic in pool_to_classify:
            obj = lic.get("objetoCompra", "")
            val = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
            if isinstance(val, str):
                try:
                    val = float(val.replace(".", "").replace(",", "."))
                except ValueError:
                    val = 0.0
            else:
                val = float(val) if val else 0.0
            batch_items.append({"objeto": obj, "valor": val})

        batches = [batch_items[i:i + LLM_ZERO_MATCH_BATCH_SIZE] for i in range(0, len(batch_items), LLM_ZERO_MATCH_BATCH_SIZE)]
        lic_batches = [pool_to_classify[i:i + LLM_ZERO_MATCH_BATCH_SIZE] for i in range(0, len(pool_to_classify), LLM_ZERO_MATCH_BATCH_SIZE)]

        for batch_idx, (batch, lic_batch) in enumerate(zip(batches, lic_batches)):
            elapsed = time.time() - budget_start
            if elapsed > FILTER_ZERO_MATCH_BUDGET_S:
                for remaining_lic in pool_to_classify[classified:]:
                    remaining_lic.update({"_relevance_source": "pending_review", "_pending_review": True, "_pending_review_reason": "zero_match_budget_exceeded"})
                    pending_count += 1
                break

            job_elapsed = time.time() - job_start
            if job_elapsed > ZERO_MATCH_JOB_TIMEOUT_S:
                for remaining_lic in pool_to_classify[classified:]:
                    remaining_lic.update({"_relevance_source": "pending_review", "_pending_review": True, "_pending_review_reason": "zero_match_job_timeout"})
                    pending_count += 1
                logger.warning(f"CRIT-059: Job timeout at batch {batch_idx}")
                break

            try:
                batch_results = _classify_batch(items=batch, setor_name=sector_name, setor_id=setor, search_id=search_id)
                for lic_item, result in zip(lic_batch, batch_results):
                    is_relevant = result.get("is_primary", False) if isinstance(result, dict) else result
                    if is_relevant:
                        lic_item.update({"_relevance_source": "llm_zero_match", "_term_density": 0.0, "_matched_terms": []})
                        if isinstance(result, dict):
                            lic_item["_confidence_score"] = min(result.get("confidence", 60), 70)
                            lic_item["_llm_evidence"] = result.get("evidence", [])
                        else:
                            lic_item["_confidence_score"] = 60
                            lic_item["_llm_evidence"] = []
                        approved.append(lic_item)
                    else:
                        _is_pending = isinstance(result, dict) and result.get("pending_review", False)
                        if _is_pending and LLM_FALLBACK_PENDING_ENABLED:
                            lic_item.update({"_relevance_source": "pending_review", "_pending_review": True})
                            pending_count += 1
                        else:
                            rejected_count += 1
                    classified += 1
            except Exception as batch_err:
                logger.warning(f"CRIT-059: Batch {batch_idx} failed: {batch_err}")
                for lic_item in lic_batch:
                    if LLM_FALLBACK_PENDING_ENABLED:
                        lic_item.update({"_relevance_source": "pending_review", "_pending_review": True})
                        pending_count += 1
                    else:
                        rejected_count += 1
                    classified += 1

            if tracker:
                await tracker.emit("zero_match_progress", -1, f"Classificação IA: {classified}/{will_classify}", classified=classified, total=will_classify, approved=len(approved))

    except Exception as e:
        logger.error(f"CRIT-059: classify_zero_match_job failed: {e}", exc_info=True)
        ZERO_MATCH_JOB_STATUS.labels(status="failed").inc()
        if approved:
            await store_zero_match_results(search_id, approved)
        if tracker:
            await tracker.emit("zero_match_error", -1, "Classificação IA falhou parcialmente", approved=len(approved), error=str(e)[:200])
        duration = time.time() - job_start
        ZERO_MATCH_JOB_DURATION.observe(duration)
        return {"status": "failed", "approved": len(approved), "rejected": rejected_count, "pending": pending_count, "error": str(e)}

    await store_zero_match_results(search_id, approved)
    duration = time.time() - job_start
    ZERO_MATCH_JOB_DURATION.observe(duration)
    ZERO_MATCH_JOB_STATUS.labels(status="completed").inc()
    logger.info(f"CRIT-059: classify_zero_match_job complete (search_id={search_id}, classified={classified}, approved={len(approved)}, rejected={rejected_count}, pending={pending_count}, duration={duration:.1f}s)")
    if tracker:
        await tracker.emit("zero_match_ready", -1, f"Classificação concluída: {len(approved)} oportunidades encontradas", total_classified=classified, approved=len(approved), rejected=rejected_count)
    return {"status": "completed", "total_classified": classified, "approved": len(approved), "rejected": rejected_count, "pending": pending_count, "duration_s": round(duration, 1)}
