/**
 * Tests for GTM-RESILIENCE-A05 operational state components (AC16-AC17).
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { OperationalStateBanner } from "../../app/buscar/components/OperationalStateBanner";
import { CoverageBar } from "../../app/buscar/components/CoverageBar";
import type { UfStatusDetailItem } from "../../app/types";

// ============================================================================
// AC16: OperationalStateBanner renders correct state
// ============================================================================

describe("OperationalStateBanner", () => {
  it("AC16: coverage_pct=100, response_state=live -> green (operational)", () => {
    const { container } = render(
      <OperationalStateBanner
        coveragePct={100}
        responseState="live"
        ultimaAtualizacao={new Date().toISOString()}
      />
    );

    const banner = container.querySelector("[role='status']");
    expect(banner).toBeTruthy();
    expect(banner?.className).toContain("bg-green-50");
    expect(screen.getByText(/Cobertura completa/)).toBeInTheDocument();
  });

  it("AC16: coverage_pct=78, response_state=live -> amber (partial)", () => {
    const ufs: UfStatusDetailItem[] = [
      { uf: "SP", status: "ok", results_count: 20 },
      { uf: "RJ", status: "ok", results_count: 15 },
      { uf: "BA", status: "timeout", results_count: 0 },
    ];

    const { container } = render(
      <OperationalStateBanner
        coveragePct={78}
        responseState="live"
        ufsStatusDetail={ufs}
        ultimaAtualizacao={new Date().toISOString()}
      />
    );

    const banner = container.querySelector("[role='status']");
    expect(banner?.className).toContain("bg-amber-50");
    expect(screen.getAllByText(/78% de cobertura/).length).toBeGreaterThanOrEqual(1);
  });

  it("AC16: response_state=cached -> amber/orange (degraded)", () => {
    const { container } = render(
      <OperationalStateBanner
        coveragePct={100}
        responseState="cached"
        cachedAt={new Date(Date.now() - 7200000).toISOString()}
        cacheStatus="stale"
      />
    );

    const banner = container.querySelector("[role='status']");
    expect(banner?.className).toContain("bg-orange-50");
    expect(screen.getByText(/Dados de cache/)).toBeInTheDocument();
  });

  it("AC16: response_state=empty_failure -> red (unavailable)", () => {
    const { container } = render(
      <OperationalStateBanner
        coveragePct={0}
        responseState="empty_failure"
      />
    );

    const banner = container.querySelector("[role='status']");
    expect(banner?.className).toContain("bg-red-50");
    expect(screen.getByText(/Fontes indisponíveis/)).toBeInTheDocument();
  });

  it("shows ReliabilityBadge", () => {
    render(
      <OperationalStateBanner
        coveragePct={100}
        responseState="live"
        ultimaAtualizacao={new Date().toISOString()}
      />
    );

    expect(screen.getByText("Alta")).toBeInTheDocument();
  });

  it("shows FreshnessIndicator when timestamp provided", () => {
    render(
      <OperationalStateBanner
        coveragePct={100}
        responseState="live"
        ultimaAtualizacao={new Date().toISOString()}
      />
    );

    expect(screen.getByText("agora")).toBeInTheDocument();
  });
});

// ============================================================================
// AC17: CoverageBar renders segments
// ============================================================================

describe("CoverageBar", () => {
  it("AC17: 5 OK + 2 error -> 7 segments, text '71% de cobertura'", () => {
    const ufs: UfStatusDetailItem[] = [
      { uf: "SP", status: "ok", results_count: 20 },
      { uf: "RJ", status: "ok", results_count: 15 },
      { uf: "MG", status: "ok", results_count: 10 },
      { uf: "RS", status: "ok", results_count: 8 },
      { uf: "PR", status: "ok", results_count: 5 },
      { uf: "BA", status: "error", results_count: 0 },
      { uf: "CE", status: "timeout", results_count: 0 },
    ];

    const { container } = render(
      <CoverageBar coveragePct={71} ufsStatusDetail={ufs} />
    );

    // 7 segments total
    const segments = container.querySelectorAll("[role='img']");
    expect(segments).toHaveLength(7);

    // 5 green segments (OK)
    const greenSegments = container.querySelectorAll(".bg-green-500");
    expect(greenSegments).toHaveLength(5);

    // 2 gray segments (failed)
    const graySegments = container.querySelectorAll(".bg-gray-300");
    expect(graySegments).toHaveLength(2);

    // Coverage text
    expect(screen.getByText(/71% de cobertura/)).toBeInTheDocument();
    expect(screen.getByText(/5 de 7 estados processados/)).toBeInTheDocument();
  });

  it("renders tooltip with UF name and status", () => {
    const ufs: UfStatusDetailItem[] = [
      { uf: "SP", status: "ok", results_count: 45 },
      { uf: "BA", status: "timeout", results_count: 0 },
    ];

    const { container } = render(
      <CoverageBar coveragePct={50} ufsStatusDetail={ufs} />
    );

    const spSegment = container.querySelector("[title='SP: OK (45 resultados)']");
    expect(spSegment).toBeTruthy();

    const baSegment = container.querySelector("[title='BA: Timeout']");
    expect(baSegment).toBeTruthy();
  });

  it("all UFs OK -> all segments green", () => {
    const ufs: UfStatusDetailItem[] = [
      { uf: "SP", status: "ok", results_count: 20 },
      { uf: "RJ", status: "ok", results_count: 15 },
    ];

    const { container } = render(
      <CoverageBar coveragePct={100} ufsStatusDetail={ufs} />
    );

    const greenSegments = container.querySelectorAll(".bg-green-500");
    expect(greenSegments).toHaveLength(2);

    const graySegments = container.querySelectorAll(".bg-gray-300");
    expect(graySegments).toHaveLength(0);
  });
});
