'use client';

import { useState } from 'react';
import Link from 'next/link';

/**
 * CRO-CTA-003: Final CTA dinâmico para /blog/licitacoes-ti-software-2026
 *
 * Exibe um seletor compacto de foco em TI dentro do CTA final.
 * A seleção alimenta o texto e o link do botão principal.
 */
const FOCOS_TI = [
  { id: 'desenvolvimento', label: 'Desenvolvimento de software sob demanda' },
  { id: 'licenciamento', label: 'Licenciamento e revenda (Microsoft, Oracle, etc.)' },
  { id: 'suporte', label: 'Suporte técnico e help desk' },
  { id: 'infra', label: 'Infraestrutura e cloud' },
  { id: 'seguranca', label: 'Segurança da informação' },
  { id: 'fabrica', label: 'Fábrica de software (body shop)' },
] as const;

export default function FinalCTATI() {
  const [selectedFoco, setSelectedFoco] = useState<string | null>(null);

  const focoLabel = selectedFoco
    ? FOCOS_TI.find((f) => f.id === selectedFoco)?.label.toLowerCase() || selectedFoco
    : 'TI';

  const focoQuery = selectedFoco ? `&foco=${selectedFoco}` : '';

  return (
    <div className="not-prose mt-8 sm:mt-12 bg-gradient-to-br from-brand-navy to-brand-blue rounded-xl p-5 sm:p-8 text-white">
      <p className="text-lg sm:text-xl font-bold mb-2">
        {selectedFoco
          ? `Receba editais de ${focoLabel} que cabem no seu perfil técnico`
          : 'Receba editais de TI que cabem no seu perfil técnico'}
      </p>
      <p className="text-sm sm:text-base text-white/80 mb-4 max-w-lg">
        Análise automática de viabilidade antes da sua equipe abrir o edital.
        Filtramos por stack tecnológica, porte da empresa compradora, valor do
        contrato e complexidade da licitação.
      </p>

      <div className="mb-5">
        <p className="text-xs text-white/70 font-medium mb-2">
          Selecione seu foco (opcional):
        </p>
        <div className="flex flex-wrap gap-2">
          {FOCOS_TI.map((foco) => (
            <button
              key={foco.id}
              type="button"
              onClick={() =>
                setSelectedFoco(selectedFoco === foco.id ? null : foco.id)
              }
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                selectedFoco === foco.id
                  ? 'bg-white text-brand-navy border-white font-semibold'
                  : 'bg-white/10 text-white/80 border-white/20 hover:bg-white/20'
              }`}
            >
              {foco.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <Link
          href={`/consultoria-b2g?source=blog-ti${focoQuery}`}
          className="inline-block bg-white text-brand-navy font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98] text-center"
        >
          {selectedFoco
            ? `Receber editais de ${focoLabel}`
            : 'Receber editais de TI'}
        </Link>
        <Link
          href="/login"
          className="inline-block bg-white/10 hover:bg-white/20 border border-white/30 text-white font-medium px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all text-center"
        >
          Já tenho conta — ver painel
        </Link>
      </div>
    </div>
  );
}
