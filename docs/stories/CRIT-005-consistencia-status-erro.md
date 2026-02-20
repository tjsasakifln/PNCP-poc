# CRIT-005: Garantir Consistencia de Status e Erro

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 3: Contrato

## Prioridade
P0

## Estimativa
16h

## Descricao

O sistema pratica "Success Theater" — retorna HTTP 200 em 14 locais onde o processamento real falhou. Isso impede monitoramento, engana o frontend, e faz o usuario pensar que "nao ha resultados" quando na verdade as fontes de dados estao indisponiveis.

### O problema em numeros:
- **14 locais** onde excecoes sao capturadas e HTTP 200 retornado com dados degradados
- **3 locais** que produzem HTTP error codes genuinos (429, 502, 504)
- **5 route files** que SEMPRE retornam 200 independente de falhas internas
- `degradation_guidance` existe no backend mas **NAO e exibido** no frontend
- LLM fallback e **invisivel** ao usuario (nao ha badge distinguindo AI vs automatico)
- Excel botao renderiza como funcional quando `excel_status="failed"` — click resulta em 404

## Especialistas Consultados
- API Contract Architect (Error Handling Specialist)
- UX Architect (Failure Experience Specialist)

## Evidencia da Investigacao

### Mapa de "Success Theater" (cenarios onde HTTP 200 mascara falha):

| Cenario | HTTP | response_state | Usuario ve | Realidade |
|---------|------|---------------|------------|-----------|
| Todas fontes down + SEM cache | 200 | "empty_failure" | Lista vazia sem erro | Sistema quebrado |
| LLM falha | 200 | - | Resumo identico visualmente | IA nao funcionou |
| Excel falha (ARQ) | 200 | - | Botao download funcional | Click da 404 |
| Trial status falha | 200 | - | plan=free_trial, expired=true | Pago parece expirado |
| Stripe down | 200 | - | status="pending" | Assinante ativo parece pendente |
| Analytics trial-value falha | 200 | - | R$0 de valor | Tela de conversao sem incentivo |

### Arquivos com swallowed errors:
- `search_pipeline.py` L983-1175: 5 catch blocks servem cache ou vazio como 200
- `routes/analytics.py` L329-338: trial-value retorna zeros em vez de 500
- `routes/user.py` L169-178: trial-status retorna defaults em vez de erro
- `routes/billing.py` L209-210: subscription status retorna "pending" em vez de erro
- `routes/onboarding.py` L96-101: first-analysis sempre 200 (background task)

### UX Issues criticos:
- `frontend/lib/error-messages.ts`: 502 mapeia para "PNCP indisponivel" mas pode ser qualquer falha
- `SearchResults.tsx` L697-738: botao download renderiza sem checar `excel_status`
- `useSearch.ts` L237-239: `setResult(null)` no inicio apaga resultado anterior
- Transicao progresso->erro: apos 6+ min de progresso visivel, tudo apagado instantaneamente

## Criterios de Aceite

### Observabilidade de Response State
- [ ] AC1: Adicionar header `X-Response-State` em toda resposta `/buscar` espelhando `response_state`
- [ ] AC2: Adicionar header `X-Cache-Level` espelhando `cache_level` (fresh/stale/none)
- [ ] AC3: Criar Prometheus counter `search_response_state_total{state="live|cached|degraded|empty_failure"}`
- [ ] AC4: Criar Prometheus counter `search_error_type_total{type="sources_down|timeout|filter_error|llm_error|db_error"}`

### Frontend — Diferenciar "Sem Resultados" de "Fontes Indisponiveis"
- [ ] AC5: Quando `response_state="empty_failure"`, exibir componente `SourcesUnavailable` com `degradation_guidance` do backend (NAO lista vazia)
- [ ] AC6: Quando `response_state="empty_failure"` E `degradation_guidance` esta presente, exibir o texto do guidance
- [ ] AC7: Quando resultados sao REALMENTE zero (response_state="live", licitacoes=[]), exibir `EmptyState` com "Nenhuma licitacao encontrada" + sugestoes de filtro
- [ ] AC8: Nunca mostrar lista vazia sem contexto — sempre ter componente informativo

### Excel Status
- [ ] AC9: Quando `excel_status="failed"`, desabilitar botao de download e mostrar "Excel indisponivel — tente nova busca"
- [ ] AC10: Quando `excel_status="processing"`, mostrar spinner no botao com "Gerando Excel..."
- [ ] AC11: Se `excel_status` fica "processing" por mais de 90s sem SSE update, mostrar "Excel indisponivel"
- [ ] AC12: Adicionar polling para `excel_status` via endpoint de status (CRIT-003 AC11) quando SSE indisponivel

### LLM Summary Provenance
- [ ] AC13: Adicionar campo `llm_source` no response: `"ai"` | `"fallback"` | `"processing"`
- [ ] AC14: Backend `gerar_resumo_fallback()` deve setar `llm_source="fallback"` no response
- [ ] AC15: Backend `gerar_resumo()` (real) deve setar `llm_source="ai"` no response
- [ ] AC16: Frontend exibir badge discreto: "Resumo por IA" (azul) vs "Resumo automatico" (cinza)
- [ ] AC17: Quando `llm_status="processing"`, mostrar "Resumo por IA sendo preparado..." com eventual replacement

### Error Message Accuracy
- [ ] AC18: Corrigir mapeamento 502 em `error-messages.ts`: mensagem neutra "O servidor esta temporariamente indisponivel" (nao culpar PNCP especificamente)
- [ ] AC19: Adicionar mapeamentos para `response_state` no frontend (nao so HTTP status codes)
- [ ] AC20: Mensagens de erro devem incluir `search_id` para referencia de suporte (collapsible "Detalhes tecnicos")

### Progress-to-Error Transition
- [ ] AC21: Quando timeout ocorre mas UFs ja retornaram dados (`succeeded_ufs` nao vazio), mostrar resultados parciais com banner "Busca incompleta" em vez de erro
- [ ] AC22: Na transicao progresso->erro por timeout, preservar barra de progresso por 3s com overlay "Busca expirou" antes de mostrar erro
- [ ] AC23: Nunca chamar `setResult(null)` quando `forceFresh=false` e resultado anterior existe — manter resultado anterior como fallback visual

### Swallowed Error Audit
- [ ] AC24: `routes/user.py` `get_trial_status()`: retornar HTTP 503 quando Supabase falha (nao 200 com defaults enganosos)
- [ ] AC25: `routes/billing.py` `get_subscription_status()`: retornar HTTP 503 quando Stripe falha (nao 200 com "pending")
- [ ] AC26: `routes/analytics.py` `get_trial_value()`: retornar HTTP 503 quando Supabase falha (nao 200 com zeros)
- [ ] AC27: Para cada endpoint acima, frontend deve tratar 503 gracefully com mensagem "Informacao temporariamente indisponivel"

### buscar-progress Endpoint
- [ ] AC28: Quando `search_id` nao existe, retornar HTTP 404 (nao SSE 200 com "Search not found" embutido)
- [ ] AC29: Quando tracker existe mas busca ja falhou, retornar SSE event `error` com `error_message` estruturado

## Testes Obrigatorios

- [ ] `response_state="empty_failure"` mostra SourcesUnavailable (nao lista vazia)
- [ ] `excel_status="failed"` desabilita botao download
- [ ] `llm_source="fallback"` mostra badge "Resumo automatico"
- [ ] 502 error message nao menciona PNCP especificamente
- [ ] Timeout com UFs parciais mostra resultados parciais (nao erro)
- [ ] trial-status retorna 503 em vez de 200 com defaults quando DB falha
- [ ] subscription-status retorna 503 quando Stripe falha
- [ ] buscar-progress retorna 404 para search_id inexistente
- [ ] Header X-Response-State presente em toda resposta /buscar
- [ ] Prometheus counter incrementado por response_state

## Definicao de Pronto

1. Usuario NUNCA ve lista vazia quando fontes estao indisponiveis — sempre ve explicacao
2. Botao de Excel NUNCA renderiza como funcional quando Excel falhou
3. Resumo sempre mostra proveniencia (IA vs automatico)
4. Monitoramento pode alertar sobre degradacao via Prometheus/headers (sem parsear body)
5. Timeout com dados parciais mostra dados (nao erro)
6. Endpoints de user/billing/analytics retornam 503 em vez de 200 com dados falsos
7. Zero regressao nos testes existentes

## Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|----------|
| Mudar trial-status para 503 pode quebrar frontend existente | Feature flag, frontend trata 503 gracefully |
| Badge LLM pode confundir usuario | Tooltip explicativo, design discreto |
| Preservar resultado anterior pode mostrar dados stale | Badge "Resultados anteriores" quando mostrando fallback |

## Arquivos Envolvidos

### Backend (modificar):
- `backend/routes/search.py` — headers X-Response-State, X-Cache-Level
- `backend/search_pipeline.py` — llm_source field
- `backend/routes/user.py` L169-178 — trial-status error handling
- `backend/routes/billing.py` L209-210 — subscription-status error handling
- `backend/routes/analytics.py` L329-338 — trial-value error handling
- `backend/llm.py` — llm_source="ai" on success
- `backend/schemas.py` — llm_source field in BuscaResponse

### Frontend (modificar):
- `frontend/lib/error-messages.ts` — fix 502 mapping, add response_state mappings
- `frontend/app/buscar/components/SearchResults.tsx` L697-738 — Excel button state
- `frontend/app/buscar/hooks/useSearch.ts` L237-239 — preserve previous result
- `frontend/app/buscar/page.tsx` — response_state routing
- `frontend/components/EnhancedLoadingProgress.tsx` — timeout transition overlay

### Frontend (criar):
- `frontend/app/buscar/components/LlmSourceBadge.tsx` — AI vs fallback badge

## Dependencias

- **Bloqueada por:** CRIT-002 (precisa de status persistido para erro correto)
- **Paralela com:** CRIT-006
- **Bloqueia:** CRIT-007 (testes E2E precisam do contrato de erro correto)
