# TFIX-011: Corrigir testes operational-state (CoverageBar props + FreshnessIndicator text)

**Status:** Pending
**Prioridade:** Média
**Estimativa:** 1h
**Arquivos afetados:** 1 test file + possivelmente 1 componente

## Problema

4 testes em `operational-state.test.tsx` falham por causas distintas mas relacionadas.

## Causa Raiz

### Problema 1: FreshnessIndicator text matching (1 falha)
O teste espera `screen.getByText("agora")` (match exato), mas o componente renderiza `"Dados de agora"`.

`getByText("agora")` faz match exato por padrão — não encontra "Dados de agora".

**Correção**: Usar `screen.getByText(/agora/)` (regex) ou `screen.getByText("Dados de agora")`.

### Problema 2: CoverageBar recebe coverageMetadata undefined (3 falhas)
Os 3 testes do CoverageBar falham com:
```
TypeError: Cannot destructure property 'ufs_requested' of 'coverageMetadata' as it is undefined
```

O componente `CoverageBar.tsx` (linha 35) faz:
```tsx
const { ufs_requested, ufs_processed, ufs_failed, coverage_pct } = coverageMetadata;
```

Sem null-check. Os testes passam `coverageMetadata` implicitamente (via props do OperationalStateBanner) ou diretamente, mas o valor chega como `undefined`.

**Dois problemas:**
1. Componente CoverageBar não faz null-check antes do destructure
2. Testes passam props incompletas

## Testes que serão corrigidos

- `operational-state.test.tsx`: 4 falhas
  - `shows FreshnessIndicator when timestamp provided`
  - `AC17: 5 OK + 2 error -> 7 segments, text '71% de cobertura'`
  - `renders tooltip with UF name and status`
  - `all UFs OK -> all segments green`

## Critérios de Aceitação

- [ ] AC1: FreshnessIndicator test usa regex ou texto exato correto
- [ ] AC2: CoverageBar.tsx tem null guard: `if (!coverageMetadata) return null`
- [ ] AC3: Testes de CoverageBar passam `coverageMetadata` com todas as propriedades necessárias
- [ ] AC4: 9/9 testes passam
- [ ] AC5: Sem regressão no OperationalStateBanner em runtime

## Solução

1. **CoverageBar.tsx** L35: Adicionar guard:
   ```tsx
   if (!coverageMetadata) return null;
   const { ufs_requested, ufs_processed, ufs_failed, coverage_pct } = coverageMetadata;
   ```

2. **operational-state.test.tsx**:
   - FreshnessIndicator: `expect(screen.getByText(/agora/)).toBeInTheDocument()`
   - CoverageBar: Passar `coverageMetadata` completo nos testes:
     ```tsx
     <CoverageBar coverageMetadata={{
       ufs_requested: ['SP','RJ','MG','BA','RS','SC','PR'],
       ufs_processed: ['SP','RJ','MG','BA','RS'],
       ufs_failed: ['SC','PR'],
       coverage_pct: 71,
     }} />
     ```

## Arquivos

- `frontend/app/buscar/components/CoverageBar.tsx` — null guard
- `frontend/__tests__/buscar/operational-state.test.tsx` — corrigir props e seletores
