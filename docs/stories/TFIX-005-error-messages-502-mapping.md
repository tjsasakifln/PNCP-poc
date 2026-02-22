# TFIX-005: Atualizar teste de mapeamento 502 em error-messages

**Status:** Pending
**Prioridade:** Baixa
**Estimativa:** 10min
**Arquivos afetados:** 1 test file

## Problema

1 teste falha em `error-messages.test.ts` — o mapeamento de erro 502 foi atualizado no código mas o teste ainda espera a mensagem antiga.

## Causa Raiz

A mensagem de erro 502 foi generalizada de PNCP-específica para genérica:

| | Mensagem |
|---|---|
| **Teste espera** | `"O portal PNCP está temporariamente indisponível. Tente novamente em instantes."` |
| **Código retorna** | `"O servidor está temporariamente indisponível. Tente novamente em instantes."` |

A mudança no `error-messages.ts` foi intencional (502 pode vir de qualquer fonte, não só PNCP), mas o teste não foi atualizado.

## Testes que serão corrigidos

- `error-messages.test.ts`: 1 falha ("should map 502 errors") → 61/61 passam

## Critérios de Aceitação

- [ ] AC1: Teste `should map 502 errors` atualizado para mensagem genérica
- [ ] AC2: 61/61 testes passam

## Solução

Editar `__tests__/lib/error-messages.test.ts` linha 60:
```typescript
// De:
expect(getUserFriendlyError('502')).toBe('O portal PNCP está temporariamente indisponível...');
// Para:
expect(getUserFriendlyError('502')).toBe('O servidor está temporariamente indisponível. Tente novamente em instantes.');
```

## Arquivos

- `frontend/__tests__/lib/error-messages.test.ts` — atualizar expectativa linha 60
