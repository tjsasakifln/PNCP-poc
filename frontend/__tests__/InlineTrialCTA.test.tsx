/**
 * Tests for InlineTrialCTA component (#652).
 *
 * Inline (NOT sticky) CTA that lives on programmatic SEO pages
 * (/cnpj/[cnpj], /orgaos/[slug]) to capture trial signups.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import InlineTrialCTA from '../app/components/InlineTrialCTA';

describe('InlineTrialCTA', () => {
  const originalMixpanel = (window as unknown as { mixpanel?: unknown }).mixpanel;

  afterEach(() => {
    (window as unknown as { mixpanel?: unknown }).mixpanel = originalMixpanel;
  });

  it('renders CONFENGE diagnostic copy, not a SaaS trial', () => {
    render(<InlineTrialCTA page="cnpj" source="cnpj-page" />);
    expect(
      screen.getByText('Monitore contratos deste órgão — diagnóstico CONFENGE'),
    ).toBeInTheDocument();
    expect(screen.queryByText(/teste grátis|trial grátis|14 dias/i)).not.toBeInTheDocument();
  });

  it('builds /consultoria-b2g link with source=cnpj-page and orgao=<cnpj>', () => {
    render(
      <InlineTrialCTA
        page="cnpj"
        source="cnpj-page"
        extraParam={{ name: 'orgao', value: '01914765000108' }}
      />,
    );
    const link = screen.getByRole('link', { name: /diagnóstico à CONFENGE/i });
    expect(link).toHaveAttribute(
      'href',
      '/consultoria-b2g?source=cnpj-page&orgao=01914765000108',
    );
  });

  it('builds /consultoria-b2g link with source=orgao-page and slug=<slug>', () => {
    render(
      <InlineTrialCTA
        page="orgao"
        source="orgao-page"
        extraParam={{ name: 'slug', value: 'prefeitura-de-floripa' }}
      />,
    );
    const link = screen.getByRole('link', { name: /diagnóstico à CONFENGE/i });
    expect(link).toHaveAttribute(
      'href',
      '/consultoria-b2g?source=orgao-page&slug=prefeitura-de-floripa',
    );
  });

  it('omits extra param when not provided', () => {
    render(<InlineTrialCTA page="cnpj" source="cnpj-page" />);
    const link = screen.getByRole('link', { name: /diagnóstico à CONFENGE/i });
    expect(link).toHaveAttribute('href', '/consultoria-b2g?source=cnpj-page');
  });

  it('fires Mixpanel cta_click with page+position on click (cnpj)', () => {
    const trackSpy = jest.fn();
    (window as unknown as { mixpanel: { track: jest.Mock } }).mixpanel = {
      track: trackSpy,
    };

    render(
      <InlineTrialCTA
        page="cnpj"
        source="cnpj-page"
        extraParam={{ name: 'orgao', value: '01914765000108' }}
      />,
    );

    fireEvent.click(screen.getByRole('link', { name: /diagnóstico à CONFENGE/i }));

    expect(trackSpy).toHaveBeenCalledWith('cta_click', {
      page: 'cnpj',
      position: 'inline',
    });
  });

  it('fires Mixpanel cta_click with page+position on click (orgao)', () => {
    const trackSpy = jest.fn();
    (window as unknown as { mixpanel: { track: jest.Mock } }).mixpanel = {
      track: trackSpy,
    };

    render(
      <InlineTrialCTA
        page="orgao"
        source="orgao-page"
        extraParam={{ name: 'slug', value: 'foo' }}
      />,
    );

    fireEvent.click(screen.getByRole('link', { name: /diagnóstico à CONFENGE/i }));

    expect(trackSpy).toHaveBeenCalledWith('cta_click', {
      page: 'orgao',
      position: 'inline',
    });
  });

  it('does not throw when window.mixpanel is undefined', () => {
    delete (window as unknown as { mixpanel?: unknown }).mixpanel;
    render(<InlineTrialCTA page="cnpj" source="cnpj-page" />);
    expect(() =>
      fireEvent.click(screen.getByRole('link', { name: /diagnóstico à CONFENGE/i })),
    ).not.toThrow();
  });
});
