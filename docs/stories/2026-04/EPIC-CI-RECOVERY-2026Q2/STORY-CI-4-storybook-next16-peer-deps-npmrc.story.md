# STORY-CI-4 — Storybook 8.6 × Next.js 16 peer-dep conflict bloqueia `Frontend Tests`

**Epic:** EPIC-CI-RECOVERY-2026Q2  
**Sprint:** 2026-Q2-S3  
**Status:** Done  
**Priority:** P0 — Blocker (main CI + merge de PRs 6.x)  
**Effort:** XS (<30min)  
**Agents:** @dev, @devops  

---

## Contexto

Após o merge de `STORY-5.9 Storybook 8.6 setup` (commit `06092bd3`), o job `Frontend Tests` em `.github/workflows/tests.yml` passou a falhar no step "Install dependencies" com `npm error code ERESOLVE`:

```
npm error While resolving: @storybook/nextjs@8.6.18
npm error Found: next@16.2.3
npm error peer next@"^13.5.0 || ^14.0.0 || ^15.0.0" from @storybook/nextjs@8.6.18
```

`@storybook/nextjs@8.6.18` ainda não declara suporte a Next 16 em `peerDependencies`. O commit `ba1ef7fb` adicionou `--legacy-peer-deps` ao Dockerfile do frontend, mas **não** ao `tests.yml`, `frontend-tests.yml`, `e2e.yml`, `api-types-check.yml`, `chromatic.yml`, `dep-scan.yml`, `lighthouse.yml`, `pr-validation.yml`, `staging-deploy.yml` nem `sync-sectors.yml`.

Resultado: todo e qualquer push em `main` (e qualquer PR) vinha falhando a partir de `06092bd3`, **bloqueando o merge das 6.x stories** (Sprint 7 EPIC-TD-2026Q2).

O job `Backend Tests` também é cancelado como consequência (fail-fast do matrix).

---

## Acceptance Criteria

- [x] AC1: `frontend/.npmrc` criado com `legacy-peer-deps=true` — fix centralizado que afeta **todos** os workflows + dev local + Docker (sem necessidade de editar cada `.yml`).
- [x] AC2: `cd frontend && npm ci --dry-run` resolve sem erros — validado em 2026-04-16: `up to date in 2s, 356 packages are looking for funding`.
- [x] AC3: `npm audit --omit=dev --audit-level=high` continua retornando `found 0 vulnerabilities` (nenhum downgrade de Next foi necessário).
- [x] AC4: Sem mudanças em `package.json`, `package-lock.json` ou quaisquer dependências — apenas flag de resolver.

---

## Implementação

**Arquivo novo:** `frontend/.npmrc`

```
legacy-peer-deps=true
```

---

## Por que `.npmrc` e não `--legacy-peer-deps` em cada workflow

| Abordagem | Prós | Contras |
|---|---|---|
| `--legacy-peer-deps` em cada `npm ci` dos ~10 workflows | explícito por workflow | 10 arquivos alterados; fácil esquecer em novos workflows |
| **`frontend/.npmrc`** | 1 arquivo; afeta **tudo** (CI + local + Docker); padrão reconhecido pela comunidade npm | flag fica "invisível" no workflow YAML |
| Downgrade para Next 15.x | resolve peer-dep "legitimamente" | reintroduz vulnerabilidade GHSA-q4gf-8mx6-v5v3 (DoS HIGH) |
| Upgrade Storybook para versão com Next 16 | fix "próprio" | bump major não trivial; fora de escopo; Storybook 9.x ainda em release candidate |

`.npmrc` foi escolhido como **band-aid consciente** — tem custo de manutenção zero, é documentado, e pode ser removido quando Storybook 9.x estável suportar Next 16 nativamente.

---

## Verificação Local

```bash
cd frontend
cat .npmrc           # legacy-peer-deps=true
npm ci --dry-run     # up to date in 2s (resolve sem ERESOLVE)
npm audit --omit=dev --audit-level=high   # found 0 vulnerabilities
```

---

## File List

- `frontend/.npmrc` — novo arquivo, 1 linha

---

## Change Log

- **2026-04-16** — @dev: `.npmrc` criado para destravar `Frontend Tests` após merge de Storybook 8.6 em main; dry-run validado; `@devops` push direto para `main` via branch `fix/ci-destravamento-main-npm-peer-deps` (urgência: merge de 6.x bloqueado).
