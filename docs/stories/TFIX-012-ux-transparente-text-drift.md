# TFIX-012: Atualizar testes ux-transparente para textos atuais

**Status:** Pending
**Prioridade:** Média
**Estimativa:** 30min
**Arquivos afetados:** 1 test file

## Problema

1 teste não-EventSource em `ux-transparente.test.tsx` falha por texto desatualizado (os 2 outros falhas são cobertos por TFIX-002).

## Causa Raiz

### T6: SourcesUnavailable text drift
O teste busca `/fontes de dados governamentais/` mas o componente `SourcesUnavailable.tsx` renderiza `"Fontes temporariamente indisponíveis"` como título (h2). O texto "fontes de dados governamentais" não existe em nenhum lugar do componente.

**Contexto**: O componente foi reescrito em STORY-257B e os textos foram simplificados, mas o teste manteve a expectativa antiga.

## Testes que serão corrigidos

- `ux-transparente.test.tsx`: 1 falha (T6: "displays user-friendly message")
  - Os outros 2 falhas (T7 retry) são resolvidos por TFIX-002 (EventSource mock)

## Critérios de Aceitação

- [ ] AC1: Teste T6 atualizado para texto atual do componente
- [ ] AC2: 1/1 teste T6 passa (os 2 T7 dependem de TFIX-002)
- [ ] AC3: Demais 29 testes continuam passando

## Solução

Atualizar `ux-transparente.test.tsx` T6:
```typescript
// De:
expect(screen.getByText(/fontes de dados governamentais/)).toBeInTheDocument();
// Para:
expect(screen.getByText(/Fontes temporariamente indisponíveis/)).toBeInTheDocument();
```

E verificar se há outros textos no T6 que também divergiram.

## Arquivos

- `frontend/__tests__/story-257b/ux-transparente.test.tsx` — atualizar T6 expectativa
