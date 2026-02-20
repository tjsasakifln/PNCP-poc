# Value Sprint 01 - Phase 2 Test Cases

**Date:** 2026-01-29
**Owner:** @qa (Quinn - Guardian)
**Phase:** 2 of 4 (Design & Implementation Wave 1)
**Test Plan:** `value-sprint-01-phase-2-test-plan.md`

---

## 📋 Test Case Index

| Feature | Test Cases | Priority | Status |
|---------|-----------|----------|--------|
| **Analytics Tracking** | TC-ANALYTICS-INIT-001 to 010 | High | ⏳ Pending |
| **Saved Searches** | TC-SAVED-CRUD-001 to 015 | High | ⏳ Pending |
| **Enhanced Loading** | TC-LOADING-UI-001 to 012 | Medium | ⏳ Pending |
| **Regression Tests** | TC-REGRESSION-001 to 008 | High | ⏳ Pending |

**Total Test Cases:** 45
**Automated:** 38 (84%)
**Manual:** 7 (16%)

---

## 🎯 Analytics Tracking Test Cases

### TC-ANALYTICS-INIT-001: Mixpanel Initialization Success

**Priority:** High
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- NEXT_PUBLIC_MIXPANEL_TOKEN set in environment
- App loads for first time

**Test Steps:**
1. Mock `mixpanel.init()` function
2. Render `<AnalyticsProvider>` component
3. Verify `mixpanel.init()` called with correct token
4. Verify debug mode enabled in development

**Expected Result:**
- `mixpanel.init()` called once with token and config
- Config includes: `debug: true`, `track_pageview: false`, `persistence: 'localStorage'`
- No errors in console

**Test Code Location:** `frontend/__tests__/analytics.test.ts`

**Status:** ⏳ Pending
**Actual Result:** _To be filled after execution_

---

### TC-ANALYTICS-INIT-002: Graceful Degradation Without Token

**Priority:** High
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- NEXT_PUBLIC_MIXPANEL_TOKEN is undefined or empty

**Test Steps:**
1. Unset `process.env.NEXT_PUBLIC_MIXPANEL_TOKEN`
2. Render `<AnalyticsProvider>`
3. Verify warning logged to console
4. Verify `mixpanel.init()` NOT called
5. Verify app continues to function normally

**Expected Result:**
- Console warning: "⚠️ NEXT_PUBLIC_MIXPANEL_TOKEN not found. Analytics disabled."
- `mixpanel.init()` never called
- No errors thrown
- App renders normally

**Status:** ⏳ Pending
**Actual Result:** _To be filled_

---

### TC-ANALYTICS-EVENT-001: page_load Event Fires

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Mixpanel initialized
- User navigates to homepage

**Test Steps:**
1. Mock `mixpanel.track()`
2. Render `<AnalyticsProvider>`
3. Verify `mixpanel.track()` called with 'page_load'
4. Check event properties

**Expected Result:**
```javascript
mixpanel.track('page_load', {
  path: '/',
  timestamp: '2026-01-29T...',
  environment: 'development',
  referrer: 'direct' or document.referrer,
  user_agent: navigator.userAgent
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-002: page_exit Event Fires

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Mixpanel initialized
- User has been on page for 30 seconds

**Test Steps:**
1. Mock `mixpanel.track()`
2. Render `<AnalyticsProvider>`
3. Simulate `beforeunload` event
4. Verify `page_exit` event fired
5. Check session_duration_ms property

**Expected Result:**
```javascript
mixpanel.track('page_exit', {
  path: '/',
  session_duration_ms: ~30000,
  session_duration_readable: '30s',
  timestamp: '2026-01-29T...'
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-003: search_started Event Properties

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- User fills search form
- User clicks "Buscar" button

**Test Steps:**
1. Mock `useAnalytics().trackEvent()`
2. Render `<HomePage>`
3. Select UFs: ['SC', 'PR']
4. Set dates: 2026-01-01 to 2026-01-07
5. Select sector: "vestuario"
6. Click "Buscar" button
7. Verify `search_started` event fired

**Expected Result:**
```javascript
trackEvent('search_started', {
  ufs: ['SC', 'PR'],
  uf_count: 2,
  date_range: {
    inicial: '2026-01-01',
    final: '2026-01-07',
    days: 7
  },
  search_mode: 'setor',
  setor_id: 'vestuario',
  termos_busca: null,
  termos_count: 0
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-004: search_completed Event Properties

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Search initiated successfully
- Backend returns results

**Test Steps:**
1. Mock fetch to return mock results (50 opportunities, R$ 1,000,000)
2. Initiate search
3. Wait for search to complete
4. Verify `search_completed` event fired
5. Check timing and result properties

**Expected Result:**
```javascript
trackEvent('search_completed', {
  time_elapsed_ms: ~5000,
  time_elapsed_readable: '5s',
  total_raw: 200,
  total_filtered: 50,
  filter_ratio: '25.0%',
  valor_total: 1000000,
  has_summary: true,
  ufs: ['SC', 'PR'],
  uf_count: 2,
  search_mode: 'setor'
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-005: search_failed Event Properties

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Search initiated
- Backend returns error

**Test Steps:**
1. Mock fetch to reject with error
2. Initiate search
3. Wait for error
4. Verify `search_failed` event fired
5. Check error details

**Expected Result:**
```javascript
trackEvent('search_failed', {
  error_message: 'Backend indisponível. Tente novamente.',
  error_type: 'Error',
  time_elapsed_ms: ~2000,
  ufs: ['SC'],
  uf_count: 1,
  search_mode: 'setor'
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-006: download_started Event

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Search completed with results
- User clicks "Baixar Excel" button

**Test Steps:**
1. Complete search successfully
2. Click download button
3. Verify `download_started` event fired
4. Check download ID and totals

**Expected Result:**
```javascript
trackEvent('download_started', {
  download_id: 'uuid-v4-string',
  total_filtered: 50,
  valor_total: 1000000,
  search_mode: 'setor',
  ufs: ['SC', 'PR'],
  uf_count: 2
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-007: download_completed Event

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Download initiated
- File downloads successfully

**Test Steps:**
1. Mock successful download (5KB file)
2. Initiate download
3. Wait for completion
4. Verify `download_completed` event fired
5. Check file size and timing

**Expected Result:**
```javascript
trackEvent('download_completed', {
  download_id: 'uuid-v4-string',
  time_elapsed_ms: ~500,
  time_elapsed_readable: '0s',
  file_size_bytes: 5120,
  file_size_readable: '5.00 KB',
  filename: 'DescompLicita_Vestuário_e_Uniformes_2026-01-01_a_2026-01-07.xlsx',
  total_filtered: 50,
  valor_total: 1000000
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-008: download_failed Event

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Download initiated
- Download fails (404 or network error)

**Test Steps:**
1. Mock failed download (404)
2. Initiate download
3. Wait for error
4. Verify `download_failed` event fired
5. Check error message

**Expected Result:**
```javascript
trackEvent('download_failed', {
  download_id: 'uuid-v4-string',
  error_message: 'Arquivo expirado. Faça uma nova busca para gerar o Excel.',
  error_type: 'Error',
  time_elapsed_ms: ~300,
  total_filtered: 50
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-009: Custom Terms Search Mode

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- User switches to "Termos Específicos" mode
- User enters custom terms

**Test Steps:**
1. Click "Termos Específicos" button
2. Enter terms: "uniforme", "jaleco", "fardamento"
3. Initiate search
4. Verify `search_started` event has correct mode

**Expected Result:**
```javascript
trackEvent('search_started', {
  ufs: ['SC'],
  uf_count: 1,
  date_range: {...},
  search_mode: 'termos',
  setor_id: null,
  termos_busca: 'uniforme jaleco fardamento',
  termos_count: 3
})
```

**Status:** ⏳ Pending

---

### TC-ANALYTICS-EVENT-010: Error Handling - Track Fails Silently

**Priority:** High
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- Mixpanel SDK throws error on `track()` call

**Test Steps:**
1. Mock `mixpanel.track()` to throw error
2. Call `trackEvent('test_event')`
3. Verify error caught and logged
4. Verify app continues to function

**Expected Result:**
- Error logged to console: "Analytics tracking failed: ..."
- No error thrown to caller
- App does not crash

**Status:** ⏳ Pending

---

## 💾 Saved Searches Test Cases

### TC-SAVED-CRUD-001: Save Search with Valid Name

**Priority:** High
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- User has completed a search
- Saved searches list has < 10 items

**Test Steps:**
1. Fill search form: UFs=['SC'], dates=2026-01-01 to 2026-01-07, sector='vestuario'
2. Click "Salvar Busca" button
3. Enter name: "Minha Busca de Testes"
4. Confirm save
5. Verify search added to localStorage
6. Verify search appears in dropdown

**Expected Result:**
- Search saved with structure:
```javascript
{
  id: 'uuid-v4',
  name: 'Minha Busca de Testes',
  ufs: ['SC'],
  dataInicial: '2026-01-01',
  dataFinal: '2026-01-07',
  searchMode: 'setor',
  setorId: 'vestuario',
  termosArray: [],
  savedAt: '2026-01-29T...'
}
```
- localStorage updated
- Dropdown shows new search

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-002: Load Saved Search

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- At least 1 saved search exists

**Test Steps:**
1. Open saved searches dropdown
2. Click on saved search "Minha Busca de Testes"
3. Verify form fields auto-fill

**Expected Result:**
- UFs selected: ['SC']
- Date inicial: 2026-01-01
- Date final: 2026-01-07
- Search mode: "setor"
- Sector: "vestuario"
- Terms: [] (empty)

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-003: Delete Saved Search

**Priority:** High
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- 3 saved searches exist

**Test Steps:**
1. Open saved searches dropdown
2. Click delete icon on 2nd search
3. Confirm deletion
4. Verify search removed from localStorage
5. Verify dropdown updated

**Expected Result:**
- Search removed from localStorage
- Dropdown shows only 2 searches
- `saved_search_deleted` event fired

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-004: Maximum 10 Searches Enforced

**Priority:** High
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- 10 saved searches already exist

**Test Steps:**
1. Attempt to save 11th search
2. Verify oldest search removed
3. Verify new search added
4. Verify total remains 10

**Expected Result:**
- Oldest search (by `savedAt` timestamp) removed
- New search added
- localStorage has exactly 10 searches
- User notified: "Busca mais antiga removida (limite de 10)"

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-005: Validate Empty Name

**Priority:** Medium
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- User attempts to save search

**Test Steps:**
1. Click "Salvar Busca"
2. Leave name field empty
3. Click confirm
4. Verify validation error

**Expected Result:**
- Error message: "Nome da busca é obrigatório"
- Search NOT saved
- Modal remains open

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-006: Validate Duplicate Name

**Priority:** Medium
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- Search named "Test" already exists

**Test Steps:**
1. Attempt to save new search with name "Test"
2. Verify validation error or auto-rename

**Expected Result:**
**Option A (Strict):** Error: "Nome já existe. Escolha outro."
**Option B (Friendly):** Auto-rename to "Test (2)"

**Status:** ⏳ Pending
**Notes:** Decide on approach with @ux-design-expert

---

### TC-SAVED-CRUD-007: Special Characters in Name

**Priority:** Low
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- User saves search

**Test Steps:**
1. Enter name with special characters: "Busca #1 - Região Sul (SC/PR/RS)"
2. Save search
3. Verify name stored correctly
4. Load search and verify

**Expected Result:**
- Special characters preserved: `#`, `-`, `(`, `)`, `/`
- Name displays correctly in dropdown
- Search loads successfully

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-008: localStorage Persistence

**Priority:** High
**Type:** Integration Test
**Automation:** Yes (with mock localStorage)

**Preconditions:**
- 3 searches saved

**Test Steps:**
1. Save searches
2. Simulate page reload (unmount and remount component)
3. Verify searches restored from localStorage

**Expected Result:**
- All 3 searches restored
- Order preserved (newest first)
- All properties intact

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-009: Analytics - saved_search_created Event

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Analytics initialized

**Test Steps:**
1. Save a search
2. Verify analytics event fired

**Expected Result:**
```javascript
trackEvent('saved_search_created', {
  search_id: 'uuid-v4',
  name: 'Minha Busca de Testes',
  ufs_count: 1,
  search_mode: 'setor',
  total_saved_searches: 4
})
```

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-010: Analytics - saved_search_loaded Event

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Saved search exists

**Test Steps:**
1. Load saved search from dropdown
2. Verify analytics event fired

**Expected Result:**
```javascript
trackEvent('saved_search_loaded', {
  search_id: 'uuid-v4',
  name: 'Minha Busca de Testes',
  age_days: 2 // Days since savedAt
})
```

**Status:** ⏳ Pending

---

### TC-SAVED-CRUD-011: Analytics - saved_search_deleted Event

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Saved search exists

**Test Steps:**
1. Delete saved search
2. Verify analytics event fired

**Expected Result:**
```javascript
trackEvent('saved_search_deleted', {
  search_id: 'uuid-v4',
  name: 'Minha Busca de Testes',
  age_days: 5
})
```

**Status:** ⏳ Pending

---

### TC-SAVED-UI-012: Mobile Responsive Dropdown

**Priority:** Medium
**Type:** Manual Visual Test
**Automation:** No

**Preconditions:**
- 5 saved searches exist
- Testing on mobile viewport (375px width)

**Test Steps:**
1. Resize browser to 375px width
2. Open saved searches dropdown
3. Verify dropdown fits screen
4. Verify all searches visible
5. Verify touch targets ≥ 44px

**Expected Result:**
- Dropdown width adjusts to screen
- No horizontal scroll
- All text readable
- Delete buttons touchable

**Status:** ⏳ Pending
**Tools:** Chrome DevTools Device Mode

---

### TC-SAVED-UI-013: Keyboard Navigation

**Priority:** High (Accessibility)
**Type:** Manual Accessibility Test
**Automation:** Partial (can test focus with Testing Library)

**Preconditions:**
- Saved searches dropdown exists

**Test Steps:**
1. Tab to "Salvar Busca" button → should focus
2. Enter → should open save modal
3. Tab → should focus name input
4. Enter name, Tab → focus "Salvar" button
5. Enter → should save and close modal
6. Tab to dropdown → should focus dropdown button
7. Enter → should open dropdown
8. Arrow Down → should focus first search
9. Enter → should load search
10. Tab to delete button → should focus
11. Enter → should delete

**Expected Result:**
- All interactive elements keyboard accessible
- Focus indicators visible (blue outline)
- No keyboard traps
- Logical tab order

**Status:** ⏳ Pending

---

### TC-SAVED-EDGE-014: localStorage Full

**Priority:** Low
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- localStorage is full (5MB limit reached)

**Test Steps:**
1. Mock `localStorage.setItem()` to throw QuotaExceededError
2. Attempt to save search
3. Verify error handled gracefully

**Expected Result:**
- Error message: "Não foi possível salvar. Espaço insuficiente. Exclua buscas antigas."
- App does not crash
- User can delete old searches to free space

**Status:** ⏳ Pending

---

### TC-SAVED-EDGE-015: Corrupted localStorage Data

**Priority:** Medium
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- localStorage contains invalid JSON

**Test Steps:**
1. Set `localStorage.getItem('savedSearches')` to invalid JSON: `"{invalid"`
2. Attempt to load saved searches
3. Verify error handled

**Expected Result:**
- Invalid data cleared
- localStorage reset to `[]`
- Console error logged
- User sees empty searches list (no crash)

**Status:** ⏳ Pending

---

## ⏳ Enhanced Loading Progress Test Cases

### TC-LOADING-UI-001: Stage 1 Display

**Priority:** High
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- Search initiated
- Elapsed time: 0-5 seconds

**Test Steps:**
1. Render `<LoadingProgress currentStep={1} stateCount={3} />`
2. Advance timer to 3 seconds
3. Verify stage 1 active

**Expected Result:**
- Status message: "Conectando ao PNCP..."
- Stage 1 badge: blue background, pulsing animation
- Progress bar: ~15% (3s / estimated 30s)

**Status:** ⏳ Pending

---

### TC-LOADING-UI-002: Stage 2 with Dynamic Count

**Priority:** High
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- Elapsed time: 10 seconds
- 3 states selected

**Test Steps:**
1. Render `<LoadingProgress stateCount={3} />`
2. Advance timer to 10 seconds
3. Verify stage 2 active
4. Check dynamic message

**Expected Result:**
- Status message: "Consultando 3 estados no PNCP..."
- Stage 2 badge: blue background, pulsing
- Progress bar: ~33%

**Status:** ⏳ Pending

---

### TC-LOADING-UI-003: Stage 3 Display

**Priority:** Medium
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- Elapsed time: 20 seconds
- Fetching complete

**Test Steps:**
1. Render component
2. Advance timer to 20 seconds (past fetchTime)
3. Verify stage 3 active

**Expected Result:**
- Status message: "Filtrando e analisando licitações..."
- Stage 3 badge: blue background, pulsing
- Stages 1-2: green checkmark

**Status:** ⏳ Pending

---

### TC-LOADING-UI-004: Stage 4 Display

**Priority:** Medium
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- Elapsed time: 35 seconds
- Near completion

**Test Steps:**
1. Advance timer to 35 seconds
2. Verify stage 4 active

**Expected Result:**
- Status message: "Gerando relatório e resumo executivo..."
- Stage 4 badge: blue background, pulsing
- Stages 1-3: green checkmarks
- Progress bar: ~85%

**Status:** ⏳ Pending

---

### TC-LOADING-UI-005: Progress Bar Animation

**Priority:** Medium
**Type:** Visual Test
**Automation:** Partial (can test value, not smoothness)

**Preconditions:**
- Loading in progress

**Test Steps:**
1. Render component
2. Advance timer by 1 second increments
3. Verify progress increases
4. Manual: Verify smooth transition (not jumpy)

**Expected Result:**
- Progress increases monotonically (never decreases)
- Value: 0% → 95% (asymptotic, never reaches 100%)
- Animation: `transition-all duration-1000 ease-out` applied
- Visual: Smooth gradient animation

**Status:** ⏳ Pending
**Notes:** Smoothness requires manual verification

---

### TC-LOADING-UI-006: Elapsed Time Formatting

**Priority:** Medium
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- Timer running

**Test Steps:**
1. Test elapsed = 0s → Display: "0s"
2. Test elapsed = 45s → Display: "45s"
3. Test elapsed = 90s → Display: "1min 30s"
4. Test elapsed = 125s → Display: "2min 05s"

**Expected Result:**
- Correct formatting for all cases
- Padded seconds (05 not 5)
- Minutes shown when ≥ 60s

**Status:** ⏳ Pending

---

### TC-LOADING-UI-007: Remaining Time Calculation

**Priority:** Medium
**Type:** Unit Test
**Automation:** Yes

**Preconditions:**
- estimatedTime = 45s
- Elapsed time varies

**Test Steps:**
1. Elapsed = 10s → Remaining: "~35s restantes"
2. Elapsed = 30s → Remaining: "~15s restantes"
3. Elapsed = 70s → Remaining: "~0min 0s restantes" or "Finalizando..."
4. Elapsed = 100s (past estimate) → Display: "Finalizando..."

**Expected Result:**
- Accurate subtraction: estimated - elapsed
- Minutes shown when remaining ≥ 60s
- "Finalizando..." when past estimate

**Status:** ⏳ Pending

---

### TC-LOADING-UI-008: Curiosidades Rotation

**Priority:** Low
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- Component mounted

**Test Steps:**
1. Render component
2. Note initial curiosidade (e.g., index 0)
3. Advance timer by 5 seconds
4. Verify curiosidade changed (index 1)
5. Advance by 5s again → index 2
6. Repeat until cycle completes (26 curiosidades)

**Expected Result:**
- Curiosidade changes every 5 seconds
- Cycles through all 26 items
- Returns to index 0 after last item

**Status:** ⏳ Pending

---

### TC-LOADING-UI-009: Mobile Responsive Layout

**Priority:** Medium
**Type:** Manual Visual Test
**Automation:** No

**Preconditions:**
- Mobile viewport (375px width)

**Test Steps:**
1. Resize to 375px width
2. Trigger loading state
3. Verify all elements visible
4. Verify no horizontal scroll
5. Verify text readable

**Expected Result:**
- Progress bar full width
- Stage labels hidden on mobile (`hidden sm:inline`)
- Curiosidade text wraps correctly
- No layout shift

**Status:** ⏳ Pending

---

### TC-LOADING-UI-010: Context Info Display

**Priority:** Low
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- 3 states selected

**Test Steps:**
1. Render component with `stateCount={3}`
2. Verify context message

**Expected Result:**
- Message: "Buscando em 3 estados com 5 modalidades de contratação"
- Plural form correct ("estados" not "estado")

**Test Cases:**
- 1 state → "1 estado"
- 2 states → "2 estados"

**Status:** ⏳ Pending

---

### TC-LOADING-ANALYTICS-011: loading_abandoned Event

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Search in progress
- User navigates away before completion

**Test Steps:**
1. Initiate search
2. Wait 10 seconds (mid-progress)
3. Simulate navigation away (unmount component)
4. Verify `loading_abandoned` event fired

**Expected Result:**
```javascript
trackEvent('loading_abandoned', {
  elapsed_time_ms: ~10000,
  elapsed_time_readable: '10s',
  progress_percentage: ~30,
  active_stage: 2,
  ufs_count: 3
})
```

**Status:** ⏳ Pending
**Notes:** Event name TBD - confirm with @analyst

---

### TC-LOADING-EDGE-012: Estimate Exceeded

**Priority:** Low
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- estimatedTime = 30s
- Actual time > 60s (slow backend)

**Test Steps:**
1. Render with estimatedTime={30}
2. Advance timer to 60 seconds
3. Verify display adjusts gracefully

**Expected Result:**
- Progress bar: 95% (capped, never 100%)
- Remaining time: "Finalizando..."
- No negative values displayed
- App does not crash

**Status:** ⏳ Pending

---

## 🔄 Regression Test Cases

### TC-REGRESSION-SEARCH-001: Full Search Flow

**Priority:** High
**Type:** End-to-End (Manual or Automated)
**Automation:** Partial

**Preconditions:**
- Backend running
- Frontend loaded

**Test Steps:**
1. Select UF: SC
2. Set dates: 2026-01-01 to 2026-01-07
3. Select sector: "Vestuário e Uniformes"
4. Click "Buscar"
5. Wait for results
6. Verify summary displayed
7. Click "Baixar Excel"
8. Verify file downloads

**Expected Result:**
- Search completes successfully
- Results show opportunities count
- Excel file downloads with correct name
- All analytics events fire

**Status:** ⏳ Pending

---

### TC-REGRESSION-ERROR-002: Invalid Date Range

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- User on homepage

**Test Steps:**
1. Set data inicial: 2026-01-15
2. Set data final: 2026-01-10 (earlier than inicial)
3. Attempt to click "Buscar"
4. Verify validation error

**Expected Result:**
- Error message: "Data final deve ser maior ou igual à data inicial"
- "Buscar" button disabled
- No API call made

**Status:** ⏳ Pending

---

### TC-REGRESSION-ERROR-003: No UFs Selected

**Priority:** High
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- User on homepage

**Test Steps:**
1. Clear all UF selections
2. Set valid dates
3. Attempt to click "Buscar"
4. Verify validation error

**Expected Result:**
- Error message: "Selecione pelo menos um estado"
- "Buscar" button disabled
- No API call made

**Status:** ⏳ Pending

---

### TC-REGRESSION-EMPTY-004: No Results Found

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Backend returns 0 results

**Test Steps:**
1. Mock backend to return empty results
2. Perform search
3. Verify empty state displayed

**Expected Result:**
- Empty state component shown
- Message: helpful suggestions to adjust search
- "Ajustar Busca" button scrolls to top
- No error thrown

**Status:** ⏳ Pending

---

### TC-REGRESSION-THEME-005: Theme Toggle Persistence

**Priority:** Medium
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- Default theme: light

**Test Steps:**
1. Click theme toggle → dark mode
2. Verify `<html>` has `class="dark"`
3. Reload page
4. Verify dark mode persists

**Expected Result:**
- Theme persists in localStorage
- All colors invert correctly
- No flash of wrong theme (FOUC)

**Status:** ⏳ Pending

---

### TC-REGRESSION-REGION-006: Region Selector

**Priority:** Medium
**Type:** Component Test
**Automation:** Yes

**Preconditions:**
- No UFs selected

**Test Steps:**
1. Click "Sul" region button
2. Verify SC, PR, RS selected
3. Click "Sul" again
4. Verify SC, PR, RS deselected

**Expected Result:**
- Toggle behavior works correctly
- UF count updates: 0 → 3 → 0
- Results cleared when selection changes

**Status:** ⏳ Pending

---

### TC-REGRESSION-DOWNLOAD-007: Expired Download

**Priority:** Medium
**Type:** Integration Test
**Automation:** Yes

**Preconditions:**
- Download cache expired (10+ minutes)

**Test Steps:**
1. Perform search
2. Wait 11 minutes (or mock cache expiry)
3. Click "Baixar Excel"
4. Verify error message

**Expected Result:**
- Error: "Arquivo expirado. Faça uma nova busca para gerar o Excel."
- User can retry search
- `download_failed` event fired

**Status:** ⏳ Pending

---

### TC-REGRESSION-ACCESSIBILITY-008: WCAG 2.1 AA Compliance

**Priority:** High
**Type:** Accessibility Audit
**Automation:** Partial (aXe DevTools)

**Preconditions:**
- App loaded in Chrome with aXe extension

**Test Steps:**
1. Run aXe DevTools scan on homepage
2. Verify no violations
3. Test keyboard navigation (Tab through all elements)
4. Test with screen reader (NVDA or VoiceOver)
5. Verify color contrast ratios

**Expected Result:**
- aXe DevTools: 0 violations
- All interactive elements keyboard accessible
- Screen reader announces all content correctly
- Color contrast ≥ 4.5:1 for normal text
- Color contrast ≥ 3:1 for large text (≥18pt)

**Status:** ⏳ Pending
**Tools:** aXe DevTools, Chrome Lighthouse, NVDA

---

## 📊 Test Coverage Matrix

### Feature Coverage

| Feature | Unit Tests | Integration Tests | E2E Tests | Manual Tests | Total |
|---------|-----------|-------------------|-----------|--------------|-------|
| Analytics | 3 | 7 | 0 | 0 | 10 |
| Saved Searches | 8 | 5 | 0 | 2 | 15 |
| Loading Progress | 7 | 1 | 0 | 4 | 12 |
| Regression | 0 | 6 | 1 | 1 | 8 |
| **TOTAL** | **18** | **19** | **1** | **7** | **45** |

### Acceptance Criteria Coverage

| Feature | AC Items | Test Cases | Coverage |
|---------|----------|------------|----------|
| **Analytics** | 12 | 10 | 83% |
| **Saved Searches** | 12 | 15 | 125% (over-tested) |
| **Loading Progress** | 12 | 12 | 100% |
| **Regression** | 10 | 8 | 80% |

---

## 🚀 Test Execution Schedule

### Phase 2A: Analytics Testing (Day 3-4)
- TC-ANALYTICS-INIT-001 to 002
- TC-ANALYTICS-EVENT-001 to 010
- **Estimated Time:** 6 hours
- **Owner:** @qa + @dev

### Phase 2B: Saved Searches Testing (Day 5-6)
- TC-SAVED-CRUD-001 to 011
- TC-SAVED-UI-012 to 013
- TC-SAVED-EDGE-014 to 015
- **Estimated Time:** 10 hours
- **Owner:** @qa + @dev

### Phase 2C: Loading Progress Testing (Day 6-7)
- TC-LOADING-UI-001 to 010
- TC-LOADING-ANALYTICS-011
- TC-LOADING-EDGE-012
- **Estimated Time:** 8 hours
- **Owner:** @qa

### Phase 2D: Regression Testing (Day 7)
- TC-REGRESSION-SEARCH-001 to 008
- **Estimated Time:** 4 hours
- **Owner:** @qa

**Total Estimated Effort:** 28 hours (~3.5 days for 1 QA engineer)

---

## 📝 Test Execution Log Template

```markdown
## Test Execution Log - {Date}

**Tester:** @qa
**Build/Commit:** {commit-hash}
**Environment:** Development

### Tests Executed

| Test ID | Status | Actual Result | Notes |
|---------|--------|---------------|-------|
| TC-ANALYTICS-INIT-001 | ✅ Pass | Mixpanel initialized correctly | - |
| TC-ANALYTICS-INIT-002 | ✅ Pass | Warning logged, no crash | - |
| TC-ANALYTICS-EVENT-001 | ❌ Fail | Event missing 'referrer' property | BUG-P2-001 created |
| ... | ... | ... | ... |

### Summary
- **Total:** 10
- **Passed:** 9 (90%)
- **Failed:** 1 (10%)
- **Blocked:** 0

### Bugs Found
- **BUG-P2-001 (High):** page_load event missing 'referrer' property
  - **Assigned:** @dev
  - **Fix ETA:** Day 4

### Next Steps
- Fix BUG-P2-001
- Re-run failed test
- Continue to Phase 2B if pass rate ≥ 95%
```

---

## ✅ Sign-Off Checklist

### Phase 2A Sign-Off (Analytics)
- [ ] All 10 analytics tests pass
- [ ] `useAnalytics.ts` coverage ≥ 85%
- [ ] `AnalyticsProvider.tsx` coverage ≥ 80%
- [ ] Manual verification in Mixpanel dashboard (dev)
- [ ] No console errors
- [ ] @qa sign-off
- [ ] @dev sign-off

### Phase 2B Sign-Off (Saved Searches)
- [ ] All 15 saved searches tests pass
- [ ] `useSavedSearches.ts` coverage ≥ 75%
- [ ] `<SavedSearchesDropdown>` coverage ≥ 70%
- [ ] Mobile responsive verified (375px, 768px)
- [ ] Keyboard navigation works
- [ ] @qa sign-off
- [ ] @ux-design-expert sign-off

### Phase 2C Sign-Off (Loading Progress)
- [ ] All 12 loading tests pass
- [ ] `LoadingProgress.tsx` coverage ≥ 70%
- [ ] Stage transitions smooth (manual)
- [ ] Mobile responsive verified
- [ ] No layout shift or flicker
- [ ] @qa sign-off

### Phase 2D Sign-Off (Regression)
- [ ] All 8 regression tests pass
- [ ] Backend coverage ≥ 70% (maintained)
- [ ] Frontend coverage ≥ 60% (achieved)
- [ ] Lighthouse score ≥ 90
- [ ] WCAG 2.1 AA compliance (aXe: 0 violations)
- [ ] @qa sign-off
- [ ] @po sign-off (final approval for Phase 3)

---

**Document Status:** ✅ COMPLETE
**Next Step:** Execute Phase 2A Tests
**Owner:** @qa (Quinn - Guardian)
**Date:** 2026-01-29
