import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

/**
 * STORY-253 AC7: Server-side token refresh for API proxy routes.
 *
 * Gets a fresh access token by refreshing the session via Supabase server client.
 * Returns the access token string or null if no valid session.
 */
export async function getRefreshedToken(): Promise<string | null> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) return null;

  const cookieStore = await cookies();

  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        } catch {
          // Cannot set cookies in certain contexts — middleware handles it
        }
      },
    },
  });

  // Try getting user (validates token server-side)
  const { data: { user }, error } = await supabase.auth.getUser();

  if (user && !error) {
    // Token is still valid — get it from session
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  }

  // Token expired — attempt refresh
  const { data: { session: refreshed } } = await supabase.auth.refreshSession();
  return refreshed?.access_token || null;
}
