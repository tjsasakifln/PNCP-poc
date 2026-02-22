# TFIX-003: Atualizar signup-confirmation.test.tsx para formulário simplificado

**Status:** Pending
**Prioridade:** Alta
**Estimativa:** 1h
**Arquivos afetados:** 2 test files

## Problema

12 testes em `signup-confirmation.test.tsx` falham porque tentam interagir com campos que foram **removidos** do formulário de signup (Empresa, Setor de atuação, etc.).

Adicionalmente, `sector-sync.test.tsx` falha 1 teste porque tenta encontrar a constante `SECTORS` em `signup/page.tsx`, que não existe mais.

## Causa Raiz

A página de signup foi simplificada (GTM-FIX-037) para apenas 3 campos: Nome, Email, Senha. Os campos removidos foram: Empresa, Setor de atuação, Telefone, Consentimento, Confirmação de senha.

O teste `signup-confirmation.test.tsx` (helper `signupAndGetToConfirmation`) ainda tenta:
```typescript
const companyInput = screen.getByLabelText(/Empresa/i);         // REMOVIDO
const sectorSelect = screen.getByLabelText(/Setor de atuação/i); // REMOVIDO
```

O `SignupPage.test.tsx` já foi atualizado e passa corretamente (33/33).

O `sector-sync.test.tsx` tenta parsear `SECTORS` de `signup/page.tsx`, mas essa constante foi removida junto com o campo de setor.

## Testes que serão corrigidos

- `signup-confirmation.test.tsx`: 12 falhas → 0
- `sector-sync.test.tsx`: 1 falha (AC2: signup SECTORS)

## Critérios de Aceitação

- [ ] AC1: `signupAndGetToConfirmation()` helper atualizado para preencher apenas Nome, Email, Senha
- [ ] AC2: Todos 12 testes de `signup-confirmation.test.tsx` passam
- [ ] AC3: `sector-sync.test.tsx` AC2 atualizado ou removido (SECTORS não existe mais no signup)
- [ ] AC4: `SignupPage.test.tsx` continua passando (33/33)

## Solução

1. **`signup-confirmation.test.tsx`**: Atualizar `signupAndGetToConfirmation()` para:
   - Remover interação com `Empresa`, `Setor de atuação`
   - Preencher apenas `Nome completo`, email, senha
   - Ajustar seletores para o layout atual

2. **`sector-sync.test.tsx`**: Remover ou skip o teste AC2 ("signup SECTORS has backend sectors + outro") já que setores não fazem mais parte do signup.

## Arquivos

- `frontend/__tests__/auth/signup-confirmation.test.tsx` — atualizar helper
- `frontend/__tests__/sector-sync.test.tsx` — remover/skip teste AC2
