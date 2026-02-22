/**
 * Tests for PlanBadge component (STORY-165)
 * Updated UX-343: Legacy plans now display as "SmartLic Pro"
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PlanBadge } from '../app/components/PlanBadge';

describe('PlanBadge', () => {
  describe('Plan tier rendering', () => {
    it('renders FREE trial badge with correct styling', () => {
      render(
        <PlanBadge
          planId="free_trial"
          planName="Avaliação"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('Avaliação');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-gray-500');
    });

    it('renders legacy Consultor Ágil as SmartLic Pro', () => {
      render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('SmartLic Pro');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-brand-navy');
    });

    it('renders legacy Máquina as SmartLic Pro', () => {
      render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('SmartLic Pro');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-brand-navy');
    });

    it('renders legacy Sala de Guerra as SmartLic Pro', () => {
      render(
        <PlanBadge
          planId="sala_guerra"
          planName="Sala de Guerra"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('SmartLic Pro');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-brand-navy');
    });

    it('renders SmartLic Pro badge correctly', () => {
      render(
        <PlanBadge
          planId="smartlic_pro"
          planName="SmartLic Pro"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('SmartLic Pro');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-brand-navy');
    });
  });

  describe('Trial countdown', () => {
    it('shows countdown when trial expires in 3 days', () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 3);

      render(
        <PlanBadge
          planId="free_trial"
          planName="Avaliação"
          trialExpiresAt={futureDate.toISOString()}
          onClick={jest.fn()}
        />
      );

      expect(screen.getByText(/3 dias restantes/i)).toBeInTheDocument();
    });

    it('shows singular "dia restante" when 1 day left', () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 1);

      render(
        <PlanBadge
          planId="free_trial"
          planName="Avaliação"
          trialExpiresAt={futureDate.toISOString()}
          onClick={jest.fn()}
        />
      );

      expect(screen.getByText(/1 dia restante/i)).toBeInTheDocument();
    });

    it('applies pulse animation when less than 2 days remaining', () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 1);

      render(
        <PlanBadge
          planId="free_trial"
          planName="Avaliação"
          trialExpiresAt={futureDate.toISOString()}
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByRole('button');
      expect(badge).toHaveClass('animate-pulse');
    });

    it('does not show countdown for paid plans', () => {
      render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={jest.fn()}
        />
      );

      expect(screen.queryByText(/dias restantes/i)).not.toBeInTheDocument();
    });

    it('handles expired trial (0 days remaining)', () => {
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - 1);

      render(
        <PlanBadge
          planId="free_trial"
          planName="Avaliação"
          trialExpiresAt={pastDate.toISOString()}
          onClick={jest.fn()}
        />
      );

      expect(screen.getByText(/0 dias restantes/i)).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClick when badge is clicked', () => {
      const handleClick = jest.fn();

      render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={handleClick}
        />
      );

      const badge = screen.getByRole('button');
      fireEvent.click(badge);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('has accessible label with SmartLic Pro for legacy plans', () => {
      render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByRole('button');
      expect(badge).toHaveAttribute('aria-label', expect.stringContaining('SmartLic Pro'));
    });
  });

  describe('Icons', () => {
    it('shows A letter icon for FREE trial', () => {
      const { container } = render(
        <PlanBadge
          planId="free_trial"
          planName="Avaliação"
          onClick={jest.fn()}
        />
      );

      expect(container.textContent).toContain('A');
    });

    it('shows P letter icon for legacy Consultor Ágil', () => {
      const { container } = render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={jest.fn()}
        />
      );

      // Legacy plans now show P for Pro
      expect(container.textContent).toContain('P');
    });

    it('shows P letter icon for legacy Máquina', () => {
      const { container } = render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      // Legacy plans now show P for Pro
      expect(container.textContent).toContain('P');
    });

    it('shows P letter icon for legacy Sala de Guerra', () => {
      const { container } = render(
        <PlanBadge
          planId="sala_guerra"
          planName="Sala de Guerra"
          onClick={jest.fn()}
        />
      );

      // Legacy plans now show P for Pro
      expect(container.textContent).toContain('P');
    });

    it('shows P letter icon for SmartLic Pro', () => {
      const { container } = render(
        <PlanBadge
          planId="smartlic_pro"
          planName="SmartLic Pro"
          onClick={jest.fn()}
        />
      );

      expect(container.textContent).toContain('P');
    });
  });
});
