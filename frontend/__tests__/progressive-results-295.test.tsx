/**
 * STORY-295: Progressive Results Delivery — Frontend tests.
 *
 * AC9: Results appear in table as partial_results SSE events arrive
 * AC10: Visual indicator per source (SourceStatusGrid)
 * AC11: Counter updates in real-time
 * AC14: Banner "Análise em andamento — resultados parciais disponíveis"
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import SourceStatusGrid from "../app/buscar/components/SourceStatusGrid";
import SearchResults from "../app/buscar/components/SearchResults";
import type { SearchResultsProps } from "../app/buscar/components/SearchResults";
import type { SourceStatus } from "../hooks/useSearchSSE";

// ============================================================================
// SourceStatusGrid tests (AC10)
// ============================================================================

describe("SourceStatusGrid", () => {
  it("renders nothing when sourceStatuses is empty", () => {
    const { container } = render(
      <SourceStatusGrid sourceStatuses={new Map()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders source badges for each source", () => {
    const statuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "success", recordCount: 42, durationMs: 1500 }],
      ["PORTAL_COMPRAS", { status: "fetching", recordCount: 0, durationMs: 0 }],
    ]);

    render(<SourceStatusGrid sourceStatuses={statuses} />);

    expect(screen.getByText("PNCP")).toBeInTheDocument();
    expect(screen.getByText("Portal de Compras")).toBeInTheDocument();
    expect(screen.getByText("(42)")).toBeInTheDocument();
  });

  it("shows correct icon for success status", () => {
    const statuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "success", recordCount: 10, durationMs: 1000 }],
    ]);

    render(<SourceStatusGrid sourceStatuses={statuses} />);
    // Check mark icon (✓)
    expect(screen.getByText("\u2713")).toBeInTheDocument();
  });

  it("shows correct icon for error status", () => {
    const statuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "error", recordCount: 0, durationMs: 500, error: "Connection refused" }],
    ]);

    render(<SourceStatusGrid sourceStatuses={statuses} />);
    // X mark icon (✗)
    expect(screen.getByText("\u2717")).toBeInTheDocument();
  });

  it("shows correct icon for timeout status", () => {
    const statuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "timeout", recordCount: 0, durationMs: 90000 }],
    ]);

    render(<SourceStatusGrid sourceStatuses={statuses} />);
    // Stopwatch icon (⏱)
    expect(screen.getByText("\u23F1")).toBeInTheDocument();
  });

  it("does not show count when recordCount is 0", () => {
    const statuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "error", recordCount: 0, durationMs: 500 }],
    ]);

    render(<SourceStatusGrid sourceStatuses={statuses} />);
    expect(screen.queryByText("(0)")).not.toBeInTheDocument();
  });

  it("applies custom className", () => {
    const statuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "success", recordCount: 5, durationMs: 1000 }],
    ]);

    const { container } = render(
      <SourceStatusGrid sourceStatuses={statuses} className="mt-4" />
    );
    expect(container.firstChild).toHaveClass("mt-4");
  });
});

// ============================================================================
// SearchResults integration tests (AC11, AC14)
// ============================================================================

const createMockProps = (overrides?: Partial<SearchResultsProps>): SearchResultsProps => ({
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
  error: null,
  quotaError: null,
  result: null,
  rawCount: 0,
  ufsSelecionadas: new Set(["SP"]),
  sectorName: "Vestuario",
  searchMode: "setor",
  termosArray: [],
  ordenacao: "relevancia" as const,
  onOrdenacaoChange: jest.fn(),
  downloadLoading: false,
  downloadError: null,
  onDownload: jest.fn(),
  onSearch: jest.fn(),
  planInfo: {
    plan_id: "smartlic_pro",
    plan_name: "SmartLic Pro",
    quota_used: 5,
    quota_reset_date: "2026-03-01",
    capabilities: {
      max_history_days: 365,
      max_requests_per_month: 100,
      allow_excel: true,
    },
  },
  session: { access_token: "test-token" },
  onShowUpgradeModal: jest.fn(),
  onTrackEvent: jest.fn(),
  ...overrides,
});

describe("SearchResults with progressive results", () => {
  it("shows SourceStatusGrid during loading when sourceStatuses has entries", () => {
    const sourceStatuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "success", recordCount: 25, durationMs: 1500 }],
      ["PORTAL_COMPRAS", { status: "fetching", recordCount: 0, durationMs: 0 }],
    ]);

    render(
      <SearchResults
        {...createMockProps({
          loading: true,
          sourceStatuses,
        })}
      />
    );

    expect(screen.getByText("PNCP")).toBeInTheDocument();
    expect(screen.getByText("Portal de Compras")).toBeInTheDocument();
  });

  it("shows progressive results counter during loading (AC11)", () => {
    render(
      <SearchResults
        {...createMockProps({
          loading: true,
          partialProgress: {
            newCount: 25,
            totalSoFar: 25,
            ufsCompleted: ["PNCP"],
            ufsPending: ["PORTAL_COMPRAS"],
          },
        })}
      />
    );

    expect(screen.getByText(/Analisando 25 licitações encontradas/)).toBeInTheDocument();
  });

  it("shows singular when only 1 result (AC11)", () => {
    render(
      <SearchResults
        {...createMockProps({
          loading: true,
          partialProgress: {
            newCount: 1,
            totalSoFar: 1,
            ufsCompleted: ["PNCP"],
            ufsPending: [],
          },
        })}
      />
    );

    expect(screen.getByText(/Analisando 1 licitações encontradas/)).toBeInTheDocument();
  });

  it('shows "Análise em andamento" label in progressive banner (AC14)', () => {
    render(
      <SearchResults
        {...createMockProps({
          loading: true,
          partialProgress: {
            newCount: 10,
            totalSoFar: 10,
            ufsCompleted: ["PNCP"],
            ufsPending: ["PCP"],
          },
        })}
      />
    );

    expect(screen.getByText("Análise em andamento")).toBeInTheDocument();
  });

  it("does not show progressive banner when no partial results", () => {
    render(
      <SearchResults
        {...createMockProps({
          loading: true,
          partialProgress: null,
        })}
      />
    );

    expect(screen.queryByText(/oportunidades encontradas até agora/)).not.toBeInTheDocument();
    expect(screen.queryByText("Análise em andamento")).not.toBeInTheDocument();
  });

  it("does not show progressive banner when totalSoFar is 0", () => {
    render(
      <SearchResults
        {...createMockProps({
          loading: true,
          partialProgress: {
            newCount: 0,
            totalSoFar: 0,
            ufsCompleted: [],
            ufsPending: ["PNCP"],
          },
        })}
      />
    );

    expect(screen.queryByText(/oportunidades encontradas até agora/)).not.toBeInTheDocument();
  });

  it("does not show SourceStatusGrid or banner when not loading", () => {
    const sourceStatuses = new Map<string, SourceStatus>([
      ["PNCP", { status: "success", recordCount: 25, durationMs: 1500 }],
    ]);

    render(
      <SearchResults
        {...createMockProps({
          loading: false,
          sourceStatuses,
          partialProgress: {
            newCount: 25,
            totalSoFar: 25,
            ufsCompleted: ["PNCP"],
            ufsPending: [],
          },
        })}
      />
    );

    // Not in loading state — should not show progressive UI
    expect(screen.queryByText("Análise em andamento")).not.toBeInTheDocument();
  });
});
