"use client";

import { useState } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";

export default function ContaPage() {
  const { user, session, loading: authLoading, signOut } = useAuth();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    );
  }

  if (!user || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center">
          <p className="text-[var(--ink-secondary)] mb-4">Faça login para acessar sua conta</p>
          <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
            Ir para login
          </Link>
        </div>
      </div>
    );
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (newPassword.length < 6) {
      setError("Senha deve ter no mínimo 6 caracteres");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("As senhas não coincidem");
      return;
    }

    setLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      if (!backendUrl) {
        throw new Error("Backend não configurado. Contate o suporte.");
      }
      const res = await fetch(`${backendUrl}/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ new_password: newPassword }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao alterar senha");
      }

      setSuccess(true);
      setNewPassword("");
      setConfirmPassword("");
      setShowNewPassword(false);
      setShowConfirmPassword(false);

      // Logout apos 2 segundos para o usuario ver a mensagem de sucesso
      setTimeout(async () => {
        await signOut();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-display font-bold text-[var(--ink)]">Minha Conta</h1>
          <Link href="/buscar" className="text-sm text-[var(--brand-blue)] hover:underline">
            Voltar
          </Link>
        </div>

        {/* Profile info */}
        <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Dados do perfil</h2>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-[var(--ink-muted)]">Email</span>
              <p className="text-[var(--ink)]">{user.email}</p>
            </div>
            <div>
              <span className="text-sm text-[var(--ink-muted)]">Nome</span>
              <p className="text-[var(--ink)]">
                {user.user_metadata?.full_name || user.user_metadata?.name || "-"}
              </p>
            </div>
          </div>
        </div>

        {/* Change password */}
        <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Alterar senha</h2>

          {error && (
            <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-[var(--success-subtle)] text-[var(--success)] rounded-input text-sm">
              Senha alterada com sucesso! Redirecionando para login...
            </div>
          )}

          {/* Aviso sobre logout */}
          <div className="mb-4 p-3 bg-[var(--warning-subtle,#fef3cd)] text-[var(--warning,#856404)] rounded-input text-sm flex items-start gap-2">
            <svg
              role="img"
              aria-label="Aviso" className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Ao alterar sua senha, voce sera desconectado e precisara fazer login novamente.</span>
          </div>

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
                Nova senha
              </label>
              <div className="relative">
                <input
                  id="newPassword"
                  type={showNewPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)]
                             bg-[var(--surface-0)] text-[var(--ink)]
                             focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                             focus:ring-[var(--brand-blue-subtle)]"
                  placeholder="Minimo 6 caracteres"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                             hover:text-[var(--ink)] transition-colors"
                  aria-label={showNewPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showNewPassword ? (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
                Confirmar nova senha
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)]
                             bg-[var(--surface-0)] text-[var(--ink)]
                             focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                             focus:ring-[var(--brand-blue-subtle)]"
                  placeholder="Repita a nova senha"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                             hover:text-[var(--ink)] transition-colors"
                  aria-label={showConfirmPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showConfirmPassword ? (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button
                         font-semibold hover:bg-[var(--brand-blue)] transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Alterando..." : "Alterar senha"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
