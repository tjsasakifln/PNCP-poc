# STORY-240 Track 4: Quick Reference

## What Changed

### Frontend Hooks Now Support "abertas" Mode

**Key Behavior:**
- Default search mode is now "abertas" (open bids only)
- Default date range is 180 days (was 7 days)
- Date range auto-updates when switching modes
- UI shows info box instead of date pickers in "abertas" mode

## Code Locations

### 1. useSearchFilters Hook
**File:** `frontend/app/buscar/hooks/useSearchFilters.ts`

**New State:**
```typescript
const [modoBusca, setModoBusca] = useState<"abertas" | "publicacao">("abertas");
```

**Auto-Override Effect:**
```typescript
useEffect(() => {
  if (modoBusca === "abertas") {
    // Auto-set to last 180 days
  }
}, [modoBusca]);
```

**Computed Label:**
```typescript
const dateLabel = modoBusca === "abertas"
  ? "Mostrando licitações abertas para proposta"
  : "Período de publicação";
```

### 2. useSearch Hook
**File:** `frontend/app/buscar/hooks/useSearch.ts`

**Payload Addition:**
```typescript
body: JSON.stringify({
  // ... existing fields
  modo_busca: filters.modoBusca,  // NEW
  // ... rest of fields
})
```

### 3. SearchForm Component
**File:** `frontend/app/buscar/components/SearchForm.tsx`

**Conditional Rendering:**
```tsx
{modoBusca === "abertas" ? (
  <div className="p-3 bg-brand-blue-subtle rounded-card border border-brand-blue/20">
    <p className="text-sm font-medium text-brand-navy">{dateLabel}</p>
    <p className="text-xs text-ink-secondary mt-1">
      Buscando nos últimos 180 dias — somente licitações com prazo aberto
    </p>
  </div>
) : (
  // Standard date pickers
)}
```

## API Contract

### POST /api/buscar Payload
```json
{
  "ufs": ["SC", "PR"],
  "data_inicial": "2025-08-18",
  "data_final": "2026-02-14",
  "setor_id": "vestuario",
  "modo_busca": "abertas",  // NEW FIELD
  "status": "recebendo_proposta"
}
```

## User Experience

### Before (7-day default, always show pickers):
```
Data inicial: [2026-02-07]
Data final:   [2026-02-14]
```

### After (180-day default, context-aware UI):
```
┌───────────────────────────────────────────────────────────┐
│ Mostrando licitações abertas para proposta               │
│ Buscando nos últimos 180 dias — somente licitações com   │
│ prazo aberto                                              │
└───────────────────────────────────────────────────────────┘
```

## Testing Checklist

- [ ] Load /buscar page
- [ ] Verify default is "abertas" mode
- [ ] Verify date range is 180 days
- [ ] Verify info box shows instead of date pickers
- [ ] Execute search
- [ ] Verify payload includes `modo_busca: "abertas"`
- [ ] Backend processes request correctly

## Migration Notes

**No breaking changes:**
- Existing code continues to work
- Default expanded from 7 to 180 days (more permissive)
- Backend validates modo_busca with fallback to "abertas"
- UI gracefully degrades if backend doesn't support field

**When to retest:**
- After Track 5 (UI toggle) is implemented
- When switching modes should update UI dynamically

---

**Quick Commit:**
```bash
git add frontend/app/buscar/hooks/useSearchFilters.ts
git add frontend/app/buscar/hooks/useSearch.ts
git add frontend/app/buscar/components/SearchForm.tsx
git commit -m "feat(frontend): STORY-240 Track 4 - add modoBusca state and contextual date UI"
```
