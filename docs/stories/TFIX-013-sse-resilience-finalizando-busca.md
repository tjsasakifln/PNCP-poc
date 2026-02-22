# TFIX-013: Atualizar teste sse-resilience para mensagem SSE disconnect atual

**Status:** Pending
**Prioridade:** Baixa
**Estimativa:** 15min
**Arquivos afetados:** 1 test file

## Problema

1 teste em `gtm-fix-033-sse-resilience.test.tsx` falha buscando texto "Finalizando busca" que não existe mais no componente.

## Causa Raiz

O teste espera `screen.getByText(/Finalizando busca/i)` quando `sseDisconnected=true`, mas o componente `EnhancedLoadingProgress.tsx` (linha 471) renderiza:

```
"O progresso em tempo real foi interrompido. A busca continua no servidor e os resultados serão exibidos quando prontos."
```

O texto "Finalizando busca" foi substituído por uma mensagem mais informativa em CRIT-006, mas o teste não acompanhou a mudança.

## Testes que serão corrigidos

- `gtm-fix-033-sse-resilience.test.tsx`: 1 falha ("EnhancedLoadingProgress shows 'Finalizando busca...' on sseDisconnected")

## Critérios de Aceitação

- [ ] AC1: Teste atualizado para buscar o texto atual ("progresso em tempo real foi interrompido" ou similar)
- [ ] AC2: 7/7 testes passam

## Solução

```typescript
// De:
expect(screen.getByText(/Finalizando busca/i)).toBeTruthy();
// Para:
expect(screen.getByText(/progresso em tempo real foi interrompido/i)).toBeTruthy();
```

## Arquivos

- `frontend/__tests__/gtm-fix-033-sse-resilience.test.tsx` — atualizar expectativa L309
