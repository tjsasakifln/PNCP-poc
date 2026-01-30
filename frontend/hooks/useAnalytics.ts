import mixpanel from 'mixpanel-browser';

/**
 * Analytics hook for tracking user events with Mixpanel
 *
 * @example
 * const { trackEvent } = useAnalytics();
 * trackEvent('search_started', { ufs: ['SC', 'PR'], setor: 'vestuario' });
 */
export const useAnalytics = () => {
  /**
   * Track an event with optional properties
   *
   * @param eventName - Name of the event (e.g., 'search_started')
   * @param properties - Additional event properties
   */
  const trackEvent = (eventName: string, properties?: Record<string, any>) => {
    // Only track if Mixpanel is initialized (token exists)
    if (process.env.NEXT_PUBLIC_MIXPANEL_TOKEN) {
      try {
        mixpanel.track(eventName, {
          ...properties,
          timestamp: new Date().toISOString(),
          environment: process.env.NODE_ENV || 'development',
        });
      } catch (error) {
        // Silently fail - analytics should never break the app
        console.warn('Analytics tracking failed:', error);
      }
    }
  };

  /**
   * Identify a user (for future use when auth is implemented)
   *
   * @param userId - Unique user identifier
   * @param properties - User properties
   */
  const identifyUser = (userId: string, properties?: Record<string, any>) => {
    if (process.env.NEXT_PUBLIC_MIXPANEL_TOKEN) {
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
   * Track page view
   *
   * @param pageName - Name of the page
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
