import { render, screen } from '@testing-library/react';
import DifferentialsGrid from '@/app/components/landing/DifferentialsGrid';

describe('DifferentialsGrid', () => {
  it('renders section title with value positioning', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/Inteligência que gera resultado/i)).toBeInTheDocument();
  });

  it('renders subtitle focused on winning bids', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/ganhar licitações, não apenas encontrá-las/i)).toBeInTheDocument();
  });

  it('renders 4 value differentials with correct titles (AC6)', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText('FILTRO SETORIAL INTELIGENTE')).toBeInTheDocument();
    expect(screen.getByText('SÓ OPORTUNIDADES ABERTAS')).toBeInTheDocument();
    expect(screen.getByText('RESUMO EXECUTIVO POR IA')).toBeInTheDocument();
    expect(screen.getByText('ZERO RUÍDO')).toBeInTheDocument();
  });

  it('renders bullet points for each differential (AC6)', () => {
    render(<DifferentialsGrid />);

    // FILTRO SETORIAL INTELIGENTE
    expect(screen.getByText(/9 setores especializados/i)).toBeInTheDocument();
    expect(screen.getByText(/Só oportunidades do seu mercado/i)).toBeInTheDocument();

    // SÓ OPORTUNIDADES ABERTAS
    expect(screen.getByText(/Editais com prazo vigente/i)).toBeInTheDocument();
    expect(screen.getByText(/Ação imediata garantida/i)).toBeInTheDocument();

    // RESUMO EXECUTIVO POR IA
    expect(screen.getByText(/Análise automática de cada edital/i)).toBeInTheDocument();
    expect(screen.getByText(/Decisão em segundos, não horas/i)).toBeInTheDocument();

    // ZERO RUÍDO
    expect(screen.getByText(/Sem editais irrelevantes/i)).toBeInTheDocument();
    expect(screen.getByText(/Curadoria, não listagem/i)).toBeInTheDocument();
  });

  it('uses 1+3 asymmetric layout', () => {
    const { container } = render(<DifferentialsGrid />);

    expect(container.querySelector('.lg\\:col-span-4')).toBeInTheDocument();

    const smallCards = container.querySelectorAll('.lg\\:col-span-1');
    expect(smallCards.length).toBe(3);
  });

  it('does NOT use forbidden terms (AC11)', () => {
    const { container } = render(<DifferentialsGrid />);
    const text = container.textContent || '';

    expect(text).not.toMatch(/busca rápida/i);
    expect(text).not.toMatch(/ferramenta de busca/i);
    expect(text).not.toMatch(/planilha automatizada/i);
  });

  it('uses design system colors', () => {
    const { container } = render(<DifferentialsGrid />);

    expect(container.querySelector('.bg-brand-navy')).toBeInTheDocument();
    expect(container.querySelector('.bg-surface-1')).toBeInTheDocument();
  });
});
