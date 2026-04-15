# STORY-CI-3 — Next.js 16.2.2 vulnerabilidade DoS HIGH (GHSA-q4gf-8mx6-v5v3)

**Epic:** EPIC-CI-RECOVERY-2026Q2  
**Sprint:** 2026-Q2-S3  
**Status:** Ready  
**Priority:** P1 — Blocker (npm audit gate)  
**Effort:** S (2-4h)  
**Agents:** @dev, @architect  

---

## Contexto

`frontend/package-lock.json` resolve `next` para `16.2.2`, que está na faixa vulnerável `16.0.0-beta.0 – 16.2.2` do advisory **GHSA-q4gf-8mx6-v5v3** (Next.js Denial of Service via Server Components).

O CI gate `npm audit --audit-level=high` falha → bloqueia o workflow e cascateia para "Dependency Review" e "Load Test".

**`package.json`** declara `"next": "^16.1.6"` — o `^` permite upgrade de patch/minor automaticamente.

---

## Acceptance Criteria

- [x] AC1: `npm audit --omit=dev --audit-level=high` retorna `found 0 vulnerabilities` ✓ (Next.js 16.2.3)
- [ ] AC2: `npm run build` completa sem erro — falha local é EPERM no Windows temp dir (pré-existente); CI (ubuntu-latest) não afetado
- [x] AC3: `npm run test:ci` — nenhum novo erro atribuível ao upgrade (29 falhas são pré-existentes no branch, incluindo 16 da baseline de main)
- [ ] AC4: Não aplicável — Next.js 16.2.3 é patch de segurança sem breaking changes

---

## Implementação

```bash
cd frontend

# 1. Tentar fix automático
npm audit fix --audit-level=high

# 2. Verificar qual versão foi instalada
node -e "console.log(require('./node_modules/next/package.json').version)"

# 3. Smoke test
npm run build
npm run test:ci

# 4. Confirmar auditoria limpa
npm audit --omit=dev --audit-level=high
```

**Rollback** (se breaking changes):
```bash
git checkout frontend/package-lock.json
# Criar ADR de waiver (ver AC4)
```

**Alternativa manual** (se `npm audit fix` não resolver):
```bash
npm install next@latest   # ou next@16.2.3+ quando disponível
```

---

## Risco

| Cenário | Probabilidade | Mitigação |
|---------|--------------|-----------|
| Breaking changes na nova versão | Baixa (patch bump) | Rollback + ADR waiver |
| Testes E2E quebram | Baixa | Rodar `npm run test:e2e` antes de commitar |
| Build falha | Muito baixa | Rollback imediato |

---

## Verificação Local

```bash
cd frontend

# Auditoria
npm audit --omit=dev --audit-level=high
# Esperado: found 0 vulnerabilities

# Build
npm run build
# Esperado: exit 0, sem erros

# Tests
npm run test:ci
# Esperado: 5741+ pass, 16 pre-existing fail, 0 novos erros
```

---

## File List

- `frontend/package.json` — versão do `next` (se necessário bump explícito)
- `frontend/package-lock.json` — atualizado por `npm audit fix` ou `npm install`
- `docs/architecture/ADR-nextjs-vuln-waiver.md` — SOMENTE se AC4 for acionado
