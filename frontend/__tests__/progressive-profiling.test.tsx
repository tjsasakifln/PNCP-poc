/**
 * STORY-260 AC19 — Progressive Profiling tests
 * Tests ProfileCompletionPrompt, ProfileProgressBar, and ProfileCongratulations.
 */
import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Framer Motion mock (prevent animation issues in jsdom) ───────────────────
jest.mock("framer-motion", () => ({
  motion: {
    div: React.forwardRef(
      (
        { children, className, ...rest }: React.HTMLAttributes<HTMLDivElement>,
        ref: React.Ref<HTMLDivElement>
      ) => (
        <div className={className} ref={ref} {...rest}>
          {children}
        </div>
      )
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ─── localStorage / sessionStorage helpers ────────────────────────────────────
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

const sessionStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock, writable: true });
Object.defineProperty(window, "sessionStorage", { value: sessionStorageMock, writable: true });

// ─── Import components after mocks ────────────────────────────────────────────
import ProfileCompletionPrompt from "../components/ProfileCompletionPrompt";
import ProfileProgressBar from "../components/ProfileProgressBar";
import ProfileCongratulations from "../components/ProfileCongratulations";

// ─── ProfileCompletionPrompt ──────────────────────────────────────────────────
describe("ProfileCompletionPrompt (STORY-260 AC19)", () => {
  beforeEach(() => {
    localStorageMock.clear();
    sessionStorageMock.clear();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders exactly 1 question at a time when API returns a next_question", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 25,
        next_question: "company_size",
        is_complete: false,
      }),
    });

    render(<ProfileCompletionPrompt />);

    await waitFor(() => {
      expect(screen.getByTestId("profile-completion-prompt")).toBeInTheDocument();
    });

    // Exactly one question block rendered
    const prompts = screen.getAllByTestId("profile-completion-prompt");
    expect(prompts).toHaveLength(1);
  });

  it("shows the correct question title for company_size", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 0,
        next_question: "company_size",
        is_complete: false,
      }),
    });

    render(<ProfileCompletionPrompt />);

    await waitFor(() => {
      expect(screen.getByText(/qual o porte da sua empresa/i)).toBeInTheDocument();
    });
  });

  it("shows the correct question title for experience_level", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 25,
        next_question: "experience_level",
        is_complete: false,
      }),
    });

    render(<ProfileCompletionPrompt />);

    await waitFor(() => {
      expect(screen.getByText(/qual sua experiência com licitações/i)).toBeInTheDocument();
    });
  });

  it("calls PUT /api/profile-context when save button is clicked after selecting an option", async () => {
    // First fetch: returns completeness (fetchNextQuestion)
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 0,
        next_question: "company_size",
        is_complete: false,
      }),
    });
    // Second fetch: GET profile-context before merge (handleSave)
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ context_data: {} }),
    });
    // Third fetch: PUT response (save)
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    // Fourth fetch: updated completeness after save
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ completeness_pct: 25, is_complete: false }),
    });

    render(<ProfileCompletionPrompt accessToken="test-token" />);

    // Wait for question to appear
    await waitFor(() => {
      expect(screen.getByTestId("option-mei")).toBeInTheDocument();
    });

    // Select an option
    fireEvent.click(screen.getByTestId("option-mei"));

    // Click save
    const saveBtn = screen.getByTestId("save-button");
    fireEvent.click(saveBtn);

    await waitFor(() => {
      const calls = (global.fetch as jest.Mock).mock.calls;
      const putCall = calls.find(
        ([url, opts]: [string, RequestInit]) =>
          url === "/api/profile-context" && opts?.method === "PUT"
      );
      expect(putCall).toBeDefined();
    });
  });

  it("hides prompt when skip button is clicked", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 0,
        next_question: "company_size",
        is_complete: false,
      }),
    });

    render(<ProfileCompletionPrompt />);

    await waitFor(() => {
      expect(screen.getByTestId("skip-button")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("skip-button"));

    await waitFor(() => {
      expect(screen.queryByTestId("profile-completion-prompt")).not.toBeInTheDocument();
    });
  });

  it("does not render when profile is already complete", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 100,
        next_question: null,
        is_complete: true,
      }),
    });

    render(<ProfileCompletionPrompt />);

    // Allow time for fetch to resolve
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(screen.queryByTestId("profile-completion-prompt")).not.toBeInTheDocument();
  });

  it("does not render when API call fails", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network error"));

    render(<ProfileCompletionPrompt />);

    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(screen.queryByTestId("profile-completion-prompt")).not.toBeInTheDocument();
  });

  it("calls onProfileUpdated callback with updated percentage after save", async () => {
    const onProfileUpdated = jest.fn();

    // 1: fetchNextQuestion → completeness
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 0,
        next_question: "company_size",
        is_complete: false,
      }),
    });
    // 2: handleSave GET existing context before merge
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ context_data: {} }),
    });
    // 3: handleSave PUT new data
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    // 4: post-save completeness check
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ completeness_pct: 25, is_complete: false }),
    });

    render(<ProfileCompletionPrompt onProfileUpdated={onProfileUpdated} />);

    await waitFor(() => {
      expect(screen.getByTestId("option-mei")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("option-mei"));
    fireEvent.click(screen.getByTestId("save-button"));

    await waitFor(() => {
      expect(onProfileUpdated).toHaveBeenCalledWith(25);
    });
  });

  it("shows question progress counter (e.g. 1/4)", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        completeness_pct: 0,
        next_question: "company_size",
        is_complete: false,
      }),
    });

    render(<ProfileCompletionPrompt />);

    await waitFor(() => {
      expect(screen.getByText(/1\/4/)).toBeInTheDocument();
    });
  });
});

// ─── ProfileProgressBar ───────────────────────────────────────────────────────
describe("ProfileProgressBar (STORY-260 AC19)", () => {
  it("renders with red stroke for percentage < 40", () => {
    render(<ProfileProgressBar percentage={25} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toBeInTheDocument();
    // The aria-label should describe incomplete state
    expect(bar).toHaveAttribute("aria-label", expect.stringMatching(/incompleto/i));
  });

  it("renders with yellow stroke for percentage 40-69", () => {
    render(<ProfileProgressBar percentage={55} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveAttribute("aria-label", expect.stringMatching(/em progresso/i));
  });

  it("renders with green stroke for percentage >= 70", () => {
    render(<ProfileProgressBar percentage={80} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveAttribute("aria-label", expect.stringMatching(/excelente/i));
  });

  it("displays the percentage value in the center", () => {
    render(<ProfileProgressBar percentage={42} />);

    expect(screen.getByText("42%")).toBeInTheDocument();
  });

  it("renders as a button when onClickNext prop is provided", () => {
    const onClickNext = jest.fn();
    render(<ProfileProgressBar percentage={30} onClickNext={onClickNext} />);

    const btn = screen.getByTestId("profile-progress-bar");
    expect(btn.tagName).toBe("BUTTON");
  });

  it("calls onClickNext callback when button is clicked", () => {
    const onClickNext = jest.fn();
    render(<ProfileProgressBar percentage={30} onClickNext={onClickNext} />);

    fireEvent.click(screen.getByTestId("profile-progress-bar"));

    expect(onClickNext).toHaveBeenCalledTimes(1);
  });

  it("renders as a div with role=progressbar when no onClickNext provided", () => {
    render(<ProfileProgressBar percentage={60} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar.tagName).toBe("DIV");
    expect(bar).toHaveAttribute("role", "progressbar");
  });

  it("clamps percentage to 0 minimum", () => {
    render(<ProfileProgressBar percentage={-10} />);

    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("clamps percentage to 100 maximum", () => {
    render(<ProfileProgressBar percentage={150} />);

    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("has correct aria-valuenow attribute matching percentage", () => {
    render(<ProfileProgressBar percentage={65} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveAttribute("aria-valuenow", "65");
  });
});

// ─── ProfileCongratulations ───────────────────────────────────────────────────
describe("ProfileCongratulations (STORY-260 AC19)", () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  it("renders congratulations card when not previously dismissed", async () => {
    render(<ProfileCongratulations />);

    await waitFor(() => {
      expect(screen.getByTestId("profile-congratulations")).toBeInTheDocument();
    });
  });

  it("does not render when profile_congratulations_dismissed=true in localStorage", async () => {
    localStorageMock.setItem("profile_congratulations_dismissed", "true");

    render(<ProfileCongratulations />);

    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(screen.queryByTestId("profile-congratulations")).not.toBeInTheDocument();
  });

  it("hides the card when dismiss button is clicked", async () => {
    render(<ProfileCongratulations />);

    await waitFor(() => {
      expect(screen.getByTestId("dismiss-congratulations")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("dismiss-congratulations"));

    await waitFor(() => {
      expect(screen.queryByTestId("profile-congratulations")).not.toBeInTheDocument();
    });
  });

  it("sets localStorage flag to 'true' after dismissal", async () => {
    render(<ProfileCongratulations />);

    await waitFor(() => {
      expect(screen.getByTestId("dismiss-congratulations")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("dismiss-congratulations"));

    await waitFor(() => {
      expect(localStorageMock.getItem("profile_congratulations_dismissed")).toBe("true");
    });
  });

  it("shows 'Perfil completo!' heading text", async () => {
    render(<ProfileCongratulations />);

    await waitFor(() => {
      expect(screen.getByText(/perfil completo!/i)).toBeInTheDocument();
    });
  });

  it("shows the 'Perfil Completo' badge inside the card", async () => {
    render(<ProfileCongratulations />);

    await waitFor(() => {
      // The badge span text
      expect(screen.getByText("Perfil Completo")).toBeInTheDocument();
    });
  });
});
