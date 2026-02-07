# AC15: Setores Fallback Implementation

**Story:** STORY-170 UX Polish 10/10
**Acceptance Criteria:** AC15 - Fallback Hardcoded de Setores (P3)
**Status:** ✅ COMPLETED
**Date:** 2026-02-07

## Overview

This acceptance criteria ensures that the sector dropdown **never** appears empty, even when the backend API is unavailable. It implements a resilient fallback mechanism with automatic retry logic and user transparency.

## Implementation Details

### 1. Hardcoded Fallback List

**Location:** `frontend/app/buscar/page.tsx` (lines 279-292)

```typescript
const SETORES_FALLBACK: Setor[] = [
  { id: "vestuario", name: "Vestuário e Uniformes", description: "Uniformes, fardamentos, roupas profissionais" },
  { id: "facilities", name: "Facilities (Manutenção Predial)", description: "Manutenção, limpeza, conservação" },
  { id: "software", name: "Software & TI", description: "Software, sistemas, hardware, tecnologia" },
  { id: "alimentacao", name: "Alimentação", description: "Merenda, refeições, alimentos" },
  { id: "equipamentos", name: "Equipamentos", description: "Máquinas, equipamentos, ferramentas" },
  { id: "transporte", name: "Transporte", description: "Veículos, combustível, frete" },
  { id: "saude", name: "Saúde", description: "Medicamentos, material hospitalar" },
  { id: "limpeza", name: "Limpeza", description: "Produtos de limpeza, higiene" },
  { id: "seguranca", name: "Segurança", description: "Vigilância, segurança patrimonial" },
  { id: "escritorio", name: "Material de Escritório", description: "Papelaria, escritório" },
  { id: "construcao", name: "Construção Civil", description: "Obras, materiais de construção" },
  { id: "servicos", name: "Serviços Gerais", description: "Serviços diversos" },
];
```

**Features:**
- 12 core sectors covering major procurement categories
- Complete with id, name, and description fields
- Matches backend Setor type structure
- Serves as last-resort when API is unreachable

### 2. Retry Logic with Exponential Backoff

**Location:** `frontend/app/buscar/page.tsx` (lines 294-322)

```typescript
const fetchSetores = async (attempt = 0) => {
  setSetoresLoading(true);
  setSetoresError(false);
  try {
    const res = await fetch("/api/setores");
    const data = await res.json();
    if (data.setores && data.setores.length > 0) {
      setSetores(data.setores);
      setSetoresUsingFallback(false);
    } else {
      throw new Error("Empty response");
    }
  } catch {
    if (attempt < 2) {
      // Retry with exponential backoff
      setTimeout(() => fetchSetores(attempt + 1), Math.pow(2, attempt) * 1000);
      return;
    }
    // After 3 failures, use fallback
    setSetores(SETORES_FALLBACK);
    setSetoresUsingFallback(true);
    setSetoresError(true);
  } finally {
    if (attempt >= 2 || !setoresError) {
      setSetoresLoading(false);
    }
    setSetoresRetryCount(attempt);
  }
};
```

**Retry Schedule:**
- **Attempt 1:** Immediate (0s delay)
- **Attempt 2:** 1 second delay (2^0 = 1)
- **Attempt 3:** 2 seconds delay (2^1 = 2)
- **Fallback:** After 3 failures, use `SETORES_FALLBACK`

**State Management:**
- `setoresLoading` - Loading indicator
- `setoresError` - Error flag
- `setoresUsingFallback` - Fallback mode flag
- `setoresRetryCount` - Current retry attempt number

### 3. Warning Banner

**Location:** `frontend/app/buscar/page.tsx` (lines 950-967)

```tsx
{setoresUsingFallback && (
  <div className="mb-4 p-3 bg-[var(--warning-subtle)] border border-[var(--warning)]/20 rounded-card flex items-start gap-3 animate-fade-in-up" role="alert">
    <svg className="w-5 h-5 text-[var(--warning)] flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <div className="flex-1">
      <p className="text-sm font-medium text-[var(--warning)]">Usando lista offline de setores</p>
      <p className="text-xs text-ink-secondary mt-0.5">Alguns setores novos podem não aparecer.</p>
    </div>
    <button
      onClick={() => fetchSetores(0)}
      className="text-xs font-medium text-brand-blue hover:underline flex-shrink-0"
      type="button"
    >
      Tentar atualizar
    </button>
  </div>
)}
```

**Features:**
- Warning icon (triangle with exclamation mark)
- Clear message: "Usando lista offline de setores"
- Transparency note: "Alguns setores novos podem não aparecer"
- "Tentar atualizar" button to retry API call
- Accessible with `role="alert"`
- Styled with theme CSS variables

### 4. Sync Script

**Location:** `scripts/sync-setores-fallback.js`

**Purpose:** Keep hardcoded fallback list synchronized with backend's current sector definitions.

**Features:**
- Fetches sectors from backend `/setores` endpoint
- Validates sector data structure (id, name, description required)
- Compares current frontend fallback vs new backend data
- Reports added, removed, and unchanged sectors
- Updates `SETORES_FALLBACK` in page.tsx
- Supports `--dry-run` mode for safe preview
- Supports custom `--backend-url`
- Colored terminal output for readability

**Usage:**
```bash
# Preview changes without modifying files
node scripts/sync-setores-fallback.js --dry-run

# Apply changes to frontend
node scripts/sync-setores-fallback.js

# Use production backend
node scripts/sync-setores-fallback.js --backend-url https://api.smartlic.tech
```

**Example Output:**
```
============================================================
  Sync Setores Fallback Script
  STORY-170 AC15: Monthly sector synchronization
============================================================

📡 Fetching sectors from backend...
   URL: http://localhost:8000/setores

✅ Successfully fetched 12 sectors

🔍 Validating sector data...
✅ All 12 sectors validated successfully

📊 Sector comparison:
   Total sectors: 12
   ✨ Added: software, saude
   🗑️  Removed: None
   ✓ Unchanged: 10 sectors

📝 Reading frontend page...
✅ Successfully updated frontend page

============================================================
  ✅ Synchronization complete!
============================================================
```

### 5. Documentation

**Location:** `scripts/README-sync-setores.md`

**Contents:**
- Purpose and rationale
- Prerequisites
- Usage examples
- When to run (monthly, after backend changes, before releases)
- Error handling guide
- Testing instructions
- Automation suggestions (GitHub Actions, cron jobs)
- Troubleshooting guide
- Related files reference

### 6. Test Script

**Location:** `scripts/test-sync-setores.sh`

**Tests:**
1. Node.js version check
2. Backend availability check
3. Dry run execution
4. Script file validation (exists, executable, valid size)
5. Documentation existence check
6. Frontend implementation validation (SETORES_FALLBACK exists)
7. State management validation (setoresUsingFallback exists)
8. Warning banner validation
9. Retry logic validation (3 attempts)
10. Exponential backoff validation

**Usage:**
```bash
bash scripts/test-sync-setores.sh
```

## User Experience Flow

### Scenario 1: Backend Available

1. User visits `/buscar` page
2. Frontend calls `/api/setores`
3. API responds successfully with 12+ sectors
4. Dropdown shows live sector data
5. No warning banner displayed
6. User searches normally

### Scenario 2: Backend Temporarily Unavailable

1. User visits `/buscar` page
2. Frontend calls `/api/setores` (Attempt 1) → fails
3. Wait 1 second
4. Retry (Attempt 2) → fails
5. Wait 2 seconds
6. Retry (Attempt 3) → fails
7. Use `SETORES_FALLBACK` list
8. Warning banner appears: "Usando lista offline de setores"
9. User can still search with fallback sectors
10. User can click "Tentar atualizar" to retry

### Scenario 3: Backend Recovers During Session

1. User sees warning banner (fallback mode)
2. User clicks "Tentar atualizar"
3. API call succeeds
4. Dropdown updates with live data
5. Warning banner disappears
6. User continues with full functionality

## Acceptance Criteria Verification

### ✅ AC15.1: Lista estática com 12 setores

**Verified:**
- `SETORES_FALLBACK` contains 12 sectors
- All sectors have `id`, `name`, and `description` fields
- Covers major procurement categories

### ✅ AC15.2: Retry logic com 3 tentativas

**Verified:**
- `fetchSetores` function uses `attempt` parameter
- Retries up to 2 additional times (3 total attempts)
- Exponential backoff: `Math.pow(2, attempt) * 1000`
- Only uses fallback after all retries exhausted

### ✅ AC15.3: Banner de aviso

**Verified:**
- Warning banner renders when `setoresUsingFallback` is true
- Message: "Usando lista offline de setores"
- Secondary message: "Alguns setores novos podem não aparecer"
- "Tentar atualizar" button to retry API call
- Accessible with `role="alert"`

### ✅ AC15.4: Script de sincronização

**Verified:**
- `scripts/sync-setores-fallback.js` exists and is executable
- Fetches from backend `/setores`
- Validates data structure
- Shows comparison (added/removed/unchanged)
- Supports `--dry-run` and `--backend-url` flags
- Updates frontend file correctly
- Documentation provided in `scripts/README-sync-setores.md`

## Testing

### Manual Testing

1. **Backend Online:**
   ```bash
   cd frontend && npm run dev
   # Visit http://localhost:3000/buscar
   # Verify dropdown shows sectors
   # Verify no warning banner
   ```

2. **Backend Offline:**
   ```bash
   # Stop backend
   cd frontend && npm run dev
   # Visit http://localhost:3000/buscar
   # Wait for 3 retries (~3 seconds)
   # Verify warning banner appears
   # Verify dropdown has 12 fallback sectors
   ```

3. **Recovery:**
   ```bash
   # Start backend
   # Click "Tentar atualizar" button
   # Verify warning banner disappears
   # Verify dropdown updates
   ```

### Automated Testing

**Test script:**
```bash
bash scripts/test-sync-setores.sh
```

**All tests passing:**
- ✅ Node.js installed
- ✅ Backend running (optional)
- ✅ Dry run successful
- ✅ Script exists and executable
- ✅ Documentation exists
- ✅ Frontend has SETORES_FALLBACK
- ✅ Fallback state management exists
- ✅ Warning banner exists
- ✅ Retry logic with 3 attempts
- ✅ Exponential backoff

## Maintenance

### Monthly Sync (Recommended)

```bash
# 1. Check for backend updates
cd backend
git pull
uvicorn main:app --reload

# 2. Run sync script
cd ..
node scripts/sync-setores-fallback.js --dry-run

# 3. Review changes
git diff frontend/app/buscar/page.tsx

# 4. Apply if needed
node scripts/sync-setores-fallback.js

# 5. Commit
git add frontend/app/buscar/page.tsx
git commit -m "chore: sync setores fallback list"
```

### Automation Option

Create `.github/workflows/sync-setores.yml`:

```yaml
name: Sync Setores Fallback

on:
  schedule:
    - cron: '0 0 1 * *' # Monthly on 1st at 00:00 UTC
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: node scripts/sync-setores-fallback.js
      - uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'chore: sync setores fallback list'
          title: '[Automated] Sync Setores Fallback'
```

## Related Files

### Frontend
- `frontend/app/buscar/page.tsx` - Main implementation
- `frontend/app/api/setores/route.ts` - API proxy
- `frontend/app/types.ts` - Setor type definition

### Backend
- `backend/main.py` - `/setores` endpoint
- `backend/sectors.py` - Source of truth for sectors

### Scripts
- `scripts/sync-setores-fallback.js` - Sync script
- `scripts/README-sync-setores.md` - Documentation
- `scripts/test-sync-setores.sh` - Test script

### Documentation
- `docs/stories/STORY-170-ux-polish-10-10.md` - Original story
- `CLAUDE.md` - Updated with sync instructions

## Benefits

1. **Resilience:** System works even when backend is down
2. **Transparency:** Users know when offline mode is active
3. **Recovery:** Users can manually trigger retry
4. **Maintainability:** Sync script keeps fallback current
5. **User Experience:** No empty dropdowns, no confusion
6. **Developer Experience:** Clear documentation and testing

## Future Enhancements (Optional)

- [ ] Store last successful fetch timestamp
- [ ] Show age of fallback data ("Lista de 15 dias atrás")
- [ ] Add service worker for true offline support
- [ ] Cache successful API responses in localStorage
- [ ] Add telemetry to track fallback usage frequency

---

**Implementation Completed:** 2026-02-07
**Tested By:** Automated test script + manual verification
**Approved By:** Development team
**Status:** ✅ Ready for production
