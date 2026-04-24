# EXT-002: Playwright Extractor Engine — Engine Genérico de URL

**Status:** Ready
**Origem:** EPIC-EXT-001 — Fontes Externas de Licitações
**Prioridade:** P0 — Habilitador (crawlers EXT-003/004/005 dependem desta)
**Complexidade:** M (Medium) — ~10h
**Sprint:** EXT-sprint-01
**Owner:** @dev + @architect
**Tipo:** Backend / Infrastructure

---

## Problema

Os crawlers de fontes externas (Querido Diário, BNC, IPM) precisam visitar URLs de editais para extrair dados estruturados. Portais governamentais têm formatos heterogêneos: alguns são HTML simples, outros são SPAs (Vue.js/React), outros apenas expõem PDFs.

Sem um engine centralizado:
- Cada crawler teria que reimplementar rate limiting, circuit breaker, retry, e PDF parsing
- LLM extraction seria duplicada em cada crawler
- Playwright browser pool seria instanciado múltiplas vezes, consumindo memória no worker Railway

Esta story cria o engine reutilizável que todos os crawlers consomem.

---

## Critérios de Aceite

- [ ] **AC1:** `PlaywrightExtractor.extract(url: str) → ExternalBidRaw | None` funciona para URLs HTML simples
- [ ] **AC2:** Para URLs de PDF (`.pdf` no path ou `Content-Type: application/pdf`), extrai texto com `pypdf` e passa para LLM
- [ ] **AC3:** LLM fallback (GPT-4.1-nano) ativado quando BeautifulSoup não encontra campos mínimos — prompt retorna `ExternalBidRaw` ou `null` em JSON estruturado
- [ ] **AC4:** Rate limiting enforced: mínimo 2s entre requests para o mesmo domínio (via `asyncio.sleep` + dict de timestamps por domínio)
- [ ] **AC5:** Circuit breaker por domínio: 5 falhas consecutivas → domínio marcado como `circuit_open` por 1h (estado em Redis)
- [ ] **AC6:** Retry com exponential backoff: 3 tentativas, delays 1s → 2s → 4s
- [ ] **AC7:** `ExternalBidRaw` Pydantic model com campos obrigatórios (`objeto`, `uf`, `data_publicacao`, `url_fonte`) e demais opcionais
- [ ] **AC8:** Métrica `smartlic_external_extractor_success_total{source}` incrementada em sucesso
- [ ] **AC9:** Métrica `smartlic_external_extractor_errors_total{source,reason}` incrementada em falha (timeout, circuit_open, parse_failed, llm_failed)
- [ ] **AC10:** Chromium headless roda com `args=["--no-sandbox", "--disable-gpu"]` (compatível com Railway/Docker)
- [ ] **AC11:** Pool de browsers limitado a `max_concurrent=3` via `asyncio.Semaphore`
- [ ] **AC12:** `pytest tests/ingestion/external/test_playwright_extractor.py` passa com mocks de Playwright e httpx

### Anti-requisitos

- Não fazer login em portais autenticados — apenas páginas públicas
- Não implementar CAPTCHA solving — se CAPTCHA detectado, registrar erro `captcha_detected` e pular URL
- Não armazenar screenshots ou HTML completo — apenas campos extraídos
- Não usar `time.sleep()` síncrono — sempre `asyncio.sleep()`

---

## Interface Pública

```python
# backend/ingestion/external/playwright_extractor.py

from pydantic import BaseModel
from datetime import date
from typing import Optional

class ExternalBidRaw(BaseModel):
    # Obrigatórios
    objeto: str
    uf: str  # 2 chars
    data_publicacao: date
    url_fonte: str
    # Opcionais
    orgao_cnpj: Optional[str] = None
    orgao_nome: Optional[str] = None
    municipio_ibge: Optional[str] = None
    esfera: str = "municipal"
    modalidade_codigo: Optional[int] = None
    valor_estimado: Optional[float] = None
    data_abertura: Optional[str] = None  # ISO datetime string
    situacao: Optional[str] = None
    external_id: Optional[str] = None  # ID original da fonte
    raw_html_hash: Optional[str] = None

class PlaywrightExtractor:
    async def extract(self, url: str, source_name: str) -> ExternalBidRaw | None:
        """Visita URL e retorna campos estruturados ou None se falhar."""
        ...

    async def extract_batch(self, urls: list[str], source_name: str) -> list[ExternalBidRaw]:
        """Extrai múltiplas URLs com semaphore (max_concurrent=3)."""
        ...
```

---

## LLM Extraction Prompt

```python
EXTRACTION_PROMPT = """
Você é um extrator de dados de licitações públicas brasileiras.
Analise o HTML/texto abaixo e extraia os campos da licitação.

Retorne JSON com estes campos (omita os que não encontrar):
{
  "objeto": "descrição do objeto da licitação",
  "orgao_nome": "nome do órgão",
  "orgao_cnpj": "CNPJ apenas números 14 dígitos",
  "uf": "sigla do estado 2 letras",
  "municipio_ibge": "código IBGE 7 dígitos se disponível",
  "modalidade_codigo": 8,  // 4=Concorrência, 5=Concurso, 6=Leilão, 7=Diálogo Competitivo, 8=Pregão, 12=Dispensa
  "valor_estimado": 150000.00,
  "data_publicacao": "YYYY-MM-DD",
  "data_abertura": "YYYY-MM-DDTHH:MM:SS",
  "situacao": "aberto|encerrado|cancelado"
}

Se não encontrar dados suficientes para preencher 'objeto', 'uf' e 'data_publicacao', retorne null.

HTML/texto:
{content}
"""
```

---

## Tarefas

- [ ] Criar `backend/ingestion/external/__init__.py`
- [ ] Criar `backend/ingestion/external/playwright_extractor.py` com `PlaywrightExtractor` e `ExternalBidRaw`
- [ ] Implementar extração HTML via BeautifulSoup (campos comuns: título, valor, datas, CNPJ)
- [ ] Implementar PDF detection + pypdf text extraction
- [ ] Implementar LLM fallback com prompt EXTRACTION_PROMPT
- [ ] Implementar rate limiter por domínio (dict + asyncio.sleep)
- [ ] Implementar circuit breaker com estado em Redis (key: `ext_circuit:{domain}`)
- [ ] Implementar retry com exponential backoff
- [ ] Registrar métricas Prometheus em `backend/metrics.py`
- [ ] Adicionar `playwright` e `pypdf` a `backend/requirements.txt`
- [ ] Criar `backend/tests/ingestion/external/test_playwright_extractor.py`

---

## Referência de Implementação

- Rate limiting pattern: ver `backend/ingestion/crawler.py` (delay entre batches)
- Circuit breaker Redis pattern: ver `backend/redis_client.py` + padrão de circuit breaker do `pncp_client.py`
- LLM integration: ver `backend/llm_arbiter.py` — `_get_client()` + `AsyncOpenAI`
- Métricas Prometheus: ver `backend/metrics.py` para padrão de `Counter` com labels
- Playwright async: usar `playwright.async_api.async_playwright`

---

## Riscos

- **R1 (Alto):** Playwright + Chromium aumenta tamanho da imagem Docker (~400MB). Avaliar usar imagem `mcr.microsoft.com/playwright/python` ou instalar via `playwright install chromium` no Dockerfile.
- **R2 (Médio):** Worker Railway tem memory limit. Pool limitado a 3 browsers concorrentes mitiga, mas monitorar.
- **R3 (Baixo):** `pypdf` pode falhar em PDFs escaneados (imagens). Nesses casos, registrar erro `pdf_scanned` e pular — não tentar OCR agora.

---

## Dependências

- **EXT-001** (schema `external_bids`) — para ter `ExternalBidRaw` schema definido
- `playwright` Python package (adicionar a `requirements.txt`)
- `pypdf` Python package (adicionar a `requirements.txt`)
- Redis disponível (já presente no stack)
- OpenAI API key (já configurado em `config.py`)

---

## Arquivos Relevantes

| Arquivo | Ação |
|---------|------|
| `backend/ingestion/external/__init__.py` | Criar |
| `backend/ingestion/external/playwright_extractor.py` | Criar |
| `backend/metrics.py` | Atualizar (adicionar métricas EXT) |
| `backend/requirements.txt` | Atualizar (playwright, pypdf) |
| `backend/Dockerfile` | Atualizar (instalar Chromium) |
| `backend/tests/ingestion/external/test_playwright_extractor.py` | Criar |

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — EPIC-EXT-001 |
| 2026-04-23 | @po | Validação 10-pontos: **9/10 → GO** — R1 (Playwright imagem Docker) requer atenção no Dockerfile; não bloqueia. Status: Draft → Ready |
