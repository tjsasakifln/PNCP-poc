/**
 * Stripe.js client singleton (STORY-CONV-003b AC2).
 *
 * `loadStripe` is cached so we never download the library twice per
 * session. The publishable key arrives at runtime via the backend's
 * setup-intent response, so the frontend does not need a build-time
 * `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (but can use one as fallback for
 * tests/local dev).
 */
import { loadStripe, type Stripe } from "@stripe/stripe-js";

let stripePromise: Promise<Stripe | null> | null = null;
let cachedPublishableKey: string | null = null;

export function getStripePromise(publishableKey: string): Promise<Stripe | null> {
  if (!stripePromise || cachedPublishableKey !== publishableKey) {
    cachedPublishableKey = publishableKey;
    stripePromise = loadStripe(publishableKey);
  }
  return stripePromise;
}

export function resetStripePromiseForTests() {
  stripePromise = null;
  cachedPublishableKey = null;
}
