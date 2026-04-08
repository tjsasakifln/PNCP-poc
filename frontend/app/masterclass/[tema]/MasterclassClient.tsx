'use client';

import { useState } from 'react';

interface MasterclassClientProps {
  tema: string;
  title: string;
  topics: string[];
}

/**
 * Email-gated masterclass player.
 * Shows an inline email capture form; on successful submission unlocks
 * the video placeholder + topic outline.
 *
 * NOTE: LeadCapture does not expose an onSuccess callback, so this component
 * implements its own equivalent inline email gate to support the unlock flow.
 */
export default function MasterclassClient({ tema, title, topics }: MasterclassClientProps) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const [unlocked, setUnlocked] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || status === 'loading') return;

    setStatus('loading');
    try {
      const res = await fetch('/api/lead-capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, source: `masterclass-${tema}` }),
      });
      if (res.ok) {
        setUnlocked(true);
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  }

  if (unlocked) {
    return (
      <section className="space-y-6">
        {/* Video placeholder */}
        <div className="rounded-2xl bg-surface-1 border border-[var(--border)] overflow-hidden">
          <div className="aspect-video bg-gradient-to-br from-brand-blue/10 to-blue-900/20 flex flex-col items-center justify-center gap-4 p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-brand-blue/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-brand-blue" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
            <div>
              <p className="text-lg font-bold text-ink-primary">Em breve — masterclass em produção</p>
              <p className="mt-1 text-sm text-ink-secondary">
                Você será notificado por email quando a masterclass estiver disponível.
              </p>
            </div>
          </div>
        </div>

        {/* Unlocked topic outline */}
        <div className="rounded-2xl border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20 p-6">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-5 h-5 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <p className="text-sm font-semibold text-green-800 dark:text-green-200">
              Acesso liberado — você receberá o link por email
            </p>
          </div>
          <h3 className="text-base font-bold text-ink-primary mb-3">Conteúdo da masterclass: {title}</h3>
          <ol className="space-y-2">
            {topics.map((topic, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-ink-secondary">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-blue/10 text-brand-blue font-bold text-xs flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                {topic}
              </li>
            ))}
          </ol>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-[var(--border)] bg-surface-1 p-6 sm:p-8">
      {/* Lock icon */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-brand-blue/10 flex items-center justify-center">
          <svg className="w-5 h-5 text-brand-blue" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0110 0v4" />
          </svg>
        </div>
        <div>
          <p className="font-bold text-ink-primary">Assista gratuitamente</p>
          <p className="text-sm text-ink-muted">Informe seu email para liberar o acesso</p>
        </div>
      </div>

      <p className="text-sm text-ink-secondary mb-5 leading-relaxed">
        A masterclass <strong className="text-ink-primary">{title}</strong> é gratuita.
        Basta deixar seu email — sem spam, cancele quando quiser.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <input
          type="email"
          required
          placeholder="seu@email.com.br"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={status === 'loading'}
          className="flex-1 px-4 py-3 rounded-lg border border-border bg-surface-0 text-ink placeholder:text-ink-secondary/50 focus:outline-none focus:ring-2 focus:ring-brand-blue disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={status === 'loading'}
          className="px-6 py-3 bg-brand-blue text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 whitespace-nowrap"
        >
          {status === 'loading' ? 'Aguarde...' : 'Liberar acesso grátis'}
        </button>
      </form>

      {status === 'error' && (
        <p className="mt-3 text-sm text-red-600 dark:text-red-400">
          Erro ao processar. Tente novamente em instantes.
        </p>
      )}

      <p className="mt-3 text-xs text-ink-muted">
        Seus dados estão seguros. Nunca compartilhamos com terceiros.
      </p>
    </section>
  );
}
