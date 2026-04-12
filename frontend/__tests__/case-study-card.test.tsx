/**
 * STORY-372 AC4: Tests for CaseStudyCard component.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { CaseStudyCard } from '../components/CaseStudyCard';

const defaultProps = {
  sector: 'Limpeza e Conservação',
  location: 'Curitiba-PR',
  companySize: '12 funcionários',
  problem: 'Monitorava editais manualmente no PNCP 2h por dia',
  result: 'Encontrou Pregão Eletrônico de R$87.000',
  highlight: {
    value: 'R$ 87.000',
    label: 'em oportunidades encontradas',
    time: 'em 6 minutos',
  },
};

describe('CaseStudyCard', () => {
  it('renders sector and location', () => {
    render(<CaseStudyCard {...defaultProps} />);
    expect(screen.getByText('Limpeza e Conservação')).toBeInTheDocument();
    expect(screen.getByText(/Curitiba-PR/)).toBeInTheDocument();
  });

  it('renders highlight value prominently', () => {
    render(<CaseStudyCard {...defaultProps} />);
    expect(screen.getByText('R$ 87.000')).toBeInTheDocument();
    expect(screen.getByText('em oportunidades encontradas')).toBeInTheDocument();
    expect(screen.getByText('em 6 minutos')).toBeInTheDocument();
  });

  it('renders problem and result', () => {
    render(<CaseStudyCard {...defaultProps} />);
    expect(screen.getByText(/Monitorava editais manualmente/)).toBeInTheDocument();
    expect(screen.getByText(/Encontrou Pregão Eletrônico/)).toBeInTheDocument();
  });

  it('renders without optional quote prop', () => {
    const { container } = render(<CaseStudyCard {...defaultProps} />);
    // Should render without errors when quote is absent
    expect(container.firstChild).toBeTruthy();
  });

  it('renders with optional quote prop', () => {
    render(<CaseStudyCard {...defaultProps} quote="Economizei 10 horas por semana." />);
    expect(screen.getByText(/Economizei 10 horas por semana/)).toBeInTheDocument();
  });
});
