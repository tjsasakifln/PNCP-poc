'use client';

import { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from 'recharts';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SectorAggregate {
  sector_id: string;
  sector_name: string;
  count: number;
  total_value: number;
  avg_value: number;
}

interface UfAggregate {
  uf: string;
  count: number;
  total_value: number;
}

interface ModalidadeAggregate {
  code: number;
  name: string;
  count: number;
  pct: number;
}

interface TrendPoint {
  date: string;
  count: number;
  value: number;
}

export interface DadosData {
  updated_at: string;
  period: string;
  period_start: string;
  period_end: string;
  total_bids: number;
  total_value: number;
  avg_value: number;
  by_sector: SectorAggregate[];
  by_uf: UfAggregate[];
  by_modalidade: ModalidadeAggregate[];
  trend_30d: TrendPoint[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});

const CHART_COLORS = [
  '#2563eb',
  '#16a34a',
  '#d97706',
  '#dc2626',
  '#7c3aed',
  '#0891b2',
  '#db2777',
  '#059669',
];

function generateCSV(data: DadosData): string {
  const rows: string[] = ['Tipo,Nome,Quantidade,Valor Total,Valor Médio'];

  for (const s of data.by_sector) {
    rows.push(
      `Setor,${s.sector_name},${s.count},${s.total_value},${s.avg_value}`
    );
  }
  for (const u of data.by_uf) {
    rows.push(`UF,${u.uf},${u.count},${u.total_value},`);
  }
  for (const m of data.by_modalidade) {
    rows.push(`Modalidade,${m.name},${m.count},,`);
  }
  for (const t of data.trend_30d) {
    rows.push(`Tendência,${t.date},${t.count},${t.value},`);
  }

  return rows.join('\n');
}

// ---------------------------------------------------------------------------
// Email-gated download modal
// ---------------------------------------------------------------------------

function DownloadModal({
  onClose,
  onConfirm,
}: {
  onClose: () => void;
  onConfirm: (email: string) => void;
}) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setError('Insira um e-mail válido.');
      return;
    }
    onConfirm(email);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="download-modal-title"
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl">
        <h2
          id="download-modal-title"
          className="mb-2 text-xl font-bold text-gray-900"
        >
          Baixar dados em CSV
        </h2>
        <p className="mb-6 text-sm text-gray-600">
          Informe seu e-mail para receber novidades sobre o painel de dados e
          licitações do seu setor.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="download-email"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              E-mail profissional
            </label>
            <input
              id="download-email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError('');
              }}
              placeholder="voce@empresa.com.br"
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              required
              autoFocus
            />
            {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            >
              Baixar CSV
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
          </div>
        </form>
        <p className="mt-4 text-xs text-gray-400">
          Seus dados são tratados conforme a LGPD. Sem spam.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab types
// ---------------------------------------------------------------------------

type Tab = 'setor' | 'uf' | 'modalidade' | 'tendencia';

const TABS: { id: Tab; label: string }[] = [
  { id: 'setor', label: 'Por Setor' },
  { id: 'uf', label: 'Por UF' },
  { id: 'modalidade', label: 'Por Modalidade' },
  { id: 'tendencia', label: 'Tendência' },
];

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function DadosClient({ data }: { data: DadosData }) {
  const [activeTab, setActiveTab] = useState<Tab>('setor');
  const [showModal, setShowModal] = useState(false);

  function handleDownloadClick() {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('dados_download_email');
      if (stored) {
        triggerDownload();
        return;
      }
    }
    setShowModal(true);
  }

  function handleModalConfirm(email: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('dados_download_email', email);
    }
    setShowModal(false);
    triggerDownload();
  }

  function triggerDownload() {
    const csv = generateCSV(data);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `smartlic-dados-licitacoes-${data.period_end}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <div className="w-full">
      {/* Download button */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={handleDownloadClick}
          className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-300"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
            />
          </svg>
          Baixar dados (CSV)
        </button>
      </div>

      {/* Tab navigation */}
      <div className="mb-6 flex gap-1 rounded-xl bg-gray-100 p-1" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-300 ${
              activeTab === tab.id
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div id={`panel-setor`} role="tabpanel" hidden={activeTab !== 'setor'}>
        {activeTab === 'setor' && <SetorTab data={data.by_sector} />}
      </div>
      <div id={`panel-uf`} role="tabpanel" hidden={activeTab !== 'uf'}>
        {activeTab === 'uf' && <UfTab data={data.by_uf} />}
      </div>
      <div
        id={`panel-modalidade`}
        role="tabpanel"
        hidden={activeTab !== 'modalidade'}
      >
        {activeTab === 'modalidade' && (
          <ModalidadeTab data={data.by_modalidade} />
        )}
      </div>
      <div
        id={`panel-tendencia`}
        role="tabpanel"
        hidden={activeTab !== 'tendencia'}
      >
        {activeTab === 'tendencia' && <TendenciaTab data={data.trend_30d} />}
      </div>

      {showModal && (
        <DownloadModal
          onClose={() => setShowModal(false)}
          onConfirm={handleModalConfirm}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SetorTab({ data }: { data: SectorAggregate[] }) {
  const top = data.slice(0, 15);
  return (
    <div className="space-y-6">
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={top}
            layout="vertical"
            margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis
              dataKey="sector_name"
              type="category"
              width={140}
              tick={{ fontSize: 11 }}
            />
            <Tooltip
              formatter={(v: unknown) => [(v as number).toLocaleString('pt-BR'), 'Editais']}
            />
            <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <th className="pb-2 pr-4">Setor</th>
              <th className="pb-2 pr-4 text-right">Editais</th>
              <th className="pb-2 pr-4 text-right">Valor Total</th>
              <th className="pb-2 text-right">Valor Médio</th>
            </tr>
          </thead>
          <tbody>
            {data.map((s) => (
              <tr
                key={s.sector_id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 pr-4 font-medium text-gray-900">
                  {s.sector_name}
                </td>
                <td className="py-2 pr-4 text-right text-gray-700">
                  {s.count.toLocaleString('pt-BR')}
                </td>
                <td className="py-2 pr-4 text-right text-gray-700">
                  {BRL.format(s.total_value)}
                </td>
                <td className="py-2 text-right text-gray-700">
                  {BRL.format(s.avg_value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function UfTab({ data }: { data: UfAggregate[] }) {
  const top = data.slice(0, 27);
  return (
    <div className="space-y-6">
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={top}
            layout="vertical"
            margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis
              dataKey="uf"
              type="category"
              width={40}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(v: unknown) => [(v as number).toLocaleString('pt-BR'), 'Editais']}
            />
            <Bar dataKey="count" fill="#16a34a" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <th className="pb-2 pr-4">UF</th>
              <th className="pb-2 pr-4 text-right">Editais</th>
              <th className="pb-2 text-right">Valor Total</th>
            </tr>
          </thead>
          <tbody>
            {data.map((u) => (
              <tr
                key={u.uf}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 pr-4 font-medium text-gray-900">{u.uf}</td>
                <td className="py-2 pr-4 text-right text-gray-700">
                  {u.count.toLocaleString('pt-BR')}
                </td>
                <td className="py-2 text-right text-gray-700">
                  {BRL.format(u.total_value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModalidadeTab({ data }: { data: ModalidadeAggregate[] }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        <div className="h-64 w-full sm:w-64 flex-shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="count"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any -- TD-FE-001 STORY-3.2: recharts PieLabelRenderProps doesn't expose custom data shape
                label={(entry: any) => `${(entry as { pct: number }).pct}%`}
                labelLine
              >
                {data.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill={CHART_COLORS[idx % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(v: unknown, name: unknown) => [
                  (v as number).toLocaleString('pt-BR'),
                  name as string,
                ]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                <th className="pb-2 pr-4">Modalidade</th>
                <th className="pb-2 pr-4 text-right">Editais</th>
                <th className="pb-2 text-right">%</th>
              </tr>
            </thead>
            <tbody>
              {data.map((m, idx) => (
                <tr
                  key={m.code}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="flex items-center gap-2 py-2 pr-4 font-medium text-gray-900">
                    <span
                      className="inline-block h-3 w-3 rounded-full flex-shrink-0"
                      style={{
                        background: CHART_COLORS[idx % CHART_COLORS.length],
                      }}
                    />
                    {m.name}
                  </td>
                  <td className="py-2 pr-4 text-right text-gray-700">
                    {m.count.toLocaleString('pt-BR')}
                  </td>
                  <td className="py-2 text-right text-gray-700">{m.pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function TendenciaTab({ data }: { data: TrendPoint[] }) {
  return (
    <div className="space-y-4">
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: string) => v.slice(5)}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11 }}
              label={{
                value: 'Editais',
                angle: -90,
                position: 'insideLeft',
                offset: 10,
                style: { fontSize: 11, fill: '#6b7280' },
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: number) =>
                v >= 1e9
                  ? `R$${(v / 1e9).toFixed(1)}B`
                  : v >= 1e6
                  ? `R$${(v / 1e6).toFixed(1)}M`
                  : `R$${(v / 1e3).toFixed(0)}K`
              }
            />
            <Tooltip
              formatter={(v: unknown, name: unknown) => {
                const val = v as number;
                const key = name as string;
                return [
                  key === 'count' ? val.toLocaleString('pt-BR') : BRL.format(val),
                  key === 'count' ? 'Editais' : 'Valor',
                ];
              }}
              labelFormatter={(label: unknown) => `Data: ${label as string}`}
            />
            <Legend
              formatter={(v: string) =>
                v === 'count' ? 'Editais' : 'Valor Total'
              }
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="count"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="value"
              stroke="#16a34a"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-400">
        Editais publicados por dia nos últimos 30 dias no PNCP.
      </p>
    </div>
  );
}
