/**
 * STORY-445: NewBidsNotificationBadge tests
 */

import React from "react";
import { render, screen } from "@testing-library/react";

// Mock SWR
jest.mock("swr", () => {
  const actual = jest.requireActual("swr");
  return {
    ...actual,
    __esModule: true,
    default: jest.fn(),
    mutate: jest.fn(),
  };
});

// Mock AuthProvider
jest.mock("@/app/components/AuthProvider", () => ({
  useAuth: jest.fn(),
}));

import useSWR from "swr";
import { useAuth } from "@/app/components/AuthProvider";
import { NewBidsNotificationBadge } from "@/components/NewBidsNotificationBadge";

const mockUseSWR = useSWR as jest.MockedFunction<typeof useSWR>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe("NewBidsNotificationBadge", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders nothing when count is 0", () => {
    mockUseAuth.mockReturnValue({ session: { access_token: "tok" } } as any);
    mockUseSWR.mockReturnValue({ data: { count: 0 } } as any);

    const { container } = render(<NewBidsNotificationBadge />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when no session", () => {
    mockUseAuth.mockReturnValue({ session: null } as any);
    mockUseSWR.mockReturnValue({ data: undefined } as any);

    const { container } = render(<NewBidsNotificationBadge />);
    expect(container.firstChild).toBeNull();
  });

  it("renders badge with count > 0", () => {
    mockUseAuth.mockReturnValue({ session: { access_token: "tok" } } as any);
    mockUseSWR.mockReturnValue({ data: { count: 5 } } as any);

    render(<NewBidsNotificationBadge />);
    expect(screen.getByTestId("new-bids-badge")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows 99+ for counts above 99", () => {
    mockUseAuth.mockReturnValue({ session: { access_token: "tok" } } as any);
    mockUseSWR.mockReturnValue({ data: { count: 150 } } as any);

    render(<NewBidsNotificationBadge />);
    expect(screen.getByText("99+")).toBeInTheDocument();
  });

  it("renders nothing when data is undefined (loading)", () => {
    mockUseAuth.mockReturnValue({ session: { access_token: "tok" } } as any);
    mockUseSWR.mockReturnValue({ data: undefined } as any);

    const { container } = render(<NewBidsNotificationBadge />);
    expect(container.firstChild).toBeNull();
  });
});
