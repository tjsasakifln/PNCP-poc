/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: process.env.SITE_URL || 'https://smartlic.tech',
  generateRobotsTxt: true, // (optional) Generate robots.txt
  generateIndexSitemap: false, // For small sites, single sitemap is better
  exclude: [
    '/admin',
    '/admin/*',
    '/auth/callback',
    '/api/*',
    '/server-sitemap.xml', // Exclude if using server-side sitemap
  ],
  robotsTxtOptions: {
    policies: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/admin', '/auth/callback', '/api'],
      },
    ],
    additionalSitemaps: [
      'https://smartlic.tech/sitemap.xml',
    ],
  },
  // Additional pages priority configuration
  additionalPaths: async (config) => {
    const result = [];

    // High priority pages
    const highPriorityPages = [
      '/',
      '/buscar',
      '/planos',
      '/features',
    ];

    // Medium priority pages
    const mediumPriorityPages = [
      '/pricing',
      '/login',
      '/signup',
      '/ajuda',
      '/onboarding',
    ];

    // Low priority pages
    const lowPriorityPages = [
      '/privacidade',
      '/termos',
      '/dashboard',
      '/historico',
      '/pipeline',
      '/mensagens',
      '/conta',
      '/recuperar-senha',
      '/redefinir-senha',
      '/planos/obrigado',
    ];

    // Add high priority pages
    for (const page of highPriorityPages) {
      result.push({
        loc: page,
        changefreq: 'daily',
        priority: 1.0,
        lastmod: new Date().toISOString(),
      });
    }

    // Add medium priority pages
    for (const page of mediumPriorityPages) {
      result.push({
        loc: page,
        changefreq: 'weekly',
        priority: 0.7,
        lastmod: new Date().toISOString(),
      });
    }

    // Add low priority pages
    for (const page of lowPriorityPages) {
      result.push({
        loc: page,
        changefreq: 'monthly',
        priority: 0.5,
        lastmod: new Date().toISOString(),
      });
    }

    return result;
  },
  transform: async (config, path) => {
    // Custom transformation for each URL
    return {
      loc: path,
      changefreq: config.changefreq || 'weekly',
      priority: config.priority || 0.7,
      lastmod: config.autoLastmod ? new Date().toISOString() : undefined,
      alternateRefs: config.alternateRefs ?? [],
    };
  },
};
