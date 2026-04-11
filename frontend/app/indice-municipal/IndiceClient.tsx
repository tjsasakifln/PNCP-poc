'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface IndiceItem {
  municipio_nome: string;
  municipio_slug: string;
  uf: string;
  uf_nome: string;
  periodo: string;
  score_total: number;
  total_editais: number;
  ranking_nacional: number;
}

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
  'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
  'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

const PERIODOS = ['2026-Q1'];

function scoreColor(score: number): string {
  if (score >= 60) return 'text-green-600 font-semibold';
  if (score >= 40) return 'text-yellow-600 font-semibold';
  return 'text-red-600 font-semibold';
}

export default function IndiceClient() {
  const [periodo, setPeriodo] = useState('2026-Q1');
  const [uf, setUf] = useState('');
  const [dados, setDados] = useState<IndiceItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();

    async function fetchDados() {
      setLoading(true);
      setError('');
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || '';
        const ufParam = uf ? `&uf=${uf}` : '';
        const url = `${backendUrl}/v1/indice-municipal?periodo=${periodo}${ufParam}&limit=50`;
        const res = await fetch(url, { signal: controller.signal });
        if (!res.ok) {
          throw new Error(`Erro ${res.status}: ${res.statusText}`);
        }
        const json = await res.json();
        setDados(Array.isArray(json) ? json : json.resultados ?? json.items ?? []);
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setError('Não foi possível carregar os dados. Tente novamente em instantes.');
      } finally {
        setLoading(false);
      }
    }

    fetchDados();

    return () => controller.abort();
  }, [periodo, uf]);

  return (
    <section>
      {/* Filtros */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div>
          <label htmlFor="select-periodo" className="block text-xs text-gray-500 mb-1">
            Período
          </label>
          <select
            id="select-periodo"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            {PERIODOS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="select-uf" className="block text-xs text-gray-500 mb-1">
            Estado (UF)
          </label>
          <select
            id="select-uf"
            value={uf}
            onChange={(e) => setUf(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="">Todos os estados</option>
            {UFS.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3" aria-label="Carregando dados">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Empty */}
      {!loading && !error && dados !== null && dados.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center text-gray-500 text-sm">
          Nenhum dado disponível para este período.
        </div>
      )}

      {/* Tabela */}
      {!loading && !error && dados && dados.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left w-12">#</th>
                <th className="px-4 py-3 text-left">Município</th>
                <th className="px-4 py-3 text-left w-16">UF</th>
                <th className="px-4 py-3 text-right w-28">Score Total</th>
                <th className="px-4 py-3 text-right w-24">Editais</th>
                <th className="px-4 py-3 text-left w-28">Detalhes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {dados.map((item) => (
                <tr key={`${item.municipio_slug}-${item.periodo}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400 tabular-nums">
                    {item.ranking_nacional ?? '—'}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-800">
                    {item.municipio_nome}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{item.uf}</td>
                  <td className={`px-4 py-3 text-right tabular-nums ${scoreColor(Number(item.score_total))}`}>
                    {Number(item.score_total).toFixed(1)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600 tabular-nums">
                    {new Intl.NumberFormat('pt-BR').format(item.total_editais)}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/indice-municipal/${item.municipio_slug}?periodo=${periodo}`}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      Ver detalhes
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
