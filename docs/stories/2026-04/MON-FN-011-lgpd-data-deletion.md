# MON-FN-011: LGPD Data Deletion (Right to Erasure, Soft + Hard D+30)

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 4 (20–26/mai)
**Sprint Window:** Sprint 4 (depende de MON-FN-010)
**Dependências bloqueadoras:** MON-FN-010 (tabela `lgpd_requests` criada e padrão estabelecido)

---

## Contexto

LGPD Art. 18 IV (Brasil) garante ao titular **direito ao apagamento** dos dados pessoais (right to erasure, GDPR equivalente Art. 17). Hoje SmartLic não tem endpoint para usuário deletar conta + dados — risco compliance idêntico ao MON-FN-010.

Pattern Fortune-500: **two-phase deletion**:
1. **Soft delete (D+0):** marca conta como deleted (`profiles.deleted_at = now()`), anonimiza email/nome em `auth.users`, revoga sessões. User não pode mais logar. Dados ainda existem em DB para period de "regret window" 30 dias + recuperar conta possível neste período.
2. **Hard delete (D+30):** ARQ job purga linhas de TODAS tabelas relacionadas. Cascade FKs cuidam da maioria; tabelas com `ON DELETE SET NULL` (ex: `lgpd_requests` para audit) preservam metadata mas perdem `user_id`.

`backend/routes/conta.py` já tem trial cancel flow — reutilizar pattern de token/JWT signed para confirm critical actions. Account deletion exige DOUBLE-confirm: email link + senha re-confirmation no frontend.

**Por que P1:** mesmo motivo que MON-FN-010 — compliance Brasil obrigatório. Sem este, advogado-savvy user ou ANPD audit causa exposição. A combinação export + delete é o "pacote LGPD" comum.

**Paths críticos:**
- `backend/routes/conta.py` (endpoints DELETE + confirm)
- `backend/services/data_deletion.py` (NOVO — soft + hard delete)
- `backend/cron/lgpd_hard_delete.py` (NOVO — D+30 purge)
- `supabase/migrations/` (`profiles.deleted_at` column + cascade audit)
- `backend/templates/emails/lgpd_deletion_*.html`

---

## Acceptance Criteria

### AC1: Coluna `profiles.deleted_at` + status

Given que precisamos soft-delete primeiro,
When migration roda,
Then coluna `deleted_at` adicionada.

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_add_profiles_deleted_at.sql`:
```sql
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS deleted_at timestamptz,
  ADD COLUMN IF NOT EXISTS deletion_scheduled_for timestamptz,  -- D+30 hard delete time
  ADD COLUMN IF NOT EXISTS deletion_reason text;

CREATE INDEX idx_profiles_deleted_at ON public.profiles (deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_profiles_pending_hard_delete ON public.profiles (deletion_scheduled_for)
  WHERE deletion_scheduled_for IS NOT NULL AND deleted_at IS NOT NULL;

-- Update existing RLS to filter out deleted users
DROP POLICY IF EXISTS "Users read own profile" ON public.profiles;
CREATE POLICY "Users read own active profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id AND deleted_at IS NULL);
```
- [ ] Migration paired down `.down.sql` (DROP COLUMNs)
- [ ] **Importante:** atualizar TODAS queries a `profiles` em código backend para filtrar `deleted_at IS NULL` (ou via RLS automático)

### AC2: Endpoint `DELETE /api/me` (soft delete)

Given user autenticado,
When DELETE request,
Then soft-delete + cria lgpd_request action='delete' + email confirmação.

- [ ] Em `backend/routes/conta.py`:
```python
@router.delete("/v1/me", status_code=202)
async def request_account_deletion(
    request: Request,
    body: DeletionRequest,  # {confirmation_password: str, reason?: str}
    user: User = Depends(require_auth),
):
    """LGPD Art. 18 IV: right to erasure.

    Soft-deletes immediately:
    - profiles.deleted_at = now()
    - profiles.deletion_scheduled_for = now() + 30 days
    - auth.users email anonymized to 'deleted-{user_id}@smartlic.deleted'
    - Active sessions revoked

    Hard-delete: ARQ cron job at deletion_scheduled_for purges related rows.
    Within 30 days, user can email support to cancel deletion (manual restore).
    """
    sb = get_supabase()

    # Verify password (additional confirmation beyond JWT)
    if not _verify_user_password(user["id"], body.confirmation_password):
        raise HTTPException(403, "Senha incorreta")

    if user.get("deleted_at"):
        raise HTTPException(409, "Conta já está marcada para deleção")

    # Cancel active subscriptions (Stripe)
    await _cancel_active_subscriptions(user["id"])

    # Soft-delete
    deletion_scheduled_for = datetime.now(timezone.utc) + timedelta(days=30)
    sb.table("profiles").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deletion_scheduled_for": deletion_scheduled_for.isoformat(),
        "deletion_reason": body.reason,
    }).eq("id", user["id"]).execute()

    # Anonymize auth.users (Supabase Admin API)
    await _anonymize_auth_user(user["id"], user["email"])

    # Revoke sessions
    await _revoke_all_sessions(user["id"])

    # Audit log
    new_request = sb.table("lgpd_requests").insert({
        "user_id": user["id"],  # FK still valid until hard delete (ON DELETE SET NULL handles later)
        "email_at_request": user["email"],
        "action": "delete",
        "status": "processing",  # processing until D+30 hard delete completes
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "metadata": {
            "deletion_scheduled_for": deletion_scheduled_for.isoformat(),
            "deletion_reason": body.reason,
        },
    }).execute()

    # Send confirmation email
    await _send_deletion_confirmation_email(user["email"], deletion_scheduled_for)

    track_funnel_event("lgpd_deletion_requested", user["id"], properties={
        "reason": body.reason,
        "scheduled_for": deletion_scheduled_for.isoformat(),
    })

    smartlic_lgpd_deletion_requested_total.inc()

    return {
        "request_id": new_request.data[0]["id"],
        "status": "scheduled",
        "deletion_scheduled_for": deletion_scheduled_for.isoformat(),
        "message": "Conta desativada. Dados serão permanentemente deletados em 30 dias.",
        "cancel_until": deletion_scheduled_for.isoformat(),
        "support_email": "tiago@smartlic.tech",
    }
```
- [ ] Pydantic model `DeletionRequest`: `confirmation_password: str = Field(..., min_length=8)`, `reason: Optional[str]`
- [ ] Helper `_verify_user_password` via Supabase Auth `signInWithPassword` (ou similar)
- [ ] Helper `_cancel_active_subscriptions`: cancela Stripe subscription + atualiza dunning_state se aplicável

### AC3: Anonymization de `auth.users`

Given soft-delete,
When happens,
Then email/nome em auth.users são anonimizados (preserva UUID para FKs).

- [ ] Helper `_anonymize_auth_user(user_id, original_email)`:
```python
async def _anonymize_auth_user(user_id: str, original_email: str) -> None:
    """Anonymize auth.users row. Preserves UUID for FK integrity until hard delete."""
    from supabase_client import get_supabase_admin
    admin = get_supabase_admin()  # service role
    anonymized_email = f"deleted-{user_id}@smartlic.deleted"
    admin.auth.admin.update_user_by_id(user_id, {
        "email": anonymized_email,
        "user_metadata": {"deleted": True, "original_email_hash": _hash_email(original_email)},
        "ban_duration": "876000h",  # 100 years (effective permanent ban)
    })
```
- [ ] Hash original email (SHA-256) para audit (provar identidade em recovery legal sem armazenar PII)
- [ ] Teste: tentativa de login com email original retorna 401 (banido)

### AC4: Cron `lgpd_hard_delete_job` (D+30)

Given profiles com `deletion_scheduled_for < now() AND deleted_at IS NOT NULL`,
When cron diário roda (10 UTC),
Then hard delete: cascade FK + DELETE auth.users.

- [ ] Novo `backend/cron/lgpd_hard_delete.py`:
```python
async def lgpd_hard_delete_job() -> dict:
    """Daily: hard-delete soft-deleted users past deletion_scheduled_for."""
    lock = await acquire_redis_lock("smartlic:lgpd_hard_delete:lock", 30 * 60)
    if not lock:
        return {"status": "skipped"}
    try:
        sb = get_supabase()
        admin = get_supabase_admin()
        now = datetime.now(timezone.utc)
        results = {"deleted": 0, "errors": 0}

        pending = sb.table("profiles").select("id, deletion_scheduled_for") \
            .lte("deletion_scheduled_for", now.isoformat()) \
            .not_.is_("deleted_at", "null") \
            .execute()

        for profile in pending.data or []:
            user_id = profile["id"]
            try:
                # 1. DELETE FK-cascading rows (most tables ON DELETE CASCADE)
                # Some tables have ON DELETE SET NULL — those preserve audit (lgpd_requests)
                # Manual cleanup of tables that don't cascade properly:
                tables_explicit_delete = [
                    "search_results_cache", "search_results_store",  # may be too granular for CASCADE
                    "feedback", "classification_feedback",
                    "trial_email_log", "resend_webhook_events",  # delete delivery log
                    "analytics_events",                            # MON-FN-006
                    "dunning_state",                               # MON-FN-007
                    "abandoned_carts",                             # MON-FN-009
                ]
                for table in tables_explicit_delete:
                    sb.table(table).delete().eq("user_id", user_id).execute()

                # 2. DELETE auth.users (cascades to profiles via FK)
                admin.auth.admin.delete_user(user_id)

                # 3. Update lgpd_requests (status: processing → completed)
                sb.table("lgpd_requests").update({
                    "status": "completed",
                    "completed_at": now.isoformat(),
                }).eq("user_id", user_id).eq("action", "delete").execute()
                # Note: lgpd_requests.user_id will be SET NULL by FK ON DELETE SET NULL — audit preserved

                track_funnel_event("lgpd_deletion_completed", user_id, properties={
                    "completed_at": now.isoformat(),
                })

                smartlic_lgpd_deletion_completed_total.inc()
                results["deleted"] += 1
            except Exception as e:
                logger.error(f"Hard delete failed for user {user_id}: {e}")
                sentry_sdk.capture_exception(e, tags={"lgpd_action": "hard_delete", "user_id": user_id})
                # Mark for retry next cron tick (don't update status)
                results["errors"] += 1

        return results
    finally:
        await release_redis_lock("smartlic:lgpd_hard_delete:lock")
```
- [ ] Cron schedule: 12 UTC daily (after morning bursts)
- [ ] Send final confirmation email DEPOIS de hard delete (last touchpoint)
- [ ] Idempotência: após admin.auth.admin.delete_user, profiles row vai (CASCADE); next run skip naturally

### AC5: Endpoint cancel deletion (D+0 to D+30)

Given user mudou de ideia em <30 dias,
When email support OR endpoint cancel,
Then restore.

- [ ] Endpoint `POST /v1/me/cancel-deletion` (token-based, similar a cancel_trial):
```python
@router.post("/v1/me/cancel-deletion")
async def cancel_account_deletion(
    body: CancelDeletionRequest,  # {token: str}
):
    """User-initiated cancellation of pending deletion (within 30d window)."""
    user_id = verify_cancel_deletion_token(body.token)
    sb = get_supabase()
    profile = sb.table("profiles").select("deleted_at, deletion_scheduled_for").eq("id", user_id).single().execute()
    if not profile.data or not profile.data.get("deleted_at"):
        raise HTTPException(404, "No pending deletion found")
    if datetime.fromisoformat(profile.data["deletion_scheduled_for"].replace("Z", "+00:00")) < datetime.now(timezone.utc):
        raise HTTPException(410, "Deletion window expired")

    sb.table("profiles").update({
        "deleted_at": None,
        "deletion_scheduled_for": None,
        "deletion_reason": None,
    }).eq("id", user_id).execute()
    # Restore auth.users (un-ban)
    admin = get_supabase_admin()
    admin.auth.admin.update_user_by_id(user_id, {"ban_duration": "none"})
    # Note: email anonymization NÃO é revertida automaticamente — user precisa contactar suporte para email original

    sb.table("lgpd_requests").update({
        "status": "cancelled",
        "notes": "Cancelled by user within 30d window",
    }).eq("user_id", user_id).eq("action", "delete").eq("status", "processing").execute()

    track_funnel_event("lgpd_deletion_cancelled", user_id, properties={
        "cancelled_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "cancelled", "message": "Deleção cancelada. Sua conta está ativa novamente."}
```
- [ ] Token gerado em email confirmação D+0; expires_at = deletion_scheduled_for
- [ ] **Email original requires manual support intervention to restore** — esta é design choice (audit-friendly)

### AC6: Email templates

- [ ] Novo `backend/templates/emails/lgpd_deletion_d0_confirmation.html`:
  - Subject: `Sua conta SmartLic foi desativada — Deleção em 30 dias`
  - Conteúdo: confirmação ação + data de hard delete + link cancel + support email
- [ ] `lgpd_deletion_d30_completed.html`:
  - Subject: `Sua conta SmartLic foi permanentemente deletada`
  - Conteúdo: confirmação final + audit info (request_id, deleted_at)
  - Importante: enviar para email anonimizado FAILS — usar `email_at_request` da `lgpd_requests` row

### AC7: Frontend UI

- [ ] Em `frontend/app/conta/LgpdSection.tsx` (de MON-FN-010):
  - Adicionar card "Deletar minha conta"
  - Modal confirmação dupla: 1) modal info ("Tem certeza? 30 dias para cancelar") 2) input senha + checkbox "Entendo que..."
  - Disabled CTA até checkbox marcado
  - Pós-success: redirect `/login` com mensagem "Conta desativada"

### AC8: Métricas

- [ ] `smartlic_lgpd_deletion_requested_total`
- [ ] `smartlic_lgpd_deletion_completed_total` (hard delete done)
- [ ] `smartlic_lgpd_deletion_cancelled_total`
- [ ] Histograma `smartlic_lgpd_deletion_duration_seconds` (request → hard delete)

### AC9: Testes

- [ ] Unit `backend/tests/services/test_data_deletion.py`:
  - [ ] Soft-delete updates correct columns
  - [ ] Anonymization changes email but preserves UUID
  - [ ] Sessions revoked
  - [ ] Stripe subscriptions cancelled
- [ ] Integration `backend/tests/cron/test_lgpd_hard_delete.py`:
  - [ ] User soft-deleted >30d → hard delete cascades
  - [ ] User soft-deleted <30d → skip
  - [ ] FK CASCADE testado para todas tabelas relacionadas
  - [ ] lgpd_requests.user_id → NULL após hard delete (SET NULL)
  - [ ] Re-run cron mesmo dia → no errors (idempotente — user já deletado)
- [ ] Integration `backend/tests/routes/test_lgpd_deletion.py`:
  - [ ] DELETE /me com senha incorreta → 403
  - [ ] DELETE /me success → 202 + soft-delete
  - [ ] User soft-deleted não pode logar (auth.users banned)
  - [ ] Cancel-deletion antes de D+30 → restore funciona
  - [ ] Cancel-deletion após D+30 → 410
- [ ] E2E Playwright:
  - [ ] User flow: /conta → "Deletar conta" → modal confirmation → submit
  - [ ] Email recebido com cancel link
  - [ ] Click cancel → conta restaurada
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Coluna `profiles.deleted_at` + RLS update
- Endpoint DELETE /me (soft-delete)
- Endpoint cancel-deletion (D+0 a D+30 window)
- Cron lgpd_hard_delete_job (D+30 purge)
- Anonymization auth.users
- Stripe subscription cancellation antes
- 2 email templates
- Frontend UI

**OUT:**
- Manual restore de email original (support handles)
- Mass admin deletion endpoint
- Backup retention pós-hard-delete (Supabase backup separadamente)
- Right to rectification endpoint (LGPD Art. 18 III) — fora deste epic
- Right to data portability beyond export (MON-FN-010 cobre)
- Hard delete < 30d (compliance trade-off: 30d é razoável + permite cancelamento)
- Encryption-at-rest before deletion (over-engineering)

---

## Definition of Done

- [ ] Migration aplicada
- [ ] Endpoint DELETE /me funcional
- [ ] Soft-delete validado: user não loga, profiles.deleted_at set, sessions revoked
- [ ] Stripe subscriptions canceladas pre-deletion
- [ ] Cancel-deletion endpoint funciona com token
- [ ] Cron `lgpd_hard_delete_job` executando 12 UTC daily
- [ ] FK cascade testado para todas relevant tables
- [ ] 2 email templates criados + validados
- [ ] Frontend UI com double-confirm
- [ ] Cobertura ≥85%
- [ ] CodeRabbit clean
- [ ] Operational runbook em `docs/operations/lgpd-runbook.md` (estende MON-FN-010)
- [ ] LGPD compliance documentado em `docs/compliance/lgpd.md`
- [ ] Testar E2E completo: soft-delete → 30d (freezegun em CI) → hard-delete → confirmação

---

## Dev Notes

### Padrões existentes a reutilizar

- **`require_auth`:** existing
- **JWT signed token:** `services/trial_cancel_token.py` é referência (existing)
- **Supabase admin client:** `supabase_client.get_supabase_admin` (service role)
- **ARQ cron:** `cron/_loop.py`
- **`track_funnel_event`:** MON-FN-006

### Funções afetadas

- `backend/routes/conta.py` (NOVOS endpoints)
- `backend/services/data_deletion.py` (NOVO)
- `backend/services/lgpd_cancel_token.py` (NOVO ou estender `trial_cancel_token`)
- `backend/cron/lgpd_hard_delete.py` (NOVO)
- `backend/templates/emails/lgpd_deletion_*.html` (NOVO)
- `backend/job_queue.py::WorkerSettings` (registrar)
- `backend/metrics.py`
- `frontend/app/conta/LgpdSection.tsx` (estender de MON-FN-010)
- `supabase/migrations/YYYYMMDDHHMMSS_add_profiles_deleted_at.sql` + `.down.sql`

### Trade-off: 30 days regret window

Padrão GDPR/LGPD: 30 dias é "cooling-off period" comum. Trade-offs:
- Mais curto (7d): user mid-stress não tem tempo de se arrepender
- Mais longo (90d): legitimate compliance risk se ANPD audit pede prova de "right to erasure executed"
- 30d é Goldilocks zone

### Cascade FK setup

Antes de hard delete, audit cada tabela:
- `pipeline_items.user_id REFERENCES profiles(id) ON DELETE CASCADE` ✓
- `feedback.user_id REFERENCES profiles(id) ON DELETE CASCADE` ✓
- `analytics_events.user_id REFERENCES profiles(id) ON DELETE CASCADE` ✓ (MON-FN-006 setup)
- `lgpd_requests.user_id REFERENCES profiles(id) ON DELETE SET NULL` ✓ (audit preservation)

Migration de FKs missing → adicionar antes de MON-FN-011 deploy.

### Testing Standards

- Mock Supabase admin via `@patch("supabase_client.get_supabase_admin")`
- Mock Stripe subscription cancel via `@patch("stripe.Subscription.delete")`
- `freezegun` para advance to D+30
- Cobertura: `pytest --cov=backend/services/data_deletion.py --cov=backend/cron/lgpd_hard_delete.py`
- Anti-hang: pytest-timeout 30s

---

## Risk & Rollback

### Triggers de rollback
- Bug em cascade: orphan rows após hard delete
- User accidentally double-confirmed deletion (regret post-30d)
- Mass deletion abuse (bot? troll?)
- Stripe sub não cancelado pre-deletion (continua cobrando user deletado)

### Ações de rollback
1. **Imediato:** `LGPD_DELETION_ENABLED=false` — endpoint retorna 503; manual support
2. **Bug cascade:** manual SQL fix orphan rows; investigate FK constraints
3. **Wrong deletion:** support email pode restaurar via SQL pre-D+30 OR via Supabase backup post-D+30 (last resort)
4. **Mass abuse:** rate limit 1/dia per user + IP; CAPTCHA se necessário (futuro)

### Compliance
- Audit log em `lgpd_requests` é evidência legal — preservar via ON DELETE SET NULL
- Email confirmation final é prova de execução
- Hash do email original em `auth.users metadata` permite identificar request ANPD sem PII

---

## Dependencies

### Entrada
- **MON-FN-010** (LGPD export): tabela `lgpd_requests` criada + padrão estabelecido
- Supabase Admin API (service role key)
- Stripe API (cancel subscription)
- ARQ worker

### Saída
- Compliance LGPD baseline completo (export + delete = pacote)
- Habilita confiança enterprise (B2G consultorias auditam compliance)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "LGPD Data Deletion (Right to Erasure, Soft + Hard D+30)" |
| 2 | Complete description | Y | LGPD Art. 18 IV + 30d regret window + double-confirm pattern |
| 3 | Testable acceptance criteria | Y | 9 ACs incluindo cron D+30 + cancel-deletion + freezegun avançar 30d |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui rectification (Art. 18 III separate) |
| 5 | Dependencies mapped | Y | Entrada MON-FN-010 (mesma tabela `lgpd_requests`) |
| 6 | Complexity estimate | Y | M (3-4 dias) coerente — soft + hard + cancel + UI + cascade FK audit |
| 7 | Business value | Y | "Pacote LGPD" completo + confiança enterprise B2G |
| 8 | Risks documented | Y | Bug cascade + accidental deletion + mass abuse + Stripe sub não cancelado |
| 9 | Criteria of Done | Y | **Audit log preservado via ON DELETE SET NULL; FK cascade testado para todas relevant tables** |
| 10 | Alignment with PRD/Epic | Y | EPIC Constraint LGPD + Success Metric 6 (100% audit log) |

### Observations
- **Audit log obrigatório verificado:** Tabela `lgpd_requests.user_id` usa `ON DELETE SET NULL` (não CASCADE) explicitamente — preserva audit trail pós-hard delete; status="completed" + completed_at gravam evidência legal
- **SLA <72h aplicável aqui também:** soft-delete imediato; hard-delete em cron D+30 (não faz parte do SLA Art. 18 II que é para export)
- Anonymization correta: `auth.users.email` → `deleted-{user_id}@smartlic.deleted` + hash original SHA-256 em metadata (audit sem PII)
- Two-phase deletion (soft + hard) é GDPR/LGPD-compliant best practice
- Stripe subscription cancellation antes do soft-delete previne cobrança continuada
- Cancel deletion endpoint com token expira em `deletion_scheduled_for` (D+30)
- FK cascade audit listado em Dev Notes — migrations futuras devem revisar
- 30d regret window explicitamente justificado (Goldilocks zone)

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — LGPD right to erasure, soft + hard D+30 | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P1 compliance LGPD pacote completo; audit preservation via SET NULL verified; Status Draft → Ready. | @po (Pax) |
