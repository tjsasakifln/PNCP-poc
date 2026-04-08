import { Metadata } from 'next';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import EmbedPreviewClient from './EmbedPreviewClient';

export const revalidate = 86400; // 24h ISR

export const metadata: Metadata = {
  title: 'Embed Badge de Estatísticas | SmartLic',
  description:
    'Incorpore estatísticas de licitações públicas no seu site, blog ou reportagem. Widget HTML auto-contido com dados atualizados do PNCP.',
  alternates: { canonical: buildCanonical('/estatisticas/embed') },
  openGraph: {
    title: 'Embed Badge de Estatísticas de Licitações | SmartLic',
    description:
      'Widget HTML para incorporar dados de licitações públicas do PNCP. Atribuição automática.',
    url: buildCanonical('/estatisticas/embed'),
    type: 'website',
    locale: 'pt_BR',
  },
  twitter: {
    card: 'summary',
    title: 'Embed Badge de Estatísticas | SmartLic',
    description: 'Incorpore dados de licitações públicas no seu site.',
  },
};

const breadcrumbSchema = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: 'Início', item: SITE_URL },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Estatísticas',
      item: buildCanonical('/estatisticas'),
    },
    {
      '@type': 'ListItem',
      position: 3,
      name: 'Embed Badge',
      item: buildCanonical('/estatisticas/embed'),
    },
  ],
};

export default function EstatisticasEmbedPage() {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || 'https://api.smartlic.tech';

  const embedHtml = `<iframe src="${backendUrl}/v1/stats/public?format=embed" width="500" height="260" frameborder="0" style="border:none;border-radius:12px;max-width:100%"></iframe>`;
  const badgeHtml = `<a href="https://smartlic.tech/estatisticas"><img src="${backendUrl}/v1/stats/public?format=badge" alt="Estatísticas SmartLic - PNCP" /></a>`;

  return (
    <main className="min-h-screen bg-white dark:bg-gray-950">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-blue to-blue-700 text-white py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Embed de Estatísticas de Licitações
          </h1>
          <p className="text-blue-100 text-lg">
            Incorpore dados atualizados do PNCP no seu site, blog ou
            reportagem. Widget HTML auto-contido com atribuição automática.
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-12 space-y-16">
        {/* Option 1: Embed Widget */}
        <section>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Opção 1: Widget Completo (iframe)
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Mostra 4 estatísticas-chave (total editais, valor total, valor
            médio, UF líder) com atualização automática. Ideal para reportagens e blogs.
          </p>
          <EmbedPreviewClient code={embedHtml} label="Widget" />
        </section>

        {/* Option 2: Badge */}
        <section>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Opção 2: Badge Compacto (SVG)
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Badge estilo shields.io com total de editais. Leve (SVG), ideal para
            READMEs, sidebars e rodapés.
          </p>
          <EmbedPreviewClient code={badgeHtml} label="Badge" />
        </section>

        {/* Option 3: JSON API */}
        <section>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Opção 3: API JSON (para desenvolvedores)
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Endpoint público, sem autenticação. Retorna ~15 métricas agregadas
            com schema Dataset/DataDownload para Google Dataset Search.
          </p>
          <div className="bg-gray-900 dark:bg-gray-800 rounded-lg p-4 text-sm font-mono text-green-400 overflow-x-auto">
            GET {backendUrl}/v1/stats/public
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
            Cache: 6h · Formato: JSON · Licença: CC BY 4.0
          </p>
        </section>

        {/* Attribution */}
        <section className="bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800 p-6">
          <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
            Atribuição
          </h3>
          <p className="text-blue-800 dark:text-blue-300 text-sm">
            Os dados são públicos (fonte: PNCP) e podem ser citados livremente.
            Pedimos apenas a manutenção do link para{' '}
            <a
              href="https://smartlic.tech/estatisticas"
              className="underline"
            >
              smartlic.tech/estatisticas
            </a>{' '}
            como atribuição.
          </p>
        </section>

        {/* Back link */}
        <div className="text-center">
          <a
            href="/estatisticas"
            className="text-brand-blue hover:underline font-medium"
          >
            &larr; Voltar para Estatísticas
          </a>
        </div>
      </div>
    </main>
  );
}
