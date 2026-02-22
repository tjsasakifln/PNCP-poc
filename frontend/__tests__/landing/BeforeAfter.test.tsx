import { render, screen } from '@testing-library/react';
import BeforeAfter from '@/app/components/landing/BeforeAfter';

describe('BeforeAfter', () => {
  it('renders section title focused on strategic filter contrast (GTM-COPY-001 AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/O que acontece sem filtro estratégico — e com ele/i)).toBeInTheDocument();
  });

  it('renders "Sem Filtro Estratégico" card with concrete consequences (AC5)', () => {
    render(<BeforeAfter />);

    // "Sem Filtro Estratégico" appears in both heading and card title — use getAllByText
    const matches = screen.getAllByText(/Sem Filtro Estratégico/i);
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Gasta horas analisando editais que não se encaixam/i)).toBeInTheDocument();
    expect(screen.getByText(/Perde licitações porque não sabia que existiam/i)).toBeInTheDocument();
    expect(screen.getByText(/Descobre oportunidades quando o prazo já está curto/i)).toBeInTheDocument();
    expect(screen.getByText(/Decide com base em intuição — opera no escuro/i)).toBeInTheDocument();
  });

  it('renders "Com SmartLic" card with filtering-focused positives (AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Com SmartLic/i)).toBeInTheDocument();
    expect(screen.getByText(/87% dos editais descartados antes de chegar até você/i)).toBeInTheDocument();
    expect(screen.getByText(/Cobertura nacional automática — 27 UFs/i)).toBeInTheDocument();
    expect(screen.getByText(/Acesso assim que publicados — você se posiciona antes/i)).toBeInTheDocument();
    expect(screen.getByText(/Cada decisão baseada em critérios objetivos documentados/i)).toBeInTheDocument();
  });

  it('uses asymmetric 40/60 layout', () => {
    const { container } = render(<BeforeAfter />);

    expect(container.querySelector('.md\\:col-span-2')).toBeInTheDocument();
    expect(container.querySelector('.md\\:col-span-3')).toBeInTheDocument();
  });

  it('does NOT use forbidden terms (AC11)', () => {
    const { container } = render(<BeforeAfter />);
    const text = container.textContent || '';

    expect(text).not.toMatch(/8h\/dia/i);
    expect(text).not.toMatch(/economize.*tempo/i);
    expect(text).not.toMatch(/busca rápida/i);
    expect(text).not.toMatch(/inteligência automatizada/i);
  });

  it('uses design system semantic colors', () => {
    const { container } = render(<BeforeAfter />);

    expect(container.querySelector('.text-red-600')).toBeInTheDocument();
    expect(container.querySelector('.text-red-500')).toBeInTheDocument();
    expect(container.querySelector('.text-green-500')).toBeInTheDocument();
    expect(container.querySelector('.text-blue-600')).toBeInTheDocument();
  });
});
