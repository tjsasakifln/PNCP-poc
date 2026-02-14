import { render, screen } from '@testing-library/react';
import BeforeAfter from '@/app/components/landing/BeforeAfter';

describe('BeforeAfter', () => {
  it('renders section title focused on decision quality (AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Da incerteza à decisão precisa/i)).toBeInTheDocument();
  });

  it('renders "Sem Curadoria" card with quality-focused negatives (AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Sem Curadoria/i)).toBeInTheDocument();
    expect(screen.getByText(/informação incompleta/i)).toBeInTheDocument();
    expect(screen.getByText(/Oportunidades certas passam despercebidas/i)).toBeInTheDocument();
    expect(screen.getByText(/Ruído demais, relevância de menos/i)).toBeInTheDocument();
    expect(screen.getByText(/Sem visão consolidada do mercado/i)).toBeInTheDocument();
  });

  it('renders "Com SmartLic" card with intelligence-focused positives (AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Com SmartLic/i)).toBeInTheDocument();
    expect(screen.getByText(/Curadoria inteligente/i)).toBeInTheDocument();
    expect(screen.getByText(/Resumo executivo por IA/i)).toBeInTheDocument();
    expect(screen.getByText(/Cobertura nacional com precisão setorial/i)).toBeInTheDocument();
    expect(screen.getByText(/Decisões com confiança, não com achismo/i)).toBeInTheDocument();
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
  });

  it('uses design system semantic colors', () => {
    const { container } = render(<BeforeAfter />);

    expect(container.querySelector('.text-red-600')).toBeInTheDocument();
    expect(container.querySelector('.text-red-500')).toBeInTheDocument();
    expect(container.querySelector('.text-green-500')).toBeInTheDocument();
    expect(container.querySelector('.text-blue-600')).toBeInTheDocument();
  });
});
