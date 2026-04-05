"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Copy, Gift, Users, CheckCircle2, TrendingUp } from "lucide-react";
import { useAuth } from "../components/AuthProvider";
import { PageHeader } from "../../components/PageHeader";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";

interface ReferralCodeResponse {
  code: string;
  share_url: string;
}

interface ReferralStatsResponse {
  code: string;
  total_signups: number;
  total_converted: number;
  credits_earned_months: number;
}

export default function IndicarPage() {
  const { session, loading: authLoading } = useAuth();
  const router = useRouter();

  const [codeData, setCodeData] = useState<ReferralCodeResponse | null>(null);
  const [stats, setStats] = useState<ReferralStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!authLoading && !session) {
      router.replace("/login?redirect=/indicar");
    }
  }, [authLoading, session, router]);

  const fetchData = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true);
    setError(null);
    try {
      const headers = { Authorization: `Bearer ${session.access_token}` };
      const [codeRes, statsRes] = await Promise.all([
        fetch("/api/referral/code", { headers }),
        fetch("/api/referral/stats", { headers }),
      ]);

      if (!codeRes.ok) throw new Error("Erro ao obter código");
      if (!statsRes.ok) throw new Error("Erro ao obter estatísticas");

      setCodeData(await codeRes.json());
      setStats(await statsRes.json());
    } catch (e) {
      console.error("[indicar] fetch failed", e);
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    if (session?.access_token) {
      fetchData();
    }
  }, [session, fetchData]);

  const handleCopyLink = async () => {
    if (!codeData?.share_url) return;
    try {
      await navigator.clipboard.writeText(codeData.share_url);
      toast.success("Link copiado! Cole onde quiser compartilhar.");
    } catch {
      toast.error("Não foi possível copiar. Copie manualmente.");
    }
  };

  const handleCopyCode = async () => {
    if (!codeData?.code) return;
    try {
      await navigator.clipboard.writeText(codeData.code);
      toast.success("Código copiado!");
    } catch {
      toast.error("Não foi possível copiar.");
    }
  };

  if (authLoading || !session) {
    return <AuthLoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-canvas">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <PageHeader title="Indique o SmartLic" />
        <p className="text-ink-secondary text-sm mb-6">
          Ganhe 1 mês grátis a cada amigo que assinar. Sem limite.
        </p>

        {/* Hero card */}
        <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950/30 dark:to-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-card p-6 md:p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-600 rounded-full flex items-center justify-center">
              <Gift className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-display font-bold text-ink mb-2">
                1 mês grátis por cada indicação que converter
              </h2>
              <p className="text-ink-secondary text-sm leading-relaxed">
                Compartilhe seu link com empresas que participam de licitações.
                Quando elas assinarem o SmartLic Pro, você recebe 30 dias de
                crédito automaticamente na sua próxima cobrança. Sem limite —
                quanto mais indica, mais meses ganha.
              </p>
            </div>
          </div>
        </div>

        {loading && (
          <div className="bg-surface-0 rounded-card shadow p-8 text-center text-ink-secondary">
            Carregando seu código...
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-card p-6 text-center">
            <p className="text-red-700 dark:text-red-300 mb-3">{error}</p>
            <button
              onClick={fetchData}
              className="text-sm text-red-700 dark:text-red-300 underline"
            >
              Tentar novamente
            </button>
          </div>
        )}

        {!loading && !error && codeData && (
          <>
            {/* Code card */}
            <div className="bg-surface-0 rounded-card shadow p-6 md:p-8 mb-6">
              <p className="text-xs uppercase tracking-wider text-ink-secondary mb-3">
                Seu código exclusivo
              </p>
              <div className="flex items-center justify-between gap-4 mb-6">
                <code
                  onClick={handleCopyCode}
                  className="text-3xl md:text-4xl font-mono font-bold text-emerald-600 dark:text-emerald-400 tracking-wider cursor-pointer select-all"
                  title="Clique para copiar"
                >
                  {codeData.code}
                </code>
                <button
                  onClick={handleCopyCode}
                  className="text-sm text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
                >
                  <Copy className="w-4 h-4" />
                  Copiar
                </button>
              </div>

              <p className="text-xs uppercase tracking-wider text-ink-secondary mb-2">
                Link para compartilhar
              </p>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={codeData.share_url}
                  className="flex-1 px-3 py-2 bg-canvas border border-border rounded-input text-sm font-mono text-ink"
                  onClick={(e) => (e.target as HTMLInputElement).select()}
                />
                <button
                  onClick={handleCopyLink}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-input text-sm font-semibold whitespace-nowrap flex items-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  Copiar link
                </button>
              </div>
            </div>

            {/* Stats cards */}
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-surface-0 rounded-card shadow p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <Users className="w-5 h-5 text-ink-secondary" />
                    <p className="text-xs uppercase tracking-wider text-ink-secondary">
                      Indicados
                    </p>
                  </div>
                  <p className="text-3xl font-bold text-ink">
                    {stats.total_signups}
                  </p>
                  <p className="text-xs text-ink-secondary mt-1">
                    Pessoas que se cadastraram
                  </p>
                </div>

                <div className="bg-surface-0 rounded-card shadow p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <TrendingUp className="w-5 h-5 text-ink-secondary" />
                    <p className="text-xs uppercase tracking-wider text-ink-secondary">
                      Convertidos
                    </p>
                  </div>
                  <p className="text-3xl font-bold text-ink">
                    {stats.total_converted}
                  </p>
                  <p className="text-xs text-ink-secondary mt-1">
                    Assinaram o SmartLic Pro
                  </p>
                </div>

                <div className="bg-surface-0 rounded-card shadow p-6 border-2 border-emerald-500">
                  <div className="flex items-center gap-3 mb-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <p className="text-xs uppercase tracking-wider text-emerald-600">
                      Créditos ganhos
                    </p>
                  </div>
                  <p className="text-3xl font-bold text-emerald-600">
                    {stats.credits_earned_months}{" "}
                    <span className="text-base font-normal">
                      {stats.credits_earned_months === 1 ? "mês" : "meses"}
                    </span>
                  </p>
                  <p className="text-xs text-ink-secondary mt-1">
                    Grátis na sua conta
                  </p>
                </div>
              </div>
            )}

            {/* How it works */}
            <div className="bg-surface-0 rounded-card shadow p-6">
              <h3 className="text-lg font-display font-bold text-ink mb-4">
                Como funciona
              </h3>
              <ol className="space-y-3 text-sm text-ink-secondary">
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 rounded-full flex items-center justify-center text-xs font-bold">
                    1
                  </span>
                  <span>
                    Compartilhe seu código ou link com quem conhece que
                    participa de licitações.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 rounded-full flex items-center justify-center text-xs font-bold">
                    2
                  </span>
                  <span>
                    Seu amigo se cadastra usando seu código e assina o SmartLic
                    Pro.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 rounded-full flex items-center justify-center text-xs font-bold">
                    3
                  </span>
                  <span>
                    Na sua próxima cobrança, 30 dias extras entram
                    automaticamente — sem ação sua.
                  </span>
                </li>
              </ol>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
