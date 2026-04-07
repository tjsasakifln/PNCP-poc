"use client";

import Link from "next/link";
import { Button } from "../../../components/ui/button";

export function AlertsEmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="text-center py-16 px-4" data-testid="alerts-empty-state">
      <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--brand-blue-subtle)]">
        <svg
          aria-hidden="true"
          className="w-8 h-8 text-[var(--brand-blue)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
      </div>
      <h2 className="text-xl font-display font-semibold text-[var(--ink)] mb-3">
        Nenhum alerta configurado
      </h2>
      <p className="text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
        Crie alertas para receber notificações por e-mail quando novas
        licitações forem publicadas nos setores e estados que você acompanha.
      </p>
      <ol className="text-left max-w-sm mx-auto mb-8 space-y-3">
        {[
          "Defina um nome para o alerta",
          "Escolha setor, estados e palavras-chave",
          "Receba e-mails automáticos com novas oportunidades",
        ].map((step, i) => (
          <li key={i} className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--brand-blue)] text-white text-xs font-bold flex items-center justify-center mt-0.5">
              {i + 1}
            </span>
            <span className="text-sm text-[var(--ink-secondary)]">{step}</span>
          </li>
        ))}
      </ol>
      <div className="mt-3 mb-4 text-center">
        <Link href="/ajuda#como-buscar" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
          Precisa de ajuda?
        </Link>
      </div>
      <Button
        onClick={onCreate}
        variant="primary"
        size="lg"
        data-testid="alerts-create-first"
      >
        Criar primeiro alerta
        <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </Button>
    </div>
  );
}
