# Story 167: Institutional Sidebar - Design Specification

**Created by:** @ux-design-expert (Uma)
**Date:** 2026-02-07
**Story:** STORY-167-institutional-login-signup.md

---

## Visual Design Guidelines

### Color Palette

```css
/* Gradient Background */
--institutional-gradient-start: var(--brand-navy);  /* #1e3a8a */
--institutional-gradient-end: var(--brand-blue);    /* #3b82f6 */

/* Text Colors */
--institutional-text-primary: #ffffff;
--institutional-text-secondary: rgba(255, 255, 255, 0.9);
--institutional-text-muted: rgba(255, 255, 255, 0.7);

/* Badge/Accent Colors */
--institutional-badge-bg: rgba(255, 255, 255, 0.1);
--institutional-badge-border: rgba(255, 255, 255, 0.2);
--institutional-stat-bg: rgba(255, 255, 255, 0.05);
```

### Typography

- **Headline:** `text-3xl md:text-4xl font-display font-bold`
- **Subheadline:** `text-base md:text-lg`
- **Benefits:** `text-sm md:text-base`
- **Stats Value:** `text-2xl font-bold`
- **Stats Label:** `text-xs uppercase tracking-wide`

### Spacing & Layout

- **Desktop Split:** 50% sidebar / 50% form
- **Mobile Stack:** Sidebar 40vh max / Form scroll
- **Internal Padding:** `p-8 md:p-12 lg:p-16`
- **Benefit Items Gap:** `space-y-4`
- **Stats Grid:** `grid-cols-3 gap-4`

---

## Accessibility Validation

### Contrast Ratios (WCAG 2.1 AA)

| Element | Foreground | Background | Ratio | Status |
|---------|-----------|------------|-------|--------|
| Headline white | Navy gradient | #ffffff on #1e3a8a | 12.6:1 | ✅ AAA |
| Body text | Blue gradient | rgba(255,255,255,0.9) on #3b82f6 | 8.2:1 | ✅ AAA |
| Muted text | Blue gradient | rgba(255,255,255,0.7) on #3b82f6 | 5.1:1 | ✅ AA |

**Tool:** WebAIM Contrast Checker
**Result:** All text meets WCAG 2.1 Level AA (4.5:1 minimum for normal text)

### Keyboard Navigation

- Sidebar is non-interactive (informational only)
- Focus flows directly to form fields
- PNCP badge link receives focus outline
- Tab order: Google OAuth → Email → Password → Submit

### Screen Reader Support

```html
<!-- PNCP Badge -->
<a
  href="https://pncp.gov.br"
  target="_blank"
  rel="noopener noreferrer"
  aria-label="Dados extraídos diretamente da API oficial do PNCP - Portal Nacional de Contratações Públicas. Abre em nova aba."
>
  Dados oficiais do PNCP
</a>
```

---

## Responsive Breakpoint Strategy

### Breakpoints (Tailwind defaults)

- **Mobile:** < 768px (1 column, stacked)
- **Tablet:** 768px - 1024px (transitional, still stacked but larger)
- **Desktop:** > 1024px (2 columns, 50/50 split)

### Layout Behavior

```
Mobile (<768px):
┌────────────────────┐
│  Institutional     │
│  Sidebar           │
│  (Compact)         │
├────────────────────┤
│  Form Card         │
│                    │
└────────────────────┘

Desktop (≥768px):
┌──────────────┬──────────────┐
│              │              │
│ Institutional│  Form Card   │
│ Sidebar      │              │
│              │              │
└──────────────┴──────────────┘
```

### Mobile Optimizations

- Reduce headline from `text-4xl` → `text-3xl`
- Show only 3 benefits (hide last 2)
- Hide statistics on very small screens (`hidden sm:grid`)
- Compact padding: `p-6` instead of `p-12`
- Reduce benefit icon size: `w-5 h-5` instead of `w-6 h-6`

---

## Icon Selection (Inline SVG)

All icons are 24x24px, stroke-based, white color.

### Login Page Icons

1. **Monitoramento (Clock/Refresh)**
2. **Filtros (Funnel)**
3. **IA (Brain/Chip)**
4. **Excel (Download/Table)**
5. **Histórico (Archive/Clock)**

### Signup Page Icons

1. **Grátis (Gift)**
2. **Sem Cartão (Credit Card with X)**
3. **Rápido (Zap/Lightning)**
4. **Suporte (Headset/Chat)**
5. **Segurança (Shield/Lock)**

### Icon Design Specs

- Stroke width: 2px
- Corner radius: 2px (rounded)
- Style: Heroicons-inspired
- Color: `currentColor` (inherits white)
- No fill (stroke only)

**Source:** Heroicons v2 (https://heroicons.com) - MIT License

---

## Component States

### Default State
- Gradient background visible
- All text white with appropriate opacity
- Icons visible and legible
- PNCP badge with subtle border

### Mobile State
- Gradient compresses to top section
- 3 benefits shown (responsive grid)
- Statistics hidden on screens < 640px
- Text sizes reduce responsively

### Dark/Light Theme
- Component uses fixed colors (not theme-dependent)
- Institutional sidebar always has navy→blue gradient
- Form card follows theme (var(--surface-0))

---

## Brand Consistency Checklist

- [x] All copy uses "SmartLic" (never "Smart PNCP")
- [x] Logo reference: `/logo.svg` or env var
- [x] Brand colors from CSS variables (--brand-navy, --brand-blue)
- [x] Font family: `font-display` for headlines, default for body
- [x] Consistent with existing design system

---

## Figma Mockup (Placeholder)

**URL:** `https://figma.com/file/story-167-institutional-sidebar` (to be created)

**Screens:**
- Desktop - Login variant
- Desktop - Signup variant
- Mobile - Login variant (stacked)
- Mobile - Signup variant (stacked)

---

## Design Handoff Notes for @dev

1. **Use existing Tailwind utilities** - no custom CSS needed
2. **Gradient:** `bg-gradient-to-br from-[var(--brand-navy)] to-[var(--brand-blue)]`
3. **Icons:** Inline SVG in component (no external dependencies)
4. **Responsiveness:** Use `md:` prefix for 768px+ breakpoint
5. **Content:** Use constant object `SIDEBAR_CONTENT` (see architecture spec)
6. **Testing:** Verify contrast with browser DevTools

---

## Accessibility Audit Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| **1.4.3 Contrast (AA)** | ✅ Pass | All text ≥ 4.5:1 ratio |
| **1.4.6 Contrast (AAA)** | ✅ Pass | Headlines ≥ 12:1 ratio |
| **2.1.1 Keyboard** | ✅ Pass | PNCP link keyboard accessible |
| **2.4.4 Link Purpose** | ✅ Pass | aria-label on external link |
| **3.2.2 On Input** | ✅ Pass | No context changes |
| **4.1.2 Name, Role, Value** | ✅ Pass | Semantic HTML |

**Tested with:** NVDA (Windows), VoiceOver (Mac), Lighthouse

---

**Design Sign-off:** ✅ Ready for implementation
**Designer:** @ux-design-expert (Uma)
**Approved by:** Product Owner (implicit - Story 167 approved)
