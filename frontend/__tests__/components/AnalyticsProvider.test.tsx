/**
 * AnalyticsProvider Component Tests
 *
 * Tests Mixpanel initialization, event tracking, and privacy mode
 * Target: 80%+ coverage
 */

import { render, waitFor } from '@testing-library/react';
import { AnalyticsProvider } from '@/app/components/AnalyticsProvider';
import mixpanel from 'mixpanel-browser';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/'),
}));

// Mock Mixpanel
jest.mock('mixpanel-browser', () => ({
  init: jest.fn(),
  track: jest.fn(),
  identify: jest.fn(),
  people: {
    set: jest.fn(),
  },
}));

describe('AnalyticsProvider Component', () => {
  const originalEnv = process.env;
  const mockMixpanel = mixpanel as jest.Mocked<typeof mixpanel>;

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment
    process.env = { ...originalEnv };
    // Reset DOM
    Object.defineProperty(document, 'referrer', {
      value: '',
      writable: true,
      configurable: true,
    });
    // Reset navigator
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Jest Test Agent',
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('Mixpanel Initialization', () => {
    it('should initialize Mixpanel when token is provided', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).toHaveBeenCalledWith('test-token-123', {
        debug: false,
        track_pageview: false,
        persistence: 'localStorage',
      });
    });

    it('should enable debug mode in development environment', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';
      process.env.NODE_ENV = 'development';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).toHaveBeenCalledWith('test-token-123', {
        debug: true,
        track_pageview: false,
        persistence: 'localStorage',
      });
    });

    it('should disable debug mode in production environment', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';
      process.env.NODE_ENV = 'production';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).toHaveBeenCalledWith('test-token-123', {
        debug: false,
        track_pageview: false,
        persistence: 'localStorage',
      });
    });

    it('should not initialize Mixpanel when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
    });

    it('should log success message when Mixpanel initializes', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(consoleSpy).toHaveBeenCalledWith('✅ Mixpanel initialized successfully');
      consoleSpy.mockRestore();
    });

    it('should log warning when token is missing', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        '⚠️ NEXT_PUBLIC_MIXPANEL_TOKEN not found. Analytics disabled.'
      );
      consoleSpy.mockRestore();
    });

    it('should handle initialization errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      mockMixpanel.init.mockImplementationOnce(() => {
        throw new Error('Init failed');
      });

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(consoleSpy).toHaveBeenCalledWith('❌ Mixpanel initialization failed:', expect.any(Error));
      consoleSpy.mockRestore();
    });
  });

  describe('Page Load Tracking', () => {
    it('should track page_load event on mount', () => {
      const { usePathname } = require('next/navigation');
      usePathname.mockReturnValue('/');
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';
      process.env.NODE_ENV = 'test';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
        path: '/',
        environment: 'test',
        referrer: 'direct',
        user_agent: 'Jest Test Agent',
      }));
    });

    it('should include referrer in page_load event when available', () => {
      const { usePathname } = require('next/navigation');
      usePathname.mockReturnValue('/');
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';
      Object.defineProperty(document, 'referrer', {
        value: 'https://google.com',
        writable: true,
        configurable: true,
      });

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
        path: '/',
        referrer: 'https://google.com',
      }));
    });

    it('should use "direct" as referrer when document.referrer is empty', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';
      Object.defineProperty(document, 'referrer', {
        value: '',
        writable: true,
        configurable: true,
      });

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
        referrer: 'direct',
      }));
    });

    it('should include ISO timestamp in page_load event', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      const trackCall = mockMixpanel.track.mock.calls[0];
      const timestamp = trackCall[1].timestamp;

      // Verify ISO format
      expect(timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
      expect(new Date(timestamp).toISOString()).toBe(timestamp);
    });

    it('should use pathname from usePathname hook', () => {
      const { usePathname } = require('next/navigation');
      usePathname.mockReturnValue('/search/results');
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
        path: '/search/results',
      }));
    });
  });

  describe('Page Exit Tracking', () => {
    it('should register beforeunload event listener', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(addEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
      addEventListenerSpy.mockRestore();
    });

    it('should track page_exit event on beforeunload', () => {
      const { usePathname } = require('next/navigation');
      usePathname.mockReturnValue('/');

      // Mock performance.timing.navigationStart
      Object.defineProperty(performance, 'timing', {
        value: { navigationStart: Date.now() - 5000 },
        writable: true,
        configurable: true,
      });

      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      // Clear page_load call
      mockMixpanel.track.mockClear();

      // Trigger beforeunload
      const beforeUnloadEvent = new Event('beforeunload');
      window.dispatchEvent(beforeUnloadEvent);

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_exit', expect.objectContaining({
        path: '/',
        session_duration_ms: expect.any(Number),
        session_duration_readable: expect.stringMatching(/^\d+s$/),
      }));
    });

    it('should calculate session duration in page_exit event', () => {
      // Mock performance.timing.navigationStart
      Object.defineProperty(performance, 'timing', {
        value: { navigationStart: Date.now() - 5000 },
        writable: true,
        configurable: true,
      });

      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      mockMixpanel.track.mockClear();

      const beforeUnloadEvent = new Event('beforeunload');
      window.dispatchEvent(beforeUnloadEvent);

      const trackCall = mockMixpanel.track.mock.calls[0];
      const sessionDuration = trackCall[1].session_duration_ms;

      expect(sessionDuration).toBeGreaterThanOrEqual(0);
      expect(typeof sessionDuration).toBe('number');
    });

    it('should format session duration as readable string', () => {
      // Mock performance.timing.navigationStart
      Object.defineProperty(performance, 'timing', {
        value: { navigationStart: Date.now() - 5000 },
        writable: true,
        configurable: true,
      });

      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      mockMixpanel.track.mockClear();

      const beforeUnloadEvent = new Event('beforeunload');
      window.dispatchEvent(beforeUnloadEvent);

      const trackCall = mockMixpanel.track.mock.calls[0];
      const readableDuration = trackCall[1].session_duration_readable;

      expect(readableDuration).toMatch(/^\d+s$/);
    });

    it('should not track page_exit when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      const beforeUnloadEvent = new Event('beforeunload');
      window.dispatchEvent(beforeUnloadEvent);

      expect(mockMixpanel.track).not.toHaveBeenCalled();
    });

    it('should handle page_exit tracking errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      mockMixpanel.track.mockImplementationOnce(() => {
        // First call (page_load) succeeds
      }).mockImplementationOnce(() => {
        // Second call (page_exit) fails
        throw new Error('Track failed');
      });

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      const beforeUnloadEvent = new Event('beforeunload');
      window.dispatchEvent(beforeUnloadEvent);

      expect(consoleSpy).toHaveBeenCalledWith('Failed to track page_exit:', expect.any(Error));
      consoleSpy.mockRestore();
    });
  });

  describe('Cleanup', () => {
    it('should remove beforeunload listener on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      const { unmount } = render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
      removeEventListenerSpy.mockRestore();
    });

    it('should not throw error when unmounting without token', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

      const { unmount } = render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(() => unmount()).not.toThrow();
    });
  });

  describe('Children Rendering', () => {
    it('should render children components', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      const { getByText } = render(
        <AnalyticsProvider>
          <div>Test Child Content</div>
        </AnalyticsProvider>
      );

      expect(getByText('Test Child Content')).toBeInTheDocument();
    });

    it('should render multiple children', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      const { getByText } = render(
        <AnalyticsProvider>
          <div>First Child</div>
          <div>Second Child</div>
          <div>Third Child</div>
        </AnalyticsProvider>
      );

      expect(getByText('First Child')).toBeInTheDocument();
      expect(getByText('Second Child')).toBeInTheDocument();
      expect(getByText('Third Child')).toBeInTheDocument();
    });

    it('should render children when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;

      const { getByText } = render(
        <AnalyticsProvider>
          <div>Content Without Analytics</div>
        </AnalyticsProvider>
      );

      expect(getByText('Content Without Analytics')).toBeInTheDocument();
    });
  });

  describe('Route Changes', () => {
    it('should track events when pathname changes', async () => {
      const { usePathname } = require('next/navigation');
      let currentPath = '/';
      usePathname.mockImplementation(() => currentPath);

      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      const { rerender } = render(
        <AnalyticsProvider>
          <div>Test</div>
        </AnalyticsProvider>
      );

      // Clear initial page_load call
      mockMixpanel.track.mockClear();

      // Change pathname
      currentPath = '/search';
      usePathname.mockReturnValue('/search');

      rerender(
        <AnalyticsProvider>
          <div>Test</div>
        </AnalyticsProvider>
      );

      // Should trigger new page_load event
      await waitFor(() => {
        expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
          path: '/search',
        }));
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing NODE_ENV gracefully', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';
      delete process.env.NODE_ENV;

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.track).toHaveBeenCalledWith('page_load', expect.objectContaining({
        environment: 'development',
      }));
    });

    it('should handle performance.timing being undefined', () => {
      const originalPerformance = performance;
      Object.defineProperty(window, 'performance', {
        value: { timing: undefined },
        writable: true,
        configurable: true,
      });

      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      const beforeUnloadEvent = new Event('beforeunload');
      window.dispatchEvent(beforeUnloadEvent);

      // Should not throw error
      expect(mockMixpanel.track).toHaveBeenCalled();

      Object.defineProperty(window, 'performance', {
        value: originalPerformance,
        writable: true,
        configurable: true,
      });
    });

    it('should handle empty MIXPANEL_TOKEN string', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = '';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).not.toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(
        '⚠️ NEXT_PUBLIC_MIXPANEL_TOKEN not found. Analytics disabled.'
      );
      consoleSpy.mockRestore();
    });
  });

  describe('Configuration', () => {
    it('should disable automatic pageview tracking', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          track_pageview: false,
        })
      );
    });

    it('should use localStorage for persistence', () => {
      process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token-123';

      render(
        <AnalyticsProvider>
          <div>Test Child</div>
        </AnalyticsProvider>
      );

      expect(mockMixpanel.init).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          persistence: 'localStorage',
        })
      );
    });
  });
});
