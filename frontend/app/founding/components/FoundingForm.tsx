'use client';

import { useState } from 'react';

type Status = 'idle' | 'loading' | 'success' | 'error';

interface FoundingCheckoutResponse {
  checkout_url: string;
  lead_id: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MOTIVO_MIN = 140;
const MOTIVO_MAX = 1000;

function cleanCnpj(raw: string): string {
  return raw.replace(/\D/g, '');
}

function formatCnpj(raw: string): string {
  const digits = cleanCnpj(raw).slice(0, 14);
  if (digits.length <= 2) return digits;
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
  if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
  if (digits.length <= 12)
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}

function trackEvent(name: string, props?: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  const mp = (window as unknown as { mixpanel?: { track: (e: string, p?: Record<string, unknown>) => void } }).mixpanel;
  if (!mp) return;
  try {
    mp.track(name, props ?? {});
  } catch {
    // best-effort; never break UX on analytics failure.
  }
}

export default function FoundingForm() {
  const [email, setEmail] = useState('');
  const [nome, setNome] = useState('');
  const [cnpj, setCnpj] = useState('');
  const [razaoSocial, setRazaoSocial] = useState('');
  const [motivo, setMotivo] = useState('');

  const [status, setStatus] = useState<Status>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  function validate(): string | null {
    if (!email.trim() || !EMAIL_RE.test(email.trim())) return 'Informe um email corporativo valido.';
    if (!nome.trim() || nome.trim().length < 2) return 'Informe seu nome completo.';
    const cnpjDigits = cleanCnpj(cnpj);
    if (cnpjDigits.length !== 14) return 'CNPJ deve ter 14 dígitos.';
    if (motivo.trim().length < MOTIVO_MIN) return `Conte-nos um pouco mais (mínimo ${MOTIVO_MIN} caracteres).`;
    if (motivo.trim().length > MOTIVO_MAX) return `Máximo ${MOTIVO_MAX} caracteres.`;
    return null;
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const v = validate();
    if (v) {
      setErrorMsg(v);
      setStatus('error');
      return;
    }

    setStatus('loading');
    setErrorMsg('');
    trackEvent('founding_form_submitted', { cnpj_length: cleanCnpj(cnpj).length });

    try {
      const res = await fetch('/api/founding/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          nome: nome.trim(),
          cnpj: cleanCnpj(cnpj),
          razao_social: razaoSocial.trim() || null,
          motivo: motivo.trim(),
        }),
      });

      if (!res.ok) {
        let msg = 'Nao foi possivel iniciar seu checkout. Tente novamente em instantes.';
        try {
          const data = await res.json();
          if (typeof data?.detail === 'string') msg = data.detail;
        } catch {
          // ignore JSON parse errors — keep default message
        }
        setErrorMsg(msg);
        setStatus('error');
        return;
      }

      const data = (await res.json()) as FoundingCheckoutResponse;
      trackEvent('founding_checkout_started', { lead_id: data.lead_id });
      window.location.href = data.checkout_url;
    } catch {
      setErrorMsg('Falha de rede. Verifique sua conexao e tente novamente.');
      setStatus('error');
    }
  }

  const loading = status === 'loading';
  const motivoLen = motivo.trim().length;

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="founding-nome" className="block text-sm font-medium text-slate-900">
          Seu nome completo
        </label>
        <input
          id="founding-nome"
          type="text"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          required
          maxLength={200}
          className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
      </div>

      <div>
        <label htmlFor="founding-email" className="block text-sm font-medium text-slate-900">
          Email corporativo
        </label>
        <input
          id="founding-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          maxLength={320}
          className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
      </div>

      <div>
        <label htmlFor="founding-cnpj" className="block text-sm font-medium text-slate-900">
          CNPJ
        </label>
        <input
          id="founding-cnpj"
          type="text"
          inputMode="numeric"
          value={cnpj}
          onChange={(e) => setCnpj(formatCnpj(e.target.value))}
          required
          placeholder="00.000.000/0000-00"
          className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
      </div>

      <div>
        <label htmlFor="founding-razao" className="block text-sm font-medium text-slate-900">
          Razão social <span className="text-slate-500 font-normal">(opcional)</span>
        </label>
        <input
          id="founding-razao"
          type="text"
          value={razaoSocial}
          onChange={(e) => setRazaoSocial(e.target.value)}
          maxLength={300}
          className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
      </div>

      <div>
        <label htmlFor="founding-motivo" className="block text-sm font-medium text-slate-900">
          Por que o SmartLic é relevante para você?
        </label>
        <textarea
          id="founding-motivo"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          required
          minLength={MOTIVO_MIN}
          maxLength={MOTIVO_MAX}
          rows={4}
          className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <p className="mt-1 text-xs text-slate-500" data-testid="founding-motivo-counter">
          {motivoLen}/{MOTIVO_MAX} caracteres (mínimo {MOTIVO_MIN})
        </p>
      </div>

      {status === 'error' && errorMsg && (
        <div role="alert" className="rounded bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-800">
          {errorMsg}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        {loading ? 'Processando...' : 'Quero ser um founding partner'}
      </button>
    </form>
  );
}
