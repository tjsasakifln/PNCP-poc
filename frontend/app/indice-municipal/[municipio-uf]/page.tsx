/**
 * STORY-435 AC2: Página de município — /indice-municipal/[municipio-uf]
 *
 * SSG com revalidate 1h. Schema.org: Article.
 * Slug format: "sao-paulo-sp" (nome-slug + "-" + uf 2 chars)
 */

import { Metadata } from 'next';
import Link from 'next/link';

interface PageProps {
  params: Promise<{ 'municipio-uf': string }>;
  searchParams: Promise<{ periodo?: string }>;
}

/** Extrai UF das últimas 2 chars do slug (ex: "sao-paulo-sp" -> "SP") */
function extractUF(slug: string): string {
  return slug.slice(-2).toUpperCase();
}

/** Remove o sufixo "-uf" do slug (ex: "sao-paulo-sp" -> "sao-paulo") */
function extractMunicipioSlug(slug: string): string {
  return slug.slice(0, -3);
}

/** Deslugifica o nome do município (ex: "sao-paulo" -> "Sao Paulo") */
function deslugify(slug: string): string {
  return slug
    .split('-')
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(' ');
}

async function fetchMunicipio(slug: string, periodo: string) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(
      `${backendUrl}/v1/indice-municipal/${slug}?periodo=${periodo}`,
      { next: { revalidate: 3600 }, signal: AbortSignal.timeout(10000) }
    );
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({ params, searchParams }: PageProps): Promise<Metadata> {
  const { 'municipio-uf': slug } = await params;
  const { periodo = '2026-Q1' } = await searchParams;

  const uf = extractUF(slug);
  const municipioSlug = extractMunicipioSlug(slug);
  const municipioTitulo = deslugify(municipioSlug);

  const data = await fetchMunicipio(slug, periodo);
  const score = data?.score_total != null ? Number(data.score_total) : null;
  const scoreText = score != null ? ` Score ${score.toFixed(1)} de 100.` : '';

  const title = `${municipioTitulo} (${uf}) — Índice de Transparência Municipal`;
  const description = `Transparência em compras públicas de ${municipioTitulo}/${uf}.${scoreText} Dados do PNCP: volume, eficiência e diversidade de mercado.`;

  return {
    title,
    description,
    alternates: { canonical: `https://smartlic.tech/indice-municipal/${slug}` },
    openGraph: {
      title,
      description,
      url: `https://smartlic.tech/indice-municipal/${slug}`,
      type: 'article',
      locale: 'pt_BR',
      images: score != null ? [
        {
          url: `https://smartlic.tech/api/og/indice-municipal?cidade=${encodeURIComponent(municipioTitulo)}&uf=${uf}&score=${Math.round(score)}`,
          width: 1200,
          height: 630,
          alt: `Índice de Transparência Municipal — ${municipioTitulo}/${uf}: ${score.toFixed(1)} de 100`,
        },
      ] : [],
    },
    robots: { index: true },
  };
}

export default async function MunicipioPage({ params, searchParams }: PageProps) {
  const { 'municipio-uf': slug } = await params;
  const { periodo = '2026-Q1' } = await searchParams;

  const uf = extractUF(slug);
  const municipioSlug = extractMunicipioSlug(slug);
  const municipioTitulo = deslugify(municipioSlug);

  const data = await fetchMunicipio(slug, periodo);

  const score = data?.score_total != null ? Number(data.score_total) : null;
  const scoreColor =
    score == null
      ? 'text-gray-500'
      : score >= 60
        ? 'text-green-600'
        : score >= 40
          ? 'text-yellow-600'
          : 'text-red-600';

  const dimensoes = data
    ? [
        {
          nome: 'Transparência Digital',
          score: Number(data.score_transparencia_digital || 0),
          desc: 'Uso de pregão eletrônico',
        },
        {
          nome: 'Eficiência Temporal',
          score: Number(data.score_eficiencia_temporal || 0),
          desc: 'Tempo publicação → abertura',
        },
        {
          nome: 'Diversidade de Mercado',
          score: Number(data.score_diversidade_mercado || 0),
          desc: 'Fornecedores únicos',
        },
        {
          nome: 'Volume de Publicação',
          score: Number(data.score_volume_publicacao || 0),
          desc: 'Total de editais publicados',
        },
        {
          nome: 'Consistência',
          score: Number(data.score_consistencia || 0),
          desc: 'Publicações regulares por mês',
        },
      ]
    : [];

  const articleSchema =
    data && score != null
      ? {
          '@context': 'https://schema.org',
          '@type': 'Article',
          headline: `${municipioTitulo} (${uf}) — Índice de Transparência em Compras Públicas`,
          datePublished: data.calculado_em,
          dateModified: data.calculado_em,
          author: {
            '@type': 'Organization',
            name: 'SmartLic',
            url: 'https://smartlic.tech',
          },
          description: `Score ${score.toFixed(1)} pontos. Ranking ${data.ranking_nacional}º entre municípios brasileiros.`,
        }
      : null;

  return (
    <>
      {articleSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
        />
      )}

      <main className="max-w-3xl mx-auto px-4 py-10">
        <nav className="text-sm text-gray-500 mb-6">
          <Link href="/indice-municipal" className="hover:underline">
            Índice Municipal
          </Link>
          {' / '}
          <span>
            {municipioTitulo} ({uf})
          </span>
        </nav>

        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          {municipioTitulo} ({uf})
        </h1>
        <p className="text-gray-500 text-sm mb-6">
          Período: {periodo} · Fonte: PNCP via SmartLic
        </p>

        {!data && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-800 font-medium">Dados não disponíveis</p>
            <p className="text-yellow-700 text-sm mt-1">
              {municipioTitulo} não possui editais suficientes no PNCP para este período (mínimo
              10).
            </p>
            <Link
              href="/indice-municipal"
              className="text-blue-600 hover:underline mt-3 block text-sm"
            >
              ← Ver ranking completo
            </Link>
          </div>
        )}

        {data && (
          <>
            {/* Score principal */}
            <div className="bg-white border rounded-xl p-6 mb-6 flex items-center gap-6 shadow-sm">
              <div className="text-center">
                <div className={`text-5xl font-bold ${scoreColor}`}>
                  {score?.toFixed(1)}
                </div>
                <div className="text-xs text-gray-400 mt-1">de 100 pontos</div>
              </div>
              <div className="flex-1">
                {data.ranking_nacional && (
                  <p className="text-sm text-gray-700">
                    <span className="font-medium">Ranking nacional:</span>{' '}
                    {data.ranking_nacional}º lugar
                  </p>
                )}
                {data.ranking_uf && (
                  <p className="text-sm text-gray-700">
                    <span className="font-medium">Ranking em {uf}:</span>{' '}
                    {data.ranking_uf}º lugar
                  </p>
                )}
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Total de editais:</span>{' '}
                  {new Intl.NumberFormat('pt-BR').format(data.total_editais)}
                </p>
              </div>
            </div>

            {/* 5 dimensões */}
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Dimensões do índice</h2>
            <div className="space-y-3 mb-8">
              {dimensoes.map((dim) => (
                <div key={dim.nome} className="bg-white border rounded-lg p-4 shadow-sm">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-gray-700">{dim.nome}</span>
                    <span
                      className={`text-sm font-bold ${
                        dim.score >= 14
                          ? 'text-green-600'
                          : dim.score >= 8
                            ? 'text-yellow-600'
                            : 'text-red-600'
                      }`}
                    >
                      {dim.score.toFixed(1)}/20
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        dim.score >= 14
                          ? 'bg-green-500'
                          : dim.score >= 8
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                      }`}
                      style={{ width: `${(dim.score / 20) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{dim.desc}</p>
                </div>
              ))}
            </div>

            {/* CTA */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-center">
              <h3 className="text-base font-semibold text-blue-900 mb-1">
                Acompanhe as licitações de {municipioTitulo}
              </h3>
              <p className="text-sm text-blue-700 mb-3">
                Receba alertas de novos editais e analise oportunidades em tempo real.
              </p>
              <Link
                href="/cadastro"
                className="inline-block bg-blue-600 text-white text-sm font-medium px-5 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Trial 14 dias grátis →
              </Link>
            </div>
          </>
        )}

        <div className="mt-8 text-xs text-gray-400 border-t pt-4">
          Dados derivados do PNCP (Portal Nacional de Contratações Públicas). Licença{' '}
          <a
            href="https://creativecommons.org/licenses/by/4.0/"
            className="underline"
            target="_blank"
            rel="noopener"
          >
            CC BY 4.0
          </a>{' '}
          — cite: SmartLic Índice Municipal.
          <Link href="/indice-municipal" className="ml-4 hover:underline">
            ← Voltar ao ranking
          </Link>
        </div>
      </main>
    </>
  );
}
