'use client';

/**
 * STORY-431 AC3+AC4+AC5: Client component for Observatory report page.
 * Renders Recharts visualizations, CSV download button, and embed code.
 */

import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const CHART_COLORS = [
  '#2563eb', '#7c3aed', '#db2777', '#ea580c', '#d97706',
  '#65a30d', '#0891b2', '#4f46e5', '#be185d', '#b45309',
];

interface UfCount {
  uf: string;
  uf_name: string;
  total: number;
  pct: number;
}

interface ModalidadeCount {
  modalidade_id: number;
  modalidade_name: string;
  total: number;
  pct: number;
}

interface SetorHighlight {
  setor_id: string;
  setor_name: string;
  total_atual: number;
  total_anterior: number;
  variacao_pct: number;
}

interface Relatorio {
  mes: number;
  ano: number;
  mes_nome: string;
  periodo: string;
  total_editais: number;
  valor_total: number;
  valor_medio: number;
  top_ufs: UfCount[];
  modalidades: ModalidadeCount[];
  tendencia_semanal: { semana: string; total: number }[];
  setores_em_alta: SetorHighlight[];
  gerado_em: string;
  fonte: string;
  license: string;
}

function formatBRL(v: number): string {
  if (v >= 1e9) return `R$ ${(v / 1e9).toFixed(1).replace('.', ',')} bi`;
  if (v >= 1e6) return `R$ ${(v / 1e6).toFixed(1).replace('.', ',')} mi`;
  if (v >= 1e3) return `R$ ${(v / 1e3).toFixed(0)} mil`;
  return `R$ ${v.toFixed(0)}`;
}

function formatInt(n: number): string {
  return new Intl.NumberFormat('pt-BR').format(n);
}

export default function ObservatorioRelatorioClient({
  relatorio,
  slug,
  mesDisplay,
  ano,
  mes,
}: {
  relatorio: Relatorio;
  slug: string;
  mesDisplay: string;
  ano: number;
  mes: number;
}) {
  const [embedCopied, setEmbedCopied] = useState(false);

  const csvUrl = `/v1/observatorio/relatorio/${mes}/${ano}/csv`;
  const embedUrl = `https://smartlic.tech/observatorio/embed/${slug}`;
  const embedCode = `<iframe src="${embedUrl}" width="100%" height="500" frameborder="0" title="Raio-X das Licitações — ${mesDisplay} ${ano} | SmartLic Observatório"></iframe>`;

  async function handleCopyEmbed() {
    try {
      await navigator.clipboard.writeText(embedCode);
      setEmbedCopied(true);
      setTimeout(() => setEmbedCopied(false), 2500);
    } catch {/* ignore */}
  }

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      {/* Header */}
      <div className="mb-8">
        <nav className="text-sm text-gray-500 mb-3">
          <a href="/observatorio" className="hover:underline text-blue-600">Observatório</a>
          {' '}/{' '}
          <span>{mesDisplay} {ano}</span>
        </nav>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Raio-X das Licitações — {mesDisplay} de {ano}
        </h1>
        <p className="text-gray-500 text-sm">{relatorio.periodo}</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
          <p className="text-xs text-blue-500 font-semibold uppercase tracking-wide mb-1">Total de editais</p>
          <p className="text-3xl font-black text-blue-800">{formatInt(relatorio.total_editais)}</p>
          <p className="text-xs text-blue-400 mt-1">editais publicados</p>
        </div>
        <div className="bg-green-50 rounded-xl p-5 border border-green-100">
          <p className="text-xs text-green-500 font-semibold uppercase tracking-wide mb-1">Valor total estimado</p>
          <p className="text-3xl font-black text-green-800">{formatBRL(relatorio.valor_total)}</p>
          <p className="text-xs text-green-400 mt-1">soma dos valores estimados</p>
        </div>
        <div className="bg-purple-50 rounded-xl p-5 border border-purple-100">
          <p className="text-xs text-purple-500 font-semibold uppercase tracking-wide mb-1">Valor médio por edital</p>
          <p className="text-3xl font-black text-purple-800">{formatBRL(relatorio.valor_medio)}</p>
          <p className="text-xs text-purple-400 mt-1">excluindo outliers P95+</p>
        </div>
      </div>

      {/* Chart 1: Top 10 UFs */}
      {relatorio.top_ufs.length > 0 && (
        <section className="mb-10">
          <h2 className="text-xl font-bold text-gray-800 mb-1">Top 10 estados por volume</h2>
          <p className="text-sm text-gray-500 mb-4">Fonte: SmartLic Observatório — dados PNCP</p>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={relatorio.top_ufs} layout="vertical" margin={{ left: 80, right: 20, top: 5, bottom: 5 }}>
                <XAxis type="number" tickFormatter={(v) => formatInt(v)} tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="uf_name" width={80} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number | undefined) => [formatInt(v ?? 0), 'Editais']} />
                <Bar dataKey="total" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Chart 2: Modalidade distribution */}
      {relatorio.modalidades.length > 0 && (
        <section className="mb-10">
          <h2 className="text-xl font-bold text-gray-800 mb-1">Distribuição por modalidade</h2>
          <p className="text-sm text-gray-500 mb-4">Fonte: SmartLic Observatório — dados PNCP</p>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={relatorio.modalidades}
                  dataKey="total"
                  nameKey="modalidade_name"
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- TD-FE-001 STORY-3.2: recharts PieLabelRenderProps doesn't expose custom data shape
                  label={(entry: any) => `${(entry.pct as number ?? 0).toFixed(0)}%`}
                >
                  {relatorio.modalidades.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Legend
                  formatter={(value) => <span className="text-xs">{value}</span>}
                />
                <Tooltip formatter={(v: number | undefined, name) => [formatInt(v ?? 0) + ' editais', name]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Sectors in high growth */}
      {relatorio.setores_em_alta.length > 0 && (
        <section className="mb-10">
          <h2 className="text-xl font-bold text-gray-800 mb-1">Setores em alta</h2>
          <p className="text-sm text-gray-500 mb-4">Crescimento vs. mês anterior — Fonte: SmartLic Observatório</p>
          <div className="space-y-2">
            {relatorio.setores_em_alta.map((s) => (
              <div key={s.setor_id} className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg">
                <span className="font-medium text-gray-800">{s.setor_name}</span>
                <div className="text-right">
                  <span className="text-green-600 font-bold text-lg">+{s.variacao_pct.toFixed(0)}%</span>
                  <p className="text-xs text-gray-400">{formatInt(s.total_atual)} editais (anterior: {formatInt(s.total_anterior)})</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Actions: CSV + Embed */}
      <section className="mt-10 p-6 bg-gray-50 rounded-xl border border-gray-200">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Dados e incorporação</h2>
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <a
            href={csvUrl}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
          >
            ↓ Baixar dados (CSV)
          </a>
          <button
            onClick={handleCopyEmbed}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-200 text-gray-700 text-sm font-semibold hover:bg-gray-300 transition-colors"
          >
            {embedCopied ? '✓ Código copiado!' : '<> Incorporar gráficos'}
          </button>
        </div>
        {embedCopied && (
          <p className="text-xs text-gray-500">
            Cole o código no seu site. O link de volta ao SmartLic é obrigatório pelo CC BY 4.0.
          </p>
        )}
        <p className="text-xs text-gray-400 mt-3">
          Licença: Creative Commons BY 4.0 — cite como "SmartLic Observatório (smartlic.tech/observatorio/{slug})"
        </p>
      </section>

      <footer className="mt-8 pt-6 border-t border-gray-100">
        <p className="text-xs text-gray-400">
          {relatorio.fonte} · Gerado em {new Date(relatorio.gerado_em).toLocaleDateString('pt-BR')}
        </p>
      </footer>
    </main>
  );
}
