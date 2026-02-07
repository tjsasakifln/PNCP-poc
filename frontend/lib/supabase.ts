import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

/**
 * Browser Supabase client using @supabase/ssr for proper cookie handling.
 * This ensures cookies are compatible with the middleware for SSR auth.
 *
 * Uses 'implicit' flow to avoid PKCE issues with magic links opened in
 * different browsers/devices (code_verifier not found error).
 */
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    flowType: "implicit",
  },
});
