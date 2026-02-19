# GTM-RESILIENCE-D01 — Inspeção Item/Lote para Classificação Granular

| Campo | Valor |
|-------|-------|
| **Track** | D — Classificação de Precisao |
| **Prioridade** | P1 |
| **Sprint** | 3 |
| **Estimativa** | 6-8 horas |
| **Gaps Endereçados** | CL-01 |
| **Dependências** | Nenhuma (usa API PNCP existente) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O pipeline de classificação atual (4 camadas em `filter.py`) analisa exclusivamente o campo `objetoCompra` — a descrição de nivel superior da licitação. Essa descrição e frequentemente generica ("Aquisição de materiais diversos") e nao revela a composição real dos itens.

A API PNCP fornece um endpoint de itens por contratação (`/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens`) que retorna o array `itens[]` com descrição individual, codigo NCM, unidade de medida, quantidade e valor unitario. Essa granularidade e invisivel para o classificador atual.

**Exemplo real do problema:**
- `objetoCompra`: "Registro de preços para aquisição de materiais diversos"
- `itens[]`: 80% uniformes/EPIs + 20% material de escritorio
- **Resultado atual**: Rejeitado (densidade de keywords <1% no objeto genérico)
- **Resultado esperado**: Aceito (majority rule: >50% itens do setor)

## Problema

A classificação baseada apenas em `objetoCompra` gera falsos negativos para licitações com descrições genéricas cujos itens individuais sao claramente relevantes. Licitações de registro de preço sao particularmente afetadas — o objeto e genérico mas os itens revelam a composição real. Estima-se que 10-20% dos falsos negativos atuais seriam corrigidos pela inspeção de itens.

## Solução

Implementar inspeção de itens/lotes da API PNCP para licitações na "zona cinza" (0-5% density), aplicando majority rule e sinais de domínio para decisão mais precisa.

### Fluxo proposto:

```
Bid chega ao filter.py
  └─ Densidade 0-5% (zona cinza)?
       └─ SIM → Fetch itens[] da API PNCP
            ├─ Majority rule: >50% itens matching setor → ACCEPT
            ├─ Sinais de domínio: NCM, unidades, tamanhos → boost
            └─ Source weighting: evidência de itens > evidência de objeto
       └─ NAO → Fluxo normal (keyword/LLM)
```

### Sinais de domínio por setor:
- **Vestuário**: NCM 61xx/62xx (vestuário), unidades "peça/kit/conjunto", tamanhos "P/M/G/GG/XG"
- **Saúde**: NCM 3004/3006 (medicamentos/dispositivos), unidades "ampola/frasco/cx"
- **TI**: NCM 8471/8473 (computadores/partes), unidades "unidade/licença"

### Budget de custo:
- Max 20 licitações com item-fetch por busca (evitar overhead excessivo)
- Timeout de 5s por fetch de itens (não bloquear pipeline)
- Cache de itens por 24h (itens não mudam frequentemente)

---

## Acceptance Criteria

### AC1 — Fetch de Itens da API PNCP
- [x] Nova função `fetch_bid_items(cnpj, ano, sequencial)` em `pncp_client.py`
- [x] Endpoint: `GET /v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens`
- [x] Timeout de 5s por request (independente do timeout de busca)
- [x] Retry 1x em caso de 429/5xx (usando mesma logica de backoff existente)
- [x] Retorna `List[Dict]` com campos: `descricao`, `codigoNcm`, `unidadeMedida`, `quantidade`, `valorUnitario`
- [x] Retorna lista vazia (sem erro) se endpoint retorna 404 ou timeout

### AC2 — Trigger de Inspeção (Zona Cinza)
- [x] Item inspection dispara SOMENTE para licitações com density 0-5% no `objetoCompra`
- [x] Limit de 20 item-fetches por busca (configurável via `MAX_ITEM_INSPECTIONS` env var, default 20)
- [x] Licitações com density >5% (auto-accept) ou <0% (impossível) nao disparam fetch
- [x] Contador de inspections resetado por busca

### AC3 — Majority Rule
- [x] Para cada bid inspecionada, cada item e classificado como "matching" ou "non-matching" usando keywords do setor
- [x] Se >50% dos itens sao matching → bid aceita com `relevance_source="item_inspection"`
- [x] Se <=50% → bid segue para LLM arbiter normalmente (nao e rejeitada automaticamente)
- [x] Matching e por contagem de itens, NAO por valor (item de R$1 conta igual a item de R$10.000)

### AC4 — Sinais de Domínio (Domain Signals)
- [x] Novo campo `domain_signals` em `sectors_data.yaml` por setor com: `ncm_prefixes[]`, `unit_patterns[]`, `size_patterns[]`
- [x] NCM prefix match: se `codigoNcm` começa com qualquer prefix listado → item e matching (independente de keywords)
- [x] Unit pattern match: se `unidadeMedida` contém pattern do setor → boost de 0.5 item equivalente
- [x] Size pattern match: se `descricao` contém padrão de tamanho do setor (P/M/G/GG) → boost de 0.5 item equivalente
- [x] Boosts sao aditivos mas capped (1 item real + boosts = max 2 items equivalentes)

### AC5 — Source Weighting
- [x] Quando item inspection e majority rule decidem ACCEPT, a decisão NAO e sobrescrita pelo LLM do objeto
- [x] Hierarquia: `item_inspection` (peso 3) > `keyword` no objeto (peso 2) > `llm_standard` (peso 1)
- [x] Log indica qual source decidiu: `"Accepted by item_inspection: 12/15 items matching (80%)"`

### AC6 — Budget e Performance
- [x] Max 20 item-fetches por busca (hardcoded floor, env var pode aumentar mas nao diminuir abaixo de 5)
- [x] Item fetches executam em paralelo via ThreadPoolExecutor com max_workers=5
- [x] Tempo total de item inspection nao excede 15s (timeout global de fase)
- [x] Se timeout global de fase estoura, bids nao inspecionadas seguem fluxo normal (LLM)
- [x] Métrica logada: `item_inspections_performed`, `item_inspections_accepted`, `item_fetch_avg_ms`

### AC7 — Cache de Itens
- [x] Itens fetchados sao cacheados em memória por 24h (key = `cnpj:ano:sequencial`)
- [x] Cache usa OrderedDict LRU (similar pattern to `_arbiter_cache`)
- [x] Eviction LRU com max 1000 entries
- [x] Cache hit nao conta contra o budget de 20 fetches

### AC8 — Feature Flag
- [x] `ITEM_INSPECTION_ENABLED` env var (default `true`)
- [x] Quando `false`, zona cinza segue direto para LLM sem fetch de itens
- [x] Flag verificada no runtime (nao na importação)
- [x] Adicionada ao `_FEATURE_FLAG_REGISTRY` existente

### AC9 — Testes
- [x] Teste unitário: fetch_bid_items retorna dados estruturados com mock HTTP
- [x] Teste unitário: majority rule aceita bid com 8/10 itens matching
- [x] Teste unitário: majority rule rejeita (envia para LLM) bid com 4/10 itens matching
- [x] Teste unitário: domain signals NCM prefix match funciona
- [x] Teste unitário: budget de 20 nao e excedido (21a bid vai para LLM)
- [x] Teste unitário: timeout de 5s por fetch respeitado
- [x] Teste unitário: cache hit nao conta contra budget
- [x] Teste de integração: busca com 3 bids na zona cinza, 2 aceitas por item inspection, 1 vai para LLM

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/pncp_client.py` | Nova função `fetch_bid_items()` |
| `backend/filter.py` | Integração de item inspection na zona cinza (density 0-5%) |
| `backend/sectors_data.yaml` | Novo campo `domain_signals` por setor |
| `backend/sectors.py` | Parser para `domain_signals` |
| `backend/item_inspector.py` | **NOVO** — lógica de majority rule, domain signals, budget |
| `backend/config.py` | `MAX_ITEM_INSPECTIONS`, `ITEM_INSPECTION_ENABLED` |
| `backend/tests/test_item_inspector.py` | **NOVO** — testes unitários e integração |

---

## Definition of Done

- [x] Todos os 9 ACs verificados e passando
- [x] Nenhuma regressão nos testes existentes de filter.py e llm_arbiter.py
- [x] Coverage do novo módulo >= 80% (19 tests covering all paths)
- [x] Tempo de busca não aumenta mais que 15s no p95 (phase timeout enforced)
- [x] Feature flag permite desabilitar sem deploy
- [x] Métricas de item inspection logadas em formato JSON estruturado
- [ ] Code review aprovado por @architect
