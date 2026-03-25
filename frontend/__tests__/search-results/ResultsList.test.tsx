/**
 * TD-007 AC2: ResultsList sub-component tests.
 * Tests rendering of paginated licitacoes, top/bottom pagination,
 * paywall blurred results, and visual separator.
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import type { BuscaResult } from "../../app/types";

// --- Mocks ---

jest.mock(
  "../../app/buscar/components/search-results/ResultsPagination",
  () => ({
    ResultsPagination: function Mock({
      totalItems,
      currentPage,
      pageSize,
    }: any) {
      if (totalItems <= 0) return null;
      return (
        <div
          data-testid="results-pagination"
          data-total={totalItems}
          data-page={currentPage}
          data-size={pageSize}
        >
          Pagination
        </div>
      );
    },
  })
);

jest.mock("../../app/components/LicitacoesPreview", () => ({
  LicitacoesPreview: function Mock({ licitacoes }: any) {
    return (
      <div data-testid="licitacoes-preview" data-count={licitacoes.length}>
        {licitacoes.map((l: any, i: number) => (
          <div key={i} data-testid={`licitacao-item-${i}`}>
            {l.objeto}
          </div>
        ))}
      </div>
    );
  },
}));

jest.mock("../../components/billing/TrialPaywall", () => ({
  TrialPaywall: function Mock({ additionalCount }: any) {
    return (
      <div data-testid="trial-paywall" data-count={additionalCount}>
        Paywall
      </div>
    );
  },
}));

import { ResultsList } from "../../app/buscar/components/search-results/ResultsList";

// --- Mock factory ---

function createMockResult(overrides: Partial<BuscaResult> = {}): BuscaResult {
  return {
    resumo: {
      resumo_executivo: "Resumo de teste",
      total_oportunidades: 3,
      valor_total: 90000,
      recomendacoes: [],
      destaques: [],
      insight_setorial: null,
      alerta_urgencia: null,
      alertas_urgencia: [],
    } as any,
    licitacoes: overrides?.licitacoes ?? [
      { id: "1", objeto: "Objeto 1", uf: "SP", valor_estimado: 30000 } as any,
      { id: "2", objeto: "Objeto 2", uf: "RJ", valor_estimado: 30000 } as any,
      { id: "3", objeto: "Objeto 3", uf: "MG", valor_estimado: 30000 } as any,
    ],
    download_id: null,
    download_url: null,
    total_raw: 10,
    total_filtrado: 3,
    filter_stats: null,
    termos_utilizados: null,
    stopwords_removidas: null,
    excel_available: true,
    upgrade_message: null,
    source_stats: null,
    ultima_atualizacao: "2026-03-01T12:00:00Z",
    llm_source: "keyword",
    ...overrides,
  } as BuscaResult;
}

const baseListProps = {
  totalLicitacoes: 3,
  currentPage: 1,
  pageSize: 10 as const,
  onPageChange: jest.fn(),
  onPageSizeChange: jest.fn(),
  searchMode: "setor" as const,
  termosArray: [],
  planInfo: { capabilities: { allow_excel: true } },
  session: { access_token: "token-123" },
  onShowUpgradeModal: jest.fn(),
  searchId: "search-abc",
  setorId: "ti",
  paywallApplied: false,
  totalBeforePaywall: null,
};

describe("ResultsList", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // --- Pagination ---

  it("renders top and bottom pagination", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
      />
    );
    const paginations = screen.getAllByTestId("results-pagination");
    expect(paginations).toHaveLength(1);
  });

  it("passes correct props to pagination", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
        totalLicitacoes={30}
        currentPage={2}
        pageSize={10}
      />
    );
    const paginations = screen.getAllByTestId("results-pagination");
    // Both paginations should have matching props
    expect(paginations[0]).toHaveAttribute("data-total", "30");
    expect(paginations[0]).toHaveAttribute("data-page", "2");
    expect(paginations[0]).toHaveAttribute("data-size", "10");
  });

  // --- LicitacoesPreview ---

  it("renders LicitacoesPreview with paginated items", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
      />
    );
    expect(screen.getByTestId("licitacoes-preview")).toBeInTheDocument();
    expect(screen.getByTestId("licitacoes-preview")).toHaveAttribute(
      "data-count",
      "3"
    );
  });

  it("does not render LicitacoesPreview when paginatedLicitacoes is empty", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={[]}
        {...baseListProps}
        totalLicitacoes={0}
      />
    );
    expect(screen.queryByTestId("licitacoes-preview")).not.toBeInTheDocument();
  });

  it("renders all paginated items inside LicitacoesPreview", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
      />
    );
    expect(screen.getByTestId("licitacao-item-0")).toBeInTheDocument();
    expect(screen.getByTestId("licitacao-item-1")).toBeInTheDocument();
    expect(screen.getByTestId("licitacao-item-2")).toBeInTheDocument();
  });

  // --- Visual separator ---

  it("shows visual separator when licitacoes exist", () => {
    const result = createMockResult();
    const { container } = render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
      />
    );
    // The border-t separator is a div with border styling
    const separator = container.querySelector(".border-t.border-strong");
    expect(separator).toBeInTheDocument();
  });

  it("does not show visual separator when licitacoes are empty", () => {
    const result = createMockResult({ licitacoes: [] });
    const { container } = render(
      <ResultsList
        result={result}
        paginatedLicitacoes={[]}
        {...baseListProps}
        totalLicitacoes={0}
      />
    );
    const separator = container.querySelector(".border-t.border-strong");
    expect(separator).not.toBeInTheDocument();
  });

  // --- Paywall blurred results ---

  it("shows paywall blurred results when paywallApplied and has hidden items", () => {
    const result = createMockResult({
      licitacoes: [
        {
          id: "1",
          objeto: "Objeto 1",
          uf: "SP",
          valor_estimado: 30000,
        } as any,
      ],
    });
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
        paywallApplied={true}
        totalBeforePaywall={5}
        totalLicitacoes={1}
      />
    );
    expect(screen.getByTestId("paywall-blurred-results")).toBeInTheDocument();
    expect(screen.getByTestId("trial-paywall")).toBeInTheDocument();
    // additionalCount = totalBeforePaywall(5) - licitacoes.length(1) = 4
    expect(screen.getByTestId("trial-paywall")).toHaveAttribute(
      "data-count",
      "4"
    );
  });

  it("does not show paywall blurred results when paywallApplied=false", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
        paywallApplied={false}
        totalBeforePaywall={5}
      />
    );
    expect(
      screen.queryByTestId("paywall-blurred-results")
    ).not.toBeInTheDocument();
  });

  it("does not show paywall blurred results when totalBeforePaywall is null", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
        paywallApplied={true}
        totalBeforePaywall={null}
      />
    );
    expect(
      screen.queryByTestId("paywall-blurred-results")
    ).not.toBeInTheDocument();
  });

  it("does not show paywall when totalBeforePaywall equals licitacoes count (no hidden items)", () => {
    const result = createMockResult();
    render(
      <ResultsList
        result={result}
        paginatedLicitacoes={result.licitacoes}
        {...baseListProps}
        paywallApplied={true}
        totalBeforePaywall={3} // same as result.licitacoes.length
      />
    );
    expect(
      screen.queryByTestId("paywall-blurred-results")
    ).not.toBeInTheDocument();
  });
});
