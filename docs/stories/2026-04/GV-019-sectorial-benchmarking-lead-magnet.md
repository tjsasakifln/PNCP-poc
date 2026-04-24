# GV-019: Sectorial Benchmarking Lead Magnet Público

**Priority:** P2
**Effort:** M (8 SP, 4 dias)
**Squad:** @dev + @data-engineer + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 4

---

## Contexto

Ferramenta pública `/benchmark` (sem auth) onde usuário submete setor + UF → recebe relatório agregado: "Empresas do setor X em UF Y: N contratos, R$ Z total, P50/P90 valores, top 10 órgãos compradores".

Top-of-funnel clássico content marketing:
- SEO-friendly (uma URL indexável por setor×UF = 405 pages)
- Lead magnet PDF gated por email → entra em drip sequence → trial
- Dados agregados = zero risco LGPD

Integra com EPIC-SEO-ORGANIC (estende observatório) e EPIC-MON-SCHEMA (usa supplier_contracts enriquecido).

---

## Acceptance Criteria

### AC1: Página `/benchmark`

- [ ] `frontend/app/benchmark/page.tsx`:
  - Form: setor (select 15 setores) + UF (select 27) + opcional "range de valor"
  - Submit → redirect `/benchmark/{setor_slug}/{uf}` com dados agregados
  - Indexável (noindex off)

### AC2: Páginas de resultado

- [ ] `frontend/app/benchmark/[setor]/[uf]/page.tsx`:
  - SSG + ISR 1h
  - Conteúdo público (sem email gate):
    - Hero: "Benchmark {Setor} em {UF}"
    - Stats agregados: total contratos, valor total, P50/P90 valores
    - Gráfico temporal últimos 12 meses
    - Top 3 órgãos compradores (nome + valor)
    - Insight textual gerado via LLM: "Setor X cresceu Y% em Z"
  - Conteúdo gated (email capture):
    - Top 10 órgãos completos
    - Top 10 fornecedores (concorrentes)
    - PDF download com relatório full
    - CTA "Receber relatório completo grátis" → email form

### AC3: Endpoint agregado

- [ ] `backend/routes/benchmark.py`:
  - `GET /v1/benchmark/{setor}/{uf}` retorna agregados públicos
  - `POST /v1/benchmark/{setor}/{uf}/request-full` — email capture + envia PDF
  - Cache Redis 1h
  - Rate limit 100/min por IP

### AC4: PDF generator

- [ ] `backend/services/pdf_generator.py` (reutiliza `report_generator.py` se existe):
  - Template branded
  - Dados do benchmark + top 10 + insights
  - Footer CTA "Análise personalizada com SmartLic — 14 dias grátis"
- [ ] `GET /v1/benchmark/{id}/pdf` — gera + retorna PDF; logging user_email

### AC5: Drip email sequence

- [ ] `backend/services/benchmark_drip.py`:
  - D+0: email "Seu relatório chegou!" com PDF anexo
  - D+3: "Como usar insights do benchmark" com link blog post
  - D+7: "Encontre oportunidades específicas — teste SmartLic 14d"
  - D+14: "Último convite — trial ainda disponível"
  - Unsubscribe 1-click

### AC6: SEO

- [ ] Schema.org `Dataset`:
  ```json
  {"@type": "Dataset", "name": "Benchmark {setor} {UF}", "description": "...", "keywords": [...]}
  ```
- [ ] `frontend/app/sitemap.ts` inclui 405 páginas (15×27) com ISR
- [ ] Meta tags otimizadas por combinação

### AC7: Tracking

- [ ] Mixpanel:
  - `benchmark_page_viewed` com setor/uf
  - `benchmark_email_captured`
  - `benchmark_pdf_downloaded`
  - Drip email opens/clicks via Resend webhooks

### AC8: Testes

- [ ] Unit aggregation queries
- [ ] E2E Playwright: select setor+uf → page → email capture → PDF download
- [ ] Load test endpoint agregado p95 <300ms

---

## Scope

**IN:**
- Página público + gated
- Endpoints agregação
- PDF generator
- Drip sequence
- SEO schema

**OUT:**
- Benchmark por CNPJ específico (overlap EPIC-MON-REP-03) — rejeitado, é produto pago
- Benchmark histórico 10 anos (v2, performance)
- Comparação multi-UF lado-a-lado (v2)

---

## Dependências

- **Nenhuma** direta
- `supplier_contracts` tabela (2M rows)
- `frontend/app/sitemap.ts` existente

---

## Riscos

- **Privacy: agregação tão granular que identifica empresa:** floor mínimo 5 contratos por combo antes de publicar
- **LLM insight hallucination:** templates estáticos + verificação factual antes publish (human review primeiras 30 combinações)
- **PDF generation lenta em scale:** async + email delivery se >5s

---

## Arquivos Impactados

### Novos
- `frontend/app/benchmark/page.tsx`
- `frontend/app/benchmark/[setor]/[uf]/page.tsx`
- `backend/routes/benchmark.py`
- `backend/services/benchmark_drip.py`
- `backend/templates/emails/benchmark_d0.html`, `benchmark_d3.html`, `benchmark_d7.html`, `benchmark_d14.html`
- `backend/tests/test_benchmark.py`

### Modificados
- `frontend/app/sitemap.ts` (incluir /benchmark/*)
- `backend/services/pdf_generator.py` se existe, ou criar

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — top-of-funnel content magnet com drip sequence |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Human review LLM insights nas 30 primeiras combinações antes publish. Status Draft → Ready. |
