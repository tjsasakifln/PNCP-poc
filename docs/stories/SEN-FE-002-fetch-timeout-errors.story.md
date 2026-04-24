# SEN-FE-002: `TimeoutError: The operation was aborted due to timeout` (cluster 8 issues)

**Status:** Ready
**Origem:** Sentry unresolved — 8 issues: 7432040248, 7432039136, 7432037624 (sitemap/4.xml 9evt), 7431736871, 7432037939, 7431063905 (32evt), 7431063920 (52evt), 7412085160
**Prioridade:** P1 — Alto (113+ eventos combinados)
**Complexidade:** M (Medium)
**Owner:** @dev
**Tipo:** Resilience

---

## Problema

8 issues separadas com mesmo título `TimeoutError: The operation was aborted due to timeout` — diferentes fingerprints pois stacks diferem, mas root cause é compartilhada: fetches do Next.js/browser ultrapassando timeout padrão.

Um caso com culprit identificado: `GET /sitemap/4.xml` (9 eventos) — fetch de sitemap stático demorou além do limite.

Total eventos em 14d: ~113+ (concentrados em 2026-04-22).

Hipóteses:
- Fetches do Next.js server-side (Node) para o backend bateram >120s → abort
- Sitemap XML gerados no Next.js dependem de `/v1/sitemap/*` backend (SEN-BE-007)
- `fetch(..., { signal: AbortSignal.timeout(N) })` sem fallback user-friendly

Impacto:
- Sitemap XML servido com erro → Google GSC marca sitemap inválido
- Páginas SSR que fazem fetch podem crashar com 500

---

## Critérios de Aceite

- [ ] **AC1:** Auditar todos os `fetch(` em `frontend/app/**/*.ts[x]` + `frontend/lib/**/*.ts` com timeout implícito
- [ ] **AC2:** Criar helper `frontend/lib/fetch-with-retry.ts` com `AbortSignal.timeout(30000)` + retry exponencial (2 tentativas, 500ms/1500ms delay)
- [ ] **AC3:** Aplicar helper nos 3 principais call-sites: sitemap routes, SSR pages, `fetch` no blog
- [ ] **AC4:** Em sitemap XML (`frontend/app/sitemap.ts` + namespaced), catch de TimeoutError retorna sitemap parcial ou último cacheado (revalidate já existe em 1h)
- [ ] **AC5:** Sentry `captureException` anotado com `tag: "fetch_timeout"` + `contexts.fetch.url` para triagem — NÃO deixar ser unhandled rejection
- [ ] **AC6:** Issues Sentry listadas reduzem a <5 eventos/semana no agregado
- [ ] **AC7:** Teste unitário Jest: `frontend/__tests__/lib/fetch-with-retry.test.ts` cobrindo timeout + retry + eventual success

### Anti-requisitos

- NÃO aumentar timeout para 120s+ — bloqueia worker Next.js
- NÃO engolir TimeoutError silenciosamente — sempre log + Sentry tag

---

## Referência de implementação

- `frontend/app/sitemap.ts`
- `frontend/app/sitemaps/*.ts` (se existir, namespaced sitemaps)
- `frontend/lib/api.ts` ou similar — cliente backend

---

## Riscos

- **R1 (Médio):** Retry em fetch não-idempotente (POST) pode duplicar — só aplicar retry em GET
- **R2 (Baixo):** Sitemap parcial pode confundir GSC — preferir fallback a cached

## Dependências

- SEN-BE-007 (slow sitemap endpoints) — fix do backend reduz causa raiz

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — 8 issues clustered, ~113 eventos |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (lastSeen 2026-04-22). Promovida Draft → Ready |
