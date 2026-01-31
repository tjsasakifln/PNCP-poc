"use client";

import { useEffect } from 'react';

/**
 * Hook to register Service Worker for offline support
 * Issue #108 - Offline fallback UI for mobile users
 */
export function useServiceWorker() {
  useEffect(() => {
    if (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      process.env.NODE_ENV === 'production'
    ) {
      window.addEventListener('load', () => {
        navigator.serviceWorker
          .register('/sw.js')
          .then((registration) => {
            console.log('Service Worker registered:', registration.scope);
          })
          .catch((error) => {
            console.error('Service Worker registration failed:', error);
          });
      });

      // Listen for updates
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('Service Worker updated');
      });
    }
  }, []);
}
