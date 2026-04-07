/**
 * STORY-312: TrialUpsellCTA component tests
 * AC12: Tests for each variant (5 variants x render + dismiss + click)
 * AC13: Frequency max test (1 per session)
 * AC14: Test CTA hidden for paid users
 * AC15: Zero regressions
 */

import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TrialUpsellCTA, type UpsellVariant } from "../../components/billing/TrialUpsellCTA";

// Mock useAnalytics
const mockTrackEvent = jest.fn();
jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

// Mock useExperiments
jest.mock("../../hooks/useExperiments", () => ({
  useExperiments: () => ({
    experiments: {},
    getVariant: () => null,
    getExperimentProperties: () => ({}),
    isLoaded: true,
  }),
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({ children, href, onClick, ...props }: any) {
    return (
      <a href={href} onClick={onClick} {...props}>
        {children}
      </a>
    );
  };
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const SESSION_KEY = "smartlic_upsell_shown_count";
const DISMISS_PREFIX = "smartlic_upsell_dismiss_";

function clearStorage() {
  sessionStorage.clear();
  localStorage.clear();
}

const TRIAL_PLAN = {
  planId: "free_trial" as string | null | undefined,
  subscriptionStatus: "trial",
};

const PAID_PLAN = {
  planId: "smartlic_pro" as string | null | undefined,
  subscriptionStatus: "active",
};

const EXPIRED_TRIAL = {
  planId: "free_trial" as string | null | undefined,
  subscriptionStatus: "expired",
};

const ALL_VARIANTS: UpsellVariant[] = [
  "post-search",
  "post-download",
  "post-pipeline",
  "dashboard",
  "quota",
];

const CONTEXT_BY_VARIANT: Record<UpsellVariant, Record<string, any>> = {
  "post-search": { opportunities: 15 },
  "post-download": { exportLimit: 1000 },
  "post-pipeline": { pipelineLimit: 1000 },
  dashboard: { valor: "150.5k" },
  quota: { usageLabel: "40/50", usagePct: 80 },
};

// ---------------------------------------------------------------------------
// AC12: Tests for each variant (render + dismiss + click)
// ---------------------------------------------------------------------------

describe("TrialUpsellCTA", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    clearStorage();
  });

  describe("AC12: Per-variant render, dismiss, click", () => {
    ALL_VARIANTS.forEach((variant) => {
      describe(`variant: ${variant}`, () => {
        it("renders for trial user", () => {
          render(
            <TrialUpsellCTA
              variant={variant}
              {...TRIAL_PLAN}
              contextData={CONTEXT_BY_VARIANT[variant]}
            />
          );
          expect(screen.getByTestId(`trial-upsell-${variant}`)).toBeInTheDocument();
        });

        it("tracks trial_upsell_shown on render", () => {
          render(
            <TrialUpsellCTA
              variant={variant}
              {...TRIAL_PLAN}
              contextData={CONTEXT_BY_VARIANT[variant]}
            />
          );
          expect(mockTrackEvent).toHaveBeenCalledWith(
            "trial_upsell_shown",
            expect.objectContaining({ variant })
          );
        });

        it("dismisses and tracks trial_upsell_dismissed", async () => {
          const user = userEvent.setup();
          render(
            <TrialUpsellCTA
              variant={variant}
              {...TRIAL_PLAN}
              contextData={CONTEXT_BY_VARIANT[variant]}
            />
          );

          const dismissBtn = screen.getByTestId(`trial-upsell-${variant}-dismiss`);
          await user.click(dismissBtn);

          expect(screen.queryByTestId(`trial-upsell-${variant}`)).not.toBeInTheDocument();
          expect(mockTrackEvent).toHaveBeenCalledWith("trial_upsell_dismissed", { variant });
        });

        it("does not re-render after dismiss (24h localStorage)", () => {
          // First render + dismiss
          const { unmount } = render(
            <TrialUpsellCTA
              variant={variant}
              {...TRIAL_PLAN}
              contextData={CONTEXT_BY_VARIANT[variant]}
            />
          );
          // Simulate dismiss via localStorage (already set by the component)
          localStorage.setItem(DISMISS_PREFIX + variant, String(Date.now()));
          unmount();

          // Clear session counter to isolate dismiss test
          sessionStorage.removeItem(SESSION_KEY);

          // Re-render — should not appear
          render(
            <TrialUpsellCTA
              variant={variant}
              {...TRIAL_PLAN}
              contextData={CONTEXT_BY_VARIANT[variant]}
            />
          );
          expect(screen.queryByTestId(`trial-upsell-${variant}`)).not.toBeInTheDocument();
        });

        it("CTA link points to /planos and tracks click", async () => {
          const user = userEvent.setup();
          render(
            <TrialUpsellCTA
              variant={variant}
              {...TRIAL_PLAN}
              contextData={CONTEXT_BY_VARIANT[variant]}
            />
          );

          const cta = screen.getByTestId(`trial-upsell-${variant}-cta`);
          expect(cta).toHaveAttribute("href", "/planos");

          await user.click(cta);
          expect(mockTrackEvent).toHaveBeenCalledWith(
            "trial_upsell_clicked",
            expect.objectContaining({ variant })
          );
        });
      });
    });
  });

  // ---------------------------------------------------------------------------
  // AC13: Frequency max (1 per session, except quota)
  // ---------------------------------------------------------------------------

  describe("AC13: Session frequency control", () => {
    it("only shows 1 non-quota CTA per session", () => {
      // First CTA renders
      const { unmount: u1 } = render(
        <TrialUpsellCTA
          variant="post-search"
          {...TRIAL_PLAN}
          contextData={{ opportunities: 20 }}
        />
      );
      expect(screen.getByTestId("trial-upsell-post-search")).toBeInTheDocument();
      u1();

      // Second non-quota CTA should NOT render (session limit reached)
      render(
        <TrialUpsellCTA
          variant="post-download"
          {...TRIAL_PLAN}
          contextData={{ exportLimit: 1000 }}
        />
      );
      expect(screen.queryByTestId("trial-upsell-post-download")).not.toBeInTheDocument();
    });

    it("quota variant always shows regardless of session count", () => {
      // First: show a non-quota CTA (consumes session slot)
      const { unmount: u1 } = render(
        <TrialUpsellCTA
          variant="dashboard"
          {...TRIAL_PLAN}
          contextData={{ valor: "100k" }}
        />
      );
      expect(screen.getByTestId("trial-upsell-dashboard")).toBeInTheDocument();
      u1();

      // Quota CTA should still show (AC7 exception)
      render(
        <TrialUpsellCTA
          variant="quota"
          {...TRIAL_PLAN}
          contextData={{ usageLabel: "40/50", usagePct: 80 }}
        />
      );
      expect(screen.getByTestId("trial-upsell-quota")).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // AC14: CTA hidden for paid users
  // ---------------------------------------------------------------------------

  describe("AC14: Hidden for paid users", () => {
    ALL_VARIANTS.forEach((variant) => {
      it(`does not render ${variant} for paid user (smartlic_pro)`, () => {
        render(
          <TrialUpsellCTA
            variant={variant}
            {...PAID_PLAN}
            contextData={CONTEXT_BY_VARIANT[variant]}
          />
        );
        expect(screen.queryByTestId(`trial-upsell-${variant}`)).not.toBeInTheDocument();
      });
    });

    it("does not render for expired trial (TrialConversionScreen handles it)", () => {
      render(
        <TrialUpsellCTA
          variant="post-search"
          {...EXPIRED_TRIAL}
          contextData={{ opportunities: 20 }}
        />
      );
      expect(screen.queryByTestId("trial-upsell-post-search")).not.toBeInTheDocument();
    });

    it("does not render when planId is null", () => {
      render(
        <TrialUpsellCTA
          variant="post-search"
          planId={null}
          subscriptionStatus={undefined}
          contextData={{ opportunities: 20 }}
        />
      );
      expect(screen.queryByTestId("trial-upsell-post-search")).not.toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Variant-specific copy validation
  // ---------------------------------------------------------------------------

  describe("Copy validation", () => {
    it("post-search shows opportunity count in message", () => {
      render(
        <TrialUpsellCTA
          variant="post-search"
          {...TRIAL_PLAN}
          contextData={{ opportunities: 42 }}
        />
      );
      expect(screen.getByText(/42 oportunidades/)).toBeInTheDocument();
    });

    it("dashboard shows value in message", () => {
      render(
        <TrialUpsellCTA
          variant="dashboard"
          {...TRIAL_PLAN}
          contextData={{ valor: "2.5M" }}
        />
      );
      expect(screen.getByText(/R\$2\.5M/)).toBeInTheDocument();
    });

    it("quota shows usage label in message", () => {
      render(
        <TrialUpsellCTA
          variant="quota"
          {...TRIAL_PLAN}
          contextData={{ usageLabel: "800/1000", usagePct: 80 }}
        />
      );
      expect(screen.getByText(/800\/1000/)).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Dismiss TTL (24h expiry)
  // ---------------------------------------------------------------------------

  describe("Dismiss TTL", () => {
    it("re-shows CTA after 24h dismiss expiry", () => {
      // Set dismiss timestamp 25 hours ago
      const twentyFiveHoursAgo = Date.now() - 25 * 60 * 60 * 1000;
      localStorage.setItem(DISMISS_PREFIX + "post-search", String(twentyFiveHoursAgo));

      render(
        <TrialUpsellCTA
          variant="post-search"
          {...TRIAL_PLAN}
          contextData={{ opportunities: 20 }}
        />
      );
      // Should show because dismiss expired
      expect(screen.getByTestId("trial-upsell-post-search")).toBeInTheDocument();
    });
  });
});
