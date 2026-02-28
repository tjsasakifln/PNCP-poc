"use client";

/**
 * STORY-316 AC12: Uptime chart showing last 90 days as horizontal bars.
 * Green = 100%, Yellow = partially degraded, Red = incident.
 */

interface DayData {
  date: string;
  uptime_pct: number;
  checks: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
}

interface UptimeChartProps {
  history: DayData[];
}

function getBarColor(pct: number): string {
  if (pct >= 99) return "bg-green-500";
  if (pct >= 80) return "bg-yellow-500";
  return "bg-red-500";
}

function getBarTitle(day: DayData): string {
  return `${day.date}: ${day.uptime_pct}% uptime (${day.checks} checks — ${day.healthy} healthy, ${day.degraded} degraded, ${day.unhealthy} unhealthy)`;
}

export default function UptimeChart({ history }: UptimeChartProps) {
  if (!history || history.length === 0) {
    return (
      <div className="text-center py-8 text-ink-secondary text-sm">
        Dados de uptime serão exibidos após o primeiro dia de monitoramento.
      </div>
    );
  }

  // Show last 90 days, pad with empty if needed
  const days = history.slice(-90);

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-lg font-semibold text-ink">Uptime — Últimos 90 dias</h3>
      </div>

      {/* Bar chart */}
      <div className="flex gap-[2px] items-end h-10" role="img" aria-label="Gráfico de uptime dos últimos 90 dias">
        {days.map((day) => (
          <div
            key={day.date}
            className={`flex-1 min-w-[2px] rounded-sm ${getBarColor(day.uptime_pct)} transition-opacity hover:opacity-80 cursor-default`}
            style={{ height: `${Math.max(day.uptime_pct, 5)}%` }}
            title={getBarTitle(day)}
            role="presentation"
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 text-xs text-ink-secondary">
        <span className="flex items-center gap-1">
          <span className="inline-block w-2.5 h-2.5 rounded-sm bg-green-500" />
          100%
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2.5 h-2.5 rounded-sm bg-yellow-500" />
          Parcial
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2.5 h-2.5 rounded-sm bg-red-500" />
          Incidente
        </span>
        <span className="ml-auto">{days.length} dias</span>
      </div>
    </div>
  );
}
