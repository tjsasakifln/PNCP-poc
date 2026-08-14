'use client';

import { useState, useRef } from 'react';
import { SECTORS } from '@/lib/sectors';
import { trackFormStarted, trackFormSubmitted } from '@/lib/analytics-events';
import { getStoredUTMParams } from '@/hooks/useAnalytics';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DiagnosticFormProps {
  /** Required: identifies where the form was embedded (e.g. 'consultoria-b2g'). */
  source: string;
  /** Pre-select a modalidade value, e.g. from ?modalidade= URL param. */
  defaultModalidade?: 'radar' | 'report' | 'intel' | 'nao_sei';
  /** When true renders a compact inline variant (smaller padding, single-col). */
  compact?: boolean;
  /** Called after a successful submission so parent can react (e.g. scroll). */
  onSuccess?: () => void;
}

type Status = 'idle' | 'loading' | 'success' | 'error';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Progressively formats a CNPJ string as the user types:
 * XX.XXX.XXX/XXXX-XX
 */
function formatCnpj(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 14);
  if (digits.length <= 2) return digits;
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
  if (digits.length <= 8)
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
  if (digits.length <= 12)
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}

/**
 * Progressively formats a phone string as the user types:
 * (XX) XXXXX-XXXX
 */
function formatPhone(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 11);
  if (digits.length <= 2) return digits.length ? `(${digits}` : '';
  if (digits.length <= 7)
    return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}

function validate(fields: {
  nome: string;
  email: string;
  cnpj: string;
  setor: string;
  modalidade_interesse: string;
  mensagem: string;
}): string | null {
  if (!fields.nome.trim() || fields.nome.trim().length < 2)
    return 'Nome obrigatório (mínimo 2 caracteres).';
  if (!fields.email.trim() || !EMAIL_RE.test(fields.email.trim()))
    return 'Informe um email válido.';
  if (!fields.setor) return 'Selecione seu setor de atuação.';
  if (!fields.modalidade_interesse)
    return 'Selecione a modalidade de interesse.';
  const cnpjDigits = fields.cnpj.replace(/\D/g, '');
  if (cnpjDigits.length > 0 && cnpjDigits.length !== 14)
    return 'CNPJ deve ter 14 dígitos.';
  if (fields.mensagem && fields.mensagem.length > 500)
    return 'Mensagem deve ter no máximo 500 caracteres.';
  return null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const MODALIDADE_OPTIONS = [
  { value: 'radar', label: 'Radar Operacional (alertas + briefing)' },
  { value: 'report', label: 'Inteligência Estratégica (relatórios + análise)' },
  { value: 'intel', label: 'Operação Premium (consultoria)' },
  { value: 'nao_sei', label: 'Ainda não sei' },
] as const;

export default function DiagnosticForm({
  source,
  defaultModalidade,
  compact = false,
  onSuccess,
}: DiagnosticFormProps) {
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [empresa, setEmpresa] = useState('');
  const [cnpj, setCnpj] = useState('');
  const [setor, setSetor] = useState('');
  const [modalidade, setModalidade] = useState<string>(
    defaultModalidade ?? ''
  );
  const [mensagem, setMensagem] = useState('');
  const [telefone, setTelefone] = useState('');

  const [status, setStatus] = useState<Status>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [receiptId, setReceiptId] = useState<string | null>(null);

  // Fire form_started only once on first field interaction.
  const startedRef = useRef(false);

  function handleFirstTouch() {
    if (startedRef.current) return;
    startedRef.current = true;
    trackFormStarted({ form_name: 'diagnostic_form', source });
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const error = validate({
      nome,
      email,
      cnpj,
      setor,
      modalidade_interesse: modalidade,
      mensagem,
    });
    if (error) {
      setErrorMsg(error);
      setStatus('error');
      return;
    }

    setStatus('loading');
    setErrorMsg('');

    const utms = getStoredUTMParams();

    try {
      const res = await fetch('/api/lead-capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nome.trim(),
          email: email.trim().toLowerCase(),
          empresa: empresa.trim() || undefined,
          cnpj: cnpj.replace(/\D/g, '') || undefined,
          setor: setor || undefined,
          modalidade_interesse: modalidade || undefined,
          mensagem: mensagem.trim() || undefined,
          telefone: telefone.replace(/\D/g, '') || undefined,
          source,
          cta_id: 'cta.consultoria.submit',
          route_family: 'consultoria',
          landing_url: '/consultoria-b2g',
          ...utms,
        }),
      });

      if (!res.ok) {
        let msg = 'Não foi possível enviar. Tente novamente em instantes.';
        try {
          const data = await res.json();
          if (typeof data?.error === 'string') msg = data.error;
          else if (typeof data?.detail === 'string') msg = data.detail;
        } catch {
          // ignore JSON parse errors
        }
        setErrorMsg(msg);
        setStatus('error');
        return;
      }

      let receipt: string | null = null;
      try {
        const data = (await res.json()) as { receipt_id?: string };
        receipt = data.receipt_id || null;
      } catch {
        receipt = null;
      }
      setReceiptId(receipt);

      trackFormSubmitted({
        form_name: 'diagnostic_form',
        source,
        modalidade: modalidade as 'radar' | 'report' | 'intel' | 'nao_sei' | undefined,
      });

      setStatus('success');
      onSuccess?.();
    } catch (err) {
      // Dynamic import keeps Sentry out of the initial bundle.
      import('@sentry/nextjs')
        .then((Sentry) => {
          Sentry.captureException(err, {
            tags: { component: 'DiagnosticForm', source },
          });
        })
        .catch(() => {});
      setErrorMsg('Falha de rede. Verifique sua conexão e tente novamente.');
      setStatus('error');
    }
  }

  const loading = status === 'loading';
  const containerPadding = compact ? 'p-4' : 'p-6 sm:p-8';
  const inputBase =
    'mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 disabled:bg-slate-50 disabled:text-slate-400';

  if (status === 'success') {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 ${containerPadding} text-center`}
        data-testid="diagnostic-form-success"
      >
        <p className="text-green-800 dark:text-green-200 font-medium">
          Diagnóstico solicitado. A CONFENGE retoma a partir deste recibo.
        </p>
        {receiptId ? (
          <p className="mt-2 font-mono text-sm text-green-900 dark:text-green-100" data-testid="diagnostic-form-receipt">
            Recibo {receiptId}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 ${containerPadding} space-y-4`}
      noValidate
      data-testid="diagnostic-form"
    >
      {/* Nome */}
      <div>
        <label
          htmlFor="diag-nome"
          className="block text-sm font-medium text-slate-900 dark:text-slate-100"
        >
          Nome <span className="text-red-500">*</span>
        </label>
        <input
          id="diag-nome"
          type="text"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          onFocus={handleFirstTouch}
          required
          maxLength={200}
          placeholder="Seu nome completo"
          className={inputBase}
          disabled={loading}
          data-testid="diag-nome"
        />
      </div>

      {/* Email */}
      <div>
        <label
          htmlFor="diag-email"
          className="block text-sm font-medium text-slate-900 dark:text-slate-100"
        >
          Email <span className="text-red-500">*</span>
        </label>
        <input
          id="diag-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onFocus={handleFirstTouch}
          required
          maxLength={320}
          placeholder="seu@empresa.com"
          className={inputBase}
          disabled={loading}
          data-testid="diag-email"
        />
      </div>

      {/* Empresa + CNPJ side by side if not compact */}
      <div className={compact ? 'space-y-4' : 'grid sm:grid-cols-2 gap-4'}>
        <div>
          <label
            htmlFor="diag-empresa"
            className="block text-sm font-medium text-slate-900 dark:text-slate-100"
          >
            Empresa{' '}
            <span className="text-slate-400 font-normal">(opcional)</span>
          </label>
          <input
            id="diag-empresa"
            type="text"
            value={empresa}
            onChange={(e) => setEmpresa(e.target.value)}
            onFocus={handleFirstTouch}
            maxLength={200}
            placeholder="Nome da empresa"
            className={inputBase}
            disabled={loading}
            data-testid="diag-empresa"
          />
        </div>

        <div>
          <label
            htmlFor="diag-cnpj"
            className="block text-sm font-medium text-slate-900 dark:text-slate-100"
          >
            CNPJ{' '}
            <span className="text-slate-400 font-normal">(opcional)</span>
          </label>
          <input
            id="diag-cnpj"
            type="text"
            inputMode="numeric"
            value={cnpj}
            onChange={(e) => setCnpj(formatCnpj(e.target.value))}
            onFocus={handleFirstTouch}
            placeholder="00.000.000/0000-00"
            className={inputBase}
            disabled={loading}
            data-testid="diag-cnpj"
          />
        </div>
      </div>

      {/* Setor */}
      <div>
        <label
          htmlFor="diag-setor"
          className="block text-sm font-medium text-slate-900 dark:text-slate-100"
        >
          Setor <span className="text-red-500">*</span>
        </label>
        <select
          id="diag-setor"
          value={setor}
          onChange={(e) => setSetor(e.target.value)}
          onFocus={handleFirstTouch}
          required
          className={inputBase}
          disabled={loading}
          data-testid="diag-setor"
        >
          <option value="">Selecione seu setor</option>
          {SECTORS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {/* Modalidade */}
      <div>
        <label
          htmlFor="diag-modalidade"
          className="block text-sm font-medium text-slate-900 dark:text-slate-100"
        >
          Modalidade de interesse <span className="text-red-500">*</span>
        </label>
        <select
          id="diag-modalidade"
          value={modalidade}
          onChange={(e) => setModalidade(e.target.value)}
          onFocus={handleFirstTouch}
          required
          className={inputBase}
          disabled={loading}
          data-testid="diag-modalidade"
        >
          <option value="">Selecione uma modalidade</option>
          {MODALIDADE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Mensagem */}
      <div>
        <label
          htmlFor="diag-mensagem"
          className="block text-sm font-medium text-slate-900 dark:text-slate-100"
        >
          Mensagem{' '}
          <span className="text-slate-400 font-normal">(opcional)</span>
        </label>
        <textarea
          id="diag-mensagem"
          value={mensagem}
          onChange={(e) => setMensagem(e.target.value)}
          onFocus={handleFirstTouch}
          maxLength={500}
          rows={compact ? 3 : 4}
          placeholder="Conte um pouco sobre sua operação..."
          className={inputBase}
          disabled={loading}
          data-testid="diag-mensagem"
        />
        {mensagem.length > 400 && (
          <p className="mt-1 text-xs text-slate-500 text-right">
            {mensagem.length}/500
          </p>
        )}
      </div>

      {/* Telefone */}
      <div>
        <label
          htmlFor="diag-telefone"
          className="block text-sm font-medium text-slate-900 dark:text-slate-100"
        >
          Telefone{' '}
          <span className="text-slate-400 font-normal">(opcional)</span>
        </label>
        <input
          id="diag-telefone"
          type="tel"
          inputMode="numeric"
          value={telefone}
          onChange={(e) => setTelefone(formatPhone(e.target.value))}
          onFocus={handleFirstTouch}
          placeholder="(11) 99999-9999"
          className={inputBase}
          disabled={loading}
          data-testid="diag-telefone"
        />
      </div>

      {/* Error */}
      {status === 'error' && errorMsg && (
        <div
          role="alert"
          className="rounded bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-800"
          data-testid="diagnostic-form-error"
        >
          {errorMsg}
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white hover:bg-blue-700 disabled:bg-slate-300 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        data-testid="diagnostic-form-submit"
      >
        {loading ? 'Enviando...' : 'Solicitar diagnóstico gratuito'}
      </button>
    </form>
  );
}
