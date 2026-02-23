# UX-354 — Histórico: Unicode Escape, Sector Slugs, English Errors

**Severity:** P2 — Important
**Origin:** UX Production Audit 2026-02-23 (Bugs #3, #4, #5)
**Parent:** UX-351, UX-353
**Status:** [x] Completed

---

## Problema

A página /historico apresenta 3 problemas de rendering que degradam a qualidade percebida:

### Bug 1: Unicode Escape no Header Bar
O título na barra de navegação exibe `Hist\u00f3rico` como texto literal em vez de "Histórico". O sidebar exibe corretamente, mas o header bar da página não.

### Bug 2: Nomes de Setor como Slugs
As entradas mostram slugs internos em vez de nomes legíveis:
- "vestuario" → deveria ser "Vestuário e Uniformes"
- "engenharia" → deveria ser "Engenharia, Projetos e Obras"

### Bug 3: Mensagens de Erro em Inglês
Entradas com status "Falhou" exibem "Server restart — retry recommended" em inglês.
UX-351 implementou `getUserFriendlyError()`, mas a mensagem do backend para server restart não está mapeada.

## Acceptance Criteria

- [x] **AC1**: Header bar da página exibe "Histórico" com acento correto (não unicode escape)
- [x] **AC2**: Nomes de setor no histórico usam o display name completo do setor (mapeamento slug → nome)
- [x] **AC3**: Todos os 15 setores mapeiam corretamente (vestuario → "Vestuário e Uniformes", etc.)
- [x] **AC4**: Erro "Server restart" exibe "O servidor reiniciou. Recomendamos tentar novamente."
- [x] **AC5**: Nenhuma mensagem de erro em inglês visível no histórico (audit todas as mensagens de erro possíveis)
- [x] **AC6**: Teste: render de entry com setor "vestuario" → exibe "Vestuário e Uniformes"
- [x] **AC7**: Teste: render de entry com error "Server restart" → exibe mensagem em PT-BR
- [x] **AC8**: Zero regressão no baseline

## Arquivos Prováveis

- `frontend/app/historico/page.tsx` — header title, entry rendering
- `frontend/app/buscar/components/error-messages.ts` — error message mapping
- `frontend/app/buscar/page.tsx` — SETORES_FALLBACK (slug → name mapping source)
- `backend/sectors.py` ou `sectors_data.yaml` — sector name canonical source
- `frontend/__tests__/historico/`

## Notas Técnicas

**Bug 1 (unicode):** Provável que o header use `JSON.parse()` ou template literal sem decoding. Verificar se o título vem de uma prop que passa por serialização JSON.

**Bug 2 (slugs):** O backend provavelmente salva o `setor` como slug na tabela de sessões. O frontend precisa de um mapa slug→displayName. Reutilizar o array de setores que já existe no dropdown da busca.

**Bug 3 (inglês):** Adicionar mapeamento em `getUserFriendlyError()` ou `ERROR_CODE_MESSAGES` para "Server restart" → mensagem PT-BR.

## Files Changed

- `frontend/app/historico/page.tsx` — Replaced all `\u00XX` unicode escapes with UTF-8 chars; added `SECTOR_NAMES` mapping (15 sectors) + `getSectorDisplayName()` helper; changed sector rendering from raw `s.sectors.join(", ")` to `s.sectors.map(getSectorDisplayName).join(", ")`; added `data-testid="sector-display"` for testing
- `frontend/lib/error-messages.ts` — Added 8 new English→PT-BR mappings: "Server restart", "retry recommended", "Connection reset", "connection refused", "Internal server error", "Pipeline failed", "All sources failed", "No results found"
- `frontend/__tests__/pages/HistoricoUX354.test.tsx` — NEW: 18 tests (AC1-AC8 coverage)
- `frontend/__tests__/lib/error-messages.test.ts` — Added 8 new tests for UX-354 English→PT-BR mappings
- `docs/stories/UX-354-historico-rendering-polish.md` — Marked all ACs completed

## Referência

- Screenshots: `audit-08-historico.jpeg`, `audit-09-historico-full.jpeg`
- Audit doc: `docs/sessions/2026-02/2026-02-23-ux-production-audit.md`
