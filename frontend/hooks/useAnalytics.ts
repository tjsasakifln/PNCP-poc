import mixpanel from 'mixpanel-browser';
import { getCookieConsent } from '../app/components/CookieConsentBanner';

const UTM_PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'] as const;
const UTM_STORAGE_KEY = 'smartlic_utm_params';

/**
 * Check if analytics consent has been granted.
 * Returns true only if user explicitly accepted analytics cookies.
 */
function hasAnalyticsConsent(): boolean {
  const consent = getCookieConsent();
  return consent?.analytics === true;
}

/**
 * Capture UTM parameters from the current URL and store in sessionStorage.
 * Sets them as Mixpanel super properties so they persist across the session.
 * Should be called once on first page load (e.g., in layout or _app).
 * STORY-219 AC24, AC25, AC27.
 */
export function captureUTMParams(): void {
  if (typeof window === 'undefined') return;

  try {
    const params = new URLSearchParams(window.location.search);
    const utmData: Record<string, string> = {};

    for (const key of UTM_PARAMS) {
      const value = params.get(key);
      if (value) {
        utmData[key] = value;
      }
    }

    if (Object.keys(utmData).length === 0) return;

    // AC25: Store in sessionStorage
    sessionStorage.setItem(UTM_STORAGE_KEY, JSON.stringify(utmData));

    // AC27: Set as Mixpanel super properties (persist across session)
    if (process.env.NEXT_PUBLIC_MIXPANEL_TOKEN && hasAnalyticsConsent()) {
      mixpanel.register(utmData);
    }
  } catch (error) {
    console.warn('UTM capture failed:', error);
  }
}

/**
 * Retrieve stored UTM parameters from sessionStorage.
 * Used to include UTM data in signup_completed and other events.
 * STORY-219 AC26.
 */
export function getStoredUTMParams(): Record<string, string> {
  if (typeof window === 'undefined') return {};

  try {
    const stored = sessionStorage.getItem(UTM_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

/**
 * Analytics hook for tracking user events with Mixpanel.
 * All tracking functions respect LGPD cookie consent (AC8).
 *
 * @example
 * const { trackEvent } = useAnalytics();
 * trackEvent('search_started', { ufs: ['SC', 'PR'], setor: 'vestuario' });
 */
export const useAnalytics = () => {
  /**
   * Track an event with optional properties.
   * Only fires if analytics consent is granted.
   */
  const trackEvent = (eventName: string, properties?: Record<string, any>) => {
    if (process.env.NEXT_PUBLIC_MIXPANEL_TOKEN && hasAnalyticsConsent()) {
      try {
        mixpanel.track(eventName, {
          ...properties,
          timestamp: new Date().toISOString(),
          environment: process.env.NODE_ENV || 'development',
        });
      } catch (error) {
        console.warn('Analytics tracking failed:', error);
      }
    }
  };

  /**
   * Identify a user for Mixpanel people profiles.
   * Only fires if analytics consent is granted (LGPD AC8).
   * STORY-219 AC10: Sets user properties for segmentation.
   */
  const identifyUser = (userId: string, properties?: Record<string, any>) => {
    if (process.env.NEXT_PUBLIC_MIXPANEL_TOKEN && hasAnalyticsConsent()) {
      try {
        mixpanel.identify(userId);
        if (properties) {
          mixpanel.people.set(properties);
        }
      } catch (error) {
        console.warn('User identification failed:', error);
      }
    }
  };

  /**
   * Reset Mixpanel identity on logout.
   * Generates new distinct_id so post-logout events are anonymous.
   * STORY-219 AC11.
   */
  const resetUser = () => {
    if (process.env.NEXT_PUBLIC_MIXPANEL_TOKEN) {
      try {
        mixpanel.reset();
      } catch (error) {
        console.warn('Mixpanel reset failed:', error);
      }
    }
  };

  /**
   * Track page view. Only fires if analytics consent is granted.
   */
  const trackPageView = (pageName: string) => {
    trackEvent('page_view', { page: pageName });
  };

  return {
    trackEvent,
    identifyUser,
    resetUser,
    trackPageView,
  };
};
