# MON-AI-02: AI Copilot de Propostas (RAG sobre Contratos Vencedores)

**Priority:** P1
**Effort:** XL (8-10 dias)
**Squad:** @dev + @architect + @qa
**Status:** Draft
**Epic:** [EPIC-MON-AI-2026-04](EPIC-MON-AI-2026-04.md)
**Sprint:** Wave 2 (depende MON-AI-01 + MON-REP-01 + MON-SUB-01)

---

## Contexto

**Produto mais alto ticket do epic IA** e **forte moat**. Usuário sobe o PDF do edital → IA extrai requisitos → busca semântica em contratos vencedores similares (MON-AI-01 RAG) → gera rascunho de proposta estruturada com justificativa técnica.

**Diferencial único:** 2M+ contratos vencedores como corpus de referência — nenhum competidor tem isso.

**Modelo comercial:**
- **R$ 197/proposta one-shot** (via MON-REP-01) — para uso esporádico
- **Add-on R$ 497/mês** (via MON-SUB-01) — 20 propostas/mês, sobra acumula

---

## Acceptance Criteria

### AC1: Upload e extração de edital

- [ ] Endpoint `POST /v1/copilot/proposta/draft`:
  - Body multipart: `edital_pdf` (file) + `tier` (one-shot | subscription) + `contexto_empresa` (str, opcional — ex: razão social, CNAE)
  - Upload file para Supabase Storage (bucket `copilot-uploads`, 7 days TTL)
  - Enfileira ARQ job `generate_proposal_draft(upload_id)`
  - Retorna `{job_id, eta_seconds: 120}`

- [ ] ARQ job `generate_proposal_draft`:
  1. **Extração** — GPT-4.1-nano com structured output extrai do edital: objeto, requisitos técnicos, critérios de julgamento, valor estimado, prazo, modalidade
  2. **Retrieval (RAG)** — usa MON-AI-01 para encontrar 10 contratos similares (filtrar por mesma modalidade + similaridade >0.75)
  3. **Análise** — LLM analisa: "dado esses 10 vencedores, quais elementos comuns nas propostas venceu?"
  4. **Geração** — LLM produz rascunho em seções:
     - Apresentação da empresa (usa `contexto_empresa`)
     - Compreensão do objeto
     - Metodologia (baseada em padrões detectados)
     - Cronograma sugerido
     - Valor proposto (range com justificativa: mediana + 10%)
     - Elementos diferenciais
     - Fontes: citar contract_ids vencedores usados como referência
  5. Gera PDF + Word (.docx) + Markdown
  6. Cria `generated_reports` row + envia email (reusa MON-REP-02)

### AC2: Schema Pydantic para extração

- [ ] `backend/schemas/copilot/edital_extracted.py`:
```python
class EditalExtracted(BaseModel):
    objeto: str
    objeto_resumo: str
    requisitos_tecnicos: list[str]
    criterios_julgamento: list[str]
    valor_estimado_cents: int | None
    prazo_dias: int | None
    modalidade: int
    uf_execucao: str | None
    catmat_catser_sugerido: str | None
```

### AC3: Prompts multi-stage

- [ ] `backend/llm/prompts/copilot_extraction.py` (stage 1)
- [ ] `backend/llm/prompts/copilot_analysis.py` (stage 3) — input: 10 contratos similares + edital extraído
- [ ] `backend/llm/prompts/copilot_generation.py` (stage 4) — structured output com todas as seções
- [ ] **Ground-truth enforcement:** output DEVE citar `numero_controle_pncp` de contratos vencedores usados; sem citação → falha geração com fallback

### AC4: Geração PDF + Word

- [ ] `backend/reports/copilot_proposal_report.py`:
  - PDF via reportlab (como outros relatórios)
  - Word via `python-docx`
  - Markdown versão raw para copy-paste
- [ ] Todos os 3 formatos entregues no email (ZIP) + download endpoints separados

### AC5: Frontend `/copilot`

- [ ] `frontend/app/copilot/page.tsx`:
  - Upload dropzone para PDF de edital (max 20 MB)
  - Campo "Contexto da empresa" (opcional)
  - Seletor "One-shot R$ 197" ou "Assinar R$ 497/mês" (se não assinou)
  - Checkout via MON-REP-01 ou MON-SUB-01
  - Após compra: página de "processando" (polling a cada 10s)
  - Resultado: preview HTML + buttons download (PDF/Word/MD)

### AC6: Limites de uso do add-on

- [ ] Tier add-on R$ 497/mês = 20 propostas/mês
- [ ] Tracking em `monitored_subscriptions.config.proposals_used_current_month`
- [ ] Se excedido: 402 com CTA "Comprar 5 propostas extras por R$ 99" (one-shot bundle)
- [ ] Reset no início do ciclo de billing

### AC7: Testes

- [ ] Unit: mock LLM → extração estruturada correta
- [ ] Integration: E2E com PDF de edital real (bundle 3 editais de teste em `backend/tests/fixtures/`)
- [ ] Quality gate: manual review de 10 propostas geradas antes do release — nenhuma com dados inventados (ground truth)
- [ ] E2E Playwright: upload → checkout → processing → download

---

## Scope

**IN:**
- Upload + extraction
- RAG pipeline
- Prompt multi-stage + ground truth
- 3 formatos de output (PDF, Word, MD)
- Frontend wizard
- Limite de uso tier add-on
- Testes + quality gate humano

**OUT:**
- Refinamento interativo ("melhore a seção X") — v2
- Tradução para outros idiomas — fora de escopo
- Assinatura digital do PDF — fora de escopo
- Integração com sistemas de gestão de propostas — v2

---

## Dependências

- MON-AI-01 (embeddings para RAG)
- MON-REP-01 (checkout one-shot)
- MON-REP-02 (delivery)
- MON-SUB-01 (add-on recorrente)
- OpenAI API (já em uso)

---

## Riscos

- **LLM alucinação em proposta paga:** ground-truth + citação obrigatória + quality gate humano antes release
- **Custo LLM por proposta:** 10 contratos RAG × chunks + prompt grande ≈ 30k tokens × USD 0.002 / 1K = USD 0.06/proposta. Margem ok para R$ 197
- **Edital pdf com imagens (tabelas):** OCR fallback via Tesseract ou GPT-4 Vision; v1 documentar "apenas PDFs textuais"
- **Proposta gerada rejeita pelo órgão:** disclaimer "rascunho para revisão humana, não é proposta final aprovada por órgão"

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/copilot/proposta_generator.py` (novo — orquestração)
- `backend/llm/prompts/copilot_*.py` (3 files)
- `backend/schemas/copilot/*.py` (novo)
- `backend/reports/copilot_proposal_report.py` (novo)
- `backend/jobs/copilot_jobs.py` (novo)
- `backend/routes/copilot.py` (novo)
- `frontend/app/copilot/page.tsx` (novo)
- `backend/tests/copilot/test_proposal_generator.py` (novo)
- `backend/tests/fixtures/editais/*.pdf` (seed 3 editais reais)

---

## Definition of Done

- [ ] 10 propostas geradas em staging, validadas em review humano (0 dados inventados, 0 citações fake)
- [ ] E2E: upload → checkout → geração em <3 min → download funciona
- [ ] Add-on subscription com 20 usos/mês rastreado corretamente
- [ ] Custo médio por proposta <USD 0.10 (observado via Prometheus)
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — produto de moat IA, high ticket |
