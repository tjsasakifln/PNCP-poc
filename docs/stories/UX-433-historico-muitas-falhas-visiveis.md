# UX-433: Historico mostra excesso de falhas e timeouts

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I2)
**Sprint:** Proximo

## Contexto

Das ~20 entradas visiveis no historico, ~8 sao "Falhou" ou "Tempo esgotado". Buscas consecutivas da mesma query aparecem como entradas separadas. Primeira impressao para trial e de produto instavel.

## Acceptance Criteria

- [ ] AC1: Agrupar retries consecutivos da mesma busca em uma unica entrada (mostrar "3 tentativas")
- [ ] AC2: Adicionar filtro "Esconder falhas" ou "Apenas concluidas" no topo
- [ ] AC3: Limitar exibicao de falhas antigas (>7 dias) automaticamente
- [ ] AC4: Considerar nao salvar no historico buscas que falharam em <5s (erros instantaneos)

## Arquivos Provaveis

- `frontend/app/historico/page.tsx` — renderizacao da lista
- `backend/routes/sessions.py` — endpoint de historico
- `backend/search_cache.py` — persistencia de sessoes

## Screenshot

`ux-audit/10-historico.png`
