'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { ContractMonthlyTrend } from '@/lib/contracts-fallback';

interface TrendBarChartProps {
  data: ContractMonthlyTrend[];
}

const MESES_PT: Record<string, string> = {
  '01': 'jan', '02': 'fev', '03': 'mar', '04': 'abr',
  '05': 'mai', '06': 'jun', '07': 'jul', '08': 'ago',
  '09': 'set', '10': 'out', '11': 'nov', '12': 'dez',
};

function formatMonth(raw: string): string {
  // Esperado: "YYYY-MM" (ex.: "2024-03")
  const parts = raw.split('-');
  if (parts.length === 2) {
    const mes = MESES_PT[parts[1]] ?? parts[1];
    return `${mes}/${parts[0].slice(2)}`;
  }
  return raw;
}

interface TooltipPayloadEntry {
  value: number;
  dataKey: string;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const count = payload[0]?.value ?? 0;
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-3 py-2 text-xs shadow-lg">
      <p className="font-medium text-[var(--ink)] mb-1">{label}</p>
      <p className="text-[var(--ink-secondary)]">
        {count.toLocaleString('pt-BR')} contrato{count !== 1 ? 's' : ''}
      </p>
    </div>
  );
}

export default function TrendBarChart({ data }: TrendBarChartProps) {
  const chartData = data.map((point) => ({
    month: formatMonth(point.month),
    count: point.count,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="month"
          tick={{ fill: 'var(--ink-muted)', fontSize: 11 }}
          axisLine={{ stroke: 'var(--border)' }}
          tickLine={false}
          interval={1}
        />
        <YAxis
          tick={{ fill: 'var(--ink-muted)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v))}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--surface-2)' }} />
        <Bar dataKey="count" fill="var(--brand-blue)" radius={[3, 3, 0, 0]} maxBarSize={36} />
      </BarChart>
    </ResponsiveContainer>
  );
}
