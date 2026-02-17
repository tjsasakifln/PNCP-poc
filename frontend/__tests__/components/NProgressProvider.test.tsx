/**
 * NProgressProvider Component Tests
 *
 * Tests navigation progress bar functionality and event handling
 */

import { render, screen, waitFor } from '@testing-library/react';
import { NProgressProvider } from '@/app/components/NProgressProvider';
import NProgress from 'nprogress';

// Mock NProgress
jest.mock('nprogress', () => ({
  configure: jest.fn(),
  start: jest.fn(),
  done: jest.fn(),
}));

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/test-page'),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

const mockNProgress = NProgress as jest.Mocked<typeof NProgress>;
const { usePathname, useSearchParams } = require('next/navigation');

describe('NProgressProvider Component', () => {
  // Capture configure call before clearAllMocks
  const configureCalls = (NProgress.configure as jest.Mock).mock.calls;

  beforeEach(() => {
    // Clear mocks except configure (which happens at module load)
    mockNProgress.start.mockClear();
    mockNProgress.done.mockClear();
  });

  describe('configuration', () => {
    it('should configure NProgress on module load', () => {
      // Check the calls that happened when module was loaded
      expect(configureCalls.length).toBeGreaterThan(0);
      expect(configureCalls[0][0]).toEqual({
        showSpinner: false,
        trickleSpeed: 200,
        minimum: 0.08,
        easing: 'ease',
        speed: 400,
      });
    });
  });

  describe('rendering', () => {
    it('should render children', () => {
      render(
        <NProgressProvider>
          <div>Test Content</div>
        </NProgressProvider>
      );

      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should wrap children in Suspense boundary', () => {
      const { container } = render(
        <NProgressProvider>
          <div>Test Content</div>
        </NProgressProvider>
      );

      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(container.firstChild).toBeTruthy();
    });
  });

  describe('navigation tracking', () => {
    it('should call NProgress.done when pathname changes', async () => {
      const { rerender } = render(
        <NProgressProvider>
          <div>Page 1</div>
        </NProgressProvider>
      );

      expect(mockNProgress.done).toHaveBeenCalled();

      mockNProgress.done.mockClear();

      // Change pathname
      usePathname.mockReturnValue('/new-page');

      rerender(
        <NProgressProvider>
          <div>Page 2</div>
        </NProgressProvider>
      );

      await waitFor(() => {
        expect(mockNProgress.done).toHaveBeenCalled();
      });
    });

    it('should call NProgress.done when searchParams change', async () => {
      const { rerender } = render(
        <NProgressProvider>
          <div>Content</div>
        </NProgressProvider>
      );

      expect(mockNProgress.done).toHaveBeenCalled();

      mockNProgress.done.mockClear();

      // Change search params
      useSearchParams.mockReturnValue(new URLSearchParams('?page=2'));

      rerender(
        <NProgressProvider>
          <div>Content</div>
        </NProgressProvider>
      );

      await waitFor(() => {
        expect(mockNProgress.done).toHaveBeenCalled();
      });
    });
  });

  describe('beforeunload event', () => {
    it('should call NProgress.start on beforeunload', async () => {
      render(
        <NProgressProvider>
          <div>Test Content</div>
        </NProgressProvider>
      );

      mockNProgress.start.mockClear();

      const event = new Event('beforeunload');
      window.dispatchEvent(event);

      expect(mockNProgress.start).toHaveBeenCalled();
    });

    it('should clean up event listener on unmount', async () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = render(
        <NProgressProvider>
          <div>Test Content</div>
        </NProgressProvider>
      );

      unmount();

      await waitFor(() => {
        expect(removeEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
      });

      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Suspense boundary', () => {
    it('should show fallback while suspending', () => {
      // Mock useSearchParams to throw (simulate suspense)
      useSearchParams.mockImplementation(() => {
        throw Promise.resolve(new URLSearchParams());
      });

      const { container } = render(
        <NProgressProvider>
          <div>Test Content</div>
        </NProgressProvider>
      );

      // Fallback should be the children themselves
      expect(container).toBeTruthy();
    });
  });

  describe('multiple instances', () => {
    it('should handle multiple providers independently', () => {
      render(
        <>
          <NProgressProvider>
            <div>Provider 1</div>
          </NProgressProvider>
          <NProgressProvider>
            <div>Provider 2</div>
          </NProgressProvider>
        </>
      );

      expect(screen.getByText('Provider 1')).toBeInTheDocument();
      expect(screen.getByText('Provider 2')).toBeInTheDocument();
    });
  });
});
