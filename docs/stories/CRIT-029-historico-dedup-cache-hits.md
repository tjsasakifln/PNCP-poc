# CRIT-029 — Histórico: Dedup Falha em Cache Hits

**Severity:** P1 — Blocker
**Origin:** UX Production Audit 2026-02-23 (Bug #1)
**Parent:** UX-351
**Status:** [x] Done — fix deployed (`.filter()` PG array literals + sorted arrays)

---

## Problema

O histórico de buscas mostra entradas duplicadas. Quando uma busca retorna resultado do cache (duração ~0.5s), ela cria uma segunda entrada ao lado da busca original (duração ~183s).

**Exemplo observado em produção (22/02/2026):**
- engenharia | Concluída | 20:40 | 0 resultados | **183.7s** ← busca real
- engenharia | Concluída | 20:40 | 0 resultados | **0.5s** ← cache hit (duplicata)
- vestuario | Concluída | 20:37 | 0 resultados | **183.6s** ← busca real
- vestuario | Concluída | 20:37 | 0 resultados | **0.5s** ← cache hit (duplicata)

O UX-351 implementou dedup no backend via session check, mas o mecanismo não detecta cache hits do mesmo search_id.

## Root Cause Provável

Duas chamadas POST `/buscar` são feitas para a mesma busca:
1. Primeira busca → backend processa → salva sessão → retorna em ~183s
2. Segunda busca (retry do SSE?) → backend retorna do cache → salva OUTRA sessão → retorna em ~0.5s

O dedup check provavelmente compara `search_id`, mas cada chamada tem um search_id diferente.

## Acceptance Criteria

- [x] **AC1**: Uma busca com mesmos parâmetros (setor + UFs + datas + modalidades) não cria entrada duplicada no histórico quando executada dentro de 5 minutos
- [x] **AC2**: Cache hits (duração < 2s) são mesclados com a busca original (update, não insert)
- [x] **AC3**: O dedup verifica (user_id + setor + ufs_hash + data_range) em vez de apenas search_id
- [x] **AC4**: Teste de integração: busca + retry → apenas 1 entrada no histórico
- [x] **AC5**: Teste unitário: cache hit com mesmos parâmetros → update em vez de insert
- [x] **AC6**: Zero regressão no baseline de testes existentes (14 fail / 5024 pass = pre-existing)

## Arquivos Prováveis

- `backend/routes/sessions.py` — lógica de criação de sessão
- `backend/routes/search.py` — `buscar_licitacoes()` cria sessão após resultado
- `backend/search_cache.py` — cache hit path
- `backend/tests/test_sessions.py` — testes de dedup

## Root Cause Confirmado

`supabase-py` v2.28.0 `.eq()` serializa Python lists como `"['SP', 'RJ']"` (Python repr)
em vez de `"{SP,RJ}"` (PostgreSQL array literal). O PostgREST não entende esse formato,
fazendo a query de dedup retornar sempre vazio → silently falls through to INSERT → duplicatas.

## Fix Aplicado

1. **`quota.py:register_search_session()`** — Substituiu `.eq("sectors", sectors)` e
   `.eq("ufs", sorted_ufs)` por `.filter("sectors", "eq", "{val1,val2}")` com formato
   de array literal PostgreSQL
2. **`quota.py:register_search_session()`** — Arrays (sectors, ufs) são sorted antes do INSERT
   para matching consistente
3. **`quota.py:save_search_session()`** — Mesma correção de sorted arrays no fallback INSERT
4. **`test_crit029_session_dedup.py`** — 12 testes reescritos com FluidMock (chain-agnostic)
   incluindo AC5: verifica que `.filter()` recebe formato PG array literal

## Referência

- Screenshot: `audit-09-historico-full.jpeg` (duplicatas visíveis)
- Audit doc: `docs/sessions/2026-02/2026-02-23-ux-production-audit.md`
