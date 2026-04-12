# STORY-447: PDF Executivo por Edital

**Priority:** P2 — Viral B2B + diferencial de exportação
**Effort:** L (5-7 dias)
**Squad:** @dev + @qa
**Status:** Ready
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 3 — Semanas 5-8

---

## Contexto

O SmartLic exporta para Excel (consolidado) e Google Sheets, mas não há PDF individual por edital. Um PDF de 1 página com resumo IA + score de viabilidade + dados-chave é compartilhável internamente (gerente → time, empresa → cliente) e funciona como viral B2B — cada PDF com watermark "Gerado por SmartLic" é marketing gratuito.

Para trial users, o PDF mostra o resumo COMPLETO (não truncado) — o PDF é o hook para o upgrade, não uma recompensa pós-upgrade.

**Impacto estimado:** +0.5-1pp em conversão + efeito viral B2B.

---

## Acceptance Criteria

### AC1: Botão "Exportar PDF" em cada ResultCard
- [ ] Botão "↓ PDF" ou ícone de PDF em cada card de resultado, ao lado dos outros botões
- [ ] Botão disponível para trial E pagantes
- [ ] Click dispara geração do PDF (loading state no botão enquanto gera)

### AC2: Conteúdo do PDF
- [ ] PDF de 1 página A4 com:
  - Header: logo SmartLic + data de geração
  - Título do edital (bold, destaque)
  - Órgão contratante
  - Modalidade
  - Valor estimado (formatado em R$)
  - Prazo de encerramento
  - Score de viabilidade (badge colorido + breakdown dos 4 fatores)
  - Resumo executivo COMPLETO (não truncado — diferencial do trial)
  - Recomendação de participação (se disponível no campo `recomendacao` do resumo)
  - Footer: "Fonte: PNCP" + data de publicação do edital

### AC3: Watermark para trial users
- [ ] Para usuários trial: adicionar watermark no rodapé: "Gerado com SmartLic Trial — smartlic.tech | Assine para remover"
- [ ] Para pagantes: PDF limpo sem watermark, footer apenas "Gerado por SmartLic — smartlic.tech"

### AC4: Geração no backend
- [ ] Endpoint: `POST /v1/export/pdf` com body `{ result_id: string, search_id: string }`
- [ ] Retorna PDF binário como response com `Content-Type: application/pdf`
- [ ] Ou retorna URL temporária (se geração for lenta)
- [ ] Autenticado (Bearer token)

### AC5: Geração síncrona (não ARQ) para simplicidade
- [ ] Dado o tamanho pequeno (1 página), gerar de forma síncrona (não ARQ background job)
- [ ] Timeout da geração: 10 segundos máximo
- [ ] Se timeout: retornar 503 com mensagem "Tente novamente"

### AC6: Biblioteca PDF — reportlab (já instalada)
- [ ] Usar `reportlab==4.4.0` (confirmado em `requirements.txt` — já instalado)
- [ ] NÃO instalar nova biblioteca; NÃO usar `weasyprint`
- [ ] Implementar com `reportlab.platypus` (PLATYPUS para layout simples de 1 página)

### AC7: Download no frontend
- [ ] Ao receber o PDF: trigger download automático com filename `SmartLic_{titulo_curto}_{data}.pdf`
- [ ] Loading state no botão: spinner durante geração
- [ ] Error state: toast de erro se geração falhar

### AC8: Testes
- [ ] Teste: PDF gerado tem Content-Type correto (`application/pdf`)
- [ ] Teste: PDF para trial user contém "smartlic.tech" no footer
- [ ] Teste: PDF para pagante não contém "Trial"
- [ ] Teste: campos obrigatórios presentes no PDF (título, órgão, valor)
- [ ] Teste: geração com dados mock completos → PDF válido (não corrompido)

---

## Scope

**IN:**
- Endpoint `POST /v1/export/pdf`
- Gerador de PDF no backend (`pdf_generator.py`)
- Botão "PDF" no `ResultCard`
- Watermark condicional por plano
- Download automático no frontend

**OUT:**
- PDF consolidado de múltiplos editais (→ Excel já cobre isso)
- PDF com gráficos/charts
- Geração assíncrona via ARQ (síncrona é suficiente para 1 página)
- Armazenamento/histórico de PDFs gerados
- Custom branding para clientes Consultoria

---

## Dependencies

- `viability.py` retorna breakdown dos 4 fatores (AC2 requer o breakdown)
- STORY-440 (ViabilityBadge) — PDF deve mostrar o mesmo score/breakdown do badge
- `reportlab` ou `weasyprint` — verificar requirements.txt antes de iniciar
- Dados do resultado de busca devem ser passíveis de re-fetch por `result_id` (ou passados no body da request)

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| `result_id` não é persistido — dados do resultado só existem em memória/cache | Alta | Aceitar o resultado completo no body da request POST (não só o ID); cliente envia os dados | 
| Geração de PDF lenta (>5s) para PDFs complexos | Baixa | 1 página simples com texto — deve ser <2s com reportlab |
| `reportlab` não suporta UTF-8/caracteres especiais PT-BR adequadamente | Média | Verificar encoding no setup; usar fonte que suporte PT-BR (Helvetica ou embed TTF) |

---

## File List

- [ ] `backend/pdf_generator.py` — AC2, AC3, AC6: novo gerador de PDF
- [ ] `backend/routes/export.py` — AC4: novo endpoint POST /v1/export/pdf
- [ ] `backend/requirements.txt` — AC6: adicionar lib PDF se necessário
- [ ] `frontend/app/buscar/components/search-results/ResultCard.tsx` — AC1, AC7: botão + download
- [ ] `frontend/app/api/export/pdf/route.ts` — AC4: proxy para backend (novo)
- [ ] `backend/tests/test_pdf_generator.py` — AC8: testes de geração

---

## Dev Notes

- Design do PDF deve ser simples e limpo — não tentar replicar o design web
- Body da request: enviar o objeto completo do resultado (não apenas ID) para evitar re-fetch:
  ```json
  {
    "titulo": "...",
    "orgao": "...",
    "valor_estimado": 150000.00,
    "prazo": "2026-05-15",
    "modalidade": "Pregão Eletrônico",
    "viability_score": 78,
    "viability_breakdown": {...},
    "resumo_executivo": "...",
    "recomendacao": "..."
  }
  ```
- Download frontend: `const url = URL.createObjectURL(blob); a.click(); URL.revokeObjectURL(url)`
- Verificar `backend/routes/export_sheets.py` para padrão de como outros endpoints de export são implementados

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +0.5-1pp + viral B2B |
| 2026-04-12 | @po | GO — AC6 atualizado: reportlab==4.4.0 confirmado instalado. Usar reportlab.platypus. |
