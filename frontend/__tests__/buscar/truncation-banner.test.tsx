/**
 * GTM-FIX-004 AC9: Tests for TruncationWarningBanner component.
 *
 * Covers both legacy (UF-only) and revised (per-source truncation_details) modes.
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

  // =========================================================================
  // AC2r / AC6r: Per-source truncation details
  // =========================================================================

  describe("per-source truncation details", () => {
    it("shows PNCP-only truncation when only PNCP is truncated", () => {
      render(
        <TruncationWarningBanner
          truncationDetails={{ pncp: true, portal_compras: false }}
        />
      );
      expect(
        screen.getByText(/Resultados do PNCP atingiram o limite/)
      ).toBeInTheDocument();
    });

    it("shows PNCP truncation with UFs when both provided", () => {
      render(
        <TruncationWarningBanner
          truncatedUfs={["SP", "RJ"]}
          truncationDetails={{ pncp: true }}
        />
      );
      expect(
        screen.getByText(/Resultados do PNCP truncados para SP, RJ/)
      ).toBeInTheDocument();
    });

    it("shows Portal de Compras truncation when only PCP is truncated", () => {
      render(
        <TruncationWarningBanner
          truncationDetails={{ pncp: false, portal_compras: true }}
        />
      );
      expect(
        screen.getByText(/Resultados do Portal de Compras Publicas atingiram o limite/)
      ).toBeInTheDocument();
    });

    it("shows both sources when both are truncated", () => {
      render(
        <TruncationWarningBanner
          truncationDetails={{ pncp: true, portal_compras: true }}
        />
      );
      expect(
        screen.getByText(/Resultados truncados em PNCP e Portal de Compras Publicas/)
      ).toBeInTheDocument();
    });

    it("falls back to UF-based message when truncation_details has no true values", () => {
      render(
        <TruncationWarningBanner
          truncatedUfs={["SP"]}
          truncationDetails={{ pncp: false }}
        />
      );
      expect(
        screen.getByText(/mais registros do que o limite para SP/)
      ).toBeInTheDocument();
    });

    it("falls back to generic message when truncation_details is empty", () => {
      render(
        <TruncationWarningBanner
          truncationDetails={{}}
        />
      );
      expect(
        screen.getByText(/mais de 250\.000 registros do PNCP/)
      ).toBeInTheDocument();
    });
  });
});
