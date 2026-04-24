# SEN-BE-008: Slow-request em rotas core `/health`, `/v1/me`, `/v1/orgao/*`, `/v1/empresa/*/perfil-b2g`

**Status:** Ready
**Origem:** Sentry unresolved — issues 7409200983 (/health 160.9s 51evt), 7406847180 (/v1/me 160.9s 36evt), 7401422575 (/v1/empresa/.../perfil-b2g 160.9s 153evt), 7409199844 (/v1/orgao/.../stats 692.6s 263evt), 7409549197 (HEAD /health 148.2s 7evt), 7409553347 (/health/cache 148.1s 5evt), 7409549184 (OPTIONS /v1/me 148.2s 13evt), 7409504498 (/v1/fornecedores/.../profile 148.2s 61evt)
**Prioridade:** P0 — Crítico (`/health` lento afeta uptime monitoring; `/v1/me` lento impacta toda UI autenticada)
**Complexidade:** L (Large)
**Owner:** @dev + @data-engineer
**Tipo:** Performance / Observability

---

## Problema

Rotas de alto tráfego críticas estão com slow_request warnings:

| Rota | p95 observado | Eventos |
|------|---------------|---------|
| `GET /v1/orgao/*/stats` | 692.6s | 263 |
| `GET /v1/empresa/*/perfil-b2g` | 160.9s | 153 |
| `GET /v1/fornecedores/*/profile` | 148.2s | 61 |
| `GET /health` | 160.9s | 51 |
| `GET /v1/me` | 160.9s | 36 |
| `OPTIONS /v1/me` | 148.2s | 13 |
| `HEAD /health` | 148.2s | 7 |
| `GET /health/cache` | 148.1s | 5 |

Impacto:
- **`/health`**: uptime monitor (Railway, UptimeRobot) marca serviço down → false-positive pages
- **`/v1/me`**: chamado por toda tela autenticada — UI trava esperando resposta
- **`OPTIONS /v1/me`**: preflight CORS lento — bloqueia primeira request do browser
- **`/v1/empresa/*/perfil-b2g`**: 153 evt em rota principal de landing page B2G — alto impacto em SEO

---

## Critérios de Aceite

- [ ] **AC1:** `/health` e `HEAD /health` devem retornar <100ms em 99% dos casos — SEM tocar DB (apenas memory probe + simple counters)
- [ ] **AC2:** `/health/cache` deve ter timeout hard de 5s — retornar "unknown" após timeout, NÃO travar o request
- [ ] **AC3:** `/v1/me` usa cache L1 por `user_id` com TTL 30s — evita JOIN repetido com `profiles` + `subscription_status` a cada request
- [ ] **AC4:** `OPTIONS /v1/me` (preflight CORS) responde em <20ms — adicionar middleware dedicado no topo do pipeline
- [ ] **AC5:** `/v1/orgao/*/stats` — paginar resultados + índice composto (ver SEN-BE-001)
- [ ] **AC6:** `/v1/empresa/*/perfil-b2g` e `/v1/fornecedores/*/profile` — cache L2 (Supabase) TTL 1h, `stale-while-revalidate` 6h
- [ ] **AC7:** Sentry issues listadas reduzem para <5 eventos/dia cada após fix
- [ ] **AC8:** p95 de `/v1/me` <500ms medido 7 dias pós-deploy

### Anti-requisitos

- NÃO usar cache em `/health` de forma que esconda falha real — check leve deve ser sempre "agora"
- NÃO adicionar cache em `/v1/me` sem invalidação em webhook Stripe (subscription_updated)

---

## Referência de implementação

Arquivos prováveis:
- `backend/health.py` — separar endpoint rápido (liveness) de `/health/detailed` (readiness)
- `backend/routes/user.py::me`
- `backend/routes/orgao_publico.py`
- `backend/routes/empresa_publico.py`
- `backend/routes/fornecedores_publicos.py`
- CORS middleware em `backend/main.py`

---

## Riscos

- **R1 (Alto):** Cache de `/v1/me` desatualizado pode mostrar plano antigo pós-upgrade — invalidar no webhook Stripe `customer.subscription.updated`
- **R2 (Médio):** Separar `/health` (fast) de `/health/detailed` (deep) precisa ajustar config Railway/UptimeRobot
- **R3 (Baixo):** OPTIONS middleware novo precisa testar com preflight real (ex.: `curl -X OPTIONS ... -H "Origin: https://smartlic.tech"`)

## Dependências

- SEN-BE-001 (statement_timeout) — `orgao/*/stats` possivelmente compartilha fix
- SEN-BE-006 (slow stats) — fornecedores/profile provavelmente compartilha índice

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — 8 issues core endpoints, 589 eventos combinados |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (lastSeen 2026-04-22). Promovida Draft → Ready |
