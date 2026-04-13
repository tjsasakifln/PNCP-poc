# UX-434: Endpoints 404 em todas as paginas autenticadas

**Status:** Done
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I3)
**Sprint:** Atual

## Contexto

Duas rotas retornam 404 em toda navegacao autenticada:
- `/api/alerts` — 404 em Dashboard, Pipeline, Historico, Conta
- `/api/profile-completeness` — 404 no Dashboard

Endpoints nao implementados no backend gerando requests desnecessarios e erros no console.

## Acceptance Criteria

- [x] AC1: Implementar `/api/alerts` (retornar `[]` se nao ha alertas) OU remover chamada do frontend
- [x] AC2: Implementar `/api/profile-completeness` OU remover chamada do frontend
- [x] AC3: Zero erros 404 no console durante navegacao normal
- [x] AC4: Se endpoints sao planejados para futuro, retornar 200 com body vazio (nao 404)

## Arquivos Provaveis

- `frontend/` — componente que chama /api/alerts (provavelmente no layout ou header)
- `frontend/app/api/alerts/route.ts` — proxy (ausente?)
- `frontend/app/api/profile-completeness/route.ts` — proxy (ausente?)

## Escopo

**IN:** `frontend/app/api/alerts/route.ts` (criar stub 200), `frontend/app/api/profile-completeness/route.ts` (criar stub 200), componente frontend que dispara as chamadas (identificar e remover ou conectar)  
**OUT:** Implementação real de alertas (pipeline separado), implementação real de completude de perfil (UX-429 já cobre o lado do perfil)

## Complexidade

**XS** (< 4h) — criar stubs de rota retornando `[]` / `{ complete: false }` para eliminar 404s

## Riscos

- **Stub vs remoção:** Stubs podem mascarar que a feature nunca foi implementada — documentar claramente que são placeholders até implementação real

## Critério de Done

- Console do browser sem erros 404 em `/api/alerts` e `/api/profile-completeness` durante navegação autenticada normal
- Dashboard, Pipeline, Histórico e Conta carregam sem erros no console
