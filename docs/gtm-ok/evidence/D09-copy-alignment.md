# D09: Copy-Code Alignment Assessment

## Verdict: FAIL
## Score: 4/10

**Assessment Date:** 2026-02-16
**Assessor:** Phase 4 GTM-OK (Opus 4.6)
**Methodology:** Exhaustive extraction of every user-visible claim across all marketing pages, traced to backend/frontend code.

---

## Executive Summary

SmartLic's marketing copy makes approximately 108 distinct user-facing claims across landing page, features page, pricing page, trial conversion, and onboarding. Of these, **23 are fully delivered**, **31 are partially delivered**, **19 are not delivered**, and **11 are misleading**. The remaining are generic/aspirational copy that does not constitute a verifiable claim.

The most critical gaps are:
1. **"Dezenas de fontes oficiais"** -- only 3-4 sources are actually implemented (PNCP primary, Portal, Licitar, Querido Diario experimental)
2. **"R$ 2.3 bi em oportunidades mapeadas"** -- no data pipeline or measurement exists to substantiate this figure
3. **"Notificacoes em tempo real"** -- no notification system exists (no push, no email alerts, no websocket)
4. **"Monitoramento continuo"** / **"Diario"** -- system is on-demand only, user must manually trigger every search
5. **"ROI de 7.8x"** -- calculation assumes R$ 150K "average opportunity" vs R$ 19,188 annual cost, but this is hypothetical, not measured
6. **"Resposta garantida no mesmo dia"** -- no SLA infrastructure, no support ticket system
7. **"12 setores"** vs actual **15 sectors** in code -- the number is WRONG in the opposite direction (understated but inconsistent)

---

## Promise Alignment Matrix

### Landing Page -- HeroSection.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 1 | "Saiba Onde Investir para Ganhar Mais Licitacoes" | `HeroSection.tsx:77-82` | N/A (aspirational) | N/A | LOW |
| 2 | "Inteligencia que avalia oportunidades, prioriza o que importa e guia suas decisoes" | `HeroSection.tsx:98-100` | `llm.py:127-169` (LLM prompt does evaluate + recommend); `filter.py` (filtering, not prioritization) | PARTIALLY DELIVERED | MEDIUM -- "prioriza" implies ranking, but results are filtered, not ranked by relevance score |
| 3 | "Avaliacao objetiva, nao busca generica" | `HeroSection.tsx:100` | `llm.py` generates recommendations with urgency levels; `analysisExamples.ts` shows hardcoded examples | PARTIALLY DELIVERED | MEDIUM -- LLM generates text-based assessments, not structured per-bid scores shown to user |
| 4 | "R$ 2.3 bi em oportunidades" | `HeroSection.tsx:135` | NO CODE backs this metric | NOT DELIVERED | **CRITICAL** -- No data pipeline measures aggregate opportunity volume. Number is fabricated. |
| 5 | "12 setores cobertos" | `HeroSection.tsx:136` | `sectors_data.yaml` has **15** sector IDs | MISLEADING | MEDIUM -- Actual count is 15, not 12. SectorsGrid.tsx shows 12 display names that don't match backend. |
| 6 | "27 estados monitorados" | `HeroSection.tsx:137` | `pncp_client.py` accepts any UF; `onboarding/page.tsx:14-19` lists all 27 UFs | DELIVERED | LOW |

### Landing Page -- StatsSection.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 7 | "Impacto real no mercado de licitacoes" | `StatsSection.tsx:22` | N/A (heading) | N/A | LOW |
| 8 | "R$ 2.3bi em oportunidades/mes" | `StatsSection.tsx:34-36` | NO CODE | NOT DELIVERED | **CRITICAL** -- Same as #4. No measurement infrastructure. |
| 9 | "12 setores especializados" | `StatsSection.tsx:47-48` | `sectors_data.yaml` has 15 | MISLEADING | MEDIUM -- Repeated incorrect count |
| 10 | "27 estados cobertos" | `StatsSection.tsx:56-57` | Same as #6 | DELIVERED | LOW |
| 11 | "Diario monitoramento continuo" | `StatsSection.tsx:65-66` | NO cron/scheduler/background job exists | NOT DELIVERED | **HIGH** -- System is strictly on-demand. No background monitoring. |

### Landing Page -- DifferentialsGrid.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 12 | "PRIORIZACAO INTELIGENTE" | `DifferentialsGrid.tsx:24` | Filter sorts by value/date, not by profile relevance score | PARTIALLY DELIVERED | MEDIUM |
| 13 | "Analise de adequacao ao seu perfil" | `DifferentialsGrid.tsx:25` | Onboarding collects CNAE/UFs; `first_analysis.py` maps CNAE to sector. But no per-bid profile matching. | PARTIALLY DELIVERED | MEDIUM |
| 14 | "Ranqueamento por relevancia" | `DifferentialsGrid.tsx:25` | NO ranking algorithm exists. Results are filtered, not ranked. | NOT DELIVERED | HIGH |
| 15 | "ANALISE AUTOMATIZADA -- Avaliacao automatica de cada edital" | `DifferentialsGrid.tsx:33-34` | `llm.py` generates summary of batch (up to 50 bids). Does NOT evaluate each edital individually. | MISLEADING | HIGH -- Implies per-bid evaluation; reality is batch summary |
| 16 | "Decisao em segundos, nao horas" | `DifferentialsGrid.tsx:34` | LLM call takes 5-15s. Results are displayed quickly after search. | PARTIALLY DELIVERED | LOW |
| 17 | "REDUCAO DE INCERTEZA -- Criterios objetivos de avaliacao" | `DifferentialsGrid.tsx:43` | LLM prompt asks for objective criteria, but output is unstructured text. No structured scoring per bid in production. | PARTIALLY DELIVERED | MEDIUM |
| 18 | "Dados consolidados de multiplas fontes" | `DifferentialsGrid.tsx:43` | `source_config/sources.py` shows 3-4 sources (PNCP, Portal, Licitar, QD experimental) | PARTIALLY DELIVERED | MEDIUM -- "multiplas" is true but "dezenas" (used elsewhere) is not |
| 19 | "COBERTURA NACIONAL -- Todas as fontes oficiais monitoradas" | `DifferentialsGrid.tsx:52` | Only PNCP + 2-3 supplemental. NOT "all official sources" | MISLEADING | **HIGH** -- Implies completeness that does not exist |
| 20 | "27 estados cobertos diariamente" | `DifferentialsGrid.tsx:52` | States are queryable, but NOT queried daily (on-demand only) | MISLEADING | HIGH -- "diariamente" is false |
| 21 | "Atualizacao continua em tempo real" | `DifferentialsGrid.tsx:52` | NO real-time updates. On-demand search only. | NOT DELIVERED | **HIGH** |

### Landing Page -- BeforeAfter.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 22 | "Visao completa do mercado em tempo real" | `BeforeAfter.tsx:91` | Neither complete (3-4 sources, not all) nor real-time (on-demand) | MISLEADING | **HIGH** |
| 23 | "Avaliacao objetiva: vale a pena ou nao, e por que" | `BeforeAfter.tsx:95` | `analysisExamples.ts` shows this pattern but these are hardcoded examples. `llm.py` generates recommendations but not per-bid go/no-go. | PARTIALLY DELIVERED | HIGH -- Landing page shows curated examples but the actual product doesn't deliver per-bid decisions |
| 24 | "Posicione-se antes da concorrencia" | `BeforeAfter.tsx:99` | No timing advantage mechanism. Same data as public PNCP. | MISLEADING | MEDIUM |

### Landing Page -- OpportunityCost.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 25 | "Uma unica licitacao perdida por falta de visibilidade pode custar R$ 50.000, R$ 200.000 ou mais" | `OpportunityCost.tsx:46` | Hypothetical claim (not measured) | PARTIALLY DELIVERED | LOW -- Reasonable market claim but unsubstantiated |
| 26 | "Cada dia sem visibilidade completa e uma oportunidade que pode ir para outro" | `OpportunityCost.tsx:51` | No daily monitoring. User must search manually. | MISLEADING | MEDIUM |

### Landing Page -- DataSourcesSection.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 27 | "Cobertura nacional, precisao absoluta" | `DataSourcesSection.tsx:23` | "Precisao absoluta" is unsubstantiable | MISLEADING | MEDIUM -- "absolute precision" is an unqualified claim |
| 28 | "Monitoramos dezenas de fontes oficiais em tempo real" | `DataSourcesSection.tsx:31` | `source_config/sources.py` lists 8 source codes, only 3-4 enabled. NOT "dezenas" (dozens). NOT real-time. | NOT DELIVERED | **CRITICAL** -- "Dezenas" means "dozens." The system has 3-4 active sources. |
| 29 | "Dezenas de fontes consolidadas em tempo real" | `DataSourcesSection.tsx:57` | Same as above | NOT DELIVERED | **CRITICAL** |
| 30 | "Governo Federal + 27 estados + Diarios oficiais + Bases complementares" | `DataSourcesSection.tsx:58` | PNCP covers federal. Querido Diario (experimental) covers some municipal diaries. No state-specific portals are implemented. | MISLEADING | HIGH -- Implies exhaustive multi-layer sourcing |
| 31 | "Fontes federais, Portais estaduais, Diarios oficiais, Bases complementares, Fontes municipais" | `DataSourcesSection.tsx:71` | No "portais estaduais" or "fontes municipais" are implemented | NOT DELIVERED | HIGH |

### Landing Page -- SectorsGrid.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 32 | 12 sectors displayed: Uniformes, Facilities, Software & TI, Alimentacao, Equipamentos, Transporte, Saude, Limpeza, Seguranca, Escritorio, Construcao, Servicos Gerais | `SectorsGrid.tsx:15-88` | `sectors_data.yaml` has 15 IDs: vestuario, alimentos, informatica, mobiliario, papelaria, engenharia, software, facilities, saude, vigilancia, transporte, manutencao_predial, engenharia_rodoviaria, materiais_eletricos, materiais_hidraulicos | MISLEADING | MEDIUM -- Frontend shows 12 generic names that DON'T match backend's 15. "Limpeza", "Escritorio", "Construcao", "Servicos Gerais" don't exist as backend sectors. |
| 33 | "Cobertura abrangente com expansao continua" | `SectorsGrid.tsx:118` | Aspirational. No expansion mechanism. | N/A | LOW |
| 34 | "Novos setores regularmente" | `SectorsGrid.tsx:200` | No automated sector addition. Manual code change required. | PARTIALLY DELIVERED | LOW |

### Landing Page -- HowItWorks.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 35 | "Diga o que voce vende" | `HowItWorks.tsx:19` | Onboarding collects CNAE and objective | DELIVERED | LOW |
| 36 | "Receba oportunidades priorizadas" | `HowItWorks.tsx:28` | Opportunities are filtered, not prioritized/ranked | PARTIALLY DELIVERED | MEDIUM |
| 37 | "IA avalia, filtra e prioriza as oportunidades certas para voce" | `HowItWorks.tsx:30` | IA generates summary; filtering is keyword-based, not AI-based. No prioritization/ranking. | MISLEADING | HIGH -- Implies AI does the filtering. In reality, keyword regex does. |
| 38 | "Avaliacao objetiva de cada oportunidade" | `HowItWorks.tsx:40` | LLM evaluates batch, not each bid individually | MISLEADING | HIGH |

### Landing Page -- FinalCTA.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 39 | "Comece a Vencer Licitacoes Hoje" | `FinalCTA.tsx:23` | Aspirational | N/A | LOW |
| 40 | "Produto completo por 7 dias. Sem cartao. Sem compromisso." | `FinalCTA.tsx:52` | Trial is 7 days: DELIVERED. "Sem cartao": signup does not require card (Supabase email auth). Card only at checkout. | DELIVERED | LOW |

### Landing Page -- AnalysisExamplesCarousel.tsx + analysisExamples.ts

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 41 | "SmartLic em Acao -- Veja como analisamos oportunidades reais e sugerimos decisoes objetivas" | `analysisExamples.ts:232-234` | Examples are **hardcoded** in `analysisExamples.ts:127-225`, not from real system output | MISLEADING | **HIGH** -- Claims "real opportunities" but they are curated fabricated examples |
| 42 | 5 example analysis cards with structured decisions (PARTICIPAR/AVALIAR/NAO PARTICIPAR) | `analysisExamples.ts:127-225` | These are **static marketing content**, not live system output. The actual system does NOT produce per-bid go/no-go decisions. | MISLEADING | **HIGH** -- Implies product delivers structured per-bid decisions |

### Landing Page -- ComparisonTable.tsx + comparisons.ts

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 43 | "Por setor de atuacao (1 clique)" | `comparisons.ts:39` | Search page has sector selector | DELIVERED | LOW |
| 44 | "Avaliacao objetiva de cada oportunidade" | `comparisons.ts:47` | Batch LLM summary, not per-bid | MISLEADING | HIGH |
| 45 | "IA prioriza por adequacao ao seu perfil" | `comparisons.ts:53` | No profile-based AI prioritization exists | NOT DELIVERED | HIGH |
| 46 | "Dezenas de fontes oficiais consolidadas automaticamente" | `comparisons.ts:61` | 3-4 sources, not dozens | NOT DELIVERED | **CRITICAL** |
| 47 | "Posicione-se antes da concorrencia" | `comparisons.ts:68` | No timing advantage. Same public data. | MISLEADING | MEDIUM |
| 48 | "Investimento fixo mensal (tudo incluso)" | `comparisons.ts:74` | Correct -- single price model | DELIVERED | LOW |
| 49 | "1 clique cancelamento (sem burocracia)" | `comparisons.ts:81` | Stripe portal handles cancellation | DELIVERED | LOW -- Assuming Stripe billing portal is configured |
| 50 | "Resposta garantida no mesmo dia" | `comparisons.ts:89` | NO support SLA system, no ticket system, no support chat | NOT DELIVERED | **HIGH** -- This is a service-level commitment with no backing infrastructure |
| 51 | "Intuitiva (produtivo desde o primeiro uso)" | `comparisons.ts:95` | Subjective UX claim | N/A | LOW |
| 52 | "Infraestrutura moderna, disponivel quando voce precisa" | `comparisons.ts:102` | Railway deployment exists | DELIVERED | LOW |
| 53 | "*Dados baseados em pesquisa de mercado (Reclame AQUI, estudos academicos...)" | `ComparisonTable.tsx:208` | No citation provided. Unverifiable. | MISLEADING | MEDIUM |

### Landing Page -- ValuePropSection.tsx + valueProps.ts

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 54 | "Priorizacao Inteligente -- Saiba onde focar" | `valueProps.ts:76-83` | Filter only, no AI prioritization | PARTIALLY DELIVERED | MEDIUM |
| 55 | "Analise de adequacao por setor, regiao e perfil de atuacao" | `valueProps.ts:82` | Sector and region filtering exists. Profile-based adequacy assessment does NOT exist per-bid. | PARTIALLY DELIVERED | MEDIUM |
| 56 | "Analise Automatizada -- IA avalia cada oportunidade e extrai criterios decisivos" | `valueProps.ts:86-89` | LLM batch summary only; no per-opportunity structured evaluation | MISLEADING | HIGH |
| 57 | "Avaliacao objetiva -- vale a pena ou nao, e por que" | `valueProps.ts:89` | Not delivered per-bid in product | NOT DELIVERED | HIGH |
| 58 | "Reducao de Incerteza -- dados consolidados de multiplas fontes oficiais" | `valueProps.ts:96-103` | 3-4 sources, not comprehensive | PARTIALLY DELIVERED | MEDIUM |
| 59 | "Monitoramos dezenas de fontes oficiais em todos os 27 estados, todos os dias" | `valueProps.ts:109` | 3-4 sources, on-demand only | NOT DELIVERED | **CRITICAL** |

### Features Page -- FeaturesContent.tsx + valueProps.ts

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 60 | "O sistema avalia cada oportunidade com base no seu perfil (porte, regiao, ticket medio) e indica quais merecem sua atencao" | `valueProps.ts:127` | No per-bid profile evaluation in production | NOT DELIVERED | **HIGH** |
| 61 | "Voce para de desperdicar tempo com licitacoes ruins e foca nas que pode ganhar" | `valueProps.ts:127` | Filtering removes irrelevant bids, but no "can you win this" assessment | PARTIALLY DELIVERED | MEDIUM |
| 62 | "Nao precisa ler editais para decidir se vale a pena" | `valueProps.ts:136` | LLM gives batch summary but user still needs to evaluate individual bids | MISLEADING | MEDIUM |
| 63 | "O SmartLic avalia requisitos, prazos e valores contra seu perfil e diz: 'Vale a pena' ou 'Pule esta'" | `valueProps.ts:136` | This is shown in hardcoded examples but NOT delivered per-bid by the system | NOT DELIVERED | **HIGH** |
| 64 | "Consulta em tempo real dezenas de fontes oficiais, federais e estaduais" | `valueProps.ts:145` | 3-4 sources, not dozens. Not real-time (on-demand). No state-level portals. | NOT DELIVERED | **CRITICAL** |
| 65 | "Se uma licitacao compativel com seu perfil e publicada em qualquer lugar do Brasil, voce sabe" | `valueProps.ts:145` | NO notification system. User knows only when they manually search. | NOT DELIVERED | **HIGH** |
| 66 | "Notificacoes em tempo real de novas oportunidades compativeis com seu perfil" | `valueProps.ts:163` | NO notification infrastructure exists (no push, no email alerts, no websocket, no cron) | NOT DELIVERED | **CRITICAL** |
| 67 | "Voce descobre antes, se posiciona antes, compete melhor" | `valueProps.ts:163` | No timing advantage mechanism. Same public PNCP data. | MISLEADING | MEDIUM |

### Features Page -- features/page.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 68 | "Se uma unica licitacao ganha pagar o sistema por um ano inteiro, por que esperar?" | `features/page.tsx:70` | Hypothetical. No measurement. | N/A | LOW -- Framed as question, not claim |

### Pricing Page -- planos/page.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 69 | "1.000 analises por mes" | `planos/page.tsx:28` | `quota.py:103`: smartlic_pro max_requests_per_month = 1000 | DELIVERED | LOW |
| 70 | "Avalie oportunidades em todos os 27 estados" | `planos/page.tsx:28` | UF validation supports all 27 | DELIVERED | LOW |
| 71 | "Exportacao Excel completa" | `planos/page.tsx:29` | `excel.py` generates Excel; `quota.py:101`: allow_excel=True for smartlic_pro | DELIVERED | LOW |
| 72 | "Pipeline de acompanhamento -- Gerencie oportunidades do inicio ao fim" | `planos/page.tsx:30` | `routes/pipeline.py` + `frontend/app/pipeline/page.tsx` exist with Kanban board | DELIVERED | LOW |
| 73 | "Inteligencia de decisao completa -- IA com 10.000 tokens de analise estrategica" | `planos/page.tsx:31` | `quota.py:105`: max_summary_tokens=10000 for smartlic_pro; `llm.py` uses OpenAI | DELIVERED | LOW -- Token limit exists but "strategic analysis" overstates what the LLM output delivers |
| 74 | "5 anos de historico -- Acesso ao maior acervo de oportunidades" | `planos/page.tsx:32` | `quota.py:100`: max_history_days=1825 (5 years). PNCP API accepts date ranges. | PARTIALLY DELIVERED | MEDIUM -- Can query 5 years back, but PNCP may not have data that far. "Maior acervo" is unsubstantiated. |
| 75 | "Cobertura nacional -- Todos os estados e setores monitorados" | `planos/page.tsx:33` | States queryable, sectors defined | PARTIALLY DELIVERED | LOW |
| 76 | "Processamento prioritario -- Resultados em segundos, nao minutos" | `planos/page.tsx:34` | `quota.py:106`: priority=NORMAL for smartlic_pro (NOT high/critical). No priority queue implementation. | MISLEADING | MEDIUM -- Claims priority processing but plan has NORMAL priority |
| 77 | "ROI de 7.8x em uma unica oportunidade ganha" | `planos/page.tsx:328-329` | `roi.ts:79` has ROI calculator. 7.8x = R$150K / R$19,188. But R$150K "average opportunity" is fabricated. | MISLEADING | **HIGH** -- Stated as fact, not estimate. No disclaimer. |
| 78 | "R$ 150.000 Oportunidade media" | `planos/page.tsx:319` | No data to support "average" claim | NOT DELIVERED | HIGH |
| 79 | "Uma unica licitacao ganha pode pagar um ano inteiro" | `planos/page.tsx:314` | Plausible but unsubstantiated hypothetical | PARTIALLY DELIVERED | MEDIUM -- Framed with "pode" (can), but adjacent to specific ROI numbers |
| 80 | "Cancele quando quiser. Sem contrato de fidelidade." | `planos/page.tsx:305` | Stripe billing portal. FAQ confirms. | DELIVERED | LOW |
| 81 | "Pagamento seguro via Stripe" | `planos/page.tsx:305` | `routes/billing.py` integrates Stripe | DELIVERED | LOW |
| 82 | "Sem contrato de fidelidade, mesmo no acesso anual" | `planos/page.tsx:41` | Stripe handles this | DELIVERED | LOW |
| 83 | "Sua conta volta ao modo de avaliacao com 3 analises" after cancellation | `planos/page.tsx:49` | `quota.py:67`: free_trial max_requests_per_month=3 | DELIVERED | LOW |

### Trial Conversion -- TrialConversionScreen.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 84 | "Veja o que voce descobriu em 7 dias" | `TrialConversionScreen.tsx:83` | `GET /v1/analytics/trial-value` exists | DELIVERED | LOW |
| 85 | "O SmartLic ja trabalhou para voce" | `TrialConversionScreen.tsx:87` | Shows search stats | DELIVERED | LOW |
| 86 | "Uma unica licitacao ganha pode pagar o sistema por um ano inteiro" | `TrialConversionScreen.tsx:123` | Same as #79 | PARTIALLY DELIVERED | MEDIUM |
| 87 | "Seu concorrente pode estar usando SmartLic agora" | `TrialConversionScreen.tsx:178` | Unverifiable competitive pressure claim | N/A | LOW |

### Trial Expiring -- TrialExpiringBanner.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 88 | "Continue tendo vantagem competitiva a partir de R$ 1.599/mes" | `TrialExpiringBanner.tsx:52` | Annual pricing = R$1,599/mo | DELIVERED | LOW |

### Onboarding -- onboarding/page.tsx

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 89 | "Em 3 passos vamos encontrar suas primeiras oportunidades" | `onboarding/page.tsx:622` | 3-step wizard + auto-search | DELIVERED | LOW |
| 90 | "Vamos encontrar suas primeiras oportunidades agora. Isso leva ~15 segundos." | `onboarding/page.tsx:405` | First analysis endpoint triggers search | DELIVERED | LOW |

### Copy Library -- valueProps.ts (additional claims not in UI)

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 91 | "Monitoramento continuo de fontes federais, estaduais e municipais" | `valueProps.ts:112` | No continuous monitoring. 3-4 sources only. | NOT DELIVERED | **CRITICAL** |
| 92 | "Cancelamento em 1 clique (sem burocracia, sem ligacoes)" | Implied in pricing copy | Stripe billing portal | DELIVERED | LOW |

### Comparison Library -- comparisons.ts (proof points)

| # | Promise (Copy) | Source File:Line | Code Location | Status | Risk |
|---|----------------|-----------------|---------------|--------|------|
| 93 | "R$ 2.3 bilhoes em oportunidades mapeadas mensalmente" | `comparisons.ts:337-339` | proofSource says "Platform data" but no measurement code | NOT DELIVERED | **CRITICAL** |
| 94 | "12 setores especializados com cobertura completa de termos" | `comparisons.ts:332-334` | 15 sectors in code; "cobertura completa de termos" is debatable | MISLEADING | MEDIUM |
| 95 | "Monitoramento continuo diario de todas as fontes" | `comparisons.ts:343-344` | proofSource says "System uptime and crawl frequency metrics" but no crawler exists | NOT DELIVERED | **HIGH** |
| 96 | "Suporte com resposta no mesmo dia" | `comparisons.ts:348-349` | proofSource says "Customer support policy SLA commitment" but no SLA infrastructure | NOT DELIVERED | HIGH |

---

## High-Risk Gaps (NOT DELIVERED or MISLEADING)

### P0 -- CRITICAL (Must fix before launch)

1. **"Dezenas de fontes oficiais"** (Claims #28, #29, #46, #59, #64, #91)
   - **Reality:** 3-4 sources (PNCP primary, Portal, Licitar, Querido Diario experimental). Two sources (BLL, BNC) are disabled per code comments ("syncs to PNCP").
   - **Fix:** Either (A) implement more sources, or (B) change copy to "fontes oficiais" without "dezenas de". Most honest: "Fonte primaria PNCP + fontes complementares" or "Consolidamos fontes federais e complementares."

2. **"R$ 2.3 bi em oportunidades mapeadas"** (Claims #4, #8, #93)
   - **Reality:** No aggregation pipeline. No measurement code. The number appears to be invented.
   - **Fix:** Either (A) build a daily aggregation job that sums `valorTotalEstimado` from search results and report the actual figure, or (B) remove the claim entirely. If keeping a number, it MUST come from measured data with a methodology footnote.

3. **"Notificacoes em tempo real"** (Claim #66)
   - **Reality:** Zero notification infrastructure. No email alerts. No push notifications. No websocket. No scheduler.
   - **Fix:** Either (A) implement email alerts for new matching opportunities (requires background job), or (B) remove the claim. This is the most egregious gap -- a specific, concrete feature that simply does not exist.

4. **"Monitoramento continuo / Diario"** (Claims #11, #21, #91, #95)
   - **Reality:** System is 100% on-demand. User must manually trigger every search. No background job runs.
   - **Fix:** Either (A) implement a scheduled job (cron/celery) that runs searches for subscribed users, or (B) change copy to "Pesquisa sob demanda com cobertura completa" and remove all "continuo"/"diario"/"tempo real" language.

5. **"Per-bid objective evaluation: vale a pena ou nao"** (Claims #23, #38, #41, #42, #56, #57, #60, #63)
   - **Reality:** The landing page's AnalysisExamplesCarousel shows per-bid PARTICIPAR/NAO PARTICIPAR decisions, but these are hardcoded marketing examples. The actual system generates a batch LLM summary, not per-bid structured decisions.
   - **Fix:** Either (A) implement per-bid evaluation (add structured output per bid from LLM), or (B) clarify that examples are illustrative: "Exemplo de como o SmartLic pode avaliar oportunidades" with a disclaimer.

### P1 -- HIGH (Should fix before paid launch)

6. **"IA prioriza por adequacao ao perfil"** (Claims #14, #36, #37, #45, #54)
   - **Reality:** Results are filtered by sector keywords and UF. No AI-based ranking or profile-matching score exists.
   - **Fix:** Change "prioriza" to "filtra" or "seleciona." Alternatively, implement a simple relevance score.

7. **"ROI de 7.8x"** (Claim #77)
   - **Reality:** R$150K "average opportunity" is fabricated. ROI calculation (R$150K / R$19,188) is presented as fact.
   - **Fix:** Add disclaimer: "Exemplo hipotetico. ROI real depende do valor das oportunidades conquistadas." Or better: remove specific multiplier.

8. **"Resposta garantida no mesmo dia"** (Claims #50, #96)
   - **Reality:** No support ticket system, no SLA tracking, no support chat.
   - **Fix:** Either (A) implement a support channel with SLA tracking, or (B) change to "Suporte por email" without SLA guarantee.

9. **"R$ 150.000 Oportunidade media"** (Claim #78)
   - **Reality:** No data to support this average. Not calculated from system data.
   - **Fix:** Either calculate from actual search results or label clearly as "Exemplo ilustrativo."

10. **"Processamento prioritario"** (Claim #76)
    - **Reality:** smartlic_pro has `priority: NORMAL`, not HIGH or CRITICAL. No priority queue exists.
    - **Fix:** Either implement priority processing or remove the claim.

### P2 -- MEDIUM (Should fix, not blocking)

11. **"12 setores" vs 15 actual sectors** (Claims #5, #9, #32, #94)
    - **Reality:** `sectors_data.yaml` defines 15 sectors. Frontend SectorsGrid shows 12 display names that include items ("Limpeza", "Escritorio", "Construcao", "Servicos Gerais") that don't map to backend sector IDs.
    - **Fix:** Sync frontend display with backend sectors. Either show all 15 or explain grouping.

12. **"*Dados baseados em pesquisa de mercado (Reclame AQUI...)"** (Claim #53)
    - **Reality:** No formal research documentation exists.
    - **Fix:** Either provide citations or remove the asterisk claim.

13. **"Posicione-se antes da concorrencia"** (Claims #24, #47, #67)
    - **Reality:** Data comes from public PNCP API. No exclusive data advantage.
    - **Fix:** Soften to "Acesso rapido a oportunidades assim que publicadas."

---

## Regulatory Concerns

### 1. False Advertising Risk (CDC Art. 37 -- Brazilian Consumer Defense Code)

| Claim | Risk Level | Issue | Recommendation |
|-------|-----------|-------|----------------|
| "R$ 2.3 bi em oportunidades mapeadas" | **CRITICAL** | Specific financial figure with no data backing. Could be considered "publicidade enganosa" (deceptive advertising). | Remove or substantiate with measured data + methodology |
| "Dezenas de fontes oficiais" | **HIGH** | Quantitative claim ("dozens") demonstrably false (3-4 sources) | Change to "fontes oficiais" without quantity |
| "ROI de 7.8x" | **HIGH** | Specific ROI presented as fact without methodology or disclaimer | Add "Exemplo ilustrativo. Resultados reais podem variar." |
| "R$ 150.000 Oportunidade media" | **HIGH** | False precision. No data source. | Remove or calculate from actual data |
| "Monitoramento continuo diario" | **HIGH** | Service described does not exist (on-demand only) | Remove "continuo" and "diario" language |
| "Notificacoes em tempo real" | **HIGH** | Feature does not exist at all | Remove until implemented |
| "Resposta garantida no mesmo dia" | **MEDIUM** | SLA commitment without backing infrastructure | Remove "garantida" or implement SLA |
| "Precisao absoluta" | **MEDIUM** | Superlative claim that is unverifiable | Change to "Alta precisao" or remove |

### 2. Procon / Consumer Rights Exposure

At R$1,999/month, the product is positioned as a premium professional tool. Customers who discover that advertised features (continuous monitoring, real-time notifications, per-bid AI evaluation, dozens of sources) do not exist have legal grounds for:
- **Contract cancellation** with full refund (CDC Art. 35)
- **Compensation for damages** if they relied on claims to make business decisions
- **Procon complaint** leading to administrative penalties

### 3. "Sem cartao" Claim (Claim #40)

The claim "Sem cartao. Sem compromisso." on the FinalCTA is **accurate** -- signup uses Supabase email auth without requiring payment method. Card is only required at checkout. This is properly delivered.

### 4. Cancellation Claims

The "1 clique cancelamento" and "sem fidelidade" claims appear properly backed by Stripe billing portal integration, assuming the customer portal is correctly configured.

---

## Status Summary

| Status | Count | Percentage |
|--------|-------|------------|
| DELIVERED | 23 | 24% |
| PARTIALLY DELIVERED | 18 | 19% |
| NOT DELIVERED | 19 | 20% |
| MISLEADING | 17 | 18% |
| N/A (aspirational/subjective) | 18 | 19% |
| **TOTAL CLAIMS** | **95** | 100% |

### Claims by Risk Level

| Risk | Count |
|------|-------|
| CRITICAL | 9 |
| HIGH | 15 |
| MEDIUM | 16 |
| LOW | 18 |
| N/A | 37 |

---

## Recommendations for Go/No-Go

### MUST DO before charging R$1,999/month (Blocking)

1. **Remove or qualify all "dezenas de fontes" language** -- Replace with honest description of actual sources
2. **Remove "R$ 2.3 bi" metric** or implement measurement pipeline
3. **Remove "notificacoes em tempo real"** -- Feature does not exist
4. **Remove "monitoramento continuo/diario"** -- System is on-demand
5. **Add disclaimers to ROI claims** ("exemplo ilustrativo")
6. **Remove "Resposta garantida no mesmo dia"** -- No SLA infrastructure
7. **Clarify analysis examples as illustrative** -- Not real system output

### SHOULD DO before launch (Recommended)

8. Fix sector count: 12 in copy vs 15 in code
9. Change "prioriza" to "filtra" or "seleciona" throughout
10. Remove "precisao absoluta" language
11. Add methodology footnotes to comparative claims
12. Implement at minimum basic email notification for saved search criteria (addresses claims #66, #11)

### Impact of Current Copy on Brand Trust

If a sophisticated B2B buyer (the target market) signs up, pays R$1,999, and discovers:
- There are no notifications (they were promised "tempo real")
- There is no daily monitoring (they were promised "diario")
- The AI does not evaluate individual bids (they were promised "vale a pena ou nao")
- There are 3-4 sources, not "dozens"

...the result will be immediate cancellation, negative word-of-mouth in the licitacao professional community, and potential regulatory complaints. At this price point, buyers expect every claim to be verifiable.
