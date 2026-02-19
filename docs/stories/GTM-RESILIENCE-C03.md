# GTM-RESILIENCE-C03 -- Cobertura Percentual Visivel no Frontend

| Campo | Valor |
|-------|-------|
| **Track** | C: Valorizacao de Percepcao |
| **Prioridade** | P1 |
| **Sprint** | 2 |
| **Estimativa** | 6-10 horas (backend enrichment + frontend UI) |
| **Gaps Cobertos** | UX-05 |
| **Dependencias** | GTM-RESILIENCE-C01 (copy baseline), A-02 (SSE "degraded" event -- soft) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

A investigacao (Frente 3, Gap UX-05) revelou que o usuario nao tem como avaliar a **completude** dos resultados de uma busca. Quando o sistema processa 7 de 9 UFs solicitadas (2 falharam por timeout), o usuario ve o resultado final sem saber que 22% da cobertura foi perdida. Da mesma forma, nao ha indicador de **freshness** -- os resultados podem ser de cache de 4 horas atras, mas o usuario so descobre isso se o CacheBanner aparecer (o que so acontece em cenarios de falha total).

Isso e critico para a proposta de valor "inteligencia de decisao": o usuario precisa saber a extensao e a atualidade da informacao para tomar decisoes confiaveis.

### Estado Atual

**O que ja existe:**
- `failed_ufs` no BuscaResult -- lista de UFs que falharam (STORY-257B AC10)
- `cached_at` / `cache_status` / `cached_sources` -- metadata de cache (UX-303/GTM-FIX-010)
- `CacheBanner` componente -- mostra freshness quando servindo cache
- `is_partial` flag -- indica busca incompleta (STORY-252)
- `data_sources` array -- status por fonte (STORY-252)
- `PartialResultsPrompt` -- UF progress grid durante loading
- `ultima_atualizacao` -- ISO timestamp da busca (existe no BuscaResult, raramente usado no UI)
- SSE `on_uf_complete` callback -- progresso per-UF durante busca

**O que falta:**
- Nenhum indicador de cobertura percentual apos a busca completar
- Nenhum "X de Y UFs processadas" no header de resultados
- Nenhum "ultima atualizacao ha Z min" persistente nos resultados (CacheBanner so aparece para cache)
- Nenhum indicador de freshness para resultados live (verde = dados de agora)
- UFs que falharam nao sao listadas por nome -- so o count existe

## Problema

1. **Sem indicador de cobertura** -- usuario nao sabe se buscou 100% ou 70% das UFs
2. **Sem timestamp visivel** -- usuario nao sabe se dados sao de agora ou de horas atras
3. **Sem freshness para live results** -- CacheBanner so aparece em cenario de cache, resultados live nao comunicam "dados de agora"
4. **UFs falhadas invisíveis** -- `failed_ufs` existe no payload mas nao e exibido ao usuario
5. **Tomada de decisao comprometida** -- "Nao encontrei licitacoes no Parana" pode ser "Nao buscamos o Parana porque deu timeout"

## Solucao

### Backend: Enriquecer BuscaResponse com coverage metadata

Adicionar campos ao BuscaResponse:

```python
class CoverageMetadata(BaseModel):
    """Metadata sobre cobertura da busca."""
    ufs_requested: list[str]          # UFs solicitadas pelo usuario
    ufs_processed: list[str]          # UFs que retornaram dados com sucesso
    ufs_failed: list[str]             # UFs que falharam (ja existe como failed_ufs)
    coverage_pct: float               # Porcentagem de cobertura (processed/requested * 100)
    data_timestamp: str               # ISO timestamp de quando os dados foram obtidos
    freshness: Literal["live", "cached_fresh", "cached_stale"]  # Indicador de freshness
```

O pipeline ja rastreia UFs processadas e falhadas internamente. O objetivo e consolidar essa informacao num objeto estruturado.

### Frontend: Barra de cobertura + timestamp no header de resultados

#### 1. Coverage Bar (barra de cobertura)
- Barra horizontal mostrando `coverage_pct` visualmente
- Texto: "Cobertura: 7 de 9 UFs (78%)"
- Cor: verde (100%), amarelo (70-99%), vermelho (<70%)
- Hover/click: expande lista de UFs processadas vs falhadas

#### 2. Freshness Indicator (indicador de freshness)
- Badge no header de resultados:
  - **Live** (verde pulsante): "Dados de agora" -- busca acabou de rodar, resultados diretos das fontes
  - **Cache recente** (verde estatico): "Dados de ha X minutos" -- cache fresh (0-6h)
  - **Cache desatualizado** (amarelo): "Dados de ha X horas" -- cache stale (6-24h)
- Substituicao contextual: quando CacheBanner ja esta visivel, freshness indicator no header nao duplica a informacao

#### 3. UF Breakdown on Hover
- Ao hover na barra de cobertura, tooltip mostra:
  ```
  Processadas: SP, RJ, MG, PR, SC, RS, BA
  Falharam: PE, CE (timeout)
  ```
- Em mobile: tappable para expandir

---

## Criterios de Aceitacao

### Backend

### AC1: CoverageMetadata no schema
- [x] Novo modelo `CoverageMetadata` com campos: `ufs_requested`, `ufs_processed`, `ufs_failed`, `coverage_pct`, `data_timestamp`, `freshness`
- [x] `freshness` e `Literal["live", "cached_fresh", "cached_stale"]`
- [x] `coverage_pct` calculado como `len(ufs_processed) / len(ufs_requested) * 100`, arredondado para 1 decimal
- [x] Campo e `Optional` no BuscaResponse para backward compatibility

### AC2: Pipeline popula CoverageMetadata
- [x] `search_pipeline.py` popula `coverage_metadata` no final do pipeline
- [x] `ufs_processed` derivado das UFs que retornaram pelo menos 1 resultado
- [x] `ufs_failed` reusa logica existente de `failed_ufs`
- [x] `data_timestamp` = `datetime.utcnow().isoformat()` para live, ou `cached_at` para cache
- [x] `freshness` = "live" para resultado direto, "cached_fresh" se cache 0-6h, "cached_stale" se cache 6-24h

### AC3: Testes backend
- [x] Teste: 9 UFs solicitadas, 9 processadas -> coverage_pct = 100.0, freshness = "live"
- [x] Teste: 9 UFs solicitadas, 7 processadas, 2 falharam -> coverage_pct = 77.8, ufs_failed = ["PE", "CE"]
- [x] Teste: resultado de cache fresh -> freshness = "cached_fresh"
- [x] Teste: resultado de cache stale -> freshness = "cached_stale"
- [x] Teste: 1 UF solicitada, 1 processada -> coverage_pct = 100.0
- [x] Teste: 27 UFs solicitadas, 0 processadas (total failure) -> coverage_pct = 0.0
- [x] Todos os testes passam sem regressao vs baseline (~45 pre-existentes)

### Frontend

### AC4: Tipo CoverageMetadata no frontend
- [x] `frontend/app/types.ts` inclui interface `CoverageMetadata` com campos correspondentes
- [x] `BuscaResult` inclui `coverage_metadata?: CoverageMetadata | null`
- [x] `npx tsc --noEmit --pretty` passa limpo

### AC5: Coverage bar no header de resultados
- [x] Barra de cobertura visivel abaixo do header de resultados
- [x] Texto mostra "Cobertura: X de Y UFs (Z%)"
- [x] Cor da barra: verde para 100%, amarelo/amber para 70-99%, vermelho para <70%
- [x] Barra e proporcional ao percentual (ex: 78% preenche 78% da largura)
- [x] Quando `coverage_metadata` e null (backend antigo), barra nao aparece (graceful degradation)

### AC6: UF breakdown on hover
- [x] Hover (desktop) ou tap (mobile) na barra de cobertura expande painel com:
  - Lista de UFs processadas (com checkmark verde)
  - Lista de UFs falhadas (com X vermelho + motivo se disponivel)
- [x] Painel fecha ao clicar fora ou pressionar Escape
- [x] Em mobile (< 768px), tap abre painel abaixo da barra (nao tooltip flutuante)

### AC7: Freshness indicator no header
- [x] Badge de freshness visivel no header de resultados, alinhado a direita
- [x] **Live**: badge verde com dot pulsante + "Dados de agora"
- [x] **Cache recente**: badge verde estatico + "Dados de ha X minutos/horas" (formatacao relativa em pt-BR)
- [x] **Cache desatualizado**: badge amarelo + "Dados de ha X horas" (formatacao relativa)
- [x] Quando CacheBanner ja esta visivel (cenario de fallback), freshness badge mostra "Cache" em vez de duplicar

### AC8: Consistencia com CacheBanner existente
- [x] Freshness indicator e CacheBanner nao apresentam informacoes conflitantes
- [x] Quando cache stale servido: CacheBanner aparece (com botao refresh) + freshness badge no header mostra "Cache"
- [x] Quando resultado live: CacheBanner nao aparece + freshness badge mostra "Dados de agora"
- [x] `formatRelativeTimePtBr()` exportada de FreshnessIndicator.tsx (reutilizavel, nao duplicada)

### AC9: Acessibilidade
- [x] Coverage bar tem `role="progressbar"` com `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- [x] `aria-label` descritivo: "Cobertura da busca: 7 de 9 estados processados, 78 por cento"
- [x] Freshness badge tem `aria-label`: "Dados obtidos ha 30 minutos"
- [x] UF breakdown acessivel via teclado (Enter para abrir, Escape para fechar)
- [x] Cores nao sao unico diferenciador (texto + icones complementam)

### AC10: Responsividade
- [x] Mobile (375px): coverage bar empilhada verticalmente, freshness badge abaixo do titulo
- [x] Tablet (768px): coverage bar e freshness badge lado a lado
- [x] Desktop (1280px): layout completo com hover tooltips
- [x] Dark mode funcional em todos os breakpoints

### AC11: Testes frontend
- [x] Teste: coverage bar renderizada com 100% (verde)
- [x] Teste: coverage bar renderizada com 78% (amarelo)
- [x] Teste: coverage bar renderizada com 50% (vermelho)
- [x] Teste: coverage bar nao renderizada quando coverage_metadata = null
- [x] Teste: UF breakdown mostra UFs processadas e falhadas
- [x] Teste: freshness badge "Dados de agora" para live
- [x] Teste: freshness badge com tempo relativo para cached
- [x] Teste: CacheBanner + freshness badge nao conflitam
- [x] Teste: aria-label correto na progressbar
- [x] Nenhum novo teste failure vs baseline (33 frontend pre-existentes)

### AC12: Integracao com SSE (se A-02 estiver completo)
- [x] Se SSE event "degraded" existir (Track A, Story A-02), coverage bar atualiza em real-time conforme UFs completam
- [x] Se SSE "degraded" nao existir, coverage bar aparece apenas no resultado final
- [x] Nenhuma dependencia hard de A-02 -- funciona sem SSE degraded

---

## Arquivos Afetados

### Backend

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/schemas.py` ou modelo equivalente | Novo modelo CoverageMetadata + campo em BuscaResponse |
| `backend/search_pipeline.py` | Populacao de coverage_metadata no final do pipeline |
| `backend/search_cache.py` | Populacao de freshness baseado em cache status |
| `backend/tests/test_pipeline_coverage.py` | Novo: 6+ testes de coverage metadata |

### Frontend

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/types.ts` | Interface CoverageMetadata + campo em BuscaResult |
| `frontend/app/buscar/components/SearchResults.tsx` | Coverage bar, freshness badge, UF breakdown |
| `frontend/app/buscar/components/CoverageBart.tsx` | Novo componente: barra de cobertura |
| `frontend/app/buscar/components/FreshnessIndicator.tsx` | Novo componente: badge de freshness |
| `frontend/app/buscar/components/CacheBanner.tsx` | Reutilizar `formatRelativeTime`, ajustar interacao com freshness |
| `frontend/__tests__/buscar/coverage-bar.test.tsx` | Novo: testes do componente CoverageBar |
| `frontend/__tests__/buscar/freshness-indicator.test.tsx` | Novo: testes do FreshnessIndicator |

---

## Dependencias

| Dependencia | Tipo | Motivo |
|-------------|------|--------|
| **GTM-RESILIENCE-C01** | Soft | Copy de cobertura deve seguir tom estabelecido (sem contagem de fontes, mas "cobertura %" e comunicada) |
| **Track A, Story A-02** | Soft | SSE "degraded" event permitiria coverage bar atualizar em real-time. Sem A-02, coverage bar so aparece no resultado final -- funciona, mas menos dinamico |
| **STORY-257B** (ja completo) | Hard | `failed_ufs`, `cached_at`, `is_partial` ja existem -- esta story adiciona `coverage_metadata` como camada consolidada |
| **UX-303** (ja completo) | Hard | `cache_status` (fresh/stale) ja existe -- esta story expoe visualmente de forma mais proeminente |

---

## Decisoes de Design

### Por que CoverageMetadata como objeto separado (nao campos soltos)?

Os campos `failed_ufs`, `is_partial`, `cached_at`, `cache_status` ja existem individualmente no BuscaResult. Um objeto `coverage_metadata` consolidado:
1. Evita que o frontend faca calculo de cobertura (logica fica no backend)
2. Facilita extensao futura (adicionar `sources_coverage` por fonte, nao so por UF)
3. Nao breaking change -- campos existentes continuam funcionando, `coverage_metadata` e aditivo

### Por que freshness no header alem do CacheBanner?

CacheBanner so aparece em cenarios de cache fallback. Para resultados live, o usuario nao tem feedback de freshness. O freshness indicator no header cobre todos os cenarios:
- Live: "Dados de agora" (feedback positivo, reforça valor)
- Cache fresh: "Dados de ha 15 min" (tranquiliza)
- Cache stale: "Dados de ha 3 horas" (alerta sutil, CacheBanner complementa com botao de refresh)

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Mitigacao |
|-------|---------------|-----------|
| Coverage bar + freshness badge + CacheBanner = UI congestionada | Media | Design review: CacheBanner e freshness badge devem ser mutuamente contextuais, nao duplicar |
| Backend nao rastreia UFs processadas explicitamente | Baixa | Pipeline ja tem logica de `on_uf_complete` callback; derivar `ufs_processed` de la |
| Calculo de coverage_pct incorreto quando UF retorna 0 resultados (processada mas vazia) | Media | Definir: UF "processada" = recebeu resposta HTTP 2xx, independente de 0 resultados. Distinguir de "falhada" = timeout/erro |

---

## Definition of Done

- [x] `coverage_metadata` presente na resposta da API `/buscar` com todos os campos
- [x] Coverage bar visivel no header de resultados com porcentagem e cor semantica
- [x] UF breakdown acessivel via hover/tap
- [x] Freshness indicator visivel em todos os cenarios (live, cache fresh, cache stale)
- [x] Nenhum conflito visual entre freshness indicator e CacheBanner
- [x] `npm run build` e `pytest` passam sem novos failures
- [x] `npx tsc --noEmit --pretty` limpo
- [x] Dark mode funcional
- [x] Acessibilidade: progressbar com ARIA, teclado navegavel
- [x] Backward compatible: frontend funciona normalmente quando `coverage_metadata = null`
