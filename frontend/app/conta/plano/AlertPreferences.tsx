"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { toast } from "sonner";

/**
 * DEBT-011: Alert preferences + user alerts list (extracted from plano page).
 */

interface AlertPreferencesProps {
  accessToken: string;
}

export function AlertPreferences({ accessToken }: AlertPreferencesProps) {
  const [alertEnabled, setAlertEnabled] = useState(true);
  const [alertFrequency, setAlertFrequency] = useState("daily");
  const [alertLoading, setAlertLoading] = useState(false);
  const [alertSaving, setAlertSaving] = useState(false);
  const [digestMode, setDigestMode] = useState<"individual" | "consolidated">("individual");
  const [userAlerts, setUserAlerts] = useState<Array<{ id: string; name: string; active: boolean }>>([]);
  const [userAlertsLoading, setUserAlertsLoading] = useState(false);

  const fetchAlertPrefs = useCallback(async () => {
    setAlertLoading(true);
    try {
      const res = await fetch("/api/alert-preferences", { headers: { Authorization: `Bearer ${accessToken}` } });
      if (res.ok) { const data = await res.json(); setAlertEnabled(data.enabled ?? true); setAlertFrequency(data.frequency ?? "daily"); }
    } catch { /* silent */ } finally { setAlertLoading(false); }
  }, [accessToken]);

  const fetchUserAlerts = useCallback(async () => {
    setUserAlertsLoading(true);
    try {
      const res = await fetch("/api/alerts", { headers: { Authorization: `Bearer ${accessToken}` } });
      if (res.ok) { const data = await res.json(); setUserAlerts(Array.isArray(data) ? data : data.alerts || []); }
    } catch { /* silent */ } finally { setUserAlertsLoading(false); }
  }, [accessToken]);

  const handleSave = useCallback(async (enabled: boolean, frequency: string) => {
    setAlertSaving(true);
    try {
      const res = await fetch("/api/alert-preferences", {
        method: "PUT",
        headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ enabled, frequency }),
      });
      if (res.ok) { const data = await res.json(); setAlertEnabled(data.enabled); setAlertFrequency(data.frequency); toast.success("Preferências de alerta atualizadas"); }
      else toast.error("Erro ao salvar preferências");
    } catch { toast.error("Erro de conexão"); } finally { setAlertSaving(false); }
  }, [accessToken]);

  useEffect(() => { fetchAlertPrefs(); fetchUserAlerts(); }, [fetchAlertPrefs, fetchUserAlerts]);

  return (
    <>
      {/* Alert Preferences */}
      <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card" data-testid="alert-preferences-section">
        <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Alertas por Email</h2>
        <p className="text-sm text-[var(--ink-secondary)] mb-4">Receba oportunidades de licitação filtradas para seu perfil no seu email.</p>

        {alertLoading ? (
          <div className="h-16 bg-[var(--surface-1)] rounded animate-pulse" />
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-[var(--ink)]">Receber alerta por email</span>
              <button type="button" role="switch" aria-checked={alertEnabled} disabled={alertSaving} data-testid="alert-toggle"
                onClick={() => { const v = !alertEnabled; setAlertEnabled(v); handleSave(v, alertFrequency); }}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--brand-blue)] ${alertEnabled ? "bg-[var(--brand-navy)]" : "bg-[var(--surface-2)]"} ${alertSaving ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}>
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${alertEnabled ? "translate-x-6" : "translate-x-1"}`} />
              </button>
            </div>

            {alertEnabled && (
              <>
                <div>
                  <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">Frequência</label>
                  <div className="flex flex-wrap gap-2">
                    {[{ value: "daily", label: "Diário" }, { value: "twice_weekly", label: "2x por semana" }, { value: "weekly", label: "Semanal" }].map((opt) => (
                      <button key={opt.value} type="button" disabled={alertSaving} data-testid={`alert-freq-${opt.value}`}
                        onClick={() => { setAlertFrequency(opt.value); handleSave(alertEnabled, opt.value); }}
                        className={`px-4 py-2 rounded-button text-sm font-medium transition-colors ${alertFrequency === opt.value ? "bg-[var(--brand-navy)] text-white" : "border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:bg-[var(--surface-1)]"} ${alertSaving ? "opacity-50 cursor-not-allowed" : ""}`}>
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">Formato do email</label>
                  <div className="flex flex-wrap gap-2">
                    {[{ value: "individual" as const, label: "1 email por alerta" }, { value: "consolidated" as const, label: "1 email consolidado" }].map((opt) => (
                      <button key={opt.value} type="button" data-testid={`digest-mode-${opt.value}`} onClick={() => setDigestMode(opt.value)}
                        className={`px-4 py-2 rounded-button text-sm font-medium transition-colors ${digestMode === opt.value ? "bg-[var(--brand-navy)] text-white" : "border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:bg-[var(--surface-1)]"}`}>
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-[var(--ink-muted)] mt-1">{digestMode === "consolidated" ? "1 email com todos os alertas reunidos." : "1 email separado para cada alerta."}</p>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* User Alerts List */}
      <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card" data-testid="meus-alertas-section">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[var(--ink)]">Meus Alertas</h2>
          <Link href="/alertas" className="text-sm font-medium text-[var(--brand-blue)] hover:underline">Gerenciar alertas</Link>
        </div>

        {userAlertsLoading ? (
          <div className="space-y-2">{[1, 2].map((i) => <div key={i} className="h-12 bg-[var(--surface-1)] rounded animate-pulse" />)}</div>
        ) : userAlerts.length === 0 ? (
          <div className="text-center py-6">
            <p className="text-sm text-[var(--ink-muted)] mb-3">Nenhum alerta configurado.</p>
            <Link href="/alertas" className="inline-flex items-center gap-2 px-4 py-2 rounded-button text-sm font-medium bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] transition-colors" data-testid="create-first-alert-btn">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
              Criar primeiro alerta
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {userAlerts.slice(0, 5).map((alert) => (
              <div key={alert.id} className={`flex items-center justify-between px-3 py-2.5 rounded-lg border ${alert.active ? "border-[var(--brand-blue)]/20 bg-[var(--surface-0)]" : "border-[var(--border)] bg-[var(--surface-1)] opacity-60"}`} data-testid={`conta-alert-${alert.id}`}>
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${alert.active ? "bg-green-500" : "bg-[var(--ink-faint)]"}`} />
                  <span className="text-sm font-medium text-[var(--ink)] truncate">{alert.name}</span>
                </div>
                <span className="text-xs text-[var(--ink-muted)] flex-shrink-0 ml-2">{alert.active ? "Ativo" : "Inativo"}</span>
              </div>
            ))}
            {userAlerts.length > 5 && <Link href="/alertas" className="block text-center text-sm text-[var(--brand-blue)] hover:underline py-1">Ver todos os {userAlerts.length} alertas</Link>}
          </div>
        )}
      </div>
    </>
  );
}
