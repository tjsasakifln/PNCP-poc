# MON-FN-001: Resend Webhook HMAC Verify (svix-signature)

**Priority:** P0
**Effort:** S (1 dia)
**Squad:** @dev
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 1 (29/abr–05/mai)
**Sprint Window:** Sprint 1 (não-bloqueador para outras MON-FN)
**Dependências bloqueadoras:** Nenhuma

---

## Contexto

`backend/email_service.py:195+` envia transacionais via Resend SDK (`smartlic.tech` domain verified, memory `reference_resend_personal_tone_send`). Existe webhook Resend cadastrado em produção mas **sem HMAC verify** (memory `reference_trial_email_log_delivery_status_null` — webhook ID `758ea803` criado via API mas gap aberto: HMAC ainda não implementado). Hoje qualquer POST para o endpoint `webhooks/resend` é processado como evento legítimo — risco de spoofing + bounces silenciosos minam deliverability + funil cego (user marcado como "delivered" sem prova).

Resend usa o protocolo Svix com 3 headers obrigatórios: `svix-id`, `svix-timestamp`, `svix-signature`. SDK `resend.webhooks._webhook` já está instalado em `backend/venv/Lib/site-packages/resend/webhooks/_webhook.py` (verificado). A mecânica é HMAC-SHA256 sobre `{svix_id}.{svix_timestamp}.{payload}` com chave em base64 derivada de `RESEND_WEBHOOK_SECRET` (formato `whsec_xxx`).

**Por que P0:** outreach pessoal pivô (memory 2026-04-26) depende 100% de deliverability mensurável — bounces silenciosos = decisões de SEO/funil baseadas em ruído. Single point of failure em compliance LGPD (proof of delivery). Sprint 1 paralelo, S effort, 0 bloqueio.

**Paths críticos:**
- `backend/email_service.py:195` (Resend send)
- `backend/webhooks/` (criar `resend.py` ao lado de `stripe.py`)
- `backend/startup/routes.py` ou `main.py` (registrar router)
- `supabase/migrations/` (tabela `resend_webhook_events`)

---

## Acceptance Criteria

### AC1: Tabela `resend_webhook_events` (idempotência + audit)

Given que webhooks Resend entregam 7 tipos de eventos (`email.sent`, `email.delivered`, `email.delivery_delayed`, `email.complained`, `email.bounced`, `email.opened`, `email.clicked`),
When um evento chega no endpoint,
Then o handler grava em `resend_webhook_events` (similar a `stripe_webhook_events` STORY-307).

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_resend_webhook_events.sql`:
```sql
CREATE TABLE public.resend_webhook_events (
  id text PRIMARY KEY,                              -- svix-id (idempotência)
  type text NOT NULL,                                -- email.sent | email.bounced | etc.
  status text NOT NULL DEFAULT 'processing',        -- processing | completed | failed | invalid_signature
  email_id text,                                     -- Resend email_id (Resend's UUID)
  recipient text,                                    -- to address
  payload jsonb,                                     -- full event payload
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz NULL,
  error text NULL
);
CREATE INDEX idx_resend_webhook_events_received_at ON public.resend_webhook_events (received_at DESC);
CREATE INDEX idx_resend_webhook_events_type ON public.resend_webhook_events (type);
CREATE INDEX idx_resend_webhook_events_email_id ON public.resend_webhook_events (email_id) WHERE email_id IS NOT NULL;

-- RLS: only service-role (no user-facing access)
ALTER TABLE public.resend_webhook_events ENABLE ROW LEVEL SECURITY;
```
- [ ] Migration paired down `.down.sql` (DROP TABLE + DROP INDEX cascade)
- [ ] Schema documentado em `docs/architecture/webhooks.md` ou inline comment

### AC2: HMAC verify usando `svix-signature`

Given um POST em `/webhooks/resend` com headers `svix-id`, `svix-timestamp`, `svix-signature`,
When o handler processa,
Then verifica HMAC-SHA256 com `RESEND_WEBHOOK_SECRET` (env var); rejeita 401 em mismatch.

- [ ] Novo `backend/webhooks/resend.py`:
```python
import os
import hmac
import hashlib
import base64
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

router = APIRouter()

RESEND_WEBHOOK_SECRET = os.getenv("RESEND_WEBHOOK_SECRET", "")  # whsec_xxx format

def _verify_svix_signature(
    payload: bytes,
    svix_id: str,
    svix_timestamp: str,
    svix_signature: str,
    secret: str,
) -> bool:
    """Verify Svix HMAC signature using timing-safe compare.

    Signature format: 'v1,base64(hmac_sha256(svix_id.svix_timestamp.payload, secret))'
    Multiple signatures may be space-separated (rotation grace period).
    """
    if not secret.startswith("whsec_"):
        return False
    secret_bytes = base64.b64decode(secret[len("whsec_"):])
    signed_content = f"{svix_id}.{svix_timestamp}.{payload.decode('utf-8')}".encode()
    expected = base64.b64encode(
        hmac.new(secret_bytes, signed_content, hashlib.sha256).digest()
    ).decode()

    # Compare against ALL provided signatures (Svix supports rotation)
    for sig in svix_signature.split(" "):
        if "," in sig:
            _version, value = sig.split(",", 1)
            if hmac.compare_digest(value, expected):
                return True
    return False

@router.post("/webhooks/resend")
async def resend_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
):
    if not (svix_id and svix_timestamp and svix_signature):
        raise HTTPException(status_code=400, detail="Missing svix headers")
    if not RESEND_WEBHOOK_SECRET:
        # fail-closed in prod, fail-open dev (FAILOPEN_SVIX flag if needed)
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    payload = await request.body()
    if not _verify_svix_signature(
        payload, svix_id, svix_timestamp, svix_signature, RESEND_WEBHOOK_SECRET
    ):
        # AC4: increment counter, return 401
        smartlic_resend_webhook_invalid_total.inc()
        raise HTTPException(status_code=401, detail="Invalid signature")
    # ... idempotency check + handler dispatch
```
- [ ] Use `hmac.compare_digest` (timing-safe)
- [ ] Sentry breadcrumb com `svix_id` em failure (sem expor secret)
- [ ] Replay protection: rejeitar se `svix_timestamp` é >5min antigo (clock skew tolerance)

### AC3: Idempotência via tabela `resend_webhook_events`

Given evento com mesmo `svix-id` recebido duas vezes,
When o handler tenta processar,
Then o segundo é detectado como duplicate e ignorado (200 OK retornado).

- [ ] INSERT ON CONFLICT (id) DO NOTHING; se `data` vazio → já processado, retornar `{"status": "already_processed"}`
- [ ] Padrão idêntico ao usado em `webhooks/stripe.py:136-145` (STORY-307)
- [ ] Status workflow: `processing` → `completed` ou `failed`
- [ ] Test: dispatchar mesmo `svix-id` 2x consecutivos; verificar uma única linha em DB

### AC4: Counter Prometheus + Sentry alert

Given webhook signature mismatch,
When mais de 5 ocorrências em 5 min,
Then Sentry capture_message + Prometheus counter exposed.

- [ ] Prometheus counter `smartlic_resend_webhook_invalid_total{reason}` (reason ∈ {missing_headers, signature_mismatch, expired_timestamp, secret_not_configured})
- [ ] Counter `smartlic_resend_webhook_processed_total{type, status}` (sucesso/falha por tipo de evento)
- [ ] Sentry tag `webhook=resend`, fingerprint `["resend_webhook", "invalid_signature"]`
- [ ] Logger sanitization: nunca logar secret nem payload completo (apenas svix_id + type)

### AC5: Handler dispatcher por event type

Given evento `email.bounced` validado,
When o handler dispatcher route,
Then atualiza `trial_email_log` ou tabela apropriada com `delivery_status='bounced'`.

- [ ] Mapear 7 event types Resend para handlers internos:
  - `email.sent` → mark `trial_email_log.delivery_status='sent'`
  - `email.delivered` → `'delivered'`
  - `email.bounced` → `'bounced'` + sentry alert se rate >2% nas últimas 100 entregas
  - `email.complained` → `'complained'` + bloquear envios futuros para este recipient (suppression list)
  - `email.delivery_delayed` → `'delayed'`
  - `email.opened` → `opened_at = now()`
  - `email.clicked` → `clicked_at = now()`
- [ ] Suppression list em tabela existente ou nova `email_suppression` (recipient, reason, suppressed_at)

### AC6: Configuração env vars + registro do router

- [ ] Adicionar `RESEND_WEBHOOK_SECRET` em `.env.example` com comentário "Get from Resend Dashboard > Webhooks > Signing secret"
- [ ] Validar variável em startup (warn se ausente em dev, fail em prod via MON-FN-005 pattern)
- [ ] Registrar router em `backend/main.py` ou `backend/startup/routes.py`: `app.include_router(resend_webhook.router, tags=["webhooks"])`
- [ ] Documentar URL final em `docs/architecture/webhooks.md`: `https://api.smartlic.tech/webhooks/resend`

### AC7: Testes (unit + integration + E2E simulado)

- [ ] Unit `backend/tests/webhooks/test_resend_webhook.py`:
  - [ ] HMAC válido com `whsec_test...` → 200
  - [ ] HMAC inválido (signature flip) → 401 + counter incrementado
  - [ ] Headers ausentes → 400
  - [ ] Replay >5min antigo → 400 (timestamp expired)
  - [ ] Multi-signature (rotation) → primeiro válido autoriza
  - [ ] Idempotência: 2x mesmo svix-id → primeira processa, segunda retorna `already_processed`
  - [ ] Suppression list: `email.complained` insere em `email_suppression`
- [ ] Integration: simular POST com fixture `resend_webhook_event` (factory util `tests/factories/resend.py`)
- [ ] E2E Playwright (opcional Sprint 1+): trigger envio real → simular bounce via Resend test mode → verificar `trial_email_log.delivery_status='bounced'`
- [ ] Cobertura ≥85% em `backend/webhooks/resend.py`

---

## Scope

**IN:**
- HMAC verify via Svix protocol (svix-id, svix-timestamp, svix-signature)
- Tabela `resend_webhook_events` (idempotência + audit)
- Counter Prometheus + Sentry alert
- 7 event types dispatched
- Suppression list (`email.complained`)
- Migration paired down.sql

**OUT:**
- Reescrever `email_service.py:send_email` (apenas adiciona webhook leitor)
- Dashboard frontend de delivery (futuro)
- Bounces re-send automation (futuro, lifecycle-team)
- Migrar para Resend API v2 SDK helper `resend.webhooks.verify()` — preferimos implementação custom para timing-safe compare auditável
- Email reputation monitoring externo (Postmaster Tools etc.)

---

## Definition of Done

- [ ] Migration aplicada em prod (`npx supabase db push`); RLS validada
- [ ] Endpoint `/webhooks/resend` configurado no Resend Dashboard como `https://api.smartlic.tech/webhooks/resend`
- [ ] `RESEND_WEBHOOK_SECRET` setado em Railway (`bidiq-backend`) — valor `whsec_xxx`
- [ ] HMAC verify ativo: tentativa de POST sem signature retorna 401 (validar com curl)
- [ ] Counter `smartlic_resend_webhook_invalid_total` exposto em `/metrics`
- [ ] `smartlic_resend_webhook_processed_total{type=email.delivered}` >0 após 24h em prod (sinal de tráfego real)
- [ ] Idempotência verificada: dispatchar mesmo `svix-id` 2x → único registro em DB
- [ ] `trial_email_log.delivery_status` atualiza corretamente (sample manual: enviar trial start email + verificar status `delivered` no log)
- [ ] Sentry alert dispara em invalid_signature (teste com header forjado)
- [ ] Cobertura ≥85% nas linhas tocadas (`pytest --cov=backend/webhooks/resend.py`)
- [ ] CodeRabbit clean (no CRITICAL findings)
- [ ] Runbook rollback documentado abaixo
- [ ] Memory `reference_trial_email_log_delivery_status_null` atualizada com "HMAC verify implementado"

---

## Dev Notes

### Padrões existentes a reutilizar

- **Idempotência:** copiar pattern `webhooks/stripe.py:136-178` (claim_result + stuck_check) — ajuste: 1min stuck threshold em vez de 5min (Resend events são leves).
- **Logger sanitizer:** `from log_sanitizer import get_sanitized_logger` (já standard).
- **Counter Prometheus:** registrar em `backend/metrics.py` no padrão dos counters existentes (`smartlic_*_total`).
- **Resend SDK helper:** `resend.webhooks.Webhook(secret).verify(payload, headers)` existe — pode usar para AC2 ao invés de implementação custom (decisão @dev: custom traz timing-safe explícito + auditabilidade; SDK introduz dependência em update).

### Funções afetadas

- `backend/webhooks/resend.py` (NOVO)
- `backend/main.py` ou `backend/startup/routes.py` (registrar router)
- `backend/metrics.py` (adicionar counters)
- `backend/email_service.py` (adicionar `from email_suppression import is_suppressed` antes de `resend.Emails.send` para skip suppressed addresses)
- `supabase/migrations/YYYYMMDDHHMMSS_create_resend_webhook_events.sql` + `.down.sql`

### Testing Standards

- Tests em `backend/tests/webhooks/test_resend_webhook.py`
- Fixture `resend_webhook_event_factory` em `backend/tests/factories/resend.py` para gerar eventos válidos com signature pre-computada
- Mock `RESEND_WEBHOOK_SECRET` via `monkeypatch.setenv`
- Anti-hang: pytest-timeout 30s default — não introduzir loops síncronos
- Use `client.post` do `TestClient`; passe headers explicitamente

---

## Risk & Rollback

### Triggers de rollback
- `smartlic_resend_webhook_invalid_total` rate >10/min (signature legítima quebrando) — provável misconfig do secret
- `email.delivered` events param de chegar (Resend desabilita endpoint após 5 falhas 5xx consecutivas)
- Webhook handler timeout >5s causando 504 cascade

### Ações de rollback
1. **Imediato:** desabilitar webhook no Resend Dashboard (preserva eventos no Resend retry queue 24h)
2. **Code-level:** feature flag `RESEND_WEBHOOK_HMAC_ENFORCED=false` — temporariamente aceita sem verify (apenas dev/staging; nunca em prod)
3. **Schema:** down.sql disponível; mas tabela é append-only e tem audit value — preferir manter mesmo em rollback
4. **Comunicação:** Sentry fingerprint `["resend_webhook", "invalid_signature"]` notifica DevOps imediatamente

### Compliance LGPD
- Tabela `resend_webhook_events` armazena PII (recipient email) — incluir em LGPD data export (MON-FN-010) e deletion (MON-FN-011)
- Retention: 90 dias (alinhado com `analytics_events`)

---

## Dependencies

### Entrada
- Resend account + domain verified `smartlic.tech` (já existe; memory `reference_resend_personal_tone_send`)
- Webhook ID `758ea803` criado em prod (memory `reference_trial_email_log_delivery_status_null`)
- Tabela `trial_email_log` (existe; alimentada por `email_service.py`)

### Saída
- MON-FN-007 (dunning) consome `email.bounced` events para skip retry
- MON-FN-009 (abandoned cart) consome `email.delivered` para confirmar entrega
- MON-FN-010 (LGPD export) inclui `resend_webhook_events` no ZIP do user

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Resend Webhook HMAC Verify (svix-signature)" — ação + protocolo claros |
| 2 | Complete description | Y | Contexto cita memory `reference_trial_email_log_delivery_status_null` + paths código |
| 3 | Testable acceptance criteria | Y | 7 ACs com Given/When/Then + checklists granulares |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT cita decisão custom vs SDK helper |
| 5 | Dependencies mapped | Y | Entrada (Resend account, webhook ID 758ea803) e Saída (MON-FN-007/009/010) |
| 6 | Complexity estimate | Y | S (1 dia) coerente com escopo (1 endpoint + 1 tabela + tests) |
| 7 | Business value | Y | Outreach pessoal pivô + LGPD proof of delivery + funnel não cego |
| 8 | Risks documented | Y | Triggers de rollback + ações + compliance LGPD (90d retention) |
| 9 | Criteria of Done | Y | DoD inclui validação curl, counter exposed, idempotência verificada |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #1 explicitamente endereçado; Resend SDK já instalado |

### Observations
- Padrão `track_funnel_event` API canônica respeitado via referência indireta (handler dispatcher atualiza `trial_email_log`)
- HMAC custom implementation com `hmac.compare_digest` é decisão acertada vs SDK helper (auditabilidade timing-safe)
- Replay protection (>5min) é detalhe Fortune-500 standard
- Migration paired `.down.sql` documentada (CI gate STORY-6.2 satisfeita)

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada a partir EPIC-MON-FN-2026-Q2 (gap HMAC Resend) | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Story P0 enterprise-ready; Status Draft → Ready. | @po (Pax) |
