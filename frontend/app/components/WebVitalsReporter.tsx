/**
 * STORY-SEO-006: Real User Monitoring (RUM) for Core Web Vitals.
 *
 * Reports LCP / INP / CLS / TTFB / FCP from real users into Google Analytics 4
 * via custom `web_vitals` events. GA4 was chosen over Vercel Speed Insights
 * because SmartLic is hosted on Railway, not Vercel (Opção B in the story).
 *
 * Silently no-ops if `window.gtag` is unavailable (consent denied, ad-blocker,
 * script failure) — never throws, never blocks rendering.
 *
 * Read docs/observability/web-vitals.md for interpretation thresholds and
 * how to build the GA4 Explorations dashboard.
 */
"use client";

import { useEffect } from "react";
import { onCLS, onINP, onLCP, onTTFB, onFCP, type Metric } from "web-vitals";

// `window.gtag` is declared globally (with a broader signature) in
// `app/components/GoogleAnalytics.tsx` — reuse it here instead of redeclaring.

function report(metric: Metric): void {
  if (typeof window === "undefined" || typeof window.gtag !== "function") {
    return;
  }

  // CLS is a unitless ratio; multiply by 1000 so GA4 can aggregate as integer.
  const value = metric.name === "CLS" ? Math.round(metric.value * 1000) : Math.round(metric.value);

  window.gtag("event", "web_vitals", {
    event_category: "Web Vitals",
    event_label: metric.name,
    value,
    non_interaction: true,
    metric_id: metric.id,
    metric_value: metric.value,
    metric_delta: metric.delta,
    metric_rating: metric.rating,
    navigation_type: metric.navigationType,
  });
}

export function WebVitalsReporter(): null {
  useEffect(() => {
    onCLS(report);
    onINP(report);
    onLCP(report);
    onTTFB(report);
    onFCP(report);
  }, []);

  return null;
}
