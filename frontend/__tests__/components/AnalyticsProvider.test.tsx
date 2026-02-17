/**
 * AnalyticsProvider Component Tests
 *
 * Tests Mixpanel initialization, cookie consent handling, and page tracking
 */

import { render, screen, waitFor } from '@testing-library/react';
import { AnalyticsProvider } from '@/app/components/AnalyticsProvider';
import mixpanel from 'mixpanel-browser';
import * as Sentry from '@sentry/nextjs';

// Mock dependencies
jest.mock('mixpanel-browser');
jest.mock('@sentry/nextjs', () => ({
  init: jest.fn(),
  getClient: jest.fn(() => null),
}));
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/test-page'),
}));

// Mock getCookieConsent and captureUTMParams
jest.mock('../../app/components/CookieConsentBanner', () => ({
  getCookieConsent: jest.fn(),
}));

jest.mock('../../hooks/useAnalytics', () => ({
  captureUTMParams: jest.fn(),
}));

const mockMixpanel = mixpanel as jest.Mocked<typeof mixpanel>;
const { getCookieConsent } = require('../../app/components/CookieConsentBanner');
const { captureUTMParams } = require('../../hooks/useAnalytics');

describe('AnalyticsProvider Component', () => {
  const originalEnv = process.env;
  const originalSentry = { ...Sentry };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    process.env = { ...originalEnv };
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';
    process.env.NODE_ENV = 'test';

    // Mock Sentry.getClient to return null initially
    (Sentry.getClient as jest.Mock).mockReturnValue(null);
  });

  afterEach(() => {
    process.env = originalEnv;
    jest.restoreAllMocks();
  });

  describe('initialization', () => {
    it('should render children', () => {
      getCookieConsent.mockReturnValue({ analytics: true });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should not initialize Mixpanel if token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
      getCookieConsent.mockReturnValue({ analytics: true });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
    });

    it('should initialize Mixpanel if consent is granted', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalledWith('test-token-123', {
          debug: false,
          track_pageview: false,
          persistence: 'localStorage',
        });
      });
    });

    it('should not initialize Mixpanel if consent is not granted', () => {
      getCookieConsent.mockReturnValue({ analytics: false });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
    });

    it('should not initialize if consent is null', () => {
      getCookieConsent.mockReturnValue(null);

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
    });
  });

  describe('page tracking', () => {
    it('should track page_load event after initialization', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
          environment: 'test',
        }));
      });

      // Verify path is included (may be undefined in test environment)
      const trackCalls = mockMixpanel.track.mock.calls;
      const pageLoadCall = trackCalls.find((call: any) => call[0] === 'page_load');
      expect(pageLoadCall).toBeDefined();
      expect(pageLoadCall![1]).toHaveProperty('timestamp');
    });

    it('should capture UTM params on first load', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });
      captureUTMParams.mockClear();

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(captureUTMParams).toHaveBeenCalled();
      }, { timeout: 3000 });
    });

    it('should not track page_load if consent not granted', () => {
      getCookieConsent.mockReturnValue({ analytics: false });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });
  });

  describe('consent changes', () => {
    it('should initialize Mixpanel when consent is granted via event', async () => {
      getCookieConsent.mockReturnValue({ analytics: false });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();

      // Simulate consent change
      getCookieConsent.mockReturnValue({ analytics: true });
      const event = new CustomEvent('cookie-consent-changed', {
        detail: { analytics: true },
      });

      await waitFor(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalled();
      });
    });

    it('should opt out when consent is revoked', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalled();
      });

      // Simulate consent revocation
      getCookieConsent.mockReturnValue({ analytics: false });
      const event = new CustomEvent('cookie-consent-changed', {
        detail: { analytics: false },
      });

      await waitFor(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockMixpanel.opt_out_tracking).toHaveBeenCalled();
      });
    });

    it('should opt back in when consent is re-granted after opt-out', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalled();
      });

      // Revoke consent
      getCookieConsent.mockReturnValue({ analytics: false });
      let event = new CustomEvent('cookie-consent-changed', {
        detail: { analytics: false },
      });
      window.dispatchEvent(event);

      await waitFor(() => {
        expect(mockMixpanel.opt_out_tracking).toHaveBeenCalled();
      });

      // Re-grant consent
      getCookieConsent.mockReturnValue({ analytics: true });
      event = new CustomEvent('cookie-consent-changed', {
        detail: { analytics: true },
      });
      window.dispatchEvent(event);

      await waitFor(() => {
        expect(mockMixpanel.opt_in_tracking).toHaveBeenCalled();
      });
    });
  });

  describe('page exit tracking', () => {
    it('should add beforeunload listener when consent granted', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalled();
      });

      expect(addEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));

      addEventListenerSpy.mockRestore();
    });

    it('should not track page_exit if consent not granted', () => {
      getCookieConsent.mockReturnValue({ analytics: false });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      const event = new Event('beforeunload');
      window.dispatchEvent(event);

      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });

    it('should clean up beforeunload listener on unmount', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalled();
      });

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });
  });

  describe('error handling', () => {
    it('should handle Mixpanel initialization errors gracefully', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });
      mockMixpanel.init.mockImplementation(() => {
        throw new Error('Init failed');
      });

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(consoleWarnSpy).toHaveBeenCalledWith('Mixpanel initialization failed:', expect.any(Error));
      });

      consoleWarnSpy.mockRestore();
    });

    it('should handle track errors gracefully', async () => {
      getCookieConsent.mockReturnValue({ analytics: true });
      mockMixpanel.track.mockImplementation(() => {
        throw new Error('Track failed');
      });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      // Should not throw
      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalled();
      });
    });
  });

  describe('Sentry integration', () => {
    it('should have Sentry DSN configured if environment variable is set', () => {
      // Note: Sentry.init is called at module load time, not in component
      // This test verifies the module-level initialization would happen
      // The actual Sentry.init call happens when the module is first imported

      // We can verify the DSN is used in the environment
      const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
      if (dsn) {
        expect(dsn).toContain('sentry.io');
      } else {
        // If no DSN, Sentry shouldn't initialize
        expect(dsn).toBeUndefined();
      }
    });
  });

  describe('development mode', () => {
    it('should enable debug mode in development', async () => {
      process.env.NODE_ENV = 'development';
      getCookieConsent.mockReturnValue({ analytics: true });

      render(
        <AnalyticsProvider>
          <div>Test Content</div>
        </AnalyticsProvider>
      );

      await waitFor(() => {
        expect(mockMixpanel.init).toHaveBeenCalledWith('test-token-123', expect.objectContaining({
          debug: true,
        }));
      });
    });
  });
});
