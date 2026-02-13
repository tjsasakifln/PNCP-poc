# STORY-220: JSON Structured Logging + Log Forwarding Foundation

**Status:** Pending
**Priority:** P1 — Should-Fix Before Launch
**Sprint:** Sprint 3 (Weeks 4-5)
**Estimated Effort:** 1 day
**Source:** AUDIT-FRENTE-4-OBSERVABILITY (Risk #3, #9), AUDIT-CONSOLIDATED
**Squad:** team-bidiq-backend (dev, devops)

---

## Context

Backend logs use pipe-delimited plain text format:
```
2026-02-12 03:17:42 | ERROR    | a3f5b2c8-... | backend.auth | JWT token expired
```

Railway's log viewer provides basic text filtering, but there is no way to run structured queries (e.g., "show all ERROR logs where request_id=X and duration > 5000ms"). No `python-json-logger`, `structlog`, or equivalent is installed.

Additionally:
- Import-time logging race condition: `config.py` lines 222-227 emit logs before `setup_logging()` is called
- `SanitizedLogAdapter` exists but is underutilized — only `log_auth_event` uses it, most modules use raw `logger`

## Acceptance Criteria

### JSON Logging

- [ ] AC1: Install `python-json-logger` in `backend/requirements.txt`
- [ ] AC2: Update `setup_logging()` in `config.py` to use `pythonjsonlogger.jsonlogger.JsonFormatter`
- [ ] AC3: JSON output includes: `timestamp`, `level`, `request_id`, `logger_name`, `message`, `module`, `funcName`, `lineno`
- [ ] AC4: Production uses JSON format, development uses human-readable pipe-delimited format (configurable via `LOG_FORMAT=json|text` env var)
- [ ] AC5: All existing log statements work without modification (format change is transparent)

### Import-time Fix

- [ ] AC6: Move feature flag logging in `config.py` lines 222-227 to a function called AFTER `setup_logging()` (not at module import time)
- [ ] AC7: Verify no logs are emitted before `RequestIDFilter` is installed

### SanitizedLogAdapter Adoption

- [ ] AC8: Replace raw `logger` with `get_sanitized_logger()` in at minimum 3 critical modules: `auth.py`, `webhooks/stripe.py`, `routes/search.py`
- [ ] AC9: Ensure all PII-containing log calls go through sanitized logger

### Testing

- [ ] AC10: Test: JSON format produces valid JSON for each log line
- [ ] AC11: Test: `request_id` is present in JSON output during requests
- [ ] AC12: Test: `request_id` defaults to `"-"` outside request context
- [ ] AC13: Test: Development mode produces human-readable format

## Validation Metric

- `curl /health` and check Railway logs — each line is valid JSON
- `echo '<log_line>' | python -m json.tool` succeeds for every log line

## Risk Mitigated

- P1: Cannot run structured log queries for debugging
- P2: Import-time logging race condition
- P3: PII in logs from modules not using SanitizedLogAdapter

## File References

| File | Change |
|------|--------|
| `backend/requirements.txt` | Add `python-json-logger` |
| `backend/config.py` | JSON formatter + move import-time logs |
| `backend/auth.py` | Use sanitized logger |
| `backend/webhooks/stripe.py` | Use sanitized logger |
| `backend/routes/search.py` | Use sanitized logger |
