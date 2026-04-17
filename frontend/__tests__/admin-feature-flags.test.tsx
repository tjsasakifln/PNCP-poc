/**
 * Tests for /admin/feature-flags page — STORY-5.2 AC4
 *
 * Covers: flag table rendering, toggle PATCH call, non-admin access restriction.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock useAuth
const mockUseAuth = jest.fn();
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock useAdminSWR
const mockMutate = jest.fn();
const mockUseAdminSWR = jest.fn();
jest.mock("../hooks/useAdminSWR", () => ({
  useAdminSWR: (key: string | null) => mockUseAdminSWR(key),
}));

// Mock next/link
jest.mock("next/link", () => {
  const MockLink = ({ href, children, ...props }: { href: string; children: React.ReactNode; [key: string]: unknown }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
  MockLink.displayName = "MockLink";
  return MockLink;
});

// Mock sonner toast
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

import AdminFeatureFlagsPage from "../app/admin/feature-flags/page";
import { toast } from "sonner";

const MOCK_FLAGS_RESPONSE = {
  flags: [
    {
      name: "LLM_ARBITER_ENABLED",
      value: true,
      source: "env",
      description: "Enable LLM classification arbiter",
      env_var: "LLM_ARBITER_ENABLED",
      default: "true",
      lifecycle: {
        owner: "backend",
        category: "llm",
        lifecycle: "permanent",
        created: "2025-01",
        remove_after: null,
      },
    },
    {
      name: "FILTER_DEBUG_MODE",
      value: false,
      source: "default",
      description: "Log verbose filter debug output",
      env_var: "FILTER_DEBUG_MODE",
      default: "false",
      lifecycle: {
        owner: "backend",
        category: "debug",
        lifecycle: "ops-toggle",
        created: "2025-02",
        remove_after: null,
      },
    },
  ],
  total: 2,
  redis_available: true,
};

const ADMIN_AUTH = {
  session: { access_token: "tok-admin" },
  loading: false,
  isAdmin: true,
  isAdminLoading: false,
};

describe("AdminFeatureFlagsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  it("renders flag table when user is admin", () => {
    mockUseAuth.mockReturnValue(ADMIN_AUTH);
    mockUseAdminSWR.mockReturnValue({
      data: MOCK_FLAGS_RESPONSE,
      error: null,
      isLoading: false,
      mutate: mockMutate,
    });

    render(<AdminFeatureFlagsPage />);

    expect(screen.getByText("LLM_ARBITER_ENABLED")).toBeInTheDocument();
    expect(screen.getByText("FILTER_DEBUG_MODE")).toBeInTheDocument();
    expect(screen.getByText("ativo")).toBeInTheDocument();
    expect(screen.getByText("inativo")).toBeInTheDocument();
  });

  it("shows access restricted message for non-admin users", () => {
    mockUseAuth.mockReturnValue({
      ...ADMIN_AUTH,
      isAdmin: false,
    });
    mockUseAdminSWR.mockReturnValue({
      data: null,
      error: null,
      isLoading: false,
      mutate: mockMutate,
    });

    render(<AdminFeatureFlagsPage />);

    expect(screen.getByText("Acesso Restrito")).toBeInTheDocument();
  });

  it("shows login link when no session", () => {
    mockUseAuth.mockReturnValue({
      ...ADMIN_AUTH,
      session: null,
      isAdmin: false,
    });
    mockUseAdminSWR.mockReturnValue({
      data: null,
      error: null,
      isLoading: false,
      mutate: mockMutate,
    });

    render(<AdminFeatureFlagsPage />);

    expect(screen.getByText("Login necessário")).toBeInTheDocument();
  });

  it("calls PATCH with toggled value when toggle button clicked", async () => {
    mockUseAuth.mockReturnValue(ADMIN_AUTH);
    mockUseAdminSWR.mockReturnValue({
      data: MOCK_FLAGS_RESPONSE,
      error: null,
      isLoading: false,
      mutate: mockMutate,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        name: "LLM_ARBITER_ENABLED",
        value: false,
        source: "redis",
        previous_value: true,
        previous_source: "env",
      }),
    });

    render(<AdminFeatureFlagsPage />);

    // First toggle button = LLM_ARBITER_ENABLED (value: true → click to disable)
    const toggleButtons = screen.getAllByRole("button", { name: /Desativar|Ativar/i });
    fireEvent.click(toggleButtons[0]);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/admin/feature-flags/LLM_ARBITER_ENABLED",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ value: false }),
        })
      );
    });

    expect(mockMutate).toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalled();
  });

  it("shows error toast when toggle PATCH fails", async () => {
    mockUseAuth.mockReturnValue(ADMIN_AUTH);
    mockUseAdminSWR.mockReturnValue({
      data: MOCK_FLAGS_RESPONSE,
      error: null,
      isLoading: false,
      mutate: mockMutate,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Flag not found" }),
    });

    render(<AdminFeatureFlagsPage />);

    const toggleButtons = screen.getAllByRole("button", { name: /Desativar|Ativar/i });
    fireEvent.click(toggleButtons[0]);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Flag not found");
    });
  });

  it("renders redis status indicator", () => {
    mockUseAuth.mockReturnValue(ADMIN_AUTH);
    mockUseAdminSWR.mockReturnValue({
      data: MOCK_FLAGS_RESPONSE,
      error: null,
      isLoading: false,
      mutate: mockMutate,
    });

    render(<AdminFeatureFlagsPage />);

    expect(
      screen.getByText(/Redis:.*Conectado/i)
    ).toBeInTheDocument();
  });

  it("passes null key to useAdminSWR when not admin", () => {
    mockUseAuth.mockReturnValue({
      ...ADMIN_AUTH,
      isAdmin: false,
    });
    mockUseAdminSWR.mockReturnValue({
      data: null,
      error: null,
      isLoading: false,
      mutate: mockMutate,
    });

    render(<AdminFeatureFlagsPage />);

    expect(mockUseAdminSWR).toHaveBeenCalledWith(null);
  });
});
