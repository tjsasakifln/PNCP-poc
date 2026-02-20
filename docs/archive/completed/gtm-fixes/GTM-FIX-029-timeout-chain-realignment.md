# GTM-FIX-029 — Realinhamento da Cadeia de Timeouts do Pipeline de Busca

**Prioridade:** P0 — Bloqueio total de funcionalidade core
**Severidade:** Crítica — 100% das buscas nacionais retornam 0 resultados
**Estimativa:** 4-6 horas (6 tracks paralelizáveis)
**Dependências:** GTM-FIX-027 (page size 500→50), commit `12c99e8` (tamanhoPagina fix)
**Autor:** @pm (Morgan)
**Data:** 2026-02-17

---

## Contexto

Em fevereiro de 2026, a PNCP reduziu silenciosamente o `tamanhoPagina` máximo de 500 para 50 itens/página. O commit `12c99e8` corrigiu o valor enviado, mas **não recalibrou a cadeia de timeouts** que foi dimensionada para 500 itens/página (1 página por modalidade na maioria dos casos).

Com 50 itens/página, cada combinação UF+modalidade precisa de **10x mais requisições HTTP**. Os timeouts internos (especialmente `PER_UF_TIMEOUT=30s`) matam as buscas antes que a paginação complete, resultando em 0 resultados para 100% das buscas nacionais.

---

## Root Cause Analysis

### Cadeia de Timeouts Atual (6 camadas aninhadas)

```
CAMADA 0: Frontend Proxy               300s   (route.ts)          ✅ OK
CAMADA 1: Pipeline FETCH_TIMEOUT        240s   (search_pipeline)   ✅ OK
CAMADA 2: Consolidation Global          120s*  (sources.py)        ⚠️  Apertado
CAMADA 3: Consolidation Per-Source       50s*  (sources.py)        ❌ INSUFICIENTE
CAMADA 4: Per-UF Timeout                 30s   (pncp_client.py)    ❌ BLOQUEIO FATAL
CAMADA 5: Per-Modality Timeout          120s   (pncp_client.py)    ❌ INVERSÃO
CAMADA 6: Per-Page HTTP                  30s   (config.py)         ✅ OK
```

*Valores já alterados parcialmente no código mas NÃO em produção.

### 3 Bugs Identificados

**BUG 1 — Inversão de Timeout (Per-UF < Per-Modality)**

```python
# pncp_client.py:1366
PER_UF_TIMEOUT = 30   # ← mata o UF inteiro em 30s

# pncp_client.py:54
PNCP_TIMEOUT_PER_MODALITY = 120  # ← cada modalidade pode levar até 120s
```

As 4 modalidades rodam em **paralelo** dentro do UF, mas o `asyncio.wait_for()` do UF (30s) cancela TODAS as modalidades antes que qualquer uma complete se houver mais de ~6 páginas (6 × 0.5s/req × 10 rate-limit = ~30s).

**Cálculo real**: Com 50 items/page e ~100 resultados por modalidade, cada mod precisa de 2 páginas × ~1s = 2s. Mas com 500+ resultados (SP Saúde mod 6), seriam 10+ páginas × ~1s = 10-15s por modalidade. O UF precisa de pelo menos 20s para as 4 mods em paralelo, mais overhead. **30s é marginal.**

Com PNCP instável (retries, 429s, jitter), 30s é insuficiente.

**BUG 2 — Per-Source Timeout Estrangula PNCP Nacional**

```python
# sources.py:261
timeout_per_source: int = 50  # ← a consolidation mata o PNCP adapter em 50s
```

O PNCP adapter para 27 UFs × 4 modalidades com `max_concurrent=10`:
- 3 batches de ~10 UFs
- Cada batch: ~20-30s (com o per-UF de 30s como teto)
- Total realista: 60-90s para completar
- **50s per-source = PNCP cortado no meio**, perdendo 1/3 das UFs

A consolidation **salva resultados parciais** (status="partial"), mas se as primeiras UFs forem lentas (SP, RJ com mais dados), pode perder UFs inteiras.

**BUG 3 — HTTP 422 Não-Retryable Causa Perda Silenciosa**

```python
# config.py:59-60
retryable_status_codes: Tuple[int, ...] = (408, 429, 500, 502, 503, 504)
# 422 NÃO está na lista → PNCPAPIError imediato
```

Quando PNCP retorna 422 para uma combinação UF+modalidade:
1. Não faz retry (falha imediata)
2. Não conta no circuit breaker (não incrementa failure counter)
3. UF é marcada como "succeeded" com 0 resultados (não "failed")
4. **Zero visibilidade** — parece que não havia dados, não que houve erro

Observado em produção: DF/mod5, RJ/mod5, PR/mod4, RS/mod7 → 422.

---

## Acceptance Criteria

### Track 1 — Recalibração de Timeouts (P0, pncp_client.py)

- [ ] **AC1**: `PER_UF_TIMEOUT` aumentado de 30s para 90s em modo normal
- [ ] **AC2**: `PER_UF_TIMEOUT` aumentado de 45s para 120s em modo degradado
- [ ] **AC3**: Comentário no código explicando o cálculo: `4 mods × ~15s/mod (com retry) = ~60s + margem`
- [ ] **AC4**: `PNCP_TIMEOUT_PER_MODALITY` mantido em 120s (adequado para até 240 páginas)
- [ ] **AC5**: `PER_UF_TIMEOUT` configurável via env var `PNCP_TIMEOUT_PER_UF` (fallback=90)

### Track 2 — Timeouts da Consolidation (P0, sources.py + consolidation.py)

- [ ] **AC6**: Default `timeout_per_source` aumentado de 50s para 180s
- [ ] **AC7**: Default `timeout_global` aumentado de 120s para 300s
- [ ] **AC8**: `DEGRADED_GLOBAL_TIMEOUT` aumentado de 90s para 360s
- [ ] **AC9**: `FAILOVER_TIMEOUT_PER_SOURCE` aumentado de 40s para 120s
- [ ] **AC10**: Log de warning se `timeout_per_source > timeout_global * 0.8` (quase-inversão)
- [ ] **AC11**: Env vars `CONSOLIDATION_TIMEOUT_GLOBAL=300` e `CONSOLIDATION_TIMEOUT_PER_SOURCE=180` setados no Railway

### Track 3 — Tratamento do HTTP 422 (P1, pncp_client.py + config.py)

- [ ] **AC12**: HTTP 422 adicionado à lista `retryable_status_codes` com max 1 retry (não 3)
- [ ] **AC13**: Quando 422 persiste após 1 retry, logar resposta completa do PNCP (body[:500]) com nível WARNING
- [ ] **AC14**: 422 após retry conta como falha no circuit breaker (`record_failure()`)
- [ ] **AC15**: Métrica: contar quantos 422s por UF+modalidade para diagnóstico

### Track 4 — Pipeline FETCH_TIMEOUT (P1, search_pipeline.py)

- [ ] **AC16**: `FETCH_TIMEOUT` aumentado de 240s (4min) para 360s (6min)
- [ ] **AC17**: `FETCH_TIMEOUT` configurável via env var `SEARCH_FETCH_TIMEOUT` (fallback=360)
- [ ] **AC18**: Frontend proxy timeout verificado ≥ FETCH_TIMEOUT + 60s de margem (atualmente 300s → manter ou aumentar para 420s)

### Track 5 — Frontend Proxy Timeout (P1, frontend/app/api/buscar/route.ts)

- [ ] **AC19**: Timeout do frontend proxy aumentado de 300s (5min) para 480s (8min) para acomodar FETCH_TIMEOUT=360s + margem
- [ ] **AC20**: Comentário explicando hierarquia: `FE proxy (480s) > Pipeline (360s) > Consolidation (300s) > Per-Source (180s) > Per-UF (90s)`

### Track 6 — Testes e Validação (P0)

- [ ] **AC21**: Teste unitário: `PER_UF_TIMEOUT >= PNCP_TIMEOUT_PER_MODALITY * 0.75` (garante que UF dá tempo para modalities)
- [ ] **AC22**: Teste unitário: `timeout_per_source >= PER_UF_TIMEOUT * 2` (garante que consolidation dá tempo para UFs)
- [ ] **AC23**: Teste unitário: `timeout_global >= timeout_per_source * 1.5` (margem entre global e per-source)
- [ ] **AC24**: Teste unitário: `FETCH_TIMEOUT >= timeout_global * 1.1` (pipeline dá tempo para consolidation)
- [ ] **AC25**: Teste unitário: 422 é retryable com max 1 retry
- [ ] **AC26**: Teste de integração: busca de 5 UFs × 4 modalidades com mocks retornando 3 páginas cada, completa sem timeout
- [ ] **AC27**: Teste de integração: 1 UF retorna 422 em 2 modalidades, as outras 2 retornam dados → resultado parcial preservado
- [ ] **AC28**: Atualizar `test_gtm_fix_027_track1.py` e `test_pipeline_resilience.py` com novos valores

---

## Valores Finais da Cadeia (Após Fix)

```
CAMADA 0: Frontend Proxy               480s   (route.ts)          ✅
CAMADA 1: Pipeline FETCH_TIMEOUT        360s   (search_pipeline)   ✅ FETCH_TIMEOUT env var
CAMADA 2: Consolidation Global          300s   (sources.py)        ✅ CONSOLIDATION_TIMEOUT_GLOBAL env var
CAMADA 3: Consolidation Per-Source      180s   (sources.py)        ✅ CONSOLIDATION_TIMEOUT_PER_SOURCE env var
CAMADA 4: Per-UF Timeout                 90s   (pncp_client.py)    ✅ PNCP_TIMEOUT_PER_UF env var
CAMADA 5: Per-Modality Timeout          120s   (pncp_client.py)    ✅ PNCP_TIMEOUT_PER_MODALITY env var
CAMADA 6: Per-Page HTTP                  30s   (config.py)         ✅ (inalterado)
```

**Invariantes garantidas por testes:**
```
FE Proxy (480s) > Pipeline (360s) > Consolidation Global (300s) > Per-Source (180s) > Per-UF (90s) ≈ Per-Modality (120s) > HTTP (30s)
```

Nota: Per-UF (90s) < Per-Modality (120s) é **intencional** — as 4 modalidades rodam em paralelo, então o UF completa em ~max(mod1, mod2, mod3, mod4) ≈ 15-60s tipicamente. O timeout de 90s é para o caso degenerado.

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/pncp_client.py` | PER_UF_TIMEOUT 30→90, env var, 422 retry logic |
| `backend/source_config/sources.py` | timeout_global 120→300, timeout_per_source 50→180 |
| `backend/consolidation.py` | DEGRADED_GLOBAL_TIMEOUT 90→360, FAILOVER 40→120 |
| `backend/search_pipeline.py` | FETCH_TIMEOUT 240→360, env var |
| `backend/config.py` | 422 added to retryable_status_codes |
| `frontend/app/api/buscar/route.ts` | Proxy timeout 300→480s |
| `backend/tests/test_timeout_chain.py` | **NOVO** — invariantes de timeout |
| `backend/tests/test_gtm_fix_027_track1.py` | Atualizar valores |
| `backend/tests/test_pipeline_resilience.py` | Atualizar valores |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Timeouts muito altos causam requests pendurados | Média | Médio | Todos configuráveis via env var; monitorar Sentry |
| 422 retry aumenta carga no PNCP | Baixa | Baixo | Max 1 retry (não 3); rate limiter já ativo |
| Frontend mostra loading por 8min | Baixa | Alto | SSE progress tracking já implementado; mostrar dados parciais |
| Gunicorn worker timeout kill | Média | Alto | Verificar `GUNICORN_TIMEOUT` ≥ 600s no Railway |

---

## Validação em Produção

1. Deploy no Railway
2. Busca Saúde nacional (27 UFs) — deve retornar resultados > 0
3. Verificar logs: nenhum "timed out after 30s" para UFs
4. Verificar logs: nenhum "Per-source timeout" para PNCP
5. Verificar logs: 422s logados com body detalhado
6. Busca por setor pequeno (1 UF) — deve completar em < 15s
7. Comparar tempo total com baseline pré-fix

---

## Notas Técnicas

### Por que PER_UF_TIMEOUT (90s) < PER_MODALITY_TIMEOUT (120s)?

As 4 modalidades executam em **paralelo** via `asyncio.gather()`. O tempo real do UF é `max(mod1, mod2, mod3, mod4)`, não a soma. Na prática:
- Modalidade com 2 páginas: ~2s
- Modalidade com 10 páginas: ~15s
- Modalidade com 50 páginas: ~60s (raro, SP/RJ em saúde)

O PER_UF_TIMEOUT de 90s cobre o caso de 1 modalidade lenta com retry. Se uma modalidade sozinha precisa de >90s, ela é cortada, mas as outras 3 já completaram.

### Por que não aumentar PER_UF_TIMEOUT para 120s (= per-modality)?

Porque com `max_concurrent=10` e 27 UFs, os UFs executam em ~3 batches. Se cada UF bloqueasse por 120s, o batch demoraria 120s e o total ~360s. Com 90s, o total fica ~270s, cabendo folgadamente no per-source de 180s (pois os UFs de batches anteriores já liberaram).

### PNCP 422 — Hipótese

Os 422s observados (DF/mod5, RJ/mod5, PR/mod4, RS/mod7) podem ser causados por:
1. Combinações UF+modalidade que o PNCP não suporta para o período
2. Parâmetro `situacaoCompra` inválido para certas modalidades
3. Bug do lado do PNCP (temporário)

O retry com 1 tentativa extra resolve o caso 3. Os casos 1 e 2 precisam de diagnóstico adicional via logs detalhados (AC13).
