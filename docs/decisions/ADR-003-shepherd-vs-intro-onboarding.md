# ADR-003: Choose Shepherd.js over Intro.js for Interactive Onboarding

**Status:** ✅ Accepted
**Date:** 2026-01-30
**Deciders:** @architect (Aria), @dev (James)
**Context:** Feature #3 - Interactive Onboarding implementation for BidIQ Uniformes

---

## Context and Problem Statement

We need to implement an interactive onboarding wizard to help new users understand the BidIQ platform. The onboarding should:

1. Guide users through 3 steps (Welcome → Demo → Your turn)
2. Be customizable with Tailwind CSS
3. Support skip/dismiss functionality
4. Track completion status (localStorage)
5. Allow re-triggering the wizard
6. Be lightweight and well-maintained

Two main libraries were evaluated: **Shepherd.js** and **Intro.js**.

---

## Decision Drivers

- **TypeScript support**: First-class TS types required
- **Customizability**: Must work with Tailwind CSS design system
- **Bundle size**: Frontend performance is critical (target <200KB initial)
- **Maintenance**: Active development and community support
- **Licensing**: Must be compatible with commercial use
- **React integration**: Clean React hooks/components pattern
- **Accessibility**: WCAG 2.1 AA compliance (required for Phase 3 QA)

---

## Considered Options

### Option 1: Shepherd.js
- **Version:** 14.4.0
- **License:** MIT
- **Bundle size:** ~20KB (gzipped)
- **TypeScript:** ✅ Native TypeScript support
- **React:** ✅ Clean React integration
- **Last update:** Active (Dec 2024)
- **Stars:** 13k+ on GitHub

### Option 2: Intro.js
- **Version:** 7.2.0
- **License:** AGPL (commercial license required) / MIT (for open-source)
- **Bundle size:** ~15KB (gzipped)
- **TypeScript:** ⚠️ Community types (@types/intro.js)
- **React:** ⚠️ Wrapper needed
- **Last update:** Active (Nov 2024)
- **Stars:** 22k+ on GitHub

---

## Decision Outcome

**Chosen option:** **Shepherd.js**

### Rationale

1. **MIT License**: No commercial license concerns (Intro.js AGPL is risky for commercial POC)
2. **Native TypeScript**: First-class TypeScript support without community types
3. **Better React Integration**: Designed for modern frameworks, cleaner hooks pattern
4. **Accessibility Focus**: Better ARIA labels, keyboard navigation (critical for QA Phase 3)
5. **Proven in Production**: Used by GitHub, Dropbox, Google
6. **Tailwind Compatibility**: Easier to style with utility classes (documented examples)
7. **Smaller Bundle**: 20KB vs 15KB is acceptable (5KB difference negligible)

### Pros

- ✅ **Zero licensing risk** - MIT license, no commercial restrictions
- ✅ **Type-safe** - Native TypeScript, reduces bugs
- ✅ **Accessible** - WCAG 2.1 AA compliant (required for QA sign-off)
- ✅ **Customizable** - Full control over CSS, works with Tailwind
- ✅ **Well-documented** - Extensive docs, many examples
- ✅ **Active community** - Regular updates, responsive maintainers

### Cons

- ⚠️ **Slightly larger bundle** - 5KB extra (acceptable for value gained)
- ⚠️ **Learning curve** - More configuration options (but better docs)

---

## Alternatives Considered and Rejected

### Why not Intro.js?

- **AGPL license risk**: Commercial use unclear, would need paid license ($19/month/domain)
- **Community types**: @types/intro.js maintained separately, version lag risk
- **React wrapper complexity**: Needs extra wrapper library (introjs-react)
- **Accessibility gaps**: Less focus on ARIA labels, keyboard nav

### Why not custom build?

- **Time constraint**: Phase 3 is 3 days (Day 8-10), Feature #3 is 8 SP
- **Complexity**: Tour logic, positioning, animations, accessibility = high effort
- **Maintenance burden**: Library updates are free, custom code requires ongoing work

---

## Implementation Plan

### Day 8 (Today)
- [x] Install Shepherd.js 14.4.0
- [x] Create `useOnboarding` hook skeleton
- [ ] Import Shepherd CSS and customize with Tailwind

### Day 9
- [ ] Implement 3-step wizard:
  - Step 1: Welcome & value proposition
  - Step 2: Interactive demo (trigger real search)
  - Step 3: Your turn (prompt user's first search)
- [ ] localStorage completion flag (`bidiq_onboarding_completed`)
- [ ] Skip button + re-trigger logic

### Day 10
- [ ] Custom Tailwind styling (match BidIQ design system)
- [ ] Integration with main page.tsx
- [ ] QA testing (accessibility, mobile, cross-browser)

---

## Validation

### Success Criteria
- [ ] All 3 steps complete successfully
- [ ] Skip button works, completion flag persists
- [ ] Re-trigger via button (for returning users)
- [ ] WCAG 2.1 AA compliance (axe-core scan passes)
- [ ] Mobile responsive (iOS Safari + Android Chrome)
- [ ] Cross-browser (Chrome, Firefox, Safari, Edge)

### Rollback Plan

If Shepherd.js blocks implementation (e.g., CSS conflicts, performance issues):

1. **Fallback to Intro.js** (estimated 4 hours rework)
   - Use MIT version (open-source compliant)
   - Accept community types (@types/intro.js)
   - Add introjs-react wrapper

2. **Delay Feature #3** to Phase 4 (if time constraint)
   - Mark as SHOULD HAVE instead of MUST HAVE
   - Prioritize bugfixes and testing

---

## References

- **Shepherd.js Docs:** https://shepherdjs.dev/
- **Shepherd.js GitHub:** https://github.com/shepherd-pro/shepherd
- **Intro.js Docs:** https://introjs.com/
- **Tailwind Integration Example:** https://shepherdjs.dev/docs/tutorial-examples.html#custom-styling
- **WCAG 2.1 AA Checklist:** https://www.w3.org/WAI/WCAG21/quickref/?currentsidebar=%23col_customize&levels=aaa

---

**Decision recorded by:** @architect (Aria)
**Implemented by:** @dev (James)
**Reviewed by:** @pm (Morgan)
**Phase:** Value Sprint 01 - Phase 3 - Day 8
