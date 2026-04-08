'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function OrgaoSearchForm() {
  const router = useRouter();
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  function formatCnpj(raw: string): string {
    const d = raw.replace(/\D/g, '').slice(0, 14);
    if (d.length <= 2) return d;
    if (d.length <= 5) return `${d.slice(0, 2)}.${d.slice(2)}`;
    if (d.length <= 8) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5)}`;
    if (d.length <= 12) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8)}`;
    return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const digits = input.replace(/\D/g, '');
    if (digits.length !== 14) {
      setError('Informe um CNPJ válido com 14 dígitos');
      return;
    }
    setError('');
    router.push(`/orgaos/${digits}`);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-xl">
      <input
        type="text"
        value={input}
        onChange={(e) => {
          setInput(formatCnpj(e.target.value));
          setError('');
        }}
        placeholder="Digite o CNPJ do órgão (ex: 00.394.494/0058-87)"
        className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
        inputMode="numeric"
      />
      <button
        type="submit"
        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-colors whitespace-nowrap"
      >
        Consultar Órgão
      </button>
      {error && <p className="text-red-600 text-sm sm:col-span-2">{error}</p>}
    </form>
  );
}
