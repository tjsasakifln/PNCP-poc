# Error Handling Validation Checklist

## ✅ Frontend Error Handling

### Content-Type Validation
- [x] Check Content-Type header before parsing JSON
- [x] Implement fallback for non-JSON responses
- [x] Add try-catch around all `.json()` calls
- [x] Log parsing errors for debugging

### HTTP Status Code Handling
- [x] 401 Unauthorized → Redirect to OAuth
- [x] 403 Forbidden → Show permission error
- [x] 429 Rate Limit → Show rate limit message
- [x] 500 Server Error → Show generic error
- [x] Network errors → Show connection error

### User-Facing Messages
- [x] All error messages in Portuguese
- [x] Messages are user-friendly (no technical jargon)
- [x] Messages suggest next steps
- [x] Toast notifications work correctly

### Edge Cases
- [x] Empty licitacoes list handled
- [x] Missing session handled
- [x] Network timeout handled
- [x] HTML response handled (main fix)

## ✅ Backend Error Handling

### Response Format
- [ ] ALL endpoints return JSON (not HTML redirects)
- [ ] Error responses have consistent structure
- [ ] HTTP status codes are semantically correct
- [ ] Error messages are descriptive

### OAuth Error Handling
- [ ] Expired token → Return 401 with JSON
- [ ] Revoked token → Return 403 with JSON
- [ ] Missing token → Return 401 with JSON
- [ ] Refresh failure → Return 401 with JSON

### Google API Error Handling
- [ ] 403 Forbidden → Map to 403 JSON response
- [ ] 404 Not Found → Map to 404 JSON response
- [ ] 429 Rate Limit → Map to 429 JSON response
- [ ] 500 Server Error → Map to 500 JSON response
- [ ] HTML error pages → Convert to JSON

### Logging
- [ ] All errors logged with context
- [ ] Token errors logged (without exposing tokens)
- [ ] Request IDs included in logs
- [ ] Severity levels are appropriate

## ✅ Test Coverage

### Unit Tests
- [x] Test Content-Type checking
- [ ] Test HTML response handling
- [ ] Test all HTTP status codes
- [ ] Test token refresh failures

### Integration Tests
- [ ] Test full OAuth flow
- [ ] Test export with expired token
- [ ] Test export with revoked token
- [ ] Test export with Google API down

### E2E Tests
- [ ] Test user clicking export button
- [ ] Test OAuth redirect flow
- [ ] Test error toast notifications
- [ ] Test spreadsheet opening in new tab

## ✅ Performance

### Response Times
- [ ] Error responses return quickly (<500ms)
- [ ] No unnecessary API calls on errors
- [ ] Proper caching of error states

### Retry Logic
- [ ] Transient errors trigger retry (with backoff)
- [ ] Auth errors do NOT retry (redirect instead)
- [ ] Max retry attempts configured
- [ ] Retry delays are reasonable

## ✅ Security

### Token Handling
- [x] Tokens never logged in plaintext
- [x] Tokens encrypted at rest
- [x] Token refresh is automatic
- [x] Expired tokens handled gracefully

### Error Messages
- [x] No sensitive data in error messages
- [x] No stack traces exposed to users
- [x] Error details sanitized

## ✅ Documentation

### Code Documentation
- [ ] Error handling patterns documented
- [ ] Common errors documented
- [ ] Troubleshooting guide exists

### User Documentation
- [ ] Error messages explained
- [ ] OAuth flow documented
- [ ] FAQ updated

## ✅ Monitoring

### Error Tracking
- [ ] Sentry (or similar) configured
- [ ] Error rates monitored
- [ ] Alerts set up for error spikes
- [ ] Dashboard shows error trends

### Metrics
- [ ] Track 401/403/429/500 error rates
- [ ] Track token refresh failures
- [ ] Track export success rate
- [ ] Track MTTR (Mean Time To Recovery)

---

## Validation Steps

### Step 1: Local Testing
```bash
# Start backend
cd backend && python main.py

# Start frontend
cd frontend && npm run dev

# Test scenarios:
1. Export with valid token ✅
2. Export with expired token ✅
3. Export with revoked token
4. Export with Google API down (mock)
```

### Step 2: Automated Tests
```bash
# Backend tests
pytest backend/tests/test_html_error_response.py -v

# Frontend tests
npm test -- GoogleSheetsExportButton.test.tsx
```

### Step 3: Manual Validation
- [ ] Click export button
- [ ] Revoke OAuth access in Google
- [ ] Try export → Should show clear error
- [ ] Re-authorize → Export should work

### Step 4: Staging Validation
- [ ] Deploy to staging
- [ ] Test full flow end-to-end
- [ ] Monitor error logs
- [ ] Validate metrics

---

**Last Updated:** 2026-02-10
**Reviewed By:** Error Handler, Test Engineer
**Status:** 🟡 In Progress (3/5 sections complete)
