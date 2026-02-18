# GTM-FIX-036: Copy ainda diz "15 dias" — deveria ser "10 dias"

**Priority:** P1 (informação incorreta exibida ao usuário)
**Effort:** XS (30 min)
**Origin:** Teste de produção manual 2026-02-18
**Status:** CONCLUÍDO
**Assignee:** @dev
**Tracks:** Frontend (1 AC), Tests (1 AC)

---

## Problem Statement

A mensagem na página de busca diz:
> "Buscando nos últimos **15** dias — somente licitações com prazo aberto"

Mas o período real de busca foi alterado para **10 dias** em GTM-FIX-031 (commit `c696200`). A copy do frontend ficou desatualizada.

### Onde aparece

Página `/buscar` → banner azul claro abaixo dos estados, visível quando status = "Abertas"

### Impacto

Usuário espera ver resultados de 15 dias mas recebe apenas 10. Pode pensar que está perdendo oportunidades dos dias 11-15.

---

## Acceptance Criteria

### Frontend

- [x] **AC1**: Alterar copy para "Buscando nos últimos **10** dias — somente licitações com prazo aberto" em `app/buscar/page.tsx` (ou no hook/componente que gera essa mensagem)

### Tests

- [x] **AC2**: Verificar que `useSearchFilters.ts` tem `DEFAULT_DAYS = 10` e que a copy reflete esse valor (idealmente usar a constante em vez de hardcode)

---

## Arquivos Exatos

| Arquivo | Linha | O que mudar |
|---------|-------|-------------|
| `frontend/app/buscar/components/SearchForm.tsx` | 491 | "últimos 15 dias" → "últimos 10 dias" |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | 208, 216 | Valor `-10` hardcoded (correto), mas sem constante nomeada |
| `frontend/__tests__/components/SearchForm.test.tsx` | 203, 358, 379, 392 | Assertions que mencionam "15 dias" |

## Technical Notes

- **NÃO existe** constante `DEFAULT_DAYS` em `useSearchFilters.ts` — o valor `10` está hardcoded em `addDays(getBrtDate(), -10)` nas linhas 208 e 216
- **Solução ideal (2 passos):**
  1. Criar `export const DEFAULT_SEARCH_DAYS = 10` em `useSearchFilters.ts`
  2. Usar essa constante tanto no cálculo de datas quanto na string de copy em `SearchForm.tsx`
- Isso elimina qualquer desync futuro entre período real e copy exibida
- Grep por "15 dias" no frontend para encontrar todas as instâncias residuais
- Os testes em `SearchForm.test.tsx` (linhas 203, 358, 379, 392) também fazem assertions em "15 dias" — atualizar junto
