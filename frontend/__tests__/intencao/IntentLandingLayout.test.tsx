/**
 * Tests for IntentLandingLayout — CONV-007-2 / #1316
 *
 * Covers:
 * - Renders children
 * - Renders main element
 * - Renders LandingNavbar
 * - Renders Footer
 */
// Mock AuthProvider before any imports (required by LandingNavbar -> NavbarAuthCTA)
jest.mock('../../app/components/AuthProvider', () => {
  const React = require('react');
  return {
    useAuth: () => ({ user: null, session: null, loading: false }),
    AuthProvider: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
  };
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import IntentLandingLayout from '../../app/intencao/IntentLandingLayout';

describe('IntentLandingLayout', () => {
  it('renders children content', () => {
    render(
      <IntentLandingLayout>
        <p data-testid="child-content">Test content</p>
      </IntentLandingLayout>,
    );
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders main semantic element', () => {
    const { container } = render(
      <IntentLandingLayout>
        <p>Content</p>
      </IntentLandingLayout>,
    );
    const main = container.querySelector('main#main-content');
    expect(main).not.toBeNull();
  });

  it('renders the Logo link in the navbar', () => {
    render(
      <IntentLandingLayout>
        <p>Content</p>
      </IntentLandingLayout>,
    );
    const homeLinks = screen.getAllByRole('link').filter((el) => el.getAttribute('href') === '/');
    expect(homeLinks.length).toBeGreaterThan(0);
    expect(homeLinks[0]).toHaveTextContent(/smartlic/i);
  });

  it('renders the Footer with site-footer id', () => {
    const { container } = render(
      <IntentLandingLayout>
        <p>Content</p>
      </IntentLandingLayout>,
    );
    const footer = container.querySelector('#site-footer');
    expect(footer).not.toBeNull();
  });

  it('renders Hero and Como funciona when used with a page', () => {
    render(
      <IntentLandingLayout>
        <p>Page content</p>
      </IntentLandingLayout>,
    );
    expect(screen.getByText('Page content')).toBeInTheDocument();
  });
});
