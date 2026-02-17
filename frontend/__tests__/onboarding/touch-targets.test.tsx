import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock next/navigation
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

// Mock AuthProvider
const mockUseAuth = jest.fn();
jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock sonner
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

import OnboardingPage from '../../app/onboarding/page';

describe('Onboarding Touch Targets (WCAG 2.1)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { id: 'test-user', email: 'test@test.com' },
      session: { access_token: 'fake-token' },
      loading: false,
    });

    // Mock fetch for profile-context
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ context_data: {} }),
    });

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // Helper: navigate to step 2 (UF selection)
  async function goToStep2() {
    render(<OnboardingPage />);

    // Fill step 1 required fields
    const cnaeInput = screen.getByPlaceholderText(/Ex: Comércio de uniformes/i);
    fireEvent.change(cnaeInput, { target: { value: 'Uniformes' } });

    const objetivoInput = screen.getByPlaceholderText(/Ex: Encontrar oportunidades/i);
    fireEvent.change(objetivoInput, { target: { value: 'Encontrar uniformes' } });

    // Click Continuar
    const continuar = screen.getByTestId('btn-continuar');
    fireEvent.click(continuar);

    // Wait for step 2
    await waitFor(() => {
      expect(screen.getByText('Onde você atua e qual valor ideal?')).toBeInTheDocument();
    });
  }

  // AC7: UF buttons are WCAG-compliant (min-h-[44px])
  it('UF buttons have min-h-[44px] and min-w-[44px]', async () => {
    await goToStep2();

    const ufButton = screen.getByTestId('uf-button-SP');
    expect(ufButton.className).toContain('min-h-[44px]');
    expect(ufButton.className).toContain('min-w-[44px]');
  });

  it('UF buttons use text-sm instead of text-xs', async () => {
    await goToStep2();

    const ufButton = screen.getByTestId('uf-button-RJ');
    expect(ufButton.className).toContain('text-sm');
    expect(ufButton.className).not.toContain('text-xs');
  });

  // AC8: Region buttons have 44px touch targets
  it('region buttons have min-h-[44px]', async () => {
    await goToStep2();

    const regionButton = screen.getByTestId('region-button-Sudeste');
    expect(regionButton.className).toContain('min-h-[44px]');
  });

  // AC9: All CTAs are min-h-[44px]
  it('Continuar button has min-h-[44px]', () => {
    render(<OnboardingPage />);
    const btn = screen.getByTestId('btn-continuar');
    expect(btn.className).toContain('min-h-[44px]');
  });

  it('Pular button has min-h-[44px]', () => {
    render(<OnboardingPage />);
    const btn = screen.getByTestId('btn-pular');
    expect(btn.className).toContain('min-h-[44px]');
  });

  it('Voltar button has min-h-[44px] on step 2', async () => {
    await goToStep2();
    const btn = screen.getByTestId('btn-voltar');
    expect(btn.className).toContain('min-h-[44px]');
  });

  // All UF buttons across all regions are WCAG compliant
  it('all UF buttons across regions have WCAG touch targets', async () => {
    await goToStep2();

    const allUfButtons = screen.getAllByTestId(/^uf-button-/);
    expect(allUfButtons.length).toBe(27); // All 27 UFs

    allUfButtons.forEach((btn) => {
      expect(btn.className).toContain('min-h-[44px]');
      expect(btn.className).toContain('min-w-[44px]');
    });
  });

  // Value selects have proper height
  it('value selects have min-h-[44px]', async () => {
    await goToStep2();

    const selects = screen.getAllByRole('combobox');
    selects.forEach((select) => {
      expect(select.className).toContain('min-h-[44px]');
    });
  });
});
