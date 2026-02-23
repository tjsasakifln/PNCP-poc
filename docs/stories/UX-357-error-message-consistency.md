# UX-357 — Inconsistência nas Mensagens de Erro de Restart no Histórico

**Status:** Done
**Priority:** P3 — Cosmetic
**Severity:** Visual (todas em PT-BR, mas inconsistentes entre si)
**Created:** 2026-02-23
**Relates to:** UX-354 (Histórico Rendering Polish)

---

## Problema

O histórico exibe 3 variantes diferentes de mensagem para erros de restart do servidor:

| # | Mensagem | Status Badge | Onde observado |
|---|----------|-------------|----------------|
| 1 | "O servidor reiniciou. Tente novamente." | Falhou | /historico entry 23:13 |
| 2 | "O servidor reiniciou durante o processamento." | Tempo esgotado | /historico entry 23:12 |
| 3 | "O servidor reiniciou. Recomendamos tentar novamente." | Falhou | /historico entries 10:47, 10:52 |

### Análise

- Variante 1 e 3 são quase idênticas (diferem em "Tente" vs "Recomendamos tentar")
- Variante 2 é contextualmente diferente (timeout durante processamento)
- Todas em PT-BR (UX-354 AC5 passa), mas a experiência é inconsistente

### Causa Provável

O mapeamento `error → PT-BR message` em `error-messages.ts` tem múltiplas chaves para erros similares:

```
"Server restart — retry recommended" → variante 3
"server_restart" → variante 1 (?)
Timeout com restart → variante 2 (?)
```

## Acceptance Criteria

- [x] **AC1**: Unificar mensagens de restart para máximo 2 variantes: "falha" e "timeout"
- [x] **AC2**: Variante "falha": "O servidor reiniciou. Recomendamos tentar novamente." (mais educada)
- [x] **AC3**: Variante "timeout": "A busca excedeu o tempo limite. Recomendamos tentar novamente."
- [x] **AC4**: Auditar `error-messages.ts` para remover duplicatas de restart
- [x] **AC5**: Test: todos error codes de restart → max 2 mensagens distintas

## Files Envolvidos

- `frontend/lib/error-messages.ts` — Added "reiniciou" partial-match key (catches PT-BR variants)
- `frontend/app/historico/page.tsx` — timed_out always shows canonical timeout message
- `frontend/__tests__/lib/error-messages.test.ts` — 8 new tests (UX-357 section)
- `frontend/__tests__/pages/HistoricoUX357.test.tsx` — NEW: 9 tests for historico rendering
- `frontend/__tests__/pages/HistoricoUX354.test.tsx` — Updated timed_out test expectation
