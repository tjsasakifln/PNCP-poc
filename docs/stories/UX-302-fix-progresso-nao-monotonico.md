# Story UX-302: Fix Progresso Não-Monotônico (Reinício Abrupto)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Story ID:** UX-302
**Priority:** 🔴 P0 CRITICAL
**Story Points:** 8 SP
**Created:** 2026-02-18
**Owner:** @dev
**Status:** 🔴 TODO

---

## Story Overview

**Problema:** Barra de progresso reinicia abruptamente durante busca, voltando de 47% para 12% sem explicação. Quebra total de confiança do usuário.

**User Report:**
> "a barra de progresso reinicia abruptamente sem motivo aparente"

**Evidência de Logs:**
```
Progresso: 12% → 18% → 34% → 47% → [RESTART] → 12% → 18% ...
Causa: Múltiplas fontes (PNCP + PCP) reportando progresso independente
```

**Impacto:** Usuário perde confiança na estimativa de tempo. Sistema parece bugado ou congelado.

**Goal:** Garantir que progresso NUNCA volta para trás. Progresso deve ser **monotonicamente crescente**.

---

## Acceptance Criteria

### AC1: Progresso Sempre Crescente (Backend)
- [ ] **GIVEN** backend emite evento SSE de progresso
- [ ] **THEN** valor NUNCA é menor que o último emitido
- [ ] **AND** se nova fonte reporta valor menor, sistema ignora ou normaliza

**Exemplo:**
```python
# ANTES (bugado):
emit_progress(18)  # OK
emit_progress(34)  # OK
emit_progress(12)  # ❌ BUG — volta para trás

# DEPOIS (fixado):
emit_progress(18)  # OK
emit_progress(34)  # OK
emit_progress(12)  # Ignored, mantém 34%
```

### AC2: Aggregação Multi-Source Ponderada
- [ ] **GIVEN** PNCP contribui 70% do progresso total
- [ ] **AND** PCP contribui 30% do progresso total
- [ ] **WHEN** ambas fontes reportam progresso independente
- [ ] **THEN** progresso final = weighted average MONOTÔNICO

**Fórmula:**
```python
progress_total = (pncp_progress * 0.7) + (pcp_progress * 0.3)
progress_total = max(progress_total, last_progress)  # Garantia de monotonia
```

### AC3: Feedback Visual de Progresso Estimado vs Medido
- [ ] **GIVEN** progresso é calculado (não reportado diretamente)
- [ ] **WHEN** mostra na UI
- [ ] **THEN** usa variante visual diferente:

**Exemplo UI:**
```tsx
<ProgressBar
  value={progress.percent}
  variant={progress.isEstimated ? 'estimated' : 'measured'}
  label={progress.isEstimated ? 'Estimado' : 'Medido'}
/>

// Estimado: barra animada com padrão diagonal
// Medido: barra sólida
```

### AC4: Logs de Debug Quando Progresso Tenta Voltar
- [ ] **GIVEN** fonte reporta progresso < progresso atual
- [ ] **WHEN** sistema detecta tentativa de regressão
- [ ] **THEN** loga warning:
  ```python
  logger.warning(
      f"[Progress] Ignored backward progress from {source}: "
      f"{new_progress}% < {current_progress}%",
      extra={
          "source": source,
          "new_progress": new_progress,
          "current_progress": current_progress,
          "correlation_id": correlation_id
      }
  )
  ```

### AC5: Progresso por Estágio (Não Global)
- [ ] **GIVEN** busca tem 5 estágios:
  1. Consultando fontes (0-10%)
  2. Buscando dados (10-70%)
  3. Filtrando (70-85%)
  4. Avaliando (85-95%)
  5. Preparando Excel (95-100%)
- [ ] **WHEN** transita entre estágios
- [ ] **THEN** progresso NUNCA volta mesmo ao mudar de estágio

**Exemplo:**
```
Stage 1: 10% ✓
Stage 2: 10% → 35% → 70% ✓
Stage 3: 70% → 75% → 85% ✓  (NUNCA volta para 70%)
```

### AC6: Progresso "Freeze" Quando Aguardando Backend
- [ ] **GIVEN** backend para de emitir eventos SSE por >10s
- [ ] **WHEN** frontend detecta falta de heartbeat
- [ ] **THEN** mantém progresso atual + mostra animação de "processando"
- [ ] **AND** NÃO reinicia progresso

**Exemplo UI:**
```tsx
{lastProgressUpdate > 10_000 && (
  <ProcessingIndicator>
    ⏳ Processando... (pode levar mais alguns instantes)
  </ProcessingIndicator>
)}
```

### AC7: Teste de Progresso Monotônico
- [ ] **GIVEN** teste automatizado de busca
- [ ] **WHEN** coleta todos os eventos de progresso
- [ ] **THEN** verifica que array é monotônico:
  ```python
  progress_values = [12, 18, 34, 47, 52, 68, 89, 100]
  assert all(progress_values[i] <= progress_values[i+1] for i in range(len(progress_values)-1))
  ```

### AC8: Telemetria de Progresso Regressivo
- [ ] **GIVEN** sistema detecta tentativa de progresso regressivo
- [ ] **THEN** envia evento Sentry (warning level):
  ```python
  sentry_sdk.capture_message(
      "Progress regression detected",
      level="warning",
      extra={
          "source": source,
          "attempted_progress": new_progress,
          "current_progress": current_progress,
          "correlation_id": correlation_id
      }
  )
  ```

### AC9: Frontend State Management Robusto
- [ ] **GIVEN** múltiplos eventos SSE chegam rapidamente
- [ ] **WHEN** React re-renderiza
- [ ] **THEN** estado de progresso é atualizado atomicamente
- [ ] **AND** não há race conditions que causam regressão

**Implementação:**
```tsx
const [progress, setProgress] = useState(0);
const progressRef = useRef(0);  // Evitar stale closures

const updateProgress = useCallback((newProgress: number) => {
  setProgress(prev => {
    const safeProgress = Math.max(newProgress, prev);
    progressRef.current = safeProgress;
    return safeProgress;
  });
}, []);
```

### AC10: Documentação de Progresso Multi-Source
- [ ] **GIVEN** documentação técnica
- [ ] **THEN** explica como progresso é calculado
- [ ] **AND** inclui diagrama de fluxo de eventos SSE

---

## Technical Implementation

### Backend Changes

#### 1. ProgressTracker com Monotonia Garantida
```python
# backend/progress.py

class ProgressTracker:
    def __init__(self, search_id: str):
        self.search_id = search_id
        self.current_progress = 0
        self.max_reached_progress = 0
        self.source_progress: Dict[str, int] = {}  # Por fonte
        self.queue: asyncio.Queue = asyncio.Queue()

    async def update_progress(
        self,
        new_progress: int,
        source: str,
        stage: Optional[str] = None
    ):
        """
        Atualiza progresso garantindo monotonia.
        """
        # Garantia de monotonia
        safe_progress = max(new_progress, self.current_progress)

        # Se tentou voltar, loga warning
        if new_progress < self.current_progress:
            logger.warning(
                f"[Progress] Ignored backward progress from {source}: "
                f"{new_progress}% < {self.current_progress}%",
                extra={
                    "search_id": self.search_id,
                    "source": source,
                    "attempted": new_progress,
                    "current": self.current_progress
                }
            )
            # Sentry telemetria
            sentry_sdk.capture_message(
                "Progress regression detected",
                level="warning",
                extra={"source": source, ...}
            )
            return  # NÃO emite evento regressivo

        # Atualiza estado
        self.current_progress = safe_progress
        self.max_reached_progress = max(safe_progress, self.max_reached_progress)
        self.source_progress[source] = new_progress

        # Emite evento SSE
        await self.emit_progress_event({
            "percent": safe_progress,
            "stage": stage,
            "source": source,
            "is_estimated": self._is_estimated_progress(source)
        })

    async def update_multi_source_progress(self, sources: Dict[str, int]):
        """
        Agrega progresso de múltiplas fontes com ponderação.
        """
        weights = {"pncp": 0.7, "pcp": 0.3}
        weighted_avg = sum(
            progress * weights.get(source, 0)
            for source, progress in sources.items()
        )

        # SEMPRE crescente
        safe_progress = max(weighted_avg, self.current_progress)

        await self.update_progress(
            safe_progress,
            source="multi_source_aggregate",
            stage="buscando_dados"
        )

    def _is_estimated_progress(self, source: str) -> bool:
        """
        Determina se progresso é medido ou estimado.
        """
        return source in ["time_based_estimate", "multi_source_aggregate"]
```

#### 2. SSE Event Emission
```python
# backend/routes/buscar.py

async def emit_progress_event(data: dict):
    """
    Emite evento SSE com garantia de monotonia.
    """
    event = {
        "event": "progress",
        "data": json.dumps({
            "percent": data["percent"],
            "stage": data["stage"],
            "source": data["source"],
            "is_estimated": data["is_estimated"],
            "timestamp": datetime.utcnow().isoformat()
        })
    }

    await queue.put(event)
```

### Frontend Changes

#### 1. SSE Consumer com State Management Robusto
```typescript
// app/buscar/useSearchProgress.ts

export const useSearchProgress = (searchId: string | null) => {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<string | null>(null);
  const [isEstimated, setIsEstimated] = useState(false);
  const progressRef = useRef(0);  // Evitar stale closures

  useEffect(() => {
    if (!searchId) return;

    const eventSource = new EventSource(`/api/buscar-progress/${searchId}`);

    eventSource.addEventListener("progress", (event) => {
      const data = JSON.parse(event.data);

      // Garantia de monotonia no frontend também
      setProgress(prev => {
        const safeProgress = Math.max(data.percent, prev, progressRef.current);
        progressRef.current = safeProgress;

        // Debug log
        if (data.percent < prev) {
          console.warn(
            `[Progress] Ignored backward SSE: ${data.percent}% < ${prev}%`,
            { source: data.source, stage: data.stage }
          );
        }

        return safeProgress;
      });

      setStage(data.stage);
      setIsEstimated(data.is_estimated);
    });

    return () => eventSource.close();
  }, [searchId]);

  return { progress, stage, isEstimated };
};
```

#### 2. ProgressBar com Variantes
```tsx
// components/ProgressBar.tsx

interface ProgressBarProps {
  value: number;
  variant?: 'measured' | 'estimated';
  label?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  variant = 'measured',
  label
}) => {
  return (
    <div className="relative">
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full transition-all duration-500 ease-out",
            variant === 'measured'
              ? "bg-blue-600"
              : "bg-blue-400 animate-progress-shimmer"
          )}
          style={{ width: `${value}%` }}
        />
      </div>

      {label && (
        <span className="text-xs text-gray-500 mt-1">
          {label}
        </span>
      )}
    </div>
  );
};
```

#### 3. Animação de Shimmer para Progresso Estimado
```css
/* styles/animations.css */

@keyframes progress-shimmer {
  0% {
    background-position: -200% center;
  }
  100% {
    background-position: 200% center;
  }
}

.animate-progress-shimmer {
  background: linear-gradient(
    90deg,
    rgba(59, 130, 246, 0.4) 25%,
    rgba(59, 130, 246, 1) 50%,
    rgba(59, 130, 246, 0.4) 75%
  );
  background-size: 200% 100%;
  animation: progress-shimmer 2s infinite linear;
}
```

#### 4. Processing Indicator (Heartbeat Missing)
```tsx
// components/ProcessingIndicator.tsx

const [lastUpdate, setLastUpdate] = useState(Date.now());

useEffect(() => {
  const interval = setInterval(() => {
    const timeSinceUpdate = Date.now() - lastUpdate;

    if (timeSinceUpdate > 10_000 && isSearching) {
      setShowProcessing(true);
    }
  }, 1000);

  return () => clearInterval(interval);
}, [lastUpdate, isSearching]);

{showProcessing && (
  <div className="flex items-center gap-2 text-sm text-yellow-700">
    <Spinner />
    <span>Processando... (pode levar mais alguns instantes)</span>
  </div>
)}
```

---

## Testing Strategy

### Unit Tests (Backend)
```python
# backend/tests/test_progress_monotonic.py

async def test_progress_never_regresses():
    tracker = ProgressTracker("test-123")

    await tracker.update_progress(20, source="pncp")
    assert tracker.current_progress == 20

    await tracker.update_progress(40, source="pncp")
    assert tracker.current_progress == 40

    # Tentativa de regressão
    await tracker.update_progress(15, source="pcp")
    assert tracker.current_progress == 40  # Mantém 40, não volta para 15

async def test_multi_source_weighted_average():
    tracker = ProgressTracker("test-456")

    await tracker.update_multi_source_progress({
        "pncp": 50,  # 70% weight
        "pcp": 20    # 30% weight
    })

    expected = (50 * 0.7) + (20 * 0.3)  # 41%
    assert tracker.current_progress == 41

async def test_sentry_event_on_regression():
    with patch("sentry_sdk.capture_message") as mock_sentry:
        tracker = ProgressTracker("test-789")

        await tracker.update_progress(60, source="pncp")
        await tracker.update_progress(30, source="pcp")  # Tenta regressão

        mock_sentry.assert_called_once()
        assert "regression" in mock_sentry.call_args[0][0].lower()
```

### Integration Tests (Frontend)
```typescript
// __tests__/progress-monotonic.test.tsx

it("never shows backward progress", async () => {
  const mockEventSource = createMockEventSource();
  render(<SearchProgress searchId="test-123" />);

  // Emite eventos de progresso
  act(() => {
    mockEventSource.emit("progress", { percent: 20, source: "pncp" });
  });
  expect(screen.getByRole("progressbar")).toHaveValue(20);

  act(() => {
    mockEventSource.emit("progress", { percent: 45, source: "pncp" });
  });
  expect(screen.getByRole("progressbar")).toHaveValue(45);

  // Tenta regressão
  act(() => {
    mockEventSource.emit("progress", { percent: 10, source: "pcp" });
  });

  // DEVE manter 45, NÃO voltar para 10
  expect(screen.getByRole("progressbar")).toHaveValue(45);
});

it("shows visual indicator for estimated progress", () => {
  render(<ProgressBar value={50} variant="estimated" />);

  const bar = screen.getByRole("progressbar");
  expect(bar).toHaveClass("animate-progress-shimmer");
});
```

### E2E Test (Playwright)
```typescript
// e2e-tests/progress-monotonic.spec.ts

test("progress bar never goes backward during search", async ({ page }) => {
  await page.goto("/buscar");

  await page.click("text=Buscar Vestuário e Uniformes");

  const progressValues: number[] = [];

  // Captura todos os valores de progresso
  page.on("console", (msg) => {
    if (msg.text().includes("Progress:")) {
      const match = msg.text().match(/(\d+)%/);
      if (match) {
        progressValues.push(parseInt(match[1]));
      }
    }
  });

  // Aguarda busca completar ou falhar
  await page.waitForSelector("text=Resultados", { timeout: 180_000 });

  // Verifica monotonia
  for (let i = 1; i < progressValues.length; i++) {
    expect(progressValues[i]).toBeGreaterThanOrEqual(progressValues[i - 1]);
  }
});
```

---

## File List

### Backend
- [ ] `backend/progress.py` — Classe ProgressTracker com monotonia
- [ ] `backend/routes/buscar.py` — SSE emission com garantia
- [ ] `backend/tests/test_progress_monotonic.py` — 8 novos testes

### Frontend
- [ ] `frontend/app/buscar/useSearchProgress.ts` — Hook robusto com ref
- [ ] `frontend/components/ProgressBar.tsx` — Variantes measured/estimated
- [ ] `frontend/components/ProcessingIndicator.tsx` — NOVO componente
- [ ] `frontend/styles/animations.css` — Shimmer animation
- [ ] `frontend/__tests__/progress-monotonic.test.tsx` — 5 novos testes
- [ ] `frontend/e2e-tests/progress-monotonic.spec.ts` — NOVO E2E test

---

## Dependencies

### Blockers
- Nenhum

### Related Stories
- UX-301 (Timeout catastrófico) — Ambos mexem no search flow
- UX-311 (Estimativa de tempo) — Usa progresso para calcular ETA

---

## Risks & Mitigations

### Risk 1: Agregação Ponderada Pode Não Ser Intuitiva
**Mitigation:**
- Mostrar "Estimado" vs "Medido" visualmente
- Documentar lógica de agregação

### Risk 2: Progresso "Congelado" Pode Parecer Travado
**Mitigation:**
- ProcessingIndicator com animação
- Heartbeat de 5s para detectar falta de progresso

---

## Definition of Done

- [ ] Todos os ACs passam
- [ ] 8 testes backend passam
- [ ] 5 testes frontend passam
- [ ] 1 teste E2E Playwright passa
- [ ] Sentry telemetria funcionando (warning on regression)
- [ ] QA sign-off (teste manual de busca completa)
- [ ] Code review aprovado

---

## Estimation Breakdown

- Backend ProgressTracker: 2 SP
- Frontend useSearchProgress hook: 2 SP
- ProgressBar variantes + animações: 2 SP
- Testing (unit + integration + E2E): 2 SP

**Total:** 8 SP

---

**Status:** 🔴 TODO
**Next:** @dev iniciar após UX-301 (depende parcialmente)
