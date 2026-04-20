# Task: Query DataLake (SmartLic-specific)

Procedimento canônico para agentes `aiox-deep-research` consultarem o DataLake do SmartLic.

## Quando usar

Sempre que a pesquisa envolva:
- Histórico de contratos de um CNPJ/órgão/setor
- Análise quantitativa de editais (N, valores, timeline, UF distribution)
- Volume de mercado por segmento

## Fontes

### `supplier_contracts` (2M+ linhas, histórico, sem TTL)

Campos principais:
- `cnpj_fornecedor`, `nome_fornecedor`
- `cnpj_orgao`, `nome_orgao`, `uf_orgao`, `esfera`
- `objeto_contrato`, `modalidade_id`
- `valor_contrato`, `data_assinatura`, `vigencia_inicio`, `vigencia_fim`
- `origem` (fonte da ingestão)

Uso típico:
```sql
-- Top 10 fornecedores em um setor/UF
SELECT cnpj_fornecedor, nome_fornecedor, COUNT(*) AS contratos, SUM(valor_contrato) AS volume
FROM supplier_contracts
WHERE uf_orgao = 'SC'
  AND objeto_contrato ILIKE ANY(ARRAY['%limpeza%', '%conservação%', '%zeladoria%'])
  AND data_assinatura >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY cnpj_fornecedor, nome_fornecedor
ORDER BY volume DESC
LIMIT 10;
```

### `pncp_raw_bids` (~50K linhas, abertos, TTL 12d)

Campos principais:
- `id_licitacao`, `objeto_licitacao`
- `uf`, `modalidade_id`, `esfera`
- `valor_estimado`, `data_publicacao`, `data_abertura`
- `orgao_cnpj`, `orgao_nome`
- `is_active` (soft-delete)
- `tsvector_portuguese(objeto_licitacao)` com GIN

Uso canônico via RPC:
```python
# backend/datalake_query.py
from datalake_query import query_datalake

results = query_datalake(
    query="limpeza conservação",
    filters={
        "uf": ["SC"],
        "modalidade_id": [8],  # Pregão
        "valor_min": 10000,
        "valor_max": 500000,
        "date_from": "2026-01-01",
    }
)
```

SQL equivalente (para exploração ad-hoc):
```sql
SELECT * FROM search_datalake(
  'limpeza & conservação',  -- tsquery Portuguese
  '{"uf": ["SC"], "modalidade_id": [8]}'::jsonb
);
```

## Decisão sobre qual usar

| Pergunta | Fonte |
|---|---|
| "Quem ganhou o que no último ano?" | `supplier_contracts` |
| "Quais editais abertos agora para o meu setor?" | `pncp_raw_bids` via `search_datalake` |
| "Qual o histórico deste CNPJ?" | `supplier_contracts` + filtro `cnpj_fornecedor` |
| "Tendência temporal de volume?" | `supplier_contracts` com `date_trunc('month', ...)` |
| "O que está abrindo em SC essa semana?" | `pncp_raw_bids` com `data_publicacao >= CURRENT_DATE - 7` |

## Gotchas

- **Não fazer SELECT \* em `supplier_contracts`** sem LIMIT — 2M linhas estouram o timeout
- **`pncp_raw_bids` tem `is_active=false` para soft-deletes** — sempre filtrar `WHERE is_active=true` a menos que queira histórico
- **tsquery PT exige operadores**: `'limpeza & conservação'` (AND), `'limpeza | zeladoria'` (OR). Usuários tendem a passar texto cru — normalizar antes
- **`pncp_raw_bids` tem retenção 12 dias** — queries "últimos 30 dias" não retornam tudo. Combinar com `supplier_contracts` (ou live API fallback)

## Performance

- `search_datalake` RPC: p95 <100ms com filtros UF+modalidade
- SELECT direto em `supplier_contracts`: adicionar LIMIT sempre; com índice em `cnpj_fornecedor` ou `(uf_orgao, data_assinatura)` responde em <500ms
- Se query ultrapassa 2s: simplificar, ou quebrar em paralelo (delegar a `aiox-dispatch`)

## Patterns em tests

Se você escrever test que usa estas tabelas:
- Patch `supabase_client.get_supabase` (não `search_cache.get_supabase`)
- Fixture para 100-500 linhas (não 2M — tests devem terminar em <30s)
- Não criar linhas reais — usar `returning_execute` mocked
