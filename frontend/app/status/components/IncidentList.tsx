"use client";

/**
 * STORY-316 AC13: Recent incidents list for public status page.
 */

interface Incident {
  id: string;
  started_at: string;
  resolved_at: string | null;
  status: "ongoing" | "resolved";
  affected_sources: string[];
  description: string;
}

interface IncidentListProps {
  incidents: Incident[];
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatDuration(start: string, end: string | null): string {
  if (!end) return "Em andamento";
  try {
    const ms = new Date(end).getTime() - new Date(start).getTime();
    const minutes = Math.floor(ms / 60000);
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remainingMins = minutes % 60;
    return remainingMins > 0 ? `${hours}h ${remainingMins}min` : `${hours}h`;
  } catch {
    return "—";
  }
}

export default function IncidentList({ incidents }: IncidentListProps) {
  if (!incidents || incidents.length === 0) {
    return (
      <div className="text-center py-6 text-ink-secondary text-sm">
        Nenhum incidente nos últimos 30 dias.
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-semibold text-ink mb-4">Incidentes Recentes</h3>
      <div className="space-y-3">
        {incidents.map((incident) => (
          <div
            key={incident.id}
            className={`border rounded-lg p-4 ${
              incident.status === "ongoing"
                ? "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950"
                : "border-border bg-surface-2"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      incident.status === "ongoing" ? "bg-red-500 animate-pulse" : "bg-green-500"
                    }`}
                  />
                  <span className="text-sm font-medium text-ink">
                    {incident.status === "ongoing" ? "Em andamento" : "Resolvido"}
                  </span>
                  <span className="text-xs text-ink-muted">
                    {formatDate(incident.started_at)}
                  </span>
                </div>
                <p className="text-sm text-ink-secondary">{incident.description}</p>
                {incident.affected_sources.length > 0 && (
                  <div className="flex gap-1 mt-2">
                    {incident.affected_sources.map((src) => (
                      <span
                        key={src}
                        className="text-xs px-2 py-0.5 rounded bg-surface-1 text-ink-muted border border-border"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <span className="text-xs text-ink-muted whitespace-nowrap">
                {formatDuration(incident.started_at, incident.resolved_at)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
