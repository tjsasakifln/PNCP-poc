# GTM-FIX-025: Pipeline Resilience & ComprasGov Sunset — Consolidação Sobrevive a Fontes Instáveis

## Classificação
- **Priority:** P0 BLOCKER
- **Effort:** S (1-2h para T1-T3+T5) + M (2-3h para T4, deferível)
- **Severidade:** Crítica — busca retorna 500 Internal Server Error quando ComprasGov está fora do ar (condição recorrente/permanente)
- **Predecessora:** GTM-FIX-024 (fix de 6 bugs encadeados no pipeline)
- **Sprint:** Current (hotfix imediato para T1-T3)

## Dimension Impact
- D01 (Core Functionality): 9/10 → **10/10** — pipeline nunca mais retorna 500 por fonte instável
- D02 (Revenue Reliability): 8/10 → **9/10** — buscas completam mesmo com fontes degradadas
- D03 (Data Quality): 8/10 → **9/10** — 25x menos requests = 25x menos dados perdidos por timeout
- D09 (Observability): 4/10 → **6/10** — exceções genéricas logadas+sentried, não silenciadas

## Problema

Apesar do fix GTM-FIX-024 (6 bugs encadeados), o pipeline de consolidação continua **incapaz de completar buscas em produção**. A causa raiz desta vez é diferente: a API `compras.dados.gov.br` (ComprasGov) está **permanentemente instável** — o governo brasileiro [reporta instabilidade constante](https://gestgov.discourse.group/t/api-compras-dados-gov-instabilidade-constante/27386) e a comunidade [confirma que está frequentemente fora do ar](https://gestgov.discourse.group/t/compras-dados-fora-do-ar/26000). A API retorna 503 após 3 retries e o erro **propaga para o pipeline inteiro**, matando resultados do PNCP e PCP que foram buscados com sucesso.

Adicionalmente, o PNCP está usando `tamanhoPagina=20` (default) ao invés de um valor maior, gerando **milhares de requests** para uma busca de 27 UFs x 4 modalidades, causando timeouts em cascata.

### Erro em Produção (2026-02-17T18:47:50)

```
[COMPRAS_GOV] Server error 503. Retrying in 2.1s
[COMPRAS_GOV] Server error 503. Retrying in 2.6s
[COMPRAS_GOV] Server error 503. Retrying in 11.8s
[COMPRAS_GOV] Error fetching offset 0: [COMPRAS_GOV] HTTP 503:
  <html><body><h1>503 Service Unavailable</h1>
  No server is available to handle this request.</body></html>

SourceAPIError → Internal server error during procurement search
```

**Cenário completo do Sentry trace:**

| Fonte | Status | Detalhe |
|-------|--------|---------|
| PNCP | Parcial | 18+ UF/modalidade combos timeout (15s), vários 422 |
| PCP (Portal de Compras) | OK | 23 páginas fetched com sucesso |
| ComprasGov | CRASH | 503 → 3 retries → `SourceAPIError` → **mata pipeline inteiro** |
| PortalTransparencia | Desabilitado | `ENABLE_SOURCE_PORTAL_TRANSPARENCIA=false` (default) |

---

## Análise de Causa-Raiz: 5 Bugs

### BUG 1 — ComprasGov é uma API morta usada como fonte primária E fallback (ARQUITETURAL)
**Arquivo:** `search_pipeline.py:626-642`
**Causa:** ComprasGov (`compras.dados.gov.br`) é instanciado como adapter primário (L626-629) **e** como `fallback_adapter` (L640-642). O consolidation.py verifica `already_tried` (L280) e pula o fallback quando a fonte já foi tentada como primária. Resultado: o mecanismo de fallback é **inútil** — o único fallback é ele mesmo.
**Agravante:** A API `compras.dados.gov.br` é [reconhecidamente instável](https://gestgov.discourse.group/t/api-compras-dados-gov-instabilidade-constante/27386) pelo próprio governo. O Ministério da Gestão lançou uma [nova API v3](https://dadosabertos.compras.gov.br/swagger-ui/index.html) em `dadosabertos.compras.gov.br` como substituta, mas a antiga segue no ar (intermitente) sem deprecation formal.
**Impacto:** Cada 503 do ComprasGov é um tiro no pipeline. E a API fora do ar é a condição normal, não exceção.

### BUG 2 — Pipeline não captura exceções genéricas de consolidation (CRASH PATH)
**Arquivo:** `search_pipeline.py:657-806`
**Causa:** O try-except da L657-806 só captura `AllSourcesFailedError` (L716) e `asyncio.TimeoutError` (L792). Se consolidation.py levantar qualquer outra exceção (e.g., `SourceAPIError` propagada de forma inesperada, `TypeError`, `KeyError` em mapeamento de resultados), ela **não é capturada** e vira HTTP 500 genérico.
**Impacto:** Qualquer edge case em qualquer fonte = Internal Server Error para o usuário, sem fallback, sem cache, sem graceful degradation.

### BUG 3 — PNCP usa `tamanhoPagina=20` gerando milhares de requests (PERFORMANCE)
**Arquivo:** `pncp_client.py:907` (`_fetch_page_async`)
**Causa:** O parâmetro `tamanho` tem default `20`, e `_fetch_single_modality` (L1115) nunca override esse valor. Para uma busca de 180 dias com 27 UFs x 4 modalidades, cada UF/modalidade gera dezenas de páginas de 20 itens. Total: **milhares de requests HTTP** ao PNCP. Com timeout de 15s por modalidade, muitas não completam.
**Evidência Sentry:** Logs mostram `pagina=7`, `pagina=8`, `pagina=12`... sequenciais para mesma UF/modalidade — cada request buscando apenas 20 itens.
**Impacto:** Timeouts em cascata para UFs com muitos resultados (MG, PR, SC, MT, GO, SE, RO, RR). Perda de dados significativa.

### BUG 4 — ComprasGov `fetch()` re-raise sem dados parciais (PROPAGATION)
**Arquivo:** `clients/compras_gov_client.py:361-366`
**Causa:** Quando a primeira página falha (`total_fetched == 0`), o `except` block faz `raise` direto (L366). Embora `_wrap_source()` em `consolidation.py:473` capture essa exceção e a converta em `{"status": "error"}`, a cadeia de propagação funciona **em teoria**. Na prática, o erro é capturado mas o ComprasGov nunca retorna dados — amplificando a percepção de falha.
**Mitigação:** Track 1 (desabilitar ComprasGov) elimina este bug completamente. Quando T4 reimplementar ComprasGov v3, o `fetch()` deve tratar erros de forma idêntica ao `PortalComprasAdapter`.

### BUG 5 — `compras_gov_client.py` aponta para API v1 obsoleta
**Arquivo:** `clients/compras_gov_client.py:52`
**Causa:** `BASE_URL = "https://compras.dados.gov.br"` com endpoint `/licitacoes/v1/licitacoes.json`. Esta é a API v1 legacy que o governo está descontinuando. A nova API v3 está em `https://dadosabertos.compras.gov.br` com endpoints `/modulo-legado/1_consultarLicitacao` (legacy data) e `/modulo-contratacoes/1_consultarContratacoes_PNCP_14133` (Lei 14.133).
**Impacto:** Vamos trocar para uma API que terá estabilidade e suporte a longo prazo.

---

## Solução: 5 Tracks Parallelizáveis

### Track 1 — Desabilitar ComprasGov como fonte primária (P0, imediato)
**Arquivo:** `source_config/sources.py`

Trocar default de `ENABLE_SOURCE_COMPRAS_GOV` para `false`. O ComprasGov v1 é mais problema que solução — instável, dados federais apenas (PNCP já cobre federal), e API obsoleta.

```python
# ANTES (source_config/sources.py:406)
os.getenv("ENABLE_SOURCE_COMPRAS_GOV", "true").lower() == "true"

# DEPOIS
os.getenv("ENABLE_SOURCE_COMPRAS_GOV", "false").lower() == "true"
```

**Fallback adapter:** Trocar de ComprasGov para PNCP single-UF (ou remover fallback — já temos SWR cache como fallback via GTM-FIX-010).

```python
# ANTES (search_pipeline.py:640-642)
fallback_adapter = ComprasGovAdapter(
    timeout=source_config.compras_gov.timeout
)

# DEPOIS — Sem fallback adapter dedicado. O AllSourcesFailedError handler (L716)
# já tem fallback para Supabase stale cache (GTM-FIX-010)
fallback_adapter = None
```

### Track 2 — Exception catch genérico no pipeline (P0, segurança)
**Arquivo:** `search_pipeline.py:716-806`

Adicionar `except Exception` após os handlers existentes para capturar qualquer exceção inesperada e degradar gracefully em vez de 500.

```python
# DEPOIS (search_pipeline.py, após L791, antes de L792)
except Exception as e:
    # GTM-FIX-025 T2: Generic catch — never let source errors kill the pipeline
    logger.error(
        f"Unexpected error in multi-source fetch: {type(e).__name__}: {e}",
        exc_info=True,
    )
    sentry_sdk.set_tag("data_source", "consolidation_unexpected")
    sentry_sdk.capture_exception(e)

    # Try stale cache as last resort
    stale_cache = None
    if ctx.user and ctx.user.get("id"):
        stale_cache = await _supabase_get_cache(
            user_id=ctx.user["id"],
            params={
                "setor_id": request.setor_id,
                "ufs": request.ufs,
                "status": request.status.value if request.status else None,
                "modalidades": request.modalidades,
                "modo_busca": request.modo_busca,
            },
        )

    if stale_cache:
        logger.info(f"Serving stale cache after unexpected error: {e}")
        ctx.licitacoes_raw = stale_cache["results"]
        ctx.cached = True
        ctx.cached_at = stale_cache["cached_at"]
        ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
        ctx.is_partial = True
        ctx.degradation_reason = f"Unexpected error: {type(e).__name__}: {e}"
    else:
        logger.warning("No stale cache — returning empty after unexpected error")
        ctx.licitacoes_raw = []
        ctx.is_partial = True
        ctx.degradation_reason = f"Unexpected error: {type(e).__name__}: {e}"
```

### Track 3 — PNCP tamanhoPagina de 20→500 (P0, performance)
**Arquivo:** `pncp_client.py:1082-1158` (`_fetch_single_modality` → `_fetch_page_async`)

Passar `tamanho=500` na chamada de `_fetch_page_async`. A API PNCP suporta até 500 itens/página (documentado no PRD.md). Isto reduz as requests de ~50 por UF/modalidade para ~1-2.

```python
# ANTES (pncp_client.py:1115, dentro de _fetch_single_modality)
response = await self._fetch_page_async(
    data_inicial=data_inicial,
    data_final=data_final,
    modalidade=modalidade,
    uf=uf,
    pagina=pagina,
    status=status,
)

# DEPOIS
response = await self._fetch_page_async(
    data_inicial=data_inicial,
    data_final=data_final,
    modalidade=modalidade,
    uf=uf,
    pagina=pagina,
    tamanho=500,  # GTM-FIX-025 T3: PNCP supports up to 500/page
    status=status,
)
```

**Impacto estimado:**
- Busca 27 UFs x 4 mod: ~2700 requests → ~108 requests (25x redução)
- Timeouts esperados: 18+ → ~0 (cada request retorna mais dados por call)
- Tempo total de busca: ~18s → ~5-8s

### Track 4 — Migrar ComprasGov para API v3 (P1, evolução)
**Arquivo:** `clients/compras_gov_client.py` (rewrite)

Migrar `ComprasGovAdapter` da API v1 (`compras.dados.gov.br`) para API v3 (`dadosabertos.compras.gov.br`). A nova API tem Swagger, paginação moderna, e suporte ativo do Ministério da Gestão.

```python
# ANTES
BASE_URL = "https://compras.dados.gov.br"
# Endpoint: /licitacoes/v1/licitacoes.json

# DEPOIS
BASE_URL = "https://dadosabertos.compras.gov.br"
# Endpoint legacy: /modulo-legado/1_consultarLicitacao
# Endpoint 14.133: /modulo-contratacoes/1_consultarContratacoes_PNCP_14133
```

**API v3 Characteristics:**
- Base URL: `https://dadosabertos.compras.gov.br`
- Auth: Bearer token opcional (maioria dos endpoints abertos)
- Paginação: `pagina` + `tamanhoPagina` (configurável)
- Resposta: `resultado[]`, `totalRegistros`, `totalPaginas`, `paginasRestantes`
- Endpoint legacy: `/modulo-legado/1_consultarLicitacao` — params: `data_publicacao_inicial`, `data_publicacao_final`, `uasg`, `modalidade`
- Endpoint Lei 14.133: `/modulo-contratacoes/1_consultarContratacoes_PNCP_14133` — params: `dataPublicacaoPncpInicial`, `dataPublicacaoPncpFinal`, `codigoModalidade`
- Docs: [Swagger UI](https://dadosabertos.compras.gov.br/swagger-ui/index.html) | [OpenAPI](https://dadosabertos.compras.gov.br/v3/api-docs) | [Manual PDF](https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/manual-dados-abertos/manual-api-compras.pdf)

**Decisão:** Usar AMBOS endpoints (legacy + 14.133) em paralelo para máxima cobertura. O endpoint legacy cobre compras anteriores a 2024, e o endpoint 14.133 cobre as novas contratações.

**Nota:** Este track pode ser implementado como story separada (GTM-FIX-026) se o time preferir — os Tracks 1-3 são suficientes para resolver o crash imediato. O Track 4 adiciona valor mas não é bloqueante.

### Track 5 — Testes de resiliência do pipeline (P1, qualidade)
**Arquivos:** `tests/test_pipeline_resilience.py` (novo)

Testes específicos para os cenários que causaram o crash:

1. **ComprasGov 503 não mata pipeline** — mock ComprasGov retornando 503, verificar que PNCP+PCP results são preservados
2. **Exceção genérica em consolidation** — mock lançando TypeError, verificar fallback para cache
3. **Timeout global com dados parciais** — verificar que dados salvaged são retornados
4. **Todas as fontes falham** — verificar fallback para stale cache
5. **PNCP com tamanhoPagina=500** — verificar que requests usam page size correto

---

## Acceptance Criteria

### Track 1 — Desabilitar ComprasGov v1
- [ ] AC1: `ENABLE_SOURCE_COMPRAS_GOV` default é `"false"` em `source_config/sources.py`
- [ ] AC2: `fallback_adapter` em `search_pipeline.py:640` é `None` (sem fallback dedicado)
- [ ] AC3: Quando `ENABLE_SOURCE_COMPRAS_GOV=false`, ComprasGov não aparece em `Available sources` log
- [ ] AC4: Busca completa com sucesso usando apenas PNCP+PCP (2 fontes)

### Track 2 — Exception catch genérico
- [ ] AC5: `except Exception` handler existe em `_execute_multi_source()` após `AllSourcesFailedError` e `TimeoutError`
- [ ] AC6: Handler tenta stale cache via `_supabase_get_cache()` antes de retornar vazio
- [ ] AC7: Handler loga `type(e).__name__` + `str(e)` + envia para Sentry com tag `data_source=consolidation_unexpected`
- [ ] AC8: Handler seta `ctx.is_partial=True` + `ctx.degradation_reason` com tipo do erro
- [ ] AC9: Nenhuma exceção de consolidation resulta em HTTP 500 — sempre retorna resultado (mesmo que vazio + degraded)

### Track 3 — PNCP tamanhoPagina 500
- [ ] AC10: `_fetch_single_modality` passa `tamanho=500` para `_fetch_page_async`
- [ ] AC11: Logs de produção mostram `tamanhoPagina=500` nas requests PNCP
- [ ] AC12: Busca 27 UFs completa sem timeouts de modalidade (sob condições normais de rede)
- [ ] AC13: Testes existentes do PNCP client continuam passando

### Track 4 — ComprasGov v3 (se implementado nesta story)
- [ ] AC14: `ComprasGovAdapter.BASE_URL` aponta para `https://dadosabertos.compras.gov.br`
- [ ] AC15: Endpoint usa `/modulo-legado/1_consultarLicitacao` com params corretos
- [ ] AC16: `health_check()` valida a nova API
- [ ] AC17: `normalize()` mapeia campos da v3 para `UnifiedProcurement`
- [ ] AC18: Testes de `compras_gov_client.py` reescritos para v3

### Track 5 — Testes de resiliência
- [ ] AC19: Teste "ComprasGov 503 preserves PNCP+PCP results" passa
- [ ] AC20: Teste "unexpected exception triggers cache fallback" passa
- [ ] AC21: Teste "all sources fail triggers stale cache" passa
- [ ] AC22: Teste "PNCP uses tamanhoPagina=500" verifica parâmetro na request
- [ ] AC23: Zero regressões nos testes existentes

---

## Arquivos Afetados

| Track | Arquivo | Linhas | Mudança |
|-------|---------|--------|---------|
| T1 | `source_config/sources.py` | 406 | Default `COMPRAS_GOV` → `false` |
| T1 | `search_pipeline.py` | 640-642 | `fallback_adapter = None` |
| T2 | `search_pipeline.py` | 791+ | Add `except Exception` handler |
| T3 | `pncp_client.py` | 1115 | `tamanho=500` em `_fetch_page_async` |
| T4 | `clients/compras_gov_client.py` | Full | Rewrite BASE_URL + endpoints + normalize |
| T4 | `tests/test_compras_gov_*.py` | Full | Rewrite para v3 |
| T5 | `tests/test_pipeline_resilience.py` | New | ~150 linhas de testes de resiliência |

---

## Mapa de Dependências

```
BUG 1 (ComprasGov morta) ──┐
                           ├──→ Track 1 (desabilitar v1) ──→ Imediato
BUG 5 (API v1 obsoleta) ──┘         │
                                     ├──→ Track 4 (migrar v3) ──→ Pode ser GTM-FIX-026
BUG 2 (no generic catch) ──────────→ Track 2 (exception safety)
BUG 3 (tamanhoPagina=20) ─────────→ Track 3 (500/page)
BUG 4 (re-raise sem parciais) ────→ Mitigado por Track 1 (ComprasGov desabilitado)

Track 5 (testes) ← depende de T1+T2+T3
```

**Caminho crítico:** T1 + T2 + T3 (paralelo) → T5 → commit
**Track 4:** Independente, pode ser implementado após T1-T3 ou como story separada.

---

## Priorização de Implementação

| Ordem | Track | Tempo | Bloqueante? |
|-------|-------|-------|-------------|
| 1 | T1 (disable ComprasGov) | 15min | Sim — remove a fonte instável |
| 1 | T2 (generic catch) | 30min | Sim — impede qualquer 500 futuro |
| 1 | T3 (tamanhoPagina=500) | 15min | Sim — elimina timeouts PNCP |
| 2 | T5 (testes) | 1-2h | Sim — valida os 3 fixes |
| 3 | T4 (ComprasGov v3) | 2-3h | Não — valor incremental |

**Tracks 1-3 são ~1h de implementação e resolvem 100% do crash.** Track 4 é melhoria evolutiva.

---

## Rollback Plan

1. `ENABLE_SOURCE_COMPRAS_GOV=true` — re-ativa ComprasGov v1 (reverte T1)
2. `tamanhoPagina` pode ser revertido para 20 removendo o parâmetro
3. Exception handler genérico é aditivo — sem risco de remoção

---

## Post-Fix Verification

```bash
# 1. Confirmar ComprasGov desabilitado
grep "ENABLE_SOURCE_COMPRAS_GOV" backend/source_config/sources.py
# Expected: "false"

# 2. Confirmar tamanhoPagina=500
grep -n "tamanho=500" backend/pncp_client.py
# Expected: match in _fetch_single_modality

# 3. Confirmar exception handler genérico
grep -n "except Exception" backend/search_pipeline.py
# Expected: handler after AllSourcesFailedError

# 4. Rodar testes
cd backend && python -m pytest tests/test_pipeline_resilience.py -v
cd backend && python -m pytest tests/ -x --timeout=60

# 5. Teste de produção
# Busca vestuário, 10+ UFs, 180 dias → deve completar sem 500
```

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| PNCP rejeita `tamanhoPagina=500` | Baixa | Alto | API docs confirmam suporte; fallback: testar com 100 se 500 falhar |
| ComprasGov v3 também instável | Média | Baixo | T4 é deferível; PNCP+PCP já cobrem 95%+ dos editais |
| `except Exception` mascara bugs reais | Média | Médio | Handler envia para Sentry com tag específica; não silencia, apenas graceful degrade |
| Page size 500 causa responses lentas | Baixa | Médio | PNCP responses são ~50KB/page max; network impact negligível |
| Testes existentes quebram com `tamanho=500` | Baixa | Baixo | Testes usam mocks; `tamanho` não é verificado nos asserts existentes |

---

## Definition of Done

- [ ] T1-T3 implementados e testados
- [ ] T5 testes de resiliência passando (5+ novos testes)
- [ ] Zero regressões nos testes existentes (backend + frontend)
- [ ] Busca em produção com 10+ UFs completa sem HTTP 500
- [ ] Sentry mostra zero `SourceAPIError` não-capturadas nas últimas 2h pós-deploy
- [ ] Story file atualizado com ACs checked

---

## Referências

- [ComprasGov API Instabilidade Constante (GestGov)](https://gestgov.discourse.group/t/api-compras-dados-gov-instabilidade-constante/27386)
- [Compras Dados Fora do Ar (GestGov)](https://gestgov.discourse.group/t/compras-dados-fora-do-ar/26000)
- [Nova API v3 — Swagger UI](https://dadosabertos.compras.gov.br/swagger-ui/index.html)
- [Nova API v3 — OpenAPI Docs](https://dadosabertos.compras.gov.br/v3/api-docs)
- [Manual API Compras.gov.br (PDF)](https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/manual-dados-abertos/manual-api-compras.pdf)
- [Comprasnet x PNCP — Migração (GestGov)](https://gestgov.discourse.group/t/comprasnet-x-pncp/27592)
- GTM-FIX-024: Fix anterior (6 bugs encadeados)
- GTM-FIX-010: SWR Cache (fallback cascade)
