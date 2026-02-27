const path = require("path");
const { withSentryConfig } = require("@sentry/nextjs");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Fix standalone output when repo has multiple lockfiles (root + frontend)
  // Without this, Next.js infers the wrong workspace root and server.js
  // ends up in a nested path instead of .next/standalone/server.js
  outputFileTracingRoot: path.join(__dirname, './'),
  // CRITICAL: Generate unique build ID to force cache invalidation on deploy
  // This prevents "Failed to find Server Action" errors from stale client bundles
  generateBuildId: async () => {
    // Use timestamp + random for true uniqueness (not git commit)
    return `build-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'static.wixstatic.com',
        pathname: '/media/**',
      },
    ],
  },
  // STORY-210 AC10: Security headers for all responses
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // CSP script-src: 'unsafe-inline' and 'unsafe-eval' are required because:
              // 1. Next.js injects inline scripts for hydration and dynamic imports
              // 2. Stripe.js (https://js.stripe.com) uses eval() for fraud detection
              // Risk accepted and documented (STORY-284 AC4).
              // Future plan: migrate to nonce-based CSP when Next.js supports it
              // natively (tracked in https://github.com/vercel/next.js/discussions/54907)
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://static.cloudflareinsights.com",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https: blob:",
              "font-src 'self' data:",
              "connect-src 'self' https://*.supabase.co https://*.supabase.in https://api.stripe.com https://*.railway.app https://*.ingest.sentry.io https://*.smartlic.tech https://api-js.mixpanel.com https://api.mixpanel.com",
              "frame-src 'self' https://js.stripe.com",
              "object-src 'none'",
              "base-uri 'self'",
            ].join('; '),
          },
        ],
      },
    ];
  },
}

// STORY-211: Wrap with Sentry for error tracking and source map upload (AC8)
module.exports = withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  authToken: process.env.SENTRY_AUTH_TOKEN,

  // Only print logs for uploading source maps in CI
  silent: !process.env.CI,

  // Upload larger set of source maps for prettier stack traces
  widenClientFileUpload: true,

  // Route browser requests to Sentry through Next.js rewrite to circumvent ad-blockers
  tunnelRoute: "/monitoring",

  // Hides source maps from generated client bundles
  hideSourceMaps: true,

  // Tree-shake Sentry debug logger statements to reduce bundle size
  bundleSizeOptimizations: {
    excludeDebugStatements: true,
  },
});
