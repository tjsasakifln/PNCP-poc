/**
 * COPY-377: Reescrever empty state de zero resultados
 * Tests for OnboardingEmptyState copy changes (AC1-AC5)
 *
 * OnboardingEmptyState is not exported from page.tsx, so we verify
 * the source file contains the correct copy strings. This is the
 * standard pattern for copy validation in non-exported components.
 */

import * as fs from "fs";
import * as path from "path";

describe("COPY-377: OnboardingEmptyState copy rewrite", () => {
  let source: string;

  beforeAll(() => {
    const filePath = path.resolve(
      __dirname,
      "../app/buscar/page.tsx"
    );
    source = fs.readFileSync(filePath, "utf-8");
  });

  // AC1: Headline change
  it('AC1: headline should be "Sua análise foi concluída"', () => {
    expect(source).toContain("Sua análise foi concluída");
    expect(source).not.toContain(
      "Nenhuma oportunidade encontrada para seu perfil"
    );
  });

  // AC2: Subtexto change
  it("AC2: subtexto should use empathetic copy with hope framing", () => {
    expect(source).toContain(
      "Não encontramos oportunidades compatíveis no período selecionado"
    );
    expect(source).toContain("pode mudar nos próximos dias");
    expect(source).not.toContain(
      "Não encontramos oportunidades recentes para o seu perfil"
    );
  });

  // AC3: Suggestions rewritten
  it("AC3: suggestions should use rewritten active copy", () => {
    expect(source).toContain("Incluir estados vizinhos");
    expect(source).toContain("Ampliar a faixa de valor estimado");
    expect(source).toContain("Estender o período para 15 ou 30 dias");
    expect(source).toContain("Para ampliar resultados, tente:");
  });

  it("AC3: old suggestion copy should not be present", () => {
    expect(source).not.toContain("Adicionar mais estados");
    expect(source).not.toContain("Sugestões para ampliar resultados:");
    // Note: "Ampliar a faixa de valor" is a substring of the new copy, so we check the exact old line
    expect(source).not.toMatch(/>\s*Ampliar a faixa de valor\s*</);
    expect(source).not.toContain("Expandir o período de análise");
  });

  // AC4: CTA change
  it('AC4: CTA should be "Refinar análise"', () => {
    expect(source).toContain("Refinar análise");
    expect(source).not.toContain("Ajustar Filtros");
  });
});
