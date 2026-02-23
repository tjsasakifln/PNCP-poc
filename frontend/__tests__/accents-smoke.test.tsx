/**
 * GTM-FIX-034 AC6: Smoke test for Portuguese accents
 *
 * Validates that user-facing labels contain correct Portuguese accents.
 * Prevents regression of systematically missing diacritical marks.
 */

import { render, screen } from "@testing-library/react";
import { ModalidadeFilter, MODALIDADES } from "@/components/ModalidadeFilter";
import { StatusFilter } from "@/components/StatusFilter";
import { getUserFriendlyError } from "@/lib/error-messages";
import * as fs from "fs";

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

  // UX-355 AC1+AC5: Error message accent verification
  describe("UX-355: Error message and label accents", () => {
    it("useSearch fallback error should contain accented 'licitações'", () => {
      const src = fs.readFileSync(
        require.resolve("../app/buscar/hooks/useSearch.ts"),
        "utf-8"
      );
      expect(src).toContain("Erro ao buscar licitações");
      expect(src).not.toMatch(/Erro ao buscar licitacoes/);
    });

    it("SearchResults should use accented 'licitações' in user-facing text", () => {
      const src = fs.readFileSync(
        require.resolve("../app/buscar/components/SearchResults.tsx"),
        "utf-8"
      );
      expect(src).toContain("Licitações abertas");
      expect(src).not.toMatch(/Licitacoes abertas/);
      expect(src).toContain("licitações adicionais");
      expect(src).not.toMatch(/licitacoes adicionais/);
    });

    it("error-messages mapping should match accented 'Erro ao buscar licitações'", () => {
      const result = getUserFriendlyError("Erro ao buscar licitações");
      expect(result).toBeTruthy();
      expect(result).not.toBe("Erro ao buscar licitações"); // Should be mapped, not passthrough
    });
  });

  // UX-355 AC2+AC5: Suporte label consistency
  describe("UX-355: Suporte label consistency", () => {
    it("mensagens page should use 'Suporte' title, not 'Mensagens'", () => {
      const src = fs.readFileSync(
        require.resolve("../app/mensagens/page.tsx"),
        "utf-8"
      );
      expect(src).toMatch(/title="Suporte"/);
      expect(src).not.toMatch(/title="Mensagens"/);
    });

    it("MessageBadge should use 'Suporte' title", () => {
      const src = fs.readFileSync(
        require.resolve("../app/components/MessageBadge.tsx"),
        "utf-8"
      );
      expect(src).toMatch(/title="Suporte"/);
      expect(src).not.toMatch(/title="Mensagens"/);
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
