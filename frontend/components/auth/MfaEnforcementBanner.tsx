"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../../lib/supabase";
import { useAuth } from "../../app/components/AuthProvider";

interface MfaEnforcementBannerProps {
  className?: string;
}

/**
 * AC16-17: Persistent, non-dismissible red banner for admin/master users without MFA.
 *
 * Shows when:
 * - User is admin or master
 * - MFA is not yet configured (no verified TOTP factors)
 *
 * Behavior:
 * - Non-dismissible (AC17)
 * - Links to /conta/seguranca
 * - Blocks /admin/* access when shown
 */
export function MfaEnforcementBanner({ className = "" }: MfaEnforcementBannerProps) {
  const router = useRouter();
  const { isAdmin, session } = useAuth();
  const [mfaRequired, setMfaRequired] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!session || !isAdmin) {
      setChecking(false);
      return;
    }

    (async () => {
      try {
        // Check if MFA is already set up
        const { data } = await supabase.auth.mfa.listFactors();
        const hasVerifiedTotp = data?.totp?.some(
          (f: { status: string }) => f.status === "verified"
        );

        if (!hasVerifiedTotp && isAdmin) {
          setMfaRequired(true);
        }
      } catch {
        // Can't check — don't block
      } finally {
        setChecking(false);
      }
    })();
  }, [session, isAdmin]);

  if (checking || !mfaRequired) return null;

  return (
    <div
      className={`w-full bg-[var(--error)] text-white px-4 py-3 ${className}`}
      role="alert"
      data-testid="mfa-enforcement-banner"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-sm font-medium">
            MFA obrigatório para sua conta. Configure a autenticação em dois fatores para continuar.
          </p>
        </div>
        <button
          onClick={() => router.push("/conta/seguranca")}
          className="flex-shrink-0 px-4 py-1.5 bg-white text-[var(--error)] rounded-button text-sm font-semibold hover:bg-white/90 transition-colors"
        >
          Configurar agora
        </button>
      </div>
    </div>
  );
}
