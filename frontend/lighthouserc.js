/**
 * Lighthouse CI Configuration
 *
 * Performance budgets and assertions for BidIQ frontend.
 *
 * Run locally:
 *   npm run build
 *   npm run lighthouse
 *
 * CI integration: .github/workflows/lighthouse.yml
 */

module.exports = {
  ci: {
    collect: {
      // Build and serve the app
      startServerCommand: 'npm run start',
      startServerReadyPattern: 'Ready',
      startServerReadyTimeout: 30000,
      url: [
        'http://localhost:3000',
      ],
      numberOfRuns: 3, // Run 3 times and take median
      settings: {
        preset: 'desktop',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0,
        },
        screenEmulation: {
          mobile: false,
          width: 1350,
          height: 940,
          deviceScaleFactor: 1,
          disabled: false,
        },
        formFactor: 'desktop',
      },
    },
    upload: {
      target: 'temporary-public-storage', // Or 'filesystem' for local
    },
    assert: {
      preset: 'lighthouse:recommended',
      assertions: {
        // ====================================================================
        // Performance Metrics (Core Web Vitals)
        // ====================================================================

        // First Contentful Paint - when first content appears
        'first-contentful-paint': ['error', { maxNumericValue: 2000 }], // < 2s

        // Largest Contentful Paint - main content loaded (Core Web Vital)
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }], // < 2.5s (Good)

        // Cumulative Layout Shift - visual stability (Core Web Vital)
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }], // < 0.1 (Good)

        // Total Blocking Time - interactivity
        'total-blocking-time': ['error', { maxNumericValue: 300 }], // < 300ms

        // Speed Index - how quickly content is visually displayed
        'speed-index': ['error', { maxNumericValue: 3400 }], // < 3.4s

        // Interactive - when page becomes fully interactive
        'interactive': ['error', { maxNumericValue: 3800 }], // < 3.8s

        // ====================================================================
        // Category Scores (0-100)
        // ====================================================================

        'categories:performance': ['error', { minScore: 0.85 }], // 85+
        'categories:accessibility': ['warn', { minScore: 0.90 }], // 90+
        'categories:best-practices': ['warn', { minScore: 0.90 }], // 90+
        'categories:seo': ['warn', { minScore: 0.90 }], // 90+

        // ====================================================================
        // Resource Optimization
        // ====================================================================

        // Image optimization
        'uses-optimized-images': 'warn',
        'modern-image-formats': 'warn',
        'uses-responsive-images': 'warn',

        // JavaScript optimization
        'unminified-javascript': 'warn',
        'unused-javascript': 'off', // Often has false positives with Next.js

        // CSS optimization
        'unminified-css': 'warn',
        'unused-css-rules': 'off', // Often has false positives with Tailwind

        // Network optimization
        'uses-text-compression': 'warn',
        'uses-rel-preconnect': 'warn',

        // ====================================================================
        // Next.js Specific
        // ====================================================================

        // Ensure next/image is used (no native img tags without optimization)
        'unsized-images': 'error',

        // Font optimization
        'font-display': 'warn',

        // ====================================================================
        // Accessibility (A11y)
        // ====================================================================

        'color-contrast': 'warn',
        'image-alt': 'error',
        'label': 'warn',
        'link-name': 'warn',

        // ====================================================================
        // Best Practices
        // ====================================================================

        'errors-in-console': 'warn',
        'is-on-https': 'off', // Local dev uses HTTP
        'uses-http2': 'off', // Local dev uses HTTP/1.1
      },
    },
  },
};
