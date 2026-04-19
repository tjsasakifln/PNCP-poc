'use client';

import { useState } from 'react';

interface FaqItem {
  q: string;
  a: string;
}

const FAQS: FaqItem[] = [
  {
    q: 'O que acontece depois de 12 meses de desconto?',
    a: 'O preço volta ao valor cheio do plano SmartLic Pro (R$ 397/mês anual). Avisamos por email 30 dias antes da renovação. Se optar pela renovação anual, mantém o desconto anual regular da época (hoje ~25%).',
  },
  {
    q: 'Posso cancelar a qualquer momento?',
    a: 'Sim. O trial é gratuito por 14 dias. Após isso, você pode cancelar a qualquer momento via /conta, sem multa. O acesso continua até o fim do ciclo pago.',
  },
  {
    q: 'Que tipo de suporte tenho como founding partner?',
    a: 'Linha direta comigo (Tiago, fundador) via WhatsApp. Response time < 4h úteis para bugs. Onboarding 1:1 de 30 min por Zoom nos primeiros 7 dias do trial.',
  },
  {
    q: 'Eu realmente tenho voz no roadmap?',
    a: 'Sim, mas com disciplina: feature requests passam por um ritual quinzenal de priorização com founding partners (call de 30 min por Meet). Features sem consenso ou fora do core ficam em backlog público.',
  },
  {
    q: 'O SmartLic escala para múltiplos CNPJs / time?',
    a: 'O plano Pro cobre 1 CNPJ + até 5 usuários. Para consultorias atendendo múltiplos CNPJs, há o plano Consultoria (R$ 997/mês, até 20 CNPJs). Founding discount se aplica ao Pro; para Consultoria, peça uma proposta individual via form abaixo.',
  },
];

export default function FoundingFAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section aria-labelledby="faq-heading" className="mt-16">
      <h2 id="faq-heading" className="text-2xl font-semibold text-slate-900 mb-6">
        Perguntas frequentes
      </h2>
      <div className="divide-y divide-slate-200 border border-slate-200 rounded-lg">
        {FAQS.map((item, idx) => {
          const isOpen = openIndex === idx;
          return (
            <div key={item.q}>
              <button
                type="button"
                className="w-full flex justify-between items-center px-4 py-3 text-left text-slate-900 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-expanded={isOpen}
                onClick={() => setOpenIndex(isOpen ? null : idx)}
              >
                <span className="font-medium">{item.q}</span>
                <span aria-hidden="true" className="ml-4 text-slate-500">
                  {isOpen ? '−' : '+'}
                </span>
              </button>
              {isOpen && (
                <div className="px-4 pb-4 text-slate-700 leading-relaxed">{item.a}</div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
