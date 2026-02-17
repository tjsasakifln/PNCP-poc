import Script from 'next/script';

export function StructuredData() {
  // Organization Schema
  const organizationSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'SmartLic',
    legalName: 'SmartLic - Busca Inteligente de Licitações',
    url: 'https://smartlic.tech',
    logo: 'https://smartlic.tech/logo.png',
    foundingDate: '2025',
    description: 'Inteligência de decisão em licitações com avaliação objetiva por setor, região e período',
    address: {
      '@type': 'PostalAddress',
      addressCountry: 'BR',
      addressLocality: 'Brasil',
    },
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'customer support',
      email: 'contato@smartlic.tech',
      availableLanguage: ['Portuguese', 'pt-BR'],
    },
    sameAs: [
      'https://www.linkedin.com/company/smartlic',
      // Add other social profiles when available
    ],
  };

  // WebSite Schema with Search Action
  const websiteSchema = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'SmartLic',
    url: 'https://smartlic.tech',
    description: 'Inteligência de decisão em licitações com avaliação objetiva por setor, região e período',
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      logo: {
        '@type': 'ImageObject',
        url: 'https://smartlic.tech/logo.png',
      },
    },
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: 'https://smartlic.tech/buscar?q={search_term_string}',
      },
      'query-input': 'required name=search_term_string',
    },
  };

  // SoftwareApplication Schema
  const softwareApplicationSchema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'SmartLic',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    offers: {
      '@type': 'Offer',
      price: '1999.00',
      priceCurrency: 'BRL',
      priceValidUntil: '2026-12-31',
      availability: 'https://schema.org/InStock',
      seller: {
        '@type': 'Organization',
        name: 'SmartLic',
      },
    },
    description: 'Inteligência de decisão para oportunidades de licitação. Busca inteligente, análise por setor, geração de relatórios e muito mais.',
    screenshot: 'https://smartlic.tech/og-image.png',
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.8',
      reviewCount: '127',
      bestRating: '5',
      worstRating: '1',
    },
    featureList: [
      'Busca inteligente de licitações',
      'Análise por setor e região',
      'Relatórios personalizados',
      'Pipeline de oportunidades',
      'Avaliação por IA',
      'Exportação para Excel',
    ],
  };

  return (
    <>
      {/* Organization Schema */}
      <Script
        id="organization-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(organizationSchema),
        }}
      />

      {/* WebSite Schema with Search Action */}
      <Script
        id="website-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(websiteSchema),
        }}
      />

      {/* SoftwareApplication Schema */}
      <Script
        id="software-application-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(softwareApplicationSchema),
        }}
      />
    </>
  );
}
