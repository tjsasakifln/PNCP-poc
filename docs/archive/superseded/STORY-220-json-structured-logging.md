# STORY-220: JSON Structured Logging + Log Forwarding Foundation

**Status:** Done
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

- [x] AC1: Install `python-json-logger` in `backend/requirements.txt`
- [x] AC2: Update `setup_logging()` in `config.py` to use `pythonjsonlogger.jsonlogger.JsonFormatter`
- [x] AC3: JSON output includes: `timestamp`, `level`, `request_id`, `logger_name`, `message`, `module`, `funcName`, `lineno`
- [x] AC4: Production uses JSON format, development uses human-readable pipe-delimited format (configurable via `LOG_FORMAT=json|text` env var)
- [x] AC5: All existing log statements work without modification (format change is transparent)

### Import-time Fix

- [x] AC6: Move feature flag logging in `config.py` lines 222-227 to a function called AFTER `setup_logging()` (not at module import time)
- [x] AC7: Verify no logs are emitted before `RequestIDFilter` is installed

### SanitizedLogAdapter Adoption

- [x] AC8: Replace raw `logger` with `get_sanitized_logger()` in at minimum 3 critical modules: `auth.py`, `webhooks/stripe.py`, `routes/search.py`
- [x] AC9: Ensure all PII-containing log calls go through sanitized logger

### Testing

- [x] AC10: Test: JSON format produces valid JSON for each log line
- [x] AC11: Test: `request_id` is present in JSON output during requests
- [x] AC12: Test: `request_id` defaults to `"-"` outside request context
- [x] AC13: Test: Development mode produces human-readable format

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
| `backend/requirements.txt` | Add `python-json-logger>=2.0.4,<3.0.0` |
| `backend/config.py` | JSON formatter + `LOG_FORMAT` env var + `log_feature_flags()` function |
| `backend/main.py` | Import and call `log_feature_flags()` after `setup_logging()` |
| `backend/auth.py` | Use `get_sanitized_logger()` |
| `backend/webhooks/stripe.py` | Use `get_sanitized_logger()` |
| `backend/routes/search.py` | Use `get_sanitized_logger()` |
| `backend/tests/test_structured_logging.py` | 16 tests covering AC3, AC4, AC5, AC6, AC7, AC8, AC9, AC10-AC13 |
| `.env.example` | Add `LOG_FORMAT` and `LOG_LEVEL` documentation |
