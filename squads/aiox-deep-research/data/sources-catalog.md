# Catálogo de Fontes — aiox-deep-research SmartLic

Fontes autorizadas + constraints + cite-guidelines. Agente pesquisador DEVE citar fonte de cada afirmação.

## Internas (primary)

### DataLake Supabase (fonte principal)

| Tabela | Cobertura | Confiabilidade | Citar como |
|---|---|---|---|
| `supplier_contracts` | Contratos históricos (múltiplos anos, ~2M linhas) | Alta (dados oficiais pós-homologação) | "supplier_contracts (SmartLic DataLake, ingestion date N)" |
| `pncp_raw_bids` | Editais abertos (12d window) | Alta (dados diretos PNCP) | "pncp_raw_bids (SmartLic DataLake, snapshot X)" |
| `ingestion_runs` | Audit de crawls | Operacional | "ingestion_runs (SmartLic Layer 1)" |

## APIs públicas oficiais (secondary — quando datalake não cobre)

### PNCP — Portal Nacional de Contratações Públicas

- URL: `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`
- Confiabilidade: **Fonte oficial** (Lei 14.133, Art. 174)
- Cobertura: União + Estados + Municípios (crescente desde 2023)
- Constraints: `tamanhoPagina <= 50` (reduzido Feb/2026, >50 retorna HTTP 400 silencioso)
- Circuit breaker: 15 falhas → 60s cooldown
- Cite como: "PNCP (pncp.gov.br), consulta YYYY-MM-DD, N registros"

### PCP v2 — Portal de Compras Públicas

- URL: `https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos`
- Confiabilidade: **Média-alta** (agregador privado, dados sem validação governamental direta)
- Cobertura: Complementa PNCP em UFs onde PNCP é fraco
- Constraints: `valor_estimado=0.0` (v2 sem dado de valor — NÃO usar para análise de valor)
- Cite como: "PCP v2 (portaldecompraspublicas.com.br), N registros"

### ComprasGov v3

- URL: `https://dadosabertos.compras.gov.br`
- Confiabilidade: **Alta** (oficial federal — SIASG)
- Cobertura: Federal + algumas estaduais
- Constraints: Dual-endpoint (Lei 8.666 legacy + Lei 14.133)
- Cite como: "ComprasGov v3 (dadosabertos.compras.gov.br), N registros"

## Web search (tertiary — contexto)

Use via MCP EXA (`mcp__docker-gateway__web_search_exa`) apenas para:
- Notícias sobre órgãos/fornecedores específicos
- Mudanças regulatórias (decretos, IN, atos normativos — mas **validar com legal-analyst**)
- Consultas públicas abertas
- Ranking/relatórios setoriais (FGV, IBPT, ABIN, etc)

### Hierarquia de confiança (web)

1. **.gov.br** (oficial, federal ou estadual)
2. **.jus.br** (Poder Judiciário, STF, TCU, TCE)
3. **Imprensa oficial** (DOU, diários oficiais estaduais)
4. **Publicações acadêmicas** (FGV, USP, UFRJ, periódicos peer-reviewed)
5. **Imprensa profissional** (Valor, Folha, Estadão para business; Consultor Jurídico, Jota para jurídico)
6. **Blogs/Medium/LinkedIn posts** — apenas como ponto de partida, NUNCA como fonte única

## Não-fontes (vetadas)

- ChatGPT/Perplexity output cru — use como discovery tool, mas cite a fonte ORIGINAL encontrada
- Agregadores pagos sem transparência metodológica
- Wikipedia para afirmações sobre empresa/edital específico (OK para conceito genérico)
- Reddit/Twitter/X sem link de fonte primária

## Política de citação

Toda afirmação quantitativa DEVE ter:
- Número específico (não "vários", "muitos")
- Unidade (R$, quantidade, percentual)
- Período (datas exatas)
- Fonte (tabela+filtros OU URL+data de acesso OU DOI)
- N amostral se for amostra (não população)

**Exemplo bom:**
> "Em SC, no segmento limpeza (CNAE 81.21), 73 contratos foram assinados em 2026-Q1 com valor médio R$ 187K (mediana R$ 92K, N=73). Fonte: supplier_contracts (SmartLic DataLake, snapshot 2026-04-20, filtro `uf_orgao='SC' AND objeto_contrato ILIKE '%limpeza%' AND data_assinatura BETWEEN '2026-01-01' AND '2026-03-31'`)."

**Exemplo ruim:**
> "Em SC há muita demanda por serviços de limpeza nos últimos meses."
