/**
 * useFeatureFlags Hook Tests
 *
 * STORY-171 AC7: Testes Unitários - Frontend
 * Tests feature flags hook with caching and SWR-like behavior
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { useFeatureFlags } from '@/hooks/useFeatureFlags';

// Mock fetch
global.fetch = jest.fn();

// Track test number to advance system time past cache TTL between tests
let testTimeOffset = 0;
const CACHE_TTL = 5 * 60 * 1000 + 1000; // 5min + 1s buffer

describe('useFeatureFlags Hook', () => {
  const mockFeaturesData = {
    features: ['early_access', 'proactive_search'],
    plan_id: 'consultor_agil',
    billing_period: 'annual' as const,
    cached_at: '2026-02-07T00:00:00Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Advance system time past cache TTL to ensure cache misses
    testTimeOffset += CACHE_TTL;
    jest.useFakeTimers({ now: new Date(Date.now() + testTimeOffset) });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Initial Load', () => {
    it('should start with loading state', () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      expect(result.current.isLoading).toBe(true);
      expect(result.current.features).toEqual([]);
    });

    it('should fetch features on mount', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/features/me',
        expect.objectContaining({
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        })
      );
    });

    it('should set features data after successful fetch', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.features).toEqual(['early_access', 'proactive_search']);
      expect(result.current.planId).toBe('consultor_agil');
      expect(result.current.billingPeriod).toBe('annual');
      expect(result.current.isError).toBe(false);
    });

    it('should handle fetch errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBeTruthy();
      expect(result.current.features).toEqual([]);
    });

    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isError).toBe(true);
      expect(result.current.error?.message).toBe('Network error');
    });
  });

  describe('hasFeature Helper', () => {
    it('should return true when feature is in features array', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.hasFeature('early_access')).toBe(true);
      expect(result.current.hasFeature('proactive_search')).toBe(true);
    });

    it('should return false when feature is not in features array', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.hasFeature('ai_edital_analysis')).toBe(false);
      expect(result.current.hasFeature('nonexistent_feature')).toBe(false);
    });

    it('should return false when data is not loaded', () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      expect(result.current.hasFeature('early_access')).toBe(false);
    });

    it('should return false when error occurred', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Error'));

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.hasFeature('early_access')).toBe(false);
    });
  });

  describe('Refresh Method', () => {
    it('should refetch features when refresh is called', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockFeaturesData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            ...mockFeaturesData,
            features: ['early_access', 'proactive_search', 'ai_edital_analysis'],
          }),
        });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.features).toHaveLength(2);

      // Refresh
      await act(async () => {
        await result.current.refresh();
      });

      await waitFor(() => {
        expect(result.current.features).toHaveLength(3);
      });

      expect(result.current.features).toContain('ai_edital_analysis');
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('should set loading state during refresh', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockFeaturesData,
        })
        .mockImplementationOnce(
          () =>
            new Promise((resolve) => {
              setTimeout(() => {
                resolve({
                  ok: true,
                  json: async () => mockFeaturesData,
                });
              }, 100);
            })
        );

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.refresh();
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should handle errors during refresh', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockFeaturesData,
        })
        .mockRejectedValueOnce(new Error('Refresh failed'));

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.refresh();
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Refresh failed');
    });
  });

  describe('Mutate Method (Optimistic UI)', () => {
    it('should update data optimistically with new data', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const newData = {
        features: ['early_access', 'proactive_search', 'ai_edital_analysis'],
        plan_id: 'sala_guerra',
        billing_period: 'annual' as const,
      };

      act(() => {
        result.current.mutate(newData, false); // Don't revalidate
      });

      expect(result.current.features).toEqual(newData.features);
      expect(result.current.planId).toBe('sala_guerra');
      expect(result.current.hasFeature('ai_edital_analysis')).toBe(true);
    });

    it('should support function updater', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.mutate(
          (prev) => ({
            ...prev!,
            features: [...prev!.features, 'new_feature'],
          }),
          false
        );
      });

      expect(result.current.features).toContain('new_feature');
      expect(result.current.features).toHaveLength(3);
    });

    it('should revalidate when revalidate is true', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockFeaturesData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            ...mockFeaturesData,
            features: ['server_feature'],
          }),
        });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.mutate(
          {
            features: ['optimistic_feature'],
            plan_id: 'test',
            billing_period: 'annual' as const,
          },
          true // Revalidate
        );
      });

      // Initially optimistic
      expect(result.current.features).toEqual(['optimistic_feature']);

      // Wait for revalidation
      await waitFor(() => {
        expect(result.current.features).toEqual(['server_feature']);
      });

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('should not revalidate when revalidate is false', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeaturesData,
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.mutate(
          {
            features: ['optimistic_feature'],
            plan_id: 'test',
            billing_period: 'monthly' as const,
          },
          false // Don't revalidate
        );
      });

      expect(result.current.features).toEqual(['optimistic_feature']);
      expect(global.fetch).toHaveBeenCalledTimes(1); // Only initial fetch
    });
  });

  describe('Empty/Null Data Handling', () => {
    it('should handle empty features array', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          features: [],
          plan_id: null,
          billing_period: null,
        }),
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.features).toEqual([]);
      expect(result.current.planId).toBeNull();
      expect(result.current.billingPeriod).toBeNull();
      expect(result.current.hasFeature('any_feature')).toBe(false);
    });

    it('should handle null plan_id and billing_period', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          features: ['early_access'],
          plan_id: null,
          billing_period: null,
        }),
      });

      const { result } = renderHook(() => useFeatureFlags());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.planId).toBeNull();
      expect(result.current.billingPeriod).toBeNull();
      expect(result.current.features).toEqual(['early_access']);
    });
  });

  describe('Cleanup', () => {
    it('should not update state after unmount', async () => {
      let resolvePromise: any;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      (global.fetch as jest.Mock).mockReturnValueOnce(promise);

      const { result, unmount } = renderHook(() => useFeatureFlags());

      expect(result.current.isLoading).toBe(true);

      unmount();

      // Resolve after unmount
      resolvePromise({
        ok: true,
        json: async () => mockFeaturesData,
      });

      await act(async () => {
        await promise;
      });

      // Should not crash or show warnings
    });
  });
});
