/**
 * STORY-BIZ-002: tests for ConsultoriaUpsellBanner.
 *
 * Covers:
 *  - banner renders only for trial users with consultancy recommendation
 *  - dismiss persists in localStorage and hides immediately
 *  - dismiss TTL (7 days) — simulated by setting an old timestamp
 *  - no render for non-trial or non-consultancy cases
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ConsultoriaUpsellBanner from '../components/ConsultoriaUpsellBanner';
import type { RecommendedPlan } from '../hooks/useRecommendedPlan';

const mockTrackEvent = jest.fn();

jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

const mockUseRecommendedPlan = jest.fn<
  { data: RecommendedPlan | null; loading: boolean; error: string | null },
  []
>();

jest.mock('../hooks/useRecommendedPlan', () => ({
  useRecommendedPlan: () => mockUseRecommendedPlan(),
}));

jest.mock('next/link', () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return ({ children, href, onClick }: any) => (
    <a href={href} onClick={onClick}>
      {children}
    </a>
  );
});

const DISMISS_KEY = 'consultoria_banner_dismissed_ts';

describe('ConsultoriaUpsellBanner', () => {
  beforeEach(() => {
    mockTrackEvent.mockClear();
    window.localStorage.clear();
    mockUseRecommendedPlan.mockReset();
  });

  function mockRecommendation(plan_key: 'consultoria' | 'smartlic_pro', reason: 'cnae_consultoria' | 'default') {
    mockUseRecommendedPlan.mockReturnValue({
      data: { plan_key, reason },
      loading: false,
      error: null,
    });
  }

  it('renders banner when trial user is a consultancy', async () => {
    mockRecommendation('consultoria', 'cnae_consultoria');
    render(<ConsultoriaUpsellBanner isTrialing />);
    expect(await screen.findByRole('region', { name: /oferta plano consultoria/i })).toBeInTheDocument();
  });

  it('fires consultoria_upsell_viewed event on mount when visible', async () => {
    mockRecommendation('consultoria', 'cnae_consultoria');
    render(<ConsultoriaUpsellBanner isTrialing />);
    await waitFor(() => {
      expect(mockTrackEvent).toHaveBeenCalledWith('consultoria_upsell_viewed', { surface: 'banner' });
    });
  });

  it('does not render for paid (non-trial) users', () => {
    mockRecommendation('consultoria', 'cnae_consultoria');
    render(<ConsultoriaUpsellBanner isTrialing={false} />);
    expect(screen.queryByRole('region', { name: /oferta plano consultoria/i })).not.toBeInTheDocument();
  });

  it('does not render when recommended plan is Pro (default)', () => {
    mockRecommendation('smartlic_pro', 'default');
    render(<ConsultoriaUpsellBanner isTrialing />);
    expect(screen.queryByRole('region', { name: /oferta plano consultoria/i })).not.toBeInTheDocument();
  });

  it('does not render when still loading the recommendation', () => {
    mockUseRecommendedPlan.mockReturnValue({ data: null, loading: true, error: null });
    render(<ConsultoriaUpsellBanner isTrialing />);
    expect(screen.queryByRole('region', { name: /oferta plano consultoria/i })).not.toBeInTheDocument();
  });

  it('hides after dismiss and writes timestamp to localStorage', async () => {
    mockRecommendation('consultoria', 'cnae_consultoria');
    render(<ConsultoriaUpsellBanner isTrialing />);
    const banner = await screen.findByRole('region', { name: /oferta plano consultoria/i });
    expect(banner).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /dispensar oferta/i }));
    });

    expect(window.localStorage.getItem(DISMISS_KEY)).toBeTruthy();
    expect(screen.queryByRole('region', { name: /oferta plano consultoria/i })).not.toBeInTheDocument();
    expect(mockTrackEvent).toHaveBeenCalledWith('consultoria_upsell_dismissed', { surface: 'banner' });
  });

  it('stays hidden when dismissed within the 7-day TTL', () => {
    mockRecommendation('consultoria', 'cnae_consultoria');
    // 2 days ago — still inside the TTL
    window.localStorage.setItem(DISMISS_KEY, String(Date.now() - 2 * 24 * 60 * 60 * 1000));
    render(<ConsultoriaUpsellBanner isTrialing />);
    expect(screen.queryByRole('region', { name: /oferta plano consultoria/i })).not.toBeInTheDocument();
  });

  it('re-shows banner once the 7-day dismiss TTL expires', async () => {
    mockRecommendation('consultoria', 'cnae_consultoria');
    // 8 days ago — TTL expired
    window.localStorage.setItem(DISMISS_KEY, String(Date.now() - 8 * 24 * 60 * 60 * 1000));
    render(<ConsultoriaUpsellBanner isTrialing />);
    expect(await screen.findByRole('region', { name: /oferta plano consultoria/i })).toBeInTheDocument();
  });
});
