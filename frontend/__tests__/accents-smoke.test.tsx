/**
 * GTM-FIX-034 AC6: Smoke test for Portuguese accents
 *
 * Validates that user-facing labels contain correct Portuguese accents.
 * Prevents regression of systematically missing diacritical marks.
 */

import { render, screen } from "@testing-library/react";
import { ModalidadeFilter, MODALIDADES } from "@/components/ModalidadeFilter";
import { StatusFilter } from "@/components/StatusFilter";

describe("GTM-FIX-034: Portuguese accents smoke test", () => {
  describe("ModalidadeFilter accents", () => {
    it("should have accented modalidade names", () => {
      const names = MODALIDADES.map((m) => m.nome);

      expect(names).toContain("Concorrência Eletrônica");
      expect(names).toContain("Concorrência Presencial");
      expect(names).toContain("Pregão Eletrônico");
      expect(names).toContain("Pregão Presencial");
      expect(names).toContain("Dispensa de Licitação");
      expect(names).toContain("Leilão Eletrônico");
      expect(names).toContain("Diálogo Competitivo");
    });

    it("should render 'Contratação' label with accent", () => {
      render(
        <ModalidadeFilter value={[]} onChange={() => {}} />
      );
      expect(screen.getByText(/Modalidade de Contratação/)).toBeInTheDocument();
    });

    it("should render 'opções' button with accent", () => {
      render(
        <ModalidadeFilter value={[]} onChange={() => {}} />
      );
      expect(screen.getByText(/opções/)).toBeInTheDocument();
    });
  });

  describe("StatusFilter accents", () => {
    it("should render 'Licitação' label with accent", () => {
      render(
        <StatusFilter value="recebendo_proposta" onChange={() => {}} />
      );
      expect(screen.getByText(/Status da Licitação/)).toBeInTheDocument();
    });

    it("should have accented aria-label", () => {
      render(
        <StatusFilter value="recebendo_proposta" onChange={() => {}} />
      );
      expect(screen.getByRole("radiogroup", { name: /licitação/i })).toBeInTheDocument();
    });

    it("should render accented helper text", () => {
      render(
        <StatusFilter value="recebendo_proposta" onChange={() => {}} />
      );
      expect(screen.getByText(/licitações que ainda aceitam propostas/)).toBeInTheDocument();
    });
  });

  describe("No unaccented Portuguese patterns in MODALIDADES data", () => {
    const allText = MODALIDADES.map((m) => `${m.nome} ${m.descricao}`).join(" ");

    const forbiddenPatterns = [
      { pattern: /\bLicitacao\b/, correct: "Licitação" },
      { pattern: /\bPregao\b/, correct: "Pregão" },
      { pattern: /\bConcorrencia\b/, correct: "Concorrência" },
      { pattern: /\bContratacao\b/, correct: "Contratação" },
      { pattern: /\bLeilao\b/, correct: "Leilão" },
      { pattern: /\bDialogo\b/, correct: "Diálogo" },
      { pattern: /\beletronico\b/i, correct: "eletrônico" },
      { pattern: /\blicitatorio\b/i, correct: "licitatório" },
      { pattern: /\bservicos\b/i, correct: "serviços" },
      { pattern: /\btecnico\b/i, correct: "técnico" },
      { pattern: /\bcientifico\b/i, correct: "científico" },
      { pattern: /\bartistico\b/i, correct: "artístico" },
    ];

    forbiddenPatterns.forEach(({ pattern, correct }) => {
      it(`should NOT contain unaccented "${pattern.source}" (should be "${correct}")`, () => {
        expect(allText).not.toMatch(pattern);
      });
    });
  });
});
