# GTM-RESILIENCE-E01 — Consolidar Logs para 50-60 Linhas/Busca

| Campo | Valor |
|-------|-------|
| **Track** | E — "Log Cirurgico" |
| **Prioridade** | P0 |
| **Sprint** | 1 |
| **Estimativa** | 6-8 horas |
| **Gaps Endereçados** | L-01, L-02, L-03, L-04 |
| **Dependências** | Nenhuma (pode iniciar imediatamente) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O backend do SmartLic gera **70-120 linhas de log por busca** distribuídas em 252+ chamadas `logger.*` nos módulos de hot path. O Railway tem um rate limit de aproximadamente 20K mensagens/dia. Com 1K buscas/dia projetadas para o GTM, seriam geradas 70K-120K linhas — **3-6x acima do limite**, resultando em dropped messages já observados em produção.

**Distribuição atual de logger calls no hot path:**

| Módulo | Logger Calls | % Total |
|--------|-------------|---------|
| `search_pipeline.py` | 82 | 32% |
| `pncp_client.py` | 75 | 30% |
| `filter.py` | 71 | 28% |
| `consolidation.py` | 15 | 6% |
| `progress.py` | 9 | 4% |

---

## Problema

### P1: Filter Stats — 9 `logger.info` Separados (L-01)

Em `search_pipeline.py` L1095-1105, as estatisticas de filtro sao emitidas como 9 chamadas individuais:

```python
logger.info(f"  - Total processadas: {stats.get('total', ...)}")
logger.info(f"  - Aprovadas: {stats.get('aprovadas', ...)}")
logger.info(f"  - Rejeitadas (UF): {stats.get('rejeitadas_uf', 0)}")
logger.info(f"  - Rejeitadas (Status): {stats.get('rejeitadas_status', 0)}")
logger.info(f"  - Rejeitadas (Esfera): {stats.get('rejeitadas_esfera', 0)}")
logger.info(f"  - Rejeitadas (Modalidade): {stats.get('rejeitadas_modalidade', 0)}")
logger.info(f"  - Rejeitadas (Municipio): {stats.get('rejeitadas_municipio', 0)}")
logger.info(f"  - Rejeitadas (Valor): {stats.get('rejeitadas_valor', 0)}")
logger.info(f"  - Rejeitadas (Keyword): {stats.get('rejeitadas_keyword', 0)}")
```

Sao 9 linhas onde 1 linha JSON estruturada seria suficiente e mais util para analise programatica.

### P2: Per-UF Logging — 15-20 Linhas por Busca Multi-UF (L-02)

Em `pncp_client.py`, cada UF gera 3+ logs: inicio do fetch, conclusao com contagem, e recovery se houver retry. Uma busca de 5 UFs gera 15-20 linhas so para o tracking per-UF. Linhas relevantes:

- L790: `logger.info(f"Fetching modalidade={modalidade}, UF={uf}")`
- L795: `logger.info(f"Fetching modalidade={modalidade}, UF={uf}")` (duplicado em outro branch)
- L1536: `logger.info(f"Fetched {len(all_items)} items for UF={uf} (truncated={...})")`
- L1654: `logger.warning(f"UF={uf} timed out after {PER_UF_TIMEOUT}s -- skipping")`
- L1765: `logger.info(f"AC7: UF={uf} recovered with {len(items)} items")`

### P3: Per-Retry Logging — 5-15 Linhas por Busca (L-03)

Cada tentativa de retry e logada individualmente em `pncp_client.py`:

- L1188: `logger.warning(f"Rate limited (429). Waiting {retry_after}s")`
- L1318: `logger.warning(f"Timeout. Retrying in {delay:.1f}s")`
- L1329: `logger.warning(f"HTTP error: {e}. Retrying in {delay:.1f}s")`

Com 5 retries por UF e 5 UFs, sao ate 25 linhas de retry. Apenas o resultado final importa (sucesso ou falha definitiva).

### P4: Per-Page Fetch Logging — 30-50 Linhas por Busca (L-04)

O fetch paginado loga cada pagina acessada. Com `tamanhoPagina=50` e centenas de resultados por UF, sao dezenas de logs implicitos. Linhas em `pncp_client.py`:

- L550: `logger.debug(...)` por pagina
- L614: `logger.debug(...)` por pagina
- L622: `logger.debug(f"No content (204) for page {pagina}")` por pagina
- L644: `logger.info(...)` por pagina com dados

---

## Solucao

### S1: Consolidar Filter Stats em 1 Log JSON Estruturado

Substituir as 9 chamadas `logger.info` (L1095-1105) por uma unica emissao JSON:

```python
logger.info(json.dumps({
    "event": "filter_complete",
    "total": stats.get("total", len(ctx.licitacoes_raw)),
    "passed": stats.get("aprovadas", len(ctx.licitacoes_filtradas)),
    "rejected": {
        "uf": stats.get("rejeitadas_uf", 0),
        "status": stats.get("rejeitadas_status", 0),
        "esfera": stats.get("rejeitadas_esfera", 0),
        "modalidade": stats.get("rejeitadas_modalidade", 0),
        "municipio": stats.get("rejeitadas_municipio", 0),
        "valor": stats.get("rejeitadas_valor", 0),
        "keyword": stats.get("rejeitadas_keyword", 0),
        "min_match": stats.get("rejeitadas_min_match", 0),
        "outros": stats.get("rejeitadas_outros", 0),
    }
}))
```

Reducao: 9 linhas -> 1 linha. (-8)

### S2: Agregar Per-UF em Sumario Final

Acumular resultados per-UF em um dict durante o fetch e emitir 1 log de sumario no final:

```python
logger.info(json.dumps({
    "event": "fetch_complete",
    "ufs_requested": len(request.ufs),
    "ufs_succeeded": len(successful_ufs),
    "ufs_failed": list(failed_ufs),
    "ufs_timed_out": list(timed_out_ufs),
    "ufs_recovered": list(recovered_ufs),
    "total_items": total_items,
    "total_pages": total_pages,
    "elapsed_s": round(elapsed, 2),
}))
```

Logs per-UF de start/completion rebaixados para `logger.debug`. Reducao: ~15 linhas -> 1 (+debug). (-12)

### S3: Per-Retry — Somente Resultado Final

Rebaixar logs de cada tentativa para `logger.debug`. Manter apenas 1 `logger.warning` no resultado final quando todas as retries falharam, ou 1 `logger.info` quando retry teve sucesso apos N tentativas:

```python
# Apos todas as retries
if success:
    if attempts > 1:
        logger.info(f"Succeeded after {attempts} attempts for UF={uf} mod={mod}")
else:
    logger.warning(f"Failed after {attempts} attempts for UF={uf} mod={mod}: {last_error}")
```

Reducao: ~10 linhas -> 1. (-10)

### S4: Per-Page Fetch — 1 Agregado

Substituir logs por pagina por um unico log agregado ao final da paginacao por UF:

```python
logger.info(f"Fetched {total_items} items in {pages_fetched} pages for UF={uf} ({elapsed:.1f}s)")
```

Logs individuais de pagina rebaixados para `logger.debug`. Reducao: ~40 linhas -> ~5 (1 por UF). (-35)

---

## Criterios de Aceite

### AC1: Filter Stats Consolidados em 1 Log JSON
- [ ] As 9 chamadas `logger.info` em `search_pipeline.py` L1095-1105 sao substituidas por 1 unica chamada `logger.info` com JSON estruturado
- [ ] O JSON contem todos os campos de rejeicao (`rejeitadas_uf`, `rejeitadas_status`, `rejeitadas_esfera`, `rejeitadas_modalidade`, `rejeitadas_municipio`, `rejeitadas_valor`, `rejeitadas_keyword`, `rejeitadas_min_match`, `rejeitadas_outros`) mais `total` e `passed`
- [ ] O JSON e parseable por ferramentas de analise (Railway log search, jq)
- **Verificacao:** Rodar busca com 3 UFs e confirmar 1 (nao 9) log line com prefixo `filter_complete`

### AC2: Per-UF Logging Agregado
- [ ] Logs de inicio per-UF (`Fetching modalidade=..., UF=...`) rebaixados de `logger.info` para `logger.debug`
- [ ] Logs de conclusao per-UF (`Fetched N items for UF=...`) rebaixados para `logger.debug`
- [ ] 1 log de sumario final emitido com contagem de UFs sucesso/falha/timeout/recovered e total de itens
- [ ] Log de sumario e JSON estruturado com campo `event: "fetch_complete"`
- **Verificacao:** Busca com 5 UFs gera no maximo 2 linhas INFO relacionadas a fetch (sumario + batch info), nao 15-20

### AC3: Per-Retry Somente Resultado Final
- [ ] `logger.warning` para cada tentativa de retry em `pncp_client.py` (L1188, L1318, L1329) rebaixados para `logger.debug`
- [ ] Apenas 1 log emitido no resultado final: `logger.info` se sucesso apos retries, `logger.warning` se falha definitiva
- [ ] O log final inclui numero de tentativas e motivo da falha (se aplicavel)
- **Verificacao:** Simular 3 retries com mock e confirmar 1 (nao 3) log line nivel INFO/WARNING

### AC4: Per-Page Fetch Agregado
- [ ] Logs individuais de cada pagina (L550, L614, L622, L644 em `pncp_client.py`) rebaixados para `logger.debug`
- [ ] 1 log agregado por UF no final da paginacao: `"Fetched X items in Y pages (Zs)"`
- **Verificacao:** Busca com UF que retorna 3+ paginas gera 1 (nao 3+) log line INFO

### AC5: Total de Logs por Busca <= 60
- [ ] Teste automatizado que executa pipeline completo com mock e conta linhas de log nivel INFO+WARNING+ERROR
- [ ] O total nao excede 60 linhas para uma busca de 5 UFs
- [ ] O total nao excede 35 linhas para uma busca de 1 UF
- **Verificacao:** `pytest test_log_volume.py -v` passa com assertivas de contagem

### AC6: Railway Rate Limit Respeitado
- [ ] Projecao documentada: 1K buscas/dia x 60 logs/busca = 60K linhas (dentro de 3x do limite de 20K com margem para logs de startup/cron)
- [ ] Se projecao excede, logs adicionais de menor prioridade sao rebaixados para DEBUG
- **Verificacao:** Calculo documentado no PR com baseline antes/depois

### AC7: Sem Regressao de Informacao
- [ ] Nenhuma informacao diagnostica e perdida — toda informacao previamente em INFO agora esta em DEBUG (acessivel via `LOG_LEVEL=DEBUG`)
- [ ] Logs de erro (`logger.error`) e alertas criticos (`logger.warning` para circuit breaker trip, timeout definitivo, etc.) nao sao rebaixados
- [ ] O log JSON final por estagio (fetch, filter, LLM, Excel) contem todas as metricas necessarias para debug pos-mortem
- **Verificacao:** Revisao manual comparando informacao antes/depois

### AC8: Zero Regressao nos Testes Existentes
- [ ] `pytest backend/` passa com baseline atual (excluindo pre-existing failures)
- [ ] Nenhum teste existente quebra por mudanca em asserções de log
- [ ] Testes que assertam sobre logs especificos sao atualizados para o novo formato
- **Verificacao:** CI pipeline verde

---

## Arquivos Afetados

| Arquivo | Mudanca |
|---------|---------|
| `backend/search_pipeline.py` | Consolidar filter stats (L1095-1105), agregar per-UF sumario, rebaixar logs internos |
| `backend/pncp_client.py` | Rebaixar per-retry, per-page, per-UF para DEBUG; agregar fetch sumario |
| `backend/filter.py` | Rebaixar logs internos de cada filtro individual para DEBUG |
| `backend/consolidation.py` | Rebaixar per-source detail logs para DEBUG; manter sumario |
| `backend/tests/test_log_volume.py` | **NOVO** — teste de contagem de linhas de log por busca |

---

## Definition of Done

- [ ] Todos os 8 ACs verificados e marcados
- [ ] PR aprovado com before/after log count documentado
- [ ] Testes existentes passam sem regressao
- [ ] Novo teste `test_log_volume.py` com threshold de 60 linhas
- [ ] Manual spot-check: busca em staging gera <= 60 linhas (captura de tela do Railway logs)
- [ ] MEMORY.md atualizado com baseline de log count
