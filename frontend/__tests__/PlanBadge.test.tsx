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
          planName="FREE Trial"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('FREE Trial');
      expect(badge).toBeInTheDocument();
      expect(badge.parentElement).toHaveClass('bg-gray-500');
    });

    it('renders Consultor Ágil badge with correct styling', () => {
      render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('Consultor Ágil');
      expect(badge).toBeInTheDocument();
      expect(badge.parentElement).toHaveClass('bg-blue-500');
    });

    it('renders Máquina badge with correct styling', () => {
      render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      const badge = screen.getByText('Máquina');
      expect(badge).toBeInTheDocument();
      expect(badge.parentElement).toHaveClass('bg-green-500');
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
      expect(badge.parentElement).toHaveClass('bg-yellow-500');
    });
  });

  describe('Trial countdown', () => {
    it('shows countdown when trial expires in 3 days', () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 3);

      render(
        <PlanBadge
          planId="free_trial"
          planName="FREE Trial"
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
          planName="FREE Trial"
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
          planName="FREE Trial"
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
          planName="FREE Trial"
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
      expect(badge).toHaveAttribute('aria-label', expect.stringContaining('Máquina'));
    });
  });

  describe('Icons', () => {
    it('shows warning icon for FREE trial', () => {
      const { container } = render(
        <PlanBadge
          planId="free_trial"
          planName="FREE Trial"
          onClick={jest.fn()}
        />
      );

      expect(container.textContent).toContain('⚠️');
    });

    it('shows briefcase icon for Consultor Ágil', () => {
      const { container } = render(
        <PlanBadge
          planId="consultor_agil"
          planName="Consultor Ágil"
          onClick={jest.fn()}
        />
      );

      expect(container.textContent).toContain('💼');
    });

    it('shows gear icon for Máquina', () => {
      const { container } = render(
        <PlanBadge
          planId="maquina"
          planName="Máquina"
          onClick={jest.fn()}
        />
      );

      expect(container.textContent).toContain('⚙️');
    });

    it('shows crown icon for Sala de Guerra', () => {
      const { container } = render(
        <PlanBadge
          planId="sala_guerra"
          planName="Sala de Guerra"
          onClick={jest.fn()}
        />
      );

      expect(container.textContent).toContain('👑');
    });
  });
});
