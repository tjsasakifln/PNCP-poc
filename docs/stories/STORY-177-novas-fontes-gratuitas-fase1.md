# STORY-177: Integração de Novas Fontes Gratuitas de Licitações - Fase 1

**Status:** Complete
**Prioridade:** P1 - Alta
**Estimativa:** 13 story points (2 sprints)
**Tipo:** Feature (Brownfield Enhancement)
**Pesquisa Base:** `docs/research/novas-fontes.md`

---

## Contexto

O SmartLic atualmente depende exclusivamente do PNCP como fonte de dados. A pesquisa em `docs/research/novas-fontes.md` mapeou 10+ plataformas gratuitas que cobrem ~3.000 municípios adicionais. Esta story implementa a **Fase 1: fontes baseadas em API pública** — o caminho de menor risco e maior ROI.

### Por que Fase 1 foca em APIs (não scraping)?

| Abordagem | Risco Técnico | Risco Legal | Manutenção | Time-to-Value |
|-----------|---------------|-------------|------------|---------------|
| API pública (Fase 1) | Baixo | Nenhum (dados abertos) | Baixa | 2 sprints |
| Scraping (Fase 2+) | Alto | Médio (ToS, robots.txt) | Alta | 4+ sprints |

**Decisão:** Implementar primeiro as fontes com API documentada + o `ConsolidationService` (infraestrutura que serve Fase 2+).

### Arquitetura Existente (já implementada, pronta para uso)

O backend já possui infraestrutura multi-fonte em `backend/clients/`:

| Artefato | Arquivo | Status |
|----------|---------|--------|
| `SourceAdapter` (ABC) | `clients/base.py` | Completo |
| `UnifiedProcurement` (modelo canônico) | `clients/base.py` | Completo |
| `to_legacy_format()` (compatibilidade) | `clients/base.py:251` | Completo |
| `SourceConfig` (config multi-fonte) | `source_config/sources.py` | Completo |
| `PortalComprasAdapter` (parcial) | `clients/portal_compras_client.py` | ~50% |
| `LicitarAdapter` (stub) | `clients/licitar_client.py` | 0% |
| `ConsolidationService` | **NÃO EXISTE** | 0% |

**O que falta:** o serviço que orquestra tudo (`ConsolidationService`) + adaptadores para novas fontes gratuitas.

---

## Escopo

### Dentro do Escopo (Fase 1)

1. **ConsolidationService** — orquestrador multi-fonte
2. **ComprasGovAdapter** — API federal de dados abertos (sem auth)
3. **Completar PortalComprasAdapter** — API com chave (já parcialmente implementada)
4. **Registrar novas fontes** em `SourceConfig` + `.env`
5. **Integrar no endpoint `/buscar`** com feature flag
6. **Endpoint `/sources/health`** para monitoramento
7. **Frontend:** indicador de fonte nos resultados
8. **Testes unitários e de integração**

### Fora do Escopo (Fase 2+)

- IPM Sistemas / Atende.Net (requer Playwright + scraping)
- Betha Sistemas (padrão de URLs desconhecido)
- ABASE, Fiorilli, Elotech, CECAM, Better Tech, JR Sistemas (investigação necessária)
- Portais Estaduais AL/SP (podem entrar em Fase 1.5 como fast-follow)
- Sistema de descoberta de municípios
- Playwright-based scrapers

---

## Acceptance Criteria

### AC1: ConsolidationService — Orquestrador Multi-Fonte

**Arquivo:** `backend/consolidation.py`

- [x] Classe `ConsolidationService` que recebe `SourceConfig` e dict de `SourceAdapter` instances
- [x] Método `async fetch_all(data_inicial, data_final, ufs, on_source_complete=None) -> ConsolidationResult`
- [x] Busca de todas as fontes habilitadas em paralelo via `asyncio.gather(return_exceptions=True)`
- [x] Cada fonte executa com timeout individual (`consolidation.timeout_per_source`, default 25s)
- [x] Timeout global (`consolidation.timeout_global`, default 60s) cancela fontes pendentes
- [x] Deduplicação por `dedup_key` (manter item da fonte com menor `priority` = maior prioridade)
- [x] Conversão automática de `UnifiedProcurement` → formato legado via `to_legacy_format()`
- [x] Callback `on_source_complete(source_code, count, error)` para progress tracking
- [x] Se TODAS as fontes falharem e `fail_on_all_errors=True`, levantar `AllSourcesFailedError`
- [x] Se pelo menos uma fonte retornar dados, retornar resultados parciais (graceful degradation)
- [x] Log estruturado com métricas por fonte: duration_ms, record_count, error

**Dataclass de retorno:**
```python
@dataclass
class SourceResult:
    source_code: str
    record_count: int
    duration_ms: int
    error: Optional[str] = None
    status: str = "success"  # "success" | "error" | "timeout" | "disabled"

@dataclass
class ConsolidationResult:
    records: List[Dict[str, Any]]  # formato legado (já convertido)
    total_before_dedup: int
    total_after_dedup: int
    duplicates_removed: int
    source_results: List[SourceResult]
    elapsed_ms: int
```

**Testes:** `backend/tests/test_consolidation.py`
- [x] Test com 2+ fontes mock retornando dados sem overlap → todos aparecem
- [x] Test com 2 fontes retornando mesmo `dedup_key` → mantém fonte de maior prioridade
- [x] Test com 1 fonte timeout + 1 OK → retorna resultados parciais
- [x] Test com todas fontes em erro + `fail_on_all_errors=True` → levanta exceção
- [x] Test com todas fontes em erro + `fail_on_all_errors=False` → retorna lista vazia
- [x] Test de callback `on_source_complete` chamado para cada fonte

---

### AC2: ComprasGovAdapter — API Federal de Dados Abertos

**Arquivo:** `backend/clients/compras_gov_client.py`

**API Base:** `https://compras.dados.gov.br/licitacoes/v1/licitacoes.json`
**Auth:** Nenhuma (dados abertos governamentais)
**Formato:** JSON

- [x] Classe `ComprasGovAdapter(SourceAdapter)` com metadata:
  ```python
  code = "COMPRAS_GOV"
  name = "ComprasGov - Dados Abertos Federal"
  base_url = "https://compras.dados.gov.br"
  priority = 3  # Após PNCP (1) e Portal (2)
  rate_limit_rps = 2.0  # Conservador
  ```
- [x] `health_check()`: GET na base URL com timeout 5s, retorna `SourceStatus.AVAILABLE` se HTTP 200
- [x] `fetch()`: Async generator que:
  - Monta URL com parâmetros de data (`data_inicio`, `data_fim`)
  - Lida com paginação (incrementa `offset` enquanto houver resultados)
  - Aplica rate limiting interno (sleep entre requests)
  - Filtra por UF client-side se `ufs` fornecido
  - Yield `UnifiedProcurement` normalizado para cada item
  - Loga progresso a cada 100 items
- [x] `normalize()`: Mapeia campos da API → `UnifiedProcurement`:

  | Campo API ComprasGov | Campo UnifiedProcurement |
  |----------------------|--------------------------|
  | `identificador` | `source_id` |
  | `objeto` ou `descricao` | `objeto` |
  | `valor_licitacao` | `valor_estimado` |
  | `orgao_nome` ou `nome_orgao` | `orgao` |
  | `orgao_cnpj` ou `cnpj` | `cnpj_orgao` |
  | `uf` | `uf` |
  | `municipio` | `municipio` |
  | `data_publicacao` | `data_publicacao` |
  | `data_abertura` | `data_abertura` |
  | `modalidade_licitacao` | `modalidade` |
  | `situacao` | `situacao` |
  | (construído) | `link_edital` |
  | `"COMPRAS_GOV"` | `source_name` |
  | `"F"` (Federal) | `esfera` |

  **Nota:** Os nomes exatos dos campos da API devem ser confirmados no primeiro teste. O adapter deve ter mapeamento flexível que tente múltiplas variações de nome.

- [x] Header `User-Agent: SmartLic/1.0 (contato@smartlic.com.br)` em todos os requests
- [x] Retry com backoff exponencial (3 tentativas, base 2s)
- [x] Se API retornar 429, respeitar `Retry-After` header

**Testes:** `backend/tests/test_compras_gov_client.py`
- [x] Test `health_check()` com mock HTTP 200 → AVAILABLE
- [x] Test `health_check()` com mock timeout → UNAVAILABLE
- [x] Test `fetch()` com mock de 1 página de resultados → yields UnifiedProcurement corretos
- [x] Test `fetch()` com paginação (2+ páginas) → yields todos os resultados
- [x] Test `fetch()` com filtro de UF → exclui UFs não solicitadas
- [x] Test `normalize()` com resposta completa → campos mapeados corretamente
- [x] Test `normalize()` com campos faltando → defaults sem crash
- [x] Test rate limiting (sleep entre requests)

---

### AC3: Completar PortalComprasAdapter

**Arquivo:** `backend/clients/portal_compras_client.py` (já existe, ~50% implementado)

- [x] Verificar e completar método `fetch()` (async generator yielding `UnifiedProcurement`)
- [x] Verificar e completar método `normalize()` (mapeamento de campos)
- [x] Garantir que `health_check()` funciona
- [x] Se `PORTAL_COMPRAS_API_KEY` não estiver configurada, adapter se desabilita gracefully (log warning, não crash)
- [x] Adicionar testes para os métodos completados

**Testes:** `backend/tests/test_portal_compras_client.py`
- [x] Test `health_check()` com API key válida
- [x] Test `fetch()` com mock de resultados
- [x] Test behavior quando API key está ausente → não crash, retorna vazio

---

### AC4: Registrar ComprasGov em SourceConfig

**Arquivos:**
- `backend/source_config/sources.py`
- `backend/.env.example` (documentação)

- [x] Adicionar `COMPRAS_GOV = "ComprasGov"` ao enum `SourceCode`
- [x] Adicionar `compras_gov: SingleSourceConfig` ao `SourceConfig`:
  ```python
  compras_gov: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
      code=SourceCode.COMPRAS_GOV,
      name="ComprasGov - Dados Abertos Federal",
      base_url="https://compras.dados.gov.br",
      enabled=True,   # Habilitado por padrão (não requer auth)
      timeout=30,
      rate_limit_rps=2.0,
      priority=3,
  ))
  ```
- [x] Adicionar `ENABLE_SOURCE_COMPRAS_GOV` ao `from_env()`
- [x] Incluir `compras_gov` em `get_enabled_sources()`, `get_enabled_source_configs()`, `get_source()`
- [x] Adicionar variáveis ao `.env.example` com documentação

---

### AC5: Integrar ConsolidationService no Endpoint /buscar

**Arquivo:** `backend/main.py` — método `buscar_licitacoes()` (~linha 778+)

- [x] Feature flag: `ENABLE_MULTI_SOURCE` (env var, default `false`)
- [x] Quando `ENABLE_MULTI_SOURCE=false`: comportamento atual (PNCP only) — ZERO risco de regressão
- [x] Quando `ENABLE_MULTI_SOURCE=true`:
  1. Instanciar `ConsolidationService` com fontes habilitadas
  2. Chamar `consolidation.fetch_all(data_inicial, data_final, ufs, on_source_complete=callback)`
  3. Resultado já está em formato legado → pipeline existente funciona sem alteração:
     - `aplicar_todos_filtros()` → funciona
     - `create_excel()` → funciona
     - `llm.py` → funciona
  4. Incluir `source_results` nas métricas da resposta
- [x] Progress tracking via SSE deve mostrar progresso por fonte quando multi-source ativo
- [x] `BuscaResponse` ganha campo opcional `source_stats: Optional[List[SourceResult]]`

**IMPORTANTE:** A integração NÃO altera o fluxo PNCP existente. Multi-source é aditivo.

**Teste de Integração:**
- [x] Com `ENABLE_MULTI_SOURCE=false` → busca funciona exatamente como antes
- [x] Com `ENABLE_MULTI_SOURCE=true` e fontes adicionais habilitadas → resultados incluem dados de múltiplas fontes
- [x] Com multi-source ativo e fonte secundária em timeout → resultados do PNCP retornam normalmente

---

### AC6: Endpoint de Health Check de Fontes

**Arquivo:** `backend/main.py`

- [x] `GET /sources/health` → retorna status de todas as fontes configuradas
- [x] Response format:
  ```json
  {
    "sources": [
      {
        "code": "PNCP",
        "name": "Portal Nacional de Contratações Públicas",
        "enabled": true,
        "status": "available",
        "response_ms": 245,
        "priority": 1
      },
      {
        "code": "COMPRAS_GOV",
        "name": "ComprasGov - Dados Abertos Federal",
        "enabled": true,
        "status": "available",
        "response_ms": 890,
        "priority": 3
      }
    ],
    "multi_source_enabled": true,
    "total_enabled": 3,
    "total_available": 2,
    "checked_at": "2026-02-09T15:30:00Z"
  }
  ```
- [x] Não requer autenticação (informação não sensível)
- [x] Timeout de 5s por health check (em paralelo)
- [x] Cache de 60s para evitar spam na API

---

### AC7: Frontend — Indicador de Fonte nos Resultados

**Arquivo:** `frontend/app/buscar/page.tsx`

- [x] Quando resultado tem campo `_source` (presente no formato legado):
  - Exibir badge pequeno no card de resultado: "PNCP", "ComprasGov", "Portal"
  - Badge com cor distinta por fonte (ex: PNCP=azul, ComprasGov=verde, Portal=roxo)
- [x] No resumo da busca, mostrar breakdown por fonte:
  ```
  120 licitações encontradas (PNCP: 95, ComprasGov: 22, Portal: 3)
  ```
- [x] Se multi-source desabilitado (default), nenhuma mudança visual (backward compatible)

---

### AC8: Testes e Qualidade

- [x] Todos os novos arquivos têm 90%+ de cobertura de testes
- [x] Testes existentes continuam passando (0 regressões)
- [x] `pytest --cov` mantém threshold de 70%+
- [x] TypeScript check frontend: `npx tsc --noEmit` passa limpo
- [x] `npm test` frontend: sem novas falhas além das 70 pré-existentes
- [x] Backend 21 falhas pré-existentes: não aumentar

---

## Arquitetura de Implementação

### Diagrama de Fluxo Multi-Fonte

```
BuscaRequest
    │
    ├── ENABLE_MULTI_SOURCE=false ──→ AsyncPNCPClient (fluxo atual, sem mudanças)
    │
    └── ENABLE_MULTI_SOURCE=true ──→ ConsolidationService
                                        ├── PNCPAdapter (priority=1)
                                        ├── PortalComprasAdapter (priority=2)
                                        └── ComprasGovAdapter (priority=3)
                                              │
                                        [asyncio.gather com timeouts]
                                              │
                                        [Deduplicação por dedup_key]
                                              │
                                        [to_legacy_format() para cada]
                                              │
                                        List[Dict] (formato legado)
                                              │
                                   ┌──────────┴──────────┐
                                   │ Pipeline existente   │
                                   │ (SEM ALTERAÇÕES)     │
                                   │                      │
                                   │ aplicar_todos_filtros │
                                   │ create_excel          │
                                   │ llm.py summary        │
                                   └──────────┬──────────┘
                                              │
                                        BuscaResponse
                                        + source_stats (novo)
```

### Mapeamento de Campos (Contrato de Dados)

Para o pipeline existente funcionar, cada fonte DEVE fornecer estes campos no formato legado (via `to_legacy_format()`):

| Campo Legado (filter.py/excel.py) | Obrigatório? | Fallback se ausente |
|-----------------------------------|--------------|---------------------|
| `objetoCompra` | **SIM** | Sem match de keyword → excluído |
| `valorTotalEstimado` | **SIM** | `0.0` (pode ser filtrado por range) |
| `uf` | **SIM** | `""` (excluído pelo filtro de UF) |
| `codigoCompra` | SIM | `source_id` |
| `nomeOrgao` | Recomendado | `"Não informado"` |
| `municipio` | Recomendado | `""` |
| `dataPublicacaoPncp` | Recomendado | `None` |
| `dataAberturaProposta` | Recomendado | `None` (afeta heurística de status) |
| `modalidadeNome` | Opcional | `""` |
| `situacaoCompraNome` | Opcional | `""` (afeta inferência de status) |
| `linkSistemaOrigem` | Opcional | `""` |
| `_source` | Automático | Sempre preenchido pelo adapter |
| `_dedup_key` | Automático | Gerado por `UnifiedProcurement` |

---

## Variáveis de Ambiente

Adicionar ao `.env.example`:

```bash
# === Multi-Source Configuration ===
# Feature flag para busca multi-fonte (default: false)
ENABLE_MULTI_SOURCE=false

# --- ComprasGov (Federal - Dados Abertos) ---
# Não requer API key (dados abertos governamentais)
ENABLE_SOURCE_COMPRAS_GOV=true

# --- Portal de Compras Públicas ---
# Requer API key: https://bibliotecapcp.zendesk.com/hc/pt-br/articles/4593549708570
ENABLE_SOURCE_PORTAL=true
PORTAL_COMPRAS_API_KEY=

# --- Consolidação ---
CONSOLIDATION_TIMEOUT_GLOBAL=60
CONSOLIDATION_TIMEOUT_PER_SOURCE=25
CONSOLIDATION_DEDUP_STRATEGY=first_seen
CONSOLIDATION_MAX_CONCURRENT=5
```

---

## Ordem de Implementação (Sequência Recomendada)

| # | Task | Arquivo(s) | Depende de | SP |
|---|------|-----------|------------|-----|
| 1 | Registrar ComprasGov em SourceConfig (AC4) | `source_config/sources.py` | — | 1 |
| 2 | Implementar ComprasGovAdapter (AC2) | `clients/compras_gov_client.py` | #1 | 3 |
| 3 | Completar PortalComprasAdapter (AC3) | `clients/portal_compras_client.py` | — | 2 |
| 4 | Implementar ConsolidationService (AC1) | `consolidation.py` | #2, #3 | 3 |
| 5 | Integrar no /buscar (AC5) | `main.py` | #4 | 2 |
| 6 | Endpoint /sources/health (AC6) | `main.py` | #4 | 1 |
| 7 | Frontend source indicator (AC7) | `app/buscar/page.tsx` | #5 | 1 |
| **Total** | | | | **13** |

---

## Riscos e Mitigações

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| ComprasGov API instável ou offline | Baixa | Baixo | É fonte complementar; PNCP continua sendo primary. Feature flag permite desabilitar. |
| Campos da API ComprasGov diferentes do esperado | Média | Médio | `normalize()` com mapeamento flexível + fallbacks. Teste manual na primeira integração. |
| Aumento de latência com multi-source | Baixa | Médio | Fontes em paralelo; timeout per-source de 25s. PNCP não é bloqueado por outras fontes. |
| Duplicatas entre PNCP e ComprasGov | Alta | Baixo | Dedup por `dedup_key` (CNPJ + número edital + ano). |
| Regressão no fluxo existente | Muito Baixa | Alto | Feature flag `ENABLE_MULTI_SOURCE=false` como default. Testes de regressão. |

---

## Definition of Done

- [x] Todos os ACs (1-8) implementados e testados
- [x] Feature flag `ENABLE_MULTI_SOURCE` funciona corretamente (false = sem mudanças, true = multi-fonte)
- [x] `pytest --cov` > 70% no backend
- [x] Zero regressões nos testes existentes
- [x] TypeScript check limpo
- [x] `.env.example` atualizado com novas variáveis documentadas
- [x] Code review aprovado
- [x] Deploy com feature flag desligado (ativação gradual posterior)

---

## Relação com Fase 2+

Esta story cria a **infraestrutura fundamental** (`ConsolidationService`, patterns de adapter, dedup, health checks) que será reutilizada em stories futuras:

| Fase | Story Futura | Novas Fontes | Depende de STORY-177 |
|------|-------------|--------------|---------------------|
| 1.5 | Portais Estaduais (AL, SP) | 2 APIs estaduais | ConsolidationService, SourceConfig |
| 2 | IPM Atende.Net | 850+ municípios (scraping) | ConsolidationService, adapter pattern |
| 2 | Betha Sistemas | 800 municípios (investigar) | ConsolidationService, adapter pattern |
| 3 | ABASE, Fiorilli, Elotech | 1300+ municípios | ConsolidationService, scraping infra |
| 3 | CECAM, Better Tech, JR | Long tail | ConsolidationService |

**Cada fonte futura = 1 novo arquivo `clients/xxx_client.py`** + registro no `SourceConfig`. O pipeline inteiro (filtros, Excel, LLM) funciona automaticamente via `to_legacy_format()`.
