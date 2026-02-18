# Story UX-301: Fix Timeout Catastrófico na Busca Principal

**Epic:** EPIC-UX-PREMIUM-2026-02
**Story ID:** UX-301
**Priority:** 🔴 P0 CRITICAL
**Story Points:** 13 SP
**Created:** 2026-02-18
**Owner:** @dev + @qa
**Status:** 🔴 TODO

---

## Story Overview

**Problema:** Busca com 27 estados resulta em timeout 524 após ~2 minutos, deixando usuário sem resultados e com mensagem de erro genérica não-acionável.

**Impacto:** Funcionalidade CORE completamente quebrada para buscas amplas. Usuário investe tempo → recebe erro → não sabe o que fazer.

**Evidência:**
```
HTTP 524 Gateway Timeout
Busca de 27 estados: ~120s → timeout
Mensagem: "Não foi possível processar sua busca"
Botão: "Tentar novamente (0:24)" [disabled]
```

**Goal:** Transformar timeout catastrófico em experiência degradada graciosa com guidance proativo.

---

## Acceptance Criteria

### AC1: Prevenção Proativa (Warning Antes de Buscar)
- [ ] **GIVEN** usuário seleciona >10 estados
- [ ] **WHEN** clica em "Buscar"
- [ ] **THEN** mostra modal de warning:
  ```
  ⚠️ Busca Ampla Detectada

  Buscas com mais de 10 estados podem levar 5+ minutos e ocasionalmente
  falhar por timeout.

  Recomendamos:
  • Começar com sua região de atuação (3-5 estados)
  • Ou focar nos estados com maior volume de licitações

  [Continuar mesmo assim]  [Selecionar minha região]
  ```

### AC2: Timeout Progressivo (Não Abrupto)
- [ ] **GIVEN** busca está rodando há >90s
- [ ] **WHEN** ainda não completou
- [ ] **THEN** mostra warning inline:
  ```
  ⏱️ A busca está demorando mais que o esperado

  Você pode:
  • Continuar aguardando (pode levar mais 2-3 min)
  • Cancelar e refinar a busca (recomendado)

  [Continuar aguardando]  [Cancelar e refinar]
  ```

### AC3: Erro 524 Acionável (Não Genérico)
- [ ] **GIVEN** busca resulta em HTTP 524
- [ ] **WHEN** erro é capturado
- [ ] **THEN** mostra mensagem específica:
  ```
  ⏱️ A Busca Excedeu o Tempo Limite

  Buscas muito amplas (20+ estados) podem demorar além do esperado
  e ocasionalmente falhar.

  O que você pode fazer:

  [Tentar com menos estados]  [Ver buscas salvas]  [Falar com suporte]

  💡 Dica: Comece buscando apenas nos estados onde você já atua.
  Você sempre pode ampliar depois.
  ```

### AC4: Retry Inteligente (Não Punitivo)
- [ ] **GIVEN** usuário clica "Tentar novamente"
- [ ] **THEN** botão NÃO tem countdown forçado
- [ ] **AND** mostra hint: "Considere reduzir o escopo para evitar novo timeout"
- [ ] **AND** abre modal de filtros com sugestão de reduzir UFs

### AC5: Timeout Backend Aumentado (Railway)
- [ ] **GIVEN** env var `GUNICORN_TIMEOUT` em Railway
- [ ] **THEN** valor = 600s (10 min) (era 120s)
- [ ] **AND** `WEB_CONCURRENCY` = 2 (era 4, reduz memory pressure)
- [ ] **AND** logs mostram timeout efetivo = 600s

### AC6: Frontend Proxy Timeout Aumentado
- [ ] **GIVEN** `app/api/buscar/route.ts`
- [ ] **THEN** timeout = 480s (8 min) (era 300s)
- [ ] **AND** não crasha antes do backend

### AC7: Fallback para Cache Stale
- [ ] **GIVEN** busca timeout mas cache stale existe (6-24h)
- [ ] **WHEN** erro 524 ocorre
- [ ] **THEN** oferece opção:
  ```
  ⏱️ Busca Excedeu o Tempo Limite

  Encontramos resultados da mesma busca de 8 horas atrás (732 oportunidades).

  [Ver resultados de 8h atrás]  [Tentar busca atualizada novamente]
  ```

### AC8: Telemetria de Timeout
- [ ] **GIVEN** timeout 524 ocorre
- [ ] **THEN** envia evento Sentry:
  ```python
  sentry_sdk.capture_message("Search timeout", level="warning", extra={
      "num_states": 27,
      "elapsed_time_s": 124,
      "modalities": 4,
      "user_id": "...",
      "search_id": "...",
      "correlation_id": "..."
  })
  ```
- [ ] **AND** Mixpanel event `search_timeout` com mesmos extras

### AC9: UX de Seleção Inteligente de Estados
- [ ] **GIVEN** usuário na tela de busca
- [ ] **WHEN** seleciona >10 estados
- [ ] **THEN** mostra badge warning:
  ```
  ⚠️ 27 estados selecionados — busca pode demorar 5+ minutos
  ```
- [ ] **AND** botão "Buscar" muda para:
  ```
  [Buscar 27 estados (pode demorar)]
  ```

### AC10: Testes de Carga
- [ ] **GIVEN** teste de carga em staging
- [ ] **WHEN** 10 buscas simultâneas de 27 estados
- [ ] **THEN** <30% resultam em timeout
- [ ] **AND** as que completam levam <3min (p95)

---

## Technical Implementation

### Backend Changes

#### 1. Railway Env Vars
```bash
# railway.json ou via CLI
GUNICORN_TIMEOUT=600
WEB_CONCURRENCY=2
GUNICORN_GRACEFUL_TIMEOUT=60
```

#### 2. Timeout Chain Realignment
```python
# backend/config.py
SEARCH_FETCH_TIMEOUT = int(os.getenv("SEARCH_FETCH_TIMEOUT", "360"))  # 6 min
PNCP_TIMEOUT_PER_UF = int(os.getenv("PNCP_TIMEOUT_PER_UF", "90"))  # 90s normal
PCP_TIMEOUT = int(os.getenv("PCP_TIMEOUT", "30"))

# Ordem: Railway(600s) > Pipeline(360s) > PerUF(90s) > PerPage(30s)
```

#### 3. Graceful Degradation com Cache Stale
```python
# backend/search_pipeline.py
try:
    results = await execute_multi_source_search(...)
except asyncio.TimeoutError:
    logger.warning("Search timeout, checking stale cache...")

    stale_cache = await get_from_cache(
        cache_key,
        allow_stale=True,  # 6-24h
        max_age_hours=24
    )

    if stale_cache:
        return {
            "results": stale_cache["results"],
            "cached": True,
            "cache_age_hours": stale_cache["age_hours"],
            "stale_fallback": True,
            "warning": "Busca excedeu tempo limite. Mostrando resultados de cache."
        }
    else:
        raise  # Re-raise timeout se nem cache stale tem
```

### Frontend Changes

#### 1. Proxy Timeout
```typescript
// app/api/buscar/route.ts
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 480_000); // 8min

const response = await fetch(`${BACKEND_URL}/buscar`, {
  signal: controller.signal,
  // ...
});
```

#### 2. Warning Proativo (>10 Estados)
```tsx
// app/buscar/page.tsx
const showAmpleBuscaWarning = (numEstados: number) => {
  if (numEstados <= 10) return;

  setShowWarningModal({
    title: "Busca Ampla Detectada",
    message: `Buscas com ${numEstados} estados podem levar 5+ minutos...`,
    actions: [
      {
        label: "Continuar mesmo assim",
        variant: "secondary",
        onClick: () => executeBusca()
      },
      {
        label: "Selecionar minha região",
        variant: "primary",
        onClick: () => openFilterModal({ preselect: "sudeste" })
      }
    ]
  });
};
```

#### 3. Timeout Progressivo (>90s)
```tsx
useEffect(() => {
  if (!isSearching) return;

  const progressiveWarningTimer = setTimeout(() => {
    if (searchProgress < 80) {  // Ainda não perto do fim
      setShowProgressiveWarning(true);
    }
  }, 90_000); // 1.5min

  return () => clearTimeout(progressiveWarningTimer);
}, [isSearching, searchProgress]);
```

#### 4. Erro 524 Acionável
```tsx
const handleSearchError = (error: any) => {
  if (error.response?.status === 524) {
    return {
      type: "timeout",
      title: "A Busca Excedeu o Tempo Limite",
      message: "Buscas muito amplas (20+ estados) podem demorar...",
      actions: [
        {
          label: "Tentar com menos estados",
          onClick: () => openFilterModal({ maxStates: 5 })
        },
        {
          label: "Ver buscas salvas",
          onClick: () => router.push('/historico')
        },
        {
          label: "Falar com suporte",
          onClick: () => router.push('/mensagens')
        }
      ],
      tip: "💡 Dica: Comece buscando apenas nos estados onde você já atua."
    };
  }

  // Outros tipos de erro...
};
```

#### 5. Retry Sem Countdown
```tsx
<Button
  onClick={retrySearch}
  disabled={false}  // SEM countdown forçado
  variant="primary"
>
  Tentar novamente
</Button>

{lastSearchFailed && (
  <p className="text-sm text-yellow-700">
    💡 A busca anterior foi muito ampla. Considere reduzir o escopo.
  </p>
)}
```

#### 6. Stale Cache Fallback
```tsx
if (searchResponse.stale_fallback) {
  return (
    <StaleCacheBanner
      cacheAgeHours={searchResponse.cache_age_hours}
      onRetry={() => retrySearch({ force: true })}
      onAccept={() => setShowResults(true)}
    >
      ⏱️ Busca excedeu o tempo limite. Mostrando resultados de {searchResponse.cache_age_hours}h atrás.
    </StaleCacheBanner>
  );
}
```

---

## Testing Strategy

### Unit Tests
```python
# backend/tests/test_timeout_handling.py

async def test_timeout_returns_stale_cache():
    # Mock timeout
    with patch("search_pipeline.execute_multi_source_search", side_effect=asyncio.TimeoutError):
        # Mock stale cache exists
        with patch("search_cache.get_from_cache", return_value={
            "results": [...],
            "age_hours": 12
        }):
            response = await buscar_licitacoes(...)

            assert response["stale_fallback"] is True
            assert response["cache_age_hours"] == 12
            assert len(response["results"]) > 0
```

### Integration Tests
```typescript
// frontend/__tests__/buscar-timeout.test.tsx

it("shows progressive warning after 90s", async () => {
  jest.useFakeTimers();
  render(<BuscarPage />);

  fireEvent.click(screen.getByText("Buscar"));

  act(() => jest.advanceTimersByTime(90_000));

  expect(screen.getByText(/está demorando mais que o esperado/)).toBeInTheDocument();
});

it("shows proactive warning for 27 states", () => {
  render(<BuscarPage />);

  // Select all 27 states
  fireEvent.click(screen.getByText("Selecionar todos"));
  fireEvent.click(screen.getByText("Buscar"));

  expect(screen.getByText(/Busca Ampla Detectada/)).toBeInTheDocument();
});
```

### Load Tests (Artillery)
```yaml
# artillery-timeout-test.yml
config:
  target: "https://smartlic.tech"
  phases:
    - duration: 300  # 5 min
      arrivalRate: 2  # 2 searches/sec
scenarios:
  - name: "27-state search timeout test"
    flow:
      - post:
          url: "/api/buscar"
          json:
            ufs: ["AC", "AL", ..., "TO"]  # All 27
            setor_id: 1
          expect:
            - statusCode: [200, 524]  # Both acceptable
```

---

## File List

### Backend
- [ ] `backend/config.py` — Aumentar timeouts
- [ ] `backend/search_pipeline.py` — Graceful degradation + stale cache
- [ ] `backend/search_cache.py` — `allow_stale` parameter
- [ ] `backend/main.py` — Error handling para 524
- [ ] `backend/tests/test_timeout_handling.py` — 8 novos testes

### Frontend
- [ ] `frontend/app/api/buscar/route.ts` — Proxy timeout 480s
- [ ] `frontend/app/buscar/page.tsx` — Warning modal + progressive warning
- [ ] `frontend/components/StaleCacheBanner.tsx` — NOVO componente
- [ ] `frontend/components/AmpleBuscaWarningModal.tsx` — NOVO componente
- [ ] `frontend/__tests__/buscar-timeout.test.tsx` — 6 novos testes

### DevOps
- [ ] `railway.json` ou CLI — Env vars (GUNICORN_TIMEOUT, WEB_CONCURRENCY)
- [ ] `artillery-timeout-test.yml` — NOVO load test

---

## Dependencies

### Blockers
- Nenhum

### Related Stories
- UX-302 (Progresso não-monotônico) — Ambos mexem no search flow
- UX-310 (Mensagens de erro acionáveis) — Overlap em error handling

---

## Risks & Mitigations

### Risk 1: Aumentar Timeout Pode Piorar Memory Pressure
**Mitigation:**
- Reduzir `WEB_CONCURRENCY` de 4 → 2
- Monitorar Railway metrics

### Risk 2: Stale Cache Pode Mostrar Dados Desatualizados
**Mitigation:**
- Banner claro mostrando idade do cache
- Botão "Tentar busca atualizada" disponível

### Risk 3: Warning Modal Pode Irritar Usuários Experientes
**Mitigation:**
- Checkbox "Não mostrar novamente" (localStorage)
- Só mostrar 1x por sessão

---

## Definition of Done

- [ ] Todos os ACs passam
- [ ] 8 testes backend passam
- [ ] 6 testes frontend passam
- [ ] Load test artillery mostra <30% timeout rate
- [ ] Sentry/Mixpanel telemetria funcionando
- [ ] QA sign-off
- [ ] Staging deployment OK
- [ ] Code review aprovado

---

## Estimation Breakdown

- Backend timeout handling: 3 SP
- Frontend warning modals: 3 SP
- Stale cache fallback: 2 SP
- Telemetria (Sentry + Mixpanel): 1 SP
- Testing (unit + integration + load): 3 SP
- DevOps (Railway configs): 1 SP

**Total:** 13 SP

---

**Status:** 🔴 TODO
**Next:** @dev iniciar implementação após approval
