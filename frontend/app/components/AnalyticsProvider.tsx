"use client";

import { useEffect } from 'react';
import mixpanel from 'mixpanel-browser';
import { usePathname } from 'next/navigation';

/**
 * Analytics Provider - Initializes Mixpanel and tracks page views
 *
 * This component:
 * 1. Initializes Mixpanel on app load
 * 2. Tracks page_load event
 * 3. Tracks page_exit event (beforeunload)
 * 4. Tracks route changes
 */
export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  useEffect(() => {
    // Initialize Mixpanel
    const token = process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

    if (token) {
      try {
        mixpanel.init(token, {
          debug: process.env.NODE_ENV === 'development',
          track_pageview: false, // We'll track manually for more control
          persistence: 'localStorage',
        });

        // Track page_load event
        mixpanel.track('page_load', {
          path: pathname,
          timestamp: new Date().toISOString(),
          environment: process.env.NODE_ENV || 'development',
          referrer: document.referrer || 'direct',
          user_agent: navigator.userAgent,
        });

        console.log('✅ Mixpanel initialized successfully');
      } catch (error) {
        console.warn('❌ Mixpanel initialization failed:', error);
      }
    } else if (process.env.NODE_ENV === 'development') {
      // Only log in development - no warning in production
      console.log('ℹ️ Mixpanel token not configured. Analytics disabled.');
    }

    // Track page_exit event when user leaves
    const handleBeforeUnload = () => {
      if (token) {
        try {
          // Use modern Performance API instead of deprecated performance.timing
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
        } catch (error) {
          console.warn('Failed to track page_exit:', error);
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [pathname]);

  return <>{children}</>;
}
