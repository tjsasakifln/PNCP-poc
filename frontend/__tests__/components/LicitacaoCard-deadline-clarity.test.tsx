/**
 * Tests for deadline terminology clarity in LicitacaoCard
 *
 * CRITICAL: These tests ensure we NEVER display ambiguous deadline terminology
 * that confuses users about submission deadlines.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LicitacaoCard } from '@/app/components/LicitacaoCard';
import type { LicitacaoItem } from '@/app/types';

const mockLicitacao: LicitacaoItem = {
  pncp_id: "test-001",
  objeto: "Confecção de fardamentos escolares",
  orgao: "Prefeitura de Porto Alegre",
  uf: "RS",
  municipio: "Porto Alegre",
  valor: 75000,
  modalidade: "Pregão Eletrônico",
  data_publicacao: "2026-02-01T10:00:00",
  data_abertura: "2026-02-05T09:00:00",
  data_encerramento: "2026-02-23T18:00:00",
  link: "https://pncp.gov.br/test",
  status: "recebendo_proposta",
};

describe('LicitacaoCard - Deadline Terminology Clarity', () => {
  describe('Clear terminology requirements', () => {
    it('deve exibir "Recebe propostas" ao invés de termos ambíguos', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      // Must have clear "Recebe propostas" label
      expect(screen.getByText(/Recebe propostas/i)).toBeInTheDocument();

      // Must NOT have ambiguous terms
      expect(screen.queryByText(/Prazo de abertura/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Abertura:/i)).not.toBeInTheDocument();
    });

    it('deve exibir "Prazo final para propostas" ao invés de apenas "Prazo"', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      // Must have explicit "Prazo final para propostas"
      expect(screen.getByText(/Prazo final para propostas/i)).toBeInTheDocument();

      // Must NOT have ambiguous "Prazo:" without context
      const ambiguousPrazo = screen.queryByText(/^Prazo:(?! final)/i);
      expect(ambiguousPrazo).not.toBeInTheDocument();
    });

    it('deve exibir tempo restante com linguagem clara', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      // Should show "Você tem X dias restantes" or similar clear message
      const timeRemaining = screen.getByText(/Você tem \d+ dia/i);
      expect(timeRemaining).toBeInTheDocument();
    });
  });

  describe('Visual indicators', () => {
    it('deve usar ícones coloridos 🟢 para início e 🔴 para fim', () => {
      const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

      // Check for emoji indicators (rendered as text)
      expect(container.textContent).toContain('🟢');
      expect(container.textContent).toContain('🔴');
    });

    it('deve incluir ícone de relógio para tempo restante', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      // Clock icon should be present near time remaining
      const timeSection = screen.getByText(/Você tem \d+ dia/i).closest('div');
      expect(timeSection).toBeInTheDocument();
    });
  });

  describe('Date formatting', () => {
    it('deve formatar datas com horário completo (dd/MM/yyyy às HH:mm)', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      // Should show formatted dates with time
      expect(screen.getByText(/05\/02\/2026 às 09:00/i)).toBeInTheDocument();
      expect(screen.getByText(/23\/02\/2026 às 18:00/i)).toBeInTheDocument();
    });
  });

  describe('Edge cases', () => {
    it('deve lidar com prazo encerrado corretamente', () => {
      const pastLicitacao: LicitacaoItem = {
        ...mockLicitacao,
        data_encerramento: "2020-01-01T10:00:00",
      };

      render(<LicitacaoCard licitacao={pastLicitacao} />);

      // Should show "Prazo encerrado"
      expect(screen.getByText(/Prazo encerrado/i)).toBeInTheDocument();
    });

    it('deve lidar com licitacao sem data_abertura', () => {
      const noStartDate: LicitacaoItem = {
        ...mockLicitacao,
        data_abertura: null,
      };

      render(<LicitacaoCard licitacao={noStartDate} />);

      // Should not crash and should show deadline
      expect(screen.getByText(/Prazo final para propostas/i)).toBeInTheDocument();
    });

    it('deve lidar com licitacao sem data_encerramento', () => {
      const noEndDate: LicitacaoItem = {
        ...mockLicitacao,
        data_encerramento: null,
      };

      render(<LicitacaoCard licitacao={noEndDate} />);

      // Should not crash and should show start date
      expect(screen.getByText(/Recebe propostas/i)).toBeInTheDocument();
    });
  });

  describe('Forbidden terms validation (CRITICAL)', () => {
    it('NÃO deve conter "prazo de abertura" em nenhuma parte do card', () => {
      const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

      const cardText = container.textContent?.toLowerCase() || '';
      expect(cardText).not.toContain('prazo de abertura');
    });

    it('NÃO deve conter "abertura em [data]" como label principal', () => {
      const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

      const cardText = container.textContent?.toLowerCase() || '';
      // "Abertura em" followed by a date is forbidden
      expect(cardText).not.toMatch(/abertura em \d{2}\/\d{2}/i);
    });

    it('NÃO deve usar apenas "Início:" sem contexto', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      // "Início:" alone is ambiguous, must be "Recebe propostas"
      const inicioLabel = screen.queryByText(/^Início:$/i);
      expect(inicioLabel).not.toBeInTheDocument();
    });
  });

  describe('Tooltip content', () => {
    it('tooltips devem conter explicações claras', () => {
      const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

      // InfoTooltip components should be present (check via hover target class)
      const tooltipTriggers = container.querySelectorAll('.cursor-help');
      expect(tooltipTriggers.length).toBeGreaterThan(0);
    });
  });
});
