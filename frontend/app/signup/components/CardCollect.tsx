/**
 * CardCollect — Stripe PaymentElement for pre-signup card capture
 * (STORY-CONV-003b AC1 + AC2).
 *
 * Flow:
 * 1. Parent renders `<CardCollect />` after step-1 form is valid and the
 *    user is on the "card" rollout branch.
 * 2. CardCollect fetches `POST /v1/billing/setup-intent`, receives
 *    `{ client_secret, publishable_key }`.
 * 3. Mounts `<Elements options={{ clientSecret }} stripe={stripePromise}>`
 *    wrapping `<PaymentForm />` which owns `<PaymentElement />`.
 * 4. User submits → `stripe.confirmSetup({ redirect: 'if_required' })`
 *    returns the SetupIntent with `payment_method` (string id).
 * 5. We lift `payment_method_id` to the parent via `onCardReady`. Parent
 *    then POSTs `/v1/auth/signup` with it.
 *
 * Errors surface via `toast.error` + inline message. Submit button is
 * disabled until Stripe Elements signal `complete`.
 */
"use client";

import { useEffect, useState } from "react";
import {
  Elements,
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import type { StripePaymentElementChangeEvent } from "@stripe/stripe-js";
import { toast } from "sonner";
import { getStripePromise } from "../../../lib/stripe-client";
import { TrialTermsNotice } from "./TrialTermsNotice";

type CardCollectProps = {
  onCardReady: (paymentMethodId: string) => void | Promise<void>;
  onBack?: () => void;
  loading?: boolean;
  submitLabel?: string;
};

type SetupIntentPayload = {
  client_secret: string;
  publishable_key: string;
};

/**
 * Inner form that has access to the `useStripe` / `useElements` hooks —
 * these only work inside `<Elements>`.
 */
function PaymentForm({ onCardReady, onBack, loading, submitLabel }: CardCollectProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [complete, setComplete] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onChange = (ev: StripePaymentElementChangeEvent) => {
    setComplete(ev.complete);
    if (ev.complete) setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stripe || !elements || !complete) return;
    setSubmitting(true);
    setError(null);

    try {
      // FE submit validates Elements state before confirmSetup.
      const submitResult = await elements.submit();
      if (submitResult.error) {
        const message = submitResult.error.message || "Erro ao validar cartão.";
        setError(message);
        return;
      }

      const { error: setupError, setupIntent } = await stripe.confirmSetup({
        elements,
        redirect: "if_required",
      });

      if (setupError) {
        const message = setupError.message || "Cartão recusado. Tente outro.";
        setError(message);
        toast.error(message);
        return;
      }

      const pmId =
        typeof setupIntent?.payment_method === "string"
          ? setupIntent.payment_method
          : setupIntent?.payment_method?.id;

      if (!pmId) {
        const message = "Não foi possível validar o cartão. Tente novamente.";
        setError(message);
        toast.error(message);
        return;
      }

      await onCardReady(pmId);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Erro inesperado ao validar cartão.";
      setError(message);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const busy = submitting || loading;

  return (
    <form onSubmit={handleSubmit} className="space-y-4" data-testid="card-collect-form">
      <TrialTermsNotice />
      <PaymentElement onChange={onChange} />
      {error && (
        <p role="alert" className="text-sm text-red-600" data-testid="card-collect-error">
          {error}
        </p>
      )}
      <div className="flex gap-2">
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            disabled={busy}
            className="flex-1 py-2 px-4 border border-ink-secondary rounded-input text-ink"
          >
            Voltar
          </button>
        )}
        <button
          type="submit"
          disabled={!complete || !stripe || busy}
          className="flex-1 py-2 px-4 bg-brand-blue text-white rounded-input disabled:opacity-50"
          data-testid="card-collect-submit"
        >
          {busy ? "Processando…" : submitLabel ?? "Criar conta com trial"}
        </button>
      </div>
    </form>
  );
}

export default function CardCollect(props: CardCollectProps) {
  const [payload, setPayload] = useState<SetupIntentPayload | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/billing/setup-intent", { method: "POST" });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body?.detail ?? `setup-intent failed (${res.status})`);
        }
        const data: SetupIntentPayload = await res.json();
        if (!cancelled) setPayload(data);
      } catch (err: unknown) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Erro ao iniciar pagamento.";
          setLoadError(msg);
          toast.error(msg);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loadError) {
    return (
      <div role="alert" className="p-4 text-sm text-red-600" data-testid="card-collect-load-error">
        {loadError}
      </div>
    );
  }

  if (!payload) {
    return (
      <div
        className="p-4 text-center text-sm text-ink-secondary"
        data-testid="card-collect-loading"
      >
        Preparando coleta segura de cartão…
      </div>
    );
  }

  const stripePromise = getStripePromise(payload.publishable_key);

  return (
    <Elements
      stripe={stripePromise}
      options={{ clientSecret: payload.client_secret, appearance: { theme: "stripe" } }}
    >
      <PaymentForm {...props} />
    </Elements>
  );
}
