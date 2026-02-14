# STORY-255: Querido Diário — Cobertura Municipal via Diários Oficiais

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-255 |
| **Priority** | P3 |
| **Sprint** | Sprint 4 |
| **Estimate** | 10h |
| **Depends on** | STORY-252 (multi-source ativo) |
| **Blocks** | Nenhuma |

## Contexto

O [Querido Diário](https://queridodiario.ok.org.br/) é um projeto open-source da Open Knowledge Brasil que indexa e disponibiliza diários oficiais municipais em formato pesquisável. A API é **100% gratuita, sem autenticação**, e cobre ~1.047 municípios com busca full-text.

### Por Que Integrar

1. **Cobertura municipal complementar** — captura licitações publicadas em diários oficiais que ainda não apareceram no PNCP (delay de publicação)
2. **Zero dependência** — sem auth, sem API key, sem cost
3. **Early detection** — avisos de licitação aparecem no diário oficial ANTES do PNCP em muitos casos
4. **Fonte resiliente** — quando PNCP está fora, diários oficiais continuam disponíveis
5. **Text search poderoso** — OpenSearch com operadores booleanos, wildcards, frases exatas

### Dados da API

| Item | Valor |
|------|-------|
| **Base URL** | `https://api.queridodiario.ok.org.br` |
| **Docs** | `https://api.queridodiario.ok.org.br/docs` |
| **Auth** | Nenhuma |
| **Rate Limit** | ~60 req/min (soft, não enforced) |
| **Cobertura** | ~1.047 municípios (full-text), municipal apenas |
| **Formato datas** | YYYY-MM-DD |
| **Paginação** | `size` + `offset` (max 10.000 resultados por query) |
| **GitHub** | [okfn-brasil/querido-diario-api](https://github.com/okfn-brasil/querido-diario-api) |

### Desafio Principal: Dados Não-Estruturados

Diferente do PNCP (dados estruturados com campos tipados), o Querido Diário retorna **texto bruto de PDFs** dos diários oficiais. Uma licitação de uniformes aparece assim:

```
AVISO DE LICITAÇÃO - PREGÃO ELETRÔNICO Nº 023/2026
OBJETO: Aquisição de uniformes escolares para a rede municipal de ensino,
compreendendo camisetas, bermudas e tênis, conforme especificações do
Termo de Referência. VALOR ESTIMADO: R$ 450.000,00. ABERTURA:
28/02/2026 às 09:00. Edital disponível em: compras.gov.br
```

**Solução:** Usar LLM (GPT-4.1-nano) para extração estruturada dos campos de licitação a partir do texto bruto.

### Limitações

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| **Municipal apenas** | Sem dados federais/estaduais | Complementar ao PNCP |
| **~1.047 de 5.570 municípios** | Cobertura parcial (~19%) | Focar nos maiores/mais relevantes |
| **Texto não-estruturado** | Requer NLP/LLM para extrair dados | GPT-4.1-nano com structured output |
| **Qualidade OCR variável** | Erros de reconhecimento em PDFs scaneados | Fuzzy matching em keywords |
| **Max 10.000 resultados** | Cap do OpenSearch | Refinar queries com operadores |
| **Freshness variável** | Scraping não é real-time | Aceitar delay de 1-7 dias |

---

## Acceptance Criteria

### Track 1: Client Adapter (3h)

- [ ] **AC1:** Novo arquivo `backend/clients/querido_diario_client.py` com classe `QueridoDiarioClient`.
- [ ] **AC2:** Método `search_gazettes(query, territory_ids, since, until, size, offset)` consultando `GET /gazettes`.
- [ ] **AC3:** Querystring builder que converte keywords do setor em sintaxe OpenSearch: `"pregao eletronico" + (uniforme | fardamento | vestimenta)`.
- [ ] **AC4:** Rate limiter: max 1 req/s (60 req/min) com token bucket.
- [ ] **AC5:** Paginação automática: iterar pages até `total_gazettes` alcançado ou max 500 resultados.
- [ ] **AC6:** Para cada gazette com match, baixar `txt_url` (texto completo) para extração.

### Track 2: LLM Extraction Pipeline (4h)

- [ ] **AC7:** Função `extract_procurement_from_text(text: str) -> list[ExtractedProcurement]` usando GPT-4.1-nano com structured output (Pydantic).
- [ ] **AC8:** Schema `ExtractedProcurement` com campos: `modality`, `number`, `object_description`, `estimated_value`, `opening_date`, `agency_name`, `municipality`, `uf`, `source_url`.
- [ ] **AC9:** Prompt otimizado para extrair múltiplas licitações de um mesmo texto de diário (um PDF pode conter dezenas de avisos).
- [ ] **AC10:** Batch processing: processar até 10 gazettes por busca (evitar custo excessivo de LLM).
- [ ] **AC11:** Fallback sem LLM: regex-based extraction para campos óbvios (número do pregão, valor estimado com `R$`, data de abertura).
- [ ] **AC12:** Resultados extraídos são convertidos para formato `UnifiedProcurement` (compatível com pipeline existente).

### Track 3: Integration & Dedup (2h)

- [ ] **AC13:** Registrar `QUERIDO_DIARIO` como fonte em `source_config/sources.py` com prioridade 5 (mais baixa que PNCP/ComprasGov/Portal).
- [ ] **AC14:** Env var `ENABLE_SOURCE_QUERIDO_DIARIO=false` (default off — opt-in por ser experimental).
- [ ] **AC15:** Deduplicação com PNCP: match por número de edital + órgão + ano. Se já existe no PNCP, descartar o resultado do QD.
- [ ] **AC16:** Marcar resultados do QD com `source="Querido Diário"` e `confidence="extracted"` para distinguir de dados estruturados.
- [ ] **AC17:** Response inclui `extraction_confidence: float` (0-1) do LLM para cada campo extraído.

### Track 4: Tests (1h)

- [ ] **AC18:** Testes unitários: querystring builder, pagination, rate limiting.
- [ ] **AC19:** Testes unitários: LLM extraction com mock (texto de exemplo → structured output).
- [ ] **AC20:** Teste de regex fallback: extrai pregão nº, valor R$, data de abertura sem LLM.
- [ ] **AC21:** Integration test (marcado `@pytest.mark.integration`): busca real "licitacao uniforme" no QD API.

---

## Schema: `ExtractedProcurement`

```python
@dataclass
class ExtractedProcurement:
    modality: Optional[str]          # "Pregão Eletrônico", "Concorrência", etc.
    number: Optional[str]            # "023/2026"
    object_description: str          # Texto do objeto
    estimated_value: Optional[float] # R$ 450.000,00 → 450000.0
    opening_date: Optional[date]     # Data de abertura
    agency_name: Optional[str]       # Órgão/prefeitura
    municipality: str                # Extraído do territory_name
    uf: str                          # Extraído do state_code
    source_url: str                  # URL do PDF/TXT no QD
    gazette_date: date               # Data de publicação do diário
    extraction_confidence: float     # 0-1, média dos campos extraídos
    raw_excerpt: str                 # Trecho original do texto
```

## Querystring Builder — Exemplos por Setor

| Setor | Querystring Gerada |
|-------|--------------------|
| Vestuário e Uniformes | `(licitacao \| pregao \| edital) + (uniforme \| fardamento \| vestimenta \| jaleco \| camiseta)` |
| Alimentos e Merenda | `(licitacao \| pregao) + ("merenda escolar" \| "generos alimenticios" \| "kit alimentacao")` |
| Facilities | `(licitacao \| pregao) + ("servicos de limpeza" \| "manutencao predial" \| "conservacao" \| zeladoria)` |
| Software | `(licitacao \| pregao) + (software \| "sistema de informacao" \| "licenca" \| SaaS)` |

## Arquivos

| Arquivo | Tipo | Mudança |
|---------|------|---------|
| `backend/clients/querido_diario_client.py` | **NOVO** | Client HTTP + querystring builder |
| `backend/clients/qd_extraction.py` | **NOVO** | LLM extraction + regex fallback |
| `backend/source_config/sources.py` | Editar | Registrar QUERIDO_DIARIO |
| `backend/schemas.py` | Editar | ExtractedProcurement |
| `backend/tests/test_querido_diario.py` | **NOVO** | Unit + integration tests |
| `.env.example` | Editar | `ENABLE_SOURCE_QUERIDO_DIARIO=false` |

## Definition of Done

- [ ] Client funcional consultando QD API com querystring otimizada por setor
- [ ] LLM extraction converte texto bruto → dados estruturados
- [ ] Fallback regex funciona sem LLM (campos básicos)
- [ ] Integrado no multi-source consolidation com dedup
- [ ] Resultados marcados com `source="Querido Diário"` + confidence
- [ ] Testes passando
- [ ] Zero regressão
- [ ] Default OFF (opt-in experimental)

## Referências

- [API Docs (PT-BR)](https://docs.queridodiario.ok.org.br/pt-br/latest/utilizando/api-publica.html)
- [Swagger UI](https://api.queridodiario.ok.org.br/docs)
- [GitHub — API](https://github.com/okfn-brasil/querido-diario-api)
- [GitHub — Scrapers](https://github.com/okfn-brasil/querido-diario)
- [Python Wrapper](https://pypi.org/project/querido-diario-api-wrapper/)
- [Open Knowledge Brasil](https://ok.org.br/projetos/querido-diario/)
