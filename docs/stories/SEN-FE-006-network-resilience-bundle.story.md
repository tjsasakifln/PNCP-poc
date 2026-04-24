# SEN-FE-006: AbortError Lock broken + UnhandledRejection Object Not Found (Supabase/Office extension)

**Status:** Ready
**Origem:** Sentry unresolved — 2 issues live: 7434019021 (AbortError Lock broken 4evt), 7434019069 (UnhandledRejection Object Not Found 5evt)
**Prioridade:** P3 — Baixo (9 eventos total, 2 fingerprints vivos)
**Complexidade:** S (Small) — scope reduzido pós-validação @po
**Owner:** @dev
**Tipo:** Resilience / Observability

---

## Problema

Duas issues live (lastSeen 2026-04-22) com causas raiz distintas mas solução compartilhada via `sentry.client.config.ts::beforeSend` + investigação pontual:

| Issue | Mensagem | Eventos | Causa provável |
|-------|----------|---------|----------------|
| 7434019021 | `AbortError: Lock broken by another request with the 'steal' option.` | 4 | Web Locks API (IndexedDB/auth locks) — Supabase SDK faz `navigator.locks.request({ steal: true })` em auth refresh concorrente |
| 7434019069 | `UnhandledRejection: Non-Error promise rejection captured with value: Object Not Found Matching Id` | 5 | Pattern confirmado de extensão Microsoft/OneDrive Office injetada no browser — NÃO é código nosso |

Escopo original (bundle com 7 issues) foi **reduzido pelo @po** — 4 fingerprints stale (Connection closed, RSC text/plain, TypeError terminated, AbortError signal) movidos para **SEN-HOUSEKEEP-001** (Sentry resolve).

---

## Critérios de Aceite

- [ ] **AC1:** Em `frontend/sentry.client.config.ts::beforeSend`, adicionar filtro:
  - Ignorar `UnhandledRejection` com value contendo `"Object Not Found Matching Id"` + tag `source: "office_extension"` (não é nosso bug, não poluir dashboard)
- [ ] **AC2:** Para AbortError Lock broken: auditar usos de `supabase.auth.getSession()` e `onAuthStateChange` em `frontend/app/**/*.ts[x]` — identificar se concorrência pode ser debounced
- [ ] **AC3:** Se AbortError persistir >5 eventos/semana após auditoria, adicionar retry graceful em `frontend/lib/supabase-client.ts`: catch AbortError do Lock → retry único após 100ms
- [ ] **AC4:** Documentar em `frontend/sentry.client.config.ts` com comentário: qual erro filtra + por quê (audit trail, evita confusão futura)
- [ ] **AC5:** Issues `7434019021` e `7434019069` reduzem para <2 eventos/semana após fix (filter + retry)
- [ ] **AC6:** Métrica nova (Mixpanel ou Sentry tag): `smartlic_frontend_ignored_errors_total{reason}` — monitorar volume filtrado (detecta se filtro está escondendo bug novo)

### Anti-requisitos

- NÃO filtrar AbortError genericamente — pode mascarar fetch abort legítimo do backend lento
- NÃO fazer retry infinito em auth — Supabase já tem retry interno

---

## Referência de implementação

- `frontend/sentry.client.config.ts` — `beforeSend` hook
- `frontend/lib/supabase-client.ts` — investigar Lock API usage (ou wrapper similar)

---

## Riscos

- **R1 (Médio):** Filtro amplo pode esconder bug novo de mesmo formato — mitigar com métrica de ignored + review mensal
- **R2 (Baixo):** Retry em auth session pode duplicar request — usar debounce 100ms

## Dependências

- SEN-HOUSEKEEP-001 — fingerprints stale do escopo original tratados lá

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — 7 issues network-lifecycle, 55+ eventos combinados |
| 2026-04-23 | @po | Validação 7/10 → **NEEDS REVISION**. Scope trimmed: 5 fingerprints stale movidos para SEN-HOUSEKEEP-001. Mantidas 2 issues live (7434019021, 7434019069). Promovida Draft → Ready |
