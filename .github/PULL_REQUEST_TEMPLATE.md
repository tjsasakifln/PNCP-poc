## Context

<!-- Por que esta mudança é necessária? Qual problema ela resolve? -->
<!-- P0/P1 não podem introduzir billing/SaaS/DataLake/crawler próprio (ADR-STRAT-001). -->

## Changes

<!-- Lista técnica de mudanças implementadas -->

-
-
-

## Testing Plan

<!-- Como esta mudança foi testada? -->

- [ ] Unit tests passing
- [ ] Integration tests passing (if applicable)
- [ ] Manual validation performed on: [describe scenario]
- [ ] No regressions detected

### Evidence

<!-- Screenshots, logs ou outputs que demonstram o funcionamento -->

```bash
# Exemplo de comando executado e resultado
```

## Risks & Rollback

<!-- O que pode dar errado? Como reverter se necessário? -->

**Risks:**
-

**Rollback plan:**
-

## Closes

<!-- Link para a issue que este PR resolve -->

Closes #

---

### Accessibility Checklist (WCAG AA)
- [ ] Keyboard navigation works for new/changed components
- [ ] ARIA labels added for screen readers (icon-only buttons, dynamic regions)
- [ ] Color contrast meets WCAG AA (4.5:1 text, 3:1 large text, 3:1 UI components)
- [ ] Forms have associated labels (htmlFor/id or aria-labelledby) and error messages (aria-describedby)
- [ ] Focus management works for modals/drawers (focus trap, focus return)
- [ ] axe-core CI gate passes (zero critical/serious violations)
- [ ] Information not conveyed by color alone

## Checklist (Não remover)

- [ ] Alinha a [ADR-STRAT-001](../docs/adr/ADR-STRAT-001-smartlic-confenge-inbound.md) (não reabre tese SaaS/billing/DataLake próprio)
- [ ] PR title follows Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)
- [ ] All acceptance criteria from the issue are met
- [ ] Code is formatted (backend: `ruff format`, frontend: `npm run lint`)
- [ ] No sensitive data (API keys, passwords) in code
- [ ] Documentation updated (if public APIs changed)
- [ ] Tests added/updated for new functionality
- [ ] CI checks are passing locally
- [ ] **Zero test failures** — backend (`pytest`) and frontend (`npm test`) exit code 0
- [ ] **API contract** — If this PR changes API endpoints, update the OpenAPI snapshot: delete `backend/tests/snapshots/openapi_schema.json`, re-run `pytest tests/test_openapi_schema.py`, commit the new snapshot

> **Zero-Failure Policy (CRIT-038):** Se testes falharem, corrija os testes — não adicione ao baseline.
> O único baseline aceitável é **0 failures**. PRs com testes falhando serão bloqueados pelo CI.

---

<!--
DICA: Use o comando `/review-pr <number>` após criar o PR para análise automatizada
-->
