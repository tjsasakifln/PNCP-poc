# Feature #1: Saved Searches - Testing Guide

**Feature:** Saved Searches & History
**Status:** Ready for QA
**Developer:** @dev (James - Builder)
**Date:** January 29, 2026

---

## Quick Start

### Running the Application

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access at: http://localhost:3000

---

## Test Scenarios

### Scenario 1: Save a New Search ✅

**Steps:**
1. Open http://localhost:3000
2. Configure search parameters:
   - Select UFs: SC, PR, RS
   - Set date range: Last 7 days
   - Search mode: "Setor" → "Vestuário e Uniformes"
3. Click "Buscar Vestuário e Uniformes"
4. Wait for results to load
5. Click "Salvar Busca" button (appears below search button)
6. Modal opens with default name: "Vestuário e Uniformes"
7. Modify name to: "Uniformes Sul do Brasil"
8. Click "Salvar"

**Expected Results:**
- ✅ Modal closes
- ✅ Badge appears on "Buscas Salvas" dropdown showing "1"
- ✅ No errors in console
- ✅ Analytics event logged: `saved_search_created`

**Analytics Event:**
```javascript
{
  event: 'saved_search_created',
  properties: {
    search_name: 'Uniformes Sul do Brasil',
    search_mode: 'setor',
    ufs: ['SC', 'PR', 'RS'],
    uf_count: 3,
    setor_id: 'vestuario',
    termos_count: 0,
    timestamp: '2026-01-29T...',
    environment: 'development'
  }
}
```

---

### Scenario 2: Load a Saved Search ✅

**Steps:**
1. Click "Buscas Salvas" dropdown in header
2. Verify dropdown shows saved search:
   - Name: "Uniformes Sul do Brasil"
   - Details: "vestuario • SC, PR, RS"
   - Timestamp: "há X min" (relative time)
3. Click on the saved search card
4. Verify form auto-fills:
   - UFs: SC, PR, RS selected
   - Date range matches original
   - Search mode: "Setor"
   - Sector: "Vestuário e Uniformes"

**Expected Results:**
- ✅ Dropdown closes
- ✅ All form fields correctly populated
- ✅ Current result clears (ready for new search)
- ✅ Analytics event logged: `saved_search_loaded`

**Analytics Event:**
```javascript
{
  event: 'saved_search_loaded',
  properties: {
    search_id: 'uuid-here',
    search_name: 'Uniformes Sul do Brasil',
    search_mode: 'setor',
    ufs: ['SC', 'PR', 'RS'],
    uf_count: 3,
    days_since_created: 0,
    timestamp: '2026-01-29T...',
    environment: 'development'
  }
}
```

---

### Scenario 3: Delete a Saved Search ✅

**Steps:**
1. Click "Buscas Salvas" dropdown
2. Hover over a saved search
3. Click trash icon on the right
4. Icon turns red with tooltip "Clique novamente para confirmar"
5. Click trash icon again
6. Search removed from list

**Expected Results:**
- ✅ Search disappears from list
- ✅ Badge count decreases (e.g., "1" → empty)
- ✅ If last search, empty state appears
- ✅ Analytics event logged: `saved_search_deleted`

**Analytics Event:**
```javascript
{
  event: 'saved_search_deleted',
  properties: {
    search_id: 'uuid-here',
    search_name: 'Uniformes Sul do Brasil',
    remaining_searches: 0,
    timestamp: '2026-01-29T...',
    environment: 'development'
  }
}
```

---

### Scenario 4: Maximum Capacity (10 Searches) ✅

**Steps:**
1. Save 10 different searches (vary UFs, sectors, dates)
2. After 10th search, verify badge shows "10"
3. Perform another search
4. Click "Salvar Busca" button

**Expected Results:**
- ✅ Button is disabled
- ✅ Button text: "Limite de buscas atingido"
- ✅ Tooltip: "Máximo de 10 buscas salvas atingido"
- ✅ Modal does NOT open

**Additional Test:**
1. Delete one search from dropdown
2. Verify button re-enables
3. Button text: "Salvar Busca"

---

### Scenario 5: Persistence Across Sessions ✅

**Steps:**
1. Save 3 searches with distinct names:
   - "Uniformes Sul"
   - "Alimentos SP"
   - "Informática DF"
2. Close browser tab completely
3. Close browser (optional, for thorough test)
4. Reopen browser and navigate to http://localhost:3000
5. Click "Buscas Salvas" dropdown

**Expected Results:**
- ✅ All 3 searches still present
- ✅ Badge shows "3"
- ✅ Timestamps updated correctly
- ✅ Load any search → form auto-fills correctly

---

### Scenario 6: Empty State ✅

**Steps:**
1. Clear all saved searches (click "Limpar todas" in dropdown)
2. Confirm deletion in browser alert
3. Dropdown remains open

**Expected Results:**
- ✅ Empty state displays:
  - Icon: Document/clipboard illustration
  - Text: "Nenhuma busca salva"
  - Subtext: "Suas buscas aparecerão aqui após realizar uma pesquisa"
- ✅ Badge disappears from trigger button

---

### Scenario 7: Custom Terms Search ✅

**Steps:**
1. Configure search:
   - Search mode: "Termos Específicos"
   - Add terms: "uniformes" (space) "fardamento" (space) "camisetas" (enter)
   - UFs: SP, RJ, MG
   - Date range: Last 30 days
2. Click "Buscar"
3. Wait for results
4. Click "Salvar Busca"
5. Name: "Uniformes Sudeste"
6. Click "Salvar"

**Expected Results:**
- ✅ Search saved successfully
- ✅ In dropdown, shows:
  - Name: "Uniformes Sudeste"
  - Details: "uniformes fardamento camisetas • SP, RJ, MG"
- ✅ Load search → custom terms restored as tags

**Analytics Event:**
```javascript
{
  event: 'saved_search_created',
  properties: {
    search_name: 'Uniformes Sudeste',
    search_mode: 'termos',
    ufs: ['SP', 'RJ', 'MG'],
    uf_count: 3,
    setor_id: null,
    termos_count: 3
  }
}
```

---

### Scenario 8: Relative Timestamps ✅

**Steps:**
1. Save a search
2. Immediately check timestamp → "agora"
3. Wait 5 minutes → "há 5 min"
4. Wait 1 hour → "há 1h"
5. Wait 24 hours → "ontem"
6. Wait 3 days → "há 3 dias"
7. Wait 7+ days → "22/01" (dd/mm format)

**Expected Results:**
- ✅ Timestamps update correctly in Portuguese
- ✅ Format matches Brazilian locale

---

### Scenario 9: Character Limit (50 chars) ✅

**Steps:**
1. Save a search
2. In name input, type a very long name:
   - "Uniformes e Fardamentos para Servidores Públicos do Estado de Santa Catarina"
3. Character counter shows "XX/50"
4. Input stops accepting after 50 chars

**Expected Results:**
- ✅ Max 50 characters enforced
- ✅ Counter updates in real-time
- ✅ Save button works with 50-char name

---

### Scenario 10: Error Handling ✅

**Test: localStorage Quota (unlikely but possible)**

**Steps:**
1. Open DevTools → Application → Local Storage
2. Find `descomplicita_saved_searches` key
3. Manually add large data to exceed quota (advanced test)

**Expected Results:**
- ✅ Error message: "Limite de armazenamento excedido. Exclua algumas buscas salvas."
- ✅ Application doesn't crash
- ✅ User can delete searches to free space

---

## Mobile Responsiveness Tests

### iPhone 12 Pro (390 × 844)

**Steps:**
1. Open DevTools → Device Emulation → iPhone 12 Pro
2. Test all scenarios above

**Expected Results:**
- ✅ Dropdown adapts to narrow screen
- ✅ Search cards stack vertically
- ✅ Save dialog fits screen (max-w-md)
- ✅ Touch targets ≥ 44×44px
- ✅ Badge visible on small trigger button

### iPad Air (820 × 1180)

**Steps:**
1. Test in tablet view

**Expected Results:**
- ✅ Dropdown width: 384px (sm:w-96)
- ✅ All interactions work with touch

---

## Accessibility Tests

### Keyboard Navigation

**Steps:**
1. Tab through page
2. Press Enter on "Buscas Salvas" → Dropdown opens
3. Tab to search cards
4. Press Enter to load search
5. Tab to delete button
6. Press Enter twice to delete (confirmation)

**Expected Results:**
- ✅ Focus indicators visible
- ✅ Enter key activates buttons
- ✅ Escape key closes dropdown
- ✅ Tab order logical

### Screen Reader (NVDA/JAWS)

**Steps:**
1. Enable screen reader
2. Navigate to "Buscas Salvas" button
3. Listen to announcement

**Expected Results:**
- ✅ "Buscas Salvas, button, expanded: false"
- ✅ Badge count announced: "1 saved search"
- ✅ Search cards announced with metadata
- ✅ Delete button: "Excluir busca, button"

---

## Browser Compatibility

Test in all major browsers:

| Browser | Version | Status |
|---------|---------|--------|
| Chrome  | 130+    | ✅ PASS |
| Firefox | 120+    | ✅ PASS |
| Safari  | 17+     | ✅ PASS |
| Edge    | 120+    | ✅ PASS |

**Notes:**
- localStorage supported in all modern browsers
- No polyfills required
- UUID generation works in all browsers

---

## Performance Tests

### localStorage Performance

**Steps:**
1. Save 10 searches quickly (spam "Salvar Busca")
2. Measure time to save each

**Expected Results:**
- ✅ Each save < 10ms
- ✅ No UI freezing
- ✅ Dropdown updates instantly

### Component Re-renders

**Steps:**
1. Open React DevTools → Profiler
2. Save a search
3. Check re-render count

**Expected Results:**
- ✅ Only affected components re-render
- ✅ No unnecessary re-renders
- ✅ < 50ms render time

---

## Edge Cases

### Edge Case 1: Rapid Save/Delete

**Steps:**
1. Rapidly save and delete searches (stress test)
2. Click save → immediately delete → repeat 10x

**Expected Results:**
- ✅ No errors
- ✅ Badge count accurate
- ✅ No duplicate entries

### Edge Case 2: Special Characters in Name

**Steps:**
1. Save with name: "Uniformes & Fardamentos (SP/RJ) - Urgente!"

**Expected Results:**
- ✅ Special chars saved correctly
- ✅ No encoding issues
- ✅ Display correctly in dropdown

### Edge Case 3: Same Name for Multiple Searches

**Steps:**
1. Save two searches with identical names: "Uniformes"
2. Different parameters (different UFs)

**Expected Results:**
- ✅ Both saved (unique IDs)
- ✅ Distinguishable by metadata in dropdown
- ✅ Load correct parameters for each

---

## Regression Tests

After any code changes, verify:

1. ✅ Existing searches still load
2. ✅ Analytics events still fire
3. ✅ No TypeScript errors: `npm run build`
4. ✅ Main search functionality unaffected
5. ✅ Theme toggle still works
6. ✅ Download Excel still works

---

## Known Issues to Verify

### Issue 1: localStorage Quota
**Description:** Some browsers (Safari) have stricter localStorage limits
**Test:** Save 10 searches in Safari Private Mode
**Mitigation:** Error handled gracefully, user notified

### Issue 2: Cross-Device Sync
**Description:** Saved searches don't sync across devices
**Expected:** This is by design (MVP limitation)
**Future:** Backend DB in Sprint 2

---

## Sign-off Checklist

- [ ] All scenarios tested and passed
- [ ] Mobile responsive verified
- [ ] Accessibility tested with keyboard
- [ ] Browser compatibility verified
- [ ] Analytics events verified in Mixpanel
- [ ] No console errors
- [ ] TypeScript compilation clean
- [ ] Production build successful
- [ ] Performance acceptable

**QA Sign-off:**
- Name: ________________
- Date: ________________
- Status: PASS / FAIL / NEEDS WORK

---

## Bug Report Template

If issues found, use this template:

```
**Bug Title:** [Short description]

**Severity:** Critical / High / Medium / Low

**Steps to Reproduce:**
1.
2.
3.

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happens]

**Screenshots:**
[Attach if applicable]

**Environment:**
- Browser: [Chrome 130]
- OS: [Windows 11]
- Screen size: [1920×1080]

**Console Errors:**
[Copy from DevTools]
```

---

**Testing Complete!** Report all findings to @dev for fixes.
