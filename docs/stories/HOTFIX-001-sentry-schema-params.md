# HOTFIX-001 — Sentry: Fix schema mismatches e params errados

**Status:** Ready  
**Tipo:** Hotfix  
**Prioridade:** P0  
**Criada por:** @sm  
**Data:** 2026-04-13

---

## Contexto

Auditoria do Sentry (76 issues abertas) identificou:
- 2 erros de código ativos que quebram funcionalidades reais (P0)
- 5 issues já corrigidas no código mas ainda abertas no Sentry (só precisam de resolve)
- Demais: transient, externos, ou com fallback

---

## Acceptance Criteria

### AC1 — Fix `search_sessions.setor` → `search_sessions.sectors`
- [ ] Em `backend/routes/analytics.py`, função `get_trial_value`: trocar coluna `setor` por `sectors` no `.select()`
- [ ] Ajustar acesso ao valor retornado: `sectors` é `text[]`, pegar primeiro elemento (`sectors[0]` ou similar)
- [ ] `pytest tests/test_trial_endpoints.py -v` passa sem falhas

### AC2 — Fix params `/observatorio/[mes]-[ano]/page.tsx`
- [ ] Trocar tipo de `params` de `{ 'mes-ano': string }` para `{ mes: string; ano: string }`
- [ ] Reconstruir slug onde necessário: `const slug = \`\${mes}-\${ano}\``
- [ ] Page `/observatorio/2026-03` renderiza sem InvariantError

### AC3 — Resolve issues já corrigidas no Sentry
- [ ] BACKEND-47 (`objeto_resumo`) → Resolve
- [ ] BACKEND-59 (`data_publicacao_pncp`) → Resolve  
- [ ] BACKEND-43 (`is_master` trigger) → Resolve
- [ ] BACKEND-4E (TypeError coroutine) → Resolve
- [ ] BACKEND-15 + BACKEND-14 (Application startup failed) → Resolve

### AC4 — Não regressão
- [ ] `pytest tests/test_trial_endpoints.py tests/test_analytics.py -v` passa
- [ ] `npm test` no frontend passa (sem novas falhas)

---

## Implementação

### Arquivos a modificar
- `backend/routes/analytics.py` (linhas ~357-358, ~405)
- `frontend/app/observatorio/[mes]-[ano]/page.tsx`

### Fora de escopo (Grupo 3 — investigação posterior)
- FRONTEND-A: slug conflict `setor` vs `cnpj`
- BACKEND-5F/4Z: statement timeouts em queries públicas
- BACKEND-5J: sitemap slow

---

## Escopo

**IN:** `backend/routes/analytics.py` (AC1 — coluna `setor` → `sectors`), `frontend/app/observatorio/[mes]-[ano]/page.tsx` (AC2 — tipo de params), Sentry (AC3 — resolve 5 issues)  
**OUT:** Refatoração do módulo de analytics, mudanças no schema de `search_sessions`, resolução de issues do Grupo 3 (FRONTEND-A, BACKEND-5F/4Z/5J)

## Complexidade

**XS** (< 4h) — duas correções pontuais de 1–2 linhas cada + resolve manual de 5 issues no Sentry

## Riscos

- **`sectors` é `text[]`:** Acessar `sectors[0]` pode retornar `None` se array vazio — garantir que o código é defensivo e não quebra `get_trial_value` para usuários sem setor
- **Sentry resolve (AC3):** Se alguma issue resolver incorretamente (bug ainda ativo mas resolve marcada), o Sentry silencia alertas futuros — verificar cada issue antes de resolver

## Critério de Done

- `GET /v1/analytics/trial-value` retorna sem erro para todos os usuários
- `/observatorio/2026-03` renderiza sem InvariantError no console
- 5 issues do Sentry com status Resolved
- `pytest tests/test_trial_endpoints.py tests/test_analytics.py -v` passa

---

## File List

- [ ] `backend/routes/analytics.py`
- [ ] `frontend/app/observatorio/[mes]-[ano]/page.tsx`
