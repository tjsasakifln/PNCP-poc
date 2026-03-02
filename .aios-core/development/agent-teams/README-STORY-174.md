# STORY-174 Squad - Quick Reference

## 🎯 One-Command Activation

```bash
/squad-creator team-story-174-landing-redesign
```

---

## 👥 Squad Composition (8 Agents)

| Agent | Icon | Focus | Parallel Stream |
|-------|------|-------|-----------------|
| **Olivia** | 🎨 | Design System, Responsive | Stream 1: Design |
| **Morgan** | 🏗️ | Architecture, Performance | Stream 1: Design |
| **Alex #1** | 💻 | Hero, Value Props, Table | Stream 2: Core UI |
| **Alex #2** | 💻 | Sectors, Testimonials, Footer | Stream 3: Secondary UI |
| **Casey** | ⚡ | Animations, Scroll Effects | Stream 6: Animations |
| **Quinn** | ✅ | QA, A11y, Visual Regression | Stream 4: Quality |
| **Gage** | 🚀 | Bundle, Lighthouse, WebP | Stream 7: Performance |
| **Jordan** | 📊 | Coordination, Progress | Stream 5: Orchestration |

---

## 📋 3-Phase Execution

### Phase 1: Foundation (2h)
```
4 parallel streams → Design system + Base components + Testing setup
```

### Phase 2: Implementation (4h)
```
3 parallel streams → Hero + Value Props + Table + Sectors + Testimonials + Footer
```

### Phase 3: Refinement (3h)
```
3 parallel streams → Responsive + Performance + Quality Assurance
```

**Total:** 9h with maximum parallelization

---

## 📊 Deliverables Checklist

### Components Created/Modified
- [ ] `GlassCard.tsx` (NEW - reusable glassmorphism component)
- [ ] `GradientButton.tsx` (NEW - premium button with glow)
- [ ] `BentoGrid.tsx` (NEW - asymmetric grid layout)
- [ ] `HeroSection.tsx` (REDESIGN - gradient text, animated CTAs)
- [ ] `ValuePropSection.tsx` (REDESIGN - bento grid, glassmorphism)
- [ ] `ComparisonTable.tsx` (REDESIGN - sticky header, animated checks)
- [ ] `SectorsGrid.tsx` (REDESIGN - 3D tilt, gradient overlays)
- [ ] `TestimonialsCarousel.tsx` (NEW - carousel with glassmorphism)
- [ ] `Footer.tsx` (REDESIGN - gradient separator, link animations)

### Infrastructure
- [ ] `globals.css` (CSS variables: colors, typography, spacing, shadows)
- [ ] `tailwind.config.ts` (Extended theme: brand colors, custom shadows, animations)
- [ ] `scrollAnimations.ts` (Intersection Observer hooks)
- [ ] `framerVariants.ts` (Framer Motion animation variants)
- [ ] `easing.ts` (Custom easing curves)

### Quality Gates
- [ ] Visual regression tests pass
- [ ] A11y audit passes (keyboard nav, screen readers, contrast)
- [ ] Cross-browser tests pass (Chrome, Safari, Firefox, Edge)
- [ ] Animation performance verified (60fps, no jank)
- [ ] Bundle size < 150KB gzipped
- [ ] Lighthouse score 95+
- [ ] Core Web Vitals < thresholds (LCP <2.5s, FID <100ms, CLS <0.1)

---

## 🎯 Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Bounce Rate | 60% | 36% | -40% |
| Time on Page | 45s | 67s | +50% |
| Trial Signup | 2.5% | 3.25% | +30% |
| Lighthouse | ~78 | 95+ | +17 points |

---

## 📚 Key Resources

- **Squad Config:** `team-story-174-landing-redesign.yaml`
- **Activation Guide:** `tasks/story-174-squad-activation.md`
- **Squad Summary:** `docs/squads/SQUAD-STORY-174-SUMMARY.md`
- **Story:** `docs/stories/STORY-174-landing-page-visual-redesign.md`

---

## 🎨 Design References

| Site | Steal This |
|------|-----------|
| **Linear** | Dark theme, gradient text, floating elements |
| **Notion** | Bento grids, glassmorphism, testimonials |
| **Stripe** | Gradient backgrounds, animated tables |
| **Vercel** | Black/white with accent, geometric patterns |
| **Raycast** | Glassmorphism everywhere, smooth scroll |

---

## ⚡ Maximum Parallelization Commands

### Start All Streams Simultaneously

```bash
# Phase 1: Foundation (4 parallel streams)
@ux-design-expert *start "Design system foundation" &
@architect *start "Component architecture" &
@devops *start "Infrastructure setup" &
@dev *start "Base components" &
@qa *start "Testing setup"

# Phase 2: Core Implementation (3 parallel streams)
@dev *start "Hero + Value Props" &
@dev *start "Table + Sectors" &
@ux-design-expert *start "Footer + Testimonials" &
@data-engineer *start "Animations"

# Phase 3: Refinement (3 parallel streams)
@ux-design-expert *start "Responsive design" &
@devops *start "Performance optimization" &
@qa *start "Quality assurance"

# Coordination (runs throughout)
@pm *start "Track progress and orchestrate"
```

---

## 🛡️ Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Animation jank | CSS transforms, lazy-load Framer Motion, test on low-end devices |
| Bundle bloat | Dynamic imports, tree-shake Tailwind, monitor bundle size |
| Brand inconsistency | Document design system, create reusable components |

---

**Status:** 🚀 Ready for Activation
**Last Updated:** 2026-02-09
