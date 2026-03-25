# UX-437: Valor R$ 0 no historico para buscas com resultados

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I6)
**Sprint:** Proximo

## Contexto

No historico, buscas com 2 e 6 resultados mostram "R$ 0" como valor total. No entanto, o dashboard agrega R$ 31,2 bi no total. Ou o historico nao agrega `valor_estimado` dos resultados, ou PCP v2 retorna `valor_estimado=0.0` e so essas fontes foram usadas nessas buscas.

## Acceptance Criteria

- [ ] AC1: Investigar se `valor_estimado` e persistido na sessao/historico
- [ ] AC2: Se valor e 0 por causa do PCP v2 (que nao tem dados de valor), nao exibir "R$ 0" — exibir "Valor nao disponivel"
- [ ] AC3: Se e bug de agregacao, corrigir soma de valor_estimado no endpoint de historico
- [ ] AC4: Dashboard e historico devem ser consistentes nos valores

## Arquivos Provaveis

- `backend/routes/sessions.py` — endpoint de historico com valor
- `backend/search_cache.py` — persistencia de valor_estimado
- `backend/portal_compras_client.py` — confirmar valor_estimado=0.0 no PCP v2
- `frontend/app/historico/page.tsx` — exibicao de valor
