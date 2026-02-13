"use client";

import { useEffect, useRef } from 'react';
import mixpanel from 'mixpanel-browser';
import { usePathname } from 'next/navigation';
import { getCookieConsent, type CookieConsent } from './CookieConsentBanner';

/**
 * Analytics Provider - Initializes Mixpanel ONLY after cookie consent (LGPD Art. 7)
 *
 * This component:
 * 1. Checks cookie consent before any analytics initialization
 * 2. Initializes Mixpanel only if analytics consent is granted
 * 3. Tracks page_load event after consent
 * 4. Tracks page_exit event (beforeunload)
 * 5. Listens for consent changes and initializes/disables accordingly
 */
export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const initializedRef = useRef(false);

  useEffect(() => {
    const token = process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
    if (!token) {
      if (process.env.NODE_ENV === 'development') {
        console.log('Mixpanel token not configured. Analytics disabled.');
      }
      return;
    }

    const initMixpanel = (consent: CookieConsent | null) => {
      if (!consent || !consent.analytics) {
        // No consent or opted out — do not initialize
        if (initializedRef.current) {
          try {
            mixpanel.opt_out_tracking();
          } catch {
            // ignore
          }
        }
        return;
      }

      // Consent granted — initialize Mixpanel
      if (!initializedRef.current) {
        try {
          mixpanel.init(token, {
            debug: process.env.NODE_ENV === 'development',
            track_pageview: false,
            persistence: 'localStorage',
          });
          initializedRef.current = true;
        } catch (error) {
          console.warn('Mixpanel initialization failed:', error);
          return;
        }
      } else {
        // Re-enable tracking if previously opted out
        try {
          mixpanel.opt_in_tracking();
        } catch {
          // ignore
        }
      }

      // Track page_load
      try {
        mixpanel.track('page_load', {
          path: pathname,
          timestamp: new Date().toISOString(),
          environment: process.env.NODE_ENV || 'development',
          referrer: document.referrer || 'direct',
          user_agent: navigator.userAgent,
        });
      } catch {
        // ignore
      }
    };

    // Check current consent and initialize
    const consent = getCookieConsent();
    initMixpanel(consent);

    // Listen for consent changes
    const handleConsentChanged = (e: Event) => {
      const detail = (e as CustomEvent).detail as CookieConsent | null;
      initMixpanel(detail);
    };
    window.addEventListener('cookie-consent-changed', handleConsentChanged);

    // Track page_exit only if consent was granted
    const handleBeforeUnload = () => {
      const currentConsent = getCookieConsent();
      if (currentConsent?.analytics && initializedRef.current) {
        try {
          const navEntries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
          const navigationStart = navEntries.length > 0
            ? navEntries[0].startTime
            : performance.timeOrigin;

          const sessionDuration = Date.now() - navigationStart;

          mixpanel.track('page_exit', {
            path: pathname,
            session_duration_ms: sessionDuration,
            session_duration_readable: `${Math.floor(sessionDuration / 1000)}s`,
            timestamp: new Date().toISOString(),
          });
        } catch {
          // ignore
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('cookie-consent-changed', handleConsentChanged);
    };
  }, [pathname]);

  return <>{children}</>;
}
