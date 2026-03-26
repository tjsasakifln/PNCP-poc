# UX Production Readiness Checklist

Use this checklist for UX audit track validation.

## Core Search Flow

- [x] Landing → Login → Search navigable
- [x] UF selector: single, multi, "Todo o Brasil"
- [x] Date range: default 10 days, custom works
- [x] Sector selector: all 15 sectors displayed
- [x] Submit: triggers search with progress
- [x] Results: displayed in readable format
- [x] Download: Excel generates and downloads
- [x] Empty: helpful message with suggestions

## Progress & Feedback

- [x] Progress bar starts within 2s of submit
- [x] Progress advances smoothly (no long freezes)
- [x] Per-UF status visible during search
- [x] Source badges show which APIs responded
- [x] Estimated time reasonable
- [x] Completion celebration/transition smooth

## Error Handling

- [x] Single error message per error (no doubles)
- [x] Network error: clear, actionable message
- [x] Timeout: suggests fewer UFs
- [x] Partial results: shown with explanation
- [x] Auth expired: redirect to login
- [x] Server error: apologetic, suggests retry
- [x] All errors in Portuguese

## Onboarding

- [x] New user redirected to onboarding
- [x] Each step has clear instructions
- [x] CNAE: helper text or optional
- [x] Skip/later option available
- [x] Completion → first search guided

## Navigation & Layout

- [x] Header: logo, nav links, user menu
- [x] Footer: legal links, contact
- [x] Breadcrumbs or clear location
- [x] Mobile hamburger menu works
- [x] All pages load under 3s
- [x] No broken links (404s)

## Visual Consistency

- [x] Color scheme consistent
- [x] Typography hierarchy clear
- [x] Spacing and padding consistent
- [x] Icons render correctly
- [x] Emojis display cross-platform
- [x] Dark/light theme works (if applicable)

## Accessibility

- [x] Semantic HTML (headings, landmarks)
- [x] Alt text on images
- [x] Focus visible on interactive elements
- [x] Color contrast meets WCAG AA
- [x] Keyboard navigation functional
- [x] Screen reader compatible (basic)

## Mobile Specific

- [x] Touch targets >= 44px
- [x] No horizontal scroll
- [x] Forms usable on small screens
- [x] Modals don't overflow viewport
- [x] Pinch-to-zoom not disabled

## Quick UX Check

For rapid validation:
- [x] Can complete a search in under 2 minutes
- [x] Can download results
- [x] No confusing error messages
- [x] Works on mobile phone
