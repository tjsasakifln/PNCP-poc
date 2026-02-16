/**
 * Tests for QuotaCounter component (STORY-165)
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { QuotaCounter } from '../app/components/QuotaCounter';

describe('QuotaCounter', () => {
  const mockResetDate = '2026-03-01T00:00:00Z';

  describe('Progress bar colors', () => {
    it('shows green progress bar when usage < 70%', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={30}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const progressBar = container.querySelector('.bg-green-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('shows yellow progress bar when usage 70-89%', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={40}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const progressBar = container.querySelector('.bg-yellow-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('shows orange progress bar when usage 90-99%', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={47}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const progressBar = container.querySelector('.bg-orange-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('shows red progress bar when quota exhausted', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={50}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const progressBar = container.querySelector('.bg-red-500');
      expect(progressBar).toBeInTheDocument();
    });
  });

  describe('Quota display', () => {
    it('displays quota used and limit correctly', () => {
      render(
        <QuotaCounter
          quotaUsed={23}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      expect(screen.getByText(/27 análises restantes neste mês/i)).toBeInTheDocument();
    });

    it('formats reset date correctly (pt-BR)', () => {
      render(
        <QuotaCounter
          quotaUsed={10}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      expect(screen.getByText(/Renovação:/i)).toBeInTheDocument();
      // Date formatting includes the reset date (may vary by timezone)
      expect(screen.getByText(/\/2026/i)).toBeInTheDocument();
    });

    it('calculates progress percentage correctly', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={25}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const progressBar = container.querySelector('[style*="width"]');
      expect(progressBar).toHaveStyle({ width: '50%' });
    });
  });

  describe('Exhausted state', () => {
    it('shows exhausted message when quota fully used', () => {
      render(
        <QuotaCounter
          quotaUsed={50}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
          onUpgradeClick={jest.fn()}
        />
      );

      expect(screen.getByText(/análises foram usadas/i)).toBeInTheDocument();
    });

    it('shows upgrade button when exhausted and onUpgradeClick provided', () => {
      const handleUpgrade = jest.fn();

      render(
        <QuotaCounter
          quotaUsed={300}
          quotaLimit={300}
          resetDate={mockResetDate}
          planId="maquina"
          onUpgradeClick={handleUpgrade}
        />
      );

      const upgradeButton = screen.getByRole('button', { name: /Continuar com SmartLic Pro/i });
      expect(upgradeButton).toBeInTheDocument();

      fireEvent.click(upgradeButton);
      expect(handleUpgrade).toHaveBeenCalledTimes(1);
    });

    it('does not show upgrade button when exhausted but no onUpgradeClick', () => {
      render(
        <QuotaCounter
          quotaUsed={50}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      expect(screen.queryByRole('button', { name: /Continuar com SmartLic Pro/i })).not.toBeInTheDocument();
    });
  });

  describe('Warning states', () => {
    it('shows warning when approaching limit (70-99%)', () => {
      render(
        <QuotaCounter
          quotaUsed={42}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      expect(screen.getByText(/próximo do limite mensal/i)).toBeInTheDocument();
    });

    it('does not show warning when below 70%', () => {
      render(
        <QuotaCounter
          quotaUsed={30}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      expect(screen.queryByText(/próximo do limite/i)).not.toBeInTheDocument();
    });

    it('does not show warning when exhausted (100%)', () => {
      render(
        <QuotaCounter
          quotaUsed={50}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
          onUpgradeClick={jest.fn()}
        />
      );

      // Should show exhausted message instead
      expect(screen.queryByText(/próximo do limite/i)).not.toBeInTheDocument();
      expect(screen.getByText(/análises foram usadas/i)).toBeInTheDocument();
    });
  });

  describe('Unlimited quota (FREE trial)', () => {
    it('shows "Buscas ilimitadas" for trial users', () => {
      render(
        <QuotaCounter
          quotaUsed={5}
          quotaLimit={999999}
          resetDate={mockResetDate}
          planId="free_trial"
        />
      );

      expect(screen.getByText(/Buscas ilimitadas/i)).toBeInTheDocument();
      expect(screen.getByText(/Durante o trial/i)).toBeInTheDocument();
    });

    it('does not show progress bar for unlimited quota', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={5}
          quotaLimit={999999}
          resetDate={mockResetDate}
          planId="free_trial"
        />
      );

      // Should not have progress bar
      expect(container.querySelector('.bg-green-500')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="status" for screen readers', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={23}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const status = container.querySelector('[role="status"]');
      expect(status).toBeInTheDocument();
    });

    it('has aria-live="polite" for updates', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={23}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const status = container.querySelector('[aria-live="polite"]');
      expect(status).toBeInTheDocument();
    });

    it('has aria-label on progress bar', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={25}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      const progressBar = container.querySelector('[aria-label*="quota"]');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-label', expect.stringContaining('50%'));
    });
  });

  describe('Edge cases', () => {
    it('handles zero quota limit gracefully', () => {
      render(
        <QuotaCounter
          quotaUsed={0}
          quotaLimit={0}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      expect(screen.getByText(/0 análises completas restantes/i)).toBeInTheDocument();
    });

    it('handles quota used exceeding limit', () => {
      render(
        <QuotaCounter
          quotaUsed={60}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
          onUpgradeClick={jest.fn()}
        />
      );

      // Should show exhausted state
      expect(screen.getByText(/análises foram usadas/i)).toBeInTheDocument();
    });

    it('caps percentage at 100% when usage exceeds limit', () => {
      const { container } = render(
        <QuotaCounter
          quotaUsed={120}
          quotaLimit={100}
          resetDate={mockResetDate}
          planId="maquina"
        />
      );

      const progressBar = container.querySelector('[style*="width"]');
      // Should be 100%, not 120%
      expect(progressBar).toHaveStyle({ width: '100%' });
    });
  });

  describe('Credits display formatting', () => {
    it('formats large quota numbers correctly', () => {
      render(
        <QuotaCounter
          quotaUsed={250}
          quotaLimit={1000}
          resetDate={mockResetDate}
          planId="sala_guerra"
        />
      );

      expect(screen.getByText(/750 análises restantes neste mês/i)).toBeInTheDocument();
    });

    it('shows remaining searches clearly', () => {
      render(
        <QuotaCounter
          quotaUsed={30}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      // 50 - 30 = 20 remaining
      expect(screen.getByText(/20 análises restantes neste mês/i)).toBeInTheDocument();
    });

    it('handles single search remaining', () => {
      render(
        <QuotaCounter
          quotaUsed={49}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      // 1 search remaining should trigger warning
      expect(screen.getByText(/1 análise restante neste mês/i)).toBeInTheDocument();
    });
  });

  describe('Free tier displays', () => {
    it('shows "análises completas" for free tier (planId="free")', () => {
      render(
        <QuotaCounter
          quotaUsed={1}
          quotaLimit={3}
          resetDate={mockResetDate}
          planId="free"
        />
      );

      expect(screen.getByText(/2 análises completas restantes/i)).toBeInTheDocument();
      expect(screen.getByText(/Período de avaliação/i)).toBeInTheDocument();
      expect(screen.queryByText(/Renovação:/i)).not.toBeInTheDocument();
    });

    it('shows "análises completas" for free tier (quotaLimit <= 5)', () => {
      render(
        <QuotaCounter
          quotaUsed={2}
          quotaLimit={5}
          resetDate={mockResetDate}
          planId="some_plan"
        />
      );

      expect(screen.getByText(/3 análises completas restantes/i)).toBeInTheDocument();
      expect(screen.getByText(/Período de avaliação/i)).toBeInTheDocument();
      expect(screen.queryByText(/Renovação:/i)).not.toBeInTheDocument();
    });
  });

  describe('Plan-specific displays', () => {
    it('correctly displays Consultor Ágil quota', () => {
      render(
        <QuotaCounter
          quotaUsed={10}
          quotaLimit={50}
          resetDate={mockResetDate}
          planId="consultor_agil"
        />
      );

      expect(screen.getByText(/40 análises restantes neste mês/i)).toBeInTheDocument();
      expect(screen.getByText(/Renovação:/i)).toBeInTheDocument();
    });

    it('correctly displays Máquina quota', () => {
      render(
        <QuotaCounter
          quotaUsed={100}
          quotaLimit={300}
          resetDate={mockResetDate}
          planId="maquina"
        />
      );

      expect(screen.getByText(/200 análises restantes neste mês/i)).toBeInTheDocument();
      expect(screen.getByText(/Renovação:/i)).toBeInTheDocument();
    });

    it('correctly displays Sala de Guerra quota', () => {
      render(
        <QuotaCounter
          quotaUsed={500}
          quotaLimit={1000}
          resetDate={mockResetDate}
          planId="sala_guerra"
        />
      );

      expect(screen.getByText(/500 análises restantes neste mês/i)).toBeInTheDocument();
      expect(screen.getByText(/Renovação:/i)).toBeInTheDocument();
    });
  });
});
