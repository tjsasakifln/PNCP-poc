/**
 * UserMenu Component Tests
 *
 * Tests logged in/out states, menu items, sign out functionality
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserMenu } from '@/app/components/UserMenu';

// Mock useAuth hook
const mockSignOut = jest.fn();
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockLink({ children, href, onClick }: { children: React.ReactNode; href: string; onClick?: () => void }) {
    return <a href={href} onClick={onClick}>{children}</a>;
  };
});

describe('UserMenu Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading state', () => {
    it('should render nothing when loading', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        session: null,
        loading: true,
        signOut: mockSignOut,
      });

      const { container } = render(<UserMenu />);
      expect(container).toBeEmptyDOMElement();
    });
  });

  describe('Logged out state', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: null,
        session: null,
        loading: false,
        signOut: mockSignOut,
      });
    });

    it('should show login link when not authenticated', () => {
      render(<UserMenu />);

      const loginLink = screen.getByRole('link', { name: /Entrar/i });
      expect(loginLink).toBeInTheDocument();
      expect(loginLink).toHaveAttribute('href', '/login');
    });

    it('should show signup link when not authenticated', () => {
      render(<UserMenu />);

      const signupLink = screen.getByRole('link', { name: /Criar conta/i });
      expect(signupLink).toBeInTheDocument();
      expect(signupLink).toHaveAttribute('href', '/signup');
    });
  });

  describe('Logged in state', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { email: 'test@example.com', id: '123' },
        session: { access_token: 'token123' },
        loading: false,
        signOut: mockSignOut,
        isAdmin: false,
      });
    });

    it('should show user initial button when authenticated', () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('T'); // First letter of email
      expect(button).toHaveAttribute('title', 'test@example.com');
    });

    it('should show dropdown when clicking user button', async () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
      });
    });

    it('should show all menu items in dropdown for regular user', async () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Minha conta/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Histórico/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Planos/i })).toBeInTheDocument();
        // Admin link should NOT be shown for non-admin users
        expect(screen.queryByRole('link', { name: /Admin/i })).not.toBeInTheDocument();
      });
    });

    it('should show Admin link for admin users', async () => {
      mockUseAuth.mockReturnValue({
        user: { email: 'admin@example.com', id: '123' },
        session: { access_token: 'token123' },
        loading: false,
        signOut: mockSignOut,
        isAdmin: true,
      });

      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Admin/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Admin/i })).toHaveAttribute('href', '/admin');
      });
    });

    it('should have correct hrefs for menu items', async () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Minha conta/i })).toHaveAttribute('href', '/conta');
        expect(screen.getByRole('link', { name: /Histórico/i })).toHaveAttribute('href', '/historico');
        expect(screen.getByRole('link', { name: /Planos/i })).toHaveAttribute('href', '/planos');
      });
    });

    it('should show sign out button in dropdown', async () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        const signOutButton = screen.getByRole('button', { name: /Sair/i });
        expect(signOutButton).toBeInTheDocument();
      });
    });

    it('should call signOut when clicking sign out button', async () => {
      render(<UserMenu />);

      const userButton = screen.getByRole('button');
      fireEvent.click(userButton);

      await waitFor(() => {
        const signOutButton = screen.getByRole('button', { name: /Sair/i });
        fireEvent.click(signOutButton);
      });

      expect(mockSignOut).toHaveBeenCalled();
    });

    it('should close dropdown when clicking sign out', async () => {
      render(<UserMenu />);

      const userButton = screen.getByRole('button');
      fireEvent.click(userButton);

      await waitFor(() => {
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
      });

      const signOutButton = screen.getByRole('button', { name: /Sair/i });
      fireEvent.click(signOutButton);

      await waitFor(() => {
        expect(screen.queryByText('Minha conta')).not.toBeInTheDocument();
      });
    });

    it('should toggle dropdown on multiple clicks', async () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');

      // First click - open
      fireEvent.click(button);
      await waitFor(() => {
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
      });

      // Second click - close
      fireEvent.click(button);
      await waitFor(() => {
        expect(screen.queryByText('Minha conta')).not.toBeInTheDocument();
      });
    });

    it('should close dropdown when clicking outside', async () => {
      render(
        <div>
          <UserMenu />
          <div data-testid="outside">Outside</div>
        </div>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
      });

      // Click outside
      const outside = screen.getByTestId('outside');
      fireEvent.mouseDown(outside);

      await waitFor(() => {
        expect(screen.queryByText('Minha conta')).not.toBeInTheDocument();
      });
    });

    it('should close dropdown when clicking menu link', async () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('Minha conta')).toBeInTheDocument();
      });

      // Click the link - onClick={() => setOpen(false)} should close dropdown
      const contaLink = screen.getByRole('link', { name: /Minha conta/i });
      fireEvent.click(contaLink);

      await waitFor(() => {
        expect(screen.queryByText('Histórico')).not.toBeInTheDocument();
      });
    });
  });

  describe('Edge cases', () => {
    it('should handle user with no email gracefully', () => {
      mockUseAuth.mockReturnValue({
        user: { id: '123' }, // No email
        session: { access_token: 'token123' },
        loading: false,
        signOut: mockSignOut,
      });

      render(<UserMenu />);

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('U'); // Default initial
    });

    it('should uppercase the first letter of email', () => {
      mockUseAuth.mockReturnValue({
        user: { email: 'lowercase@example.com', id: '123' },
        session: { access_token: 'token123' },
        loading: false,
        signOut: mockSignOut,
      });

      render(<UserMenu />);

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('L');
    });
  });
});
