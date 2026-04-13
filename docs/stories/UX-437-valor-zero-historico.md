# UX-437: Valor R$ 0 no historico para buscas com resultados

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I6)
**Sprint:** Próximo

## Contexto

No histórico, buscas com 2 e 6 resultados mostram "R$ 0" como valor total. O dashboard agrega R$ 31,2 bilhões no total — os valores existem no banco. O problema é na agregação ou exibição do valor por sessão de busca.

Hipóteses em ordem de probabilidade:
1. **PCP v2** retorna `valor_estimado=0.0` por design (a API v2 não tem dados de valor) — se essas buscas usaram apenas PCP v2, o total zero é correto mas a exibição deve ser "Valor não disponível"
2. **Bug de agregação:** `save_session` não persiste `valor_total` dos resultados, ou persiste `0` por default
3. **Problema de tipagem:** `valor_estimado` é `float` nos resultados mas `valor_total` em `search_sessions` pode ser `Decimal` ou `None` que serializa como `0`

## Acceptance Criteria

- [ ] AC1: Diagnosticar causa: verificar `search_sessions.valor_total` no banco para as sessões com "R$ 0" — se campo é `NULL` ou `0.0`
- [ ] AC2: Se `valor_total = NULL`: corrigir `save_session()` para agregar `sum(r.valor_estimado for r in results where r.valor_estimado > 0)`
- [ ] AC3: Se `valor_total = 0` porque todos os resultados vieram de PCP v2 (`valor_estimado=0.0`): exibir "Valor não disponível" no histórico (não "R$ 0")
- [ ] AC4: Histórico e dashboard usam a mesma fonte de dados para `valor_total` — sem discrepância entre as duas telas
- [ ] AC5: Após fix, novas sessões de busca com resultados PNCP exibem valor correto no histórico

## Escopo

**IN:** `backend/routes/sessions.py` (aggregação de `valor_total` no `save_session`), `frontend/app/historico/page.tsx` (exibir "Valor não disponível" quando `valor_total = 0 ou null`), `backend/portal_compras_client.py` (confirmar que `valor_estimado=0.0` é comportamento esperado do PCP v2)
**OUT:** Mudanças no schema de `search_sessions` (adicionar coluna apenas se necessário e não existir), alterações no dashboard de analytics (deve continuar usando sua própria agregação)

## Complexidade

**S** (1 dia) — diagnóstico primeiro (AC1) determina qual fix aplicar (AC2 ou AC3); ambos são pontuais

## Dependências

Nenhuma dependência de outras stories.

## Riscos

- **Retroatividade:** Sessões já salvas com `valor_total = 0` não serão corrigidas retroativamente — aceitar como limitação; fix aplica apenas para novas sessões
- **PCP v2 como única fonte:** Se a busca de 2 resultados usou PNCP mas ainda assim mostra R$ 0, a hipótese 1 está errada e é bug de aggregação (AC2) — o diagnóstico AC1 é obrigatório antes de implementar

## Critério de Done

- Diagnosticar e documentar causa raiz (AC1) como primeiro commit
- Novas buscas com resultados PNCP exibem valor correto no histórico
- Buscas onde todos os resultados vieram de PCP v2 exibem "Valor não disponível" (não "R$ 0")
- `pytest tests/ -k session -v` passa sem regressões

## Arquivos Prováveis

- `backend/routes/sessions.py` — `save_session()` e endpoint `GET /sessions`
- `backend/search_cache.py` — verificar se `valor_total` é calculado ao persistir
- `backend/portal_compras_client.py` — confirmar `valor_estimado=0.0` no PCP v2
- `frontend/app/historico/page.tsx` — exibição condicional de valor
