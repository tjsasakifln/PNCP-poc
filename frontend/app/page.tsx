"use client";

import { useState, useEffect } from "react";
import type { BuscaResult, ValidationErrors } from "./types";

const UFS = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
  "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
  "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

/**
 * Calculate date difference in days
 */
function dateDiffInDays(date1: string, date2: string): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Main search form page
 */
export default function HomePage() {
  // Form state
  const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(
    new Set(["SC", "PR", "RS"]) // Default: Sul region
  );
  const [dataInicial, setDataInicial] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split("T")[0];
  });
  const [dataFinal, setDataFinal] = useState(() => {
    return new Date().toISOString().split("T")[0];
  });

  // API state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [result, setResult] = useState<BuscaResult | null>(null);

  // Validation state
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  /**
   * Validate form inputs (PRD Section 7.3 lines 1259-1262)
   */
  function validateForm(): ValidationErrors {
    const errors: ValidationErrors = {};

    // Rule 1: Min 1 UF selected
    if (ufsSelecionadas.size === 0) {
      errors.ufs = "Selecione pelo menos um estado";
    }

    // Rule 2: data_final >= data_inicial
    if (dataFinal < dataInicial) {
      errors.date_range = "Data final deve ser maior ou igual à data inicial";
    }

    // Rule 3: Max range 30 days (PRD Section 1.2)
    const rangeDays = dateDiffInDays(dataInicial, dataFinal);
    if (rangeDays > 30) {
      errors.date_range = `Período máximo de 30 dias (selecionado: ${rangeDays} dias)`;
    }

    return errors;
  }

  /**
   * Validate on every form change
   */
  useEffect(() => {
    setValidationErrors(validateForm());
  }, [ufsSelecionadas, dataInicial, dataFinal]);

  /**
   * Toggle UF selection
   */
  const toggleUf = (uf: string) => {
    const newSet = new Set(ufsSelecionadas);
    if (newSet.has(uf)) {
      newSet.delete(uf);
    } else {
      newSet.add(uf);
    }
    setUfsSelecionadas(newSet);
  };

  /**
   * Select all UFs
   */
  const selecionarTodos = () => {
    setUfsSelecionadas(new Set(UFS));
  };

  /**
   * Clear UF selection
   */
  const limparSelecao = () => {
    setUfsSelecionadas(new Set());
  };

  /**
   * Submit search request
   */
  const buscar = async () => {
    // Final validation check
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/buscar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ufs: Array.from(ufsSelecionadas),
          data_inicial: dataInicial,
          data_final: dataFinal
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message || "Erro ao buscar licitações");
      }

      const data: BuscaResult = await response.json();
      setResult(data);

    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Excel download with error handling
   */
  const handleDownload = async () => {
    if (!result) return;

    setDownloadError(null);

    try {
      const downloadUrl = `/api/download?id=${result.download_id}`;

      // Check if file exists by making a HEAD request first
      const headResponse = await fetch(downloadUrl, { method: 'HEAD' });

      if (!headResponse.ok) {
        if (headResponse.status === 404) {
          throw new Error('Arquivo não encontrado ou expirado');
        }
        throw new Error(`Erro ao fazer download: ${headResponse.statusText}`);
      }

      // Proceed with download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `licitacoes_${result.download_id}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao fazer download do Excel';
      setDownloadError(`Erro no download: ${errorMessage}`);
    }
  };

  // Check if form is valid
  const isFormValid = Object.keys(validationErrors).length === 0;

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">
        BidIQ Uniformes
      </h1>

      {/* UF Selection Section */}
      <section className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="font-medium">Selecione os Estados (UFs):</label>
          <div className="space-x-2">
            <button
              onClick={selecionarTodos}
              className="text-sm text-blue-600 hover:underline"
              type="button"
            >
              Selecionar todos
            </button>
            <button
              onClick={limparSelecao}
              className="text-sm text-gray-600 hover:underline"
              type="button"
            >
              Limpar
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {UFS.map(uf => (
            <button
              key={uf}
              onClick={() => toggleUf(uf)}
              type="button"
              className={`px-3 py-1 rounded border transition-colors ${
                ufsSelecionadas.has(uf)
                  ? "bg-green-600 text-white border-green-600"
                  : "bg-white text-gray-700 border-gray-300 hover:border-green-400"
              }`}
            >
              {uf}
            </button>
          ))}
        </div>

        <p className="text-sm text-gray-500 mt-2">
          {ufsSelecionadas.size} estado(s) selecionado(s)
        </p>

        {/* Inline UF error */}
        {validationErrors.ufs && (
          <p className="text-sm text-red-600 mt-1">
            {validationErrors.ufs}
          </p>
        )}
      </section>

      {/* Date Range Section */}
      <section className="mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="data-inicial" className="block text-sm font-medium mb-1">
              Data inicial:
            </label>
            <input
              id="data-inicial"
              type="date"
              value={dataInicial}
              onChange={e => setDataInicial(e.target.value)}
              className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="flex-1">
            <label htmlFor="data-final" className="block text-sm font-medium mb-1">
              Data final:
            </label>
            <input
              id="data-final"
              type="date"
              value={dataFinal}
              onChange={e => setDataFinal(e.target.value)}
              className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
        </div>

        {/* Inline date range error */}
        {validationErrors.date_range && (
          <p className="text-sm text-red-600 mt-2">
            {validationErrors.date_range}
          </p>
        )}
      </section>

      {/* Search Button */}
      <button
        onClick={buscar}
        disabled={loading || !isFormValid}
        type="button"
        className="w-full bg-green-600 text-white py-3 rounded font-medium
                   hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                   transition-colors"
      >
        {loading ? "Buscando..." : "🔍 Buscar Licitações de Uniformes"}
      </button>

      {/* Loading State */}
      {loading && (
        <div className="mt-6 p-4 bg-gray-50 rounded">
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-4">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Buscando licitações...
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {/* Result Display (placeholder for #23) */}
      {result && (
        <div className="mt-6 space-y-4">
          {/* Resumo LLM */}
          <div className="p-4 bg-green-50 border border-green-200 rounded">
            <p className="text-lg">{result.resumo.resumo_executivo}</p>

            <div className="flex gap-6 mt-4">
              <div>
                <span className="text-3xl font-bold text-green-700">
                  {result.resumo.total_oportunidades}
                </span>
                <span className="text-sm text-gray-600 block">licitações</span>
              </div>
              <div>
                <span className="text-3xl font-bold text-green-700">
                  R$ {result.resumo.valor_total.toLocaleString("pt-BR")}
                </span>
                <span className="text-sm text-gray-600 block">valor total</span>
              </div>
            </div>

            {result.resumo.alerta_urgencia && (
              <div className="mt-4 p-2 bg-yellow-100 border border-yellow-300 rounded text-yellow-800">
                ⚠️ {result.resumo.alerta_urgencia}
              </div>
            )}

            {result.resumo.destaques.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Destaques:</h4>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {result.resumo.destaques.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            className="w-full bg-blue-600 text-white py-3 rounded
                       font-medium hover:bg-blue-700 transition-colors"
          >
            📥 Baixar Excel ({result.resumo.total_oportunidades} licitações)
          </button>

          {/* Download Error Display */}
          {downloadError && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
              {downloadError}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
