# BidIQ Design System

## Domain Exploration

**Product:** BidIQ Uniformes — procurement opportunity discovery for Brazilian public contracts (PNCP)

**Domain concepts:** Edital, pregão eletrônico, licitação, diário oficial, certame, homologação, órgão público, modalidade de contratação, ata de registro de preços, nota de empenho

**Color world:** The physical space of Brazilian procurement:
- Verde institucional (gov.br portals, institutional trust)
- Azul-marinho (selo oficial, carimbo de autenticidade)
- Cinza-papel (documento impresso, papel timbrado)
- Dourado-sutil (selo/carimbo, destaque oficial)
- Branco-off (papel bond, limpeza documental)
- Vermelho-urgência (prazos, alertas de deadline)

**Signature element:** "Document stamp" aesthetic — thin precise borders, monospace data displays, institutional green accents. The interface should feel like a well-organized digital filing cabinet of official documents, not a consumer app.

**Defaults rejected:**
- Generic system font stack → DM Sans (body) + Source Serif 4 (display)
- border-2 everywhere → whisper-thin borders with low opacity
- Mixed shadows + borders → borders-only depth strategy
- bg-green-50 / bg-red-50 dramatic jumps → subtle surface elevation scale

## Direction

**Personality:** Sophistication & Trust
**Foundation:** Cool (slate-based neutrals)
**Depth:** Borders-only (no shadows — clean, institutional, data-focused)

## Tokens

### Spacing
Base: 4px
Scale: 4, 8, 12, 16, 24, 32, 64

### Typography
Body: DM Sans (via next/font/google)
Display: Source Serif 4 (via next/font/google)
Data: DM Mono (via next/font/google) with tabular-nums
Scale: 12, 13, 14 (base), 16, 18, 24, 32
Weights: 400 (body), 500 (labels/UI), 600 (headings), 700 (display headings)

### Colors
```
--foreground: slate-900 (light) / gray-100 (dark)
--secondary: slate-600 (light) / gray-400 (dark)
--muted: slate-400 (light) / gray-500 (dark)
--faint: slate-200 (light) / gray-700 (dark)
--accent: emerald-700 (institutional green — not generic green-600)
--accent-subtle: emerald-50 (light) / emerald-950 (dark)
```

### Borders
```
--border-default: rgba(0, 0, 0, 0.08) (light) / rgba(255, 255, 255, 0.08) (dark)
--border-subtle: rgba(0, 0, 0, 0.05) (light) / rgba(255, 255, 255, 0.05) (dark)
--border-strong: rgba(0, 0, 0, 0.15) (light) / rgba(255, 255, 255, 0.12) (dark)
Weight: 1px (never 2px)
```

### Surfaces
```
Level 0: Base background (canvas)
Level 1: Cards, panels (barely different — 2% lightness shift)
Level 2: Dropdowns, popovers (3-4% shift + border-strong)
```

### Radius
Scale: 4px (inputs), 6px (buttons), 8px (cards), 12px (modals)

## Patterns

### Button Primary
- Height: 44px (touch target)
- Padding: 12px 20px
- Radius: 6px
- Font: DM Sans 14px, 600 weight
- Background: emerald-700 (no shadow)
- Border: none (bg contrast is enough)
- Hover: emerald-800
- Active: emerald-900

### Card Default
- Border: 1px solid var(--border-default)
- Padding: 16px
- Radius: 8px
- Background: var(--surface-1)
- No shadow

### Input Default
- Height: 44px
- Border: 1px solid var(--border-strong) (interactive affordance needs stronger border)
- Radius: 4px
- Font: DM Sans 14px, 400 weight
- Focus: 2px emerald-600 ring

### Data Display
- Font: DM Mono
- font-variant-numeric: tabular-nums
- Color: var(--foreground)

## Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Borders-only depth | Procurement data tool — users want density and clarity. Shadows add visual weight without information value. | 2026-01-28 |
| 4px spacing base | Tight enough for data tables, divisible by common UI sizes. | 2026-01-28 |
| DM Sans body | Professional, geometric, excellent legibility at small sizes. Not Inter (overused). | 2026-01-28 |
| Source Serif 4 display | Serif for headings adds institutional gravitas, contrasts with sans body. Trust-evoking for government procurement context. | 2026-01-28 |
| DM Mono for data | Monospace from same family as DM Sans, visual harmony. tabular-nums for aligned numbers. | 2026-01-28 |
| Emerald-700 accent | Darker green than generic green-600. Institutional, gov.br aligned, serious. | 2026-01-28 |
| 1px borders only | 2px borders are loud and amateur. 1px with low opacity creates structure without demanding attention. | 2026-01-28 |
