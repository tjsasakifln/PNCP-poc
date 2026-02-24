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
    expect(screen.getByText(/Resultados salvos/)).toBeInTheDocument();
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

    // FreshnessIndicator renders "Dados de agora" for fresh live data
    expect(screen.getByText(/Dados de agora|agora/)).toBeInTheDocument();
  });
});

// ============================================================================
// AC17: CoverageBar renders progress bar
// ============================================================================

import type { CoverageMetadata } from "../../app/types";

describe("CoverageBar", () => {
  it("AC17: 5 OK + 2 failed -> renders coverage bar with progress", () => {
    const coverageMetadata: CoverageMetadata = {
      ufs_requested: ["SP", "RJ", "MG", "RS", "PR", "BA", "CE"],
      ufs_processed: ["SP", "RJ", "MG", "RS", "PR"],
      ufs_failed: ["BA", "CE"],
      coverage_pct: 71.4,
      data_timestamp: new Date().toISOString(),
      freshness: "live",
    };

    const { container } = render(
      <CoverageBar coverageMetadata={coverageMetadata} />
    );

    // Progress bar renders
    const progressBar = container.querySelector("[role='progressbar']");
    expect(progressBar).toBeTruthy();

    // Coverage text label
    expect(screen.getByText(/Cobertura:.*5 de 7 UFs/)).toBeInTheDocument();
  });

  it("renders with 2 UFs, shows processed and failed", () => {
    const coverageMetadata: CoverageMetadata = {
      ufs_requested: ["SP", "BA"],
      ufs_processed: ["SP"],
      ufs_failed: ["BA"],
      coverage_pct: 50,
      data_timestamp: new Date().toISOString(),
      freshness: "live",
    };

    const { container } = render(
      <CoverageBar coverageMetadata={coverageMetadata} />
    );

    // Progress bar renders with the correct percentage
    const progressBar = container.querySelector("[role='progressbar']");
    expect(progressBar).toBeTruthy();
    expect(progressBar?.getAttribute("aria-valuenow")).toBe("50");
  });

  it("all UFs OK -> coverage bar shows 100%", () => {
    const coverageMetadata: CoverageMetadata = {
      ufs_requested: ["SP", "RJ"],
      ufs_processed: ["SP", "RJ"],
      ufs_failed: [],
      coverage_pct: 100,
      data_timestamp: new Date().toISOString(),
      freshness: "live",
    };

    const { container } = render(
      <CoverageBar coverageMetadata={coverageMetadata} />
    );

    // Progress bar at 100%
    const progressBar = container.querySelector("[role='progressbar']");
    expect(progressBar?.getAttribute("aria-valuenow")).toBe("100");

    // Bar fill should use green color for 100%
    const barFill = container.querySelector(".bg-green-500");
    expect(barFill).toBeTruthy();
  });
});
