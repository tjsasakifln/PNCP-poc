/**
 * STORY-432 AC2: Calculadora embeddável — versão stripped sem header/footer/nav.
 *
 * Uso (iframe):
 *   <iframe src="https://smartlic.tech/calculadora/embed" width="100%" height="600"
 *           frameborder="0" title="Calculadora de Oportunidades em Licitações"></iframe>
 *
 * Link de crédito no footer é followable (rel="noopener", SEM nofollow) — gera backlink automático.
 */

import { Metadata } from 'next';
import CalculadoraClient from '../CalculadoraClient';

export const metadata: Metadata = {
  title: 'Calculadora de Oportunidades em Licitações | SmartLic',
  description: 'Descubra quantas licitações do seu setor sua empresa está perdendo. Dados reais do PNCP.',
  robots: { index: false, follow: true }, // noindex — página embed não deve aparecer em busca
};

export default function CalculadoraEmbedPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Logo mínimo */}
      <div className="px-4 py-3 border-b border-gray-100">
        <a
          href="https://smartlic.tech"
          target="_blank"
          rel="noopener"
          className="text-sm font-semibold text-blue-700 hover:underline"
        >
          SmartLic
        </a>
        <span className="text-gray-400 text-sm ml-2">— Inteligência em Licitações</span>
      </div>

      {/* Calculadora */}
      <div className="flex-1 px-4 py-6 max-w-2xl mx-auto w-full">
        <h1 className="text-xl font-bold text-gray-900 mb-1">
          Calculadora de Oportunidades em Licitações
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          Dados reais do PNCP. Atualizado diariamente.
        </p>
        <CalculadoraClient />
      </div>

      {/* Footer com backlink followable — STORY-432 AC2 */}
      <footer className="px-4 py-3 border-t border-gray-100 text-center">
        <p className="text-xs text-gray-400">
          Calculadora por{' '}
          <a
            href="https://smartlic.tech/calculadora"
            target="_blank"
            rel="noopener"
            className="text-blue-600 hover:underline font-medium"
          >
            SmartLic — Inteligência em Licitações Públicas
          </a>
          {' '}· Dados: PNCP
        </p>
      </footer>
    </div>
  );
}
