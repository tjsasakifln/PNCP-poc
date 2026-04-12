/**
 * GTM-FIX-034 AC6: Smoke test for Portuguese accents
 *
 * Validates that user-facing labels contain correct Portuguese accents.
 * Prevents regression of systematically missing diacritical marks.
 */

import { render, screen } from "@testing-library/react";
import { ModalidadeFilter, MODALIDADES } from "@/app/buscar/components/ModalidadeFilter";
import { StatusFilter } from "@/app/buscar/components/StatusFilter";
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
        require.resolve("../app/buscar/hooks/execution/useSearchAPI.ts"),
        "utf-8"
      );
      expect(src).toContain("Erro ao buscar licitações");
      expect(src).not.toMatch(/Erro ao buscar licitacoes/);
    });

    it("SearchResults should use accented 'licitações' in user-facing text", () => {
      // TD-007: SearchResults decomposed — check orchestrator + sub-components
      // DEBT-204: Banner content moved to SearchResultsBanners
      const orchestrator = fs.readFileSync(
        require.resolve("../app/buscar/components/SearchResults.tsx"),
        "utf-8"
      );
      const filters = fs.readFileSync(
        require.resolve("../app/buscar/components/search-results/ResultsFilters.tsx"),
        "utf-8"
      );
      const banners = fs.readFileSync(
        require.resolve("../app/buscar/components/SearchResultsBanners.tsx"),
        "utf-8"
      );
      const combined = orchestrator + filters + banners;
      expect(combined).toContain("Licitações abertas");
      expect(combined).not.toMatch(/Licitacoes abertas/);
      expect(combined).toContain("licitações adicionais");
      expect(combined).not.toMatch(/licitacoes adicionais/);
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

  // SAB-002 AC9: Detect \u00 unicode escapes in hardcoded frontend strings
  describe("SAB-002: No \\u00 unicode escapes in frontend source files", () => {
    // Files that previously had \u00 escapes rendered as literal text
    const filesToCheck = [
      { path: "../app/historico/page.tsx", name: "historico/page.tsx" },
      { path: "../app/pipeline/page.tsx", name: "pipeline/page.tsx" },
      { path: "../app/alertas/page.tsx", name: "alertas/page.tsx" },
      { path: "../app/dashboard/page.tsx", name: "dashboard/page.tsx" },
      { path: "../app/ajuda/page.tsx", name: "ajuda/page.tsx" },
      { path: "../components/BottomNav.tsx", name: "BottomNav.tsx" },
      { path: "../components/Sidebar.tsx", name: "Sidebar.tsx" },
      { path: "../app/buscar/components/SearchResults.tsx", name: "SearchResults.tsx" },
    ];

    // Match \u00XX patterns that are NOT inside comments (// or /* */)
    // This regex finds literal backslash-u-00-hex-hex sequences in source
    const unicodeEscapePattern = /\\u00[0-9a-fA-F]{2}/;

    filesToCheck.forEach(({ path, name }) => {
      it(`${name} should not contain \\u00 unicode escape sequences`, () => {
        const src = fs.readFileSync(require.resolve(path), "utf-8");
        // Strip single-line comments to avoid false positives from comment references
        const withoutComments = src.replace(/\/\/.*$/gm, "").replace(/\/\*[\s\S]*?\*\//g, "");
        const matches = withoutComments.match(/\\u00[0-9a-fA-F]{2}/g);
        expect(matches).toBeNull();
      });
    });

    it("historico header should display 'Histórico' with accent", () => {
      const src = fs.readFileSync(
        require.resolve("../app/historico/page.tsx"),
        "utf-8"
      );
      expect(src).toContain('title="Histórico"');
    });

    it("pipeline subtitle should use 'licitações' with cedilla", () => {
      const src = fs.readFileSync(
        require.resolve("../app/pipeline/page.tsx"),
        "utf-8"
      );
      expect(src).toContain("licitações entre os estágios");
    });

    it("alertas subtitle should use 'notificações automáticas'", () => {
      const src = fs.readFileSync(
        require.resolve("../app/alertas/components/AlertsPageHeader.tsx"),
        "utf-8"
      );
      expect(src).toContain("notificações automáticas sobre novas licitações");
    });
  });
});
