# DATA-001: Integrar LicitaJa como Fonte de Dados no intel-busca

**Status:** Done
**Priority:** P1 — Alta (amplia cobertura de editais)
**Track:** DATA — Data Sources
**Created:** 2026-03-23
**Depends on:** —
**Blocks:** —

---

## Contexto

O comando `/intel-busca` coleta editais de 3 fontes (PNCP, PCP v2, ComprasGov v3), sendo que ComprasGov v3 está fora do ar desde 03/03/2026. A integração do **LicitaJa** (licitaja.com.br) como 4a fonte amplia significativamente a cobertura, pois o LicitaJa agrega editais de portais municipais, estaduais e federais que nem sempre aparecem no PNCP.

### API LicitaJa v1.1.3

- **Base URL:** `https://www.licitaja.com.br/api/v1`
- **Auth:** Header `X-API-KEY` com chave fornecida
- **Rate limit:** 10 requisicoes/minuto (imposto pelo provedor)
- **Formato:** JSON (header `Accept: application/json`)
- **Paginacao:** `page` + `items` (max 25/pagina)
- **Documentacao:** https://app.swaggerhub.com/apis-docs/bidhits/licitaja-br/1.1.3

### Endpoints Relevantes

| Endpoint | Metodo | Uso |
|----------|--------|-----|
| `/tender/search` | GET | Busca com filtros (keyword, UF, cidade, valor, data, modalidade) |
| `/tender/{tenderId}` | GET | Detalhes completo de um edital |

### Parametros de Busca Relevantes

| Param | Tipo | Descricao |
|-------|------|-----------|
| `keyword` | string | Termos de busca |
| `state` | string | UF(s) — cod estado |
| `opening_date_from` | string | Data inicio (YYYYmmdd) |
| `opening_date_to` | string | Data fim (YYYYmmdd) |
| `tender_value_min` | int | Valor minimo |
| `tender_value_max` | int | Valor maximo |
| `type` | string | Modalidade(s), separadas por virgula |
| `page` | int | Pagina (default 1) |
| `items` | int | Itens/pagina (max 25) |
| `order` | int | 0=abertura, 1=cadastro, 4=relevancia |
| `smartsearch` | int | 0=desabilitar IA do LicitaJa |

### Resposta do `/tender/search`

```json
{
  "page": 1,
  "total_results": 342,
  "results": [
    {
      "tenderId": "ABC123",
      "catalog_date": "20260320",
      "close_date": "20260415",
      "tender_object": "Construcao de escola municipal...",
      "city": "Florianopolis",
      "state": "SC",
      "agency": "Prefeitura Municipal de Florianopolis",
      "type": "Pregao Eletronico",
      "value": 1500000.00,
      "url": "https://...",
      "lots": [...],
      ...
    }
  ]
}
```

### Restricoes

- **10 req/min** — necessario rate limiter dedicado (mais restritivo que PNCP)
- **Max 25 items/pagina** — paginacao obrigatoria para resultados grandes
- **`smartsearch=0`** recomendado para controle total (evitar expansao automatica de termos)
- **HTTP 401** = chave invalida OU quota excedida (mesma resposta)

---

## Acceptance Criteria

### Configuracao & Infra

- [x] **AC1:** Adicionar variaveis ao `.env` local e `.env.example`:
  ```
  LICITAJA_API_KEY=EBC0F0F7564D3617FEE09174796EDF74
  LICITAJA_BASE_URL=https://www.licitaja.com.br/api/v1
  LICITAJA_ENABLED=true
  LICITAJA_RATE_LIMIT_RPM=10
  LICITAJA_TIMEOUT=30
  ```

- [x] **AC2:** Registrar variaveis em `backend/config.py` com defaults seguros:
  ```python
  LICITAJA_API_KEY = os.environ.get("LICITAJA_API_KEY", "")
  LICITAJA_BASE_URL = os.environ.get("LICITAJA_BASE_URL", "https://www.licitaja.com.br/api/v1")
  LICITAJA_ENABLED = os.environ.get("LICITAJA_ENABLED", "false").lower() == "true"
  LICITAJA_RATE_LIMIT_RPM = int(os.environ.get("LICITAJA_RATE_LIMIT_RPM", "10"))
  LICITAJA_TIMEOUT = int(os.environ.get("LICITAJA_TIMEOUT", "30"))
  ```

### Cliente API (`scripts/licitaja_client.py`)

- [x] **AC3:** Criar modulo `scripts/licitaja_client.py` com classe `LicitaJaClient`:
  - Header `X-API-KEY` em todas as requisicoes
  - Header `Accept: application/json`
  - Rate limiter: max 10 req/min com token bucket ou sliding window
  - Retry: backoff `[2.0, 6.0, 15.0]` em HTTP 429/500/502/503/504
  - Timeout: 30s por requisicao (configuravel)
  - Logging estruturado com contadores de req/erro/throttle

- [x] **AC4:** Metodo `search_tenders(keyword, states, date_from, date_to, value_min, value_max, page, items)`:
  - Converte parametros para formato LicitaJa (datas YYYYmmdd, states como string)
  - `smartsearch=0` fixo (controle nosso, nao do LicitaJa)
  - `order=0` (por data de abertura — consistente com pipeline)
  - Retorna `(results: list[dict], total_results: int, status: str)`
  - Status tags: `"API"`, `"API_FAILED"`, `"API_PARTIAL"`, `"RATE_LIMITED"`

- [x] **AC5:** Metodo `search_all_pages(keyword, states, ...)` com paginacao automatica:
  - Itera ate `total_results` ou `max_pages` (default 20 = 500 editais)
  - Respeita rate limit (10 req/min = 1 req a cada 6s minimo)
  - Yield de resultados por pagina (nao acumula tudo em memoria)
  - Checkpoint: salva progresso em `data/licitaja_checkpoint.json` para retomar

- [x] **AC6:** Metodo `get_tender(tender_id)` para detalhes completos:
  - Usado na fase de enriquecimento (Step 5 do intel-busca) se necessario
  - Cache local em `data/licitaja_cache.json` (TTL 24h por tender)

- [x] **AC7:** Health check: `GET /tender/search?keyword=teste&items=1` com timeout 10s:
  - HTTP 200 + results array = AVAILABLE
  - HTTP 401 = UNAUTHORIZED (chave invalida)
  - HTTP 429 = RATE_LIMITED
  - Timeout/error = UNAVAILABLE

### Integracao no intel-collect.py

- [x] **AC8:** Adicionar coleta LicitaJa no Step 2 do `scripts/intel-collect.py`:
  - Prioridade 4 (apos PNCP=1, PCP=2, ComprasGov=3)
  - Executar APOS fontes principais (nao paralelo — respeitar rate limit)
  - Usar keywords do setor detectado (sample de 10-15 termos mais relevantes)
  - Filtrar por UFs solicitadas + range de datas + modalidades competitivas

- [x] **AC9:** Normalizar registros LicitaJa para formato unificado do pipeline:
  ```python
  {
    "_id": f"LICITAJA-{tender_id}",
    "_source": "licitaja",
    "objeto": tender_object,
    "orgao": agency,
    "cnpj_orgao": "",  # LicitaJa nao fornece CNPJ do orgao
    "uf": state,
    "municipio": city,
    "valor_estimado": value or 0.0,
    "modalidade_nome": type,
    "data_publicacao": catalog_date,  # converter YYYYmmdd -> YYYY-MM-DD
    "data_abertura_proposta": close_date,  # converter YYYYmmdd -> ISO
    "link_edital": url,
    "link_pncp": None,  # nao e fonte PNCP
    "status_temporal": "URGENTE|PLANEJAVEL|IMINENTE",  # calcular
    "dias_restantes": int,  # calcular
  }
  ```

- [x] **AC10:** Deduplicacao cross-source:
  - Comparar `objeto` via Jaccard similarity (threshold 0.6) contra editais PNCP/PCP
  - Se duplicata, manter versao da fonte com maior prioridade (PNCP > PCP > ComprasGov > LicitaJa)
  - Registrar em `estatisticas.total_licitaja_dedup_removed`

### Estatisticas & Observabilidade

- [x] **AC11:** Adicionar campos a secao `estatisticas` do JSON de saida:
  ```python
  "licitaja_total_raw": int,          # total bruto retornado
  "licitaja_pages_fetched": int,      # paginas consumidas
  "licitaja_errors": int,             # erros HTTP
  "licitaja_rate_limited": int,       # vezes throttled
  "licitaja_dedup_removed": int,      # removidos por dedup cross-source
  "licitaja_after_filter": int,       # aprovados apos filtro semantico
  "licitaja_unique_added": int,       # editais unicos contribuidos (nao duplicatas)
  "licitaja_status": "API|API_FAILED|RATE_LIMITED|DISABLED|UNAVAILABLE"
  ```

- [x] **AC12:** Log resumo no final da coleta:
  ```
  [LicitaJa] 3 paginas, 67 editais brutos, 12 apos filtro, 8 unicos (4 dedup)
  ```

### Feature Flag & Graceful Degradation

- [x] **AC13:** Se `LICITAJA_ENABLED=false` ou `LICITAJA_API_KEY` vazio:
  - Skip silencioso, sem erro
  - `licitaja_status: "DISABLED"` nas estatisticas
  - Pipeline funciona identicamente ao atual

- [x] **AC14:** Se API retorna HTTP 401 (chave invalida/quota):
  - Log WARNING com detalhe
  - `licitaja_status: "UNAUTHORIZED"`
  - Nao retry (diferente de 429)
  - Pipeline continua sem LicitaJa

- [x] **AC15:** Se rate limit atingido (HTTP 429 ou 10 req/min):
  - Backoff exponencial com cap de 60s
  - Apos 3 throttles consecutivos, interromper coleta LicitaJa
  - Retornar resultados parciais com `licitaja_status: "API_PARTIAL"`

### Testes

- [x] **AC16:** `tests/test_licitaja_client.py` (unit):
  - Mock HTTP: search com paginacao, get tender, health check
  - Rate limiter: verifica intervalo minimo entre requests
  - Retry: backoff em 429/500
  - Normalizacao de datas (YYYYmmdd -> YYYY-MM-DD)
  - Timeout handling
  - Minimo 15 testes

- [x] **AC17:** `tests/test_intel_collect_licitaja.py` (integracao):
  - Mock LicitaJaClient: verifica que intel-collect chama LicitaJa com params corretos
  - Dedup cross-source: edital duplicado PNCP+LicitaJa -> mantém PNCP
  - Feature flag OFF -> skip silencioso
  - Estatisticas preenchidas corretamente
  - Minimo 8 testes

---

## Notas Tecnicas

### Rate Limiting (CRITICO)

O LicitaJa impoe **10 req/min** — muito mais restritivo que PNCP (~40 req/min efetivo). Estrategia:

1. **Token bucket** com capacidade 10, reposicao 1 token/6s
2. **Nao paralelizar** requests LicitaJa (sequencial estrito)
3. **Executar APOS** PNCP/PCP (nao concorre por tempo de pipeline)
4. **Max pages configurable** — default 20 (= 120s de coleta no pior caso)
5. Se pipeline esta perto do timeout (>90s elapsed), **skip LicitaJa**

### Conversao de Datas

LicitaJa usa formato `YYYYmmdd` (ex: `20260415`), pipeline usa `YYYY-MM-DD`. Converter em normalize.

### Campo `cnpj_orgao` Ausente

LicitaJa nao fornece CNPJ do orgao comprador. Impactos:
- Competitive intel (historico de contratos) nao funciona para editais LicitaJa-only
- Dedup por `_id` usa `LICITAJA-{tenderId}` (prefixo dedicado)
- Se o mesmo edital existir no PNCP (com CNPJ), a versao PNCP e mantida

### Keyword Strategy

Usar amostra de 10-15 keywords mais relevantes do setor (nao as 250+ completas):
- LicitaJa busca por relevancia, nao por densidade como nosso filtro
- Muitos termos = resultados muito amplos + mais paginas = mais rate limit consumido
- Agrupar em 2-3 buscas com termos diferentes para cobertura

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Rate limit insuficiente para UFs grandes | Media | Medio | Max pages + timeout guard |
| API instavel/fora do ar | Baixa | Baixo | Graceful degradation (AC13-15) |
| Duplicatas nao detectadas (objeto diferente) | Baixa | Baixo | Dedup Jaccard + manual review |
| Custo de API (quota excedida) | Media | Medio | Monitorar licitaja_rate_limited |
| Formato de resposta muda sem aviso | Baixa | Alto | Validacao de schema + alerta |

---

## Estimativa

| Componente | Complexidade |
|-----------|-------------|
| LicitaJaClient + rate limiter | Media |
| Integracao intel-collect.py | Media |
| Normalizacao + dedup | Baixa |
| Testes | Media |
| **Total** | **Media** |

---

## File List

| File | Action | Description |
|------|--------|-------------|
| `.env` | Edit | Adicionar LICITAJA_* vars |
| `.env.example` | Edit | Documentar LICITAJA_* vars |
| `backend/config.py` | Edit | Registrar LICITAJA_* configs |
| `scripts/licitaja_client.py` | **Create** | Cliente API LicitaJa |
| `scripts/intel-collect.py` | Edit | Integrar coleta LicitaJa no Step 2 |
| `tests/test_licitaja_client.py` | **Create** | Testes unitarios do cliente |
| `tests/test_intel_collect_licitaja.py` | **Create** | Testes integracao pipeline |
