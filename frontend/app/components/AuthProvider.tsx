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
    // CRITICAL FIX: Add timeout to prevent infinite loading from stale cache/network issues
    const authTimeout = setTimeout(() => {
      console.warn("[AuthProvider] Auth check timeout - forcing loading=false");
      setLoading(false);
    }, 10000); // 10 second timeout

    // Get initial user - SECURITY FIX: Use getUser() for validated user data
    // getUser() ensures the user is authenticated by Supabase server (not just from cookies)
    supabase.auth.getUser()
      .then(({ data: { user } }) => {
        clearTimeout(authTimeout);
        setUser(user);
        setLoading(false);
        // Get session for access token (after user is validated)
        if (user) {
          supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            if (session?.access_token) {
              fetchAdminStatus(session.access_token);
            }
          });
        }
      })
      .catch((error) => {
        console.error("[AuthProvider] Auth check failed:", error);
        clearTimeout(authTimeout);
        setUser(null);
        setSession(null);
        setLoading(false);
      });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        setSession(session);
        setLoading(false);
        if (session) {
          // SECURITY FIX: Revalidate user on auth state change
          const { data: { user } } = await supabase.auth.getUser();
          setUser(user);
          if (session.access_token) {
            fetchAdminStatus(session.access_token);
          }
        } else {
          setUser(null);
          setIsAdmin(false);
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

    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: redirectUrl },
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
