# UX-433: Historico mostra excesso de falhas e timeouts

**Status:** InReview
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I2)
**Sprint:** Próximo

## Contexto

Das ~20 entradas visíveis no histórico, ~8 são "Falhou" ou "Tempo esgotado". Buscas consecutivas da mesma query aparecem como entradas separadas. Para um usuário em trial, a primeira impressão é de produto instável.

Nota: após CRIT-082 (eliminar retry amplification), o volume de entradas de falha deve diminuir organicamente — esta story trata da **exibição** do histórico, não da causa das falhas.

## Acceptance Criteria

- [x] AC1: Buscas com mesmo `setor + UFs` executadas com menos de 5 minutos de intervalo são agrupadas em uma única entrada no histórico com label "N tentativas"
- [x] AC2: Filtro "Apenas concluídas" no topo do histórico — oculta entradas com `status != 'Concluída'` quando ativado; desativado por padrão
- [x] AC3: Entradas com `status = 'Falhou'` ou `status = 'Tempo esgotado'` com `created_at < now() - 7 days` são automaticamente ocultadas da listagem padrão (mas ainda acessíveis via filtro "Mostrar todas")
- [x] AC4: Buscas que falharam em menos de 3 segundos (erro instantâneo, não timeout) não são salvas no histórico — verificar se o backend já tem essa lógica e adicionar se não tiver

## Escopo

**IN:** `frontend/app/historico/page.tsx` (agrupamento, filtros, ocultação automática), `backend/routes/sessions.py` (AC4 — filtrar saves de falhas instantâneas)
**OUT:** Mudanças no schema de `search_sessions`, alterações no pipeline de busca, resolução das causas de falha (CRIT-080, UX-430)

## Complexidade

**M** (2–3 dias) — agrupamento por setor+UFs+janela de tempo requer lógica de deduplicação no frontend ou backend; AC4 requer ajuste no save do pipeline

## Dependências

- **CRIT-082** (recomendado antes): reduz o volume de falhas na origem, tornando esta story mais efetiva
- **UX-430** (independente): timeout fix pode reduzir entradas de "Tempo esgotado"

## Riscos

- **Agrupamento (AC1):** Se buscas agrupadas têm resultados diferentes (ex: 6 vs 394), qual exibir? Exibir o da tentativa bem-sucedida se existir, senão o mais recente
- **AC4 — falhas instantâneas:** Definir "< 3 segundos" requer que o backend rastreie `duration_ms` no save — verificar se campo já existe em `search_sessions`

## Critério de Done

- Histórico com 8 entradas de falha: agrupadas em no máximo 2–3 entradas com "N tentativas"
- Filtro "Apenas concluídas" oculta entradas com falha
- Entradas de falha com mais de 7 dias não aparecem por padrão
- `npm test` passa sem regressões

## Arquivos Modificados

- `frontend/app/historico/page.tsx` — groupSessions(), filtros AC1/AC2/AC3, badge "N tentativas"
- `frontend/hooks/useSessions.ts` — param hideOldFailures para AC3
- `backend/routes/sessions.py` — param hide_old_failures + filtro de 7 dias (AC3)
- `backend/quota/session_tracker.py` — _delete_session_if_exists + AC4 (instant failure)
- `frontend/__tests__/ux-433-historico-melhorias.test.tsx` — 17 testes AC1/AC2/AC3
- `backend/tests/test_ux433_historico_melhorias.py` — 11 testes AC3/AC4
- `backend/tests/test_routes_sessions.py` — or_() adicionado ao mock helper

## Screenshot

`ux-audit/10-historico.png`
