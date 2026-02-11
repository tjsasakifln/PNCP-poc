/**
 * Tests for PlanBadge component (STORY-165)
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
          planName="Gratuito"
          onClick={jest.fn()}
        />
      );

      // getPlanDisplayName returns "Gratuito" for free_trial
      const badge = screen.getByText('Gratuito');
      expect(badge).toBeInTheDocument();
      // The button element has the styling class
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-gray-500');
    });

    it('renders Consultor Ágil badge with correct styling', () => {
      render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={jest.fn()}
        />
      );

      // getPlanDisplayName returns "Consultor Agil" (no accent)
      const badge = screen.getByText('Consultor Agil');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-blue-500');
    });

    it('renders Máquina badge with correct styling', () => {
      render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      // getPlanDisplayName returns "Maquina" (no accent)
      const badge = screen.getByText('Maquina');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-green-500');
    });

    it('renders Sala de Guerra badge with correct styling', () => {
      render(
        <PlanBadge
          planId="sala_guerra"
          planName="Sala de Guerra"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('Sala de Guerra');
      expect(badge).toBeInTheDocument();
      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-yellow-500');
    });
  });

  describe('Trial countdown', () => {
    it('shows countdown when trial expires in 3 days', () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 3);

      render(
        <PlanBadge
          planId="free_trial"
          planName="Gratuito"
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
          planName="Gratuito"
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
          planName="Gratuito"
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
          planName="Gratuito"
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

    it('has accessible label', () => {
      render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByRole('button');
      // aria-label uses getPlanDisplayName which returns "Maquina" (no accent)
      expect(badge).toHaveAttribute('aria-label', expect.stringContaining('Maquina'));
    });
  });

  describe('Icons', () => {
    it('shows G letter icon for FREE trial', () => {
      const { container } = render(
        <PlanBadge
          planId="free_trial"
          planName="Gratuito"
          onClick={jest.fn()}
        />
      );

      // Component uses letter icons: G for Gratuito
      expect(container.textContent).toContain('G');
    });

    it('shows C letter icon for Consultor Ágil', () => {
      const { container } = render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={jest.fn()}
        />
      );

      // Component uses letter icons: C for Consultor
      expect(container.textContent).toContain('C');
    });

    it('shows M letter icon for Máquina', () => {
      const { container } = render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      // Component uses letter icons: M for Maquina
      expect(container.textContent).toContain('M');
    });

    it('shows S letter icon for Sala de Guerra', () => {
      const { container } = render(
        <PlanBadge
          planId="sala_guerra"
          planName="Sala de Guerra"
          onClick={jest.fn()}
        />
      );

      // Component uses letter icons: S for Sala de Guerra
      expect(container.textContent).toContain('S');
    });
  });
});
