import mixpanel from 'mixpanel-browser';
import { getCookieConsent } from '../app/components/CookieConsentBanner';

/**
 * Check if analytics consent has been granted.
 * Returns true only if user explicitly accepted analytics cookies.
 */
function hasAnalyticsConsent(): boolean {
  const consent = getCookieConsent();
  return consent?.analytics === true;
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
   * Track page view. Only fires if analytics consent is granted.
   */
  const trackPageView = (pageName: string) => {
    trackEvent('page_view', { page: pageName });
  };

  return {
    trackEvent,
    identifyUser,
    trackPageView,
  };
};
