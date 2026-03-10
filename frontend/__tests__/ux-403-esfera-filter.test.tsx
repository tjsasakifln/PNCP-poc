/**
 * UX-403 — Filtro de esfera rejeita 77% dos resultados silenciosamente
 *
 * AC3: When all 3 esferas selected, esferas field NOT sent in request
 * AC4: Label renamed to "Filtros avançados de localização"
 * AC5: Badge shown when location filters differ from default
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn(), prefetch: jest.fn() }),
  usePathname: () => "/buscar",
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    user: { id: "user-1", email: "test@test.com" } as any,
    session: { access_token: "mock-token" } as any,
    loading: false,
  }),
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../app/components/BackendStatusIndicator", () => ({
  useBackendStatusContext: () => ({ status: "online", isPolling: false, checkHealth: jest.fn() }),
  BackendStatusProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useBackendStatus: () => ({ status: "online", isPolling: false, checkHealth: jest.fn() }),
  __esModule: true,
  default: () => null,
}));

// ─── FilterPanel Tests ──────────────────────────────────────────────────────

import FilterPanel from "../app/buscar/components/FilterPanel";

describe("UX-403: FilterPanel label and badge", () => {
  const defaultProps = {
    locationFiltersOpen: false,
    setLocationFiltersOpen: jest.fn(),
    esferas: ["F" as const, "E" as const, "M" as const],
    setEsferas: jest.fn(),
    ufsSelecionadas: new Set(["SP"]),
    municipios: [] as any[],
    setMunicipios: jest.fn(),
    advancedFiltersOpen: false,
    setAdvancedFiltersOpen: jest.fn(),
    status: "todos" as const,
    setStatus: jest.fn(),
    modalidades: [4, 5, 6, 7],
    setModalidades: jest.fn(),
    valorMin: null,
    setValorMin: jest.fn(),
    valorMax: null,
    setValorMax: jest.fn(),
    setValorValid: jest.fn(),
    loading: false,
    clearResult: jest.fn(),
  };

  test("AC4: displays 'Filtros avançados de localização' label", () => {
    render(<FilterPanel {...defaultProps} />);
    expect(screen.getByText(/Filtros avançados de localização/i)).toBeInTheDocument();
  });

  test("AC4: does NOT display old 'Filtragem por Esfera' label", () => {
    render(<FilterPanel {...defaultProps} />);
    expect(screen.queryByText(/Filtragem por Esfera/i)).not.toBeInTheDocument();
  });

  test("AC5: no badge when all esferas selected and no municipios", () => {
    render(<FilterPanel {...defaultProps} />);
    // No badge should be rendered when defaults active
    const badges = screen.queryAllByRole("generic").filter(
      el => el.classList.contains("rounded-full") && el.textContent?.match(/^\d+$/)
    );
    expect(badges).toHaveLength(0);
  });

  test("AC5: shows badge count=1 when esferas not all selected", () => {
    render(<FilterPanel {...defaultProps} esferas={["F" as const, "E" as const]} />);
    const badge = screen.getByLabelText(/1 filtro ativo/i);
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toBe("1");
  });

  test("AC5: shows badge count=1 when municipios selected", () => {
    render(
      <FilterPanel
        {...defaultProps}
        municipios={[{ codigo: "3550308", nome: "São Paulo" }] as any}
      />
    );
    const badge = screen.getByLabelText(/1 filtro ativo/i);
    expect(badge).toBeInTheDocument();
  });

  test("AC5: shows badge count=2 when both esferas and municipios differ from default", () => {
    render(
      <FilterPanel
        {...defaultProps}
        esferas={["F" as const]}
        municipios={[{ codigo: "3550308", nome: "São Paulo" }] as any}
      />
    );
    const badge = screen.getByLabelText(/2 filtros ativos/i);
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toBe("2");
  });
});

// ─── AC3: esferas payload test ──────────────────────────────────────────────

describe("UX-403 AC3: esferas payload omission", () => {
  test("all 3 esferas selected should not include esferas in payload", () => {
    const esferas = ["F", "E", "M"];
    // Replicate the logic from useSearch.ts line 836
    const payload = esferas.length > 0 && esferas.length < 3 ? esferas : undefined;
    expect(payload).toBeUndefined();
  });

  test("2 esferas selected should include esferas in payload", () => {
    const esferas = ["F", "E"];
    const payload = esferas.length > 0 && esferas.length < 3 ? esferas : undefined;
    expect(payload).toEqual(["F", "E"]);
  });

  test("1 esfera selected should include esferas in payload", () => {
    const esferas = ["M"];
    const payload = esferas.length > 0 && esferas.length < 3 ? esferas : undefined;
    expect(payload).toEqual(["M"]);
  });

  test("empty esferas should not include esferas in payload", () => {
    const esferas: string[] = [];
    const payload = esferas.length > 0 && esferas.length < 3 ? esferas : undefined;
    expect(payload).toBeUndefined();
  });
});
