export interface PipelineItem {
  id: string;
  user_id: string;
  pncp_id: string;
  objeto: string;
  orgao: string | null;
  uf: string | null;
  valor_estimado: number | null;
  data_encerramento: string | null;
  link_pncp: string | null;
  stage: PipelineStage;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type PipelineStage = "descoberta" | "analise" | "preparando" | "enviada" | "resultado";

export const STAGE_CONFIG: Record<PipelineStage, { label: string; color: string; icon: string }> = {
  descoberta: { label: "Descoberta", color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300", icon: "🔍" },
  analise: { label: "Em Análise", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300", icon: "📋" },
  preparando: { label: "Preparando Proposta", color: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300", icon: "📝" },
  enviada: { label: "Enviada", color: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300", icon: "📤" },
  resultado: { label: "Resultado", color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300", icon: "🏁" },
};

export const STAGES_ORDER: PipelineStage[] = ["descoberta", "analise", "preparando", "enviada", "resultado"];

export interface PipelineListResponse {
  items: PipelineItem[];
  total: number;
  limit: number;
  offset: number;
}
