# GTM-RESILIENCE-A05 — Indicadores de Cobertura e Estado Operacional

**Track:** A — "Nunca Resposta Vazia" (P0)
**Prioridade:** P0
**Sprint:** 1
**Estimativa:** 4-5 horas
**Gaps cobertos:** UX-04 (Alertas vermelhos genericos), UX-05 (Sem indicador de cobertura percentual)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

A investigacao estrategica (FRENTE 3 — UX-04 e UX-05) identificou que o frontend trata falhas parciais com semantica de ERRO quando deveria usar semantica de ESTADO OPERACIONAL. Isso degrada severamente a percepcao de valor do produto.

### O que acontece hoje

Quando o PNCP responde mas o PCP falha:
- `DegradationBanner` aparece com `variant="warning"` ou `variant="error"` (amarelo/vermelho)
- Mensagem: generica ("Algumas fontes nao responderam")
- O usuario interpreta como: "o sistema tem problemas" / "os resultados nao sao confiaveis"

### O que deveria acontecer

Quando 7 de 9 UFs foram processadas com sucesso:
- Indicador de cobertura: "**78% de cobertura** — 7 de 9 estados processados"
- Estado operacional: badge "Operacional" (verde), "Parcial" (amber), "Degradado" (vermelho)
- Freshness: "Ultima atualizacao ha 3 minutos" ou "Dados de 2h atras"
- Confiabilidade: indicador de qualidade dos dados ("Alta" / "Media" / "Baixa")

### Principio de design

> Vermelho = o usuario precisa tomar uma acao. Amber = informacao contextual. Verde = tudo normal.
>
> "7 de 9 UFs processadas" NAO requer acao do usuario → NAO deve ser vermelho.
> "Dados de 2h atras, atualizando..." NAO e um erro → NAO deve ter alerta.

---

## Problema

1. **Semantica de erro onde deveria ser de estado**: O `DegradationBanner` usa vermelho para situacoes que sao operacionais (cobertura parcial, cache serving). Vermelho dispara reacao emocional negativa e mina confianca no produto.

2. **Nenhum indicador quantitativo de cobertura**: O usuario nao sabe se "parcial" significa 90% ou 10% dos dados. Sem numero, qualquer parcialidade e percebida como falha total.

3. **Sem indicador de freshness em tempo real**: O `CacheBanner` mostra "dados de X minutos atras" mas APENAS quando cache e servido explicitamente. Em busca ao vivo com UFs faltando, nao ha indicacao temporal.

4. **Sem nivel de confiabilidade**: O usuario nao tem como avaliar se pode confiar nos resultados para tomar decisoes de negocio. Um score de confiabilidade baseado em cobertura + freshness + metodo resolveria isso.

---

## Solucao Proposta

### 1. Substituir DegradationBanner por OperationalStateBanner

Novo componente que usa semantica de estado (nao de erro):

| Estado | Cor | Icone | Exemplo |
|--------|-----|-------|---------|
| `operational` | Verde | Check | "100% de cobertura — todos os estados processados" |
| `partial` | Amber | Info | "78% de cobertura — 7 de 9 estados processados" |
| `degraded` | Amber escuro | Clock | "Dados de 2h atras — atualizando em background" |
| `unavailable` | Vermelho | Alert | "Fontes indisponiveis — tente novamente em 5 min" |

Vermelho SO aparece quando nenhum dado esta disponivel e o usuario precisa tomar acao.

### 2. Barra de cobertura percentual

Componente `CoverageBar` que mostra:
- Porcentagem numerica: "78%"
- Barra visual (progress bar) com segmentos por UF
- Tooltip por segmento: "SP: OK", "BA: Timeout"
- Subtexto: "7 de 9 estados processados"

### 3. Indicador de freshness

Badge de tempo real baseado em:
- `ultima_atualizacao` (campo ja presente no `BuscaResponse`)
- `cached_at` (quando cache)
- Formatacao relativa: "agora", "ha 3 min", "ha 2h"

### 4. Badge de confiabilidade

Score calculado no frontend baseado em:
- Cobertura (peso 50%): 100% = 1.0, 50% = 0.5, 0% = 0
- Freshness (peso 30%): < 5min = 1.0, < 1h = 0.7, < 6h = 0.4, > 6h = 0.1
- Metodo (peso 20%): Live = 1.0, Cache fresh = 0.8, Cache stale = 0.4

Labels: "Alta" (>0.8), "Media" (0.5-0.8), "Baixa" (<0.5)

---

## Acceptance Criteria

### AC1 — Backend fornece `coverage_pct` na resposta
O `BuscaResponse` DEVE incluir campo `coverage_pct: int` (0-100) calculado como `(succeeded_ufs / total_ufs_requested) * 100`.

### AC2 — Backend fornece `ufs_status_detail` na resposta
O `BuscaResponse` DEVE incluir campo `ufs_status_detail: list[UfStatusDetail]` com `{uf: str, status: "ok" | "timeout" | "error" | "skipped", results_count: int}` para cada UF solicitada.

### AC3 — Componente `OperationalStateBanner` substitui alertas vermelhos
Novo componente que renderiza estado operacional com semantica de cor correta:
- `operational` (verde): todas as fontes OK, dados ao vivo
- `partial` (amber): cobertura > 50% mas < 100%
- `degraded` (amber escuro): servindo cache ou cobertura < 50%
- `unavailable` (vermelho): nenhum dado disponivel

### AC4 — Vermelho SO para `unavailable`
O estado `unavailable` (vermelho) DEVE ser usado APENAS quando `response_state === "empty_failure"` (nenhum dado para mostrar). Cobertura parcial, cache serving, e falha de 1-2 UFs NAO devem usar vermelho.

### AC5 — Componente `CoverageBar` exibe porcentagem + barra visual
Novo componente que renderiza:
- Numero: "78% de cobertura"
- Barra de progresso segmentada (verde para OK, cinza para falha)
- Subtexto: "7 de 9 estados processados"

### AC6 — `CoverageBar` tooltip por UF
Cada segmento da barra DEVE ter tooltip/title com nome da UF e status: "SP: OK (45 resultados)", "BA: Timeout".

### AC7 — Indicador de freshness com formatacao relativa
Badge que mostra tempo desde ultima atualizacao com formatacao relativa em portugues: "agora", "ha 3 min", "ha 2h", "ha 1 dia".

### AC8 — Freshness atualiza em tempo real
O indicador de freshness DEVE atualizar a cada 60 segundos (via `setInterval`) sem re-render da pagina inteira.

### AC9 — Badge de confiabilidade calculado no frontend
Badge que mostra nivel de confiabilidade: "Alta" (verde), "Media" (amber), "Baixa" (vermelho) baseado na formula de cobertura + freshness + metodo descrita na solucao.

### AC10 — DegradationBanner existente mantido como deprecated
O componente `DegradationBanner` NAO deve ser deletado (preservar para retrocompatibilidade), mas o `SearchResults.tsx` DEVE usar `OperationalStateBanner` em seu lugar.

### AC11 — Resultado ao vivo 100% → estado "operational" (verde)
Quando busca ao vivo completa com 100% de cobertura, `OperationalStateBanner` DEVE renderizar em verde com "Cobertura completa".

### AC12 — Resultado parcial → estado "partial" (amber) + CoverageBar
Quando `coverage_pct < 100` e `coverage_pct >= 50`, DEVE renderizar em amber com `CoverageBar` mostrando porcentagem.

### AC13 — Cache servido → estado "degraded" (amber escuro) + freshness
Quando `response_state === "cached"`, DEVE renderizar em amber escuro com freshness indicator mostrando idade do cache.

### AC14 — Teste backend: `coverage_pct` calculado corretamente
Teste: 7 UFs succeeded de 9 solicitadas → `coverage_pct = 78`.

### AC15 — Teste backend: `ufs_status_detail` preenchido
Teste: busca com 3 UFs (2 OK, 1 timeout) → `ufs_status_detail` tem 3 entries com status corretos.

### AC16 — Teste frontend: OperationalStateBanner renderiza estado correto
Teste de componente:
- `coverage_pct=100`, `response_state="live"` → verde
- `coverage_pct=78`, `response_state="live"` → amber
- `response_state="cached"` → amber escuro
- `response_state="empty_failure"` → vermelho

### AC17 — Teste frontend: CoverageBar renderiza segmentos
Teste de componente: `ufs_status_detail` com 5 OK + 2 error → barra com 5 segmentos verdes e 2 cinzas, texto "71% de cobertura".

### AC18 — Teste frontend: confiabilidade calculada
Teste unitario: `coverage=100%, freshness<5min, method=live` → "Alta"; `coverage=50%, freshness>6h, method=stale_cache` → "Baixa".

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/schemas.py` | Adicionar `coverage_pct`, `ufs_status_detail`, tipo `UfStatusDetail` ao `BuscaResponse` |
| `backend/search_pipeline.py` | Calcular `coverage_pct` e `ufs_status_detail` na fase de response building |
| `frontend/app/buscar/components/OperationalStateBanner.tsx` | **NOVO** — substitui DegradationBanner |
| `frontend/app/buscar/components/CoverageBar.tsx` | **NOVO** — barra de cobertura percentual |
| `frontend/app/buscar/components/FreshnessIndicator.tsx` | **NOVO** — badge de freshness relativo |
| `frontend/app/buscar/components/ReliabilityBadge.tsx` | **NOVO** — badge de confiabilidade |
| `frontend/app/buscar/components/SearchResults.tsx` | Substituir `DegradationBanner` por novos componentes |
| `frontend/types/index.ts` (ou equivalente) | Adicionar `coverage_pct`, `ufs_status_detail`, `UfStatusDetail` |
| `frontend/utils/reliability.ts` | **NOVO** — funcao de calculo de confiabilidade |
| `backend/tests/test_search_pipeline.py` | AC14, AC15 |
| `frontend/__tests__/buscar/operational-state.test.tsx` | **NOVO** — AC16, AC17 |
| `frontend/__tests__/utils/reliability.test.ts` | **NOVO** — AC18 |

---

## Dependencias

| Story | Relacao |
|-------|---------|
| **A-01** (Timeout Cache Fallback) | A-01 define `response_state` que A-05 consome para determinar o estado visual. A-01 DEVE ser completada antes de A-05 no que tange `response_state`. |
| **A-02** (SSE Degraded) | A-02 fornece `coverage_pct` via SSE que A-05 pode usar para atualizar em tempo real. Complementar, nao bloqueante. |
| **C-02** (Indicador de confiabilidade detalhado) | C-02 aprofunda o badge de confiabilidade com dados per-resultado. A-05 implementa a versao macro (por busca). |

---

## Design System

### Paleta de cores para estados

| Estado | Background | Border | Text | Icon |
|--------|-----------|--------|------|------|
| `operational` | `bg-green-50 dark:bg-green-950` | `border-green-200 dark:border-green-800` | `text-green-700 dark:text-green-300` | CheckCircle |
| `partial` | `bg-amber-50 dark:bg-amber-950` | `border-amber-200 dark:border-amber-800` | `text-amber-700 dark:text-amber-300` | InfoCircle |
| `degraded` | `bg-orange-50 dark:bg-orange-950` | `border-orange-200 dark:border-orange-800` | `text-orange-700 dark:text-orange-300` | Clock |
| `unavailable` | `bg-red-50 dark:bg-red-950` | `border-red-200 dark:border-red-800` | `text-red-700 dark:text-red-300` | AlertTriangle |

### Responsividade

- Desktop: banner horizontal completo com barra + texto + badge
- Mobile (< 640px): banner compacto com porcentagem + badge; barra oculta; tooltip em press-and-hold

---

## Definition of Done

- [ ] Todos os 18 ACs verificados e passing
- [ ] Testes backend: 2 novos, zero regressoes
- [ ] Testes frontend: 3 novos, zero regressoes
- [ ] TypeScript check (`npx tsc --noEmit`) passing
- [ ] Nenhum alerta vermelho visivel quando cobertura > 0%
- [ ] Resultado ao vivo 100% → verde
- [ ] Resultado parcial (7/9 UFs) → amber com porcentagem
- [ ] Cache servido → amber escuro com freshness
- [ ] Nenhum dado → vermelho com orientacao
- [ ] Mobile responsivo (375px) verificado
- [ ] Dark mode verificado
- [ ] Code review aprovado
- [ ] Commit convencional: `feat(backend+frontend): GTM-RESILIENCE-A05 — operational state indicators + coverage bar + reliability badge`
