"use client";

import { useState } from "react";
import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";
import { toast } from "sonner";
import { useAdminSWR } from "../../../hooks/useAdminSWR";

interface FeatureFlagLifecycle {
  owner: string;
  category: string;
  lifecycle: string;
  created: string;
  remove_after: string | null;
}

interface FeatureFlag {
  name: string;
  value: boolean;
  source: "redis" | "memory" | "env" | "default";
  description: string;
  env_var: string;
  default: string;
  lifecycle: FeatureFlagLifecycle | null;
}

interface FeatureFlagListResponse {
  flags: FeatureFlag[];
  total: number;
  redis_available: boolean;
}

const SOURCE_COLORS: Record<string, string> = {
  redis: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  memory: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  env: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  default: "bg-gray-100 text-gray-700 dark:bg-gray-800/50 dark:text-gray-400",
};

const LIFECYCLE_COLORS: Record<string, string> = {
  permanent: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  experimental: "bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300",
  "ops-toggle": "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  gate: "bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300",
  deprecating: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
};

export default function AdminFeatureFlagsPage() {
  const { session, loading: authLoading, isAdmin, isAdminLoading } = useAuth();
  const [toggling, setToggling] = useState<string | null>(null);
  const [reloading, setReloading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>("");

  const shouldFetch = isAdmin && !authLoading && !isAdminLoading;
  const {
    data,
    error,
    isLoading,
    mutate,
  } = useAdminSWR<FeatureFlagListResponse>(
    shouldFetch ? "/api/admin/feature-flags" : null
  );

  const handleToggle = async (flag: FeatureFlag) => {
    if (!session?.access_token) return;
    setToggling(flag.name);
    try {
      const res = await fetch(`/api/admin/feature-flags/${flag.name}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ value: !flag.value }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }
      toast.success(`${flag.name}: ${!flag.value ? "ativado" : "desativado"}`);
      mutate();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao atualizar flag");
    } finally {
      setToggling(null);
    }
  };

  const handleReload = async () => {
    if (!session?.access_token) return;
    setReloading(true);
    try {
      const res = await fetch("/api/admin/feature-flags/reload", {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const result = await res.json();
      toast.success(`Flags recarregadas — ${result.overrides_cleared} overrides limpos`);
      mutate();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao recarregar flags");
    } finally {
      setReloading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <Link href="/login" className="text-[var(--brand-blue)]">
          Login necessário
        </Link>
      </div>
    );
  }

  if (!isAdmin && !isAdminLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center max-w-md px-4">
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">
            Acesso Restrito
          </h1>
          <p className="text-[var(--ink-secondary)] mb-6">
            Esta página é exclusiva para administradores.
          </p>
          <Link
            href="/buscar"
            className="inline-block px-6 py-2 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors"
          >
            Voltar
          </Link>
        </div>
      </div>
    );
  }

  const categories = data
    ? Array.from(
        new Set(
          data.flags
            .map((f) => f.lifecycle?.category)
            .filter((c): c is string => Boolean(c))
        )
      ).sort()
    : [];

  const visibleFlags = data?.flags.filter(
    (f) => !categoryFilter || f.lifecycle?.category === categoryFilter
  ) ?? [];

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)]">
              Admin — Feature Flags
            </h1>
            <p className="text-[var(--ink-secondary)]">
              {data
                ? `${data.total} flags · Redis ${data.redis_available ? "conectado" : "indisponível"}`
                : "Controle de flags em runtime"}
            </p>
          </div>
          <div className="flex gap-3 flex-wrap">
            <Link
              href="/admin"
              className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
            >
              Usuários
            </Link>
            <Link
              href="/admin/cache"
              className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
            >
              Cache
            </Link>
            <button
              onClick={() => mutate()}
              disabled={isLoading}
              className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)] disabled:opacity-50"
            >
              {isLoading ? "Atualizando..." : "Atualizar"}
            </button>
            <button
              onClick={handleReload}
              disabled={reloading}
              className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm hover:bg-[var(--brand-blue)] disabled:opacity-50"
            >
              {reloading ? "Recarregando..." : "Recarregar do Env"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-[var(--error-subtle)] border border-[var(--error)] rounded-card text-[var(--error)]">
            {error.message ?? "Erro ao carregar flags"}
          </div>
        )}

        {/* Redis status */}
        {data && (
          <div
            className={`mb-6 p-4 rounded-card border flex items-center gap-3 ${
              data.redis_available
                ? "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800"
                : "bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800"
            }`}
          >
            <span
              className={`inline-block w-3 h-3 rounded-full ${
                data.redis_available ? "bg-green-500" : "bg-amber-500 animate-pulse"
              }`}
            />
            <span
              className={`font-medium ${
                data.redis_available
                  ? "text-green-800 dark:text-green-300"
                  : "text-amber-800 dark:text-amber-300"
              }`}
            >
              Redis:{" "}
              {data.redis_available
                ? "Conectado — overrides persistem entre restarts"
                : "Indisponível — overrides em memória apenas (voláteis)"}
            </span>
          </div>
        )}

        {/* Category filter */}
        {categories.length > 0 && (
          <div className="mb-4 flex gap-2 flex-wrap">
            <button
              onClick={() => setCategoryFilter("")}
              className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                categoryFilter === ""
                  ? "bg-[var(--brand-navy)] text-white border-[var(--brand-navy)]"
                  : "border-[var(--border)] text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
              }`}
            >
              Todos
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                  categoryFilter === cat
                    ? "bg-[var(--brand-navy)] text-white border-[var(--brand-navy)]"
                    : "border-[var(--border)] text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        )}

        {/* Flags table */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card overflow-hidden">
          <div className="px-6 py-4 border-b border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--ink)]">
              {categoryFilter ? `${categoryFilter} (${visibleFlags.length})` : `Todas as Flags (${visibleFlags.length})`}
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[var(--surface-2)] text-left">
                  <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Flag</th>
                  <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Status</th>
                  <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Fonte</th>
                  <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Ciclo</th>
                  <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Categoria</th>
                  <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Ação</th>
                </tr>
              </thead>
              <tbody>
                {visibleFlags.map((flag) => (
                  <tr
                    key={flag.name}
                    className="border-t border-[var(--border)] hover:bg-[var(--surface-2)]"
                  >
                    <td className="px-4 py-3">
                      <div className="font-mono text-xs font-medium text-[var(--ink)]">
                        {flag.name}
                      </div>
                      {flag.description && (
                        <div className="text-xs text-[var(--ink-secondary)] mt-0.5 max-w-xs">
                          {flag.description}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
                          flag.value
                            ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                            : "bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            flag.value ? "bg-green-500" : "bg-gray-400"
                          }`}
                        />
                        {flag.value ? "ativo" : "inativo"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${SOURCE_COLORS[flag.source] ?? ""}`}
                      >
                        {flag.source}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {flag.lifecycle?.lifecycle ? (
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${LIFECYCLE_COLORS[flag.lifecycle.lifecycle] ?? ""}`}
                        >
                          {flag.lifecycle.lifecycle}
                        </span>
                      ) : (
                        <span className="text-[var(--ink-secondary)]">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--ink-secondary)]">
                      {flag.lifecycle?.category ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggle(flag)}
                        disabled={toggling === flag.name}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
                          flag.value
                            ? "bg-[var(--brand-navy)]"
                            : "bg-[var(--border)]"
                        }`}
                        aria-label={`${flag.value ? "Desativar" : "Ativar"} ${flag.name}`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                            flag.value ? "translate-x-6" : "translate-x-1"
                          }`}
                        />
                      </button>
                    </td>
                  </tr>
                ))}
                {visibleFlags.length === 0 && !isLoading && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-8 text-center text-[var(--ink-secondary)]"
                    >
                      {data ? "Nenhuma flag encontrada" : "Carregando..."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {isLoading && !data && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-[var(--brand-navy)] border-t-transparent rounded-full" />
          </div>
        )}
      </div>
    </div>
  );
}
