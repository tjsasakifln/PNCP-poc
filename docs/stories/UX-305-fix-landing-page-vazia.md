# Story UX-305: Fix Landing Page Vazia (Usuário Logado)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 3 SP
**Owner:** @dev

## Problem
Página /planos mostra tela vazia quando usuário já possui plano ativo. Hydration mismatch causa flash de conteúdo.

## Acceptance Criteria
- [ ] Loading state (skeleton) enquanto verifica autenticação
- [ ] Usuário com plano ativo vê card "Você possui acesso completo" + CTA
- [ ] Usuário sem plano vê pricing completo
- [ ] FAQ visível em ambos os casos
- [ ] Zero flash de conteúdo (SSR → Client hydration smooth)

## Implementation
```tsx
if (loading) return <PlanosSkeleton />;
if (user && plan?.status === 'active') return <AlreadySubscribedView />;
return <PricingPage />;
```

**Files:** `app/planos/page.tsx`, `components/AlreadySubscribedView.tsx`
