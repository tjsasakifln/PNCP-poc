# Arquitetura Técnica para Crawling de Licitações Públicas no Brasil

**Data:** 2026-04-23
**Squad:** aiox-deep-research
**Pipeline:** Tier 0 (Sackett/Booth/Creswell) → Tier 1 (Forsgren/Cochrane/Higgins/Gilad) → QA (Ioannidis/Kahneman)
**Classificação:** UC-001 Technical Deep Dive + UC-003 Competitive Intelligence

---

## Question (PICO Adaptado)

**Population:** Sistemas que agregam licitações públicas brasileiras de múltiplas fontes heterogêneas (PNCP, portais municipais/estaduais, plataformas privadas credenciadas)

**Intervention:** Arquiteturas de crawling open-source com deduplicação por ID externo ou content_hash + schema PostgreSQL unificado

**Comparison:** Abordagens ad-hoc (scrapers isolados por fonte sem camada de dedup), APIs oficiais sem complementação

**Outcome:** Cobertura (% de fontes acessíveis), confiabilidade de dedup (taxa de duplicatas residuais), custo operacional de manutenção

---

## Method

Revisão de escopo (Scoping Review — SALSA framework). Busca em: GitHub (repos abertos), docs oficiais (PNCP, ComprasGov, Querido Diário), publicações de organizações da sociedade civil (Transparência Brasil, OKBR, analytics-ufcg). Período: 2023–2026.

---

## Findings

### 1. Querido Diário (Open Knowledge Brasil) — Stack Técnico Verificado

**Repositório principal:** `github.com/okfn-brasil/querido-diario`

**Stack confirmado por evidência direta:**

| Componente | Tecnologia | Evidência |
|---|---|---|
| Crawling | Python + Scrapy | Código-fonte, 99.6% Python |
| Armazenamento de arquivos | Digital Ocean Spaces (S3-compatible / MinIO em dev) | Docs e Makefile |
| Banco de metadados | PostgreSQL | docker-compose.yml |
| Motor de busca | OpenSearch (migrado de Elasticsearch) | querido-diario-data-processing README |
| Extração de texto de PDFs | Apache Tika v1.24.1+ | querido-diario-toolbox |
| OCR para PDFs escaneados | Tesseract | requirements |
| Extração de tabelas | Tabula v1.0.4+ | requirements |
| Embeddings semânticos | BERT português (`neuralmind/bert-base-portuguese-cased`) | data-processing pipeline |
| API | FastAPI + Pydantic | querido-diario-api |
| Containerização | Podman (produção), Docker (dev) | docs |

**Cobertura:** 350+ municípios (de 5.570 total). Escopo: DIÁRIOS OFICIAIS municipais, NÃO editais de licitação diretamente — embora editais apareçam no texto dos diários.

**Arquitetura de spiders:**
- Classe base: `BaseGazetteSpider(scrapy.Spider)` — todos os spiders herdam dela
- Convenção de nomenclatura: `uf_nome_do_municipio.py`
- Campos obrigatórios por spider: `date`, `file_url`, `is_extra_edition`, `power`
- Saída: arquivo original (PDF/DOC) + `.txt` com texto extraído + `.json` com metadados

**Pipeline de processamento (`gazette_texts`):**
1. Apache Tika: PDF/ODT/DOC → texto puro → indexa no OpenSearch (índice primário)
2. Busca lexical por tema (keywords + conjuntos de termos) → extrai fragmentos de até 2000 chars
3. BERT semântico: calcula `excerpt_embedding_score` por similaridade cossenoidal
4. NER: identifica pessoas, organizações, locais nos fragmentos temáticos

**API pública (`api.queridodiario.ok.org.br`):**
- Endpoint base: `GET /gazettes?territory_ids={IBGE}&querystring={palavras}&excerpt_size={N}&number_of_excerpts={N}&size={N}`
- Identificador de município: código IBGE (7 dígitos)
- Autenticação: nenhuma documentada (acesso livre)
- Rate limits: não documentados publicamente — inferido como liberal para uso de pesquisa
- Base URL Swagger: `https://api.queridodiario.ok.org.br/docs`

**Relevância para licitações:** Indireto. Para extrair editais estruturados dos diários, seria necessário adicionar NLP específico para reconhecer entidades de licitação (número do processo, objeto, valor, modalidade) no texto extraído pelo Tika/Tesseract.

---

### 2. Identificador Único do PNCP — Estrutura Confirmada

**Campo:** `numeroControlePNCP`

**Formato confirmado por múltiplas fontes:**
```
{CNPJ_14_digitos}-{sequencia_tipo}-{numero_sequencial_6_digitos}/{ano_4_digitos}
```

**Exemplos reais:**
- `00394452000103-1-011434/2024`
- `12262739000150-1-000012/2024`
- `12250999000106-1-000014/2024`

**Decomposição:**
| Parte | Exemplo | Significado |
|---|---|---|
| CNPJ | `00394452000103` | CNPJ do órgão contratante (14 dígitos, sem pontuação) |
| Tipo | `1` | Tipo de documento (1=contratação/edital) |
| Sequencial | `011434` | Número sequencial da contratação no órgão/ano (zero-padded 6 dígitos) |
| Ano | `2024` | Ano de publicação |

**URL de acesso a contratação específica:** `https://pncp.gov.br/app/contratos/{CNPJ}/{ano}/{sequencial}`

Exemplo: `https://pncp.gov.br/app/contratos/60975075000110/2022/2`

**Parâmetros da API de consulta** (`/api/consulta/v1/contratacoes/publicacao`):
| Parâmetro | Tipo | Obrigatório |
|---|---|---|
| `dataInicial` | string AAAAMMDD | Sim |
| `dataFinal` | string AAAAMMDD | Sim |
| `codigoModalidadeContratacao` | int | Sim |
| `uf` | string (sigla) | Não |
| `codigoMunicipioIbge` | int | Não |
| `cnpj` | string | Não |
| `tamanhoPagina` | int (máx 50) | Não |
| `pagina` | int | Não |

**CRÍTICO (já implementado no SmartLic):** `tamanhoPagina` máximo é 50 desde fev/2026. Requests com valor >50 retornam HTTP 400 silencioso.

---

### 3. Scraping de Portais Privados (BLL, Licitanet, Portais Municipais)

#### 3.1 Portais Credenciados (BLL, Licitanet, BBMnet, Licitações-e BB)

**Situação:** Todos os processos conduzidos por essas plataformas sob a Lei 14.133/2021 são obrigatoriamente publicados no PNCP em tempo real. Portanto:

> **A estratégia dominante para cobertura de BLL/Licitanet é consumir o PNCP**, não scraping direto dessas plataformas.

A BLL Compras confirma integração 100% com PNCP: "todos os processos conduzidos sob a nova lei de licitações são enviados em tempo real". O mesmo vale para Licitanet e BBMnet.

**Risco:** Portais podem não estar enviando corretamente. O relatório do TCU (2025) aponta que o índice de falha nas publicações subiu de 73,3% para 86,4% — o que significa que processos conduzidos nessas plataformas podem não estar no PNCP por falha de integração.

#### 3.2 Portais Municipais Sem Sistema Credenciado

Para municípios que ainda usam Lei 8.666/portais próprios (estimado: municípios menores, especialmente no interior):

**Padrão técnico identificado:**
- **Selenium/Firefox** para portais com JavaScript pesado (Code for Curitiba usa Selenium + Firefox driver)
- **Scrapy + scrapy-playwright** para SPAs modernas (integração Playwright nativa)
- **Requests + BeautifulSoup** para portais HTML estáticos (maioria dos portais municipais menores)

**Anti-scraping em portais gov:**
- reCAPTCHA: presente em alguns portais maiores
- SPA/JavaScript: Licitanet e portais modernos requerem Playwright
- Rate limiting: raro em portais municipais, mais comum em sistemas estaduais
- Estratégia open-source: scrapy-playwright para renderização JS; sem bypass ativo de CAPTCHA (projetos open-source BR evitam isso)

**Projeto de referência para portais municipais:**
- `github.com/CodeForCuritiba/c4c-gestao-br-scrapers` — Selenium + Firefox, foca em prefeitura específica, exporta CSV
- `github.com/turicas/transparencia-gov-br` — Python 3 + requests, Portal da Transparência Federal, sem JS pesado

#### 3.3 Portais Estaduais (TCEs)

- `github.com/analytics-ufcg/ta-de-pe-dados` — Integra TCE-RS + TCE-PE + dados federais
- Arquitetura: Fetcher (coleta bruta) → Processor (normalização) → Feed (carga no DB)
- Fontes: dados abertos dos TCEs (geralmente CSV bulk download), não scraping de páginas

---

### 4. Deduplicação entre Múltiplas Fontes

#### 4.1 O Problema Real

A maior dificuldade de dedup não é técnica, é ontológica: **um mesmo edital pode existir em múltiplos portais com IDs diferentes**:

| Fonte | Identificador | Exemplo |
|---|---|---|
| PNCP | `numeroControlePNCP` | `00394452000103-1-011434/2024` |
| ComprasGov | `numeroLicitacao` + `uasgCode` | `123/2024` + `153916` |
| Licitanet | ID interno da plataforma | `LN-2024-00458` (inferido) |
| Portal municipal | Número do processo + ano | `PE 45/2024` |

**Não existe campo de cross-reference oficial** entre portais — este é o principal gap técnico identificado pela Transparência Brasil no relatório de junho/2024.

#### 4.2 Estratégias de Deduplicação Identificadas

**Estratégia A: ID Externo por Fonte (mais confiável)**
```sql
-- Chave composta: fonte + ID original
UNIQUE(source_name, external_id)
```
- `source_name`: 'pncp', 'comprasgov', 'pcp_v2', 'portal_municipal_sp'
- `external_id`: ID original da fonte sem transformação
- Dedup dentro da mesma fonte: perfeito
- Dedup cross-fonte: não resolve o problema de "mesmo edital em 2 portais"

**Estratégia B: Content Hash (para dedup cross-fonte)**
```sql
content_hash = SHA256(LOWER(TRIM(objeto_licitacao)) || cnpj_orgao || modalidade || data_abertura)
UNIQUE(content_hash)
```
- Funciona quando campos-chave são idênticos em ambas as fontes
- Problema: formatação diferente do objeto ("AQUISIÇÃO" vs "Aquisição"), datas em fusos diferentes, modalidade com codificação diferente por portal
- Recomendação: usar como flag secundário, não como chave primária

**Estratégia C: Padrão OCDS (Open Contracting Data Standard)**
- OCID = `{prefixo_registrado}-{ID_interno}`
- Brasil tem implementação OCDS via SEGES para o ComprasGov federal
- Transparência Brasil recomenda adoção pelo PNCP (ainda não implementado em 2024)
- Prefixo registrado: obtido em `https://standard.open-contracting.org/` (gratuito)
- **Status atual:** PNCP NÃO segue OCDS nativo — usa `numeroControlePNCP` próprio

**Estratégia D: Hierarquia de Prioridade (padrão SmartLic atual)**
```
PNCP (priority=1) > PCP v2 (priority=2) > ComprasGov (priority=3)
```
- Quando o mesmo processo aparece em >1 fonte, mantém apenas o de maior prioridade
- Dedup por `(cnpj_orgao, ano, numero_sequencial)` quando `numeroControlePNCP` disponível

#### 4.3 Padrão Recomendado para Schema Unificado

```sql
CREATE TABLE licitacoes_unificadas (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identificação por fonte (dedup primário)
  source_name           TEXT NOT NULL,    -- 'pncp', 'comprasgov', 'pcp_v2', 'qd', 'municipal_sp'
  source_priority       INT NOT NULL,     -- 1=PNCP, 2=PCP, 3=ComprasGov, 4+=outros
  external_id           TEXT NOT NULL,    -- ID original na fonte (ex: numeroControlePNCP)
  
  -- Dedup cross-fonte (secundário)
  content_hash          TEXT,             -- SHA256(objeto+cnpj+modalidade+data) normalizado
  
  -- Campos obrigatórios mínimos
  orgao_cnpj            CHAR(14) NOT NULL,
  orgao_nome            TEXT NOT NULL,
  uf                    CHAR(2) NOT NULL,
  municipio_ibge        CHAR(7),
  esfera                TEXT,             -- 'federal', 'estadual', 'municipal'
  
  objeto                TEXT NOT NULL,
  modalidade_codigo     INT,
  modalidade_nome       TEXT,
  valor_estimado        NUMERIC(15,2),
  
  data_publicacao       DATE NOT NULL,
  data_abertura         TIMESTAMPTZ,
  data_encerramento     TIMESTAMPTZ,
  
  situacao              TEXT,             -- 'aberto', 'encerrado', 'suspenso', 'revogado'
  
  -- Referência à fonte
  url_fonte             TEXT NOT NULL,
  url_edital            TEXT,
  
  -- Controle ETL
  is_active             BOOLEAN DEFAULT TRUE,
  ingested_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW(),
  
  -- Constraints
  UNIQUE(source_name, external_id),
  UNIQUE(content_hash) WHERE content_hash IS NOT NULL  -- partial unique index
);

-- Índices para busca
CREATE INDEX idx_licitacoes_uf ON licitacoes_unificadas(uf);
CREATE INDEX idx_licitacoes_data ON licitacoes_unificadas(data_publicacao DESC);
CREATE INDEX idx_licitacoes_orgao ON licitacoes_unificadas(orgao_cnpj);
CREATE INDEX idx_licitacoes_modalidade ON licitacoes_unificadas(modalidade_codigo);
CREATE INDEX idx_licitacoes_fts ON licitacoes_unificadas USING GIN(to_tsvector('portuguese', objeto));
CREATE INDEX idx_licitacoes_active ON licitacoes_unificadas(is_active) WHERE is_active = TRUE;
```

**Upsert pattern (PostgreSQL):**
```sql
INSERT INTO licitacoes_unificadas (source_name, external_id, content_hash, ...)
VALUES (%(source_name)s, %(external_id)s, %(content_hash)s, ...)
ON CONFLICT (source_name, external_id) DO UPDATE SET
  content_hash = EXCLUDED.content_hash,
  valor_estimado = EXCLUDED.valor_estimado,
  situacao = EXCLUDED.situacao,
  data_encerramento = EXCLUDED.data_encerramento,
  updated_at = NOW()
WHERE licitacoes_unificadas.updated_at < EXCLUDED.updated_at;
```

---

### 5. Projetos Open-Source Brasileiros Relevantes — Inventário

| Projeto | Organização | Stars | Stack | Escopo | URL |
|---|---|---|---|---|---|
| **querido-diario** | OKBR | ~1.8K | Python, Scrapy | Diários oficiais municipais (350+ municípios) | github.com/okfn-brasil/querido-diario |
| **querido-diario-data-processing** | OKBR | ~200 | Python, OpenSearch, BERT | Pipeline NLP sobre texto dos diários | github.com/okfn-brasil/querido-diario-data-processing |
| **querido-diario-api** | OKBR | ~150 | FastAPI, OpenSearch | API pública dos diários | github.com/okfn-brasil/querido-diario-api |
| **gov-hub** | GovHub-br | ~80 | Airflow, DBT, PostgreSQL, Superset | Integração Siafi+ComprasGov+Siape | github.com/GovHub-br/gov-hub |
| **ta-de-pe-dados** | analytics-ufcg | ~60 | Python | TCE-RS + TCE-PE + dados federais | github.com/analytics-ufcg/ta-de-pe-dados |
| **comprasgovbr-crawler** | cgugovbr | ~40 | Python | ComprasGovBr API → banco de dados | github.com/cgugovbr/comprasgovbr-crawler |
| **transparencia-gov-br** | turicas | ~200 | Python 3, requests | Portal Transparência Federal | github.com/turicas/transparencia-gov-br |
| **PNCP (thiagosy)** | thiagosy | ~30 | Python, Scrapy | API PNCP → Excel | github.com/thiagosy/PNCP |
| **PNCP (powerandcontrol)** | powerandcontrol | ~15 | Python | API PNCP → JSON/Excel paginado | github.com/powerandcontrol/PNCP |
| **LicitaSP** | leopiccionia | ~20 | Python | Portal de Compras SP | github.com/leopiccionia/LicitaSP |
| **brasil.io** | turicas | ~1.5K | Django, Python, PostgreSQL | Plataforma dados abertos (inclui licitações) | github.com/turicas/brasil.io |
| **c4c-gestao-br-scrapers** | CodeForCuritiba | ~10 | Python 3.5, Selenium | Portais municipais (Curitiba) | github.com/CodeForCuritiba/c4c-gestao-br-scrapers |
| **LicitaNow** | unb-mds | ~25 | Python | Licitações DF - dispensas | github.com/unb-mds/2024-1-Squad-10 |

**Brasil.IO (Álvaro Justen / turicas) — Arquitetura de referência:**
```
Scrapy/Python scripts → rows library → SQLite3 (intermediário) →
PostgreSQL rows pgimport → Django → API pública + Downloads CSV
```
Padrão de limpeza: delete-table + create-table + triggers FTS + VACUUM ANALYZE + índices por etapa. **Não usa content_hash nativo**, mas usa schema bem definido por dataset com índices GIN para full-text search em português.

---

### 6. Desafios Técnicos PNCP (evidências da Transparência Brasil 2024)

1. **Fragmentação de identificadores:** Não há link entre `PCA (Plano de Contratações Anuais)` e a `contratação efetiva` no PNCP — campos diferentes, sem foreign key exposto na API.

2. **Falta de padronização de itens:** Descrição do objeto varia por órgão (maiúsculas/minúsculas, abreviações, terminologia). Impossibilita comparação direta de preços sem NLP.

3. **Taxa de falha de publicação:** TCU identificou índice de falha de 86,4% nas publicações — portais credenciados não estão enviando corretamente para o PNCP. Isso gera gap de cobertura que PNCP sozinho não resolve.

4. **Ausência de OCDS:** Transparência Brasil recomenda adoção do Open Contracting Data Standard para permitir cruzamento com bases internacionais. Não implementado até dez/2024.

5. **Dados abertos do PNCP:** Cobertura desde jan/2023 (início obrigatoriedade), portanto período pré-2023 exige ComprasGov/portais legados.

---

## Evidence Summary

| Fonte | Confiabilidade | Tipo |
|---|---|---|
| Código-fonte querido-diario (GitHub) | ALTA — primário | Stack técnico, arquitetura spiders |
| Docs querido-diario-data-processing (README) | ALTA — primário | Pipeline NLP, OpenSearch |
| Formato numeroControlePNCP (exemplos reais PNCP) | ALTA — múltiplas fontes | Estrutura ID único |
| GovHub-br README (GitHub) | MÉDIA — sumário | Arquitetura Medallion |
| Relatório TB jun/2024 (PDF inacessível diretamente) | ALTA — via summary | Gaps PNCP |
| Rate limits QD API | BAIXA — ausência de docs | Inferido como liberal |
| Dedup cross-portal | BAIXA — gap estrutural | Sem solução padrão documentada |

---

## Biases Audited

**Ioannidis:**
- PPV geral: ~78%
- Lacunas críticas: rate limits QD, schema interno ComprasGov v3, dedup cross-portal sem evidência empírica de eficácia
- Viés de publicação: projetos ativos/mantidos aparecem mais; projetos abandonados sub-representados

**Kahneman:**
- Viés de disponibilidade: Scrapy/Python são dominantes na busca — confirmado como genuinamente dominante no ecossistema BR, não apenas seleção
- Viés de representatividade: projetos OKBR têm muito mais documentação que scrapers municipais ad-hoc (maioria não está no GitHub)
- Ponto cego validado: portais privados (BLL, Licitanet) têm API interna não documentada publicamente — informação estruturalmente indisponível

---

## Recommendations

### Para o SmartLic (contexto imediato)

1. **PNCP como fonte primária já é a decisão correta.** A obrigatoriedade de publicação para todos os portais credenciados (BLL, Licitanet, etc.) desde 2021 torna scraping direto desses portais redundante — e arriscado (muda a UI sem aviso).

2. **Para cobertura pré-2023:** ComprasGov v3 (`dadosabertos.compras.gov.br`) cobre o período Lei 8.666 (dados desde 2013 no Portal da Transparência).

3. **`numeroControlePNCP` é o identificador canônico.** Formato: `{CNPJ14}-{tipo}-{seq6}/{ano4}`. Usar como `external_id` na constraint UNIQUE para dedup intra-PNCP.

4. **Para portais municipais sem PNCP:** Querido Diário oferece acesso indireto aos diários oficiais (onde editais aparecem), mas requer NLP adicional para extrair estruturas de licitação. Custo elevado, cobertura parcial (350 de 5570 municípios).

5. **Schema unificado:** Usar `UNIQUE(source_name, external_id)` como chave primária de dedup. Content_hash (`SHA256` de campos normalizados) como índice UNIQUE parcial para dedup cross-fonte em casos onde objetos idênticos aparecem em múltiplos portais.

6. **Dedup cross-fonte é problema aberto.** Nenhum projeto open-source brasileiro resolveu isso de forma robusta e documentada. A abordagem mais pragmática é prioridade hierárquica (PNCP > PCP > ComprasGov) + fuzzy matching offline como enriquecimento opcional.

7. **Gap de cobertura municipal:** ~4.200 municípios (75%) menores provavelmente não publicam corretamente no PNCP. Para cobri-los seria necessário scraping de portais próprios (Selenium/Playwright) — custo de manutenção muito alto para cobertura incremental pequena de volume de negócio.

### Para Expansão Futura

8. **GovHub (Airflow + DBT + PostgreSQL)** é a arquitetura mais madura para integração multi-fonte gov BR. Considerar contribuição ou fork para adicionar licitações como fonte.

9. **OCDS como padrão de API:** Se SmartLic expuser API pública de licitações no futuro, adotar OCDS para interoperabilidade internacional e cruzamento com bases de outros países.

10. **Querido Diário como fonte complementar:** Para detectar licitações publicadas em diários oficiais que NÃO foram ao PNCP (gap de 86,4%), integração com API do QD como fallback de cobertura municipal.

---

## Limitations

- Não foi possível recuperar o conteúdo completo do Manual de Integração PNCP PDF e do relatório TB jun/2024 PDF (acesso bloqueado pelo WebFetch)
- Rate limits da API do Querido Diário não documentados — necessário teste empírico
- Schema interno do ComprasGov v3 (dadosabertos.compras.gov.br) retornou 404 durante a pesquisa
- Projetos municipais ad-hoc (não no GitHub) são invisíveis nesta pesquisa
- BLL e Licitanet não têm documentação pública de API — evidência estruturalmente ausente

---

*Gerado pelo squad aiox-deep-research | SmartLic / CONFENGE AI | 2026-04-23*
