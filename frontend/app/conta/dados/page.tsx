"use client";

import { useState } from "react";
import { useUser } from "../../../contexts/UserContext";
import { getUserFriendlyError } from "../../../lib/error-messages";
import { Button } from "../../../components/ui/button";
import Link from "next/link";
import { toast } from "sonner";

/**
 * DEBT-011 FE-001: /conta/dados — Data export + account deletion (LGPD).
 */

export default function DadosPage() {
  const { user, session, authLoading, signOut } = useUser();

  const [exporting, setExporting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleted, setDeleted] = useState(false);

  if (authLoading) {
    return <div className="flex items-center justify-center py-12"><p className="text-[var(--ink-secondary)]">Carregando...</p></div>;
  }

  if (!user || !session) {
    return (
      <div className="text-center py-12">
        <p className="text-[var(--ink-secondary)] mb-4">Faça login para acessar sua conta</p>
        <Link href="/login" className="text-[var(--brand-blue)] hover:underline">Ir para login</Link>
      </div>
    );
  }

  if (deleted) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--success-subtle)] flex items-center justify-center">
            <svg role="img" aria-label="Sucesso" className="w-8 h-8 text-[var(--success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-3">Conta excluída</h1>
          <p className="text-[var(--ink-secondary)] mb-6">Sua conta e todos os dados associados foram excluídos permanentemente. Você será redirecionado para a página inicial.</p>
        </div>
      </div>
    );
  }

  const handleExportData = async () => {
    setExporting(true);
    try {
      const res = await fetch("/api/me/export", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error("Erro ao exportar dados");

      const disposition = res.headers.get("Content-Disposition");
      let filename = `smartlic_dados_${user.id.slice(0, 8)}_${new Date().toISOString().slice(0, 10)}.json`;
      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/);
        if (match) filename = match[1];
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(getUserFriendlyError(err));
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      const res = await fetch("/api/me", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || data.message || "Erro ao excluir conta");
      }
      setShowDeleteModal(false);
      setDeleted(true);
      setTimeout(async () => { await signOut(); }, 3000);
    } catch (err) {
      setDeleteError(getUserFriendlyError(err));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Data & Privacy */}
      <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
        <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Dados e Privacidade</h2>
        <p className="text-sm text-[var(--ink-secondary)] mb-4">
          Conforme a LGPD, você pode exportar seus dados ou excluir sua conta a qualquer momento.
        </p>

        <div className="space-y-3">
          <Button onClick={handleExportData} disabled={exporting} loading={exporting} variant="outline" size="lg" className="w-full">
            <svg role="img" aria-label="Exportar" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {exporting ? "Exportando..." : "Exportar Meus Dados"}
          </Button>

          <Button
            onClick={() => setShowDeleteModal(true)}
            variant="destructive"
            size="lg"
            className="w-full bg-transparent text-error border border-error hover:bg-error-subtle"
          >
            <svg role="img" aria-label="Excluir" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Excluir Minha Conta
          </Button>
        </div>
      </div>

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div role="alertdialog" aria-labelledby="delete-title" aria-describedby="delete-desc" className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-6 max-w-md w-full shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-[var(--error-subtle)] flex items-center justify-center flex-shrink-0">
                <svg role="img" aria-label="Atencao" className="w-5 h-5 text-[var(--error)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 id="delete-title" className="text-lg font-semibold text-[var(--ink)]">Excluir conta permanentemente?</h3>
            </div>

            <p id="delete-desc" className="text-sm text-[var(--ink-secondary)] mb-6">
              Todos os seus dados serão excluídos permanentemente: perfil, histórico de buscas, assinaturas, mensagens. Esta ação <strong>não pode ser desfeita</strong>.
            </p>

            {deleteError && (
              <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">{deleteError}</div>
            )}

            <div className="flex gap-3 justify-end">
              <Button onClick={() => { setShowDeleteModal(false); setDeleteError(null); }} disabled={deleting} variant="outline" size="default">Cancelar</Button>
              <Button onClick={handleDeleteAccount} disabled={deleting} loading={deleting} variant="destructive" size="default">
                {deleting ? "Excluindo..." : "Excluir Permanentemente"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
