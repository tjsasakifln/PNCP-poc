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
      expect(screen.getAllByText('Conectando ao PNCP')[0]).toBeInTheDocument();
      expect(screen.getByText(/Estabelecendo conexão com o Portal Nacional/)).toBeInTheDocument();
    });

    it('should display state count correctly', () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={27}
        />
      );

      expect(screen.getByText(/Processando 27 estados/)).toBeInTheDocument();
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
    it('should transition through all 5 stages', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={50}
          stateCount={3}
          onStageChange={mockOnStageChange}
        />
      );

      // Stage 1: Conectando (0-10%)
      expect(screen.getAllByText('Conectando ao PNCP')[0]).toBeInTheDocument();

      // Fast-forward to Stage 2: Buscando (10-40%)
      act(() => {
        jest.advanceTimersByTime(6000); // 12% of 50s
      });
      await waitFor(() => {
        expect(screen.getByText('Buscando dados')).toBeInTheDocument();
      });

      // Fast-forward to Stage 3: Filtrando (40-70%)
      act(() => {
        jest.advanceTimersByTime(15000); // 30% more
      });
      await waitFor(() => {
        expect(screen.getByText('Filtrando resultados')).toBeInTheDocument();
      });

      // Fast-forward to Stage 4: Gerando resumo (70-90%)
      act(() => {
        jest.advanceTimersByTime(10000); // 20% more
      });
      await waitFor(() => {
        expect(screen.getByText('Gerando resumo IA')).toBeInTheDocument();
      });

      // Fast-forward to Stage 5: Preparando Excel (90-100%)
      act(() => {
        jest.advanceTimersByTime(7000); // 14% more
      });
      await waitFor(() => {
        expect(screen.getByText('Preparando Excel')).toBeInTheDocument();
      });
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
        expect(screen.getByText(/10s \/ 60s/)).toBeInTheDocument();
      });
    });

    it('should show remaining time estimate', async () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={30}
          stateCount={3}
        />
      );

      // Fast-forward 10 seconds
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      await waitFor(() => {
        expect(screen.getByText(/~20s restantes/)).toBeInTheDocument();
      });
    });

    it('should show "Finalizando..." when elapsed exceeds estimated', async () => {
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
        expect(screen.getByText(/Finalizando\.\.\./)).toBeInTheDocument();
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
