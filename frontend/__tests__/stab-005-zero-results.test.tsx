/**
 * STAB-005 AC2-5: Zero Results UX Tests
 *
 * Tests for:
 * - ZeroResultsSuggestions (AC2): Shows source total + filter breakdown
 * - FilterStatsBreakdown (AC3): Visual funnel of filter rejections
 * - FilterRelaxedBanner (AC4): Dismissible relaxation notice
 * - UfFailureDetail (AC5): Per-UF failure messages with retry
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ZeroResultsSuggestions } from "../app/buscar/components/ZeroResultsSuggestions";
import { FilterStatsBreakdown } from "../app/buscar/components/FilterStatsBreakdown";
import { FilterRelaxedBanner } from "../app/buscar/components/FilterRelaxedBanner";
import { UfFailureDetail } from "../app/buscar/components/UfFailureDetail";

// ---------------------------------------------------------------------------
// Test 1: ZeroResultsSuggestions renders with correct message and total
// ---------------------------------------------------------------------------
describe("ZeroResultsSuggestions", () => {
  it("renders source total message when totalFromSources is provided", () => {
    render(
      <ZeroResultsSuggestions
        sectorName="Informatica"
        ufCount={3}
        dayRange={10}
        totalFromSources={47}
      />
    );

    expect(screen.getByTestId("zero-results-suggestions")).toBeInTheDocument();
    expect(screen.getByTestId("source-total-message")).toBeInTheDocument();
    expect(screen.getByText("47")).toBeInTheDocument();
    expect(screen.getByText(/licitacoes encontradas/)).toBeInTheDocument();
    expect(screen.getByText(/Informatica/)).toBeInTheDocument();
  });

  it("renders fallback message when totalFromSources is not provided", () => {
    render(
      <ZeroResultsSuggestions
        sectorName="Saude"
        ufCount={1}
        dayRange={30}
      />
    );

    expect(screen.getByTestId("zero-results-suggestions")).toBeInTheDocument();
    expect(screen.queryByTestId("source-total-message")).not.toBeInTheDocument();
    expect(screen.getByText(/1 estado/)).toBeInTheDocument();
    expect(screen.getByText(/30 dias/)).toBeInTheDocument();
  });

  it("renders filter stats breakdown when filterStats provided", () => {
    const stats = {
      rejeitadas_uf: 12,
      rejeitadas_valor: 8,
      rejeitadas_keyword: 27,
      rejeitadas_min_match: 0,
      rejeitadas_prazo: 0,
      rejeitadas_outros: 0,
    };

    render(
      <ZeroResultsSuggestions
        sectorName="Engenharia"
        ufCount={5}
        dayRange={10}
        totalFromSources={47}
        filterStats={stats}
      />
    );

    expect(screen.getByTestId("filter-stats-breakdown")).toBeInTheDocument();
  });

  it("renders action buttons when callbacks provided", () => {
    const onAdjust = jest.fn();
    const onExpand = jest.fn();
    const onSector = jest.fn();

    render(
      <ZeroResultsSuggestions
        sectorName="Software"
        ufCount={2}
        dayRange={10}
        onAdjustPeriod={onAdjust}
        onAddNeighborStates={onExpand}
        onChangeSector={onSector}
      />
    );

    const adjustBtn = screen.getByTestId("suggestion-adjust-period");
    const neighborsBtn = screen.getByTestId("suggestion-add-neighbors");
    const sectorBtn = screen.getByTestId("suggestion-change-sector");

    fireEvent.click(adjustBtn);
    expect(onAdjust).toHaveBeenCalledTimes(1);

    fireEvent.click(neighborsBtn);
    expect(onExpand).toHaveBeenCalledTimes(1);

    fireEvent.click(sectorBtn);
    expect(onSector).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// Test 2: FilterStatsBreakdown renders funnel correctly
// ---------------------------------------------------------------------------
describe("FilterStatsBreakdown", () => {
  it("renders bars for each active filter stage", () => {
    const stats = {
      rejeitadas_uf: 12,
      rejeitadas_valor: 8,
      rejeitadas_keyword: 27,
      rejeitadas_min_match: 0,
      rejeitadas_prazo: 0,
      rejeitadas_outros: 0,
    };

    render(<FilterStatsBreakdown stats={stats} />);

    expect(screen.getByTestId("filter-stats-breakdown")).toBeInTheDocument();
    // Should show 3 active stages (UF, valor, keyword) — others are 0
    expect(screen.getByText("UF (estado)")).toBeInTheDocument();
    expect(screen.getByText("Faixa de valor")).toBeInTheDocument();
    expect(screen.getByText("Palavras-chave")).toBeInTheDocument();
    // Should NOT show stages with 0 removals
    expect(screen.queryByText("Prazo/status")).not.toBeInTheDocument();
    expect(screen.queryByText("Outros")).not.toBeInTheDocument();
  });

  it("renders nothing when all stats are zero", () => {
    const stats = {
      rejeitadas_uf: 0,
      rejeitadas_valor: 0,
      rejeitadas_keyword: 0,
      rejeitadas_min_match: 0,
      rejeitadas_prazo: 0,
      rejeitadas_outros: 0,
    };

    const { container } = render(<FilterStatsBreakdown stats={stats} />);
    expect(container.firstChild).toBeNull();
  });

  it("shows correct percentages", () => {
    const stats = {
      rejeitadas_uf: 50,
      rejeitadas_valor: 50,
      rejeitadas_keyword: 0,
      rejeitadas_min_match: 0,
      rejeitadas_prazo: 0,
      rejeitadas_outros: 0,
    };

    render(<FilterStatsBreakdown stats={stats} />);

    // Each should be 50% — getAllByText since both bars have same value
    const percentLabels = screen.getAllByText("50 (50%)");
    expect(percentLabels).toHaveLength(2);
  });

  it("shows total rejection count", () => {
    const stats = {
      rejeitadas_uf: 10,
      rejeitadas_valor: 5,
      rejeitadas_keyword: 15,
      rejeitadas_min_match: 0,
      rejeitadas_prazo: 0,
      rejeitadas_outros: 0,
    };

    render(<FilterStatsBreakdown stats={stats} />);

    expect(screen.getByText(/30 licitacoes removidas/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Test 3: FilterRelaxedBanner shows/dismisses correctly
// ---------------------------------------------------------------------------
describe("FilterRelaxedBanner", () => {
  it("renders with relaxation message", () => {
    render(
      <FilterRelaxedBanner
        relaxationLevel="keywords_relaxed"
        originalCount={0}
        relaxedCount={5}
      />
    );

    expect(screen.getByTestId("filter-relaxed-banner")).toBeInTheDocument();
    expect(screen.getByText("Resultados com filtro ampliado")).toBeInTheDocument();
    expect(screen.getByText(/menor correspondencia de palavras-chave/)).toBeInTheDocument();
    expect(screen.getByText(/5 resultados encontrados/)).toBeInTheDocument();
  });

  it("dismisses when X button clicked", () => {
    render(
      <FilterRelaxedBanner
        relaxationLevel="keywords_relaxed"
        originalCount={0}
        relaxedCount={5}
      />
    );

    expect(screen.getByTestId("filter-relaxed-banner")).toBeInTheDocument();

    const dismissBtn = screen.getByTestId("filter-relaxed-dismiss");
    fireEvent.click(dismissBtn);

    expect(screen.queryByTestId("filter-relaxed-banner")).not.toBeInTheDocument();
  });

  it("shows default message when no relaxation level specified", () => {
    render(
      <FilterRelaxedBanner
        originalCount={0}
        relaxedCount={3}
      />
    );

    expect(screen.getByText(/criterios de filtragem foram ampliados/)).toBeInTheDocument();
  });

  it("shows value range message for value_range_expanded", () => {
    render(
      <FilterRelaxedBanner
        relaxationLevel="value_range_expanded"
        originalCount={0}
        relaxedCount={2}
      />
    );

    expect(screen.getByText(/faixa de valor foi ampliada/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Test 4: UfFailureDetail shows correct message per reason type
// ---------------------------------------------------------------------------
describe("UfFailureDetail", () => {
  it("shows timeout message", () => {
    render(<UfFailureDetail uf="SP" reason="timeout" source="PNCP" />);

    expect(screen.getByTestId("uf-failure-SP")).toBeInTheDocument();
    expect(screen.getByText(/PNCP nao respondeu para SP/)).toBeInTheDocument();
    expect(screen.getByText(/tempo esgotado/)).toBeInTheDocument();
  });

  it("shows rate limit message", () => {
    render(<UfFailureDetail uf="RJ" reason="rate_limit" source="PCP" />);

    expect(screen.getByTestId("uf-failure-RJ")).toBeInTheDocument();
    expect(screen.getByText(/Taxa limite atingida para RJ/)).toBeInTheDocument();
  });

  it("shows offline message", () => {
    render(<UfFailureDetail uf="MG" reason="offline" source="ComprasGov" />);

    expect(screen.getByTestId("uf-failure-MG")).toBeInTheDocument();
    expect(screen.getByText(/Fonte ComprasGov indisponivel para MG/)).toBeInTheDocument();
  });

  it("shows generic error message", () => {
    render(<UfFailureDetail uf="BA" reason="error" source="PNCP" />);

    expect(screen.getByTestId("uf-failure-BA")).toBeInTheDocument();
    expect(screen.getByText(/Erro ao consultar BA/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Test 5: UfFailureDetail retry button calls callback
// ---------------------------------------------------------------------------
describe("UfFailureDetail retry", () => {
  it("shows retry button when onRetry provided", () => {
    const onRetry = jest.fn();
    render(<UfFailureDetail uf="SP" reason="timeout" source="PNCP" onRetry={onRetry} />);

    const retryBtn = screen.getByTestId("uf-retry-SP");
    expect(retryBtn).toBeInTheDocument();
    expect(retryBtn).toHaveTextContent("Tentar novamente");

    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("does not show retry button when onRetry not provided", () => {
    render(<UfFailureDetail uf="RJ" reason="error" source="PNCP" />);

    expect(screen.queryByTestId("uf-retry-RJ")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Test 6: Components render nothing when no data provided (graceful)
// ---------------------------------------------------------------------------
describe("Graceful empty rendering", () => {
  it("FilterStatsBreakdown renders null with empty stats", () => {
    const stats = {
      rejeitadas_uf: 0,
      rejeitadas_valor: 0,
      rejeitadas_keyword: 0,
      rejeitadas_min_match: 0,
      rejeitadas_prazo: 0,
      rejeitadas_outros: 0,
    };

    const { container } = render(<FilterStatsBreakdown stats={stats} />);
    expect(container.firstChild).toBeNull();
  });

  it("ZeroResultsSuggestions renders without optional props", () => {
    render(
      <ZeroResultsSuggestions
        sectorName="Alimentos"
        ufCount={0}
        dayRange={10}
      />
    );

    expect(screen.getByTestId("zero-results-suggestions")).toBeInTheDocument();
    // Should not crash — buttons should not appear without callbacks
    expect(screen.queryByTestId("suggestion-adjust-period")).not.toBeInTheDocument();
    expect(screen.queryByTestId("suggestion-add-neighbors")).not.toBeInTheDocument();
    expect(screen.queryByTestId("suggestion-change-sector")).not.toBeInTheDocument();
  });

  it("ZeroResultsSuggestions renders without filter breakdown when filterStats null", () => {
    render(
      <ZeroResultsSuggestions
        sectorName="Saude"
        ufCount={2}
        dayRange={10}
        totalFromSources={10}
        filterStats={null}
      />
    );

    expect(screen.queryByTestId("filter-stats-breakdown")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Test 7: Integration: zero results + filter stats shows suggestions
// ---------------------------------------------------------------------------
describe("Integration: zero results + filter stats", () => {
  it("shows source total AND filter breakdown together", () => {
    const stats = {
      rejeitadas_uf: 5,
      rejeitadas_valor: 10,
      rejeitadas_keyword: 32,
      rejeitadas_min_match: 0,
      rejeitadas_prazo: 0,
      rejeitadas_outros: 0,
    };

    render(
      <ZeroResultsSuggestions
        sectorName="Mobiliario"
        ufCount={4}
        dayRange={10}
        totalFromSources={47}
        filterStats={stats}
        onAdjustPeriod={() => {}}
        onAddNeighborStates={() => {}}
        onChangeSector={() => {}}
      />
    );

    // Source total message
    expect(screen.getByTestId("source-total-message")).toBeInTheDocument();
    expect(screen.getByText("47")).toBeInTheDocument();

    // Filter breakdown
    expect(screen.getByTestId("filter-stats-breakdown")).toBeInTheDocument();
    expect(screen.getByText("UF (estado)")).toBeInTheDocument();
    expect(screen.getByText("Faixa de valor")).toBeInTheDocument();
    expect(screen.getByText("Palavras-chave")).toBeInTheDocument();

    // Action buttons
    expect(screen.getByTestId("suggestion-adjust-period")).toBeInTheDocument();
    expect(screen.getByTestId("suggestion-add-neighbors")).toBeInTheDocument();
    expect(screen.getByTestId("suggestion-change-sector")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Test 8: FilterRelaxedBanner auto-hides after dismiss
// ---------------------------------------------------------------------------
describe("FilterRelaxedBanner dismiss persistence", () => {
  it("stays dismissed after click — does not reappear", () => {
    const { rerender } = render(
      <FilterRelaxedBanner
        relaxationLevel="min_match_lowered"
        originalCount={0}
        relaxedCount={8}
      />
    );

    expect(screen.getByTestId("filter-relaxed-banner")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("filter-relaxed-dismiss"));
    expect(screen.queryByTestId("filter-relaxed-banner")).not.toBeInTheDocument();

    // Re-render with same props — should still be dismissed (state persists)
    rerender(
      <FilterRelaxedBanner
        relaxationLevel="min_match_lowered"
        originalCount={0}
        relaxedCount={8}
      />
    );
    // Note: useState is preserved across rerenders of same component instance
    expect(screen.queryByTestId("filter-relaxed-banner")).not.toBeInTheDocument();
  });
});
