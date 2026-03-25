# UX-429: Perfil de Licitante vazio — erro 500 em /api/profile-context

**Status:** Draft
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C4)
**Sprint:** Atual

## Contexto

Na pagina /conta/perfil, a secao "Perfil de Licitante" aparece vazia com apenas o botao "Editar". O console mostra `500 Internal Server Error` em `/api/profile-context`. O usuario nao recebe feedback de erro — simplesmente ve uma secao vazia.

## Acceptance Criteria

- [ ] AC1: Diagnosticar causa do 500 em `/api/profile-context` (rota backend, DB, schema?)
- [ ] AC2: Corrigir endpoint para retornar dados do perfil ou 404 adequado
- [ ] AC3: Frontend deve exibir erro amigavel se endpoint falhar (nao secao vazia)
- [ ] AC4: Se perfil nao preenchido, mostrar CTA para completar perfil
- [ ] AC5: Verificar se `/api/profile-completeness` (404 no dashboard) depende do mesmo endpoint

## Arquivos Provaveis

- `backend/routes/user.py` — endpoint profile-context
- `frontend/app/api/profile-context/route.ts` — proxy
- `frontend/app/conta/perfil/page.tsx` — renderizacao

## Screenshot

`ux-audit/11-minha-conta.png`
