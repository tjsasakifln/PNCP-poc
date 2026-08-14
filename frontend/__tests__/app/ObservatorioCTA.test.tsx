import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ObservatorioCTA } from '@/app/observatorio/ObservatorioCTA';

jest.mock('@/contexts/UserContext', () => ({
  useUser: jest.fn(),
}));

import { useUser } from '@/contexts/UserContext';
const mockUseUser = useUser as jest.Mock;

describe('ObservatorioCTA', () => {
  it('renders signup link when user is not authenticated', () => {
    mockUseUser.mockReturnValue({ user: null, authLoading: false });
    render(<ObservatorioCTA />);
    const link = screen.getByRole('link', { name: /ver editais do meu setor/i });
    expect(link).toHaveAttribute('href', '/consultoria-b2g?ref=observatorio-hub');
  });

  it('renders buscar link when user is authenticated', () => {
    mockUseUser.mockReturnValue({ user: { id: 'u1' }, authLoading: false });
    render(<ObservatorioCTA />);
    const link = screen.getByRole('link', { name: /ver editais personalizados/i });
    expect(link).toHaveAttribute('href', '/buscar');
  });

  it('renders signup link while auth is loading (safe fallback)', () => {
    mockUseUser.mockReturnValue({ user: null, authLoading: true });
    render(<ObservatorioCTA />);
    const link = screen.getByRole('link', { name: /ver editais do meu setor/i });
    expect(link).toHaveAttribute('href', '/consultoria-b2g?ref=observatorio-hub');
  });
});
