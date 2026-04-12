# STORY-370 — Funil de Ativação Instrumentado

**Status:** InReview
**Priority:** P1 — Dados (sem momento "aha" mapeado hoje, otimização de onboarding é chute)
**Origem:** Conselho de CEOs Advisory Board — melhorias on-page funil conversão (2026-04-11)
**Componentes:** frontend/app/onboarding/, frontend/app/buscar/, frontend/app/pipeline/, frontend/lib/mixpanel.ts
**Depende de:** nenhuma
**Bloqueia:** nenhuma
**Estimativa:** ~4h

---

## Contexto

O SmartLic tem Mixpanel integrado no frontend, mas **não rastreia os momentos-chave do trial** que predizem conversão. Sem esses eventos, é impossível saber:

- Quantos trials completam o onboarding de 3 etapas?
- Qual etapa do onboarding tem maior abandono?
- O "momento aha" acontece na primeira busca, no primeiro resultado relevante, ou quando o usuário adiciona ao pipeline?
- Qual ação tem maior correlação com conversão para pagante?

Com esses dados, cada melhoria de produto pode ser direcionada ao gargalo real — não ao que parece importante.

**Hipótese:** O momento "aha" provavelmente é `first_relevant_result_found` (não simplesmente executar uma busca). Usuários que chegam a esse evento convertem a taxas 3-5x maiores. Essa hipótese precisa ser validada com dados.

## Acceptance Criteria

### AC1: Wrapper Mixpanel tipado

- [x] Verificar se existe `frontend/lib/mixpanel.ts` ou equivalente; se existir, estender; se não, criar
- [x] Exportar função `trackEvent(event: AnalyticsEvent, properties?: Record<string, unknown>): void`
- [x] Tipo `AnalyticsEvent` (union type) inclui:
  - `'onboarding_step_completed'`
  - `'first_search_executed'`
  - `'first_relevant_result_found'`
  - `'pipeline_item_added'`
- [x] Wrapper é no-op quando Mixpanel não está inicializado (graceful degradation)
- [x] Não usar `mixpanel.track` diretamente nos componentes — sempre via wrapper

### AC2: Evento `onboarding_step_completed`

- [x] Disparado em `frontend/app/onboarding/` ao completar cada etapa
- [x] Properties: `{ step: 1 | 2 | 3, total_steps: 3, cnae?: string, ufs_count?: number }`
- [x] Step 1 = CNAE + objetivo selecionado
- [x] Step 2 = UFs + faixa de valor configurada
- [x] Step 3 = confirmação + primeiro acesso ao produto
- [x] Disparado apenas 1x por etapa (não re-disparar se usuário voltar)

### AC3: Evento `first_search_executed`

- [x] Disparado na **primeira** busca executada pelo usuário (não em buscas subsequentes)
- [x] Properties: `{ setor: string, ufs: string[], resultado_count: number, days_in_trial: number }`
- [x] Controle de "primeira vez" via localStorage (chave: `first_search_tracked`) — não depende de API
- [x] Disparado em `frontend/app/buscar/hooks/useSearchOrchestration.ts` após receber resultados

### AC4: Evento `first_relevant_result_found`

- [x] Disparado quando o usuário vê pelo menos 1 resultado com classificação relevante na primeira busca
- [x] "Relevante" = resultado que não foi filtrado pela IA (presente na lista de resultados exibida)
- [x] Properties: `{ setor: string, top_value: number, result_count: number, days_in_trial: number }`
- [x] Disparado apenas 1x (primeira ocorrência) via localStorage (chave: `first_relevant_result_tracked`)
- [x] Disparado junto com ou logo após `first_search_executed` se resultados > 0

### AC5: Evento `pipeline_item_added`

- [x] Disparado quando usuário adiciona primeiro item ao pipeline kanban
- [x] Properties: `{ days_in_trial: number, is_first_item: boolean }`
- [x] `is_first_item: true` apenas no primeiro item; eventos subsequentes também rastreados com `is_first_item: false`
- [x] Disparado no hook `usePipeline.ts` ao confirmar adição (sucesso no POST /pipeline)
- [x] Não disparar em items adicionados via seed/admin

### AC6: Propriedade global de dias no trial

- [x] Todos os eventos incluem `days_in_trial: number` calculado a partir de `trial_started_at` (disponível via `GET /me`)
- [x] Criar helper `getDaysInTrial(trialStartedAt: string): number` em `frontend/lib/analytics-helpers.ts`
- [x] Fallback: `-1` se `trial_started_at` não disponível

### AC7: Testes

- [x] Testes unitários para o wrapper `trackEvent` (mock do Mixpanel)
- [x] Testes para cada evento: verifica que é disparado nas condições corretas e não re-disparado
- [x] Testes para helper `getDaysInTrial`
- [x] Testes não fazem chamadas reais ao Mixpanel (mock via `jest.mock`)

## Escopo

**IN:**
- 4 eventos Mixpanel nos momentos-chave
- Wrapper tipado
- Helper de dias no trial
- Controle de "primeira vez" via localStorage

**OUT:**
- Dashboard Mixpanel (configuração da plataforma Mixpanel — fora do código)
- Eventos de comportamento granular (scroll, hover, cliques em geral)
- Backend analytics (eventos são apenas frontend nesta story)
- Retroativo: eventos para trials anteriores (só para novos trials)

## Riscos

- localStorage pode ser limpo pelo usuário → evento re-disparado; aceitável (melhor falso positivo que perder evento real)
- Mixpanel bloqueado por adblockers → mitigado pelo graceful degradation no wrapper

## Arquivos a Criar/Modificar

- [x] `frontend/hooks/useAnalytics.ts` (modificar — AnalyticsEvent type + trackEvent tipado)
- [x] `frontend/lib/analytics-helpers.ts` (novo)
- [x] `frontend/app/onboarding/page.tsx` (modificar — onboarding_step_completed)
- [x] `frontend/app/buscar/hooks/useSearchOrchestration.ts` (modificar — first_search + first_relevant)
- [x] `frontend/hooks/usePipeline.ts` (modificar — pipeline_item_added)
- [x] `frontend/__tests__/analytics-events.test.tsx` (novo)
- [x] `frontend/__tests__/analytics-helpers.test.ts` (novo)

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-11 | @sm | Story criada — Conselho de CEOs Advisory Board |
| 2026-04-11 | @po | GO 10/10 — Draft → Ready |
