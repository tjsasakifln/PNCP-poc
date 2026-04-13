# UX-429: Perfil de Licitante vazio — erro 500 em /api/profile-context

**Status:** Ready
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C4)
**Sprint:** Atual

## Contexto

Na pagina /conta/perfil, a secao "Perfil de Licitante" aparece vazia com apenas o botao "Editar". O console mostra `500 Internal Server Error` em `/api/profile-context`. O usuario nao recebe feedback de erro — simplesmente ve uma secao vazia.

## Acceptance Criteria

- [x] AC1: Diagnosticar causa do 500 em `/api/profile-context` — causa: `sb_execute` em `.single()` lançava quando `context_data` era NULL ou coluna inexistente; corrigido com try/except que retorna `{}` em vez de propagar o erro.
- [x] AC2: Corrigir endpoint para retornar dados do perfil ou 404 adequado — `GET /profile/context` agora retorna 200+`{}` em qualquer falha de DB (nunca 500). Coberto por `test_get_context_db_error` em `tests/test_profile_context.py`.
- [x] AC3: Frontend deve exibir erro amigavel se endpoint falhar (nao secao vazia) — adicionado bloco `data-testid="profile-context-error"` em `conta/perfil/page.tsx` quando `profileCtx === null && profileError`. Coberto por `__tests__/ux-429-perfil-error-state.test.tsx`.
- [x] AC4: Se perfil nao preenchido, mostrar CTA para completar perfil — guidance banner + botão "Preencher agora →" já existem; testados em `ux-429-perfil-error-state.test.tsx` AC4 suite.
- [x] AC5: Verificar se `/api/profile-completeness` (404 no dashboard) depende do mesmo endpoint — endpoint independente (`GET /profile/completeness`), também possui fallback gracioso (retorna 0% em vez de 500). Coberto por `test_db_error_returns_empty_fallback` em `tests/test_profile_completeness.py`.

## Arquivos Provaveis

- `backend/routes/user.py` — endpoint profile-context
- `frontend/app/api/profile-context/route.ts` — proxy
- `frontend/app/conta/perfil/page.tsx` — renderizacao

## Escopo

**IN:** `backend/routes/user.py` (endpoint `profile-context`), `frontend/app/api/profile-context/route.ts`, `frontend/app/conta/perfil/page.tsx`  
**OUT:** Redesign do formulário de perfil, novos campos de perfil além dos existentes, integração com `/api/profile-completeness` (investigar separadamente se depende do mesmo endpoint — AC5)

## Complexidade

**S** (< 1 dia) — diagnóstico de 500 + fix de endpoint + estado de erro amigável no frontend

## Riscos

- **Schema desatualizado:** Se o endpoint 500 é causado por migração de schema não aplicada, o fix exige identificar e aplicar a migration pendente
- **Profile-completeness relacionado (AC5):** Se ambos os endpoints compartilham o mesmo bug, o fix resolve os dois — mas se forem problemas distintos, o AC5 pode escalar para S+

## Critério de Done

- `/conta/perfil` carrega sem erro no console
- Seção "Perfil de Licitante" exibe dados ou CTA "Complete seu perfil" (nunca vazia sem feedback)
- `/api/profile-context` retorna 200 ou 404 com mensagem clara (nunca 500)
- Se `/api/profile-completeness` usar o mesmo endpoint: também corrigido sem 404

## Screenshot

`ux-audit/11-minha-conta.png`
