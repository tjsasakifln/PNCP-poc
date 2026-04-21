# DEBT-CI-lighthouse: Lighthouse Performance Audit hang 6-8min before timeout

**Sprint:** 2026-Q2
**Effort:** 2-3h
**Priority:** MEDIUM (não-bloqueador, mas gasta CI minutes + falso negativo)
**Agent:** @dev (Dex) + @devops (Gage)
**Status:** Ready
**Owner:** @dev

## Context

Workflow `Lighthouse Performance Audit` roda 6-8 minutos antes de timeout em cada PR. Falha final reportada como "failure" mas é timeout de tool — não performance regression real.

Observado em PRs #447, #452, #453, #455. Gasta ~30 min de CI minutes por PR contra nenhum sinal útil.

Sessão prancy-pudding 2026-04-21 documentou como cluster pre-existing; mergear SEO PRs via `--admin` deixou o débito acumulado.

## Scope

Diagnosticar timeout e corrigir — OU reduzir frequência do workflow (não rodar em todo push, apenas em main ou scheduled).

## Acceptance Criteria

- [ ] AC1: Workflow `Lighthouse Performance Audit` completa em < 3 min em 95% dos runs
- [ ] AC2: Se timeout ocorrer: falha com erro específico ("Chrome launch timed out"), não silent hang
- [ ] AC3: Workflow tem um `timeout-minutes: 5` explicito para fail-fast
- [ ] AC4: Thresholds de performance documentados (LCP, INP, CLS targets)
- [ ] AC5 (alternativo): Se consertar for > 1h custo, mover para schedule (weekly) em main apenas

## Investigation Steps

1. Ler `.github/workflows/lighthouse.yml` — entender setup atual
2. Verificar versão `treosh/lighthouse-ci-action` ou similar em uso
3. Rodar Lighthouse local contra staging/prod para estabelecer baseline de duração
4. Comparar com GitHub Actions runner (ubuntu-latest) specs
5. Diagnose: Chrome headless hang? Network throttle issue? Storybook download?
6. Patch timeout config ou restructurar trigger

## Fix Alternatives

| Opção | Prós | Contras |
|-------|------|---------|
| Fix tool hang (root cause) | Workflow útil volta a funcionar | Pode levar 2-3h investigação |
| Mover para `schedule` weekly + main-only | Economiza CI minutes imediatamente | Perde signal em PRs até main |
| Substituir por PageSpeed Insights API | Mais confiável, menos local tooling | Outra dependency externa |
| Desabilitar temporariamente | Zero custo | Perde visibility total até fix |

**Recomendação:** Opção 2 (mover para schedule main-only). Combina com STORY-SEO-006 (web-vitals RUM) que dá sinal em produção real.

## Dependencies

- **Related:** STORY-SEO-006 (web-vitals RUM) — pode substituir Lighthouse CI como sinal primary
- **Affected PRs:** #452, #453, #455 passam `--admin` porque Lighthouse falso-negativo

## Tests Required

- [ ] Test: 5 PRs consecutivos não-críticos passam (ou são skipados corretamente)
- [ ] Test: Scheduled runs em main retornam dados reais (sem timeout)

## Definition of Done

- [ ] Todos os ACs marcados
- [ ] PR mergeado em main
- [ ] 7 dias sem timeout-failure em Lighthouse workflow

## Change Log

| Data | Autor | Evento |
|------|-------|--------|
| 2026-04-21 | @sm | Story created (Draft → Ready, user-approved) |
