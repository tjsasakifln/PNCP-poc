"use client";

import { useState, useEffect, useCallback } from "react";

/**
 * useFeatureFlags Hook
 *
 * Fetches and caches user feature flags from backend
 * STORY-171 AC6: Feature Flags por Tipo de Plano
 *
 * Features:
 * - Client-side caching (5min TTL to match backend Redis)
 * - Manual revalidation with refresh()
 * - hasFeature() helper for conditional rendering
 * - Optimistic UI support via mutate()
 *
 * NOTE: This is a lightweight implementation. For production,
 * consider installing SWR: npm install swr
 */

interface FeatureFlagsData {
  features: string[];
  plan_id: string | null;
  billing_period: 'monthly' | 'annual' | null;
  cached_at?: string;
}

interface FeatureFlagsState {
  data: FeatureFlagsData | null;
  error: Error | null;
  isLoading: boolean;
}

// In-memory cache
const cache = new Map<string, { data: FeatureFlagsData; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes (matches backend Redis TTL)

export function useFeatureFlags() {
  const [state, setState] = useState<FeatureFlagsState>({
    data: null,
    error: null,
    isLoading: true,
  });

  // Fetch feature flags from API
  const fetchFeatures = useCallback(async (skipCache = false): Promise<FeatureFlagsData> => {
    const cacheKey = 'features:me';

    // Check cache first (unless explicitly skipping)
    if (!skipCache) {
      const cached = cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
      }
    }

    // Fetch from API
    const response = await fetch('/api/features/me', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Include cookies for authentication
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch features: ${response.statusText}`);
    }

    const data: FeatureFlagsData = await response.json();

    // Update cache
    cache.set(cacheKey, {
      data,
      timestamp: Date.now(),
    });

    return data;
  }, []);

  // Load features on mount
  useEffect(() => {
    let mounted = true;

    const loadFeatures = async () => {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        const data = await fetchFeatures();
        if (mounted) {
          setState({ data, error: null, isLoading: false });
        }
      } catch (error) {
        if (mounted) {
          setState({
            data: null,
            error: error instanceof Error ? error : new Error('Unknown error'),
            isLoading: false,
          });
        }
      }
    };

    loadFeatures();

    return () => {
      mounted = false;
    };
  }, [fetchFeatures]);

  // Refresh features (force cache bypass)
  const refresh = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      const data = await fetchFeatures(true); // Skip cache
      setState({ data, error: null, isLoading: false });
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error : new Error('Unknown error'),
        isLoading: false,
      }));
    }
  }, [fetchFeatures]);

  // Optimistic update (mutate)
  const mutate = useCallback((newData: FeatureFlagsData | ((prev: FeatureFlagsData | null) => FeatureFlagsData), revalidate = true) => {
    // Update state optimistically
    setState(prev => {
      const updatedData = typeof newData === 'function' ? newData(prev.data) : newData;

      // Update cache
      cache.set('features:me', {
        data: updatedData,
        timestamp: Date.now(),
      });

      return {
        ...prev,
        data: updatedData,
      };
    });

    // Optionally revalidate with server
    if (revalidate) {
      refresh();
    }
  }, [refresh]);

  // Helper: Check if user has a specific feature
  const hasFeature = useCallback((featureKey: string): boolean => {
    return state.data?.features.includes(featureKey) || false;
  }, [state.data]);

  return {
    // Data
    features: state.data?.features || [],
    planId: state.data?.plan_id || null,
    billingPeriod: state.data?.billing_period || null,

    // State
    isLoading: state.isLoading,
    isError: !!state.error,
    error: state.error,

    // Methods
    hasFeature,
    refresh,
    mutate,
  };
}
