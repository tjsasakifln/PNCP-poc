import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { AnalysisViewTracker } from './AnalysisViewTracker';
import ShareButtons from '@/components/share/ShareButtons';
import SchemaMarkup from '@/components/blog/SchemaMarkup';

const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';
const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

export const revalidate = 3600; // ISR 1h

interface SharedAnalysis {
  hash: string;
  bid_id: string;
  bid_title: string;
  bid_orgao: string | null;
  bid_uf: string | null;
  bid_valor: number | null;
  bid_modalidade: string | null;
  viability_score: number;
  viability_level: string;
  viability_factors: {
    modalidade?: number;
    modalidade_label?: string;
    timeline?: number;
    timeline_label?: string;
    value_fit?: number;
    value_fit_label?: string;
    geography?: number;
    geography_label?: string;
  };
  view_count: number;
  created_at: string;
}

async function fetchAnalysis(hash: string): Promise<SharedAnalysis | null> {
  try {
    const res = await fetch(`${backendUrl}/v1/share/analise/${hash}`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function formatAnalysisDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ hash: string }>;
}): Promise<Metadata> {
  const { hash } = await params;
  const data = await fetchAnalysis(hash);
  if (!data) return { title: 'Análise não encontrada' };

  const levelLabel = data.viability_level === 'alta' ? 'ALTA' : data.viability_level === 'media' ? 'MÉDIA' : 'BAIXA';
  const setor = data.bid_modalidade || data.bid_uf || 'licitações';
  const cnpjLike = data.bid_orgao || '';
  const dataFmt = formatAnalysisDate(data.created_at);

  const title = `Análise de Viabilidade - ${setor}`;
  const description = cnpjLike
    ? `Score ${data.viability_score}/100 para ${cnpjLike} no setor ${setor}. Veja análise completa.`
    : `Score ${data.viability_score}/100 (${levelLabel}) no setor ${setor}. Veja análise completa.`;

  const ogParams = new URLSearchParams({
    type: 'analise',
    score: String(data.viability_score),
    level: data.viability_level,
    title: data.bid_title.slice(0, 60),
  });
  if (cnpjLike) ogParams.set('cnpj', cnpjLike);
  if (setor) ogParams.set('setor', setor);
  if (dataFmt) ogParams.set('data', dataFmt);

  const ogImageUrl = `${baseUrl}/api/og?${ogParams.toString()}`;
  const canonical = `${baseUrl}/analise/${hash}`;

  return {
    title,
    description,
    robots: { index: false, follow: true },
    alternates: { canonical },
    openGraph: {
      title: `Score ${data.viability_score}/100 — ${levelLabel} VIABILIDADE`,
      description,
      url: canonical,
      type: 'article',
      locale: 'pt_BR',
      images: [
        {
          url: ogImageUrl,
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [ogImageUrl],
    },
  };
}

export default async function AnalisePage({
  params,
}: {
  params: Promise<{ hash: string }>;
}) {
  const { hash } = await params;
  const data = await fetchAnalysis(hash);
  if (!data) notFound();

  const levelLabel = data.viability_level === 'alta' ? 'ALTA' : data.viability_level === 'media' ? 'MÉDIA' : 'BAIXA';
  const levelColor =
    data.viability_level === 'alta'
      ? 'text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700'
      : data.viability_level === 'media'
        ? 'text-yellow-700 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700'
        : 'text-gray-700 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600';

  const scoreColor =
    data.viability_level === 'alta' ? 'text-green-600 dark:text-green-400'
      : data.viability_level === 'media' ? 'text-yellow-600 dark:text-yellow-400'
        : 'text-gray-500';

  const factors = [
    { key: 'Modalidade', weight: '30%', score: data.viability_factors.modalidade, label: data.viability_factors.modalidade_label },
    { key: 'Prazo', weight: '25%', score: data.viability_factors.timeline, label: data.viability_factors.timeline_label },
    { key: 'Valor', weight: '25%', score: data.viability_factors.value_fit, label: data.viability_factors.value_fit_label },
    { key: 'Geografia', weight: '20%', score: data.viability_factors.geography, label: data.viability_factors.geography_label },
  ];

  const reviewSchema = {
    '@context': 'https://schema.org',
    '@type': 'Review',
    reviewRating: {
      '@type': 'Rating',
      ratingValue: data.viability_score.toString(),
      bestRating: '100',
      worstRating: '0',
    },
    itemReviewed: {
      '@type': 'GovernmentService',
      name: data.bid_title,
      provider: data.bid_orgao ? { '@type': 'GovernmentOrganization', name: data.bid_orgao } : undefined,
    },
    author: { '@type': 'Organization', name: 'SmartLic', url: baseUrl },
    reviewBody: `Análise de viabilidade com score ${data.viability_score}/100 (${levelLabel}).`,
  };

  const shareUrl = `${baseUrl}/analise/${hash}`;
  const setor = data.bid_modalidade || data.bid_uf || 'licitações';
  const shareTitle = `Análise de Viabilidade — Score ${data.viability_score}/100 (${levelLabel})`;
  const shareDescription = `Análise de viabilidade SmartLic para "${data.bid_title.slice(0, 80)}"${data.bid_orgao ? ` — ${data.bid_orgao}` : ''}.`;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(reviewSchema) }}
      />

      {/* SEO-PLAYBOOK P6: Article schema for shareable analysis */}
      <SchemaMarkup
        pageType="analise"
        title={shareTitle}
        description={shareDescription}
        url={shareUrl}
        datePublished={data.created_at}
        dateModified={data.created_at}
        sectorName={setor}
      />

      {/* SEO-PLAYBOOK P6: track analysis_viewed */}
      <AnalysisViewTracker hash={hash} viabilityScore={data.viability_score} bidUf={data.bid_uf} />

      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        {/* Score Hero */}
        <div className="text-center mb-10">
          <p className="text-sm text-ink-secondary mb-2">Análise de Viabilidade</p>
          <div className={`inline-flex items-center justify-center w-28 h-28 rounded-full border-4 ${levelColor} mb-4`}>
            <span className={`text-4xl font-bold font-data ${scoreColor}`}>
              {data.viability_score}
            </span>
          </div>
          <p className={`text-lg font-bold ${scoreColor}`}>{levelLabel} VIABILIDADE</p>
        </div>

        {/* Bid Info */}
        <div className="p-6 bg-surface border border-border rounded-card mb-8">
          <h1 className="text-lg font-semibold text-ink mb-4 leading-snug">
            {data.bid_title}
          </h1>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {data.bid_orgao && (
              <div>
                <span className="text-ink-muted">Órgão</span>
                <p className="text-ink font-medium">{data.bid_orgao}</p>
              </div>
            )}
            {data.bid_uf && (
              <div>
                <span className="text-ink-muted">UF</span>
                <p className="text-ink font-medium">{data.bid_uf}</p>
              </div>
            )}
            {data.bid_valor != null && data.bid_valor > 0 && (
              <div>
                <span className="text-ink-muted">Valor estimado</span>
                <p className="text-ink font-medium">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(data.bid_valor)}
                </p>
              </div>
            )}
            {data.bid_modalidade && (
              <div>
                <span className="text-ink-muted">Modalidade</span>
                <p className="text-ink font-medium">{data.bid_modalidade}</p>
              </div>
            )}
          </div>
        </div>

        {/* Factor Breakdown */}
        <div className="mb-10">
          <h2 className="text-base font-semibold text-ink mb-4">Breakdown dos 4 Fatores</h2>
          <div className="space-y-4">
            {factors.map((f) => (
              <div key={f.key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-ink">
                    {f.key} <span className="text-ink-muted font-normal">({f.weight})</span>
                  </span>
                  <span className="text-sm font-semibold text-ink">{f.score ?? '—'}/100</span>
                </div>
                <div className="w-full h-2 bg-surface-2 rounded-full overflow-hidden">
                  {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width is computed from viability factor score */}
                  <div
                    className={`h-full rounded-full transition-all ${
                      (f.score ?? 0) >= 70
                        ? 'bg-green-500'
                        : (f.score ?? 0) >= 40
                          ? 'bg-yellow-500'
                          : 'bg-gray-400'
                    }`}
                    style={{ width: `${f.score ?? 0}%` }}
                  />
                </div>
                {f.label && (
                  <p className="text-xs text-ink-secondary mt-1">{f.label}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA Watermark */}
        <div className="text-center p-8 bg-brand-blue-subtle border border-accent rounded-card">
          <p className="text-sm text-ink-secondary mb-1">
            Análise gerada pelo SmartLic
          </p>
          <p className="text-lg font-bold text-ink mb-4">
            14 dias grátis para analisar editais do seu setor
          </p>
          <Link
            href={`/signup?ref=share-${hash}`}
            className="inline-flex items-center px-6 py-3 bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold rounded-button transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Analisar editais para o meu setor →
          </Link>
        </div>

        {/* SEO-PLAYBOOK P6: Share buttons */}
        <div className="mt-8">
          <ShareButtons
            url={shareUrl}
            title={shareTitle}
            description={shareDescription}
            hashtags={['SmartLic', 'Licitacoes', 'B2G']}
            trackingContext={{ source: 'analise', hash, viability_score: data.viability_score }}
          />
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-ink-muted mt-6">
          Esta análise expira em 30 dias. Visualizações: {data.view_count + 1}.
        </p>
      </main>
    </>
  );
}
