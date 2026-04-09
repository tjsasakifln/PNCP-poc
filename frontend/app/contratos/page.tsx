import { Metadata } from 'next';
import Link from 'next/link';
import { SECTORS } from '@/lib/sectors';
import { ALL_UFS, UF_NAMES } from '@/lib/programmatic';
import { buildCanonical } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const metadata: Metadata = {
  title: 'Contratos Publicos por Setor e Estado — SmartLic',
  description:
    'Consulte contratos publicos do governo por setor e estado. Dados do PNCP atualizados diariamente. Transparencia em gastos publicos.',
  alternates: { canonical: buildCanonical('/contratos') },
  openGraph: {
    title: 'Contratos Publicos por Setor e Estado',
    description: 'Transparencia em gastos publicos — dados do PNCP atualizados diariamente.',
    type: 'website',
    locale: 'pt_BR',
  },
  robots: { index: true, follow: true },
};

export default function ContratosHubPage() {
  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Contratos Publicos', url: '/contratos' },
  ];

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Contratos Publicos por Setor e Estado',
    description: 'Diretorio de contratos publicos do governo brasileiro por setor e estado.',
    url: 'https://smartlic.tech/contratos',
    provider: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
    breadcrumb: {
      '@type': 'BreadcrumbList',
      itemListElement: breadcrumbs.map((b, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: b.name,
        item: `https://smartlic.tech${b.url}`,
      })),
    },
  };

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-gray-50 pt-20 pb-16">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />

        {/* Breadcrumb */}
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 text-sm text-gray-500">
          {breadcrumbs.map((b, i) => (
            <span key={b.url}>
              {i > 0 && <span className="mx-1">/</span>}
              {i < breadcrumbs.length - 1 ? (
                <Link href={b.url} className="hover:text-blue-600">{b.name}</Link>
              ) : (
                <span className="text-gray-900 font-medium">{b.name}</span>
              )}
            </span>
          ))}
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Contratos Publicos por Setor e Estado
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Consulte quanto o governo gasta por setor em cada estado. Dados do Portal Nacional de
            Contratacoes Publicas (PNCP), atualizados diariamente.
          </p>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {SECTORS.map((sector) => (
              <div
                key={sector.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow"
              >
                <h2 className="text-lg font-semibold text-gray-900 mb-1">{sector.name}</h2>
                <p className="text-sm text-gray-500 mb-3">{sector.description}</p>
                <div className="flex flex-wrap gap-1.5">
                  {ALL_UFS.map((uf) => (
                    <Link
                      key={uf}
                      href={`/contratos/${sector.slug}/${uf.toLowerCase()}`}
                      className="inline-block px-2 py-0.5 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
                    >
                      {uf}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Internal linking */}
          <div className="mt-12 border-t border-gray-200 pt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Explore tambem</h2>
            <div className="flex flex-wrap gap-3">
              <Link href="/fornecedores" className="text-blue-600 hover:underline">
                Fornecedores do Governo
              </Link>
              <Link href="/dados" className="text-blue-600 hover:underline">
                Dados Publicos Agregados
              </Link>
              <Link href="/alertas-publicos" className="text-blue-600 hover:underline">
                Alertas de Licitacoes
              </Link>
              <Link href="/orgaos" className="text-blue-600 hover:underline">
                Orgaos Compradores
              </Link>
              <Link href="/licitacoes" className="text-blue-600 hover:underline">
                Licitacoes por Setor
              </Link>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
