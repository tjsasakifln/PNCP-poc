/**
 * Tests for GTM-RESILIENCE-D05 AC12: FeedbackButtons component.
 *
 * Tests:
 * 1. Thumbs-up sends "correct" feedback
 * 2. Thumbs-down opens category dropdown
 * 3. Category selection sends feedback with category
 * 4. localStorage prevents re-submit
 * 5. Visual state changes after feedback
 * 6. Toast appears after submission
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import FeedbackButtons from "../app/buscar/components/FeedbackButtons";

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch as any;

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: jest.fn((key: string) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

beforeEach(() => {
  jest.clearAllMocks();
  localStorageMock.clear();
  mockFetch.mockResolvedValue({
    ok: true,
    json: async () => ({ id: "fb-001", received_at: "2026-02-20T00:00:00Z", updated: false }),
  });
});

const defaultProps = {
  searchId: "search-001",
  bidId: "bid-001",
  setorId: "vestuario",
  bidObjeto: "Uniforme escolar",
  bidValor: 50000,
  bidUf: "SP",
  accessToken: "test-token",
};

// --- AC12 Test 1: Thumbs-up sends correct feedback ---

test("thumbs-up sends correct feedback via API", async () => {
  render(<FeedbackButtons {...defaultProps} />);

  const thumbsUp = screen.getByLabelText("Marcar como relevante");
  await act(async () => {
    fireEvent.click(thumbsUp);
  });

  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/feedback",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"user_verdict":"correct"'),
      })
    );
  });
});

// --- AC12 Test 2: Thumbs-down opens dropdown ---

test("thumbs-down opens category dropdown", () => {
  render(<FeedbackButtons {...defaultProps} />);

  const thumbsDown = screen.getByLabelText("Marcar como irrelevante");
  fireEvent.click(thumbsDown);

  expect(screen.getByText("Setor errado")).toBeInTheDocument();
  expect(screen.getByText("Modalidade irrelevante")).toBeInTheDocument();
  expect(screen.getByText("Valor muito baixo")).toBeInTheDocument();
  expect(screen.getByText("Valor muito alto")).toBeInTheDocument();
  expect(screen.getByText("Ja encerrada")).toBeInTheDocument();
  expect(screen.getByText("Outro motivo")).toBeInTheDocument();
});

// --- AC12 Test 3: Category selection sends feedback ---

test("selecting 'Setor errado' sends feedback with category", async () => {
  render(<FeedbackButtons {...defaultProps} />);

  // Open dropdown
  const thumbsDown = screen.getByLabelText("Marcar como irrelevante");
  fireEvent.click(thumbsDown);

  // Select category
  await act(async () => {
    fireEvent.click(screen.getByText("Setor errado"));
  });

  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/feedback",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"category":"wrong_sector"'),
      })
    );
  });
});

// --- AC12 Test 4: localStorage prevents re-submit ---

test("feedback persisted in localStorage prevents re-submit", async () => {
  // Pre-populate localStorage
  localStorageMock.getItem.mockReturnValueOnce(
    JSON.stringify({ verdict: "correct" })
  );

  render(<FeedbackButtons {...defaultProps} />);

  // Wait for useEffect to read localStorage
  await waitFor(() => {
    const thumbsUp = screen.getByLabelText("Marcado como relevante");
    expect(thumbsUp).toBeDisabled();
  });
});

// --- AC12 Test 5: Visual state changes after feedback ---

test("visual state changes after feedback sent", async () => {
  render(<FeedbackButtons {...defaultProps} />);

  const thumbsUp = screen.getByLabelText("Marcar como relevante");
  await act(async () => {
    fireEvent.click(thumbsUp);
  });

  await waitFor(() => {
    expect(screen.getByLabelText("Marcado como relevante")).toBeInTheDocument();
  });
});

// --- AC12 Test 6: Toast appears after submission ---

test("toast confirmation appears after feedback sent", async () => {
  render(<FeedbackButtons {...defaultProps} />);

  const thumbsUp = screen.getByLabelText("Marcar como relevante");
  await act(async () => {
    fireEvent.click(thumbsUp);
  });

  await waitFor(() => {
    expect(
      screen.getByText("Feedback recebido. Obrigado por nos ajudar a melhorar!")
    ).toBeInTheDocument();
  });
});

// --- Extra: "Outro motivo" opens text field ---

test("selecting 'Outro motivo' opens text input", () => {
  render(<FeedbackButtons {...defaultProps} />);

  const thumbsDown = screen.getByLabelText("Marcar como irrelevante");
  fireEvent.click(thumbsDown);
  fireEvent.click(screen.getByText("Outro motivo"));

  expect(screen.getByPlaceholderText("Motivo (max 200 chars)")).toBeInTheDocument();
});

// --- Extra: Context fields included in API call ---

test("context fields sent with feedback", async () => {
  render(<FeedbackButtons {...defaultProps} />);

  const thumbsUp = screen.getByLabelText("Marcar como relevante");
  await act(async () => {
    fireEvent.click(thumbsUp);
  });

  await waitFor(() => {
    const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(callBody.setor_id).toBe("vestuario");
    expect(callBody.bid_uf).toBe("SP");
    expect(callBody.bid_valor).toBe(50000);
    expect(callBody.bid_objeto).toBe("Uniforme escolar");
  });
});

// --- Extra: Auth header included ---

test("authorization header included in API call", async () => {
  render(<FeedbackButtons {...defaultProps} />);

  const thumbsUp = screen.getByLabelText("Marcar como relevante");
  await act(async () => {
    fireEvent.click(thumbsUp);
  });

  await waitFor(() => {
    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders.Authorization).toBe("Bearer test-token");
  });
});
