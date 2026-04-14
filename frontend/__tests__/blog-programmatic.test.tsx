/**
 * MKT-002: Tests for programmatic SEO infrastructure.
 *
 * Tests: SchemaMarkup, BlogCTA, RelatedPages, programmatic helpers, sitemap.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock next/link
jest.mock('next/link', () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

// ---------------------------------------------------------------------------
// SchemaMarkup tests (AC3)
// ---------------------------------------------------------------------------

import SchemaMarkup from '@/components/blog/SchemaMarkup';

describe('SchemaMarkup (AC3)', () => {
  it('renders Article schema for sector pages', () => {
    const { container } = render(
      <SchemaMarkup
        pageType="sector"
        title="Licitações de Vestuário"
        description="Test description"
        url="https://smartlic.tech/blog/programmatic/vestuario"
        sectorName="Vestuário e Uniformes"
      />,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    expect(scripts.length).toBeGreaterThanOrEqual(2); // Article + at least one more

    const schemas = Array.from(scripts).map((s) =>
      JSON.parse(s.textContent || '{}'),
    );

    // Should have Article schema
    const article = schemas.find((s) => s['@type'] === 'Article');
    expect(article).toBeDefined();
    expect(article?.headline).toBe('Licitações de Vestuário');
  });

  it('renders FAQPage schema when FAQs provided', () => {
    // Answers must be >= 300 chars to pass the rich-results eligibility filter (SEO-Sprint2 P6.6)
    const longAnswer = 'Esta é uma resposta completa sobre licitações públicas que fornece informações detalhadas e contextualizadas para o usuário. O processo de licitação pública no Brasil é regido pela Lei 14.133/2021 e envolve diversas modalidades como pregão eletrônico, concorrência e dispensa. Empresas que desejam participar devem estar regularizadas e com documentação em dia.';
    const faqs = [
      { question: 'Test Q?', answer: longAnswer },
      { question: 'Test Q2?', answer: longAnswer },
    ];

    const { container } = render(
      <SchemaMarkup
        pageType="sector"
        title="Test"
        description="Test"
        url="https://smartlic.tech/test"
        faqs={faqs}
      />,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) =>
      JSON.parse(s.textContent || '{}'),
    );

    const faqSchema = schemas.find((s) => s['@type'] === 'FAQPage');
    expect(faqSchema).toBeDefined();
    expect(faqSchema?.mainEntity).toHaveLength(2);
  });

  it('renders Dataset schema with data points', () => {
    const { container } = render(
      <SchemaMarkup
        pageType="sector"
        title="Test"
        description="Test"
        url="https://smartlic.tech/test"
        sectorName="Software"
        totalEditais={42}
        dataPoints={[
          { name: 'Total', value: 42 },
          { name: 'Avg', value: 150000 },
        ]}
      />,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) =>
      JSON.parse(s.textContent || '{}'),
    );

    const dataset = schemas.find((s) => s['@type'] === 'Dataset');
    expect(dataset).toBeDefined();
    expect(dataset?.variableMeasured).toHaveLength(2);
  });

  it('renders HowTo schema for sector pages', () => {
    const { container } = render(
      <SchemaMarkup
        pageType="sector"
        title="Test"
        description="Test"
        url="https://smartlic.tech/test"
        sectorName="Software"
      />,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) =>
      JSON.parse(s.textContent || '{}'),
    );

    const howTo = schemas.find((s) => s['@type'] === 'HowTo');
    expect(howTo).toBeDefined();
    expect(howTo?.step).toHaveLength(4);
  });

  it('renders BreadcrumbList when breadcrumbs provided', () => {
    const breadcrumbs = [
      { name: 'Home', url: 'https://smartlic.tech' },
      { name: 'Blog', url: 'https://smartlic.tech/blog' },
    ];

    const { container } = render(
      <SchemaMarkup
        pageType="sector"
        title="Test"
        description="Test"
        url="https://smartlic.tech/test"
        breadcrumbs={breadcrumbs}
      />,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) =>
      JSON.parse(s.textContent || '{}'),
    );

    const bc = schemas.find((s) => s['@type'] === 'BreadcrumbList');
    expect(bc).toBeDefined();
    expect(bc?.itemListElement).toHaveLength(2);
  });

  it('renders ItemList for sector-uf pages', () => {
    const { container } = render(
      <SchemaMarkup
        pageType="sector-uf"
        title="Test"
        description="Test"
        url="https://smartlic.tech/test"
        sectorName="Software"
        uf="SP"
        totalEditais={25}
      />,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) =>
      JSON.parse(s.textContent || '{}'),
    );

    const itemList = schemas.find((s) => s['@type'] === 'ItemList');
    expect(itemList).toBeDefined();
    expect(itemList?.numberOfItems).toBe(25);
  });

  it('renders LocalBusiness for city pages', () => {
    const { container } = render(
      <SchemaMarkup
        pageType="city"
        title="Test"
        description="Test"
        url="https://smartlic.tech/test"
        cidade="São Paulo"
        uf="SP"
      />,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) =>
      JSON.parse(s.textContent || '{}'),
    );

    const lb = schemas.find((s) => s['@type'] === 'LocalBusiness');
    expect(lb).toBeDefined();
    expect(lb?.address?.addressLocality).toBe('São Paulo');
  });

  it('generates 3-4 schemas per page type', () => {
    const { container: sectorContainer } = render(
      <SchemaMarkup
        pageType="sector"
        title="Test"
        description="Test"
        url="https://smartlic.tech/test"
        sectorName="Software"
        totalEditais={10}
        breadcrumbs={[{ name: 'Home', url: '/' }]}
        faqs={[{ question: 'Q?', answer: 'A.' }]}
      />,
    );

    const sectorSchemas = sectorContainer.querySelectorAll(
      'script[type="application/ld+json"]',
    );
    // Article + Breadcrumb + FAQ + Dataset + HowTo = 5
    expect(sectorSchemas.length).toBeGreaterThanOrEqual(3);
    expect(sectorSchemas.length).toBeLessThanOrEqual(6);
  });
});

// ---------------------------------------------------------------------------
// BlogCTA tests (AC6)
// ---------------------------------------------------------------------------

import BlogCTA from '@/components/blog/BlogCTA';

describe('BlogCTA (AC6)', () => {
  it('renders inline variant', () => {
    render(
      <BlogCTA
        variant="inline"
        setor="Vestuário"
        uf="SP"
        count={42}
        slug="programmatic/vestuario/sp"
      />,
    );

    expect(screen.getByText(/42 licitações/i)).toBeInTheDocument();
    expect(screen.getByText(/Comece Agora/i)).toBeInTheDocument();
  });

  it('renders final variant', () => {
    render(
      <BlogCTA
        variant="final"
        setor="Software"
        count={15}
        slug="programmatic/software"
      />,
    );

    expect(screen.getByText(/15 licitações/i)).toBeInTheDocument();
    expect(screen.getByText(/Começar Teste Grátis/i)).toBeInTheDocument();
  });

  it('includes UTM params in href', () => {
    render(
      <BlogCTA
        variant="inline"
        slug="programmatic/vestuario"
      />,
    );

    const link = screen.getByText(/Comece Agora/i).closest('a');
    expect(link?.getAttribute('href')).toContain('utm_source=blog');
    expect(link?.getAttribute('href')).toContain('utm_medium=programmatic');
    expect(link?.getAttribute('href')).toContain('utm_content=programmatic%2Fvestuario');
  });

  it('renders without count', () => {
    render(
      <BlogCTA
        variant="inline"
        setor="Saúde"
        slug="programmatic/saude"
      />,
    );

    expect(screen.getByText(/Veja todas as licitações/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// RelatedPages tests (AC5)
// ---------------------------------------------------------------------------

import RelatedPages from '@/components/blog/RelatedPages';

describe('RelatedPages (AC5)', () => {
  it('renders related links for sector page', () => {
    render(
      <RelatedPages
        sectorId="vestuario"
        currentType="sector"
      />,
    );

    expect(screen.getByText(/Explore mais/i)).toBeInTheDocument();
    const links = screen.getAllByRole('link');
    expect(links.length).toBeGreaterThanOrEqual(2);
  });

  it('renders neighboring UF links for sector-uf page', () => {
    render(
      <RelatedPages
        sectorId="informatica"
        currentUf="SP"
        currentType="sector-uf"
      />,
    );

    const links = screen.getAllByRole('link');
    // Should include neighboring UFs (RJ, MG, PR, MS)
    // Some UFs use /blog/licitacoes/ path when available (LICITACOES_SECTORS × LICITACOES_UFS)
    const hrefs = links.map((l) => l.getAttribute('href'));
    const ufLinks = hrefs.filter(
      (h) => h?.includes('/blog/programmatic/informatica/') || h?.includes('/blog/licitacoes/informatica/')
    );
    expect(ufLinks.length).toBeGreaterThanOrEqual(1);
  });

  it('includes editorial links when available', () => {
    render(
      <RelatedPages
        sectorId="informatica"
        currentType="sector"
      />,
    );

    const links = screen.getAllByRole('link');
    const hrefs = links.map((l) => l.getAttribute('href'));
    const editorialLinks = hrefs.filter((h) => h?.startsWith('/blog/') && !h?.includes('programmatic'));
    expect(editorialLinks.length).toBeGreaterThanOrEqual(1);
  });

  it('limits to max 7 links', () => {
    render(
      <RelatedPages
        sectorId="engenharia"
        currentUf="MG"
        currentType="sector-uf"
      />,
    );

    const links = screen.getAllByRole('link');
    expect(links.length).toBeLessThanOrEqual(7);
  });

  it('shows type badges', () => {
    render(
      <RelatedPages
        sectorId="vestuario"
        currentType="sector"
      />,
    );

    // Should have at least one badge type
    const badges = screen.getAllByText(/Artigo|Panorama|Dados/);
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it('returns null for unknown sector', () => {
    const { container } = render(
      <RelatedPages
        sectorId="nonexistent"
        currentType="sector"
      />,
    );

    expect(container.innerHTML).toBe('');
  });
});

// ---------------------------------------------------------------------------
// Programmatic helpers tests
// ---------------------------------------------------------------------------

import {
  generateSectorParams,
  generateSectorUfParams,
  formatBRL,
  generateSectorFAQs,
  getEditorialContent,
  ALL_UFS,
  UF_NAMES,
} from '@/lib/programmatic';

describe('Programmatic helpers', () => {
  it('generates 15 sector params', () => {
    const params = generateSectorParams();
    expect(params).toHaveLength(15);
    expect(params[0]).toHaveProperty('setor');
  });

  it('generates 405 sector×UF params', () => {
    const params = generateSectorUfParams();
    expect(params).toHaveLength(15 * 27);
    expect(params[0]).toHaveProperty('setor');
    expect(params[0]).toHaveProperty('uf');
  });

  it('formats BRL correctly', () => {
    const formatted = formatBRL(150000);
    expect(formatted).toContain('150');
    expect(formatted).toContain('R$');
  });

  it('generates 5 FAQs per sector', () => {
    const faqs = generateSectorFAQs('Vestuário', 42, 'São Paulo');
    expect(faqs).toHaveLength(5);
    faqs.forEach((faq) => {
      expect(faq.question).toBeTruthy();
      expect(faq.answer).toBeTruthy();
      expect(faq.question).toContain('Vestuário');
    });
  });

  it('has editorial content for all 15 sectors', () => {
    const sectorIds = [
      'vestuario', 'alimentos', 'informatica', 'mobiliario', 'papelaria',
      'engenharia', 'software', 'facilities', 'saude', 'vigilancia',
      'transporte', 'manutencao_predial', 'engenharia_rodoviaria',
      'materiais_eletricos', 'materiais_hidraulicos',
    ];

    for (const id of sectorIds) {
      const content = getEditorialContent(id);
      expect(content.length).toBeGreaterThan(300);
    }
  });

  it('ALL_UFS has 27 states', () => {
    expect(ALL_UFS).toHaveLength(27);
  });

  it('UF_NAMES maps all 27 UFs', () => {
    for (const uf of ALL_UFS) {
      expect(UF_NAMES[uf]).toBeTruthy();
    }
  });
});
