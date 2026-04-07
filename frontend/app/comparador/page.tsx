import { Metadata } from 'next';
import { Suspense } from 'react';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import ComparadorClient from './ComparadorClient';

export const revalidate = 86400;

export const metadata: Metadata = {
  title: 'Comparador de Editais — Compare Licitações Lado a Lado | SmartLic',
  description:
    'Compare até 3 editais de licitação lado a lado gratuitamente. Veja modalidade, valor, prazo e localização de cada edital. Dados reais do PNCP atualizados diariamente.',
  alternates: {
    canonical: buildCanonical('/comparador'),
  },
  openGraph: {
    title: 'Comparador de Editais — Compare Licitações Lado a Lado',
    description:
      'Compare até 3 editais de licitação lado a lado gratuitamente. Dados reais do PNCP atualizados diariamente.',
    url: buildCanonical('/comparador'),
    type: 'website',
    images: [
      {
        url: '/api/og?title=Comparador+de+Editais',
        width: 1200,
        height: 630,
        alt: 'Comparador de Editais — SmartLic',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Comparador de Editais — Compare Licitações Lado a Lado',
    description:
      'Compare até 3 editais de licitação gratuitamente. Dados reais do PNCP.',
    images: ['/api/og?title=Comparador+de+Editais'],
  },
  robots: { index: true, follow: true },
};

const webAppSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebApplication',
  name: 'Comparador de Editais — SmartLic',
  url: buildCanonical('/comparador'),
  description:
    'Ferramenta gratuita para comparar até 3 editais de licitação lado a lado. Modalidade, valor, prazo e localização em uma única tela.',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'BRL',
  },
};

const breadcrumbSchema = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Início',
      item: SITE_URL,
    },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Ferramentas',
      item: buildCanonical('/ferramentas'),
    },
    {
      '@type': 'ListItem',
      position: 3,
      name: 'Comparador de Editais',
      item: buildCanonical('/comparador'),
    },
  ],
};

export default function ComparadorPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(webAppSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      <LandingNavbar />

      <main className="mx-auto max-w-6xl px-4 pb-20 pt-10 sm:px-6 lg:px-8">
        {/* Hero */}
        <div className="mb-10 text-center">
          <h1 className="mb-3 text-3xl font-extrabold tracking-tight text-[var(--ink)] sm:text-4xl">
            Comparador de Editais
          </h1>
          <p className="mx-auto max-w-2xl text-base text-[var(--ink-secondary)] sm:text-lg">
            Compare até 3 editais de licitação lado a lado — modalidade, valor estimado, prazo de
            abertura e localização. Dados reais do PNCP, atualizados diariamente.
          </p>
        </div>

        {/* Interactive client component — wrapped in Suspense for useSearchParams() */}
        <Suspense
          fallback={
            <div className="py-16 text-center text-sm text-[var(--ink-secondary)]">
              Carregando comparador…
            </div>
          }
        >
          <ComparadorClient />
        </Suspense>
      </main>

      <Footer />
    </>
  );
}
