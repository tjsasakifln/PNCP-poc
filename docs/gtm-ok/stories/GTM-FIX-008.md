# GTM-FIX-008: Fix Mobile Navigation + Onboarding Touch Targets

## Dimension Impact
- Moves D03 (Mobile Experience) +0.5
- Moves D08 (Onboarding) +1

## Problem
Two critical mobile UX issues: (1) Landing page navbar is completely hidden on mobile (LandingNavbar.tsx:52 `hidden md:flex` - no hamburger menu), blocking access to pricing/features pages. (2) Onboarding UF selection buttons are too small (onboarding/page.tsx:351 `px-2 py-1 text-xs` = ~28px height) violating WCAG 2.1 touch target guidelines (minimum 44×44px).

## Solution
**Part A: Landing Navbar**
1. Add hamburger menu icon (visible on mobile only: `md:hidden`)
2. Implement slide-out mobile menu with full navigation
3. Include Login/Cadastro buttons in mobile menu
4. Add close button (X) and overlay backdrop

**Part B: Onboarding Touch Targets**
1. Increase UF button size from `px-2 py-1 text-xs` to `min-h-[44px] px-4 py-2 text-sm`
2. Increase sector card touch areas (currently 32px height → 44px)
3. Add larger tap zones for all interactive elements (CTAs, back button)

## Acceptance Criteria
- [ ] AC1: Hamburger icon visible on mobile (<768px) in LandingNavbar
- [ ] AC2: Clicking hamburger opens slide-out menu from right
- [ ] AC3: Mobile menu includes: Home, Recursos, Setores, Planos, Login, Cadastro
- [ ] AC4: Mobile menu overlay closes menu when clicked
- [ ] AC5: Close button (X) in top-right of mobile menu
- [ ] AC6: Navigation links in mobile menu close menu after click
- [ ] AC7: Onboarding UF buttons are min-h-[44px] (WCAG compliant)
- [ ] AC8: Onboarding sector cards are min-h-[44px] touch targets
- [ ] AC9: All CTAs (Avançar, Voltar, Começar Análise) are min-h-[44px]
- [ ] AC10: Frontend test: test_mobile_menu_opens_and_closes()
- [ ] AC11: Frontend test: test_onboarding_touch_targets_wcag_compliant()
- [ ] AC12: Manual test on iPhone 13 (390×844) - verify all interactive elements tappable
- [ ] AC13: Manual test on Android (360×640) - verify no layout overflow
- [ ] AC14: Lighthouse mobile accessibility score ≥90

## Effort: S (4h)
## Priority: P1 (Blocks mobile conversion)
## Dependencies: None

## Files to Modify
- `frontend/components/layout/LandingNavbar.tsx` (add mobile menu)
- `frontend/components/layout/MobileMenu.tsx` (NEW)
- `frontend/app/onboarding/page.tsx` (increase button sizes)
- `frontend/__tests__/layout/mobile-menu.test.tsx` (NEW)
- `frontend/__tests__/onboarding/touch-targets.test.tsx` (NEW)

## Testing Strategy
1. Component test: Render MobileMenu → click hamburger → verify menu opens
2. Component test: Click overlay → verify menu closes
3. Component test: Render onboarding UF buttons → measure height ≥44px
4. Visual regression test: Compare mobile screenshots before/after
5. Manual test: Real device testing on iOS + Android
6. Accessibility audit: Lighthouse + axe DevTools

## Mobile Menu Design Spec

**LandingNavbar changes:**
```tsx
{/* Desktop nav - existing */}
<nav className="hidden md:flex items-center gap-8">
  {/* existing links */}
</nav>

{/* Mobile hamburger - NEW */}
<button
  onClick={() => setMobileMenuOpen(true)}
  className="md:hidden p-2 hover:bg-gray-100 rounded-lg"
  aria-label="Abrir menu"
>
  <Menu className="w-6 h-6" />
</button>

<MobileMenu
  isOpen={mobileMenuOpen}
  onClose={() => setMobileMenuOpen(false)}
/>
```

**MobileMenu.tsx structure:**
```tsx
<AnimatePresence>
  {isOpen && (
    <>
      {/* Overlay */}
      <motion.div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      />

      {/* Slide-out menu */}
      <motion.div
        className="fixed top-0 right-0 h-full w-80 bg-white dark:bg-gray-900 z-50 shadow-2xl"
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
      >
        {/* Close button */}
        {/* Nav links */}
        {/* Auth buttons */}
      </motion.div>
    </>
  )}
</AnimatePresence>
```

## Touch Target Updates

**Onboarding UF buttons (before):**
```tsx
<button className="px-2 py-1 text-xs border rounded">
  {uf}
</button>
```

**After:**
```tsx
<button className="min-h-[44px] px-4 py-2 text-sm border rounded flex items-center justify-center">
  {uf}
</button>
```

**Onboarding sector cards (before):**
```tsx
<div className="p-3 border rounded cursor-pointer">
  {/* content */}
</div>
```

**After:**
```tsx
<div className="min-h-[44px] p-4 border rounded cursor-pointer flex items-center">
  {/* content */}
</div>
```

## Future Enhancement (not in scope)
- Swipe-to-close gesture for mobile menu
- Deep linking to mobile menu sections
- Progressive disclosure: Collapsible submenus for Recursos/Setores
- Bottom navigation bar for mobile (easier thumb reach)
