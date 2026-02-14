/**
 * STORY-241 AC7/AC8/AC9: ModalidadeFilter component tests.
 *
 * Verifies:
 * - Competitive modalities (4, 5, 6, 7) are present and marked popular
 * - Inexigibilidade (9) and Inaplicabilidade (14) are not selectable
 * - All MODALIDADES use real PNCP API codes
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ModalidadeFilter, MODALIDADES } from "../components/ModalidadeFilter";

describe("ModalidadeFilter — STORY-241", () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  // ========================================================================
  // AC7: Competitive modalities present and popular
  // ========================================================================
  describe("AC7: Competitive modalities", () => {
    it("includes Concorrencia Eletronica (code 4)", () => {
      const m = MODALIDADES.find((m) => m.codigo === 4);
      expect(m).toBeDefined();
      expect(m!.nome).toContain("Concorrencia Eletronica");
    });

    it("includes Concorrencia Presencial (code 5)", () => {
      const m = MODALIDADES.find((m) => m.codigo === 5);
      expect(m).toBeDefined();
      expect(m!.nome).toContain("Concorrencia Presencial");
    });

    it("includes Pregao Eletronico (code 6)", () => {
      const m = MODALIDADES.find((m) => m.codigo === 6);
      expect(m).toBeDefined();
      expect(m!.nome).toContain("Pregao Eletronico");
    });

    it("includes Pregao Presencial (code 7)", () => {
      const m = MODALIDADES.find((m) => m.codigo === 7);
      expect(m).toBeDefined();
      expect(m!.nome).toContain("Pregao Presencial");
    });

    it("marks all four competitive modalities as popular", () => {
      const popularCodes = MODALIDADES.filter((m) => m.popular).map(
        (m) => m.codigo
      );
      expect(popularCodes).toEqual(expect.arrayContaining([4, 5, 6, 7]));
      expect(popularCodes.length).toBe(4);
    });
  });

  // ========================================================================
  // AC8: Excluded modalities not selectable
  // ========================================================================
  describe("AC8: Excluded modalities", () => {
    it("does NOT include Inexigibilidade (code 9)", () => {
      const m = MODALIDADES.find((m) => m.codigo === 9);
      expect(m).toBeUndefined();
    });

    it("does NOT include Inaplicabilidade (code 14)", () => {
      const m = MODALIDADES.find((m) => m.codigo === 14);
      expect(m).toBeUndefined();
    });

    it("does NOT contain any modality named Inexigibilidade", () => {
      const m = MODALIDADES.find((m) =>
        m.nome.toLowerCase().includes("inexigibilidade")
      );
      expect(m).toBeUndefined();
    });
  });

  // ========================================================================
  // AC9: Component rendering and interaction
  // ========================================================================
  describe("AC9: Component behavior", () => {
    it("renders popular modalities always visible", () => {
      render(
        <ModalidadeFilter value={[]} onChange={mockOnChange} />
      );

      expect(screen.getByText("Concorrencia Eletronica")).toBeInTheDocument();
      expect(screen.getByText("Concorrencia Presencial")).toBeInTheDocument();
      expect(screen.getByText("Pregao Eletronico")).toBeInTheDocument();
      expect(screen.getByText("Pregao Presencial")).toBeInTheDocument();
    });

    it("does not render Inexigibilidade in UI", () => {
      render(
        <ModalidadeFilter value={[]} onChange={mockOnChange} />
      );

      expect(screen.queryByText("Inexigibilidade")).not.toBeInTheDocument();
    });

    it("calls onChange when a modality is toggled", () => {
      render(
        <ModalidadeFilter value={[]} onChange={mockOnChange} />
      );

      fireEvent.click(screen.getByText("Pregao Eletronico"));
      expect(mockOnChange).toHaveBeenCalledWith([6]);
    });

    it("selects all 9 modalities when Todas is clicked", () => {
      render(
        <ModalidadeFilter value={[]} onChange={mockOnChange} />
      );

      fireEvent.click(screen.getByText("Todas"));
      const selectedCodes = mockOnChange.mock.calls[0][0];
      expect(selectedCodes).toHaveLength(9);
      expect(selectedCodes).not.toContain(9); // no Inexigibilidade
      expect(selectedCodes).not.toContain(14); // no Inaplicabilidade
    });

    it("uses real PNCP API codes (not old Lei 8.666 codes)", () => {
      const allCodes = MODALIDADES.map((m) => m.codigo);
      // Old codes that should NOT exist:
      // Old code 1 was Pregão Eletrônico (now 6)
      // Old code 2 was Pregão Presencial (now 7)
      // Verify new codes 4 and 5 are present (Concorrência)
      expect(allCodes).toContain(4);
      expect(allCodes).toContain(5);
      // Verify Pregão uses new codes
      expect(MODALIDADES.find((m) => m.codigo === 6)?.nome).toContain("Pregao");
      expect(MODALIDADES.find((m) => m.codigo === 7)?.nome).toContain("Pregao");
    });
  });
});
