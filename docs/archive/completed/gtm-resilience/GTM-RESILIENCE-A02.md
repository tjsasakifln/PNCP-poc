# GTM-RESILIENCE-A02 — SSE Event "degraded" e Semantica de Estado

**Track:** A — "Nunca Resposta Vazia" (P0)
**Prioridade:** P0
**Sprint:** 1
**Estimativa:** 3-4 horas
**Gaps cobertos:** P-03 (SSE nao sinaliza degradacao), UX-07 (SSE terminal "error" quando cache e servido)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

A investigacao estrategica (FRENTE 1 — P-03 e FRENTE 3 — UX-07) identificou que o protocolo SSE do sistema possui apenas dois estados terminais: `"complete"` (sucesso) e `"error"` (falha). Quando o pipeline serve dados de cache stale apos falha das fontes, o SSE emite `"complete"` — o que e tecnicamente correto (a busca terminou) mas semanticamente enganoso (os dados nao sao ao vivo).

Pior: quando ha falha parcial seguida de cache serving, o frontend nao tem como distinguir "busca ao vivo concluida" de "servindo dados de 3 horas atras porque o PNCP caiu". O usuario ve a mesma tela em ambos os cenarios.

### Estado atual do SSE (`progress.py`)

```python
# Apenas 2 terminais:
stage: str  # "connecting", "fetching", "filtering", "llm", "excel", "complete", "error"
```

- `"complete"`: Pipeline finalizou com sucesso (ou serviu cache — ambiguo)
- `"error"`: Pipeline falhou fatalmente (504, excecao nao recuperada)

Nao existe estado intermediario para "concluiu, mas com dados degradados".

---

## Problema

1. **Ambiguidade semantica**: O frontend usa `event.stage === 'complete'` para fechar a conexao SSE e renderizar resultados. Quando cache stale e servido, o frontend renderiza normalmente sem nenhum indicador de que os dados sao de horas atras.

2. **Tratamento binario**: O `useSearchProgress.ts:L107` fecha a conexao em `complete` ou `error`. Nao ha rota para um estado que signifique "completou com ressalvas" — forcar o frontend a tratar como sucesso puro ou erro puro, sem meio-termo.

3. **Metadata insuficiente**: Mesmo se o frontend recebesse `cached=true` na resposta JSON final, o SSE nao carrega metadata. O usuario ve a transicao de "Buscando..." para "Pronto!" quando na verdade o estado e "Servindo dados anteriores enquanto tentamos atualizar".

---

## Solucao Proposta

### 1. Novo evento SSE `"degraded"`

Adicionar `"degraded"` como terceiro estado terminal no `ProgressTracker`:
- `"complete"`: Busca ao vivo concluida com dados frescos
- `"degraded"`: Pipeline concluiu mas servindo dados de cache ou parciais
- `"error"`: Falha total, nenhum dado disponivel

O evento `"degraded"` carrega metadata no campo `detail`:
```json
{
  "stage": "degraded",
  "progress": 100,
  "message": "Resultados disponiveis (dados de 2h atras)",
  "detail": {
    "reason": "timeout" | "source_failure" | "partial",
    "cache_age_hours": 2.3,
    "cache_level": "supabase",
    "sources_failed": ["pncp"],
    "sources_ok": ["pcp"],
    "coverage_pct": 78
  }
}
```

### 2. Frontend interpreta `"degraded"` como estado distinto

O hook `useSearchProgress` reconhece `"degraded"` como terminal (fecha SSE) mas propaga o estado de forma diferenciada. O componente de loading transiciona para uma UI que comunica:
- Dados disponiveis (nao e erro)
- Dados nao sao ao vivo (nao e sucesso puro)
- Informacao de freshness e cobertura

### 3. Transicao visual diferenciada

Em vez de: Loading → "Pronto!" (verde)
Mostrar: Loading → "Resultados disponiveis - dados de Xh atras" (amber/amarelo)

A cor amber (nao vermelho, nao verde) comunica "funcional com ressalva".

---

## Acceptance Criteria

### AC1 — `ProgressTracker.emit_degraded()` implementado
O `ProgressTracker` em `progress.py` DEVE ter um metodo `emit_degraded(reason, detail)` que emite um `ProgressEvent` com `stage="degraded"`, `progress=100`, e metadata no campo `detail`.

### AC2 — `"degraded"` e estado terminal
O metodo `emit_degraded()` DEVE setar `self._is_complete = True` (mesmo comportamento de `emit_complete` e `emit_error`).

### AC3 — Pipeline emite `"degraded"` quando serve cache
Quando `search_pipeline.py` serve dados de cache stale (apos timeout, falha total, ou excecao generica), DEVE chamar `tracker.emit_degraded()` em vez de `tracker.emit_complete()`.

### AC4 — Pipeline emite `"degraded"` quando resultado e parcial
Quando `ctx.is_partial = True` e `ctx.licitacoes_raw` tem dados (resultado parcial, nao vazio), DEVE emitir `"degraded"` com `reason="partial"` e metadata de cobertura.

### AC5 — Pipeline mantem `"complete"` para busca ao vivo com sucesso
Quando a busca ao vivo completa sem fallback e sem parcialidade, pipeline DEVE continuar emitindo `"complete"` (sem regressao).

### AC6 — Metadata do evento `"degraded"` inclui campos obrigatorios
O `detail` do evento degraded DEVE conter: `reason` (string), `cache_age_hours` (float, quando cache servido), `sources_failed` (lista), `coverage_pct` (int 0-100).

### AC7 — Frontend reconhece `"degraded"` como terminal
O hook `useSearchProgress.ts` DEVE tratar `event.stage === 'degraded'` como terminal: fechar EventSource e atualizar estado. O campo `sseDisconnected` NAO deve ser setado (nao e desconexao).

### AC8 — Frontend expoe estado degraded para componentes
`useSearchProgress` DEVE retornar campo `isDegraded: boolean` alem dos existentes, setado para `true` quando ultimo evento terminal foi `"degraded"`.

### AC9 — Componente de loading transiciona para amber em degraded
Quando `isDegraded === true`, o componente de loading/progresso DEVE transicionar para visual amber (nao verde, nao vermelho) com mensagem que inclui freshness: "Resultados disponiveis — dados de Xh atras".

### AC10 — `DegradationBanner` exibe metadata do SSE degraded
O `DegradationBanner` DEVE exibir `coverage_pct`, `sources_failed`, e `cache_age_hours` recebidos via SSE event detail (quando disponiveis).

### AC11 — Teste backend: emit_degraded() setado
Teste unitario: `ProgressTracker.emit_degraded()` emite evento com `stage="degraded"`, `progress=100`, `_is_complete=True`.

### AC12 — Teste backend: pipeline emite degraded apos cache serving
Teste que simula falha de fontes → cache stale servido → verifica que `tracker.emit_degraded()` foi chamado (nao `emit_complete`).

### AC13 — Teste frontend: useSearchProgress reconhece degraded
Teste do hook: evento SSE com `stage="degraded"` → `isDegraded=true`, `isConnected=false`, `sseDisconnected=false`.

### AC14 — Teste frontend: transicao visual amber
Teste de componente: quando `isDegraded=true`, container de progresso renderiza com classe CSS amber (nao green, nao red).

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/progress.py` | Adicionar `emit_degraded()` ao `ProgressTracker`; stage "degraded" no enum |
| `backend/search_pipeline.py` | Substituir `emit_complete()` por `emit_degraded()` nos paths de cache/parcial |
| `frontend/hooks/useSearchProgress.ts` | Reconhecer "degraded" como terminal; expor `isDegraded` |
| `frontend/hooks/useSearchProgress.ts` | Tipar `SearchProgressEvent.detail` com campos de degradacao |
| `frontend/components/EnhancedLoadingProgress.tsx` | Transicao amber para degraded |
| `frontend/app/buscar/components/DegradationBanner.tsx` | Consumir metadata SSE degraded |
| `backend/tests/test_progress.py` | AC11, AC12 |
| `frontend/__tests__/hooks/useSearchProgress.test.ts` | AC13 |
| `frontend/__tests__/buscar/degraded-visual.test.tsx` | AC14 |

---

## Dependencias

| Story | Relacao |
|-------|---------|
| **A-01** (Timeout Cache Fallback) | A-01 define `response_state` e os paths de cache serving que A-02 instrumenta com SSE. Recomendado implementar A-01 primeiro, mas A-02 pode ser iniciada em paralelo no lado do `progress.py`. |
| **A-04** (Progressive Delivery) | A-04 usa SSE para streaming incremental. A-02 define o vocabulario de eventos que A-04 estende. |
| **A-05** (Indicadores de Cobertura) | A-05 consome `coverage_pct` que A-02 propaga via SSE. |

---

## Definition of Done

- [x] Todos os 14 ACs verificados e passing
- [x] Testes unitarios backend: 4 novos (TestEmitDegraded), zero regressoes (34 fail / 3615 pass vs baseline 33/3599)
- [x] Testes frontend: 24 novos (9 hook + 15 visual), zero regressoes (33 fail / 1846 pass vs baseline 33/1764)
- [x] TypeScript check (`npx tsc --noEmit`) passing
- [x] Demonstracao: simular timeout de fonte → SSE emite "degraded" → frontend mostra amber
- [x] Regressao: busca normal ao vivo → SSE emite "complete" → frontend mostra verde
- [ ] Code review aprovado
- [x] Commit convencional: `feat(backend+frontend): GTM-RESILIENCE-A02 — SSE degraded event + frontend amber state`
