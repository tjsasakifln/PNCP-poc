"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../../lib/supabase";
import type { User, Session } from "@supabase/supabase-js";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAdmin: boolean;
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

  // Fetch admin status when session changes
  const fetchAdminStatus = useCallback(async (accessToken: string) => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

    // Skip admin check if backend URL not configured (avoids localhost fallback in production)
    if (!backendUrl) {
      setIsAdmin(false);
      return;
    }

    try {
      const res = await fetch(`${backendUrl}/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setIsAdmin(data.is_admin === true);
      } else {
        setIsAdmin(false);
      }
    } catch {
      setIsAdmin(false);
    }
  }, []);

  useEffect(() => {
    const authTimeout = setTimeout(async () => {
      console.warn("[AuthProvider] Auth check timeout — attempting session fallback");
      // AC5: On timeout, try getSession() which reads local cookies (fast, no network)
      try {
        const { data: { session: fallbackSession } } = await supabase.auth.getSession();
        if (fallbackSession?.user) {
          console.info("[AuthProvider] Timeout fallback: using session data");
          setUser(fallbackSession.user);
          setSession(fallbackSession);
          setLoading(false);
          return;
        }
      } catch {
        // getSession also failed — give up
      }
      setLoading(false);
    }, 10000);

    const initAuth = async () => {
      try {
        // Primary: server-validated user
        const { data: { user: validatedUser }, error: userError } = await supabase.auth.getUser();

        if (validatedUser) {
          clearTimeout(authTimeout);
          setUser(validatedUser);
          setLoading(false);
          const { data: { session: sess } } = await supabase.auth.getSession();
          setSession(sess);
          if (sess?.access_token) {
            fetchAdminStatus(sess.access_token);
          }
          return;
        }

        // AC6: getUser returned null — try refreshing the session once
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        if (currentSession) {
          console.info("[AuthProvider] getUser returned null, attempting session refresh (AC6)");
          const { data: { session: refreshedSession }, error: refreshError } = await supabase.auth.refreshSession();

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
        console.error("[AuthProvider] Auth check failed:", error);

        // AC5: getUser() threw an error — fall back to session data
        try {
          const { data: { session: fallbackSession } } = await supabase.auth.getSession();
          if (fallbackSession?.user) {
            console.info("[AuthProvider] Falling back to session data (AC5)");
            clearTimeout(authTimeout);
            setUser(fallbackSession.user);
            setSession(fallbackSession);
            setLoading(false);
            // Don't fetch admin status on fallback — keep isAdmin=false as safe default
            return;
          }
        } catch (sessionError) {
          console.error("[AuthProvider] Session fallback also failed:", sessionError);
        }

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
            if (user) setUser(user); // Upgrade to validated user
          }).catch(() => { /* keep session user as fallback */ });
        } else {
          setUser(null);
          setIsAdmin(false);
          setLoading(false);
        }
      }
    );

    return () => {
      clearTimeout(authTimeout);
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

    // DEBUG: Log OAuth configuration
    console.log("[AuthProvider] Google OAuth Login Starting");
    console.log("[AuthProvider] NEXT_PUBLIC_CANONICAL_URL:", process.env.NEXT_PUBLIC_CANONICAL_URL);
    console.log("[AuthProvider] window.location.origin:", window.location.origin);
    console.log("[AuthProvider] Final redirect URL:", redirectUrl);

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
      console.error("[AuthProvider] Google OAuth error:", error);
      throw error;
    }
    console.log("[AuthProvider] OAuth redirect initiated");
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
