'use client';

import { useEffect } from 'react';
import { getCookieConsent, type CookieConsent } from './CookieConsentBanner';

// SEO-FIX: nonce prop removed. Replaced <Script> inline with useEffect — the script
// src loads from https://www.clarity.ms (allowed by CSP domain allowlist), no
// inline script needed in HTML so no hash/nonce required.
export function ClarityAnalytics() {
  const CLARITY_PROJECT_ID = process.env.NEXT_PUBLIC_CLARITY_PROJECT_ID;

  useEffect(() => {
    if (!CLARITY_PROJECT_ID) return;

    type ClarityWin = Window & { clarity?: ((...args: unknown[]) => void) & { q?: unknown[] } };

    const loadScript = () => {
      // LGPD: só carrega após consentimento analytics (mesmo gate do Mixpanel/GA4)
      const consent = getCookieConsent();
      if (!consent?.analytics) return;

      const win = window as ClarityWin;
      // Initialize clarity queue before script loads
      win.clarity = win.clarity || function (...args: unknown[]) {
        (win.clarity!.q = win.clarity!.q || []).push(args);
      };

      // Avoid double-loading
      if (document.querySelector(`script[src*="clarity.ms/tag/${CLARITY_PROJECT_ID}"]`)) return;

      // Dynamically load Clarity — src allowed by https://www.clarity.ms in CSP script-src
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.clarity.ms/tag/${CLARITY_PROJECT_ID}`;
      document.head.appendChild(script);
    };

    loadScript();

    // Listen for consent changes (user accepts after initial load)
    const handleConsentChanged = (e: Event) => {
      const detail = (e as CustomEvent).detail as CookieConsent | null;
      if (detail?.analytics) loadScript();
    };
    window.addEventListener('cookie-consent-changed', handleConsentChanged);

    return () => {
      window.removeEventListener('cookie-consent-changed', handleConsentChanged);
    };
  }, [CLARITY_PROJECT_ID]);

  return null;
}
