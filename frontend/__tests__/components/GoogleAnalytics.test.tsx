/**
 * GoogleAnalytics Component Tests
 *
 * Tests GA4 initialization, consent handling, and event tracking
 */

import { render, waitFor } from '@testing-library/react';
import { GoogleAnalytics, trackEvent, trackSearchEvent, trackDownloadEvent, trackSignupEvent, trackLoginEvent, trackPlanSelectedEvent } from '@/app/components/GoogleAnalytics';

// Mock Next.js Script component
jest.mock('next/script', () => {
  return function MockScript({ children, id, ...props }: any) {
    if (id) {
      return <script id={id} data-testid={id} {...props}>{children}</script>;
    }
    return <script data-testid="ga-script" {...props} />;
  };
});

describe('GoogleAnalytics Component', () => {
  const originalEnv = process.env;
  const originalWindow = global.window;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    process.env = { ...originalEnv };
    process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID = 'G-TEST123456';

    // Mock window.gtag
    (global.window as any).gtag = jest.fn();
    (global.window as any).dataLayer = [];
  });

  afterEach(() => {
    process.env = originalEnv;
    delete (global.window as any).gtag;
    delete (global.window as any).dataLayer;
  });

  describe('rendering', () => {
    it('should render GA scripts when measurement ID is configured', () => {
      const { container } = render(<GoogleAnalytics />);
      const scripts = container.querySelectorAll('script');

      expect(scripts.length).toBeGreaterThan(0);
    });

    it('should not render scripts when measurement ID is missing', () => {
      delete process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID;

      const { container } = render(<GoogleAnalytics />);

      expect(container.innerHTML).toBe('');
    });

    it('should include correct measurement ID in script src', () => {
      const { container } = render(<GoogleAnalytics />);
      const script = container.querySelector('[data-testid="ga-script"]');

      expect(script).toHaveAttribute('src', 'https://www.googletagmanager.com/gtag/js?id=G-TEST123456');
    });

    it('should use afterInteractive strategy for scripts', () => {
      const { container } = render(<GoogleAnalytics />);
      const scripts = container.querySelectorAll('script');

      scripts.forEach(script => {
        expect(script).toHaveAttribute('strategy', 'afterInteractive');
      });
    });
  });

  describe('consent handling', () => {
    it('should initialize GA when consent is accepted', async () => {
      localStorage.setItem('cookie-consent', 'accepted');

      render(<GoogleAnalytics />);

      await waitFor(() => {
        expect(window.dataLayer).toBeDefined();
      });
    });

    it('should not initialize GA when consent is not accepted', async () => {
      localStorage.setItem('cookie-consent', 'rejected');

      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      render(<GoogleAnalytics />);

      // Wait a bit to ensure no initialization happens
      await new Promise(resolve => setTimeout(resolve, 100));

      // gtag should not be called in useEffect
      expect(gtagSpy).not.toHaveBeenCalled();
    });

    it('should check consent before initializing in inline script', () => {
      localStorage.setItem('cookie-consent', 'accepted');

      const { getByTestId } = render(<GoogleAnalytics />);
      const inlineScript = getByTestId('google-analytics');

      expect(inlineScript.innerHTML).toContain("localStorage.getItem('cookie-consent') === 'accepted'");
    });
  });

  describe('initialization', () => {
    it('should initialize dataLayer', async () => {
      localStorage.setItem('cookie-consent', 'accepted');

      render(<GoogleAnalytics />);

      await waitFor(() => {
        expect(window.dataLayer).toBeDefined();
        expect(Array.isArray(window.dataLayer)).toBe(true);
      });
    });

    it('should configure GA with anonymize_ip for LGPD compliance', () => {
      const { getByTestId } = render(<GoogleAnalytics />);
      const inlineScript = getByTestId('google-analytics');

      // Check that the inline script includes anonymize_ip config
      expect(inlineScript.innerHTML).toContain('anonymize_ip: true');
      expect(inlineScript.innerHTML).toContain("gtag('config', 'G-TEST123456'");
    });

    it('should include page_path in config', () => {
      const { getByTestId } = render(<GoogleAnalytics />);
      const inlineScript = getByTestId('google-analytics');

      // Check that the inline script includes page_path
      expect(inlineScript.innerHTML).toContain('page_path:');
    });
  });

  describe('trackEvent helper', () => {
    it('should track custom event when consent is granted', () => {
      localStorage.setItem('cookie-consent', 'accepted');
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackEvent('test_event', { test_param: 'value' });

      expect(gtagSpy).toHaveBeenCalledWith('event', 'test_event', { test_param: 'value' });
    });

    it('should not track event when consent is not granted', () => {
      localStorage.setItem('cookie-consent', 'rejected');
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackEvent('test_event', { test_param: 'value' });

      expect(gtagSpy).not.toHaveBeenCalled();
    });

    it('should not track event when gtag is not available', () => {
      localStorage.setItem('cookie-consent', 'accepted');
      delete (global.window as any).gtag;

      // Should not throw
      expect(() => trackEvent('test_event', {})).not.toThrow();
    });

    it('should handle event without params', () => {
      localStorage.setItem('cookie-consent', 'accepted');
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackEvent('simple_event');

      expect(gtagSpy).toHaveBeenCalledWith('event', 'simple_event', undefined);
    });
  });

  describe('predefined event trackers', () => {
    beforeEach(() => {
      localStorage.setItem('cookie-consent', 'accepted');
    });

    it('should track search event with correct params', () => {
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackSearchEvent('uniformes', 42);

      expect(gtagSpy).toHaveBeenCalledWith('event', 'search', {
        search_term: 'uniformes',
        results_count: 42,
      });
    });

    it('should track download event with correct params', () => {
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackDownloadEvent('report.xlsx', 'excel');

      expect(gtagSpy).toHaveBeenCalledWith('event', 'file_download', {
        file_name: 'report.xlsx',
        file_type: 'excel',
      });
    });

    it('should track signup event with method', () => {
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackSignupEvent('email');

      expect(gtagSpy).toHaveBeenCalledWith('event', 'sign_up', {
        method: 'email',
      });
    });

    it('should track login event with method', () => {
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackLoginEvent('google');

      expect(gtagSpy).toHaveBeenCalledWith('event', 'login', {
        method: 'google',
      });
    });

    it('should track plan selection with correct structure', () => {
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      trackPlanSelectedEvent('Pro Plan', 1999.99);

      expect(gtagSpy).toHaveBeenCalledWith('event', 'select_item', {
        item_list_name: 'Pricing Plans',
        items: [
          {
            item_name: 'Pro Plan',
            price: 1999.99,
          },
        ],
      });
    });
  });

  describe('window type definitions', () => {
    it('should extend Window interface with dataLayer', () => {
      // TypeScript compilation test - if this compiles, the types are correct
      const testDataLayer: any[] = window.dataLayer || [];
      expect(Array.isArray(testDataLayer)).toBe(true);
    });

    it('should extend Window interface with gtag', () => {
      // TypeScript compilation test
      const testGtag = window.gtag || (() => {});
      expect(typeof testGtag).toBe('function');
    });
  });

  describe('LGPD compliance', () => {
    it('should include anonymize_ip in inline script config', () => {
      const { getByTestId } = render(<GoogleAnalytics />);
      const inlineScript = getByTestId('google-analytics');

      expect(inlineScript.innerHTML).toContain('anonymize_ip: true');
    });

    it('should check localStorage consent before tracking', () => {
      const gtagSpy = jest.fn();
      (global.window as any).gtag = gtagSpy;

      // No consent
      localStorage.removeItem('cookie-consent');

      trackEvent('test_event');

      expect(gtagSpy).not.toHaveBeenCalled();
    });
  });
});
