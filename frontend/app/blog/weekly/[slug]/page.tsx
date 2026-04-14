import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import { getAuthorBySlug, DEFAULT_AUTHOR_SLUG } from '@/lib/authors';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const revalidate = 3600;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WeeklySector {
  sector_name: string;
  sector_id: string;
  count: number;
  avg_value: number;
  trend: string;
}

interface WeeklyUf {
  uf: string;
  count: number;
  total_value: number;
}

interface WeeklyModalidade {
  modalidade: string;
  count: number;
  pct: number;
}

interface WeeklyData {
  year: number;
  week: number;
  slug: string;
  title: string;
  period_start: string;
  period_end: string;
  total_bids: number;
  total_value: number;
  avg_value: number;
  by_sector: WeeklySector[];
  by_uf: WeeklyUf[];
  by_modalidade: WeeklyModalidade[];
  top_sector: string;
  top_uf: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

async function fetchWeeklyData(slug: string): Promise<WeeklyData | null> {
  const match = slug.match(/^(\d{4})-w(\d{1,2})$/i);
  if (!match) return null;
  const [, year, week] = match;

  const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(
      `${BACKEND_URL}/v1/blog/weekly/${year}/${week}`,
      { next: { revalidate: 3600 }, signal: AbortSignal.timeout(10000) }
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const data = await fetchWeeklyData(slug);

  if (!data) {
    return {
      title: 'Digest Semanal',
      robots: { index: false },
    };
  }

  const description = `Digest da semana ${data.week}/${data.year}: ${data.total_bids} editais publicados no PNCP, totalizando ${formatBRL(data.total_value)}. Setor em destaque: ${data.top_sector}. Estado com mais publicações: ${data.top_uf}.`;

  return {
    title: `${data.title}`,
    description,
    authors: [{ name: getAuthorBySlug(DEFAULT_AUTHOR_SLUG)!.name }],
    alternates: { canonical: buildCanonical(`/blog/weekly/${slug}`) },
    openGraph: {
      title: data.title,
      description,
      type: 'article',
      url: buildCanonical(`/blog/weekly/${slug}`),
      locale: 'pt_BR',
      publishedTime: data.period_start,
      images: [{
        url: `${SITE_URL}/api/og?type=weekly&week=${data.week}&year=${data.year}&bids=${data.total_bids}&sector=${encodeURIComponent(data.top_sector)}`,
        width: 1200,
        height: 630,
        alt: data.title,
      }],
    },
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPeriod(start: string, end: string): string {
  const fmt = new Intl.DateTimeFormat('pt-BR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'America/Sao_Paulo',
  });
  const startDate = new Date(start + 'T12:00:00');
  const endDate = new Date(end + 'T12:00:00');
  return `${fmt.format(startDate)} – ${fmt.format(endDate)}`;
}

function TrendArrow({ trend }: { trend: string }) {
  if (trend === 'up') return <span className="text-emerald-600 font-bold">↑</span>;
  if (trend === 'down') return <span className="text-red-500 font-bold">↓</span>;
  return <span className="text-ink-secondary">→</span>;
}

// ---------------------------------------------------------------------------
// JSON-LD
// ---------------------------------------------------------------------------

function buildJsonLd(data: WeeklyData, slug: string) {
  const url = buildCanonical(`/blog/weekly/${slug}`);
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'NewsArticle',
        headline: data.title,
        description: `Digest semanal de licitações públicas: semana ${data.week} de ${data.year}.`,
        url,
        datePublished: data.period_start,
        dateModified: data.updated_at,
        publisher: {
          '@type': 'Organization',
          name: 'SmartLic',
          url: SITE_URL,
        },
        author: {
          '@type': 'Person',
          name: getAuthorBySlug(DEFAULT_AUTHOR_SLUG)!.name,
          jobTitle: getAuthorBySlug(DEFAULT_AUTHOR_SLUG)!.role,
          url: buildCanonical(`/blog/author/${DEFAULT_AUTHOR_SLUG}`),
          sameAs: getAuthorBySlug(DEFAULT_AUTHOR_SLUG)!.sameAs,
        },
        isAccessibleForFree: true,
        speakable: {
          '@type': 'SpeakableSpecification',
          cssSelector: ['h1', '.weekly-summary'],
        },
      },
      {
        '@type': 'Dataset',
        name: data.title,
        description: `Dados de licitações públicas publicadas no PNCP entre ${data.period_start} e ${data.period_end}.`,
        url,
        temporalCoverage: `${data.period_start}/${data.period_end}`,
        measurementTechnique: 'Agregação automática via API PNCP',
        creator: {
          '@type': 'Organization',
          name: 'SmartLic',
          url: SITE_URL,
        },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
          { '@type': 'ListItem', position: 2, name: 'Blog', item: `${SITE_URL}/blog` },
          { '@type': 'ListItem', position: 3, name: 'Digest Semanal', item: `${SITE_URL}/blog/weekly` },
          { '@type': 'ListItem', position: 4, name: `Semana ${data.week}`, item: url },
        ],
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default async function WeeklyDigestPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const data = await fetchWeeklyData(slug);

  if (!data) {
    notFound();
  }

  const canonicalUrl = buildCanonical(`/blog/weekly/${slug}`);
  const jsonLd = buildJsonLd(data, slug);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="min-h-screen flex flex-col bg-canvas">
        <LandingNavbar />

        <main className="flex-1">
          {/* Hero */}
          <div className="bg-surface-1 border-b border-[var(--border)]">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
              {/* Breadcrumbs */}
              <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6 flex-wrap">
                <Link href="/" className="hover:text-brand-blue transition-colors">Home</Link>
                <span>/</span>
                <Link href="/blog" className="hover:text-brand-blue transition-colors">Blog</Link>
                <span>/</span>
                <Link href="/blog/weekly" className="hover:text-brand-blue transition-colors">Digest Semanal</Link>
                <span>/</span>
                <span className="text-ink">Semana {data.week}</span>
              </nav>

              {/* Period badge */}
              <div className="inline-flex items-center gap-2 bg-brand-blue/10 text-brand-blue text-xs font-semibold px-3 py-1 rounded-full mb-4">
                <span>Semana {data.week} / {data.year}</span>
                <span className="opacity-50">·</span>
                <span>{formatPeriod(data.period_start, data.period_end)}</span>
              </div>

              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-ink tracking-tight mb-3">
                {data.title}
              </h1>
              <p className="text-sm text-ink-secondary">
                Atualizado em{' '}
                {new Date(data.updated_at).toLocaleDateString('pt-BR', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric',
                  timeZone: 'America/Sao_Paulo',
                })}
              </p>
              <p className="text-sm text-ink-secondary mt-1">
                Por{' '}
                <Link href={`/blog/author/${DEFAULT_AUTHOR_SLUG}`} className="font-medium text-ink hover:text-brand-blue transition-colors">
                  {getAuthorBySlug(DEFAULT_AUTHOR_SLUG)!.name}
                </Link>{' '}
                · Equipe SmartLic
              </p>
            </div>
          </div>

          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
            {/* Key metrics */}
            <section className="weekly-summary">
              <h2 className="text-lg font-semibold text-ink mb-4">Resumo da Semana</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-surface-1 border border-[var(--border)] rounded-xl p-5">
                  <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">Total de Editais</p>
                  <p className="text-3xl font-bold text-ink">{data.total_bids.toLocaleString('pt-BR')}</p>
                </div>
                <div className="bg-surface-1 border border-[var(--border)] rounded-xl p-5">
                  <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">Volume Total</p>
                  <p className="text-2xl font-bold text-ink">{formatBRL(data.total_value)}</p>
                </div>
                <div className="bg-surface-1 border border-[var(--border)] rounded-xl p-5">
                  <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">Valor Médio</p>
                  <p className="text-2xl font-bold text-ink">{formatBRL(data.avg_value)}</p>
                </div>
              </div>
            </section>

            {/* Top sectors */}
            {data.by_sector.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold text-ink mb-4">Setores em Destaque</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-ink-secondary">
                        <th className="text-left py-2 pr-4 font-medium">Setor</th>
                        <th className="text-right py-2 px-4 font-medium">Editais</th>
                        <th className="text-right py-2 px-4 font-medium">Valor Médio</th>
                        <th className="text-center py-2 pl-4 font-medium">Tendência</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.by_sector.map((s) => (
                        <tr
                          key={s.sector_id}
                          className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors"
                        >
                          <td className="py-3 pr-4">
                            <Link
                              href={`/licitacoes/${s.sector_id}`}
                              className="text-brand-blue hover:underline font-medium"
                            >
                              {s.sector_name}
                            </Link>
                          </td>
                          <td className="py-3 px-4 text-right font-mono">
                            {s.count.toLocaleString('pt-BR')}
                          </td>
                          <td className="py-3 px-4 text-right font-mono">
                            {formatBRL(s.avg_value)}
                          </td>
                          <td className="py-3 pl-4 text-center">
                            <TrendArrow trend={s.trend} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* Top UFs */}
            {data.by_uf.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold text-ink mb-4">Estados com Mais Publicações</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-ink-secondary">
                        <th className="text-left py-2 pr-4 font-medium">Estado</th>
                        <th className="text-right py-2 px-4 font-medium">Editais</th>
                        <th className="text-right py-2 pl-4 font-medium">Volume Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.by_uf.map((u) => (
                        <tr
                          key={u.uf}
                          className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors"
                        >
                          <td className="py-3 pr-4 font-semibold text-ink">{u.uf}</td>
                          <td className="py-3 px-4 text-right font-mono">
                            {u.count.toLocaleString('pt-BR')}
                          </td>
                          <td className="py-3 pl-4 text-right font-mono">
                            {formatBRL(u.total_value)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* Modalidade breakdown */}
            {data.by_modalidade.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold text-ink mb-4">Por Modalidade</h2>
                <ul className="space-y-2">
                  {data.by_modalidade.map((m) => (
                    <li key={m.modalidade} className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-ink">{m.modalidade}</span>
                          <span className="text-sm text-ink-secondary font-mono">
                            {m.count.toLocaleString('pt-BR')} ({m.pct}%)
                          </span>
                        </div>
                        <div className="w-full bg-surface-2 rounded-full h-1.5">
                          <div
                            className="bg-brand-blue h-1.5 rounded-full"
                            style={{ width: `${Math.min(m.pct, 100)}%` }}
                          />
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* CTA */}
            <section className="bg-brand-blue/5 border border-brand-blue/20 rounded-2xl p-8 text-center">
              <h2 className="text-xl font-bold text-ink mb-2">
                Monitore editais do seu setor em tempo real
              </h2>
              <p className="text-ink-secondary mb-6 max-w-lg mx-auto">
                Receba alertas automáticos quando novos editais do seu setor forem publicados.
                Análise de viabilidade com IA inclusa.
              </p>
              <Link
                href="/signup"
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-brand-blue text-white font-semibold hover:bg-brand-blue/90 transition-colors"
              >
                Começar gratuitamente — 14 dias grátis
              </Link>
            </section>

            {/* Navigation */}
            <nav className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
              <Link
                href="/blog/weekly"
                className="text-sm text-ink-secondary hover:text-brand-blue transition-colors"
              >
                ← Todos os digests
              </Link>
              <Link
                href="/blog"
                className="text-sm text-ink-secondary hover:text-brand-blue transition-colors"
              >
                Blog →
              </Link>
            </nav>
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}
