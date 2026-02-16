import { render, screen } from '@testing-library/react';
import BeforeAfter from '@/app/components/landing/BeforeAfter';

describe('BeforeAfter', () => {
  it('renders section title focused on decision quality (AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Da busca manual à decisão estratégica/i)).toBeInTheDocument();
  });

  it('renders "Sem Curadoria" card with quality-focused negatives (AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Sem Inteligência de Mercado/i)).toBeInTheDocument();
    expect(screen.getByText(/falta de visibilidade/i)).toBeInTheDocument();
    expect(screen.getByText(/Oportunidades certas passam despercebidas/i)).toBeInTheDocument();
    expect(screen.getByText(/Concorrentes se posicionam antes de você/i)).toBeInTheDocument();
    expect(screen.getByText(/Decisões baseadas em intuição, não em dados/i)).toBeInTheDocument();
  });

  it('renders "Com SmartLic" card with intelligence-focused positives (AC5)', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Com SmartLic/i)).toBeInTheDocument();
    expect(screen.getByText(/Visão completa do mercado/i)).toBeInTheDocument();
    expect(screen.getByText(/Avaliação objetiva: vale a pena ou não, e por quê/i)).toBeInTheDocument();
    expect(screen.getByText(/Posicione-se antes da concorrência/i)).toBeInTheDocument();
    expect(screen.getByText(/Decisões com confiança baseadas em inteligência/i)).toBeInTheDocument();
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
