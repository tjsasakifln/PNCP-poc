/**
 * Public intelligence surface contracts — #2112
 *
 * Empty, stale, blocked and error are distinct. Missing data is never
 * rendered as a factual zero.
 */

export type FreshnessState = "fresh" | "stale" | "unknown";
export type CompletenessState = "complete" | "incomplete" | "unknown";
export type SurfaceState = "ok" | "empty" | "stale" | "blocked" | "error" | "unknown";

export interface Provenance {
  source: string;
  asOf: string | null;
  sourceUpdatedAt?: string | null;
  freshness: FreshnessState;
  completeness: CompletenessState;
  reasonCodes: string[];
  limitations: string[];
  contractVersion?: string;
}

export interface EntityEdge {
  href: string;
  label: string;
  kind:
    | "company"
    | "contract"
    | "tender"
    | "organ"
    | "municipality"
    | "supplier"
    | "sector"
    | "observatory";
}

export function classifySurface(input: {
  hasEntity: boolean;
  rowCount?: number | null;
  freshness?: FreshnessState;
  blocked?: boolean;
  error?: boolean;
}): SurfaceState {
  if (input.error) return "error";
  if (input.blocked) return "blocked";
  if (!input.hasEntity) return "empty";
  if (input.rowCount === null || input.rowCount === undefined) return "unknown";
  if (input.freshness === "stale") return "stale";
  if (input.rowCount === 0) return "empty";
  return "ok";
}

export function defaultLimitations(family: string): string[] {
  return [
    `Recorte público da família ${family}. Não é parecer jurídico.`,
    "A autoridade dos fatos é o extra-cli via public_read_v1 quando o cutover estiver ativo.",
    "Ausência de linha não prova que o fato não existe na origem.",
  ];
}
