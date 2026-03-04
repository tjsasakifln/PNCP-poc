/**
 * STORY-300 AC9: LGPD Privacy Page Tests
 *
 * Verifies that the privacy page includes all required LGPD elements:
 * - Legal basis for each data processing type (Art. 7)
 * - Explicit data collection listing
 * - Retention periods per category
 * - Data subject rights (Art. 18)
 * - DPO contact information
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import PrivacidadePage from "../app/privacidade/page";

describe("STORY-300 AC9: LGPD Privacy Page", () => {
  beforeEach(() => {
    render(<PrivacidadePage />);
  });

  describe("Legal Basis (Art. 7 LGPD)", () => {
    it("should mention Art. 7 LGPD as legal basis reference", () => {
      const allText = document.body.textContent || "";
      expect(allText).toContain("Art. 7");
    });

    it("should include execution of contract as legal basis", () => {
      const cells = screen.getAllByText(/Execucao de contrato/i);
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });

    it("should include consent as legal basis for analytics", () => {
      const cells = screen.getAllByText(/Consentimento/i);
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });

    it("should include legitimate interest as legal basis", () => {
      const cells = screen.getAllByText(/Interesse legitimo/i);
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Data Collection (explicit listing)", () => {
    it("should list email and name as collected data", () => {
      expect(screen.getByText(/Nome e e-mail/)).toBeInTheDocument();
    });

    it("should list CNPJ/CPF as collected data", () => {
      expect(screen.getByText(/CNPJ\/CPF/)).toBeInTheDocument();
    });

    it("should list search history as collected data", () => {
      expect(screen.getByText(/Historico de análises/)).toBeInTheDocument();
    });

    it("should list payment data", () => {
      const matches = screen.getAllByText(/Dados de pagamento/);
      expect(matches.length).toBeGreaterThanOrEqual(1);
    });

    it("should list IP and browser data", () => {
      expect(screen.getByText(/IP, navegador, SO/)).toBeInTheDocument();
    });

    it("should list Mixpanel usage data", () => {
      expect(screen.getByText(/Dados de uso \(Mixpanel\)/)).toBeInTheDocument();
    });
  });

  describe("Retention Periods", () => {
    it("should specify retention for account data", () => {
      const cells = screen.getAllByText(/Duracao da conta \+ 6 meses/);
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });

    it("should specify retention for search history (12 months)", () => {
      // Multiple elements may contain "12 meses"
      const allText = document.body.textContent || "";
      expect(allText).toContain("12 meses");
    });

    it("should specify retention for fiscal data (5 years)", () => {
      const allText = document.body.textContent || "";
      expect(allText).toContain("5 anos");
    });

    it("should specify retention for security logs (90 days)", () => {
      const cells = screen.getAllByText(/90 dias/);
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Data Subject Rights (Art. 18 LGPD)", () => {
    it("should mention Art. 18 LGPD", () => {
      expect(screen.getByText(/Art\. 18/)).toBeInTheDocument();
    });

    it("should list right to access (I)", () => {
      expect(screen.getByText(/I - Confirmacao e Acesso/)).toBeInTheDocument();
    });

    it("should list right to correction (II)", () => {
      expect(screen.getByText(/II - Correcao/)).toBeInTheDocument();
    });

    it("should list right to portability (IV)", () => {
      expect(screen.getByText(/IV - Portabilidade/)).toBeInTheDocument();
    });

    it("should list right to elimination (V)", () => {
      expect(screen.getByText(/V - Eliminacao/)).toBeInTheDocument();
    });

    it("should list right to revoke consent (VII)", () => {
      expect(screen.getByText(/VII - Revogacao de Consentimento/)).toBeInTheDocument();
    });

    it("should mention self-service options in /conta", () => {
      const links = screen.getAllByRole("link", { name: /Minha Conta/i });
      expect(links.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("DPO Contact", () => {
    it("should include DPO name", () => {
      const matches = screen.getAllByText(/Tiago Sasaki/);
      expect(matches.length).toBeGreaterThanOrEqual(1);
    });

    it("should include DPO email", () => {
      const links = screen.getAllByRole("link", {
        name: /privacidade@smartlic\.tech/,
      });
      expect(links.length).toBeGreaterThanOrEqual(1);
    });

    it("should include ANPD reference", () => {
      const allText = document.body.textContent || "";
      expect(allText).toContain("ANPD");
    });

    it("should include response deadline", () => {
      const allText = document.body.textContent || "";
      expect(allText).toContain("15 dias uteis");
    });
  });

  describe("Data Sharing", () => {
    it("should explicitly state data is not sold", () => {
      expect(screen.getByText(/NAO vendemos/)).toBeInTheDocument();
    });

    it("should list all data processors", () => {
      const allText = document.body.textContent || "";
      expect(allText).toContain("Supabase");
      expect(allText).toContain("Railway");
      expect(allText).toContain("OpenAI");
      expect(allText).toContain("Stripe");
      expect(allText).toContain("Mixpanel");
      expect(allText).toContain("Sentry");
    });
  });

  describe("Cookie Policy", () => {
    it("should list essential cookies", () => {
      expect(screen.getByText(/Essenciais/)).toBeInTheDocument();
    });

    it("should list functional cookies", () => {
      expect(screen.getByText(/Funcionais/)).toBeInTheDocument();
    });

    it("should list analytical cookies with consent requirement", () => {
      expect(screen.getByText(/Analiticos/)).toBeInTheDocument();
    });
  });
});
