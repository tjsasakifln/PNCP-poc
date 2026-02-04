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

// Log feature flag state (only in development)
if (process.env.NODE_ENV === 'development') {
  console.log('[Config] Feature Flags:', {
    ENABLE_NEW_PRICING,
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
    appName: process.env.NEXT_PUBLIC_APP_NAME || 'Smart PNCP',
    logoUrl: process.env.NEXT_PUBLIC_LOGO_URL || '/logo.svg',
  },
} as const;

// Type-safe config access
export type Config = typeof config;
