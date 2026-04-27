# MON-FN-010: LGPD Data Export Endpoint (`POST /api/me/data-export`)

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 3-4 (13–26/mai)
**Sprint Window:** Sprint 3-4 (paralelo, sem bloqueio)
**Dependências bloqueadoras:** Nenhuma

---

## Contexto

LGPD Art. 18 (Brasil) garante ao titular dos dados o **direito de acesso** (data portability). SmartLic atualmente **não tem endpoint** para usuário exportar todos seus dados em formato estruturado. Risco compliance: ANPD pode multar pre-revenue (multas escalam com receita, mas advertência pública é dano reputacional).

Dados a exportar (schema `profiles` + relacionados):
- `profiles` (perfil completo)
- `auth.users` (email, created_at) — via Supabase RPC
- `searches` / `search_sessions` (histórico de busca)
- `pipeline_items` (oportunidades salvas)
- `feedback` (classificação feedback)
- `messages` / `conversations`
- `analytics_events` (de MON-FN-006)
- `dunning_state` (de MON-FN-007)
- `abandoned_carts` (de MON-FN-009)
- `resend_webhook_events` (delivery log do user)
- `trial_email_log`

Padrão Fortune-500 (GDPR-compliant by design): endpoint async (ARQ job) que gera ZIP em ≤72h, email com signed URL Supabase Storage (TTL 7d), audit log em tabela `lgpd_requests`.

**Por que P1:** compliance obrigatório no Brasil; sem endpoint, não há resposta legalmente válida a "Quero meus dados". Risk multa + perda de confiança quando primeiro lawyer-savvy user solicitar.

**Paths críticos:**
- `backend/routes/conta.py` (endpoint POST)
- `backend/services/data_export.py` (NOVO — ARQ job)
- `backend/job_queue.py` (registrar)
- `supabase/migrations/` (tabela `lgpd_requests` + Supabase Storage bucket)
- `backend/templates/emails/lgpd_data_export.html`

---

## Acceptance Criteria

### AC1: Tabela `lgpd_requests` (audit log obrigatório)

Given que LGPD exige audit trail de cada request,
When user solicita export,
Then INSERT em `lgpd_requests`.

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_lgpd_requests.sql`:
```sql
CREATE TABLE public.lgpd_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE SET NULL,
  email_at_request text NOT NULL,                    -- preserved if user deletes account
  action text NOT NULL CHECK (action IN ('export', 'delete')),
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  failed_at timestamptz,
  ip_address inet,                                   -- audit per LGPD requirements
  user_agent text,
  file_path text,                                    -- Supabase Storage path (export only)
  file_size_bytes bigint,                            -- export only
  expires_at timestamptz,                            -- signed URL expiration (export 7d)
  notes text,                                        -- optional admin notes / cancellation reason
  metadata jsonb DEFAULT '{}'::jsonb
);
CREATE INDEX idx_lgpd_requests_user ON public.lgpd_requests (user_id, requested_at DESC);
CREATE INDEX idx_lgpd_requests_status ON public.lgpd_requests (status, requested_at);

ALTER TABLE public.lgpd_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own lgpd_requests" ON public.lgpd_requests
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service full" ON public.lgpd_requests FOR ALL USING (auth.role() = 'service_role');
```
- [ ] Migration paired down `.down.sql`
- [ ] **NÃO usar `ON DELETE CASCADE`** para `user_id` — usar `ON DELETE SET NULL` para preservar audit trail mesmo após hard delete (MON-FN-011)
- [ ] Retention: nunca purgar (legal audit; pode tornar-se evidência em disputa)

### AC2: Supabase Storage bucket `lgpd-exports`

Given que ZIP files podem ser >100MB,
When export gerado,
Then upload para Supabase Storage com signed URL.

- [ ] Migration cria bucket privado `lgpd-exports`:
```sql
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('lgpd-exports', 'lgpd-exports', false, 524288000, ARRAY['application/zip'])
ON CONFLICT (id) DO NOTHING;

-- RLS: only service-role uploads/reads (signed URLs bypass RLS)
CREATE POLICY "Service role full lgpd-exports" ON storage.objects
  FOR ALL USING (bucket_id = 'lgpd-exports' AND auth.role() = 'service_role');
```
- [ ] Path convention: `lgpd-exports/{user_id}/{request_id}/data.zip`
- [ ] Signed URL TTL 7 dias

### AC3: Endpoint `POST /api/me/data-export`

Given user autenticado,
When POST request,
Then INSERT lgpd_requests + dispatch ARQ job + retorna 202.

- [ ] Em `backend/routes/conta.py` adicionar:
```python
@router.post("/v1/me/data-export", status_code=202)
async def request_data_export(
    request: Request,
    user: User = Depends(require_auth),
):
    """Submit LGPD data export request (Art. 18 II).

    Async processing: ARQ job generates ZIP in ≤72h; email with signed URL sent to user.
    Idempotent: only 1 pending export per user (returns existing).
    """
    sb = get_supabase()

    # Check for pending request
    existing = sb.table("lgpd_requests").select("*") \
        .eq("user_id", user["id"]) \
        .eq("action", "export") \
        .in_("status", ["pending", "processing"]) \
        .single().execute()

    if existing.data:
        return {
            "request_id": existing.data["id"],
            "status": existing.data["status"],
            "message": "Solicitação anterior ainda em processamento. Você receberá email quando concluída.",
            "requested_at": existing.data["requested_at"],
        }

    # Create new request
    new_request = sb.table("lgpd_requests").insert({
        "user_id": user["id"],
        "email_at_request": user["email"],
        "action": "export",
        "status": "pending",
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }).execute()

    request_id = new_request.data[0]["id"]

    # Dispatch ARQ job
    arq_pool = await get_arq_pool()
    await arq_pool.enqueue_job("lgpd_export_job", request_id=request_id)

    track_funnel_event("lgpd_export_requested", user["id"], properties={"request_id": request_id})

    return {
        "request_id": request_id,
        "status": "pending",
        "message": "Solicitação recebida. Você receberá um email com o link de download em até 72 horas.",
        "estimated_completion": (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat(),
    }
```
- [ ] Rate limit: 1 export per 24h per user (não-abuse)
- [ ] Frontend `/conta` page recebe novo botão "Exportar meus dados" (LGPD section)

### AC4: ARQ job `lgpd_export_job`

Given request pendente,
When ARQ worker pega job,
Then coleta dados, gera ZIP, faz upload, envia email.

- [ ] Novo `backend/services/data_export.py`:
```python
import json
import csv
import io
import zipfile
from datetime import datetime, timezone, timedelta

async def lgpd_export_job(ctx: dict, request_id: str) -> dict:
    """LGPD Art. 18 II: data portability export.

    Steps:
    1. Mark request as 'processing'
    2. Collect data from all user-related tables
    3. Generate ZIP with JSON + CSV
    4. Upload to Supabase Storage
    5. Generate signed URL (7d TTL)
    6. Send email with link
    7. Mark request as 'completed'

    On failure: status='failed' + Sentry capture + admin alert.
    """
    sb = get_supabase()
    request = sb.table("lgpd_requests").select("*").eq("id", request_id).single().execute()
    if not request.data or request.data["status"] != "pending":
        return {"status": "skip", "reason": "not_pending"}

    user_id = request.data["user_id"]
    email = request.data["email_at_request"]

    sb.table("lgpd_requests").update({"status": "processing"}).eq("id", request_id).execute()

    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. profiles
            profile = sb.table("profiles").select("*").eq("id", user_id).execute().data
            zf.writestr("profiles.json", json.dumps(profile, indent=2, default=str))

            # 2. searches / sessions
            sessions = sb.table("search_sessions").select("*").eq("user_id", user_id).execute().data
            zf.writestr("search_sessions.json", json.dumps(sessions, indent=2, default=str))

            # 3. pipeline
            pipeline = sb.table("pipeline_items").select("*").eq("user_id", user_id).execute().data
            zf.writestr("pipeline_items.json", json.dumps(pipeline, indent=2, default=str))

            # 4. messages / conversations
            convos = sb.table("conversations").select("*").eq("user_id", user_id).execute().data
            zf.writestr("conversations.json", json.dumps(convos, indent=2, default=str))

            # 5. analytics_events (MON-FN-006)
            events = sb.table("analytics_events").select("*").eq("user_id", user_id).execute().data
            zf.writestr("analytics_events.json", json.dumps(events, indent=2, default=str))

            # 6. dunning_state (MON-FN-007)
            dunning = sb.table("dunning_state").select("*").eq("user_id", user_id).execute().data
            zf.writestr("dunning_state.json", json.dumps(dunning, indent=2, default=str))

            # 7. abandoned_carts (MON-FN-009)
            carts = sb.table("abandoned_carts").select("*").eq("user_id", user_id).execute().data
            zf.writestr("abandoned_carts.json", json.dumps(carts, indent=2, default=str))

            # 8. trial_email_log
            emails = sb.table("trial_email_log").select("*").eq("user_id", user_id).execute().data
            zf.writestr("trial_email_log.json", json.dumps(emails, indent=2, default=str))

            # CSV duplicates for spreadsheet users
            zf.writestr("search_sessions.csv", _to_csv(sessions))
            zf.writestr("pipeline_items.csv", _to_csv(pipeline))

            # README.txt with metadata
            zf.writestr("README.txt", f"""SmartLic Data Export
Request ID: {request_id}
Generated: {datetime.now(timezone.utc).isoformat()}
User: {email}

Files included:
- profiles.json — user profile
- search_sessions.json/csv — search history
- pipeline_items.json/csv — saved opportunities
- conversations.json — message threads
- analytics_events.json — funnel events
- dunning_state.json — billing state (if applicable)
- abandoned_carts.json — abandoned checkouts (if any)
- trial_email_log.json — email delivery log

LGPD Art. 18 II — Right to data portability.
This file is auto-generated and may be re-requested at /conta.
""")

        # Upload to Supabase Storage
        zip_bytes = zip_buffer.getvalue()
        file_size = len(zip_bytes)
        file_path = f"{user_id}/{request_id}/data.zip"
        sb.storage.from_("lgpd-exports").upload(file_path, zip_bytes, {"content-type": "application/zip"})

        # Generate signed URL (7d)
        signed_url = sb.storage.from_("lgpd-exports").create_signed_url(file_path, 60 * 60 * 24 * 7)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Update request
        sb.table("lgpd_requests").update({
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "file_path": file_path,
            "file_size_bytes": file_size,
            "expires_at": expires_at.isoformat(),
        }).eq("id", request_id).execute()

        # Send email
        await _send_export_email(email, signed_url["signedURL"], expires_at)

        track_funnel_event("lgpd_export_completed", user_id, properties={
            "request_id": request_id,
            "file_size_bytes": file_size,
            "duration_seconds": (datetime.now(timezone.utc) - datetime.fromisoformat(request.data["requested_at"].replace("Z", "+00:00"))).total_seconds(),
        })

        return {"status": "completed", "request_id": request_id, "file_size": file_size}

    except Exception as e:
        sb.table("lgpd_requests").update({
            "status": "failed",
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Export failed: {str(e)[:500]}",
        }).eq("id", request_id).execute()
        sentry_sdk.capture_exception(e, tags={"lgpd_action": "export", "request_id": request_id})
        smartlic_lgpd_export_failed_total.inc()
        raise  # let ARQ retry per its config
```
- [ ] Registrar em `backend/job_queue.py::WorkerSettings.functions`
- [ ] Job timeout: 30 min (large dataset edge cases)
- [ ] Retry: 3 attempts (ARQ default)

### AC5: Email com signed URL

Given export completed,
When email enviado,
Then user recebe link expirable.

- [ ] Novo `backend/templates/emails/lgpd_data_export.html`:
  - Subject: `Seus dados SmartLic estão prontos para download`
  - Conteúdo: link signed URL + nota "Link expira em 7 dias"
  - Footer: "Se não solicitou esta exportação, ignore este email" + link para suporte
- [ ] Tag Resend `category=lgpd, action=export`

### AC6: Endpoint GET status

Given user verifica status,
When `GET /api/me/data-export/{request_id}`,
Then retorna status atual.

- [ ] Em `backend/routes/conta.py`:
```python
@router.get("/v1/me/data-export/{request_id}")
async def get_data_export_status(
    request_id: str,
    user: User = Depends(require_auth),
):
    sb = get_supabase()
    req = sb.table("lgpd_requests").select("*") \
        .eq("id", request_id).eq("user_id", user["id"]).single().execute()
    if not req.data:
        raise HTTPException(404, "Request not found")
    return {
        "request_id": req.data["id"],
        "status": req.data["status"],
        "requested_at": req.data["requested_at"],
        "completed_at": req.data.get("completed_at"),
        "expires_at": req.data.get("expires_at"),
    }
```

### AC7: Frontend UI em `/conta`

Given user vai em conta,
When vê seção LGPD,
Then pode solicitar export + ver requests anteriores.

- [ ] Em `frontend/app/conta/` adicionar componente `<LgpdSection />`:
  - Botão "Solicitar exportação dos meus dados (LGPD)"
  - Modal confirmação
  - Lista de requests anteriores (status + link download se completed)
  - Helper text explicando direito LGPD Art. 18

### AC8: Métricas + SLA tracking

- [ ] Counter `smartlic_lgpd_export_requested_total`
- [ ] Counter `smartlic_lgpd_export_completed_total`
- [ ] Counter `smartlic_lgpd_export_failed_total`
- [ ] Histograma `smartlic_lgpd_export_duration_seconds` — alvo p99 < 72h × 3600
- [ ] SLA dashboard: `(completed within 72h) / total` (alvo: >99%)
- [ ] Sentry alert se duration >72h ou status='failed' (fingerprint `["lgpd_export_failed", request_id]`)

### AC9: Testes

- [ ] Unit `backend/tests/services/test_data_export.py`:
  - [ ] Job coleta dados de todas tabelas
  - [ ] ZIP estruturado corretamente
  - [ ] Upload Storage + signed URL gerado
  - [ ] Status transitions: pending → processing → completed
  - [ ] Failure path: pending → failed + Sentry
- [ ] Integration `backend/tests/routes/test_lgpd_export.py`:
  - [ ] POST endpoint cria request + ARQ enqueued
  - [ ] Existing pending request → returns existing (idempotência)
  - [ ] Rate limit 1/24h enforced
  - [ ] GET status returns correct data
  - [ ] Audit log includes ip_address, user_agent
- [ ] E2E Playwright:
  - [ ] User goes to /conta → click "Export data"
  - [ ] Mock ARQ job sync → assert email received with link
  - [ ] Click link → download ZIP
  - [ ] Validate ZIP contents (json files present)
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Tabela `lgpd_requests` (audit) + RLS
- Bucket Supabase Storage `lgpd-exports`
- Endpoint POST + GET status
- ARQ job para gerar ZIP
- Email com signed URL
- Frontend UI em `/conta`
- Métricas + SLA tracking
- Idempotência + rate limit

**OUT:**
- Self-serve unsubscribe via export link (separate flow)
- Mass export para admin (admin endpoint separado se necessário)
- Encryption at rest (Supabase Storage já encrypta)
- PDF export além de JSON/CSV
- Programmatic API (apenas user-facing)
- Multi-language ZIP (pt-BR único)
- Real-time progress UI (status polling apenas)

---

## Definition of Done

- [ ] Migration aplicada
- [ ] Bucket `lgpd-exports` criado e RLS validada
- [ ] Endpoint POST funcional + 202 retorna pending
- [ ] ARQ job processa em ≤30 min para test user com dados típicos
- [ ] Email recebido com signed URL válido
- [ ] Download ZIP + extract → arquivos JSON/CSV legíveis
- [ ] Frontend `/conta` mostra LGPD section + history
- [ ] SLA <72h validado em load test (50 requests simultâneas)
- [ ] Cobertura ≥85%
- [ ] CodeRabbit clean
- [ ] Operational runbook em `docs/operations/lgpd-runbook.md`
- [ ] Memory `feedback_audit_env_vars_after_incident` complementada com LGPD pattern
- [ ] Audit log testado: IP + user_agent gravados

---

## Dev Notes

### Padrões existentes a reutilizar

- **`require_auth`:** `backend/auth.py` (existente)
- **ARQ enqueue:** `backend/job_queue.py::get_arq_pool`
- **Supabase Storage:** Supabase JS SDK; verificar Python SDK `sb.storage.from_(bucket).upload`
- **Email service:** `email_service.py:send_email`
- **`track_funnel_event`:** MON-FN-006

### Funções afetadas

- `backend/routes/conta.py` (NOVOS endpoints)
- `backend/services/data_export.py` (NOVO)
- `backend/job_queue.py::WorkerSettings` (registrar)
- `backend/templates/emails/lgpd_data_export.html` (NOVO)
- `frontend/app/conta/LgpdSection.tsx` (NOVO)
- `backend/metrics.py`
- `supabase/migrations/YYYYMMDDHHMMSS_create_lgpd_requests.sql` + `.down.sql`
- `supabase/migrations/YYYYMMDDHHMMSS_create_lgpd_exports_bucket.sql` + `.down.sql`

### Trade-off: Sync vs Async

Sync (synchronous endpoint generates ZIP in-request):
- Bloqueia event loop por minutos para users com muitos dados
- Risk timeout Railway 120s

Async (ARQ job, email):
- ✅ Escolhido: SLA 72h é conservador; user expectation é "vai chegar"
- Permite ZIP de qualquer tamanho
- Pattern Fortune-500 standard (Google Takeout, Notion, Stripe export)

### Testing Standards

- Mock Supabase Storage via `@patch("supabase.Client.storage")`
- `tempfile.NamedTemporaryFile` para testar ZIP generation
- `freezegun` para validar `expires_at`
- Cobertura: `pytest --cov=backend/services/data_export.py`
- Anti-hang: ARQ tests usam `asyncio.wait_for(timeout=30)`

---

## Risk & Rollback

### Triggers de rollback
- Job timeout em users com dados volumosos (raro, mas possível)
- Storage quota exceeded (monitor `lgpd-exports` size)
- Signed URL leak via email log (mitigado: TLS only)
- Massive abuse: 1000 users requesting daily

### Ações de rollback
1. **Imediato:** `LGPD_EXPORT_ENABLED=false` env flag — endpoint retorna 503 + manual fallback
2. **Manual fallback:** equipe processa requests via SQL admin queries + envio manual ZIP
3. **Schema:** down.sql; mas lgpd_requests é audit-mandatory — preservar
4. **Storage cleanup:** auto-purge `lgpd-exports/*` após `expires_at` via cron (separate from request retention)

### Compliance
- Audit trail é evidência legal — não tocar
- Rate limit 1/24h previne abuse + DoS
- Signed URL expira: previne shared link permanente
- IP/user_agent gravado: auditoria conformidade

---

## Dependencies

### Entrada
- Supabase Storage habilitado no projeto (verificar)
- ARQ worker rodando
- Email service operacional

### Saída
- **MON-FN-011** (LGPD deletion): mesma tabela `lgpd_requests` com action='delete'
- Compliance baseline desbloqueia outros features que tocam PII

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "LGPD Data Export Endpoint (`POST /api/me/data-export`)" — endpoint explícito |
| 2 | Complete description | Y | Cita LGPD Art. 18 II + 11 tabelas a exportar + benchmark Google Takeout |
| 3 | Testable acceptance criteria | Y | 9 ACs incluindo SLA load test 50 requests + E2E Playwright validate ZIP |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui PDF/multi-language/realtime progress |
| 5 | Dependencies mapped | Y | Entrada Storage habilitado + ARQ; Saída MON-FN-011 (mesma tabela) |
| 6 | Complexity estimate | Y | M (3-4 dias) coerente — endpoint + ARQ job + Storage + email + UI |
| 7 | Business value | Y | "Compliance LGPD obrigatório no Brasil; risco multa ANPD" |
| 8 | Risks documented | Y | Job timeout + Storage quota + signed URL leak + abuse 1000/dia |
| 9 | Criteria of Done | Y | **SLA <72h validado em load test; audit log testado (IP + user_agent)** |
| 10 | Alignment with PRD/Epic | Y | EPIC Constraint LGPD obrigatório + Success Metric 5 (SLA <72h) |

### Observations
- **Audit log obrigatório verificado:** AC1 inclui `ip_address`, `user_agent`, status state machine (pending/processing/completed/failed/cancelled), retention "nunca purgar (legal audit; pode tornar-se evidência em disputa)"
- **SLA <72h endereçada concretamente:** AC8 histograma `smartlic_lgpd_export_duration_seconds` + Sentry alert + load test 50 simultâneas em DoD
- ON DELETE SET NULL (não CASCADE) preserva audit pós hard-delete (MON-FN-011 compatibility)
- Idempotência: 1 pending export per user (returns existing); rate limit 1/24h
- Frontend UI em `/conta` LGPD section explicitada
- Manual fallback documentado (equipe SQL admin) em rollback

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — LGPD data export endpoint async | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P1 compliance LGPD sólido; audit + SLA <72h endereçados; Status Draft → Ready. | @po (Pax) |
