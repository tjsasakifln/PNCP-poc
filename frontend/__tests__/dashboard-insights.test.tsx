/**
 * DEBT-127: Dashboard Actionable Insights Tests
 *
 * Covers:
 * - PipelineAlerts card (AC1-AC4)
 * - NewOpportunities card (AC6-AC9)
 * - InsightCards container (AC10-AC12)
 * - CTA links (AC2, AC7)
 */

import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

jest.mock("next/link", () => {
  return function MockLink(props: Record<string, unknown>) {
    const { children, href, ...rest } = props;
    return <a href={href as string} {...rest}>{children as React.ReactNode}</a>;
  };
});

import { InsightCards } from "../app/dashboard/components/InsightCards";
import type {
  PipelineAlertsData,
  NewOpportunitiesData,
} from "../app/dashboard/components/DashboardTypes";

// ─── Test Data ──────────────────────────────────────────────────────────

const mockAlertsWithItems: PipelineAlertsData = {
  items: [
    {
      id: "item-1",
      pncp_id: "pncp-001",
      objeto: "Construcao de escola",
      orgao: "Prefeitura de SP",
      uf: "SP",
      data_encerramento: "2026-03-15T23:59:59Z",
      stage: "analise",
    },
    {
      id: "item-2",
      pncp_id: "pncp-002",
      objeto: "Reforma predial",
      orgao: "Governo RJ",
      uf: "RJ",
      data_encerramento: "2026-03-17T23:59:59Z",
      stage: "descoberta",
    },
  ],
  total: 2,
};

const mockAlertsEmpty: PipelineAlertsData = {
  items: [],
  total: 0,
};

const mockOpportunitiesWithSearch: NewOpportunitiesData = {
  count: 42,
  has_previous_search: true,
  last_search_at: "2026-03-08T14:00:00Z",
  days_since_last_search: 3,
};

const mockOpportunitiesToday: NewOpportunitiesData = {
  count: 15,
  has_previous_search: true,
  last_search_at: "2026-03-11T10:00:00Z",
  days_since_last_search: 0,
};

const mockOpportunitiesYesterday: NewOpportunitiesData = {
  count: 20,
  has_previous_search: true,
  last_search_at: "2026-03-10T10:00:00Z",
  days_since_last_search: 1,
};

const mockNoSearch: NewOpportunitiesData = {
  count: 0,
  has_previous_search: false,
};

// ─── Tests ──────────────────────────────────────────────────────────────

describe("DEBT-127: InsightCards", () => {
  describe("AC10: Rendering container", () => {
    it("should render insight cards section when data is available", () => {
      render(
        <InsightCards
          pipelineAlerts={mockAlertsWithItems}
          newOpportunities={mockOpportunitiesWithSearch}
        />
      );
      expect(screen.getByTestId("insight-cards")).toBeInTheDocument();
    });

    it("should not render when both are null", () => {
      const { container } = render(
        <InsightCards pipelineAlerts={null} newOpportunities={null} />
      );
      expect(container.firstChild).toBeNull();
    });

    it("should render even if only one card has data", () => {
      render(
        <InsightCards pipelineAlerts={mockAlertsWithItems} newOpportunities={null} />
      );
      expect(screen.getByTestId("insight-cards")).toBeInTheDocument();
      expect(screen.getByTestId("pipeline-alerts-card")).toBeInTheDocument();
    });
  });

  describe("AC1-AC4: Pipeline Alerts Card", () => {
    it("AC1/AC2: should show count of items with deadlines this week", () => {
      render(
        <InsightCards
          pipelineAlerts={mockAlertsWithItems}
          newOpportunities={null}
        />
      );
      expect(
        screen.getByText("2 editais vencem esta semana")
      ).toBeInTheDocument();
    });

    it("AC2: should link to /pipeline when there are alerts", () => {
      render(
        <InsightCards
          pipelineAlerts={mockAlertsWithItems}
          newOpportunities={null}
        />
      );
      const link = screen.getByTestId("pipeline-alerts-cta");
      expect(link).toHaveAttribute("href", "/pipeline");
      expect(link).toHaveTextContent("Ver no pipeline");
    });

    it("AC1: should show singular form for 1 item", () => {
      const singleAlert: PipelineAlertsData = {
        items: [mockAlertsWithItems.items[0]],
        total: 1,
      };
      render(
        <InsightCards pipelineAlerts={singleAlert} newOpportunities={null} />
      );
      expect(
        screen.getByText("1 edital vence esta semana")
      ).toBeInTheDocument();
    });

    it("AC4: should show encouraging message when no deadlines", () => {
      render(
        <InsightCards pipelineAlerts={mockAlertsEmpty} newOpportunities={null} />
      );
      expect(
        screen.getByText("Nenhum prazo urgente")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Todos os prazos do seu pipeline estão em dia")
      ).toBeInTheDocument();
    });

    it("AC4: should not show CTA link when no alerts", () => {
      render(
        <InsightCards pipelineAlerts={mockAlertsEmpty} newOpportunities={null} />
      );
      expect(screen.queryByTestId("pipeline-alerts-cta")).not.toBeInTheDocument();
    });
  });

  describe("AC6-AC9: New Opportunities Card", () => {
    it("AC6/AC7: should show count with days context", () => {
      render(
        <InsightCards
          pipelineAlerts={null}
          newOpportunities={mockOpportunitiesWithSearch}
        />
      );
      expect(
        screen.getByText(/42 oportunidades na sua última busca/)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Última busca há 3 dias/)
      ).toBeInTheDocument();
    });

    it("AC7: should link to /buscar with CTA", () => {
      render(
        <InsightCards
          pipelineAlerts={null}
          newOpportunities={mockOpportunitiesWithSearch}
        />
      );
      const link = screen.getByTestId("new-opportunities-cta");
      expect(link).toHaveAttribute("href", "/buscar");
      expect(link).toHaveTextContent("Buscar novamente");
    });

    it("AC8: should show 'hoje' for same-day search", () => {
      render(
        <InsightCards
          pipelineAlerts={null}
          newOpportunities={mockOpportunitiesToday}
        />
      );
      expect(
        screen.getByText(/Busca realizada hoje/)
      ).toBeInTheDocument();
    });

    it("AC8: should show 'ontem' for yesterday search", () => {
      render(
        <InsightCards
          pipelineAlerts={null}
          newOpportunities={mockOpportunitiesYesterday}
        />
      );
      expect(
        screen.getByText(/Última busca há ontem/)
      ).toBeInTheDocument();
    });

    it("AC9: should show onboarding prompt when no previous search", () => {
      render(
        <InsightCards pipelineAlerts={null} newOpportunities={mockNoSearch} />
      );
      expect(
        screen.getByText(/Faça sua primeira busca/)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Descubra oportunidades de licitação/)
      ).toBeInTheDocument();
    });

    it("AC9: onboarding prompt links to /buscar", () => {
      render(
        <InsightCards pipelineAlerts={null} newOpportunities={mockNoSearch} />
      );
      const link = screen.getByTestId("new-opportunities-cta");
      expect(link).toHaveAttribute("href", "/buscar");
      expect(link).toHaveTextContent("Buscar oportunidades");
    });

    it("AC2 (UX-431): shows custom label when label field is present", () => {
      const dataWithLabel: NewOpportunitiesData = {
        count: 394,
        has_previous_search: true,
        last_search_at: "2026-03-11T09:57:00Z",
        days_since_last_search: 0,
        label: "Última busca concluída",
      };
      render(
        <InsightCards pipelineAlerts={null} newOpportunities={dataWithLabel} />
      );
      expect(
        screen.getByText(/394 oportunidades na sua Última busca concluída/)
      ).toBeInTheDocument();
    });

    it("AC2 (UX-431): shows default 'última busca' text when label is absent", () => {
      render(
        <InsightCards
          pipelineAlerts={null}
          newOpportunities={mockOpportunitiesWithSearch}
        />
      );
      expect(
        screen.getByText(/42 oportunidades na sua última busca/)
      ).toBeInTheDocument();
    });
  });

  describe("AC12: Mobile responsive layout", () => {
    it("should use grid layout that stacks on mobile", () => {
      render(
        <InsightCards
          pipelineAlerts={mockAlertsWithItems}
          newOpportunities={mockOpportunitiesWithSearch}
        />
      );
      const container = screen.getByTestId("insight-cards");
      expect(container.className).toContain("grid-cols-1");
      expect(container.className).toContain("md:grid-cols-2");
    });
  });
});
