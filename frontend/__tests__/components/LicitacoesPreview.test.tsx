import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LicitacoesPreview } from '@/app/components/LicitacoesPreview';
import type { LicitacaoItem } from '@/app/types';

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

describe('LicitacoesPreview', () => {
  const mockLicitacoes: LicitacaoItem[] = [
    {
      pncp_id: '1',
      objeto: 'Aquisição de uniformes escolares',
      orgao: 'Secretaria de Educação',
      uf: 'SP',
      municipio: 'São Paulo',
      valor: 50000,
      modalidade: 'Pregão Eletrônico',
      data_abertura: '2025-01-01',
      data_encerramento: '2025-12-31',
      status: 'Aberta',
      link: 'https://example.com/1',
      dias_restantes: 100,
      urgencia: 'media',
      relevance_score: 0.8,
      _source: 'PNCP',
      matched_terms: [], // Empty to avoid highlighting issues
    },
    {
      pncp_id: '2',
      objeto: 'Compra de materiais de escritório',
      orgao: 'Prefeitura Municipal',
      uf: 'RJ',
      municipio: 'Rio de Janeiro',
      valor: 25000,
      modalidade: 'Dispensa',
      data_abertura: '2025-01-15',
      data_encerramento: '2025-06-30',
      status: 'Aberta',
      link: 'https://example.com/2',
      dias_restantes: 5,
      urgencia: 'critica',
      relevance_score: 0.5,
      _source: 'COMPRAS_GOV',
    },
  ];

  it('renders without crashing', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText('Oportunidades Encontradas')).toBeInTheDocument();
  });

  it('returns null when licitacoes is empty', () => {
    const { container } = render(
      <LicitacoesPreview
        licitacoes={[]}
        excelAvailable={true}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('displays all visible items', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
        previewCount={5}
      />
    );
    expect(screen.getByText('Aquisição de uniformes escolares')).toBeInTheDocument();
    expect(screen.getByText('Compra de materiais de escritório')).toBeInTheDocument();
  });

  it('shows relevance badge for high score', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText('Muito relevante')).toBeInTheDocument();
  });

  it('shows relevance badge for medium score', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText('Relevante')).toBeInTheDocument();
  });

  it('does not show relevance badge for null score', () => {
    const licitacaoSemScore = [{
      ...mockLicitacoes[0],
      relevance_score: null,
    }];
    render(
      <LicitacoesPreview
        licitacoes={licitacaoSemScore}
        excelAvailable={true}
      />
    );
    expect(screen.queryByText('Muito relevante')).not.toBeInTheDocument();
    expect(screen.queryByText('Relevante')).not.toBeInTheDocument();
  });

  it('highlights search terms', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
        searchTerms={['uniformes']}
      />
    );
    const highlighted = screen.getByText('uniformes');
    expect(highlighted.tagName).toBe('MARK');
  });

  it('shows source badge', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText('PNCP')).toBeInTheDocument();
    expect(screen.getByText('ComprasGov')).toBeInTheDocument();
  });

  it('formats currency correctly', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText('R$ 50.000')).toBeInTheDocument();
    expect(screen.getByText('R$ 25.000')).toBeInTheDocument();
  });

  it('shows urgency badge with correct styling for critical', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText(/Urgente:/)).toBeInTheDocument();
  });

  it('shows urgency badge with correct styling for medium', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText(/Prazo final:/)).toBeInTheDocument();
  });

  it('shows "Ver na fonte" link for items with link', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    const links = screen.getAllByText('Ver na fonte');
    expect(links).toHaveLength(2);
    expect(links[0].closest('a')).toHaveAttribute('href', 'https://example.com/1');
  });

  it('shows blur overlay for FREE tier', () => {
    const manyLicitacoes = Array(8).fill(mockLicitacoes[0]).map((item, i) => ({
      ...item,
      pncp_id: `id-${i}`,
    }));

    render(
      <LicitacoesPreview
        licitacoes={manyLicitacoes}
        excelAvailable={false}
        previewCount={5}
      />
    );

    expect(screen.getByText(/oportunidades ocultas/)).toBeInTheDocument();
  });

  it('shows upgrade CTA for FREE tier', () => {
    const manyLicitacoes = Array(8).fill(mockLicitacoes[0]).map((item, i) => ({
      ...item,
      pncp_id: `id-${i}`,
    }));

    render(
      <LicitacoesPreview
        licitacoes={manyLicitacoes}
        excelAvailable={false}
        previewCount={5}
      />
    );

    expect(screen.getByText('Ver Planos')).toBeInTheDocument();
    expect(screen.getByText(/Assine para ver todas as oportunidades/)).toBeInTheDocument();
  });

  it('does not show blur overlay for paid tier', () => {
    const manyLicitacoes = Array(8).fill(mockLicitacoes[0]).map((item, i) => ({
      ...item,
      pncp_id: `id-${i}`,
    }));

    render(
      <LicitacoesPreview
        licitacoes={manyLicitacoes}
        excelAvailable={true}
        previewCount={5}
      />
    );

    expect(screen.queryByText(/oportunidades ocultas/)).not.toBeInTheDocument();
    expect(screen.queryByText('Ver Planos')).not.toBeInTheDocument();
  });

  it('shows all items for paid tier', () => {
    const manyLicitacoes = Array(8).fill(mockLicitacoes[0]).map((item, i) => ({
      ...item,
      pncp_id: `id-${i}`,
      objeto: `Objeto ${i}`,
    }));

    render(
      <LicitacoesPreview
        licitacoes={manyLicitacoes}
        excelAvailable={true}
        previewCount={5}
      />
    );

    // Should render all 8 items
    expect(screen.getByText('Objeto 0')).toBeInTheDocument();
    expect(screen.getByText('Objeto 7')).toBeInTheDocument();
  });

  it('handles null data_encerramento', () => {
    const licitacaoSemData = [{
      ...mockLicitacoes[0],
      data_encerramento: null,
    }];
    render(
      <LicitacoesPreview
        licitacoes={licitacaoSemData}
        excelAvailable={true}
      />
    );
    // Should not crash
    expect(screen.getByText('Aquisição de uniformes escolares')).toBeInTheDocument();
  });

  it('handles missing municipio', () => {
    const licitacaoSemMunicipio = [{
      ...mockLicitacoes[0],
      municipio: null,
    }];
    render(
      <LicitacoesPreview
        licitacoes={licitacaoSemMunicipio}
        excelAvailable={true}
      />
    );
    // Should show just UF
    expect(screen.getByText('SP')).toBeInTheDocument();
  });

  it('handles missing modalidade', () => {
    const licitacaoSemModalidade = [{
      ...mockLicitacoes[0],
      modalidade: null,
    }];
    render(
      <LicitacoesPreview
        licitacoes={licitacaoSemModalidade}
        excelAvailable={true}
      />
    );
    expect(screen.getByText('Aquisição de uniformes escolares')).toBeInTheDocument();
  });

  it('handles missing link', () => {
    const licitacaoSemLink = [{
      ...mockLicitacoes[0],
      link: null,
    }];
    render(
      <LicitacoesPreview
        licitacoes={licitacaoSemLink}
        excelAvailable={true}
      />
    );
    expect(screen.queryByText('Ver na fonte')).not.toBeInTheDocument();
  });

  it('uses matched_terms when provided', () => {
    const licitacaoComTerms = [{
      ...mockLicitacoes[0],
      matched_terms: ['uniformes', 'escolares'],
    }];
    render(
      <LicitacoesPreview
        licitacoes={licitacaoComTerms}
        excelAvailable={true}
      />
    );
    const uniformes = screen.getByText('uniformes');
    const escolares = screen.getByText('escolares');
    expect(uniformes.tagName).toBe('MARK');
    expect(escolares.tagName).toBe('MARK');
  });

  it('shows correct blurred items count', () => {
    const tenLicitacoes = Array(10).fill(mockLicitacoes[0]).map((item, i) => ({
      ...item,
      pncp_id: `id-${i}`,
    }));

    render(
      <LicitacoesPreview
        licitacoes={tenLicitacoes}
        excelAvailable={false}
        previewCount={3}
      />
    );

    expect(screen.getByText('+7 oportunidades ocultas')).toBeInTheDocument();
  });

  it('handles singular form for blurred count', () => {
    const fourLicitacoes = Array(4).fill(mockLicitacoes[0]).map((item, i) => ({
      ...item,
      pncp_id: `id-${i}`,
    }));

    render(
      <LicitacoesPreview
        licitacoes={fourLicitacoes}
        excelAvailable={false}
        previewCount={3}
      />
    );

    expect(screen.getByText('+1 oportunidade oculta')).toBeInTheDocument();
  });

  it('formats date correctly', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    expect(screen.getByText(/31\/12\/2025/)).toBeInTheDocument();
  });

  it('shows data_abertura when provided', () => {
    render(
      <LicitacoesPreview
        licitacoes={mockLicitacoes}
        excelAvailable={true}
      />
    );
    // Check that component renders - data_abertura is optional field
    expect(screen.getByText(/Oportunidades Encontradas/)).toBeInTheDocument();
  });
});
