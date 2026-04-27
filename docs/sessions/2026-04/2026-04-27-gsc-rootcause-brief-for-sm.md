# GSC Root-Cause Brief — Brief para SM escrever stories

**Data:** 2026-04-27
**Autor:** Claude (sessão `session/2026-04-26-keen-sutton-trial-audit` — branch herdada do trial-audit; brief é GSC root-cause, não trial-audit. Considerar fork/rename antes de push.)
**Método:** Inspeção GSC via Playwright + validação empírica (curl burst 2x + Sentry API) + grep código + leitura stories prévias
**Propriedade GSC:** `sc-domain:smartlic.tech`
**Janela GSC:** 28d (28/03–25/04/2026); última atualização Indexação 23/04/2026
**Arquivos brutos coletados:** `/mnt/d/pncp-poc/gsc-{404,noindex,5xx,robots}-urls.txt`, `gsc-perf-{queries,pages}-28d.txt`

---

## ⚠️ P0 — INCIDENTE VIVO + EM CURSO HÁ 5 DIAS (validado via Sentry)

**Backend `api.smartlic.tech` está saturado/inalcançável em 2026-04-27 (tested 11:47–12:16 UTC, 2 bursts 30s apart).**

### Validação 1: curl burst (10/10 timeouts em 8s, 2 rounds, **inclusive `/buscar` user-facing**)

| Endpoint | Round 1 | Round 2 |
|----------|---------|---------|
| `GET /` | timeout 8s | timeout 8s |
| `GET /health` | timeout 8s | timeout 8s |
| `GET /v1/sitemap/cnpjs` | timeout 8s | timeout 8s |
| `GET /buscar?q=teste&uf=SP` | **timeout 8s** | **timeout 8s** |
| `GET /v1/empresa/{cnpj}/perfil-b2g` | timeout 8s | timeout 8s |

**Não é apenas SEO** — `/buscar` (feature principal usuário) também trava. Outage abrange backend inteiro.

### Validação 2: Sentry (org=confenge, proj=smartlic-backend, statsPeriod=24h)

**800 eventos em 24h**, distribuição com pico noturno 02–09 UTC (~23h-06h BRT) — picos 101 evt/hora:

```
00:00 UTC  35 events
01:00      36
02:00     101 (pico)
03:00      71
04:00      67
05:00      62
06:00      50
07:00      10
08:00      64
09:00      85
10:00      56
11:00      51
```

**Top issues (24h, ordenado por frequência):**

| Count | First/Last seen | Title |
|-------|-----------------|-------|
| **713** | desde 22-abr 22:34 | `Health incident: System status changed to degraded. Affected: pncp` ← **alerta sem resolução há 5 dias** |
| 263 | 21-abr | `slow_request: GET /v1/orgao/{cnpj}/stats (692.6s)` — query DB hung 11 min |
| 153 | 21-abr | `slow_request: GET /v1/empresa/{cnpj}/perfil-b2g (160.9s)` |
| 120 | 22-abr | `[Itens] price_data query falhou: 'canceling statement due to ...'` (DB statement_timeout) |
| 61 | 21-abr | `slow_request: GET /v1/fornecedores/{cnpj}/profile (148.2s)` |
| 51 | 21-abr | `slow_request: GET /health (160.9s)` ← health também 2.7 min |
| **48** | 20-abr | `orgao_stats DB query failed: ConnectionTerminated error_code:1` ← **DB connection pool dropping** |
| 47 | 22-abr | `slow_request: GET /v1/sitemap/contratos-orgao-indexable (318.3s)` ← raiz `SEN-BE-005` |
| 43 | 10-abr | `GET /v1/empresa/{cnpj}/perfil-b2g -> ERROR (15031ms)` |
| 40 | 22-abr | `slow_request: GET /v1/sitemap/orgaos (1682.7s)` ← **28 min** |
| 39 | 22-abr | `slow_request: GET /v1/sitemap/itens (1682.7s)` |
| 39 | 22-abr | `slow_request: GET /v1/sitemap/fornecedores-cnpj (1682.7s)` |
| 39 | 22-abr | `slow_request: GET /v1/sitemap/cnpjs (1680.8s)` |
| 37 | 21-abr | `slow_request: GET /v1/sitemap/municipios (1427.5s)` |
| 36 | 21-abr | `slow_request: GET /v1/me (160.9s)` |

### Root cause provável (alta confiança)

**DB connection pool exhaustion + queries DB hung sem timeout / com timeout exagerado.** Padrão consistente:
- ConnectionTerminated em DB (48 evt)
- "canceling statement" (server-side timeout dispara) em itens
- Sitemap endpoints rodando 28 min (1680s) — sem `statement_timeout` agressivo
- Cascata para `/health` e `/v1/me` (compartilham pool)

Combinado com:
- 1 worker Railway Hobby (memory `reference_railway_hobby_plan_actual.md`)
- 2M+ rows em `pncp_supplier_contracts`
- Crescimento de uso (build SSG hammers — memory `feedback_build_hammers_backend_cascade.md`)

### Triagem imediata @devops (antes de SM escrever)

1. Railway logs últimas 6h — procurar OOM kills, worker restarts
2. Supabase DB stats — `pg_stat_activity` para queries longas, `pg_stat_database` para conn count
3. Reciclar pool / restart workers como mitigação curta
4. Validar `statement_timeout` config no PostgREST/Supabase

---

## 1. Sumário GSC (overview)

| Métrica | Valor | Comparativo |
|---------|-------|------------|
| Cliques 28d | **145** | +15% vs baseline 24-abr (126) |
| Impressões 28d | **11.000** | +11% vs 9.9k |
| CTR médio | **1,3%** | igual |
| Posição média | **7,1** | igual |
| Páginas indexadas | **7.794** | (snapshot 25-abr; descoberta orgânica > sitemap) |
| Páginas NÃO indexadas | **4.718** | 7 motivos — ver §3 |
| HTTPS válidas | 19 / 0 inválidas | OK |
| CWV (mobile + desktop) | **Sem dados 90d** | Tráfego abaixo CrUX threshold (não actionable em engenharia) |
| Mensagens GSC não lidas | 18 | Não acessível via DOM scrape (lazy panel); duplica alertas das outras seções |

---

## 2. Sitemap status (Indexação > Sitemaps)

**Submetido:** `https://smartlic.tech/sitemap.xml` (índice de sitemaps)
**Última leitura GSC:** 26/04/2026 — **Status: Processado, mas 0 sitemaps lidos / 0 URLs descobertas** (pendente reprocessamento)

**Conteúdo real em produção (validado via curl `User-Agent: Googlebot`):**

| Sitemap | HTTP | Bytes | `<url>` count | First entry |
|---------|------|-------|---------------|-------------|
| `/sitemap.xml` (índice) | 200 | 461 | 5 `<sitemap>` entries | OK |
| `/sitemap/0.xml` | 200 | 6.779 | **42** | `https://smartlic.tech` (core) |
| `/sitemap/1.xml` | 200 | 10.550 | **60** | `/licitacoes/vestuario` (categorias) |
| `/sitemap/2.xml` | 200 | 140.645 | **810** | `/contratos/vestuario/ac` (contratos × UF) |
| `/sitemap/3.xml` | 200 | 59.937 | **327** | `/blog/...` (blog/landing) |
| `/sitemap/4.xml` | 200 | **110** | **0** | (vazio) — entity programmatic |

**Total real publicado: 1.239 URLs** versus **7.794 indexadas** → 84% das páginas indexadas vieram de descoberta orgânica (links/crawl), não do sitemap.

**Story prévia já tratando**: `STORY-SEO-001-fix-sitemap-shard-4-empty.md` — Status `InProgress` (AC3+AC4 ✅ floofy-sparkle 21-abr; AC1/AC5 aguardam @devops). **Bloqueador para SM:** SM **não deve criar nova story** para sitemap-4 vazio — cobrar @devops para concluir AC1/AC5/AC6/AC7.

---

## 3. Clusters de páginas NÃO indexadas (4.718 / 7 motivos)

> ⚠️ **Caveat metodológico (advisor flag):** O scrape DOM da tabela GSC sucou caracteres Material-Icons da Unicode Private Use Area (`` copy + `` open + `` inspect) anexados a cada URL. Após strip, os tamanhos reais de slug se tornam interpretáveis. Buckets de `{41d}/{42d}/{135d}` em scrapes anteriores eram **artefato** do scrape, não bug real.
>
> Os números abaixo refletem amostragem **com PUA stripped**. GSC limita exemplos por motivo a ~1.000 URLs cada — extrapolação para o total reportado em parêntese.

### 3.1 Não encontrado (404) — 2.113 URLs reportadas (1.000 amostradas)

Distribuição de buckets (após strip PUA):

| Bucket | Count | Diagnóstico |
|--------|-------|-------------|
| `/fornecedores/{15d}` (slug com 1 dígito a mais que CNPJ) | **268** | **Bug genuíno** — origem da string 15d **não identificada** (sitemap atual gera `{cnpj}` 14d via `/v1/sitemap/fornecedores-cnpj`). Hipóteses: 1) backend retorna CNPJ + dígito verificador extra para um subset; 2) link interno (footer/breadcrumb) com bug de formatação; 3) external backlink antigo. **Spike discovery necessário.** |
| `/cnpj/{14d}` | **250** | CNPJ válido formato OK; rota `/cnpj/[cnpj]/page.tsx` chama `/v1/empresa/{cnpj}/perfil-b2g`. Se fetch retorna null → `notFound()` (linha 125). Em 27-abr todos 5/5 amostrados retornam 404 por backend timeout (P0 acima). Pode ter sido data-gap em 21–25/abr. |
| `/orgaos/{14d}` | **177** | Mesmo padrão — `/orgaos/[slug]/page.tsx` linha 132. |
| `/fornecedores/{14d}` | **168** | Mesmo padrão — `/fornecedores/[cnpj]/page.tsx` linha 123. |
| `/blog/licitacoes/{cat}/{uf}` | **55** | Rota `/blog/licitacoes/[setor]/[uf]/page.tsx` linha 188 dispara `notFound()` se `!sector \|\| !ALL_UFS.includes(ufUpper)`. 55 URLs com categoria **possivelmente removida** (ex: `materiais_hidraulicos/mg` validado retorna 404). |
| `/contratos/orgao` (sem CNPJ) | **44** | Rota raiz `/contratos/orgao/page.tsx` não existe (só `/contratos/orgao/[cnpj]/page.tsx`). 404 esperado mas Google está descobrindo (provável sitemap/link antigo). |
| `/fornecedores/{11d}` | **18** | CNPJ truncado (3 dígitos faltando). Mesma origem do bug `{15d}` provavelmente. |
| Outros (curtos, /itens, /municipios, /perguntas) | ~33 | Rotas pontuais — investigação caso a caso |

### 3.2 Excluída pela tag `noindex` — 1.880 URLs reportadas (1.000 amostradas)

| Bucket | Count | Diagnóstico |
|--------|-------|-------------|
| `/cnpj/{14d}` | **781** | `cnpj/[cnpj]/page.tsx` linha 112: `robots: { index: total_contratos_24m > 0, follow: true }`. CNPJ tem perfil mas **0 contratos nos últimos 24 meses** → noindex correto. Mas: **listagem `/v1/sitemap/cnpjs` usa critério `≥1 bid`** (não contratos) → mismatch sitemap × frontend gate → Google descobre 781 URLs que sabidamente terão noindex. **Story candidate:** alinhar critério do endpoint sitemap ao gate de noindex (espelho do que `SEO-471` fez para `/contratos/[setor]/[uf]`). |
| `/contratos/{categoria}` (informatica, papelaria, software, engenharia, facilities, mobiliario, saude, vestuario, materiais-eletricos, transporte, vigilancia, alimentos, manutencao-predial, engenharia-rodoviaria, materiais-hidraulicos) | **~85** | Listagem categoria sem dados — noindex programmatic. Mesma classe de mismatch sitemap × gate. |
| `/fornecedores/{8-21d}` (slugs malformados) | ~91 | Não `\d{14}$` → `notFound()` ou `index: false`. Origem do bug slug (mesma raiz §3.1). |
| `/blog/licitacoes/{cat}` ou `/cidade` | ~20 | Programmatic noindex (gate dual `bids === 0 && contracts === 0`). |

### 3.3 Bloqueada pelo robots.txt — 464 URLs

| Bucket | Count | Diagnóstico |
|--------|-------|-------------|
| `/api/og?title=*` | **154** | **Intencional ✓** — `Disallow: /api` no robots.txt. OG image generator não deve indexar. |
| `/alertas-publicos/{categoria}/[uf]` | **~280** | **Bug genuíno** — `robots.txt` tem `Disallow: /alertas` que **prefix-matches `/alertas-publicos`** (RFC 9309 §2.2.2). Está bloqueando rota programmatic SEO pública. Comparar com store: `app/alertas-publicos/[setor]/[uf]/page.tsx` existe e renderiza conteúdo público. |
| Outros (`%EE%85...` PUA garbage em `/redefinir-senha`, `/mensagens`, etc.) | ~30 | Rotas privadas corretamente bloqueadas; PUA suffix é DOM artifact (não existe no Google). |

### 3.4 Erro no servidor (5xx) — 162 URLs

| Bucket | Count | Diagnóstico |
|--------|-------|-------------|
| `/contratos/orgao/{cnpj14}` | **156** | Concentração: **22-abr (53), 21-abr (46), 23-abr (32)** — **bate exatamente com janela do incidente backend wedge** (`feedback_build_hammers_backend_cascade.md`). Hotfix PR #515 em 053eb785 melhorou cache+AbortSignal mas hoje (27-abr) endpoint `/v1/contratos/orgao/{cnpj}/stats` está em **timeout** (P0 vivo) → ainda gerando falhas. |
| `/orgaos/{14d}`, `/fornecedores/{14d}`, `/cnpj/{14d}` | 6 | Mesma janela e provável mesma raiz. |

**Story prévia já existente:** `SEN-BE-005-sitemap-contratos-orgao-502.story.md` Status `Ready` — diagnostica PostgREST 502 em `sitemap_contratos_orgao_indexable`. **SM não deve duplicar — ativar essa story em vez de criar nova.**

### 3.5 Rastreada, mas não indexada — 72 URLs
- 37 `/contratos/orgao/{cnpj14}` (retry após 5xx — mesma raiz §3.4)
- 23 `/cnpj/{14d}`, `/fornecedores/{14d}`, `/orgaos/{14d}` (mismatch §3.2)
- 5 `/blog/licitacoes`
- Sem nova causa.

### 3.6 Indexada, mas bloqueada pelo robots.txt — 5 URLs
Todas `/alertas-publicos/materiais_eletricos/{ac,rr,ba,am,pe}`. Confirma o prefix-match bug §3.3 — Google indexou antes de algumas categorias serem bloqueadas; agora exibe snippet ruim.

---

## 4. Performance — sinais para SEO/Copy (não engenharia)

**Top queries (sample 25/395):**
- `smartlic` (brand): 6 cliques, CTR 66.7%, pos 1.0 — única query convertendo
- ~60% das queries são **razão social literal** (`supra distribuidora`, `tecnocenter`, `panificadora copan`, `neumann madeireira`...) → entity SEO atrai busca mas pos 5-12, CTR 0%
- ~10 CNPJs literais (`69034668000156`, `04907604000177`, ...) → mesmo padrão
- 4–5 queries `pncp contratos` / `pncp licitações` / `consulta contratos pncp` → competidor brand, pos 6-31

**Top páginas por impressões (parsed corretamente):**

| Pattern | Páginas | Cliques | Impr | CTR |
|---------|---------|---------|------|-----|
| `/fornecedores/{cnpj14}` (entity programmatic) | 649 | 54 | 2.913 | 1,9% |
| `/blog/pncp-guia-completo-empresas` | 1 | 4 | 2.354 | 0,17% |
| `/contratos/orgao/{cnpj14}` | 184 | 49 | 725 | 6,7% (melhor agregado) |
| `/blog/como-participar-primeira-licitacao-2026` | 1 | 0 | 609 | 0% |
| `/blog/licitacoes-ti-software-2026` | 1 | 8 | 587 | declínio -92% wow (recomendação GSC) |
| `/orgaos/{cnpj14}` | 57 | 8 | 228 | 3,5% |
| `/cnpj/{cnpj14}` | 35 | 1 | 155 | 0,6% |

**Sinais não-engenharia para o brief (não criar story):**
- Blog top pages com 600+ impressões e CTR <1% → title/snippet weak (copy task)
- Entity pages com CTR 0% por query CNPJ → preciso melhorar serp meta (copy/seo)
- Brand misspell `smart lic` (7 impr, pos 59.6) → não criar página separada; canonicalizar via brand authority

---

## 5. Outros relatórios

### 5.1 Conjuntos de Dados (Dataset schema) — 4 warnings

Source: GSC > Melhorias > Conjuntos de dados

| Warning | Páginas afetadas |
|---------|-----------------|
| Campo `description` ausente | 1 |
| Campo `license` ausente | **4** (maior) |
| Campo `contentUrl` ausente (em `distribution`) | 1 |
| Campo `creator` ausente | 1 |

**Localização do schema** (descoberta requerida): provavelmente `app/dados/page.tsx` ou `app/observatorio/*/page.tsx`. Procurar `@type": "Dataset"` no app router.

### 5.2 Core Web Vitals — sem dados

> "Não há dados de uso suficientes nos últimos 90 dias para este tipo de dispositivo."

**NÃO actionable na engenharia.** Causa = tráfego abaixo do CrUX threshold (~26 origins/mês). Não criar story; resolve quando crescer aquisição. Apenas sinalizar baseline para revisita futura.

### 5.3 Mensagens GSC (18 não lidas)

Painel lazy-rendered não acessível via DOM scrape. Conteúdo provavelmente duplica alertas dos relatórios principais (Coverage / Datasets). **Defer** — usuário pode triar manualmente.

---

## 6. Stories prévias relevantes (status atual)

| Story | Status | Cluster relevante | Recomendação SM |
|-------|--------|-------------------|----------------|
| `SEN-BE-005-sitemap-contratos-orgao-502.story.md` | **Ready (parado há 14+ dias)** | §3.4 5xx (156 URLs) + P0 sitemap 502 | **Pergunta para user/PO antes de duplicar:** por que essa story ficou Ready 14d sem ser puxada? Resposta determina se estamos em incident-response (corrigir agora pulando fila) ou backlog-grooming (re-priorizar e enfileirar). Sentry confirma 47 evt/24h em endpoint exato dela. |
| `STORY-SEO-001-fix-sitemap-shard-4-empty.md` | **InProgress** (AC3+AC4 done; AC1/AC5/AC6/AC7 pendentes) | §2 sitemap-4=0 | **Não duplicar** — cobrar @devops conclusão |
| `SEO-440-fix-noindex-canonical-sitemap.md` | Done | §3.2/§3.3 | Confirma padrão "noindex sem canonical herda homepage" — verificar regressão |
| `SEO-471-sitemap-licitacoes-indexable-v2-contratos.md` | Done | §3.2 | Aplicou união bids+contracts em `/contratos/[setor]/[uf]` — replicar em `/cnpj/{cnpj}` |
| `SEO-472-contratos-setor-uf-cruzamento-editais-noindex.md` | Done | §3.2 | Idem |
| `SEN-BE-007-slow-sitemap-endpoints.story.md` | (verificar) | §2 / P0 | Possível raiz comum |
| `DEBT-CI-sitemap-parallel-fetch-test-update-for-458.md` | (verificar) | §2 | Sitemap Index de SEO-460 |

---

## 7. Stories candidatas para SM escrever

> Convenção advisor: **CONFIRMED** = code path identificado + reproduzido empiricamente; **DISCOVERY** = padrão reconhecido mas hipótese precisa validação antes de implementar.

### Confirmed (criar story implementação)

**S1. [P0 / INCIDENTE — outage backend completo] — `bidiq-hotfix` — DB pool exhaustion + queries hung sem timeout**
- Trigger: this brief §"P0 INCIDENTE VIVO" (5 dias de degradação Sentry-confirmed; outage completo agora — `/buscar` user-facing afetado também)
- Escopo: aplicar `statement_timeout` agressivo (30s?) no PostgREST/Supabase, identificar e indexar/otimizar queries de `/v1/orgao/{cnpj}/stats` (692s p99) e sitemap endpoints (1680s p99), fixar `ConnectionTerminated` no pool, considerar bump de workers Railway (Hobby 1→2)
- AC: `/health` 200 < 1s, `/buscar` 200 < 5s, sitemap endpoints 200 < 30s, perfil-b2g 200 < 5s, Sentry "Health incident degraded" resolved, taxa slow_request < 5/dia em 48h
- Owner: @data-engineer (queries/indexes) + @devops (pool/workers/timeout config) + @dev (timeouts no client se necessário)
- Bloqueia: S2, S3, S4, S5
- Nota: pode subsumir SEN-BE-005 (alinhar antes de criar)

**S2. [P1] — `bidiq-data-pipeline` — Alinhar critério sitemap `/v1/sitemap/cnpjs` com gate noindex `/cnpj/[cnpj]`**
- Problema: sitemap inclui CNPJs com `≥1 bid`, mas page noindex se `total_contratos_24m === 0` → 781 noindex evitáveis
- Solução: replicar padrão `SEO-471` — sitemap retorna união `(bids ≥ N OR contratos ≥ M)` ou alinhar 100% com gate da page
- AC: 0 CNPJ com `total_contratos_24m === 0` no sitemap; total noindex `/cnpj/*` < 50 em 14 dias
- Owner: @data-engineer + @dev

**S3. [P1] — `bidiq-hotfix` — Robots.txt prefix-match bloqueia `/alertas-publicos`**
- Problema: `Disallow: /alertas` em robots.txt prefix-matches `/alertas-publicos` (RFC 9309 §2.2.2) — 280 URLs SEO bloqueadas + 5 indexadas com snippet ruim
- Solução: substituir `Disallow: /alertas` por `Disallow: /alertas$` (pattern Google extension) ou `Disallow: /alertas/` ou listar rotas privadas explicitamente. Adicionar `Allow: /alertas-publicos` defensivo.
- AC: curl `https://www.google.com/webmasters/tools/robots-testing-tool` (ou validador equivalente) confirma `/alertas-publicos/saude/sp` permitido; `/alertas` (raiz privada) ainda bloqueada
- Owner: @dev (mudança curta no `app/robots.ts` ou `public/robots.txt`)

**S4. [P2] — `bidiq-hotfix` — Sitemap inclui rota inexistente `/contratos/orgao` (sem `[cnpj]`)**
- Problema: 44 hits 404 em `/contratos/orgao` (raiz). Não há `app/contratos/orgao/page.tsx`.
- Solução: ou criar página landing categoria, ou garantir que sitemap NÃO emite essa URL (apenas `/contratos/orgao/{cnpj}`); adicionar 410 Gone se URL órfã.
- AC: 0 hits 404 em `/contratos/orgao` no GSC após 30 dias
- Owner: @dev

**S5. [P2] — `bidiq-hotfix` — Páginas `/blog/licitacoes/{cat}/{uf}` 404 (55 URLs)**
- Problema: 55 URLs em `/blog/licitacoes/{categoria}/{uf}` retornam 404 (categorias removidas/renomeadas; ex: `materiais_hidraulicos/mg`)
- Solução: identificar lista de categorias válidas atual vs lista que GSC tem; adicionar 301 redirect para alternativa equivalente OU 410 Gone explícito; remover do sitemap se ainda lá
- AC: ≤5 URLs `/blog/licitacoes/*/*` 404 no GSC em 30d
- Owner: @dev + @data-engineer

**S6. [P3] — `bidiq-hotfix` — Datasets schema warnings (4 warnings)**
- Problema: schema Dataset incompleto (license missing 4 págs, description/contentUrl/creator missing 1 cada)
- Solução: adicionar campos faltantes nos componentes que renderizam JSON-LD `@type: "Dataset"`. Localizar primeiro via `grep -rn '"Dataset"' frontend/app/`.
- AC: 0 warnings em GSC > Melhorias > Conjuntos de dados após 30d
- Owner: @dev

### Discovery (criar SPIKE story, não implementação ainda)

**D1. [SPIKE / P1] — Identificar origem dos slugs `/fornecedores/{15d}` e `/fornecedores/{11d}`**
- Sintoma: 268 URLs com 15 dígitos + 18 com 11 dígitos no cluster 404. Pattern: CNPJ válido + 1 dígito extra no fim (ex: `007352600001052` parece `00735260000105` + `2`); ou truncado.
- Hipóteses: 1) backend retorna `cnpj` com dígito verificador concatenado em algum subset; 2) link interno (footer/breadcrumb/related) com bug formatação; 3) external backlink antigo de versão pré-fix; 4) bot scraping inserindo string corrompida.
- Investigação: validar samples no `/v1/sitemap/fornecedores-cnpj` (esperar HTTP 200 quando backend recovered), grep frontend para padrões de concat de CNPJ (ex: `${cnpj}${dv}`), buscar logs Sentry por exemplos vivos.
- Output: relatório identificando origem + recomendação de fix
- Owner: @analyst + @dev

**D2. [SPIKE / P3] — Localizar e validar schema Dataset JSON-LD**
- Pré-requisito de S6 (acima)
- Procurar `'"Dataset"'` em `frontend/app/`, listar páginas que emitem, checar shape contra Google Rich Results Test
- Output: lista de arquivos + diff necessário (vira input de S6)
- Owner: @analyst

### Não criar story (defer / out-of-scope)

- **CWV "sem dados"** — root cause = baixo tráfego CrUX. Não actionable na engenharia. Revisita quando aquisição passar threshold.
- **CTR baixo entity pages + blog** — copy/seo task (`/copymasters` ou `/aiox-seo`), não eng.
- **Brand misspell `smart lic`** — não criar landing; resolve com authority orgânica.
- **Mensagens GSC (18)** — usuário tria manualmente.

---

## 8. Métricas baseline pós-correções (para SM definir KPIs)

| Métrica | Hoje | Meta após S1-S5 (60d) |
|---------|------|----------------------|
| Páginas não indexadas | 4.718 | < 1.500 |
| 404s | 2.113 | < 500 |
| noindex (excluído) | 1.880 | < 600 |
| 5xx | 162 | < 10 |
| robots blocked (excluindo `/api`) | 280 | 0 |
| Sitemap URLs publicadas | 1.239 | ≥ 5.000 (depende de STORY-SEO-001) |
| Cliques 28d | 145 | ≥ 300 |
| CTR médio | 1,3% | ≥ 2,5% (depende de copy não eng) |

---

## 9. Materiais brutos (paths absolutos)

```
/mnt/d/pncp-poc/gsc-404-urls.txt              # 1000 URLs amostradas (de 2113)
/mnt/d/pncp-poc/gsc-noindex-urls.txt          # 1000 URLs (de 1880)
/mnt/d/pncp-poc/gsc-5xx-urls.txt              # 162 URLs (full)
/mnt/d/pncp-poc/gsc-robots-urls.txt           # 464 URLs (full)
/mnt/d/pncp-poc/gsc-perf-queries-28d.txt      # 395 queries
/mnt/d/pncp-poc/gsc-perf-pages-28d.txt        # 1395 page rows
/tmp/sitemap-index.xml                         # snapshot sitemap raiz
/tmp/sm-{0,1,2,3,4}.xml                        # snapshots sitemaps filhos
```

**Caveat:** todos `gsc-*-urls.txt` contêm sufixo PUA `` em cada URL — strip via `re.sub(r'[-]+$', '', url)` antes de qualquer comparação programática.

---

## 10. Próximo passo recomendado para SM

1. **P0 já confirmado por Sentry — abrir incident response AGORA** (não adicionar à fila normal). Outage backend completo, /buscar afetado, 5 dias degradação. SEO é vítima downstream.
2. Pergunta para user/PO: **por que SEN-BE-005 ficou Ready 14 dias?** (se foi falta de capacidade → S1 absorve; se foi blocker técnico → S1 herda mesmo blocker e precisa primeiro destravar)
3. Cobrar `STORY-SEO-001` AC1+AC5+AC6+AC7 com @devops em paralelo (independente de S1, mas sitemap não vai indexar até S1 resolver)
4. Escrever S1 (incidente) primeiro; demais sequenciais com S1 como bloqueador
5. Escrever D1 (spike slug bug) em paralelo (não bloqueado por S1; usa logs Sentry quando endpoint perfil-b2g voltar)
6. **Defer todos S2-S6** até S1 estabilizar — não faz sentido medir taxa de noindex/404 enquanto backend está down (todas viram 404 por timeout)
