# TFIX-009: Corrigir null safety em BuscarHeader (saveSearchName.length)

**Status:** Pending
**Prioridade:** Alta
**Estimativa:** 30min
**Arquivos afetados:** 1 componente + 1 test file

## Problema

7 de 8 testes em `BuscarHeader.test.tsx` falham com `TypeError: Cannot read properties of undefined (reading 'length')` em `page.tsx:544`.

## Causa Raiz

A linha 544 de `page.tsx` acessa `search.saveSearchName.length` diretamente:

```tsx
<p className="text-xs text-ink-muted mt-1">{search.saveSearchName.length}/50 caracteres</p>
```

O teste de BuscarHeader renderiza a página inteira (`BuscarPage`) com mocks que não incluem `saveSearchName` no objeto `search` retornado pelo hook `useSearch`. Como `saveSearchName` é `undefined`, `.length` lança TypeError.

### Dois problemas:

1. **Componente não é null-safe**: deveria usar `(search.saveSearchName || '').length` ou optional chaining
2. **Teste com mock incompleto**: o mock do `useSearch` não inclui todos os campos do `UseSearchReturn`

## Testes que serão corrigidos

- `BuscarHeader.test.tsx`: 7 falhas (todos exceto "should show spinner during auth loading")

## Critérios de Aceitação

- [ ] AC1: `page.tsx` linha 544 usa null-safe access: `(search.saveSearchName ?? '').length`
- [ ] AC2: Mock de `useSearch` no teste inclui `saveSearchName: ''` e todos os campos obrigatórios
- [ ] AC3: 8/8 testes passam
- [ ] AC4: Sem regressão em buscar/page.tsx runtime

## Solução

1. **Componente** (`app/buscar/page.tsx` L544): Adicionar null safety:
   ```tsx
   {(search.saveSearchName ?? '').length}/50 caracteres
   ```

2. **Teste** (`BuscarHeader.test.tsx`): Adicionar `saveSearchName: ''` ao mock do useSearch, junto com quaisquer outros campos faltantes.

## Arquivos

- `frontend/app/buscar/page.tsx` — null safety em L544
- `frontend/__tests__/pages/BuscarHeader.test.tsx` — completar mock do useSearch
