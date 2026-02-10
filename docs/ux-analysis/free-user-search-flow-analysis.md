# UX Flow Analysis: Free User Search Persistence Issues

**Date:** 2026-02-10
**Analyst:** Claude Sonnet 4.5 (Frontend Specialist)
**Focus:** Navigation state management and search result persistence
**Priority:** P0 - Blocking user experience

---

## Executive Summary

**Critical Finding:** The application has **NO persistent state management** for search results across page navigations. Search results are stored exclusively in React component state, which is lost on any navigation event.

**Impact:**
- Free users lose search results when navigating to login/signup pages
- Saved searches work correctly (localStorage-based) but search results do not persist
- Users must re-execute searches after authentication
- Poor UX for conversion funnel (landing → search → signup → **results lost**)

**Root Cause:** State management architecture relies on component-level state without URL params, sessionStorage, or global state for result persistence.

---

## User Journey Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FREE USER SEARCH JOURNEY                          │
└─────────────────────────────────────────────────────────────────────────┘

PHASE 1: LANDING & SEARCH INITIATION
┌──────────────┐      Next.js        ┌──────────────┐
│   / (root)   │─────Navigation──────>│/buscar (CSR) │
│ Landing Page │     Link click      │ Search Page  │
└──────────────┘                      └──────────────┘
                                              │
                                              │ User fills form:
                                              │ - UFs: Set<string>
                                              │ - Dates: string
                                              │ - Sector/Terms
                                              │ - Filters (status, modalidade, etc)
                                              │
                                              ▼
                                      ┌──────────────┐
                                      │ Click Search │
                                      │   Button     │
                                      └──────────────┘
                                              │
                                              │
PHASE 2: SEARCH EXECUTION                     │
┌─────────────────────────────────────────────┼─────────────────────────┐
│                                             │                         │
│  const buscar = async () => {               ▼                         │
│    setLoading(true);                ┌──────────────┐                  │
│    setResult(null);                 │ API Request  │                  │
│    // ... fetch /api/buscar          │ POST /buscar │                  │
│    const data = await response.json(); └─────────┘                    │
│    setResult(data); ◄─────────────────────┘                          │
│  }                                                                     │
│                                                                        │
│  STATE STORED IN:                                                     │
│  ├─ result: BuscaResult | null  ◄── COMPONENT STATE (volatile!)      │
│  ├─ ufsSelecionadas: Set<string>                                     │
│  ├─ dataInicial/dataFinal: string                                    │
│  ├─ searchMode: "setor" | "termos"                                   │
│  └─ All filter states                                                │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                              │
                                              │ Results displayed
                                              ▼
                                      ┌──────────────┐
                                      │   Results    │
                                      │   Rendered   │
                                      └──────────────┘
                                              │
                                              │
PHASE 3: CONVERSION ATTEMPT                   │
┌─────────────────────────────────────────────┼─────────────────────────┐
│                                             │                         │
│  User sees "Login para baixar" CTA          │                         │
│                                             ▼                         │
│                                     ┌──────────────┐                  │
│                                     │ Click Login  │                  │
│                                     │    Button    │                  │
│                                     └──────────────┘                  │
│                                             │                         │
│                                             │ Next.js Navigation      │
│                                             │ <Link href="/login">    │
│                                             │                         │
│  ❌ BREAKPOINT #1: FULL PAGE NAVIGATION      │                         │
│     - Component unmounts                    │                         │
│     - All React state LOST                  │                         │
│     - result = null                         │                         │
│     - No persistence mechanism              ▼                         │
│                                     ┌──────────────┐                  │
│                                     │ /login page  │                  │
│                                     │ (new mount)  │                  │
│                                     └──────────────┘                  │
│                                             │                         │
│                                             │ User authenticates      │
│                                             │ via Google OAuth        │
│                                             ▼                         │
│                                     ┌──────────────┐                  │
│                                     │/auth/callback│                  │
│                                     └──────────────┘                  │
│                                             │                         │
│                                             │ useRouter.push()        │
│  ❌ BREAKPOINT #2: REDIRECT AFTER AUTH       │                         │
│     - Redirects to /buscar                  │                         │
│     - Fresh component mount                 │                         │
│     - result = null (initial state)         ▼                         │
│                                     ┌──────────────┐                  │
│                                     │/buscar (NEW) │                  │
│                                     │  Empty form  │                  │
│                                     │NO RESULTS ❌ │                  │
│                                     └──────────────┘                  │
│                                                                        │
│  User must:                                                           │
│  1. Re-select UFs                                                     │
│  2. Re-select dates                                                   │
│  3. Re-select sector/terms                                            │
│  4. Click search AGAIN                                                │
│  5. Wait for API response AGAIN                                       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

PARALLEL FLOW: SAVED SEARCHES (WORKING CORRECTLY)
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  ✅ Saved searches persist because:                                    │
│                                                                        │
│  1. Search parameters stored in localStorage                          │
│     Key: "descomplicita_saved_searches"                               │
│                                                                        │
│  2. Data structure:                                                   │
│     {                                                                 │
│       id: uuid,                                                       │
│       name: string,                                                   │
│       searchParams: {                                                 │
│         ufs: string[],                                                │
│         dataInicial: string,                                          │
│         dataFinal: string,                                            │
│         searchMode: "setor" | "termos",                               │
│         setorId?: string,                                             │
│         termosBusca?: string                                          │
│       },                                                              │
│       createdAt: ISO timestamp,                                       │
│       lastUsedAt: ISO timestamp                                       │
│     }                                                                 │
│                                                                        │
│  3. Load on mount from localStorage                                   │
│  4. Populate form fields                                              │
│  5. User clicks search to get NEW results                             │
│                                                                        │
│  ⚠️ BUT: Results themselves NOT persisted!                             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## State Persistence Analysis

### Current State Management

| State Type | Storage Location | Persistence | Navigation Safe |
|------------|------------------|-------------|-----------------|
| **Search Results** | Component state (`result`) | ❌ None | ❌ Lost on unmount |
| **Form Inputs** | Component state | ❌ None | ❌ Lost on unmount |
| **UF Selection** | Component state (`Set<string>`) | ❌ None | ❌ Lost on unmount |
| **Date Range** | Component state | ❌ None | ❌ Lost on unmount |
| **Filters** | Component state (multiple) | ❌ None | ❌ Lost on unmount |
| **Saved Searches** | localStorage | ✅ Persistent | ✅ Survives navigation |
| **Theme** | localStorage | ✅ Persistent | ✅ Survives navigation |
| **Onboarding Step** | localStorage | ✅ Persistent | ✅ Survives navigation |
| **Filter Collapse** | localStorage | ✅ Persistent | ✅ Survives navigation |
| **Auth Session** | Supabase (cookies) | ✅ Persistent | ✅ Survives navigation |

### Code Evidence

**buscar/page.tsx (lines 315, 537, 549, 620, etc.)**
```typescript
const [result, setResult] = useState<BuscaResult | null>(null);
const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(
  new Set(["SC", "PR", "RS"])
);

// On ANY form change, results are cleared:
const toggleUf = (uf: string) => {
  // ...
  setResult(null); // ❌ Results cleared
};

const limparSelecao = () => {
  setUfsSelecionadas(new Set());
  setResult(null); // ❌ Results cleared
};
```

**No persistence layer for results:**
```typescript
// Search executes:
const buscar = async () => {
  setLoading(true);
  setResult(null); // Clear old results

  const response = await fetch("/api/buscar", { /* ... */ });
  const data = await response.json();

  setResult(data); // ❌ Only stored in component state!
  // NO localStorage.setItem()
  // NO sessionStorage.setItem()
  // NO URL params
  // NO global state
}
```

**Navigation triggers component unmount:**
```typescript
// Login button (multiple locations)
<Link href="/login"> // ❌ Full page navigation
  Login para baixar
</Link>

// After OAuth callback:
// auth/callback/page.tsx
const router = useRouter();
router.push('/buscar'); // ❌ New mount, state reset
```

---

## Identified Breakpoints

### Breakpoint #1: Login/Signup Navigation
**Location:** `/buscar` → `/login` or `/signup`
**Trigger:** User clicks login/signup buttons
**Method:** `<Link href="/login">` (Next.js client-side navigation)
**Impact:**
- Component unmounts completely
- All state variables reset to initial values
- `result` becomes `null`
- `ufsSelecionadas` resets to `Set(["SC", "PR", "RS"])`
- All filters reset to defaults

**Code Reference:**
```typescript
// buscar/page.tsx (lines displayed in results section)
{!session && result && (
  <Link href="/login" className="...">
    <Lock className="h-5 w-5" />
    Login para baixar resultados
  </Link>
)}
```

### Breakpoint #2: OAuth Callback Redirect
**Location:** `/auth/callback` → `/buscar`
**Trigger:** After successful Google OAuth authentication
**Method:** `router.push('/buscar')`
**Impact:**
- Fresh component mount with default state
- User sees empty form
- No indication of previous search
- Must re-execute entire search

**Code Reference:** Auth callback redirects without state preservation

### Breakpoint #3: Browser Refresh
**Location:** Any page refresh on `/buscar`
**Trigger:** F5, Ctrl+R, browser navigation
**Impact:**
- Complete page reload
- All React state lost
- Component remounts with default state

### Breakpoint #4: Back/Forward Navigation
**Location:** Browser history navigation
**Trigger:** Back button, forward button
**Impact:**
- Component may remount depending on Next.js cache
- State not guaranteed to persist

---

## URL Params Analysis

### Current Implementation

**URL Params Support:** ✅ Partial (for re-run searches)

**Implementation:**
```typescript
// buscar/page.tsx lines 254-292
useEffect(() => {
  if (urlParamsApplied) return;

  const ufsParam = searchParams.get('ufs');
  const dataInicialParam = searchParams.get('data_inicial');
  const dataFinalParam = searchParams.get('data_final');
  const modeParam = searchParams.get('mode');
  const setorParam = searchParams.get('setor');
  const termosParam = searchParams.get('termos');

  if (ufsParam) {
    const ufsArray = ufsParam.split(',').filter(uf => UFS.includes(uf));
    if (ufsArray.length > 0) {
      setUfsSelecionadas(new Set(ufsArray));
      // Populate form fields
    }
  }
}, [searchParams, urlParamsApplied]);
```

**What's Supported:**
- ✅ Form parameters can be loaded from URL
- ✅ Can populate UFs, dates, mode, sector, terms
- ✅ Analytics tracking for URL-loaded params

**What's Missing:**
- ❌ Results are NOT stored in URL
- ❌ URL is NOT updated after search execution
- ❌ No `download_id` in URL params
- ❌ User must re-execute search (API call required)

**Example URL (hypothetical):**
```
/buscar?ufs=SC,PR,RS&data_inicial=2026-02-03&data_final=2026-02-10&mode=setor&setor=vestuario
```

**Missing from URL:**
- Search results data
- Download ID
- Result statistics
- LLM summary

---

## localStorage/sessionStorage Usage

### Current localStorage Usage

| Key | Purpose | Data Type | Persistence |
|-----|---------|-----------|-------------|
| `bidiq-theme` | UI theme preference | `"light" \| "dark" \| "system"` | ✅ Permanent |
| `smartlic-location-filters` | Filter panel state | `"open" \| "closed"` | ✅ Permanent |
| `smartlic-advanced-filters` | Filter panel state | `"open" \| "closed"` | ✅ Permanent |
| `smartlic-onboarding-step` | Tutorial progress | `"0" \| "1" \| "2" \| "3"` | ✅ Permanent |
| `descomplicita_saved_searches` | Saved search params | `SavedSearch[]` | ✅ Permanent |

### What's NOT in localStorage

❌ **Search results** (`BuscaResult`)
❌ **Download ID** (expires after 1 hour server-side)
❌ **Current form state** (UFs, dates during active session)
❌ **Filter selections** (status, modalidades, valor range)
❌ **Last search timestamp**
❌ **Result preview data**

### sessionStorage Analysis

**Current Usage:** ❌ **ZERO** - Not used anywhere in the application

**Potential Use Cases:**
- Store search results for current session
- Preserve form state during navigation
- Cache download_id for quick access
- Store "pending auth" flag for post-login restoration

---

## React Component Lifecycle Issues

### State Management Pattern

**Architecture:** Component-level state only (no global state manager)

```typescript
// All state is local to HomePageContent component
function HomePageContent() {
  const [result, setResult] = useState<BuscaResult | null>(null);
  const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(...);
  const [dataInicial, setDataInicial] = useState(() => ...);
  // ... 30+ state variables

  // NO context provider
  // NO Redux/Zustand store
  // NO persistence layer

  return (/* JSX */);
}
```

### Component Lifecycle Events

```
┌─────────────────────────────────────────────────┐
│        COMPONENT LIFECYCLE & STATE LOSS         │
└─────────────────────────────────────────────────┘

MOUNT (/buscar first load)
├─ useState() initializes with defaults
├─ useEffect() runs (setores fetch, URL params)
├─ User interacts, state updates
└─ result populated from API

NAVIGATION (Link to /login)
├─ Component UNMOUNT triggered
├─ All state variables DESTROYED
│  ├─ result = null
│  ├─ ufsSelecionadas cleared
│  ├─ All filters reset
│  └─ Form data lost
└─ /login page mounts (different component tree)

RE-MOUNT (/buscar after login)
├─ useState() RE-INITIALIZES with defaults
│  ├─ result = null (again)
│  ├─ ufsSelecionadas = Set(["SC","PR","RS"])
│  └─ All state reset to initial
├─ useEffect() runs
│  ├─ Fetches setores again
│  ├─ Checks URL params (none present)
│  └─ No previous state restored
└─ User sees EMPTY form (❌ poor UX)
```

### No State Restoration Mechanism

**Missing Features:**
1. Pre-navigation state snapshot
2. Post-navigation state restoration
3. Temporary storage for auth flow
4. "Return to search" functionality
5. State hydration from persisted data

---

## Recommendations for Fixes

### Priority 1: Critical (P0) - Conversion Funnel

**Problem:** Users lose search results when navigating to login/signup

**Solution 1: sessionStorage for Pending Auth**
```typescript
// Before navigation to /login or /signup:
const handleLoginClick = () => {
  // Store current state in sessionStorage
  sessionStorage.setItem('pending_search_state', JSON.stringify({
    result: result,
    downloadId: result?.download_id,
    formState: {
      ufs: Array.from(ufsSelecionadas),
      dataInicial,
      dataFinal,
      searchMode,
      setorId,
      termosArray,
      filters: { status, modalidades, valorMin, valorMax, esferas, municipios }
    },
    timestamp: Date.now()
  }));

  // Navigate
  router.push('/login?return_to=buscar&restore=true');
};

// After auth callback, restore:
useEffect(() => {
  const shouldRestore = searchParams.get('restore');
  if (shouldRestore) {
    const stored = sessionStorage.getItem('pending_search_state');
    if (stored) {
      const state = JSON.parse(stored);
      // Restore form
      setUfsSelecionadas(new Set(state.formState.ufs));
      setDataInicial(state.formState.dataInicial);
      // ... restore all fields

      // Restore results
      setResult(state.result);

      // Clean up
      sessionStorage.removeItem('pending_search_state');
    }
  }
}, [searchParams]);
```

**Benefits:**
- ✅ Zero server changes needed
- ✅ Works for session duration
- ✅ Auto-cleans on tab close
- ✅ Preserves full state including results

**Risks:**
- sessionStorage size limits (~5MB)
- Download ID may expire (1 hour server TTL)
- Results may be stale

---

**Solution 2: URL Params + Auto Re-execute**
```typescript
// After successful search:
const buscar = async () => {
  // ... execute search
  const data = await response.json();
  setResult(data);

  // Update URL with search params
  const params = new URLSearchParams({
    ufs: Array.from(ufsSelecionadas).join(','),
    data_inicial: dataInicial,
    data_final: dataFinal,
    mode: searchMode,
    setor: searchMode === 'setor' ? setorId : '',
    termos: searchMode === 'termos' ? termosArray.join(' ') : '',
    auto_execute: 'true' // Flag for auto re-run
  });

  router.replace(`/buscar?${params.toString()}`, { shallow: true });
};

// On mount with auto_execute flag:
useEffect(() => {
  if (searchParams.get('auto_execute') === 'true' && !result) {
    // Form already populated from URL params
    // Automatically re-execute search
    buscar();
  }
}, [searchParams, result]);
```

**Benefits:**
- ✅ Shareable URLs
- ✅ Browser history friendly
- ✅ No storage limits
- ✅ Fresh results on restore

**Risks:**
- Requires API call on restore (quota consumption)
- Network dependent
- Slight delay for user

---

### Priority 2: High (P1) - UX Enhancement

**Problem:** No indication that results existed before navigation

**Solution: "Last Search" Indicator**
```typescript
// Store minimal metadata in localStorage
const saveLastSearch = () => {
  localStorage.setItem('last_search_meta', JSON.stringify({
    timestamp: Date.now(),
    ufs: Array.from(ufsSelecionadas),
    sector: sectorName,
    resultCount: result?.total_filtrado || 0,
    hasResults: !!result
  }));
};

// Show banner after auth redirect:
{lastSearchMeta && !result && (
  <div className="bg-brand-blue-subtle p-4 rounded">
    <p>Sua última busca: {lastSearchMeta.sector} em {lastSearchMeta.ufs.join(', ')}</p>
    <button onClick={restoreAndRerun}>Executar novamente</button>
  </div>
)}
```

---

### Priority 3: Medium (P2) - Long-term Architecture

**Problem:** No global state management for complex flows

**Solution: Implement Zustand Store**
```typescript
// stores/searchStore.ts
import create from 'zustand';
import { persist } from 'zustand/middleware';

interface SearchStore {
  currentSearch: {
    result: BuscaResult | null;
    formState: FormState;
  };
  setSearchResult: (result: BuscaResult) => void;
  clearSearchResult: () => void;
  restoreSearchState: () => void;
}

export const useSearchStore = create<SearchStore>()(
  persist(
    (set) => ({
      currentSearch: { result: null, formState: {} },
      setSearchResult: (result) => set({ currentSearch: { ...state, result } }),
      // ...
    }),
    {
      name: 'search-state-storage', // localStorage key
      partialize: (state) => ({
        // Only persist what's needed
        formState: state.currentSearch.formState
      })
    }
  )
);
```

**Benefits:**
- ✅ Centralized state management
- ✅ Built-in persistence
- ✅ DevTools support
- ✅ Type-safe
- ✅ Scales for future features

**Effort:** 1-2 days implementation + testing

---

## Missing Persistence Mechanisms Summary

| Mechanism | Current Status | Should Use For |
|-----------|----------------|----------------|
| **URL Params** | Partial (read-only) | Form inputs, search params |
| **localStorage** | Used for UI prefs | Saved searches, user preferences |
| **sessionStorage** | ❌ Not used | Temporary state during auth flow |
| **Global State** | ❌ Not used | Cross-component state sharing |
| **Context API** | Only for Auth/Theme | Could expand for search state |
| **Server State** | Not implemented | Cache results server-side by ID |

---

## Success Metrics

### After implementing fixes, measure:

1. **Conversion Rate**
   - % of users who complete search → signup → download
   - Target: +20% increase

2. **User Satisfaction**
   - Time to first successful download
   - % of users re-executing same search
   - Target: <5% re-execution rate

3. **Technical Metrics**
   - sessionStorage usage size
   - State restoration success rate
   - Page load performance impact

4. **Analytics Events**
   - `search_state_restored` (successful)
   - `search_state_lost` (failed restoration)
   - `manual_re_search_after_auth` (user had to redo)

---

## Testing Scenarios

### Test Case 1: Free User Conversion Flow
```
1. Navigate to /buscar
2. Execute search (SC, PR, 7 days, Vestuário)
3. Verify results displayed
4. Click "Login para baixar"
5. Complete Google OAuth
6. Verify redirected to /buscar
7. ✅ PASS: Results still visible OR auto re-executed
8. ❌ FAIL: Empty form, must search again
```

### Test Case 2: Browser Refresh
```
1. Execute search with results displayed
2. Press F5 (refresh page)
3. ✅ PASS: Form state or results restored
4. ❌ FAIL: Empty form
```

### Test Case 3: Back Button
```
1. Execute search
2. Navigate to /planos
3. Press browser back button
4. ✅ PASS: Search results visible
5. ❌ FAIL: Empty form
```

### Test Case 4: Session Timeout
```
1. Execute search
2. Wait for sessionStorage to persist
3. Close tab
4. Reopen /buscar in new tab (same session)
5. ✅ PASS: Last search indicator shown
6. ❌ FAIL: No indication of previous search
```

---

## File References

### Key Files for Implementation

| File | Purpose | Changes Needed |
|------|---------|----------------|
| `frontend/app/buscar/page.tsx` | Main search component | Add state persistence hooks |
| `frontend/lib/searchStatePersistence.ts` | New file | Implement persistence utilities |
| `frontend/hooks/useSearchState.ts` | New file | Custom hook for state management |
| `frontend/app/auth/callback/page.tsx` | OAuth redirect | Restore state after auth |
| `frontend/app/login/page.tsx` | Login page | Accept return_to param |
| `frontend/app/signup/page.tsx` | Signup page | Accept return_to param |

### Current Files Examined

- ✅ `frontend/app/buscar/page.tsx` (1784 lines, main search logic)
- ✅ `frontend/app/layout.tsx` (theme, analytics, auth providers)
- ✅ `frontend/hooks/useSavedSearches.ts` (working persistence example)
- ✅ `frontend/lib/savedSearches.ts` (localStorage implementation)
- ✅ `frontend/app/components/ThemeProvider.tsx` (localStorage example)
- ✅ `frontend/e2e-tests/search-flow.spec.ts` (test coverage)
- ✅ `frontend/e2e-tests/saved-searches.spec.ts` (persistence tests)

---

## Conclusion

The application has a **critical UX gap** where search results are lost during the conversion funnel (search → login → authenticated state). This is caused by:

1. **No persistence layer** for search results or active form state
2. **Component-level state only** that's destroyed on navigation
3. **Missing sessionStorage usage** for temporary state during auth
4. **URL params support exists** but doesn't include results or auto-execution

**Immediate action required:** Implement sessionStorage-based state preservation for the auth flow to prevent user frustration and improve conversion rates.

**Recommended approach:** Solution 1 (sessionStorage) for quick fix, followed by Solution 3 (Zustand) for long-term maintainability.

---

**Analysis completed by:** Claude Sonnet 4.5 (Frontend Specialist)
**Date:** 2026-02-10
**Confidence Level:** High (based on direct code analysis and E2E test examination)
