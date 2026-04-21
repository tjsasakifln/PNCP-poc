# DEBT-CI-storybook: Storybook build falha em `.stories.tsx` TS loader

**Sprint:** 2026-Q2
**Effort:** 2-4h
**Priority:** MEDIUM (pre-existing blocker em PRs frontend)
**Agent:** @dev (Dex) + @ux-design-expert (para validar mudanças Storybook)
**Status:** Ready
**Owner:** @dev

## Context

Workflow `build` (Storybook) falha consistentemente em qualquer PR que toque `frontend/`, mesmo PRs docs-only no frontend. Observado em PRs #447, #452, #453, #455.

Symptom: Webpack/ts-loader no Storybook não parseia TypeScript syntax em `.stories.tsx`. Erro típico: parse error em type annotations ou JSX.

Blocker hoje resolvido pulando Lighthouse + storybook como "cluster pre-existing" no merge de revenue PRs.

## Scope

Diagnosticar e corrigir config de `ts-loader` / `babel-loader` / `swc-loader` no Storybook para aceitar syntax TS moderna.

## Acceptance Criteria

- [ ] AC1: `npm run build-storybook` passa local em clean checkout de main
- [ ] AC2: Workflow `Storybook Build` passa em PRs docs-only no frontend
- [ ] AC3: Workflow `Storybook Build` passa em PRs que adicionam novos `.stories.tsx`
- [ ] AC4: Chromatic Visual Regression (workflow downstream) continua passing
- [ ] AC5: Config documentada em `frontend/.storybook/README.md` ou similar

## Investigation Steps

1. Rodar `npm run build-storybook --verbose` local
2. Identificar exato erro de parsing
3. Verificar versão atual de `@storybook/*` packages em `frontend/package.json`
4. Verificar se `.storybook/main.ts` usa preset compatível com TS 5.9
5. Comparar config com boilerplate oficial Storybook 9+ (current codebase usa Storybook 9+)
6. Atualizar loader config OU atualizar dependencies se versão incompatível

## Dependencies

- **Related:** PR #452, #453, #455 — todos com `build` falhando pre-existing

## Tests Required

- [ ] Test: `npm run build-storybook` clean em main
- [ ] Test: PR fresh com 1 novo `.stories.tsx` → build passa em CI
- [ ] Test: Chromatic workflow continua verde

## Definition of Done

- [ ] Todos os ACs marcados
- [ ] PR mergeado em main
- [ ] 5 PRs consecutivos passam Storybook Build workflow

## Change Log

| Data | Autor | Evento |
|------|-------|--------|
| 2026-04-21 | @sm | Story created (Draft → Ready, user-approved) |
