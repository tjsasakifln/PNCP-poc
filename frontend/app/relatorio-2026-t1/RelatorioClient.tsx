'use client';

import { useState, useRef, useEffect } from 'react';

type Cargo = 'diretor' | 'gerente' | 'analista' | 'consultor' | 'outro';
type Status = 'idle' | 'loading' | 'success' | 'error';

interface SuccessPayload {
  download_url: string;
  email_queued: boolean;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RelatorioClient() {
  const [email, setEmail] = useState('');
  const [empresa, setEmpresa] = useState('');
  const [cargo, setCargo] = useState<Cargo | ''>('');
  const [newsletterOptIn, setNewsletterOptIn] = useState(true);

  const [status, setStatus] = useState<Status>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [result, setResult] = useState<SuccessPayload | null>(null);

  const successRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (status === 'success' && successRef.current) {
      successRef.current.focus();
    }
  }, [status]);

  function validate(): string | null {
    if (!email.trim() || !EMAIL_RE.test(email.trim())) return 'Informe um email valido.';
    if (!empresa.trim() || empresa.trim().length < 2) return 'Informe o nome da sua empresa.';
    if (empresa.trim().length > 100) return 'Nome da empresa muito longo.';
    if (!cargo) return 'Selecione seu cargo.';
    return null;
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const v = validate();
    if (v) {
      setStatus('error');
      setErrorMsg(v);
      return;
    }

    setStatus('loading');
    setErrorMsg('');

    try {
      const res = await fetch('/api/relatorio/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          empresa: empresa.trim(),
          cargo,
          newsletter_opt_in: newsletterOptIn,
        }),
      });

      if (res.ok) {
        const data = (await res.json()) as SuccessPayload;
        setResult(data);
        setStatus('success');

        // Best-effort tracking — project uses Mixpanel via window.mixpanel
        // (see CalculadoraClient.tsx for the same pattern).
        if (typeof window !== 'undefined' && (window as unknown as { mixpanel?: { track: (e: string, p?: Record<string, unknown>) => void } }).mixpanel) {
          try {
            (window as unknown as { mixpanel: { track: (e: string, p?: Record<string, unknown>) => void } }).mixpanel.track('report_lead_captured', {
              source: 'panorama-2026-t1',
              cargo,
              newsletter_opt_in: newsletterOptIn,
            });
          } catch {
            // swallow — tracking must never break UX
          }
        }
        return;
      }

      if (res.status === 429) {
        setStatus('error');
        setErrorMsg('Muitas solicitacoes. Tente novamente em 1 minuto.');
        return;
      }

      if (res.status === 400) {
        let detail = 'Dados invalidos. Confira os campos e tente novamente.';
        try {
          const payload = await res.json();
          if (payload?.error && typeof payload.error === 'string') detail = payload.error;
          else if (payload?.detail && typeof payload.detail === 'string') detail = payload.detail;
        } catch {
          // ignore
        }
        setStatus('error');
        setErrorMsg(detail);
        return;
      }

      setStatus('error');
      setErrorMsg('Algo deu errado. Tente novamente.');
    } catch {
      setStatus('error');
      setErrorMsg('Falha de rede. Verifique sua conexao e tente novamente.');
    }
  }

  if (status === 'success' && result) {
    return (
      <div
        ref={successRef}
        tabIndex={-1}
        aria-live="polite"
        className="not-prose bg-gradient-to-br from-green-50 to-blue-50 border-2 border-green-500 rounded-2xl p-8 text-center shadow-lg focus:outline-none"
      >
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500 text-white text-3xl font-bold mb-4">
          ✓
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Relatorio pronto para download</h3>
        <p className="text-gray-700 mb-6">
          Tambem enviamos uma copia para <strong>{email}</strong>. Verifique sua caixa de entrada em instantes.
        </p>
        <a
          href={result.download_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block py-4 px-8 rounded-xl font-bold text-lg text-white bg-green-600 hover:bg-green-700 transition-colors shadow-lg"
        >
          Baixar PDF agora
        </a>
        <p className="mt-4 text-sm text-gray-500">PDF · ~4 MB · 32 paginas</p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="not-prose bg-white border border-gray-200 rounded-2xl p-8 shadow-sm max-w-xl mx-auto"
      noValidate
    >
      <h3 className="text-xl font-bold text-gray-900 mb-1">Receba o relatorio gratuito</h3>
      <p className="text-sm text-gray-600 mb-6">
        Download imediato + copia por email. Sem spam.
      </p>

      <div className="space-y-4">
        <div>
          <label htmlFor="rel-email" className="block text-sm font-semibold text-gray-700 mb-1">
            Email corporativo *
          </label>
          <input
            id="rel-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="voce@empresa.com.br"
          />
        </div>

        <div>
          <label htmlFor="rel-empresa" className="block text-sm font-semibold text-gray-700 mb-1">
            Empresa *
          </label>
          <input
            id="rel-empresa"
            type="text"
            required
            minLength={2}
            maxLength={100}
            value={empresa}
            onChange={(e) => setEmpresa(e.target.value)}
            autoComplete="organization"
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Razao social ou nome fantasia"
          />
        </div>

        <div>
          <label htmlFor="rel-cargo" className="block text-sm font-semibold text-gray-700 mb-1">
            Cargo *
          </label>
          <select
            id="rel-cargo"
            required
            value={cargo}
            onChange={(e) => setCargo(e.target.value as Cargo)}
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Selecione</option>
            <option value="diretor">Diretor / C-Level</option>
            <option value="gerente">Gerente</option>
            <option value="analista">Analista</option>
            <option value="consultor">Consultor</option>
            <option value="outro">Outro</option>
          </select>
        </div>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={newsletterOptIn}
            onChange={(e) => setNewsletterOptIn(e.target.checked)}
            className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">
            Quero receber a newsletter mensal do SmartLic com panoramas e insights de licitacoes (opcional).
          </span>
        </label>
      </div>

      <div aria-live="polite" className="min-h-[1.5rem] mt-4">
        {status === 'error' && errorMsg && (
          <p className="text-red-600 text-sm font-medium">{errorMsg}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={status === 'loading'}
        className="mt-2 w-full py-4 px-6 rounded-xl font-bold text-lg text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-md"
      >
        {status === 'loading' ? 'Enviando...' : 'Baixar relatorio gratuito'}
      </button>

      <p className="mt-3 text-xs text-gray-500 text-center">
        Ao enviar voce concorda com nossa{' '}
        <a href="/privacidade" className="underline hover:text-blue-600">
          Politica de Privacidade
        </a>
        .
      </p>
    </form>
  );
}
