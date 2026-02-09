/**
 * PNCP Statistics Types
 * Matches backend schema from schemas.py:PNCPStatsResponse
 */

export interface PNCPStats {
  total_bids_30d: number;
  annualized_total: number;
  total_value_30d: number;
  annualized_value: number;
  total_sectors: number;
  last_updated: string;
}

export interface PNCPStatsAPIResponse extends PNCPStats {
  // API response matches PNCPStats exactly
}
