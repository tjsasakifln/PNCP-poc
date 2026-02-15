# STORY-TD-003: Split Requirements + Cleanup

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 0: Verificacao e Quick Wins

## Prioridade
P0

## Estimativa
3h

## Descricao

Esta story resolve problemas de higiene do repositorio que afetam a experiencia de desenvolvimento e a clareza do codebase.

1. **Screenshots .png em git status (SYS-19, LOW, 1h)** -- 18 arquivos `.png` untracked no root do repositorio poluem o git status. Devem ser adicionados ao `.gitignore` para manter o working tree limpo.

2. **Deprecated migration file (SYS-23/DB-12, LOW, 0.5h)** -- `006b_DEPRECATED_...DUPLICATE.sql` no diretorio de migrations confunde compreensao do schema. Mover para `supabase/archive/` com README explicando a razao.

3. **Dead code: `format_resumo_html` (SYS-22, LOW, 1h)** -- Funcao de ~70 linhas em `backend/llm.py` linhas 232-300 nunca e chamada. Frontend renderiza resumo a partir de JSON, nao HTML. Remover dead code.

4. **`datetime.now()` sem timezone (SYS-18, MEDIUM, 0.5h)** -- `backend/excel.py` linha 227 e `backend/llm.py` linha 97 usam `datetime.now()` sem timezone. Em ambientes nao-UTC, timestamps ficam incorretos. Substituir por `datetime.now(timezone.utc)`.

## Itens de Debito Relacionados
- SYS-19 (LOW): Screenshot .png files em git status (18 untracked)
- SYS-23 (LOW): Deprecated migration file no diretorio
- DB-12 (LOW): Mesmo que SYS-23 (cross-reference)
- SYS-22 (LOW): `format_resumo_html` funcao nao usada (~70 linhas dead code)
- SYS-18 (MEDIUM): `datetime.now()` sem timezone em excel.py e llm.py

## Criterios de Aceite

### Gitignore
- [ ] `.gitignore` inclui pattern para `*.png` no root (ou patterns especificos para screenshots)
- [ ] `.gitignore` inclui `.playwright-mcp/` se nao incluido
- [ ] `git status` nao mostra .png files untracked

### Migration Cleanup
- [ ] `006b_DEPRECATED_...DUPLICATE.sql` movido para `supabase/archive/`
- [ ] `supabase/archive/README.md` criado (ou atualizado) explicando o conteudo
- [ ] Nenhuma migration ativa referencia o arquivo movido

### Dead Code
- [ ] `format_resumo_html` removida de `backend/llm.py`
- [ ] Nenhuma referencia a `format_resumo_html` em nenhum arquivo do projeto
- [ ] Testes existentes continuam passando

### Timezone Fix
- [ ] `backend/excel.py` usa `datetime.now(timezone.utc)` ou `datetime.now(tz=timezone.utc)`
- [ ] `backend/llm.py` usa `datetime.now(timezone.utc)` ou `datetime.now(tz=timezone.utc)`
- [ ] Import de `timezone` adicionado onde necessario

## Testes Requeridos

- Testes existentes de `excel.py` e `llm.py` devem continuar passando
- `grep -r "format_resumo_html" backend/` retorna zero matches
- `grep -r "datetime.now()" backend/` retorna zero matches sem timezone

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (paralelo com TD-001 e TD-002)

## Riscos
- Risco muito baixo. Todas as mudancas sao cleanup sem impacto funcional.
- Unica atencao: `datetime.now(timezone.utc)` pode alterar comportamento se algum codigo assumia timezone local. Verificar testes.

## Rollback Plan
- Nao aplicavel -- mudancas sao triviais e reversiveis via git revert.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + integracao)
- [ ] CI/CD green
- [ ] `git status` limpo (sem .png untracked)
- [ ] Deploy em staging verificado
