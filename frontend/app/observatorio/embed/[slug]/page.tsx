/**
 * STORY-431 AC5: Observatory embed — stripped version for iframe embedding.
 *
 * Backlink to full report is required (CC BY 4.0) and followable.
 */

import { Metadata } from 'next';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const MONTH_NAMES_PT: Record<string, number> = {
  janeiro: 1, fevereiro: 2, marco: 3, abril: 4, maio: 5, junho: 6,
  julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12,
};

function parseSlug(slug: string): { mes: number; ano: number } | null {
  const parts = slug.split('-');
  if (parts.length < 4) return null;
  const mesNome = parts[parts.length - 2];
  const anoStr = parts[parts.length - 1];
  const mes = MONTH_NAMES_PT[mesNome.toLowerCase()];
  const ano = parseInt(anoStr, 10);
  if (!mes || isNaN(ano)) return null;
  return { mes, ano };
}

export const metadata: Metadata = {
  robots: { index: false, follow: true }, // noindex — embed não deve aparecer em busca
};

export default async function ObservatorioEmbedPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const parsed = parseSlug(slug);

  if (!parsed) {
    return <div className="p-4 text-gray-500 text-sm">Relatório não encontrado.</div>;
  }

  const { mes, ano } = parsed;

  type UfBreakdown = { uf: string; total: number };
  type ObservatorioRelatorio = {
    mes_nome: string;
    total_editais: number;
    valor_medio: number;
    top_ufs: UfBreakdown[];
  };
  let relatorio: ObservatorioRelatorio | null = null;
  try {
    const resp = await fetch(`${BACKEND_URL}/v1/observatorio/relatorio/${mes}/${ano}`, {
      next: { revalidate: 86400 },
      signal: AbortSignal.timeout(10000),
    });
    if (resp.ok) relatorio = (await resp.json()) as ObservatorioRelatorio;
  } catch {/* fail gracefully */}

  if (!relatorio) {
    return <div className="p-4 text-gray-500 text-sm">Dados indisponíveis.</div>;
  }

  const fullUrl = `https://smartlic.tech/observatorio/${slug}`;
  const topUfs: UfBreakdown[] = (relatorio.top_ufs ?? []).slice(0, 5);
  const maxCount = topUfs.reduce((m: number, u: UfBreakdown) => Math.max(m, u.total), 1);

  return (
    <div className="min-h-screen bg-white font-sans text-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <div>
          <a href="https://smartlic.tech" target="_blank" rel="noopener" className="text-blue-700 font-bold text-xs hover:underline">
            SmartLic Observatório
          </a>
          <span className="text-gray-400 text-xs ml-1">— Raio-X das Licitações {relatorio.mes_nome} {ano}</span>
        </div>
        <a href={fullUrl} target="_blank" rel="noopener" className="text-xs text-blue-600 hover:underline">
          Ver relatório completo →
        </a>
      </div>

      {/* Summary */}
      <div className="px-4 py-4 grid grid-cols-2 gap-3">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-black text-blue-800">
            {new Intl.NumberFormat('pt-BR').format(relatorio.total_editais)}
          </p>
          <p className="text-xs text-blue-500 mt-1">editais publicados</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-black text-green-800">
            {relatorio.valor_medio >= 1e6
              ? `R$ ${(relatorio.valor_medio / 1e6).toFixed(1).replace('.', ',')} mi`
              : `R$ ${(relatorio.valor_medio / 1e3).toFixed(0)} mil`}
          </p>
          <p className="text-xs text-green-500 mt-1">valor médio por edital</p>
        </div>
      </div>

      {/* Mini bar chart */}
      {topUfs.length > 0 && (
        <div className="px-4 pb-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Top 5 estados</p>
          {topUfs.map((u: UfBreakdown) => (
            <div key={u.uf} className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-500 w-6 shrink-0">{u.uf}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-3">
                {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width is computed from UF total relative to max count */}
                <div
                  className="bg-blue-500 h-3 rounded-full"
                  style={{ width: `${(u.total / maxCount) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-600 w-10 text-right shrink-0">
                {new Intl.NumberFormat('pt-BR').format(u.total)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Footer with required backlink (CC BY 4.0) */}
      <footer className="px-4 py-3 border-t border-gray-100 text-center">
        <p className="text-xs text-gray-400">
          Dados:{' '}
          <a href={fullUrl} target="_blank" rel="noopener" className="text-blue-600 hover:underline font-medium">
            SmartLic Observatório — {relatorio.mes_nome} de {ano}
          </a>
          {' '}· CC BY 4.0
        </p>
      </footer>
    </div>
  );
}
