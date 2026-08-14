/**
 * First inbound vertical — /licitacoes/[setor]
 * No SaaS CTA; honesty + CONFENGE consultative path.
 */
import React from "react";
import { render, screen } from "@testing-library/react";

global.fetch = (() =>
  Promise.resolve({ ok: true, json: () => Promise.resolve({}) })) as unknown as typeof fetch;

jest.mock("next/link", () => {
  return ({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [k: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("next/navigation", () => ({
  notFound: jest.fn(),
}));

jest.mock("@/lib/sectors", () => ({
  getSectorBySlug: jest.fn(),
  getAllSectorSlugs: jest.fn(() => ["saude"]),
  getRelatedSectors: jest.fn(() => []),
  fetchSectorStats: jest.fn(),
  formatBRL: jest.fn((v: number) => `R$ ${v}`),
  SECTORS: [],
}));
jest.mock("@/data/sector-faqs", () => ({ getSectorFaqs: jest.fn(() => []) }));
jest.mock("@/lib/seo", () => ({ getFreshnessLabel: jest.fn(() => "Hoje") }));
jest.mock("@/components/seo/MicroDemo", () => ({ MicroDemo: () => null }));
jest.mock("@/components/seo/MicroDemoSchema", () => ({ MicroDemoSchema: () => null }));
jest.mock("@/lib/programmatic", () => ({ UF_NAMES: { SP: "São Paulo" } }));

const { getSectorBySlug, fetchSectorStats, getRelatedSectors } = require("@/lib/sectors");
const { getSectorFaqs } = require("@/data/sector-faqs");
import SectorPage from "@/app/licitacoes/[setor]/page";

const MOCK_SECTOR = {
  id: "saude",
  name: "Saúde",
  slug: "saude",
  description: "Setor de saúde pública",
};

describe("/licitacoes/[setor] first inbound vertical", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getSectorBySlug.mockReturnValue(MOCK_SECTOR);
    getSectorFaqs.mockReturnValue([]);
    getRelatedSectors.mockReturnValue([]);
    fetchSectorStats.mockResolvedValue({
      total_open: 10,
      total_value: 1_000_000,
      avg_value: 100_000,
      top_ufs: [{ name: "SP", count: 5 }],
      sample_items: [],
      last_updated: "2026-05-04T12:00:00Z",
    });
  });

  it("shows honesty + CONFENGE CTAs and no SaaS signup", async () => {
    const ui = await SectorPage({ params: Promise.resolve({ setor: "saude" }) });
    const { container } = render(ui as React.ReactElement);
    const html = container.innerHTML;

    expect(screen.getByTestId("provenance-bar")).toBeInTheDocument();
    expect(screen.getByTestId("data-state-banner")).toBeInTheDocument();
    expect(screen.getByTestId("family-cta")).toHaveAttribute(
      "data-cta-id",
      "cta.tender.go_nogo",
    );

    expect(html).not.toMatch(/href=["'][^"']*\/signup/);
    expect(html).not.toMatch(/href=["'][^"']*\/planos/);
    expect(html).not.toMatch(/href=["'][^"']*\/pricing/);
    expect(html).not.toMatch(/Começar Grátis|teste grátis|14 dias|trial grátis/i);
    expect(html).toMatch(/\/consultoria-b2g/);
    expect(html).toMatch(/Pedir diagnóstico à CONFENGE/);
  });
});
