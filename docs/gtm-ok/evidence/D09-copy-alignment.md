# D09 - Copy-Code Alignment Evidence

**Date:** 2026-02-17
**Analyst:** @analyst (Phase 4, GTM-OK v2.0)
**Methodology:** Exhaustive extraction of every user-facing promise from all marketing surfaces, mapped against the actual running codebase.

---

## Executive Summary

SmartLic's marketing copy has undergone significant improvement since the GTM-001/007/008/009 rewrites. The "decision intelligence" positioning is well-crafted and mostly defensible. However, several specific promises are either not delivered, misleading, or carry regulatory risk. The most severe issue is **fabricated review ratings in structured data (schema.org)** and a **pipeline access bug that blocks the paying plan from using a feature the pricing page promises**.

**Score: 6/10** (Several gaps, some misleading claims)

---

## Promise Inventory & Verification

### CATEGORY A: DELIVERED (Code Exists, Working, Tested)

| # | Promise | Location | Code Evidence | Status |
|---|---------|----------|---------------|--------|
| A1 | "27 estados cobertos" | HeroSection, StatsSection, InstitutionalSidebar, Pricing page | `onboarding/page.tsx` REGIONS lists all 27 UFs; backend `pncp_client.py` accepts any UF; `buscar_todas_ufs_paralelo()` queries per-UF | **DELIVERED** |
| A2 | "15 setores especializados" | HeroSection, StatsSection, SectorsGrid, Pricing page | `sectors_data.yaml` defines exactly 15 sectors: vestuario, alimentos, informatica, mobiliario, papelaria, engenharia, software, facilities, saude, vigilancia, transporte, manutencao_predial, engenharia_rodoviaria, materiais_eletricos, materiais_hidraulicos | **DELIVERED** |
| A3 | "1000+ regras de filtragem" | HeroSection, StatsSection | Verified: 1,437 keywords + 1,049 exclusions = **2,486 total rules**. Claim is conservative and accurate. | **DELIVERED** |
| A4 | "Exportacao Excel completa" | Pricing page FEATURES | `excel.py` generates styled workbooks; `allow_excel: True` for smartlic_pro in `quota.py` | **DELIVERED** |
| A5 | "5 anos de historico" | Pricing page FEATURES | `smartlic_pro.max_history_days = 1825` (5 years) in `quota.py` line 100 | **DELIVERED** |
| A6 | "1.000 analises por mes" | Pricing page FEATURES | `smartlic_pro.max_requests_per_month = 1000` in `quota.py` line 103; enforced via `check_and_increment_quota_atomic()` | **DELIVERED** |
| A7 | "PNCP e Portal de Compras Publicas integrados" | DifferentialsGrid, DataSourcesSection, Pricing page | `pncp_client.py` (PNCP) + `portal_compras_client.py` (PCP) both active; `PCP_ENABLED=true` default | **DELIVERED** |
| A8 | "2 bases oficiais" | Multiple locations | PNCP + PCP confirmed as two functional source adapters | **DELIVERED** |
| A9 | "Avaliacao por IA" / "Avaliacao estrategica" | HeroSection, ValuePropSection, HowItWorks | `llm.py` uses GPT-4.1-nano for structured summaries via `gerar_resumo_executivo()`; filter.py has LLM arbiter layer (GPT-4o-mini) for false positive elimination | **DELIVERED** |
| A10 | "Cancelamento em 1 clique" | Pricing page FAQ, comparisons.ts | `POST /api/subscriptions/cancel` exists in `routes/subscriptions.py` line 169; sets `cancel_at_period_end=True` in Stripe; `CancelSubscriptionModal.tsx` exists in frontend | **DELIVERED** |
| A11 | "Sem necessidade de cartao de credito" (trial) | InstitutionalSidebar signup | Trial uses `free_trial` plan with no Stripe checkout required; verified in auth flow | **DELIVERED** |
| A12 | "7 dias do produto completo" | FinalCTA, pricing page FAQ | `free_trial` capabilities in `quota.py` mirror smartlic_pro: `allow_excel: True`, `allow_pipeline: True`, `max_summary_tokens: 10000`, `max_history_days: 365` (actually 1 year, not 5) | **PARTIALLY DELIVERED** (see B4) |
| A13 | "Pagamento seguro via Stripe" | Pricing page | Stripe integration confirmed in billing routes, checkout flow, webhooks | **DELIVERED** |
| A14 | "Dados de fontes oficiais federais e estaduais" | InstitutionalSidebar, Footer | PNCP is federal; Portal de Compras Publicas is mixed. Claim is accurate. | **DELIVERED** |
| A15 | "Filtragem com 1.000+ regras" | Pricing page | 2,486 total rules. Accurate. | **DELIVERED** |
| A16 | "Busca por setor de atuacao" | Comparisons, Features page | Search endpoint accepts `setor` parameter; maps to keyword sets via `sectors.py` | **DELIVERED** |
| A17 | "Historico completo de buscas" | InstitutionalSidebar login | `saved_searches` table exists; `SavedSearchesDropdown.tsx` loads history | **DELIVERED** |

### CATEGORY B: PARTIALLY DELIVERED (Feature Exists But Incomplete/Mismatched)

| # | Promise | Location | Issue | Risk Level |
|---|---------|----------|-------|------------|
| B1 | "Resumos executivos com GPT-4o" | Pricing page FEATURES line 31 | **Model mismatch.** Backend uses `gpt-4.1-nano` (llm.py line 193) and `gpt-4o-mini` (filter arbiter). Neither is GPT-4o. The copy claims a more capable model than what runs. | **HIGH** - Misleading about AI capability tier |
| B2 | "Pipeline de acompanhamento" | Pricing page FEATURES line 30 | **Access bug.** `routes/pipeline.py` line 61: `allowed_plans = {"maquina", "sala_guerra"}`. The `smartlic_pro` plan is NOT in this set, meaning paying Pro customers get 403 errors. However, `quota.py` sets `allow_pipeline: True` for smartlic_pro. The route-level check overrides the capability. | **CRITICAL** - Paying customers cannot use promised feature |
| B3 | "Consulta sob demanda de 2 bases oficiais" | InstitutionalSidebar login | PCP requires `PCP_PUBLIC_KEY` env var. If not configured in production, only PNCP runs. Need to verify production env. | **MEDIUM** - Depends on deployment config |
| B4 | "7 dias do produto completo" (trial) | Multiple locations | Trial has `max_history_days: 365` (1 year), not 1825 (5 years) like smartlic_pro. Also only 3 analyses vs 1000/month. "Produto completo" is somewhat misleading when trial has 3 analyses and 1 year history vs 1000 analyses and 5 years. | **MEDIUM** - Trial is "full-featured" but heavily quota-limited |

### CATEGORY C: NOT DELIVERED (Promise in Copy, No Code)

| # | Promise | Location | Missing Code | Risk Level |
|---|---------|----------|-------------|------------|
| C1 | "Diario -- analises programadas" | StatsSection line 65-66 | **No scheduled/cron job exists.** Search is entirely on-demand (`POST /buscar`). There is no daily automated analysis pipeline, no cron scheduler, no background job runner. The word "Diario" with "analises programadas" implies daily automatic scanning. | **HIGH** - False claim of automated daily analysis |
| C2 | "Suporte com resposta garantida no mesmo dia" | comparisons.ts line 88 | No SLA enforcement in code. No support ticketing system. Help page (`ajuda/page.tsx`) says "Respondemos em ate 24 horas uteis" which contradicts "mesmo dia" claim. No monitoring or alerting for support response times. | **HIGH** - Unsubstantiated SLA claim |
| C3 | "1000+ licitacoes/dia" | InstitutionalSidebar signup stats | No daily monitoring exists to substantiate this number. System queries on-demand, not continuously. The claim implies a daily throughput metric that is never measured. | **MEDIUM** - Unverifiable metric |
| C4 | "Novas fontes adicionadas regularmente" | DifferentialsGrid, DataSourcesSection | Querido Diario adapter exists but is disabled by default (`ENABLE_SOURCE_QUERIDO_DIARIO=false`). Other adapters (Licitar, ComprasGov, BLL, BNC, Portal Transparencia) are coded but most are not enabled. This is forward-looking but currently misleading. | **LOW** - Aspirational, code exists |
| C5 | "Oportunidades identificadas assim que publicadas" | painPoints, beforeAfter comparisons | No real-time monitoring or webhook from PNCP/PCP. System queries on-demand only. There is no "as soon as published" detection. | **MEDIUM** - Implies real-time which does not exist |

### CATEGORY D: MISLEADING (Implies Something Code Does Not Do)

| # | Promise | Location | What It Implies vs Reality | Risk Level |
|---|---------|----------|--------------------------|------------|
| D1 | **AggregateRating 4.8/5 (127 reviews)** | StructuredData.tsx lines 77-82 | **FABRICATED.** Schema.org structured data claims 127 reviews with 4.8 average rating. This is completely fabricated -- there is no review collection system, no review database, no user rating mechanism anywhere in the codebase. This is fed directly to Google Search via JSON-LD. | **CRITICAL** - Potential Google penalty, false advertising, legal liability |
| D2 | "Prioriza por adequacao ao seu perfil" | Multiple comparison tables, HowItWorks | The system does sector-based keyword filtering, not profile-based prioritization. There is no user profile scoring, no per-user ranking algorithm. The onboarding collects CNAE/UFs but the search just filters by these parameters -- it does not "prioritize" results by user-specific adequacy. | **HIGH** - Overstates AI personalization |
| D3 | "IA avalia cada oportunidade e indica se vale a pena" | Features page, comparisons | LLM generates structured summaries (ResumoLicitacoes schema). It does not produce per-item "vale a pena ou nao" decisions with justification. The carousel examples show decision cards ("Prioridade Alta", "Analise com Cautela") but these are hardcoded in `analysisExamples.ts`, not generated by AI for real results. | **HIGH** - Implies per-opportunity AI decisions that don't exist |
| D4 | "Ranqueamento por relevancia" | DifferentialsGrid bullets | No ranking/scoring algorithm exists. Results are returned in API order after filtering. No relevance score is computed or displayed. | **HIGH** - Feature does not exist |
| D5 | "Analise de adequacao por setor, regiao e perfil de atuacao" | valueProps.prioritization.proof | System filters by sector keywords and UF. There is no "adequacy analysis" that considers user's porte, experience, or ticket medio in result ranking. | **MEDIUM** - Overstates analysis depth |
| D6 | "Confiavel 24/7" | comparisons.ts line 103 | No uptime monitoring, no SLA, no redundancy documented. Railway single-instance deployment. | **LOW** - Aspirational |
| D7 | "Decisao em segundos, nao horas" | DifferentialsGrid bullets | This is more marketing hyperbole than a measurable claim. Search takes 10s-2min per the help page. | **LOW** - Acceptable marketing language |

---

## Regulatory Risk Assessment

### HIGH RISK: Fabricated Reviews (D1)

The `StructuredData.tsx` file emits:
```json
{
  "aggregateRating": {
    "ratingValue": "4.8",
    "reviewCount": "127",
    "bestRating": "5",
    "worstRating": "1"
  }
}
```

**Legal exposure:**
- Brazil's CDC (Codigo de Defesa do Consumidor) Art. 37 prohibits misleading advertising
- Google's guidelines explicitly prohibit fabricated review markup and can result in manual actions (penalty/delisting)
- This structured data is machine-readable and directly consumed by Google Search for rich snippets
- 127 reviews at 4.8 stars for a product that has near-zero paying customers (D02 revenue score: 3/10) is obviously fabricated

**Recommendation:** Remove immediately. This is the single highest regulatory risk in the entire codebase.

### MEDIUM RISK: GPT-4o Model Claim (B1)

Pricing page states "Resumos executivos com GPT-4o" but the system uses GPT-4.1-nano (a smaller, cheaper model). While both are OpenAI models, claiming GPT-4o implies significantly more capable analysis. Under CDC Art. 37, this could be considered misleading about the quality of the service.

**Recommendation:** Change copy to match actual model, or use generic "IA avancada" language.

### MEDIUM RISK: Support SLA (C2)

Claiming "resposta garantida no mesmo dia" without any system to enforce or track this creates liability if customers complain about slow support. The help page already contradicts this with "24 horas uteis" language.

**Recommendation:** Standardize on the more conservative "24 horas uteis" claim across all surfaces.

### LOW RISK: ROI Claims

The pricing page ROI section includes:
- "R$ 150.000 -- Oportunidade media" as illustrative
- "Uma unica licitacao ganha pode pagar um ano inteiro"
- Disclaimer present: "Exemplo ilustrativo com base em oportunidades tipicas do setor"

The disclaimer adequately hedges these claims. ROI calculator in `roi.ts` uses transparent assumptions.

---

## Copy Hygiene Audit

### Banned Phrases Check

The `BANNED_PHRASES` array in `valueProps.ts` contains 29+ banned phrases. Quick scan results:

| Banned Phrase | Still Present? | Location |
|---------------|---------------|----------|
| "PNCP" | Yes, in technical contexts only (comparisons, data sources) | comparisons.ts, DataSourcesSection |
| "GPT-4" | Yes -- "GPT-4o" on pricing page | planos/page.tsx line 31 |
| "resumo" | "Resumos executivos" on pricing page | planos/page.tsx line 31 |

**Note:** The banned phrases list bans "PNCP" but it is used legitimately in data source descriptions where users need to know which government portals are queried. The ban should apply to hero/headline use only, not technical descriptions. However, "resumo" and "GPT-4" violations on the pricing page directly contradict GTM-007 and GTM-008 copy guidelines.

---

## Pipeline Access Bug (B2) -- Detailed Analysis

**Pricing page promise:** "Pipeline de acompanhamento -- Gerencie oportunidades do inicio ao fim"

**Backend capability definition** (`quota.py` line 102):
```python
"smartlic_pro": {
    "allow_pipeline": True,
    ...
}
```

**Route-level access check** (`routes/pipeline.py` line 61):
```python
allowed_plans = {"maquina", "sala_guerra"}
if plan_id not in allowed_plans:
    raise HTTPException(status_code=403, ...)
```

**Impact:** SmartLic Pro customers (the only current plan at R$1,999/month) will receive 403 errors when trying to use the pipeline. The route check was written for the old 3-tier plan system and was never updated for GTM-002's single-plan model.

**Fix:** Add `"smartlic_pro"` to `allowed_plans` set in `routes/pipeline.py`.

---

## "Daily Analysis" Claim (C1) -- Detailed Analysis

**StatsSection displays:** "Diario -- analises programadas"

**Codebase reality:**
- No cron job definitions found
- No task scheduler (Celery, APScheduler, etc.)
- No background worker processes
- All search is triggered by user `POST /buscar` requests
- No evidence of any scheduled/automated analysis pipeline

The word "programadas" (scheduled) combined with "Diario" (daily) explicitly claims automated daily scanning exists. This is factually false.

---

## Consistency Audit Across Surfaces

| Claim | Landing | Pricing | Features | Sidebar | Consistent? |
|-------|---------|---------|----------|---------|-------------|
| Sectors count | 15 | 15 | N/A | 15 | Yes |
| UF count | 27 | 27 | N/A | 27 | Yes |
| Sources count | "2 bases" | "2" | "2 bases principais" | "2 bases oficiais" | Yes |
| Trial duration | "7 dias" | "7 dias" | N/A | "7 dias" | Yes |
| Cancel policy | N/A | "sem contrato" | N/A | N/A | Yes |
| AI capability | "Avaliacao por IA" | "GPT-4o" | "IA avalia" | "Avaliacao por IA" | **No** -- Pricing says GPT-4o, others say generic IA |
| Support SLA | N/A | N/A | N/A | N/A | "mesmo dia" (comparisons) vs "24h uteis" (ajuda) -- **Inconsistent** |
| Daily analysis | "Diario" (Stats) | N/A | N/A | "24h atualizacao" (sidebar) | **Misleading** -- implies automation |

---

## Scoring Rationale

| Criterion | Score | Evidence |
|-----------|-------|----------|
| Core product claims (sectors, UFs, sources) | 9/10 | All verified, accurate, conservative |
| AI/Intelligence claims | 4/10 | Wrong model name, no per-item decisions, no ranking |
| Feature availability | 5/10 | Pipeline blocked for paying plan, no daily analysis |
| Support/operational claims | 3/10 | Fabricated reviews, unsubstantiated SLA, inconsistent |
| Disclaimer/hedging quality | 7/10 | ROI disclaimers good, but no disclaimers on AI claims |
| Regulatory compliance | 3/10 | Fabricated schema.org ratings = critical legal risk |

**Weighted Average: 6/10**

This is generous given the fabricated ratings issue (D1) which alone could warrant a 4/10, but the core product claims (A1-A17) are genuinely well-backed by code. The product does what it says for sectors, UFs, sources, filtering, and Excel export. The gaps are concentrated in: (1) AI intelligence overpromises, (2) operational claims without backing infrastructure, and (3) the fabricated review data.

---

## Priority Remediation (Ordered by Risk)

1. **[CRITICAL] Remove fabricated AggregateRating** from `StructuredData.tsx` -- Legal liability, Google penalty risk. Effort: 5 minutes.
2. **[CRITICAL] Fix pipeline access for smartlic_pro** in `routes/pipeline.py` -- Paying customers blocked from promised feature. Effort: 1 line change.
3. **[HIGH] Change "GPT-4o" to accurate model name** or generic "IA" on pricing page. Effort: 5 minutes.
4. **[HIGH] Remove "Diario -- analises programadas"** from StatsSection or change to "Sob demanda" (on-demand). Effort: 5 minutes.
5. **[HIGH] Remove "resposta garantida no mesmo dia"** from comparisons.ts; standardize on "24 horas uteis". Effort: 5 minutes.
6. **[HIGH] Tone down per-item AI decision language** -- "IA avalia e indica se vale a pena" is not what the code does (it generates summaries, not per-item decisions). Effort: 30 minutes copy review.
7. **[MEDIUM] Remove "1000+ licitacoes/dia"** stat from InstitutionalSidebar or add "publicadas nos portais" qualifier. Effort: 5 minutes.
8. **[MEDIUM] Clarify trial limitations** -- "produto completo" with 3 analyses and 1-year history is not truly "complete". Add "(3 analises)" qualifier. Effort: 5 minutes.

---

## Files Analyzed

### Frontend (copy sources)
- `frontend/app/page.tsx` -- Landing page composition
- `frontend/app/planos/page.tsx` -- Pricing page (FEATURES array, FAQ)
- `frontend/app/planos/obrigado/page.tsx` -- Thank you page
- `frontend/app/features/page.tsx` + `FeaturesContent.tsx` -- Features page
- `frontend/app/onboarding/page.tsx` -- Onboarding wizard
- `frontend/app/components/InstitutionalSidebar.tsx` -- Login/signup sidebar
- `frontend/app/components/StructuredData.tsx` -- Schema.org JSON-LD
- `frontend/app/components/landing/HeroSection.tsx`
- `frontend/app/components/landing/OpportunityCost.tsx`
- `frontend/app/components/landing/BeforeAfter.tsx`
- `frontend/app/components/landing/DifferentialsGrid.tsx`
- `frontend/app/components/landing/HowItWorks.tsx`
- `frontend/app/components/landing/StatsSection.tsx`
- `frontend/app/components/landing/DataSourcesSection.tsx`
- `frontend/app/components/landing/SectorsGrid.tsx`
- `frontend/app/components/landing/FinalCTA.tsx`
- `frontend/app/components/landing/AnalysisExamplesCarousel.tsx`
- `frontend/app/components/ValuePropSection.tsx`
- `frontend/app/components/ComparisonTable.tsx`
- `frontend/lib/copy/valueProps.ts`
- `frontend/lib/copy/comparisons.ts`
- `frontend/lib/copy/roi.ts`

### Backend (code verification)
- `backend/sectors.py` + `sectors_data.yaml` -- 15 sectors, 2486 rules
- `backend/quota.py` -- Plan capabilities, quota enforcement
- `backend/llm.py` -- GPT-4.1-nano (not GPT-4o)
- `backend/routes/pipeline.py` -- Pipeline access restricted to maquina/sala_guerra
- `backend/routes/subscriptions.py` -- Cancel subscription endpoint
- `backend/routes/billing.py` -- Stripe billing portal
- `backend/filter.py` -- Keyword filtering engine
- `backend/pncp_client.py` -- PNCP API integration
- `backend/clients/portal_compras_client.py` -- PCP integration
- `backend/search_pipeline.py` -- Multi-source search orchestration
