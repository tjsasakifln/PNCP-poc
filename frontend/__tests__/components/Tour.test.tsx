/**
 * STORY-4.2 (TD-FE-002) — Tour component unit tests.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

import {
  Tour,
  isTourPermanentlyDismissed,
  markTourPermanentlyDismissed,
} from '@/components/tour/Tour';

const STEPS = [
  { id: 's1', title: 'Bem-vindo', text: 'Comece por aqui.' },
  { id: 's2', title: 'Próximos passos', text: 'Aprenda a filtrar editais.' },
  { id: 's3', title: 'Finalização', text: 'Você está pronto!' },
];

describe('Tour (STORY-4.2 TD-FE-002)', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('does not render when active=false', () => {
    render(<Tour tourId="onboard" steps={STEPS} active={false} />);
    expect(screen.queryByTestId('tour-onboard')).toBeNull();
  });

  it('renders first step with ARIA attributes', () => {
    render(<Tour tourId="onboard" steps={STEPS} active />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'false');
    expect(dialog).toHaveAttribute('aria-labelledby');
    expect(dialog).toHaveAttribute('aria-describedby');
    expect(screen.getByText('Bem-vindo')).toBeInTheDocument();
  });

  it('announces step progress in a polite live region', () => {
    render(<Tour tourId="onboard" steps={STEPS} active />);
    // sr-only live region with "Passo 1 de 3"
    const liveRegion = document.querySelector('[aria-live="polite"]');
    expect(liveRegion).not.toBeNull();
    expect(liveRegion?.textContent).toContain('Passo 1 de 3');
  });

  it('advances on Next and Back buttons', () => {
    render(<Tour tourId="onboard" steps={STEPS} active />);
    expect(screen.getByText('Bem-vindo')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));
    expect(screen.getByText('Próximos passos')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /voltar/i }));
    expect(screen.getByText('Bem-vindo')).toBeInTheDocument();
  });

  it('calls onComplete when Next is pressed on the last step', () => {
    const onComplete = jest.fn();
    render(<Tour tourId="onboard" steps={STEPS} active onComplete={onComplete} />);
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));
    fireEvent.click(screen.getByRole('button', { name: /concluir/i }));
    expect(onComplete).toHaveBeenCalledWith(3);
  });

  it('calls onSkip when ESC is pressed', () => {
    const onSkip = jest.fn();
    render(<Tour tourId="onboard" steps={STEPS} active onSkip={onSkip} />);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onSkip).toHaveBeenCalledWith(0);
  });

  it('honors permanent dismiss via button', () => {
    const onSkip = jest.fn();
    const { rerender } = render(
      <Tour tourId="onboard" steps={STEPS} active onSkip={onSkip} />,
    );
    fireEvent.click(screen.getByRole('button', { name: /não mostrar novamente/i }));
    expect(onSkip).toHaveBeenCalled();
    expect(isTourPermanentlyDismissed('onboard')).toBe(true);
    // Re-mounting with active=true should be suppressed by the flag.
    rerender(<Tour tourId="onboard" steps={STEPS} active />);
    expect(screen.queryByTestId('tour-onboard')).toBeNull();
  });

  it('respects disabled prop', () => {
    render(<Tour tourId="onboard" steps={STEPS} active disabled />);
    expect(screen.queryByTestId('tour-onboard')).toBeNull();
  });

  it('markTourPermanentlyDismissed / isTourPermanentlyDismissed round-trip', () => {
    expect(isTourPermanentlyDismissed('xyz')).toBe(false);
    markTourPermanentlyDismissed('xyz');
    expect(isTourPermanentlyDismissed('xyz')).toBe(true);
  });

  it('fires onStepChange for each transition', () => {
    const onStepChange = jest.fn();
    render(
      <Tour tourId="onboard" steps={STEPS} active onStepChange={onStepChange} />,
    );
    expect(onStepChange).toHaveBeenCalledWith(0, STEPS[0]);
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));
    expect(onStepChange).toHaveBeenCalledWith(1, STEPS[1]);
  });

  it('ArrowRight / ArrowLeft navigate steps', () => {
    render(<Tour tourId="onboard" steps={STEPS} active />);
    fireEvent.keyDown(window, { key: 'ArrowRight' });
    expect(screen.getByText('Próximos passos')).toBeInTheDocument();
    fireEvent.keyDown(window, { key: 'ArrowLeft' });
    expect(screen.getByText('Bem-vindo')).toBeInTheDocument();
  });
});
