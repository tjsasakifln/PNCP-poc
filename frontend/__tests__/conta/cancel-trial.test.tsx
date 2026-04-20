/**
 * STORY-CONV-003c AC7: cancel-trial page render tests.
 *
 * Scope: fetch + render happy/error/already-cancelled paths. The POST
 * cancel flow is asserted via click → fetch stub verification.
 */
/** @jest-environment jsdom */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock next/navigation BEFORE importing the component under test.
const mockPush = jest.fn();
const mockGet = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: mockGet }),
}));

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

import CancelTrialPage from "../../app/conta/cancelar-trial/page";

function mockFetch(...responses: Array<{ ok: boolean; status?: number; body: unknown }>) {
  const impls = responses.map((r) => async () => ({
    ok: r.ok,
    status: r.status ?? (r.ok ? 200 : 500),
    json: async () => r.body,
  }));
  (global as any).fetch = jest.fn().mockImplementation(() => impls.shift()!());
}

describe("CancelTrialPage", () => {
  beforeEach(() => {
    mockPush.mockReset();
    mockGet.mockReset();
  });

  afterEach(() => {
    (global as any).fetch = undefined;
  });

  it("shows error when token query param is missing", async () => {
    mockGet.mockReturnValue("");
    render(<CancelTrialPage />);
    await waitFor(() =>
      expect(screen.getByTestId("cancel-trial-error")).toHaveTextContent(
        /Token de cancelamento ausente/i,
      ),
    );
  });

  it("renders confirmation UI after a valid token returns trial info", async () => {
    mockGet.mockReturnValue("jwt.valid.token");
    mockFetch({
      ok: true,
      body: {
        user_id: "u-1",
        email: "founder@b2g.com",
        plan_name: "SmartLic Pro",
        trial_end_ts: Math.floor(Date.now() / 1000) + 86_400,
        already_cancelled: false,
      },
    });
    render(<CancelTrialPage />);
    await waitFor(() =>
      expect(screen.getByTestId("cancel-trial-confirm")).toBeInTheDocument(),
    );
    expect(screen.getByText(/founder@b2g\.com/)).toBeInTheDocument();
    expect(screen.getByText(/SmartLic Pro/)).toBeInTheDocument();
  });

  it("short-circuits to already-cancelled view when backend says so", async () => {
    mockGet.mockReturnValue("jwt.old.token");
    mockFetch({
      ok: true,
      body: {
        user_id: "u-1",
        email: "x@y.com",
        plan_name: "Consultoria",
        trial_end_ts: Math.floor(Date.now() / 1000) + 3600,
        already_cancelled: true,
      },
    });
    render(<CancelTrialPage />);
    await waitFor(() =>
      expect(
        screen.getByTestId("cancel-trial-already-cancelled"),
      ).toBeInTheDocument(),
    );
  });

  it("surfaces 410/400 token errors with the backend message", async () => {
    mockGet.mockReturnValue("jwt.expired.token");
    mockFetch({ ok: false, status: 410, body: { detail: "Token expirado" } });
    render(<CancelTrialPage />);
    await waitFor(() =>
      expect(screen.getByTestId("cancel-trial-error")).toHaveTextContent(
        "Token expirado",
      ),
    );
  });

  it("POSTs { token } on confirm and redirects to /confirmado on success", async () => {
    mockGet.mockReturnValue("jwt.valid.token");
    mockFetch(
      {
        ok: true,
        body: {
          user_id: "u-1",
          email: "a@b.com",
          plan_name: "SmartLic Pro",
          trial_end_ts: Math.floor(Date.now() / 1000) + 86_400,
          already_cancelled: false,
        },
      },
      {
        ok: true,
        body: { cancelled: true, access_until: "2026-05-04T00:00:00Z", already_cancelled: false },
      },
    );
    render(<CancelTrialPage />);
    await waitFor(() =>
      expect(screen.getByTestId("cancel-trial-submit")).toBeInTheDocument(),
    );
    await userEvent.click(screen.getByTestId("cancel-trial-submit"));
    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith("/conta/cancelar-trial/confirmado"),
    );

    // Verify POST payload
    const postCall = (global.fetch as jest.Mock).mock.calls[1];
    expect(postCall[0]).toBe("/api/conta/cancelar-trial");
    expect(postCall[1].method).toBe("POST");
    expect(JSON.parse(postCall[1].body)).toEqual({ token: "jwt.valid.token" });
  });
});
