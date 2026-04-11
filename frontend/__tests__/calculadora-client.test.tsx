/**
 * STORY-432 AC8: Tests for Calculadora edge cases.
 *
 * Tests: resultado quando total_ativas = 0, quando analisa > total_ativas,
 *        share buttons presentes no resultado.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock next/link
jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

import CalculadoraClient from '@/app/calculadora/CalculadoraClient';

// Helper: mock fetch for /api/calculadora/dados
function mockCalcFetch(data: {
  total_editais_mes: number;
  avg_value: number;
  p25_value?: number;
  p75_value?: number;
  setor_name: string;
  uf: string;
}) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => data,
  } as Response);
}

async function preencherECalcular(
  setorValue = 'engenharia',
  ufValue = 'SP',
  editaisMes = 20,
) {
  // Step 1: escolher setor e UF
  const setorSelect = screen.getByLabelText(/setor de atuação/i);
  const ufSelect = screen.getByLabelText(/uf principal/i);
  fireEvent.change(setorSelect, { target: { value: setorValue } });
  fireEvent.change(ufSelect, { target: { value: ufValue } });
  fireEvent.click(screen.getByRole('button', { name: /continuar/i }));

  // Step 2: ajustar slider de editais
  await waitFor(() => screen.getByLabelText(/editais que sua equipe/i));
  const slider = screen.getByLabelText(/editais que sua equipe/i);
  fireEvent.change(slider, { target: { value: String(editaisMes) } });
  fireEvent.click(screen.getByRole('button', { name: /continuar/i }));

  // Step 3: calcular
  await waitFor(() => screen.getByRole('button', { name: /calcular/i }));
  fireEvent.click(screen.getByRole('button', { name: /calcular/i }));
}

describe('CalculadoraClient — STORY-432 AC8', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Silence JSDOM window.location errors for share URL tests
    Object.defineProperty(window, 'location', {
      value: { origin: 'https://smartlic.tech', search: '' },
      writable: true,
    });
  });

  it('exibe resultado correto quando total_editais_mes = 0', async () => {
    mockCalcFetch({
      total_editais_mes: 0,
      avg_value: 0,
      setor_name: 'Engenharia, Projetos e Obras',
      uf: 'SP',
    });

    render(<CalculadoraClient />);
    await preencherECalcular('engenharia', 'SP', 10);

    await waitFor(() => {
      // valorPerdido = max(0, 0 - 10) * avgVal * taxa = 0
      expect(screen.getByText('R$ 0')).toBeInTheDocument();
    });
  });

  it('exibe cobertura 100% quando analisa > total_editais_mes', async () => {
    mockCalcFetch({
      total_editais_mes: 5,
      avg_value: 100000,
      setor_name: 'Engenharia, Projetos e Obras',
      uf: 'SP',
    });

    render(<CalculadoraClient />);
    await preencherECalcular('engenharia', 'SP', 100); // analisa 100, há apenas 5

    await waitFor(() => {
      // coberturaAtual = min(100, 100/5 * 100) = 100%
      // O texto "Sua equipe cobre 100% do total disponível" está no DOM
      expect(document.body.textContent).toContain('100%');
    });
  });

  it('exibe valor perdido = 0 quando analisa >= total_editais_mes', async () => {
    mockCalcFetch({
      total_editais_mes: 10,
      avg_value: 50000,
      setor_name: 'Saúde',
      uf: 'RJ',
    });

    render(<CalculadoraClient />);
    await preencherECalcular('medicamentos', 'RJ', 15); // analisa 15, há 10

    await waitFor(() => {
      // editaisNaoAnalisados = max(0, 10 - 15) = 0 → valorPerdido = 0
      expect(screen.getByText('R$ 0')).toBeInTheDocument();
    });
  });

  it('exibe botão de compartilhamento no resultado (AC5)', async () => {
    mockCalcFetch({
      total_editais_mes: 50,
      avg_value: 200000,
      setor_name: 'Vestuário e Uniformes',
      uf: 'SC',
    });

    render(<CalculadoraClient />);
    await preencherECalcular('vestuario', 'SC', 10);

    await waitFor(() => {
      expect(screen.getByText(/copiar link/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /whatsapp/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /linkedin/i })).toBeInTheDocument();
    });
  });

  it('link WhatsApp contém wa.me e URL de compartilhamento', async () => {
    mockCalcFetch({
      total_editais_mes: 30,
      avg_value: 80000,
      setor_name: 'Saúde',
      uf: 'MG',
    });

    render(<CalculadoraClient />);
    await preencherECalcular('medicamentos', 'MG', 5);

    await waitFor(() => {
      const waLink = screen.getByRole('link', { name: /whatsapp/i });
      expect(waLink).toHaveAttribute('href', expect.stringContaining('wa.me'));
      expect(waLink).toHaveAttribute('href', expect.stringContaining('calculadora'));
    });
  });

  it('link LinkedIn contém linkedin.com/sharing', async () => {
    mockCalcFetch({
      total_editais_mes: 20,
      avg_value: 60000,
      setor_name: 'TI',
      uf: 'PR',
    });

    render(<CalculadoraClient />);
    await preencherECalcular('informatica', 'PR', 5);

    await waitFor(() => {
      const liLink = screen.getByRole('link', { name: /linkedin/i });
      expect(liLink).toHaveAttribute('href', expect.stringContaining('linkedin.com/sharing'));
    });
  });

  it('exibe erro quando fetch falha', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    render(<CalculadoraClient />);
    await preencherECalcular('engenharia', 'SP', 10);

    await waitFor(() => {
      expect(screen.getByText(/não foi possível obter os dados/i)).toBeInTheDocument();
    });
  });
});
