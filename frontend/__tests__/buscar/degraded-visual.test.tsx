/**
 * Tests for EnhancedLoadingProgress degraded visual state
 * GTM-RESILIENCE-A02 AC14 — Amber visual transition for degraded data
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { EnhancedLoadingProgress } from '../../components/EnhancedLoadingProgress';

describe('EnhancedLoadingProgress - GTM-RESILIENCE-A02 Degraded Visuals', () => {
  const defaultProps = {
    currentStep: 2,
    estimatedTime: 30,
    stateCount: 5,
  };

  describe('AC14: Amber visual styling when isDegraded=true', () => {
    it('should render with amber styling when isDegraded=true', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
          degradedMessage="Dados de cache de 3 horas atrás — PNCP indisponível"
        />
      );

      // Verify degraded progress container
      const degradedContainer = screen.getByTestId('degraded-progress');
      expect(degradedContainer).toBeInTheDocument();
      expect(degradedContainer).toHaveClass('bg-amber-50');
      expect(degradedContainer).toHaveClass('border-amber-200');

      // Verify degraded message banner
      const degradedMessage = screen.getByTestId('degraded-message');
      expect(degradedMessage).toBeInTheDocument();
      expect(degradedMessage).toHaveTextContent('Dados de cache de 3 horas atrás — PNCP indisponível');
      expect(degradedMessage).toHaveClass('bg-amber-100');
      expect(degradedMessage).toHaveClass('border-amber-300');
    });

    it('should use default degraded message when none provided', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
        />
      );

      const degradedMessage = screen.getByTestId('degraded-message');
      expect(degradedMessage).toHaveTextContent('Resultados disponíveis com ressalvas');
    });

    it('should apply amber color to progress bar when degraded', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      const progressBarParent = progressBar.parentElement;

      // Progress bar should have amber gradient
      expect(progressBar).toHaveClass('bg-gradient-to-r');
      expect(progressBar).toHaveClass('from-amber-500');
      expect(progressBar).toHaveClass('to-amber-600');

      // Should NOT have blue gradient
      expect(progressBar).not.toHaveClass('from-brand-blue');
      expect(progressBar).not.toHaveClass('to-brand-blue-hover');
    });

    it('should apply amber color to percentage text when degraded', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
        />
      );

      // Find percentage text by looking for aria-valuemax attribute on progressbar
      const progressBar = screen.getByRole('progressbar');
      const percentage = parseInt(progressBar.getAttribute('aria-valuenow') || '0');

      // Find text containing the percentage (using getAllByText since there might be multiple)
      const percentageElements = screen.getAllByText(new RegExp(`${percentage}%`));
      const percentageText = percentageElements.find(el => el.classList.contains('font-bold'));

      expect(percentageText).toBeInTheDocument();
      expect(percentageText).toHaveClass('text-amber-600');
    });

    it('should apply amber styling to active stage indicator when degraded', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
        />
      );

      // Active stage (stage 1 by default) — pick the stage indicator label (second occurrence)
      const labels = screen.getAllByText('Consultando fontes oficiais');
      const stageLabel = labels.find(el => el.classList.contains('text-center'));
      expect(stageLabel).toBeDefined();
      expect(stageLabel).toHaveClass('text-amber-600');
      expect(stageLabel).toHaveClass('font-semibold');
    });
  });

  describe('AC14: Normal styling when isDegraded=false', () => {
    it('should render with normal styling when isDegraded=false', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={false}
        />
      );

      // Verify normal progress container
      const loadingContainer = screen.getByTestId('loading-progress');
      expect(loadingContainer).toBeInTheDocument();
      expect(loadingContainer).toHaveClass('bg-surface-0');
      expect(loadingContainer).toHaveClass('border-strong');

      // Should NOT have amber styling
      expect(loadingContainer).not.toHaveClass('bg-amber-50');
      expect(loadingContainer).not.toHaveClass('border-amber-200');

      // Degraded message should NOT be present
      const degradedMessage = screen.queryByTestId('degraded-message');
      expect(degradedMessage).not.toBeInTheDocument();
    });

    it('should apply blue color to progress bar when not degraded', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={false}
        />
      );

      const progressBar = screen.getByRole('progressbar');

      // Progress bar should have blue gradient
      expect(progressBar).toHaveClass('bg-gradient-to-r');
      expect(progressBar).toHaveClass('from-brand-blue');
      expect(progressBar).toHaveClass('to-brand-blue-hover');

      // Should NOT have amber gradient
      expect(progressBar).not.toHaveClass('from-amber-500');
      expect(progressBar).not.toHaveClass('to-amber-600');
    });

    it('should apply blue color to percentage text when not degraded', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={false}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      const percentage = parseInt(progressBar.getAttribute('aria-valuenow') || '0');

      const percentageElements = screen.getAllByText(new RegExp(`${percentage}%`));
      const percentageText = percentageElements.find(el => el.classList.contains('font-bold'));

      expect(percentageText).toBeInTheDocument();
      expect(percentageText).toHaveClass('text-brand-blue');
    });

    it('should apply blue styling to active stage indicator when not degraded', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={false}
        />
      );

      // Active stage (stage 1 by default) — pick the stage indicator label (second occurrence)
      const labels = screen.getAllByText('Consultando fontes oficiais');
      const stageLabel = labels.find(el => el.classList.contains('text-center'));
      expect(stageLabel).toBeDefined();
      expect(stageLabel).toHaveClass('text-brand-blue');
      expect(stageLabel).toHaveClass('font-semibold');
    });
  });

  describe('AC14: degradedMessage prop display', () => {
    it('should display custom degradedMessage in amber banner', () => {
      const customMessage = 'Cache local de 18 horas — PNCP e PCP indisponíveis';
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
          degradedMessage={customMessage}
        />
      );

      const degradedMessage = screen.getByTestId('degraded-message');
      expect(degradedMessage).toHaveTextContent(customMessage);
    });

    it('should not show degraded banner when isDegraded=false even if message provided', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={false}
          degradedMessage="This should not appear"
        />
      );

      const degradedMessage = screen.queryByTestId('degraded-message');
      expect(degradedMessage).not.toBeInTheDocument();
    });

    it('should render amber warning icon in degraded banner', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
          degradedMessage="Test message"
        />
      );

      const degradedMessage = screen.getByTestId('degraded-message');
      const icon = degradedMessage.querySelector('svg');

      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-amber-600');
    });
  });

  describe('AC14: aria-label updates for degraded state', () => {
    it('should have degraded-specific aria-label when isDegraded=true', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={true}
        />
      );

      const container = screen.getByTestId('degraded-progress');
      expect(container).toHaveAttribute('aria-label', 'Resultados disponíveis com ressalvas');
    });

    it('should have normal aria-label when isDegraded=false', () => {
      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          isDegraded={false}
        />
      );

      const container = screen.getByTestId('loading-progress');
      expect(container).toHaveAttribute('aria-label', expect.stringMatching(/Buscando licitações, \d+% completo/));
    });
  });

  describe('AC14: Overtime message should NOT show when degraded', () => {
    it('should not show overtime message when isDegraded=true even if elapsed > estimated', () => {
      // Mock Date.now to simulate elapsed time > estimated time
      const originalDateNow = Date.now;
      const startTime = 1000000;
      Date.now = jest.fn(() => startTime + 60000); // 60s elapsed

      render(
        <EnhancedLoadingProgress
          {...defaultProps}
          estimatedTime={30} // Only 30s estimated
          isDegraded={true}
        />
      );

      // Overtime message should NOT be present (degraded takes precedence)
      const overtimeMessage = screen.queryByText(/Quase pronto|Estamos trabalhando|Esta busca está demorando/);
      expect(overtimeMessage).not.toBeInTheDocument();

      // Degraded message should be present instead
      const degradedMessage = screen.getByTestId('degraded-message');
      expect(degradedMessage).toBeInTheDocument();

      Date.now = originalDateNow;
    });
  });
});
