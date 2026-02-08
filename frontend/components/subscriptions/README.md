# Subscription Components - STORY-171

## Overview

This directory contains all UI components for the Annual Subscription Toggle feature (STORY-171).

## Components

### PlanToggle.tsx
**Purpose:** Toggle component for switching between monthly and annual billing periods

**Props:**
- `value: 'monthly' | 'annual'` - Current billing period
- `onChange: (value) => void` - Callback when billing period changes
- `className?: string` - Additional CSS classes
- `disabled?: boolean` - Disable the toggle

**Features:**
- ✅ Keyboard accessible (Space/Enter)
- ✅ ARIA compliant
- ✅ Shows "💰 Economize 20%" badge when annual
- ✅ Smooth transition (300ms)
- ✅ Responsive (mobile + desktop)

**Usage:**
```tsx
import { PlanToggle } from '@/components/subscriptions/PlanToggle';

function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');

  return (
    <PlanToggle
      value={billingPeriod}
      onChange={setBillingPeriod}
    />
  );
}
```

---

### PlanCard.tsx
**Purpose:** Displays subscription plan with dynamic pricing calculation

**Props:**
- `id: string` - Plan identifier
- `name: string` - Plan display name
- `monthlyPrice: number` - Monthly price in BRL
- `billingPeriod: 'monthly' | 'annual'` - Current billing period
- `features: string[]` - List of plan features
- `highlighted?: boolean` - Highlight this plan
- `onSelect?: () => void` - Callback when plan is selected
- `className?: string` - Additional CSS classes

**Features:**
- ✅ Dynamic price calculation (annual = monthly × 9.6)
- ✅ Shows 20% savings badge when annual
- ✅ Tooltip with detailed savings breakdown
- ✅ BRL currency formatting (R$ 2.851,20)
- ✅ Responsive layout

**Pricing Formula:**
- **Monthly:** Display monthly price as-is
- **Annual:** `displayPrice = monthlyPrice × 9.6`
- **Savings:** `monthlyPrice × 12 - (monthlyPrice × 9.6)`

**Usage:**
```tsx
import { PlanCard } from '@/components/subscriptions/PlanCard';

<PlanCard
  id="consultor_agil"
  name="Consultor Ágil"
  monthlyPrice={297}
  billingPeriod={billingPeriod}
  features={[
    'Busca ilimitada',
    'Exportar Excel',
    'Resumo IA',
  ]}
  highlighted={true}
  onSelect={() => handleSelectPlan('consultor_agil')}
/>
```

---

### FeatureBadge.tsx
**Purpose:** Displays feature status badges with tooltips

**Props:**
- `status: 'active' | 'coming_soon' | 'future'` - Feature status
- `launchDate?: string` - Launch date for coming_soon features
- `className?: string` - Additional CSS classes

**Badge Types:**
- **Active (✅):** Feature is currently available
- **Coming Soon (🚀):** Feature launching soon (shows tooltip with date)
- **Future (🔮):** Feature planned for future

**Usage:**
```tsx
import { FeatureBadge } from '@/components/subscriptions/FeatureBadge';

<FeatureBadge status="coming_soon" launchDate="Março 2026" />
```

---

### AnnualBenefits.tsx
**Purpose:** Displays annual subscription benefits with status badges

**Props:**
- `billingPeriod: 'monthly' | 'annual'` - Current billing period
- `planId?: string` - Plan ID for exclusive benefits
- `className?: string` - Additional CSS classes

**Features:**
- ✅ Only renders when `billingPeriod === 'annual'`
- ✅ Shows general benefits (all plans)
- ✅ Shows exclusive benefits (Sala de Guerra only)
- ✅ Status badges for each benefit
- ✅ Early adopter messaging

**Benefit Categories:**
1. **All Plans:** Early Access, Busca Proativa, 20% discount
2. **Sala de Guerra Exclusive:** AI Edital Analysis, Dashboard Executivo, Alertas Multi-Canal

**Usage:**
```tsx
import { AnnualBenefits } from '@/components/subscriptions/AnnualBenefits';

<AnnualBenefits
  billingPeriod={billingPeriod}
  planId="sala_guerra"
/>
```

---

### TrustSignals.tsx
**Purpose:** Displays trust signals, guarantees, and urgency elements

**Props:**
- `annualConversionRate?: number` - Social proof percentage (0-100)
- `currentAnnualSignups?: number` - Current annual signups count
- `launchOfferLimit?: number` - Launch offer limit (default: 100)
- `showEarlyBirdCode?: boolean` - Show EARLYBIRD discount code
- `className?: string` - Additional CSS classes

**Features:**
- ✅ Social proof badge (dynamic conversion rate)
- ✅ Launch offer countdown (first 100 signups)
- ✅ EARLYBIRD discount code with copy button
- ✅ 3 guarantees (30-day refund, security, 24/7 support)
- ✅ Additional trust elements (LGPD, no hidden fees)

**Usage:**
```tsx
import { TrustSignals } from '@/components/subscriptions/TrustSignals';

<TrustSignals
  annualConversionRate={68}
  currentAnnualSignups={45}
  launchOfferLimit={100}
  showEarlyBirdCode={true}
/>
```

---

### DowngradeModal.tsx
**Purpose:** Warning modal for downgrade action from annual to monthly

**Props:**
- `isOpen: boolean` - Control modal visibility
- `onClose: () => void` - Callback when modal closes
- `onConfirm: () => void` - Callback when user confirms downgrade
- `currentPlanName?: string` - Current plan display name
- `expiryDate?: string` - ISO date string for plan expiry
- `retainedBenefits?: string[]` - List of benefits retained until expiry
- `isLoading?: boolean` - Show loading state

**Features:**
- ✅ Warning about no refund policy
- ✅ Shows retained benefits until expiry
- ✅ Requires confirmation checkbox
- ✅ Loading state during API call
- ✅ Accessible (ARIA compliant)

**Usage:**
```tsx
import { DowngradeModal } from '@/components/subscriptions/DowngradeModal';

const [showModal, setShowModal] = useState(false);

<DowngradeModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  onConfirm={handleDowngrade}
  expiryDate="2027-02-07T00:00:00Z"
  retainedBenefits={[
    'Early access a novas features',
    'Busca proativa de oportunidades',
  ]}
  isLoading={isDowngrading}
/>
```

---

## Hooks

### useFeatureFlags.ts
**Purpose:** Fetches and caches user feature flags from backend

**Returns:**
- `features: string[]` - Array of enabled feature keys
- `planId: string | null` - User's current plan ID
- `billingPeriod: 'monthly' | 'annual' | null` - User's billing period
- `isLoading: boolean` - Loading state
- `isError: boolean` - Error state
- `error: Error | null` - Error object if any
- `hasFeature: (key: string) => boolean` - Helper to check feature access
- `refresh: () => Promise<void>` - Manual refresh
- `mutate: (data, revalidate?) => void` - Optimistic update

**Features:**
- ✅ Client-side caching (5min TTL)
- ✅ Automatic fetch on mount
- ✅ Manual revalidation with `refresh()`
- ✅ Optimistic UI support via `mutate()`

**Usage:**
```tsx
import { useFeatureFlags } from '@/hooks/useFeatureFlags';

function MyComponent() {
  const { features, hasFeature, refresh } = useFeatureFlags();

  if (hasFeature('early_access')) {
    return <EarlyAccessFeature />;
  }

  return <StandardFeature />;
}

// Optimistic UI after billing update
const handleUpgrade = async () => {
  // Optimistically show new features
  mutate({ features: ['early_access', 'proactive_search'] }, false);

  const result = await fetch('/api/subscriptions/update-billing-period', {
    method: 'POST',
    body: JSON.stringify({ billing_period: 'annual' }),
  });

  // Revalidate to get server truth
  refresh();
};
```

---

## Testing

All components have comprehensive unit tests with ≥60% coverage target.

**Run tests:**
```bash
npm test -- subscriptions
npm test -- useFeatureFlags
```

**Test files:**
- `__tests__/components/subscriptions/PlanToggle.test.tsx`
- `__tests__/components/subscriptions/PlanCard.test.tsx`
- `__tests__/components/subscriptions/FeatureBadge.test.tsx`
- `__tests__/components/subscriptions/AnnualBenefits.test.tsx`
- `__tests__/components/subscriptions/TrustSignals.test.tsx`
- `__tests__/components/subscriptions/DowngradeModal.test.tsx`
- `__tests__/hooks/useFeatureFlags.test.ts`

---

## Design System Compliance

All components use the project's design system:

**Colors:**
- `brand-navy` - Primary brand color
- `brand-blue` - Secondary brand color
- `success` / `success-subtle` - Success states
- `warning` / `warning-subtle` - Warning states
- `error` / `error-subtle` - Error states
- `ink` / `ink-secondary` / `ink-muted` - Text colors
- `surface-0` / `surface-1` / `surface-2` - Background colors
- `strong` - Border color

**Transitions:**
- All transitions use `300ms` duration
- Use `transition-all` for smooth state changes

**Accessibility:**
- All interactive elements have ARIA labels
- Keyboard navigation fully supported
- Focus states clearly visible
- Screen reader friendly

---

## Related Documentation

- **Story:** `docs/stories/STORY-171-annual-subscription-toggle.md`
- **Architecture Review:** `docs/stories/STORY-171-architect-review.md`
- **PO Review:** `docs/stories/STORY-171-po-review.md`

---

## Backend Integration

These components integrate with backend endpoints:

- `GET /api/features/me` - Fetch user's enabled features (useFeatureFlags hook)
- `POST /api/subscriptions/update-billing-period` - Update billing period
- `POST /api/subscriptions/downgrade` - Downgrade to monthly

See backend documentation for API contracts and implementation details.
