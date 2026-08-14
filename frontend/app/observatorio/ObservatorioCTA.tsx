'use client';

import Link from 'next/link';
import { useUser } from '../../contexts/UserContext';

export function ObservatorioCTA() {
  const { user, authLoading } = useUser();

  const isAuthenticated = !authLoading && !!user;

  return (
    <section className="mt-10 rounded-xl bg-gradient-to-br from-brand-navy to-brand-blue p-8 text-white text-center">
      <h2 className="text-xl font-bold mb-2">
        Esses números são apenas o agregado público
      </h2>
      <p className="text-white/85 mb-5">
        No SmartLic você filtra milhares de editais abertos pelo seu setor, valor mínimo
        e UF — em 3 minutos, sem custo.
      </p>
      {isAuthenticated ? (
        <Link
          href="/buscar"
          className="inline-block px-7 py-3 bg-white text-brand-navy font-bold rounded-xl hover:bg-gray-100 transition-colors"
        >
          Ver editais personalizados →
        </Link>
      ) : (
        <Link
          href="/consultoria-b2g?ref=observatorio-hub"
          className="inline-block px-7 py-3 bg-white text-brand-navy font-bold rounded-xl hover:bg-gray-100 transition-colors"
        >
          Ver editais do meu setor →
        </Link>
      )}
      <p className="mt-3 text-xs text-white/70">sem login, dado verificável.</p>
    </section>
  );
}
