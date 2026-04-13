/**
 * UX-429 — Perfil de Licitante: estado de erro amigável (AC3) e CTA para perfil vazio (AC4)
 *
 * AC3: Quando o fetch de rede falha (SWR error, profileCtx = null), a seção exibe
 *      mensagem de erro explícita em vez de ficar vazia.
 * AC4: Quando o perfil não está preenchido (profileCtx = {}), exibe CTA "Preencher agora".
 */

import React from "react";
import { render, screen, act, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

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

// ─── Controllable useProfileContext mock ─────────────────────────────────────

let mockCtxData: Record<string, unknown> | null = null;
let mockCtxLoading = false;
let mockCtxError: string | null = null;
const mockUpdateCache = jest.fn();
const mockMutate = jest.fn();

jest.mock("../hooks/useProfileContext", () => ({
  useProfileContext: () => ({
    profileCtx: mockCtxData,
    isLoading: mockCtxLoading,
    error: mockCtxError,
    updateCache: mockUpdateCache,
    mutate: mockMutate,
  }),
}));

// ─── Component under test ────────────────────────────────────────────────────

import PerfilPage from "../app/conta/perfil/page";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function setupMock({
  profileCtx = null,
  isLoading = false,
  error = null,
}: {
  profileCtx?: Record<string, unknown> | null;
  isLoading?: boolean;
  error?: string | null;
}) {
  mockCtxData = profileCtx;
  mockCtxLoading = isLoading;
  mockCtxError = error;
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("UX-429 AC3: Estado de erro amigável quando fetch de rede falha", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Element.prototype.scrollIntoView = jest.fn();
  });

  it("exibe mensagem de erro quando profileCtx é null e error está definido", async () => {
    setupMock({ profileCtx: null, isLoading: false, error: "Network error" });

    await act(async () => { render(<PerfilPage />); });

    await waitFor(() => {
      expect(screen.getByTestId("profile-context-error")).toBeInTheDocument();
    });

    expect(screen.getByText(/Não foi possível carregar o perfil de licitante/)).toBeInTheDocument();
    expect(screen.getByText(/Recarregue a página para tentar novamente/)).toBeInTheDocument();
  });

  it("o estado de erro tem role='alert' para acessibilidade", async () => {
    setupMock({ profileCtx: null, isLoading: false, error: "fetch failed" });

    await act(async () => { render(<PerfilPage />); });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("NÃO exibe estado de erro quando profileCtx é null mas error também é null", async () => {
    setupMock({ profileCtx: null, isLoading: false, error: null });

    await act(async () => { render(<PerfilPage />); });

    expect(screen.queryByTestId("profile-context-error")).not.toBeInTheDocument();
  });

  it("NÃO exibe estado de erro durante carregamento (profileLoading=true)", async () => {
    setupMock({ profileCtx: null, isLoading: true, error: "fetch failed" });

    await act(async () => { render(<PerfilPage />); });

    expect(screen.queryByTestId("profile-context-error")).not.toBeInTheDocument();
  });

  it("NÃO exibe estado de erro quando profileCtx está disponível (mesmo vazio)", async () => {
    setupMock({ profileCtx: {}, isLoading: false, error: null });

    await act(async () => { render(<PerfilPage />); });

    expect(screen.queryByTestId("profile-context-error")).not.toBeInTheDocument();
  });
});

describe("UX-429 AC4: CTA para perfil não preenchido", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Element.prototype.scrollIntoView = jest.fn();
  });

  it("exibe guidance banner quando profileCtx está vazio ({})", async () => {
    setupMock({ profileCtx: {}, isLoading: false, error: null });

    await act(async () => { render(<PerfilPage />); });

    await waitFor(() => {
      expect(screen.getByTestId("profile-guidance-banner")).toBeInTheDocument();
    });
  });

  it("exibe botão 'Preencher agora' quando perfil está vazio", async () => {
    setupMock({ profileCtx: {}, isLoading: false, error: null });

    await act(async () => { render(<PerfilPage />); });

    await waitFor(() => {
      expect(screen.getByTestId("fill-now-btn")).toBeInTheDocument();
    });

    expect(screen.getByText("Preencher agora →")).toBeInTheDocument();
  });

  it("exibe progress bar 0% quando perfil está vazio", async () => {
    setupMock({ profileCtx: {}, isLoading: false, error: null });

    await act(async () => { render(<PerfilPage />); });

    await waitFor(() => {
      expect(screen.getByTestId("profile-progress-bar")).toBeInTheDocument();
    });

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveTextContent("0/7 campos");
    expect(bar).toHaveTextContent("0%");
  });

  it("oculta guidance banner quando perfil está 100% completo", async () => {
    setupMock({
      profileCtx: {
        ufs_atuacao: ["SP"],
        porte_empresa: "me",
        experiencia_licitacoes: "intermediario",
        faixa_valor_min: 50000,
        capacidade_funcionarios: 20,
        faturamento_anual: 1000000,
        atestados: ["crea"],
      },
      isLoading: false,
      error: null,
    });

    await act(async () => { render(<PerfilPage />); });

    await waitFor(() => {
      expect(screen.getByTestId("profile-licitante-section")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("profile-guidance-banner")).not.toBeInTheDocument();
  });
});
