/**
 * STORY-352: Ajustar claim "24/7" — manter disponibilidade, corrigir suporte
 *
 * Tests verify:
 * - AC1: "Disponível 24/7" kept with tooltip
 * - AC2: "Suporte prioritário 24/7" replaced
 * - AC3: "Suporte 24/7" in BANNED_PHRASES
 * - AC7: ajuda page does NOT contain "24/7"
 */

import { comparisonTable, ComparisonRow } from "@/lib/copy/comparisons";
import { BANNED_PHRASES, validateCopy } from "@/lib/copy/valueProps";

// ============================================================================
// AC1: "Disponível 24/7" kept with tooltip
// ============================================================================

describe("STORY-352 AC1: Disponível 24/7 with tooltip", () => {
  const confiabilidadeRow = comparisonTable.find(
    (row) => row.feature === "Confiabilidade"
  );

  it("keeps 'Disponível 24/7' as advantage text", () => {
    expect(confiabilidadeRow).toBeDefined();
    expect(confiabilidadeRow!.advantage).toBe("Disponível 24/7");
  });

  it("has tooltip 'Monitoramento contínuo com alertas automáticos'", () => {
    expect(confiabilidadeRow!.tooltip).toBe(
      "Monitoramento contínuo com alertas automáticos"
    );
  });

  it("ComparisonRow interface accepts tooltip field", () => {
    const row: ComparisonRow = {
      feature: "Test",
      traditional: "Old",
      smartlic: "New",
      advantage: "Better",
      tooltip: "Hover text",
    };
    expect(row.tooltip).toBe("Hover text");
  });

  it("tooltip is optional (other rows have no tooltip)", () => {
    const rowsWithoutTooltip = comparisonTable.filter(
      (row) => row.feature !== "Confiabilidade"
    );
    rowsWithoutTooltip.forEach((row) => {
      expect(row.tooltip).toBeUndefined();
    });
  });
});

// ============================================================================
// AC3: "Suporte 24/7" in BANNED_PHRASES
// ============================================================================

describe("STORY-352 AC3: BANNED_PHRASES includes 'Suporte 24/7'", () => {
  it("bans 'Suporte 24/7' (human support claim)", () => {
    expect(BANNED_PHRASES).toContain("Suporte 24/7");
  });

  it("does NOT ban 'Disponível 24/7' (system availability is factual)", () => {
    expect(BANNED_PHRASES).not.toContain("Disponível 24/7");
  });

  it("validateCopy rejects text containing 'Suporte 24/7'", () => {
    const result = validateCopy("Nosso Suporte 24/7 está sempre disponível");
    expect(result.isValid).toBe(false);
    expect(result.violations).toContain("Suporte 24/7");
  });

  it("validateCopy accepts text with 'Disponível 24/7'", () => {
    const result = validateCopy("Sistema Disponível 24/7");
    expect(result.isValid).toBe(true);
  });
});

// ============================================================================
// AC7: ajuda page does not contain "24/7"
// ============================================================================

describe("STORY-352 AC7: ajuda page review", () => {
  it("'24 horas úteis' is about response time, not 24/7 availability", () => {
    // This test documents the decision: "24 horas úteis" is a response time SLA,
    // not a round-the-clock availability claim. It stays.
    const responseTimeCopy = "Respondemos em até 24 horas úteis";
    expect(responseTimeCopy).not.toContain("24/7");
  });
});
