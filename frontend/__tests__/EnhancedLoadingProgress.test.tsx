/**
 * EnhancedLoadingProgress Component Tests
 * Feature #2 - Phase 3 Day 9
 * Target: +5% test coverage
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EnhancedLoadingProgress } from '../components/EnhancedLoadingProgress';

describe('EnhancedLoadingProgress Component', () => {
  const mockOnStageChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    // Clean up all timers before switching back to real timers
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  describe('TC-LOADING-001: Basic rendering', () => {
    it('should render loading indicator with initial stage', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
        />
      );

      expect(screen.getByRole('status')).toBeInTheDocument();
      // Use getAllByText and check first match (main heading) to handle duplicates
      expect(screen.getAllByText('Consultando fontes oficiais')[0]).toBeInTheDocument();
      expect(screen.getByText(/Consultando fontes oficiais\. Resultados em aproximadamente 60s\./)).toBeInTheDocument();
    });

    it('should display state count correctly', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={27}
        />
      );

      expect(screen.getByText(/Buscando em todo o Brasil/)).toBeInTheDocument();
    });

    it('should display singular state when count is 1', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={1}
        />
      );

      expect(screen.getByText(/Processando 1 estado/)).toBeInTheDocument();
    });
  });

  describe('TC-LOADING-002: Progress calculation', () => {
    it('should start at 0% progress', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
        />
      );

      // Initially should show 0%
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should update progress over time', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={10}
          stateCount={3}
        />
      );

      // Fast-forward 5 seconds (50% of 10s estimated time)
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        const progressText = screen.getByText(/\d+%/);
        const percentage = parseInt(progressText.textContent || '0');
        expect(percentage).toBeGreaterThan(0);
        expect(percentage).toBeLessThanOrEqual(100);
      });
    });

    it('should cap progress at 100%', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={5}
          stateCount={3}
        />
      );

      // Fast-forward past estimated time (10s > 5s)
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      await waitFor(() => {
        const progressText = screen.getByText(/\d+%/);
        const percentage = parseInt(progressText.textContent || '0');
        expect(percentage).toBeLessThanOrEqual(100);
      });
    });
  });

  describe('TC-LOADING-003: Stage transitions', () => {
    it('should transition through stages as progress increases', async () => {
      // GTM-FIX-035: With UF-based progress, stages now depend on statesProcessed
      // Stage 1 (0-10%): Consultando fontes oficiais
      // Stage 2 (10-70%): Buscando dados (driven by UF completion)
      // Stage 3 (70%+): Filtrando resultados
      const { rerender } = render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={50}
          stateCount={3}
          statesProcessed={0}
          onStageChange={mockOnStageChange}
        />
      );

      // Stage 1: Consultando fontes oficiais (0% progress, no states processed)
      expect(screen.getAllByText('Consultando fontes oficiais')[0]).toBeInTheDocument();

      // Rerender with 2 of 3 states processed → 10 + (2/3 * 60) = 50% → Stage 2
      rerender(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={50}
          stateCount={3}
          statesProcessed={2}
          onStageChange={mockOnStageChange}
        />
      );
      // "Buscando dados" appears both in header and in stage indicator
      expect(screen.getAllByText('Buscando dados').length).toBeGreaterThanOrEqual(1);

      // Rerender with all states processed + ufAllComplete → 70% → Stage 3
      rerender(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={50}
          stateCount={3}
          statesProcessed={3}
          ufAllComplete={true}
          onStageChange={mockOnStageChange}
        />
      );
      expect(screen.getAllByText('Filtrando resultados')[0]).toBeInTheDocument();
    });

    it('should call onStageChange callback when stage changes', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={20}
          stateCount={3}
          onStageChange={mockOnStageChange}
        />
      );

      // Fast-forward to trigger stage 2 (40% of 20s = 8s)
      // Need to reach 40% threshold for stage 2
      act(() => {
        jest.advanceTimersByTime(9000);
      });

      await waitFor(() => {
        expect(mockOnStageChange).toHaveBeenCalledWith(expect.any(Number));
      });
    });
  });

  describe('TC-LOADING-004: Elapsed time display', () => {
    it('should display elapsed time in seconds', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
        />
      );

      // Fast-forward 10 seconds
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      await waitFor(() => {
        expect(screen.getByText(/10s/)).toBeInTheDocument();
        expect(screen.getByText(/~60s/)).toBeInTheDocument();
      });
    });

    it('should show remaining time estimate', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={30}
          stateCount={3}
          statesProcessed={1}
        />
      );

      // Fast-forward 10 seconds
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      await waitFor(() => {
        // GTM-FIX-035: "~20s restantes" appears in both status description and meta area
        expect(screen.getAllByText(/~20s restantes/).length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should show overtime message when elapsed exceeds estimated', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={10}
          stateCount={3}
        />
      );

      // Fast-forward past estimated time
      act(() => {
        jest.advanceTimersByTime(15000);
      });

      await waitFor(() => {
        expect(screen.getByText(/Quase pronto, finalizando\.\.\./)).toBeInTheDocument();
      });
    });
  });

  describe('TC-LOADING-005: Stage indicators', () => {
    it('should show all 5 stage circles', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
        />
      );

      // Should have 5 stage indicators (1 to 5)
      const stages = screen.getAllByText(/^[1-5]$/);
      expect(stages).toHaveLength(5);
    });

    it('should mark completed stages with checkmark', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={20}
          stateCount={3}
        />
      );

      // Fast-forward to stage 3 (40% of 20s = 8s)
      act(() => {
        jest.advanceTimersByTime(9000);
      });

      await waitFor(() => {
        // Stages 1 and 2 should be completed (showing checkmarks)
        const completedStages = screen.getAllByRole('img', { hidden: true });
        expect(completedStages.length).toBeGreaterThan(0);
      });
    });
  });

  describe('TC-LOADING-006: Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
        />
      );

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');
      expect(statusElement).toHaveAttribute('aria-label', expect.stringContaining('Buscando licitações'));
    });

    it('should have progressbar role with correct values', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('should update aria-valuenow as progress changes', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={20}
          stateCount={3}
        />
      );

      // Fast-forward 10 seconds (50% of 20s)
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        const valueNow = parseInt(progressBar.getAttribute('aria-valuenow') || '0');
        expect(valueNow).toBeGreaterThan(0);
        expect(valueNow).toBeLessThanOrEqual(100);
      });
    });
  });

  describe('TC-LOADING-007: Progress bar visual', () => {
    it('should render gradient progress bar', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('bg-gradient-to-r');
      expect(progressBar).toHaveClass('from-brand-blue');
      expect(progressBar).toHaveClass('to-brand-blue-hover');
    });

    it('should update progress bar width based on percentage', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={10}
          stateCount={3}
        />
      );

      const progressBar = screen.getByRole('progressbar');

      // Initially 0%
      expect(progressBar).toHaveStyle({ width: '0%' });

      // Fast-forward 5 seconds (50% of 10s)
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        const width = progressBar.style.width;
        const percentage = parseInt(width);
        expect(percentage).toBeGreaterThan(0);
      });
    });
  });

  describe('TC-LOADING-035: GTM-FIX-035 Progress UX improvements', () => {
    it('AC3: should sync progress with UF completion (statesProcessed drives percentage)', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={5}
          statesProcessed={3}
        />
      );

      // With 3 of 5 states processed, UF-based progress = 10 + (3/5 * 60) = 46%
      // The percentage shown should be >= 46%
      const progressText = screen.getByText(/\d+%/);
      const percentage = parseInt(progressText.textContent || '0');
      expect(percentage).toBeGreaterThanOrEqual(46);
    });

    it('AC3: should show 70% when all UFs complete (ufAllComplete=true)', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          statesProcessed={3}
          ufAllComplete={true}
        />
      );

      // ufAllComplete=true → ufRatio=1 → 10 + (1 * 60) = 70%
      const progressText = screen.getByText(/\d+%/);
      const percentage = parseInt(progressText.textContent || '0');
      expect(percentage).toBeGreaterThanOrEqual(70);
    });

    it('AC3: should cap at connecting stage (10%) when no states processed yet', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={5}
          statesProcessed={0}
        />
      );

      const progressText = screen.getByText(/\d+%/);
      const percentage = parseInt(progressText.textContent || '0');
      expect(percentage).toBeLessThanOrEqual(10);
    });

    it('AC4: should show contextual message with source count and time estimate', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={45}
          stateCount={3}
          statesProcessed={0}
        />
      );

      expect(screen.getByText(/Consultando fontes oficiais\. Resultados em aproximadamente 45s\./)).toBeInTheDocument();
    });

    it('AC5: should show 2x overrun reassurance message', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={10}
          stateCount={3}
          statesProcessed={3}
        />
      );

      // Fast-forward past 2x estimate (>20s)
      act(() => {
        jest.advanceTimersByTime(21000);
      });

      await waitFor(() => {
        expect(screen.getByText(/Esta busca está demorando mais que o normal/)).toBeInTheDocument();
        expect(screen.getByText(/os resultados serão exibidos automaticamente/)).toBeInTheDocument();
      });
    });

    it('AC2: should accept sseDisconnected prop without crashing', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      expect(screen.getByText(/Finalizando busca/)).toBeInTheDocument();
    });
  });

  describe('TC-LOADING-008: Edge cases', () => {
    it('should handle very short estimated time (< 1s)', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={0.5}
          stateCount={1}
        />
      );

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('should handle very long estimated time (> 5min)', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={360}
          stateCount={27}
        />
      );

      // Component formats as "6m 0s" for times > 5min (appears multiple times in UI)
      expect(screen.getAllByText(/6m/)[0]).toBeInTheDocument();
    });

    it('should handle state count = 0', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={0}
        />
      );

      expect(screen.getByText(/Processando 0 estados/)).toBeInTheDocument();
    });
  });
});
