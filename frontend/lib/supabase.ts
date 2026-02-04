import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

/**
 * Browser Supabase client using @supabase/ssr for proper cookie handling.
 * This ensures cookies are compatible with the middleware for SSR auth.
 *
 * Uses singleton pattern by default for consistent session state.
 */
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey);
