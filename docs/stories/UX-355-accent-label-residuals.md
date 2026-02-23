# UX-355 — Acentuação e Labels: Resíduos da UX-353

**Severity:** P2/P3 — Important/Cosmetic
**Origin:** UX Production Audit 2026-02-23 (Bugs #6, #7)
**Parent:** UX-353
**Status:** [x] Completed

---

## Problema

Dois resíduos de acentuação/consistência que escaparam do UX-353:

### Bug 1 (P2): Mensagem de Erro sem Acento
A mensagem de erro na busca exibe "Erro ao buscar licitacoes" sem acento em "licitações".

**Local:** Alert box vermelha em `/buscar` quando a busca falha (HTTP 524).

### Bug 2 (P3): Inconsistência Sidebar vs Header em /mensagens
- Sidebar: "Suporte" (correto, alterado no UX-353)
- Header da página /mensagens: "Mensagens" (não atualizado)

## Acceptance Criteria

- [x] **AC1**: Mensagem de erro exibe "Erro ao buscar licitações" com acento cedilha
- [x] **AC2**: Header da página /mensagens exibe "Suporte" (consistente com sidebar)
- [x] **AC3**: Grep completo por "licitacoes" (sem acento) em todo o frontend — zero ocorrências em texto user-facing
- [x] **AC4**: Grep completo por inconsistências "Mensagens" vs "Suporte" — todas as referências user-facing usam "Suporte"
- [x] **AC5**: Teste existente atualizado para verificar acento
- [x] **AC6**: Zero regressão no baseline

## Arquivos Prováveis

### Bug 1 (accent)
- `frontend/hooks/useSearch.ts` — mensagem de erro default
- `frontend/app/buscar/components/error-messages.ts` — error message templates
- `frontend/app/api/buscar/route.ts` — proxy error messages

### Bug 2 (label)
- `frontend/app/mensagens/page.tsx` — page header title
- `frontend/app/mensagens/layout.tsx` — layout title (se existir)

## Estimativa

Correção trivial — 2 strings para alterar + teste.

## Referência

- Screenshot: `audit-13-saude-error.jpeg` (acento faltando)
- Audit doc: `docs/sessions/2026-02/2026-02-23-ux-production-audit.md`
