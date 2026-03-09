/**
 * SAB-010 — Conta: polish do perfil de licitante e acentos
 * DEBT-011 Updated: Tests PerfilPage (decomposed from monolithic ContaPage)
 *
 * AC1: Banner motivacional (40% viabilidade)
 * AC2: Botão "Preencher agora"
 * AC3: Progress bar colorida (red/yellow/green)
 * AC4-AC8: Correção de acentos específicos
 * AC9: Grep — sem palavras faltando acento
 * AC10-AC11: SKIPPED — Sticky nav moved to layout.tsx
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────────

jest.mock("../contexts/UserContext", () => ({
  useUser: () => ({
    user: { id: "u1", email: "test@test.com", user_metadata: { full_name: "Test" } },
    session: { access_token: "tok" },
    authLoading: false,
    isAdmin: false,
    sessionExpired: false,
    signOut: jest.fn(),
    planInfo: {
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      subscription_status: "active",
      quota_used: 5,
      capabilities: { max_requests_per_month: 1000 },
    },
    planLoading: false,
    planError: null,
    isFromCache: false,
    cachedAt: null,
    quota: null,
    quotaLoading: false,
    trial: { phase: "active", daysLeft: 14, isExpired: false, isExpiring: false, isNewUser: false },
    refresh: jest.fn(),
  }),
}));

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [k: string]: unknown }) => (
    <a href={href} {...rest}>{children}</a>
  ),
}));

// ─── Helpers ────────────────────────────────────────────────────────────────────

const EMPTY_PROFILE = {
  context_data: {
    ufs_atuacao: [],
    porte_empresa: "",
    experiencia_licitacoes: "",
    faixa_valor_min: null,
    faixa_valor_max: null,
    capacidade_funcionarios: null,
    faturamento_anual: null,
    atestados: [],
  },
};

const PARTIAL_PROFILE = {
  context_data: {
    ufs_atuacao: ["SP", "RJ"],
    porte_empresa: "me",
    experiencia_licitacoes: "basico",
    faixa_valor_min: null,
    faixa_valor_max: null,
    capacidade_funcionarios: null,
    faturamento_anual: null,
    atestados: [],
  },
};

const FULL_PROFILE = {
  context_data: {
    ufs_atuacao: ["SP"],
    porte_empresa: "me",
    experiencia_licitacoes: "intermediario",
    faixa_valor_min: 50000,
    faixa_valor_max: 500000,
    capacidade_funcionarios: 20,
    faturamento_anual: 1000000,
    atestados: ["crea"],
  },
};

function mockFetchResponses(profileData: Record<string, unknown> = EMPTY_PROFILE) {
  global.fetch = jest.fn().mockImplementation((url: string) => {
    if (url.includes("/api/profile-context")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(profileData) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  }) as jest.Mock;
}

// ─── Import component after mocks ───────────────────────────────────────────────

import PerfilPage from "../app/conta/perfil/page";

// ─── Tests ──────────────────────────────────────────────────────────────────────

describe("SAB-010: Conta page polish (DEBT-011 decomposed)", () => {

  beforeEach(() => {
    jest.clearAllMocks();
    Element.prototype.scrollIntoView = jest.fn();
  });

  // ────────────────── AC1: Motivational banner ──────────────────

  describe("AC1: Motivational banner", () => {
    it("shows banner with 40% viability message when profile is incomplete", async () => {
      mockFetchResponses(EMPTY_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("profile-guidance-banner")).toBeInTheDocument();
      });

      expect(screen.getByText(/melhora a precisão da análise de viabilidade em até 40%/)).toBeInTheDocument();
    });

    it("hides banner when profile is 100% complete", async () => {
      mockFetchResponses(FULL_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("profile-licitante-section")).toBeInTheDocument();
      });

      expect(screen.queryByTestId("profile-guidance-banner")).not.toBeInTheDocument();
    });
  });

  // ────────────────── AC2: "Preencher agora" button ──────────────────

  describe("AC2: Fill now button", () => {
    it("shows 'Preencher agora' button when profile is incomplete", async () => {
      mockFetchResponses(EMPTY_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("fill-now-btn")).toBeInTheDocument();
      });

      expect(screen.getByText("Preencher agora →")).toBeInTheDocument();
    });

    it("clicking 'Preencher agora' enters edit mode and scrolls", async () => {
      mockFetchResponses(EMPTY_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("fill-now-btn")).toBeInTheDocument();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("fill-now-btn"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("save-profile-btn")).toBeInTheDocument();
      });
    });
  });

  // ────────────────── AC3: Color progress bar ──────────────────

  describe("AC3: Color-coded progress bar", () => {
    it("shows red progress bar when 0% complete (0/7)", async () => {
      mockFetchResponses(EMPTY_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("profile-progress-bar")).toBeInTheDocument();
      });

      const bar = screen.getByTestId("profile-progress-bar");
      expect(bar).toHaveTextContent("0/7 campos");
      expect(bar).toHaveTextContent("0%");

      const innerBar = bar.querySelector(".bg-red-500");
      expect(innerBar).toBeInTheDocument();
    });

    it("shows yellow progress bar for partial completion (3/7 = 42%)", async () => {
      mockFetchResponses(PARTIAL_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("profile-progress-bar")).toBeInTheDocument();
      });

      const bar = screen.getByTestId("profile-progress-bar");
      expect(bar).toHaveTextContent("3/7 campos");
      expect(bar).toHaveTextContent("42%");

      const innerBar = bar.querySelector(".bg-yellow-500");
      expect(innerBar).toBeInTheDocument();
    });

    it("shows green progress bar for full completion (7/7 = 100%)", async () => {
      mockFetchResponses(FULL_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("profile-progress-bar")).toBeInTheDocument();
      });

      const bar = screen.getByTestId("profile-progress-bar");
      expect(bar).toHaveTextContent("7/7 campos");
      expect(bar).toHaveTextContent("100%");

      const innerBar = bar.querySelector(".bg-green-500");
      expect(innerBar).toBeInTheDocument();
    });
  });

  // ────────────────── AC4-AC6: Accent fixes in PerfilPage ──────────────────

  describe("AC4-AC6: Accent corrections in profile", () => {
    beforeEach(async () => {
      mockFetchResponses(EMPTY_PROFILE);
      await act(async () => { render(<PerfilPage />); });
      await waitFor(() => {
        expect(screen.getByTestId("profile-licitante-section")).toBeInTheDocument();
      });
    });

    it("AC4: shows 'Estados de atuação' with accent", () => {
      expect(screen.getByText("Estados de atuação")).toBeInTheDocument();
    });

    it("AC5: shows 'Experiência' with accent", () => {
      expect(screen.getByText("Experiência")).toBeInTheDocument();
    });

    it("AC6: shows 'Funcionários' with accent", () => {
      expect(screen.getByText("Funcionários")).toBeInTheDocument();
    });
  });

  // ────────────────── AC7-AC8: Alerts accents (in AlertPreferences) ──────────────────

  describe("AC7-AC8: Alert section accents", () => {
    it.skip("AC7: 'licitação filtradas' — moved to AlertPreferences component (separate test)", () => {});
    it.skip("AC8: 'Frequência' — moved to AlertPreferences component (separate test)", () => {});
  });

  // ────────────────── AC9: No remaining unaccented words ──────────────────

  describe("AC9: No remaining unaccented display text", () => {
    it("does not contain 'Nao informado' (should be 'Não informado')", async () => {
      mockFetchResponses(EMPTY_PROFILE);
      const { container } = await act(async () => render(<PerfilPage />));

      await waitFor(() => {
        expect(screen.getByTestId("profile-licitante-section")).toBeInTheDocument();
      });

      const textContent = container.textContent || "";
      expect(textContent).not.toMatch(/\bNao informado\b/);
      expect(textContent).toContain("Não informado");
    });

    it("does not contain 'Voce' without accent (should be 'Você')", async () => {
      mockFetchResponses(EMPTY_PROFILE);
      const { container } = await act(async () => render(<PerfilPage />));

      await waitFor(() => {
        expect(screen.getByTestId("profile-licitante-section")).toBeInTheDocument();
      });

      const textContent = container.textContent || "";
      expect(textContent).not.toMatch(/\bVoce\b/);
    });
  });

  // ────────────────── AC10-AC11: Sticky nav (moved to layout.tsx) ──────────────────

  describe("AC10-AC11: Sticky anchor navigation", () => {
    it.skip("DEBT-011: Sticky nav moved to conta/layout.tsx — not testable as page component", () => {});
    it.skip("DEBT-011: Scroll behavior moved to conta/layout.tsx", () => {});
  });

  // ────────────────── Integration: Edit mode accents ──────────────────

  describe("Edit mode accent corrections", () => {
    it("edit mode labels have proper accents", async () => {
      mockFetchResponses(EMPTY_PROFILE);
      await act(async () => { render(<PerfilPage />); });

      await waitFor(() => {
        expect(screen.getByTestId("edit-profile-btn")).toBeInTheDocument();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("edit-profile-btn"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("save-profile-btn")).toBeInTheDocument();
      });

      expect(screen.getByText("Estados de atuação")).toBeInTheDocument();
      expect(screen.getByText("Experiência com licitações")).toBeInTheDocument();
      expect(screen.getByText("Funcionários")).toBeInTheDocument();
      expect(screen.getByText("Valor mínimo (R$)")).toBeInTheDocument();
      expect(screen.getByText("Valor máximo (R$)")).toBeInTheDocument();
      expect(screen.getByText("Atestados e certificações")).toBeInTheDocument();
    });
  });
});
