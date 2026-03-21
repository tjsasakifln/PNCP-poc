"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import { toast } from "sonner";

import { AdminUptimeWidget } from "./components/AdminUptimeWidget";
import { AdminSourceHealth } from "./components/AdminSourceHealth";
import { AdminReconciliation } from "./components/AdminReconciliation";
import { AdminSupportSLA } from "./components/AdminSupportSLA";
import { AdminUserTable } from "./components/AdminUserTable";
import { AdminCreateUser } from "./components/AdminCreateUser";

interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  company: string | null;
  plan_type: string;
  created_at: string;
  user_subscriptions: Array<{
    id: string;
    plan_id: string;
    credits_remaining: number | null;
    expires_at: string | null;
    is_active: boolean;
  }>;
}

export default function AdminPage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;

  const [showCreate, setShowCreate] = useState(false);

  // STORY-352 AC5: Uptime widget state
  const [uptimePct30d, setUptimePct30d] = useState<number | null>(null);

  // STORY-350 AC6: Source health state
  const [sourceHealth, setSourceHealth] = useState<Record<string, {
    status: string;
    latency_ms?: number;
    last_check?: string;
  }>>({});
  const [sourceHealthLoading, setSourceHealthLoading] = useState(false);

  // STORY-314: Reconciliation widget state
  const [reconHistory, setReconHistory] = useState<Array<{
    id: string;
    run_at: string;
    total_checked: number;
    divergences_found: number;
    auto_fixed: number;
    manual_review: number;
    duration_ms: number;
  }>>([]);
  const [reconLoading, setReconLoading] = useState(false);
  const [reconTriggering, setReconTriggering] = useState(false);

  // STORY-353 AC7: Support SLA widget state
  const [slaData, setSlaData] = useState<{
    avg_response_hours: number;
    pending_count: number;
    breached_count: number;
  } | null>(null);
  const [slaLoading, setSlaLoading] = useState(false);

  const fetchUsers = useCallback(async () => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
      if (search) params.set("search", search);
      const res = await fetch(`/api/admin/users?${params}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.status === 403) {
        setError("Acesso negado. Você não é administrador.");
        return;
      }
      if (!res.ok) throw new Error("Erro ao carregar usuários");
      const data = await res.json();
      setUsers(data.users);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [session, page, search]);

  const fetchSourceHealth = useCallback(async () => {
    setSourceHealthLoading(true);
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        if (data.sources) setSourceHealth(data.sources);
        if (data.uptime_pct_30d !== undefined) setUptimePct30d(data.uptime_pct_30d);
      }
    } catch {
      // Non-critical
    } finally {
      setSourceHealthLoading(false);
    }
  }, []);

  const fetchSlaData = useCallback(async () => {
    if (!session) return;
    setSlaLoading(true);
    try {
      const res = await fetch("/api/admin/support-sla", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSlaData(data);
      }
    } catch {
      // Non-critical
    } finally {
      setSlaLoading(false);
    }
  }, [session]);

  const fetchReconHistory = useCallback(async () => {
    if (!session) return;
    setReconLoading(true);
    try {
      const res = await fetch("/api/admin/reconciliation/history?limit=5", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setReconHistory(data.runs || []);
      }
    } catch {
      // Non-critical
    } finally {
      setReconLoading(false);
    }
  }, [session]);

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
        fetchReconHistory();
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

  useEffect(() => {
    if (!authLoading && session) {
      fetchUsers();
      fetchReconHistory();
      fetchSourceHealth();
      fetchSlaData();
    }
  }, [authLoading, session, fetchUsers, fetchReconHistory, fetchSourceHealth, fetchSlaData]);

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

        <AdminUptimeWidget uptimePct30d={uptimePct30d} />

        <AdminSourceHealth
          sourceHealth={sourceHealth}
          sourceHealthLoading={sourceHealthLoading}
          onRefresh={fetchSourceHealth}
        />

        <AdminReconciliation
          reconHistory={reconHistory}
          reconLoading={reconLoading}
          reconTriggering={reconTriggering}
          onTrigger={handleTriggerReconciliation}
        />

        <AdminSupportSLA
          slaData={slaData}
          slaLoading={slaLoading}
          onRefresh={fetchSlaData}
        />

        {showCreate && (
          <AdminCreateUser
            session={session}
            onCreated={fetchUsers}
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
          onRefresh={fetchUsers}
        />
      </div>
    </div>
  );
}
