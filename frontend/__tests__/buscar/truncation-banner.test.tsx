/**
 * GTM-FIX-004 AC9: Tests for TruncationWarningBanner component.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { TruncationWarningBanner } from "../../app/buscar/components/TruncationWarningBanner";

describe("TruncationWarningBanner", () => {
  it("renders the truncation warning title", () => {
    render(<TruncationWarningBanner />);
    expect(screen.getByText("Resultados truncados")).toBeInTheDocument();
  });

  it("shows generic message when no truncated UFs provided", () => {
    render(<TruncationWarningBanner />);
    expect(
      screen.getByText(/mais de 250\.000 registros do PNCP/)
    ).toBeInTheDocument();
  });

  it("shows specific UFs when truncated_ufs is provided", () => {
    render(<TruncationWarningBanner truncatedUfs={["SP", "RJ"]} />);
    expect(
      screen.getByText(/mais registros do que o limite para SP, RJ/)
    ).toBeInTheDocument();
  });

  it("includes actionable guidance about refining filters", () => {
    render(<TruncationWarningBanner />);
    expect(
      screen.getByText(/refine os filtros/)
    ).toBeInTheDocument();
  });

  it("shows single UF when only one is truncated", () => {
    render(<TruncationWarningBanner truncatedUfs={["MG"]} />);
    expect(
      screen.getByText(/mais registros do que o limite para MG/)
    ).toBeInTheDocument();
  });

  it("shows generic message for empty truncated UFs array", () => {
    render(<TruncationWarningBanner truncatedUfs={[]} />);
    expect(
      screen.getByText(/mais de 250\.000 registros do PNCP/)
    ).toBeInTheDocument();
  });

  it("has the alert icon with proper aria label", () => {
    render(<TruncationWarningBanner />);
    expect(screen.getByRole("img", { name: "Alerta" })).toBeInTheDocument();
  });

  it("applies yellow warning styling classes", () => {
    const { container } = render(<TruncationWarningBanner />);
    const banner = container.firstChild as HTMLElement;
    expect(banner.className).toContain("bg-yellow-50");
    expect(banner.className).toContain("border-yellow-200");
  });
});
