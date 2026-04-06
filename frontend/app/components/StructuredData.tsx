/**
 * GTM-COPY-006 AC6: Structured Data (JSON-LD) for Google & AI Search
 *
 * Includes Organization, WebSite (with SearchAction), and SoftwareApplication schemas.
 * FAQPage schema is rendered separately in /ajuda via FaqStructuredData.
 *
 * Uses native <script> instead of next/script — JSON-LD is not executable JS,
 * so async loading via next/script adds unnecessary overhead and delays
 * structured data availability for crawlers.
 */
export function StructuredData() {
  // Organization Schema — AC6
  const organizationSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'SmartLic',
    legalName: 'CONFENGE Avaliações e Inteligência Artificial LTDA',
    url: 'https://smartlic.tech',
    logo: 'https://smartlic.tech/logo.svg',
    foundingDate: '2024',
    description: 'Inteligência de decisão em licitações públicas com avaliação objetiva de viabilidade por setor, região e modalidade',
    address: {
      '@type': 'PostalAddress',
      addressCountry: 'BR',
    },
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'customer support',
      email: 'tiago.sasaki@confenge.com.br',
      availableLanguage: ['Portuguese'],
    },
    sameAs: [
      'https://www.linkedin.com/company/smartlic',
    ],
  };

  // WebSite Schema with Search Action
  const websiteSchema = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'SmartLic',
    url: 'https://smartlic.tech',
    description: 'Inteligência de decisão em licitações públicas com avaliação objetiva de viabilidade por setor, região e modalidade',
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      logo: {
        '@type': 'ImageObject',
        url: 'https://smartlic.tech/logo.svg',
      },
    },
    // SearchAction removed: /buscar is Disallowed in robots.txt (authenticated route).
    // Keeping it would contradict robots.txt and waste crawl budget.
  };

  // SoftwareApplication Schema — AC6
  const softwareApplicationSchema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'SmartLic',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    offers: {
      '@type': 'AggregateOffer',
      lowPrice: '1599.00',
      highPrice: '1999.00',
      priceCurrency: 'BRL',
      offerCount: 3,
    },
    description: 'Avaliação de viabilidade de licitações públicas com critérios objetivos. Filtragem por setor, região e modalidade. Relatórios Excel e pipeline de oportunidades.',
    screenshot: 'https://smartlic.tech/api/og',
    featureList: [
      'Avaliação de viabilidade com 4 critérios objetivos',
      'Filtragem inteligente por setor e região',
      'Relatórios Excel detalhados',
      'Pipeline de oportunidades',
      'Classificação por IA de decisão',
      'Cobertura de fontes oficiais em 27 estados',
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(organizationSchema),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(websiteSchema),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(softwareApplicationSchema),
        }}
      />
    </>
  );
}
