"use client";

import { useState } from "react";
import { useAuth } from "../components/AuthProvider";
import { PageHeader } from "../../components/PageHeader";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import { ErrorStateWithRetry } from "../../components/ErrorStateWithRetry";
import { ComingSoonPage } from "../../components/ComingSoonPage";
import { isFeatureGated } from "../../lib/feature-gates";
import { toast } from "sonner";
import { AlertCard } from "./components/AlertCard";
import { AlertFormModal } from "./components/AlertFormModal";
import { AlertsEmptyState } from "./components/AlertsEmptyState";
import { AlertsPageHeader } from "./components/AlertsPageHeader";
import { useAlerts } from "../../hooks/useAlerts";
import type { Alert as HookAlert } from "../../hooks/useAlerts";
import type { Alert, AlertFormData } from "./components/types";

// DEBT-FE-012: Show ComingSoonPage when feature is gated
const ALERTAS_GATED = isFeatureGated("alertas");

export default function AlertasPage() {
  if (ALERTAS_GATED) {
    return (
      <>
        <PageHeader title="Alertas" />
        <ComingSoonPage
          title="Alertas por E-mail"
          description="Receba notificacoes automaticas quando novas licitacoes compativeis com seu perfil forem publicadas. Configure filtros por setor, UF e valor para nao perder nenhuma oportunidade."
        />
      </>
    );
  }

  return <AlertasPageInner />;
}

function AlertasPageInner() {
  const { session, loading: authLoading } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [editingAlert, setEditingAlert] = useState<Alert | null>(null);
  const [saving, setSaving] = useState(false);

  // SWR-based alerts (FE-007)
  const { alerts, isLoading: loading, error, mutate: mutateAlerts } = useAlerts();

  // Create or update alert
  const handleSave = async (formData: AlertFormData) => {
    if (!session?.access_token) return;
    setSaving(true);
    try {
      const payload = {
        name: formData.name.trim(),
        filters: {
          setor: formData.setor || null,
          ufs: formData.ufs.length > 0 ? formData.ufs : null,
          valor_min: formData.valor_min ? Number(formData.valor_min) : null,
          valor_max: formData.valor_max ? Number(formData.valor_max) : null,
          keywords:
            formData.keywords.length > 0 ? formData.keywords : null,
        },
      };

      let res: Response;
      if (editingAlert) {
        res = await fetch(`/api/alerts/${editingAlert.id}`, {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
      } else {
        res = await fetch("/api/alerts", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.message || `Erro ${res.status}`);
      }

      toast.success(
        editingAlert ? "Alerta atualizado com sucesso" : "Alerta criado com sucesso",
      );
      setShowForm(false);
      setEditingAlert(null);
      await mutateAlerts();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao salvar alerta";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  // Toggle active/inactive
  const handleToggle = async (id: string, active: boolean) => {
    if (!session?.access_token) return;
    // Optimistic update via SWR mutate
    await mutateAlerts(
      (prev: HookAlert[] | undefined) => (prev ?? []).map((a) => (a.id === id ? { ...a, active } : a)),
      { revalidate: false }
    );
    try {
      const res = await fetch(`/api/alerts/${id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ active: active }),
      });
      if (!res.ok) {
        throw new Error("Falha ao atualizar status");
      }
      toast.success(active ? "Alerta ativado" : "Alerta desativado");
    } catch {
      // Revert optimistic update
      await mutateAlerts(
        (prev: HookAlert[] | undefined) => (prev ?? []).map((a) => (a.id === id ? { ...a, active: !active } : a)),
        { revalidate: false }
      );
      toast.error("Erro ao atualizar status do alerta");
    }
  };

  // Delete alert
  const handleDelete = async (id: string) => {
    if (!session?.access_token) return;
    try {
      const res = await fetch(`/api/alerts/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok && res.status !== 204) {
        throw new Error("Falha ao excluir");
      }
      // Optimistic update via SWR mutate
      await mutateAlerts(
        (prev: HookAlert[] | undefined) => (prev ?? []).filter((a) => a.id !== id),
        { revalidate: false }
      );
      toast.success("Alerta excluído com sucesso");
    } catch {
      toast.error("Erro ao excluir alerta");
    }
  };

  // Edit alert
  const handleEdit = (alert: Alert) => {
    setEditingAlert(alert);
    setShowForm(true);
  };

  // Close modal
  const handleCloseForm = () => {
    setShowForm(false);
    setEditingAlert(null);
  };

  // Auth loading gate
  if (authLoading) {
    return <AuthLoadingScreen />;
  }

  if (!session?.access_token) {
    return (
      <>
        <PageHeader title="Alertas" />
        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-4">Alertas por E-mail</h1>
          <p className="text-[var(--text-secondary)]">
            Faça login para gerenciar seus alertas.
          </p>
        </div>
      </>
    );
  }

  const handleCreateClick = () => {
    setEditingAlert(null);
    setShowForm(true);
  };

  return (
    <>
      <PageHeader title="Alertas" />
      <main className="max-w-3xl mx-auto px-4 py-6">
        <AlertsPageHeader alerts={alerts} onCreateClick={handleCreateClick} />

        {/* Content: loading / error / empty / list */}
        {loading ? (
          <div className="space-y-4" data-testid="alerts-skeleton">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-32 rounded-xl bg-[var(--surface-1)] animate-pulse"
                style={{ animationDelay: `${i * 100}ms` }}
              />
            ))}
          </div>
        ) : error ? (
          <ErrorStateWithRetry
            message={error}
            onRetry={() => mutateAlerts()}
          />
        ) : alerts.length === 0 ? (
          <AlertsEmptyState onCreate={handleCreateClick} />
        ) : (
          <div className="space-y-3" data-testid="alerts-list">
            {alerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onToggle={handleToggle}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </main>

      {/* Form modal */}
      {showForm && (
        <AlertFormModal
          editingAlert={editingAlert}
          onSave={handleSave}
          onClose={handleCloseForm}
          saving={saving}
        />
      )}
    </>
  );
}
