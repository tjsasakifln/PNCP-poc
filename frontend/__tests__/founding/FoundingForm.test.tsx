/**
 * STORY-BIZ-001: FoundingForm tests
 *
 * Covers field validation, CNPJ masking, submit payload, success redirect,
 * and error surface when backend returns non-2xx.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FoundingForm from '../../app/founding/components/FoundingForm';

const VALID_MOTIVO = 'A'.repeat(160);

function fillValidForm() {
  fireEvent.change(screen.getByLabelText(/Seu nome completo/i), { target: { value: 'Maria Silva' } });
  fireEvent.change(screen.getByLabelText(/Email corporativo/i), { target: { value: 'maria@empresa.com' } });
  fireEvent.change(screen.getByLabelText(/CNPJ/i), { target: { value: '00394460000141' } });
  fireEvent.change(screen.getByLabelText(/Por que o SmartLic/i), { target: { value: VALID_MOTIVO } });
}

describe('FoundingForm', () => {
  const originalLocation = window.location;
  const hrefSetter = jest.fn();

  beforeEach(() => {
    jest.restoreAllMocks();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        assign: jest.fn(),
        set href(v: string) {
          hrefSetter(v);
        },
        get href() {
          return 'http://testhost/founding';
        },
      },
    });
    hrefSetter.mockClear();
    // Avoid real fetch
    (global.fetch as unknown as jest.Mock) = jest.fn();
  });

  afterAll(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
  });

  it('renders all required fields', () => {
    render(<FoundingForm />);
    expect(screen.getByLabelText(/Seu nome completo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email corporativo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/CNPJ/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Por que o SmartLic/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Quero ser um founding partner/i })).toBeInTheDocument();
  });

  it('masks CNPJ to 00.000.000/0000-00 as user types', () => {
    render(<FoundingForm />);
    const cnpj = screen.getByLabelText(/CNPJ/i) as HTMLInputElement;
    fireEvent.change(cnpj, { target: { value: '00394460000141' } });
    expect(cnpj.value).toBe('00.394.460/0001-41');
  });

  it('surfaces a validation error when motivo is too short', async () => {
    render(<FoundingForm />);
    fireEvent.change(screen.getByLabelText(/Seu nome completo/i), { target: { value: 'Maria' } });
    fireEvent.change(screen.getByLabelText(/Email corporativo/i), { target: { value: 'maria@e.com' } });
    fireEvent.change(screen.getByLabelText(/CNPJ/i), { target: { value: '00394460000141' } });
    fireEvent.change(screen.getByLabelText(/Por que o SmartLic/i), { target: { value: 'curto demais' } });
    fireEvent.submit(screen.getByRole('button', { name: /Quero ser um founding partner/i }).closest('form')!);
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/mínimo 140/i);
  });

  it('rejects invalid CNPJ length', async () => {
    render(<FoundingForm />);
    fillValidForm();
    fireEvent.change(screen.getByLabelText(/CNPJ/i), { target: { value: '123' } });
    fireEvent.submit(screen.getByRole('button', { name: /Quero ser um founding partner/i }).closest('form')!);
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/14 dígitos/i);
  });

  it('posts clean CNPJ digits (no mask) to the API and redirects on success', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.stripe.com/abc', lead_id: 'lead-1' }),
    });
    render(<FoundingForm />);
    fillValidForm();
    fireEvent.submit(screen.getByRole('button', { name: /Quero ser um founding partner/i }).closest('form')!);

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    const [url, opts] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toBe('/api/founding/checkout');
    const body = JSON.parse((opts as { body: string }).body);
    expect(body.cnpj).toBe('00394460000141');
    expect(body.email).toBe('maria@empresa.com');
    expect(body.motivo.length).toBeGreaterThanOrEqual(140);

    await waitFor(() => expect(hrefSetter).toHaveBeenCalledWith('https://checkout.stripe.com/abc'));
  });

  it('surfaces backend detail when API returns non-2xx', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({ detail: 'Este email já possui conta SmartLic.' }),
    });
    render(<FoundingForm />);
    fillValidForm();
    fireEvent.submit(screen.getByRole('button', { name: /Quero ser um founding partner/i }).closest('form')!);
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/já possui conta/i);
    expect(hrefSetter).not.toHaveBeenCalled();
  });

  it('surfaces a generic network error when fetch rejects', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('net down'));
    render(<FoundingForm />);
    fillValidForm();
    fireEvent.submit(screen.getByRole('button', { name: /Quero ser um founding partner/i }).closest('form')!);
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/falha de rede/i);
  });
});
