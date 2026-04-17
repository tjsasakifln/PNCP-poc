import { Metadata } from 'next';
import Link from 'next/link';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import { LeadCapture } from '@/components/LeadCapture';

export const revalidate = 3600; // 1h ISR

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

interface DailyDigestSummary {
  date: string;
  title: string;
  total_bids: number;
  total_value: number;
  top_sector: string;
  top_uf: string;
}

async function fetchLatestDigest(): Promise<DailyDigestSummary | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/v1/blog/daily/latest`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
}

function formatDateBR(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'America/Sao_Paulo',
  });
}

export const metadata: Metadata = {
  title: 'Licitacoes do Dia — Resumo Diario de Editais Publicos',
  description: 'Acompanhe diariamente os editais publicados no PNCP. Totais por setor, estado e modalidade. Dados atualizados automaticamente.',
  alternates: { canonical: buildCanonical('/blog/licitacoes-do-dia') },
  openGraph: {
    title: 'Licitacoes do Dia | SmartLic',
    description: 'Resumo diario de editais publicos do PNCP.',
    url: buildCanonical('/blog/licitacoes-do-dia'),
    type: 'website',
    locale: 'pt_BR',
  },
};

export default async function LicitacoesDoDiaHubPage() {
  const latest = await fetchLatestDigest();

  // Generate last 30 days
  const days: string[] = [];
  for (let i = 0; i < 30; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().slice(0, 10));
  }

  const collectionSchema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Licitacoes do Dia',
    description: 'Arquivo de resumos diarios de editais publicos do PNCP',
    url: buildCanonical('/blog/licitacoes-do-dia'),
    publisher: { '@type': 'Organization', name: 'SmartLic', url: SITE_URL },
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Blog', item: `${SITE_URL}/blog` },
      { '@type': 'ListItem', position: 3, name: 'Licitacoes do Dia', item: buildCanonical('/blog/licitacoes-do-dia') },
    ],
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6">
              <Link href="/" className="hover:text-brand-blue">Home</Link>
              <span>/</span>
              <Link href="/blog" className="hover:text-brand-blue">Blog</Link>
              <span>/</span>
              <span className="text-ink">Licitacoes do Dia</span>
            </nav>
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4 font-serif"
            >
              Licitacoes do Dia
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              Resumo diario de editais publicados no PNCP. Totais por setor, estado e modalidade,
              atualizados automaticamente.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Today's highlight */}
          {latest && (
            <Link
              href={`/blog/licitacoes-do-dia/${latest.date}`}
              className="block mb-10 p-6 rounded-2xl border-2 border-brand-blue/20 bg-brand-blue/5 hover:border-brand-blue/40 transition-colors"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="bg-brand-blue text-white text-xs font-semibold px-3 py-1 rounded-full">HOJE</span>
                <span className="text-sm text-ink-secondary">{formatDateBR(latest.date)}</span>
              </div>
              <h2 className="text-xl font-bold text-ink mb-2">{latest.title}</h2>
              <div className="flex flex-wrap gap-4 text-sm text-ink-secondary">
                <span>{latest.total_bids.toLocaleString('pt-BR')} editais</span>
                <span>{formatBRL(latest.total_value)}</span>
                <span>Destaque: {latest.top_sector}</span>
              </div>
            </Link>
          )}

          {/* Archive */}
          <h2 className="text-xl font-semibold text-ink mb-6">Ultimos 30 dias</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {days.map((date, i) => (
              <Link
                key={date}
                href={`/blog/licitacoes-do-dia/${date}`}
                className="p-3 rounded-lg border border-[var(--border)] hover:border-brand-blue/30 hover:bg-surface-1 transition-colors text-center"
              >
                <p className="text-sm font-medium text-ink">
                  {new Date(date + 'T12:00:00').toLocaleDateString('pt-BR', {
                    day: '2-digit',
                    month: 'short',
                    timeZone: 'America/Sao_Paulo',
                  })}
                </p>
                <p className="text-xs text-ink-secondary">
                  {new Date(date + 'T12:00:00').toLocaleDateString('pt-BR', {
                    weekday: 'short',
                    timeZone: 'America/Sao_Paulo',
                  })}
                </p>
                {i === 0 && (
                  <span className="inline-block mt-1 bg-brand-blue/10 text-brand-blue text-[10px] font-semibold px-2 py-0.5 rounded-full">
                    HOJE
                  </span>
                )}
              </Link>
            ))}
          </div>

          {/* CTA */}
          <div className="mt-12">
            <LeadCapture
              source="licitacoes-do-dia"
              heading="Receba o resumo diario no seu email"
              description="Alertas automaticos de novos editais do seu setor, toda manha."
            />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
