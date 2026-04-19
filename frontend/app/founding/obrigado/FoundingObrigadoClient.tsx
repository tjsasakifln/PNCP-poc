'use client';

import { useEffect } from 'react';

function trackEvent(name: string, props?: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  const mp = (window as unknown as { mixpanel?: { track: (e: string, p?: Record<string, unknown>) => void } }).mixpanel;
  if (!mp) return;
  try {
    mp.track(name, props ?? {});
  } catch {
    // no-op
  }
}

export default function FoundingObrigadoClient() {
  useEffect(() => {
    trackEvent('founding_checkout_completed', { source: 'obrigado_page' });
  }, []);

  const calendlyUrl = process.env.NEXT_PUBLIC_FOUNDING_CALENDLY_URL || 'https://cal.com/tiago-sasaki/founding-onboarding';

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-900">
          Bem-vindo ao SmartLic Founding Partners.
        </h1>
        <p className="mt-6 text-lg text-slate-700">
          Sua assinatura foi registrada com sucesso. Em alguns minutos você receberá um email com:
        </p>
        <ul className="mt-4 text-left inline-block text-slate-700">
          <li className="mb-1">&#x2022; Credenciais de acesso ao dashboard</li>
          <li className="mb-1">&#x2022; Confirmação do trial de 14 dias</li>
          <li className="mb-1">&#x2022; Link para agendar nosso call de 30 min</li>
        </ul>

        <section className="mt-10 rounded-lg border border-blue-200 bg-blue-50 p-6 text-left">
          <h2 className="text-xl font-semibold text-slate-900">Próximo passo: o call 1:1</h2>
          <p className="mt-2 text-slate-700">
            Agende 30 minutos comigo (Tiago, fundador) para entender seu caso, mapear editais
            relevantes no seu setor e personalizar as configurações iniciais do SmartLic.
          </p>
          <a
            href={calendlyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-block rounded bg-blue-600 px-5 py-2 font-medium text-white hover:bg-blue-700"
          >
            Agendar call 1:1
          </a>
        </section>

        <p className="mt-10 text-sm text-slate-500">
          Dúvidas imediatas? Escreva para{' '}
          <a className="text-blue-600 underline" href="mailto:tiago@confenge.com.br">
            tiago@confenge.com.br
          </a>
          .
        </p>
      </div>
    </main>
  );
}
