# UX-357 — Inconsistência nas Mensagens de Erro de Restart no Histórico

**Status:** Pending
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

- [ ] **AC1**: Unificar mensagens de restart para máximo 2 variantes: "falha" e "timeout"
- [ ] **AC2**: Variante "falha": "O servidor reiniciou. Recomendamos tentar novamente." (mais educada)
- [ ] **AC3**: Variante "timeout": "A busca excedeu o tempo limite. Recomendamos tentar novamente."
- [ ] **AC4**: Auditar `error-messages.ts` para remover duplicatas de restart
- [ ] **AC5**: Test: todos error codes de restart → max 2 mensagens distintas

## Files Envolvidos

- `frontend/app/buscar/utils/error-messages.ts` — Mapeamento error→mensagem
- `frontend/app/historico/page.tsx` — Rendering de mensagens de erro
