# Story UX-307: Add Validação de Senha em Tempo Real

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @dev

## Problem
Campo senha aceita qualquer input. Validação só no submit. Usuário descobre erro tarde demais.

## Acceptance Criteria
- [ ] Validação em tempo real (onChange)
- [ ] Mínimo 8 caracteres (não 6)
- [ ] Requer maiúscula + número
- [ ] Indicador visual de força (weak/medium/strong)
- [ ] Mensagens descritivas por requisito

## Implementation
```tsx
<PasswordInput
  validation={{ minLength: 8, requireUppercase: true, requireNumber: true }}
  showStrengthIndicator
  realTimeValidation
/>
<PasswordStrengthMeter password={value} />
```

**Files:** `components/PasswordInput.tsx`, `components/PasswordStrengthMeter.tsx`, `app/conta/page.tsx`
