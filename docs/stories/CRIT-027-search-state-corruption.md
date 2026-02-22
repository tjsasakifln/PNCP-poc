# CRIT-027 — Estado da Busca Corrompido: Empty State Prematuro + Resultados Stale

**Status:** pending
**Priority:** P0 — Blocker (impede uso do produto)
**Created:** 2026-02-22
**Origin:** Auditoria UX area logada (2026-02-22-ux-audit-area-logada.md)
**Dependencias:** CRIT-012 (SSE heartbeat)
**Estimativa:** M

---

## Problema

A busca na area logada esta fundamentalmente quebrada. Tres sintomas co-ocorrem:

1. **Empty state prematuro**: Ao clicar "Buscar", o sistema mostra instantaneamente "Nenhuma Oportunidade Relevante Encontrada" com "302 resultados eliminados" — ANTES de a busca terminar. O grid de UFs aparece por ~1 segundo e some.

2. **Resultados stale contaminam nova busca**: Ao trocar de setor (Vestuario -> Engenharia), o numero "302 eliminados" da busca anterior persiste na tela da nova busca. Dados incorretos exibidos ao usuario.

3. **"Atualizando dados em tempo real..." infinito**: Banner amarelo com spinner permanece por 2+ minutos sem nunca resolver, mesmo quando a busca ja completou no backend.

### Evidencia de Producao

- Busca Vestuario: 0 resultados + "302 eliminados" exibido em <1s, busca continuando ao fundo
- Troca para Engenharia: mesma tela "302 eliminados para engenharia" (numero stale de vestuario)
- Apos 150s: tela identica, nenhuma mudanca
- Grid de UFs (AC/AL/AM...) visivel por ~1s, depois substituido pelo empty state

### Impacto

- Usuario novo acredita que o produto nao funciona
- Usuario acredita que nao ha oportunidades quando na verdade ha (historico mostra 153 para Engenharia)
- Churn imediato no primeiro uso

---

## Solucao

Corrigir a maquina de estado da busca no frontend (`useSearch.ts` + `page.tsx`).

### Criterios de Aceitacao

**Estado da busca**
- [ ] **AC1:** Estado `result` e limpo (null) ao iniciar nova busca — nenhum resultado anterior visivel
- [ ] **AC2:** Empty state "Nenhuma Oportunidade" so aparece APOS busca concluir (status `completed` ou `error`)
- [ ] **AC3:** Enquanto busca esta em andamento, mostrar loading state adequado (nao empty state)

**Grid de UFs (progresso)**
- [ ] **AC4:** Grid de UFs persiste durante TODA a busca, nao some apos 1s
- [ ] **AC5:** Contador "Encontradas: X oportunidades ate agora" atualiza em tempo real via SSE
- [ ] **AC6:** UFs transitam de "Aguardando" -> "Consultando" -> "Sucesso/Falhou" progressivamente

**Banner de status**
- [ ] **AC7:** "Atualizando dados em tempo real..." desaparece quando busca conclui
- [ ] **AC8:** Se busca falha ou timeout (>180s), mostrar mensagem clara com botao "Tentar novamente"
- [ ] **AC9:** Se busca retorna 0 resultados APOS conclusao, empty state mostra "Analisamos X editais de Y estados e nenhum correspondeu ao seu perfil" (framing informativo, nao negativo)

**Testes**
- [ ] **AC10:** Teste: nova busca limpa resultados anteriores
- [ ] **AC11:** Teste: empty state nao aparece durante loading
- [ ] **AC12:** Teste: grid de UFs permanece visivel ate conclusao
- [ ] **AC13:** Zero regressoes (baseline: ~50 fail FE)

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---------|---------|
| `frontend/hooks/useSearch.ts` | Limpar `result` no inicio da busca; nao setar resultado ate `completed` |
| `frontend/app/buscar/page.tsx` | Condicional de empty state: so quando `!loading && !result` |
| `frontend/app/buscar/components/SearchResults.tsx` | Nao renderizar com resultado stale |
| `frontend/app/buscar/components/UfProgressGrid.tsx` | Persistir durante toda busca |
| `frontend/__tests__/search-state-*.test.tsx` | **NOVO**: testes AC10-AC13 |

---

## Analise Tecnica

O problema raiz e que `useSearch.ts` provavelmente:
1. Nao limpa `result` ao iniciar nova busca (leak de estado anterior)
2. O empty state em `page.tsx` renderiza baseado em `result?.licitacoes?.length === 0` sem checar se `loading === true`
3. O SSE stream pode estar falhando silenciosamente (heartbeat nao mantendo conexao), fazendo o frontend renderizar resultado parcial/vazio como final

Verificar se o `search_id` da nova busca esta sendo propagado corretamente ao SSE, e se o SSE do search anterior esta sendo devidamente encerrado.

---

## Referencias

- Audit: `docs/sessions/2026-02/2026-02-22-ux-audit-area-logada.md` (B01, B02, B04, H01)
- CRIT-012: SSE heartbeat (pode ser causa raiz se heartbeat falha)
- Screenshots: audit-02 a audit-08
