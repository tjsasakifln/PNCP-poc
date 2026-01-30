# 🔗 Integration Guide - Frontend ↔ Backend

This document provides step-by-step instructions for validating the integration between the Next.js frontend and FastAPI backend in the BidIQ Uniformes POC.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Starting the Application](#starting-the-application)
4. [Manual End-to-End Testing](#manual-end-to-end-testing)
5. [Automated E2E Testing](#automated-e2e-testing) ⭐ NEW
6. [Error Scenario Testing](#error-scenario-testing)
7. [Troubleshooting](#troubleshooting)
8. [Architecture Overview](#architecture-overview)

---

## Prerequisites

### Required Software

- **Docker Desktop 20.10+** with Docker Compose 2.0+
  - Download: https://www.docker.com/products/docker-desktop
  - Verify: `docker --version` and `docker-compose --version`

- **OpenAI API Key**
  - Get your key at: https://platform.openai.com/api-keys
  - Model required: `gpt-4.1-nano` (or compatible fallback)

### Optional (for local development without Docker)

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Git** for version control

---

## Environment Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/tjsasakifln/PNCP-poc.git
cd PNCP-poc
```

### Step 2: Configure Environment Variables

1. Copy the template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```bash
   # Required
   OPENAI_API_KEY=sk-your-actual-key-here

   # Optional (defaults are fine for POC)
   LOG_LEVEL=INFO
   PNCP_TIMEOUT=30
   LLM_MODEL=gpt-4.1-nano
   ```

3. Verify configuration:
   ```bash
   cat .env | grep OPENAI_API_KEY
   # Should output: OPENAI_API_KEY=sk-...
   ```

### Step 3: Verify Docker is Running

```bash
docker info
# Should show Docker server information without errors
```

**Troubleshooting:** If you see "Cannot connect to the Docker daemon", start Docker Desktop and try again.

---

## Starting the Application

### Full-Stack Mode (Recommended)

Start both frontend and backend with a single command:

```bash
docker-compose up --build
```

**Expected Output:**
```
bidiq-backend   | 2026-01-25 10:00:00 | INFO | FastAPI application initialized
bidiq-backend   | 2026-01-25 10:00:00 | INFO | Uvicorn running on http://0.0.0.0:8000
bidiq-frontend  | 2026-01-25 10:00:01 | ready - started server on 0.0.0.0:3000
```

**Services Available:**

**Production:**
- 🌐 **Frontend**: https://bidiq-uniformes.vercel.app ✅ **LIVE**
- ⚙️ **Backend API**: https://bidiq-backend-production.up.railway.app ✅ **LIVE**
- 📚 **API Docs**: https://bidiq-backend-production.up.railway.app/docs ✅ **LIVE**

**Local Development:**
- 🌐 **Frontend**: http://localhost:3000
- ⚙️ **Backend API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs (Swagger UI)

### Background Mode (Optional)

Run services in detached mode:

```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
# Press Ctrl+C to exit log view (services keep running)
```

Stop services:
```bash
docker-compose down
```

---

## Manual End-to-End Testing

### Happy Path User Journey

Follow these steps to validate the complete integration:

#### 1. Open the Application

**Production:** Navigate to https://bidiq-uniformes.vercel.app in your browser.

**Local Development:** Navigate to http://localhost:3000 in your browser.

**Expected UI:**
- Header: "BidIQ Uniformes"
- UF selection grid (27 state buttons)
- Date range inputs (default: last 7 days)
- Green "Buscar Licitações" button (enabled)

#### 2. Select States (UFs)

- **Test Action**: Click on 3 state buttons (e.g., SC, PR, RS)
- **Expected Behavior**:
  - ✅ Selected buttons turn green with white text
  - ✅ Counter shows "3 estado(s) selecionado(s)"
  - ✅ No errors displayed

**Optional Tests:**
- Click "Limpar" → All states deselected, error message appears
- Click "Selecionar todos" → All 27 states selected

#### 3. Set Date Range

- **Test Action**: Use the default date range (last 7 days)
- **Expected Behavior**:
  - ✅ Data inicial: 7 days ago (YYYY-MM-DD format)
  - ✅ Data final: Today's date
  - ✅ No validation errors

**Optional Tests:**
- Set data_final < data_inicial → Error: "Data final deve ser maior ou igual à data inicial"
- Set range > 30 days → Error: "Período máximo de 30 dias (selecionado: X dias)"

#### 4. Submit Search

- **Test Action**: Click "🔍 Buscar Licitações de Uniformes"
- **Expected Behavior**:
  - ✅ Button disabled during request
  - ✅ Loading skeleton appears
  - ✅ Message: "Consultando API do PNCP... isso pode levar alguns segundos."
  - ✅ No CORS errors in browser console (open DevTools → Console tab)

**Timing:** Request should complete in 5-30 seconds depending on PNCP API response time.

#### 5. Validate Results Display

After the request completes, verify the results section:

**Executive Summary Card** (Green border):
- ✅ Resumo text (GPT-4.1-nano generated summary in Portuguese)
- ✅ Statistics:
  - **Total licitações**: Integer count
  - **Valor total**: R$ formatted with Brazilian locale (e.g., "R$ 123.456")

**Urgency Alert** (Yellow box, conditional):
- ✅ Only appears if there are bids closing in < 7 days
- ✅ Format: "⚠️ X licitações com prazo < 7 dias"

**Highlights List** (Bullet points, conditional):
- ✅ Only appears if destaques array has items
- ✅ Header: "Destaques:"
- ✅ Each item is a bullet point with UF distribution or top bids

#### 6. Download Excel File

- **Test Action**: Click "📥 Download Excel (X licitações)"
- **Expected Behavior**:
  - ✅ File downloads immediately (no loading)
  - ✅ Filename: `licitacoes_uniformes_YYYY-MM-DD.xlsx`
  - ✅ File size > 10 KB (depends on results)

**Excel Validation:**
Open the downloaded file in Excel/LibreOffice:

**Main Sheet ("Licitações")**:
- ✅ Green header row with white text (#2E7D32)
- ✅ Columns (11 total):
  1. Código PNCP (hyperlinked to PNCP portal)
  2. Objeto da Compra
  3. Órgão
  4. UF
  5. Município
  6. Valor Estimado (R$ formatted)
  7. Modalidade
  8. Data Publicação
  9. Data Abertura
  10. Status
  11. Link PNCP
- ✅ Total row at bottom with SUM formula for Valor Estimado
- ✅ Frozen header row (scroll down to verify)

**Metadata Sheet**:
- ✅ Generation timestamp
- ✅ Filter statistics (total raw, total filtered, rejection reasons)
- ✅ Query parameters (UFs, date range)

---

## Automated E2E Testing

### Overview

Automated end-to-end tests validate the complete user journey using Playwright, ensuring system reliability and preventing regressions.

**Test Coverage:**
- ✅ Happy path user journey (AC1: 7 tests)
- ✅ LLM fallback scenarios (AC2: 4 tests)
- ✅ Form validation errors (AC3: 7 tests)
- ✅ Error handling (AC4: 7 tests)
- ✅ **Total: 25 E2E test cases**

**Performance Target:** Full suite completes in < 5 minutes (AC7)

### Quick Start

#### Option 1: Using NPM Scripts (Recommended)

```bash
cd frontend

# Run all E2E tests (headless)
npm run test:e2e

# Run with visible browser (debug)
npm run test:e2e:headed

# Run in interactive UI mode
npm run test:e2e:ui

# View last test report
npm run test:e2e:report
```

#### Option 2: Using Shell Script

```bash
# From project root
./scripts/run-e2e-tests.sh

# With options
./scripts/run-e2e-tests.sh --headed --report

# Against Docker Compose stack
./scripts/run-e2e-tests.sh --docker

# Show all options
./scripts/run-e2e-tests.sh --help
```

### Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `01-happy-path.spec.ts` | 7 | Complete user journey validation |
| `02-llm-fallback.spec.ts` | 4 | Offline/fallback summary generation |
| `03-validation-errors.spec.ts` | 7 | Client-side form validations |
| `04-error-handling.spec.ts` | 7 | Network errors, API failures |

### Running Specific Test Suites

```bash
# Run only happy path tests
npx playwright test 01-happy-path

# Run validation tests in debug mode
npx playwright test 03-validation --debug

# Run error handling with trace
npx playwright test 04-error --trace on
```

### CI/CD Integration

E2E tests run automatically on every pull request via GitHub Actions:

**Workflow:** `.github/workflows/e2e-tests.yml`

**When tests run:**
- On push to `main` branch
- On pull request creation/update
- Manual workflow dispatch

**Artifacts:**
- HTML test report (playwright-report/)
- Screenshots of failures
- Video recordings (on failure)
- Execution traces (on first retry)

### Test Reports

#### HTML Report (Interactive)

```bash
# Generate and view report
npm run test:e2e:report

# Or after any test run
npx playwright show-report
```

**Report includes:**
- Pass/fail status for each test
- Execution time
- Screenshots of failures
- Video playback
- Network logs
- Console output

#### JUnit XML (CI Integration)

Location: `frontend/test-results/junit.xml`

Used by GitHub Actions to display test results in PR checks.

### Environment Variables

E2E tests respect these environment variables:

```bash
# Frontend URL (default: http://localhost:3000)
export FRONTEND_URL=http://localhost:3000

# Backend URL (default: http://localhost:8000)
export BACKEND_URL=http://localhost:8000

# Run in CI mode (enables retries)
export CI=true
```

### Debugging Failed Tests

#### 1. Run in Headed Mode

```bash
npm run test:e2e:headed
```

Sees the browser during test execution.

#### 2. Use Debug Mode

```bash
npm run test:e2e:debug
```

Opens Playwright Inspector for step-by-step debugging.

#### 3. Check Screenshots

After a failed run:
```bash
ls -la frontend/test-results/
```

Screenshots saved with names like `test-name-chromium-failure.png`

#### 4. View Trace

```bash
npx playwright show-trace frontend/test-results/trace.zip
```

Interactive timeline of test execution with DOM snapshots.

### Writing New E2E Tests

#### Test Template

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('AC#.#: should do something', async ({ page }) => {
    // Arrange
    await page.getByRole('button', { name: 'SP' }).click();

    // Act
    await page.getByRole('button', { name: /Buscar/i }).click();

    // Assert
    await expect(page.getByText(/Resumo/i)).toBeVisible();
  });
});
```

#### Best Practices

1. **Use Semantic Selectors:**
   - ✅ `page.getByRole('button', { name: 'Submit' })`
   - ❌ `page.locator('#btn-123')`

2. **Wait for Elements:**
   - ✅ `await expect(element).toBeVisible()`
   - ❌ `await page.waitForTimeout(5000)`

3. **Handle Async:**
   - ✅ `await page.waitForSelector('text=/Ready/i')`
   - ❌ Implicit wait assumptions

4. **Cleanup State:**
   - Use `test.beforeEach()` for fresh state
   - Avoid test interdependencies

5. **Descriptive Names:**
   - ✅ `AC3.1: should show error when no UFs selected`
   - ❌ `test 1`

### Performance Optimization

**Current Performance (as of Issue #27):**

- Average test duration: ~8-12s per test
- Full suite: ~4 minutes (25 tests)
- Parallelization: Disabled for E2E stability
- Retries: 0 (local), 2 (CI)

**Future Optimizations:**

- Mock PNCP API for faster tests
- Parallel execution with test isolation
- Visual regression testing
- Accessibility testing with @axe-core/playwright

### Troubleshooting E2E Tests

#### Tests Timeout

**Symptom:** Tests fail with "Timeout 60000ms exceeded"

**Solutions:**
- Increase timeout in `playwright.config.ts`
- Check if services are running (`docker-compose ps`)
- Verify network connectivity to PNCP API

#### Browser Not Installed

**Symptom:** "Executable doesn't exist at ..."

**Solution:**
```bash
npx playwright install chromium
```

#### Port Already in Use

**Symptom:** "Error: listen EADDRINUSE: address already in use :::3000"

**Solutions:**
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9

# Or use different port
export FRONTEND_URL=http://localhost:3001
```

#### Flaky Tests

**Solutions:**
- Add explicit waits: `await page.waitForLoadState('networkidle')`
- Use `test.retry(2)` for unstable external APIs
- Check race conditions in application code

---

## Error Scenario Testing

### Scenario 1: Backend Unavailable

**Setup:**
```bash
docker-compose stop backend
```

**Test:**
1. Refresh frontend (http://localhost:3000)
2. Submit search with valid inputs
3. **Expected**: Red error message appears:
   - "Erro ao buscar licitações" or "Erro interno do servidor"
   - ✅ No application crash
   - ✅ User can modify inputs and retry

**Cleanup:**
```bash
docker-compose start backend
```

### Scenario 2: Validation Errors

**Test Cases:**

| Test | Action | Expected Error |
|------|--------|---------------|
| No UFs | Click "Limpar", then submit | "Selecione pelo menos um estado" (red text) |
| Inverted dates | Set data_inicial = 2024-02-01, data_final = 2024-01-01 | "Data final deve ser maior ou igual à data inicial" |
| Range > 30 days | Set 45-day range | "Período máximo de 30 dias (selecionado: 45 dias)" |

**Expected Behavior:**
- ✅ Submit button is **disabled** when errors exist
- ✅ Errors disappear when user fixes input
- ✅ Errors display immediately (real-time validation via useEffect)

### Scenario 3: PNCP API Timeout

**Note:** This scenario requires backend modification or mock. Document for future automated E2E tests.

**Expected Behavior:**
- Backend should retry up to 5 times with exponential backoff
- If all retries fail, return 500 error to frontend
- Frontend displays user-friendly error message

---

## Troubleshooting

### Docker Issues

**Problem:** `Cannot connect to the Docker daemon`

**Solution:**
1. Start Docker Desktop
2. Wait for Docker icon to show "Running"
3. Retry `docker-compose up`

---

**Problem:** `port 8000 is already allocated`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Stop conflicting process or change BACKEND_PORT in .env
echo "BACKEND_PORT=8001" >> .env
docker-compose up
```

---

**Problem:** `service "backend" didn't complete successfully: exit 1`

**Solution:**
```bash
# View backend logs for errors
docker-compose logs backend

# Common causes:
# 1. Missing OPENAI_API_KEY → Check .env file
# 2. Python import errors → Rebuild: docker-compose build --no-cache
# 3. Port conflict → See port allocation issue above
```

---

### Frontend Issues

**Problem:** CORS error in browser console

**Solution:**
Verify backend CORS configuration in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be * for local dev
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If still failing:
1. Check backend is running: `curl http://localhost:8000/health`
2. Check frontend is using correct URL: `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` in `.env`

---

**Problem:** Results not displaying after successful request

**Solution:**
1. Open browser DevTools → Network tab
2. Filter by `buscar`
3. Check response status:
   - **200**: Verify response JSON structure matches `BuscaResult` interface
   - **500**: Check backend logs: `docker-compose logs backend`
   - **4xx**: Validation error - verify request payload

---

### API Issues

**Problem:** "Erro ao buscar licitações" despite valid inputs

**Solution:**
1. Check backend logs:
   ```bash
   docker-compose logs backend | tail -50
   ```

2. Common causes:
   - **PNCP API timeout**: Increase `PNCP_TIMEOUT` in `.env`
   - **Rate limiting**: PNCP returned 429 - retry after a few minutes
   - **Invalid API response**: PNCP API structure changed - check `pncp_client.py`

---

**Problem:** GPT summary is generic or irrelevant

**Solution:**
This is expected if:
- **No results found**: LLM receives empty list, generates fallback summary
- **Fallback mode active**: `OPENAI_API_KEY` is missing or invalid
- **Token limit exceeded**: >50 bids sent to LLM - truncation occurs

To verify LLM is working:
```bash
docker-compose logs backend | grep "Generating LLM summary"
# Should show "Generating LLM summary for X bids"
```

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                     http://localhost:3000                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP GET /
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NEXT.JS FRONTEND                           │
│              (Docker Container: bidiq-frontend)                 │
├─────────────────────────────────────────────────────────────────┤
│  • app/page.tsx          - Main UI (UF selection, date range)   │
│  • app/api/buscar/       - Backend proxy route                  │
│  • app/api/download/     - Excel streaming route                │
│  • app/types.ts          - TypeScript interfaces                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP POST /api/buscar
                 │ { ufs: [...], data_inicial, data_final }
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│              (Docker Container: bidiq-backend)                  │
├─────────────────────────────────────────────────────────────────┤
│  • main.py               - FastAPI app + CORS                   │
│  • POST /buscar          - Main search endpoint                 │
│  • pncp_client.py        - PNCP API client (retry logic)        │
│  • filter.py             - Keyword matching engine              │
│  • llm.py                - GPT-4.1-nano integration             │
│  • excel.py              - Excel generator (openpyxl)           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP GET /api/consulta/v1/contratacoes/publicacao
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PNCP API                                 │
│              https://pncp.gov.br/api/...                        │
├─────────────────────────────────────────────────────────────────┤
│  • Government procurement database                              │
│  • Rate limited (429 responses)                                 │
│  • Unstable (requires retry logic)                              │
│  • Pagination: 500 items/page max                               │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Step 1: User submits search**
```
Frontend (page.tsx)
  → validateForm() checks:
    - Min 1 UF selected
    - data_final >= data_inicial
    - Range <= 30 days
  → If valid: fetch("/api/buscar", ...)
```

**Step 2: Frontend proxy to backend**
```
API Route (/api/buscar/route.ts)
  → Validates request body (Pydantic schemas)
  → Proxies to backend: POST http://backend:8000/buscar
  → Caches Excel buffer with UUID (10min TTL)
  → Returns: { resumo, download_id }
```

**Step 3: Backend orchestration**
```
Backend (main.py /buscar endpoint)
  ① Fetch from PNCP:
     pncp_client.fetch_all() → Generator with pagination
     • Retry logic (exponential backoff)
     • Rate limit handling (429)

  ② Filter results:
     filter.filter_batch() → Fail-fast sequential filters:
     • UF match
     • Value range (R$ 50k - R$ 5M)
     • Keyword match (uniforme, jaleco, fardamento, ...)
     • Exclusion keywords (false positive prevention)

  ③ Generate summary:
     llm.gerar_resumo() → OpenAI GPT-4.1-nano
     • Structured output (Pydantic)
     • Token optimization (<500 tokens)
     • Fallback: gerar_resumo_fallback() if API fails

  ④ Create Excel:
     excel.create_excel() → openpyxl with styling
     • Main sheet: 11 columns, formatted
     • Metadata sheet: stats and query params
     • Returns BytesIO buffer

  ⑤ Return response:
     BuscaResponse(resumo, excel_base64, totals)
```

**Step 4: Frontend displays results**
```
Frontend (page.tsx)
  → setResult(data) triggers re-render
  → Results section displays:
    - Executive summary card (green)
    - Statistics (total, valor_total)
    - Urgency alert (if < 7 days)
    - Highlights (bullet list)
    - Download button → GET /api/download?id=...
```

### Network Communication

**Docker Compose Network: `bidiq-network`**
- Frontend container: `bidiq-frontend:3000`
- Backend container: `bidiq-backend:8000`
- Bridge network allows service-to-service communication
- External access via host ports (localhost:3000, localhost:8000)

**Environment Variables:**

**Production:**
- Frontend: `NEXT_PUBLIC_BACKEND_URL=https://bidiq-backend-production.up.railway.app`
- Backend: `OPENAI_API_KEY` for LLM integration (set in Railway dashboard)

**Local Development:**
- Frontend: `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` (from host browser perspective)
- Backend: `OPENAI_API_KEY` for LLM integration (from .env file)

**Health Checks:**
- Backend: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"`
- Frontend: `wget --spider http://localhost:3000/health`
- Intervals: 30s, retries: 3, start period: 10s

---

## Integration Checklist

Use this checklist to verify complete integration:

### Setup Phase
- [ ] Docker Desktop installed and running
- [ ] `.env` file created with `OPENAI_API_KEY`
- [ ] `docker-compose up --build` starts without errors
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend accessible at http://localhost:8000
- [ ] API docs accessible at http://localhost:8000/docs

### Happy Path Testing
- [ ] UI displays correctly (UFs, dates, button)
- [ ] UF selection works (click toggles, counter updates)
- [ ] Date validation works (real-time errors)
- [ ] Form submission triggers loading state
- [ ] No CORS errors in browser console
- [ ] Results display after search completes
- [ ] Summary card shows statistics
- [ ] Download button downloads Excel file
- [ ] Excel file opens without errors
- [ ] Excel contains formatted data (green header, columns, total row)

### Error Handling
- [ ] No UFs selected → Inline error + disabled button
- [ ] Invalid date range → Inline error + disabled button
- [ ] Backend down → Friendly error message
- [ ] PNCP API timeout → Retry logic executes (check logs)

### Documentation
- [ ] Integration guide reviewed and validated
- [ ] Screenshots taken of working integration
- [ ] Troubleshooting steps tested

---

## Next Steps

After completing this manual validation:

1. **Automated E2E Tests** (Issue #27)
   - Use Playwright or Cypress
   - Automate happy path user journey
   - Add CI/CD pipeline integration

2. **Production Deployment** (Issue #31)
   - Deploy backend to Railway/Render
   - Deploy frontend to Vercel
   - Configure production environment variables
   - Restrict CORS to frontend domain only

3. **README Update** (Issue #1)
   - Add "Quick Start" section
   - Link to this integration guide
   - Include architecture diagram

---

## Contributing

Found an integration issue? Please report it:

1. Open GitHub Issue with label `integration`
2. Include:
   - Environment (OS, Docker version)
   - Steps to reproduce
   - Expected vs actual behavior
   - Browser console errors (if applicable)
   - Docker logs (`docker-compose logs`)

---

**Last Updated:** 2026-01-25
**Validated By:** Automated review protocol (Issue #26)
**Next Review:** After PR #X merge
