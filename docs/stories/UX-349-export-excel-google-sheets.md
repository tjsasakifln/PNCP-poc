# UX-349 — Export Funcional: Botao Excel Visivel + Google Sheets 404

**Status:** completed
**Priority:** P1 — Feature prometida nao funciona
**Created:** 2026-02-22
**Completed:** 2026-02-22
**Origin:** Auditoria UX area logada (2026-02-22-ux-audit-area-logada.md)
**Dependencias:** CRIT-027 (resultados precisam carregar primeiro)
**Estimativa:** S

---

## Problema

1. **Botao Excel invisivel**: Mesmo quando resultados existem, o botao de download Excel nao aparece na interface. O componente existe no codigo (`SearchResults.tsx` L791-859) mas depende de `excel_status === 'ready'` que aparentemente nunca e atingido.

2. **Google Sheets → HTTP 404**: Ao tentar exportar para Google Sheets, o endpoint retorna 404.

### Impacto

- Export e funcionalidade core do plano pago
- Usuario que espera baixar planilha fica sem acao
- Feature prometida no pricing que nao funciona

---

## Solucao

### Criterios de Aceitacao

**Excel**
- [x] **AC1:** Botao "Baixar Excel" visivel assim que resultados sao exibidos
- [x] **AC2:** Se Excel em processamento (ARQ job): botao mostra "Gerando Excel..." com spinner
- [x] **AC3:** Se Excel pronto: botao ativo com contagem "Baixar Excel (X licitacoes)"
- [x] **AC4:** Se Excel falhou: botao mostra "Gerar novamente" (retry) — inclui timeout 60s de processing
- [x] **AC5:** Fallback: se ARQ nao disponivel, gerar Excel inline e disponibilizar

**Google Sheets**
- [x] **AC6:** Backend endpoint existe em `/api/export/google-sheets` (export_sheets.py)
- [x] **AC7:** Corrigido 404 — criado proxy route `frontend/app/api/export/google-sheets/route.ts`

**Testes**
- [x] **AC8:** Teste: botao Excel aparece quando ha resultados (T1: 4 tests)
- [x] **AC9:** Teste: estados do botao (processing/ready/failed) renderizam corretamente (T2-T6: 10 tests)
- [x] **AC10:** Zero regressoes (BE: 11 fail/4952 pass, FE: 40 fail/2337 pass — all pre-existing)

---

## Implementacao

### Root Cause

**Excel:** Quando ARQ/Redis disponivel, backend retorna `excel_status='processing'` e envia `excel_ready` via SSE. Se SSE falha (conexao cai, job falha), botao fica preso em "Gerando Excel..." para sempre. Estado 'failed' era botao disabled sem retry.

**Google Sheets:** Frontend chama `/api/export/google-sheets` mas nao existia proxy route Next.js — retornava 404. Backend endpoint funcional em `routes/export_sheets.py`.

### Changes

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/buscar/components/SearchResults.tsx` | Excel button: 3-state logic (processing→retry→active) com timeout 60s + data-testid |
| `frontend/app/buscar/hooks/useSearch.ts` | handleDownload: mostra erro quando download nao disponivel (antes: silencioso) |
| `frontend/app/api/export/google-sheets/route.ts` | **NEW**: Proxy route para backend Google Sheets export (fix 404) |
| `frontend/__tests__/excel-export-button.test.tsx` | **NEW**: 20 testes (T1-T9) cobrindo todos os estados do botao Excel |
| `docs/stories/UX-349-export-excel-google-sheets.md` | Story atualizada |

---

## Referencias

- Audit: C02, C03
- GTM-RESILIENCE-F01: ARQ Job Queue (implementacao do Excel job)
