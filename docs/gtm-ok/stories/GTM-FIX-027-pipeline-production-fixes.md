# GTM-FIX-027: Pipeline Production Fixes — Zero Results + Timeout + PCP Failure + ComprasGov v3

**Priority:** P0 (BLOCKER — search is unusable in production)
**Score Impact:** D02 3→6 (revenue path unblocked), D09 4→7 (data quality)
**Estimated Effort:** 6-8 hours (5 tracks, 3 critical + 1 medium + 1 optional)
**Sprint:** Current (immediate)
**Subsumes:** GTM-FIX-026 (ComprasGov v3 migration, deferred from GTM-FIX-025 T4)
**Reviewed by:** @architect (critical review 2026-02-17)

---

## Context & Evidence

Production testing on 2026-02-17 revealed **3 critical bugs** that make search completely unusable, plus **1 deferred item** from GTM-FIX-025 T4 (ComprasGov v3) incorporated here.

### Bugs Found

1. **100% of results filtered out** — `status_mismatch` rejects every bid (226/226 and 57/57)
2. **Search times out (502)** — 1 UF (SP) causes 502 Bad Gateway after 120s+ because PNCP pagination fetches 20 items/page instead of 500
3. **PCP source always fails** — Portal de Compras Publicas returns error on every search (root cause unknown — needs diagnostic logging first)
4. **ComprasGov v3 not migrated** — (from GTM-FIX-025 T4, deferred) ComprasGov v1 permanently disabled; v3 API available but not integrated

### Production Evidence

```
# Search 1: Vestuario, 27 UFs — ComprasGov still enabled via env var
sources_attempted: ["PNCP", "COMPRAS_GOV", "PORTAL_COMPRAS"]
sources_succeeded: ["PNCP"]
sources_failed: ["COMPRAS_GOV", "PORTAL_COMPRAS"]
total_results: 226, total_filtered: 0  <- ZERO results after filtering
latency_ms: 51242

# Search 2: Software, 3 UFs (SP, RJ, MG)
total_results: 57, total_filtered: 0  <- ZERO results
latency_ms: 50562

# Search 3: Vestuario, 1 UF (SP) — AFTER ComprasGov disabled via Railway env
modalidade=6, UF=SP: Page 19/395: 20 items (total records: 7,891)  <- 20/page NOT 500!
-> 502 Bad Gateway (worker timeout exceeded 120s)

# Filter breakdown (Search 1):
Rejeitadas (Status): 217   <- 96% rejected by status_mismatch
Rejeitadas (Modalidade): 9
aplicar_todos_filtros: concluido - 0/226 aprovadas
```

### Env Var Fix Already Applied

`ENABLE_SOURCE_COMPRAS_GOV` foi alterado para `false` em Railway durante o teste (pelo usuario). Backend redeployou confirmando:
```
Feature Flags — ENABLE_NEW_PRICING=True
REDIS_URL not set — Redis disabled, using InMemoryCache fallback
```

---

## Root Cause Analysis

### Bug 1: `tamanhoPagina=500` applied to WRONG code path

**GTM-FIX-025 T3** set `tamanho=500` in `_fetch_single_modality()` (line 1121) which calls `_fetch_page_async()`.

But **production uses `PNCPLegacyAdapter`** which has TWO internal paths:
- **Multi-UF (>1 UF):** Calls `buscar_todas_ufs_paralelo()` → async `_fetch_single_modality()` → `_fetch_page_async()` — HAS `tamanho=500` ✅
- **Single-UF (==1 UF):** Calls `PNCPClient().fetch_all()` → `_fetch_by_uf()` (line 649) → `fetch_page()` (line 686) — uses default `tamanho=20` ❌

See `PNCPLegacyAdapter.fetch()` at line 1574-1597:
```python
if len(_ufs) > 1:
    fetch_result = await buscar_todas_ufs_paralelo(...)  # async path, has 500 ✅
else:
    client = PNCPClient()
    results = list(client.fetch_all(...))  # sync path, uses 20 ❌
```

The production timeout (Search 3, 1 UF SP) hit the sync path because only 1 UF was selected.

**Additionally**, the `fetch_page()` function signature at line 325 defaults to `tamanho: int = 20`. Any future caller that forgets to pass `tamanho=500` will silently get 20/page. The safest fix is to change the **default at the signature level**, not just at individual call sites.

**Impact:** SP modalidade=6 has 7,891 records → 395 pages x ~1.5s = 593s para 1 modalidade de 1 UF. Timeout garantido (gunicorn 120s).

### Bug 2: 100% `status_mismatch` rejection — The Real Root Cause

A filter chain rejeita 100% dos editais. A analise original identificou `status_inference.py` como culpado, mas a **revisao arquitetural** revelou que o problema real e a **combinacao de 3 fatores**:

**Fator 1 — Janela de 180 dias (CAUSA PRINCIPAL):**
`search_pipeline.py:406` busca editais publicados nos ultimos 180 dias. A grande maioria desses editais ja teve prazo encerrado. A inferencia de status corretamente os classifica como `"em_julgamento"` (prazo vencido).

**Fator 2 — Frontend envia `status: "recebendo_proposta"` por padrao:**
`useSearchFilters.ts:181` — `useState<StatusLicitacao>("recebendo_proposta")`. O filtro na Etapa 2 (`filter.py:1856`) compara `_status_inferido == "recebendo_proposta"` e rejeita tudo que nao bate.

**Fator 3 — Tripla filtragem de prazo (redundancia excessiva):**
Alem da Etapa 2 (status), existem mais DOIS filtros que rejeitam editais fechados:
- Etapa 7.5 `filtrar_por_prazo_aberto()` (filter.py:2075) — rejeita `dataEncerramentoProposta` no passado
- Etapa 9 safety net (filter.py:2402-2520) — heuristicas rigorosas quando `status="recebendo_proposta"`:
  - Prazo futuro → KEEP
  - Prazo passado → REJECT
  - Sem prazo, abertura <=15d → KEEP
  - Sem prazo, abertura 16-30d → KEEP so se situacao diz "recebendo"
  - Sem prazo, abertura >30d → REJECT
  - Sem datas → REJECT

**O que NÃO é a causa:** `status_inference.py` esta funcionando **corretamente**. A keyword "divulgada" foi **propositalmente removida** da lista `situacoes_abertas` em 2026-02-09 (ver comentario em status_inference.py:222-225) porque causava licitacoes fechadas serem exibidas como abertas, destruindo credibilidade. **NAO devemos reverter esse fix.**

**Solucao correta:** Reduzir a janela de datas para que a PNCP retorne majoritariamente editais que ainda estao abertos. Com 60 dias (ao inves de 180), a maioria dos editais publicados recentemente tera prazo futuro, passando naturalmente pela Etapa 2 + Etapa 7.5 + Etapa 9.

### Bug 3: PCP (Portal de Compras Publicas) always fails — Root Cause UNKNOWN

A story original assumia que o `source_config/sources.py:303` com URL v1 era a causa. **Revisao arquitetural provou que isso e incorreto:**

- `source_config/sources.py:303` tem URL v1 (`apipcp.portaldecompraspublicas.com.br`) — STALE mas **nao usado pelo adapter**
- `PortalComprasAdapter.__init__()` ignora a `base_url` do config; usa `BASE_URL` hardcoded (v2 correta)
- `search_pipeline.py` instancia o adapter com `PortalComprasAdapter(timeout=source_config.portal.timeout)` — sem `base_url`
- A `PORTAL_COMPRAS_API_KEY` tambem e irrelevante — v2 e publica

**A causa real da falha do PCP e desconhecida.** Pode ser:
- Bug no adapter (fetch logic, paginacao, timeout)
- API v2 instavel ou fora do ar
- Problema de rede Railway → PCP
- Timeout insuficiente para a API v2

**Estrategia:** Deploy diagnostic logging (Fix 3d) PRIMEIRO. Corrigir config (Fix 3a/3b) e cosmetico mas bom para consistencia. O fix real depende dos logs de erro.

### Bug 3 adicional: `validate()` warning misleading

`sources.py:528` ainda gera warning sobre PCP sem API key, contradizendo `is_available()` (line 241) que corretamente dispensa credencial para PORTAL. Fix cosmetico mas confuso nos logs.

### Item 4: ComprasGov v3 (herdado da GTM-FIX-025 T4 / GTM-FIX-026)

ComprasGov v1 (`compras.dados.gov.br`) foi permanentemente desabilitado na GTM-FIX-025 T1 por instabilidade cronica (503s constantes). A API v3 (`dadosabertos.compras.gov.br`) esta disponivel com Swagger, paginacao moderna e suporte ativo do Ministerio da Gestao. A migracao para v3 adiciona uma terceira fonte de dados mas **nao e bloqueante** — PNCP+PCP cobrem o essencial.

**Decisao da GTM-FIX-027:** ComprasGov v3 e Track 5 (P2, OPTIONAL). Os Tracks 1-4 resolvem 100% dos bugs de producao. Track 5 adiciona valor incremental quando PNCP+PCP ja estiverem funcionando.

---

## Tracks

### Track 1: Fix PNCP page size (P0 CRITICAL — fixes timeout/502)

**File:** `backend/pncp_client.py`

**Fix 1a — Change `fetch_page()` default at signature level (line 325):**

```python
# Line 325 — BEFORE:
def fetch_page(
    self,
    data_inicial: str,
    data_final: str,
    modalidade: int,
    uf: str | None = None,
    pagina: int = 1,
    tamanho: int = 20,
) -> Dict[str, Any]:

# Line 325 — AFTER:
def fetch_page(
    self,
    data_inicial: str,
    data_final: str,
    modalidade: int,
    uf: str | None = None,
    pagina: int = 1,
    tamanho: int = 500,  # GTM-FIX-027 T1: PNCP API max (was 20)
) -> Dict[str, Any]:
```

**Fix 1b — Also change `_fetch_page_async()` default at signature level (line 907):**

```python
# Line 907 — BEFORE:
async def _fetch_page_async(
    self, ..., tamanho: int = 20, ...
) -> Dict[str, Any]:

# AFTER:
async def _fetch_page_async(
    self, ..., tamanho: int = 500, ...  # GTM-FIX-027 T1: consistent default
) -> Dict[str, Any]:
```

**Why signature-level instead of call-site:** Changing the default prevents future callers from silently using 20/page. The explicit `tamanho=500` in `_fetch_single_modality()` (line 1121) becomes redundant but harmless.

**Expected impact:**
- SP modalidade=6: 395 pages → ~16 pages (25x fewer requests)
- Latency per modality: ~593s → ~24s
- Single-UF search: Under 30s (was timeout at 120s+)
- Multi-UF search (27 UFs): Already uses async path with 500, no change

### Track 2: Fix status filter (P0 CRITICAL — fixes zero results)

**Files:** `backend/search_pipeline.py`

**CRITICAL: Do NOT modify `status_inference.py`.** The removal of "divulgada" from `situacoes_abertas` on 2026-02-09 was deliberate and correct (see comment at line 222-225). Reverting it would reintroduce false positives (closed bids shown as open).

**Fix 2a — Reduce date range from 180 to 60 days:**

```python
# search_pipeline.py:406 — BEFORE:
ctx.request.data_inicial = (today - timedelta(days=180)).isoformat()

# AFTER:
ctx.request.data_inicial = (today - timedelta(days=60)).isoformat()
logger.info(
    f"modo_busca='abertas': date range overridden to "
    f"{ctx.request.data_inicial} -> {ctx.request.data_final} (60 days)"
)
```

**Why 60 days (not 30):**
- 30 dias e agressivo demais: licitacoes municipais/estaduais frequentemente tem prazos de 45-90 dias
- 60 dias captura a maioria dos editais ainda abertos sem trazer uma maioria de fechados
- A Etapa 7.5 (`filtrar_por_prazo_aberto`) e a Etapa 9 (safety net) ja rejeitam editais com prazo vencido, entao editais fechados nos ultimos 60 dias serao filtrados corretamente
- Se 60 dias ainda retornar muitos fechados, pode ser ajustado para 45 em iteracao futura

**Fix 2b — REMOVED (architect review):**

~~Pre-filter closed bids at adapter level~~ — **REMOVIDO.** `filtrar_por_prazo_aberto()` (Etapa 7.5, filter.py:2075) e a Etapa 9 safety net (filter.py:2402-2520) ja fazem exatamente isso. Adicionar um terceiro filtro no adapter cria redundancia e risco de inconsistencia. O beneficio de performance (menos items no pipeline) nao justifica a complexidade adicional dado que a reducao de 180→60 dias ja reduz o volume em ~67%.

**Analysis pos-fix — O que acontece depois da Etapa 2:**

Com janela de 60 dias, a maioria dos editais tera `dataEncerramentoProposta` no futuro. O fluxo esperado:
1. Etapa 2 (Status): `status_inference` classifica editais com prazo futuro como `"recebendo_proposta"` → PASS ✅
2. Etapa 7.5 (Prazo Aberto): Confirma que `dataEncerramentoProposta` e futuro → PASS ✅
3. Etapa 9 (Safety Net): Verifica prazo futuro → PASS ✅
4. Keywords: Filtra por setor → taxa de aprovacao depende do setor

Editais com prazo vencido (minoria nos ultimos 60 dias):
1. Etapa 2: Classificados como `"em_julgamento"` → REJECTED (correto)

### Track 3: Fix PCP v2 source (P1 MEDIUM — diagnostic first, then fix)

**Files:** `backend/source_config/sources.py`, `backend/consolidation.py`, Railway env vars

**IMPORTANT:** A causa real da falha PCP e desconhecida. A URL stale no config e a API key morta sao problemas COSMETICOS — o adapter nao os usa. O fix principal e diagnostic logging para identificar o erro real.

**Fix 3a — Diagnostic logging FIRST (deploy before other fixes):**

Add the actual PCP error message to consolidation logs. In `consolidation.py:_wrap_source()`:

```python
except Exception as e:
    logger.error(
        f"[CONSOLIDATION] {code}: FAILED after {duration}ms -- "
        f"{type(e).__name__}: {e}",
        exc_info=True,  # Full traceback for diagnosis
    )
```

**Fix 3b — Update config URL to v2 (cosmetic, for consistency):**

```python
# source_config/sources.py line 303 — BEFORE:
base_url="https://apipcp.portaldecompraspublicas.com.br",

# AFTER:
base_url="https://compras.api.portaldecompraspublicas.com.br",
```

**Fix 3c — Remove stale v1 API key (cosmetic):**

```python
# source_config/sources.py lines 423-426 — BEFORE:
config.portal.credentials = SourceCredentials(
    api_key=os.getenv("PCP_PUBLIC_KEY") or os.getenv("PORTAL_COMPRAS_API_KEY")
)

# AFTER:
# GTM-FIX-027 T3: PCP v2 API is public — no API key required
config.portal.credentials = SourceCredentials(api_key=None)
```

**Fix 3d — Fix misleading validate() warning:**

```python
# source_config/sources.py line 528 — BEFORE:
if self.portal.enabled and not self.portal.credentials.has_api_key():
    messages.append(
        "WARNING: Portal de Compras enabled but PORTAL_COMPRAS_API_KEY not set"
    )

# AFTER:
# GTM-FIX-027 T3: Portal v2 is public, no API key needed — remove misleading warning
# (is_available() at line 241 already correctly excludes PORTAL from credential check)
```

**Fix 3e — Railway env cleanup:**

```bash
railway variables set PCP_TIMEOUT=15       # Reduce from 30s
# Remove PORTAL_COMPRAS_API_KEY (stale v1 key, serves no purpose)
```

**Post-deploy:** After Fix 3a is deployed, run a search and check Railway logs for the actual PCP error. If the error reveals a bug in the adapter, create a follow-up fix.

### Track 4: Fix UX messages (P2 LOW — fixes misleading copy)

**File:** `frontend/` (search progress components)

**Fixes:**
- "Buscas com muitos estados demoram mais" shown with 1 state → only show when >10 UFs
- "A busca esta demorando mais que o esperado" → show which source/UF is being processed
- Progress estimate `~6m 13s` → recalibrate for `tamanhoPagina=500` (target: <60s)

### Track 5: ComprasGov v3 Migration (P2 OPTIONAL — adds 3rd data source)

**Herdado de:** GTM-FIX-025 T4 / GTM-FIX-026 (nunca implementada)

**Status:** ComprasGov v1 permanentemente desabilitado (GTM-FIX-025 T1). API v3 disponivel.

**Pre-requisito:** Tracks 1-3 devem estar completos e validados em prod. PNCP+PCP funcionando.

**Decisao arquitetural:** Usar AMBOS endpoints v3 em paralelo para maxima cobertura:
- Endpoint legacy: `/modulo-legado/1_consultarLicitacao` (compras anteriores a 2024)
- Endpoint Lei 14.133: `/modulo-contratacoes/1_consultarContratacoes_PNCP_14133` (novas contratacoes)

**File:** `backend/clients/compras_gov_client.py` (rewrite completo)

```python
# ANTES (v1 — morto)
BASE_URL = "https://compras.dados.gov.br"

# DEPOIS (v3)
BASE_URL = "https://dadosabertos.compras.gov.br"
```

**API v3 Characteristics:**
- Base URL: `https://dadosabertos.compras.gov.br`
- Auth: Bearer token opcional (maioria dos endpoints abertos)
- Paginacao: `pagina` + `tamanhoPagina` (configuravel)
- Resposta: `resultado[]`, `totalRegistros`, `totalPaginas`, `paginasRestantes`
- Endpoint legacy params: `data_publicacao_inicial`, `data_publicacao_final`, `uasg`, `modalidade`
- Endpoint 14.133 params: `dataPublicacaoPncpInicial`, `dataPublicacaoPncpFinal`, `codigoModalidade`
- Docs: [Swagger](https://dadosabertos.compras.gov.br/swagger-ui/index.html) | [OpenAPI](https://dadosabertos.compras.gov.br/v3/api-docs) | [Manual](https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/manual-dados-abertos/manual-api-compras.pdf)

**Implementacao:**
1. Rewrite `ComprasGovAdapter` com dual-endpoint fetch
2. `normalize()` mapeia campos v3 para `UnifiedProcurement`
3. `health_check()` valida nova API
4. Re-habilitar via `ENABLE_SOURCE_COMPRAS_GOV=true` (flag ja existe)
5. Deduplicacao: priority=3 (PNCP=1, PCP=2, ComprasGov=3)
6. Rewrite testes

**Nota:** Este track e OPCIONAL. PNCP+PCP cobrem 95%+ dos editais federais. ComprasGov v3 adiciona cobertura de compras legadas (pre-2024) e redundancia.

---

## Acceptance Criteria

### Track 1 — PNCP Page Size (P0)
- [ ] AC1: `fetch_page()` default parameter changed from `tamanho=20` to `tamanho=500` (line 325)
- [ ] AC2: `_fetch_page_async()` default parameter changed from `tamanho=20` to `tamanho=500` (line 907)
- [ ] AC3: Logs PNCP mostram `Page 1/X: 500 items` (nao 20)
- [ ] AC4: Busca 1 UF (sync path) completa em <30s
- [ ] AC5: Busca 27 UFs (async path) completa em <60s
- [ ] AC6: Zero 502 Bad Gateway em qualquer busca
- [ ] AC7: Testes existentes atualizados para novo default (500)

### Track 2 — Status Filter (P0)
- [ ] AC8: `search_pipeline.py:406` usa `timedelta(days=60)` (nao 180)
- [ ] AC9: `status_inference.py` NAO foi modificado (preservar fix de 2026-02-09)
- [ ] AC10: Busca Vestuario + SP retorna >0 resultados
- [ ] AC11: Busca Software + SP/RJ/MG retorna >0 resultados
- [ ] AC12: Taxa de `status_mismatch` cai de 100% para <60%
- [ ] AC13: Teste valida janela de 60 dias para modo "abertas"
- [ ] AC14: Nenhum edital com prazo vencido aparece nos resultados (Etapa 7.5 + 9 intactas)

### Track 3 — PCP v2 (P1)
- [ ] AC15: Diagnostic logging deployed com `exc_info=True` em `consolidation.py`
- [ ] AC16: `source_config.portal.base_url` atualizada para URL v2 (cosmetic)
- [ ] AC17: PCP credentials sao `None` (sem chave v1 morta)
- [ ] AC18: `validate()` nao gera warning sobre PCP API key
- [ ] AC19: PCP timeout reduzido para 15s no Railway
- [ ] AC20: Logs de producao revelam a causa real da falha PCP (post-deploy)
- [ ] AC21: Se causa real identificada, fix aplicado e PCP aparece em `sources_succeeded`

### Track 4 — UX Messages (P2)
- [ ] AC22: Mensagem "muitos estados" so aparece quando >10 UFs selecionados
- [ ] AC23: Estimativa de progresso recalibrada para `tamanhoPagina=500` (target: <60s para 27 UFs)
- [ ] AC24: Busca longa mostra qual fonte/UF esta sendo processada

### Track 5 — ComprasGov v3 (P2, OPTIONAL — herdado da GTM-FIX-026)
- [ ] AC25: `ComprasGovAdapter.BASE_URL` aponta para `https://dadosabertos.compras.gov.br`
- [ ] AC26: Endpoint usa `/modulo-legado/1_consultarLicitacao` com params corretos
- [ ] AC27: Endpoint usa `/modulo-contratacoes/1_consultarContratacoes_PNCP_14133` em paralelo
- [ ] AC28: `health_check()` valida a nova API v3
- [ ] AC29: `normalize()` mapeia campos da v3 para `UnifiedProcurement`
- [ ] AC30: Testes de `compras_gov_client.py` reescritos para v3
- [ ] AC31: `ENABLE_SOURCE_COMPRAS_GOV=true` re-habilita ComprasGov v3 sem deploy

---

## Test Plan

### Unit Tests (backend)

```python
# Track 1
def test_fetch_page_default_tamanho_500():
    """AC1: fetch_page() signature defaults to tamanho=500"""

def test_fetch_page_async_default_tamanho_500():
    """AC2: _fetch_page_async() signature defaults to tamanho=500"""

def test_fetch_by_uf_uses_500_per_page():
    """AC1+AC4: _fetch_by_uf -> fetch_page uses 500 items/page"""

def test_existing_tests_updated_for_500_default():
    """AC7: No test assumes tamanho=20"""

# Track 2
def test_abertas_mode_60_day_window():
    """AC8: Default date range is 60 days, not 180"""

def test_status_inference_not_modified():
    """AC9: 'divulgada' NOT in situacoes_abertas (2026-02-09 fix preserved)"""

def test_etapa_7_5_rejects_past_deadline():
    """AC14: filtrar_por_prazo_aberto rejects bids with past deadline"""

def test_etapa_9_safety_net_rejects_past_deadline():
    """AC14: Safety net rejects bids with past dataEncerramentoProposta"""

def test_60_day_window_yields_open_bids():
    """AC10+AC11: Bids from last 60 days include open ones"""

# Track 3
def test_pcp_config_v2_url():
    """AC16: PCP config base_url is v2"""

def test_pcp_no_api_key():
    """AC17: PCP credentials are None"""

def test_pcp_validate_no_warning():
    """AC18: validate() does not warn about PCP API key"""

def test_consolidation_logs_full_traceback():
    """AC15: Exception logging includes exc_info=True"""

# Track 5 (se implementado)
def test_compras_gov_v3_base_url():
    """AC25: ComprasGov BASE_URL is v3"""

def test_compras_gov_v3_normalize():
    """AC29: v3 response mapped to UnifiedProcurement"""

def test_compras_gov_v3_health_check():
    """AC28: health_check validates v3 API"""

def test_compras_gov_v3_dual_endpoint():
    """AC27: Both legacy and 14.133 endpoints called"""
```

### Integration Tests (production)

```
1. Search Vestuario + SP (1 UF, sync path) -> completes <30s, >0 results
2. Search Software + SP/RJ/MG (3 UFs, async path) -> completes <30s, >0 results
3. Search Vestuario + all 27 UFs (async path) -> completes <60s, no 502
4. Verify logs show "Page 1/X: 500 items" (not 20)
5. Verify status_mismatch < 60% (was 100%)
6. Verify no closed bids in results (Etapa 7.5 + 9 functional)
7. Check Railway logs for PCP error details (after diagnostic logging deployed)
8. [Track 5] Verify ComprasGov v3 in sources_succeeded when enabled
```

---

## Files Modified

| Track | File | Change |
|-------|------|--------|
| T1 | `backend/pncp_client.py:325` | Change `fetch_page()` default from `tamanho=20` to `tamanho=500` |
| T1 | `backend/pncp_client.py:907` | Change `_fetch_page_async()` default from `tamanho=20` to `tamanho=500` |
| T2 | `backend/search_pipeline.py:406` | Change 180 -> 60 days for "abertas" mode |
| T2 | ~~`backend/status_inference.py`~~ | **NOT MODIFIED** (2026-02-09 fix preserved) |
| T3 | `backend/consolidation.py` | Add `exc_info=True` to exception logging |
| T3 | `backend/source_config/sources.py:303` | Fix PCP base_url to v2 (cosmetic) |
| T3 | `backend/source_config/sources.py:423` | Remove stale API key (cosmetic) |
| T3 | `backend/source_config/sources.py:528` | Remove misleading PCP credential warning |
| T4 | `frontend/` (components TBD) | Fix "muitos estados" threshold, recalibrate progress |
| T5 | `backend/clients/compras_gov_client.py` | Full rewrite for v3 API (dual endpoint) |
| T5 | `backend/source_config/sources.py` | Update ComprasGov URL to v3 |
| T5 | `backend/tests/test_compras_gov_*.py` | Rewrite tests for v3 |

---

## Execution Order

```
+-------------------------------------------------+
| Phase 1: CRITICAL (parallel, 2-3h)              |
|   T1: PNCP page size fix  --+                   |
|   T2: Date range 180->60   -+-- Deploy & test   |
|   T3: PCP diagnostic log  --+                   |
+-------------------------------------------------+
| Phase 1.5: DIAGNOSE PCP (30min)                 |
|   Read Railway logs for PCP error                |
|   If bug found -> fix and redeploy               |
+-------------------------------------------------+
| Phase 2: POLISH (1-2h)                          |
|   T4: UX message fixes                          |
+-------------------------------------------------+
| Phase 3: OPTIONAL (3-4h, separate sprint)       |
|   T5: ComprasGov v3 migration                   |
+-------------------------------------------------+
```

---

## Risk Assessment

| Risk | Prob. | Impact | Mitigation |
|------|-------|--------|------------|
| PNCP rejects `tamanhoPagina=500` | Low | High | Async path already uses 500 successfully; same API endpoint |
| Changing `fetch_page()` default affects ALL callers | Low | Medium | 500 is PNCP API max; all callers benefit from larger pages. Run full test suite. |
| 60-day window misses older open bids | Low | Medium | Municipal/state bids typically 30-60d response window. Can adjust to 90 if needed. |
| PCP error is in the adapter, not the API | Medium | Low | Diagnostic logging deployed first; adapter code reviewed post-diagnosis |
| ComprasGov v3 also unstable | Medium | None | Track 5 is optional; v1 stays disabled regardless |
| Post-fix results still low due to Etapa 7.5/9 filters | Low | Medium | These filters correctly reject closed bids; 60-day window should provide enough open bids |
| Tests assume `tamanho=20` default | Medium | Low | Update test assertions to expect 500 |

---

## Architect Review Log (2026-02-17)

Changes made based on @architect critical review:

1. **FIX 2a REMOVED** — "divulgada" was intentionally removed from `situacoes_abertas` on 2026-02-09. Adding it back would reintroduce false positives.
2. **FIX 2b REMOVED** — Adapter-level pre-filter is redundant with Etapa 7.5 + Etapa 9.
3. **Date window changed from 30 to 60 days** — 30d too aggressive for municipal/state bids.
4. **Page size fix changed from call-site to signature-level** — Prevents future callers from silently using 20.
5. **PCP root cause reclassified as UNKNOWN** — Config URL is cosmetic; adapter ignores it. Added diagnostic-first strategy.
6. **Added `validate()` warning fix** — `sources.py:528` misleadingly warns about PCP credentials.
7. **Added post-fix analysis** — Documented what happens after status filter is fixed (Etapa 7.5 + 9 still active).
8. **Added `_fetch_page_async()` default fix** — Consistent with sync path.

---

## Relationship to Previous Stories

| Story | Status | Relationship |
|-------|--------|-------------|
| GTM-FIX-025 T1-T3,T5 | Done | T1: ComprasGov disabled, T3: page size fix (wrong path) |
| GTM-FIX-025 T4 | Deferred | -> Incorporated as GTM-FIX-027 Track 5 |
| GTM-FIX-026 | Never created | -> Fully subsumed by GTM-FIX-027 Track 5 |
| GTM-FIX-024 | Done | 6 multi-source pipeline bugs fixed |
| GTM-FIX-011/012b | Done | PCP v2 migration (adapter code correct, config wrong) |

---

## Definition of Done

### Minimum (Tracks 1-3):
- [ ] All P0/P1 ACs pass (AC1-AC21)
- [ ] Single-UF search completes in <30s with >0 results
- [ ] 27-UF search completes in <60s without 502
- [ ] Zero regressions in existing test suite
- [ ] Deployed to production and validated with real searches
- [ ] PCP error diagnosed from production logs

### Full (Tracks 1-4):
- [ ] All ACs through AC24 pass
- [ ] UX messages are accurate and helpful

### Optional (Track 5):
- [ ] All ACs through AC31 pass
- [ ] ComprasGov v3 contributes data alongside PNCP+PCP
- [ ] 3-source deduplication verified in production
