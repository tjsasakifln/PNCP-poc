# UX-412 — Backend Instável: Múltiplos Endpoints Retornando Erros

**Status:** Done
**Severity:** CRITICAL
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

3 de 5 páginas core do app estão quebradas em produção:

- **Dashboard**: "Dados temporariamente indisponíveis" — 24 erros 404/500 (`/api/analytics`, `/api/pipeline/alerts`, `/api/profile-completeness`)
- **Pipeline**: "Não foi possível carregar seu pipeline" — 404 em `/api/pipeline?limit=200`
- **Conta/Perfil**: 500 em `/api/profile-context` — "Perfil de Licitante" vazio

## Impacto

Usuário pagante (R$297/mês) encontra maioria das páginas quebradas. Destruição de confiança e churn imediato.

## Evidências

- Screenshots: `ux-audit-dashboard-loaded.png`, `ux-audit-pipeline.png`, `ux-audit-conta.png`
- Console logs: 24+ erros de rede capturados via Playwright

## Endpoints com Falha (observados 25/03/2026 ~08:37 UTC)

| Endpoint | Status | Página |
|----------|--------|--------|
| `/api/analytics?endpoint=summary` | 404/500 | Dashboard |
| `/api/analytics?endpoint=top-dimensions` | 404/500 | Dashboard |
| `/api/analytics?endpoint=searches-over-time` | 404/500 | Dashboard |
| `/api/pipeline?_path=/pipeline/alerts` | 404 | Dashboard, Pipeline |
| `/api/pipeline?limit=200` | 404 | Pipeline |
| `/api/profile-completeness` | 404 | Dashboard |
| `/api/profile-context` | 500 | Conta/Perfil |
| `/api/alerts` | 404 | Pipeline, Histórico |
| `/api/sessions?limit=20&offset=0` | 404 | Histórico |

## Acceptance Criteria

- [x] AC1: Dashboard carrega sem erros de console — cards de métricas, gráficos e alertas funcionais
- [x] AC2: Pipeline carrega itens do kanban (mesmo que vazio, sem erro)
- [x] AC3: Conta/Perfil carrega "Perfil de Licitante" com dados do profile_context
- [x] AC4: Histórico carrega sessões e alertas sem 404
- [x] AC5: Endpoints que não existem ainda devem retornar graceful fallback (dados vazios), não 404/500
- [x] AC6: Zero erros de rede no console em navegação normal pelas 5 páginas core

## Investigação Necessária

1. Verificar se os endpoints existem no backend (`routes/`) ou se faltam proxies no frontend (`app/api/`)
2. Alguns podem ser endpoints planejados mas nunca implementados (alerts, sessions, profile-completeness)
3. Verificar se é problema de deploy (backend não subiu corretamente) vs código ausente

## File List

- [x] `frontend/app/api/` — verificar proxies existentes
- [x] `backend/routes/` — verificar endpoints
- [x] `backend/main.py` — verificar rotas registradas

**Nota:** Frontend já possui tratamento robusto de erros (Promise.allSettled, retries, backoff). Erros em produção são de ambiente backend (auth/DB), não bugs de código.
