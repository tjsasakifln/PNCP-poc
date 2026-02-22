import { render, screen } from '@testing-library/react';
import TrustCriteria from '@/app/components/landing/TrustCriteria';

describe('TrustCriteria', () => {
  it('renders section headline (GTM-COPY-004 AC1)', () => {
    render(<TrustCriteria />);

    expect(screen.getByText(/Cada recomendação tem uma justificativa/i)).toBeInTheDocument();
    expect(screen.getByText(/Transparência de critérios/i)).toBeInTheDocument();
  });

  it('renders 5 evaluation criteria with descriptions (AC2)', () => {
    render(<TrustCriteria />);

    expect(screen.getByText('Compatibilidade setorial')).toBeInTheDocument();
    expect(screen.getByText('Faixa de valor adequada')).toBeInTheDocument();
    expect(screen.getByText('Prazo viável para preparação')).toBeInTheDocument();
    expect(screen.getByText('Região de atuação')).toBeInTheDocument();
    expect(screen.getByText('Modalidade favorável')).toBeInTheDocument();
  });

  it('renders adherence levels Alta/Média/Baixa with descriptions (AC3)', () => {
    render(<TrustCriteria />);

    expect(screen.getByText('Alta')).toBeInTheDocument();
    expect(screen.getByText('Média')).toBeInTheDocument();
    expect(screen.getByText('Baixa')).toBeInTheDocument();
    expect(screen.getByText(/3 ou mais critérios atendem seu perfil/i)).toBeInTheDocument();
    expect(screen.getByText(/2 critérios atendem/i)).toBeInTheDocument();
    expect(screen.getByText(/1 critério ou menos/i)).toBeInTheDocument();
  });

  it('communicates false positive reduction (AC4)', () => {
    render(<TrustCriteria />);

    expect(screen.getByText(/70-90% dos editais publicados são irrelevantes/i)).toBeInTheDocument();
    expect(screen.getByText(/20 recomendações qualificadas, não 2\.000 resultados genéricos/i)).toBeInTheDocument();
  });

  it('communicates false negative reduction (AC5)', () => {
    render(<TrustCriteria />);

    expect(screen.getByText(/27 UFs/)).toBeInTheDocument();
    expect(screen.getByText(/Se existe algo compatível em qualquer lugar do Brasil, você sabe/i)).toBeInTheDocument();
  });

  it('explains adherence level system (AC3)', () => {
    render(<TrustCriteria />);

    expect(screen.getByText(/Nível de aderência: como funciona/i)).toBeInTheDocument();
  });

  it('uses correct color indicators for adherence levels', () => {
    const { container } = render(<TrustCriteria />);

    expect(container.querySelector('.bg-emerald-500')).toBeInTheDocument();
    expect(container.querySelector('.bg-yellow-500')).toBeInTheDocument();
    expect(container.querySelector('.bg-gray-400')).toBeInTheDocument();
  });

  it('does NOT use forbidden terms', () => {
    const { container } = render(<TrustCriteria />);
    const text = container.textContent || '';

    expect(text).not.toMatch(/GPT-4/i);
    expect(text).not.toMatch(/inteligência automatizada/i);
    expect(text).not.toMatch(/PNCP/i);
    expect(text).not.toMatch(/economize.*tempo/i);
  });

  it('has proper semantic structure', () => {
    render(<TrustCriteria />);

    const headings = screen.getAllByRole('heading');
    expect(headings.length).toBeGreaterThanOrEqual(3);
  });
});
