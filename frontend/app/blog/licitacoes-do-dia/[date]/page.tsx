import { Metadata } from 'next';
import Link from 'next/link';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import { getAuthorBySlug, DEFAULT_AUTHOR_SLUG } from '@/lib/authors';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const revalidate = 3600; // 1h ISR

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DailySector {
  sector_name: string;
  sector_id: string;
  count: number;
  avg_value: number;
}

interface DailyUf {
  uf: string;
  count: number;
  total_value: number;
}

interface DailyModalidade {
  modalidade: string;
  count: number;
  pct: number;
}

interface DailyHighlight {
  titulo: string;
  orgao: string;
  valor: number | null;
  uf: string;
  setor: string;
}

interface DailyData {
  date: string;
  title: string;
  total_bids: number;
  total_value: number;
  avg_value: number;
  by_sector: DailySector[];
  by_uf: DailyUf[];
  by_modalidade: DailyModalidade[];
  highlights: DailyHighlight[];
  top_sector: string;
  top_uf: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

async function fetchDailyData(date: string): Promise<DailyData | null> {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;

  const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${BACKEND_URL}/v1/blog/daily/${date}`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
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

function getAdjacentDates(dateStr: string): { prev: string; next: string } {
  const d = new Date(dateStr + 'T12:00:00');
  const prev = new Date(d);
  prev.setDate(prev.getDate() - 1);
  const next = new Date(d);
  next.setDate(next.getDate() + 1);
  return {
    prev: prev.toISOString().slice(0, 10),
    next: next.toISOString().slice(0, 10),
  };
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

type Props = { params: Promise<{ date: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { date } = await params;
  const data = await fetchDailyData(date);

  // STORY-SEO-017 AC3: datas sem dados retornam 200 + noindex (nao 404).
  // Elimina os 42 URLs 404 reportados no GSC sweep 2026-04-24.
  if (!data) {
    const isValidDate = /^\d{4}-\d{2}-\d{2}$/.test(date);
    return {
      title: isValidDate ? `Sem licitacoes publicadas em ${date} | SmartLic` : 'Digest Diario',
      robots: { index: false, follow: false },
      alternates: isValidDate ? { canonical: buildCanonical(`/blog/licitacoes-do-dia/${date}`) } : undefined,
    };
  }

  const formattedDate = formatDateBR(date);
  const description = `Licitacoes do dia ${formattedDate}: ${data.total_bids} editais publicados no PNCP, totalizando ${formatBRL(data.total_value)}. Setor em destaque: ${data.top_sector}. Estado com mais publicacoes: ${data.top_uf}.`;

  return {
    title: data.title,
    description,
    authors: [{ name: getAuthorBySlug(DEFAULT_AUTHOR_SLUG)!.name }],
    alternates: { canonical: buildCanonical(`/blog/licitacoes-do-dia/${date}`) },
    openGraph: {
      title: data.title,
      description,
      type: 'article',
      url: buildCanonical(`/blog/licitacoes-do-dia/${date}`),
      locale: 'pt_BR',
      publishedTime: date,
      images: [{
        url: `${SITE_URL}/api/og?type=weekly&bids=${data.total_bids}&sector=${encodeURIComponent(data.top_sector)}`,
        width: 1200,
        height: 630,
        alt: data.title,
      }],
    },
  };
}

// ---------------------------------------------------------------------------
// JSON-LD
// ---------------------------------------------------------------------------

function buildJsonLd(data: DailyData) {
  const url = buildCanonical(`/blog/licitacoes-do-dia/${data.date}`);
  const author = getAuthorBySlug(DEFAULT_AUTHOR_SLUG)!;

  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'NewsArticle',
        headline: data.title,
        description: `Resumo diario de licitacoes publicas: ${data.date}.`,
        url,
        datePublished: data.date,
        dateModified: data.updated_at,
        publisher: { '@type': 'Organization', name: 'SmartLic', url: SITE_URL },
        author: {
          '@type': 'Person',
          name: author.name,
          jobTitle: author.role,
          url: buildCanonical(`/blog/author/${DEFAULT_AUTHOR_SLUG}`),
        },
        isAccessibleForFree: true,
      },
      {
        '@type': 'Dataset',
        name: data.title,
        description: `Editais publicados no PNCP em ${data.date}.`,
        url,
        temporalCoverage: `${data.date}/${data.date}`,
        measurementTechnique: 'Agregacao automatica via API PNCP',
        creator: { '@type': 'Organization', name: 'SmartLic', url: SITE_URL },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
          { '@type': 'ListItem', position: 2, name: 'Blog', item: `${SITE_URL}/blog` },
          { '@type': 'ListItem', position: 3, name: 'Licitacoes do Dia', item: `${SITE_URL}/blog/licitacoes-do-dia` },
          { '@type': 'ListItem', position: 4, name: data.date, item: url },
        ],
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function generateStaticParams() {
  return []; // SSR on-demand
}

export default async function DailyDigestDetailPage({ params }: Props) {
  const { date } = await params;
  const data = await fetchDailyData(date);

  // STORY-SEO-017 AC3: datas sem dados renderizam fallback graceful (200 + noindex
  // via generateMetadata). Antes era notFound() -> 404 -> 42 URLs penalizados no GSC.
  if (!data) {
    const isValidDate = /^\d{4}-\d{2}-\d{2}$/.test(date);
    const formattedDate = isValidDate ? formatDateBR(date) : date;
    return (
      <div className="min-h-screen flex flex-col bg-canvas">
        <LandingNavbar />
        <main className="flex-1">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 text-center">
            <h1 className="text-2xl sm:text-3xl font-bold text-ink mb-3">
              {isValidDate ? `Sem licitacoes publicadas em ${formattedDate}` : 'Data invalida'}
            </h1>
            <p className="text-ink-secondary mb-8">
              {isValidDate
                ? 'Nao encontramos licitacoes publicadas no PNCP nesta data. Pode ser fim de semana, feriado ou simplesmente um dia de baixo volume.'
                : 'Esta URL nao corresponde a uma data valida (formato esperado: YYYY-MM-DD).'}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/blog/licitacoes-do-dia"
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-brand-blue text-white font-semibold hover:bg-brand-blue/90 transition-colors"
              >
                Ver outros dias
              </Link>
              <Link
                href="/buscar"
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg border border-[var(--border)] text-ink font-semibold hover:bg-surface-1 transition-colors"
              >
                Buscar editais
              </Link>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const jsonLd = buildJsonLd(data);
  const { prev, next } = getAdjacentDates(date);
  const isToday = date === new Date().toISOString().slice(0, 10);

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <div className="min-h-screen flex flex-col bg-canvas">
        <LandingNavbar />

        <main className="flex-1">
          {/* Hero */}
          <div className="bg-surface-1 border-b border-[var(--border)]">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
              <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6 flex-wrap">
                <Link href="/" className="hover:text-brand-blue transition-colors">Home</Link>
                <span>/</span>
                <Link href="/blog" className="hover:text-brand-blue transition-colors">Blog</Link>
                <span>/</span>
                <Link href="/blog/licitacoes-do-dia" className="hover:text-brand-blue transition-colors">Licitacoes do Dia</Link>
                <span>/</span>
                <span className="text-ink">{date}</span>
              </nav>

              <div className="inline-flex items-center gap-2 bg-brand-blue/10 text-brand-blue text-xs font-semibold px-3 py-1 rounded-full mb-4">
                {isToday && <span>HOJE</span>}
                <span>{formatDateBR(date)}</span>
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
            </div>
          </div>

          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
            {/* Key metrics */}
            <section>
              <h2 className="text-lg font-semibold text-ink mb-4">Resumo do Dia</h2>
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
                  <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">Valor Medio</p>
                  <p className="text-2xl font-bold text-ink">{formatBRL(data.avg_value)}</p>
                </div>
              </div>
            </section>

            {/* Highlights */}
            {data.highlights.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold text-ink mb-4">Destaques do Dia</h2>
                <div className="space-y-3">
                  {data.highlights.map((h, i) => (
                    <div key={i} className="p-4 rounded-lg border border-[var(--border)]">
                      <p className="text-sm font-medium text-ink mb-1">{h.titulo}</p>
                      <div className="flex flex-wrap gap-3 text-xs text-ink-secondary">
                        <span>{h.orgao}</span>
                        {h.valor && <span className="font-semibold text-ink">{formatBRL(h.valor)}</span>}
                        <span>{h.uf}</span>
                        <span className="bg-surface-2 px-2 py-0.5 rounded">{h.setor}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

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
                        <th className="text-right py-2 pl-4 font-medium">Valor Medio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.by_sector.map((s) => (
                        <tr key={s.sector_id} className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors">
                          <td className="py-3 pr-4">
                            <Link href={`/licitacoes/${s.sector_id.replace(/_/g, '-')}`} className="text-brand-blue hover:underline font-medium">
                              {s.sector_name}
                            </Link>
                          </td>
                          <td className="py-3 px-4 text-right font-mono">{s.count.toLocaleString('pt-BR')}</td>
                          <td className="py-3 pl-4 text-right font-mono">{formatBRL(s.avg_value)}</td>
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
                <h2 className="text-lg font-semibold text-ink mb-4">Estados com Mais Publicacoes</h2>
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
                        <tr key={u.uf} className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors">
                          <td className="py-3 pr-4 font-semibold text-ink">{u.uf}</td>
                          <td className="py-3 px-4 text-right font-mono">{u.count.toLocaleString('pt-BR')}</td>
                          <td className="py-3 pl-4 text-right font-mono">{formatBRL(u.total_value)}</td>
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
                          {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: percentage width computed from m.pct at runtime */}
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
                Receba alertas automaticos quando novos editais do seu setor forem publicados.
                Analise de viabilidade com IA inclusa.
              </p>
              <Link
                href="/signup"
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-brand-blue text-white font-semibold hover:bg-brand-blue/90 transition-colors"
              >
                Comecar gratuitamente — 14 dias gratis
              </Link>
            </section>

            {/* Navigation */}
            <nav className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
              <Link
                href={`/blog/licitacoes-do-dia/${prev}`}
                className="text-sm text-ink-secondary hover:text-brand-blue transition-colors"
              >
                ← Dia anterior
              </Link>
              <Link
                href="/blog/licitacoes-do-dia"
                className="text-sm text-ink-secondary hover:text-brand-blue transition-colors"
              >
                Todos os dias
              </Link>
              <Link
                href={`/blog/licitacoes-do-dia/${next}`}
                className="text-sm text-ink-secondary hover:text-brand-blue transition-colors"
              >
                Proximo dia →
              </Link>
            </nav>
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}
