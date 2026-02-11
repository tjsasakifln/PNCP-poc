/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
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
}

module.exports = nextConfig
