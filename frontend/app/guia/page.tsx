import type { Metadata } from 'next';
import Link from 'next/link';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import { PILLARS } from '@/lib/pillars';

export const metadata: Metadata = {
  title: 'Guias Completos de Licitações Públicas | SmartLic',
  description:
    'Guias aprofundados sobre licitações públicas no Brasil: Lei 14.133, modalidades, PNCP, habilitação, erros comuns e estratégias de participação para empresas B2G.',
  alternates: { canonical: 'https://smartlic.tech/guia' },
  robots: { index: true, follow: true },
};

export default function GuiaHub() {
  const itemListSchema = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'Guias Completos SmartLic',
    itemListElement: PILLARS.map((pillar, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: `https://smartlic.tech/guia/${pillar.slug}`,
      name: pillar.shortTitle,
    })),
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />
      <main className="flex-1">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(itemListSchema) }}
        />
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <header className="mb-12">
            <span className="inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wider text-brand-blue bg-brand-blue-subtle rounded-full mb-4">
              Guias Completos
            </span>
            <h1 className="text-4xl lg:text-5xl font-bold text-ink font-serif tracking-tight mb-4">
              Domine licitações públicas em 2026
            </h1>
            <p className="text-lg text-ink-secondary leading-relaxed max-w-3xl">
              Conteúdo denso, aprofundado, orientado à prática. Cada guia reúne, em formato único, o que sua empresa B2G precisa saber sobre os temas centrais do mercado de compras públicas brasileiro — com fontes oficiais, links para conteúdo complementar e insights operacionais validados em casos reais.
            </p>
          </header>

          <ul className="grid gap-6 md:grid-cols-1 lg:grid-cols-1" data-testid="guias-list">
            {PILLARS.map((pillar) => (
              <li key={pillar.slug}>
                <Link
                  href={`/guia/${pillar.slug}`}
                  className="block p-6 lg:p-8 rounded-xl border border-[var(--border)] bg-surface-1 hover:border-brand-blue/40 hover:shadow-md transition-all group"
                >
                  <h2 className="text-xl lg:text-2xl font-bold text-ink group-hover:text-brand-blue transition-colors font-serif mb-3">
                    {pillar.title}
                  </h2>
                  <p className="text-ink-secondary leading-relaxed mb-4">{pillar.description}</p>
                  <div className="flex items-center gap-4 text-sm text-ink-secondary">
                    <span>{pillar.wordCount.toLocaleString('pt-BR')} palavras</span>
                    <span aria-hidden="true">&middot;</span>
                    <span>{pillar.spokes.length} artigos relacionados</span>
                    <span aria-hidden="true">&middot;</span>
                    <span className="text-brand-blue font-medium group-hover:underline">
                      Ler guia &rarr;
                    </span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </main>
      <Footer />
    </div>
  );
}
