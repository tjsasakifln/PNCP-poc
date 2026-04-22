# MON-REP-02: Infra `generated_reports` + Delivery por Email + Storage

**Priority:** P0
**Effort:** M (3 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-MON-REPORTS-2026-04](EPIC-MON-REPORTS-2026-04.md)
**Sprint:** Wave 1 (bloqueador de MON-REP-03/04/05/06 + MON-AI-02)

---

## Contexto

MON-REP-01 cria `purchases` + checkout. Quando uma compra vira `status='paid'`, um job ARQ precisa:
1. Despachar para o gerador correto (strategy pattern por `product_type`)
2. Gerar PDF assincronamente (pode levar 1-5 min para relatórios complexos)
3. Armazenar em Supabase Storage
4. Gerar link assinado (signed URL) com expiração de 48h
5. Enviar email via Resend com link de download + confirmação

Hoje existe apenas 1 tipo de PDF (`backend/pdf_report.py` para diagnóstico), síncrono e sem persistência. Precisamos da camada de orquestração.

---

## Acceptance Criteria

### AC1: Tabela `generated_reports`

- [ ] Migração cria:
```sql
CREATE TABLE public.generated_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  purchase_id uuid UNIQUE NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id),
  report_type text NOT NULL,
  status text NOT NULL DEFAULT 'queued' CHECK (status IN (
    'queued', 'generating', 'completed', 'failed', 'expired'
  )),
  storage_bucket text NOT NULL DEFAULT 'generated-reports',
  storage_path text NULL,  -- reports/{user_id}/{report_id}.pdf
  file_size_bytes int NULL,
  download_count int NOT NULL DEFAULT 0,
  last_downloaded_at timestamptz NULL,
  generated_at timestamptz NULL,
  expires_at timestamptz NULL,  -- 48h after generated_at
  error_message text NULL,
  attempt_count int NOT NULL DEFAULT 0,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON generated_reports (user_id, created_at DESC);
CREATE INDEX ON generated_reports (status, attempt_count) WHERE status IN ('queued','failed');
```
- [ ] RLS: user sees only own; service-role full access
- [ ] Migração paired down

### AC2: Supabase Storage bucket

- [ ] Migração cria bucket `generated-reports` (privado) via SQL: `INSERT INTO storage.buckets (id, name, public) VALUES ('generated-reports', 'generated-reports', false)`
- [ ] RLS policy em `storage.objects`: SELECT permitido apenas se `bucket_id='generated-reports' AND auth.uid()::text = (storage.foldername(name))[1]`
- [ ] Upload via backend service-role apenas (não exposto ao frontend diretamente)

### AC3: ARQ job `generate_report`

- [ ] `backend/jobs/report_generation.py` implementa:
```python
async def generate_report_job(ctx, purchase_id: UUID) -> dict:
    # 1. fetch purchase + create generated_reports row (status=generating)
    # 2. dispatch por purchase.product_type → gerador específico (strategy)
    # 3. upload PDF to Supabase Storage at reports/{user_id}/{report_id}.pdf
    # 4. update generated_reports: status=completed, storage_path, generated_at, expires_at=now+48h
    # 5. enqueue send_report_ready_email(purchase_id)
    # 6. on exception: status=failed, error_message, attempt_count++; retry max 3x
```
- [ ] Strategy pattern em `backend/reports/` com registry:
```python
REPORT_GENERATORS = {
    'report_supplier': SupplierReportGenerator,
    'report_price_reference': PriceReferenceReportGenerator,
    # ... etc
}
```
- [ ] Timeout: 5 min por geração; exceeded → fail + retry
- [ ] Métricas Prometheus: `smartlic_report_generation_duration_seconds{product_type}`, `smartlic_report_generation_failures_total{product_type,reason}`

### AC4: Template email `report_ready.py`

- [ ] Novo `backend/templates/emails/report_ready.py`:
  - Assunto: `"📄 Seu relatório {product_name} está pronto"`
  - Body: nome do produto, parâmetros resumidos (ex: "CNPJ: XX.XXX.XXX/0001-XX"), botão CTA "Baixar relatório" (link assinado 48h), link secundário "Acessar histórico", rodapé legal
  - Versões HTML + text/plain
  - Emoji substituído por asset CDN (se branding requer)
- [ ] Invocação: `email_service.send_email_async(user_email, subject, html, text)` com retry

### AC5: Endpoint de download com signed URL

- [ ] `GET /v1/reports/{report_id}/download` — autenticado JWT (não API key)
- [ ] Valida:
  - `user_id == auth.uid()`
  - `status == 'completed'`
  - `expires_at > now()`
- [ ] Gera signed URL do Supabase Storage com TTL 5 minutos (`supabase.storage.from_('generated-reports').create_signed_url(path, 300)`)
- [ ] Retorna `{download_url, expires_at, file_size_bytes}` — frontend faz fetch direto
- [ ] Incrementa `download_count` e atualiza `last_downloaded_at`
- [ ] Rate limit 20/min por user

### AC6: Cron de limpeza

- [ ] ARQ cron diário 03:00 BRT: marca `status='expired'` em reports com `expires_at < now()` + remove PDF do storage
- [ ] Métricas: `smartlic_reports_expired_total`, `smartlic_reports_storage_cleaned_bytes_total`

### AC7: Testes

- [ ] Unit: `backend/tests/jobs/test_report_generation_dispatcher.py` — mock generator, valida strategy dispatch + status transitions
- [ ] Integration: E2E flow — purchase paid → job executes → file in storage → email sent (mock Resend)
- [ ] Unit: `backend/tests/routes/test_report_download.py` — ownership check, expiração, rate limit
- [ ] Unit: template email renderiza sem quebras (ambos HTML e text)

---

## Scope

**IN:**
- Migração + bucket + RLS
- ARQ job + strategy pattern
- Template email
- Download endpoint
- Cron de cleanup
- Testes

**OUT:**
- Geradores específicos (MON-REP-03 em diante)
- Notificação webhook para integradores (fora do escopo; podem polling GET `/reports/{id}`)

---

## Dependências

- MON-REP-01 (purchases table + webhook) — obrigatória
- Supabase Storage habilitado (já em uso para outros ativos)
- Resend configurado (já em uso — STORY-301 e outras)
- ARQ worker (já em prod)

---

## Riscos

- **Geração PDF pesada bloqueia worker:** timeout 5 min previne; considerar worker dedicado `PROCESS_TYPE=report_worker` se volume crescer
- **Storage cost runaway:** 48h TTL + cleanup cron limita; monitorar Supabase Storage usage semanalmente
- **Email não entregue:** Resend tem retry automático; fallback manual via admin UI para reenvio (`POST /v1/admin/reports/{id}/resend-email`)

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_generated_reports_table.sql` + `.down.sql`
- `supabase/migrations/.../create_generated_reports_bucket.sql`
- `backend/jobs/report_generation.py` (novo)
- `backend/reports/__init__.py` + `_registry.py` (novo)
- `backend/templates/emails/report_ready.py` (novo)
- `backend/routes/reports.py` (estender — adicionar `/v1/reports/{id}/download`)
- `backend/jobs/cron/report_cleanup.py` (novo)
- `backend/tests/jobs/test_report_generation_dispatcher.py` (novo)
- `backend/tests/routes/test_report_download.py` (novo)

---

## Definition of Done

- [ ] Migração + bucket aplicados em produção
- [ ] Mock generator (`debug_report`) end-to-end: purchase → job → storage → email → download funciona
- [ ] p95 geração (mock) < 30s
- [ ] Cron cleanup rodando + métricas Prometheus visíveis
- [ ] Testes backend passando
- [ ] E2E Playwright cobrindo fluxo completo (mock Stripe + Resend)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — pipeline de geração + entrega, bloqueador de todos os 4 tipos de relatório |
