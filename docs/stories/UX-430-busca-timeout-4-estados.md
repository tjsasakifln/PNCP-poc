# UX-430: Busca com 4+ estados causa timeout frequente

**Status:** Done
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C1)
**Sprint:** Proximo

## Contexto

Busca por "Engenharia, Projetos e Obras" com SP/PR/RS/SC causou timeout na primeira tentativa (~30s). Segunda tentativa levou ~60s mas funcionou. Mensagem de erro "Tente com menos estados" culpa o usuario.

O fluxo async (CRIT-072) deveria evitar isso — POST retorna 202 e resultados vem via SSE. O timeout sugere que o frontend esta esperando demais ou o SSE esta falhando.

## Acceptance Criteria

- [x] AC1: Busca com 4 UFs deve completar sem timeout (ou retornar resultados parciais)
- [x] AC2: Se timeout, mostrar resultados parciais das UFs que completaram
- [x] AC3: Mensagem de erro nao deve culpar usuario — "Algumas fontes demoraram. Mostrando resultados parciais."
- [x] AC4: Botao "Tentar novamente" deve sugerir ou auto-reduzir UFs
- [x] AC5: Investigar timeout chain: frontend timeout vs SSE timeout vs pipeline timeout
- [x] AC6: Verificar se cache SWR pode servir resultados stale durante retry

## Arquivos Provaveis

- `frontend/app/buscar/page.tsx` — client timeout, SSE handling
- `backend/search_pipeline.py` — pipeline timeout (110s)
- `backend/routes/search.py` — SSE event generator
- `backend/progress.py` — progress tracker

## Escopo

**IN:** `frontend/app/buscar/page.tsx` (client timeout, SSE handling), `backend/routes/search.py` (SSE event generator), `backend/progress.py` (timeout de tracker)  
**OUT:** Aumento de capacidade de infra (mais UFs paralelas), mudanças nos timeouts do `search_pipeline.py` (já ajustado em GTM-FIX-029), modificações no circuito breaker de fontes individuais

## Complexidade

**M** (2–3 dias) — investigação da cadeia de timeout (3 camadas: frontend/SSE/pipeline) + resultados parciais + mensagens adequadas

## Riscos

- **Resultados parciais vs cache:** Servir resultados parciais pode interagir com SWR cache — garantir que resultados incompletos não sejam cacheados como completos
- **SSE inactivity timeout (120s):** Se a busca de 4 UFs dura >120s sem eventos SSE, o gateway encerra a conexão — pode ser a causa raiz real do "timeout" observado
- **Depends on CRIT-082:** A simplificação de retry (CRIT-082) pode resolver parte do problema (83s de retry amplification); verificar antes de implementar AC4

## Critério de Done

- Busca "Engenharia, Projetos e Obras" com SP/PR/RS/SC completa ou retorna resultados parciais sem mensagem de timeout genérica
- Mensagem de erro não contém "Tente com menos estados"
- Se timeout ocorre: usuário vê quantas UFs completaram e opção de tentar novamente
- Nenhum teste existente quebrado

## Screenshot

`ux-audit/05-busca-timeout.png`
