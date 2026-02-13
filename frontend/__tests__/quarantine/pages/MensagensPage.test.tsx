/**
 * MensagensPage Component Tests
 *
 * Tests messaging interface, conversation list, thread view, new messages, replies
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import MensagensPage from '@/app/mensagens/page';

// Mock useAuth
const mockUser = { id: 'user-1', email: 'test@test.com' };
const mockSession = { access_token: 'mock-token' };

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    user: mockUser,
    session: mockSession,
    loading: false,
    isAdmin: false,
  }),
}));

// Mock Next.js navigation
const mockPush = jest.fn();
const mockRouter = { push: mockPush, replace: jest.fn(), back: jest.fn(), refresh: jest.fn() };

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => '/mensagens',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock fetch
global.fetch = jest.fn();

const mockConversations = [
  {
    id: 'conv-1',
    subject: 'Dúvida sobre pagamento',
    category: 'suporte',
    status: 'aberto',
    last_message_at: '2026-02-10T10:00:00Z',
    unread_count: 2,
    user_email: 'test@test.com',
  },
  {
    id: 'conv-2',
    subject: 'Sugestão de funcionalidade',
    category: 'sugestao',
    status: 'respondido',
    last_message_at: '2026-02-09T15:30:00Z',
    unread_count: 0,
    user_email: 'test@test.com',
  },
];

const mockConversationDetail = {
  id: 'conv-1',
  subject: 'Dúvida sobre pagamento',
  category: 'suporte',
  status: 'aberto',
  created_at: '2026-02-10T09:00:00Z',
  user_email: 'test@test.com',
  messages: [
    {
      id: 'msg-1',
      body: 'Oi, tenho uma dúvida sobre o pagamento.',
      sender_email: 'test@test.com',
      is_admin_reply: false,
      created_at: '2026-02-10T09:00:00Z',
    },
    {
      id: 'msg-2',
      body: 'Olá! Como posso ajudar?',
      sender_email: 'admin@smartlic.tech',
      is_admin_reply: true,
      created_at: '2026-02-10T10:00:00Z',
    },
  ],
};

beforeEach(() => {
  jest.clearAllMocks();
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({ conversations: mockConversations }),
  });
});

describe('MensagensPage', () => {
  describe('Initial render', () => {
    it('should render page header with title', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByText('Mensagens')).toBeInTheDocument();
      });
    });

    it('should render new message button', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Nova mensagem/i })).toBeInTheDocument();
      });
    });

    it('should render status filter tabs', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Todos/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Aberto/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Respondido/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Resolvido/i })).toBeInTheDocument();
      });
    });
  });

  describe('Conversation list', () => {
    it('should fetch and display conversations', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByText('Dúvida sobre pagamento')).toBeInTheDocument();
        expect(screen.getByText('Sugestão de funcionalidade')).toBeInTheDocument();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/messages/conversations',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer mock-token',
          }),
        })
      );
    });

    it('should show loading state while fetching', () => {
      render(<MensagensPage />);

      // Should show spinner during initial load
      const spinners = document.querySelectorAll('.animate-spin');
      expect(spinners.length).toBeGreaterThan(0);
    });

    it('should show empty state when no conversations', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ conversations: [] }),
      });

      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByText(/Nenhuma mensagem ainda/i)).toBeInTheDocument();
      });
    });

    it('should show error message on fetch failure', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByText(/Erro ao carregar conversas/i)).toBeInTheDocument();
      });
    });

    it('should display unread indicator', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        const unreadIndicators = document.querySelectorAll('.bg-\\[var\\(--brand-blue\\)\\].rounded-full');
        expect(unreadIndicators.length).toBeGreaterThan(0);
      });
    });
  });

  describe('New conversation form', () => {
    it('should toggle new message form when button clicked', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Nova mensagem/i })).toBeInTheDocument();
      });

      const newButton = screen.getByRole('button', { name: /Nova mensagem/i });
      fireEvent.click(newButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Assunto/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Sua mensagem/i)).toBeInTheDocument();
      });
    });

    it('should show cancel button when form is open', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /Nova mensagem/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Cancelar/i })).toBeInTheDocument();
      });
    });

    it('should have category selector', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /Nova mensagem/i }));
      });

      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toBeInTheDocument();
      });
    });

    it('should submit new conversation', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => ({ conversations: mockConversations }) })
        .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'new-conv' }) })
        .mockResolvedValueOnce({ ok: true, json: async () => ({ conversations: mockConversations }) })
        .mockResolvedValueOnce({ ok: true, json: async () => mockConversationDetail });

      render(<MensagensPage />);

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /Nova mensagem/i }));
      });

      await waitFor(() => {
        fireEvent.change(screen.getByPlaceholderText(/Assunto/i), {
          target: { value: 'Novo assunto' },
        });
        fireEvent.change(screen.getByPlaceholderText(/Sua mensagem/i), {
          target: { value: 'Mensagem de teste' },
        });
      });

      const submitButton = screen.getByRole('button', { name: /Enviar/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/messages/conversations',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Novo assunto'),
          })
        );
      });
    });
  });

  describe('Thread view', () => {
    it('should load thread when conversation clicked', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => ({ conversations: mockConversations }) })
        .mockResolvedValueOnce({ ok: true, json: async () => mockConversationDetail });

      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByText('Dúvida sobre pagamento')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Dúvida sobre pagamento'));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/messages/conversations/conv-1',
          expect.any(Object)
        );
      });
    });

    it('should display messages in thread', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => ({ conversations: mockConversations }) })
        .mockResolvedValueOnce({ ok: true, json: async () => mockConversationDetail });

      render(<MensagensPage />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Dúvida sobre pagamento'));
      });

      await waitFor(() => {
        expect(screen.getByText('Oi, tenho uma dúvida sobre o pagamento.')).toBeInTheDocument();
        expect(screen.getByText('Olá! Como posso ajudar?')).toBeInTheDocument();
      });
    });

    it('should show reply form when status is not resolvido', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => ({ conversations: mockConversations }) })
        .mockResolvedValueOnce({ ok: true, json: async () => mockConversationDetail });

      render(<MensagensPage />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Dúvida sobre pagamento'));
      });

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Escreva sua resposta/i)).toBeInTheDocument();
      });
    });
  });

  describe('Authentication redirect', () => {
    it('should redirect to login if not authenticated', async () => {
      jest.spyOn(require('../../app/components/AuthProvider'), 'useAuth').mockReturnValue({
        user: null,
        session: null,
        loading: false,
        isAdmin: false,
      });

      render(<MensagensPage />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });
  });

  describe('Status filter', () => {
    it('should filter conversations by status', async () => {
      render(<MensagensPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Aberto/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Aberto/i }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/messages/conversations?status=aberto',
          expect.any(Object)
        );
      });
    });
  });
});
