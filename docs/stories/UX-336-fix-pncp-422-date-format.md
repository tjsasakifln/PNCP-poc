# Story UX-336: Fix PNCP 422 Date Format Issue

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🔴 P0 CRITICAL
**Story Points:** 5 SP
**Owner:** @dev
**Status:** 🔴 TODO

## Problem
PNCP retorna HTTP 422 "Período maior que 365 dias" para período de apenas 10 dias. Bug no parser de datas da API.

**Evidência:**
```
PNCP 422: "Período inicial e final maior que 365 dias."
Params: dataInicial=20260208, dataFinal=20260218
Raw dates: 2026-02-08 → 2026-02-18 (10 dias)
```

## Acceptance Criteria
- [ ] Testar 4 formatos: YYYYMMDD, YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
- [ ] Retry automático com formato alternativo se 422
- [ ] Cache do formato aceito (TTL 24h)
- [ ] Log detalhado de cada tentativa
- [ ] Telemetria Sentry do formato correto
- [ ] Fallback se todos falharem: "Reduza o período"

## Implementation
```python
formats = [DateFormat.YYYYMMDD, DateFormat.ISO_DASH, ...]
for fmt in formats:
    try:
        return await fetch_pncp(format_date(date, fmt))
    except HTTP422:
        continue
```

**Files:** `backend/pncp_client.py`, `backend/tests/test_pncp_date_formats.py`
