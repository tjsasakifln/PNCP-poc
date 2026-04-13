// Shared types and utilities for the Histórico page.
// Extracted to a separate file so they can be imported by tests without
// triggering Next.js's restriction on arbitrary named exports from page files.

export type SearchSessionStatus =
  | 'created'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'timed_out'
  | 'cancelled';

export interface SearchSession {
  id: string;
  sectors: string[];
  ufs: string[];
  data_inicial: string;
  data_final: string;
  custom_keywords: string[] | null;
  total_raw: number;
  total_filtered: number;
  valor_total: number;
  resumo_executivo: string | null;
  created_at: string;
  status: SearchSessionStatus;
  error_message: string | null;
  error_code: string | null;
  duration_ms: number | null;
  pipeline_stage: string | null;
  started_at: string;
  response_state: string | null;
  download_available?: boolean;
}

export interface GroupedSession {
  representative: SearchSession; // completed session if exists, otherwise most recent
  attempts: number;              // total sessions in this group
}

// UX-433 AC1: Group sessions by setor+UFs within a 5-minute window.
// Consecutive attempts of the same search appear as a single entry with "N tentativas".
export function groupSessions(sessions: SearchSession[]): GroupedSession[] {
  if (sessions.length === 0) return [];

  const groups: GroupedSession[] = [];

  for (const session of sessions) {
    const sessionKey = [...session.sectors].sort().join("|") + "##" + [...session.ufs].sort().join("|");
    const sessionTime = new Date(session.created_at).getTime();

    // Find a matching group within 5 minutes
    const matchingGroup = groups.find((g) => {
      const repKey =
        [...g.representative.sectors].sort().join("|") +
        "##" +
        [...g.representative.ufs].sort().join("|");
      if (repKey !== sessionKey) return false;
      // Check within 5-minute window using the group's earliest/latest entry
      const repTime = new Date(g.representative.created_at).getTime();
      const diffMs = Math.abs(sessionTime - repTime);
      return diffMs < 5 * 60 * 1000;
    });

    if (matchingGroup) {
      matchingGroup.attempts += 1;
      // Prefer the completed session as representative; otherwise keep most recent
      if (session.status === "completed") {
        matchingGroup.representative = session;
      } else if (
        matchingGroup.representative.status !== "completed" &&
        sessionTime > new Date(matchingGroup.representative.created_at).getTime()
      ) {
        matchingGroup.representative = session;
      }
    } else {
      groups.push({ representative: session, attempts: 1 });
    }
  }

  return groups;
}
