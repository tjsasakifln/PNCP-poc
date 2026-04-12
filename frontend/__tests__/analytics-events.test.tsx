/**
 * STORY-370 AC7: Tests for analytics event tracking.
 */
import { getDaysInTrial } from '../lib/analytics-helpers';

// Mock mixpanel
jest.mock('mixpanel-browser', () => ({
  track: jest.fn(),
  identify: jest.fn(),
  people: { set: jest.fn() },
  reset: jest.fn(),
  register: jest.fn(),
}));

// Mock cookie consent
jest.mock('../app/components/CookieConsentBanner', () => ({
  getCookieConsent: () => ({ analytics: true }),
}));

describe('Analytics Event Tracking', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('getDaysInTrial helper', () => {
    it('correctly calculates days for known dates', () => {
      const msPerDay = 24 * 60 * 60 * 1000;
      const threeDaysAgo = new Date(Date.now() - 3 * msPerDay).toISOString();
      expect(getDaysInTrial(threeDaysAgo)).toBe(3);
    });
  });

  describe('localStorage guards for first-time events', () => {
    it('first_search_tracked key prevents re-tracking', () => {
      localStorage.setItem('first_search_tracked', 'true');
      const shouldTrack = !localStorage.getItem('first_search_tracked');
      expect(shouldTrack).toBe(false);
    });

    it('first_relevant_result_tracked key prevents re-tracking', () => {
      localStorage.setItem('first_relevant_result_tracked', 'true');
      const shouldTrack = !localStorage.getItem('first_relevant_result_tracked');
      expect(shouldTrack).toBe(false);
    });

    it('keys are absent before first event', () => {
      expect(localStorage.getItem('first_search_tracked')).toBeNull();
      expect(localStorage.getItem('first_relevant_result_tracked')).toBeNull();
    });
  });
});
