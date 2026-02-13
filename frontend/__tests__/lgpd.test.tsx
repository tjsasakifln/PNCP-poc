/**
 * LGPD Compliance Tests (STORY-213)
 *
 * Tests for CookieConsentBanner, AnalyticsProvider, and useAnalytics hook
 * to ensure full compliance with LGPD (Lei Geral de Proteção de Dados)
 *
 * Coverage:
 * - AC24: Cookie consent banner display and interaction
 * - AC25: Analytics initialization based on consent
 * - AC8: Hook respects consent before tracking
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { renderHook, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  CookieConsentBanner,
  getCookieConsent,
  setCookieConsent,
  clearCookieConsent,
} from '../app/components/CookieConsentBanner';
import { AnalyticsProvider } from '../app/components/AnalyticsProvider';
import { useAnalytics } from '../hooks/useAnalytics';

// Mock mixpanel-browser — use jest.fn() inline to avoid hoisting issues
jest.mock('mixpanel-browser', () => ({
  init: jest.fn(),
  track: jest.fn(),
  identify: jest.fn(),
  people: {
    set: jest.fn(),
  },
  opt_out_tracking: jest.fn(),
  opt_in_tracking: jest.fn(),
}));

// Get reference to the mocked module after jest.mock hoisting
import mixpanel from 'mixpanel-browser';
const mockMixpanel = mixpanel as jest.Mocked<typeof mixpanel> & {
  opt_out_tracking: jest.Mock;
  opt_in_tracking: jest.Mock;
};

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/buscar'),
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('CookieConsentBanner Component (AC24, AC25)', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('TC-LGPD-001: Banner Visibility', () => {
    it('should render banner on fresh visit (no localStorage)', () => {
      render(<CookieConsentBanner />);

      expect(screen.getByRole('dialog', { name: 'Consentimento de cookies' })).toBeInTheDocument();
      expect(screen.getByText('Utilizamos cookies')).toBeInTheDocument();
    });

    it('should NOT render banner when consent already exists in localStorage', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(<CookieConsentBanner />);

      expect(screen.queryByRole('dialog', { name: 'Consentimento de cookies' })).not.toBeInTheDocument();
    });

    it('should NOT render banner when consent is rejected in localStorage', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: false,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(<CookieConsentBanner />);

      expect(screen.queryByRole('dialog', { name: 'Consentimento de cookies' })).not.toBeInTheDocument();
    });
  });

  describe('TC-LGPD-002: Accept All Button', () => {
    it('should store consent with analytics:true when "Aceitar Todos" is clicked', () => {
      render(<CookieConsentBanner />);

      const acceptButton = screen.getByRole('button', { name: 'Aceitar Todos' });
      fireEvent.click(acceptButton);

      const consent = getCookieConsent();
      expect(consent).not.toBeNull();
      expect(consent?.analytics).toBe(true);
      expect(consent?.timestamp).toBeDefined();
    });

    it('should hide banner after "Aceitar Todos" is clicked', async () => {
      render(<CookieConsentBanner />);

      const acceptButton = screen.getByRole('button', { name: 'Aceitar Todos' });
      fireEvent.click(acceptButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog', { name: 'Consentimento de cookies' })).not.toBeInTheDocument();
      });
    });

    it('should dispatch cookie-consent-changed event when accepted', () => {
      const eventListener = jest.fn();
      window.addEventListener('cookie-consent-changed', eventListener);

      render(<CookieConsentBanner />);

      const acceptButton = screen.getByRole('button', { name: 'Aceitar Todos' });
      fireEvent.click(acceptButton);

      expect(eventListener).toHaveBeenCalled();
      const event = eventListener.mock.calls[0][0] as CustomEvent;
      expect(event.detail.analytics).toBe(true);

      window.removeEventListener('cookie-consent-changed', eventListener);
    });
  });

  describe('TC-LGPD-003: Reject Non-Essential Button', () => {
    it('should store consent with analytics:false when "Rejeitar Não Essenciais" is clicked', () => {
      render(<CookieConsentBanner />);

      const rejectButton = screen.getByRole('button', { name: 'Rejeitar Não Essenciais' });
      fireEvent.click(rejectButton);

      const consent = getCookieConsent();
      expect(consent).not.toBeNull();
      expect(consent?.analytics).toBe(false);
      expect(consent?.timestamp).toBeDefined();
    });

    it('should hide banner after "Rejeitar Não Essenciais" is clicked', async () => {
      render(<CookieConsentBanner />);

      const rejectButton = screen.getByRole('button', { name: 'Rejeitar Não Essenciais' });
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog', { name: 'Consentimento de cookies' })).not.toBeInTheDocument();
      });
    });

    it('should dispatch cookie-consent-changed event when rejected', () => {
      const eventListener = jest.fn();
      window.addEventListener('cookie-consent-changed', eventListener);

      render(<CookieConsentBanner />);

      const rejectButton = screen.getByRole('button', { name: 'Rejeitar Não Essenciais' });
      fireEvent.click(rejectButton);

      expect(eventListener).toHaveBeenCalled();
      const event = eventListener.mock.calls[0][0] as CustomEvent;
      expect(event.detail.analytics).toBe(false);

      window.removeEventListener('cookie-consent-changed', eventListener);
    });
  });

  describe('TC-LGPD-004: Manage Cookies Event', () => {
    it('should re-show banner when "manage-cookies" event is dispatched', async () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(<CookieConsentBanner />);

      // Banner should be hidden initially
      expect(screen.queryByRole('dialog', { name: 'Consentimento de cookies' })).not.toBeInTheDocument();

      // Dispatch "manage-cookies" event
      act(() => {
        window.dispatchEvent(new Event('manage-cookies'));
      });

      // Banner should reappear
      await waitFor(() => {
        expect(screen.getByRole('dialog', { name: 'Consentimento de cookies' })).toBeInTheDocument();
      });
    });

    it('should clear localStorage when "manage-cookies" event is dispatched', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(<CookieConsentBanner />);

      act(() => {
        window.dispatchEvent(new Event('manage-cookies'));
      });

      expect(getCookieConsent()).toBeNull();
    });
  });

  describe('TC-LGPD-005: Banner Content and Links', () => {
    it('should display privacy policy link to /privacidade', () => {
      render(<CookieConsentBanner />);

      const privacyLink = screen.getByRole('link', { name: 'Saiba mais' });
      expect(privacyLink).toBeInTheDocument();
      expect(privacyLink).toHaveAttribute('href', '/privacidade');
    });

    it('should display description of essential and analytical cookies', () => {
      render(<CookieConsentBanner />);

      expect(screen.getByText(/cookies essenciais/i)).toBeInTheDocument();
      expect(screen.getByText(/cookies analíticos/i)).toBeInTheDocument();
      expect(screen.getByText(/Mixpanel/i)).toBeInTheDocument();
    });
  });

  describe('TC-LGPD-006: Helper Functions', () => {
    it('getCookieConsent should return null when no consent exists', () => {
      const consent = getCookieConsent();
      expect(consent).toBeNull();
    });

    it('getCookieConsent should return valid consent object', () => {
      setCookieConsent(true);
      const consent = getCookieConsent();

      expect(consent).not.toBeNull();
      expect(consent?.analytics).toBe(true);
      expect(consent?.timestamp).toBeDefined();
    });

    it('getCookieConsent should handle corrupted localStorage data', () => {
      localStorageMock.setItem('bidiq_cookie_consent', 'invalid-json');
      const consent = getCookieConsent();
      expect(consent).toBeNull();
    });

    it('setCookieConsent should store consent in localStorage', () => {
      const consent = setCookieConsent(true);

      expect(consent.analytics).toBe(true);
      expect(consent.timestamp).toBeDefined();

      const stored = JSON.parse(localStorageMock.getItem('bidiq_cookie_consent') || '{}');
      expect(stored.analytics).toBe(true);
    });

    it('clearCookieConsent should remove consent from localStorage', () => {
      setCookieConsent(true);
      expect(getCookieConsent()).not.toBeNull();

      clearCookieConsent();
      expect(getCookieConsent()).toBeNull();
    });
  });
});

describe('AnalyticsProvider Component (AC25)', () => {
  const mockToken = 'test-mixpanel-token';

  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = mockToken;
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
  });

  describe('TC-LGPD-007: Mixpanel Initialization with Consent', () => {
    it('should NOT initialize Mixpanel without consent', () => {
      render(
        <AnalyticsProvider>
          <div>Test content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });

    it('should initialize Mixpanel when consent with analytics:true exists', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(
        <AnalyticsProvider>
          <div>Test content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).toHaveBeenCalledWith(mockToken, {
        debug: false, // NODE_ENV is 'test' by default
        track_pageview: false,
        persistence: 'localStorage',
      });
    });

    it('should track page_load event after initialization with consent', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(
        <AnalyticsProvider>
          <div>Test content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
        timestamp: expect.any(String),
        environment: 'test',
      }));
    });

    it('should NOT initialize Mixpanel when consent with analytics:false exists', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: false,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(
        <AnalyticsProvider>
          <div>Test content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-008: Consent Revocation', () => {
    it('should call opt_out_tracking when consent is revoked', () => {
      // Start with consent
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(
        <AnalyticsProvider>
          <div>Test content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).toHaveBeenCalled();

      // Revoke consent
      act(() => {
        clearCookieConsent();
        window.dispatchEvent(new CustomEvent('cookie-consent-changed', { detail: null }));
      });

      expect(mockMixpanel.opt_out_tracking).toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-009: Missing Mixpanel Token', () => {
    it('should NOT initialize Mixpanel when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      render(
        <AnalyticsProvider>
          <div>Test content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-010: Consent Change Handling', () => {
    it('should initialize Mixpanel when consent is granted after page load', () => {
      render(
        <AnalyticsProvider>
          <div>Test content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();

      // Grant consent
      act(() => {
        const consent = setCookieConsent(true);
        window.dispatchEvent(new CustomEvent('cookie-consent-changed', { detail: consent }));
      });

      expect(mockMixpanel.init).toHaveBeenCalled();
    });
  });
});

describe('useAnalytics Hook (AC8)', () => {
  const mockToken = 'test-mixpanel-token';

  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = mockToken;
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
  });

  describe('TC-LGPD-011: trackEvent without Consent', () => {
    it('should NOT call mixpanel.track without consent', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('test_event', { foo: 'bar' });
      });

      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });

    it('should NOT call mixpanel.track when consent with analytics:false', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: false,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('test_event', { foo: 'bar' });
      });

      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-012: trackEvent with Consent', () => {
    it('should call mixpanel.track when consent with analytics:true', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('test_event', { foo: 'bar' });
      });

      expect(mockMixpanel.track).toHaveBeenCalledWith('test_event', expect.objectContaining({
        foo: 'bar',
        timestamp: expect.any(String),
        environment: 'test',
      }));
    });

    it('should include custom properties in track call', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('search_started', {
          ufs: ['SC', 'PR'],
          setor: 'vestuario',
        });
      });

      expect(mockMixpanel.track).toHaveBeenCalledWith('search_started', expect.objectContaining({
        ufs: ['SC', 'PR'],
        setor: 'vestuario',
      }));
    });
  });

  describe('TC-LGPD-013: identifyUser without Consent', () => {
    it('should NOT call mixpanel.identify without consent', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.identifyUser('user-123', { email: 'test@example.com' });
      });

      expect(mockMixpanel.identify).not.toHaveBeenCalled();
      expect(mockMixpanel.people.set).not.toHaveBeenCalled();
    });

    it('should NOT call mixpanel.identify when consent with analytics:false', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: false,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.identifyUser('user-123', { email: 'test@example.com' });
      });

      expect(mockMixpanel.identify).not.toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-014: identifyUser with Consent', () => {
    it('should call mixpanel.identify when consent with analytics:true', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.identifyUser('user-123', { email: 'test@example.com' });
      });

      expect(mockMixpanel.identify).toHaveBeenCalledWith('user-123');
      expect(mockMixpanel.people.set).toHaveBeenCalledWith({ email: 'test@example.com' });
    });

    it('should call mixpanel.identify without properties', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.identifyUser('user-456');
      });

      expect(mockMixpanel.identify).toHaveBeenCalledWith('user-456');
      expect(mockMixpanel.people.set).not.toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-015: trackPageView', () => {
    it('should call trackEvent with page_view event when consent granted', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageView('/buscar');
      });

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_view', expect.objectContaining({
        page: '/buscar',
      }));
    });

    it('should NOT track page view without consent', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageView('/buscar');
      });

      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-016: Missing Mixpanel Token', () => {
    it('should NOT track events when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('test_event');
      });

      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });
  });

  describe('TC-LGPD-017: Error Handling', () => {
    it('should handle mixpanel.track errors gracefully', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      mockMixpanel.track.mockImplementationOnce(() => {
        throw new Error('Mixpanel error');
      });

      const { result } = renderHook(() => useAnalytics());

      expect(() => {
        act(() => {
          result.current.trackEvent('test_event');
        });
      }).not.toThrow();
    });

    it('should handle mixpanel.identify errors gracefully', () => {
      localStorageMock.setItem('bidiq_cookie_consent', JSON.stringify({
        analytics: true,
        timestamp: '2026-02-13T00:00:00.000Z',
      }));

      mockMixpanel.identify.mockImplementationOnce(() => {
        throw new Error('Mixpanel error');
      });

      const { result } = renderHook(() => useAnalytics());

      expect(() => {
        act(() => {
          result.current.identifyUser('user-123');
        });
      }).not.toThrow();
    });
  });
});
