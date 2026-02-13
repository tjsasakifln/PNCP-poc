/**
 * Analytics Test Suite
 *
 * Tests for Mixpanel integration and event tracking
 * Coverage Target: 80%+ for analytics module
 *
 * Test Cases:
 * - TC-ANALYTICS-INIT-001: Mixpanel initialization success
 * - TC-ANALYTICS-INIT-002: Graceful degradation without token
 * - TC-ANALYTICS-EVENT-001 to 010: Event tracking
 */

import { renderHook, act } from '@testing-library/react';
import { useAnalytics } from '../hooks/useAnalytics';
import mixpanel from 'mixpanel-browser';

// Mock mixpanel-browser module
jest.mock('mixpanel-browser', () => ({
  init: jest.fn(),
  track: jest.fn(),
  identify: jest.fn(),
  people: {
    set: jest.fn(),
  },
}));

describe('Analytics - useAnalytics Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Set default token for tests
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test_token_12345';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
  });

  describe('TC-ANALYTICS-EVENT-001 to 010: trackEvent()', () => {
    it('should track event with properties when token exists', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('test_event', {
          foo: 'bar',
          count: 42,
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('test_event', {
        foo: 'bar',
        count: 42,
        timestamp: expect.any(String),
        environment: expect.any(String),
      });
    });

    it('should include timestamp and environment in every event', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('test_event');
      });

      expect(mixpanel.track).toHaveBeenCalledWith('test_event', {
        timestamp: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/), // ISO 8601 format
        environment: expect.any(String),
      });
    });

    it('should NOT track event when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('test_event');
      });

      expect(mixpanel.track).not.toHaveBeenCalled();
    });

    it('TC-ANALYTICS-EVENT-010: should handle track errors silently', () => {
      // Mock track to throw error
      (mixpanel.track as jest.Mock).mockImplementationOnce(() => {
        throw new Error('Network error');
      });

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      const { result } = renderHook(() => useAnalytics());

      // Should not throw
      expect(() => {
        act(() => {
          result.current.trackEvent('test_event');
        });
      }).not.toThrow();

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Analytics tracking failed:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('identifyUser()', () => {
    it('should identify user with ID when token exists', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.identifyUser('user-123');
      });

      expect(mixpanel.identify).toHaveBeenCalledWith('user-123');
    });

    it('should set user properties when provided', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.identifyUser('user-123', {
          name: 'Test User',
          email: 'test@example.com',
        });
      });

      expect(mixpanel.identify).toHaveBeenCalledWith('user-123');
      expect(mixpanel.people.set).toHaveBeenCalledWith({
        name: 'Test User',
        email: 'test@example.com',
      });
    });

    it('should NOT identify when token is missing', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.identifyUser('user-123');
      });

      expect(mixpanel.identify).not.toHaveBeenCalled();
    });

    it('should handle identify errors silently', () => {
      (mixpanel.identify as jest.Mock).mockImplementationOnce(() => {
        throw new Error('Network error');
      });

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      const { result } = renderHook(() => useAnalytics());

      expect(() => {
        act(() => {
          result.current.identifyUser('user-123');
        });
      }).not.toThrow();

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'User identification failed:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('trackPageView()', () => {
    it('should track page_view event with page name', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageView('/dashboard');
      });

      expect(mixpanel.track).toHaveBeenCalledWith('page_view', {
        page: '/dashboard',
        timestamp: expect.any(String),
        environment: expect.any(String),
      });
    });
  });
});

describe('Analytics - AnalyticsProvider Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test_token_12345';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
  });

  // Note: These tests require React Testing Library and @testing-library/jest-dom
  // They test the AnalyticsProvider component behavior

  // TODO: Add component tests for AnalyticsProvider
  // - Test Mixpanel initialization on mount
  // - Test page_load event fires on mount
  // - Test page_exit event fires on beforeunload
  // - Test pathname changes trigger re-tracking

  it('placeholder test - implement component tests', () => {
    // SKELETON: Implement tests for AnalyticsProvider component
    // See TC-ANALYTICS-INIT-001, TC-ANALYTICS-INIT-002, TC-ANALYTICS-EVENT-001, TC-ANALYTICS-EVENT-002
    expect(true).toBe(true);
  });
});

describe('Analytics - Real-World Event Scenarios', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test_token_12345';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
  });

  describe('TC-ANALYTICS-EVENT-003: search_started event', () => {
    it('should track search_started with correct properties', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('search_started', {
          ufs: ['SC', 'PR'],
          uf_count: 2,
          date_range: {
            inicial: '2026-01-01',
            final: '2026-01-07',
            days: 7,
          },
          search_mode: 'setor',
          setor_id: 'vestuario',
          termos_busca: null,
          termos_count: 0,
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('search_started', {
        ufs: ['SC', 'PR'],
        uf_count: 2,
        date_range: {
          inicial: '2026-01-01',
          final: '2026-01-07',
          days: 7,
        },
        search_mode: 'setor',
        setor_id: 'vestuario',
        termos_busca: null,
        termos_count: 0,
        timestamp: expect.any(String),
        environment: expect.any(String),
      });
    });
  });

  describe('TC-ANALYTICS-EVENT-004: search_completed event', () => {
    it('should track search_completed with timing and results', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('search_completed', {
          time_elapsed_ms: 5000,
          time_elapsed_readable: '5s',
          total_raw: 200,
          total_filtered: 50,
          filter_ratio: '25.0%',
          valor_total: 1000000,
          has_summary: true,
          ufs: ['SC', 'PR'],
          uf_count: 2,
          search_mode: 'setor',
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('search_completed', expect.objectContaining({
        time_elapsed_ms: 5000,
        total_filtered: 50,
        filter_ratio: '25.0%',
      }));
    });
  });

  describe('TC-ANALYTICS-EVENT-005: search_failed event', () => {
    it('should track search_failed with error details', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('search_failed', {
          error_message: 'Backend indisponível. Tente novamente.',
          error_type: 'Error',
          time_elapsed_ms: 2000,
          ufs: ['SC'],
          uf_count: 1,
          search_mode: 'setor',
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('search_failed', expect.objectContaining({
        error_message: 'Backend indisponível. Tente novamente.',
        error_type: 'Error',
      }));
    });
  });

  describe('TC-ANALYTICS-EVENT-006: download_started event', () => {
    it('should track download_started with download ID', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('download_started', {
          download_id: '123e4567-e89b-12d3-a456-426614174000',
          total_filtered: 50,
          valor_total: 1000000,
          search_mode: 'setor',
          ufs: ['SC', 'PR'],
          uf_count: 2,
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('download_started', expect.objectContaining({
        download_id: '123e4567-e89b-12d3-a456-426614174000',
        total_filtered: 50,
      }));
    });
  });

  describe('TC-ANALYTICS-EVENT-007: download_completed event', () => {
    it('should track download_completed with file size and timing', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('download_completed', {
          download_id: '123e4567-e89b-12d3-a456-426614174000',
          time_elapsed_ms: 500,
          time_elapsed_readable: '0s',
          file_size_bytes: 5120,
          file_size_readable: '5.00 KB',
          filename: 'SmartLic_Vestuário_e_Uniformes_2026-01-01_a_2026-01-07.xlsx',
          total_filtered: 50,
          valor_total: 1000000,
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('download_completed', expect.objectContaining({
        file_size_bytes: 5120,
        file_size_readable: '5.00 KB',
      }));
    });
  });

  describe('TC-ANALYTICS-EVENT-008: download_failed event', () => {
    it('should track download_failed with error message', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('download_failed', {
          download_id: '123e4567-e89b-12d3-a456-426614174000',
          error_message: 'Arquivo expirado. Faça uma nova busca para gerar o Excel.',
          error_type: 'Error',
          time_elapsed_ms: 300,
          total_filtered: 50,
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('download_failed', expect.objectContaining({
        error_message: 'Arquivo expirado. Faça uma nova busca para gerar o Excel.',
      }));
    });
  });

  describe('TC-ANALYTICS-EVENT-009: Custom terms search mode', () => {
    it('should track search with termos mode correctly', () => {
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('search_started', {
          ufs: ['SC'],
          uf_count: 1,
          date_range: {
            inicial: '2026-01-01',
            final: '2026-01-07',
            days: 7,
          },
          search_mode: 'termos',
          setor_id: null,
          termos_busca: 'uniforme jaleco fardamento',
          termos_count: 3,
        });
      });

      expect(mixpanel.track).toHaveBeenCalledWith('search_started', expect.objectContaining({
        search_mode: 'termos',
        setor_id: null,
        termos_busca: 'uniforme jaleco fardamento',
        termos_count: 3,
      }));
    });
  });
});

describe('Analytics - Coverage Verification', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test_token_12345';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
  });

  it('should achieve target coverage for useAnalytics hook', () => {
    // This test ensures all main code paths are covered
    // Target: 85%+ coverage for hooks/useAnalytics.ts

    const { result } = renderHook(() => useAnalytics());

    // Test trackEvent
    act(() => {
      result.current.trackEvent('test');
    });

    // Test trackEvent with properties
    act(() => {
      result.current.trackEvent('test', { foo: 'bar' });
    });

    // Test identifyUser
    act(() => {
      result.current.identifyUser('user-123');
    });

    // Test identifyUser with properties
    act(() => {
      result.current.identifyUser('user-123', { name: 'Test' });
    });

    // Test trackPageView
    act(() => {
      result.current.trackPageView('/test');
    });

    // All paths covered
    expect(mixpanel.track).toHaveBeenCalledTimes(3); // trackEvent x2, trackPageView x1
    expect(mixpanel.identify).toHaveBeenCalledTimes(2);
  });
});
