# Fontes Externas de Licitações — Pesquisa Consolidada

**Data:** 2026-04-23  
**Squad:** aiox-deep-research (pipeline 3-tier executado)  
**Questão:** Quais fontes de licitações existem fora do PNCP, e qual arquitetura viabiliza sua integração no SmartLic com deduplicação no Supabase?

---

## Question (PICO)

- **P** (Population): Editais de licitação publicados por órgãos municipais/estaduais que não chegam ao PNCP
- **I** (Intervention): Crawler 2-tier (descoberta de URLs + extração Playwright/LLM) + ingestão Supabase deduped
- **C** (Comparison): Cobertura atual: PNCP + PCP v2 + ComprasGov v3
- **O** (Outcome): Aumento de cobertura de editais capturados, especialmente municípios <20k hab e fontes com falha de publicação PNCP

---

## Gap Central: 86,4% de Falha no PNCP (TCU 2025)

**Achado crítico (Higgins/OSINT):** O TCU (2025) verificou que o índice de falha nas publicações ao PNCP pelos portais credenciados subiu de 73,3% para **86,4%**. Portais como BLL, Licitanet, BNC são credenciados mas não sincronizam todos os atos. Além disso, municípios com até 20.000 habitantes têm prazo legal até **abril de 2027** para aderir ao PNCP (Lei 14.133, Art. 176) — estimativa de ~3.000 municípios fora do PNCP até lá.

---

## Fontes Identificadas

### Tier A — APIs Públicas (REST, sem auth)

| Fonte | URL | Dados | Cobertura | Esforço |
|---|---|---|---|---|
| **Querido Diário** | `api.queridodiario.ok.org.br/gazettes` | Texto não estruturado (trechos de diário) | ~350 municípios | Médio (NLP para extrair licitações) |
| **ComprasGov histórico** | `compras.dados.gov.br/licitacoes/v1/licitacoes.json` | Estruturado (JSON) | Federal (pre-2023 gap) | Baixo (API estável) |
| **API Licitações SP** | `apilib.prefeitura.sp.gov.br` | Estruturado | São Paulo capital | Baixo (API key) |
| **API Licitações AL** | `transparencia.al.gov.br/portal/api/licitacoes` | Estruturado | Alagoas | Baixo |

### Tier B — Portais com HTML Estruturado (Scraping)

| Fonte | URL Base | Cobertura | Tecnologia | Esforço |
|---|---|---|---|---|
| **BNC** | `bnccompras.com/Process/ProcessSearchPublic` | 23 estados, 1.500+ órgãos | HTML estático | Baixo-Médio |
| **BBMnet** | `bbmnet.com.br` | SP, RS, PR, MG, RJ | HTML estático | Médio |
| **DOM/SC** | `diariomunicipal.sc.gov.br` | 550+ entidades SC | HTML + PDF | Médio |
| **IPM/Atende.Net** | `{municipio}.atende.net/cidadao/noticia/categoria/licitacoes` | 850+ municípios (RS, SC, PR, MG) | Vue.js (Playwright) | Médio |
| **Betha Sistemas** | Varia por município | 800 municípios, 22 estados | Desconhecido (investigação pendente) | Alto |

### Tier C — Texto de Diário Oficial (PDF/HTML, extração pesada)

| Fonte | Canal | NLP Necessário | Cobertura |
|---|---|---|---|
| **DOU Seção 3** | `in.gov.br/acesso-a-informacao/dados-abertos` (XML bulk) | Sim (regex + LLM) | Federal |
| **Querido Diário** | API REST | Sim (LLM extraction) | ~350 municípios |
| **DOM estaduais** | Scraping HTML | Sim | Varia por estado |

---

## Arquitetura Recomendada (2-Tier)

```
TIER A — Descoberta de URLs
├── Querido Diário API → trechos de texto com menção a licitações
├── Portal scraping (BNC, IPM, DOM/SC) → lista de URLs de editais
└── Web search API (EXA/Google) → URLs de editais em prefeituras

         ↓ fila de URLs descobertas (Redis ou Supabase)

TIER B — Extração Estruturada
├── Playwright visita cada URL descoberta
├── HTML parser (BeautifulSoup) para campos padrão
├── LLM (GPT-4.1-nano) para páginas não estruturadas / PDFs
└── Pydantic validation → rejeita registros incompletos

         ↓ external_bids (Supabase)

TIER C — Storage + Dedup
├── UNIQUE(source_name, external_id) → dedup intra-fonte
├── content_hash = SHA256(objeto + cnpj_orgao + data_publicacao) → dedup cross-fonte
└── Soft-delete: is_active=false após prazo
```

**Schema proposto (`external_bids`):**
```sql
CREATE TABLE external_bids (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name      TEXT NOT NULL,        -- 'querido_diario', 'bnc', 'ipm_atende', 'dom_sc'
  source_priority  INT NOT NULL,         -- 4=querido_diario, 5=bnc, 6=ipm, etc.
  external_id      TEXT NOT NULL,        -- ID original sem transformação
  content_hash     TEXT,                 -- SHA256 normalizado (dedup cross-fonte)
  orgao_cnpj       CHAR(14),
  orgao_nome       TEXT NOT NULL,
  uf               CHAR(2) NOT NULL,
  municipio_ibge   CHAR(7),
  esfera           TEXT DEFAULT 'municipal',
  objeto           TEXT NOT NULL,
  modalidade_codigo INT,
  valor_estimado   NUMERIC(15,2),
  data_publicacao  DATE NOT NULL,
  data_abertura    TIMESTAMPTZ,
  situacao         TEXT,
  url_fonte        TEXT NOT NULL,        -- URL visitada pelo Playwright
  raw_html_hash    TEXT,                 -- fingerprint para detectar mudança de conteúdo
  is_active        BOOLEAN DEFAULT TRUE,
  ingested_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(source_name, external_id),
  UNIQUE(content_hash) WHERE content_hash IS NOT NULL
);
CREATE INDEX ON external_bids USING GIN(to_tsvector('portuguese', objeto));
CREATE INDEX ON external_bids(uf, data_publicacao DESC);
CREATE INDEX ON external_bids(is_active, data_publicacao DESC);
```

---

## Identificador Único PNCP (referência para dedup cross-source)

```
{CNPJ_14_dígitos}-{tipo}-{sequencial_6_zeros}/{ano_4_dígitos}
Ex: 00394452000103-1-011434/2024
```

Dedup canônico: `UNIQUE(source_name, external_id)` para intra-fonte. Para cross-fonte: `SHA256(normalize(objeto) + cnpj_orgao + date_trunc('day', data_publicacao))`.

---

## Priorização por ROI

| Prioridade | Source | Razão |
|---|---|---|
| **P1** | Querido Diário + LLM | API pública, cobre municípios sem PNCP, wrapper Python oficial |
| **P1** | BNC | Portal público estruturado, 23 estados, sem CAPTCHA confirmado |
| **P2** | IPM/Atende.Net | 850+ municípios com padrão URL identificado (`*.atende.net`) |
| **P2** | ComprasGov histórico API | Pre-2023 gap, API estável, dados estruturados |
| **P3** | DOM/SC | 550 entidades SC, piloto de diário estadual |
| **P3** | Betha Sistemas | Maior cobertura (22 estados) mas URL patterns desconhecidos |

---

## Riscos Críticos (Ioannidis QA)

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Querido Diário cobre apenas ~350/5.570 municípios | Alta | Médio | Complementar com outras fontes; priorizar municípios de interesse do cliente |
| IPM/Atende.Net Vue.js muda sem aviso | Alta | Alto | Versionamento de scraper + testes semanais de estrutura |
| BNC/BBMnet introduz CAPTCHA | Média | Alto | Playwright stealth mode; fallback para Querido Diário |
| ToS / robots.txt de fontes privadas | Média | Crítico | Verificar ANTES do deploy; User-Agent identificador obrigatório |
| Duplicatas cross-fonte (mesmo edital em 2 fontes) | Alta | Médio | content_hash + prioridade hierárquica (source_priority) |
| LLM extraction: campos ausentes em texto livre | Alta | Médio | Pydantic validation rigorosa; PENDING_REVIEW para registros incompletos |

---

## Biases Auditados (Kahneman)

- **Survivorship bias**: Querido Diário só cobre municípios que digitalizaram e têm scraper ativo → não representa o universo total. Mitigation: combinar com IPM/Atende.Net para RS/SC/PR.
- **Recency bias**: Priorizar Querido Diário pode sobre-representar municípios do sul/sudeste que adotaram tecnologia mais cedo. Mitigation: medir cobertura por UF antes de produção.
- **Sunk cost bias**: A pesquisa de 2025-02-09 já mapeou IPM/Betha sem PoC implementado. Não presumir que a arquitetura está validada só porque foi pesquisada antes.
- **Complexity bias**: Selenium/Playwright parece mais poderoso, mas para portais com APIs REST públicas (Querido Diário, BNC via HTML simples) é overhead desnecessário. Usar httpx+BS4 onde possível; Playwright apenas para SPAs.

---

## Fontes de Evidência

- [Querido Diário API docs](https://api.queridodiario.ok.org.br/docs)
- [okfn-brasil/querido-diario](https://github.com/okfn-brasil/querido-diario)
- [TCU — Qualidade PNCP 2025](https://www.transparencia.org.br/downloads/publicacoes/qualidade_dados_portal_nacional_de_contratacoes_publicas.pdf)
- [Lei 14.133 Art. 176 — prazo municípios](https://www.gov.br/pncp/pt-br/integre-se-ao-pncp/perguntas-e-respostas/qual-o-prazo-para-os)
- [BNC Portal de Busca Pública](https://bnccompras.com/Process/ProcessSearchPublic?param1=0)
- [DOM/SC](https://diariomunicipal.sc.gov.br/)
- [IPM Sistemas eLicita](https://www.ipm.com.br/elicita-conheca-o-lancamento-da-ipm-para-automatizar-licitacoes-publicas/)
- [GovHub — Medallion Architecture gov BR](https://github.com/GovHub-br/gov-hub)
- Pesquisa interna: `docs/research/novas-fontes.md` (2025-02-09)
- Pesquisa interna: `docs/research/2026-04-23-crawling-licitacoes-arquitetura.md`

---

## Recomendações

1. **Iniciar pelo Querido Diário** — menor risco técnico, API pública estável, LLM já disponível no stack
2. **BNC como segundo** — portal estruturado sem API, HTML previsível, sem CAPTCHA confirmado
3. **Schema `external_bids` primeiro** — fundação necessária para todas as fontes
4. **Engine Playwright reutilizável** — abstração que todas as fontes usam para visitar URLs
5. **Verificar ToS/robots.txt de BNC/IPM antes de produção** — risco jurídico classificado como CRÍTICO

---

*Pipeline executado: Sackett → Booth → Creswell (Tier 0) | Higgins + Cochrane + Gilad (Tier 1) | Ioannidis + Kahneman (QA)*  
*Fontes externas verificadas via WebSearch (2026-04-23)*
