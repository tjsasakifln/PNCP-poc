/**
 * GTM-RESILIENCE-D04: ViabilityBadge component tests.
 *
 * AC8: Visual indicators with 3 levels
 * AC11: Tooltip shows factor breakdown
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import ViabilityBadge from "../app/buscar/components/ViabilityBadge";
import type { ViabilityFactors } from "../app/buscar/components/ViabilityBadge";

const mockFactors: ViabilityFactors = {
  modalidade: 100,
  modalidade_label: "Ótimo",
  timeline: 80,
  timeline_label: "12 dias",
  value_fit: 100,
  value_fit_label: "Ideal",
  geography: 100,
  geography_label: "Sua região",
};

describe("ViabilityBadge", () => {
  // AC8: Three levels with correct labels
  it("renders 'Viabilidade alta' in green for alta level", () => {
    render(<ViabilityBadge level="alta" score={85} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("Viabilidade alta");
    expect(badge).toHaveAttribute("data-viability-level", "alta");
    // Green styling
    expect(badge.className).toContain("bg-emerald-100");
  });

  it("renders 'Viabilidade média' in yellow for media level", () => {
    render(<ViabilityBadge level="media" score={55} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge).toHaveTextContent("Viabilidade média");
    expect(badge).toHaveAttribute("data-viability-level", "media");
    expect(badge.className).toContain("bg-yellow-100");
  });

  it("renders 'Viabilidade baixa' in gray for baixa level", () => {
    render(<ViabilityBadge level="baixa" score={25} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge).toHaveTextContent("Viabilidade baixa");
    expect(badge).toHaveAttribute("data-viability-level", "baixa");
    expect(badge.className).toContain("bg-gray-100");
  });

  // AC8: Returns null when no level
  it("returns null when level is null", () => {
    const { container } = render(
      <ViabilityBadge level={null} score={null} factors={null} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("returns null when level is undefined", () => {
    const { container } = render(
      <ViabilityBadge level={undefined} score={undefined} factors={undefined} />
    );
    expect(container.firstChild).toBeNull();
  });

  // AC11: Tooltip with factor breakdown
  it("shows tooltip with factor breakdown", () => {
    render(<ViabilityBadge level="alta" score={95} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    const title = badge.getAttribute("title") || "";
    expect(title).toContain("Viabilidade: 95/100");
    expect(title).toContain("Modalidade: Ótimo (100/100)");
    expect(title).toContain("Prazo: 12 dias (80/100)");
    expect(title).toContain("Valor: Ideal (100/100)");
    expect(title).toContain("UF: Sua região (100/100)");
  });

  it("shows basic tooltip without factors", () => {
    render(<ViabilityBadge level="media" score={60} factors={null} />);
    const badge = screen.getByTestId("viability-badge");
    const title = badge.getAttribute("title") || "";
    expect(title).toContain("Viabilidade: 60/100");
    expect(title).not.toContain("Modalidade");
  });

  // Accessibility
  it("has correct aria-label for alta", () => {
    render(<ViabilityBadge level="alta" score={80} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge).toHaveAttribute(
      "aria-label",
      "Viabilidade alta para sua empresa"
    );
  });

  it("is keyboard-focusable", () => {
    render(<ViabilityBadge level="media" score={55} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge).toHaveAttribute("tabIndex", "0");
  });

  it("has role=img for semantic meaning", () => {
    render(<ViabilityBadge level="baixa" score={20} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge).toHaveAttribute("role", "img");
  });

  // Renders distinct icon (chart bar, not shield)
  it("contains an SVG icon", () => {
    render(<ViabilityBadge level="alta" score={80} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    const svg = badge.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  // Score display edge cases
  it("handles score of 0", () => {
    render(<ViabilityBadge level="baixa" score={0} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge.getAttribute("title")).toContain("Viabilidade: 0/100");
  });

  it("handles score of 100", () => {
    render(<ViabilityBadge level="alta" score={100} factors={mockFactors} />);
    const badge = screen.getByTestId("viability-badge");
    expect(badge.getAttribute("title")).toContain("Viabilidade: 100/100");
  });
});
