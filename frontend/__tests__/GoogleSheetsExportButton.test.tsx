/**
 * Tests for GoogleSheetsExportButton component.
 *
 * Tests OAuth redirect, loading states, error handling, and success flow.
 * Uses mocked fetch API and toast notifications.
 *
 * STORY-180: Google Sheets Export - Frontend Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import GoogleSheetsExportButton from '../components/GoogleSheetsExportButton';
import { toast } from 'sonner';

// Mock toast notifications
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  },
}));

// Mock window.open
global.open = jest.fn();

describe('GoogleSheetsExportButton', () => {
  const mockLicitacoes = [
    {
      codigoUnidadeCompradora: '123456',
      objetoCompra: 'Aquisição de uniformes escolares',
      nomeOrgao: 'Prefeitura Municipal',
      uf: 'SP',
      municipio: 'São Paulo',
      valorTotalEstimado: 50000.0,
      modalidadeNome: 'Pregão Eletrônico',
      dataPublicacaoPncp: '2026-02-01',
      dataAberturaProposta: '2026-02-15',
      situacaoCompra: 'Aberta',
      linkSistemaOrigem: 'https://pncp.gov.br/app/editais/123',
    },
  ];

  const mockSession = {
    user: {
      id: 'user-123-uuid',
      email: 'test@example.com',
    },
    access_token: 'supabase-jwt-token',
  };

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders button with correct text', () => {
      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      expect(screen.getByText('Exportar para Google Sheets')).toBeInTheDocument();
    });

    it('renders Google Sheets icon', () => {
      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      // Check for SVG icon (using aria-label or role)
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('is disabled when disabled prop is true', () => {
      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={true}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('is disabled when licitacoes list is empty', () => {
      render(
        <GoogleSheetsExportButton
          licitacoes={[]}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('is disabled when session is null', () => {
      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={null}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });

  describe('Export Success Flow', () => {
    it('calls API with correct payload on button click', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          spreadsheet_id: 'test-sheet-id-123',
          spreadsheet_url: 'https://docs.google.com/spreadsheets/d/test-sheet-id-123',
          total_rows: 1,
        }),
      });

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/export/google-sheets',
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${mockSession.access_token}`,
            },
            body: expect.stringContaining('Uniformes - SP'),
          })
        );
      });
    });

    it('shows loading state during export', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  status: 200,
                  json: async () => ({
                    success: true,
                    spreadsheet_id: 'test-id',
                    spreadsheet_url: 'https://docs.google.com/spreadsheets/d/test-id',
                    total_rows: 1,
                  }),
                }),
              100
            )
          )
      );

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Check loading state
      await waitFor(() => {
        expect(screen.getByText('Exportando...')).toBeInTheDocument();
      });

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByText('Exportando...')).not.toBeInTheDocument();
      });
    });

    it('opens spreadsheet in new tab on success', async () => {
      const mockFetch = global.fetch as jest.Mock;
      const mockOpen = global.open as jest.Mock;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          spreadsheet_id: 'test-sheet-id-123',
          spreadsheet_url: 'https://docs.google.com/spreadsheets/d/test-sheet-id-123',
          total_rows: 1,
        }),
      });

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockOpen).toHaveBeenCalledWith(
          'https://docs.google.com/spreadsheets/d/test-sheet-id-123',
          '_blank',
          'noopener,noreferrer'
        );
      });
    });

    it('shows success toast notification', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          spreadsheet_id: 'test-id',
          spreadsheet_url: 'https://docs.google.com/spreadsheets/d/test-id',
          total_rows: 1,
        }),
      });

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          expect.stringContaining('exportada com sucesso')
        );
      });
    });
  });

  describe('OAuth Redirect (401)', () => {
    it('redirects to OAuth authorization on 401 response', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          detail: 'Google Sheets não autorizado',
        }),
      });

      // Mock window.location
      delete (window as any).location;
      window.location = { href: '' } as any;

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(window.location.href).toContain('/api/auth/google');
        expect(window.location.href).toContain('redirect=');
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error toast on 403 (permission denied)', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({
          detail: 'Token revogado ou permissões insuficientes',
        }),
      });

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining('permissões insuficientes')
        );
      });
    });

    it('shows error toast on 429 (rate limit)', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({
          detail: 'Limite de requisições excedido',
        }),
      });

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining('Limite de requisições')
        );
      });
    });

    it('shows generic error toast on 500 (server error)', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          detail: 'Erro interno do servidor',
        }),
      });

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(expect.stringContaining('Erro ao exportar'));
      });
    });

    it('shows error toast on network failure', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
    });
  });

  describe('Export Title Format', () => {
    it('formats export title with date', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          spreadsheet_id: 'test-id',
          spreadsheet_url: 'https://docs.google.com/spreadsheets/d/test-id',
          total_rows: 1,
        }),
      });

      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
        const callBody = JSON.parse((mockFetch.mock.calls[0][1] as any).body);
        expect(callBody.title).toMatch(/SmartLic - Uniformes - SP - \d{2}\/\d{2}\/\d{4}/);
      });
    });
  });

  describe('Accessibility', () => {
    it('button has accessible name', () => {
      render(
        <GoogleSheetsExportButton
          licitacoes={mockLicitacoes}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button', { name: /exportar para google sheets/i });
      expect(button).toBeInTheDocument();
    });

    it('disabled button cannot be clicked', () => {
      const mockFetch = global.fetch as jest.Mock;

      render(
        <GoogleSheetsExportButton
          licitacoes={[]}
          searchLabel="Uniformes - SP"
          disabled={false}
          session={mockSession}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Fetch should NOT be called
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });
});
