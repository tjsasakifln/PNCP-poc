# STORY-168: Component Architecture Design

**Date:** 2026-02-07
**Architect:** @architect (via Squad Creator)
**Story:** Landing Page Institucional + Conversão

## Component Dependency Graph

```
LandingPage (page.tsx)
├── LandingNavbar (sticky, global)
├── HeroSection
│   ├── Badge (credibilidade)
│   └── CTA Buttons (primary + secondary)
├── OpportunityCost
│   ├── Headline (provocativa)
│   └── 3 Key Points (list items)
├── BeforeAfter
│   ├── BeforeCard (left)
│   └── AfterCard (right)
├── DifferentialsGrid
│   └── 4 x DifferentialCard (icon + title + description)
├── HowItWorks
│   └── 3 x StepCard (numbered, with arrows)
├── StatsSection
│   └── 4 x StatCard (large number + label)
├── DataSourcesSection
│   ├── Headline (credibilidade)
│   ├── Source Badges (PNCP + complementares)
│   └── External Link (PNCP)
├── SectorsGrid
│   └── 12 x SectorCard (icon + name)
└── FinalCTA
    ├── Headline
    ├── Primary CTA Button
    └── Secondary Text (sem cartão)
```

## Component Props Interfaces (TypeScript)

```typescript
// ============================================================================
// LandingNavbar.tsx
// ============================================================================
interface LandingNavbarProps {
  className?: string;
}

// ============================================================================
// HeroSection.tsx
// ============================================================================
interface HeroSectionProps {
  className?: string;
}

interface CTAButton {
  label: string;
  variant: 'primary' | 'secondary';
  onClick: () => void;
}

// ============================================================================
// OpportunityCost.tsx
// ============================================================================
interface OpportunityCostProps {
  className?: string;
}

interface KeyPoint {
  text: string;
  icon?: React.ReactNode;
}

// ============================================================================
// BeforeAfter.tsx
// ============================================================================
interface BeforeAfterProps {
  className?: string;
}

interface ComparisonCard {
  title: string;
  points: string[];
  variant: 'before' | 'after';
}

// ============================================================================
// DifferentialsGrid.tsx
// ============================================================================
interface DifferentialsGridProps {
  className?: string;
}

interface DifferentialCard {
  icon: React.ReactNode;
  title: string;
  description: string;
}

// ============================================================================
// HowItWorks.tsx
// ============================================================================
interface HowItWorksProps {
  className?: string;
}

interface StepCard {
  stepNumber: number;
  title: string;
  description: string;
  icon?: React.ReactNode;
}

// ============================================================================
// StatsSection.tsx
// ============================================================================
interface StatsSectionProps {
  className?: string;
}

interface StatCard {
  value: string;
  label: string;
  highlight?: boolean; // Para destacar "Criado por servidores públicos"
}

// ============================================================================
// DataSourcesSection.tsx
// ============================================================================
interface DataSourcesSectionProps {
  className?: string;
}

interface DataSource {
  name: string;
  logo?: string;
  url?: string;
  isPrimary?: boolean; // PNCP é primary
}

// ============================================================================
// SectorsGrid.tsx
// ============================================================================
interface SectorsGridProps {
  className?: string;
}

interface SectorCard {
  icon: React.ReactNode;
  name: string;
}

// ============================================================================
// FinalCTA.tsx
// ============================================================================
interface FinalCTAProps {
  className?: string;
}
```

## Performance Optimization Strategy

### 1. Lazy Loading
- **Images:** Use Next.js `<Image>` component with `loading="lazy"` for all visual assets
- **Icons:** SVG inline (no external library) - small footprint
- **Sections:** All sections render immediately (no lazy loading for above-the-fold content)

### 2. Code Splitting
- **Route-based:** (landing)/ route group ensures landing page is separate bundle from (dashboard)/
- **Component-based:** No additional splitting needed (components are small)

### 3. Image/Icon Optimization
- **Strategy:** Use SVG icons inline (no external library)
- **Rationale:** Reduces bundle size, no network requests
- **Accessibility:** All SVG icons have `aria-label` or `role="img"`

### 4. Bundle Size Target
- **Target:** <200KB initial bundle (as per CLAUDE.md)
- **Measurement:** `npm run build` + analyze output
- **Mitigation:** No heavy libraries (Chart.js, etc.) - just Tailwind CSS

### 5. Lighthouse Performance
- **Target:** >90 score
- **Metrics:**
  - First Contentful Paint: <1.5s
  - Time to Interactive: <3s
  - Cumulative Layout Shift: <0.1
  - Largest Contentful Paint: <2.5s

## File Structure Validation

```
frontend/app/
├── (landing)/
│   ├── page.tsx                    # Main landing page
│   ├── layout.tsx                  # Layout específico landing (minimal wrapper)
│   └── components/
│       ├── HeroSection.tsx
│       ├── OpportunityCost.tsx
│       ├── BeforeAfter.tsx
│       ├── DifferentialsGrid.tsx
│       ├── HowItWorks.tsx
│       ├── StatsSection.tsx
│       ├── DataSourcesSection.tsx
│       ├── SectorsGrid.tsx
│       ├── FinalCTA.tsx
│       └── LandingNavbar.tsx
├── (dashboard)/
│   └── page.tsx                    # Interface de busca (existing, unchanged)
└── layout.tsx                      # Root layout (global)
```

**Notes:**
- Route group `(landing)/` ensures `/` maps to landing page
- Route group `(dashboard)/` will map to `/dashboard` (future authenticated route)
- `layout.tsx` in `(landing)/` can be minimal (just children wrapper)
- Root `layout.tsx` stays global (theme provider, fonts)

## Design System Patterns

### Reusable Utility Classes (Tailwind)

```typescript
// frontend/app/(landing)/utils/classNames.ts
export const sectionContainer = "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24";
export const headlineText = "text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white";
export const subheadlineText = "text-lg sm:text-xl text-gray-600 dark:text-gray-300 mt-4";
export const ctaPrimary = "bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors";
export const ctaSecondary = "border-2 border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 font-semibold px-6 py-3 rounded-lg transition-colors";
export const cardBase = "bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow";
```

### Tailwind Config Extensions

**No new dependencies needed.** Existing Tailwind config supports:
- Responsive breakpoints (sm, md, lg, xl)
- Dark mode (class-based)
- Utility classes for spacing, colors, typography

### Consistent Patterns

1. **Section Wrapper:**
   ```tsx
   <section className={sectionContainer}>
     {/* content */}
   </section>
   ```

2. **Card Hover Effect:**
   ```tsx
   <div className={cardBase}>
     {/* content */}
   </div>
   ```

3. **CTA Buttons:**
   ```tsx
   <button className={ctaPrimary}>Primary Action</button>
   <button className={ctaSecondary}>Secondary Action</button>
   ```

## Accessibility Requirements Checklist

### Semantic HTML
- [ ] Use `<section>` for each major content block
- [ ] Use `<header>` for LandingNavbar
- [ ] Use `<nav>` for navigation links
- [ ] Use `<footer>` for footer section
- [ ] Use `<h1>` for main headline (Hero Section)
- [ ] Use `<h2>` for section headlines
- [ ] Use `<h3>` for card titles

### ARIA Labels
- [ ] All icon-only buttons have `aria-label`
- [ ] External links have `aria-label` with "opens in new tab" note
- [ ] SVG icons have `role="img"` and `aria-label` if meaningful (or `aria-hidden="true"` if decorative)

### Keyboard Navigation
- [ ] All interactive elements are focusable (buttons, links)
- [ ] Focus states visible (ring utilities in Tailwind)
- [ ] Scroll-to-section button works with Enter key
- [ ] Skip-to-content link (optional, recommended)

### Contrast Ratios (WCAG AA)
- [ ] Text on background: minimum 4.5:1 for normal text
- [ ] Large text (>18pt or 14pt bold): minimum 3:1
- [ ] Interactive elements: minimum 3:1 for borders/focus states
- [ ] Test with Chrome DevTools Lighthouse

### Screen Reader Support
- [ ] Alt text for all images (if any)
- [ ] `aria-label` for icon buttons
- [ ] Proper heading hierarchy (h1 → h2 → h3, no skips)
- [ ] Lists use `<ul>` and `<li>` (not div spam)

## Component Implementation Order (For @dev)

**Recommended sequence for parallel development:**

### Group 1: Foundational Components (Start First)
1. `LandingNavbar.tsx` - Required for page structure
2. `HeroSection.tsx` - Above-the-fold, highest priority
3. `FinalCTA.tsx` - Simple, can be done quickly

### Group 2: Content Sections (Parallel)
4. `OpportunityCost.tsx`
5. `BeforeAfter.tsx`
6. `DifferentialsGrid.tsx`
7. `HowItWorks.tsx`

### Group 3: Data-Driven Sections (Parallel)
8. `StatsSection.tsx`
9. `DataSourcesSection.tsx`
10. `SectorsGrid.tsx`

### Group 4: Integration
11. `page.tsx` - Assemble all components

## Testing Strategy (For @qa)

### Unit Tests (Jest + React Testing Library)
- Test each component renders without crashing
- Test responsive behavior (mock window.matchMedia)
- Test interactive elements (button clicks, link navigation)
- Test accessibility (aria-labels, semantic HTML)

### E2E Tests (Playwright)
- Test full landing page navigation flow
- Test scroll-to-section behavior ("Ver como funciona")
- Test CTA button navigation (Login, Signup)
- Test responsive breakpoints (mobile, tablet, desktop)

### Performance Tests
- Lighthouse CI threshold: >90 (Performance, Accessibility, Best Practices, SEO)
- Bundle size check: <200KB initial

## Handoff to @dev

**All component specs are ready for implementation.**

**Priority:** Start with Group 1 (Navbar, Hero, Final CTA), then parallelize Groups 2 and 3.

**Reference files:**
- `frontend/app/page.tsx` (existing structure)
- `PRD.md` (TypeScript standards)
- `CLAUDE.md` (coding standards, testing requirements)

**Next steps:**
1. Create `(landing)/` route group
2. Implement components in order above
3. Write unit tests for each component
4. Assemble in `page.tsx`
5. Run E2E tests

---

**Architect:** @architect (Kira)
**Reviewed by:** Squad Creator
**Status:** Ready for Implementation
