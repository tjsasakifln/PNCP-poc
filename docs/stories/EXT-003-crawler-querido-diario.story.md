# EXT-003: Crawler Querido Diário

**Status:** Ready
**Origem:** EPIC-EXT-001 — Fontes Externas de Licitações
**Prioridade:** P1 — Alta (maior cobertura municipal com menor risco técnico)
**Complexidade:** M (Medium) — ~8h
**Sprint:** EXT-sprint-02
**Owner:** @dev
**Tipo:** Backend / Ingestion

---

## Problema

O Querido Diário (Open Knowledge Brasil) disponibiliza API REST pública que indexa diários oficiais de ~350 municípios brasileiros. Esses municípios publicam editais de licitação no diário oficial que nunca chegam ao PNCP (prazo legal até 2027 para municípios <20k hab).

A API retorna trechos de texto não estruturado onde o termo buscado aparece. Para extrair os campos estruturados da licitação (objeto, valor, órgão, datas), precisamos usar o `PlaywrightExtractor` (EXT-002) na URL do documento ou, como fallback, enviar o excerpt diretamente ao LLM.

**API pública:** `https://api.queridodiario.ok.org.br/gazettes`
- Sem autenticação
- Parâmetros: `territory_ids`, `querystring`, `since`, `until`, `size`, `offset`

---

## Critérios de Aceite

- [ ] **AC1:** `QueridoDiarioCrawler.crawl_full()` busca últimos 10 dias para todos os municípios configurados
- [ ] **AC2:** `QueridoDiarioCrawler.crawl_incremental()` busca últimos 3 dias
- [ ] **AC3:** Para cada excerpt retornado, tenta extração via `PlaywrightExtractor.extract(gazette_url)`
- [ ] **AC4:** Fallback ativo: se PlaywrightExtractor retornar `None`, passa `excerpt_text` diretamente ao LLM para extração
- [ ] **AC5:** Keywords usadas na querystring vêm de `backend/sectors_data.yaml` — campo `keywords` dos 15 setores, concatenados com OR lógico (querystring separada por espaços ou `|`)
- [ ] **AC6:** Arquivo `backend/ingestion/external/qd_territory_ids.yaml` com mapeamento UF → lista de códigos IBGE cobertos pelo Querido Diário (iniciar com as ~350 cobertos)
- [ ] **AC7:** `source_name='querido_diario'`, `source_priority=4` nos registros gerados
- [ ] **AC8:** ARQ cron job `querido_diario_full_job` agendado para 3am BRT diário
- [ ] **AC9:** ARQ cron job `querido_diario_incremental_job` agendado para 9am, 3pm, 9pm BRT
- [ ] **AC10:** Métricas `smartlic_querido_diario_gazettes_fetched_total` e `smartlic_querido_diario_bids_extracted_total` incrementadas corretamente
- [ ] **AC11:** `pytest tests/ingestion/external/test_querido_diario_crawler.py` passa com mock da API

### Anti-requisitos

- Não buscar municipios fora do `qd_territory_ids.yaml` — sem discovery dinâmico por ora
- Não armazenar os excerpts de texto completo — apenas os campos extraídos
- Não bloquear o job se um município falhar — continue para o próximo, logue o erro

---

## Tarefas

- [ ] Criar `backend/ingestion/external/querido_diario_crawler.py`
- [ ] Implementar `QueridoDiarioCrawler` com `crawl_full()` e `crawl_incremental()`
- [ ] Criar `backend/ingestion/external/qd_territory_ids.yaml` com lista inicial de ~350 municípios cobertos
- [ ] Integrar com `PlaywrightExtractor` (EXT-002) para visitar URL do documento
- [ ] Implementar fallback LLM direto no excerpt quando PlaywrightExtractor falhar
- [ ] Registrar ARQ jobs em `backend/job_queue.py` (ou `cron_jobs.py`)
- [ ] Adicionar métricas Prometheus
- [ ] Criar `backend/tests/ingestion/external/test_querido_diario_crawler.py`

---

## Referência de Implementação

```python
# Exemplo de chamada à API do Querido Diário
async def fetch_gazettes(
    territory_id: str,
    keywords: list[str],
    since: date,
    until: date,
) -> list[dict]:
    url = "https://api.queridodiario.ok.org.br/gazettes"
    params = {
        "territory_ids": territory_id,
        "querystring": " ".join(keywords[:10]),  # top 10 keywords do setor
        "since": since.isoformat(),
        "until": until.isoformat(),
        "excerpt_size": 500,
        "number_of_excerpts": 3,
        "size": 50,
        "offset": 0,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("gazettes", [])
```

- Pattern de ARQ cron job: ver `backend/cron_jobs.py` e `backend/ingestion/scheduler.py`
- Pattern de keywords: ver `backend/sectors_data.yaml` — campo `keywords` por setor
- `ExternalBidLoader` (EXT-006): passar resultados para loader após extração

---

## Riscos

- **R1 (Médio):** Querido Diário pode ter rate limiting não documentado. Iniciar com delay de 1s entre territory_ids; monitorar HTTP 429.
- **R2 (Alto):** Excerpt de texto do diário oficial é genérico — pode conter menção a licitação em contexto de resultado, não de abertura. LLM pode extrair dados incorretos. Mitigação: validar `data_publicacao` está dentro da janela esperada; rejeitar se `data_publicacao > NOW() + 30 days` (publicação futura suspeita).
- **R3 (Médio):** URL do documento (`gazette.url`) pode ser um PDF escaneado. PlaywrightExtractor retorna None → fallback LLM no excerpt. Aceitar campos parciais nesse caso.

---

## Dependências

- **EXT-001** — tabela `external_bids` deve existir
- **EXT-002** — `PlaywrightExtractor` deve estar implementado
- **EXT-006** — `ExternalBidLoader` deve estar implementado (ou implementar upsert inline temporariamente)
- `qd_territory_ids.yaml` pode ser criado com lista inicial de municípios conhecidos do Querido Diário (dataset público disponível em `github.com/okfn-brasil/censo-querido-diario`)

---

## Arquivos Relevantes

| Arquivo | Ação |
|---------|------|
| `backend/ingestion/external/querido_diario_crawler.py` | Criar |
| `backend/ingestion/external/qd_territory_ids.yaml` | Criar |
| `backend/job_queue.py` (ou `cron_jobs.py`) | Atualizar (adicionar jobs QD) |
| `backend/metrics.py` | Atualizar (adicionar métricas QD) |
| `backend/tests/ingestion/external/test_querido_diario_crawler.py` | Criar |

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — EPIC-EXT-001 |
| 2026-04-23 | @po | Validação 10-pontos: **9/10 → GO** — R2 (excerpt context) requer validação de data_publicacao no LLM extraction; documentado. Status: Draft → Ready |
