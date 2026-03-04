"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../components/AuthProvider";
import { usePlan } from "../../../hooks/usePlan";
import { PageHeader } from "../../../components/PageHeader";
import { InviteMemberModal } from "../../../components/org/InviteMemberModal";
import Link from "next/link";

// ─── Types ────────────────────────────────────────────────────────────────────

interface OrgMember {
  id: string;
  user_id: string | null;
  email: string;
  name: string | null;
  role: "owner" | "admin" | "member";
  status: "accepted" | "pending";
  joined_at: string | null;
  invited_at: string;
}

interface Organization {
  id: string;
  name: string;
  slug: string;
  max_seats: number;
  members: OrgMember[];
}

interface OrgRef {
  id: string;
  name: string;
  role: "owner" | "admin" | "member";
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  owner: "Proprietário",
  admin: "Admin",
  member: "Membro",
};

const ROLE_COLORS: Record<string, string> = {
  owner: "bg-[var(--brand-blue-subtle,#eff6ff)] text-[var(--brand-blue)]",
  admin: "bg-[var(--success-subtle,#d1fae5)] text-[var(--success,#059669)]",
  member: "bg-[var(--surface-1)] text-[var(--ink-secondary)]",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function EquipePage() {
  const { session } = useAuth();
  const { planInfo, loading: planLoading } = usePlan();
  const accessToken = session?.access_token ?? "";

  const [org, setOrg] = useState<Organization | null>(null);
  const [loadingOrg, setLoadingOrg] = useState(true);
  const [orgError, setOrgError] = useState<string | null>(null);

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [confirmRemoveId, setConfirmRemoveId] = useState<string | null>(null);
  const [removeError, setRemoveError] = useState<string | null>(null);

  // ─── Fetch org ─────────────────────────────────────────────────────────────

  const fetchOrg = useCallback(async () => {
    if (!accessToken) return;
    setLoadingOrg(true);
    setOrgError(null);

    try {
      // Step 1: get org reference (id + role) for the current user
      const refRes = await fetch("/api/organizations", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (refRes.status === 404) {
        // User has no org yet
        setOrg(null);
        setLoadingOrg(false);
        return;
      }

      if (!refRes.ok) {
        const data = await refRes.json().catch(() => ({}));
        throw new Error(data.message || "Erro ao carregar organização");
      }

      const ref: OrgRef = await refRes.json();

      // Step 2: fetch full org details including members
      const detailRes = await fetch(`/api/organizations/${ref.id}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (!detailRes.ok) {
        const data = await detailRes.json().catch(() => ({}));
        throw new Error(data.message || "Erro ao carregar detalhes da organização");
      }

      const detail: Organization = await detailRes.json();
      setOrg(detail);
    } catch (err) {
      setOrgError(err instanceof Error ? err.message : "Erro ao carregar equipe");
    } finally {
      setLoadingOrg(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchOrg();
  }, [fetchOrg]);

  // ─── Remove member ─────────────────────────────────────────────────────────

  const handleRemoveMember = async (memberId: string) => {
    if (!org) return;
    setRemovingId(memberId);
    setRemoveError(null);

    try {
      const res = await fetch(`/api/organizations/${org.id}?member_id=${memberId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.message || "Erro ao remover membro");
      }

      // Optimistic update
      setOrg((prev) =>
        prev
          ? { ...prev, members: prev.members.filter((m) => m.id !== memberId) }
          : prev,
      );
      setConfirmRemoveId(null);
    } catch (err) {
      setRemoveError(err instanceof Error ? err.message : "Erro ao remover membro");
    } finally {
      setRemovingId(null);
    }
  };

  // ─── Plan gate ─────────────────────────────────────────────────────────────

  if (!planLoading && planInfo && !planInfo.plan_id.includes("consultoria")) {
    return (
      <>
        <PageHeader title="Equipe" />
        <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
          <div className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-8 text-center">
            <div className="w-12 h-12 rounded-full bg-[var(--brand-blue-subtle,#eff6ff)] flex items-center justify-center mx-auto mb-4">
              <svg
                aria-hidden="true"
                className="w-6 h-6 text-[var(--brand-blue)]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-[var(--ink)] mb-2">
              Gestão de Equipe
            </h2>
            <p className="text-sm text-[var(--ink-secondary)] mb-6">
              O gerenciamento de equipes está disponível no SmartLic Consultoria. Convide colaboradores,
              gerencie permissões e compartilhe análises em um só lugar.
            </p>
            <Link
              href="/planos"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-button
                         bg-[var(--brand-blue)] text-white text-sm font-medium
                         hover:opacity-90 transition-opacity"
            >
              Ver opções
            </Link>
          </div>
        </main>
      </>
    );
  }

  // ─── Loading skeleton ───────────────────────────────────────────────────────

  if (loadingOrg || planLoading) {
    return (
      <>
        <PageHeader title="Equipe" />
        <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-16 bg-[var(--surface-1)] rounded-card animate-pulse"
            />
          ))}
        </main>
      </>
    );
  }

  // ─── Error state ────────────────────────────────────────────────────────────

  if (orgError) {
    return (
      <>
        <PageHeader title="Equipe" />
        <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
          <div className="bg-[var(--error-subtle,#fee2e2)] border border-[var(--error,#dc2626)] rounded-card p-4 text-sm text-[var(--error,#dc2626)]">
            {orgError}
          </div>
          <button
            onClick={fetchOrg}
            className="mt-4 px-4 py-2 rounded-button border border-[var(--border)]
                       text-[var(--ink)] text-sm hover:bg-[var(--surface-1)] transition-colors"
          >
            Tentar novamente
          </button>
        </main>
      </>
    );
  }

  // ─── No org state ───────────────────────────────────────────────────────────

  if (!org) {
    return (
      <>
        <PageHeader title="Equipe" />
        <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
          <div className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-8 text-center">
            <div className="w-12 h-12 rounded-full bg-[var(--surface-1)] flex items-center justify-center mx-auto mb-4">
              <svg
                aria-hidden="true"
                className="w-6 h-6 text-[var(--ink-secondary)]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-[var(--ink)] mb-2">
              Nenhuma organização encontrada
            </h2>
            <p className="text-sm text-[var(--ink-secondary)]">
              Entre em contato com o suporte para configurar sua organização.
            </p>
          </div>
        </main>
      </>
    );
  }

  // ─── Main content ───────────────────────────────────────────────────────────

  const acceptedCount = org.members.filter((m) => m.status === "accepted").length;
  const pendingCount = org.members.filter((m) => m.status === "pending").length;
  const totalCount = org.members.length;
  const maxSeats = org.max_seats;
  const slotsUsed = acceptedCount;
  const canInvite = totalCount < maxSeats;

  // Determine current user's role
  const myEmail = session?.user?.email ?? "";
  const myMember = org.members.find(
    (m) => m.email.toLowerCase() === myEmail.toLowerCase(),
  );
  const isOwnerOrAdmin = myMember?.role === "owner" || myMember?.role === "admin";

  return (
    <>
      <PageHeader title="Equipe" />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        {/* Header card */}
        <div className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-5 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-[var(--ink)]">{org.name}</h2>
              <div className="flex items-center gap-3 mt-1">
                {/* Slot counter */}
                <span className="text-sm text-[var(--ink-secondary)]">
                  <span
                    className={`font-medium ${slotsUsed >= maxSeats ? "text-[var(--error,#dc2626)]" : "text-[var(--ink)]"}`}
                  >
                    {slotsUsed}
                  </span>
                  /{maxSeats} membros
                </span>
                {pendingCount > 0 && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--warning-subtle,#fef3cd)] text-[var(--warning,#856404)]">
                    {pendingCount} pendente{pendingCount > 1 ? "s" : ""}
                  </span>
                )}
              </div>
            </div>

            {/* Invite button — only for owner/admin, only if slots available */}
            {isOwnerOrAdmin && (
              <button
                onClick={() => setShowInviteModal(true)}
                disabled={!canInvite}
                title={!canInvite ? `Limite de ${maxSeats} membros atingido` : undefined}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-button
                           bg-[var(--brand-blue)] text-white text-sm font-medium
                           hover:opacity-90 transition-opacity
                           disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              >
                <svg
                  aria-hidden="true"
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Convidar membro
              </button>
            )}
          </div>

          {/* Slot progress bar */}
          <div className="mt-4">
            <div className="h-1.5 rounded-full bg-[var(--surface-1)] overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  slotsUsed >= maxSeats ? "bg-[var(--error,#dc2626)]" : "bg-[var(--brand-blue)]"
                }`}
                style={{ width: `${Math.min((slotsUsed / maxSeats) * 100, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Remove error */}
        {removeError && (
          <div
            role="alert"
            className="mb-4 p-3 bg-[var(--error-subtle,#fee2e2)] text-[var(--error,#dc2626)] rounded-card text-sm"
          >
            {removeError}
          </div>
        )}

        {/* Members list */}
        <div className="space-y-2">
          {org.members.map((member) => {
            const isMe = member.email.toLowerCase() === myEmail.toLowerCase();
            const isOwner = member.role === "owner";
            const isPending = member.status === "pending";
            const isConfirmingRemove = confirmRemoveId === member.id;
            const isRemoving = removingId === member.id;

            return (
              <div
                key={member.id}
                className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-4
                           flex flex-col sm:flex-row sm:items-center gap-3"
              >
                {/* Avatar */}
                <div
                  className="w-9 h-9 rounded-full bg-[var(--brand-blue-subtle,#eff6ff)]
                               flex items-center justify-center flex-shrink-0"
                  aria-hidden="true"
                >
                  <span className="text-sm font-semibold text-[var(--brand-blue)]">
                    {(member.name ?? member.email).charAt(0).toUpperCase()}
                  </span>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-[var(--ink)] truncate">
                      {member.name ?? member.email}
                      {isMe && (
                        <span className="ml-1 text-xs text-[var(--ink-secondary)]">(você)</span>
                      )}
                    </span>

                    {/* Role badge */}
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROLE_COLORS[member.role] ?? ROLE_COLORS.member}`}
                    >
                      {ROLE_LABELS[member.role] ?? member.role}
                    </span>

                    {/* Status badge */}
                    {isPending && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--warning-subtle,#fef3cd)] text-[var(--warning,#856404)]">
                        Pendente
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-[var(--ink-secondary)] mt-0.5 truncate">
                    {member.name ? member.email : null}
                    {member.name ? " • " : null}
                    {isPending
                      ? `Convidado em ${formatDate(member.invited_at)}`
                      : member.joined_at
                        ? `Membro desde ${formatDate(member.joined_at)}`
                        : null}
                  </p>
                </div>

                {/* Remove controls — only owner/admin can remove, never remove owner, never remove self */}
                {isOwnerOrAdmin && !isOwner && !isMe && (
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {isConfirmingRemove ? (
                      <>
                        <span className="text-xs text-[var(--ink-secondary)]">Confirmar remoção?</span>
                        <button
                          onClick={() => {
                            setConfirmRemoveId(null);
                            setRemoveError(null);
                          }}
                          disabled={isRemoving}
                          className="text-xs px-3 py-1.5 rounded-button border border-[var(--border)]
                                     text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors
                                     disabled:opacity-50"
                        >
                          Cancelar
                        </button>
                        <button
                          onClick={() => handleRemoveMember(member.id)}
                          disabled={isRemoving}
                          className="text-xs px-3 py-1.5 rounded-button
                                     bg-[var(--error,#dc2626)] text-white
                                     hover:opacity-90 transition-opacity
                                     disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isRemoving ? "Removendo..." : "Remover"}
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => {
                          setConfirmRemoveId(member.id);
                          setRemoveError(null);
                        }}
                        className="text-xs px-3 py-1.5 rounded-button border border-[var(--error,#dc2626)]
                                   text-[var(--error,#dc2626)] hover:bg-[var(--error-subtle,#fee2e2)]
                                   transition-colors"
                      >
                        Remover
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Empty members state */}
        {org.members.length === 0 && (
          <div className="text-center py-12 text-[var(--ink-secondary)] text-sm">
            Nenhum membro encontrado. Convide o primeiro membro da sua equipe.
          </div>
        )}
      </main>

      {/* Invite modal */}
      <InviteMemberModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        onInviteSent={fetchOrg}
        accessToken={accessToken}
        orgId={org.id}
      />
    </>
  );
}
