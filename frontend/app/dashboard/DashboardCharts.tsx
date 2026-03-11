"use client";

import React from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { formatCurrencyBR } from "../../lib/format-currency";

const formatCurrency = formatCurrencyBR;

function formatNumber(val: number): string {
  return new Intl.NumberFormat("pt-BR").format(val);
}

// ============================================================================
// Memoized Chart Tooltip (prevents re-creation on hover)
// ============================================================================

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

const ChartTooltip = React.memo(function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[var(--surface-elevated)] border border-[var(--border)] rounded-card p-3 shadow-lg text-sm">
      <p className="font-medium text-[var(--ink)] mb-1">{label}</p>
      {payload.map((entry, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-xs">
          {entry.name}: {entry.name === "value" ? formatCurrency(entry.value) : formatNumber(entry.value)}
        </p>
      ))}
    </div>
  );
});

// ============================================================================
// Time Series Line Chart
// ============================================================================

interface TimeSeriesPoint {
  label: string;
  searches: number;
  opportunities: number;
  value: number;
}

export function TimeSeriesChart({
  data,
  isMobile,
}: {
  data: TimeSeriesPoint[];
  isMobile: boolean;
}) {
  return (
    <ResponsiveContainer width="100%" height={isMobile ? 220 : 280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="label"
          tick={{ fill: "var(--ink-muted)", fontSize: isMobile ? 10 : 12 }}
          axisLine={{ stroke: "var(--border)" }}
          interval={isMobile ? "preserveStartEnd" : 0}
          angle={isMobile ? -45 : 0}
          textAnchor={isMobile ? "end" : "middle"}
          height={isMobile ? 50 : 30}
        />
        <YAxis
          tick={{ fill: "var(--ink-muted)", fontSize: isMobile ? 10 : 12 }}
          axisLine={{ stroke: "var(--border)" }}
          width={isMobile ? 35 : 60}
        />
        <Tooltip content={<ChartTooltip />} />
        <Line
          type="monotone"
          dataKey="searches"
          stroke="var(--brand-blue)"
          strokeWidth={2}
          dot={{ fill: "var(--brand-blue)", r: isMobile ? 6 : 4 }}
          activeDot={{ r: isMobile ? 10 : 8 }}
          name="Análises"
        />
        <Line
          type="monotone"
          dataKey="opportunities"
          stroke="var(--success)"
          strokeWidth={2}
          dot={{ fill: "var(--success)", r: isMobile ? 6 : 4 }}
          activeDot={{ r: isMobile ? 10 : 8 }}
          name="Oportunidades"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ============================================================================
// UF Pie Chart (Donut)
// ============================================================================

interface PieDataPoint {
  name: string;
  value: number;
  fill: string;
}

export function UfPieChart({ data }: { data: PieDataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={40}
          outerRadius={80}
          dataKey="value"
          stroke="none"
          minAngle={5}
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ============================================================================
// Sector Bar Chart (Vertical Layout)
// ============================================================================

interface SectorDataPoint {
  name: string;
  count: number;
  value: number;
}

export function SectorBarChart({
  data,
  isMobile,
}: {
  data: SectorDataPoint[];
  isMobile: boolean;
}) {
  return (
    <div className={isMobile ? "overflow-x-auto -mx-2 px-2" : ""}>
      <ResponsiveContainer width="100%" height={isMobile ? 250 : 200}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: isMobile ? 0 : 10, right: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis type="number" tick={{ fill: "var(--ink-muted)", fontSize: isMobile ? 10 : 11 }} />
          <YAxis
            type="category"
            dataKey="name"
            width={isMobile ? 100 : 160}
            tick={{ fill: "var(--ink-secondary)", fontSize: isMobile ? 10 : 11 }}
            tickFormatter={(v: string) => {
              const maxLen = isMobile ? 14 : 22;
              return v.length > maxLen ? v.slice(0, maxLen - 2) + "\u2026" : v;
            }}
          />
          <Tooltip content={<ChartTooltip />} />
          <Bar dataKey="count" fill="var(--brand-blue)" radius={[0, 4, 4, 0]} name="Análises" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
