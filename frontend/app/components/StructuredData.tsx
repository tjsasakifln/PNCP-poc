import Script from 'next/script';

/**
 * GTM-COPY-006 AC6: Structured Data (JSON-LD) for Google & AI Search
 *
 * Includes Organization, WebSite (with SearchAction), and SoftwareApplication schemas.
 * FAQPage schema is rendered separately in /ajuda via FaqStructuredData.
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
      email: 'contato@smartlic.tech',
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
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: 'https://smartlic.tech/buscar?q={search_term_string}',
      },
      'query-input': 'required name=search_term_string',
    },
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
      lowPrice: '297.00',
      highPrice: '397.00',
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
      <Script
        id="organization-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(organizationSchema),
        }}
      />
      <Script
        id="website-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(websiteSchema),
        }}
      />
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
