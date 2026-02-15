/**
 * STORY-253: SessionExpiredBanner component tests
 */

import { render, screen } from '@testing-library/react';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: () => '/buscar',
}));

// Mock useAuth — the import path must match what SessionExpiredBanner uses
// SessionExpiredBanner imports from './AuthProvider' (relative), but with @/ alias
// it resolves to app/components/AuthProvider
const mockUseAuth = jest.fn();
jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

import { SessionExpiredBanner } from '../../app/components/SessionExpiredBanner';

describe('SessionExpiredBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not render when sessionExpired is false', () => {
    mockUseAuth.mockReturnValue({
      sessionExpired: false,
      user: { id: '123', email: 'test@example.com' },
    });

    const { container } = render(<SessionExpiredBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('should not render when user is null', () => {
    mockUseAuth.mockReturnValue({
      sessionExpired: true,
      user: null,
    });

    const { container } = render(<SessionExpiredBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('should render when sessionExpired is true and user exists', () => {
    mockUseAuth.mockReturnValue({
      sessionExpired: true,
      user: { id: '123', email: 'test@example.com' },
    });

    render(<SessionExpiredBanner />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/sessao expirou/i)).toBeInTheDocument();
  });

  it('should have login link with redirect param', () => {
    mockUseAuth.mockReturnValue({
      sessionExpired: true,
      user: { id: '123', email: 'test@example.com' },
    });

    render(<SessionExpiredBanner />);

    const loginLink = screen.getByRole('link', { name: /fazer login/i });
    expect(loginLink).toHaveAttribute(
      'href',
      '/login?reason=session_expired&redirect=%2Fbuscar'
    );
  });

  it('should display the warning message', () => {
    mockUseAuth.mockReturnValue({
      sessionExpired: true,
      user: { id: '123', email: 'test@example.com' },
    });

    render(<SessionExpiredBanner />);

    expect(
      screen.getByText('Sua sessao expirou. Faca login novamente para continuar.')
    ).toBeInTheDocument();
  });
});
