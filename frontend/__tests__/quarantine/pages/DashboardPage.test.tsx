/**
 * DashboardPage Component Tests
 *
 * Tests analytics dashboard, stat cards, charts, empty states
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import DashboardPage from '@/app/dashboard/page';

// Mock useAuth
const mockUser = { id: 'user-1', email: 'test@test.com' };
const mockSession = { access_token: 'mock-token' };

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    user: mockUser,
    session: mockSession,
    loading: false,
  }),
}));

// Mock useAnalytics
const mockTrackEvent = jest.fn();

jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock recharts to avoid rendering issues
jest.mock('recharts', () => ({
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
}));

// Mock fetch
global.fetch = jest.fn();

const mockSummary = {
  total_searches: 42,
  total_downloads: 38,
  total_opportunities: 1523,
  total_value_discovered: 45000000,
  estimated_hours_saved: 84,
  avg_results_per_search: 36,
  success_rate: 90,
  member_since: '2025-01-15T00:00:00Z',
};

const mockTimeSeries = {
  data: [
    { label: '01/02', searches: 5, opportunities: 120, value: 5000000 },
    { label: '02/02', searches: 8, opportunities: 180, value: 7500000 },
    { label: '03/02', searches: 6, opportunities: 150, value: 6000000 },
  ],
};

const mockDimensions = {
  top_ufs: [
    { name: 'SP', count: 15, value: 20000000 },
    { name: 'RJ', count: 10, value: 12000000 },
    { name: 'MG', count: 8, value: 8000000 },
  ],
  top_sectors: [
    { name: 'Vestuário', count: 20, value: 15000000 },
    { name: 'Facilities', count: 12, value: 10000000 },
    { name: 'TI', count: 10, value: 8000000 },
  ],
};

beforeEach(() => {
  jest.clearAllMocks();
  (global.fetch as jest.Mock).mockImplementation((url: string) => {
    if (url.includes('summary')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockSummary,
      });
    }
    if (url.includes('searches-over-time')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeSeries,
      });
    }
    if (url.includes('top-dimensions')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockDimensions,
      });
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({}),
    });
  });
});

describe('DashboardPage', () => {
  describe('Loading state', () => {
    it('should show loading skeletons initially', () => {
      render(<DashboardPage />);

      // Loading skeletons
      const pulses = document.querySelectorAll('.animate-pulse');
      expect(pulses.length).toBeGreaterThan(0);
    });
  });

  describe('Summary stats', () => {
    it('should display stat cards with correct values', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument(); // total_searches
        expect(screen.getByText('1.523')).toBeInTheDocument(); // total_opportunities (formatted)
        expect(screen.getByText('84h')).toBeInTheDocument(); // estimated_hours_saved
        expect(screen.getByText('90%')).toBeInTheDocument(); // success_rate
      });
    });

    it('should show currency formatted values', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/R\$ 45M/i)).toBeInTheDocument(); // total_value_discovered
      });
    });

    it('should display member since date', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/Membro desde/i)).toBeInTheDocument();
      });
    });
  });

  describe('Charts', () => {
    it('should render time series chart', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });
    });

    it('should render top UFs pie chart', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
      });
    });

    it('should render top sectors bar chart', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      });
    });

    it('should have period toggle buttons', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Dia/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Semana/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Mês/i })).toBeInTheDocument();
      });
    });
  });

  describe('Empty state', () => {
    it('should show empty state when no searches', async () => {
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes('summary')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ ...mockSummary, total_searches: 0 }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({}),
        });
      });

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/Seu dashboard está vazio/i)).toBeInTheDocument();
        expect(screen.getByText(/Fazer primeira busca/i)).toBeInTheDocument();
      });
    });

    it('should have link to search page in empty state', async () => {
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes('summary')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ ...mockSummary, total_searches: 0 }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({}),
        });
      });

      render(<DashboardPage />);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /Fazer primeira busca/i });
        expect(link).toHaveAttribute('href', '/buscar');
      });
    });
  });

  describe('Export functionality', () => {
    it('should have CSV export button', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Exportar CSV/i })).toBeInTheDocument();
      });
    });

    it('should trigger export on button click', async () => {
      const createElementSpy = jest.spyOn(document, 'createElement');
      const createObjectURLSpy = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock');

      render(<DashboardPage />);

      await waitFor(() => {
        const exportButton = screen.getByRole('button', { name: /Exportar CSV/i });
        fireEvent.click(exportButton);
      });

      await waitFor(() => {
        expect(createElementSpy).toHaveBeenCalledWith('a');
        expect(createObjectURLSpy).toHaveBeenCalled();
        expect(mockTrackEvent).toHaveBeenCalledWith('analytics_exported', { format: 'csv' });
      });

      createElementSpy.mockRestore();
      createObjectURLSpy.mockRestore();
    });
  });

  describe('Quick links', () => {
    it('should display quick access links', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Nova Busca/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Histórico/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Minha Conta/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Planos/i })).toBeInTheDocument();
      });
    });

    it('should have correct href attributes', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Nova Busca/i })).toHaveAttribute('href', '/buscar');
        expect(screen.getByRole('link', { name: /Histórico/i })).toHaveAttribute('href', '/historico');
        expect(screen.getByRole('link', { name: /Minha Conta/i })).toHaveAttribute('href', '/conta');
        expect(screen.getByRole('link', { name: /Planos/i })).toHaveAttribute('href', '/planos');
      });
    });
  });

  describe('Error handling', () => {
    it('should display error message on fetch failure', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      });
    });

    it('should have retry button on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Tentar novamente/i })).toBeInTheDocument();
      });
    });
  });

  describe('Auth guard', () => {
    it('should show login prompt when not authenticated', () => {
      jest.spyOn(require('../../app/components/AuthProvider'), 'useAuth').mockReturnValue({
        user: null,
        session: null,
        loading: false,
      });

      render(<DashboardPage />);

      expect(screen.getByText(/Faça login para acessar o dashboard/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Ir para login/i })).toBeInTheDocument();
    });

    it('should show loading when auth is loading', () => {
      jest.spyOn(require('../../app/components/AuthProvider'), 'useAuth').mockReturnValue({
        user: null,
        session: null,
        loading: true,
      });

      render(<DashboardPage />);

      expect(screen.getByText(/Carregando/i)).toBeInTheDocument();
    });
  });

  describe('Analytics tracking', () => {
    it('should track dashboard view on mount', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(mockTrackEvent).toHaveBeenCalledWith('dashboard_viewed', { period: 'week' });
      });
    });
  });
});
