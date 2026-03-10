# Contributing to SmartLic Frontend

## Component Directory Convention

Components are organized by scope of usage:

| Directory | Scope | Rule |
|-----------|-------|------|
| `components/` | Global | Used in **3+ pages** (e.g., `PageHeader`, `MobileDrawer`) |
| `app/components/` | App-shared | Used in **2+ authenticated pages** (e.g., `AuthProvider`, `Footer`, `BackendStatusIndicator`) |
| Page-local (e.g., `app/buscar/components/`) | Single page | Used in **only 1 page** — lives in that page's directory |

When deciding where to place a new component:

1. If it is used by a single page, put it in that page's directory.
2. If it is shared across 2 or more authenticated app pages, put it in `app/components/`.
3. If it is truly global (used in 3+ pages, including unauthenticated pages or the root layout), put it in `components/`.

When a component's usage grows or shrinks, move it to the appropriate directory and update all imports.
