/**
 * STORY-449: ReferralToast tests
 */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ReferralToast, shouldShowReferralToast } from "@/app/buscar/components/ReferralToast";

// Mock Next.js Link
jest.mock("next/link", () => {
  return function MockLink({ children, href, onClick, ...rest }: any) {
    return <a href={href} onClick={onClick} {...rest}>{children}</a>;
  };
});

function setupStorage() {
  sessionStorage.clear();
  localStorage.clear();
}

describe("ReferralToast", () => {
  beforeEach(() => {
    setupStorage();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    setupStorage();
  });

  it("renders toast with referral message", () => {
    const onClose = jest.fn();
    render(<ReferralToast onClose={onClose} />);
    expect(screen.getByTestId("referral-toast")).toBeInTheDocument();
    expect(screen.getByText(/Indique um amigo/i)).toBeInTheDocument();
  });

  it("calls onClose and tracks dismiss when X button clicked", () => {
    const onClose = jest.fn();
    const onTrack = jest.fn();
    render(<ReferralToast onClose={onClose} onTrack={onTrack} />);

    fireEvent.click(screen.getByTestId("referral-toast-dismiss"));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onTrack).toHaveBeenCalledWith("referral_prompt_dismissed");
    expect(localStorage.getItem("smartlic_referral_shown_at")).not.toBeNull();
  });

  it("auto-closes after 8 seconds and saves timestamp", async () => {
    const onClose = jest.fn();
    const onTrack = jest.fn();
    render(<ReferralToast onClose={onClose} onTrack={onTrack} />);

    act(() => { jest.advanceTimersByTime(8000); });

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onTrack).toHaveBeenCalledWith("referral_prompt_dismissed");
  });

  it("saves sessionStorage key on mount", () => {
    render(<ReferralToast onClose={jest.fn()} />);
    expect(sessionStorage.getItem("referral_shown_session")).toBe("1");
  });

  it("calls onTrack with referral_prompt_clicked on link click", () => {
    const onClose = jest.fn();
    const onTrack = jest.fn();
    render(<ReferralToast onClose={onClose} onTrack={onTrack} />);

    fireEvent.click(screen.getByTestId("referral-toast-link"));

    expect(onTrack).toHaveBeenCalledWith("referral_prompt_clicked");
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe("shouldShowReferralToast", () => {
  beforeEach(() => {
    setupStorage();
  });

  afterEach(() => {
    setupStorage();
  });

  it("returns true when no throttle state exists", () => {
    expect(shouldShowReferralToast()).toBe(true);
  });

  it("returns false when sessionStorage key is set", () => {
    sessionStorage.setItem("referral_shown_session", "1");
    expect(shouldShowReferralToast()).toBe(false);
  });

  it("returns false when localStorage timestamp is within 7 days", () => {
    localStorage.setItem("smartlic_referral_shown_at", String(Date.now() - 1000 * 60 * 60));
    expect(shouldShowReferralToast()).toBe(false);
  });

  it("returns true when localStorage timestamp is older than 7 days", () => {
    const eightDaysAgo = Date.now() - 8 * 24 * 60 * 60 * 1000;
    localStorage.setItem("smartlic_referral_shown_at", String(eightDaysAgo));
    expect(shouldShowReferralToast()).toBe(true);
  });
});
