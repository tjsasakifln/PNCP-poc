/**
 * UX-437: Valor R$ 0 no histórico para buscas com resultados
 *
 * AC3: Quando valor_total = 0 (bids do PCP v2 sem dados de valor),
 * o histórico deve exibir "Valor não disponível" — não "R$ 0" nem "Valor não informado".
 *
 * AC5: Quando bids PNCP têm valor real, o histórico exibe o valor formatado.
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ============================================================================
// Mocks (seguindo padrão de story-sab012-microcopy-ux.test.tsx)
// ============================================================================

let mockAuthState: any = {
  session: {
    access_token: "test-token",
    user: { id: "u1", email: "test@test.com", created_at: "2026-01-01" },
  },
  user: { id: "u1", email: "test@test.com" },
  loading: false,
  signOut: jest.fn(),
  signInWithEmail: jest.fn(),
  signInWithMagicLink: jest.fn(),
  signInWithGoogle: jest.fn(),
};

jest.mock("next/link", () => {
  return function MockLink({ children, ...props }: any) {
    return <a {...props}>{children}</a>;
  };
});
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/historico",
  useSearchParams: () => new URLSearchParams(),
}));
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockAuthState,
}));
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn(), identifyUser: jest.fn() }),
}));
jest.mock("../hooks/usePlan", () => ({
  usePlan: () => ({ planInfo: null }),
}));
jest.mock("../components/PageHeader", () => ({
  PageHeader: function Mock({ title }: any) {
    return <h1>{title}</h1>;
  },
}));
jest.mock("../components/EmptyState", () => ({
  EmptyState: function Mock() {
    return null;
  },
}));
jest.mock("../components/ErrorStateWithRetry", () => ({
  ErrorStateWithRetry: function Mock() {
    return null;
  },
}));
jest.mock("../components/AuthLoadingScreen", () => ({
  AuthLoadingScreen: function Mock() {
    return null;
  },
}));
jest.mock("../lib/error-messages", () => ({
  getUserFriendlyError: (m: string) => m,
  translateAuthError: (m: string) => m,
}));
jest.mock("../lib/constants/sector-names", () => ({
  getSectorDisplayName: (s: string) => s,
}));
jest.mock("sonner", () => ({
  toast: { error: jest.fn(), info: jest.fn(), success: jest.fn() },
  Toaster: () => null,
}));
jest.mock("../app/components/InstitutionalSidebar", () => {
  return function MockSidebar() {
    return <div data-testid="sidebar" />;
  };
});
jest.mock("next/dynamic", () => {
  return function mockDynamic() {
    return function MockDynamicComponent() {
      return null;
    };
  };
});

let mockUseSessionsReturn: any = {
  sessions: [],
  total: 0,
  loading: false,
  error: null,
  errorTimestamp: null,
  refresh: jest.fn(),
  silentRefresh: jest.fn(),
};
jest.mock("../hooks/useSessions", () => ({
  useSessions: () => mockUseSessionsReturn,
}));

import HistoricoPage from "../app/historico/page";

// ============================================================================
// Helper
// ============================================================================

function makeSession(overrides: Record<string, any> = {}) {
  return {
    id: "session-1",
    sectors: ["informatica"],
    ufs: ["SP"],
    data_inicial: "2026-01-01",
    data_final: "2026-01-10",
    custom_keywords: null,
    total_raw: 100,
    total_filtered: 6,
    valor_total: 50000,
    resumo_executivo: "Test",
    created_at: "2026-01-01T00:00:00Z",
    status: "completed",
    error_message: null,
    error_code: null,
    duration_ms: null,
    pipeline_stage: null,
    started_at: "2026-01-01T00:00:00Z",
    response_state: null,
    ...overrides,
  };
}

// ============================================================================
// UX-437 AC3: "Valor não disponível" para valor_total = 0
// ============================================================================

describe("UX-437 AC3: Exibição de valor no histórico", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("exibe 'Valor não disponível' quando valor_total = 0 (todos PCP v2)", async () => {
    mockUseSessionsReturn = {
      sessions: [makeSession({ valor_total: 0, total_filtered: 6 })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("Valor não disponível")).toBeInTheDocument();
    });
  });

  it("NÃO exibe 'R$ 0' quando valor_total = 0", async () => {
    mockUseSessionsReturn = {
      sessions: [makeSession({ valor_total: 0, total_filtered: 2 })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.queryByText("R$ 0")).not.toBeInTheDocument();
    });
  });

  it("NÃO exibe 'Valor não informado' (texto antigo trocado por UX-437)", async () => {
    mockUseSessionsReturn = {
      sessions: [makeSession({ valor_total: 0, total_filtered: 2 })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(
        screen.queryByText("Valor não informado")
      ).not.toBeInTheDocument();
    });
  });

  it("exibe 'Valor não disponível' quando valor_total = null", async () => {
    mockUseSessionsReturn = {
      sessions: [makeSession({ valor_total: null, total_filtered: 3 })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("Valor não disponível")).toBeInTheDocument();
    });
  });

  it("AC5: exibe valor formatado quando valor_total > 0 (bids PNCP)", async () => {
    mockUseSessionsReturn = {
      sessions: [makeSession({ valor_total: 450_000, total_filtered: 5 })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    render(<HistoricoPage />);

    await waitFor(() => {
      // formatCurrencyBR(450_000) = "R$ 450.000"
      expect(screen.getByText("R$ 450.000")).toBeInTheDocument();
      expect(
        screen.queryByText("Valor não disponível")
      ).not.toBeInTheDocument();
    });
  });

  it("AC5: exibe valor em bilhões para grandes contratos PNCP", async () => {
    mockUseSessionsReturn = {
      sessions: [makeSession({ valor_total: 1_500_000_000, total_filtered: 1 })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("R$ 1,5 bi")).toBeInTheDocument();
    });
  });
});
