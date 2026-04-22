# Glossário de Domínio B2G — SmartLic

Termos canônicos usados em todos os squads. Tradução livre ou uso do termo original em português onde apropriado.

## Portais e Fontes

| Termo | Definição |
|---|---|
| **PNCP** | Portal Nacional de Contratações Públicas (`pncp.gov.br`). Fonte oficial, priority 1. API: `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`. `tamanhoPagina` max=50 (reduzido de 500 em Feb/2026 — >50 retorna HTTP 400 silencioso). |
| **PCP v2** | Portal de Compras Públicas v2 (`compras.api.portaldecompraspublicas.com.br/v2`). Priority 2. API pública sem auth. Paginação fixa 10/página. `valor_estimado=0.0` (v2 sem dado de valor). |
| **ComprasGov v3** | `dadosabertos.compras.gov.br`. Priority 3. Dual-endpoint (Lei 8.666 legacy + Lei 14.133). |
| **DataLake (Layer 1)** | Ingestão periódica para Supabase: `pncp_raw_bids` (~50K open bids, retenção 12d) + `supplier_contracts` (~2M historical, feed inbound orgânico). Crawl completo diário 2am BRT; incremental 3x/dia. |
| **SICAF** | Sistema de Cadastramento Unificado de Fornecedores — cadastro nacional. Não integrado diretamente (contexto). |

## Modalidades (Lei 14.133)

| Código | Modalidade | Uso típico |
|---|---|---|
| 4 | Concorrência | Obras e serviços de grande porte |
| 5 | Concurso | Escolha de trabalho técnico/artístico/científico |
| 6 | Leilão | Alienação de bens |
| 7 | Diálogo Competitivo | Inovação tecnológica, soluções complexas |
| 8 | Pregão | Bens/serviços comuns (mais usada) |
| 12 | Dispensa/Inexigibilidade | Valor baixo ou fornecedor único |

**Lei 14.133** (Nova Lei de Licitações, 2021) substituiu gradualmente a **Lei 8.666** (1993) até abril 2023. A Lei 10.520 (Pregão) também foi revogada. **Lei 13.303** rege estatais.

## Entidades de Negócio

| Termo | Definição |
|---|---|
| **Edital** | Documento público convocando fornecedores. Sinônimo de "licitação" no uso cotidiano. |
| **Órgão** | Entidade pública compradora (prefeitura, secretaria, autarquia, estatal). |
| **CNPJ** | Cadastro Nacional da Pessoa Jurídica — identifica fornecedor e órgão. |
| **UF** | Unidade Federativa (estado). 27 no total (26 + DF). |
| **Esfera** | Federal / Estadual / Municipal. |
| **Valor estimado** | Preço base do edital. PCP v2 não fornece, fica 0.0. |
| **Contrato** | Acordo formalizado após edital vencido. `supplier_contracts` armazena histórico. |
| **Fornecedor** | Empresa que se candidata/vence. |

## Setores (domínio SmartLic)

15 setores definidos em `backend/sectors_data.yaml`, cada um com `keywords`, `exclusions`, e `viability_value_range`. Ver `sectors-15.yaml` neste diretório para referência.

## Conceitos do Produto

| Termo | Definição |
|---|---|
| **Viabilidade** | Score 0-100 baseado em 4 fatores: modalidade (30%) + timeline (25%) + valor (25%) + geografia (20%). Implementado em `backend/viability.py`. |
| **Classificação LLM** | Pipeline para determinar relevância setorial de edital: keyword density > 5% ("keyword"), 2-5% ("llm_standard"), 1-2% ("llm_conservative"), 0% ("llm_zero_match" via GPT-4.1-nano). |
| **Fallback PENDING_REVIEW** | Quando LLM falha: marca como `PENDING_REVIEW` se `LLM_FALLBACK_PENDING_ENABLED=true`; caso contrário, `REJECT` hard. |
| **Trial** | 14 dias gratuitos (STORY-264/277/319). Sem cartão de crédito. |
| **Plano Pro** | R$397/mes mensal, R$357/mes semestral (10% off), R$297/mes anual (25% off). |
| **Plano Consultoria** | R$997/mes mensal, R$897/mes semestral, R$797/mes anual. |
| **Sessão de busca** | Conjunto de resultados salvos em `search_sessions` + `search_results_cache`. |
| **Pipeline (kanban)** | Funil de oportunidades do usuário: drag-and-drop de editais através de estágios. |

## Observabilidade

| Métrica Prometheus | Significado |
|---|---|
| `smartlic_filter_decisions_by_setor_total` | Decisões do filtro por setor |
| `smartlic_llm_fallback_rejects_total` | Rejeições por falha do LLM |
| `smartlic_pipeline_budget_exceeded_total{phase,source}` | Budget de tempo excedido (timeout waterfall) |
| `smartlic_pncp_max_page_size_changed_total` | Canário: PNCP quebrou limite de página |
| `smartlic_pncp_canary_consecutive_failures` | Canário: falhas consecutivas PNCP |

## Nunca confundir

- **Modalidade 8 (Pregão)** ≠ Pregão Eletrônico específico — é a modalidade genérica, que pode ser eletrônico ou presencial (raro hoje)
- **PCP v2** ≠ "Portal de Compras Públicas v1" (descontinuado)
- **`pncp_raw_bids`** (abertos, 12d TTL) ≠ **`supplier_contracts`** (históricos, 2M+ rows, sem TTL)
- **Layer 1** (ingestão ETL) ≠ **Layer 3** (cache de resultados, passivo SWR)
