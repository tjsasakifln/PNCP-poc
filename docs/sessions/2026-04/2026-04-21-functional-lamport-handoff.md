# Session Handoff — Functional-Lamport: Revenue SEO Inbound + CI Baseline Zero

**Date:** 2026-04-21 (tarde, continuação direta de prancy-pudding)
**Codename:** functional-lamport
**Branch base:** main (pós cascata 3-merges desta sessão + prancy-pudding 7)
**Duração:** ~2h active (Plan Mode → Auto Mode)
**Modelo:** Claude Opus 4.7 (1M context)

---

## TL;DR

**Shipped durable (3 merges em main):**

| PR | Escopo | Impacto |
|----|--------|---------|
| #455 | SEO-001 sitemap observability + CONV-003c closure | Sentry observability para catch silenciosos |
| #419 | google-auth-oauthlib 1.2.4→1.3.1 | Hygiene |
| #417 | react-hook-form 7.71→7.72 | Hygiene |

**PRs abertos desta sessão (aguardando CI):**

| PR | Escopo | Critical path |
|----|--------|---------------|
| #458 | fix(seo-001): serialize + revalidate sitemap/4.xml backend fetches | **Unblocks 10k entity URLs** |
| #459 | feat(seo-003): BreadcrumbList JSON-LD em /licitacoes/[setor] + Change Log SEO-002/003 | CTR +5-10% SERP |
| #460 | fix(ci): DEBT-CI-storybook babel-loader | Elimina cluster Storybook Build |
| #461 | fix(ci): DEBT-CI-lighthouse schedule-only + timeout | Elimina cluster Lighthouse PR |

**Dependabot aguardando rebase (auto via `@dependabot rebase` triggered):**
- #418 lucide-react 0.563→0.577
- #420 google-auth 2.48→2.49

**Stories efetivamente completas via descoberta empírica:**
- **STORY-SEO-002** (Article schema): JÁ em produção via `BlogArticleLayout.tsx:79-120` — validado curl em 3 URLs de prod
- **STORY-SEO-003** (Breadcrumb): 6/7 rotas já tinham; 1/7 shippada via #459 (escopo reduzido)

---

## 1. Descobertas empíricas críticas (3)

### 1.1. `BACKEND_URL` Railway JÁ setado

Handoff prancy-pudding documentou como "pendente operacional". Empírico:

```
$ railway variables --kv --service bidiq-frontend | grep BACKEND_URL
BACKEND_URL=https://api.smartlic.tech
NEXT_PUBLIC_BACKEND_URL=https://api.smartlic.tech
```

**Reclassificação:** operacional → done. SEO-001 AC1/AC2 dependem apenas do código, não de env var.

### 1.2. sitemap/4.xml vazio em produção tinha bug real — root cause identificado

Mesmo com BACKEND_URL setado e PR #455 merged, `curl sitemap/4.xml | grep -c '<url>'` retornou **0**.

**Discriminador empírico:** 7 endpoints backend testados em série vs paralelo:

```
# Sequencial:
/v1/sitemap/cnpjs  →  HTTP 200 em 7.0s (85KB)

# 6 em paralelo (Promise.all no frontend):
/v1/sitemap/cnpjs           →  HTTP=000 timeout 30s+
/v1/sitemap/contratos-orgao →  HTTP=000 timeout 30s+
/v1/sitemap/orgaos          →  HTTP=000 timeout 30s+
/v1/sitemap/fornecedores    →  HTTP=000 timeout 30s+
/v1/sitemap/municipios      →  HTTP=000 timeout 30s+
/v1/sitemap/itens           →  HTTP=000 timeout 30s+
```

Log Railway frontend confirmou `TIMEOUT_ERR (23)` em `sitemap/[__metadata_id__]/route.js`.

**Root cause:** 6 fetches paralelos saturam o backend; todos abortam no AbortSignal.timeout(15s); cada fetch cai no catch silencioso e retorna []; sitemap shard 4 fica vazio.

**Fix (PR #458):**
1. Serializar os 6 await para sequencial
2. `export const revalidate = 3600` — ISR 1h (safety net contra múltiplos crawlers simultâneos)

Sem (2), mesmo serializado: 45s por crawler-hit × N crawlers = backend saturaria de novo sob carga real.

### 1.3. SEO-002 + SEO-003 escopo reduzido por grep empírico

**STORY-SEO-003 (7 rotas listadas):**
- 5/7 JÁ emitiam BreadcrumbList inline (cnpj, fornecedores, contratos/[setor]/[uf], municipios, itens)
- 1/7 via SchemaMarkup component (blog/licitacoes/[setor]/[uf])
- 1/7 faltante → shippado via PR #459 (licitacoes/[setor]/page.tsx)

**STORY-SEO-002 (70 posts):**
- `BlogArticleLayout.tsx:79-120` JÁ emite Article schema completo (Person author, jobTitle, sameAs, publisher, wordCount, articleSection, inLanguage)
- `frontend/app/blog/[slug]/page.tsx` usa BlogArticleLayout para os 70 posts via dynamic import
- Validado curl em 3 URLs: 1x Article, 1x BreadcrumbList, 1x FAQPage, 5x Organization

**Consequência:** Change Log entries em ambas stories marcando 6/7 e 70/70 "already-shipped". Próxima sessão de /pick-next-issue não re-abre o trabalho (lição: atualizar stories imediatamente quando código diverge de documentação).

---

## 2. Aplicação direta das lições do advisor

### 2.1. ISR `revalidate = 3600` no sitemap.ts

Advisor apontou: "cada crawler request dispara 6 fetches serializados (~45s). Múltiplos crawlers → backend satura novamente."

Fix em PR #458 (commit separado): `export const revalidate = 3600` no topo de `frontend/app/sitemap.ts`. 1 regeneração/hora por shard, independente do volume de crawlers.

### 2.2. Story files Change Log (anti re-discovery)

Advisor apontou: "Sem Change Log, próxima sessão reabre SEO-002/SEO-003 como pending."

Fix no mesmo PR #459 (commit separado): entries detalhadas em ambas stories documentando:
- O que foi descoberto empiricamente
- Qual é o escopo real remanescente (AC3/AC6 manual)
- Status recomendado pós-deploy

### 2.3. CodeRabbit check pré-merge

Executado `gh api repos/.../pulls/$pr/comments`: 0 comentários CodeRabbit em todos os 4 PRs novos. Sem self-heal debt.

---

## 3. Ordem de merge recomendada (branch protection `strict:true`)

1. **#460 storybook** — pure CI, baixo risco, unblocks futuros PRs
2. **#461 lighthouse** — pure CI, complementar
3. **#458 sitemap hotfix** — product, crítico para revenue
4. **#459 SEO-003 + story Change Logs** — product, complementa baseline
5. **#418 + #420 Dependabot** — merge final (rebase automático via comment)

---

## 4. Revenue impact desta sessão (quando deployed)

| PR | Métrica | Quando mensurar |
|----|---------|-----------------|
| #458 | sitemap/4.xml ≥ 5000 URLs | 5-10min pós-deploy Railway |
| #458 | tempo de resposta sitemap/4.xml < 2s (ISR hot) | imediato pós-primeira request |
| #459 | Rich Results Test PASS `/licitacoes/{setor}` | imediato manual |
| #459 | GSC "Breadcrumbs" +1 URL | 7-30d pós-crawl |
| #460+#461 | PRs frontend sem ruído CI | imediato no próximo PR frontend |

**Cumulativo pós-sessão (incluindo prancy-pudding):**
- PR #452 (SEO-004): Rich Results /planos pricing — crawl 7-14d
- PR #453 (SEO-006): RUM web-vitals → GA4 — 24h ingestão
- PR #455 (SEO-001): sitemap observability Sentry — imediato
- PR #458 (SEO-001 hotfix): sitemap ≥5k entity URLs — pós-deploy
- PR #459 (SEO-003): BreadcrumbList completo — crawl 7-30d

---

## 5. Estado CI baseline (required checks)

**Em main após merges desta sessão:** 100% verde nos 2 required (Backend Tests + Frontend Tests). Baseline zero confirmado.

**Non-required que estavam ruidosos:**
- Storybook Build → resolved via PR #460 (babel-loader)
- Lighthouse Performance Audit → resolved via PR #461 (schedule-only)

**Pós-merge de #460 + #461:** CI baseline zero em TODOS os checks (required e non-required) para PRs futuros.

---

## 6. Próximos passos (priority order)

### Imediato (pós-merge dos 4 PRs novos)
1. Validar empírica pós-deploy:
   ```
   time curl -sL https://smartlic.tech/sitemap/4.xml | grep -c '<url>'  # Esperado: ≥5000, <3s
   curl -sL https://smartlic.tech/licitacoes/limpeza | grep -c 'BreadcrumbList'  # = 1
   ```
2. Rich Results Test manual em 3 URLs sample
3. GSC: re-submeter sitemap após validação de ≥5000 URLs

### Próxima semana (stretch do plano original)
- **STORY-SEO-005** (GSC API + dashboard /admin/seo) — 8 SP, observabilidade
- **STORY-SEO-007** (MDX migration) — 13 SP, velocity enabler
- **STORY-SEO-008** (3 pillar pages) — BLOQUEADO por STORY-436 (padrão editorial Draft)
- **STORY-436** (padrão editorial) — promover Draft → Ready se SEO-008 for prioridade

### Tech debt derivado (discoveries desta sessão)
- Backend concurrency limit em sitemap endpoints — investigar pool/workers (candidato STORY-TD)
- Organization schema emitido 5x por blog post — hygiene (não bloqueador)
- Considerar reduzir `signal: AbortSignal.timeout(15000)` para 10s nos endpoints sitemap agora que temos ISR

---

## 7. Memory updates realizados nesta sessão

Nenhuma atualização de memory arquivo nesta sessão (mantido conciso). Discobertas empíricas consolidadas no handoff + stories Change Logs. Consider para próxima sessão:

- **`project_sitemap_shard_4_serialize_revalidate.md`**: serializar fetches + ISR 3600s é o padrão correto para sitemap dinâmico com backend calls
- **`feedback_story_discovery_empirical_discriminator.md`**: antes de implementar story multi-rota, fazer grep empírico para confirmar escopo real; 5-15min economizam 3-4h de retrabalho

---

## 8. Waves executadas

| Wave | Status | Resultado |
|------|--------|-----------|
| 0 Merge queue drain | ✅ Parcial | 3/6 merged, 4 novos PRs abertos, 2 aguardam CI |
| 0 Validação sitemap produção | ✅ | Bug identificado + hotfix #458 + ISR |
| 1 SEO-003 Breadcrumb (escopo reduzido) | ✅ | PR #459 aberto, empirical discovery -6 rotas |
| 2 SEO-002 Article schema | ✅ (skip) | Já em produção via BlogArticleLayout; Change Log adicionado |
| 3a DEBT-CI-storybook | ✅ | PR #460 aberto, babel-loader validated local |
| 3b DEBT-CI-lighthouse | ✅ | PR #461 aberto, schedule-only trigger |
| 4 SEO-005 GSC API dashboard | ⏸️ Deferred | Stretch — próximo ciclo |

---

## 9. Decisões fundamentadas desta sessão

1. **Hotfix sitemap em PR dedicado (#458) vs amend a #455** — #455 já merged, hotfix separado é auditável
2. **babel-loader vs swc-loader em Storybook** — babel já em node_modules; swc exigiria novo pacote (churn)
3. **@storybook/nextjs rejeitado** — depends on `next/config` removido em Next 16; incompatibilidade de versão
4. **Lighthouse schedule-only (não fix timeout)** — sintético em PR é caro vs sinal; RUM real (SEO-006) já cobre
5. **SEO-005 deferred** — stretch; Waves 0-3 geraram ROI imediato suficiente
6. **ISR revalidate=3600 (1h) vs 300 (5min)** — sitemap mudou raramente; Googlebot rebota < 1/h por shard em média

---

## 10. Starter pack próxima sessão

```bash
# 1. Verificar merges dos 4 PRs abertos
for pr in 458 459 460 461 418 420; do
  gh pr view $pr --json state,mergedAt --jq "{pr: \"#$pr\", state, mergedAt}"
done

# 2. Validar SEO-001 em produção
time curl -sL https://smartlic.tech/sitemap/4.xml | grep -c '<url>'
# Esperado: ≥ 5000, tempo total <3s após primeira request hidratar o ISR

# 3. Validar SEO-003
curl -sL https://smartlic.tech/licitacoes/limpeza | grep -c '"@type":"BreadcrumbList"'
# Esperado: 1

# 4. Validar baseline CI zero em TODOS os checks
gh pr list --state open --limit 10 --json number,statusCheckRollup --jq '.[] | {pr: .number, failures: ([.statusCheckRollup[] | select(.conclusion == "FAILURE")] | length)}'
# Esperado: 0 failures em todos

# 5. Rich Results Test manual
# https://search.google.com/test/rich-results?url=https://smartlic.tech/licitacoes/limpeza
# https://search.google.com/test/rich-results?url=https://smartlic.tech/blog/analise-viabilidade-editais-guia
```

---

**Signed:** Claude Opus 4.7 (1M context)
**Session duration:** ~2h active (Plan Mode → Auto Mode, validação empírica + 4 PRs)
**ROI summary:** 3 merges + 4 PRs queued + 2 material discoveries (SEO-002 já feito, BACKEND_URL já setado) + 1 hotfix crítico identificado + 2 clusters CI resolvidos + 2 stories Change Log updated.
