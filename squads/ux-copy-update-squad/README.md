# UX Copy Update Squad

**Domain:** ux-copy-management
**Version:** 1.0.0
**Created:** 2026-02-10

## Purpose

Specialized squad for managing UX copy updates, microcopy changes, and content modifications across the BidiQ application. This squad ensures that text changes maintain quality, accessibility, and user experience standards.

## Use Cases

- Update welcome messages and onboarding copy
- Modify loading states and feedback messages
- Change call-to-action (CTA) texts
- Update error messages and tooltips
- Refine microcopy throughout the application

## Current Mission

**Two copy updates in the logged area:**

1. **Welcome Message** (frontend/app/buscar/page.tsx)
   - OLD: "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)"
   - NEW: "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio."

2. **Loading Message** (frontend/app/buscar/page.tsx)
   - OLD: "O PNCP está mais lento que o normal. Aguarde..."
   - NEW: "Estamos trabalhando nisso, só mais um instante!"

## Agents

### 1. @copy-editor (Lead)
Manages content and copy updates across the application.

**Commands:**
- `*update-copy` - Update text in code files
- `*find-copy` - Locate text across the codebase
- `*validate-text` - Validate text quality and tone

### 2. @ux-validator
Validates UX quality, accessibility, and user experience.

**Commands:**
- `*validate-ux` - Review UX quality of changes
- `*check-accessibility` - Verify WCAG compliance

### 3. @frontend-tester
Tests UI changes and ensures visual consistency.

**Commands:**
- `*test-ui-changes` - Run UI tests after changes
- `*visual-regression` - Check for visual regressions

## Workflow

```
1. @copy-editor *find-copy "text to find"
2. @copy-editor *update-copy <file> "old" "new"
3. @ux-validator *validate-ux
4. @ux-validator *check-accessibility
5. @frontend-tester *test-ui-changes
```

## Quick Start

```bash
# Activate the squad
@ux-copy

# Find all occurrences of a text
*find-copy "O PNCP está mais lento"

# Update copy
*update-copy frontend/app/buscar/page.tsx "old text" "new text"

# Validate changes
*validate-ux
*check-accessibility

# Test UI
*test-ui-changes
```

## Team

- **Product Owner:** Defines copy requirements
- **UX Designer:** Reviews tone and messaging
- **Frontend Developer:** Implements changes
- **QA Engineer:** Validates changes

## Standards

- **Tone:** Professional, helpful, user-centric
- **Language:** Brazilian Portuguese (pt-BR)
- **Accessibility:** WCAG 2.1 Level AA
- **Testing:** Visual regression + functional tests

## Related Documentation

- [Messaging Guidelines](../../docs/content-strategy/messaging-guidelines.md)
- [Value Proposition](../../docs/content-strategy/value-proposition.md)
- [Frontend Spec](../../docs/frontend/frontend-spec.md)
