import { Metadata } from 'next';
import Link from 'next/link';
import { SECTORS } from '@/lib/sectors';
import { ALL_UFS, UF_NAMES } from '@/lib/programmatic';
import { buildCanonical } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const metadata: Metadata = {
  title: 'Alertas de Licitações Públicas — Todos os Setores e Estados | SmartLic',
  description: 'Acompanhe licitações em tempo real por setor e estado. Feeds RSS disponíveis. Dados do PNCP atualizados a cada hora.',
  alternates: { canonical: buildCanonical('/alertas-publicos') },
  openGraph: {
    title: 'Alertas de Licitações Públicas | SmartLic',
    description: 'Licitações em tempo real por setor e estado — dados do PNCP',
    type: 'website',
    locale: 'pt_BR',
  },
};

const TOP_UFS = ['SP', 'RJ', 'MG', 'DF', 'PR', 'BA', 'RS', 'SC', 'GO', 'PE'];

export default function AlertasIndexPage() {
  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        <section className="bg-gradient-to-br from-brand-navy to-brand-blue text-white py-16 px-4">
          <div className="max-w-5xl mx-auto text-center">
            <h1 className="text-3xl sm:text-4xl font-bold mb-4">
              Alertas de Licitações Públicas
            </h1>
            <p className="text-white/80 text-lg max-w-2xl mx-auto">
              Acompanhe as licitações mais recentes por setor e estado.
              Dados atualizados a cada hora do PNCP. Feed RSS disponível.
            </p>
          </div>
        </section>

        <section className="max-w-5xl mx-auto py-12 px-4">
          <div className="space-y-10">
            {SECTORS.map((sector) => (
              <div key={sector.slug}>
                <h2 className="text-xl font-bold text-ink mb-4">{sector.name}</h2>
                <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-2">
                  {TOP_UFS.map((uf) => (
                    <Link
                      key={uf}
                      href={`/alertas-publicos/${sector.slug}/${uf.toLowerCase()}`}
                      className="p-2 text-center text-sm rounded-lg border border-border hover:border-brand-blue hover:bg-brand-blue/5 transition-colors"
                    >
                      {uf}
                    </Link>
                  ))}
                  <details className="col-span-full">
                    <summary className="text-sm text-brand-blue cursor-pointer hover:underline">
                      Todos os estados →
                    </summary>
                    <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-2 mt-2">
                      {ALL_UFS.filter((u) => !TOP_UFS.includes(u)).map((uf) => (
                        <Link
                          key={uf}
                          href={`/alertas-publicos/${sector.slug}/${uf.toLowerCase()}`}
                          className="p-2 text-center text-sm rounded-lg border border-border hover:border-brand-blue hover:bg-brand-blue/5 transition-colors"
                        >
                          {uf}
                        </Link>
                      ))}
                    </div>
                  </details>
                </div>
              </div>
            ))}
          </div>
        </section>

        <Footer />
      </main>
    </>
  );
}
