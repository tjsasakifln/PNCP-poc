"use client";

import { useState, useEffect } from "react";
import type { BuscaResult, ValidationErrors } from "./types";
import { LoadingProgress } from "./components/LoadingProgress";
import { EmptyState } from "./components/EmptyState";

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
  const [loadingStep, setLoadingStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [result, setResult] = useState<BuscaResult | null>(null);
  const [rawCount, setRawCount] = useState(0);

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
   * Submit search request with step tracking
   */
  const buscar = async () => {
    // Final validation check
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setLoading(true);
    setLoadingStep(1); // Consultando PNCP
    setError(null);
    setResult(null);
    setRawCount(0);

    try {
      // Simulate step progression for better UX
      // In future, use SSE for real-time updates
      const stepTimeout = setTimeout(() => setLoadingStep(2), 8000); // ~8s for PNCP
      const stepTimeout2 = setTimeout(() => setLoadingStep(3), 12000); // ~12s for filter + LLM start
      const stepTimeout3 = setTimeout(() => setLoadingStep(4), 18000); // ~18s for Excel

      const response = await fetch("/api/buscar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ufs: Array.from(ufsSelecionadas),
          data_inicial: dataInicial,
          data_final: dataFinal
        })
      });

      // Clear timeouts as we got response
      clearTimeout(stepTimeout);
      clearTimeout(stepTimeout2);
      clearTimeout(stepTimeout3);

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message || "Erro ao buscar licitacoes");
      }

      const data: BuscaResult = await response.json();
      setResult(data);
      setRawCount(data.total_raw || 0);

    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
      setLoadingStep(1);
    }
  };

  /**
   * Handle Excel download with error handling and loading state
   */
  const handleDownload = async () => {
    if (!result) return;

    setDownloadError(null);
    setDownloadLoading(true);

    try {
      const downloadUrl = `/api/download?id=${result.download_id}`;

      // Check if file exists by making a HEAD request first
      const headResponse = await fetch(downloadUrl, { method: 'HEAD' });

      if (!headResponse.ok) {
        if (headResponse.status === 404) {
          throw new Error('Arquivo nao encontrado ou expirado. Faca uma nova busca.');
        }
        throw new Error(`Erro ao fazer download: ${headResponse.statusText}`);
      }

      // Proceed with download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `bidiq_uniformes_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao fazer download do Excel';
      setDownloadError(`Erro no download: ${errorMessage}`);
    } finally {
      setDownloadLoading(false);
    }
  };

  // Check if form is valid
  const isFormValid = Object.keys(validationErrors).length === 0;

  return (
    <main className="max-w-4xl mx-auto p-6 sm:p-8">
      <h1 className="text-3xl font-bold mb-8 text-gray-900 dark:text-gray-100">
        BidIQ Uniformes
      </h1>

      {/* UF Selection Section */}
      <section className="mb-8">
        <div className="flex justify-between items-center mb-3">
          <label className="text-lg font-semibold text-gray-800 dark:text-gray-200">
            Selecione os Estados (UFs):
          </label>
          <div className="space-x-3">
            <button
              onClick={selecionarTodos}
              className="text-base font-medium text-green-700 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 hover:underline transition-colors"
              type="button"
            >
              Selecionar todos
            </button>
            <button
              onClick={limparSelecao}
              className="text-base font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:underline transition-colors"
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
              aria-pressed={ufsSelecionadas.has(uf)}
              className={`px-4 py-2 rounded-lg border-2 font-medium transition-all duration-150 ${
                ufsSelecionadas.has(uf)
                  ? "bg-green-600 text-white border-green-600 shadow-sm hover:bg-green-700"
                  : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/20"
              }`}
            >
              {uf}
            </button>
          ))}
        </div>

        <p className="text-base text-gray-600 dark:text-gray-400 mt-3">
          {ufsSelecionadas.size} estado(s) selecionado(s)
        </p>

        {/* Inline UF error */}
        {validationErrors.ufs && (
          <p className="text-base text-red-600 dark:text-red-400 mt-2 font-medium" role="alert">
            {validationErrors.ufs}
          </p>
        )}
      </section>

      {/* Date Range Section */}
      <section className="mb-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="data-inicial" className="block text-base font-semibold text-gray-800 dark:text-gray-200 mb-2">
              Data inicial:
            </label>
            <input
              id="data-inicial"
              type="date"
              value={dataInicial}
              onChange={e => setDataInicial(e.target.value)}
              className="w-full border-2 border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-base
                         bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                         focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500
                         transition-colors"
            />
          </div>
          <div className="flex-1">
            <label htmlFor="data-final" className="block text-base font-semibold text-gray-800 dark:text-gray-200 mb-2">
              Data final:
            </label>
            <input
              id="data-final"
              type="date"
              value={dataFinal}
              onChange={e => setDataFinal(e.target.value)}
              className="w-full border-2 border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-base
                         bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                         focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500
                         transition-colors"
            />
          </div>
        </div>

        {/* Inline date range error */}
        {validationErrors.date_range && (
          <p className="text-base text-red-600 dark:text-red-400 mt-3 font-medium" role="alert">
            {validationErrors.date_range}
          </p>
        )}
      </section>

      {/* Search Button */}
      <button
        onClick={buscar}
        disabled={loading || !isFormValid}
        type="button"
        aria-busy={loading}
        className="w-full bg-green-600 text-white py-4 rounded-lg text-lg font-semibold
                   hover:bg-green-700 active:bg-green-800
                   disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed
                   shadow-md hover:shadow-lg transition-all duration-150"
      >
        {loading ? "Buscando..." : "Buscar Licitacoes de Uniformes"}
      </button>

      {/* Loading State with Progress and Curiosities */}
      {loading && (
        <div aria-live="polite">
          <LoadingProgress
            currentStep={loadingStep}
            estimatedTime={45}
            stateCount={ufsSelecionadas.size}
          />
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-8 p-5 bg-red-50 dark:bg-red-900/30 border-2 border-red-300 dark:border-red-700 rounded-lg" role="alert">
          <p className="text-base font-medium text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Empty State - When search returns 0 filtered results */}
      {result && result.resumo.total_oportunidades === 0 && (
        <EmptyState
          onAdjustSearch={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          rawCount={rawCount}
          stateCount={ufsSelecionadas.size}
        />
      )}

      {/* Result Display - When search returns results */}
      {result && result.resumo.total_oportunidades > 0 && (
        <div className="mt-8 space-y-6">
          {/* Resumo LLM */}
          <div className="p-6 bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800 rounded-xl">
            <p className="text-lg leading-relaxed text-gray-800 dark:text-gray-200">
              {result.resumo.resumo_executivo}
            </p>

            <div className="flex flex-wrap gap-8 mt-6">
              <div>
                <span className="text-4xl font-bold text-green-700 dark:text-green-400">
                  {result.resumo.total_oportunidades}
                </span>
                <span className="text-base text-gray-700 dark:text-gray-300 block mt-1">licitacoes</span>
              </div>
              <div>
                <span className="text-4xl font-bold text-green-700 dark:text-green-400">
                  R$ {result.resumo.valor_total.toLocaleString("pt-BR")}
                </span>
                <span className="text-base text-gray-700 dark:text-gray-300 block mt-1">valor total</span>
              </div>
            </div>

            {result.resumo.alerta_urgencia && (
              <div className="mt-6 p-4 bg-yellow-100 dark:bg-yellow-900/30 border-2 border-yellow-400 dark:border-yellow-700 rounded-lg" role="alert">
                <p className="text-base font-medium text-yellow-800 dark:text-yellow-200">
                  <span aria-hidden="true">Atencao: </span>
                  {result.resumo.alerta_urgencia}
                </p>
              </div>
            )}

            {result.resumo.destaques.length > 0 && (
              <div className="mt-6">
                <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3">Destaques:</h4>
                <ul className="list-disc list-inside text-base space-y-2 text-gray-700 dark:text-gray-300">
                  {result.resumo.destaques.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Download Button with Loading State */}
          <button
            onClick={handleDownload}
            disabled={downloadLoading}
            aria-label={`Baixar Excel com ${result.resumo.total_oportunidades} licitacoes`}
            className="w-full bg-green-600 text-white py-4 rounded-lg text-lg font-semibold
                       hover:bg-green-700 active:bg-green-800
                       disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed
                       shadow-md hover:shadow-lg transition-all duration-150
                       flex items-center justify-center gap-3"
          >
            {downloadLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Preparando download...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Baixar Excel ({result.resumo.total_oportunidades} licitacoes)
              </>
            )}
          </button>

          {/* Download Error Display */}
          {downloadError && (
            <div className="p-5 bg-red-50 dark:bg-red-900/30 border-2 border-red-300 dark:border-red-700 rounded-lg" role="alert">
              <p className="text-base font-medium text-red-700 dark:text-red-300">{downloadError}</p>
            </div>
          )}

          {/* Search Stats */}
          <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
            {rawCount > 0 && (
              <p>
                Encontradas {result.resumo.total_oportunidades} de {rawCount.toLocaleString("pt-BR")} licitacoes
                ({((result.resumo.total_oportunidades / rawCount) * 100).toFixed(1)}% relacionadas a uniformes)
              </p>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
