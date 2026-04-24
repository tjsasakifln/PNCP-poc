# EXT-005: Crawler IPM/Atende.Net

**Status:** Ready [⚠️ deploy produção bloqueado até validação ToS/robots.txt]
**Origem:** EPIC-EXT-001 — Fontes Externas de Licitações
**Prioridade:** P2 — Alta (850+ municípios RS/SC/PR/MG com URL pattern identificado)
**Complexidade:** L (Large) — ~13h
**Sprint:** EXT-sprint-02
**Owner:** @dev
**Tipo:** Backend / Ingestion

---

## Problema

O IPM Sistemas (Santa Catarina, desde 1989) fornece o sistema `Atende.Net` para 850+ municípios em RS, SC, PR e MG. O portal público de licitações segue o padrão URL `{municipio}.atende.net/cidadao/noticia/categoria/licitacoes` — uma das poucas fontes com padrão de URL identificado e consistente.

O portal usa Vue.js com rendering client-side, portanto requer Playwright (não httpx+BS4). A cobertura inclui municípios que frequentemente não publicam no PNCP por serem de menor porte.

---

## Critérios de Aceite

- [ ] **AC1:** `IpmAtendeCrawler.crawl_all()` processa todos os municípios ativos em `ipm_municipalities.yaml`
- [ ] **AC2:** Playwright aguarda renderização Vue.js: `page.wait_for_load_state("networkidle")` ou `wait_for_selector` com timeout 15s
- [ ] **AC3:** Campos extraídos da listagem: título do edital, data de publicação, link de detalhe, número (se disponível)
- [ ] **AC4:** Para cada item de listagem, passa URL de detalhe para `PlaywrightExtractor` (campos completos + valor estimado)
- [ ] **AC5:** Discovery automática ao processar cada município: se HTTP 404 ou estrutura Vue não reconhecida após timeout, marcar município como `status: inactive` no YAML e pular nas próximas execuções
- [ ] **AC6:** Concorrência: máximo 10 municípios processados em paralelo via `asyncio.Semaphore(10)`
- [ ] **AC7:** `source_name='ipm_atende'`, `source_priority=6`
- [ ] **AC8:** Structural change detection: hash do HTML estrutural da listagem (seletores presentes/ausentes). Se mudar, `capture_message(level="warning")` Sentry + pular município
- [ ] **AC9:** ARQ cron job `ipm_full_job` agendado para 5am BRT diário
- [ ] **AC10:** Métricas `smartlic_ipm_municipalities_crawled_total` e `smartlic_ipm_bids_discovered_total`
- [ ] **AC11:** Arquivo `backend/ingestion/external/ipm_municipalities.yaml` com ~100 municípios iniciais confirmados
- [ ] **AC12:** `pytest tests/ingestion/external/test_ipm_crawler.py` passa com mock Playwright

### Anti-requisitos

- Não tentar todos os 850+ municípios de uma vez — iniciar com ~100 confirmados e expandir gradualmente
- Não usar `asyncio.gather` sem semaphore — cria N browsers simultâneos, explode memória do worker
- Não crashar job inteiro se município falhar — continue para o próximo

---

## Lista Inicial de Municípios (`ipm_municipalities.yaml`)

Formato:
```yaml
municipalities:
  - slug: gramado
    municipio: Gramado
    uf: RS
    ibge: "4309100"
    status: active
  - slug: sao-jose
    municipio: São José
    uf: SC
    ibge: "4216602"
    status: active
  # ... ~100 municípios iniciais
```

Fonte da lista: verificar municípios que aparecem em `supplier_contracts` com `orgao_uf IN ('RS','SC','PR','MG')` e órgão municipal — cruzar com domínios conhecidos do Atende.Net.

---

## Tarefas

- [ ] Inspecionar `{municipio}.atende.net` em 3-5 municípios reais (DevTools) para confirmar seletores Vue.js antes de implementar
- [ ] Criar `backend/ingestion/external/ipm_municipalities.yaml` com lista inicial (~100 municípios)
- [ ] Criar `backend/ingestion/external/ipm_crawler.py`
- [ ] Implementar `IpmAtendeCrawler` com Playwright
- [ ] Implementar discovery/status management (active/inactive por município)
- [ ] Implementar structural hash detection
- [ ] Integrar com `PlaywrightExtractor` para páginas de detalhe
- [ ] Registrar ARQ job
- [ ] Adicionar métricas
- [ ] Criar `backend/tests/ingestion/external/test_ipm_crawler.py`

---

## Referência de Implementação

```python
async def crawl_municipality(self, muni: dict) -> list[ExternalBidRaw]:
    url = f"https://{muni['slug']}.atende.net/cidadao/noticia/categoria/licitacoes"
    
    async with self._semaphore:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu"]
            )
            ctx = await browser.new_context(
                user_agent="SmartLic-Bot/1.0 (pesquisa-licitacoes; contato@smartlic.tech)"
            )
            page = await ctx.new_page()
            
            try:
                await page.goto(url, timeout=20000)
                await page.wait_for_load_state("networkidle", timeout=15000)
                
                # Verificar se estrutura Vue.js está presente
                # (seletores a confirmar via inspeção manual)
                items = await page.query_selector_all(".noticia-item")  # CONFIRMAR
                
                results = []
                for item in items:
                    link = await item.query_selector("a")
                    href = await link.get_attribute("href") if link else None
                    if href:
                        detail = await self.extractor.extract(href, "ipm_atende")
                        if detail:
                            detail.uf = muni["uf"]
                            results.append(detail)
                return results
                
            except Exception as e:
                # Marcar município como inactive se 404 ou timeout estrutural
                ...
            finally:
                await browser.close()
```

---

## Riscos

- **R1 (Alto):** Seletores Vue.js confirmados apenas via inspeção — podem diferir entre municípios ou versões do Atende.Net. Implementar fallback: se `query_selector_all` retornar 0 items, tentar seletor alternativo antes de declarar structural drift.
- **R2 (Médio):** 100 municípios em paralelo (10 por vez) ainda cria 10 browsers Playwright simultâneos no worker. Monitorar RAM no Railway após deploy.
- **R3 (Baixo):** Alguns municípios podem usar versão diferente do Atende.Net com URL diferente. Discovery status=inactive captura isso sem crashar.
- **R4 (Crítico):** ToS do IPM Sistemas/Atende.Net — verificar antes do deploy em produção.

---

## Dependências

- **EXT-001** — tabela `external_bids`
- **EXT-002** — `PlaywrightExtractor`
- **EXT-006** — `ExternalBidLoader`
- Inspeção manual prévia de 3-5 municípios Atende.Net (primeiro passo das tarefas)

---

## Arquivos Relevantes

| Arquivo | Ação |
|---------|------|
| `backend/ingestion/external/ipm_crawler.py` | Criar |
| `backend/ingestion/external/ipm_municipalities.yaml` | Criar |
| `backend/job_queue.py` | Atualizar |
| `backend/metrics.py` | Atualizar |
| `backend/tests/ingestion/external/test_ipm_crawler.py` | Criar |

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — EPIC-EXT-001 |
| 2026-04-23 | @po | Validação 10-pontos: **9/10 → GO condicional** — R4 (ToS IPM) é BLOQUEADOR de deploy em produção; desenvolvimento pode prosseguir. Inspeção manual de seletores Vue.js obrigatória antes de implementar. Status: Draft → Ready [deploy produção bloqueado] |
