// Shared types for dashboard components

export interface AnalyticsSummary {
  total_searches: number;
  total_downloads: number;
  total_opportunities: number;
  total_value_discovered: number;
  estimated_hours_saved: number;
  avg_results_per_search: number;
  success_rate: number;
  member_since: string;
}

export interface TimeSeriesPoint {
  label: string;
  searches: number;
  opportunities: number;
  value: number;
}

export interface DimensionItem {
  name: string;
  count: number;
  value: number;
}

export interface TopDimensions {
  top_ufs: DimensionItem[];
  top_sectors: DimensionItem[];
}

export type Period = "day" | "week" | "month";

// DEBT-127: Pipeline alerts and new opportunities
export interface PipelineAlertItem {
  id: string;
  pncp_id: string;
  objeto: string;
  orgao?: string;
  uf?: string;
  data_encerramento?: string;
  stage: string;
}

export interface PipelineAlertsData {
  items: PipelineAlertItem[];
  total: number;
}

export interface NewOpportunitiesData {
  count: number;
  has_previous_search: boolean;
  last_search_at?: string;
  days_since_last_search?: number;
  label?: string; // UX-431 AC2: "Última busca concluída" when most recent session failed/pending
}

// CRIT-018 AC4/AC5: Per-section error flags for independent failure handling
export interface DashboardData {
  summary: AnalyticsSummary | null;
  timeSeries: TimeSeriesPoint[];
  dimensions: TopDimensions | null;
  summaryError?: boolean;
  timeSeriesError?: boolean;
  dimensionsError?: boolean;
}
