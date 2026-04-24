# EXT-004: Crawler BNC (Bolsa Nacional de Compras)

**Status:** Ready [⚠️ deploy produção bloqueado até validação ToS/robots.txt]
**Origem:** EPIC-EXT-001 — Fontes Externas de Licitações
**Prioridade:** P1 — Alta (23 estados, HTML estruturado, sem CAPTCHA confirmado)
**Complexidade:** M (Medium) — ~8h
**Sprint:** EXT-sprint-02
**Owner:** @dev
**Tipo:** Backend / Ingestion

---

## Problema

A BNC (Bolsa Nacional de Compras) opera como plataforma privada de pregão eletrônico em 23 estados, com 1.500+ órgãos públicos. Diferente do BLL (que sincroniza 100% com PNCP), a BNC não tem integração completa confirmada com o PNCP — editais existem no portal público `bnccompras.com` que não chegam ao SmartLic.

O portal de busca pública (`bnccompras.com/Process/ProcessSearchPublic`) tem HTML estruturado com campos bem definidos (processo, objeto, modalidade, datas, situação), sem autenticação.

**CRÍTICO:** Verificar `robots.txt` e ToS antes do primeiro crawl em produção.

---

## Critérios de Aceite

- [ ] **AC1:** `BncCrawler.crawl()` itera pelas 27 UFs e coleta editais dos últimos 10 dias
- [ ] **AC2:** Paginação funcional — detecta total de páginas via HTML e itera com delay de 2s entre páginas
- [ ] **AC3:** Campos extraídos da listagem: número do processo, objeto, órgão, modalidade, data publicação, data abertura, situação, link do edital
- [ ] **AC4:** Para cada edital na listagem, enfileira URL de detalhe para `PlaywrightExtractor` (pega valor estimado e campos adicionais)
- [ ] **AC5:** `source_name='bnc'`, `source_priority=5` nos registros gerados
- [ ] **AC6:** `robots.txt` de `bnccompras.com` verificado e logado no início do crawl (não bloqueia automaticamente — apenas loga)
- [ ] **AC7:** User-Agent identificador: `SmartLic-Bot/1.0 (pesquisa-licitacoes; contato@smartlic.tech)`
- [ ] **AC8:** Circuit breaker estrutural: se HTML da listagem não contiver campos-chave esperados, emitir `capture_message(level="warning", message="BNC structure drift")` via Sentry e parar crawl
- [ ] **AC9:** ARQ cron job `bnc_full_job` agendado para 4am BRT diário
- [ ] **AC10:** Métricas `smartlic_bnc_bids_discovered_total` e `smartlic_bnc_extraction_errors_total` incrementadas
- [ ] **AC11:** `pytest tests/ingestion/external/test_bnc_crawler.py` passa com mocks de httpx e BeautifulSoup

### Anti-requisitos

- Não fazer login — apenas endpoints públicos sem auth
- Não ignorar o rate limit de 2s entre requests — portais gov tendem a bloquear IPs que excedem
- Não crashar o job inteiro se uma UF falhar — continuar para a próxima, logar o erro
- Não remover/alterar sources existentes (PNCP, PCP, ComprasGov) — BNC é adição, não substituição

---

## Tarefas

- [ ] Inspecionar manualmente `bnccompras.com/Process/ProcessSearchPublic` (DevTools) para confirmar seletores CSS antes de implementar
- [ ] Verificar `bnccompras.com/robots.txt` e documentar resultado no código (comentário)
- [ ] Criar `backend/ingestion/external/bnc_crawler.py`
- [ ] Implementar parsing de listagem com BeautifulSoup (seletores a confirmar via inspeção)
- [ ] Implementar paginação com detecção de total de páginas
- [ ] Integrar com `PlaywrightExtractor` para páginas de detalhe
- [ ] Implementar structural drift detection (hash de seletores esperados)
- [ ] Registrar ARQ job em `backend/job_queue.py`
- [ ] Adicionar métricas Prometheus
- [ ] Criar `backend/tests/ingestion/external/test_bnc_crawler.py` (mock HTML para evitar requests reais nos testes)

---

## Referência de Implementação

```python
# Pattern de iteração por UF com BeautifulSoup
async def crawl_uf(self, uf: str, window_days: int = 10) -> list[ExternalBidRaw]:
    base_url = "https://bnccompras.com/Process/ProcessSearchPublic"
    since = (date.today() - timedelta(days=window_days)).isoformat()
    
    params = {
        "uf": uf,
        "dataInicial": since,
        # confirmar nomes dos params via inspeção do form
    }
    
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        resp = await client.get(base_url, params=params)
        soup = BeautifulSoup(resp.text, "html.parser")
        # ... extrair itens e paginar
```

- Pattern de circuit breaker: ver `backend/clients/base.py` (circuit breaker existente)
- Structural hash: `hashlib.md5("|".join(seletores_encontrados).encode()).hexdigest()` comparado a hash esperado
- Sentry warning: `from sentry_sdk import capture_message`

---

## Riscos

- **R1 (Crítico):** ToS da BNC pode proibir scraping automatizado. **Bloqueia deploy em produção** até revisão jurídica. Dev pode implementar e testar localmente enquanto isso.
- **R2 (Alto):** Estrutura HTML da listagem pode mudar sem aviso. Circuit breaker estrutural mitiga impacto — para de ingerir sem crashar o worker.
- **R3 (Médio):** Portais como BNC às vezes retornam páginas de resultado vazias por sobrecarga. Implementar retry (2 tentativas) antes de registrar erro.
- **R4 (Baixo):** Editais BNC podem estar no PNCP (integração parcial). content_hash dedup resolve — duplicatas são silenciosamente ignoradas.

---

## Dependências

- **EXT-001** — tabela `external_bids`
- **EXT-002** — `PlaywrightExtractor`
- **EXT-006** — `ExternalBidLoader`
- Inspeção manual do HTML do BNC antes de escrever seletores (tarefas marcam isso como primeiro passo)

---

## Arquivos Relevantes

| Arquivo | Ação |
|---------|------|
| `backend/ingestion/external/bnc_crawler.py` | Criar |
| `backend/job_queue.py` | Atualizar (adicionar BNC job) |
| `backend/metrics.py` | Atualizar (adicionar métricas BNC) |
| `backend/tests/ingestion/external/test_bnc_crawler.py` | Criar |

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — EPIC-EXT-001 |
| 2026-04-23 | @po | Validação 10-pontos: **9/10 → GO condicional** — R1 (ToS BNC) é BLOQUEADOR de deploy em produção; desenvolvimento pode prosseguir. Status: Draft → Ready [deploy produção bloqueado] |
