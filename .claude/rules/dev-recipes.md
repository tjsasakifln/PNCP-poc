# Development Recipes — SmartLic

Common step-by-step procedures for recurring development tasks.

## Adding a New Filter / Sector Keywords

1. Edit sector keywords in `backend/sectors_data.yaml` (not hardcoded in filter.py)
2. Update test_filter.py with new keyword coverage
3. Run `pytest -k test_filter` to verify no regressions
4. Run `node scripts/sync-setores-fallback.js --dry-run` if sector structure changed

## Modifying Excel Output

1. Update create_excel() in excel.py
2. Adjust column widths/styles as needed
3. Update example in PRD.md if structure changes
4. Test with various data sizes

## Changing LLM Prompt

1. Update system_prompt in llm.py
2. Adjust ResumoLicitacoes schema if output format changes
3. Update fallback logic to match new schema
4. Test with edge cases (0 bids, 100+ bids)

## Adding Environment Variables

1. Add to .env.example with documentation
2. Update config.py to load variable
3. Document in PRD.md section 10
4. Update README.md if user-facing

## Syncing Frontend Sector Fallback (STORY-170 AC15)

The frontend has a hardcoded fallback list of sectors that should be kept in sync with the backend's sector definitions.

**When to run:** Monthly, after adding new sectors, or before major releases.

```bash
# Dry run (preview changes without modifying files)
node scripts/sync-setores-fallback.js --dry-run

# Apply changes
node scripts/sync-setores-fallback.js

# Use custom backend URL
node scripts/sync-setores-fallback.js --backend-url https://api.smartlic.tech

# Test the script
bash scripts/test-sync-setores.sh
```

**What it does:**
1. Fetches sectors from backend `/setores` endpoint
2. Validates sector data structure (id, name, description)
3. Compares current frontend fallback vs new backend data
4. Updates `frontend/app/buscar/page.tsx` with new `SETORES_FALLBACK` list
5. Reports added, removed, and unchanged sectors

**Files involved:**
- `scripts/sync-setores-fallback.js` - Sync script
- `frontend/app/buscar/page.tsx` - Contains `SETORES_FALLBACK` constant
- `backend/sectors.py` - Source of truth for sector definitions
