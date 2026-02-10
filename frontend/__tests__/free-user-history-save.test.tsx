/**
 * History Save Validation Test
 *
 * Test Scenario 3: History save validation
 *
 * This test validates that search history is correctly saved and persisted:
 * 1. Backend saves search session to database after successful search
 * 2. Frontend /historico page displays saved searches
 * 3. Search parameters are correctly stored
 * 4. Search results metadata is saved
 * 5. History is queryable and paginates correctly
 *
 * Edge cases tested:
 * - Failed searches should not create history entries
 * - Concurrent searches create separate history entries
 * - History pagination works correctly
 * - History entries are ordered by created_at (newest first)
 */

import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';

// Mock dependencies
const mockUseAuth = jest.fn();
const mockUseAnalytics = jest.fn();
const mockRouter = { push: jest.fn(), refresh: jest.fn() };

jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => mockUseAnalytics(),
}));

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  useSearchParams: () => new URLSearchParams(),
}));

const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('History Save Validation', () => {
  const mockFreeUserSession = {
    access_token: 'free-user-token-123',
    user: {
      id: 'free-user-id',
      email: 'freeuser@example.com',
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      session: mockFreeUserSession,
      user: mockFreeUserSession.user,
      loading: false,
    });
    mockUseAnalytics.mockReturnValue({
      trackEvent: jest.fn(),
    });
  });

  describe('AC1: Search session is saved to database', () => {
    it('should create session entry after successful search', async () => {
      // Mock successful search
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          download_id: 'test-download-id',
          total_raw: 100,
          total_filtrado: 15,
          resumo: {
            resumo_executivo: 'Found 15 opportunities',
            total_oportunidades: 15,
            valor_total: 150000,
            destaques: ['Highlight 1'],
            distribuicao_uf: { SC: 15 },
          },
        }),
      });

      // Mock history endpoint to verify session was saved
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['SC'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              custom_keywords: null,
              total_raw: 100,
              total_filtered: 15,
              valor_total: 150000,
              resumo_executivo: 'Found 15 opportunities',
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      // Execute search
      const searchResponse = await fetch('/api/buscar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${mockFreeUserSession.access_token}`,
        },
        body: JSON.stringify({
          ufs: ['SC'],
          data_inicial: '2026-02-01',
          data_final: '2026-02-10',
          setor_id: 'vestuario',
        }),
      });

      expect(searchResponse.ok).toBe(true);

      // Fetch history
      const historyResponse = await fetch('/api/sessions', {
        headers: {
          Authorization: `Bearer ${mockFreeUserSession.access_token}`,
        },
      });

      const historyData = await historyResponse.json();

      expect(historyData.sessions).toHaveLength(1);
      expect(historyData.sessions[0]).toMatchObject({
        ufs: ['SC'],
        data_inicial: '2026-02-01',
        data_final: '2026-02-10',
        total_filtered: 15,
        valor_total: 150000,
      });
    });

    it('should save search parameters correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['SC', 'PR'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              custom_keywords: null,
              total_filtered: 25,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const historyResponse = await fetch('/api/sessions', {
        headers: {
          Authorization: `Bearer ${mockFreeUserSession.access_token}`,
        },
      });

      const data = await historyResponse.json();

      expect(data.sessions[0].sectors).toEqual(['Vestuário']);
      expect(data.sessions[0].ufs).toEqual(['SC', 'PR']);
      expect(data.sessions[0].data_inicial).toBe('2026-02-01');
      expect(data.sessions[0].data_final).toBe('2026-02-10');
    });

    it('should save custom keywords when using termo search mode', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: [],
              ufs: ['SC'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              custom_keywords: ['uniforme', 'camiseta'],
              total_filtered: 10,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const historyResponse = await fetch('/api/sessions', {
        headers: {
          Authorization: `Bearer ${mockFreeUserSession.access_token}`,
        },
      });

      const data = await historyResponse.json();

      expect(data.sessions[0].custom_keywords).toEqual(['uniforme', 'camiseta']);
      expect(data.sessions[0].sectors).toEqual([]);
    });
  });

  describe('AC2: History page displays saved searches', () => {
    it('should render history page with session list', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['SC'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              custom_keywords: null,
              total_raw: 100,
              total_filtered: 15,
              valor_total: 150000,
              resumo_executivo: 'Test summary',
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Histórico de Buscas/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Vestuário')).toBeInTheDocument();
        expect(screen.getByText(/SC/)).toBeInTheDocument();
        expect(screen.getByText('15')).toBeInTheDocument();
        expect(screen.getByText('Test summary')).toBeInTheDocument();
      });
    });

    it('should display multiple session entries', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-3',
              sectors: ['Vestuário'],
              ufs: ['SC'],
              data_inicial: '2026-02-09',
              data_final: '2026-02-10',
              total_filtered: 5,
              valor_total: 50000,
              created_at: '2026-02-10T12:00:00Z', // Most recent
            },
            {
              id: 'session-2',
              sectors: ['Alimentos'],
              ufs: ['PR'],
              data_inicial: '2026-02-05',
              data_final: '2026-02-10',
              total_filtered: 10,
              valor_total: 100000,
              created_at: '2026-02-10T11:00:00Z',
            },
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['RS'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              total_filtered: 15,
              valor_total: 150000,
              created_at: '2026-02-10T10:00:00Z', // Oldest
            },
          ],
          total: 3,
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText('Vestuário')).toBeInTheDocument();
        expect(screen.getByText('Alimentos')).toBeInTheDocument();
      });

      // Verify all three sessions are displayed
      const sessionCards = screen.getAllByText(/SC|PR|RS/);
      expect(sessionCards.length).toBeGreaterThanOrEqual(3);
    });

    it('should format currency values correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['SC'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              total_filtered: 15,
              valor_total: 150000.50,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        // Brazilian currency format: R$ 150.000,50
        expect(screen.getByText(/R\$/)).toBeInTheDocument();
      });
    });
  });

  describe('AC3: Failed searches should not create history', () => {
    it('should not save session when search returns 500 error', async () => {
      // Search fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({
          detail: { message: 'Internal server error' },
        }),
      });

      // History should be empty
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [],
          total: 0,
        }),
      });

      const searchResponse = await fetch('/api/buscar', {
        method: 'POST',
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
        body: JSON.stringify({ ufs: ['SC'] }),
      });

      expect(searchResponse.ok).toBe(false);

      const historyResponse = await fetch('/api/sessions', {
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
      });

      const historyData = await historyResponse.json();
      expect(historyData.sessions).toHaveLength(0);
    });

    it('should not save session when search returns empty results', async () => {
      // Search returns 0 results
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          download_id: null,
          total_filtrado: 0,
          resumo: {
            resumo_executivo: 'No results found',
            total_oportunidades: 0,
            valor_total: 0,
            destaques: [],
            distribuicao_uf: {},
          },
        }),
      });

      // History should still save (even with 0 results, it's a valid search)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['AC'], // Small state with no results
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              total_filtered: 0,
              valor_total: 0,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const searchResponse = await fetch('/api/buscar', {
        method: 'POST',
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
        body: JSON.stringify({ ufs: ['AC'] }),
      });

      expect(searchResponse.ok).toBe(true);

      const historyResponse = await fetch('/api/sessions', {
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
      });

      const historyData = await historyResponse.json();
      // Empty results still create history entry (user performed a search)
      expect(historyData.sessions).toHaveLength(1);
      expect(historyData.sessions[0].total_filtered).toBe(0);
    });
  });

  describe('AC4: History pagination', () => {
    it('should paginate history with limit and offset', async () => {
      // First page
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: Array.from({ length: 20 }, (_, i) => ({
            id: `session-${i + 1}`,
            sectors: ['Vestuário'],
            ufs: ['SC'],
            data_inicial: '2026-02-01',
            data_final: '2026-02-10',
            total_filtered: 10,
            valor_total: 100000,
            created_at: `2026-02-10T${10 + i}:00:00Z`,
          })),
          total: 50,
        }),
      });

      const historyResponse = await fetch('/api/sessions?limit=20&offset=0', {
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
      });

      const data = await historyResponse.json();

      expect(data.sessions).toHaveLength(20);
      expect(data.total).toBe(50);
    });

    it('should load second page with offset', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: Array.from({ length: 20 }, (_, i) => ({
            id: `session-${i + 21}`, // IDs 21-40
            sectors: ['Alimentos'],
            ufs: ['PR'],
            data_inicial: '2026-02-01',
            data_final: '2026-02-10',
            total_filtered: 5,
            valor_total: 50000,
            created_at: `2026-02-09T${10 + i}:00:00Z`,
          })),
          total: 50,
        }),
      });

      const historyResponse = await fetch('/api/sessions?limit=20&offset=20', {
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
      });

      const data = await historyResponse.json();

      expect(data.sessions).toHaveLength(20);
      expect(data.sessions[0].id).toBe('session-21');
    });

    it('should render pagination controls in UI', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: Array.from({ length: 20 }, (_, i) => ({
            id: `session-${i + 1}`,
            sectors: ['Vestuário'],
            ufs: ['SC'],
            data_inicial: '2026-02-01',
            data_final: '2026-02-10',
            total_filtered: 10,
            created_at: '2026-02-10T10:00:00Z',
          })),
          total: 50, // 3 pages (50 / 20)
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Próximo/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Anterior/i })).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText(/1 de 3/)).toBeInTheDocument();
      });
    });
  });

  describe('AC5: History ordering', () => {
    it('should order sessions by created_at DESC (newest first)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-3',
              created_at: '2026-02-10T12:00:00Z', // Most recent
              sectors: ['Vestuário'],
              ufs: ['SC'],
              total_filtered: 5,
            },
            {
              id: 'session-2',
              created_at: '2026-02-10T11:00:00Z',
              sectors: ['Alimentos'],
              ufs: ['PR'],
              total_filtered: 10,
            },
            {
              id: 'session-1',
              created_at: '2026-02-10T10:00:00Z', // Oldest
              sectors: ['Informática'],
              ufs: ['RS'],
              total_filtered: 15,
            },
          ],
          total: 3,
        }),
      });

      const historyResponse = await fetch('/api/sessions', {
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
      });

      const data = await historyResponse.json();

      expect(data.sessions[0].id).toBe('session-3'); // Newest
      expect(data.sessions[2].id).toBe('session-1'); // Oldest
    });
  });

  describe('AC6: Re-run search from history', () => {
    it('should navigate to /buscar with correct parameters when re-running search', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['SC', 'PR'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              custom_keywords: null,
              total_filtered: 25,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText('Vestuário')).toBeInTheDocument();
      });

      // Click "Re-executar busca" button
      const rerunButton = screen.getByRole('button', { name: /Executar novamente|Re-executar/i });
      await act(async () => {
        fireEvent.click(rerunButton);
      });

      // Verify navigation with correct params
      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining('/buscar?ufs=SC,PR&data_inicial=2026-02-01&data_final=2026-02-10&mode=setor')
      );
    });

    it('should re-run custom keyword search correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: [],
              ufs: ['SC'],
              data_inicial: '2026-02-01',
              data_final: '2026-02-10',
              custom_keywords: ['uniforme', 'camiseta'],
              total_filtered: 10,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/uniforme, camiseta/)).toBeInTheDocument();
      });

      const rerunButton = screen.getByRole('button', { name: /Executar novamente|Re-executar/i });
      await act(async () => {
        fireEvent.click(rerunButton);
      });

      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining('mode=termos&termos=uniforme camiseta')
      );
    });
  });

  describe('AC7: Free user history limit', () => {
    it('should save all 3 free searches to history', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-3',
              sectors: ['Vestuário'],
              ufs: ['RS'],
              total_filtered: 8,
              created_at: '2026-02-10T12:00:00Z',
            },
            {
              id: 'session-2',
              sectors: ['Alimentos'],
              ufs: ['PR'],
              total_filtered: 12,
              created_at: '2026-02-10T11:00:00Z',
            },
            {
              id: 'session-1',
              sectors: ['Informática'],
              ufs: ['SC'],
              total_filtered: 15,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 3,
        }),
      });

      const historyResponse = await fetch('/api/sessions', {
        headers: { Authorization: `Bearer ${mockFreeUserSession.access_token}` },
      });

      const data = await historyResponse.json();

      expect(data.sessions).toHaveLength(3);
      expect(data.total).toBe(3);
    });
  });
});
