# Sync Setores Fallback Script

## Purpose

This script synchronizes the hardcoded fallback sector list in the frontend with the backend's sector definitions. It ensures that when the backend API is unavailable, the frontend can still display an up-to-date list of procurement sectors.

**Related:** STORY-170 AC15 - Fallback Hardcoded de Setores

## Why This Exists

The frontend's `/buscar` page has a resilience mechanism:

1. **Primary:** Fetch sectors from backend API (`/api/setores`)
2. **Retry:** If fetch fails, retry 3 times with exponential backoff
3. **Fallback:** After 3 failures, use hardcoded `SETORES_FALLBACK` list

The hardcoded list can become outdated when new sectors are added to the backend. This script keeps them synchronized.

## Prerequisites

- Node.js 18+
- Backend server running at `http://localhost:8000` (or custom URL)
- Backend must have `/setores` endpoint operational

## Usage

### Basic Usage

```bash
# Sync with local backend
node scripts/sync-setores-fallback.js
```

### Dry Run (Preview Changes)

```bash
# See what would change without modifying files
node scripts/sync-setores-fallback.js --dry-run
```

### Custom Backend URL

```bash
# Sync with production backend
node scripts/sync-setores-fallback.js --backend-url https://api.smartlic.tech
```

## When to Run

Run this script:

- **Monthly** - Scheduled maintenance (recommended)
- **After adding new sectors** to backend
- **Before major releases** - Ensure frontend fallback is current
- **When backend structure changes** - If sector fields are modified

## What It Does

1. **Fetches** sectors from backend `/setores` endpoint
2. **Validates** sector data structure (id, name, description)
3. **Compares** current frontend fallback vs new backend data
4. **Updates** `frontend/app/buscar/page.tsx` with new fallback list
5. **Reports** added, removed, and unchanged sectors

## Output Example

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
   File: D:\pncp-poc\frontend\app\buscar\page.tsx

============================================================
  ✅ Synchronization complete!
============================================================

📝 Next steps:
   1. Review the changes in page.tsx
   2. Test the frontend with: npm run dev
   3. Commit the changes if everything looks good
```

## Error Handling

### Backend Not Running

```
❌ Failed to fetch sectors: fetch failed

💡 Make sure the backend is running:
   cd backend && uvicorn main:app --reload
```

**Solution:** Start the backend server

### Invalid Response Format

```
❌ Failed to fetch sectors: Invalid response format: missing "setores" array
```

**Solution:** Ensure backend `/setores` endpoint returns correct format:

```json
{
  "setores": [
    { "id": "vestuario", "name": "Vestuário e Uniformes", "description": "..." },
    ...
  ]
}
```

### Cannot Find SETORES_FALLBACK

```
❌ Failed to update frontend: Could not find SETORES_FALLBACK constant in page.tsx
```

**Solution:** Verify that `frontend/app/buscar/page.tsx` contains:

```typescript
// Hardcoded fallback list of sectors
const SETORES_FALLBACK: Setor[] = [
  ...
];
```

## Testing

After running the script:

1. **Verify Changes:**
   ```bash
   git diff frontend/app/buscar/page.tsx
   ```

2. **Test Frontend:**
   ```bash
   cd frontend
   npm run dev
   # Visit http://localhost:3000/buscar
   # Simulate backend failure and verify fallback works
   ```

3. **Run Tests:**
   ```bash
   npm test -- page.test.tsx
   ```

## Automation

### GitHub Actions (Recommended)

Create `.github/workflows/sync-setores.yml`:

```yaml
name: Sync Setores Fallback

on:
  schedule:
    # Run monthly on the 1st at 00:00 UTC
    - cron: '0 0 1 * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm install

      - name: Start backend
        run: |
          cd backend
          pip install -r requirements.txt
          uvicorn main:app &
          sleep 5

      - name: Sync setores
        run: node scripts/sync-setores-fallback.js

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'chore: sync setores fallback list'
          title: '[Automated] Sync Setores Fallback'
          body: |
            Monthly synchronization of fallback sector list.

            This PR updates the hardcoded `SETORES_FALLBACK` in the frontend
            to match the current backend sector definitions.
          branch: automated/sync-setores
          labels: automation, frontend, maintenance
```

### Cron Job (Local/Server)

```bash
# Add to crontab (run monthly on 1st at 2 AM)
0 2 1 * * cd /path/to/pncp-poc && node scripts/sync-setores-fallback.js >> /var/log/sync-setores.log 2>&1
```

## Maintenance

- **Script Location:** `scripts/sync-setores-fallback.js`
- **Target File:** `frontend/app/buscar/page.tsx`
- **Backend Endpoint:** `/setores` (defined in `backend/main.py`)
- **Sector Definitions:** `backend/sectors.py`

## Troubleshooting

### Script Fails Silently

**Check Node.js version:**
```bash
node --version  # Should be 18+
```

### Permissions Error

**Make script executable:**
```bash
chmod +x scripts/sync-setores-fallback.js
```

### Network Errors

**Verify backend is accessible:**
```bash
curl http://localhost:8000/setores
```

## Related Files

- `frontend/app/buscar/page.tsx` - Contains `SETORES_FALLBACK` constant
- `frontend/app/api/setores/route.ts` - Frontend API proxy
- `backend/main.py` - Backend `/setores` endpoint
- `backend/sectors.py` - Source of truth for sector definitions
- `docs/stories/STORY-170-ux-polish-10-10.md` - Original story

## Support

For issues or questions:
1. Check error messages carefully
2. Verify backend is running and accessible
3. Review `frontend/app/buscar/page.tsx` structure
4. Consult STORY-170 AC15 acceptance criteria

---

**Last Updated:** 2026-02-07
**Maintainer:** Development Team
**STORY:** STORY-170 AC15
