/**
 * Tests for IntelReportCTA component (#632).
 *
 * Validates the CTA on /cnpj/[cnpj] pages:
 * - Renders with correct copy
 * - Redirects to /consultoria-b2g when unauthenticated (401 from checkout endpoint)
 * - Redirects to checkout_url on successful checkout
 * - Fires Mixpanel events
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useRouter } from "next/navigation";
import IntelReportCTA from "../../app/cnpj/[cnpj]/IntelReportCTA";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() })),
}));

describe("IntelReportCTA", () => {
  const cnpj = "12345678000195";
  let originalFetch: typeof global.fetch;
  let originalLocation: typeof window.location;

  beforeEach(() => {
    originalFetch = global.fetch;
    // jsdom does not allow direct assignment of window.location,
    // so we keep a reference and spy/mock per test.
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  it("renders the buy button with correct copy", () => {
    render(<IntelReportCTA cnpj={cnpj} />);
    expect(
      screen.getByRole("button", { name: /Comprar Raio-X.*R\$197/i }),
    ).toBeInTheDocument();
  });

  it("redirects to /consultoria-b2g when checkout returns 401", async () => {
    const mockPush = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });

    global.fetch = jest.fn().mockResolvedValue({
      status: 401,
      ok: false,
      json: async () => ({ message: "Autenticação necessária" }),
    });

    render(<IntelReportCTA cnpj={cnpj} />);
    fireEvent.click(screen.getByRole("button", { name: /Comprar Raio-X/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        `/consultoria-b2g?ref=cnpj-${cnpj}&intent=intel_report`,
      );
    });
  });

  it("navigates to checkout_url on successful response", async () => {
    const checkoutUrl = "https://checkout.stripe.com/pay/cs_test_abc";

    // window.location.href assignment is tracked by jsdom
    delete (window as unknown as { location?: unknown }).location;
    (window as unknown as { location: { href: string } }).location = {
      href: "",
    };

    global.fetch = jest.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ checkout_url: checkoutUrl, session_id: "cs_test_abc" }),
    });

    render(<IntelReportCTA cnpj={cnpj} />);
    fireEvent.click(screen.getByRole("button", { name: /Comprar Raio-X/i }));

    await waitFor(() => {
      expect(
        (window as unknown as { location: { href: string } }).location.href,
      ).toBe(checkoutUrl);
    });
  });

  it("fires intel_report_cta_clicked Mixpanel event on click", async () => {
    const trackSpy = jest.fn();
    (window as unknown as { mixpanel: { track: jest.Mock } }).mixpanel = {
      track: trackSpy,
    };

    global.fetch = jest.fn().mockResolvedValue({
      status: 401,
      ok: false,
      json: async () => ({}),
    });

    (useRouter as jest.Mock).mockReturnValue({ push: jest.fn() });

    render(<IntelReportCTA cnpj={cnpj} />);
    fireEvent.click(screen.getByRole("button", { name: /Comprar Raio-X/i }));

    await waitFor(() => {
      expect(trackSpy).toHaveBeenCalledWith("intel_report_cta_clicked", {
        cnpj,
        page_path: `/cnpj/${cnpj}`,
      });
    });

    delete (window as unknown as { mixpanel?: unknown }).mixpanel;
  });

  it("does not throw when window.mixpanel is undefined", async () => {
    delete (window as unknown as { mixpanel?: unknown }).mixpanel;

    global.fetch = jest.fn().mockResolvedValue({
      status: 401,
      ok: false,
      json: async () => ({}),
    });

    (useRouter as jest.Mock).mockReturnValue({ push: jest.fn() });

    render(<IntelReportCTA cnpj={cnpj} />);
    expect(() =>
      fireEvent.click(screen.getByRole("button", { name: /Comprar Raio-X/i })),
    ).not.toThrow();
  });

  it("shows loading state while fetching", () => {
    global.fetch = jest.fn().mockImplementation(
      () => new Promise(() => {}), // never resolves
    );

    render(<IntelReportCTA cnpj={cnpj} />);
    const btn = screen.getByRole("button", { name: /Comprar Raio-X/i });
    fireEvent.click(btn);
    expect(screen.getByRole("button", { name: /Aguarde/i })).toBeDisabled();
  });
});
