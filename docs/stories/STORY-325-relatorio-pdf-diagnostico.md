# STORY-325: Relatorio PDF — Diagnostico de Oportunidades

**Epic:** EPIC-TURBOCASH-2026-03
**Sprint:** Sprint 1 (Quick Cash)
**Priority:** P0 — BLOCKER
**Story Points:** 8 SP
**Estimate:** 4-6 dias
**Owner:** @dev
**Origem:** TurboCash Playbook — Acao 1 (Diagnostico de Oportunidades, Semana 1-2)

---

## Problem

O founder precisa gerar relatorios profissionais em PDF para vender como "Diagnostico de Oportunidades" (R$1.500-3.000 por relatorio). Atualmente, o SmartLic so exporta Excel. Um PDF com branding, score de viabilidade visual, e resumo executivo com IA e essencial para a oferta services-led que gera cash nos primeiros 30 dias.

## Solution

Gerar PDF profissional a partir dos resultados de busca com:
- Capa com branding SmartLic (ou logo da consultoria, STORY-322)
- Resumo executivo com IA (reutilizar LLM summary)
- Top 20 oportunidades rankeadas por viabilidade
- Score de viabilidade visual (gauge/barra) por oportunidade
- Metricas agregadas (total, valor medio, distribuicao por UF/modalidade)
- Footer com disclaimer e data de geracao

**Meta:** 3-5 diagnosticos = R$4.500-15.000 em receita imediata.

---

## Acceptance Criteria

### Backend — Geracao de PDF

- [ ] **AC1:** Endpoint `POST /v1/reports/diagnostico`:
  - Input: `search_id` (referencia a uma busca realizada)
  - Input opcional: `logo_url` (logo da consultoria/cliente)
  - Input opcional: `client_name` (nome da empresa-alvo)
  - Input opcional: `max_items` (default: 20)
  - Output: PDF file (application/pdf)
  - Auth: require_auth (qualquer plano, inclusive trial)
- [ ] **AC2:** Usar **WeasyPrint** ou **reportlab** para geracao de PDF:
  - WeasyPrint preferido (HTML→PDF, mais flexivel para layout)
  - Fallback: reportlab se WeasyPrint tiver problemas em Railway (C deps)
- [ ] **AC3:** Template HTML para o PDF em `backend/templates/reports/diagnostico.html`:
  - CSS inline (WeasyPrint suporta subset do CSS3)
  - Responsivo para A4 (210mm x 297mm)

### Backend — Conteudo do PDF

- [ ] **AC4:** **Capa (pagina 1):**
  - Logo SmartLic (ou logo customizado se fornecido)
  - Titulo: "Diagnostico de Oportunidades em Licitacoes"
  - Subtitulo: "Preparado para {client_name}" (se fornecido)
  - Setor(es) buscado(s)
  - Data de geracao
  - Periodo da busca
  - UFs analisadas
- [ ] **AC5:** **Resumo Executivo (pagina 2):**
  - Resumo IA (reutilizar `llm.py` summary ou buscar do cache)
  - Metricas em destaque: total encontradas, total filtradas, valor total, valor medio
  - Distribuicao por UF (top 5, bar chart ou tabela)
  - Distribuicao por modalidade (pie chart ou tabela)
  - Recomendacao: "Das {N} oportunidades, {M} tem score de viabilidade acima de 70%"
- [ ] **AC6:** **Top 20 Oportunidades (paginas 3+):**
  - Tabela com: #, Titulo (truncado 100 chars), Orgao, UF, Valor, Modalidade, Prazo, Score Viabilidade
  - Score de viabilidade com indicador visual: verde (>70%), amarelo (40-70%), vermelho (<40%)
  - Ordenado por score de viabilidade (desc)
  - Se menos de 20 resultados, mostrar todos
- [ ] **AC7:** **Footer em todas as paginas:**
  - "Gerado por SmartLic (smartlic.tech) em {data}"
  - "Este relatorio e uma analise automatizada e nao constitui consultoria juridica"
  - Numero da pagina: "Pagina X de Y"
- [ ] **AC8:** **Metadados do PDF:**
  - Title: "Diagnostico de Oportunidades — {setor} — {data}"
  - Author: "SmartLic"
  - Creator: "SmartLic v0.5"

### Backend — Integracao com Pipeline Existente

- [ ] **AC9:** Reutilizar dados do `search_id` (nao refazer busca):
  - Buscar resultados do cache (L1/L2)
  - Se cache expirado, retornar 404 com mensagem "Busca expirada, refaca a busca"
- [ ] **AC10:** Reutilizar LLM summary do cache/ARQ (nao rechamar LLM)
- [ ] **AC11:** Se viability scores existem, usar. Se nao, calcular on-the-fly.

### Frontend — Botao de Download

- [ ] **AC12:** Botao "Gerar Relatorio PDF" em `SearchResults.tsx`:
  - Icone de PDF + texto "Relatorio PDF"
  - Posicao: ao lado do botao "Baixar Excel"
  - Loading state durante geracao (pode levar 5-10s)
- [ ] **AC13:** Modal de opcoes antes de gerar:
  - Campo: "Nome da empresa" (opcional)
  - Campo: "Logo" (upload opcional, max 2MB, PNG/JPG)
  - Campo: "Numero de oportunidades" (slider: 10/20/50, default 20)
  - Botao: "Gerar PDF"
- [ ] **AC14:** Download automatico apos geracao (blob URL)

### Frontend — API Proxy

- [ ] **AC15:** Proxy route `frontend/app/api/reports/diagnostico/route.ts`:
  - POST → backend `/v1/reports/diagnostico`
  - Stream response (PDF pode ser grande)
  - Content-Type: application/pdf
  - Content-Disposition: attachment; filename="diagnostico-{setor}-{data}.pdf"

### Testes

- [ ] **AC16:** Testes backend: gera PDF valido (verifica que output e PDF)
- [ ] **AC17:** Testes backend: capa com/sem logo, com/sem client_name
- [ ] **AC18:** Testes backend: top 20 ordenado por viability score
- [ ] **AC19:** Testes backend: search_id invalido → 404
- [ ] **AC20:** Testes frontend: modal de opcoes, botao de download
- [ ] **AC21:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Excel export | `backend/excel.py` | Existe (referencia para layout) |
| LLM summary | `backend/llm.py` | Existe |
| Viability assessment | `backend/viability.py` | Existe |
| Search cache | `backend/search_cache.py` | Existe |
| Search results | `frontend/app/buscar/components/SearchResults.tsx` | Existe |

## Files Esperados (Output)

**Novos:**
- `backend/pdf_report.py` (ou `backend/services/pdf_report.py`)
- `backend/templates/reports/diagnostico.html`
- `backend/templates/reports/diagnostico.css`
- `backend/routes/reports.py`
- `backend/tests/test_pdf_report.py`
- `frontend/app/api/reports/diagnostico/route.ts`
- `frontend/components/reports/PdfOptionsModal.tsx`
- `frontend/__tests__/reports/pdf-options.test.tsx`

**Modificados:**
- `backend/main.py` (registrar router)
- `backend/requirements.txt` (WeasyPrint ou reportlab)
- `frontend/app/buscar/components/SearchResults.tsx` (botao PDF)

## Dependencias

- Nenhuma bloqueadora (pode ser feita em paralelo com STORY-319)
- STORY-322 (Plano Consultoria) — logo da org no PDF (fase 2)
- WeasyPrint requer dependencias C no Railway (cairo, pango, gdk-pixbuf)
  - Alternativa: reportlab (pure Python, sem deps C)
  - Alternativa: usar wkhtmltopdf via subprocess
  - **Decisao tecnica necessaria antes de implementar**

## Riscos

- WeasyPrint pode ter problemas de instalacao no Railway (Alpine/Debian) → testar em Docker primeiro
- Geracao de PDF pode ser lenta (5-10s) → considerar ARQ background job + SSE notification
- Tamanho do PDF com 50 items pode ser grande (>5MB) → limitar a 20 items default
- CSS para PDF (WeasyPrint) tem limitacoes vs CSS normal → testar layout antes de refinar
