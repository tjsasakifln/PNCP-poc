"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../components/AuthProvider";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";

interface Partner {
  id: string;
  name: string;
  slug: string;
  contact_email: string;
  contact_name: string | null;
  revenue_share_pct: number;
  status: string;
  stripe_coupon_id: string | null;
  created_at: string;
  referrals_total?: number;
  referrals_active?: number;
  monthly_share?: number;
}

interface Referral {
  id: string;
  signup_at: string;
  converted_at: string | null;
  churned_at: string | null;
  monthly_revenue: number | null;
  revenue_share_amount: number | null;
  profiles?: { email: string; full_name: string | null };
}

interface RevenueReport {
  partner_name: string;
  total_revenue: number;
  share_amount: number;
  active_clients: number;
  share_pct: number;
}

export default function AdminPartnersPage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const router = useRouter();
  const [partners, setPartners] = useState<Partner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create partner form
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    slug: "",
    contact_email: "",
    contact_name: "",
    revenue_share_pct: 25,
  });
  const [creating, setCreating] = useState(false);

  // Detail view
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [revenue, setRevenue] = useState<RevenueReport | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Auth guard
  useEffect(() => {
    if (!authLoading && !isAdmin) router.push("/");
  }, [authLoading, isAdmin, router]);

  const fetchPartners = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true);
    try {
      const res = await fetch("/api/admin/partners", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error("Falha ao carregar parceiros");
      const data = await res.json();
      setPartners(data.partners || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    fetchPartners();
  }, [fetchPartners]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.access_token) return;
    setCreating(true);
    try {
      const res = await fetch("/api/admin/partners", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(createForm),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao criar parceiro");
      }
      toast.success("Parceiro criado com sucesso");
      setShowCreate(false);
      setCreateForm({ name: "", slug: "", contact_email: "", contact_name: "", revenue_share_pct: 25 });
      fetchPartners();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao criar parceiro");
    } finally {
      setCreating(false);
    }
  };

  const handlePartnerDetail = async (partner: Partner) => {
    if (!session?.access_token) return;
    setSelectedPartner(partner);
    setDetailLoading(true);
    try {
      const [refsRes, revRes] = await Promise.all([
        fetch(`/api/admin/partners/${partner.id}/referrals`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        }),
        fetch(`/api/admin/partners/${partner.id}/revenue`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        }),
      ]);
      if (refsRes.ok) {
        const refsData = await refsRes.json();
        setReferrals(refsData.referrals || []);
      }
      if (revRes.ok) {
        const revData = await revRes.json();
        setRevenue(revData);
      }
    } catch {
      toast.error("Erro ao carregar detalhes do parceiro");
    } finally {
      setDetailLoading(false);
    }
  };

  // AC18: CSV Export
  const handleExportCSV = () => {
    if (!partners.length) return;
    const headers = ["Nome", "Slug", "Email", "Referrals Ativos", "Share Mensal (R$)", "Status"];
    const rows = partners.map((p) => [
      p.name,
      p.slug,
      p.contact_email,
      String(p.referrals_active || 0),
      String(p.monthly_share?.toFixed(2) || "0.00"),
      p.status,
    ]);
    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `partners_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatCurrency = (value: number) =>
    `R$ ${value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="w-8 h-8 border-4 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAdmin) return null;

  return (
    <div className="min-h-screen bg-[var(--canvas)] p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/admin" className="text-sm text-[var(--brand-blue)] hover:underline mb-2 inline-block">
              &larr; Admin
            </Link>
            <h1 className="text-2xl font-bold text-[var(--ink)]">Parceiros & Revenue Share</h1>
            <p className="text-sm text-[var(--ink-secondary)]">
              STORY-323 — Gestão de consultorias parceiras
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleExportCSV}
              className="px-4 py-2 text-sm border border-[var(--border)] rounded-button hover:bg-[var(--surface-1)] transition-colors"
            >
              Exportar CSV
            </button>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-4 py-2 text-sm bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors"
            >
              {showCreate ? "Cancelar" : "Novo Parceiro"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-[var(--error-subtle)] text-[var(--error)] rounded-card">
            {error}
          </div>
        )}

        {/* Create Partner Form */}
        {showCreate && (
          <div className="mb-8 p-6 bg-[var(--surface-0)] rounded-card border border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Novo Parceiro</h2>
            <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Nome da Consultoria</label>
                <input
                  type="text"
                  required
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]"
                  placeholder="Triunfo Legis"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Slug (URL)</label>
                <input
                  type="text"
                  required
                  value={createForm.slug}
                  onChange={(e) => setCreateForm({ ...createForm, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]"
                  placeholder="triunfo-legis"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Email de Contato</label>
                <input
                  type="email"
                  required
                  value={createForm.contact_email}
                  onChange={(e) => setCreateForm({ ...createForm, contact_email: e.target.value })}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]"
                  placeholder="contato@consultoria.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Nome do Contato</label>
                <input
                  type="text"
                  value={createForm.contact_name}
                  onChange={(e) => setCreateForm({ ...createForm, contact_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]"
                  placeholder="João Silva"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Revenue Share (%)</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={0.01}
                  value={createForm.revenue_share_pct}
                  onChange={(e) => setCreateForm({ ...createForm, revenue_share_pct: parseFloat(e.target.value) || 25 })}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={creating}
                  className="px-6 py-2 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] disabled:opacity-50"
                >
                  {creating ? "Criando..." : "Criar Parceiro"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Partners Table */}
        <div className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] bg-[var(--surface-1)]">
                <th className="text-left px-4 py-3 font-medium text-[var(--ink-secondary)]">Parceiro</th>
                <th className="text-left px-4 py-3 font-medium text-[var(--ink-secondary)]">Email</th>
                <th className="text-center px-4 py-3 font-medium text-[var(--ink-secondary)]">Referrals</th>
                <th className="text-center px-4 py-3 font-medium text-[var(--ink-secondary)]">Ativos</th>
                <th className="text-right px-4 py-3 font-medium text-[var(--ink-secondary)]">Share/Mês</th>
                <th className="text-center px-4 py-3 font-medium text-[var(--ink-secondary)]">Status</th>
                <th className="text-center px-4 py-3 font-medium text-[var(--ink-secondary)]">Ações</th>
              </tr>
            </thead>
            <tbody>
              {partners.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-[var(--ink-muted)]">
                    Nenhum parceiro cadastrado
                  </td>
                </tr>
              ) : (
                partners.map((p) => (
                  <tr key={p.id} className="border-b border-[var(--border)] hover:bg-[var(--surface-1)] transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-[var(--ink)]">{p.name}</p>
                      <p className="text-xs text-[var(--ink-muted)]">{p.slug}</p>
                    </td>
                    <td className="px-4 py-3 text-[var(--ink-secondary)]">{p.contact_email}</td>
                    <td className="px-4 py-3 text-center">{p.referrals_total || 0}</td>
                    <td className="px-4 py-3 text-center font-medium">{p.referrals_active || 0}</td>
                    <td className="px-4 py-3 text-right font-medium text-emerald-600">
                      {formatCurrency(p.monthly_share || 0)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        p.status === "active"
                          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                          : p.status === "pending"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-gray-100 text-gray-600"
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handlePartnerDetail(p)}
                        className="text-[var(--brand-blue)] hover:underline text-xs"
                      >
                        Detalhes
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Partner Detail Modal */}
        {selectedPartner && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-[var(--surface-0)] rounded-card shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-[var(--ink)]">{selectedPartner.name}</h2>
                    <p className="text-sm text-[var(--ink-secondary)]">{selectedPartner.contact_email}</p>
                  </div>
                  <button
                    onClick={() => { setSelectedPartner(null); setReferrals([]); setRevenue(null); }}
                    className="p-2 hover:bg-[var(--surface-1)] rounded-full transition-colors text-[var(--ink-muted)]"
                    aria-label="Fechar"
                  >
                    &#10005;
                  </button>
                </div>

                {detailLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="w-6 h-6 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : (
                  <>
                    {/* Revenue Summary */}
                    {revenue && (
                      <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="p-4 bg-[var(--surface-1)] rounded-card text-center">
                          <p className="text-2xl font-bold text-[var(--ink)]">{revenue.active_clients}</p>
                          <p className="text-xs text-[var(--ink-muted)]">Clientes ativos</p>
                        </div>
                        <div className="p-4 bg-[var(--surface-1)] rounded-card text-center">
                          <p className="text-2xl font-bold text-[var(--ink)]">{formatCurrency(revenue.total_revenue)}</p>
                          <p className="text-xs text-[var(--ink-muted)]">Receita total</p>
                        </div>
                        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 rounded-card text-center">
                          <p className="text-2xl font-bold text-emerald-600">{formatCurrency(revenue.share_amount)}</p>
                          <p className="text-xs text-emerald-700 dark:text-emerald-400">Share ({revenue.share_pct}%)</p>
                        </div>
                      </div>
                    )}

                    {/* Referrals Table */}
                    <h3 className="text-sm font-semibold text-[var(--ink)] mb-3">Clientes Indicados</h3>
                    <div className="border border-[var(--border)] rounded-card overflow-hidden">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-[var(--border)] bg-[var(--surface-1)]">
                            <th className="text-left px-3 py-2">Usuário</th>
                            <th className="text-left px-3 py-2">Cadastro</th>
                            <th className="text-left px-3 py-2">Conversão</th>
                            <th className="text-right px-3 py-2">Receita</th>
                            <th className="text-right px-3 py-2">Share</th>
                            <th className="text-center px-3 py-2">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {referrals.length === 0 ? (
                            <tr>
                              <td colSpan={6} className="text-center py-6 text-[var(--ink-muted)]">
                                Nenhum referral encontrado
                              </td>
                            </tr>
                          ) : (
                            referrals.map((r) => (
                              <tr key={r.id} className="border-b border-[var(--border)]">
                                <td className="px-3 py-2 text-[var(--ink)]">
                                  {r.profiles?.full_name || r.profiles?.email || "—"}
                                </td>
                                <td className="px-3 py-2 text-[var(--ink-secondary)]">
                                  {r.signup_at ? new Date(r.signup_at).toLocaleDateString("pt-BR") : "—"}
                                </td>
                                <td className="px-3 py-2 text-[var(--ink-secondary)]">
                                  {r.converted_at ? new Date(r.converted_at).toLocaleDateString("pt-BR") : "—"}
                                </td>
                                <td className="px-3 py-2 text-right">
                                  {r.monthly_revenue ? formatCurrency(r.monthly_revenue) : "—"}
                                </td>
                                <td className="px-3 py-2 text-right text-emerald-600">
                                  {r.revenue_share_amount ? formatCurrency(r.revenue_share_amount) : "—"}
                                </td>
                                <td className="px-3 py-2 text-center">
                                  <span className={`inline-block px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                                    r.churned_at
                                      ? "bg-red-100 text-red-700"
                                      : r.converted_at
                                      ? "bg-emerald-100 text-emerald-700"
                                      : "bg-gray-100 text-gray-600"
                                  }`}>
                                    {r.churned_at ? "churned" : r.converted_at ? "ativo" : "signup"}
                                  </span>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
