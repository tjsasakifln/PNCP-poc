# State Persistence Recommendations - Implementation Guide

**Priority:** P0 - Critical UX Issue
**Impact:** Conversion funnel blocking
**Effort:** 4-8 hours
**Risk:** Low (isolated changes)

---

## Quick Summary

**Problem:** Search results lost when free users navigate to login/signup
**Root Cause:** No persistence mechanism for search results across navigation
**Solution:** Implement sessionStorage-based state preservation

---

## Implementation Plan

### Phase 1: Immediate Fix (4 hours)

**Goal:** Preserve search results during auth flow using sessionStorage

#### Step 1: Create Persistence Utility (1 hour)

**File:** `frontend/lib/searchStatePersistence.ts`

```typescript
/**
 * Search State Persistence Utilities
 *
 * Provides functions to save/restore search state during authentication flows
 * Uses sessionStorage for temporary persistence (auto-clears on tab close)
 */

export interface PersistedSearchState {
  // Search results
  result: BuscaResult | null;
  downloadId: string | null;

  // Form state
  formState: {
    ufs: string[];
    dataInicial: string;
    dataFinal: string;
    searchMode: "setor" | "termos";
    setorId?: string;
    termosArray?: string[];

    // P0 Filters
    status: StatusLicitacao;
    modalidades: number[];
    valorMin: number | null;
    valorMax: number | null;

    // P1 Filters
    esferas: Esfera[];
    municipios: Municipio[];
    ordenacao: OrdenacaoOption;
  };

  // Metadata
  timestamp: number;
  expiresAt: number; // 1 hour TTL
}

const STORAGE_KEY = 'smartlic_pending_search_state';
const TTL_MS = 60 * 60 * 1000; // 1 hour

/**
 * Save current search state before navigating to auth
 */
export function saveSearchStateForAuth(state: {
  result: BuscaResult | null;
  ufsSelecionadas: Set<string>;
  dataInicial: string;
  dataFinal: string;
  searchMode: "setor" | "termos";
  setorId: string;
  termosArray: string[];
  status: StatusLicitacao;
  modalidades: number[];
  valorMin: number | null;
  valorMax: number | null;
  esferas: Esfera[];
  municipios: Municipio[];
  ordenacao: OrdenacaoOption;
}): boolean {
  try {
    const now = Date.now();
    const persistedState: PersistedSearchState = {
      result: state.result,
      downloadId: state.result?.download_id || null,
      formState: {
        ufs: Array.from(state.ufsSelecionadas),
        dataInicial: state.dataInicial,
        dataFinal: state.dataFinal,
        searchMode: state.searchMode,
        setorId: state.searchMode === 'setor' ? state.setorId : undefined,
        termosArray: state.searchMode === 'termos' ? state.termosArray : undefined,
        status: state.status,
        modalidades: state.modalidades,
        valorMin: state.valorMin,
        valorMax: state.valorMax,
        esferas: state.esferas,
        municipios: state.municipios,
        ordenacao: state.ordenacao,
      },
      timestamp: now,
      expiresAt: now + TTL_MS,
    };

    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(persistedState));
    console.log('[Persistence] Search state saved for auth flow');
    return true;
  } catch (error) {
    console.error('[Persistence] Failed to save search state:', error);
    return false;
  }
}

/**
 * Restore search state after authentication
 * Returns null if expired or not found
 */
export function restoreSearchStateAfterAuth(): PersistedSearchState | null {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (!stored) {
      console.log('[Persistence] No saved search state found');
      return null;
    }

    const state: PersistedSearchState = JSON.parse(stored);
    const now = Date.now();

    // Check expiration
    if (now > state.expiresAt) {
      console.warn('[Persistence] Search state expired');
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }

    // Check download_id validity (server TTL is also 1 hour)
    const age = now - state.timestamp;
    if (state.downloadId && age > 55 * 60 * 1000) {
      console.warn('[Persistence] Download ID likely expired, clearing result');
      state.result = null;
      state.downloadId = null;
    }

    console.log('[Persistence] Search state restored successfully', {
      age_minutes: Math.floor(age / 60000),
      has_result: !!state.result,
      ufs: state.formState.ufs,
    });

    return state;
  } catch (error) {
    console.error('[Persistence] Failed to restore search state:', error);
    sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

/**
 * Clear saved search state
 */
export function clearSavedSearchState(): void {
  sessionStorage.removeItem(STORAGE_KEY);
  console.log('[Persistence] Search state cleared');
}

/**
 * Check if there's a pending search state
 */
export function hasPendingSearchState(): boolean {
  const stored = sessionStorage.getItem(STORAGE_KEY);
  if (!stored) return false;

  try {
    const state: PersistedSearchState = JSON.parse(stored);
    return Date.now() <= state.expiresAt;
  } catch {
    return false;
  }
}
```

---

#### Step 2: Update Search Page to Save State (1 hour)

**File:** `frontend/app/buscar/page.tsx`

**Add import:**
```typescript
import {
  saveSearchStateForAuth,
  restoreSearchStateAfterAuth,
  clearSavedSearchState
} from '@/lib/searchStatePersistence';
```

**Add state restoration on mount:**
```typescript
// Add after other useEffect hooks (around line 425)
useEffect(() => {
  // Check for pending state restoration after auth
  const shouldRestore = searchParams.get('restore_state') === 'true';

  if (shouldRestore && !result) {
    const restoredState = restoreSearchStateAfterAuth();

    if (restoredState) {
      // Restore form state
      setUfsSelecionadas(new Set(restoredState.formState.ufs));
      setDataInicial(restoredState.formState.dataInicial);
      setDataFinal(restoredState.formState.dataFinal);
      setSearchMode(restoredState.formState.searchMode);

      if (restoredState.formState.setorId) {
        setSetorId(restoredState.formState.setorId);
      }
      if (restoredState.formState.termosArray) {
        setTermosArray(restoredState.formState.termosArray);
      }

      // Restore filters
      setStatus(restoredState.formState.status);
      setModalidades(restoredState.formState.modalidades);
      setValorMin(restoredState.formState.valorMin);
      setValorMax(restoredState.formState.valorMax);
      setEsferas(restoredState.formState.esferas);
      setMunicipios(restoredState.formState.municipios);
      setOrdenacao(restoredState.formState.ordenacao);

      // Restore results if available and not expired
      if (restoredState.result && restoredState.downloadId) {
        setResult(restoredState.result);

        // Track successful restoration
        trackEvent('search_state_restored', {
          age_minutes: Math.floor((Date.now() - restoredState.timestamp) / 60000),
          has_results: true,
          ufs: restoredState.formState.ufs,
        });
      } else {
        // Results expired, show notification to re-run
        // Track partial restoration
        trackEvent('search_state_restored', {
          age_minutes: Math.floor((Date.now() - restoredState.timestamp) / 60000),
          has_results: false,
          form_only: true,
        });
      }

      // Clean up sessionStorage
      clearSavedSearchState();

      // Remove restore_state param from URL
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('restore_state');
      router.replace(`/buscar?${newParams.toString()}`, { shallow: true });
    } else {
      // Track restoration failure
      trackEvent('search_state_restore_failed', {
        reason: 'expired_or_missing',
      });
    }
  }
}, [searchParams, result]);
```

**Update login/signup links to save state:**
```typescript
// Find login button in results section (around line 1700+)
// Replace:
<Link href="/login">Login para baixar</Link>

// With:
<button
  onClick={() => {
    // Save state before navigation
    const saved = saveSearchStateForAuth({
      result,
      ufsSelecionadas,
      dataInicial,
      dataFinal,
      searchMode,
      setorId,
      termosArray,
      status,
      modalidades,
      valorMin,
      valorMax,
      esferas,
      municipios,
      ordenacao,
    });

    if (saved) {
      trackEvent('search_state_saved_for_auth', {
        has_results: !!result,
        ufs: Array.from(ufsSelecionadas),
      });

      // Navigate with restore flag
      router.push('/login?return_to=buscar&restore_state=true');
    } else {
      // Fallback to direct navigation
      router.push('/login?return_to=buscar');
    }
  }}
  className="..."
>
  <Lock className="h-5 w-5" />
  Login para baixar resultados
</button>
```

---

#### Step 3: Update Auth Callback (30 min)

**File:** `frontend/app/auth/callback/page.tsx`

```typescript
// After successful auth, check for restore flag
const return_to = searchParams.get('return_to');
const should_restore = searchParams.get('restore_state') === 'true';

if (return_to === 'buscar') {
  // Preserve restore_state param in redirect
  const redirectUrl = should_restore
    ? '/buscar?restore_state=true'
    : '/buscar';

  router.push(redirectUrl);
} else {
  router.push('/buscar');
}
```

---

#### Step 4: Add User Feedback UI (1 hour)

**File:** `frontend/app/buscar/page.tsx`

**Add state for restoration banner:**
```typescript
const [restorationMessage, setRestorationMessage] = useState<{
  type: 'success' | 'info' | 'warning';
  message: string;
} | null>(null);
```

**Show banner after restoration:**
```typescript
// In restoration useEffect, after restoring state:
if (restoredState.result) {
  setRestorationMessage({
    type: 'success',
    message: 'Seus resultados de busca foram restaurados!',
  });
} else {
  setRestorationMessage({
    type: 'info',
    message: 'Sua busca foi restaurada. Clique em "Buscar" para atualizar os resultados.',
  });
}

// Auto-hide after 5 seconds
setTimeout(() => setRestorationMessage(null), 5000);
```

**Render banner in JSX:**
```typescript
{restorationMessage && (
  <div className={`
    mb-4 p-4 rounded-lg border
    ${restorationMessage.type === 'success' ? 'bg-success-subtle border-success' : ''}
    ${restorationMessage.type === 'info' ? 'bg-brand-blue-subtle border-brand-blue' : ''}
    ${restorationMessage.type === 'warning' ? 'bg-warning-subtle border-warning' : ''}
  `}>
    <div className="flex items-center justify-between">
      <p className="text-sm font-medium">{restorationMessage.message}</p>
      <button
        onClick={() => setRestorationMessage(null)}
        className="text-ink-muted hover:text-ink"
      >
        ×
      </button>
    </div>
  </div>
)}
```

---

#### Step 5: Add Analytics Tracking (30 min)

**Events to track:**

1. `search_state_saved_for_auth` - When state is saved before login
2. `search_state_restored` - When state is successfully restored
3. `search_state_restore_failed` - When restoration fails
4. `search_rerun_after_restore` - When user re-runs search after form restoration

**Implementation:** Already included in code snippets above

---

### Phase 2: Testing & Validation (2 hours)

#### Manual Testing Checklist

```
✅ Test Case 1: Free User Login Flow
1. Navigate to /buscar
2. Execute search (SC, PR, Vestuário)
3. Verify results displayed
4. Click "Login para baixar"
5. Complete Google OAuth
6. Verify redirect to /buscar with results OR form populated
7. PASS if results visible or "restore" banner shown

✅ Test Case 2: Expired Download ID
1. Execute search
2. Save state
3. Wait 1 hour (or manipulate timestamp in sessionStorage)
4. Login
5. Verify form restored but results cleared
6. Verify banner shows "click to update results"

✅ Test Case 3: Browser Refresh During Auth
1. Execute search
2. Click login
3. State saved in sessionStorage
4. Press F5 during OAuth flow
5. Complete OAuth
6. Verify state still restores

✅ Test Case 4: Multiple Tab Behavior
1. Execute search in Tab A
2. Click login (state saved)
3. Complete auth in Tab B
4. Return to Tab A
5. Verify state persists per tab

✅ Test Case 5: sessionStorage Full
1. Fill sessionStorage near quota
2. Try to save search state
3. Verify graceful fallback (direct navigation)
```

#### E2E Test Addition

**File:** `frontend/e2e-tests/search-state-persistence.spec.ts` (new file)

```typescript
import { test, expect } from '@playwright/test';
import { SearchPage } from './helpers/page-objects';
import { mockSearchAPI, mockSetoresAPI } from './helpers/test-utils';

test.describe('Search State Persistence', () => {
  test('should restore search results after login', async ({ page, context }) => {
    // Setup
    const searchPage = new SearchPage(page);
    await mockSetoresAPI(page);
    await mockSearchAPI(page, 'success');
    await searchPage.goto();

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');
    await searchPage.executeSearch();
    await expect(searchPage.executiveSummary).toBeVisible();

    // Verify sessionStorage has saved state
    const savedState = await page.evaluate(() => {
      return sessionStorage.getItem('smartlic_pending_search_state');
    });
    expect(savedState).toBeNull(); // Not saved yet

    // Click login (should save state)
    await page.click('text=Login para baixar');

    // Verify state was saved
    const savedStateAfterClick = await page.evaluate(() => {
      return sessionStorage.getItem('smartlic_pending_search_state');
    });
    expect(savedStateAfterClick).toBeTruthy();

    // Simulate OAuth success (mock)
    // In real test, would complete OAuth flow
    await page.goto('/buscar?restore_state=true');

    // Verify results restored or banner shown
    const banner = page.locator('text=restaurad');
    await expect(banner).toBeVisible();
  });
});
```

---

### Phase 3: Monitoring & Rollout (1 hour)

#### Analytics Dashboard

**Mixpanel Queries to Create:**

1. **State Restoration Success Rate**
   ```
   Event: search_state_restored
   Metric: count(distinct user_id)
   Filters: has_results = true
   ```

2. **Auth Flow Completion Rate**
   ```
   Funnel:
   1. search_completed
   2. search_state_saved_for_auth
   3. search_state_restored
   ```

3. **Restoration Failures**
   ```
   Event: search_state_restore_failed
   Breakdown by: reason
   ```

#### Success Metrics

**Targets:**
- State restoration success rate: >90%
- Conversion funnel completion: +15% improvement
- User re-search rate after auth: <10%

**Monitor for:**
- sessionStorage quota errors
- Restoration failures due to expiration
- Browser compatibility issues

---

## Risk Assessment

### Low Risk Items ✅

- sessionStorage well-supported (IE11+)
- Isolated changes to search page
- No backend changes required
- Easy rollback (remove feature flag)

### Medium Risk Items ⚠️

- sessionStorage quota limits (5-10MB depending on browser)
  - **Mitigation:** Graceful fallback to direct navigation

- Download ID expiration mismatch
  - **Mitigation:** Check timestamp, clear results if >55 minutes old

- Multi-tab confusion
  - **Mitigation:** sessionStorage is per-tab, expected behavior

### High Risk Items ❌

None identified

---

## Rollback Plan

### If Issues Detected

1. **Remove state save call** from login button
2. **Disable restoration** by checking feature flag
3. **Clear sessionStorage** for affected users

### Feature Flag Implementation

```typescript
// Add to config
const ENABLE_STATE_PERSISTENCE =
  process.env.NEXT_PUBLIC_ENABLE_STATE_PERSISTENCE !== 'false';

// Wrap save/restore calls
if (ENABLE_STATE_PERSISTENCE) {
  saveSearchStateForAuth(...);
}
```

---

## Alternative Approaches Considered

### 1. URL Params Only (Not Recommended)

**Pros:**
- No storage needed
- Shareable URLs

**Cons:**
- URL pollution (very long)
- Results not included (must re-execute)
- Security concerns (params visible in history)

**Decision:** Rejected due to UX impact (requires API re-call)

---

### 2. Server-Side Session Storage (Not Recommended)

**Pros:**
- No client storage limits
- More secure

**Cons:**
- Requires backend changes
- Adds latency
- Complexity for temporary state

**Decision:** Rejected as over-engineered for this use case

---

### 3. Global State Manager (Zustand/Redux) (Future Enhancement)

**Pros:**
- Professional architecture
- Scales for complex features
- DevTools support

**Cons:**
- Larger implementation effort (2 days)
- Not needed for this specific issue

**Decision:** Recommended for Phase 2 (long-term architecture)

---

## Next Steps

1. **Implement Phase 1** (4 hours)
   - Create persistence utility
   - Update search page
   - Update auth callback
   - Add UI feedback

2. **Test Phase 2** (2 hours)
   - Manual testing
   - E2E test creation
   - Edge case validation

3. **Monitor Phase 3** (1 hour)
   - Setup analytics
   - Monitor first 24 hours
   - Gather user feedback

4. **Iterate** based on metrics
   - Adjust TTL if needed
   - Enhance UI feedback
   - Consider Zustand migration

---

## Files to Create/Modify

### New Files
- ✅ `frontend/lib/searchStatePersistence.ts` (utility)
- ✅ `frontend/e2e-tests/search-state-persistence.spec.ts` (tests)

### Modified Files
- ✅ `frontend/app/buscar/page.tsx` (main changes)
- ✅ `frontend/app/auth/callback/page.tsx` (redirect logic)
- ⚠️ `frontend/app/login/page.tsx` (optional: show "returning to search" indicator)
- ⚠️ `frontend/app/signup/page.tsx` (optional: same as login)

### Total Effort
- **Implementation:** 4 hours
- **Testing:** 2 hours
- **Monitoring:** 1 hour
- **Total:** 7 hours

---

**Created by:** Claude Sonnet 4.5 (Frontend Specialist)
**Date:** 2026-02-10
**Status:** Ready for implementation
