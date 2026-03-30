"use client";

import { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../../lib/supabase";
import type { User, Session } from "@supabase/supabase-js";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAdmin: boolean;
  isAdminLoading: boolean;
  sessionExpired: boolean;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string, fullName?: string, company?: string, sector?: string, phoneWhatsApp?: string, whatsappConsent?: boolean) => Promise<void>;
  signInWithMagicLink: (email: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isAdminLoading, setIsAdminLoading] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);

  // UX-408 AC1: isMounted ref prevents setState after unmount
  const isMountedRef = useRef(true);

  // Fetch admin status when session changes
  const fetchAdminStatus = useCallback(async (accessToken: string) => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

    // Skip admin check if backend URL not configured (avoids localhost fallback in production)
    if (!backendUrl) {
      if (isMountedRef.current) {
        setIsAdmin(false);
        setIsAdminLoading(false);
      }
      return;
    }

    if (isMountedRef.current) setIsAdminLoading(true);
    try {
      const res = await fetch(`${backendUrl}/v1/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!isMountedRef.current) return; // UX-408 AC1
      if (res.ok) {
        const data = await res.json();
        setIsAdmin(data.is_admin === true);
      } else {
        setIsAdmin(false);
      }
    } catch {
      if (isMountedRef.current) setIsAdmin(false);
    } finally {
      if (isMountedRef.current) setIsAdminLoading(false);
    }
  }, []);

  useEffect(() => {
    const authTimeout = setTimeout(async () => {
      if (!isMountedRef.current) return; // UX-408 AC1
      if (process.env.NODE_ENV !== "production") console.warn("[AuthProvider] Auth check timeout — attempting session fallback");
      // AC5: On timeout, try getSession() which reads local cookies (fast, no network)
      try {
        const { data: { session: fallbackSession } } = await supabase.auth.getSession();
        if (!isMountedRef.current) return; // UX-408 AC1
        if (fallbackSession?.user) {
          if (process.env.NODE_ENV !== "production") console.info("[AuthProvider] Timeout fallback: using session data");
          setUser(fallbackSession.user);
          setSession(fallbackSession);
          setLoading(false);
          return;
        }
      } catch {
        // getSession also failed — give up
      }
      if (isMountedRef.current) setLoading(false);
    }, 3000);

    const initAuth = async () => {
      try {
        // Fast path: getSession() reads local JWT (~50ms, no network round-trip)
        const { data: { session: localSession } } = await supabase.auth.getSession();

        if (!isMountedRef.current) return; // UX-408 AC1

        if (localSession?.user) {
          // Render immediately with session data — user sees the page NOW
          clearTimeout(authTimeout);
          setUser(localSession.user);
          setSession(localSession);
          setLoading(false);

          // Background: upgrade to server-validated user (non-blocking)
          supabase.auth.getUser().then(({ data: { user: validatedUser } }) => {
            if (validatedUser && isMountedRef.current) setUser(validatedUser);
          }).catch(() => { /* keep session user as fallback */ });

          // Background: fetch admin status (non-blocking)
          if (localSession.access_token) {
            fetchAdminStatus(localSession.access_token);
          }
          return;
        }

        // No local session — fall back to server-validated getUser() for public pages / expired sessions
        const { data: { user: validatedUser }, error: userError } = await supabase.auth.getUser();

        if (!isMountedRef.current) return; // UX-408 AC1

        if (validatedUser) {
          clearTimeout(authTimeout);
          setUser(validatedUser);
          setLoading(false);
          const { data: { session: sess } } = await supabase.auth.getSession();
          if (!isMountedRef.current) return; // UX-408 AC1
          setSession(sess);
          if (sess?.access_token) {
            fetchAdminStatus(sess.access_token);
          }
          return;
        }

        // UX-408 AC2: AuthApiError from getUser() is expected on public pages — use warn, not error
        if (userError && process.env.NODE_ENV === "development") {
          console.warn("[AuthProvider] Sessão expirada, redirecionando para login.", userError.message);
        }

        // AC6: getUser returned null — try refreshing the session once
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        if (!isMountedRef.current) return; // UX-408 AC1
        if (currentSession) {
          if (process.env.NODE_ENV !== "production") console.info("[AuthProvider] getUser returned null, attempting session refresh (AC6)");
          const { data: { session: refreshedSession } } = await supabase.auth.refreshSession();

          if (!isMountedRef.current) return; // UX-408 AC1
          if (refreshedSession?.user) {
            clearTimeout(authTimeout);
            setUser(refreshedSession.user);
            setSession(refreshedSession);
            setLoading(false);
            if (refreshedSession.access_token) {
              fetchAdminStatus(refreshedSession.access_token);
            }
            return;
          }
        }

        // No valid user found
        clearTimeout(authTimeout);
        setUser(null);
        setSession(null);
        setLoading(false);
      } catch (error) {
        // UX-408 AC2+AC5: Use console.warn for auth errors (not console.error)
        if (process.env.NODE_ENV !== "production") console.warn("[AuthProvider] Sessão expirada, redirecionando para login.", error);

        if (!isMountedRef.current) return; // UX-408 AC1

        // AC5: error — fall back to session data
        try {
          const { data: { session: fallbackSession } } = await supabase.auth.getSession();
          if (!isMountedRef.current) return; // UX-408 AC1
          if (fallbackSession?.user) {
            if (process.env.NODE_ENV !== "production") console.info("[AuthProvider] Falling back to session data (AC5)");
            clearTimeout(authTimeout);
            setUser(fallbackSession.user);
            setSession(fallbackSession);
            setLoading(false);
            // Don't fetch admin status on fallback — keep isAdmin=false as safe default
            return;
          }
        } catch (sessionError) {
          if (process.env.NODE_ENV !== "production") console.warn("[AuthProvider] Session fallback also failed:", sessionError);
        }

        if (!isMountedRef.current) return; // UX-408 AC1
        clearTimeout(authTimeout);
        setUser(null);
        setSession(null);
        setLoading(false);
      }
    };

    initAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        if (!isMountedRef.current) return; // UX-408 AC1
        setSession(session);
        if (session?.user) {
          // Set user from session IMMEDIATELY so header updates without waiting
          setUser(session.user);
          setLoading(false);
          clearTimeout(authTimeout);
          if (session.access_token) {
            fetchAdminStatus(session.access_token);
          }
          // Background: validate user with server (non-blocking)
          supabase.auth.getUser().then(({ data: { user } }) => {
            if (user && isMountedRef.current) setUser(user); // Upgrade to validated user
          }).catch(() => { /* keep session user as fallback */ });
        } else {
          setUser(null);
          setIsAdmin(false);
          setLoading(false);
        }
      }
    );

    // STORY-253 AC1: Proactive token refresh every 10 minutes
    const REFRESH_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes
    const refreshInterval = setInterval(async () => {
      if (!isMountedRef.current) return; // UX-408 AC1
      try {
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        if (!currentSession || !isMountedRef.current) return;

        const { data: { session: refreshed }, error } =
          await supabase.auth.refreshSession();

        if (!isMountedRef.current) return; // UX-408 AC1
        if (error || !refreshed) {
          // AC3: Refresh failed — mark session as expired
          if (process.env.NODE_ENV === "development") {
            console.warn("[AuthProvider] Proactive refresh failed:", error?.message);
          }
          setSessionExpired(true);
        } else {
          // AC4: Log success in dev mode
          if (process.env.NODE_ENV === "development") {
            console.info("[AuthProvider] Proactive token refresh successful");
          }
          setSessionExpired(false);
        }
      } catch (err) {
        if (!isMountedRef.current) return; // UX-408 AC1
        if (process.env.NODE_ENV === "development") {
          console.warn("[AuthProvider] Proactive refresh error:", err);
        }
        setSessionExpired(true);
      }
    }, REFRESH_INTERVAL_MS);

    // AC2: Timer cleanup to prevent memory leaks
    // UX-408 AC1: Mark as unmounted so no setState fires after cleanup
    return () => {
      isMountedRef.current = false;
      clearTimeout(authTimeout);
      clearInterval(refreshInterval);
      subscription.unsubscribe();
    };
  }, [fetchAdminStatus]);

  const signInWithEmail = useCallback(async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  }, []);

  const signUpWithEmail = useCallback(async (
    email: string,
    password: string,
    fullName?: string,
    company?: string,
    sector?: string,
    phoneWhatsApp?: string,
    whatsappConsent?: boolean
  ) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          company: company,
          sector: sector,
          phone_whatsapp: phoneWhatsApp,
          whatsapp_consent: whatsappConsent,
        },
      },
    });
    if (error) throw error;
  }, []);

  const signInWithMagicLink = useCallback(async (email: string) => {
    // Use canonical URL for OAuth redirects (not railway.app domain)
    const canonicalUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || window.location.origin;
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${canonicalUrl}/auth/callback`,
      },
    });
    if (error) throw error;
  }, []);

  const signInWithGoogle = useCallback(async () => {
    // Use canonical URL for OAuth redirects (not railway.app domain)
    const canonicalUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || window.location.origin;
    const redirectUrl = `${canonicalUrl}/auth/callback`;

    if (process.env.NODE_ENV === "development") {
      console.log("[AuthProvider] Google OAuth Login Starting");
      console.log("[AuthProvider] NEXT_PUBLIC_CANONICAL_URL:", process.env.NEXT_PUBLIC_CANONICAL_URL);
      console.log("[AuthProvider] window.location.origin:", window.location.origin);
      console.log("[AuthProvider] Final redirect URL:", redirectUrl);
    }

    // CRITICAL FIX: Force consent screen to avoid session conflicts in logged-in browsers
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: redirectUrl,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent', // Force new consent, ignore existing Google session
        },
      },
    });
    if (error) {
      if (process.env.NODE_ENV !== "production") console.error("[AuthProvider] Google OAuth error:", error);
      throw error;
    }
    if (process.env.NODE_ENV !== "production") console.log("[AuthProvider] OAuth redirect initiated");
  }, []);

  const signOut = useCallback(async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    // Redirect to home page after logout
    router.push("/");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        isAdmin,
        isAdminLoading,
        sessionExpired,
        signInWithEmail,
        signUpWithEmail,
        signInWithMagicLink,
        signInWithGoogle,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
