# Schema `supplier_contracts` para SEO (aiox-seo)

Estrutura da tabela principal usada para gerar pages programmatic.

## Colunas relevantes

| Coluna | Tipo | Descrição | Uso em SEO |
|---|---|---|---|
| `id` | uuid | Primary key | Key interno |
| `cnpj_fornecedor` | text | CNPJ do vencedor | `/fornecedores/[cnpj]` slug |
| `nome_fornecedor` | text | Razão social | Title + breadcrumb |
| `cnpj_orgao` | text | CNPJ do órgão | `/orgaos/[cnpj]` slug |
| `nome_orgao` | text | Nome do órgão | Title + breadcrumb |
| `uf_orgao` | text (2) | UF | Filtro + facet |
| `esfera` | text | Federal/Estadual/Municipal | Filtro + label |
| `objeto_contrato` | text | Descrição do objeto | Body content + SEO keywords |
| `modalidade_id` | int | Código modalidade (4/5/6/7/8/12) | Badge + filtro |
| `valor_contrato` | numeric | Valor em R$ | Destaque numérico |
| `data_assinatura` | date | Data assinatura | Timestamp + sort |
| `vigencia_inicio` | date | Início vigência | — |
| `vigencia_fim` | date | Fim vigência | Flag "em vigor" |
| `origem` | text | Fonte (PNCP/ComprasGov/etc) | Footer attribution |
| `created_at` | timestamptz | Ingestion timestamp | — |
| `updated_at` | timestamptz | Last update | "atualizado em" |

## Queries canônicas para pages

### `/fornecedores/[cnpj]` — Page de fornecedor

```sql
-- Resumo agregado
SELECT
  cnpj_fornecedor,
  nome_fornecedor,
  COUNT(*) AS total_contratos,
  SUM(valor_contrato) AS volume_total,
  AVG(valor_contrato) AS ticket_medio,
  MIN(data_assinatura) AS primeiro_contrato,
  MAX(data_assinatura) AS ultimo_contrato,
  COUNT(DISTINCT cnpj_orgao) AS orgaos_unicos,
  COUNT(DISTINCT uf_orgao) AS ufs_atuacao
FROM supplier_contracts
WHERE cnpj_fornecedor = $1
GROUP BY cnpj_fornecedor, nome_fornecedor;

-- Top 10 órgãos deste fornecedor
SELECT nome_orgao, cnpj_orgao, COUNT(*) AS contratos, SUM(valor_contrato) AS volume
FROM supplier_contracts
WHERE cnpj_fornecedor = $1
GROUP BY nome_orgao, cnpj_orgao
ORDER BY volume DESC
LIMIT 10;

-- Distribuição por setor/modalidade (via classificação)
-- (precisa join com classificação LLM ou keyword inference de objeto_contrato)
```

### `/orgaos/[cnpj]` — Page de órgão

```sql
SELECT
  cnpj_orgao,
  nome_orgao,
  uf_orgao,
  esfera,
  COUNT(*) AS contratos_assinados,
  SUM(valor_contrato) AS volume_total,
  AVG(valor_contrato) AS ticket_medio,
  COUNT(DISTINCT cnpj_fornecedor) AS fornecedores_unicos
FROM supplier_contracts
WHERE cnpj_orgao = $1
GROUP BY cnpj_orgao, nome_orgao, uf_orgao, esfera;

-- Top fornecedores deste órgão
SELECT nome_fornecedor, cnpj_fornecedor, COUNT(*) AS contratos, SUM(valor_contrato) AS volume
FROM supplier_contracts
WHERE cnpj_orgao = $1
GROUP BY nome_fornecedor, cnpj_fornecedor
ORDER BY volume DESC
LIMIT 10;
```

### `/observatorio/[setor]` — Hub por setor

```sql
-- Classificação via keywords dos sectors_data.yaml
-- Exemplo setor 'servicos-limpeza':
SELECT
  uf_orgao,
  COUNT(*) AS contratos,
  SUM(valor_contrato) AS volume,
  AVG(valor_contrato) AS ticket_medio
FROM supplier_contracts
WHERE objeto_contrato ~* '\m(limpeza|conservacao|conservação|zeladoria|higienizacao)\M'
  AND data_assinatura >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY uf_orgao
ORDER BY volume DESC;
```

## Índices importantes (já existem)

- B-tree em `(cnpj_fornecedor, data_assinatura)` — perfil fornecedor
- B-tree em `(cnpj_orgao, data_assinatura)` — perfil órgão
- B-tree em `(uf_orgao, data_assinatura)` — análise geográfica
- GIN em `to_tsvector('portuguese', objeto_contrato)` — para classificação setorial

## Performance para SSR

- Page de fornecedor/órgão (top 10k cada): query <500ms com índice adequado
- Hub setorial: query <1s se LIMIT 100 UFs (mas só 27 UFs existem — safe)
- Cache: ISR não aplica (dado muda); usar HTTP cache headers + CDN (Cache-Control: public, max-age=86400)

## Slugs canônicos

| Recurso | Pattern | Exemplo |
|---|---|---|
| Fornecedor | `/fornecedores/{cnpj-14}` | `/fornecedores/12345678000190` |
| Órgão | `/orgaos/{cnpj-14}` | `/orgaos/98765432000112` |
| Setor | `/observatorio/{setor-id}` | `/observatorio/servicos-limpeza` |
| UF × setor | `/observatorio/{setor-id}/{uf-lowercase}` | `/observatorio/servicos-limpeza/sc` |
| Contrato individual (se útil) | `/contratos/{id-uuid}` | `/contratos/ab12-...` |

CNPJ sem pontuação no URL. Em display, formatar com máscara brasileira (`XX.XXX.XXX/XXXX-XX`).
