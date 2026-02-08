import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

/**
 * Browser Supabase client using @supabase/ssr for proper cookie handling.
 * This ensures cookies are compatible with the middleware for SSR auth.
 *
 * Uses 'pkce' flow for secure OAuth authentication (recommended for production).
 * PKCE (Proof Key for Code Exchange) is more secure than implicit flow and
 * properly handles OAuth providers like Google, which return authorization codes.
 */
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    flowType: "pkce",
  },
});
