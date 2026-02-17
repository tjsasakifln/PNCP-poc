# GTM-FIX-003: Rewrite Copy to Match Delivered Features

## Dimension Impact
- Moves D09 (Copy Accuracy) from 4/10 to 7/10

## Problem
108 marketing claims made across landing page, features, and pricing pages. 19 are NOT DELIVERED (real-time notifications, continuous monitoring, pipeline management), 17 are MISLEADING ("Dezenas de fontes" = actually 3-4, "R$ 2.3 bi analisados" = no measurement), 23 are VAGUE ("inteligência artificial" without specifics). Current copy creates false expectations.

## Solution
1. Audit all 13 user-facing copy files
2. Replace/qualify/remove NOT DELIVERED claims
3. Add disclaimers to ROI figures ("exemplo baseado em caso real")
4. Replace vague AI claims with specifics ("GPT-4o para resumos executivos")
5. Change "Dezenas de fontes" → "Portal PNCP + 4 sistemas estaduais"
6. Change "Monitoramento contínuo" → "Buscas programadas diárias"
7. Remove "notificações em tempo real" or qualify as "planned feature"
8. Add "beta" or "preview" labels to incomplete features

## Acceptance Criteria
- [x] AC1: HeroSection.tsx headline passes fact-check (no undelivered claims) — removed "R$ 2.3 bi" unverified claim, fixed sector count 12→15
- [x] AC2: StatsSection.tsx ROI figures include disclaimers or removed — replaced R$ 2.3bi hero with "15 setores", fixed "12 setores"→"1000+ regras", "monitoramento contínuo"→"análises programadas"
- [x] AC3: DifferentialsGrid.tsx removes "notificações em tempo real" claim — removed "Atualização contínua em tempo real", "Todas as fontes oficiais monitoradas"→"PNCP e PCP integrados"
- [x] AC4: DataSourcesSection.tsx changes "Dezenas de fontes" → "Portal PNCP + Portal de Compras Públicas" — complete rewrite with accurate dual-source claims
- [x] AC5: SectorsGrid.tsx sector claims match actual backend coverage (15 sectors verified against sectors_data.yaml)
- [x] AC6: HowItWorks.tsx — already accurate, no false claims found
- [ ] AC7: BeforeAfter.tsx — FILE DOES NOT EXIST (not yet created)
- [ ] AC8: OpportunityCost.tsx — FILE DOES NOT EXIST (not yet created)
- [ ] AC9: comparisons.ts — FILE DOES NOT EXIST (not yet created)
- [ ] AC10: valueProps.ts — FILE DOES NOT EXIST (not yet created)
- [ ] AC11: analysisExamples.ts — FILE DOES NOT EXIST (not yet created)
- [x] AC12: planos/page.tsx plan features list matches quota.py — removed "Processamento prioritário" (Pro=NORMAL), fixed AI claim to "GPT-4o", added "1000+ regras", qualified ROI example
- [x] AC13: All NOT DELIVERED claims in existing files removed or qualified — "em tempo real", "monitoramento contínuo", "dezenas de fontes" all fixed
- [x] AC14: All MISLEADING claims in existing files qualified — "R$ 2.3 bi" removed, "12 setores"→15, ROI qualified as "exemplo ilustrativo", sources made specific
- [ ] AC15: Manual review by non-technical stakeholder confirms accuracy

## Effort: M (2-3 days)
## Priority: P0 (Legal/reputation risk)
## Dependencies: None

## Files to Modify
- `frontend/components/landing/HeroSection.tsx`
- `frontend/components/landing/StatsSection.tsx`
- `frontend/components/landing/DifferentialsGrid.tsx`
- `frontend/components/landing/DataSourcesSection.tsx`
- `frontend/components/landing/SectorsGrid.tsx`
- `frontend/components/landing/HowItWorks.tsx`
- `frontend/components/landing/BeforeAfter.tsx`
- `frontend/components/landing/OpportunityCost.tsx`
- `frontend/lib/constants/comparisons.ts`
- `frontend/lib/constants/valueProps.ts`
- `frontend/lib/constants/analysisExamples.ts`
- `frontend/app/planos/page.tsx`

## Testing Strategy
1. Extract all user-visible strings from modified files
2. Fact-check each claim against backend code + PNCP API capabilities
3. Legal review: Ensure no misleading advertising (CONAR, CDC compliance)
4. A/B test revised copy vs original on conversion rate (track with Mixpanel)

## NOT DELIVERED Claims to Remove/Qualify
1. "Notificações em tempo real" → Remove or mark "em desenvolvimento"
2. "Monitoramento contínuo 24/7" → Change to "Buscas programadas"
3. "Gestão completa de pipeline" → Mark as "beta" or remove
4. "Alertas personalizados" → Remove (no alert system exists)
5. ~~"Dezenas de fontes de dados" → "Portal PNCP + sistemas estaduais"~~ **REVISADO (PCP API):** Agora com 2 fontes reais, usar: "Portal PNCP + Portal de Compras Públicas" (claim de "múltiplas fontes" torna-se legítimo, mas ainda não são "dezenas")
6. "R$ 2.3 bilhões em oportunidades" → Add "exemplo baseado em análise de X dias"
7. "300+ horas economizadas por mês" → Add source/methodology or remove

## Copy Tone Guidelines (for revisions)
- Be specific: "GPT-4o" not "IA avançada"
- Be honest: "buscas diárias" not "monitoramento em tempo real"
- Be measurable: "até 90% de redução de tempo" with asterisk linking to methodology
- Be conservative: Under-promise, over-deliver

## ⚠️ REVISÃO — Impacto PCP API (2026-02-16)

**Contexto:** A obtenção da API key do Portal de Compras Públicas (PCP) muda o claim de fontes de dados.

**Alterações nesta story:**

1. **AC4 revisado:** `DataSourcesSection.tsx` deve agora listar **2 fontes reais**: "Portal PNCP" + "Portal de Compras Públicas". O claim "Dezenas de fontes" ainda é falso (são 2, não dezenas), mas o texto pode ser: **"Duas das maiores bases de licitações públicas do Brasil"** em vez de "Portal PNCP + sistemas estaduais".

2. **AC16 (DONE):** Todas as referências a "fonte única" ou que impliquem exclusividade PNCP atualizadas para refletir dual-source:
   - DataSourcesSection: "Dezenas de fontes" → "PNCP + Portal de Compras Públicas"
   - DifferentialsGrid: "múltiplas fontes" → "PNCP e Portal de Compras Públicas"
   - planos/page.tsx: "setores monitorados" → "PNCP e Portal de Compras Públicas integrados"

3. **Impacto no effort:** Sem aumento — é apenas ajuste de texto no mesmo escopo.

**Dependência:** Se GTM-FIX-011 (integração PCP) for implementada antes desta story, os claims de fontes serão verdadeiros. Se GTM-FIX-003 for implementada primeiro, usar "em breve" para PCP até que GTM-FIX-011 entre.
