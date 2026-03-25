/**
 * STORY-326 AC5: UfProgressGrid component tests.
 *
 * Verifies that the grid correctly renders:
 * - Total found counter (totalFound prop)
 * - Per-UF status cards with correct labels and colors
 * - Success with count > 0 (green) vs success with count = 0 (amber)
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { UfProgressGrid } from '../../app/buscar/components/UfProgressGrid';
import type { UfStatus } from '../../hooks/useSearchSSE';

describe('STORY-326 AC5: UfProgressGrid', () => {
  // ---------------------------------------------------------------------------
  // AC5: totalFound display
  // ---------------------------------------------------------------------------

  it('AC5: renders totalFound=150 and displays "150"', () => {
    const statuses = new Map<string, UfStatus>([
      ['SP', { status: 'success', count: 100 }],
      ['RJ', { status: 'success', count: 50 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={150} />);

    // The counter displays the total
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('oportunidades')).toBeInTheDocument();
  });

  it('renders totalFound=0 and displays "0"', () => {
    const statuses = new Map<string, UfStatus>([
      ['SP', { status: 'success', count: 0 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);

    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('renders totalFound=1 with singular "oportunidade"', () => {
    const statuses = new Map<string, UfStatus>([
      ['SP', { status: 'success', count: 1 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={1} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('oportunidade')).toBeInTheDocument();
  });

  it('renders large totalFound=1930 with locale formatting', () => {
    const statuses = new Map<string, UfStatus>([
      ['SP', { status: 'success', count: 1930 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={1930} />);

    // pt-BR locale: "1.930"
    expect(screen.getByText('1.930')).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // AC2: Per-UF card labels
  // ---------------------------------------------------------------------------

  it('AC2: success with count > 0 shows "N oportunidades" label', () => {
    const statuses = new Map<string, UfStatus>([
      ['SP', { status: 'success', count: 42 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={42} />);

    expect(screen.getByText('SP')).toBeInTheDocument();
    expect(screen.getByText('42 oportunidades')).toBeInTheDocument();
  });

  it('AC2: success with count=1 shows singular "1 oportunidade"', () => {
    const statuses = new Map<string, UfStatus>([
      ['RJ', { status: 'success', count: 1 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={1} />);

    expect(screen.getByText('RJ')).toBeInTheDocument();
    expect(screen.getByText('1 oportunidade')).toBeInTheDocument();
  });

  it('success with count=0 shows "Sem oportunidades" (amber state)', () => {
    const statuses = new Map<string, UfStatus>([
      ['ES', { status: 'success', count: 0 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);

    expect(screen.getByText('ES')).toBeInTheDocument();
    expect(screen.getByText('Sem oportunidades')).toBeInTheDocument();
  });

  it('pending UF shows "Aguardando..."', () => {
    const statuses = new Map<string, UfStatus>([
      ['BA', { status: 'pending' }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);

    expect(screen.getByText('BA')).toBeInTheDocument();
    expect(screen.getByText('Aguardando...')).toBeInTheDocument();
  });

  it('fetching UF shows "Consultando..."', () => {
    const statuses = new Map<string, UfStatus>([
      ['RS', { status: 'fetching' }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);

    expect(screen.getByText('RS')).toBeInTheDocument();
    expect(screen.getByText('Consultando...')).toBeInTheDocument();
  });

  it('failed UF shows "Fonte lenta"', () => {
    const statuses = new Map<string, UfStatus>([
      ['MG', { status: 'failed' }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);

    expect(screen.getByText('MG')).toBeInTheDocument();
    expect(screen.getByText('Fonte lenta')).toBeInTheDocument();
  });

  it('recovered UF shows "N oportunidades (recuperado)"', () => {
    const statuses = new Map<string, UfStatus>([
      ['PR', { status: 'recovered', count: 15 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={15} />);

    expect(screen.getByText('PR')).toBeInTheDocument();
    expect(screen.getByText('15 oportunidades (recuperado)')).toBeInTheDocument();
  });

  it('retrying UF shows attempt number', () => {
    const statuses = new Map<string, UfStatus>([
      ['SC', { status: 'retrying', attempt: 2 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);

    expect(screen.getByText('SC')).toBeInTheDocument();
    expect(screen.getByText('Tentativa 2...')).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // Grid renders all UFs sorted alphabetically
  // ---------------------------------------------------------------------------

  it('renders multiple UFs sorted alphabetically', () => {
    const statuses = new Map<string, UfStatus>([
      ['SP', { status: 'success', count: 100 }],
      ['BA', { status: 'pending' }],
      ['MG', { status: 'fetching' }],
      ['RJ', { status: 'success', count: 50 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={150} />);

    const ufLabels = screen.getAllByText(/^(BA|MG|RJ|SP)$/);
    expect(ufLabels).toHaveLength(4);
    // Sorted: BA, MG, RJ, SP
    expect(ufLabels[0]).toHaveTextContent('BA');
    expect(ufLabels[1]).toHaveTextContent('MG');
    expect(ufLabels[2]).toHaveTextContent('RJ');
    expect(ufLabels[3]).toHaveTextContent('SP');
  });

  // ---------------------------------------------------------------------------
  // Accessibility
  // ---------------------------------------------------------------------------

  it('has aria-label with UF name and status', () => {
    const statuses = new Map<string, UfStatus>([
      ['SP', { status: 'success', count: 42 }],
    ]);

    render(<UfProgressGrid ufStatuses={statuses} totalFound={42} />);

    const card = screen.getByLabelText('SP: 42 oportunidades');
    expect(card).toBeInTheDocument();
  });
});
