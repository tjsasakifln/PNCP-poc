# DescompLicita Design System

## Domain Exploration

**Product:** DescompLicita — Licitações e Contratos de Forma Descomplicada. Intelligent procurement opportunity discovery from Brazil's PNCP (Portal Nacional de Contratações Públicas).

**Brand origin:** [Descomplicita](https://www.descomplicita.com.br/) — specialized in making procurement processes safer, transparent, and agile. Courses, mentoring, and tools for public and private agents navigating Lei 14.133/2021.

**Domain concepts:** Edital, pregão eletrônico, licitação, diário oficial, certame, homologação, órgão público, modalidade de contratação, ata de registro de preços, nota de empenho

**Color world:** The physical space of Brazilian procurement:
- Azul-marinho (#0A1E3F) — selo oficial, carimbo de autenticidade, authority
- Azul-institucional (#116DFF) — links, interactive elements, digital trust
- Cinza-papel — documento impresso, papel timbrado
- Branco-off — papel bond, limpeza documental
- Vermelho-urgência — prazos, alertas de deadline
- Amarelo-atenção — avisos, alertas de prazo

**Signature element:** "Digital filing cabinet" aesthetic — thin precise borders, monospace data displays, navy-blue institutional accents. The interface feels authoritative, professional, and organized — not a consumer app.

**Defaults rejected:**
- Generic system font stack → DM Sans (body) + Fahkwang (display, matching Descomplicita)
- border-2 everywhere → whisper-thin 1px borders with low opacity
- Mixed shadows + borders → borders-only depth strategy
- bg-green-50 / bg-red-50 dramatic jumps → subtle surface elevation scale
- Emerald green palette → Navy/blue institutional palette (Descomplicita brand)

## Direction

**Personality:** Authority & Clarity
**Foundation:** Cool (slate-based neutrals with navy accent)
**Depth:** Borders-only (no shadows — clean, institutional, data-focused)
**Brand alignment:** Descomplicita navy (#0A1E3F) + blue (#116DFF)

## Tokens

### Spacing
Base: 4px
Scale: 4, 8, 12, 16, 24, 32, 64

### Typography
Body: DM Sans (via next/font/google) — professional, geometric, excellent legibility
Display: Fahkwang (via next/font/google) — matches Descomplicita brand identity
Data: DM Mono (via next/font/google) with tabular-nums
Scale: 12, 13, 14 (base), 16, 18, 24, 32
Weights: 400 (body), 500 (labels/UI), 600 (headings), 700 (display headings)

### Colors
```
--canvas: #ffffff (light) / #121212 (dark)
--ink: #1e2d3b (light) / #e8eaed (dark)
--ink-secondary: #3d5975 (light) / #a8b4c0 (dark)
--ink-muted: #808f9f (light) / #6b7a8a (dark)
--ink-faint: #c0d2e5 (light) / #3a4555 (dark)
--brand-navy: #0a1e3f (primary action)
--brand-blue: #116dff (interactive accent)
--brand-blue-hover: #0d5ad4
--brand-blue-subtle: #e8f0ff (light) / rgba(17,109,255,0.12) (dark)
```

### Semantic
```
--success: #16a34a (light) / #22c55e (dark)
--success-subtle: #f0fdf4 (light) / #052e16 (dark)
--error: #dc2626 (light) / #f87171 (dark)
--error-subtle: #fef2f2 (light) / #450a0a (dark)
--warning: #ca8a04 (light) / #facc15 (dark)
--warning-subtle: #fefce8 (light) / #422006 (dark)
```

### Borders
```
--border: rgba(0,0,0,0.08) (light) / rgba(255,255,255,0.08) (dark)
--border-strong: rgba(0,0,0,0.15) (light) / rgba(255,255,255,0.15) (dark)
--border-accent: rgba(17,109,255,0.3) (light) / rgba(17,109,255,0.4) (dark)
Weight: 1px (never 2px)
```

### Surfaces
```
--surface-0: canvas (base background)
--surface-1: #f7f8fa (light) / #1a1d22 (dark) — cards, panels (2% shift)
--surface-2: #f0f2f5 (light) / #242830 (dark) — dropdowns, insets (3-4% shift)
--surface-elevated: canvas — floating elements
```

### Focus
```
--ring: #116dff (light) / #3b8bff (dark)
```

### Radius
Scale: 4px (inputs), 6px (buttons), 8px (cards), 12px (modals)

## Patterns

### Button Primary
- Height: 44px (touch target)
- Padding: 12px 16px (sm: 12px 20px)
- Radius: 6px (rounded-button)
- Font: DM Sans 16px, 600 weight
- Background: var(--brand-navy) (#0a1e3f)
- Border: none (bg contrast is enough)
- Hover: var(--brand-blue-hover) (#0d5ad4)
- Active: var(--brand-blue) (#116dff)

### Card Default
- Border: 1px solid var(--border)
- Padding: 16px (sm: 24px)
- Radius: 8px (rounded-card)
- Background: var(--surface-1)
- No shadow

### Input Default
- Height: 44px
- Border: 1px solid var(--border-strong)
- Radius: 4px (rounded-input)
- Font: DM Sans 16px, 400 weight
- Focus: 2px brand-blue ring

### Data Display
- Font: DM Mono (font-data)
- font-variant-numeric: tabular-nums
- Color: var(--brand-navy) (light) / var(--brand-blue) (dark)

### Navigation Header
- Sticky top-0
- Border-bottom: 1px solid var(--border-strong)
- Background: var(--surface-0)
- Height: 64px
- Logo: Descomplicita (from brand URL)
- Tagline: "Busca Inteligente PNCP"

### Motion
- Entry: fadeInUp (0.4s ease-out)
- Stagger: 50ms increments for lists
- Transitions: 200ms for interactive states
- Progress bar: slide animation (1.5s ease-in-out infinite)
- Respects prefers-reduced-motion

### Background Texture
- CSS-only radial gradients using brand-blue-subtle
- Fixed position, pointer-events none
- Opacity: 0.4

## Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Navy/blue palette over emerald | Aligning with Descomplicita brand identity. Navy conveys authority, trust. | 2026-01-29 |
| Fahkwang display font | Matches Descomplicita website (fahkwang, sans-serif). Distinctive, professional. | 2026-01-29 |
| Borders-only depth | Procurement data tool — users want density and clarity. Shadows add visual weight without information value. | 2026-01-28 |
| 4px spacing base | Tight enough for data tables, divisible by common UI sizes. | 2026-01-28 |
| DM Sans body | Professional, geometric, excellent legibility at small sizes. Not Inter (overused). | 2026-01-28 |
| DM Mono for data | Monospace from same family as DM Sans, visual harmony. tabular-nums for aligned numbers. | 2026-01-28 |
| 1px borders only | 2px borders are loud and amateur. 1px with low opacity creates structure without demanding attention. | 2026-01-28 |
| CSS-only background texture | Subtle depth without image dependencies. <1KB overhead. | 2026-01-29 |
| Staggered animations | Perceived performance and polish. Respects prefers-reduced-motion. | 2026-01-29 |
| Product identity tokens | --canvas, --ink, --brand-navy instead of generic --background, --foreground, --success. | 2026-01-29 |
