const path = require("path");
const { withSentryConfig } = require("@sentry/nextjs");

// STORY-5.10 (TD-FE-012): Opt-in bundle analyzer. Run via `npm run analyze`,
// which sets ANALYZE=true. Reports are written under .next/analyze/*.html.
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
  openAnalyzer: false,
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  trailingSlash: false,
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

  // STORY-5.10 (TD-FE-012): Tree-shake heavy UI/interaction packages.
  // Next's optimizePackageImports rewrites `import { X } from 'pkg'` to
  // `import X from 'pkg/dist/X'`, eliminating transitively pulled symbols.
  // Validated targets: all framer-motion callsites use named imports
  // (motion, AnimatePresence, useInView); all @dnd-kit callsites use
  // named imports (useSortable, useDroppable, SortableContext, CSS, ...).
  experimental: {
    optimizePackageImports: [
      'framer-motion',
      '@dnd-kit/core',
      '@dnd-kit/sortable',
      '@dnd-kit/utilities',
    ],
  },
  // STORY-311 AC5: Security headers unified in middleware.ts (removed duplication).
  // Middleware covers all non-static routes. Static assets (_next/static, images)
  // don't need CSP/X-Frame-Options. HSTS is enforced at Railway edge proxy level.

  // SEO: Redirect acentuado → slug canônico (ISSUE-SEO-004)
  // SEO: Consolidar pricing pages — /pricing → /planos (ISSUE-SEO-005)
  async redirects() {
    return [
      {
        source: '/gloss%C3%A1rio',
        destination: '/glossario',
        permanent: true,
      },
      {
        source: '/gloss\u00E1rio',
        destination: '/glossario',
        permanent: true,
      },
      {
        source: '/gloss%C3%A1rio/:path*',
        destination: '/glossario/:path*',
        permanent: true,
      },
      {
        source: '/gloss\u00E1rio/:path*',
        destination: '/glossario/:path*',
        permanent: true,
      },
      {
        source: '/pricing',
        destination: '/planos',
        permanent: true,
      },
    ];
  },

  // SYS-019: Cache headers for static assets (CDN-ready)
  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=2592000, immutable' },
        ],
      },
      {
        source: '/images/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=604800' },
        ],
      },
      {
        source: '/fonts/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
    ];
  },
}

// STORY-211: Wrap with Sentry for error tracking and source map upload (AC8).
// STORY-5.10 (TD-FE-012): Wrap with Bundle Analyzer (opt-in via ANALYZE=true).
module.exports = withSentryConfig(withBundleAnalyzer(nextConfig), {
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
