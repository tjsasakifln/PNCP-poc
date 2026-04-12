/**
 * STORY-369 AC3: Tests for TrialExitSurveyModal component.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { TrialExitSurveyModal } from '../components/TrialExitSurveyModal';

// Mock analytics
jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
    identifyUser: jest.fn(),
    resetUser: jest.fn(),
    trackPageView: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn();

describe('TrialExitSurveyModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'survey-123', created_at: '2026-04-11T00:00:00Z' }),
    });
  });

  it('renders title and options', () => {
    render(<TrialExitSurveyModal onClose={jest.fn()} />);
    expect(screen.getByText(/Antes de sair/)).toBeInTheDocument();
    expect(screen.getByText(/Não encontrei editais relevantes/)).toBeInTheDocument();
    expect(screen.getByText(/preço não cabe/)).toBeInTheDocument();
    expect(screen.getByText(/Ainda estou avaliando/)).toBeInTheDocument();
    expect(screen.getByText(/Outro motivo/)).toBeInTheDocument();
  });

  it('submit button disabled until option selected', () => {
    render(<TrialExitSurveyModal onClose={jest.fn()} />);
    const btn = screen.getByRole('button', { name: /Enviar resposta/ });
    expect(btn).toBeDisabled();
  });

  it('enables submit after selecting option', () => {
    render(<TrialExitSurveyModal onClose={jest.fn()} />);
    const radio = screen.getByDisplayValue('preco_alto');
    fireEvent.click(radio);
    const btn = screen.getByRole('button', { name: /Enviar resposta/ });
    expect(btn).not.toBeDisabled();
  });

  it('shows textarea when "Outro motivo" selected', () => {
    render(<TrialExitSurveyModal onClose={jest.fn()} />);
    const radio = screen.getByDisplayValue('outro');
    fireEvent.click(radio);
    expect(screen.getByPlaceholderText(/Conte-nos mais/)).toBeInTheDocument();
  });

  it('does NOT show textarea for other options', () => {
    render(<TrialExitSurveyModal onClose={jest.fn()} />);
    const radio = screen.getByDisplayValue('no_editais');
    fireEvent.click(radio);
    expect(screen.queryByPlaceholderText(/Conte-nos mais/)).not.toBeInTheDocument();
  });

  it('calls onClose and sets localStorage on skip', () => {
    const onClose = jest.fn();
    render(<TrialExitSurveyModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /Pular/ }));
    expect(onClose).toHaveBeenCalled();
    expect(localStorage.getItem('trial_exit_survey_submitted')).toBe('true');
  });

  it('submits survey and sets localStorage on success', async () => {
    const onClose = jest.fn();
    jest.useFakeTimers();
    render(<TrialExitSurveyModal onClose={onClose} />);

    fireEvent.click(screen.getByDisplayValue('ainda_avaliando'));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Enviar resposta/ }));
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/trial/exit-survey',
        expect.objectContaining({ method: 'POST' })
      );
    });

    expect(localStorage.getItem('trial_exit_survey_submitted')).toBe('true');
    jest.useRealTimers();
  });
});
