# UX-431: Dashboard mostra dados desatualizados da ultima busca

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (C5)
**Sprint:** Próximo

## Contexto

Dashboard mostra "6 oportunidades na sua última busca" mas a busca mais recente retornou 394 resultados. O card parece referenciar uma busca anterior (de 6 resultados feita às 09:57, não a de 394 feita às ~10:00).

A causa provável é que o endpoint de `summary` consulta `search_sessions` ordenado por `created_at`, mas buscas muito recentes podem não ter sido persistidas ainda (race condition entre pipeline concluir e o save no banco) — ou a query filtra por `status = 'Concluída'` enquanto a busca de 394 ficou com status diferente.

## Acceptance Criteria

- [ ] AC1: Card "última busca" exibe dados da sessão com `status = 'Concluída'` mais recente, ordenada por `created_at DESC LIMIT 1`
- [ ] AC2: Se a sessão mais recente tem `status != 'Concluída'` (timeout, falha), exibir a última bem-sucedida com label "Última busca concluída"
- [ ] AC3: Investigar e corrigir se a busca de 394 resultados não está sendo persistida no banco — verificar se `save_session()` é chamado ao final do pipeline, inclusive para buscas grandes
- [ ] AC4: Após fix, confirmar que o card exibe `total_results` correto sem cache stale no frontend (revalidar ao montar o dashboard)

## Escopo

**IN:** `backend/routes/analytics.py` (query de última busca no `GET /summary`), `backend/routes/sessions.py` (verificar se `save_session` persiste corretamente), `frontend/app/dashboard/page.tsx` (revalidação do card)
**OUT:** Redesign do card de dashboard, mudanças no schema de `search_sessions`, alterações no pipeline de busca

## Complexidade

**S** (1 dia) — diagnóstico de query + possível fix no `save_session` + revalidação no frontend

## Dependências

Nenhuma dependência de outras stories.

## Riscos

- **Race condition:** Se o pipeline demora > X segundos para salvar no banco, o dashboard pode estar consultando antes do save — verificar se `save_session` é `await`ed ou fire-and-forget
- **Buscas grandes:** Se `save_session` tem limite de payload e 394 resultados excede, pode estar silenciosamente descartando o save

## Critério de Done

- Dashboard exibe "394 oportunidades na sua última busca" para o usuário do audit após fix
- Card revalida ao abrir o dashboard (sem cache stale por mais de 60s)
- `pytest tests/test_analytics.py -v` passa sem regressões

## Arquivos Prováveis

- `frontend/app/dashboard/page.tsx` — fetch e revalidação do card
- `backend/routes/analytics.py` — query do endpoint `GET /summary`
- `backend/routes/sessions.py` — `save_session()` e persistência
- `backend/search_cache.py` — verificar se cache interfere no dado exibido

## Screenshot

`ux-audit/08-dashboard.png`
