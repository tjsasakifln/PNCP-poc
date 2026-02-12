/**
 * Frontend Feature Flags and Configuration
 * 
 * Centralized configuration for feature toggles and environment-specific settings.
 * All feature flags use NEXT_PUBLIC_ prefix for client-side access.
 */

/**
 * Convert string to boolean with strict type safety
 * Accepts: 'true', '1', 'yes', 'on' (case-insensitive) as true
 * Everything else (including undefined) is false
 */
function stringToBoolean(value: string | undefined): boolean {
  if (!value) return false;
  return ['true', '1', 'yes', 'on'].includes(value.toLowerCase());
}

// ============================================
// Feature Flags
// ============================================

/**
 * FEATURE FLAG: New Pricing Model (STORY-165)
 *
 * Controls UI elements for plan-based capabilities:
 * - Plan badge display
 * - Locked Excel export button
 * - Date range validation
 * - Quota counter
 * - Upgrade modals
 *
 * Default: false (disabled for safety, gradual rollout)
 *
 * @example
 * ```tsx
 * import { ENABLE_NEW_PRICING } from '@/lib/config';
 *
 * {ENABLE_NEW_PRICING && <PlanBadge />}
 * ```
 */
export const ENABLE_NEW_PRICING: boolean = stringToBoolean(
  process.env.NEXT_PUBLIC_ENABLE_NEW_PRICING
);

/**
 * FEATURE FLAG: Advanced Analytics Dashboard
 *
 * Controls advanced analytics features:
 * - Time-series charts
 * - Top dimensions (UFs/Sectors)
 * - CSV export
 * - Extended metrics
 *
 * Default: true (stable feature)
 *
 * @example
 * ```tsx
 * import { ENABLE_ANALYTICS } from '@/lib/config';
 *
 * {ENABLE_ANALYTICS && <AdvancedCharts />}
 * ```
 */
export const ENABLE_ANALYTICS: boolean = stringToBoolean(
  process.env.NEXT_PUBLIC_ENABLE_ANALYTICS || 'true'
);

/**
 * FEATURE FLAG: Saved Searches
 *
 * Controls saved search functionality:
 * - Save search button
 * - Saved searches dropdown
 * - Search history persistence
 * - Load saved searches
 *
 * Default: true (stable feature)
 *
 * @example
 * ```tsx
 * import { ENABLE_SAVED_SEARCHES } from '@/lib/config';
 *
 * {ENABLE_SAVED_SEARCHES && <SaveSearchButton />}
 * ```
 */
export const ENABLE_SAVED_SEARCHES: boolean = stringToBoolean(
  process.env.NEXT_PUBLIC_ENABLE_SAVED_SEARCHES || 'true'
);

/**
 * FEATURE FLAG: Dark Mode
 *
 * Controls theme switching functionality:
 * - Theme toggle in header
 * - System preference detection
 * - Theme persistence
 * - Dark mode styles
 *
 * Default: true (stable feature)
 *
 * @example
 * ```tsx
 * import { ENABLE_DARK_MODE } from '@/lib/config';
 *
 * {ENABLE_DARK_MODE && <ThemeToggle />}
 * ```
 */
export const ENABLE_DARK_MODE: boolean = stringToBoolean(
  process.env.NEXT_PUBLIC_ENABLE_DARK_MODE || 'true'
);

/**
 * FEATURE FLAG: Real-time Search Progress (SSE)
 *
 * Controls server-sent events for search progress:
 * - Live progress updates during search
 * - Per-UF progress tracking
 * - Fallback to simulated progress
 *
 * Default: true (stable feature)
 *
 * @example
 * ```tsx
 * import { ENABLE_SSE_PROGRESS } from '@/lib/config';
 *
 * if (ENABLE_SSE_PROGRESS) {
 *   connectToProgressStream(searchId);
 * }
 * ```
 */
export const ENABLE_SSE_PROGRESS: boolean = stringToBoolean(
  process.env.NEXT_PUBLIC_ENABLE_SSE_PROGRESS || 'true'
);

// Log feature flag state (only in development)
if (process.env.NODE_ENV === 'development') {
  console.log('[Config] Feature Flags:', {
    ENABLE_NEW_PRICING,
    ENABLE_ANALYTICS,
    ENABLE_SAVED_SEARCHES,
    ENABLE_DARK_MODE,
    ENABLE_SSE_PROGRESS,
  });
}

// ============================================
// Environment Configuration
// ============================================

export const config = {
  /**
   * Backend API base URL
   * Must be set via NEXT_PUBLIC_API_URL environment variable
   * No localhost fallback to prevent local network access prompts in production
   */
  apiUrl: process.env.NEXT_PUBLIC_API_URL || '',

  /**
   * Supabase configuration (public keys only)
   */
  supabase: {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  },

  /**
   * Analytics
   */
  mixpanel: {
    token: process.env.NEXT_PUBLIC_MIXPANEL_TOKEN || '',
  },

  /**
   * Branding (white-label configuration)
   */
  branding: {
    appName: process.env.NEXT_PUBLIC_APP_NAME || 'SmartLic.tech',
    logoUrl: process.env.NEXT_PUBLIC_LOGO_URL || '/logo.svg',
  },
} as const;

// Type-safe config access
export type Config = typeof config;
