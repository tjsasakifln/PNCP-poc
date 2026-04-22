# STORY-BTS-013: story_221 asyncio.sleep retry test investigation

**Priority:** P3 — Drift cluster tail (non-blocking, xfail strict=False)
**Effort:** XS (~1-2h investigation spike)
**Squad:** @qa + @dev (review of supabase_client circuit breaker state leak)
**Status:** Draft (assigned to next sweep)
**Discovered:** 2026-04-22 during Wave G drift cluster sweep (generic-sparrow plan)
**Source:** STORY-BTS-011 cluster identification + STORY-BTS-012 attempted sweep

---

## Contexto

Wave G of generic-sparrow plan (drift cluster tail sweep) successfully closed 3 of 4 BTS-011 clusters:

- ✅ `stab005 level2_relaxation` — fixture bug ("material" is not substring of "materiais"; corrected to "materia")
- ✅ `story_257a T4+T5 health canary` — test contract drift (`health_canary` returns bool, not dict; AsyncMock vs MagicMock for response)
- ✅ `feature_flags_admin ttl_cache` — concern non-reproducible; xfail removed
- ⏸ `story_221 asyncio.sleep retry` — test TIMES OUT (>15s) when forced via `--runxfail`

The story_221 cluster requires deeper investigation that exceeds the 1h budget allocated to Wave G per spike-first decision rule.

## Symptoms

```bash
$ pytest tests/test_story_221_async_fixes.py::test_check_user_roles_uses_asyncio_sleep_on_retry -xvs --runxfail --timeout=15
+++++++++++++++++++++++++++++++++++ Timeout ++++++++++++++++++++++++++++++++++++
```

Test scenario:
- Patches `supabase_client.get_supabase` with mock that side_effects 2 Exceptions
- Patches `authorization.asyncio.sleep` with AsyncMock
- Calls `_check_user_roles("user-123")` and expects `mock_async_sleep.assert_called_once_with(0.3)`
- Expects result `(False, False)` after exhausting retries

Observed: hangs / times out instead of executing the retry path.

## Hypotheses (NOT verified — investigation needed)

1. **Circuit breaker state leak:** `supabase_client.supabase_cb` is module-level. Prior tests in the suite may have tripped it OPEN; `_check_user_roles` short-circuits on `CircuitBreakerOpenError` without retry → `asyncio.sleep` never called.
2. **`asyncio.to_thread` blocking:** `sb_execute` uses `await asyncio.to_thread(query.execute)` where `query.execute` is the mocked side_effect=Exception. Threading + Exception interaction may deadlock.
3. **Test fixture `mock_sb` chain mismatch:** The mock chains `mock_sb.return_value.table().select().eq().single().execute().side_effect = [...]`. If `sb_execute` doesn't call `.execute()` directly (instead passes the unexecuted query to the thread), the side_effect never triggers.
4. **Pool active counter leak:** `SUPABASE_POOL_ACTIVE.dec()` in finally block; if not balanced with .inc() somewhere, may cause unrelated state issue.

## Investigation steps

### Phase 1 — Isolate (≤30min)
- [ ] Run test with circuit breaker explicit reset: prepend `supabase_cb.reset()` and `for cb in (read_cb, write_cb, rpc_cb): cb.reset()`
- [ ] Add `print()` traces in `_check_user_roles` to identify which line is reached/blocked
- [ ] Try without `--runxfail`: does it actually XFAIL (expected) or XPASS (unexpected)?

### Phase 2 — Root cause (1-2h)
- [ ] If hypothesis 1: add CB reset to test fixture or use isolated CB instance for test
- [ ] If hypothesis 2: replace `asyncio.to_thread` mock or use `monkeypatch.setattr("asyncio.to_thread", ...)` to bypass
- [ ] If hypothesis 3: revise mock chain to match actual call path of `sb_execute`
- [ ] If hypothesis 4: add explicit `_pool_active_count` reset in test fixture

### Phase 3 — Fix
- [ ] Either: rewrite test with CB reset + correct mock chain, remove xfail
- [ ] Or: replace test with smaller integration that exercises the retry path without full Supabase chain (test the retry logic directly)

## Definition of Done

- [ ] Root cause identified (one of the 4 hypotheses confirmed or new one documented)
- [ ] Test passes deterministically without xfail or `--runxfail`
- [ ] Test included in standard `pytest tests/` run + no regression in other story_221 tests
- [ ] xfail marker removed from `tests/test_story_221_async_fixes.py`
- [ ] Story file updated with `Status: Done` + Change Log

## Out of scope

- Refactoring `supabase_client.sb_execute` or circuit breaker design
- Adding new tests for retry logic (this is just to fix the existing one)
- Changing `_check_user_roles` retry semantics in production code

## Linked artifacts

- `backend/tests/test_story_221_async_fixes.py:53-83` — the xfailing test
- `backend/authorization.py:35-107` — `check_user_roles` with retry + asyncio.sleep
- `backend/supabase_client.py:592-733` — `sb_execute` with circuit breaker logic
- STORY-BTS-011, STORY-BTS-012 (predecessors)

## Change Log

| Data | Quem | Mudança |
|------|------|---------|
| 2026-04-22 | @qa (generic-sparrow) | Story criada após Wave G fechou 3/4 clusters; story_221 fica para próximo sprint |
