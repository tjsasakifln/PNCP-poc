# Loading State Guidelines

**Origin:** STORY-5.12 (TD-FE-015, EPIC-TD-2026Q2 P2)
**Last updated:** 2026-04-15

## TL;DR — which loader do I use?

| Situation | Use | Why |
|-----------|-----|-----|
| Loading a list/card/table into a page | `<Skeleton variant="list" count={N}>` | Matches final layout shape; no layout shift. |
| Loading an entire page shell | `<AdminPageSkeleton>`, `<ContaPageSkeleton>`, `<PlanosPageSkeleton>` | Page-specific skeletons that match the final shell precisely. |
| In-flight button/action (submit, save, delete) | Inline `animate-spin rounded-full border-b-2` within the button | Short-lived; user is waiting on a direct action. |
| Long-running search with real progress signal | `<EnhancedLoadingProgress>` | SSE / polling; shows stages, not just a spin. |
| Full-page auth bootstrap | `<AuthLoadingScreen>` | Existing component, specialized. |

Use `Skeleton` (the primitive) for **anything else that would otherwise
reach for `animate-pulse` + `bg-[var(--surface-2)]`**. Prefer the primitive
over hand-rolling the pulse classes.

## Anti-patterns

- **Spinner inside a list**. Spinners don't convey shape. Use `<Skeleton variant="list" count={5} />` so the user perceives "this row will show up here" instead of a generic loader.
- **EnhancedLoadingProgress for trivial loads.** That component is an SSE progress animator for the consolidated search pipeline — using it for a 300ms fetch is overkill and misleading (implies long-running work).
- **Custom `animate-pulse` divs scattered around.** Reach for `Skeleton` (or the page skeletons). The primitive keeps the palette (`bg-[var(--surface-2)]`) and motion (`animate-pulse`) consistent across the app.
- **Blocking modals with a spinner.** If the action is user-triggered and the UI stays visible, a spinner inside the trigger button is enough. Only block the UI when the next step literally cannot render without the result.

## API

`components/skeletons/Skeleton.tsx`:

```tsx
import { Skeleton } from "@/components/skeletons";

// Single text line
<Skeleton variant="text" className="w-48" />

// List of rows
<Skeleton variant="list" count={5} />

// Cards grid
<div className="grid grid-cols-3 gap-4">
  {Array.from({ length: 6 }).map((_, i) => (
    <Skeleton key={i} variant="card" />
  ))}
</div>

// Custom dimensions via className
<Skeleton className="h-24 w-24 rounded-full" />
```

Variants: `text` (default) | `card` | `list` | `avatar` | `block`.

## Audit snapshot (2026-04-15)

| Pattern | Count (files, approx.) | Notes |
|---------|------------------------|-------|
| `animate-spin` (button/inline spinners) | 60+ | Valid for in-flight button actions. |
| `animate-pulse` | 40+ | Many are ad-hoc skeletons that could migrate to `<Skeleton>` — do incrementally as files are touched. |
| `<AdminPageSkeleton>`, `<ContaPageSkeleton>`, `<PlanosPageSkeleton>` | 3 pages | Page-level skeletons; keep as-is. |
| `<EnhancedLoadingProgress>` | ~10 callsites in `/buscar` flow | Specialized SSE/long-poll progress; leave alone. |

We intentionally do NOT do a bulk codemod migrating every `animate-pulse`
to `<Skeleton>` — it introduces churn without UX gain. Migrate opportunistically
when editing the surrounding file.

## Storybook

Originally (AC4) this story called for a Storybook entry for `Skeleton`.
Storybook setup itself is the scope of **STORY-5.9** (currently Draft, not in
this Sprint's tranche). AC4 is **deferred** until Storybook lands.

## Related

- `frontend/components/skeletons/Skeleton.tsx` — primitive
- `frontend/components/skeletons/index.ts` — re-export surface
- `frontend/components/AuthLoadingScreen.tsx` — full-page auth bootstrap loader
- `frontend/app/buscar/components/EnhancedLoadingProgress.tsx` — SSE progress animator
