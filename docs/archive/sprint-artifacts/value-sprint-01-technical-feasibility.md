# Value Sprint 01 - Technical Feasibility & Work Allocation

**Engineering Manager:** @pm (Morgan)
**Date:** 2026-01-29
**Sprint:** Value Sprint 01 - Phase 1 (Discovery & Planning)
**Input:** MoSCoW Prioritization (@po), UX Design Concepts (@ux-design-expert)

---

## Executive Summary

Completed technical feasibility assessment for Value Sprint MUST HAVE deliverables. **All features are technically feasible within 2-week sprint with identified mitigations for risks.**

**Tech Stack:**
- Frontend: Next.js 14 (App Router), React 18+, TypeScript 5.3+, Tailwind CSS 3.4+
- Backend: FastAPI 0.110+, Python 3.11+, httpx, OpenAI SDK
- Infrastructure: Vercel (frontend), TBD (backend)

**Capacity Assessment:**
- **Available:** ~50-55 story points (2 weeks, 9-agent squad)
- **Committed:** 30 story points (MUST HAVE)
- **Buffer:** 20-25 points (40-50% safety margin) ✅ HEALTHY

**Technical Decisions:**
1. ✅ **Analytics:** Mixpanel (recommended over GA4)
2. ✅ **Saved Searches:** localStorage (MVP), defer backend DB to next sprint
3. ✅ **Real-time Progress:** Polling (fallback from WebSocket/SSE for simplicity)
4. ✅ **Onboarding:** Intro.js library (proven, lightweight)

**Risk Level:** 🟡 MEDIUM (manageable with mitigations)

---

## 1. Technical Feasibility Matrix

| Feature | Complexity | Risk | Effort | Dependencies | Verdict |
|---------|------------|------|--------|--------------|---------|
| **Analytics Tracking** | LOW | LOW | 1 SP | None | ✅ FEASIBLE |
| **Saved Searches & History** | MEDIUM | LOW | 13 SP | localStorage API | ✅ FEASIBLE |
| **Performance + Visible Feedback** | MEDIUM-HIGH | MEDIUM | 8 SP | Backend API changes | ⚠️ FEASIBLE (with fallback) |
| **Interactive Onboarding** | MEDIUM | LOW | 8 SP | Intro.js library | ✅ FEASIBLE |

**Overall Verdict:** ✅ **ALL FEATURES FEASIBLE** (with identified mitigations)

---

## 2. Feature-by-Feature Technical Assessment

### Feature #0: Analytics Tracking (Priority #0)

**Effort:** 1 story point (2 days)
**Complexity:** LOW
**Risk:** LOW
**Owner:** @dev (frontend lead) + @analyst

#### Technical Requirements

**Frontend:**
- Integrate analytics SDK (Mixpanel OR GA4)
- Track 8 events:
  1. `search_started`
  2. `search_completed`
  3. `search_failed`
  4. `download_started`
  5. `download_completed`
  6. `download_failed`
  7. `page_load`
  8. `page_exit`

**Backend:**
- Structured logging already exists (main.py:199-207)
- No additional backend work needed

---

#### Tool Choice: Mixpanel vs. Google Analytics 4

| Criterion | Mixpanel | Google Analytics 4 | Winner |
|-----------|----------|-------------------|--------|
| **Product Analytics** | ✅ Purpose-built | ⚠️ Marketing-focused | Mixpanel |
| **Event Tracking** | ✅ Unlimited events | ⚠️ Complex event setup | Mixpanel |
| **Funnel Analysis** | ✅ Built-in | ⚠️ Manual configuration | Mixpanel |
| **User Retention** | ✅ Cohort analysis | ⚠️ Limited | Mixpanel |
| **Real-time Dashboard** | ✅ Live View | ⚠️ 24-48h delay | Mixpanel |
| **Pricing** | ⚠️ Free tier: 20M events/month | ✅ Free unlimited | Tie |
| **GDPR Compliance** | ✅ EU data residency | ✅ EU data residency | Tie |
| **Integration Complexity** | ✅ 5 lines of code | ✅ 5 lines of code | Tie |

**Decision:** ✅ **Mixpanel** (better product analytics, real-time data)

**Fallback:** If Mixpanel hits free tier limit (unlikely for POC), switch to GA4 (same event schema)

---

#### Implementation Plan

**Step 1: Install SDK**
```bash
cd frontend
npm install mixpanel-browser
```

**Step 2: Initialize (frontend/app/layout.tsx)**
```typescript
import mixpanel from 'mixpanel-browser';

// Initialize on app load
useEffect(() => {
  mixpanel.init(process.env.NEXT_PUBLIC_MIXPANEL_TOKEN!);
}, []);
```

**Step 3: Create Analytics Hook (frontend/hooks/useAnalytics.ts)**
```typescript
import mixpanel from 'mixpanel-browser';

export const useAnalytics = () => {
  const trackEvent = (eventName: string, properties?: Record<string, any>) => {
    mixpanel.track(eventName, properties);
  };

  return { trackEvent };
};
```

**Step 4: Instrument Events (frontend/app/page.tsx)**
```typescript
const { trackEvent } = useAnalytics();

// In buscar() function:
trackEvent('search_started', {
  ufs: ufsSelecionadas,
  date_range: { inicial: dataInicial, final: dataFinal },
  setor: setorId,
});

// After search completes:
trackEvent('search_completed', {
  time_elapsed: elapsedMs,
  total_raw: result.total_raw,
  total_filtered: result.total_filtrado,
});

// In handleDownload():
trackEvent('download_started', { download_id: result.download_id });
```

**Testing:**
1. Verify events appear in Mixpanel dashboard (Live View)
2. Test all 8 events manually
3. Validate event properties are correct

**Effort Breakdown:**
- Setup: 2 hours
- Instrumentation: 4 hours
- Testing: 2 hours
- **Total:** 8 hours (1 story point)

---

### Feature #1: Saved Searches & History

**Effort:** 13 story points (5 days)
**Complexity:** MEDIUM
**Risk:** LOW
**Owner:** @dev (full-stack) + @architect

#### Technical Requirements

**Frontend:**
- localStorage persistence
- UI component: SearchHistoryDropdown (recommended over Sidebar for MVP)
- Search re-execution logic
- Favorite/pin functionality

**Backend:**
- No changes needed (localStorage only)

---

#### Architecture Decision: localStorage vs. Backend DB

| Criterion | localStorage (MVP) | Backend DB (Future) | Decision |
|-----------|-------------------|---------------------|----------|
| **Implementation Time** | ✅ 5 days | ❌ 10+ days (needs API, schema, auth) | localStorage (MVP) |
| **Cross-device Sync** | ❌ No | ✅ Yes | Defer to Sprint 2 |
| **Storage Limit** | ⚠️ 5-10MB (ample for 10 searches) | ✅ Unlimited | localStorage OK for MVP |
| **Offline Support** | ✅ Works offline | ❌ Requires connection | localStorage |
| **User Privacy** | ✅ Data never leaves browser | ⚠️ Server-side storage | localStorage |
| **Complexity** | ✅ Zero backend changes | ❌ Requires auth, API, DB | localStorage |

**Decision:** ✅ **localStorage for MVP** (Sprint 1), backend DB upgrade in Sprint 2

**Rationale:**
- localStorage is FASTEST to implement (no backend work)
- Adequate for 10 saved searches (MVP constraint)
- User privacy win (data stays local)
- Future upgrade path is clear (migrate to backend when needed)

---

#### Data Schema (localStorage)

```typescript
// Key: "descomplicita_saved_searches"
// Value: JSON.stringify(SavedSearch[])

interface SavedSearch {
  id: string;                    // UUID v4
  timestamp: string;             // ISO 8601 (new Date().toISOString())
  name: string;                  // User-editable (default: setor name or "Busca customizada")
  searchParams: {
    ufs: string[];               // ["SC", "PR", "RS"]
    dataInicial: string;         // "2026-01-22"
    dataFinal: string;           // "2026-01-29"
    setorId: string | null;      // "vestuario" OR null
    termosBusca: string | null;  // "uniformes fardamento" OR null
  };
  results: {
    totalRaw: number;            // 127
    totalFiltered: number;       // 15
    valorTotal: number;          // 1200000.50
  };
  isFavorite: boolean;           // true if pinned
}
```

**Storage Estimate:**
- 1 SavedSearch: ~500 bytes
- 10 searches: ~5KB
- Well within localStorage limit (5-10MB per origin)

---

#### Component Architecture

```
<SearchHistoryDropdown />
  ├── <DropdownTrigger> (🕐 Histórico ▼)
  ├── <DropdownContent>
  │   ├── <FavoritesSection> (⭐ Favoritos)
  │   │   └── <SavedSearchCard> (x3 max)
  │   ├── <RecentsSection> (🕐 Recentes)
  │   │   └── <SavedSearchCard> (x7 recent)
  │   └── <ClearHistoryButton>
  └── <EmptyState> (if no searches)
```

**State Management:**
```typescript
// Custom hook: useSavedSearches()
const useSavedSearches = () => {
  const [searches, setSearches] = useState<SavedSearch[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('descomplicita_saved_searches');
    if (stored) setSearches(JSON.parse(stored));
  }, []);

  const saveSearch = (search: SavedSearch) => {
    const updated = [search, ...searches].slice(0, 10); // Keep max 10
    setSearches(updated);
    localStorage.setItem('descomplicita_saved_searches', JSON.stringify(updated));
  };

  const toggleFavorite = (id: string) => {
    const updated = searches.map(s =>
      s.id === id ? { ...s, isFavorite: !s.isFavorite } : s
    );
    setSearches(updated);
    localStorage.setItem('descomplicita_saved_searches', JSON.stringify(updated));
  };

  const deleteSearch = (id: string) => {
    const updated = searches.filter(s => s.id !== id);
    setSearches(updated);
    localStorage.setItem('descomplicita_saved_searches', JSON.stringify(updated));
  };

  const reExecuteSearch = (id: string) => {
    const search = searches.find(s => s.id === id);
    if (!search) return;

    // Pre-fill form with saved params
    setUfsSelecionadas(new Set(search.searchParams.ufs));
    setDataInicial(search.searchParams.dataInicial);
    setDataFinal(search.searchParams.dataFinal);
    setSetorId(search.searchParams.setorId || '');
    // ... then auto-trigger search
    buscar();
  };

  return { searches, saveSearch, toggleFavorite, deleteSearch, reExecuteSearch };
};
```

---

#### Implementation Plan

**Day 1-2: Core functionality**
1. Create `useSavedSearches` hook
2. Integrate with `buscar()` function (save after successful search)
3. Test localStorage persistence

**Day 3-4: UI component**
1. Build `<SearchHistoryDropdown>` component (using Radix UI or Headless UI)
2. Build `<SavedSearchCard>` sub-component
3. Add favorite/delete actions

**Day 5: Polish & Edge Cases**
1. Empty state design
2. Max limit handling (10 searches)
3. Mobile responsive
4. Accessibility (keyboard navigation, screen reader labels)

**Effort Breakdown:**
- Hook implementation: 8 hours (1 SP)
- UI components: 24 hours (3 SP)
- Integration with existing form: 8 hours (1 SP)
- Testing + Polish: 16 hours (2 SP)
- **Total:** 56 hours (7 SP) → Rounded to **13 SP** (includes buffer)

---

#### Risk Mitigation

**Risk:** localStorage quota exceeded (unlikely but possible)
**Mitigation:**
```typescript
try {
  localStorage.setItem('descomplicita_saved_searches', JSON.stringify(updated));
} catch (e) {
  if (e.name === 'QuotaExceededError') {
    // Auto-delete oldest non-favorite search
    const oldestNonFavorite = updated.find(s => !s.isFavorite);
    if (oldestNonFavorite) {
      deleteSearch(oldestNonFavorite.id);
      // Retry
      localStorage.setItem('descomplicita_saved_searches', JSON.stringify(updated));
    }
  }
}
```

**Risk:** User clears browser data (loses history)
**Mitigation:**
- Show warning in UI: "💡 Dica: Seus históricos são salvos localmente. Não limpe dados do navegador ou use favoritos para salvar buscas importantes."
- Future: Migrate to backend DB (cross-device sync)

---

### Feature #2: Performance + Visible Feedback

**Effort:** 8 story points (3 days)
**Complexity:** MEDIUM-HIGH
**Risk:** MEDIUM
**Owner:** @dev (frontend + backend) + @ux-design-expert

#### Technical Requirements

**Frontend:**
- Enhanced loading component with 5 stages
- Progress bar (0-100%)
- Real-time state updates (if backend supports)

**Backend:**
- Progress reporting API (optional, see decision below)
- OR: Frontend-only estimated progress (fallback)

---

#### Architecture Decision: Real-time Progress (WebSocket/SSE vs. Polling vs. Estimated)

| Approach | Pros | Cons | Effort | Decision |
|----------|------|------|--------|----------|
| **WebSocket** | ✅ True real-time, bi-directional | ❌ Complex (requires ws server, connection management) | 20 SP | ❌ Too complex for Sprint 1 |
| **SSE (Server-Sent Events)** | ✅ Real-time, simpler than WebSocket | ⚠️ FastAPI support is basic, requires async | 13 SP | ⚠️ Possible but risky |
| **Polling** (Frontend pings /progress endpoint every 2s) | ✅ Simple, works with existing REST API | ⚠️ Not true real-time (2s delay), more HTTP requests | 10 SP | ✅ RECOMMENDED (safe fallback) |
| **Estimated Progress** (Frontend-only, no backend) | ✅ Zero backend work, instant implementation | ❌ Inaccurate (guesses progress based on time) | 5 SP | ✅ MVP FALLBACK (if polling too complex) |

**Decision:** ✅ **Estimated Progress for MVP** (5 SP), with clear path to Polling upgrade (future sprint)

**Rationale:**
- Sprint 1 focus is on MUST HAVE delivery, not perfect accuracy
- Estimated progress is 80% as good as real-time (user just wants feedback, doesn't need exact %)
- Backend already logs structured data (can extract timing info later for calibration)
- Polling can be added in Sprint 2 without breaking changes

---

#### Estimated Progress Algorithm (Frontend-Only)

```typescript
const calculateProgress = (
  elapsedMs: number,
  totalEstimatedMs: number,
  stage: SearchStage
): number => {
  // Stage weights (% of total search time)
  const stageWeights = {
    'initiating': 5,      // 0-5%
    'fetching': 75,       // 5-80% (longest stage)
    'filtering': 10,      // 80-90%
    'summarizing': 5,     // 90-95%
    'generating_excel': 5 // 95-100%
  };

  // Calculate progress within current stage
  const stageProgress = Math.min((elapsedMs / totalEstimatedMs) * 100, 100);

  // Map to overall progress based on stage
  switch (stage) {
    case 'initiating':
      return Math.min(stageProgress * 0.05, 5);
    case 'fetching':
      return 5 + Math.min((stageProgress - 5) * 0.75, 75);
    case 'filtering':
      return 80 + Math.min((stageProgress - 80) * 0.10, 10);
    case 'summarizing':
      return 90 + Math.min((stageProgress - 90) * 0.05, 5);
    case 'generating_excel':
      return 95 + Math.min((stageProgress - 95) * 0.05, 5);
    default:
      return 0;
  }
};

// Time estimation formula (calibrated from baseline data)
const estimateTotalTime = (ufCount: number): number => {
  const baseTime = 10000; // 10s minimum
  const perUfTime = 3000;  // 3s per state (average)
  const filteringTime = 2000; // 2s filtering
  const llmTime = 5000;      // 5s LLM
  const excelTime = 1000;    // 1s Excel

  return baseTime + (ufCount * perUfTime) + filteringTime + llmTime + excelTime;
};

// Usage:
const totalEstimatedMs = estimateTotalTime(ufsSelecionadas.size);
const progress = calculateProgress(elapsedMs, totalEstimatedMs, currentStage);
```

**Calibration:**
- After Sprint 1 deploys, @analyst collects real timing data from backend logs
- Update `perUfTime` constant based on actual averages
- 80% accuracy is sufficient for UX improvement

---

#### Component Implementation

```typescript
// components/EnhancedLoadingProgress.tsx
interface Props {
  progress: number;        // 0-100
  currentStage: SearchStage;
  statesProcessed: number; // 5/27
  totalStates: number;     // 27
  estimatedTimeRemaining: number; // ms
  resultsFound: number;    // Early preview count
}

const EnhancedLoadingProgress: React.FC<Props> = ({
  progress,
  currentStage,
  statesProcessed,
  totalStates,
  estimatedTimeRemaining,
  resultsFound
}) => {
  const stageLabels = {
    'initiating': 'Iniciando busca...',
    'fetching': `Consultando PNCP (${statesProcessed}/${totalStates} estados)`,
    'filtering': 'Filtrando resultados...',
    'summarizing': 'Gerando resumo executivo...',
    'generating_excel': 'Preparando planilha Excel...'
  };

  return (
    <div className="mt-6 p-6 bg-surface-1 rounded-card">
      <h3 className="text-lg font-semibold mb-2">🔍 Buscando Licitações...</h3>

      {/* Progress Bar */}
      <div className="w-full bg-surface-2 rounded-full h-4 mb-3">
        <div
          className="bg-brand-blue h-4 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      <p className="text-base font-medium text-ink-secondary mb-1">
        {stageLabels[currentStage]}
      </p>

      <div className="flex justify-between text-sm text-ink-muted">
        <span>⏱️ Tempo estimado: ~{Math.ceil(estimatedTimeRemaining / 1000)}s</span>
        {resultsFound > 0 && (
          <span>✅ Já encontradas {resultsFound} licitações brutas</span>
        )}
      </div>

      {/* Educational Tips */}
      <div className="mt-4 pt-4 border-t border-strong">
        <p className="text-sm text-ink-muted">
          💡 <strong>Enquanto aguarda:</strong> Quanto mais estados selecionados,
          mais tempo leva. Filtros inteligentes eliminam resultados irrelevantes
          automaticamente.
        </p>
      </div>
    </div>
  );
};
```

---

#### Implementation Plan

**Day 1: Backend Logging Enhancement (Optional)**
- Add structured logging for timing data (if not already complete)
- Log: `logger.info("UF processed", extra={"uf": "SP", "elapsed_ms": 1234, "raw_count": 45})`

**Day 2: Frontend Component**
- Build `<EnhancedLoadingProgress>` component
- Implement estimated progress algorithm
- Test with various UF counts (1 state vs. 27 states)

**Day 3: Integration & Polish**
- Replace existing `<LoadingProgress>` in page.tsx
- Add loading skeleton (optional enhancement)
- Accessibility testing (screen readers, keyboard)

**Effort Breakdown:**
- Backend logging (if needed): 4 hours (0.5 SP)
- Component implementation: 12 hours (1.5 SP)
- Progress algorithm: 8 hours (1 SP)
- Integration + Testing: 16 hours (2 SP)
- **Total:** 40 hours (5 SP) → Rounded to **8 SP** (includes buffer + polish)

---

#### Risk Mitigation

**Risk:** Estimated time is wildly inaccurate (user loses trust)
**Mitigation:**
- Set expectations in UI: "⏱️ Tempo **estimado**: ~45s" (emphasize "estimated")
- Add ±30% margin to estimate (better to overestimate and finish early)
- Post-deploy: Collect real timing data, recalibrate constants

**Risk:** Search takes longer than expected (progress bar "stalls")
**Mitigation:**
- Progress never goes backwards
- After 100% is reached, show "Finalizando..." instead of staying at 100%
- If time exceeds 2x estimate, show message: "Busca está demorando mais que o esperado. Aguarde mais um momento..."

---

### Feature #3: Interactive Onboarding

**Effort:** 8 story points (3 days)
**Complexity:** MEDIUM
**Risk:** LOW
**Owner:** @dev (frontend) + @ux-design-expert

#### Technical Requirements

**Frontend:**
- 3-step modal wizard
- localStorage flag for completion tracking
- Interactive demo with real search
- Tooltip library integration

**Backend:**
- No changes needed

---

#### Library Choice: Intro.js vs. Shepherd.js vs. Custom

| Criterion | Intro.js | Shepherd.js | Custom Modal | Decision |
|-----------|----------|-------------|--------------|----------|
| **Bundle Size** | ⚠️ 12KB gzipped | ✅ 8KB gzipped | ✅ 5KB custom | Intro.js (acceptable) |
| **Flexibility** | ⚠️ Tooltip-only (no modals) | ✅ Modals + tooltips | ✅ Full control | Shepherd.js |
| **TypeScript Support** | ⚠️ Community types | ✅ Official types | ✅ Full control | Shepherd.js |
| **Ease of Use** | ✅ Simple API | ✅ Simple API | ❌ Build from scratch | Tie |
| **Accessibility** | ✅ WCAG 2.1 AA | ✅ WCAG 2.1 AA | ⚠️ Must implement manually | Tie |
| **Documentation** | ✅ Excellent | ✅ Excellent | N/A | Tie |
| **Community** | ✅ 6.2k stars | ✅ 12k stars | N/A | Shepherd.js |

**Decision:** ✅ **Shepherd.js** (best balance of features, size, and TypeScript support)

**Fallback:** If Shepherd.js is too complex, use **Intro.js** (simpler, tooltip-focused)

---

#### Implementation Plan

**Step 1: Install Shepherd.js**
```bash
npm install shepherd.js
npm install --save-dev @types/shepherd.js
```

**Step 2: Create Onboarding Hook (hooks/useOnboarding.ts)**
```typescript
import Shepherd from 'shepherd.js';
import 'shepherd.js/dist/css/shepherd.css';

export const useOnboarding = () => {
  const startOnboarding = () => {
    const tour = new Shepherd.Tour({
      useModalOverlay: true,
      defaultStepOptions: {
        classes: 'shadow-lg bg-surface-0 text-ink',
        scrollTo: true,
        cancelIcon: {
          enabled: true
        }
      }
    });

    // Step 1: Welcome
    tour.addStep({
      id: 'welcome',
      title: '🎉 Bem-vindo ao DescompLicita!',
      text: `
        <p>Encontre oportunidades de licitações públicas de forma rápida e descomplicada.</p>
        <ul>
          <li>✅ Busca em 27 estados simultaneamente</li>
          <li>✅ Filtros inteligentes eliminam ruído</li>
          <li>✅ Resumo executivo gerado por IA</li>
        </ul>
      `,
      buttons: [
        {
          text: 'Pular tutorial',
          action: tour.cancel,
          secondary: true
        },
        {
          text: 'Vamos começar! →',
          action: tour.next
        }
      ]
    });

    // Step 2: Interactive Demo (trigger real search)
    tour.addStep({
      id: 'demo',
      title: '📚 Vamos fazer uma busca exemplo',
      text: `
        <p>Vou buscar licitações de <strong>Vestuário</strong> nos estados do
        <strong>Sul</strong> nos últimos 7 dias.</p>
        <button id="execute-demo-search" class="btn-primary">
          🔍 Executar Busca Exemplo
        </button>
      `,
      attachTo: { element: '#search-form', on: 'bottom' },
      buttons: [
        {
          text: '← Voltar',
          action: tour.back
        },
        {
          text: 'Próximo passo →',
          action: tour.next
        }
      ],
      when: {
        show: () => {
          // Pre-fill form with demo params
          setUfsSelecionadas(new Set(['SC', 'PR', 'RS']));
          setSetorId('vestuario');
          // Bind button click
          document.getElementById('execute-demo-search')?.addEventListener('click', buscar);
        }
      }
    });

    // Step 3: Your Turn
    tour.addStep({
      id: 'your-turn',
      title: '🎯 Agora é sua vez!',
      text: `
        <p>Faça sua primeira busca personalizada. Escolha os estados e setor que te interessam.</p>
        <p class="text-sm text-ink-muted mt-2">💡 Dica: Comece com 3-5 estados para resultados rápidos.</p>
      `,
      attachTo: { element: '#search-form', on: 'top' },
      buttons: [
        {
          text: '← Voltar',
          action: tour.back
        },
        {
          text: 'Fazer minha busca!',
          action: () => {
            tour.complete();
            localStorage.setItem('onboarding_completed', 'true');
          }
        }
      ]
    });

    tour.start();
  };

  return { startOnboarding };
};
```

**Step 3: Trigger on First Visit (app/page.tsx)**
```typescript
const { startOnboarding } = useOnboarding();

useEffect(() => {
  const completed = localStorage.getItem('onboarding_completed');
  const searchCount = Number(localStorage.getItem('search_count') || 0);

  if (!completed && searchCount === 0) {
    // Delay 1s to let page load fully
    setTimeout(startOnboarding, 1000);
  }
}, []);
```

---

#### Custom Styling (Tailwind)

```css
/* globals.css */
.shepherd-element {
  @apply bg-surface-0 text-ink border border-strong rounded-card shadow-2xl;
}

.shepherd-title {
  @apply text-xl font-bold font-display text-brand-navy;
}

.shepherd-text {
  @apply text-base text-ink-secondary;
}

.shepherd-button {
  @apply px-4 py-2 rounded-button font-medium transition-colors;
}

.shepherd-button-primary {
  @apply bg-brand-navy text-white hover:bg-brand-blue-hover;
}

.shepherd-button-secondary {
  @apply bg-surface-2 text-ink-muted hover:bg-surface-1;
}
```

---

#### Implementation Plan

**Day 1: Shepherd.js Setup**
- Install library
- Create `useOnboarding` hook
- Basic 3-step tour (no real search yet)

**Day 2: Interactive Demo**
- Integrate demo search (pre-fill form, trigger buscar())
- Handle search completion (move to Step 3)
- Edge cases (what if demo search fails?)

**Day 3: Polish & Testing**
- Custom Tailwind styling
- Mobile responsive
- Accessibility (keyboard navigation, screen reader)
- Skip logic (localStorage flag)

**Effort Breakdown:**
- Shepherd.js integration: 8 hours (1 SP)
- Interactive demo logic: 12 hours (1.5 SP)
- Styling + Polish: 12 hours (1.5 SP)
- Testing + Accessibility: 8 hours (1 SP)
- **Total:** 40 hours (5 SP) → Rounded to **8 SP** (includes buffer)

---

#### Risk Mitigation

**Risk:** User skips onboarding, never learns features
**Mitigation:**
- Re-show onboarding on 3rd visit if user has 0 successful searches
- Add "Help" icon in header (re-triggers onboarding)
- Track completion rate via analytics (adjust flow if <50%)

**Risk:** Demo search fails (PNCP API down, etc.)
**Mitigation:**
- Fallback to pre-loaded results (mock data for demo only)
- Show message: "Demo indisponível. Use formulário abaixo para sua busca real."

---

## 3. Work Allocation & Team Structure

### Team Composition (9 Agents)

**Product & Process (4 agents):**
- @po - Product Owner (already completed prioritization)
- @analyst - Business Analyst (already completed baseline analysis)
- @sm - Scrum Master (will facilitate sprint planning next)
- @pm - Engineering Manager (this document)

**Technical Delivery (5 agents):**
- @architect - Technical Architect (architecture reviews, ADRs)
- @dev - Full Stack Developer (implementation lead)
- @ux-design-expert - UX Designer (already completed design concepts)
- @qa - QA Engineer (testing, quality gates)
- @devops - DevOps Engineer (CI/CD, deployment)

---

### Work Allocation Matrix

| Feature | Lead | Support | Effort | Dependencies |
|---------|------|---------|--------|--------------|
| **Analytics Tracking** | @dev (frontend) | @analyst | 1 SP | None |
| **Saved Searches** | @dev (full-stack) | @architect | 13 SP | None |
| **Performance Feedback** | @dev (frontend) | @ux-design-expert | 8 SP | Backend logging (if enhanced) |
| **Interactive Onboarding** | @dev (frontend) | @ux-design-expert | 8 SP | Saved Searches (demo uses real search) |
| **Testing & QA** | @qa | @dev | 5 SP | All features complete |
| **Deployment** | @devops | @pm | 2 SP | QA sign-off |
| **TOTAL** | | | **37 SP** | |

**Note:** 37 SP > 30 SP committed (includes testing & deployment overhead)

---

### Parallelization Strategy

**Week 1 (Day 1-7):**
```
Day 1-2:
  @dev: Analytics Tracking (1 SP) → COMPLETE
  @architect: Saved Searches architecture review (0.5 SP)

Day 3-5:
  @dev: Saved Searches implementation (13 SP) → IN PROGRESS
  @ux-design-expert: Onboarding wireframes polish (0.5 SP)

Day 6-7:
  @dev: Performance Feedback implementation (8 SP) → START
  @dev: Onboarding implementation (8 SP) → PARALLEL (different dev if 2+ devs available)
```

**Week 2 (Day 8-14):**
```
Day 8-10:
  @dev: Complete Performance + Onboarding (8 + 8 = 16 SP) → FINISH
  @qa: Start testing Analytics + Saved Searches (2 SP)

Day 11-12:
  @qa: Test all features (5 SP total) → COMPLETE
  @dev: Bugfixes from QA (2-3 SP buffer)

Day 13:
  @devops: Deploy to staging (1 SP)
  @qa: Smoke tests in staging (1 SP)

Day 14:
  @devops: Deploy to production (1 SP)
  @sm + @po: Sprint review & retrospective
```

---

### Developer Allocation (if >1 dev available)

**If 2 developers:**
- **Dev A:** Analytics + Saved Searches + Performance (22 SP)
- **Dev B:** Onboarding + Bugfixes (8 + 3 SP = 11 SP)

**If 1 developer:**
- Sequential: Analytics → Saved Searches → Performance → Onboarding
- Risk: Tight timeline, less buffer

**Recommendation:** If only 1 dev available, consider dropping Onboarding to SHOULD HAVE (defer to Week 2 decision point)

---

## 4. Technical Risks & Mitigations

### Risk #1: localStorage Quota Exceeded

**Likelihood:** LOW (5%)
**Impact:** MEDIUM (users lose saved searches)
**Mitigation:**
- Auto-delete oldest non-favorite search when quota hit
- Warning in UI about browser data clearing
- Future: Migrate to backend DB (Sprint 2)

---

### Risk #2: Estimated Progress Inaccurate

**Likelihood:** MEDIUM (30%)
**Impact:** LOW (UX is still better than current generic loading)
**Mitigation:**
- Set user expectations ("estimated", not "exact")
- Add ±30% margin to estimate
- Post-deploy calibration with real data
- Fallback: If widely inaccurate, show "Searching..." without % (still better than current)

---

### Risk #3: Shepherd.js Library Conflicts

**Likelihood:** LOW (10%)
**Impact:** MEDIUM (onboarding broken)
**Mitigation:**
- Test Shepherd.js integration in isolated branch first
- Fallback: Use Intro.js (simpler, more stable)
- Second fallback: Custom modal (no library dependency)

---

### Risk #4: PNCP API Downtime During Sprint

**Likelihood:** LOW (15%) - PNCP API is generally stable
**Impact:** HIGH (can't test real searches)
**Mitigation:**
- Mock PNCP responses for frontend testing
- Backend has retry logic already (main.py:374-386)
- Test with staging/dev PNCP endpoint if available

---

### Risk #5: Team Availability (Sick Leave, Blockers)

**Likelihood:** MEDIUM (20%)
**Impact:** HIGH (delays delivery)
**Mitigation:**
- 40-50% buffer in story points (30 committed, 50-55 capacity)
- Cross-training: @architect can implement if @dev blocked
- Daily standups: @sm escalates blockers immediately

---

## 5. Dependencies & Blockers

### External Dependencies

1. **Mixpanel API Key** - Required for analytics
   - **Owner:** @pm or @devops
   - **Timeline:** Day 1 (before dev starts)
   - **Blocker Risk:** LOW (free tier signup takes 5min)

2. **Backend Logging Enhancement** - Optional for better progress accuracy
   - **Owner:** @dev (backend)
   - **Timeline:** Day 1-2 (parallel with analytics)
   - **Blocker Risk:** LOW (not critical path)

3. **Design Assets (Figma)** - Optional high-fidelity mockups
   - **Owner:** @ux-design-expert
   - **Timeline:** Day 1-2 (can work ahead)
   - **Blocker Risk:** NONE (text specs in this doc are sufficient)

---

### Internal Dependencies

```
Analytics Tracking (Priority #0)
  ↓ (no dependency, can start immediately)
  ├─ Saved Searches (uses analytics events)
  ├─ Performance Feedback (uses analytics events)
  └─ Onboarding (uses analytics events)

Saved Searches
  ↓ (Onboarding demo uses saved search logic)
  └─ Onboarding (demo executes real search)

Performance Feedback
  ↓ (independent, no blockers)
  └─ (no dependents)
```

**Critical Path:** Analytics → Saved Searches → Onboarding
**Parallel Path:** Performance Feedback (can be done simultaneously)

---

## 6. Quality Gates & Definition of Done

### Feature-Level DoD

**For each MUST HAVE feature:**
- ✅ Code complete (all acceptance criteria met)
- ✅ Unit tests written (coverage ≥70% backend, ≥60% frontend)
- ✅ Integration tests pass (E2E for critical flows)
- ✅ Accessibility tested (WCAG 2.1 AA compliance)
- ✅ Mobile responsive (tested on iOS Safari + Android Chrome)
- ✅ Code reviewed by @architect (for architecture) and @pm (for code quality)
- ✅ QA sign-off (@qa validates against acceptance criteria)
- ✅ No P0/P1 bugs (P2 acceptable if documented)

---

### Sprint-Level DoD

**For Value Sprint 01:**
- ✅ All MUST HAVE features deployed to production
- ✅ Analytics tracking live and collecting data
- ✅ Metrics dashboard configured (Mixpanel)
- ✅ Performance benchmarks met:
  - Page load <2s (Lighthouse score)
  - Search complete <120s (99th percentile)
- ✅ No regressions (existing features still work)
- ✅ Rollback plan tested (can revert if needed)
- ✅ Sprint retrospective completed (lessons learned documented)

---

## 7. Deployment Strategy

### Staging Deployment (Day 13)

**Environment:** Vercel preview deployment (frontend) + staging backend
**Smoke Tests:**
1. Analytics events firing (check Mixpanel Live View)
2. Saved searches persist across browser refresh
3. Loading state shows progress (even if estimated)
4. Onboarding triggers on first visit
5. Search functionality unchanged (no regressions)

**Approval:** @qa + @pm sign-off required

---

### Production Deployment (Day 14)

**Strategy:** Blue-Green Deployment (Vercel supports this natively)
**Steps:**
1. Deploy frontend to Vercel production
2. Deploy backend to production (if backend changes exist)
3. Monitor error rates for 1 hour (Vercel Analytics + backend logs)
4. If error rate >5% → Rollback to previous version
5. If stable → Announce to users (email, in-app banner)

**Rollback Plan:**
- Vercel: `vercel rollback` (instant)
- Backend: Revert Git commit + redeploy
- Time to rollback: <5 minutes

---

## 8. Success Metrics (Technical)

### Sprint Velocity

**Target:** 30 story points delivered (MUST HAVE)
**Stretch:** 40-45 points (MUST HAVE + 1-2 SHOULD HAVE)
**Acceptable:** 25 points (MUST HAVE minus Onboarding)

**Measurement:** Burn-down chart (tracked by @sm in daily standups)

---

### Code Quality

**Targets:**
- Test coverage: ≥70% backend, ≥60% frontend
- Lighthouse score: ≥90 (Performance, Accessibility, Best Practices)
- Bundle size increase: <50KB gzipped (Mixpanel + Shepherd.js combined)
- Zero P0 bugs at launch

**Measurement:** CI/CD automated checks (coverage reports, Lighthouse CI)

---

### User-Facing Metrics (Post-Deploy)

**Tracked via Mixpanel:**
- Analytics events firing: >95% of searches tracked
- Saved searches usage: >30% of returning users click history dropdown
- Onboarding completion rate: >50% (finish all 3 steps)
- Time to first search (with onboarding): <90s average

**Validation:** @analyst reviews metrics on Day 17-20 (3-7 days post-deploy)

---

## 9. Post-Sprint Handoff

### Documentation Deliverables

1. **Technical Implementation Guide** (for future devs)
   - localStorage schema
   - Analytics event catalog
   - Component architecture

2. **Runbook** (for @devops)
   - Deployment steps
   - Rollback procedure
   - Monitoring dashboards

3. **User Guide** (for support/sales)
   - How to use saved searches
   - Understanding loading feedback
   - Onboarding tutorial re-trigger

---

### Knowledge Transfer

**@dev → Future Developers:**
- Code walkthrough session (1 hour)
- README updates with new features
- Inline code comments for complex logic

**@architect → Team:**
- ADR (Architecture Decision Record) for localStorage choice
- Future roadmap: Backend DB migration plan

---

## 10. Next Steps (Immediate Actions)

### Day 1 (Today):

1. **@pm:** Finalize Mixpanel account setup
   - Create free tier account
   - Get API token
   - Share with @dev

2. **@sm:** Kickoff Sprint Planning meeting
   - Present this feasibility doc
   - Create stories in backlog (use MoSCoW + UX Design docs as specs)
   - Assign owners

3. **@dev:** Start Analytics Tracking implementation
   - Install Mixpanel SDK
   - Instrument 8 events
   - Test in dev environment

4. **@architect:** Review Saved Searches architecture
   - localStorage schema approval
   - Future backend migration plan
   - Document ADR

---

### Day 2-3:

5. **@dev:** Continue Saved Searches implementation
   - `useSavedSearches` hook
   - `<SearchHistoryDropdown>` component
   - Integration with form

6. **@qa:** Prepare test plan
   - Test cases for each feature
   - Accessibility checklist
   - Staging environment validation

7. **@ux-design-expert:** Finalize onboarding copy
   - Review Step 1-3 text with @po
   - Mobile responsive design specs

---

### Day 7 (Checkpoint):

8. **@sm + @po:** Velocity review meeting
   - Actual vs. planned story points
   - **GO/NO-GO decision on SHOULD HAVE scope**
   - Adjust Week 2 plan if needed

---

## Conclusion

**Technical Feasibility:** ✅ **CONFIRMED**

**All MUST HAVE features are technically feasible within 2-week sprint with identified mitigations for risks.**

**Key Technical Decisions:**
1. ✅ Mixpanel for analytics (better product analytics than GA4)
2. ✅ localStorage for saved searches (MVP), backend DB deferred to Sprint 2
3. ✅ Estimated progress (frontend-only), polling upgrade in future sprint
4. ✅ Shepherd.js for onboarding (best balance of features + TypeScript support)

**Capacity Management:**
- Committed: 30 SP (MUST HAVE)
- Capacity: 50-55 SP
- Buffer: 40-50% (healthy safety margin)

**Risks:** 🟡 MEDIUM (all have mitigations)

**Recommendation:** ✅ **PROCEED WITH SPRINT**

**Next Agent:** @sm (Scrum Master) for Sprint Planning

---

**Report Status:** ✅ COMPLETE
**Signed:** @pm (Morgan)
**Date:** 2026-01-29
