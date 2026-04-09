"use client";

import { useEffect, useRef } from 'react';
import mixpanel from 'mixpanel-browser';
import * as Sentry from '@sentry/nextjs';
import { usePathname } from 'next/navigation';
import { getCookieConsent, type CookieConsent } from './CookieConsentBanner';
import { captureUTMParams } from '../../hooks/useAnalytics';
import { useClarity } from '../../hooks/useClarity';
import { useAuth } from './AuthProvider';
import { useUserProfile } from '../../hooks/useUserProfile';

// GTM-FIX-002: Explicit client-side Sentry initialization
// withSentryConfig webpack plugin should auto-inject sentry.client.config.ts,
// but in production builds (standalone output) it may fail silently.
// This ensures Sentry is always initialized on the client.
const sentryDsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
if (sentryDsn && !Sentry.getClient()) {
  Sentry.init({
    dsn: sentryDsn,
    tracesSampleRate: 0.1,
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV,
  });
}

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
  const clarityIdentifiedRef = useRef(false);
  const { user } = useAuth();
  const { data: profileData } = useUserProfile();
  const { clarityIdentify, claritySet } = useClarity();

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

      // STORY-219 AC24-AC27: Capture UTM params on first load
      captureUTMParams();

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

  // Identifica o usuário e tagueia sessão no Clarity quando auth + perfil estiverem disponíveis
  useEffect(() => {
    if (!user?.id || clarityIdentifiedRef.current) return;
    const consent = getCookieConsent();
    if (!consent?.analytics) return;

    clarityIdentify(user.id);

    if (profileData) {
      const planId = String(profileData.plan_id ?? 'unknown');
      const isTrial = planId === 'free_trial';
      claritySet('plan_type', planId);
      claritySet('is_trial', String(isTrial));
      claritySet('user_segment', isTrial ? 'trial' : 'paid');
    }

    clarityIdentifiedRef.current = true;
  }, [user?.id, profileData, clarityIdentify, claritySet]);

  return <>{children}</>;
}
