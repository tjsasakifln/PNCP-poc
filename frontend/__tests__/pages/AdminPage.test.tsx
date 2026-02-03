/**
 * AdminPage Component Tests
 *
 * Tests user CRUD, plan assignment, authentication, authorization
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import AdminPage from '@/app/admin/page';

// Mock useAuth hook
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock window.confirm and window.alert
const mockConfirm = jest.fn();
const mockAlert = jest.fn();
window.confirm = mockConfirm;
window.alert = mockAlert;

describe('AdminPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockConfirm.mockReturnValue(true);
  });

  describe('Authentication states', () => {
    it('should show loading message during auth check', () => {
      mockUseAuth.mockReturnValue({
        session: null,
        loading: true,
      });

      render(<AdminPage />);

      expect(screen.getByText('Carregando...')).toBeInTheDocument();
    });

    it('should show login required when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        session: null,
        loading: false,
      });

      render(<AdminPage />);

      expect(screen.getByRole('link', { name: /Login necessario/i })).toBeInTheDocument();
    });
  });

  describe('Authenticated state (admin)', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should fetch users on mount', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 0 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/admin/users'),
          expect.objectContaining({
            headers: { Authorization: 'Bearer admin-token-123' },
          })
        );
      });
    });

    it('should show page title', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 0 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Admin - Usuarios/i })).toBeInTheDocument();
      });
    });

    it('should show user count', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 5 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText(/5 usuarios/)).toBeInTheDocument();
      });
    });

    it('should use singular form for 1 user', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 1 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText(/1 usuario$/)).toBeInTheDocument();
      });
    });

    it('should show back and new user buttons', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 0 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Voltar/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Novo usuario/i })).toBeInTheDocument();
      });
    });
  });

  describe('Non-admin access', () => {
    it('should show access restricted page for non-admin users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'regular-user-token' },
        loading: false,
        isAdmin: false,
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText(/Acesso Restrito/i)).toBeInTheDocument();
        expect(screen.getByText(/Esta pagina e exclusiva para administradores/i)).toBeInTheDocument();
      });
    });

    it('should show link to go back home', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'regular-user-token' },
        loading: false,
        isAdmin: false,
      });

      render(<AdminPage />);

      await waitFor(() => {
        const backLink = screen.getByRole('link', { name: /Voltar para inicio/i });
        expect(backLink).toBeInTheDocument();
        expect(backLink).toHaveAttribute('href', '/');
      });
    });
  });

  describe('API 403 error handling', () => {
    it('should show error when API returns 403', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'admin-token-123' },
        loading: false,
        isAdmin: true,
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText(/Acesso negado/i)).toBeInTheDocument();
        expect(screen.getByText(/Voce nao e administrador/i)).toBeInTheDocument();
      });
    });
  });

  describe('User list', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    const mockUsers = [
      {
        id: '1',
        email: 'user1@example.com',
        full_name: 'John Doe',
        company: 'Acme Inc',
        plan_type: 'monthly',
        created_at: '2024-01-15T10:00:00Z',
        user_subscriptions: [
          { id: 's1', plan_id: 'monthly', credits_remaining: null, expires_at: null, is_active: true },
        ],
      },
      {
        id: '2',
        email: 'user2@example.com',
        full_name: null,
        company: null,
        plan_type: 'free',
        created_at: '2024-01-20T10:00:00Z',
        user_subscriptions: [
          { id: 's2', plan_id: 'free', credits_remaining: 3, expires_at: null, is_active: true },
        ],
      },
    ];

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should display users in table', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: mockUsers, total: 2 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText('user1@example.com')).toBeInTheDocument();
        expect(screen.getByText('user2@example.com')).toBeInTheDocument();
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Acme Inc')).toBeInTheDocument();
      });
    });

    it('should show dash for missing name/company', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: mockUsers, total: 2 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        // User 2 has no name or company
        const dashes = screen.getAllByText('-');
        expect(dashes.length).toBeGreaterThan(0);
      });
    });

    it('should show credits for pack plans', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: mockUsers, total: 2 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument(); // Free plan has 3 credits
      });
    });

    it('should show table headers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 0 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText('Email')).toBeInTheDocument();
        expect(screen.getByText('Nome')).toBeInTheDocument();
        expect(screen.getByText('Empresa')).toBeInTheDocument();
        expect(screen.getByText('Plano')).toBeInTheDocument();
        expect(screen.getByText('Creditos')).toBeInTheDocument();
        expect(screen.getByText('Criado')).toBeInTheDocument();
        expect(screen.getByText('Acoes')).toBeInTheDocument();
      });
    });

    it('should show loading skeletons while fetching', async () => {
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        }), 100))
      );

      render(<AdminPage />);

      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Search functionality', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should have search input', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 0 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Buscar por email/i)).toBeInTheDocument();
      });
    });

    it('should trigger search on Enter key', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Buscar por email/i)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Buscar por email/i);
      await act(async () => {
        fireEvent.change(searchInput, { target: { value: 'test' } });
        fireEvent.keyDown(searchInput, { key: 'Enter' });
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('search=test'),
          expect.anything()
        );
      });
    });
  });

  describe('Create user form', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should toggle create user form', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 0 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Novo usuario/i })).toBeInTheDocument();
      });

      // Click to show form
      const newButton = screen.getByRole('button', { name: /Novo usuario/i });
      await act(async () => {
        fireEvent.click(newButton);
      });

      expect(screen.getByText('Criar usuario')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Cancelar/i })).toBeInTheDocument();
    });

    it('should show form fields', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 0 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Novo usuario/i })).toBeInTheDocument();
      });

      const newButton = screen.getByRole('button', { name: /Novo usuario/i });
      await act(async () => {
        fireEvent.click(newButton);
      });

      expect(screen.getByText('Email *')).toBeInTheDocument();
      expect(screen.getByText('Senha *')).toBeInTheDocument();
      // Nome, Empresa, and Plano appear both in table headers and form labels
      // So we verify they appear at least twice (once in header, once in form)
      expect(screen.getAllByText('Nome').length).toBeGreaterThanOrEqual(2);
      expect(screen.getAllByText('Empresa').length).toBeGreaterThanOrEqual(2);
      expect(screen.getAllByText('Plano').length).toBeGreaterThanOrEqual(2);
    });

    it('should submit create user form', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ id: 'new-user-123' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Novo usuario/i })).toBeInTheDocument();
      });

      // Open form
      const newButton = screen.getByRole('button', { name: /Novo usuario/i });
      await act(async () => {
        fireEvent.click(newButton);
      });

      // Fill form
      const emailInput = screen.getAllByRole('textbox')[0]; // First input in form
      const passwordInputs = document.querySelectorAll('input[type="password"]');

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'new@example.com' } });
        fireEvent.change(passwordInputs[0], { target: { value: 'password123' } });
      });

      // Submit
      const createButton = screen.getByRole('button', { name: /^Criar$/i });
      await act(async () => {
        fireEvent.click(createButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/admin/users'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('new@example.com'),
          })
        );
      });
    });

    it('should show loading state during creation', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        })
        .mockImplementationOnce(
          () => new Promise((resolve) => setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve({ id: 'new-user-123' }),
          }), 100))
        );

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Novo usuario/i })).toBeInTheDocument();
      });

      const newButton = screen.getByRole('button', { name: /Novo usuario/i });
      await act(async () => {
        fireEvent.click(newButton);
      });

      const emailInput = screen.getAllByRole('textbox')[0];
      const passwordInputs = document.querySelectorAll('input[type="password"]');

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'new@example.com' } });
        fireEvent.change(passwordInputs[0], { target: { value: 'password123' } });
      });

      const createButton = screen.getByRole('button', { name: /^Criar$/i });
      await act(async () => {
        fireEvent.click(createButton);
      });

      expect(screen.getByRole('button', { name: /Criando.../i })).toBeInTheDocument();
    });
  });

  describe('Delete user', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    const mockUsers = [
      {
        id: '1',
        email: 'user@example.com',
        full_name: 'Test User',
        company: null,
        plan_type: 'free',
        created_at: '2024-01-15T10:00:00Z',
        user_subscriptions: [],
      },
    ];

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should show delete button for each user', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: mockUsers, total: 1 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Excluir/i })).toBeInTheDocument();
      });
    });

    it('should show confirmation before deleting', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: mockUsers, total: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Excluir/i })).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /Excluir/i });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      expect(mockConfirm).toHaveBeenCalledWith(expect.stringContaining('user@example.com'));
    });

    it('should call delete API when confirmed', async () => {
      mockConfirm.mockReturnValue(true);

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: mockUsers, total: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: [], total: 0 }),
        });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Excluir/i })).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /Excluir/i });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/admin/users/1'),
          expect.objectContaining({
            method: 'DELETE',
          })
        );
      });
    });

    it('should not delete when cancelled', async () => {
      mockConfirm.mockReturnValue(false);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: mockUsers, total: 1 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Excluir/i })).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /Excluir/i });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      // Only the initial fetch should have been made
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Plan assignment', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    const mockUsers = [
      {
        id: '1',
        email: 'user@example.com',
        full_name: 'Test User',
        company: null,
        plan_type: 'free',
        created_at: '2024-01-15T10:00:00Z',
        user_subscriptions: [
          { id: 's1', plan_id: 'free', credits_remaining: 3, expires_at: null, is_active: true },
        ],
      },
    ];

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should show plan selector for each user', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: mockUsers, total: 1 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        const selects = screen.getAllByRole('combobox');
        expect(selects.length).toBeGreaterThan(0);
      });
    });

    it('should call assign plan API when plan changed', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: mockUsers, total: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ users: mockUsers, total: 1 }),
        });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText('user@example.com')).toBeInTheDocument();
      });

      // Find the plan selector in the user row
      const selects = screen.getAllByRole('combobox');
      const planSelect = selects.find(s => s.classList.contains('text-xs'));

      await act(async () => {
        fireEvent.change(planSelect!, { target: { value: 'monthly' } });
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/admin/users/1/assign-plan?plan_id=monthly'),
          expect.objectContaining({
            method: 'POST',
          })
        );
      });
    });
  });

  describe('Pagination', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should show pagination when multiple pages', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 100 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Anterior/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Proximo/i })).toBeInTheDocument();
      });
    });

    it('should not show pagination for single page', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ users: [], total: 10 }),
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /Anterior/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Proximo/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Error handling', () => {
    const mockSession = {
      access_token: 'admin-token-123',
    };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
        isAdmin: true,
      });
    });

    it('should show error message on fetch failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText(/Erro ao carregar usuarios/i)).toBeInTheDocument();
      });
    });

    it('should show error on network failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<AdminPage />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });
});
