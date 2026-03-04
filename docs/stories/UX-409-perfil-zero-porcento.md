# STORY-409: Perfil mostra 0% de completude quando faixa_valor_min=0

**Prioridade:** P2
**Esforço:** S
**Squad:** team-bidiq-frontend

## Contexto
A função `completenessCount()` na página de conta trata `faixa_valor_min=0` como falsy (porque `0` é falsy em JS), marcando o campo como "não preenchido" no indicador de completude do perfil. Um usuário que legitimamente configurou valor mínimo como R$ 0 (aceitando qualquer valor) vê seu perfil como incompleto.

## Problema (Causa Raiz)
- `frontend/app/conta/page.tsx:63-74`: `completenessCount()` usa `fields.filter(Boolean)`. O campo `faixa_valor_min` na linha 68 já usa `ctx.faixa_valor_min != null ? ctx.faixa_valor_min : null`, que corretamente trata `0` como válido.
- PORÉM: `fields.filter(Boolean)` na linha 73 descarta `0` porque `Boolean(0) === false`.
- Isso significa que mesmo com o check `!= null`, o valor `0` é incluído na array mas depois filtrado por `Boolean`.

## Critérios de Aceitação
- [ ] AC1: Substituir `fields.filter(Boolean)` por `fields.filter(f => f !== null && f !== undefined)` para preservar valores falsy válidos como `0`.
- [ ] AC2: `faixa_valor_min=0` deve contar como campo preenchido.
- [ ] AC3: `faixa_valor_min=null` deve contar como campo NÃO preenchido.
- [ ] AC4: `capacidade_funcionarios=0` deve contar como campo preenchido (mesma lógica).
- [ ] AC5: Indicador visual deve refletir corretamente "7/7 campos preenchidos" quando todos estão preenchidos (incluindo zeros).

## Arquivos Impactados
- `frontend/app/conta/page.tsx` — Fix em `completenessCount()`.

## Testes Necessários
- [ ] Teste que `completenessCount({ faixa_valor_min: 0, ... })` retorna count incluindo esse campo.
- [ ] Teste que `completenessCount({ faixa_valor_min: null, ... })` NÃO inclui esse campo.
- [ ] Teste que todos os campos preenchidos (incluindo zeros) retorna `TOTAL_PROFILE_FIELDS`.

## Notas Técnicas
- Bug clássico de JavaScript: `[0, null, undefined, "", 1].filter(Boolean)` retorna `[1]`. A correção é `filter(f => f !== null && f !== undefined)`.
