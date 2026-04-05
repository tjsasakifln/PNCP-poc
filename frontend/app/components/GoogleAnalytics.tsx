'use client';

import Script from 'next/script';
import { useEffect } from 'react';
import { safeGetItem } from '../../lib/storage';

// SEO-FIX: nonce prop removed — layout.tsx no longer calls headers(), enabling
// static rendering and Cache-Control: public for CDN caching.
export function GoogleAnalytics() {
  const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID;

  useEffect(() => {
    // Check for user consent (LGPD/GDPR compliant)
    const hasConsent = safeGetItem('cookie-consent') === 'accepted';

    if (hasConsent && GA_MEASUREMENT_ID && typeof window !== 'undefined') {
      // Initialize dataLayer
      window.dataLayer = window.dataLayer || [];
      function gtag(...args: unknown[]) {
        window.dataLayer.push(args);
      }

      gtag('js', new Date());
      gtag('config', GA_MEASUREMENT_ID, {
        page_path: window.location.pathname,
        anonymize_ip: true, // LGPD/GDPR compliance
      });
    }
  }, [GA_MEASUREMENT_ID]);

  // Don't load GA if no measurement ID is configured
  if (!GA_MEASUREMENT_ID) {
    return null;
  }

  return (
    <>
      {/* External GA script — allowed by https://www.googletagmanager.com in CSP script-src */}
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
        strategy="afterInteractive"
      />
      {/* Inline initialization handled by useEffect above — no inline script needed */}
    </>
  );
}

// Helper function to track custom events
export function trackEvent(
  eventName: string,
  eventParams?: Record<string, string | number | boolean | object>
) {
  if (typeof window !== 'undefined' && window.gtag) {
    const hasConsent = safeGetItem('cookie-consent') === 'accepted';
    if (hasConsent) {
      window.gtag('event', eventName, eventParams);
    }
  }
}

// Predefined event trackers for key actions
export const trackSearchEvent = (query: string, resultsCount: number) => {
  trackEvent('search', {
    search_term: query,
    results_count: resultsCount,
  });
};

export const trackDownloadEvent = (filename: string, fileType: string) => {
  trackEvent('file_download', {
    file_name: filename,
    file_type: fileType,
  });
};

export const trackSignupEvent = (method: string) => {
  trackEvent('sign_up', {
    method: method, // e.g., 'email', 'google', etc.
  });
};

export const trackLoginEvent = (method: string) => {
  trackEvent('login', {
    method: method,
  });
};

export const trackPlanSelectedEvent = (planName: string, planPrice: number) => {
  trackEvent('select_item', {
    item_list_name: 'Pricing Plans',
    items: [
      {
        item_name: planName,
        price: planPrice,
      },
    ],
  });
};

// -----------------------------------------------------------------------
// GA4 Enhanced Ecommerce — conforms to GA4 ecommerce spec.
// https://developers.google.com/analytics/devguides/collection/ga4/ecommerce
// Required params: currency (ISO 4217), value (total), items[]
// Each item requires: item_id, item_name; recommended: price, quantity.
// -----------------------------------------------------------------------

export interface GA4EcommerceItem {
  item_id: string;
  item_name: string;
  price: number;
  quantity?: number;
  item_category?: string;
  item_variant?: string; // e.g. "monthly" | "annual"
}

export interface GA4Plan {
  id: string;
  name: string;
  price: number;
  billing_period?: string; // monthly | semiannual | annual
  category?: string;
}

function planToItem(plan: GA4Plan): GA4EcommerceItem {
  return {
    item_id: plan.id,
    item_name: plan.name,
    price: plan.price,
    quantity: 1,
    item_category: plan.category || 'subscription',
    item_variant: plan.billing_period,
  };
}

/**
 * Fires GA4 `view_item` — user saw a plan's product card.
 * Call on page mount or when the plan enters the viewport.
 */
export const trackViewItem = (plan: GA4Plan) => {
  trackEvent('view_item', {
    currency: 'BRL',
    value: plan.price,
    items: [planToItem(plan)],
  });
};

/**
 * Fires GA4 `begin_checkout` — user clicked the "Assinar" / CTA button
 * and is about to be redirected to Stripe.
 */
export const trackBeginCheckout = (plan: GA4Plan) => {
  trackEvent('begin_checkout', {
    currency: 'BRL',
    value: plan.price,
    items: [planToItem(plan)],
  });
};

/**
 * Fires GA4 `purchase` — subscription activation confirmed on the
 * thank-you page. `transaction_id` MUST be unique per purchase (use the
 * Stripe session id or subscription id) to avoid duplicate attribution.
 */
export const trackPurchase = (opts: {
  transaction_id: string;
  value: number;
  currency?: string;
  items: GA4EcommerceItem[];
  tax?: number;
  coupon?: string;
}) => {
  trackEvent('purchase', {
    transaction_id: opts.transaction_id,
    value: opts.value,
    currency: opts.currency || 'BRL',
    items: opts.items,
    ...(opts.tax !== undefined ? { tax: opts.tax } : {}),
    ...(opts.coupon ? { coupon: opts.coupon } : {}),
  });
};

// Declare gtag on window — must match searchStatePersistence.ts declaration
declare global {
  interface Window {
    dataLayer: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}
