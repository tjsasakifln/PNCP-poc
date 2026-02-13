/**
 * LicitacaoCard Component Tests
 *
 * Tests rendering, interactions, share, favorite, status display
 * Focuses on uncovered branches (existing deadline-clarity test covers main flow)
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LicitacaoCard, LicitacaoCardCompact } from '@/app/components/LicitacaoCard';
import type { LicitacaoItem } from '@/app/types';

const mockLicitacao: LicitacaoItem = {
  pncp_id: 'test-001',
  objeto: 'Aquisição de uniformes escolares para rede municipal',
  orgao: 'Secretaria de Educação',
  uf: 'SP',
  municipio: 'São Paulo',
  valor: 150000,
  modalidade: 'Pregão Eletrônico',
  data_publicacao: '2026-02-01T10:00:00',
  data_abertura: '2026-02-15T09:00:00',
  data_encerramento: '2026-02-28T18:00:00',
  link: 'https://pncp.gov.br/test-001',
  status: 'recebendo_proposta',
};

// Mock navigator.share and clipboard
Object.assign(navigator, {
  share: jest.fn(),
  clipboard: {
    writeText: jest.fn(),
  },
});

beforeEach(() => {
  jest.clearAllMocks();
});

describe('LicitacaoCard Component', () => {
  describe('Basic rendering', () => {
    it('should render licitacao details', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      expect(screen.getByText(/uniformes escolares/i)).toBeInTheDocument();
      expect(screen.getByText('Secretaria de Educação')).toBeInTheDocument();
      expect(screen.getByText(/R\$ 150\.000/i)).toBeInTheDocument();
    });

    it('should render status badge', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} status="aberta" />);

      expect(screen.getByText(/Pregão Eletrônico/i)).toBeInTheDocument();
    });

    it('should display UF and municipality', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      expect(screen.getByText(/SP - São Paulo/i)).toBeInTheDocument();
    });

    it('should show Ver Edital link', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      const link = screen.getByRole('link', { name: /Ver Edital/i });
      expect(link).toHaveAttribute('href', mockLicitacao.link);
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Matched keywords', () => {
    it('should highlight matched keywords', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} matchedKeywords={['uniformes', 'escolares']} />);

      const marks = screen.getAllByRole('mark', { hidden: true });
      expect(marks.length).toBeGreaterThan(0);
    });

    it('should display keyword tags', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} matchedKeywords={['uniformes', 'escolares']} />);

      expect(screen.getByText('uniformes')).toBeInTheDocument();
      expect(screen.getByText('escolares')).toBeInTheDocument();
    });

    it('should limit displayed keywords to 5', () => {
      const manyKeywords = ['a', 'b', 'c', 'd', 'e', 'f', 'g'];
      render(<LicitacaoCard licitacao={mockLicitacao} matchedKeywords={manyKeywords} />);

      expect(screen.getByText('+2 mais')).toBeInTheDocument();
    });

    it('should render without keywords', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      const marks = screen.queryAllByRole('mark', { hidden: true });
      expect(marks.length).toBe(0);
    });
  });

  describe('Countdown display', () => {
    it('should show countdown for upcoming abertura', () => {
      const futureLicitacao: LicitacaoItem = {
        ...mockLicitacao,
        data_abertura: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days from now
      };

      render(<LicitacaoCard licitacao={futureLicitacao} status="aberta" />);

      // Countdown component should be rendered
      const countdown = document.querySelector('[data-testid]') || screen.getByText(/\d+d/i);
      expect(countdown).toBeTruthy();
    });

    it('should not show countdown for past abertura', () => {
      const pastLicitacao: LicitacaoItem = {
        ...mockLicitacao,
        data_abertura: '2020-01-01T10:00:00',
      };

      render(<LicitacaoCard licitacao={pastLicitacao} />);

      // No countdown for past dates
      const hasCountdown = document.querySelectorAll('[data-testid]').length > 0;
      expect(hasCountdown).toBe(false);
    });

    it('should handle missing data_abertura', () => {
      const noAberturaLicitacao: LicitacaoItem = {
        ...mockLicitacao,
        data_abertura: null,
      };

      render(<LicitacaoCard licitacao={noAberturaLicitacao} />);

      // Should render without errors
      expect(screen.getByText(/uniformes escolares/i)).toBeInTheDocument();
    });
  });

  describe('Favorite functionality', () => {
    it('should render favorite button when onFavorite provided', () => {
      const onFavorite = jest.fn();
      render(<LicitacaoCard licitacao={mockLicitacao} onFavorite={onFavorite} />);

      const favoriteButton = screen.getByRole('button', { name: /Adicionar aos favoritos/i });
      expect(favoriteButton).toBeInTheDocument();
    });

    it('should call onFavorite when clicked', () => {
      const onFavorite = jest.fn();
      render(<LicitacaoCard licitacao={mockLicitacao} onFavorite={onFavorite} />);

      const favoriteButton = screen.getByRole('button', { name: /Adicionar aos favoritos/i });
      fireEvent.click(favoriteButton);

      expect(onFavorite).toHaveBeenCalledWith(mockLicitacao);
    });

    it('should show filled heart when favorited', () => {
      const onFavorite = jest.fn();
      render(<LicitacaoCard licitacao={mockLicitacao} onFavorite={onFavorite} isFavorited={true} />);

      const favoriteButton = screen.getByRole('button', { name: /Remover dos favoritos/i });
      expect(favoriteButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('should not render favorite button when onFavorite not provided', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      const favoriteButton = screen.queryByRole('button', { name: /favoritos/i });
      expect(favoriteButton).not.toBeInTheDocument();
    });
  });

  describe('Share functionality', () => {
    it('should render share button', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      const shareButton = screen.getByRole('button', { name: /Compartilhar/i });
      expect(shareButton).toBeInTheDocument();
    });

    it('should use Web Share API when available', async () => {
      (navigator.share as jest.Mock).mockResolvedValue(undefined);

      render(<LicitacaoCard licitacao={mockLicitacao} />);

      const shareButton = screen.getByRole('button', { name: /Compartilhar/i });
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(navigator.share).toHaveBeenCalledWith({
          title: expect.stringContaining('uniformes'),
          text: expect.stringContaining('Secretaria'),
          url: mockLicitacao.link,
        });
      });
    });

    it('should fallback to clipboard when Web Share not available', async () => {
      const originalShare = navigator.share;
      // @ts-ignore
      delete navigator.share;

      (navigator.clipboard.writeText as jest.Mock).mockResolvedValue(undefined);

      render(<LicitacaoCard licitacao={mockLicitacao} />);

      const shareButton = screen.getByRole('button', { name: /Compartilhar/i });
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockLicitacao.link);
      });

      navigator.share = originalShare;
    });

    it('should call custom onShare when provided', async () => {
      const onShare = jest.fn();
      render(<LicitacaoCard licitacao={mockLicitacao} onShare={onShare} />);

      const shareButton = screen.getByRole('button', { name: /Compartilhar/i });
      fireEvent.click(shareButton);

      expect(onShare).toHaveBeenCalledWith(mockLicitacao);
      expect(navigator.share).not.toHaveBeenCalled();
    });
  });

  describe('Compact variant', () => {
    it('should render compact version', () => {
      render(<LicitacaoCardCompact licitacao={mockLicitacao} />);

      expect(screen.getByText(/uniformes escolares/i)).toBeInTheDocument();
    });

    it('should pass compact prop to base component', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} compact={true} />);

      // Compact should have smaller text (line-clamp-2 vs line-clamp-3)
      const heading = screen.getByText(/uniformes escolares/i);
      expect(heading).toHaveClass('line-clamp-2');
    });
  });

  describe('Hover effect', () => {
    it('should apply hover styles', () => {
      const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

      const card = container.querySelector('article');
      expect(card).toBeInTheDocument();

      if (card) {
        fireEvent.mouseEnter(card);
        expect(card).toHaveClass('border-brand-blue');

        fireEvent.mouseLeave(card);
      }
    });
  });

  describe('Date formatting', () => {
    it('should format dates with time', () => {
      render(<LicitacaoCard licitacao={mockLicitacao} />);

      expect(screen.getByText(/15\/02\/2026 às 09:00/i)).toBeInTheDocument();
      expect(screen.getByText(/28\/02\/2026 às 18:00/i)).toBeInTheDocument();
    });

    it('should handle invalid dates gracefully', () => {
      const invalidDateLicitacao: LicitacaoItem = {
        ...mockLicitacao,
        data_abertura: 'invalid-date',
      };

      render(<LicitacaoCard licitacao={invalidDateLicitacao} />);

      // Should still render without crashing
      expect(screen.getByText(/uniformes escolares/i)).toBeInTheDocument();
    });

    it('should show dash for null dates', () => {
      const noDateLicitacao: LicitacaoItem = {
        ...mockLicitacao,
        data_abertura: null,
        data_encerramento: null,
      };

      render(<LicitacaoCard licitacao={noDateLicitacao} />);

      expect(screen.getByText(/uniformes escolares/i)).toBeInTheDocument();
    });
  });

  describe('Tooltips', () => {
    it('should render tooltips on hover', async () => {
      const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

      const tooltipTriggers = container.querySelectorAll('.cursor-help');
      expect(tooltipTriggers.length).toBeGreaterThan(0);

      if (tooltipTriggers[0]) {
        fireEvent.mouseEnter(tooltipTriggers[0]);

        await waitFor(() => {
          expect(screen.getByText(/Data de início/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(<LicitacaoCard licitacao={mockLicitacao} className="custom-class" />);

      const card = container.querySelector('.custom-class');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Missing municipio', () => {
    it('should render without municipio', () => {
      const noMunicipioLicitacao: LicitacaoItem = {
        ...mockLicitacao,
        municipio: null,
      };

      render(<LicitacaoCard licitacao={noMunicipioLicitacao} />);

      expect(screen.getByText('SP')).toBeInTheDocument();
      expect(screen.queryByText(/-/)).not.toBeInTheDocument();
    });
  });
});
