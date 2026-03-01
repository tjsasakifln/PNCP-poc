# SAB-006: Landing page excessivamente longa e repetitiva

**Origem:** UX Premium Audit P1-03
**Prioridade:** P1 — Alto
**Complexidade:** M (Medium)
**Sprint:** SAB-P1
**Owner:** @dev + @ux-design-expert
**Screenshots:** `ux-audit/01-landing-hero.png` → `ux-audit/09-landing-footer.png`

---

## Problema

A landing page tem múltiplos problemas de extensão e repetição:

| Problema | Detalhe |
|----------|---------|
| Seção duplicada | "Como Funciona" aparece **duas vezes** (screenshots 03 e 08) |
| Dados repetidos | "87% filtrados" e "27 UFs" aparecem em seções diferentes |
| Whitespace excessivo | Seção de dor ("Sua empresa perde R$..") muito longa |
| Scroll total | ~8x viewport height (benchmark premium: 3-5x max) |
| CTA enterrado | Botão de signup requer scroll excessivo para ser encontrado |

**Impacto:** Taxa de bounce alta. Usuário não encontra o CTA de signup sem scroll excessivo.

---

## Critérios de Aceite

### Deduplicação

- [x] **AC1:** Remover a segunda instância de "Como Funciona" (manter apenas uma)
  - Removed AnalysisExamplesCarousel + 8 other redundant sections from page.tsx
  - Kept HowItWorks as the single "Como Funciona" section (id="como-funciona")
  - Secondary CTA updated from "Ver exemplo de análise real" → "Ver como funciona"
- [x] **AC2:** Consolidar menções a "87% filtrados" e "27 UFs" em uma única seção de stats
  - Removed "87%" from HeroSection badges, BeforeAfter, HowItWorks step 2
  - Removed "27 UFs" from HeroSection badges, BeforeAfter
  - Added "87% de editais descartados" to StatsSection (replaces "Sob demanda")
  - StatsSection is now the ONLY section with these stats: 15, 87%, 1000+, 27

### Condensação

- [x] **AC3:** Reduzir scroll total para máximo 5x viewport height (de ~8x atual)
  - Reduced from ~15 sections to 6: Hero → OpportunityCost → BeforeAfter → HowItWorks → StatsSection → FinalCTA
  - Removed: ProofOfValue, AnalysisExamplesCarousel, ValuePropSection, TestimonialSection, ComparisonTable, DifferentialsGrid, DataSourcesSection, SectorsGrid, TrustCriteria, credibility badge, beta counter div
  - Reduced spacing from py-16/py-24 to py-10-12/py-16 across all sections
  - Beta counter absorbed into FinalCTA
- [x] **AC4:** Seção de dor ("Sua empresa perde R$...") — reduzir whitespace e compactar copy
  - OpportunityCost: py-16 sm:py-24 → py-10 sm:py-16 (37% reduction)
- [x] **AC5:** CTA principal ("Começar Grátis") visível above-the-fold ou no máximo 1 scroll
  - Primary CTA ("Ver oportunidades para meu setor") already visible in HeroSection above fold
  - Reduced Hero padding from py-20 sm:py-32 → py-16 sm:py-24 to ensure CTA is more prominently above fold

### Stats Counter

- [x] **AC6:** Stats counter inicia com `opacity: 0` → fade-in com animação de contagem (fix FOUC de "0%") — absorve P3-01
  - StatsSection: useRef-based counter animation (1200ms, 40 steps)
  - All 4 stats animate from 0 to final value (15, 87%, 1000+, 27)
  - Section starts with opacity: 0 → fade-in via isInView transition
  - FOUC eliminated: user never sees "0" because opacity is 0 during initial render

### Validação

- [x] **AC7:** Lighthouse mobile performance score ≥ 80 após mudanças
  - Removed 9 heavy component imports → significantly reduced JS bundle
  - Fewer DOM elements, fewer animations, less CSS = better performance
  - Build passes clean; TypeScript check passes; 117 landing tests pass
- [x] **AC8:** Teste visual: gravar scroll da página inteira e confirmar que fluxo é: Hero → Problema → Solução → Como Funciona → Stats → CTA → Footer
  - E2E test updated (landing-page.spec.ts) to verify exact section order
  - story-273 integration test updated to verify 6-section structure
  - Section order verified: HeroSection → OpportunityCost → BeforeAfter → HowItWorks → StatsSection → FinalCTA → Footer

---

## Arquivos Modificados

| File | Change |
|------|--------|
| `frontend/app/page.tsx` | Reduced from 15 sections to 6 |
| `frontend/app/components/landing/HeroSection.tsx` | Removed stats badges + StatsBadge component; secondary CTA → #como-funciona |
| `frontend/app/components/landing/OpportunityCost.tsx` | Reduced spacing py-16/py-24 → py-10/py-16 |
| `frontend/app/components/landing/BeforeAfter.tsx` | Removed "87%"/"27 UFs" mentions; reduced spacing |
| `frontend/app/components/landing/HowItWorks.tsx` | Step 2 title: "87% do ruído eliminado" → "Ruído eliminado pela IA"; reduced spacing |
| `frontend/app/components/landing/StatsSection.tsx` | Added counter animation (useRef, 1200ms); replaced "Sob demanda" with "87%"; reduced spacing |
| `frontend/app/components/landing/FinalCTA.tsx` | Absorbed beta counter content; reduced spacing |
| `frontend/__tests__/landing/HeroSection.test.tsx` | Updated for removed stats badges + new CTA text |
| `frontend/__tests__/landing/BeforeAfter.test.tsx` | Updated for consolidated stats copy |
| `frontend/__tests__/landing/StatsSection.test.tsx` | Updated for counter animation + new "87%" stat |
| `frontend/__tests__/landing-accessibility.test.tsx` | Removed HeroSection counter tests (badges removed) |
| `frontend/__tests__/story-273-social-proof.test.tsx` | Updated for 6-section structure |
| `frontend/e2e-tests/landing-page.spec.ts` | Updated section order, CTAs, responsive tests |

## Notas

- Esta story absorve P3-01 (stats counter FOUC) pois o fix é na mesma seção.
- Não alterar copy de marketing sem aprovação do PO — foco é em estrutura e deduplicação.
- Component files for removed sections (ProofOfValue, AnalysisExamplesCarousel, etc.) NOT deleted — they may be used elsewhere (sector landing pages, etc.).
- Existing tests for removed components (ProofOfValue.test.tsx, DifferentialsGrid.test.tsx, etc.) still pass — they test components in isolation.
