/**
 * Tests for StickyTrialCTA component (#626)
 * Mobile sticky trial CTA — visible after >600px scroll, hidden on desktop via sm:hidden.
 */

import React from 'react';
import { act, render, screen } from '@testing-library/react';
import StickyTrialCTA from '../app/components/StickyTrialCTA';

describe('StickyTrialCTA', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'scrollY', { value: 0, writable: true, configurable: true });
  });

  it('renders nothing when scrollY <= 600', () => {
    render(<StickyTrialCTA refParam="sticky-test" />);
    expect(screen.queryByText(/Pedir diagnóstico à CONFENGE/)).toBeNull();
  });

  it('renders the CTA link after scrolling beyond 600px', () => {
    render(<StickyTrialCTA refParam="sticky-test" />);

    act(() => {
      Object.defineProperty(window, 'scrollY', { value: 700, writable: true, configurable: true });
      window.dispatchEvent(new Event('scroll'));
    });

    const link = screen.getByRole('link', { name: /Pedir diagnóstico à CONFENGE/ });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/consultoria-b2g?ref=sticky-test');
    expect(link.getAttribute('href')).not.toContain('/signup');
  });

  it('uses sm:hidden so the bar is mobile-only', () => {
    const { container } = render(<StickyTrialCTA refParam="sticky-test" />);

    act(() => {
      Object.defineProperty(window, 'scrollY', { value: 700, writable: true, configurable: true });
      window.dispatchEvent(new Event('scroll'));
    });

    const bar = container.querySelector('.fixed');
    expect(bar).not.toBeNull();
    expect(bar?.className).toContain('sm:hidden');
  });

  it('honors a custom label prop', () => {
    render(<StickyTrialCTA refParam="sticky-test" label="Começar grátis" />);

    act(() => {
      Object.defineProperty(window, 'scrollY', { value: 700, writable: true, configurable: true });
      window.dispatchEvent(new Event('scroll'));
    });

    expect(screen.getByRole('link', { name: /Começar grátis/ })).toBeInTheDocument();
  });
});
