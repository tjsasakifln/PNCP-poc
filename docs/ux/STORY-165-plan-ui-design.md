# UX Design: Plan Restrictions & Upgrade Flow (STORY-165)

**Designer:** @ux-design-expert (Luna)
**Date:** 2026-02-03
**Story:** PNCP-165 - Plan Restructuring (3 Paid Tiers + FREE Trial)
**Status:** Design Complete - Ready for Implementation

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Component Specifications](#component-specifications)
3. [User Flows](#user-flows)
4. [Wireframes & Visual Design](#wireframes--visual-design)
5. [Implementation Notes](#implementation-notes)
6. [Accessibility Requirements](#accessibility-requirements)

---

## Design Principles

### Core UX Philosophy

1. **Progressive Disclosure:** Show limits contextually when users hit them, not preemptively
2. **Clarity over Cleverness:** Direct upgrade CTAs, no ambiguous messaging
3. **Graceful Degradation:** Locked features visible but clearly marked as unavailable
4. **Trust through Transparency:** Always show quota status, trial countdown, next reset date
5. **Frictionless Upgrade:** One-click upgrade flow from any blocked feature

### Design System Alignment

**Existing Tailwind Theme Variables:**
```css
/* From frontend theme */
--brand-navy: #1e3a5f
--brand-blue: #3b82f6
--brand-blue-hover: #2563eb
--brand-blue-subtle: rgba(59, 130, 246, 0.1)
--success: #10b981
--warning: #f59e0b
--error: #ef4444
--ink: (theme-dependent)
--ink-secondary: (theme-dependent)
--ink-muted: (theme-dependent)
--surface-0: (theme-dependent)
--surface-1: (theme-dependent)
--border: (theme-dependent)
```

---

## Component Specifications

### 1. Plan Badge Component

**Purpose:** Display current plan tier in header/sidebar with trial countdown

**Visual Design:**

```tsx
// Location: frontend/app/components/PlanBadge.tsx

interface PlanBadgeProps {
  planId: 'free_trial' | 'consultor_agil' | 'maquina' | 'sala_guerra';
  planName: string;
  trialExpiresAt?: string; // ISO timestamp
  onClick?: () => void; // Opens upgrade modal
}

// Component renders:
// [Plan Icon] Plan Name (Trial: 3 dias restantes) [Chevron Right]
```

**Tier Colors:**
| Plan | Background | Text | Border |
|------|------------|------|--------|
| FREE Trial | bg-gray-500 | text-white | border-gray-600 |
| Consultor Ágil | bg-blue-500 | text-white | border-blue-600 |
| Máquina | bg-green-500 | text-white | border-green-600 |
| Sala de Guerra | bg-yellow-500 | text-gray-900 | border-yellow-600 |

**States:**
1. **Default (Non-Trial):**
   ```
   [💼] Consultor Ágil >
   ```
   - Badge: `px-3 py-1.5 rounded-full text-sm font-medium`
   - Hover: Slight opacity change (opacity-90)
   - Cursor: pointer (clickable to upgrade modal)

2. **Trial with Countdown:**
   ```
   [⚠️] FREE Trial (3 dias restantes) >
   ```
   - Same styling as above
   - Countdown updates daily
   - Color: gray-500 (neutral, not alarming)

3. **Trial Expiring Soon (<2 days):**
   ```
   [⚠️] FREE Trial (1 dia restante) >
   ```
   - Background: yellow-500 (warning color)
   - Animated pulse: `animate-pulse` (subtle attention grab)

**Positioning:**
- **Desktop:** Header right side, between QuotaBadge and ThemeToggle
- **Mobile:** Below logo, full-width banner (less intrusive than modal)

**Interactions:**
- Click: Opens UpgradeModal (see below)
- Hover: Tooltip with plan details ("Ver planos disponíveis")
- Keyboard: Tab-accessible, Enter to activate

---

### 2. Quota Counter Component

**Purpose:** Show monthly search quota usage with visual progress bar

**Visual Design:**

```tsx
// Location: frontend/app/components/QuotaCounter.tsx

interface QuotaCounterProps {
  quotaUsed: number;
  quotaLimit: number;
  resetDate: string; // ISO timestamp
  planId: string;
}

// Component renders:
// Buscas este mês: 23/50
// [████████░░] 46%
// Renovação: 01/03/2026
```

**Layout:**
```
┌─────────────────────────────────────────┐
│ Buscas este mês: 23/50     Renovação:   │
│ [████████░░░░░░░░░░]       01/03/2026   │
└─────────────────────────────────────────┘
```

**Progress Bar Color Logic:**
| Usage | Color | Class |
|-------|-------|-------|
| 0-69% | Green | bg-green-500 |
| 70-89% | Yellow | bg-yellow-500 |
| 90-99% | Orange | bg-orange-500 |
| 100% | Red | bg-red-500 |

**Quota Exhausted State:**
```
┌─────────────────────────────────────────┐
│ ❌ Suas buscas acabaram (50/50)         │
│ [████████████████████] 100%             │
│ Renovação: 01/03/2026                   │
│ [Fazer Upgrade →]                       │
└─────────────────────────────────────────┘
```
- CTA button: `bg-brand-navy text-white px-4 py-2 rounded-button`
- Prominent placement above search form

**Positioning:**
- **Desktop:** Right sidebar (persistent)
- **Mobile:** Collapsible card below search filters
- **Always visible:** Yes (no hidden state)

**Animations:**
- Progress bar fills smoothly: `transition-all duration-300`
- Color transitions: `transition-colors duration-300`
- Quota update: Subtle scale animation (`animate-pulse-once`)

---

### 3. Locked Excel Button

**Purpose:** Show Excel export feature is available but locked for current plan

**Visual Design:**

**Unlocked State (Máquina, Sala de Guerra):**
```tsx
<button className="w-full bg-brand-navy text-white py-4 rounded-button...">
  <svg>📥</svg>
  Baixar Excel (42 licitações)
</button>
```

**Locked State (FREE Trial, Consultor Ágil):**
```tsx
<button className="w-full bg-surface-0 border-2 border-brand-navy text-brand-navy py-4 rounded-button...">
  <svg>🔒</svg>
  Exportar Excel (Disponível no plano Máquina)
</button>
```

**Hover Tooltip (Locked):**
```
┌─────────────────────────────────────────────┐
│ 🔒 Exportar Excel disponível no plano      │
│    Máquina (R$ 597/mês)                    │
│                                             │
│    Upgrade agora para baixar planilhas     │
│    com todas as licitações encontradas.    │
│    [Ver Planos →]                          │
└─────────────────────────────────────────────┘
```
- Tooltip width: max-w-sm (384px)
- Background: surface-0 with drop-shadow-lg
- Arrow pointing to button
- CTA link: text-brand-blue underline

**Click Behavior (Locked):**
- Opens UpgradeModal with Máquina plan pre-selected
- Analytics event: `upgrade_cta_clicked` with source: `excel_button`

**Visual Differentiation:**
| State | Background | Border | Icon | Cursor |
|-------|------------|--------|------|--------|
| Unlocked | bg-brand-navy | none | 📥 Download | pointer |
| Locked | bg-surface-0 | border-2 border-brand-navy | 🔒 Lock | pointer |
| Disabled | bg-surface-1 | none | ⏳ Loading | not-allowed |

---

### 4. Date Range Validation Warning

**Purpose:** Prevent users from submitting invalid date ranges and guide to upgrade

**Validation Rules:**
| Plan | Max Days | Validation Message |
|------|----------|-------------------|
| FREE Trial | 7 | "Seu plano permite buscas de até 7 dias" |
| Consultor Ágil | 30 | "Seu plano permite buscas de até 30 dias" |
| Máquina | 365 | "Seu plano permite buscas de até 365 dias" |
| Sala de Guerra | 1825 | "Seu plano permite buscas de até 5 anos" |

**Visual Design (Inline Warning):**

```tsx
// Appears below date range inputs when validation fails

<div className="mt-3 p-4 bg-warning-subtle border border-warning/20 rounded-card">
  <div className="flex items-start gap-3">
    <svg className="w-5 h-5 text-warning flex-shrink-0 mt-0.5">
      ⚠️ Triangle Warning Icon
    </svg>
    <div className="flex-1">
      <p className="text-sm font-medium text-warning mb-1">
        Período muito longo para seu plano
      </p>
      <p className="text-sm text-ink-secondary">
        Seu plano Consultor Ágil permite buscas de até 30 dias.
        Você selecionou 45 dias. Ajuste as datas ou faça upgrade
        para o plano Máquina (365 dias de histórico).
      </p>
      <button className="mt-2 text-sm font-medium text-brand-blue hover:underline">
        Ver plano Máquina →
      </button>
    </div>
  </div>
</div>
```

**Date Picker Visual Indicator:**

Add subtle visual cue in CustomDateInput component:
```tsx
// Below date input field
<p className="text-xs text-ink-muted mt-1">
  Seu plano: Histórico de até 30 dias
</p>
```

**Search Button State:**
- **When range invalid:** Disabled + Tooltip explaining why
- **Visual:** `disabled:bg-ink-faint disabled:cursor-not-allowed`
- **Tooltip:** "Ajuste o período para prosseguir (máx 30 dias)"

**Real-Time Validation:**
- Trigger: `onChange` of date inputs (no submit needed)
- Debounce: 300ms to avoid flicker
- Clear on fix: Warning disappears immediately when valid

---

### 5. Upgrade Modal

**Purpose:** Comprehensive plan comparison with clear CTAs

**Modal Layout (Desktop):**

```
┌────────────────────────────────────────────────────────────┐
│  ✕                    Escolha seu plano                    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Consultor   │  │ ⭐ Máquina  │  │ Sala de     │       │
│  │ Ágil        │  │             │  │ Guerra      │       │
│  │             │  │ Mais Popular│  │             │       │
│  │ R$ 297/mês  │  │ R$ 597/mês  │  │ R$ 1.497/mês│       │
│  │             │  │             │  │             │       │
│  │ ✓ 50 buscas │  │ ✓ 300       │  │ ✓ 1000      │       │
│  │   /mês      │  │   buscas/mês│  │   buscas/mês│       │
│  │ ✓ 30 dias   │  │ ✓ 1 ano de  │  │ ✓ 5 anos de │       │
│  │   histórico │  │   histórico │  │   histórico │       │
│  │ ✓ Resumo IA │  │ ✓ Excel     │  │ ✓ Excel Pro │       │
│  │   básico    │  │   export    │  │   export    │       │
│  │ ✗ Excel     │  │ ✓ Resumo IA │  │ ✓ Resumo IA │       │
│  │   export    │  │   completo  │  │   completo+ │       │
│  │             │  │ ✓ Suporte   │  │ ✓ Suporte   │       │
│  │             │  │   prioritário│  │   24/7      │       │
│  │             │  │             │  │ ✓ API       │       │
│  │             │  │             │  │   dedicada  │       │
│  │ [Assinar]   │  │ [Assinar]   │  │ [Assinar]   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                             │
│  💡 Dica: Upgrade a qualquer momento sem perder dados     │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
// Location: frontend/app/components/UpgradeModal.tsx

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  preSelectedPlan?: 'consultor_agil' | 'maquina' | 'sala_guerra';
  source?: string; // Analytics: 'excel_button', 'date_range', 'quota_counter'
}

// Plan card structure:
interface PlanCard {
  id: string;
  name: string;
  price: string;
  priceMonthly: number;
  popular?: boolean;
  features: PlanFeature[];
  buttonText: string;
  buttonStyle: 'outline' | 'solid' | 'premium';
}

interface PlanFeature {
  text: string;
  available: boolean; // true = ✓ green, false = ✗ gray
  highlight?: boolean; // Makes text bold
}
```

**Plan Comparison Data:**

```typescript
const PLANS: PlanCard[] = [
  {
    id: 'consultor_agil',
    name: 'Consultor Ágil',
    price: 'R$ 297/mês',
    priceMonthly: 297,
    features: [
      { text: '50 buscas por mês', available: true },
      { text: '30 dias de histórico', available: true },
      { text: 'Resumo executivo IA (básico)', available: true },
      { text: 'Filtros por setor e UF', available: true },
      { text: 'Exportar Excel', available: false },
      { text: 'Suporte prioritário', available: false },
    ],
    buttonText: 'Assinar Consultor Ágil',
    buttonStyle: 'outline',
  },
  {
    id: 'maquina',
    name: 'Máquina',
    price: 'R$ 597/mês',
    priceMonthly: 597,
    popular: true, // "Mais Popular" badge
    features: [
      { text: '300 buscas por mês', available: true, highlight: true },
      { text: '1 ano de histórico', available: true, highlight: true },
      { text: 'Resumo executivo IA (completo)', available: true },
      { text: 'Exportar Excel', available: true, highlight: true },
      { text: 'Filtros avançados', available: true },
      { text: 'Suporte prioritário', available: true },
      { text: 'API básica', available: true },
    ],
    buttonText: 'Assinar Máquina',
    buttonStyle: 'solid',
  },
  {
    id: 'sala_guerra',
    name: 'Sala de Guerra',
    price: 'R$ 1.497/mês',
    priceMonthly: 1497,
    features: [
      { text: '1000 buscas por mês', available: true, highlight: true },
      { text: '5 anos de histórico', available: true, highlight: true },
      { text: 'Resumo executivo IA (premium)', available: true },
      { text: 'Exportar Excel (formatação avançada)', available: true },
      { text: 'Alertas automáticos', available: true },
      { text: 'Suporte 24/7 dedicado', available: true, highlight: true },
      { text: 'API completa + webhooks', available: true },
      { text: 'Relatórios personalizados', available: true },
    ],
    buttonText: 'Assinar Sala de Guerra',
    buttonStyle: 'premium',
  },
];
```

**Visual Styling:**

**Modal Container:**
```css
/* Desktop */
.upgrade-modal {
  max-width: 1200px;
  width: 90vw;
  max-height: 90vh;
  padding: 2rem;
  background: var(--surface-0);
  border-radius: var(--radius-card);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

/* Mobile */
@media (max-width: 768px) {
  .upgrade-modal {
    width: 100vw;
    height: 100vh;
    max-height: none;
    border-radius: 0;
    padding: 1rem;
  }
}
```

**Plan Card Styles:**

```css
/* Base card */
.plan-card {
  border: 2px solid var(--border);
  border-radius: var(--radius-card);
  padding: 1.5rem;
  transition: all 0.2s;
}

/* Popular badge */
.plan-card.popular {
  border-color: var(--brand-blue);
  position: relative;
  transform: scale(1.05); /* Slightly larger */
  box-shadow: 0 10px 40px rgba(59, 130, 246, 0.2);
}

.plan-card.popular::before {
  content: "⭐ Mais Popular";
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--brand-blue);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

/* Pre-selected card (highlighted when opened from specific CTA) */
.plan-card.pre-selected {
  border-color: var(--brand-blue);
  background: var(--brand-blue-subtle);
  animation: pulse-border 2s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: var(--brand-blue); }
  50% { border-color: var(--brand-blue-hover); }
}
```

**Button Styles:**

```css
/* Outline (Consultor Ágil) */
.button-outline {
  border: 2px solid var(--brand-navy);
  color: var(--brand-navy);
  background: transparent;
}

.button-outline:hover {
  background: var(--brand-blue-subtle);
}

/* Solid (Máquina - Popular) */
.button-solid {
  background: var(--brand-navy);
  color: white;
  font-weight: 600;
}

.button-solid:hover {
  background: var(--brand-blue-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

/* Premium (Sala de Guerra) */
.button-premium {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #1e3a5f;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
}

.button-premium:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(251, 191, 36, 0.6);
}
```

**Modal Opening Triggers:**

1. **From Plan Badge:** Opens with no pre-selection (user is exploring)
2. **From Locked Excel Button:** Pre-selects "Máquina" (needed for Excel)
3. **From Date Range Warning:** Pre-selects next tier up (e.g., Consultor → Máquina)
4. **From Quota Counter (Exhausted):** Pre-selects next tier up
5. **From Trial Expiration Alert:** Pre-selects "Consultor Ágil" (lowest paid tier)

**Analytics Events:**
```typescript
// Track when modal opens
trackEvent('upgrade_modal_opened', {
  source: 'excel_button', // or 'date_range', 'quota_counter', etc.
  current_plan: 'consultor_agil',
  pre_selected_plan: 'maquina',
});

// Track plan selection
trackEvent('upgrade_plan_clicked', {
  selected_plan: 'maquina',
  source: 'excel_button',
  current_plan: 'consultor_agil',
});
```

---

### 6. Error Messages (403/429 Responses)

**Purpose:** User-friendly alerts for quota/limit errors with contextual upgrade CTAs

**Error Types & Designs:**

#### 6.1 Trial Expired (403)

```tsx
<div className="p-5 bg-error-subtle border border-error/20 rounded-card">
  <div className="flex items-start gap-3">
    <svg className="w-6 h-6 text-error flex-shrink-0">⛔ Circle X Icon</svg>
    <div className="flex-1">
      <h4 className="text-base font-semibold text-error mb-1">
        Trial expirado
      </h4>
      <p className="text-sm text-ink-secondary mb-3">
        Seu período de teste gratuito de 7 dias terminou.
        Escolha um plano para continuar usando o SmartLic.
      </p>
      <button className="px-4 py-2 bg-brand-navy text-white rounded-button font-medium hover:bg-brand-blue-hover">
        Ver Planos
      </button>
    </div>
  </div>
</div>
```

**Placement:** Full-page overlay (blocks all content, forces action)

---

#### 6.2 Quota Exhausted (403)

```tsx
<div className="p-5 bg-warning-subtle border border-warning/20 rounded-card">
  <div className="flex items-start gap-3">
    <svg className="w-6 h-6 text-warning flex-shrink-0">⚠️ Warning Icon</svg>
    <div className="flex-1">
      <h4 className="text-base font-semibold text-warning mb-1">
        Suas buscas acabaram
      </h4>
      <p className="text-sm text-ink-secondary mb-1">
        Você atingiu o limite de 50 buscas mensais do plano Consultor Ágil.
      </p>
      <p className="text-sm text-ink-secondary mb-3">
        Renovação automática em: <strong>01/03/2026</strong>
      </p>
      <div className="flex gap-2">
        <button className="px-4 py-2 bg-brand-navy text-white rounded-button font-medium hover:bg-brand-blue-hover">
          Fazer Upgrade
        </button>
        <button className="px-4 py-2 border border-border rounded-button text-ink-secondary hover:bg-surface-1">
          Ver Histórico
        </button>
      </div>
    </div>
  </div>
</div>
```

**Placement:** Replaces search form (user can still view history)

---

#### 6.3 Rate Limit Exceeded (429)

```tsx
<div className="p-5 bg-warning-subtle border border-warning/20 rounded-card">
  <div className="flex items-start gap-3">
    <svg className="w-6 h-6 text-warning flex-shrink-0">⏱️ Clock Icon</svg>
    <div className="flex-1">
      <h4 className="text-base font-semibold text-warning mb-1">
        Aguarde um momento
      </h4>
      <p className="text-sm text-ink-secondary mb-3">
        Você atingiu o limite de 10 requisições por minuto do plano
        Consultor Ágil. Aguarde <strong>42 segundos</strong> para fazer
        uma nova busca.
      </p>
      <p className="text-xs text-ink-muted mb-3">
        Planos superiores possuem limites maiores (Máquina: 30 req/min,
        Sala de Guerra: 60 req/min).
      </p>
      <div className="flex gap-2">
        <button
          disabled
          className="px-4 py-2 bg-ink-faint text-ink-muted rounded-button font-medium cursor-not-allowed"
        >
          <svg className="w-4 h-4 inline mr-1">⏳</svg>
          Aguardar (42s)
        </button>
        <button className="px-4 py-2 border border-brand-navy text-brand-navy rounded-button font-medium hover:bg-brand-blue-subtle">
          Ver Planos
        </button>
      </div>
    </div>
  </div>
</div>
```

**Auto-Dismiss:** Countdown timer updates every second, button re-enables when ready

**Placement:** Above search form (doesn't block entire UI)

---

#### 6.4 Date Range Exceeded (403)

```tsx
<div className="p-5 bg-warning-subtle border border-warning/20 rounded-card">
  <div className="flex items-start gap-3">
    <svg className="w-6 h-6 text-warning flex-shrink-0">📅 Calendar Icon</svg>
    <div className="flex-1">
      <h4 className="text-base font-semibold text-warning mb-1">
        Período muito longo para seu plano
      </h4>
      <p className="text-sm text-ink-secondary mb-1">
        Seu plano <strong>Consultor Ágil</strong> permite buscas de até
        <strong> 30 dias</strong>. Você solicitou <strong>45 dias</strong>.
      </p>
      <p className="text-sm text-ink-secondary mb-3">
        Ajuste o período de busca ou faça upgrade para o plano
        <strong> Máquina</strong> (até 1 ano de histórico).
      </p>
      <div className="flex gap-2">
        <button className="px-4 py-2 bg-brand-navy text-white rounded-button font-medium hover:bg-brand-blue-hover">
          Ver Plano Máquina →
        </button>
        <button
          onClick={() => adjustDatesToMaxRange()}
          className="px-4 py-2 border border-border rounded-button text-ink-secondary hover:bg-surface-1"
        >
          Ajustar Automaticamente
        </button>
      </div>
    </div>
  </div>
</div>
```

**Smart Action:** "Ajustar Automaticamente" button sets dates to max allowed (data_final - 30 days)

**Placement:** Below date inputs (inline with form)

---

#### 6.5 Excel Not Allowed (Implicit in Response)

**Not an error response, but feature is unavailable:**

Instead of showing an error after submission, show locked state upfront (see #3 Locked Excel Button above).

**Backend Response Structure:**
```json
{
  "excel_available": false,
  "excel_base64": null,
  "upgrade_message": "Exportar Excel disponível no plano Máquina (R$ 597/mês)."
}
```

**Frontend Behavior:**
- If `excel_available: false` → Show locked button (no download attempt)
- If `excel_available: true` → Show normal download button

---

## User Flows

### Flow 1: Excel Export Upgrade (Most Common)

```
User completes search with results
   ↓
Sees "Exportar Excel" button with lock icon 🔒
   ↓
Hovers → Tooltip: "Disponível no plano Máquina (R$ 597/mês)"
   ↓
Clicks button
   ↓
UpgradeModal opens with Máquina pre-selected
   ↓
Reviews plan comparison
   ↓
Clicks "Assinar Máquina"
   ↓
Redirected to Stripe Checkout
   ↓
Completes payment
   ↓
Redirected back → Plan badge shows "Máquina"
   ↓
Excel button now unlocked ✅
```

**Analytics:**
- `upgrade_cta_clicked` (source: excel_button)
- `upgrade_modal_opened` (pre_selected: maquina)
- `upgrade_plan_clicked` (plan: maquina)
- `payment_initiated` (plan: maquina)
- `payment_completed` (plan: maquina)

---

### Flow 2: Date Range Upgrade

```
User selects dates: 2025-01-01 to 2025-03-01 (60 days)
   ↓
Real-time validation triggers (on date change)
   ↓
Warning appears: "Seu plano permite até 30 dias"
   ↓
Search button disabled + tooltip explaining why
   ↓
User clicks "Ver plano Máquina" in warning
   ↓
UpgradeModal opens with Máquina pre-selected
   ↓
User reviews plan (365 days historical access)
   ↓
Proceeds to upgrade
```

**Alternative Path:**
```
User clicks "Ajustar Automaticamente" in warning
   ↓
Dates auto-adjust to: 2025-01-30 to 2025-03-01 (30 days)
   ↓
Warning disappears, search button enabled
   ↓
User proceeds with adjusted search
```

---

### Flow 3: Quota Exhaustion

```
User has used 50/50 searches this month
   ↓
Quota counter shows red (100%)
   ↓
User tries to search
   ↓
API returns 403 error (quota_exhausted)
   ↓
Error alert displays:
  - "Limite de 50 buscas atingido"
  - Reset date: "01/03/2026"
  - Upgrade CTA
   ↓
User clicks "Fazer Upgrade"
   ↓
UpgradeModal opens with Máquina suggested (300 searches/month)
   ↓
User upgrades
   ↓
Quota counter resets, user can search immediately
```

---

### Flow 4: Rate Limiting

```
User makes 10 searches in 45 seconds (limit: 10/min)
   ↓
User tries 11th search
   ↓
API returns 429 error (rate_limit_exceeded)
   ↓
Error alert displays with countdown: "Aguarde 15s"
   ↓
Search button disabled for 15 seconds
   ↓
Countdown updates every second
   ↓
After 15s → Button re-enables, alert dismisses
   ↓
User can search again
```

---

### Flow 5: Trial Expiration

```
User is on day 7 of FREE trial
   ↓
Plan badge shows: "FREE Trial (0 dias restantes)" with pulse animation
   ↓
User tries to search
   ↓
API returns 403 error (trial_expired)
   ↓
Full-page modal blocks all content:
  - "Trial expirado"
  - "Escolha um plano para continuar"
  - [Ver Planos] CTA
   ↓
User clicks CTA → UpgradeModal opens
   ↓
User upgrades to Consultor Ágil (lowest paid tier)
   ↓
Access restored immediately
```

---

## Wireframes & Visual Design

### Desktop Layout (1440px viewport)

```
┌────────────────────────────────────────────────────────────────┐
│  SmartLic                [💼 Consultor Ágil >] [🌙] [👤]     │
│                            Buscas: 23/50                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Busca de Licitações                                           │
│  Encontre oportunidades de contratação pública no PNCP        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Buscar por: [Setor] [Termos Específicos]                 │ │
│  │ Setor: [Vestuário e Uniformes ▼]                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Estados (UFs): [Selecionar todos] [Limpar]               │ │
│  │ [Sul] [Sudeste] [Centro-Oeste] [Norte] [Nordeste]       │ │
│  │ [SC] [PR] [RS] [SP] [RJ] [MG] ... (27 states)           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Data inicial: [01/02/2026]  Data final: [08/02/2026]    │ │
│  │ Seu plano: Histórico de até 30 dias                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │        [Buscar Vestuário e Uniformes]                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 📊 Resumo Executivo                                       │ │
│  │ Encontradas 42 licitações no valor total de R$ 2.3M...  │ │
│  │                                                           │ │
│  │ [42 licitações]           [R$ 2.345.678]                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 🔒 Exportar Excel (Disponível no plano Máquina)         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

### Mobile Layout (375px viewport)

```
┌───────────────────────────────┐
│ SmartLic      [🌙] [👤]    │
├───────────────────────────────┤
│ [💼 Consultor Ágil (50 buscas)│
│  Buscas: 23/50 █████░░ 46%   │
│  Renovação: 01/03/2026]       │
├───────────────────────────────┤
│                               │
│ Busca de Licitações          │
│                               │
│ [Setor] [Termos]             │
│ Setor: [Vestuário ▼]         │
│                               │
│ Estados:                      │
│ [SC][PR][RS][SP][RJ][MG]...  │
│                               │
│ Datas:                        │
│ De: [01/02/2026]             │
│ Até: [08/02/2026]            │
│ (Seu plano: 30 dias máx)     │
│                               │
│ [Buscar]                     │
│                               │
│ ─── Resultados ───            │
│                               │
│ 📊 42 licitações             │
│    R$ 2.345.678              │
│                               │
│ [🔒 Excel (Plano Máquina)]   │
│                               │
└───────────────────────────────┘
```

---

## Implementation Notes

### Backend API Integration

**Endpoints to Call:**

1. **GET `/api/me`** - Fetch user profile + capabilities on mount
   ```typescript
   const { data } = await fetch('/api/me', {
     headers: { Authorization: `Bearer ${token}` }
   });

   // Response:
   {
     plan_id: 'consultor_agil',
     plan_name: 'Consultor Ágil',
     capabilities: {
       max_history_days: 30,
       allow_excel: false,
       max_requests_per_month: 50,
       max_requests_per_min: 10,
       max_summary_tokens: 200
     },
     quota_used: 23,
     quota_remaining: 27,
     quota_reset_date: '2026-03-01T00:00:00Z',
     trial_expires_at: null
   }
   ```

2. **POST `/api/buscar`** - Search with quota tracking
   ```typescript
   const response = await fetch('/api/buscar', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       Authorization: `Bearer ${token}`
     },
     body: JSON.stringify({
       ufs: ['SC', 'PR'],
       data_inicial: '2026-01-01',
       data_final: '2026-01-31',
       setor_id: 'vestuario'
     })
   });

   if (response.status === 403) {
     const error = await response.json();
     // error.error_code: 'quota_exhausted', 'date_range_exceeded', etc.
     // error.suggested_plan: 'maquina'
     showUpgradeModal(error);
   }

   if (response.status === 429) {
     const error = await response.json();
     // error.retry_after: 42 (seconds)
     showRateLimitAlert(error.retry_after);
   }

   // Success response:
   {
     excel_available: false,
     excel_base64: null,
     upgrade_message: "Exportar Excel disponível no plano Máquina",
     quota_used: 24,
     quota_remaining: 26,
     // ... rest of search results
   }
   ```

### State Management

**React Context for Plan Info:**

```typescript
// frontend/contexts/PlanContext.tsx

interface PlanContextValue {
  planId: string;
  planName: string;
  capabilities: PlanCapabilities;
  quotaUsed: number;
  quotaRemaining: number;
  quotaResetDate: Date;
  trialExpiresAt: Date | null;
  refresh: () => Promise<void>;
}

export function usePlan() {
  const context = useContext(PlanContext);
  if (!context) throw new Error('usePlan must be used within PlanProvider');
  return context;
}

// Usage in components:
const { capabilities, quotaUsed, quotaRemaining } = usePlan();

// Check if feature allowed:
const canExportExcel = capabilities.allow_excel;
const maxDays = capabilities.max_history_days;
```

### Component Integration Points

**Where to Add Components:**

1. **PlanBadge:** Add to `frontend/app/page.tsx` header (line 693-734)
   ```tsx
   <div className="flex items-center gap-4">
     <PlanBadge {...planInfo} onClick={() => setShowUpgradeModal(true)} />
     <QuotaBadge />
     <ThemeToggle />
     <UserMenu />
   </div>
   ```

2. **QuotaCounter:** Add to sidebar or collapsible mobile section
   ```tsx
   {/* Below search form */}
   <QuotaCounter
     quotaUsed={planInfo.quota_used}
     quotaLimit={capabilities.max_requests_per_month}
     resetDate={planInfo.quota_reset_date}
     planId={planInfo.plan_id}
   />
   ```

3. **Date Range Validation:** Wrap CustomDateInput (line 953-964)
   ```tsx
   <DateRangeValidator
     maxDays={capabilities.max_history_days}
     currentPlan={planInfo.plan_name}
     onUpgradeClick={() => setShowUpgradeModal(true)}
   >
     <CustomDateInput id="data-inicial" ... />
     <CustomDateInput id="data-final" ... />
   </DateRangeValidator>
   ```

4. **Locked Excel Button:** Replace existing download button (line 1154-1180)
   ```tsx
   {result && (
     capabilities.allow_excel ? (
       <button onClick={handleDownload}>
         📥 Baixar Excel ({result.total} licitações)
       </button>
     ) : (
       <LockedExcelButton
         onUpgradeClick={() => setShowUpgradeModal(true, 'maquina')}
         totalResults={result.total}
       />
     )
   )}
   ```

5. **UpgradeModal:** Global component (rendered at root level)
   ```tsx
   <UpgradeModal
     isOpen={showUpgradeModal}
     onClose={() => setShowUpgradeModal(false)}
     preSelectedPlan={preSelectedPlan}
     currentPlan={planInfo.plan_id}
   />
   ```

---

## Accessibility Requirements

### WCAG AA Compliance Checklist

#### Color Contrast
- [ ] Plan badge text: 4.5:1 minimum contrast
- [ ] Locked button: 3:1 minimum for border, 4.5:1 for text
- [ ] Error messages: 4.5:1 contrast for all text
- [ ] Progress bar: Visible in both light/dark themes

#### Keyboard Navigation
- [ ] All interactive elements tabbable (tabindex=0)
- [ ] Modal traps focus (no escape via Tab)
- [ ] Escape key closes modal
- [ ] Enter/Space activates buttons
- [ ] Date picker keyboard accessible (arrow keys navigate dates)

#### Screen Readers
- [ ] Plan badge: `aria-label="Current plan: Consultor Ágil. Click to view upgrade options"`
- [ ] Locked button: `aria-label="Export Excel feature locked. Available on Máquina plan at R$ 597 per month. Click to view plans"`
- [ ] Quota counter: `role="status" aria-live="polite"` (updates announced)
- [ ] Error alerts: `role="alert" aria-live="assertive"` (errors announced immediately)
- [ ] Modal: `role="dialog" aria-modal="true" aria-labelledby="upgrade-modal-title"`

#### Focus Management
- [ ] Modal open: Focus moves to close button
- [ ] Modal close: Focus returns to trigger element
- [ ] Error appears: Focus moves to error message
- [ ] Rate limit countdown: Focus stays on search button, announces remaining time

#### Motion & Animations
- [ ] Respect `prefers-reduced-motion` for pulse animations
- [ ] Provide static alternative for progress bar fills
- [ ] No auto-playing animations >5 seconds

---

## Testing Checklist

### Visual Regression Tests

- [ ] Plan badge renders correctly for all 4 plan tiers
- [ ] Quota counter colors (green/yellow/red) at different thresholds
- [ ] Locked Excel button tooltip positioning
- [ ] Date range warning inline alert
- [ ] Error messages (403/429) with CTAs
- [ ] Upgrade modal layout (desktop + mobile)

### Interaction Tests

- [ ] Plan badge click opens modal
- [ ] Locked Excel button opens modal with Máquina pre-selected
- [ ] Date range validation triggers in real-time
- [ ] Quota counter updates after search
- [ ] Rate limit countdown decrements every second
- [ ] Upgrade modal closes on backdrop click

### Responsive Tests

- [ ] Mobile: Plan badge collapses to icon + name
- [ ] Mobile: Quota counter in collapsible card
- [ ] Mobile: Upgrade modal scrollable on small screens
- [ ] Tablet: 3-column plan comparison fits without horizontal scroll

### Cross-Browser Tests

- [ ] Chrome 100+ (primary)
- [ ] Safari 15+ (iOS compatibility)
- [ ] Firefox 100+
- [ ] Edge 100+

---

## Figma Design Files (Placeholder)

**Note:** For production implementation, create high-fidelity mockups in Figma:

1. **Component Library:**
   - PlanBadge (all states)
   - QuotaCounter (0-100% variations)
   - LockedExcelButton + tooltip
   - Error alert variants (5 types)

2. **Page Mockups:**
   - Homepage with Consultor Ágil plan (Excel locked)
   - Homepage with Máquina plan (Excel unlocked)
   - Quota exhausted state (full-page)
   - Rate limit error state

3. **Modal Designs:**
   - UpgradeModal (desktop 3-column)
   - UpgradeModal (mobile scrollable)
   - UpgradeModal with pre-selection (highlighted card)

**Figma Link:** `https://figma.com/file/smart-pncp-plan-restrictions` (placeholder)

---

## Design Handoff Checklist

**For @dev implementation:**

- [x] Component specifications defined
- [x] Styling classes documented (Tailwind)
- [x] State transitions documented
- [x] API integration points identified
- [x] User flows mapped
- [x] Accessibility requirements listed
- [x] Analytics events specified
- [ ] Figma designs exported (pending)
- [ ] Design tokens added to theme config
- [ ] Icon assets exported (SVG)

---

## Open Questions / Design Decisions Needed

1. **Plan badge placement:** Header vs. Sidebar?
   - **Recommendation:** Header (always visible, less clutter)

2. **Quota counter visibility:** Always visible vs. Collapsible?
   - **Recommendation:** Always visible on desktop, collapsible on mobile

3. **Trial countdown urgency:** Start pulsing at 3 days or 1 day remaining?
   - **Recommendation:** 2 days remaining (balance between urgency and annoyance)

4. **Rate limit retry button:** Auto-enable or require manual click?
   - **Recommendation:** Auto-enable after countdown (better UX)

5. **Upgrade modal pre-selection:** Highlight vs. Auto-scroll?
   - **Recommendation:** Highlight + subtle pulse (user may want to compare)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-03 | Initial design complete |

---

**Design Status:** ✅ Ready for Implementation

**Next Steps:**
1. @dev reviews component specs
2. @architect validates API integration points
3. @qa creates test scenarios based on user flows
4. Implementation begins (Task #5 in STORY-165)
