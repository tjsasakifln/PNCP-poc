# CRIT-DATA-PARITY-001 — Contrato de Paridade entre Endpoints de Entidade

**Status:** Ready
**Type:** Critical (systemic data integrity + revenue-adjacent)
**Priority:** 🔴 P0 — qualquer divergência entre endpoints que agregam o mesmo dataset é bug crítico
**Owner:** @data-engineer + @architect
**Origem:** sessão transient-hellman 2026-04-21 — user flag "não pode ocorrer com qualquer município, ente, esfera etc / tem de haver paridade entre informações"
**Motivating example:** CRIT-SEO-011 (São Paulo: 500 editais em `/municipios/...` vs 0 em `/blog/stats/cidade/...`)

---

## Problema Sistêmico

Múltiplas rotas/endpoints do SmartLic agregam o mesmo underlying dataset (`pncp_raw_bids`, `supplier_contracts`) mas **retornam números diferentes para a mesma entidade**. Isso é uma violação de integridade de dados que compromete:

- **Confiança do usuário** — dois lugares do produto mostram contagens diferentes para a mesma empresa/órgão/cidade
- **SEO indexability** — páginas com valor zero artificial são marcadas thin content pelo Google
- **UX organic funnel** — bounce 100% quando o usuário vê "0 editais" para cidade com dados reais
- **Conversão trial-to-paid** — dados inconsistentes = decisão B2G sem base

## Caso-farol (CRIT-SEO-011)

```
/v1/municipios/sao-paulo-sp/profile     → 500 editais, R$ 396M
/v1/blog/stats/cidade/sao-paulo         →   0 editais, R$   0
```

Mesmo município. Mesmo dataset. Endpoints diferentes. **Bug de normalização de acento.**

**Esse é apenas um sintoma.** O princípio violado é **paridade de informação entre agregações do mesmo dataset**.

## Contrato de Paridade (proposta de invariante)

> **Dado dois endpoints `A` e `B` que agregam atributo `attr` sobre entidade `e`:**
>
> ```
> ∀ e ∈ Entities, ∀ attr ∈ AggregationAttrs:
>     abs(A(e, attr) - B(e, attr)) / max(A(e, attr), B(e, attr), 1) ≤ ε
> ```
>
> **onde `ε ≤ 0.05` (5% de tolerância por janelas de tempo diferentes).**
>
> Divergência maior que ε é **falha de CI** e **alerta imediato** Sentry/PagerDuty.

## Pairs de endpoints que DEVEM ter paridade

### Municípios
- `/v1/municipios/{slug}/profile` ↔ `/v1/blog/stats/cidade/{cidade}`
- `/v1/municipios/{slug}/profile` ↔ `/v1/blog/stats/cidade/{cidade}/setor/{setor_id}`
- `/v1/municipios/{slug}/profile` ↔ `/v1/blog/stats/contratos/cidade/{cidade}`
- Rotas frontend: `/municipios/{slug}` ↔ `/blog/licitacoes/cidade/{cidade}`

**Atributos que precisam paridade:**
- `total_licitacoes_abertas` vs `total_editais` (rename; mesmo conceito)
- `valor_total_licitacoes` vs (cidade não expõe total — expor!)
- Órgãos frequentes (top N)
- Valor médio

### Órgãos / Entes
- `/v1/orgaos/{cnpj}/profile` (se existir) ↔ `/v1/blog/stats/contratos/orgao/{cnpj}`
- Rotas frontend: `/orgaos/{cnpj}` ↔ `/contratos/orgao/{cnpj}`

### Fornecedores
- `/v1/fornecedores/{cnpj}/profile` ↔ `/v1/blog/stats/contratos/fornecedor/{cnpj}` (se existir)
- `/cnpj/{cnpj}` ↔ `/fornecedores/{cnpj}` — mesmo CNPJ, rotas diferentes

### Setores × UF
- `/v1/blog/stats/setor/{setor_id}/uf/{uf}` ↔ `/v1/blog/stats/contratos/{setor_id}/uf/{uf}`

### Esferas (federal / estadual / municipal)
- Se houver agregação por esfera em múltiplas rotas → auditar

## Root Causes Recorrentes (padrões de regressão)

1. **Normalização de strings divergente**:
   - `.lower()` só (alguns endpoints) vs `.lower() + _strip_accents()` (outros) → caso-farol CRIT-SEO-011
   - `.strip()` em uns, não em outros
   - Case sensitivity em queries

2. **Janelas de tempo inconsistentes**:
   - Endpoint A: últimos 30 dias
   - Endpoint B: últimos 10 dias
   - Endpoint C: desde início do mês
   - Mesmo label "editais abertos" com janelas diferentes → confusão

3. **Filtros de ativação divergentes**:
   - Alguns endpoints filtram `is_active=true`, outros não
   - Alguns incluem contratos encerrados, outros só abertos
   - `STATUS_INFERENCE_ENABLED` flag pode estar on/off em contextos diferentes

4. **Source of truth divergente**:
   - Endpoint A queryies `pncp_raw_bids` (live)
   - Endpoint B queryies `supplier_contracts` (histórico)
   - Endpoint C queryies cache L2 (pode estar stale)

5. **Dedup divergente**:
   - PNCP vs PCP v2 vs ComprasGov priority
   - Content hash vs source ID
   - Cache L1 vs L2 pode ter dedup diferente

## Acceptance Criteria

### Imediato (aplicável em 1 sprint)

- [ ] **AC1:** Documentar em `docs/architecture/data-parity-contract.md` todas as pairs `(A, B)` de endpoints que agregam o mesmo dado e qual atributo exato deve ter paridade
- [ ] **AC2:** Implementar em `backend/tests/test_data_parity.py` contract tests que consultam produção (staging → prod) e falham se `|A - B| / max(A, B) > 0.05`
- [ ] **AC3:** CI workflow `.github/workflows/data-parity-nightly.yml` roda às 4am BRT diariamente, abrindo issue automático em caso de drift
- [ ] **AC4:** Fixar CRIT-SEO-011 (municipal accent bug — unblocks SP + ~70% cidades com acento)
- [ ] **AC5:** Auditar os outros 4-6 pairs listados e corrigir discrepâncias encontradas

### Sustentável (próximas 2-4 semanas)

- [ ] **AC6:** Centralizar normalização de strings em `backend/core/normalization.py` com 3 funções públicas: `normalize_slug(s)`, `normalize_for_match(s)`, `normalize_for_display(s)`. Todos os endpoints DEVEM usar essas.
- [ ] **AC7:** Padronizar janelas de tempo nos endpoints: criar `backend/core/time_windows.py` com enum `TimeWindow` (LAST_7D, LAST_30D, LAST_90D, SINCE_MONTH_START, ALL_TIME) e obrigar endpoints a declarar qual usam explicitamente
- [ ] **AC8:** Criar `backend/core/data_sources.py` com enum `DataSource` para declarar explicitamente qual tabela cada endpoint consome — nenhum endpoint pode consumir múltiplas fontes sem documentação
- [ ] **AC9:** Sentry alert: `smartlic_data_parity_drift_pct{pair_id}` > 5% → Slack + email (hourly rollup)
- [ ] **AC10:** Runbook em `docs/seo/data-parity-runbook.md` para ops quando drift é detectado

### Governança contínua

- [ ] **AC11:** Toda nova rota de agregação requer entry em `data-parity-contract.md` antes de merge (PR template update)
- [ ] **AC12:** Auditoria trimestral de drift histórico em `supplier_contracts` vs `pncp_raw_bids` para detectar pipeline bugs

---

## Impact Statement

### Se resolvermos

- **SEO**: Páginas programáticas de cidade/órgão/fornecedor deixam de ser thin content → Google re-ranqueia → organic clicks por SEO crescem (potencial 100-500% baseado no caso-farol)
- **UX**: Usuários veem dados consistentes em toda navegação → confiança aumenta → conversão trial-to-paid aumenta
- **Devs**: Contract tests impedem regressões futuras → menos bugs em produção → menos hours-to-detect

### Se não resolvermos

- **Revenue**: Continue queimando organic traffic em páginas com 0 editais, bouncing 100%
- **Trust**: Se um dia um usuário pagante perceber "municípios vs blog mostra números diferentes", churn
- **Future bugs**: Cada nova rota replica o mesmo anti-pattern porque não há contract test

---

## Priority Rationale

1. **Revenue-adjacent**: SEO orgânico é o motor inbound (confirmado em PLAN transient-hellman)
2. **Sistêmico**: O caso-farol (CRIT-SEO-011) é sintoma; a causa é estrutural — fix isolado não previne recorrência
3. **Detectável**: Contract tests são baratos e catching de regressão futura
4. **Scalable**: Toda nova rota herda o benefício automaticamente

---

## Dependências e Follow-ups

- **Blocks resolution of**: CRIT-SEO-011 (subset deste escopo); futuras stories programáticas
- **Depends on**: nenhum — pode ser iniciado imediatamente
- **Enables**: STORY-SEO-005 (GSC API dashboard com dados confiáveis), STORY-SEO-008 (pillar pages)

---

## Implementação — Roadmap Sugerido

### Sprint 1 (imediato — YOLO session ongoing)

1. Hotfix CRIT-SEO-011 (caso-farol): 15min de dev, revenue-blocking
2. Criar `docs/architecture/data-parity-contract.md` com list inicial de pairs (1-2h)

### Sprint 2 (próxima semana)

3. Implementar contract tests skeleton com 3 pairs piloto (4-6h)
4. Configurar CI workflow nightly (1h)
5. Resolver primeiros 3 drifts encontrados

### Sprint 3 (seguinte)

6. Centralizar normalização + time windows (refactor de 10-15 endpoints, 8-12h)
7. Cobrir restante dos pairs
8. Sentry alerting

---

## Referências cruzadas

- `backend/routes/blog_stats.py` — caso-farol no `get_cidade_stats` (linha 610)
- `backend/routes/municipios_publicos.py` — endpoint que funciona (referência de comportamento esperado)
- `backend/routes/supplier_contracts.py` ou similar — fonte histórica
- `docs/stories/CRIT-SEO-011-*.md` — story específica do bug cidade
- Memory `project_sitemap_serialize_isr_pattern.md` — contexto SEO
