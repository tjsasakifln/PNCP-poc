/**
 * STORY-431 AC1+AC3+AC4+AC5+AC7: Observatory monthly report page.
 *
 * Slug format: raio-x-abril-2026 → mes=4, ano=2026
 * Renders charts (BarChart, PieChart, LineChart), CSV download, embed button.
 */

import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ObservatorioRelatorioClient from './ObservatorioRelatorioClient';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const MONTH_NAMES_PT: Record<string, number> = {
  janeiro: 1, fevereiro: 2, marco: 3, abril: 4, maio: 5, junho: 6,
  julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12,
};

const MONTH_NAMES_DISPLAY: Record<number, string> = {
  1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
  7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
};

function parseSlug(slug: string): { mes: number; ano: number } | null {
  // Expected: "raio-x-{mes_nome}-{ano}" e.g. "raio-x-marco-2026"
  const parts = slug.split('-');
  if (parts.length < 4) return null;
  const mesNome = parts[parts.length - 2];
  const anoStr = parts[parts.length - 1];
  const mes = MONTH_NAMES_PT[mesNome.toLowerCase()];
  const ano = parseInt(anoStr, 10);
  if (!mes || isNaN(ano) || ano < 2024) return null;
  return { mes, ano };
}

async function fetchRelatorio(mes: number, ano: number) {
  try {
    const resp = await fetch(`${BACKEND_URL}/v1/observatorio/relatorio/${mes}/${ano}`, {
      next: { revalidate: 86400 }, // 24h ISR
    });
    if (!resp.ok) return null;
    return await resp.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ 'mes-ano': string }>;
}): Promise<Metadata> {
  const { 'mes-ano': slug } = await params;
  const parsed = parseSlug(slug);
  if (!parsed) return { title: 'Relatório não encontrado' };

  const { mes, ano } = parsed;
  const mesDisplay = MONTH_NAMES_DISPLAY[mes] ?? String(mes);
  const relatorio = await fetchRelatorio(mes, ano);

  const totalDisplay = relatorio?.total_editais
    ? new Intl.NumberFormat('pt-BR').format(relatorio.total_editais)
    : null;

  const title = totalDisplay
    ? `${totalDisplay} editais em ${mesDisplay} de ${ano} — Raio-X das Licitações`
    : `Raio-X das Licitações — ${mesDisplay} ${ano}`;

  const description = totalDisplay
    ? `O Brasil publicou ${totalDisplay} editais no PNCP em ${mesDisplay.toLowerCase()} de ${ano}. Análise completa por UF, modalidade e setor com dados reais. Licença Creative Commons BY 4.0.`
    : `Análise mensal das licitações públicas brasileiras em ${mesDisplay.toLowerCase()} de ${ano}. Dados PNCP, livre para citar.`;

  return {
    title,
    description,
    alternates: { canonical: `https://smartlic.tech/observatorio/${slug}` },
    openGraph: {
      title,
      description,
      url: `https://smartlic.tech/observatorio/${slug}`,
      type: 'article',
      locale: 'pt_BR',
    },
    robots: { index: true },
  };
}

export default async function RelatorioPage({
  params,
}: {
  params: Promise<{ 'mes-ano': string }>;
}) {
  const { 'mes-ano': slug } = await params;
  const parsed = parseSlug(slug);
  if (!parsed) notFound();

  const { mes, ano } = parsed;
  const relatorio = await fetchRelatorio(mes, ano);
  if (!relatorio) notFound();

  const mesDisplay = MONTH_NAMES_DISPLAY[mes] ?? String(mes);

  const datasetSchema = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `Raio-X das Licitações — ${mesDisplay} ${ano}`,
    description: relatorio.periodo,
    url: `https://smartlic.tech/observatorio/${slug}`,
    license: 'https://creativecommons.org/licenses/by/4.0/',
    creator: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: 'https://smartlic.tech',
    },
    temporalCoverage: `${ano}-${String(mes).padStart(2, '0')}`,
    spatialCoverage: 'Brasil',
    distribution: [
      {
        '@type': 'DataDownload',
        encodingFormat: 'text/csv',
        contentUrl: `https://smartlic.tech/v1/observatorio/relatorio/${mes}/${ano}/csv`,
      },
      {
        '@type': 'DataDownload',
        encodingFormat: 'application/json',
        contentUrl: `https://smartlic.tech/v1/observatorio/relatorio/${mes}/${ano}`,
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />
      <ObservatorioRelatorioClient
        relatorio={relatorio}
        slug={slug}
        mesDisplay={mesDisplay}
        ano={ano}
        mes={mes}
      />
    </>
  );
}
