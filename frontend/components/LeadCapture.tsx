'use client';

import { useState } from 'react';

interface LeadCaptureProps {
  source: string;         // 'calculadora' | 'cnpj' | 'alertas'
  heading?: string;
  description?: string;
  setor?: string;         // A2: sector context from parent
  uf?: string;            // A2: UF context from parent
  buttonText?: string;    // custom button label (default: "Receber Grátis")
}

export function LeadCapture({ source, heading, description, setor, uf, buttonText }: LeadCaptureProps) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [receiptId, setReceiptId] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || status === 'loading') return;

    setStatus('loading');
    try {
      const res = await fetch('/api/lead-capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, source, setor, uf }),
      });
      if (res.ok) {
        const body = (await res.json()) as { receipt_id?: string };
        setReceiptId(body.receipt_id || null);
        setStatus('success');
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  }

  if (status === 'success') {
    return (
      <div
        className="rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-6 text-center"
        data-testid="lead-receipt"
      >
        <p className="text-green-800 dark:text-green-200 font-medium">
          Pedido recebido. A CONFENGE retoma a partir deste recibo.
        </p>
        {receiptId ? (
          <p className="mt-2 font-mono text-sm text-green-900 dark:text-green-100" data-testid="lead-receipt-id">
            Recibo {receiptId}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-surface-1 border border-border p-6 sm:p-8">
      <h3 className="text-lg font-bold text-ink mb-2">
        {heading || 'Receba alertas semanais do seu setor por email'}
      </h3>
      <p className="text-ink-secondary text-sm mb-4">
        {description || 'Dados semanais das nossas fontes oficiais sobre seu setor. Sem spam — cancele a qualquer momento.'}
      </p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <input
          type="email"
          required
          placeholder="seu@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1 px-4 py-3 rounded-lg border border-border bg-surface-0 text-ink placeholder:text-ink-secondary/50 focus:outline-none focus:ring-2 focus:ring-brand-blue"
        />
        <button
          type="submit"
          disabled={status === 'loading'}
          className="px-6 py-3 bg-brand-blue text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 whitespace-nowrap"
        >
          {status === 'loading' ? 'Enviando...' : buttonText || 'Receber o recorte'}
        </button>
      </form>
      {status === 'error' && (
        <p className="mt-2 text-sm text-red-600">Erro ao enviar. Tente novamente.</p>
      )}
    </div>
  );
}
