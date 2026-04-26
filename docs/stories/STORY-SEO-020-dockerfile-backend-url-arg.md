# STORY-SEO-020: Dockerfile build-time `BACKEND_URL` ARG (sitemap fix)

## Status

Approved

## Story

**As a** crawler do Google buscando indexar `https://smartlic.tech/sitemap/4.xml`,
**I want** que o sitemap seja gerado com URLs reais durante o build do frontend (não fallback localhost),
**so that** páginas programmatic (cnpj, orgaos, municipios, fornecedores, contratos-orgao) sejam descobertas e indexadas — destravando 3x tráfego.

## Acceptance Criteria

1. `frontend/Dockerfile` declara `ARG BACKEND_URL` na seção de ARGs (logo após `NEXT_PUBLIC_BACKEND_URL`).
2. `BACKEND_URL` é convertido em `ENV BACKEND_URL=$BACKEND_URL` na seção de ENVs do estágio builder.
3. Build args do Railway service `bidiq-frontend` incluem `BACKEND_URL=https://api.smartlic.tech` (verificar via `railway variables --service bidiq-frontend --kv | grep BACKEND_URL`).
4. Build log do próximo deploy mostra fetches contra `https://api.smartlic.tech/v1/sitemap/*` (não `localhost:8000`).
5. `curl -I https://smartlic.tech/sitemap/4.xml` retorna `200` com `Content-Length` >5kB (vs 0 atualmente).
6. `curl https://smartlic.tech/sitemap/4.xml | grep -c "<loc>"` retorna ≥1000 URLs após próximo deploy.
7. Smoke-test em staging confirma comportamento antes do deploy a prod.

## Tasks / Subtasks

- [ ] Task 1 — Editar Dockerfile (AC: 1, 2)
  - [ ] Adicionar `ARG BACKEND_URL` após linha 68 (entre ARGs `NEXT_PUBLIC_*`)
  - [ ] Adicionar `ENV BACKEND_URL=$BACKEND_URL` na seção ENV (linha 71+)
- [ ] Task 2 — Configurar Railway build arg (AC: 3)
  - [ ] @devops adiciona `BACKEND_URL=https://api.smartlic.tech` nas vars do service `bidiq-frontend`
  - [ ] Confirmar via `railway variables --service bidiq-frontend --kv | grep BACKEND_URL`
- [ ] Task 3 — Validação build-time (AC: 4)
  - [ ] Forçar rebuild (cachebust em Dockerfile ou commit trivial)
  - [ ] Inspecionar build log no Railway: confirmar fetches a `api.smartlic.tech`
- [ ] Task 4 — Validação runtime (AC: 5, 6)
  - [ ] `curl -I` em todos `/sitemap/*.xml`
  - [ ] Contar `<loc>` em sitemap-4.xml
- [ ] Task 5 — Smoke staging (AC: 7)
  - [ ] Validar fluxo completo em staging primeiro

## Dev Notes

**Plano:** Wave 2, story 2 (CRITICAL — bloqueia stories 3-6 de SEO).

**Audit evidence:**
- `frontend/Dockerfile:44-68` declara `ARG NEXT_PUBLIC_BACKEND_URL` mas **não** `ARG BACKEND_URL`
- `frontend/app/sitemap.ts:22` faz fallback `process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'`
- Resultado: build-time fetches em sitemap.ts caem em `localhost:8000` → todas RPC retornam vazio → sitemap-4.xml com 0 URLs em prod

**Memória relevante:** `reference_frontend_dockerfile_backend_url_gap.md` (2026-04-24) já documentou o gap.

**Memória adicional:** `feedback_sen_fe_001_recidiva_sitemap.md` — após fix, fazer grep global por outros call sites com fallback similar (`process.env.BACKEND_URL ||`) para garantir que não há recidiva.

**Files mapeados:**
- `frontend/Dockerfile` (edit)
- `frontend/app/sitemap.ts` (validação, sem edit)

### Testing

- Manual: build local com `--build-arg BACKEND_URL=https://api.smartlic.tech` e inspecionar `.next/server/app/sitemap*.js`
- Smoke prod: `curl -I https://smartlic.tech/sitemap/{0,1,2,3,4,5}.xml` todos 200 com Content-Length >0

## Dependencies

- **Bloqueia:** STORY-SEO-021, STORY-SEO-022, STORY-SEO-023, STORY-SEO-024 (sitemap quebrado mascara fixes SEO)
- **Bloqueado por:** nenhum
- **Risco:** alto blast radius (rebuild frontend); coordenar window com @devops

## Owners

- Primary: @devops (Dockerfile + Railway vars)
- Quality: @qa (smoke prod)
- Consult: @architect (se múltiplos call sites precisam refator)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm baseado em plano de crescimento | @sm (River) |
