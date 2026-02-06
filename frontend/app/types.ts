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

/** Breakdown of filter rejection reasons */
export interface FilterStats {
  rejeitadas_uf: number;
  rejeitadas_valor: number;
  rejeitadas_keyword: number;
  rejeitadas_prazo: number;
  rejeitadas_outros: number;
}

/** Individual bid item for display in search results */
export interface LicitacaoItem {
  pncp_id: string;
  objeto: string;
  orgao: string;
  uf: string;
  municipio: string | null;
  valor: number;
  modalidade: string | null;
  data_publicacao: string | null;
  data_abertura: string | null;
  link: string;
  /** Status of the licitacao (e.g., "aberta", "em_julgamento", "encerrada") */
  status?: string | null;
  /** Keywords that matched this item during search */
  matched_keywords?: string[];
}

/** API response from POST /api/buscar */
export interface BuscaResult {
  resumo: Resumo;
  licitacoes: LicitacaoItem[];  // Individual bids for preview display
  download_id: string;
  total_raw: number;
  total_filtrado: number;
  filter_stats: FilterStats | null;
  termos_utilizados: string[] | null;
  stopwords_removidas: string[] | null;
  excel_available: boolean;
  upgrade_message: string | null;
}

/** Form validation errors */
export interface ValidationErrors {
  ufs?: string;
  data_inicial?: string;
  data_final?: string;
  date_range?: string;
}
