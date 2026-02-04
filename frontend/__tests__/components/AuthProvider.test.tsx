/**
 * AuthProvider Component Tests
 *
 * Tests authentication context, session management, login/logout flows
 */

import { render, screen, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/app/components/AuthProvider';

// Mock Supabase client
const mockGetSession = jest.fn();
const mockOnAuthStateChange = jest.fn();
const mockSignInWithPassword = jest.fn();
const mockSignUp = jest.fn();
const mockSignInWithOtp = jest.fn();
const mockSignInWithOAuth = jest.fn();
const mockSignOut = jest.fn();

jest.mock('../../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: () => mockGetSession(),
      onAuthStateChange: (callback: (event: string, session: unknown) => void) => {
        mockOnAuthStateChange(callback);
        return {
          data: {
            subscription: {
              unsubscribe: jest.fn(),
            },
          },
        };
      },
      signInWithPassword: (params: { email: string; password: string }) => mockSignInWithPassword(params),
      signUp: (params: { email: string; password: string; options?: { data?: { full_name?: string } } }) => mockSignUp(params),
      signInWithOtp: (params: { email: string }) => mockSignInWithOtp(params),
      signInWithOAuth: (params: { provider: string; options?: { redirectTo?: string } }) => mockSignInWithOAuth(params),
      signOut: () => mockSignOut(),
    },
  },
}));

// Mock fetch for admin status check
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Test component to access auth context
function TestConsumer() {
  const { user, session, loading, signOut, isAdmin } = useAuth();

  return (
    <div>
      <span data-testid="loading">{loading ? 'true' : 'false'}</span>
      <span data-testid="user">{user ? user.email : 'null'}</span>
      <span data-testid="session">{session ? 'active' : 'null'}</span>
      <span data-testid="isAdmin">{isAdmin ? 'true' : 'false'}</span>
      <button onClick={signOut}>Sign Out</button>
    </div>
  );
}

// Set backend URL before tests run (needed for admin status checks)
process.env.NEXT_PUBLIC_BACKEND_URL = 'http://test-backend:8000';

describe('AuthProvider Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ is_admin: false }),
    });
  });

  it('should provide loading state initially', async () => {
    mockGetSession.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId('loading')).toHaveTextContent('true');
  });

  it('should set loading to false after session check', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });
  });

  it('should provide null user when not authenticated', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('session')).toHaveTextContent('null');
    });
  });

  it('should provide user data when authenticated', async () => {
    const mockSession = {
      user: { email: 'test@example.com', id: '123' },
      access_token: 'token123',
    };

    mockGetSession.mockResolvedValue({ data: { session: mockSession } });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
      expect(screen.getByTestId('session')).toHaveTextContent('active');
    });
  });

  it('should subscribe to auth state changes', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(mockOnAuthStateChange).toHaveBeenCalled();
    });
  });

  it('should update state when auth changes', async () => {
    let authCallback: ((event: string, session: unknown) => void) | null = null;

    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockOnAuthStateChange.mockImplementation((callback) => {
      authCallback = callback;
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('null');
    });

    // Simulate auth state change
    const newSession = {
      user: { email: 'new@example.com', id: '456' },
      access_token: 'new-token',
    };

    await act(async () => {
      if (authCallback) {
        authCallback('SIGNED_IN', newSession);
      }
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('new@example.com');
    });
  });
});

describe('Admin status', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should set isAdmin to false when not authenticated', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('isAdmin')).toHaveTextContent('false');
    });
  });

  it('should fetch admin status when authenticated', async () => {
    const mockSession = {
      user: { email: 'test@example.com', id: '123' },
      access_token: 'token123',
    };

    mockGetSession.mockResolvedValue({ data: { session: mockSession } });
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ is_admin: true }),
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/me'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer token123' },
        })
      );
    });
  });

  it('should set isAdmin to true when backend returns is_admin true', async () => {
    const mockSession = {
      user: { email: 'admin@example.com', id: '123' },
      access_token: 'admin-token',
    };

    mockGetSession.mockResolvedValue({ data: { session: mockSession } });
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ is_admin: true }),
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('isAdmin')).toHaveTextContent('true');
    });
  });

  it('should set isAdmin to false when backend returns error', async () => {
    const mockSession = {
      user: { email: 'test@example.com', id: '123' },
      access_token: 'token123',
    };

    mockGetSession.mockResolvedValue({ data: { session: mockSession } });
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('isAdmin')).toHaveTextContent('false');
    });
  });
});

describe('useAuth hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetSession.mockResolvedValue({ data: { session: null } });
  });

  it('should throw error when used outside provider', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestConsumer />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleError.mockRestore();
  });
});

describe('Auth methods', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ is_admin: false }),
    });
  });

  it('signInWithEmail should call supabase with correct params', async () => {
    mockSignInWithPassword.mockResolvedValue({ error: null });

    function TestSignIn() {
      const { signInWithEmail } = useAuth();
      return (
        <button onClick={() => signInWithEmail('test@example.com', 'password123')}>
          Sign In
        </button>
      );
    }

    render(
      <AuthProvider>
        <TestSignIn />
      </AuthProvider>
    );

    await waitFor(() => {});

    const button = screen.getByRole('button', { name: /Sign In/i });
    await act(async () => {
      button.click();
    });

    expect(mockSignInWithPassword).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('signInWithEmail should throw on error', async () => {
    const mockError = new Error('Invalid credentials');
    mockSignInWithPassword.mockResolvedValue({ error: mockError });

    let caughtError: Error | null = null;

    function TestSignIn() {
      const { signInWithEmail } = useAuth();
      const handleClick = async () => {
        try {
          await signInWithEmail('test@example.com', 'wrong');
        } catch (err) {
          caughtError = err as Error;
        }
      };
      return <button onClick={handleClick}>Sign In</button>;
    }

    render(
      <AuthProvider>
        <TestSignIn />
      </AuthProvider>
    );

    await waitFor(() => {});

    const button = screen.getByRole('button', { name: /Sign In/i });
    await act(async () => {
      button.click();
    });

    expect(caughtError).toBe(mockError);
  });

  it('signUpWithEmail should call supabase with correct params', async () => {
    mockSignUp.mockResolvedValue({ error: null });

    function TestSignUp() {
      const { signUpWithEmail } = useAuth();
      return (
        <button onClick={() => signUpWithEmail('new@example.com', 'password123', 'John Doe')}>
          Sign Up
        </button>
      );
    }

    render(
      <AuthProvider>
        <TestSignUp />
      </AuthProvider>
    );

    await waitFor(() => {});

    const button = screen.getByRole('button', { name: /Sign Up/i });
    await act(async () => {
      button.click();
    });

    expect(mockSignUp).toHaveBeenCalledWith({
      email: 'new@example.com',
      password: 'password123',
      options: { data: { full_name: 'John Doe' } },
    });
  });

  it('signInWithMagicLink should call supabase with correct params', async () => {
    mockSignInWithOtp.mockResolvedValue({ error: null });

    function TestMagicLink() {
      const { signInWithMagicLink } = useAuth();
      return (
        <button onClick={() => signInWithMagicLink('magic@example.com')}>
          Send Link
        </button>
      );
    }

    render(
      <AuthProvider>
        <TestMagicLink />
      </AuthProvider>
    );

    await waitFor(() => {});

    const button = screen.getByRole('button', { name: /Send Link/i });
    await act(async () => {
      button.click();
    });

    expect(mockSignInWithOtp).toHaveBeenCalledWith({
      email: 'magic@example.com',
    });
  });

  it('signInWithGoogle should call supabase OAuth', async () => {
    mockSignInWithOAuth.mockResolvedValue({ error: null });

    // Mock window.location.origin
    Object.defineProperty(window, 'location', {
      value: { origin: 'http://localhost:3000', href: '' },
      writable: true,
    });

    function TestGoogle() {
      const { signInWithGoogle } = useAuth();
      return <button onClick={() => signInWithGoogle()}>Google</button>;
    }

    render(
      <AuthProvider>
        <TestGoogle />
      </AuthProvider>
    );

    await waitFor(() => {});

    const button = screen.getByRole('button', { name: /Google/i });
    await act(async () => {
      button.click();
    });

    expect(mockSignInWithOAuth).toHaveBeenCalledWith({
      provider: 'google',
      options: { redirectTo: 'http://localhost:3000/auth/callback' },
    });
  });

  it('signOut should call supabase signOut', async () => {
    mockSignOut.mockResolvedValue({ error: null });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {});

    const button = screen.getByRole('button', { name: /Sign Out/i });
    await act(async () => {
      button.click();
    });

    expect(mockSignOut).toHaveBeenCalled();
  });
});
