"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import FocusTrap from "focus-trap-react";

interface InviteMemberModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInviteSent: () => void;
  accessToken: string;
  orgId: string;
}

export function InviteMemberModal({
  isOpen,
  onClose,
  onInviteSent,
  accessToken,
  orgId,
}: InviteMemberModalProps) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Lock body scroll while open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  if (!isOpen) return null;

  const resetAndClose = () => {
    setEmail("");
    setError(null);
    setLoading(false);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();
    if (!trimmed) {
      setError("Informe o e-mail do membro a convidar.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      setError("E-mail invalido.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/organizations/${orgId}?action=invite`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: trimmed }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.message || data.detail || "Erro ao enviar convite");
      }

      toast.success(`Convite enviado para ${trimmed}`);
      onInviteSent();
      resetAndClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar convite");
    } finally {
      setLoading(false);
    }
  };

  return (
    <FocusTrap
      active={isOpen}
      focusTrapOptions={{
        escapeDeactivates: true,
        onDeactivate: resetAndClose,
        allowOutsideClick: true,
        returnFocusOnDeactivate: true,
        tabbableOptions: { displayCheck: "none" },
      }}
    >
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) resetAndClose();
      }}
    >
      <div
        role="alertdialog"
        aria-labelledby="invite-modal-title"
        aria-describedby="invite-modal-desc"
        className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-6 max-w-sm w-full shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-[var(--brand-blue-subtle,#eff6ff)] flex items-center justify-center flex-shrink-0">
            <svg
              role="img"
              aria-label="Convidar membro"
              className="w-5 h-5 text-[var(--brand-blue)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
              />
            </svg>
          </div>
          <h3 id="invite-modal-title" className="text-lg font-semibold text-[var(--ink)]">
            Convidar membro
          </h3>
        </div>

        <p id="invite-modal-desc" className="text-sm text-[var(--ink-secondary)] mb-4">
          O membro receberá um e-mail com o link de acesso para se juntar à sua equipe.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label
              htmlFor="invite-email"
              className="block text-sm font-medium text-[var(--ink)] mb-1.5"
            >
              E-mail
            </label>
            <input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (error) setError(null);
              }}
              placeholder="membro@empresa.com.br"
              autoFocus
              autoComplete="off"
              className="w-full px-3 py-2.5 rounded-button border border-[var(--border)]
                         bg-[var(--surface-0)] text-sm text-[var(--ink)]
                         placeholder:text-[var(--ink-muted,#9ca3af)]
                         focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)]
                         disabled:opacity-50"
              disabled={loading}
            />
          </div>

          {error && (
            <div
              role="alert"
              className="mb-4 p-3 bg-[var(--error-subtle,#fee2e2)] text-[var(--error,#dc2626)]
                         rounded-button text-sm"
            >
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={resetAndClose}
              disabled={loading}
              className="flex-1 px-4 py-2.5 rounded-button border border-[var(--border)]
                         text-[var(--ink)] bg-[var(--surface-0)]
                         hover:bg-[var(--surface-1)] transition-colors text-sm
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !email.trim()}
              className="flex-1 px-4 py-2.5 rounded-button bg-[var(--brand-blue)] text-white
                         hover:opacity-90 transition-opacity text-sm
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Enviando..." : "Enviar convite"}
            </button>
          </div>
        </form>
      </div>
    </div>
    </FocusTrap>
  );
}
