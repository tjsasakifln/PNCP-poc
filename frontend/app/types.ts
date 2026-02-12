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
  rejeitadas_min_match: number;
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
  data_encerramento: string | null;
  /** Days remaining until proposal deadline (negative if past) */
  dias_restantes?: number | null;
  /** Urgency level: critica (<7d), alta (7-14d), media (14-30d), baixa (>30d), encerrada (past) */
  urgencia?: string | null;
  link: string;
  /** Status of the licitacao (e.g., "aberta", "em_julgamento", "encerrada") */
  status?: string | null;
  /** Keywords that matched this item during search */
  matched_keywords?: string[];
  /** Source that provided this record (e.g., "PNCP", "COMPRAS_GOV", "PORTAL_COMPRAS") */
  _source?: string;
  /** Relevance score 0.0-1.0 (only when custom terms active) */
  relevance_score?: number | null;
  /** List of search terms that matched this bid */
  matched_terms?: string[] | null;
}

/** Per-source fetch metrics (multi-source mode) */
export interface SourceStat {
  source_code: string;
  record_count: number;
  duration_ms: number;
  error: string | null;
  status: string;
}

/** Validation metadata for search terms */
export interface TermValidationMetadata {
  termos_utilizados: string[];
  termos_ignorados: string[];
  motivos_ignorados: Record<string, string>;
}

/** API response from POST /api/buscar */
export interface BuscaResult {
  resumo: Resumo;
  licitacoes: LicitacaoItem[];  // Individual bids for preview display
  download_id: string;
  download_url?: string | null;  // STORY-202 CROSS-C02: Signed URL from object storage (60min TTL)
  total_raw: number;
  total_filtrado: number;
  filter_stats: FilterStats | null;
  termos_utilizados: string[] | null;
  stopwords_removidas: string[] | null;
  excel_available: boolean;
  upgrade_message: string | null;
  /** Per-source metrics when multi-source is active */
  source_stats: SourceStat[] | null;
  /** Number of bids with partial matches hidden by min match floor */
  hidden_by_min_match?: number | null;
  /** True if the min match filter was relaxed due to zero results */
  filter_relaxed?: boolean | null;
  /** Term validation metadata (new format for ignored terms) */
  metadata?: TermValidationMetadata | null;
  /** ISO timestamp of when search results were generated */
  ultima_atualizacao?: string | null;
}

/** Form validation errors */
export interface ValidationErrors {
  ufs?: string;
  data_inicial?: string;
  data_final?: string;
  date_range?: string;
}

// ============================================================================
// InMail Messaging Types
// ============================================================================

export type ConversationCategory = "suporte" | "sugestao" | "funcionalidade" | "bug" | "outro";
export type ConversationStatus = "aberto" | "respondido" | "resolvido";

export interface MessageResponse {
  id: string;
  sender_id: string;
  sender_email?: string | null;
  body: string;
  is_admin_reply: boolean;
  read_by_user: boolean;
  read_by_admin: boolean;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  user_id: string;
  user_email?: string | null;
  subject: string;
  category: ConversationCategory;
  status: ConversationStatus;
  last_message_at: string;
  created_at: string;
  unread_count: number;
}

export interface ConversationDetail {
  id: string;
  user_id: string;
  user_email?: string | null;
  subject: string;
  category: ConversationCategory;
  status: ConversationStatus;
  last_message_at: string;
  created_at: string;
  messages: MessageResponse[];
}

export interface ConversationsListResponse {
  conversations: ConversationSummary[];
  total: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}
