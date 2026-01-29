"use client";

import { useState, useEffect } from "react";
import type { BuscaResult, ValidationErrors, Setor } from "./types";
import { LoadingProgress } from "./components/LoadingProgress";
import { EmptyState } from "./components/EmptyState";
import { ThemeToggle } from "./components/ThemeToggle";
import { RegionSelector } from "./components/RegionSelector";

const UFS = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
  "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
  "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

function dateDiffInDays(date1: string, date2: string): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export default function HomePage() {
  // Sector state
  const [setores, setSetores] = useState<Setor[]>([]);
  const [setorId, setSetorId] = useState("vestuario");

  // Form state
  const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(
    new Set(["SC", "PR", "RS"])
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

  // Fetch sectors on mount
  useEffect(() => {
    fetch("/api/setores")
      .then(res => res.json())
      .then(data => {
        if (data.setores) setSetores(data.setores);
      })
      .catch(() => {
        // Fallback: use default sector list
        setSetores([
          { id: "vestuario", name: "Vestuário e Uniformes", description: "" },
          { id: "alimentos", name: "Alimentos e Merenda", description: "" },
          { id: "informatica", name: "Informática e Tecnologia", description: "" },
          { id: "limpeza", name: "Produtos de Limpeza", description: "" },
          { id: "mobiliario", name: "Mobiliário", description: "" },
          { id: "papelaria", name: "Papelaria e Material de Escritório", description: "" },
          { id: "engenharia", name: "Engenharia e Construção", description: "" },
        ]);
      });
  }, []);

  function validateForm(): ValidationErrors {
    const errors: ValidationErrors = {};
    if (ufsSelecionadas.size === 0) {
      errors.ufs = "Selecione pelo menos um estado";
    }
    if (dataFinal < dataInicial) {
      errors.date_range = "Data final deve ser maior ou igual à data inicial";
    }
    return errors;
  }

  useEffect(() => {
    setValidationErrors(validateForm());
  }, [ufsSelecionadas, dataInicial, dataFinal]);

  const toggleUf = (uf: string) => {
    const newSet = new Set(ufsSelecionadas);
    if (newSet.has(uf)) {
      newSet.delete(uf);
    } else {
      newSet.add(uf);
    }
    setUfsSelecionadas(newSet);
  };

  const toggleRegion = (regionUfs: string[]) => {
    const allSelected = regionUfs.every(uf => ufsSelecionadas.has(uf));
    const newSet = new Set(ufsSelecionadas);
    if (allSelected) {
      regionUfs.forEach(uf => newSet.delete(uf));
    } else {
      regionUfs.forEach(uf => newSet.add(uf));
    }
    setUfsSelecionadas(newSet);
  };

  const selecionarTodos = () => setUfsSelecionadas(new Set(UFS));
  const limparSelecao = () => setUfsSelecionadas(new Set());

  const sectorName = setores.find(s => s.id === setorId)?.name || "Licitações";

  const buscar = async () => {
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setLoading(true);
    setLoadingStep(1);
    setError(null);
    setResult(null);
    setRawCount(0);

    try {
      // Step 1 = "Consultando PNCP" (real — waiting for backend)
      const response = await fetch("/api/buscar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ufs: Array.from(ufsSelecionadas),
          data_inicial: dataInicial,
          data_final: dataFinal,
          setor_id: setorId,
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message || "Erro ao buscar licitações");
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

  const handleDownload = async () => {
    if (!result?.download_id) return;
    setDownloadError(null);
    setDownloadLoading(true);

    try {
      const downloadUrl = `/api/download?id=${result.download_id}`;
      const response = await fetch(downloadUrl);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Arquivo expirado. Faça uma nova busca para gerar o Excel.');
        }
        throw new Error('Não foi possível baixar o arquivo. Tente novamente.');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const setorLabel = sectorName.replace(/\s+/g, '_');
      link.download = `BidIQ_${setorLabel}_${dataInicial}_a_${dataFinal}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Não foi possível baixar o arquivo.';
      setDownloadError(errorMessage);
    } finally {
      setDownloadLoading(false);
    }
  };

  const isFormValid = Object.keys(validationErrors).length === 0;

  return (
    <main className="max-w-4xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold font-display text-gray-900 dark:text-gray-100">
          BidIQ
        </h1>
        <ThemeToggle />
      </div>

      {/* Sector Selection */}
      <section className="mb-6">
        <label htmlFor="setor" className="block text-base font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Setor:
        </label>
        <select
          id="setor"
          value={setorId}
          onChange={e => setSetorId(e.target.value)}
          className="w-full border border-gray-300/80 dark:border-gray-600/60 rounded-lg px-4 py-3 text-base
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-emerald-600
                     transition-colors"
        >
          {setores.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </section>

      {/* UF Selection Section */}
      <section className="mb-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-3">
          <label className="text-base sm:text-lg font-semibold text-gray-800 dark:text-gray-200">
            Estados (UFs):
          </label>
          <div className="flex gap-3">
            <button
              onClick={selecionarTodos}
              className="text-sm sm:text-base font-medium text-green-700 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 hover:underline transition-colors"
              type="button"
            >
              Selecionar todos
            </button>
            <button
              onClick={limparSelecao}
              className="text-sm sm:text-base font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:underline transition-colors"
              type="button"
            >
              Limpar
            </button>
          </div>
        </div>

        {/* Region quick-select */}
        <RegionSelector selected={ufsSelecionadas} onToggleRegion={toggleRegion} />

        {/* UF Grid */}
        <div className="grid grid-cols-5 sm:grid-cols-7 md:grid-cols-9 gap-1.5 sm:gap-2">
          {UFS.map(uf => (
            <button
              key={uf}
              onClick={() => toggleUf(uf)}
              type="button"
              aria-pressed={ufsSelecionadas.has(uf)}
              className={`px-2 py-2 sm:px-4 rounded-lg border text-sm sm:text-base font-medium transition-all duration-150 ${
                ufsSelecionadas.has(uf)
                  ? "bg-green-600 text-white border-green-600 hover:bg-green-700"
                  : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200/60 dark:border-gray-700/40 hover:border-green-500/50 hover:bg-green-50 dark:hover:bg-green-900/20"
              }`}
            >
              {uf}
            </button>
          ))}
        </div>

        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-2">
          {ufsSelecionadas.size} estado(s) selecionado(s)
        </p>

        {validationErrors.ufs && (
          <p className="text-sm sm:text-base text-red-600 dark:text-red-400 mt-2 font-medium" role="alert">
            {validationErrors.ufs}
          </p>
        )}
      </section>

      {/* Date Range Section */}
      <section className="mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="data-inicial" className="block text-base font-semibold text-gray-800 dark:text-gray-200 mb-2">
              Data inicial:
            </label>
            <input
              id="data-inicial"
              type="date"
              value={dataInicial}
              onChange={e => setDataInicial(e.target.value)}
              className="w-full border border-gray-300/80 dark:border-gray-600/60 rounded-lg px-4 py-3 text-base
                         bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                         focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-emerald-600
                         transition-colors"
            />
          </div>
          <div>
            <label htmlFor="data-final" className="block text-base font-semibold text-gray-800 dark:text-gray-200 mb-2">
              Data final:
            </label>
            <input
              id="data-final"
              type="date"
              value={dataFinal}
              onChange={e => setDataFinal(e.target.value)}
              className="w-full border border-gray-300/80 dark:border-gray-600/60 rounded-lg px-4 py-3 text-base
                         bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                         focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-emerald-600
                         transition-colors"
            />
          </div>
        </div>

        {validationErrors.date_range && (
          <p className="text-sm sm:text-base text-red-600 dark:text-red-400 mt-3 font-medium" role="alert">
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
        className="w-full bg-emerald-700 text-white py-3.5 sm:py-4 rounded-md text-base sm:text-lg font-semibold
                   hover:bg-emerald-800 active:bg-emerald-900
                   disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed
                   transition-all duration-150"
      >
        {loading ? "Buscando..." : `Buscar ${sectorName}`}
      </button>

      {/* Loading State */}
      {loading && (
        <div aria-live="polite">
          <LoadingProgress
            currentStep={loadingStep}
            estimatedTime={Math.max(30, ufsSelecionadas.size * 6)}
            stateCount={ufsSelecionadas.size}
          />
        </div>
      )}

      {/* Error Display with Retry */}
      {error && (
        <div className="mt-6 sm:mt-8 p-4 sm:p-5 bg-red-50 dark:bg-red-900/30 border border-red-500/20 dark:border-red-400/20 rounded-lg" role="alert">
          <p className="text-sm sm:text-base font-medium text-red-700 dark:text-red-300 mb-3">{error}</p>
          <button
            onClick={buscar}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Empty State */}
      {result && result.resumo.total_oportunidades === 0 && (
        <EmptyState
          onAdjustSearch={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          rawCount={rawCount}
          stateCount={ufsSelecionadas.size}
          filterStats={result.filter_stats}
          sectorName={sectorName}
        />
      )}

      {/* Result Display */}
      {result && result.resumo.total_oportunidades > 0 && (
        <div className="mt-6 sm:mt-8 space-y-4 sm:space-y-6">
          {/* Summary Card */}
          <div className="p-4 sm:p-6 bg-green-50 dark:bg-green-900/20 border border-green-500/20 dark:border-green-400/20 rounded-xl">
            <p className="text-base sm:text-lg leading-relaxed text-gray-800 dark:text-gray-200">
              {result.resumo.resumo_executivo}
            </p>

            <div className="flex flex-col sm:flex-row flex-wrap gap-4 sm:gap-8 mt-4 sm:mt-6">
              <div>
                <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-green-700 dark:text-green-400">
                  {result.resumo.total_oportunidades}
                </span>
                <span className="text-sm sm:text-base text-gray-700 dark:text-gray-300 block mt-1">licitações</span>
              </div>
              <div>
                <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-green-700 dark:text-green-400">
                  R$ {result.resumo.valor_total.toLocaleString("pt-BR")}
                </span>
                <span className="text-sm sm:text-base text-gray-700 dark:text-gray-300 block mt-1">valor total</span>
              </div>
            </div>

            {result.resumo.alerta_urgencia && (
              <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-500/20 dark:border-yellow-400/20 rounded-lg" role="alert">
                <p className="text-sm sm:text-base font-medium text-yellow-800 dark:text-yellow-200">
                  <span aria-hidden="true">Atenção: </span>
                  {result.resumo.alerta_urgencia}
                </p>
              </div>
            )}

            {result.resumo.destaques.length > 0 && (
              <div className="mt-4 sm:mt-6">
                <h4 className="text-base sm:text-lg font-semibold font-display text-gray-800 dark:text-gray-200 mb-2 sm:mb-3">Destaques:</h4>
                <ul className="list-disc list-inside text-sm sm:text-base space-y-1.5 sm:space-y-2 text-gray-700 dark:text-gray-300">
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
            disabled={downloadLoading}
            aria-label={`Baixar Excel com ${result.resumo.total_oportunidades} licitações`}
            className="w-full bg-emerald-700 text-white py-3.5 sm:py-4 rounded-md text-base sm:text-lg font-semibold
                       hover:bg-emerald-800 active:bg-emerald-900
                       disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed
                       transition-all duration-150
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
                Baixar Excel ({result.resumo.total_oportunidades} licitações)
              </>
            )}
          </button>

          {/* Download Error */}
          {downloadError && (
            <div className="p-4 sm:p-5 bg-red-50 dark:bg-red-900/30 border border-red-500/20 dark:border-red-400/20 rounded-lg" role="alert">
              <p className="text-sm sm:text-base font-medium text-red-700 dark:text-red-300">{downloadError}</p>
            </div>
          )}

          {/* Stats */}
          <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 text-center">
            {rawCount > 0 && (
              <p>
                Encontradas {result.resumo.total_oportunidades} de {rawCount.toLocaleString("pt-BR")} licitações
                ({((result.resumo.total_oportunidades / rawCount) * 100).toFixed(1)}% do setor {sectorName.toLowerCase()})
              </p>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
