# CRIT-028 — Dashboard Vazio: Skeletons Eternos + Erros de Console

**Status:** pending
**Priority:** P0 — Blocker (pagina core inacessivel)
**Created:** 2026-02-22
**Origin:** Auditoria UX area logada (2026-02-22-ux-audit-area-logada.md)
**Dependencias:** Nenhuma
**Estimativa:** S

---

## Problema

A pagina `/dashboard` mostra apenas placeholders de skeleton loading que NUNCA resolvem para conteudo real. O console mostra 5 erros identicos: "Error fetching plan info: TypeError: Failed..." em loop.

### Evidencia

- Screenshot audit-05: dashboard completamente vazio apos carregamento completo
- Console: 5x "Error fetching plan info" em todas as paginas (nao so dashboard)
- SSE warning: "SSE connection failed (attempt 0)" ao carregar dashboard

### Impacto

- Dashboard e a 2a pagina mais importante apos Busca
- Usuario logado vê pagina vazia — impressao de produto incompleto
- Erros de console indicam problema sistemico no fetch de dados do plano

---

## Solucao

Diagnosticar e corrigir o fetch de plan info. Garantir que dashboard mostra empty state educativo se nao ha dados.

### Criterios de Aceitacao

**Diagnostico**
- [ ] **AC1:** Identificar causa raiz de "Error fetching plan info" (endpoint retornando erro? CORS? Token?)
- [ ] **AC2:** Corrigir o erro para que plan info carregue corretamente

**Dashboard funcional**
- [ ] **AC3:** Dashboard carrega e exibe dados do usuario (ou empty state se nao ha dados)
- [ ] **AC4:** Empty state educativo: "Faca sua primeira busca para ver seus dados aqui" com CTA para /buscar
- [ ] **AC5:** Skeleton loading tem timeout de 10s — se nao carregar, mostra empty state (nao skeleton eterno)

**Console limpo**
- [ ] **AC6:** Zero erros de console relacionados a plan info em navegacao normal
- [ ] **AC7:** SSE warning tratado gracefully (nao visivel ao usuario)

**Testes**
- [ ] **AC8:** Teste: dashboard com dados mostra cards corretamente
- [ ] **AC9:** Teste: dashboard sem dados mostra empty state com CTA
- [ ] **AC10:** Zero regressoes

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/dashboard/page.tsx` | Timeout de skeleton + empty state educativo |
| `frontend/hooks/useFetchWithBackoff.ts` | Verificar se plan info usa backoff corretamente |
| `frontend/app/api/` | Verificar proxy de plan info |
| `backend/routes/` | Verificar endpoint de plan info |

---

## Referencias

- Audit: B03, M06
- CRIT-018: Dashboard retry storm (pode estar relacionado)
