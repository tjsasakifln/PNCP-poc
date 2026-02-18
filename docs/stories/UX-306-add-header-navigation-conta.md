# Story UX-306: Add Header/Navigation na Página de Conta

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 3 SP
**Owner:** @dev

## Problem
Página /conta não tem header global. Usuário preso com apenas botão "Voltar".

## Acceptance Criteria
- [ ] Header global com logo + navegação
- [ ] Breadcrumb: Busca > Minha Conta
- [ ] Menu dropdown do usuário acessível
- [ ] Mobile: hamburger menu funcional

## Implementation
```tsx
<AppHeader />
<Breadcrumb>
  <BreadcrumbItem href="/buscar">Busca</BreadcrumbItem>
  <BreadcrumbItem current>Minha Conta</BreadcrumbItem>
</Breadcrumb>
```

**Files:** `app/conta/layout.tsx`, `components/Breadcrumb.tsx`
