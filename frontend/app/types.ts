/**
 * Type definitions for BidIQ Uniformes POC
 */

/** Brazilian state codes (UFs) */
export const UFS = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
  "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
  "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
] as const;

export type UF = (typeof UFS)[number];

/** Search parameters for PNCP API */
export interface SearchParams {
  ufs: string[];
  data_inicial: string; // YYYY-MM-DD format
  data_final: string;   // YYYY-MM-DD format
  setor_id: string;     // Sector ID (e.g., "vestuario")
}

/** Available procurement sector */
export interface Setor {
  id: string;
  name: string;
  description: string;
}

/** Executive summary from GPT-4.1-nano */
export interface Resumo {
  resumo_executivo: string;
  total_oportunidades: number;
  valor_total: number;
  destaques: string[];
  distribuicao_uf: Record<string, number>;
  alerta_urgencia: string | null;
}

/** API response from POST /api/buscar */
export interface BuscaResult {
  resumo: Resumo;
  download_id: string;
  total_raw: number;
  total_filtrado: number;
}

/** Form validation errors */
export interface ValidationErrors {
  ufs?: string;
  data_inicial?: string;
  data_final?: string;
  date_range?: string;
}
