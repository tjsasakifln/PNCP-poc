import { render, screen } from '@testing-library/react';
import DifferentialsGrid from '@/app/components/landing/DifferentialsGrid';

describe('DifferentialsGrid', () => {
  it('renders section title with value positioning', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/Por que empresas que vencem licitações usam SmartLic/i)).toBeInTheDocument();
  });

  it('renders subtitle focused on winning bids', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/Cada funcionalidade foi projetada para você vencer, não apenas encontrar/i)).toBeInTheDocument();
  });

  it('renders 4 value differentials with correct titles (AC6)', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText('PRIORIZAÇÃO INTELIGENTE')).toBeInTheDocument();
    expect(screen.getByText('ANÁLISE AUTOMATIZADA')).toBeInTheDocument();
    expect(screen.getByText('REDUÇÃO DE INCERTEZA')).toBeInTheDocument();
    expect(screen.getByText('COBERTURA NACIONAL')).toBeInTheDocument();
  });

  it('renders bullet points for each differential (AC6)', () => {
    render(<DifferentialsGrid />);

    // PRIORIZAÇÃO INTELIGENTE
    expect(screen.getByText(/Análise de adequação ao seu perfil/i)).toBeInTheDocument();
    expect(screen.getByText(/Filtros inteligentes por setor/i)).toBeInTheDocument();
    expect(screen.getByText(/Foco no que gera resultado/i)).toBeInTheDocument();

    // ANÁLISE AUTOMATIZADA
    expect(screen.getByText(/Avaliação automática de cada edital/i)).toBeInTheDocument();
    expect(screen.getByText(/Destaques de critérios decisivos/i)).toBeInTheDocument();
    expect(screen.getByText(/Decisão em segundos, não horas/i)).toBeInTheDocument();

    // REDUÇÃO DE INCERTEZA
    expect(screen.getByText(/Critérios objetivos de avaliação/i)).toBeInTheDocument();
    expect(screen.getByText(/Dados verificados de fontes oficiais/i)).toBeInTheDocument();
    expect(screen.getByText(/Confiança em cada decisão/i)).toBeInTheDocument();

    // COBERTURA NACIONAL
    expect(screen.getByText(/Cobertura nacional integrada/i)).toBeInTheDocument();
    expect(screen.getByText(/27 estados cobertos diariamente/i)).toBeInTheDocument();
    expect(screen.getByText(/Novas fontes adicionadas regularmente/i)).toBeInTheDocument();
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
