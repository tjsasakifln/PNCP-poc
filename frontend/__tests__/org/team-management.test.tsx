/**
 * STORY-322 AC29 — Frontend Tests: Team Management
 *
 * Covers:
 *   1. InviteMemberModal — render, submit, validation, error, close, callbacks
 *   2. EquipePage (conta/equipe) — upgrade prompt, member list, slots indicator
 *   3. PlanosPage — consultoria plan card, UTM badge, billing period toggle
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Global fetch mock ────────────────────────────────────────────────────────

const mockFetch = jest.fn();
global.fetch = mockFetch as unknown as typeof fetch;

// ─── Sonner toast ─────────────────────────────────────────────────────────────

const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();
jest.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => mockToastSuccess(...args),
    error: (...args: unknown[]) => mockToastError(...args),
  },
}));

// ─── next/link ────────────────────────────────────────────────────────────────

jest.mock("next/link", () => {
  const MockLink = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "MockLink";
  return MockLink;
});

// ─── PageHeader ───────────────────────────────────────────────────────────────
// Path relative to __tests__/org/ → ../../components/PageHeader

jest.mock("../../components/PageHeader", () => ({
  PageHeader: ({ title }: { title: string }) => (
    <header>
      <h1>{title}</h1>
    </header>
  ),
}));

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 1 — InviteMemberModal
// ─────────────────────────────────────────────────────────────────────────────

import { InviteMemberModal } from "../../components/org/InviteMemberModal";

describe("InviteMemberModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onInviteSent: jest.fn(),
    accessToken: "test-token",
    orgId: "org-123",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  describe("Rendering", () => {
    it("renders nothing when isOpen is false", () => {
      const { container } = render(
        <InviteMemberModal {...defaultProps} isOpen={false} />
      );
      expect(container.firstChild).toBeNull();
    });

    it("renders modal dialog when open", () => {
      render(<InviteMemberModal {...defaultProps} />);
      expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    });

    it("shows the Convidar membro heading", () => {
      render(<InviteMemberModal {...defaultProps} />);
      expect(screen.getByText("Convidar membro")).toBeInTheDocument();
    });

    it("renders the email input field labelled E-mail", () => {
      render(<InviteMemberModal {...defaultProps} />);
      expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    });

    it("renders the Enviar convite submit button", () => {
      render(<InviteMemberModal {...defaultProps} />);
      expect(screen.getByRole("button", { name: /Enviar convite/i })).toBeInTheDocument();
    });

    it("renders a Cancelar button", () => {
      render(<InviteMemberModal {...defaultProps} />);
      expect(screen.getByRole("button", { name: /Cancelar/i })).toBeInTheDocument();
    });

    it("has aria-labelledby pointing to invite-modal-title", () => {
      render(<InviteMemberModal {...defaultProps} />);
      const dialog = screen.getByRole("alertdialog");
      expect(dialog).toHaveAttribute("aria-labelledby", "invite-modal-title");
      expect(document.getElementById("invite-modal-title")).toBeInTheDocument();
    });
  });

  // ── Submit behaviour ───────────────────────────────────────────────────────

  describe("Submit behaviour", () => {
    it("calls fetch with correct payload on valid email submit", async () => {
      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          "/api/organizations/org-123?action=invite",
          expect.objectContaining({
            method: "POST",
            headers: expect.objectContaining({
              Authorization: "Bearer test-token",
              "Content-Type": "application/json",
            }),
            body: JSON.stringify({ email: "membro@empresa.com.br" }),
          })
        );
      });
    });

    it("trims and lowercases email before sending", async () => {
      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "  MEMBRO@Empresa.COM.BR  " },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        const body = JSON.parse(
          (mockFetch.mock.calls[0][1] as RequestInit).body as string
        );
        expect(body.email).toBe("membro@empresa.com.br");
      });
    });

    it("shows Enviando... while loading", async () => {
      let resolveFetch!: (value: unknown) => void;
      mockFetch.mockReturnValue(
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
      );

      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "teste@teste.com" },
      });

      act(() => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/Enviando/i)).toBeInTheDocument();
      });

      // Resolve to clean up pending state
      resolveFetch({ ok: true, json: async () => ({}) });
    });

    it("submit button is disabled while loading", async () => {
      let resolveFetch!: (value: unknown) => void;
      mockFetch.mockReturnValue(
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
      );

      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "teste@teste.com" },
      });

      act(() => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/Enviando/i).closest("button")).toBeDisabled();
      });

      resolveFetch({ ok: true, json: async () => ({}) });
    });

    it("calls onInviteSent after successful submission", async () => {
      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(defaultProps.onInviteSent).toHaveBeenCalledTimes(1);
      });
    });

    it("calls onClose after successful submission", async () => {
      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
      });
    });

    it("shows a success toast mentioning the invited email", async () => {
      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(mockToastSuccess).toHaveBeenCalledWith(
          expect.stringContaining("membro@empresa.com.br")
        );
      });
    });
  });

  // ── Error handling ─────────────────────────────────────────────────────────

  describe("Error handling", () => {
    it("shows detail error message when API returns !ok with detail field", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "Convite já enviado para este e-mail." }),
      });

      render(<InviteMemberModal {...defaultProps} />);
      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          "Convite já enviado para este e-mail."
        );
      });
    });

    it("shows message error when detail is absent in API response", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: async () => ({ message: "Limite de membros atingido." }),
      });

      render(<InviteMemberModal {...defaultProps} />);
      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          "Limite de membros atingido."
        );
      });
    });

    it("shows fallback error when API response has no detail or message", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: async () => ({}),
      });

      render(<InviteMemberModal {...defaultProps} />);
      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent("Erro ao enviar convite");
      });
    });

    it("shows error message when fetch throws a network error", async () => {
      mockFetch.mockRejectedValue(new Error("Network error"));

      render(<InviteMemberModal {...defaultProps} />);
      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent("Network error");
      });
    });

    it("clears error when user types in the input again", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "Erro" }),
      });

      render(<InviteMemberModal {...defaultProps} />);
      const input = screen.getByLabelText("E-mail");
      fireEvent.change(input, { target: { value: "membro@empresa.com.br" } });

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Enviar convite/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toBeInTheDocument();
      });

      fireEvent.change(input, { target: { value: "novo@email.com" } });
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });

  // ── Email validation ───────────────────────────────────────────────────────

  describe("Email validation", () => {
    it("shows validation error when form submitted with empty email", async () => {
      render(<InviteMemberModal {...defaultProps} />);
      const form = screen.getByRole("alertdialog").querySelector("form")!;

      await act(async () => {
        fireEvent.submit(form);
      });

      expect(screen.getByRole("alert")).toHaveTextContent(
        "Informe o e-mail do membro a convidar."
      );
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it("shows validation error for invalid email format", async () => {
      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "not-an-email" },
      });

      const form = screen.getByRole("alertdialog").querySelector("form")!;
      await act(async () => {
        fireEvent.submit(form);
      });

      expect(screen.getByRole("alert")).toHaveTextContent("E-mail invalido.");
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it("submit button is disabled when email input is empty", () => {
      render(<InviteMemberModal {...defaultProps} />);
      expect(
        screen.getByRole("button", { name: /Enviar convite/i })
      ).toBeDisabled();
    });

    it("submit button becomes enabled when valid email is typed", () => {
      render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "a@b.com" },
      });

      expect(
        screen.getByRole("button", { name: /Enviar convite/i })
      ).not.toBeDisabled();
    });
  });

  // ── Close / backdrop ───────────────────────────────────────────────────────

  describe("Close behaviour", () => {
    it("calls onClose when Cancelar button is clicked", () => {
      render(<InviteMemberModal {...defaultProps} />);
      fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }));
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it("calls onClose when backdrop overlay is clicked", () => {
      const { container } = render(<InviteMemberModal {...defaultProps} />);
      // The outer fixed overlay is the first child of the container
      const overlay = container.firstChild as HTMLElement;
      // Simulate clicking directly on the overlay (e.target === e.currentTarget)
      fireEvent.click(overlay);
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it("does NOT call onClose when clicking inside the dialog card", () => {
      render(<InviteMemberModal {...defaultProps} />);
      // Click on the dialog box itself — should not propagate to backdrop
      fireEvent.click(screen.getByRole("alertdialog"));
      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    it("resets email field after close and re-open", () => {
      const { rerender } = render(<InviteMemberModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "membro@empresa.com.br" },
      });

      fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }));

      // Close then re-open
      rerender(<InviteMemberModal {...defaultProps} isOpen={false} />);
      rerender(<InviteMemberModal {...defaultProps} isOpen={true} />);

      expect(screen.getByLabelText("E-mail")).toHaveValue("");
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 2 — EquipePage (/conta/equipe)
// ─────────────────────────────────────────────────────────────────────────────

// Mocks for EquipePage dependencies.
// The equipe page is at app/conta/equipe/page.tsx and imports:
//   useAuth from "../../components/AuthProvider"  → app/components/AuthProvider
//   usePlan from "../../../hooks/usePlan"          → hooks/usePlan
//   PageHeader from "../../../components/PageHeader" → components/PageHeader (mocked above)

const mockUseAuth = jest.fn();
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

const mockUsePlan = jest.fn();
jest.mock("../../hooks/usePlan", () => ({
  usePlan: () => mockUsePlan(),
}));

import EquipePage from "../../app/conta/equipe/page";

describe("EquipePage — /conta/equipe", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── Upgrade prompt for non-consultoria plans ───────────────────────────────

  describe("Upgrade prompt (non-consultoria plan)", () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: { access_token: "tok", user: { email: "user@test.com" } },
      });
    });

    it("shows upgrade prompt when plan_id is smartlic_pro", async () => {
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: "smartlic_pro" },
        loading: false,
      });

      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText("Gestão de Equipe")).toBeInTheDocument();
      });
      expect(
        screen.getByText(/gerenciamento de equipes está disponível no SmartLic Consultoria/i)
      ).toBeInTheDocument();
    });

    it("shows upgrade prompt when plan_id is free_trial", async () => {
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: "free_trial" },
        loading: false,
      });

      render(<EquipePage />);

      await waitFor(() => {
        expect(
          screen.getByText(/gerenciamento de equipes está disponível no SmartLic Consultoria/i)
        ).toBeInTheDocument();
      });
    });

    it("renders Ver opções link to /planos for non-consultoria users", async () => {
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: "free_trial" },
        loading: false,
      });

      render(<EquipePage />);

      await waitFor(() => {
        const link = screen.getByRole("link", { name: /Ver opções/i });
        expect(link).toHaveAttribute("href", "/planos");
      });
    });

    it("does NOT render invite button for non-consultoria plan", async () => {
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: "smartlic_pro" },
        loading: false,
      });

      render(<EquipePage />);

      await waitFor(() => {
        expect(
          screen.queryByRole("button", { name: /Convidar membro/i })
        ).not.toBeInTheDocument();
      });
    });
  });

  // ── Member list rendering ──────────────────────────────────────────────────

  describe("Member list for consultoria plan", () => {
    const mockOrg = {
      id: "org-123",
      name: "Consultoria XYZ",
      slug: "consultoria-xyz",
      max_seats: 5,
      members: [
        {
          id: "m1",
          user_id: "u1",
          email: "owner@consultoria.com",
          name: "Fulano Owner",
          role: "owner",
          status: "accepted",
          joined_at: "2026-01-01T00:00:00Z",
          invited_at: "2025-12-01T00:00:00Z",
        },
        {
          id: "m2",
          user_id: "u2",
          email: "membro@consultoria.com",
          name: "Ciclano Membro",
          role: "member",
          status: "accepted",
          joined_at: "2026-01-10T00:00:00Z",
          invited_at: "2025-12-15T00:00:00Z",
        },
        {
          id: "m3",
          user_id: null,
          email: "pending@consultoria.com",
          name: null,
          role: "member",
          status: "pending",
          joined_at: null,
          invited_at: "2026-02-01T00:00:00Z",
        },
      ],
    };

    beforeEach(() => {
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: "consultoria_mensal" },
        loading: false,
      });
      mockUseAuth.mockReturnValue({
        session: {
          access_token: "tok",
          user: { email: "owner@consultoria.com" },
        },
      });

      // Step 1: GET /api/organizations → OrgRef
      // Step 2: GET /api/organizations/org-123 → full org
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ id: "org-123", name: "Consultoria XYZ", role: "owner" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockOrg,
        });
    });

    it("renders accepted member names in the list", async () => {
      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText("Fulano Owner")).toBeInTheDocument();
      });
      expect(screen.getByText("Ciclano Membro")).toBeInTheDocument();
    });

    it("renders pending member email when name is null", async () => {
      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText("pending@consultoria.com")).toBeInTheDocument();
      });
    });

    it("shows Proprietário role badge for owner", async () => {
      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText("Proprietário")).toBeInTheDocument();
      });
    });

    it("shows Membro role badge for regular members", async () => {
      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getAllByText("Membro").length).toBeGreaterThanOrEqual(1);
      });
    });

    it("shows Pendente badge for pending invites", async () => {
      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText("Pendente")).toBeInTheDocument();
      });
    });

    it("marks current user with (você)", async () => {
      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText("(você)")).toBeInTheDocument();
      });
    });

    it("shows Convidar membro button for owner/admin", async () => {
      render(<EquipePage />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /Convidar membro/i })
        ).toBeInTheDocument();
      });
    });
  });

  // ── Slots indicator ────────────────────────────────────────────────────────

  describe("Slots indicator (X/Y membros)", () => {
    beforeEach(() => {
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: "consultoria_anual" },
        loading: false,
      });
      mockUseAuth.mockReturnValue({
        session: {
          access_token: "tok",
          user: { email: "user0@org.com" },
        },
      });
    });

    const buildOrg = (accepted: number, pending: number, maxSeats: number) => ({
      id: "org-123",
      name: "Org Teste",
      slug: "org-teste",
      max_seats: maxSeats,
      members: [
        ...Array.from({ length: accepted }, (_, i) => ({
          id: `m${i}`,
          user_id: `u${i}`,
          email: `user${i}@org.com`,
          name: `User ${i}`,
          role: i === 0 ? "owner" : "member",
          status: "accepted",
          joined_at: "2026-01-01T00:00:00Z",
          invited_at: "2025-12-01T00:00:00Z",
        })),
        ...Array.from({ length: pending }, (_, i) => ({
          id: `p${i}`,
          user_id: null,
          email: `pending${i}@org.com`,
          name: null,
          role: "member",
          status: "pending",
          joined_at: null,
          invited_at: "2026-02-01T00:00:00Z",
        })),
      ],
    });

    it("shows correct accepted count and max seats in X/Y membros", async () => {
      const org = buildOrg(3, 1, 5);
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: "org-123", name: "Org Teste", role: "owner" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => org,
        });

      render(<EquipePage />);

      // slotsUsed = 3 accepted, maxSeats = 5
      await waitFor(() => {
        const slotEl = screen.getByText(/membros/);
        expect(slotEl.textContent).toContain("3");
        expect(slotEl.textContent).toContain("5");
      });
    });

    it("shows pending badge count when there are pending invites", async () => {
      const org = buildOrg(2, 2, 5);
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: "org-123", name: "Org Teste", role: "owner" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => org,
        });

      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText(/pendentes/i)).toBeInTheDocument();
      });
    });

    it("shows no-org state when /api/organizations returns 404", async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 404, json: async () => ({}) });

      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText(/Nenhuma organização encontrada/i)).toBeInTheDocument();
      });
    });

    it("shows empty message when org has no members", async () => {
      const org = buildOrg(0, 0, 5);
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: "org-123", name: "Org Teste", role: "owner" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => org,
        });

      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText(/Nenhum membro encontrado/i)).toBeInTheDocument();
      });
    });

    it("shows error state when org API call fails", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: "org-123", name: "Org Teste", role: "owner" }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ message: "Servidor indisponível" }),
        });

      render(<EquipePage />);

      await waitFor(() => {
        expect(screen.getByText(/Servidor indisponível/i)).toBeInTheDocument();
      });
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 3 — PlanosPage consultoria card (AC21/AC22)
// ─────────────────────────────────────────────────────────────────────────────

// PlanosPage is heavily integrated with auth, billing, analytics.
// We focus on the consultoria card static rendering via isolated unit mocks.

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../../components/subscriptions/PlanToggle", () => ({
  PlanToggle: ({
    value,
    onChange,
  }: {
    value: string;
    onChange: (v: string) => void;
  }) => (
    <div data-testid="plan-toggle">
      <button data-testid="toggle-monthly" onClick={() => onChange("monthly")}>Mensal</button>
      <button data-testid="toggle-semiannual" onClick={() => onChange("semiannual")}>Semestral</button>
      <button data-testid="toggle-annual" onClick={() => onChange("annual")}>Anual</button>
    </div>
  ),
}));

jest.mock("../../components/TestimonialSection", () => {
  const T = () => <div data-testid="testimonials" />;
  T.displayName = "TestimonialSection";
  return Object.assign(T, { TESTIMONIALS: [], default: T });
});

jest.mock("../../lib/copy/roi", () => ({
  formatCurrency: (v: number) => `R$${v}`,
}));

jest.mock("../../lib/error-messages", () => ({
  getUserFriendlyError: (e: Error) => e.message,
}));

jest.mock("../../app/components/landing/LandingNavbar", () => {
  const Nav = () => <nav data-testid="landing-navbar" />;
  Nav.displayName = "LandingNavbar";
  return Nav;
});

import PlanosPage from "../../app/planos/page";

describe("PlanosPage — Consultoria plan card (AC21/AC22)", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    jest.clearAllMocks();

    // Default: anonymous user with no plan
    mockUseAuth.mockReturnValue({
      session: null,
      user: null,
      isAdmin: false,
      loading: false,
    });
    mockUsePlan.mockReturnValue({ planInfo: null, loading: false });

    mockFetch.mockResolvedValue({ ok: false, json: async () => ({}) });

    // Reset window.location.search to empty
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, search: "" },
    });
  });

  afterAll(() => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: originalLocation,
    });
  });

  // ── Consultoria card renders ───────────────────────────────────────────────

  it("renders SmartLic Consultoria heading", () => {
    render(<PlanosPage />);
    expect(screen.getByText("SmartLic Consultoria")).toBeInTheDocument();
  });

  it("renders Para Consultorias e Assessorias section header", () => {
    render(<PlanosPage />);
    expect(screen.getByText(/Para Consultorias e Assessorias/i)).toBeInTheDocument();
  });

  it("renders Até 5 usuários feature", () => {
    render(<PlanosPage />);
    expect(screen.getByText(/Até 5 usuários/i)).toBeInTheDocument();
  });

  it("renders 5.000 análises por mês feature", () => {
    render(<PlanosPage />);
    expect(screen.getByText(/5\.000 análises por mês/i)).toBeInTheDocument();
  });

  it("renders Logo da consultoria nos relatórios feature", () => {
    render(<PlanosPage />);
    expect(screen.getByText(/Logo da consultoria nos relatórios/i)).toBeInTheDocument();
  });

  it("renders Falar com vendas CTA button", () => {
    render(<PlanosPage />);
    expect(screen.getByRole("button", { name: /Falar com vendas/i })).toBeInTheDocument();
  });

  // ── UTM badge ─────────────────────────────────────────────────────────────

  it("does NOT show UTM badge without consultoria UTM param", () => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, search: "?utm_source=google" },
    });

    render(<PlanosPage />);
    expect(screen.queryByText(/Recomendado para consultorias/i)).not.toBeInTheDocument();
  });

  it("shows UTM badge when utm_source=consultoria", () => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, search: "?utm_source=consultoria" },
    });

    render(<PlanosPage />);
    expect(screen.getByText(/Recomendado para consultorias/i)).toBeInTheDocument();
  });

  it("shows UTM badge when utm_campaign=consultoria", () => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, search: "?utm_campaign=consultoria" },
    });

    render(<PlanosPage />);
    expect(screen.getByText(/Recomendado para consultorias/i)).toBeInTheDocument();
  });

  // ── Billing period toggle affects consultoria pricing ─────────────────────

  it("shows monthly consultoria price R$997 by default", () => {
    render(<PlanosPage />);
    // formatCurrency mock returns "R$997"
    expect(screen.getByText("R$997")).toBeInTheDocument();
  });

  it("shows semiannual consultoria price R$897 when Semestral selected", () => {
    render(<PlanosPage />);
    fireEvent.click(screen.getByTestId("toggle-semiannual"));
    expect(screen.getByText("R$897")).toBeInTheDocument();
  });

  it("shows annual consultoria price R$797 when Anual selected", () => {
    render(<PlanosPage />);
    fireEvent.click(screen.getByTestId("toggle-annual"));
    expect(screen.getByText("R$797")).toBeInTheDocument();
  });

  it("shows Economize 10% badge for semiannual consultoria price", () => {
    render(<PlanosPage />);
    fireEvent.click(screen.getByTestId("toggle-semiannual"));
    // At least one "Economize 10%" must appear (in consultoria card)
    expect(screen.getAllByText(/Economize 10%/i).length).toBeGreaterThanOrEqual(1);
  });

  it("shows Economize 20% badge for annual consultoria price", () => {
    render(<PlanosPage />);
    fireEvent.click(screen.getByTestId("toggle-annual"));
    expect(screen.getAllByText(/Economize 20%/i).length).toBeGreaterThanOrEqual(1);
  });

  // ── CTA for anonymous user ─────────────────────────────────────────────────

  it("redirects to /login when anonymous user clicks Falar com vendas", () => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, href: "" },
    });

    render(<PlanosPage />);
    fireEvent.click(screen.getByRole("button", { name: /Falar com vendas/i }));

    expect(window.location.href).toBe("/login");
  });
});
