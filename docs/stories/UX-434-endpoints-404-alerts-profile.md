# UX-434: Endpoints 404 em todas as paginas autenticadas

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I3)
**Sprint:** Atual

## Contexto

Duas rotas retornam 404 em toda navegacao autenticada:
- `/api/alerts` — 404 em Dashboard, Pipeline, Historico, Conta
- `/api/profile-completeness` — 404 no Dashboard

Endpoints nao implementados no backend gerando requests desnecessarios e erros no console.

## Acceptance Criteria

- [ ] AC1: Implementar `/api/alerts` (retornar `[]` se nao ha alertas) OU remover chamada do frontend
- [ ] AC2: Implementar `/api/profile-completeness` OU remover chamada do frontend
- [ ] AC3: Zero erros 404 no console durante navegacao normal
- [ ] AC4: Se endpoints sao planejados para futuro, retornar 200 com body vazio (nao 404)

## Arquivos Provaveis

- `frontend/` — componente que chama /api/alerts (provavelmente no layout ou header)
- `frontend/app/api/alerts/route.ts` — proxy (ausente?)
- `frontend/app/api/profile-completeness/route.ts` — proxy (ausente?)
