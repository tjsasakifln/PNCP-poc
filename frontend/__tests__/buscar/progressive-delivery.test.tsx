/**
 * Tests for GTM-RESILIENCE-A04 Progressive Delivery
 *
 * AC16: Cache immediate rendering with "Atualizando..." indicator
 * AC17: Refresh banner with new opportunity count and "Atualizar resultados" button
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import RefreshBanner from '../../app/buscar/components/RefreshBanner';
import type { RefreshAvailableInfo } from '../../hooks/useSearchProgress';

// ---------------------------------------------------------------------------
// AC17: RefreshBanner component
// ---------------------------------------------------------------------------
describe('AC17: RefreshBanner', () => {
  const baseInfo: RefreshAvailableInfo = {
    totalLive: 15,
    totalCached: 10,
    newCount: 5,
    updatedCount: 0,
    removedCount: 0,
  };

  it('shows "Dados atualizados disponíveis" text', () => {
    render(<RefreshBanner refreshInfo={baseInfo} onRefresh={jest.fn()} />);
    expect(screen.getByText(/Dados atualizados disponíveis/)).toBeInTheDocument();
  });

  it('shows new opportunity count', () => {
    render(<RefreshBanner refreshInfo={baseInfo} onRefresh={jest.fn()} />);
    expect(screen.getByText(/5 novas/)).toBeInTheDocument();
  });

  it('shows "Atualizar resultados" button', () => {
    render(<RefreshBanner refreshInfo={baseInfo} onRefresh={jest.fn()} />);
    expect(screen.getByRole('button', { name: /Atualizar resultados/ })).toBeInTheDocument();
  });

  it('calls onRefresh when button clicked', () => {
    const onRefresh = jest.fn();
    render(<RefreshBanner refreshInfo={baseInfo} onRefresh={onRefresh} />);
    fireEvent.click(screen.getByRole('button', { name: /Atualizar resultados/ }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('shows updated count when present', () => {
    const info: RefreshAvailableInfo = { ...baseInfo, newCount: 1, updatedCount: 3 };
    render(<RefreshBanner refreshInfo={info} onRefresh={jest.fn()} />);
    expect(screen.getByText(/1 nova/)).toBeInTheDocument();
    expect(screen.getByText(/3 atualizadas/)).toBeInTheDocument();
  });

  it('shows removed count when present', () => {
    const info: RefreshAvailableInfo = { ...baseInfo, newCount: 0, removedCount: 2 };
    render(<RefreshBanner refreshInfo={info} onRefresh={jest.fn()} />);
    expect(screen.getByText(/2 removidas/)).toBeInTheDocument();
  });

  it('disables button when isRefreshing', () => {
    render(<RefreshBanner refreshInfo={baseInfo} onRefresh={jest.fn()} isRefreshing />);
    const button = screen.getByRole('button', { name: /Atualizando\.\.\./ });
    expect(button).toBeDisabled();
  });

  it('shows fallback text when all counts are zero', () => {
    const info: RefreshAvailableInfo = { totalLive: 8, totalCached: 8, newCount: 0, updatedCount: 0, removedCount: 0 };
    render(<RefreshBanner refreshInfo={info} onRefresh={jest.fn()} />);
    expect(screen.getByText(/8 oportunidades/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC16: "Atualizando..." indicator (tested via role="status")
// ---------------------------------------------------------------------------
describe('AC16: Atualizando indicator in RefreshBanner area', () => {
  it('RefreshBanner has role="status" for accessibility', () => {
    const info: RefreshAvailableInfo = { totalLive: 5, totalCached: 3, newCount: 2, updatedCount: 0, removedCount: 0 };
    render(<RefreshBanner refreshInfo={info} onRefresh={jest.fn()} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
