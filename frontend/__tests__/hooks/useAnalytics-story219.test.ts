/**
 * STORY-219 Analytics Tests
 *
 * AC28: identifyUser called after successful login (mock Mixpanel)
 * AC29: trackEvent called with correct properties for checkout events
 * AC30: UTM params captured from URL and included in events
 */

import { renderHook } from '@testing-library/react';
import { useAnalytics, captureUTMParams, getStoredUTMParams } from '../../hooks/useAnalytics';
import mixpanel from 'mixpanel-browser';

// Mock mixpanel-browser
jest.mock('mixpanel-browser', () => ({
  track: jest.fn(),
  identify: jest.fn(),
  reset: jest.fn(),
  register: jest.fn(),
  people: {
    set: jest.fn(),
  },
}));

// Mock CookieConsentBanner to always grant consent
jest.mock('../../app/components/CookieConsentBanner', () => ({
  getCookieConsent: () => ({ analytics: true }),
}));

describe('STORY-219: Analytics Activation', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env = { ...originalEnv };
    process.env.NEXT_PUBLIC_MIXPANEL_TOKEN = 'test-token';
    process.env.NODE_ENV = 'test';
    // Clear sessionStorage
    sessionStorage.clear();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  // AC28: identifyUser called after successful login
  describe('AC28: identifyUser after login', () => {
    it('should call mixpanel.identify with userId', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('user-abc-123');

      expect(mixpanel.identify).toHaveBeenCalledWith('user-abc-123');
    });

    it('should set user properties (plan_type, signup_date, signup_method)', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('user-abc-123', {
        plan_type: 'free_trial',
        signup_date: '2026-01-15T10:00:00Z',
        signup_method: 'email',
      });

      expect(mixpanel.identify).toHaveBeenCalledWith('user-abc-123');
      expect(mixpanel.people.set).toHaveBeenCalledWith({
        plan_type: 'free_trial',
        signup_date: '2026-01-15T10:00:00Z',
        signup_method: 'email',
      });
    });

    it('should set Google OAuth properties for OAuth callback', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('user-google-456', {
        plan_type: 'unknown',
        signup_method: 'google',
        signup_date: '2026-02-01T12:00:00Z',
      });

      expect(mixpanel.identify).toHaveBeenCalledWith('user-google-456');
      expect(mixpanel.people.set).toHaveBeenCalledWith(
        expect.objectContaining({ signup_method: 'google' })
      );
    });

    it('should not identify when consent is missing (token absent)', () => {
      delete process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
      const { result } = renderHook(() => useAnalytics());

      result.current.identifyUser('user-123');

      expect(mixpanel.identify).not.toHaveBeenCalled();
    });
  });

  // AC11: resetUser on logout
  describe('AC11: resetUser on logout', () => {
    it('should call mixpanel.reset()', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.resetUser();

      expect(mixpanel.reset).toHaveBeenCalledTimes(1);
    });

    it('should handle reset errors gracefully', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      (mixpanel.reset as jest.Mock).mockImplementationOnce(() => {
        throw new Error('Reset failed');
      });

      const { result } = renderHook(() => useAnalytics());

      expect(() => result.current.resetUser()).not.toThrow();
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Mixpanel reset failed:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  // AC29: trackEvent for checkout events
  describe('AC29: Checkout event tracking', () => {
    it('should track checkout_initiated with plan_id and billing_period', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('checkout_initiated', {
        plan_id: 'maquina',
        billing_period: 'monthly',
        source: 'planos_page',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('checkout_initiated', {
        plan_id: 'maquina',
        billing_period: 'monthly',
        source: 'planos_page',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track checkout_completed with plan_id', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('checkout_completed', {
        plan_id: 'sala_guerra',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('checkout_completed', {
        plan_id: 'sala_guerra',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track checkout_failed with error details', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('checkout_failed', {
        plan_id: 'consultor_agil',
        billing_period: 'annual',
        error: 'Stripe timeout',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('checkout_failed', {
        plan_id: 'consultor_agil',
        billing_period: 'annual',
        error: 'Stripe timeout',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track upgrade_modal_opened with source', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('upgrade_modal_opened', {
        source: 'excel_button',
        pre_selected_plan: 'maquina',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('upgrade_modal_opened', {
        source: 'excel_button',
        pre_selected_plan: 'maquina',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track upgrade_modal_plan_clicked with plan_id', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('upgrade_modal_plan_clicked', {
        plan_id: 'sala_guerra',
        source: 'quota_counter',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('upgrade_modal_plan_clicked', {
        plan_id: 'sala_guerra',
        source: 'quota_counter',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track login_attempted with method', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('login_attempted', { method: 'email' });

      expect(mixpanel.track).toHaveBeenCalledWith('login_attempted', {
        method: 'email',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track signup_completed with method', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('signup_completed', {
        method: 'email',
        utm_source: 'google',
        utm_campaign: 'launch2026',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('signup_completed', {
        method: 'email',
        utm_source: 'google',
        utm_campaign: 'launch2026',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });

    it('should track error_encountered with error details', () => {
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('error_encountered', {
        error_type: 'TypeError',
        error_message: 'Cannot read property',
        page: '/buscar',
      });

      expect(mixpanel.track).toHaveBeenCalledWith('error_encountered', {
        error_type: 'TypeError',
        error_message: 'Cannot read property',
        page: '/buscar',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });
  });

  // AC30: UTM parameter capture
  describe('AC30: UTM parameter capture', () => {
    it('should capture UTM params from URL and store in sessionStorage', () => {
      // Simulate URL with UTM params
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          ...window.location,
          search: '?utm_source=google&utm_medium=cpc&utm_campaign=launch2026',
        },
      });

      captureUTMParams();

      const stored = JSON.parse(sessionStorage.getItem('smartlic_utm_params') || '{}');
      expect(stored).toEqual({
        utm_source: 'google',
        utm_medium: 'cpc',
        utm_campaign: 'launch2026',
      });
    });

    it('should set UTM as Mixpanel super properties', () => {
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          ...window.location,
          search: '?utm_source=tiktok&utm_content=video1',
        },
      });

      captureUTMParams();

      expect(mixpanel.register).toHaveBeenCalledWith({
        utm_source: 'tiktok',
        utm_content: 'video1',
      });
    });

    it('should not store anything when no UTM params present', () => {
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          ...window.location,
          search: '',
        },
      });

      captureUTMParams();

      expect(sessionStorage.getItem('smartlic_utm_params')).toBeNull();
      expect(mixpanel.register).not.toHaveBeenCalled();
    });

    it('should capture all 5 UTM parameters', () => {
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          ...window.location,
          search: '?utm_source=src&utm_medium=med&utm_campaign=camp&utm_content=cont&utm_term=trm',
        },
      });

      captureUTMParams();

      const stored = JSON.parse(sessionStorage.getItem('smartlic_utm_params') || '{}');
      expect(stored).toEqual({
        utm_source: 'src',
        utm_medium: 'med',
        utm_campaign: 'camp',
        utm_content: 'cont',
        utm_term: 'trm',
      });
    });

    it('getStoredUTMParams should return stored UTM data', () => {
      sessionStorage.setItem('smartlic_utm_params', JSON.stringify({
        utm_source: 'newsletter',
        utm_medium: 'email',
      }));

      const params = getStoredUTMParams();
      expect(params).toEqual({
        utm_source: 'newsletter',
        utm_medium: 'email',
      });
    });

    it('getStoredUTMParams should return empty object when nothing stored', () => {
      const params = getStoredUTMParams();
      expect(params).toEqual({});
    });

    it('UTM params should be included in signup_completed event', () => {
      // Simulate stored UTM params
      sessionStorage.setItem('smartlic_utm_params', JSON.stringify({
        utm_source: 'google',
        utm_campaign: 'launch',
      }));

      const utmParams = getStoredUTMParams();
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('signup_completed', {
        method: 'email',
        ...utmParams,
      });

      expect(mixpanel.track).toHaveBeenCalledWith('signup_completed', {
        method: 'email',
        utm_source: 'google',
        utm_campaign: 'launch',
        timestamp: expect.any(String),
        environment: 'test',
      });
    });
  });
});
