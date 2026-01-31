/**
 * useAnalytics Hook Tests
 *
 * Tests analytics tracking functionality with Mixpanel
 */

import { renderHook } from '@testing-library/react';
import { useAnalytics } from '@/hooks/useAnalytics';
import mixpanel from 'mixpanel-browser';

// Mock mixpanel-browser
jest.mock('mixpanel-browser', () => ({
  track: jest.fn(),
  identify: jest.fn(),
  people: {
    set: jest.fn(),
  },
}));

describe('useAnalytics Hook', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment
    process.env = { ...originalEnv };
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token';
    process.env.NODE_ENV = 'test';
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('trackEvent', () => {
    it('should track events with correct properties', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('search_executed', {
        uf_count: 3,
        sector: 'Uniformes',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('search_executed', {
        uf_count: 3,
        sector: 'Uniformes',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track events without additional properties', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('button_clicked');

      expect(mixpanel.track).toHaveBeenCalledWith('button_clicked', {
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should include timestamp in ISO format', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('test_event');

      const callArgs = (mixpanel.track as jest.Mock).mock.calls[0][1];
      const timestamp = callArgs.timestamp;

      // Verify it's a valid ISO timestamp
      expect(new Date(timestamp).toISOString()).toBe(timestamp);
    });

    it('should include environment from NODE_ENV', () => {
      process.env.NODE_ENV = 'production';
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('test_event');

      expect(mixpanel.track).toHaveBeenCalledWith('test_event', {
        timestamp: expect.any(String),
        environment: 'production',
      });
    });

    it('should default to development environment if NODE_ENV not set', () => {
      delete process.env.NODE_ENV;
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('test_event');

      expect(mixpanel.track).toHaveBeenCalledWith('test_event', {
        timestamp: expect.any(String),
        environment: 'development',
      });
    });

    it('should not track when Mixpanel token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('test_event');

      expect(mixpanel.track).not.toHaveBeenCalled();
    });

    it('should handle tracking errors gracefully', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      (mixpanel.track as jest.Mock).mockImplementationOnce(() => {
        throw new Error('Tracking failed');
      });

      const { result } = renderHook(() => useAnalytics());

      // Should not throw
      expect(() => {
        result.current.trackEvent('test_event');
      }).not.toThrow();

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Analytics tracking failed:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('trackPageView', () => {
    it('should track page views with correct format', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackPageView('Home');

      expect(mixpanel.track).toHaveBeenCalledWith('page_view', {
        page: 'Home',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track different page names', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackPageView('Search Results');
      result.current.trackPageView('About');

      expect(mixpanel.track).toHaveBeenCalledTimes(2);
      expect(mixpanel.track).toHaveBeenNthCalledWith(1, 'page_view', {
        page: 'Search Results',
        timestamp: expect.any(String),
        environment: 'test',
      });
      expect(mixpanel.track).toHaveBeenNthCalledWith(2, 'page_view', {
        page: 'About',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should not track page views when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
      const { result } = renderHook(() => useAnalytics());

      result.current.trackPageView('Home');

      expect(mixpanel.track).not.toHaveBeenCalled();
    });
  });

  describe('identifyUser', () => {
    it('should identify user with userId only', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('user-123');

      expect(mixpanel.identify).toHaveBeenCalledWith('user-123');
      expect(mixpanel.people.set).not.toHaveBeenCalled();
    });

    it('should identify user with properties', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('user-123', {
        email: 'user@example.com',
        name: 'Test User',
        role: 'admin',
      });

      expect(mixpanel.identify).toHaveBeenCalledWith('user-123');
      expect(mixpanel.people.set).toHaveBeenCalledWith({
        email: 'user@example.com',
        name: 'Test User',
        role: 'admin',
      });
    });

    it('should not identify user when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('user-123');

      expect(mixpanel.identify).not.toHaveBeenCalled();
      expect(mixpanel.people.set).not.toHaveBeenCalled();
    });

    it('should handle identification errors gracefully', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      (mixpanel.identify as jest.Mock).mockImplementationOnce(() => {
        throw new Error('Identification failed');
      });

      const { result } = renderHook(() => useAnalytics());

      // Should not throw
      expect(() => {
        result.current.identifyUser('user-123');
      }).not.toThrow();

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'User identification failed:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });

    it('should handle people.set errors gracefully', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      (mixpanel.people.set as jest.Mock).mockImplementationOnce(() => {
        throw new Error('Set properties failed');
      });

      const { result } = renderHook(() => useAnalytics());

      // Should not throw
      expect(() => {
        result.current.identifyUser('user-123', { name: 'Test' });
      }).not.toThrow();

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'User identification failed:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('Hook stability', () => {
    it('should work correctly across multiple renders', () => {
      const { result, rerender } = renderHook(() => useAnalytics());

      // First render
      result.current.trackEvent('event1');
      expect(mixpanel.track).toHaveBeenCalledWith('event1', expect.any(Object));

      // Rerender
      rerender();

      // Should still work after rerender
      result.current.trackEvent('event2');
      expect(mixpanel.track).toHaveBeenCalledWith('event2', expect.any(Object));
      expect(mixpanel.track).toHaveBeenCalledTimes(2);
    });
  });

  describe('Real-world scenarios', () => {
    it('should track search flow correctly', () => {
      const { result } = renderHook(() => useAnalytics());

      // User starts search
      result.current.trackEvent('search_started', {
        uf_count: 2,
        has_date_range: true,
      });

      // Search executes
      result.current.trackEvent('search_executed', {
        uf_count: 2,
        results_count: 42,
        execution_time_ms: 1234,
      });

      // User downloads results
      result.current.trackEvent('download_started', {
        format: 'excel',
        results_count: 42,
      });

      expect(mixpanel.track).toHaveBeenCalledTimes(3);
      expect(mixpanel.track).toHaveBeenNthCalledWith(1, 'search_started', expect.any(Object));
      expect(mixpanel.track).toHaveBeenNthCalledWith(2, 'search_executed', expect.any(Object));
      expect(mixpanel.track).toHaveBeenNthCalledWith(3, 'download_started', expect.any(Object));
    });

    it('should track multiple page views in session', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackPageView('Home');
      result.current.trackPageView('Search Results');
      result.current.trackPageView('Home');

      expect(mixpanel.track).toHaveBeenCalledTimes(3);
      // Verify all were page_view events
      (mixpanel.track as jest.Mock).mock.calls.forEach(call => {
        expect(call[0]).toBe('page_view');
      });
    });
  });

  describe('Edge cases', () => {
    it('should handle empty event name', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('');

      expect(mixpanel.track).toHaveBeenCalledWith('', expect.any(Object));
    });

    it('should handle empty user ID', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('');

      expect(mixpanel.identify).toHaveBeenCalledWith('');
    });

    it('should handle null properties gracefully', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('test_event', null as any);

      // Should still track with timestamp and environment
      expect(mixpanel.track).toHaveBeenCalledWith('test_event', {
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should handle undefined properties gracefully', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('test_event', undefined);

      expect(mixpanel.track).toHaveBeenCalledWith('test_event', {
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should handle complex nested properties', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('complex_event', {
        nested: {
          level1: {
            level2: 'value',
          },
        },
        array: [1, 2, 3],
        mixed: {
          string: 'test',
          number: 42,
          boolean: true,
        },
      });

      expect(mixpanel.track).toHaveBeenCalledWith('complex_event', {
        nested: {
          level1: {
            level2: 'value',
          },
        },
        array: [1, 2, 3],
        mixed: {
          string: 'test',
          number: 42,
          boolean: true,
        },
        timestamp: expect.any(String),
        environment: 'test',
      });
    });
  });
});
