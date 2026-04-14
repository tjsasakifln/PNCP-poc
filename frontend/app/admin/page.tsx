"use client";

import { useState } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import { toast } from "sonner";
import { useAdminSWR, usePublicSWR } from "../../hooks/useAdminSWR";

import { AdminUptimeWidget } from "./components/AdminUptimeWidget";
import { AdminSourceHealth } from "./components/AdminSourceHealth";
import { AdminReconciliation } from "./components/AdminReconciliation";
import { AdminSupportSLA } from "./components/AdminSupportSLA";
import { AdminTrialMetrics } from "./components/AdminTrialMetrics";
import { AdminUserTable } from "./components/AdminUserTable";
import { AdminCreateUser } from "./components/AdminCreateUser";
// STORY-2.1 (EPIC-TD-2026Q2): Share the admin user shape with AdminUserTable.
import type {
  AdminUserProfile as UserProfile,
  AdminUsersResponse as UsersResponse,
} from "./types";

interface StatusResponse {
  sources: Record<string, {
    status: string;
    latency_ms?: number;
    last_check?: string;
  }>;
  uptime_pct_30d?: number;
}

interface SlaResponse {
  avg_response_hours: number;
  pending_count: number;
  breached_count: number;
}

interface ReconResponse {
  runs: Array<{
    id: string;
    run_at: string;
    total_checked: number;
    divergences_found: number;
    auto_fixed: number;
    manual_review: number;
    duration_ms: number;
  }>;
}

export default function AdminPage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;
  const [showCreate, setShowCreate] = useState(false);
  const [reconTriggering, setReconTriggering] = useState(false);

  // SWR data fetching
  const usersKey = isAdmin ? `/api/admin/users?limit=${limit}&offset=${page * limit}${search ? `&search=${search}` : ""}` : null;
  const { data: usersData, error: usersError, isLoading: usersLoading, mutate: mutateUsers } = useAdminSWR<UsersResponse>(usersKey);

  const { data: statusData, isLoading: statusLoading, mutate: mutateStatus } = usePublicSWR<StatusResponse>(isAdmin ? "/api/status" : null);

  const { data: slaData, isLoading: slaLoading, mutate: mutateSla } = useAdminSWR<SlaResponse>(isAdmin ? "/api/admin/support-sla" : null);

  const { data: reconData, isLoading: reconLoading, mutate: mutateRecon } = useAdminSWR<ReconResponse>(isAdmin ? "/api/admin/reconciliation/history?limit=5" : null);

  const { data: trialMetrics, isLoading: metricsLoading } = useAdminSWR<any>(
    isAdmin ? "/api/admin/trial-metrics" : null
  );
  const { data: atRiskData } = useAdminSWR<any>(
    isAdmin ? "/api/admin/at-risk-trials?limit=10" : null
  );

  const users = usersData?.users ?? [];
  const total = usersData?.total ?? 0;
  const loading = usersLoading;
  const error = usersError?.message ?? null;

  const uptimePct30d = statusData?.uptime_pct_30d ?? null;
  const sourceHealth = statusData?.sources ?? {};

  const reconHistory = reconData?.runs ?? [];

  const handleTriggerReconciliation = async () => {
    if (!session) return;
    setReconTriggering(true);
    try {
      const res = await fetch("/api/admin/reconciliation/trigger", {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        toast.success("Reconciliacao executada com sucesso");
        mutateRecon();
      } else if (res.status === 409) {
        toast.error("Reconciliacao ja em execucao");
      } else {
        toast.error("Erro ao executar reconciliacao");
      }
    } catch {
      toast.error("Erro de conexao");
    } finally {
      setReconTriggering(false);
    }
  };

  if (authLoading) return <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]"><p className="text-[var(--ink-secondary)]">Carregando...</p></div>;
  if (!session) return <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]"><Link href="/login" className="text-[var(--brand-blue)]">Login necessário</Link></div>;

  // Show 403 for non-admin users
  if (!isAdmin && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center max-w-md px-4">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--error-subtle)] flex items-center justify-center">
            <svg role="img" aria-label="Aviso" className="w-8 h-8 text-[var(--error)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">Acesso Restrito</h1>
          <p className="text-[var(--ink-secondary)] mb-6">
            Esta página é exclusiva para administradores do sistema. Se você acredita que deveria ter acesso, entre em contato com o suporte.
          </p>
          <Link
            href="/buscar"
            className="inline-block px-6 py-2 bg-[var(--brand-navy)] text-white rounded-button
                       hover:bg-[var(--brand-blue)] transition-colors"
          >
            Voltar para início
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)]">Admin - Usuários</h1>
            <p className="text-[var(--ink-secondary)]">{total} usuário{total !== 1 ? "s" : ""}</p>
          </div>
          <div className="flex gap-3">
            <Link href="/admin/cache" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              Cache
            </Link>
            <Link href="/admin/metrics" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              Metrics
            </Link>
            <Link href="/admin/seo" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              SEO
            </Link>
            <Link href="/admin/slo" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              SLOs
            </Link>
            <Link href="/mensagens" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)]">
              Mensagens
            </Link>
            <Link href="/buscar" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)]">
              Voltar
            </Link>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm hover:bg-[var(--brand-blue)]"
            >
              {showCreate ? "Cancelar" : "Novo usuário"}
            </button>
          </div>
        </div>

        <AdminUptimeWidget uptimePct30d={uptimePct30d} loading={statusLoading} onRetry={() => mutateStatus()} />

        <AdminSourceHealth
          sourceHealth={sourceHealth}
          sourceHealthLoading={statusLoading}
          onRefresh={() => mutateStatus()}
        />

        <AdminReconciliation
          reconHistory={reconHistory}
          reconLoading={reconLoading}
          reconTriggering={reconTriggering}
          onTrigger={handleTriggerReconciliation}
        />

        <AdminSupportSLA
          slaData={slaData ?? null}
          slaLoading={slaLoading}
          onRefresh={() => mutateSla()}
        />

        <AdminTrialMetrics
          metrics={trialMetrics ?? null}
          atRiskUsers={atRiskData?.users ?? []}
          loading={metricsLoading}
        />

        {showCreate && (
          <AdminCreateUser
            session={session}
            onCreated={() => { mutateUsers().catch(() => {}); }}
            onCancel={() => setShowCreate(false)}
          />
        )}

        <AdminUserTable
          users={users}
          total={total}
          loading={loading}
          error={error}
          search={search}
          page={page}
          limit={limit}
          session={session}
          onSearchChange={(v) => { setSearch(v); setPage(0); }}
          onPageChange={setPage}
          onRefresh={() => mutateUsers()}
        />
      </div>
    </div>
  );
}
