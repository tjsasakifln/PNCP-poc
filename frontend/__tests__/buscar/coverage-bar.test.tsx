/**
 * GTM-RESILIENCE-C03 AC11: CoverageBar component tests
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { CoverageBar } from "../../app/buscar/components/CoverageBar";
import type { CoverageMetadata } from "../../app/types";

function makeMeta(overrides: Partial<CoverageMetadata> = {}): CoverageMetadata {
  return {
    ufs_requested: ["SP", "RJ", "MG"],
    ufs_processed: ["SP", "RJ", "MG"],
    ufs_failed: [],
    coverage_pct: 100.0,
    data_timestamp: new Date().toISOString(),
    freshness: "live",
    ...overrides,
  };
}

describe("CoverageBar", () => {
  it("renders with 100% coverage (green)", () => {
    render(<CoverageBar coverageMetadata={makeMeta({ coverage_pct: 100.0 })} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "100");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
    expect(screen.getByText(/100\.0%/)).toBeInTheDocument();
  });

  it("renders with 78% coverage (amber/yellow)", () => {
    const meta = makeMeta({
      ufs_requested: ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE"],
      ufs_processed: ["SP", "RJ", "MG", "PR", "SC", "RS", "BA"],
      ufs_failed: ["PE", "CE"],
      coverage_pct: 77.8,
    });
    render(<CoverageBar coverageMetadata={meta} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "78");
    expect(screen.getByText(/77\.8%/)).toBeInTheDocument();
    expect(screen.getByText(/7 de 9 UFs/)).toBeInTheDocument();
  });

  it("renders with 50% coverage (red)", () => {
    const meta = makeMeta({
      ufs_requested: ["SP", "RJ", "MG", "BA"],
      ufs_processed: ["SP", "RJ"],
      ufs_failed: ["MG", "BA"],
      coverage_pct: 50.0,
    });
    render(<CoverageBar coverageMetadata={meta} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "50");
    expect(screen.getByText(/50\.0%/)).toBeInTheDocument();
  });

  it("shows UF breakdown on click", () => {
    const meta = makeMeta({
      ufs_requested: ["SP", "RJ", "MG"],
      ufs_processed: ["SP", "RJ"],
      ufs_failed: ["MG"],
      coverage_pct: 66.7,
    });
    render(<CoverageBar coverageMetadata={meta} />);

    // Panel should not be visible initially
    expect(screen.queryByText("Processadas (2)")).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByTestId("coverage-bar").querySelector("button")!);

    // Panel should now be visible
    expect(screen.getByText("Processadas (2)")).toBeInTheDocument();
    expect(screen.getByText("Falharam (1)")).toBeInTheDocument();
  });

  it("closes UF breakdown on Escape", () => {
    const meta = makeMeta({
      ufs_processed: ["SP"],
      ufs_failed: ["RJ", "MG"],
      coverage_pct: 33.3,
    });
    render(<CoverageBar coverageMetadata={meta} />);

    // Open panel
    fireEvent.click(screen.getByTestId("coverage-bar").querySelector("button")!);
    expect(screen.getByText(/Falharam/)).toBeInTheDocument();

    // Press Escape
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByText(/Falharam/)).not.toBeInTheDocument();
  });

  it("has correct aria-label on progressbar", () => {
    const meta = makeMeta({
      ufs_requested: ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE"],
      ufs_processed: ["SP", "RJ", "MG", "PR", "SC", "RS", "BA"],
      ufs_failed: ["PE", "CE"],
      coverage_pct: 77.8,
    });
    render(<CoverageBar coverageMetadata={meta} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute(
      "aria-label",
      expect.stringContaining("7 de 9 estados processados")
    );
    expect(bar).toHaveAttribute(
      "aria-label",
      expect.stringContaining("78 por cento")
    );
  });
});
