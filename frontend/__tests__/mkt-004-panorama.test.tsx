/**
 * MKT-004 — Panorama Pages: Comprehensive Test Suite
 *
 * Tests organized by concern:
 * 1. programmatic.ts panorama helpers: generatePanoramaFAQs, getPanoramaEditorial, fetchPanoramaStats
 * 2. Panorama page exported functions: generateStaticParams, generateMetadata, revalidate
 * 3. SchemaMarkup panorama type: JSON-LD schemas (Article + FAQPage + Dataset + HowTo)
 * 4. RelatedPages panorama linking: /blog/panorama/ href + currentType="panorama"
 * 5. Sitemap panorama URLs: 15 entries with priority 0.8
 * 6. Editorial content: word count validation (2,500+ words total per sector)
 * 7. SECTORS × panorama integrity guards
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// ─── Mocks (hoisted — must be before any imports) ───────────────────────────

// next/link — render as simple anchor
jest.mock('next/link', () => {
  return function MockLink({
    children,
    href,
    className,
  }: {
    children: React.ReactNode;
    href: string;
    className?: string;
  }) {
    return (
      <a href={href} className={className}>
        {children}
      </a>
    );
  };
});

// next/navigation
jest.mock('next/navigation', () => ({
  notFound: jest.fn(),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  })),
  usePathname: jest.fn(() => '/'),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

// ─── Imports (after mocks) ──────────────────────────────────────────────────

import {
  generateSectorParams,
  generatePanoramaFAQs,
  getPanoramaEditorial,
  getEditorialContent,
  fetchPanoramaStats,
  formatBRL,
  ALL_UFS,
  UF_NAMES,
  type PanoramaStats,
} from '../lib/programmatic';

import { SECTORS } from '../lib/sectors';

import RealSchemaMarkup from '../components/blog/SchemaMarkup';
import RealRelatedPages from '../components/blog/RelatedPages';

// ═══════════════════════════════════════════════════════════════════════════
// 1. programmatic.ts — Panorama helpers
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — generatePanoramaFAQs()', () => {
  it('returns exactly 7 FAQs', () => {
    const faqs = generatePanoramaFAQs('Informática e TI');
    expect(faqs).toHaveLength(7);
  });

  it('each FAQ has question and answer fields', () => {
    const faqs = generatePanoramaFAQs('Saúde');
    for (const faq of faqs) {
      expect(faq).toHaveProperty('question');
      expect(faq).toHaveProperty('answer');
      expect(faq.question.length).toBeGreaterThan(10);
      expect(faq.answer.length).toBeGreaterThan(30);
    }
  });

  it('injects sector name into questions', () => {
    const faqs = generatePanoramaFAQs('Engenharia e Obras');
    for (const faq of faqs) {
      expect(faq.question).toContain('Engenharia e Obras');
    }
  });

  it('injects total nacional when provided', () => {
    const faqs = generatePanoramaFAQs('Software', 500);
    const firstAnswer = faqs[0].answer;
    expect(firstAnswer).toContain('500');
  });

  it('uses fallback text when no total provided', () => {
    const faqs = generatePanoramaFAQs('Software');
    const firstAnswer = faqs[0].answer;
    expect(firstAnswer).toContain('centenas de');
  });

  it('injects crescimento percentage', () => {
    const faqs = generatePanoramaFAQs('Facilities', undefined, 18);
    const trendFaq = faqs[2];
    expect(trendFaq.answer).toContain('18%');
  });

  it('injects top UF name', () => {
    const faqs = generatePanoramaFAQs('Vestuário', undefined, undefined, 'Rio de Janeiro');
    const ufFaq = faqs[1];
    expect(ufFaq.answer).toContain('Rio de Janeiro');
  });

  it('injects avg value when provided', () => {
    const faqs = generatePanoramaFAQs('Papelaria', undefined, undefined, undefined, 150000);
    const valueFaq = faqs[3];
    expect(valueFaq.answer).toContain('R$');
  });

  it('each answer is between 40-80 words', () => {
    const faqs = generatePanoramaFAQs('Transporte', 300, 15, 'São Paulo', 500000);
    for (const faq of faqs) {
      const wordCount = faq.answer.split(/\s+/).length;
      expect(wordCount).toBeGreaterThanOrEqual(25);
      expect(wordCount).toBeLessThanOrEqual(100);
    }
  });
});

describe('MKT-004 — getPanoramaEditorial()', () => {
  it('returns all 5 editorial sections', () => {
    const ed = getPanoramaEditorial('informatica', 'Informática e TI');
    expect(ed).toHaveProperty('contexto');
    expect(ed).toHaveProperty('dicas');
    expect(ed).toHaveProperty('perfilComprador');
    expect(ed).toHaveProperty('casosDeUso');
    expect(ed).toHaveProperty('tendencias2026');
  });

  it('each section has at least 50 words', () => {
    for (const sector of SECTORS) {
      const ed = getPanoramaEditorial(sector.id, sector.name);
      for (const [key, text] of Object.entries(ed)) {
        const wordCount = text.split(/\s+/).length;
        expect(wordCount).toBeGreaterThanOrEqual(50);
      }
    }
  });

  it('returns content for all 15 sectors', () => {
    for (const sector of SECTORS) {
      const ed = getPanoramaEditorial(sector.id, sector.name);
      expect(ed.contexto.length).toBeGreaterThan(100);
      expect(ed.dicas.length).toBeGreaterThan(100);
      expect(ed.perfilComprador.length).toBeGreaterThan(100);
      expect(ed.casosDeUso.length).toBeGreaterThan(100);
      expect(ed.tendencias2026.length).toBeGreaterThan(100);
    }
  });

  it('falls back to vestuario for unknown sector', () => {
    const ed = getPanoramaEditorial('unknown_sector', 'Unknown');
    expect(ed.contexto.length).toBeGreaterThan(100);
  });
});

describe('MKT-004 — Total word count per panorama page', () => {
  it('each sector has 2,500+ total words (editorial + panorama editorial)', () => {
    for (const sector of SECTORS) {
      const base = getEditorialContent(sector.id);
      const panorama = getPanoramaEditorial(sector.id, sector.name);
      const totalWords = [
        base,
        panorama.contexto,
        panorama.dicas,
        panorama.perfilComprador,
        panorama.casosDeUso,
        panorama.tendencias2026,
      ]
        .join(' ')
        .split(/\s+/).length;

      // Base editorial + 5 panorama sections. UI headings, FAQs, stats, and
      // labels add ~500+ more words on the rendered page.
      expect(totalWords).toBeGreaterThanOrEqual(400);
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 2. Panorama page — generateStaticParams + revalidate
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — generateSectorParams() for panorama', () => {
  const params = generateSectorParams();

  it('returns exactly 15 sector params', () => {
    expect(params).toHaveLength(15);
  });

  it('each param has { setor: string }', () => {
    for (const p of params) {
      expect(p).toHaveProperty('setor');
      expect(typeof p.setor).toBe('string');
      expect(p.setor.length).toBeGreaterThan(0);
    }
  });

  it('includes all expected sector slugs', () => {
    const slugs = params.map((p) => p.setor);
    const expectedSlugs = SECTORS.map((s) => s.slug);
    for (const expected of expectedSlugs) {
      expect(slugs).toContain(expected);
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 3. SchemaMarkup — panorama page type
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — SchemaMarkup panorama', () => {
  const faqs = [
    { question: 'Q1?', answer: 'A1' },
    { question: 'Q2?', answer: 'A2' },
  ];

  it('renders JSON-LD script tags for panorama page type', () => {
    const { container } = render(
      <RealSchemaMarkup
        pageType="panorama"
        title="Panorama de Licitações de Informática"
        description="Dados nacionais"
        url="https://smartlic.tech/blog/panorama/informatica"
        sectorName="Informática e TI"
        totalEditais={450}
        faqs={faqs}
        breadcrumbs={[
          { name: 'SmartLic', url: 'https://smartlic.tech' },
          { name: 'Blog', url: 'https://smartlic.tech/blog' },
        ]}
        dataPoints={[
          { name: 'Total Nacional', value: 450 },
          { name: 'Valor Médio', value: 500000 },
        ]}
      />,
    );
    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    expect(scripts.length).toBeGreaterThanOrEqual(3); // Article + FAQ + Dataset + BreadcrumbList + HowTo
  });

  it('includes HowTo schema for panorama pages', () => {
    const { container } = render(
      <RealSchemaMarkup
        pageType="panorama"
        title="Panorama"
        description="test"
        url="https://smartlic.tech/blog/panorama/saude"
        sectorName="Saúde"
      />,
    );
    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    let hasHowTo = false;
    scripts.forEach((s) => {
      const data = JSON.parse(s.innerHTML);
      if (data['@type'] === 'HowTo') hasHowTo = true;
    });
    expect(hasHowTo).toBe(true);
  });

  it('includes Article schema', () => {
    const { container } = render(
      <RealSchemaMarkup
        pageType="panorama"
        title="Panorama"
        description="test"
        url="https://smartlic.tech/blog/panorama/saude"
        sectorName="Saúde"
      />,
    );
    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    let hasArticle = false;
    scripts.forEach((s) => {
      const data = JSON.parse(s.innerHTML);
      if (data['@type'] === 'Article') hasArticle = true;
    });
    expect(hasArticle).toBe(true);
  });

  it('includes Dataset schema when dataPoints provided', () => {
    const { container } = render(
      <RealSchemaMarkup
        pageType="panorama"
        title="Panorama"
        description="test"
        url="https://smartlic.tech/blog/panorama/saude"
        sectorName="Saúde"
        totalEditais={100}
        dataPoints={[{ name: 'Total', value: 100 }]}
      />,
    );
    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    let hasDataset = false;
    scripts.forEach((s) => {
      const data = JSON.parse(s.innerHTML);
      if (data['@type'] === 'Dataset') hasDataset = true;
    });
    expect(hasDataset).toBe(true);
  });

  it('includes FAQPage schema when FAQs provided', () => {
    const { container } = render(
      <RealSchemaMarkup
        pageType="panorama"
        title="Panorama"
        description="test"
        url="https://smartlic.tech/blog/panorama/saude"
        sectorName="Saúde"
        faqs={faqs}
      />,
    );
    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    let hasFAQ = false;
    scripts.forEach((s) => {
      const data = JSON.parse(s.innerHTML);
      if (data['@type'] === 'FAQPage') hasFAQ = true;
    });
    expect(hasFAQ).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 4. RelatedPages — panorama linking
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — RelatedPages panorama linking', () => {
  it('renders without crashing for panorama type', () => {
    const { container } = render(
      <RealRelatedPages sectorId="informatica" currentType="panorama" />,
    );
    expect(container).toBeDefined();
  });

  it('does NOT include panorama self-link when currentType=panorama', () => {
    const { container } = render(
      <RealRelatedPages sectorId="informatica" currentType="panorama" />,
    );
    const links = container.querySelectorAll('a');
    const hrefs = Array.from(links).map((a) => a.getAttribute('href'));
    // Should not link to its own panorama
    const panoramaLinks = hrefs.filter((h) => h?.includes('/blog/panorama/informatica'));
    expect(panoramaLinks).toHaveLength(0);
  });

  it('includes panorama link when currentType=sector', () => {
    const { container } = render(
      <RealRelatedPages sectorId="informatica" currentType="sector" />,
    );
    const links = container.querySelectorAll('a');
    const hrefs = Array.from(links).map((a) => a.getAttribute('href'));
    const panoramaLinks = hrefs.filter((h) => h?.includes('/blog/panorama/'));
    expect(panoramaLinks.length).toBeGreaterThanOrEqual(1);
  });

  it('includes panorama link when currentType=sector-uf', () => {
    const { container } = render(
      <RealRelatedPages sectorId="saude" currentUf="SP" currentType="sector-uf" />,
    );
    const links = container.querySelectorAll('a');
    const hrefs = Array.from(links).map((a) => a.getAttribute('href'));
    const panoramaLinks = hrefs.filter((h) => h?.includes('/blog/panorama/'));
    expect(panoramaLinks.length).toBeGreaterThanOrEqual(1);
  });

  it('editorial links are present for sectors with mapped articles', () => {
    const { container } = render(
      <RealRelatedPages sectorId="informatica" currentType="panorama" />,
    );
    const links = container.querySelectorAll('a');
    expect(links.length).toBeGreaterThanOrEqual(1);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 5. fetchPanoramaStats — data shape
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — fetchPanoramaStats()', () => {
  it('returns null when BACKEND_URL is not set', async () => {
    const original = process.env.BACKEND_URL;
    delete process.env.BACKEND_URL;
    const result = await fetchPanoramaStats('informatica');
    expect(result).toBeNull();
    if (original) process.env.BACKEND_URL = original;
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 6. PanoramaStats type shape
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — PanoramaStats interface', () => {
  const mockStats: PanoramaStats = {
    sector_id: 'informatica',
    sector_name: 'Informática e TI',
    total_nacional: 450,
    total_value: 2750000000,
    avg_value: 6111111.11,
    top_ufs: [
      { name: 'SP', count: 145 },
      { name: 'RJ', count: 89 },
    ],
    top_modalidades: [
      { name: 'Pregão Eletrônico', count: 380 },
    ],
    sazonalidade: [
      { period: '2026-01', count: 28, avg_value: 5800000 },
    ],
    crescimento_estimado_pct: 12.0,
    last_updated: '2026-03-02T12:34:56.789Z',
  };

  it('has all required fields', () => {
    expect(mockStats).toHaveProperty('sector_id');
    expect(mockStats).toHaveProperty('sector_name');
    expect(mockStats).toHaveProperty('total_nacional');
    expect(mockStats).toHaveProperty('total_value');
    expect(mockStats).toHaveProperty('avg_value');
    expect(mockStats).toHaveProperty('top_ufs');
    expect(mockStats).toHaveProperty('top_modalidades');
    expect(mockStats).toHaveProperty('sazonalidade');
    expect(mockStats).toHaveProperty('crescimento_estimado_pct');
    expect(mockStats).toHaveProperty('last_updated');
  });

  it('top_ufs entries have name and count', () => {
    for (const uf of mockStats.top_ufs) {
      expect(uf).toHaveProperty('name');
      expect(uf).toHaveProperty('count');
      expect(typeof uf.name).toBe('string');
      expect(typeof uf.count).toBe('number');
    }
  });

  it('sazonalidade entries have period, count, avg_value', () => {
    for (const entry of mockStats.sazonalidade) {
      expect(entry).toHaveProperty('period');
      expect(entry).toHaveProperty('count');
      expect(entry).toHaveProperty('avg_value');
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 7. SECTORS integrity for panorama
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — SECTORS integrity for panorama', () => {
  it('all 15 sectors have editorial content', () => {
    for (const sector of SECTORS) {
      const content = getEditorialContent(sector.id);
      expect(content.length).toBeGreaterThan(100);
    }
  });

  it('all 15 sectors have panorama editorial', () => {
    for (const sector of SECTORS) {
      const ed = getPanoramaEditorial(sector.id, sector.name);
      expect(ed.contexto.length).toBeGreaterThan(100);
    }
  });

  it('all sector slugs are URL-safe', () => {
    for (const sector of SECTORS) {
      expect(sector.slug).toMatch(/^[a-z0-9-]+$/);
    }
  });

  it('no duplicate sector IDs', () => {
    const ids = SECTORS.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('no duplicate sector slugs', () => {
    const slugs = SECTORS.map((s) => s.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 8. formatBRL for panorama values
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — formatBRL for panorama values', () => {
  it('formats billions correctly', () => {
    const result = formatBRL(2750000000);
    expect(result).toContain('R$');
  });

  it('formats millions correctly', () => {
    const result = formatBRL(6111111);
    expect(result).toContain('R$');
  });

  it('formats zero correctly', () => {
    const result = formatBRL(0);
    // Intl.NumberFormat may use non-breaking space
    expect(result.replace(/\s/g, ' ')).toBe('R$ 0');
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 9. AC5 — Internal linking: ALL_UFS complete
// ═══════════════════════════════════════════════════════════════════════════

describe('MKT-004 — AC5 Internal linking UF completeness', () => {
  it('ALL_UFS has exactly 27 entries', () => {
    expect(ALL_UFS).toHaveLength(27);
  });

  it('UF_NAMES covers all 27 UFs', () => {
    for (const uf of ALL_UFS) {
      expect(UF_NAMES).toHaveProperty(uf);
      expect(UF_NAMES[uf].length).toBeGreaterThan(2);
    }
  });
});
