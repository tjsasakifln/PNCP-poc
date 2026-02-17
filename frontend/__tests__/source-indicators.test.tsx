/**
 * GTM-FIX-011 AC32: Tests for source indicators in SearchResults component.
 *
 * Coverage:
 * - AC19: Source count summary with tooltip
 * - AC21: Partial failure banner (simple message)
 * - AC22: Toggle source badges for power users
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import SearchResults from "../app/buscar/components/SearchResults";
import type { SearchResultsProps } from "../app/buscar/components/SearchResults";
import type { BuscaResult } from "../app/types";

// Minimal mock for SearchResultsProps
const createMockProps = (overrides?: Partial<SearchResultsProps>): SearchResultsProps => ({
  // Loading state
  loading: false,
  loadingStep: 0,
  estimatedTime: 0,
  stateCount: 0,
  statesProcessed: 0,
  onCancel: jest.fn(),
  sseEvent: null,
  useRealProgress: false,
  sseAvailable: false,
  onStageChange: jest.fn(),

  // Error state
  error: null,
  quotaError: null,

  // Result
  result: null,
  rawCount: 0,

  // Empty state
  ufsSelecionadas: new Set(["SP"]),
  sectorName: "Vestuário",

  // Results display
  searchMode: "setor",
  termosArray: [],
  ordenacao: "relevancia" as const,
  onOrdenacaoChange: jest.fn(),

  // Download
  downloadLoading: false,
  downloadError: null,
  onDownload: jest.fn(),
  onSearch: jest.fn(),

  // Plan & auth
  planInfo: {
    plan_id: "smartlic_pro",
    plan_name: "SmartLic Pro",
    quota_used: 5,
    quota_reset_date: "2026-03-01",
    capabilities: {
      max_history_days: 1825,
      max_requests_per_month: 1000,
      allow_excel: true,
    },
  },
  session: { access_token: "test-token" },
  onShowUpgradeModal: jest.fn(),

  // Analytics
  onTrackEvent: jest.fn(),

  // STORY-257B props (optional with defaults)
  ufStatuses: undefined,
  ufTotalFound: 0,
  ufAllComplete: false,
  searchElapsedSeconds: 0,
  onViewPartial: undefined,
  partialDismissed: false,
  onDismissPartial: undefined,
  onRetryForceFresh: undefined,
  hasLastSearch: false,
  onLoadLastSearch: undefined,

  ...overrides,
});

// Minimal BuscaResult mock
const createMockResult = (overrides?: Partial<BuscaResult>): BuscaResult => ({
  resumo: {
    resumo_executivo: "Encontradas oportunidades no setor de vestuário.",
    total_oportunidades: 10,
    valor_total: 150000,
    destaques: ["Destaque 1"],
    alerta_urgencia: null,
    alertas_urgencia: null,
    recomendacoes: null,
    insight_setorial: null,
  },
  licitacoes: [
    {
      pncp_id: "test-001",
      objeto: "Aquisição de uniformes",
      orgao: "Prefeitura Municipal",
      uf: "SP",
      municipio: "São Paulo",
      valor: 50000,
      modalidade: "pregao",
      data_abertura: "2026-03-01",
      data_publicacao: "2026-02-15",
      situacao: "aberta",
      link: "https://pncp.gov.br/test-001",
      match_details: null,
    },
  ],
  download_id: null,
  download_url: null,
  total_raw: 100,
  total_filtrado: 10,
  filter_stats: null,
  termos_utilizados: ["uniforme", "farda"],
  stopwords_removidas: null,
  excel_available: true,
  upgrade_message: null,
  sources_used: ["PNCP"],
  source_stats: [
    {
      source_code: "PNCP",
      record_count: 100,
      duration_ms: 1500,
      error: null,
      status: "success",
    },
  ],
  hidden_by_min_match: null,
  filter_relaxed: null,
  metadata: null,
  ultima_atualizacao: "2026-02-17T10:00:00Z",
  is_partial: false,
  data_sources: undefined,
  degradation_reason: undefined,
  cached: false,
  cached_at: undefined,
  failed_ufs: undefined,
  is_truncated: false,
  truncated_ufs: undefined,
  ...overrides,
});

describe("SearchResults - Source Indicators (GTM-FIX-011 AC32)", () => {
  describe("AC19: Source count summary with tooltip", () => {
    it("shows '(2 fontes consultadas)' when multiple sources are used", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 20,
            duration_ms: 800,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      // Check for source count text
      expect(screen.getByText(/\(2 fontes consultadas\)/i)).toBeInTheDocument();
    });

    it("does not show source count when only one source is used", () => {
      const result = createMockResult({
        sources_used: ["PNCP"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 100,
            duration_ms: 1500,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      // Should NOT show source count for single source
      expect(screen.queryByText(/fontes consultadas/i)).not.toBeInTheDocument();
    });

    it("shows tooltip with per-source record counts on hover", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 20,
            duration_ms: 800,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      const { container } = render(<SearchResults {...props} />);

      // Find the tooltip element with title attribute
      const tooltipElement = container.querySelector('[title]');
      expect(tooltipElement).toBeInTheDocument();

      // Check tooltip content includes source codes and record counts
      const title = tooltipElement?.getAttribute("title");
      expect(title).toContain("PNCP: 80 registros");
      expect(title).toContain("PORTAL_COMPRAS: 20 registros");
    });
  });

  describe("AC21: Partial failure banner", () => {
    it("shows partial failure message when is_partial=true and sources_used has items", () => {
      const result = createMockResult({
        is_partial: true,
        cached: false,
        sources_used: ["PNCP"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 50,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 50 });
      render(<SearchResults {...props} />);

      // Check for partial failure message
      expect(
        screen.getByText(/Busca concluída \| Uma fonte temporariamente indisponível/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/dados podem estar incompletos/i)
      ).toBeInTheDocument();
    });

    it("does not show partial failure message when cached=true", () => {
      const result = createMockResult({
        is_partial: true,
        cached: true,
        sources_used: ["PNCP"],
      });

      const props = createMockProps({ result, rawCount: 50 });
      render(<SearchResults {...props} />);

      // Should NOT show partial message when results are cached
      expect(
        screen.queryByText(/Uma fonte temporariamente indisponível/i)
      ).not.toBeInTheDocument();
    });

    it("does not show partial failure message when not partial", () => {
      const result = createMockResult({
        is_partial: false,
        cached: false,
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      // Should NOT show partial message when search is complete
      expect(
        screen.queryByText(/Uma fonte temporariamente indisponível/i)
      ).not.toBeInTheDocument();
    });

    it("uses amber/warning styling for partial failure message", () => {
      const result = createMockResult({
        is_partial: true,
        cached: false,
        sources_used: ["PNCP"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 50,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 50 });
      const { container } = render(<SearchResults {...props} />);

      // Find the partial failure text element and check its parent for styling
      const partialText = screen.getByText(/Uma fonte temporariamente indisponível/i);
      expect(partialText.className).toContain("text-amber-");
    });
  });

  describe("AC22: Toggle source badges for power users", () => {
    it("shows 'Mostrar fontes' button when multiple source_stats exist", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 20,
            duration_ms: 800,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      // Check for toggle button
      expect(screen.getByText(/Mostrar fontes/i)).toBeInTheDocument();
    });

    it("does not show toggle button when only one source_stat", () => {
      const result = createMockResult({
        sources_used: ["PNCP"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 100,
            duration_ms: 1500,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      // Should NOT show toggle button for single source
      expect(screen.queryByText(/Mostrar fontes/i)).not.toBeInTheDocument();
    });

    it("toggles badge visibility when button clicked", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 20,
            duration_ms: 800,
            error: null,
            status: "partial",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      // Initially badges should not be visible
      expect(screen.queryByText(/PNCP: 80/)).not.toBeInTheDocument();
      expect(screen.queryByText(/PORTAL_COMPRAS: 20/)).not.toBeInTheDocument();

      // Click toggle button
      const toggleButton = screen.getByText(/Mostrar fontes/i);
      fireEvent.click(toggleButton);

      // Now badges should be visible
      expect(screen.getByText(/PNCP: 80/)).toBeInTheDocument();
      expect(screen.getByText(/PORTAL_COMPRAS: 20/)).toBeInTheDocument();

      // Button text should change to "Ocultar fontes"
      expect(screen.getByText(/Ocultar fontes/i)).toBeInTheDocument();
    });

    it("hides badges when toggle button clicked again", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 20,
            duration_ms: 800,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      // Show badges
      const toggleButton = screen.getByText(/Mostrar fontes/i);
      fireEvent.click(toggleButton);
      expect(screen.getByText(/PNCP: 80/)).toBeInTheDocument();

      // Hide badges
      const hideButton = screen.getByText(/Ocultar fontes/i);
      fireEvent.click(hideButton);
      expect(screen.queryByText(/PNCP: 80/)).not.toBeInTheDocument();

      // Button text should change back to "Mostrar fontes"
      expect(screen.getByText(/Mostrar fontes/i)).toBeInTheDocument();
    });

    it("shows correct badge styling for different sources", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 20,
            duration_ms: 800,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      const { container } = render(<SearchResults {...props} />);

      // Show badges
      const toggleButton = screen.getByText(/Mostrar fontes/i);
      fireEvent.click(toggleButton);

      // PNCP badge should have blue styling
      const pncpBadge = screen.getByText(/PNCP: 80/).closest("span");
      expect(pncpBadge?.className).toContain("bg-blue-100");

      // PORTAL_COMPRAS badge should have green styling
      const pcpBadge = screen.getByText(/PORTAL_COMPRAS: 20/).closest("span");
      expect(pcpBadge?.className).toContain("bg-green-100");
    });

    it("only shows success/partial sources in badges, not failed sources", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 0,
            duration_ms: 0,
            error: "Timeout",
            status: "timeout",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 80 });
      render(<SearchResults {...props} />);

      // Show badges
      const toggleButton = screen.getByText(/Mostrar fontes/i);
      fireEvent.click(toggleButton);

      // Only PNCP badge should show (status=success)
      expect(screen.getByText(/PNCP: 80/)).toBeInTheDocument();

      // PORTAL_COMPRAS badge should NOT show (status=timeout)
      expect(screen.queryByText(/PORTAL_COMPRAS/)).not.toBeInTheDocument();
    });

    it("has proper aria-expanded attribute on toggle button", () => {
      const result = createMockResult({
        sources_used: ["PNCP", "PORTAL_COMPRAS"],
        source_stats: [
          {
            source_code: "PNCP",
            record_count: 80,
            duration_ms: 1200,
            error: null,
            status: "success",
          },
          {
            source_code: "PORTAL_COMPRAS",
            record_count: 20,
            duration_ms: 800,
            error: null,
            status: "success",
          },
        ],
      });

      const props = createMockProps({ result, rawCount: 100 });
      render(<SearchResults {...props} />);

      const toggleButton = screen.getByText(/Mostrar fontes/i);

      // Initially aria-expanded=false
      expect(toggleButton).toHaveAttribute("aria-expanded", "false");

      // After click, aria-expanded=true
      fireEvent.click(toggleButton);
      expect(toggleButton).toHaveAttribute("aria-expanded", "true");
    });
  });
});
