/**
 * DiagnosticForm Component Tests — REPO-014 (#766)
 *
 * Covers:
 * - Renders all required fields
 * - Shows loading state during submit
 * - Shows success message after successful submit
 * - Shows error message on failure
 * - Shows validation error for missing required fields
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DiagnosticForm from '@/components/forms/DiagnosticForm';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Stub analytics to avoid Mixpanel / sessionStorage in tests
jest.mock('@/lib/analytics-events', () => ({
  trackFormStarted: jest.fn(),
  trackFormSubmitted: jest.fn(),
}));

jest.mock('@/hooks/useAnalytics', () => ({
  getStoredUTMParams: jest.fn(() => ({})),
  captureUTMParams: jest.fn(),
}));

// Stub Sentry dynamic import
jest.mock('@sentry/nextjs', () => ({
  captureException: jest.fn(),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fillRequiredFields() {
  fireEvent.change(screen.getByTestId('diag-nome'), {
    target: { value: 'Maria Silva' },
  });
  fireEvent.change(screen.getByTestId('diag-email'), {
    target: { value: 'maria@empresa.com' },
  });
  fireEvent.change(screen.getByTestId('diag-setor'), {
    target: { value: 'engenharia' },
  });
  fireEvent.change(screen.getByTestId('diag-modalidade'), {
    target: { value: 'radar' },
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DiagnosticForm', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  describe('Renders all required fields', () => {
    beforeEach(() => {
      render(<DiagnosticForm source="test" />);
    });

    it('renders nome field', () => {
      expect(screen.getByTestId('diag-nome')).toBeInTheDocument();
    });

    it('renders email field', () => {
      expect(screen.getByTestId('diag-email')).toBeInTheDocument();
    });

    it('renders empresa field (optional)', () => {
      expect(screen.getByTestId('diag-empresa')).toBeInTheDocument();
    });

    it('renders cnpj field (optional)', () => {
      expect(screen.getByTestId('diag-cnpj')).toBeInTheDocument();
    });

    it('renders setor select', () => {
      expect(screen.getByTestId('diag-setor')).toBeInTheDocument();
    });

    it('renders modalidade select', () => {
      expect(screen.getByTestId('diag-modalidade')).toBeInTheDocument();
    });

    it('renders mensagem textarea (optional)', () => {
      expect(screen.getByTestId('diag-mensagem')).toBeInTheDocument();
    });

    it('renders telefone field (optional)', () => {
      expect(screen.getByTestId('diag-telefone')).toBeInTheDocument();
    });

    it('renders submit button', () => {
      expect(
        screen.getByTestId('diagnostic-form-submit')
      ).toBeInTheDocument();
    });

    it('setor select includes sector options', () => {
      const select = screen.getByTestId('diag-setor') as HTMLSelectElement;
      const options = Array.from(select.options).map((o) => o.value);
      expect(options).toContain('engenharia');
      expect(options).toContain('saude');
      expect(options).toContain('software');
    });

    it('modalidade select includes all 4 options', () => {
      const select = screen.getByTestId(
        'diag-modalidade'
      ) as HTMLSelectElement;
      const values = Array.from(select.options).map((o) => o.value);
      expect(values).toContain('radar');
      expect(values).toContain('report');
      expect(values).toContain('intel');
      expect(values).toContain('nao_sei');
    });
  });

  describe('defaultModalidade prop', () => {
    it('pre-selects the provided modalidade', () => {
      render(<DiagnosticForm source="test" defaultModalidade="intel" />);
      const select = screen.getByTestId(
        'diag-modalidade'
      ) as HTMLSelectElement;
      expect(select.value).toBe('intel');
    });
  });

  describe('Shows loading state on submit', () => {
    it('disables submit button while loading', async () => {
      // fetch never resolves — keeps loading state
      global.fetch = jest.fn(
        () => new Promise<Response>(() => {})
      ) as jest.Mock;

      render(<DiagnosticForm source="test" />);
      fillRequiredFields();

      fireEvent.click(screen.getByTestId('diagnostic-form-submit'));

      await waitFor(() => {
        expect(
          screen.getByTestId('diagnostic-form-submit')
        ).toBeDisabled();
      });

      expect(screen.getByTestId('diagnostic-form-submit')).toHaveTextContent(
        'Enviando...'
      );
    });
  });

  describe('Shows success message after successful submit', () => {
    it('renders success message on 200 response', async () => {
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, receipt_id: 'rec-consultoria' }),
      } as Response) as jest.Mock;

      render(<DiagnosticForm source="consultoria-b2g" />);
      fillRequiredFields();

      fireEvent.click(screen.getByTestId('diagnostic-form-submit'));

      await waitFor(() => {
        expect(
          screen.getByTestId('diagnostic-form-success')
        ).toBeInTheDocument();
      });

      expect(screen.getByTestId('diagnostic-form-receipt')).toHaveTextContent('rec-consultoria');
      expect(screen.queryByText('maria@empresa.com')).not.toBeInTheDocument();
      const body = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body);
      expect(body.source).toBe('consultoria-b2g');
      expect(body.cta_id).toBe('cta.consultoria.submit');
      expect(body.route_family).toBe('consultoria');
    });

    it('calls onSuccess callback on success', async () => {
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response) as jest.Mock;

      const onSuccess = jest.fn();
      render(<DiagnosticForm source="test" onSuccess={onSuccess} />);
      fillRequiredFields();

      fireEvent.click(screen.getByTestId('diagnostic-form-submit'));

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Shows error on failure', () => {
    it('shows inline error on non-ok response', async () => {
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Servidor indisponível' }),
      } as Response) as jest.Mock;

      render(<DiagnosticForm source="test" />);
      fillRequiredFields();

      fireEvent.click(screen.getByTestId('diagnostic-form-submit'));

      await waitFor(() => {
        expect(
          screen.getByTestId('diagnostic-form-error')
        ).toBeInTheDocument();
      });
    });

    it('shows error on network failure', async () => {
      global.fetch = jest
        .fn()
        .mockRejectedValueOnce(new Error('Network Error')) as jest.Mock;

      render(<DiagnosticForm source="test" />);
      fillRequiredFields();

      fireEvent.click(screen.getByTestId('diagnostic-form-submit'));

      await waitFor(() => {
        expect(
          screen.getByTestId('diagnostic-form-error')
        ).toBeInTheDocument();
      });
    });

    it('shows validation error when required fields are missing', async () => {
      render(<DiagnosticForm source="test" />);

      // Click submit without filling anything
      fireEvent.click(screen.getByTestId('diagnostic-form-submit'));

      await waitFor(() => {
        expect(
          screen.getByTestId('diagnostic-form-error')
        ).toBeInTheDocument();
      });
    });
  });

  describe('CNPJ formatting', () => {
    it('formats CNPJ as user types', async () => {
      render(<DiagnosticForm source="test" />);
      const input = screen.getByTestId('diag-cnpj') as HTMLInputElement;

      await userEvent.type(input, '12345678000195');

      expect(input.value).toBe('12.345.678/0001-95');
    });
  });
});
