# DEBT-126: WhatsApp CTA on Pricing Page
**Priority:** P1
**Effort:** 2h
**Owner:** @dev
**Sprint:** Week 1, Day 5

## Context

B2G buyers with budget authority often need to speak with a human before committing company money at R$397-997/month. The pricing page has zero direct contact options. The UX specialist recommends an inline contact row (not a floating bubble, which is too casual for B2G price points) positioned between the FAQ section and the bottom CTA.

## Acceptance Criteria

- [x] AC1: Contact row visible below FAQ section on `/planos`
- [x] AC2: Row contains WhatsApp link with icon and "Fale conosco" label
- [x] AC3: Row contains email link with icon showing `contato@smartlic.tech`
- [x] AC4: WhatsApp number sourced from env var `NEXT_PUBLIC_WHATSAPP_NUMBER` (not hardcoded)
- [x] AC5: WhatsApp link uses `https://wa.me/{number}?text=...` format with pre-filled message
- [x] AC6: Mobile-responsive layout (horizontal on desktop, stacked on mobile)
- [x] AC7: Visual dividers above and below the contact row
- [x] AC8: Links open in new tab (`target="_blank"` with `rel="noopener noreferrer"`)

## Technical Notes

**Design (from UX assessment):**
```
[FAQ accordion]
--- divider ---
"Precisa de mais informacoes?"
[WhatsApp icon] Fale conosco   [Email icon] contato@smartlic.tech
--- divider ---
[Bottom CTA / footer]
```

**Implementation:**
- Add a `ContactRow` component or inline section in `/planos/page.tsx`
- WhatsApp pre-filled message suggestion: `"Ola! Gostaria de saber mais sobre o SmartLic Pro."`
- Use Lucide icons (`MessageCircle` for WhatsApp, `Mail` for email) -- already in the project deps
- Env var: add `NEXT_PUBLIC_WHATSAPP_NUMBER` to `.env.example` with documentation

**Styling:**
- Match existing page typography and color scheme
- Subtle background (e.g., `bg-gray-50 dark:bg-gray-900`) to differentiate from surrounding sections
- Padding: `py-8` for breathing room

## Test Requirements

- [x] Component renders WhatsApp and email links
- [x] WhatsApp link uses correct `wa.me` format
- [x] Email link has correct `mailto:` href
- [x] Links have `target="_blank"` and `rel="noopener noreferrer"`
- [x] Existing pricing page tests pass

## Files to Modify

- `frontend/app/planos/page.tsx` -- Add contact row section
- `frontend/.env.example` -- Add `NEXT_PUBLIC_WHATSAPP_NUMBER`

## Definition of Done

- [x] All ACs pass
- [x] Tests pass (existing + new)
- [ ] No regressions in CI
- [x] Code reviewed
