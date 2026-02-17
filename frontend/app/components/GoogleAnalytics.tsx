'use client';

import Script from 'next/script';
import { useEffect } from 'react';

export function GoogleAnalytics() {
  const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID;

  useEffect(() => {
    // Check for user consent (LGPD/GDPR compliant)
    const hasConsent = localStorage.getItem('cookie-consent') === 'accepted';

    if (hasConsent && GA_MEASUREMENT_ID && typeof window !== 'undefined') {
      // Initialize dataLayer
      window.dataLayer = window.dataLayer || [];
      function gtag(...args: any[]) {
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
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
        strategy="afterInteractive"
      />
      <Script id="google-analytics" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          // Wait for consent before initializing
          if (localStorage.getItem('cookie-consent') === 'accepted') {
            gtag('config', '${GA_MEASUREMENT_ID}', {
              page_path: window.location.pathname,
              anonymize_ip: true
            });
          }
        `}
      </Script>
    </>
  );
}

// Helper function to track custom events
export function trackEvent(
  eventName: string,
  eventParams?: Record<string, any>
) {
  if (typeof window !== 'undefined' && window.gtag) {
    const hasConsent = localStorage.getItem('cookie-consent') === 'accepted';
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

// Declare gtag on window
declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}
