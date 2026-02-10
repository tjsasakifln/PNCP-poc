# Quick Fix Guide: Search State Persistence

**Time to implement:** 4 hours
**Difficulty:** Easy
**Risk:** Low
**Impact:** High

---

## Problem in 30 Seconds

Users search → see results → click login → **lose everything** → must search again

**Fix:** Save state to sessionStorage before login, restore after auth

---

## Implementation Checklist

### Step 1: Create Persistence Utility (30 min)

**Create:** `frontend/lib/searchStatePersistence.ts`

Copy this file exactly as shown in `state-persistence-recommendations.md` Section "Step 1"

**What it does:**
- `saveSearchStateForAuth()` - Saves current state to sessionStorage
- `restoreSearchStateAfterAuth()` - Loads saved state, checks expiration
- `clearSavedSearchState()` - Cleanup
- `hasPendingSearchState()` - Check if state exists

---

### Step 2: Update Search Page (2 hours)

**File:** `frontend/app/buscar/page.tsx`

**2.1 Add Import (line ~35)**
```typescript
import {
  saveSearchStateForAuth,
  restoreSearchStateAfterAuth,
  clearSavedSearchState
} from '@/lib/searchStatePersistence';
```

**2.2 Add Restoration Banner State (line ~320)**
```typescript
const [restorationMessage, setRestorationMessage] = useState<{
  type: 'success' | 'info';
  message: string;
} | null>(null);
```

**2.3 Add Restoration Effect (line ~425, after other useEffects)**
```typescript
// Restore search state after authentication
useEffect(() => {
  const shouldRestore = searchParams.get('restore_state') === 'true';

  if (shouldRestore && !result) {
    const restoredState = restoreSearchStateAfterAuth();

    if (restoredState) {
      // Restore form
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

      // Restore results if available
      if (restoredState.result && restoredState.downloadId) {
        setResult(restoredState.result);
        setRestorationMessage({
          type: 'success',
          message: 'Seus resultados foram restaurados com sucesso!',
        });

        trackEvent('search_state_restored', {
          age_minutes: Math.floor((Date.now() - restoredState.timestamp) / 60000),
          has_results: true,
        });
      } else {
        // Form restored, but results expired
        setRestorationMessage({
          type: 'info',
          message: 'Sua busca foi restaurada. Clique em "Buscar" para atualizar os resultados.',
        });

        trackEvent('search_state_restored', {
          age_minutes: Math.floor((Date.now() - restoredState.timestamp) / 60000),
          has_results: false,
          form_only: true,
        });
      }

      // Auto-hide banner after 5 seconds
      setTimeout(() => setRestorationMessage(null), 5000);

      // Clean up
      clearSavedSearchState();
    } else {
      trackEvent('search_state_restore_failed', {
        reason: 'expired_or_missing',
      });
    }
  }
}, [searchParams, result]);
```

**2.4 Find Login Button in Results Section (search for "Login para baixar")**

**Old code:**
```typescript
<Link href="/login" className="...">
  <Lock className="h-5 w-5" />
  Login para baixar resultados
</Link>
```

**New code:**
```typescript
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

      router.push('/login?return_to=buscar&restore_state=true');
    } else {
      // Fallback if save fails
      router.push('/login?return_to=buscar');
    }
  }}
  className="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white rounded-button hover:bg-brand-blue-hover transition-colors"
>
  <Lock className="h-5 w-5" />
  Login para baixar resultados
</button>
```

**Note:** You'll need to add this import if not already present:
```typescript
import { useRouter } from 'next/navigation';

// In component:
const router = useRouter();
```

**2.5 Add Restoration Banner JSX (at top of form, around line 1100)**
```typescript
{/* State restoration banner */}
{restorationMessage && (
  <div className={`
    mb-4 p-4 rounded-lg border flex items-center justify-between
    ${restorationMessage.type === 'success' ? 'bg-success-subtle border-success text-success' : ''}
    ${restorationMessage.type === 'info' ? 'bg-brand-blue-subtle border-brand-blue text-brand-navy' : ''}
  `}>
    <div className="flex items-center gap-3">
      {restorationMessage.type === 'success' && (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )}
      {restorationMessage.type === 'info' && (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )}
      <p className="text-sm font-medium">{restorationMessage.message}</p>
    </div>
    <button
      onClick={() => setRestorationMessage(null)}
      className="text-current hover:opacity-75"
      aria-label="Fechar notificação"
    >
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
)}
```

---

### Step 3: Update Auth Callback (30 min)

**File:** `frontend/app/auth/callback/page.tsx`

**Find the redirect logic** (search for `router.push` or navigation code)

**Add restore_state param preservation:**

```typescript
// After successful authentication:
const returnTo = searchParams.get('return_to') || 'buscar';
const restoreState = searchParams.get('restore_state');

// Build redirect URL
let redirectUrl = `/${returnTo}`;
if (restoreState === 'true') {
  redirectUrl += '?restore_state=true';
}

router.push(redirectUrl);
```

---

### Step 4: Test (1 hour)

**Manual Test:**
```
1. Open /buscar in incognito mode
2. Execute search (select SC, search Vestuário)
3. Wait for results
4. Open DevTools → Application → Session Storage
5. Click "Login para baixar"
6. Verify sessionStorage has 'smartlic_pending_search_state'
7. Complete Google OAuth
8. Verify redirect to /buscar?restore_state=true
9. ✅ CHECK: Results visible OR banner shown
10. ✅ CHECK: Form populated with SC, dates, Vestuário
11. Verify sessionStorage cleared (state removed)
```

**Edge Cases:**
```
Test 1: Expired state (wait 1 hour)
- Should restore form only
- Should show "click to update" banner

Test 2: Browser refresh during auth
- State should persist in sessionStorage
- Should restore after completing auth

Test 3: sessionStorage disabled
- Should fail gracefully
- Should navigate without restoration
```

---

## Expected Behavior

### Before Implementation
```
User: Search → Results → Login → ❌ Empty form → Re-search 😡
```

### After Implementation
```
User: Search → Results → Login → ✅ Results restored → Download 🎉
```

---

## Debugging

### Check sessionStorage
```javascript
// In browser console:
JSON.parse(sessionStorage.getItem('smartlic_pending_search_state'))

// Should show:
{
  result: { download_id: "...", total_filtrado: 15, ... },
  formState: { ufs: ["SC"], dataInicial: "2026-02-03", ... },
  timestamp: 1707598234567,
  expiresAt: 1707601834567
}
```

### Check URL params
```
After login click:
/login?return_to=buscar&restore_state=true ✅

After auth redirect:
/buscar?restore_state=true ✅
```

### Check analytics
```javascript
// Should fire these events:
1. search_state_saved_for_auth (on login click)
2. search_state_restored (on redirect)
```

---

## Common Issues

### Issue 1: State not saving
**Symptom:** sessionStorage empty after clicking login
**Cause:** saveSearchStateForAuth() not called
**Fix:** Verify button onClick handler is correct

### Issue 2: State not restoring
**Symptom:** Empty form after auth redirect
**Cause:** Missing restore_state URL param
**Fix:** Check auth callback preserves param

### Issue 3: Results expire
**Symptom:** Form restores but no results
**Cause:** download_id expired (>1 hour)
**Fix:** This is expected! Show "re-run" banner

### Issue 4: sessionStorage quota exceeded
**Symptom:** Save fails silently
**Cause:** Browser storage full (rare)
**Fix:** Graceful fallback already implemented

---

## Performance Impact

- **sessionStorage write:** <5ms
- **sessionStorage read:** <2ms
- **Page load impact:** Negligible
- **Bundle size increase:** ~2KB

✅ No performance concerns

---

## Browser Support

| Browser | sessionStorage | Status |
|---------|----------------|--------|
| Chrome 80+ | ✅ | Full support |
| Firefox 75+ | ✅ | Full support |
| Safari 13+ | ✅ | Full support |
| Edge 80+ | ✅ | Full support |
| IE 11 | ✅ | Full support |

---

## Rollback

If you need to disable:

**Option 1: Quick disable (no deploy)**
```typescript
// In searchStatePersistence.ts
export function saveSearchStateForAuth(...) {
  return false; // Disable immediately
}
```

**Option 2: Feature flag (recommended)**
```typescript
// In config or env
const ENABLE_STATE_PERSISTENCE = process.env.NEXT_PUBLIC_ENABLE_STATE_PERSISTENCE !== 'false';

// In code
if (ENABLE_STATE_PERSISTENCE) {
  saveSearchStateForAuth(...);
}
```

**Option 3: Full revert**
```bash
git revert <commit-hash>
git push origin main
```

---

## Success Criteria

After implementation, verify:
- ✅ State saves to sessionStorage on login click
- ✅ State restores after auth redirect
- ✅ Banner shows restoration status
- ✅ Form populated correctly
- ✅ Results visible (if not expired)
- ✅ Analytics events firing
- ✅ sessionStorage cleaned up

---

## What to Watch After Deploy

**First 1 hour:**
- Error rate (should not increase)
- `search_state_restored` event count
- User feedback/support tickets

**First 24 hours:**
- Conversion rate (should improve)
- sessionStorage quota errors (should be zero)
- Restoration success rate (target >90%)

**First week:**
- User re-search rate (should decrease)
- Time to first download (should decrease)
- Overall conversion funnel (should improve)

---

## Help

**If you get stuck:**
1. Check `state-persistence-recommendations.md` for full code
2. Look at working example: `lib/savedSearches.ts`
3. Test in incognito mode to avoid state pollution
4. Check browser console for errors

**Questions to ask:**
- Is sessionStorage enabled in browser?
- Is the URL param being passed correctly?
- Is the useEffect running? (add console.log)
- Is the state structure correct? (check sessionStorage)

---

**Quick Reference:**
- Full analysis: `free-user-search-flow-analysis.md`
- Implementation details: `state-persistence-recommendations.md`
- Business case: `EXECUTIVE-SUMMARY.md`
- This guide: `QUICK-FIX-GUIDE.md`

---

**Ready to implement?** Start with Step 1 and follow linearly. Total time: 4 hours.

Good luck! 🚀
