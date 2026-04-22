# MON-API-01: API Key Management — Tabela, Middleware X-API-Key, Dashboard

**Priority:** P0
**Effort:** M (3 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-MON-API-2026-04](EPIC-MON-API-2026-04.md)
**Sprint:** Wave 1 (bloqueador de MON-API-02/03/04/05 + MON-AI-01; STORY-434 também deve reutilizar)

---

## Contexto

Hoje o backend autentica via **JWT Supabase exclusivamente** (`backend/auth.py::get_current_user` com HTTPBearer). Para monetizar a API B2B (Camada 4) e permitir integrações server-to-server (fintechs, ERPs), precisamos suporte a `X-API-Key: sk_...`:

- Fintechs não querem fazer login OAuth — querem key rotacionável em config
- RapidAPI espera header padronizado
- Rate limits e billing por key facilita auditoria

Essa infra também será usada por STORY-434 (API pública gratuita) quando for implementada, e por MON-AI-01 (Semantic Search).

---

## Acceptance Criteria

### AC1: Tabela `api_keys`

- [ ] Migração cria:
```sql
CREATE TABLE public.api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL,  -- label escolhido pelo user (ex: "Production", "Staging")
  key_prefix text NOT NULL UNIQUE,  -- primeiros 12 chars do sk_... plaintext, para lookup visual
  key_hash text NOT NULL,  -- SHA-256 do sk_ full
  scopes jsonb NOT NULL DEFAULT '["read"]'::jsonb,  -- ["read"], ["read","write"], ["admin"]
  rate_limit_per_minute int NOT NULL DEFAULT 60,
  monthly_quota_cents int NOT NULL DEFAULT 500_00,  -- R$ 500 default
  used_cents_current_month int NOT NULL DEFAULT 0,
  last_used_at timestamptz NULL,
  last_used_ip inet NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz NULL,
  expires_at timestamptz NULL,  -- optional expiration
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX ON api_keys (user_id, revoked_at) WHERE revoked_at IS NULL;
CREATE INDEX ON api_keys (key_prefix);
```
- [ ] RLS: user sees only own keys; service-role full access
- [ ] Migração paired down

### AC2: Middleware `X-API-Key`

- [ ] Novo `backend/auth/api_key.py`:
```python
async def get_current_api_key(x_api_key: str = Header(None)) -> ApiKey:
    # 1. Parse prefix + hash
    # 2. Cache L1 Redis 60s por prefix (reduz DB hit)
    # 3. Check revoked_at, expires_at, monthly_quota
    # 4. Update last_used_at + last_used_ip (fire-and-forget)
    # 5. Return ApiKey pydantic model
```
- [ ] Dependency factory `require_api_key_or_jwt()` aceita ambos: tenta `X-API-Key` primeiro, fallback `Authorization: Bearer`
- [ ] Hash SHA-256 + timing-safe compare (`hmac.compare_digest`)
- [ ] Prefix convention: `sk_live_xxxxxxxx` (prod) ou `sk_test_xxxxxxxx` (dev)

### AC3: Endpoints CRUD de API keys

- [ ] `POST /v1/api-keys` (auth JWT):
  - Body: `{name: str, scopes?: [str], monthly_quota_cents?: int, expires_at?: datetime}`
  - Gera key `sk_live_{secrets.token_urlsafe(32)}`
  - Retorna `{id, key_prefix, full_key}` — **full_key retornado SOMENTE NO CREATE** (plaintext), nunca mais
  - Limite: max 10 keys ativos por user (free); 50 (paid)
- [ ] `GET /v1/api-keys` — lista keys do user (sem plaintext, só prefix + metadata)
- [ ] `PATCH /v1/api-keys/{id}` — atualizar name, scopes, monthly_quota_cents
- [ ] `DELETE /v1/api-keys/{id}` — soft-delete (seta `revoked_at=now()`)

### AC4: Dashboard frontend `/conta/api-keys`

- [ ] `frontend/app/conta/api-keys/page.tsx`:
  - Botão "Gerar nova API key" → modal: nome + escopos + limite
  - Modal pós-criação: mostra plaintext key com botão "Copiar", aviso "Esta chave não será exibida novamente"
  - Tabela: nome, prefixo (ex: `sk_live_abc***`), último uso, status (ativa/revogada/expirada), gasto mês atual
  - Ação "Revogar" (confirm dialog)
- [ ] Link para docs `/api` (criada em MON-API-05)

### AC5: Observability

- [ ] Prometheus: `smartlic_api_key_requests_total{prefix, scope, status}`, `smartlic_api_key_active_total`
- [ ] Sentry: fingerprint `["api_key", prefix, endpoint]` para erros por key
- [ ] Log sanitization: **NUNCA** logar full key; apenas prefix

### AC6: Testes

- [ ] Unit: `backend/tests/auth/test_api_key.py`
  - Create key → hash correto, prefix estável
  - Valid key → autentica
  - Revoked key → 401
  - Expired key → 401
  - Quota exceeded → 402 Payment Required
  - Rate limit → 429
  - Timing-safe compare (teste com key quase-correta)
- [ ] Integration: `test_require_api_key_or_jwt.py` cobre fallback correto
- [ ] E2E Playwright: user cria key, copia, revoga

---

## Scope

**IN:**
- Migração + RLS
- Middleware + dependency
- CRUD endpoints
- Dashboard frontend
- Prometheus + Sentry
- Testes

**OUT:**
- Metered billing per-request (MON-API-02)
- Webhook de uso anômalo (futuro)
- OAuth2 client credentials flow (fora de escopo; API key cobre 95% dos casos)

---

## Dependências

- Nenhuma (foundation)

---

## Riscos

- **Key leaked em logs:** log sanitizer enforcement obrigatório — add regex `sk_(live|test)_[A-Za-z0-9_-]{20,}` à denylist
- **Hash SHA-256 não é BCrypt:** velocidade > segurança (chave já tem 32 bytes entropia, não sofre brute-force viável); documentar decisão
- **Migration em produção:** tabela vazia inicial, sem risco de lock

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_api_keys_table.sql` + `.down.sql`
- `backend/auth/api_key.py` (novo)
- `backend/routes/api_keys.py` (novo)
- `backend/schemas/api_key.py` (novo)
- `backend/startup/routes.py` (registrar router)
- `frontend/app/conta/api-keys/page.tsx` (novo)
- `backend/tests/auth/test_api_key.py` (novo)
- `backend/log_sanitizer.py` (adicionar regex para keys)

---

## Definition of Done

- [ ] Migração aplicada em prod
- [ ] User cria key via dashboard + faz request autenticada em endpoint de teste
- [ ] Revogação bloqueia próximos requests imediatamente
- [ ] Testes passando
- [ ] Log sanitization validada (teste de integração submete request com key e verifica logs)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — foundation B2B API; também será reutilizada por STORY-434 + MON-AI-01 |
