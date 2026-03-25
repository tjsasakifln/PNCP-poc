# UX-430: Busca com 4+ estados causa timeout frequente

**Status:** Draft
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C1)
**Sprint:** Proximo

## Contexto

Busca por "Engenharia, Projetos e Obras" com SP/PR/RS/SC causou timeout na primeira tentativa (~30s). Segunda tentativa levou ~60s mas funcionou. Mensagem de erro "Tente com menos estados" culpa o usuario.

O fluxo async (CRIT-072) deveria evitar isso — POST retorna 202 e resultados vem via SSE. O timeout sugere que o frontend esta esperando demais ou o SSE esta falhando.

## Acceptance Criteria

- [ ] AC1: Busca com 4 UFs deve completar sem timeout (ou retornar resultados parciais)
- [ ] AC2: Se timeout, mostrar resultados parciais das UFs que completaram
- [ ] AC3: Mensagem de erro nao deve culpar usuario — "Algumas fontes demoraram. Mostrando resultados parciais."
- [ ] AC4: Botao "Tentar novamente" deve sugerir ou auto-reduzir UFs
- [ ] AC5: Investigar timeout chain: frontend timeout vs SSE timeout vs pipeline timeout
- [ ] AC6: Verificar se cache SWR pode servir resultados stale durante retry

## Arquivos Provaveis

- `frontend/app/buscar/page.tsx` — client timeout, SSE handling
- `backend/search_pipeline.py` — pipeline timeout (110s)
- `backend/routes/search.py` — SSE event generator
- `backend/progress.py` — progress tracker

## Screenshot

`ux-audit/05-busca-timeout.png`
