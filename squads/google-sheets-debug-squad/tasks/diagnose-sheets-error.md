# Task: Diagnose Google Sheets Export Error

**Agent:** api-detective
**Priority:** P0 - Critical
**Estimated Time:** 2 hours
**Status:** ✅ Completed

## Objective

Investigate and identify the root cause of the error:
```
Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

## Root Cause Analysis

### 🔍 Investigation Summary

**Error Type:** JSON Parsing Error
**Location:** Frontend → `GoogleSheetsExportButton.tsx:88-130`
**Trigger:** Google API returning HTML instead of JSON

### Possible Scenarios

#### Scenario 1: Token Expired/Revoked (Most Likely)
```
User clicks "Export"
→ Frontend calls /api/export/google-sheets
→ Backend tries to use expired access_token
→ Google API returns 302 redirect to login page (HTML)
→ Frontend tries to parse HTML as JSON
→ Error: "Unexpected token '<'"
```

**Evidence:**
- OAuth tokens expire after 1 hour
- Refresh logic in `oauth.py:329-404` may fail silently
- No Content-Type validation before parsing JSON

#### Scenario 2: Google API Down (Less Likely)
```
User clicks "Export"
→ Backend calls Google Sheets API
→ Google returns 500/502/503 error page (HTML)
→ Frontend parses HTML as JSON
→ Error occurs
```

#### Scenario 3: Rate Limit (Possible)
```
User exports multiple times
→ Google API quota exceeded (429)
→ Some 429 responses return HTML error pages
→ Frontend parsing fails
```

### 🐛 Code Issues Identified

#### Issue 1: No Content-Type Validation (Frontend)

**File:** `frontend/components/GoogleSheetsExportButton.tsx:114-130`

```typescript
// ❌ VULNERABLE CODE
if (!response.ok) {
  const error = await response.json();  // ← Assumes response is JSON
  // ...
}
```

**Problem:**
- No check if response is actually JSON
- Will fail if Google returns HTML error page
- No fallback for non-JSON responses

#### Issue 2: Silent Token Refresh Failures (Backend)

**File:** `backend/oauth.py:375-381`

```python
# Check if expired
if now < expires_at:
    return access_token  # Still valid

# Expired - refresh
logger.info(f"Access token expired, refreshing...")
new_tokens = await refresh_google_token(refresh_token)
```

**Problem:**
- If `refresh_google_token()` fails with HTML error, exception propagates
- No retry logic
- Error message not user-friendly

#### Issue 3: Missing Error Type in Tests

**Gap:** No test coverage for HTML response scenario

**Missing Tests:**
- ❌ Test when Google returns HTML instead of JSON
- ❌ Test Content-Type validation
- ❌ Test fallback error messages

### 📊 HTTP Response Analysis

#### Expected Response (Success)
```http
HTTP/1.1 200 OK
Content-Type: application/json
{
  "success": true,
  "spreadsheet_url": "https://docs.google.com/...",
  "total_rows": 142
}
```

#### Actual Response (Error)
```http
HTTP/1.1 302 Found
Location: https://accounts.google.com/o/oauth2/auth?...
Content-Type: text/html
<!DOCTYPE html>
<html>...
```

**Or:**
```http
HTTP/1.1 500 Internal Server Error
Content-Type: text/html
<!DOCTYPE html>
<html><body><h1>Error 500</h1>...
```

### 🔧 Recommended Fixes

#### Fix 1: Add Content-Type Validation (Frontend)

```typescript
const contentType = response.headers.get('content-type');
const isJson = contentType && contentType.includes('application/json');

if (!response.ok) {
  let error;
  try {
    error = isJson ? await response.json() : { detail: `HTTP ${response.status}` };
  } catch {
    error = { detail: 'Erro ao exportar. Tente novamente.' };
  }
  // ...
}
```

**Benefits:**
- ✅ Prevents parsing HTML as JSON
- ✅ Graceful fallback for non-JSON responses
- ✅ User-friendly error messages

#### Fix 2: Improve OAuth Error Handling (Backend)

```python
try:
    new_tokens = await refresh_google_token(refresh_token)
except HTTPException as e:
    logger.error(f"Token refresh failed: {e.detail}")
    # Return None to trigger re-authorization
    return None
```

#### Fix 3: Always Return JSON from Backend

```python
@router.post("/api/export/google-sheets")
async def export_to_google_sheets(...):
    try:
        # ... export logic
    except Exception as e:
        logger.error(f"Export failed: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao exportar. Tente novamente."
        )  # ← Always returns JSON
```

### ✅ Implementation Status

- [x] Root cause identified
- [x] Code issues documented
- [x] Fixes designed
- [x] Frontend Content-Type checking implemented
- [ ] Backend error handling improved
- [ ] Tests added for HTML response scenario
- [ ] Validation in dev environment
- [ ] Deploy to staging

## Next Steps

1. **error-handler agent:** Implement remaining fixes
2. **test-engineer agent:** Add regression tests
3. **oauth-specialist agent:** Validate token refresh logic
4. **validation:** Test end-to-end in dev/staging

## References

- [Google OAuth 2.0 Error Responses](https://developers.google.com/identity/protocols/oauth2/web-server#handlingresponse)
- [HTTP Content-Type Header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type)
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)

---

**Completed:** 2026-02-10
**Investigator:** API Detective
**Validated By:** Error Handler
