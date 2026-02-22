# UX-349 — Export Funcional: Botao Excel Visivel + Google Sheets 404

**Status:** pending
**Priority:** P1 — Feature prometida nao funciona
**Created:** 2026-02-22
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
- [ ] **AC1:** Botao "Baixar Excel" visivel assim que resultados sao exibidos
- [ ] **AC2:** Se Excel em processamento (ARQ job): botao mostra "Gerando Excel..." com spinner
- [ ] **AC3:** Se Excel pronto: botao ativo com contagem "Baixar Excel (X licitacoes)"
- [ ] **AC4:** Se Excel falhou: botao mostra "Gerar novamente" (retry)
- [ ] **AC5:** Fallback: se ARQ nao disponivel, gerar Excel inline e disponibilizar

**Google Sheets**
- [ ] **AC6:** Se endpoint Google Sheets nao implementado, ESCONDER botao (nao mostrar feature quebrada)
- [ ] **AC7:** Se implementado, corrigir 404 e testar fluxo completo

**Testes**
- [ ] **AC8:** Teste: botao Excel aparece quando ha resultados
- [ ] **AC9:** Teste: estados do botao (processing/ready/failed) renderizam corretamente
- [ ] **AC10:** Zero regressoes

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/buscar/components/SearchResults.tsx` | Revisar condicional de exibicao do botao Excel |
| `frontend/hooks/useSearch.ts` | Verificar se `excel_status` esta sendo atualizado via SSE |
| `backend/job_queue.py` | Verificar se excel_generation_job completa corretamente |
| `frontend/app/buscar/components/SearchResults.tsx` | Esconder Google Sheets se 404 |

---

## Referencias

- Audit: C02, C03
- GTM-RESILIENCE-F01: ARQ Job Queue (implementacao do Excel job)
