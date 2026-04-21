/**
 * /conta/cancelar-trial — one-click cancel page (STORY-CONV-003c AC7).
 *
 * Arrives via link in the D-1 trial email (AC1) — token is signed by the
 * backend with TRIAL_CANCEL_JWT_SECRET (48h TTL, action="cancel_trial").
 *
 * Flow:
 * 1. GET /api/conta/cancelar-trial?token=<jwt> → fetches trial metadata
 *    (user email, plan_name, trial_end_ts, already_cancelled).
 * 2. Show "Confirmar cancelamento" — explicit confirm prevents accidental
 *    cancel from link previews / browser prefetch.
 * 3. POST /api/conta/cancelar-trial with { token } — backend cancels
 *    Stripe subscription (no proration, access keeps until trial_end_ts).
 * 4. Redirect to /conta/cancelar-trial/confirmado on success.
 */
"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";

type TrialInfo = {
  user_id: string;
  email: string;
  plan_name: string;
  trial_end_ts: number;
  already_cancelled: boolean;
};

function CancelTrialView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [info, setInfo] = useState<TrialInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!token) {
        setError("Token de cancelamento ausente. Abra o link do email original.");
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(
          `/api/conta/cancelar-trial?token=${encodeURIComponent(token)}`,
        );
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body?.detail ?? `Erro ${res.status}`);
        }
        const data: TrialInfo = await res.json();
        if (!cancelled) {
          setInfo(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Link de cancelamento inválido ou expirado.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const handleCancel = async () => {
    if (!token || submitting) return;
    setSubmitting(true);
    try {
      const res = await fetch("/api/conta/cancelar-trial", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail ?? `Erro ${res.status}`);
      }
      toast.success("Trial cancelada com sucesso.");
      router.push("/conta/cancelar-trial/confirmado");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Não foi possível cancelar agora. Tente novamente em instantes.";
      setError(msg);
      toast.error(msg);
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center text-ink-secondary" data-testid="cancel-trial-loading">
        Validando link de cancelamento…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-md mx-auto" data-testid="cancel-trial-error">
        <h1 className="text-xl font-semibold text-ink mb-3">Link inválido</h1>
        <p role="alert" className="text-sm text-red-700 bg-red-50 p-3 rounded mb-4">
          {error}
        </p>
        <p className="text-sm text-ink-secondary">
          Se você chegou aqui pelo email, o link pode ter expirado (48h). Abra{" "}
          <Link href="/conta" className="underline">
            sua conta
          </Link>{" "}
          para cancelar manualmente, ou responda o email para suporte.
        </p>
      </div>
    );
  }

  if (!info) return null;

  const trialEnd = new Date(info.trial_end_ts * 1000).toLocaleDateString("pt-BR");

  if (info.already_cancelled) {
    return (
      <div className="p-6 max-w-md mx-auto" data-testid="cancel-trial-already-cancelled">
        <h1 className="text-xl font-semibold text-ink mb-3">Trial já cancelada</h1>
        <p className="text-sm text-ink-secondary mb-4">
          Sua trial do plano <strong>{info.plan_name}</strong> já foi cancelada. Você mantém
          acesso até {trialEnd}.
        </p>
        <Link
          href="/buscar"
          className="inline-block py-2 px-4 bg-brand-blue text-white rounded-input"
        >
          Continuar usando SmartLic
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-md mx-auto" data-testid="cancel-trial-confirm">
      <h1 className="text-xl font-semibold text-ink mb-3">Cancelar trial</h1>
      <p className="text-sm text-ink-secondary mb-4">
        Você está cancelando a trial de <strong>{info.plan_name}</strong> para a conta{" "}
        <strong>{info.email}</strong>.
      </p>
      <div className="mb-4 p-3 bg-surface-1 rounded-input text-xs text-ink-secondary space-y-1">
        <p>
          ✓ Nenhuma cobrança será feita em {trialEnd}.
        </p>
        <p>
          ✓ Você continua com acesso completo até {trialEnd}.
        </p>
        <p>
          ✓ Nenhum dado da sua conta será apagado — você pode reativar depois.
        </p>
      </div>
      <div className="flex gap-2">
        <Link
          href="/buscar"
          className="flex-1 text-center py-2 px-4 border border-ink-secondary rounded-input text-ink"
        >
          Manter assinatura
        </Link>
        <button
          type="button"
          onClick={handleCancel}
          disabled={submitting}
          className="flex-1 py-2 px-4 bg-red-600 text-white rounded-input disabled:opacity-50"
          data-testid="cancel-trial-submit"
        >
          {submitting ? "Cancelando…" : "Confirmar cancelamento"}
        </button>
      </div>
    </div>
  );
}

export default function CancelTrialPage() {
  // useSearchParams requires a Suspense boundary in Next 14+ App Router.
  return (
    <Suspense fallback={<div className="p-6 text-center">Carregando…</div>}>
      <CancelTrialView />
    </Suspense>
  );
}
