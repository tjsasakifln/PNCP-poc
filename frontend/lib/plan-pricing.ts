/**
 * Single source of truth for plan pricing across the frontend.
 *
 * Runtime fallback when backend `GET /v1/plans` is unavailable; also feeds
 * structured data (JSON-LD Product/Offer schemas) and Rich Results.
 *
 * Backend canonical source: `plan_billing_periods` table (synced from Stripe).
 * Keep these values in sync with STORY-277/360 pricing policy.
 */

export type BillingPeriod = "monthly" | "semiannual" | "annual";

export interface PricingEntry {
  /** Monthly cost at this billing cadence (R$). */
  monthly: number;
  /** Total billed at cadence (R$): monthly × periods. */
  total: number;
  /** Human-readable period label ("mês", "semestre", "ano"). */
  period: string;
  /** Discount percentage vs monthly cadence, if any. */
  discount?: number;
}

export type PricingTable = Record<BillingPeriod, PricingEntry>;

export const PRO_PRICING: PricingTable = {
  monthly: { monthly: 397, total: 397, period: "mês" },
  semiannual: { monthly: 357, total: 2142, period: "semestre", discount: 10 },
  annual: { monthly: 297, total: 3564, period: "ano", discount: 25 },
};

export const CONSULTORIA_PRICING: PricingTable = {
  monthly: { monthly: 997, total: 997, period: "mês" },
  semiannual: { monthly: 897, total: 5382, period: "semestre", discount: 10 },
  annual: { monthly: 797, total: 9564, period: "ano", discount: 20 },
};

/** Stable min/max across both tiers, for AggregateOffer schema. */
export const AGGREGATE_OFFER_BOUNDS = {
  lowPrice: Math.min(PRO_PRICING.annual.monthly, CONSULTORIA_PRICING.annual.monthly),
  highPrice: Math.max(PRO_PRICING.monthly.monthly, CONSULTORIA_PRICING.monthly.monthly),
  // 2 tiers × 3 periods each
  offerCount: 6,
  priceCurrency: "BRL" as const,
};

/** ISO-8601 date one year from `now`, used for Offer.priceValidUntil. */
export function getPriceValidUntil(now: Date = new Date()): string {
  const next = new Date(now);
  next.setFullYear(next.getFullYear() + 1);
  return next.toISOString().split("T")[0];
}
