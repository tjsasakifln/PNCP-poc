import { Metadata } from 'next';
import Link from 'next/link';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import { SECTORS } from '@/lib/sectors';
import { ALL_UFS, UF_NAMES } from '@/lib/programmatic';

/**
 * MKT-003 AC7: Index page listing all sectors × UFs.
 *
 * Static page linking to all programmatic licitacoes pages.
 */

export const metadata: Metadata = {
  title: 'Licitações por Setor e Estado — Dados ao Vivo',
  description:
    'Explore licitações públicas por setor e estado. 15 setores × 27 UFs com dados ao vivo de PNCP, PCP e ComprasGov. Encontre oportunidades para sua empresa.',
  alternates: { canonical: 'https://smartlic.tech/blog/licitacoes' },
  openGraph: {
    title: 'Licitações por Setor e Estado | SmartLic',
    description: 'Diretório de licitações públicas: 15 setores, 27 estados, dados ao vivo.',
    url: 'https://smartlic.tech/blog/licitacoes',
    type: 'website',
    locale: 'pt_BR',
  },
};

/** Phase 1 sectors highlighted (5 largest) */
const PHASE1_SECTOR_IDS = ['informatica', 'saude', 'engenharia', 'facilities', 'software'];
/** Phase 1 UFs highlighted (5 largest) */
const PHASE1_UFS = ['SP', 'RJ', 'MG', 'PR', 'RS'];

export default function LicitacoesIndexPage() {
  const breadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: 'Licitações', url: 'https://smartlic.tech/blog/licitacoes' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="sector"
        title="Licitações por Setor e Estado"
        description="Diretório de licitações públicas por setor e estado brasileiro"
        url="https://smartlic.tech/blog/licitacoes"
        breadcrumbs={breadcrumbs}
      />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6">
              <Link href="/blog" className="hover:text-brand-blue">Blog</Link>
              <span>/</span>
              <span className="text-ink">Licitações</span>
            </nav>
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4 font-serif"
            >
              Licitações por Setor e Estado
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              Explore licitações públicas organizadas por setor de atuação e unidade federativa.
              Dados ao vivo de PNCP, Portal de Compras Públicas e ComprasGov.
            </p>
          </div>
        </div>

        {/* Sector Grid */}
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          <div className="space-y-12">
            {SECTORS.map((sector) => {
              const isPhase1 = PHASE1_SECTOR_IDS.includes(sector.id);
              return (
                <section key={sector.id}>
                  <div className="flex items-center gap-3 mb-4">
                    <h2 className="text-xl font-semibold text-ink">{sector.name}</h2>
                    {isPhase1 && (
                      <span className="text-xs font-medium px-2 py-0.5 rounded bg-green-100 text-green-700">
                        Dados ao vivo
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-ink-secondary mb-4">{sector.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {ALL_UFS.map((uf) => {
                      const isActive = isPhase1 && PHASE1_UFS.includes(uf);
                      return isActive ? (
                        <Link
                          key={uf}
                          href={`/blog/licitacoes/${sector.slug}/${uf.toLowerCase()}`}
                          className="inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium border border-brand-blue/20 bg-brand-blue-subtle/30 text-brand-blue hover:bg-brand-blue-subtle/50 transition-colors"
                        >
                          {uf}
                        </Link>
                      ) : (
                        <span
                          key={uf}
                          className="inline-flex items-center px-3 py-1.5 rounded-md text-sm border border-[var(--border)] text-ink-secondary"
                          title={`${sector.name} em ${UF_NAMES[uf]} — em breve`}
                        >
                          {uf}
                        </span>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>

          {/* CTA bottom */}
          <div className="mt-16 bg-gradient-to-br from-brand-navy to-brand-blue rounded-xl p-6 sm:p-8 text-white text-center">
            <h3 className="text-xl sm:text-2xl font-bold mb-3">
              Não encontrou seu setor ou estado?
            </h3>
            <p className="text-white/80 mb-6 max-w-xl mx-auto">
              O SmartLic monitora todos os 15 setores em todos os 27 estados do Brasil, com dados ao vivo.
              Teste grátis 14 dias — sem cartão de crédito.
            </p>
            <Link
              href="/signup?source=blog&utm_source=blog&utm_medium=programmatic&utm_content=licitacoes-index"
              className="inline-block bg-white text-brand-navy font-semibold px-6 py-3 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              Começar Teste Grátis
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
