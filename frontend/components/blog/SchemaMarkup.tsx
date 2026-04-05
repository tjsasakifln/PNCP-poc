/**
 * MKT-002 AC3: Automatic JSON-LD schema markup component.
 *
 * Generates structured data for programmatic SEO pages.
 * Supports: Article, FAQPage, Dataset, BreadcrumbList, HowTo, LocalBusiness, ItemList.
 * Each programmatic page receives 3-4 schema types automatically.
 */

export type SchemaPageType =
  | 'sector'
  | 'sector-uf'
  | 'city'
  | 'cidade' // SEO Frente 4: alias for pt-BR city pages (same behavior as 'city')
  | 'panorama'
  | 'article'
  | 'analise'
  | 'faq';

interface FAQ {
  question: string;
  answer: string;
}

interface BreadcrumbItem {
  name: string;
  url: string;
}

interface DatasetItem {
  name: string;
  value: string | number;
}

export interface SchemaMarkupProps {
  pageType: SchemaPageType;
  title: string;
  description: string;
  url: string;
  datePublished?: string;
  dateModified?: string;
  breadcrumbs?: BreadcrumbItem[];
  faqs?: FAQ[];
  dataPoints?: DatasetItem[];
  sectorName?: string;
  uf?: string;
  cidade?: string;
  totalEditais?: number;
  avgValue?: number;
}

function buildArticleSchema(props: SchemaMarkupProps) {
  const base: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: props.title,
    description: props.description,
    url: props.url,
    datePublished: props.datePublished || new Date().toISOString(),
    dateModified: props.dateModified || new Date().toISOString(),
    author: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: 'https://smartlic.tech',
    },
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: 'https://smartlic.tech',
      logo: {
        '@type': 'ImageObject',
        url: 'https://smartlic.tech/smartlic-logo.png',
      },
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': props.url,
    },
  };

  // SEO-PLAYBOOK P6: analise pages get an `about` field tied to the sector
  if (props.pageType === 'analise' && props.sectorName) {
    base.about = {
      '@type': 'Thing',
      name: props.sectorName,
    };
  }

  return base;
}

function buildFAQSchema(faqs: FAQ[]) {
  if (!faqs || faqs.length === 0) return null;
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };
}

function buildDatasetSchema(props: SchemaMarkupProps) {
  const dataPoints = props.dataPoints || [];
  if (dataPoints.length === 0 && !props.totalEditais) return null;

  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `Dados de Licitações — ${props.sectorName || 'Brasil'}${props.uf ? ` em ${props.uf}` : ''}`,
    description: props.description,
    url: props.url,
    creator: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: 'https://smartlic.tech',
    },
    temporalCoverage: `${new Date().getFullYear()}`,
    spatialCoverage: {
      '@type': 'Place',
      name: props.uf || props.cidade || 'Brasil',
    },
    distribution: {
      '@type': 'DataDownload',
      contentUrl: props.url,
      encodingFormat: 'text/html',
    },
    variableMeasured: dataPoints.map((dp) => ({
      '@type': 'PropertyValue',
      name: dp.name,
      value: dp.value,
    })),
  };
}

function buildBreadcrumbSchema(breadcrumbs?: BreadcrumbItem[]) {
  if (!breadcrumbs || breadcrumbs.length === 0) return null;
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  };
}

function buildHowToSchema(props: SchemaMarkupProps) {
  if (props.pageType !== 'sector' && props.pageType !== 'panorama') return null;

  return {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: `Como encontrar licitações de ${props.sectorName || 'seu setor'}`,
    description: `Guia passo a passo para encontrar e analisar licitações de ${props.sectorName || 'seu setor'} no Brasil`,
    step: [
      {
        '@type': 'HowToStep',
        name: 'Defina seu setor',
        text: `Selecione ${props.sectorName || 'o setor desejado'} nos filtros de busca do SmartLic.`,
      },
      {
        '@type': 'HowToStep',
        name: 'Escolha as UFs de interesse',
        text: 'Selecione os estados onde sua empresa atua ou deseja expandir.',
      },
      {
        '@type': 'HowToStep',
        name: 'Analise a viabilidade',
        text: 'Use o score de viabilidade de 4 fatores para priorizar as melhores oportunidades.',
      },
      {
        '@type': 'HowToStep',
        name: 'Monte sua proposta',
        text: 'Exporte os editais relevantes e prepare sua documentação com antecedência.',
      },
    ],
  };
}

function buildLocalBusinessSchema(props: SchemaMarkupProps) {
  if (props.pageType !== 'city' && props.pageType !== 'cidade') return null;
  if (!props.cidade) return null;

  return {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: `SmartLic — Licitações em ${props.cidade}`,
    description: `Oportunidades de licitação pública em ${props.cidade}${props.uf ? `, ${props.uf}` : ''}`,
    url: props.url,
    areaServed: {
      '@type': 'City',
      name: props.cidade,
      ...(props.uf
        ? {
            containedInPlace: {
              '@type': 'AdministrativeArea',
              name: props.uf,
            },
          }
        : {}),
    },
    address: {
      '@type': 'PostalAddress',
      addressLocality: props.cidade,
      addressRegion: props.uf || '',
      addressCountry: 'BR',
    },
  };
}

function buildItemListSchema(props: SchemaMarkupProps) {
  if (
    props.pageType !== 'sector-uf' &&
    props.pageType !== 'city' &&
    props.pageType !== 'cidade'
  )
    return null;
  if (!props.totalEditais || props.totalEditais === 0) return null;

  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `Licitações de ${props.sectorName || 'setor'}${props.uf ? ` em ${props.uf}` : ''}`,
    description: props.description,
    numberOfItems: props.totalEditais,
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: `${props.totalEditais} licitações abertas`,
        url: props.url,
      },
    ],
  };
}

/**
 * Generate all applicable schemas for the page type.
 * Returns 3-4 schema types per page.
 */
function getSchemas(props: SchemaMarkupProps): object[] {
  const schemas: object[] = [];

  // Article schema — always included except for pure FAQ pages
  if (props.pageType !== 'faq') {
    schemas.push(buildArticleSchema(props));
  }

  // Breadcrumb — always included if provided
  const breadcrumb = buildBreadcrumbSchema(props.breadcrumbs);
  if (breadcrumb) schemas.push(breadcrumb);

  // FAQ — included if FAQs provided
  const faq = props.faqs ? buildFAQSchema(props.faqs) : null;
  if (faq) schemas.push(faq);

  // Dataset — included for data-rich pages
  const dataset = buildDatasetSchema(props);
  if (dataset) schemas.push(dataset);

  // HowTo — sector panorama pages
  const howTo = buildHowToSchema(props);
  if (howTo) schemas.push(howTo);

  // LocalBusiness — city pages
  const localBiz = buildLocalBusinessSchema(props);
  if (localBiz) schemas.push(localBiz);

  // ItemList — sector×UF and city pages
  const itemList = buildItemListSchema(props);
  if (itemList) schemas.push(itemList);

  return schemas;
}

/**
 * SchemaMarkup component — renders JSON-LD script tags.
 *
 * Usage:
 * ```tsx
 * <SchemaMarkup
 *   pageType="sector"
 *   title="Licitações de Vestuário"
 *   description="..."
 *   url="https://smartlic.tech/blog/programmatic/vestuario"
 *   sectorName="Vestuário e Uniformes"
 *   totalEditais={42}
 *   breadcrumbs={[...]}
 *   faqs={[...]}
 * />
 * ```
 */
export default function SchemaMarkup(props: SchemaMarkupProps) {
  const schemas = getSchemas(props);

  return (
    <>
      {schemas.map((schema, i) => (
        <script
          key={`schema-${i}`}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
      ))}
    </>
  );
}
