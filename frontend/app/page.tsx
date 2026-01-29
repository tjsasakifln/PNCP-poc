"use client";

import { useState, useEffect } from "react";
import type { BuscaResult, ValidationErrors, Setor } from "./types";
import { LoadingProgress } from "./components/LoadingProgress";
import { EmptyState } from "./components/EmptyState";
import { ThemeToggle } from "./components/ThemeToggle";
import { RegionSelector } from "./components/RegionSelector";

const LOGO_URL = "https://static.wixstatic.com/media/d47bcc_9fc901ffe70149ae93fad0f461ff9565~mv2.png/v1/crop/x_0,y_301,w_5000,h_2398/fill/w_198,h_95,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Descomplicita%20-%20Azul.png";

const UFS = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
  "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
  "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

const UF_NAMES: Record<string, string> = {
  AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia",
  CE: "Ceará", DF: "Distrito Federal", ES: "Espírito Santo", GO: "Goiás",
  MA: "Maranhão", MT: "Mato Grosso", MS: "Mato Grosso do Sul", MG: "Minas Gerais",
  PA: "Pará", PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí",
  RJ: "Rio de Janeiro", RN: "Rio Grande do Norte", RS: "Rio Grande do Sul",
  RO: "Rondônia", RR: "Roraima", SC: "Santa Catarina", SP: "São Paulo",
  SE: "Sergipe", TO: "Tocantins",
};

function dateDiffInDays(date1: string, date2: string): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export default function HomePage() {
  const [setores, setSetores] = useState<Setor[]>([]);
  const [setorId, setSetorId] = useState("vestuario");

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

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [result, setResult] = useState<BuscaResult | null>(null);
  const [rawCount, setRawCount] = useState(0);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  useEffect(() => {
    fetch("/api/setores")
      .then(res => res.json())
      .then(data => {
        if (data.setores) setSetores(data.setores);
      })
      .catch(() => {
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
    setResult(null);
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
    setResult(null);
  };

  const selecionarTodos = () => { setUfsSelecionadas(new Set(UFS)); setResult(null); };
  const limparSelecao = () => { setUfsSelecionadas(new Set()); setResult(null); };

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
      link.download = `DescompLicita_${setorLabel}_${dataInicial}_a_${dataFinal}.xlsx`;
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
    <div className="min-h-screen">
      {/* Navigation Header */}
      <header className="border-b border-strong bg-surface-0 sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={LOGO_URL}
              alt="DescompLicita"
              width={140}
              height={67}
              className="h-10 w-auto"
            />
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden sm:block text-xs text-ink-muted font-medium">
              Busca Inteligente PNCP
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        {/* Page Title */}
        <div className="mb-8 animate-fade-in-up">
          <h1 className="text-2xl sm:text-3xl font-bold font-display text-ink">
            Busca de Licitações
          </h1>
          <p className="text-ink-secondary mt-1 text-sm sm:text-base">
            Encontre oportunidades de contratação pública no Portal Nacional (PNCP)
          </p>
        </div>

        {/* Sector Selection */}
        <section className="mb-6 animate-fade-in-up stagger-1">
          <label htmlFor="setor" className="block text-base font-semibold text-ink mb-2">
            Setor:
          </label>
          <select
            id="setor"
            value={setorId}
            onChange={e => { setSetorId(e.target.value); setResult(null); }}
            className="w-full border border-strong rounded-input px-4 py-3 text-base
                       bg-surface-0 text-ink
                       focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
                       transition-colors"
          >
            {setores.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </section>

        {/* UF Selection Section */}
        <section className="mb-6 animate-fade-in-up stagger-2">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-3">
            <label className="text-base sm:text-lg font-semibold text-ink">
              Estados (UFs):
            </label>
            <div className="flex gap-3">
              <button
                onClick={selecionarTodos}
                className="text-sm sm:text-base font-medium text-brand-blue hover:text-brand-blue-hover hover:underline transition-colors"
                type="button"
              >
                Selecionar todos
              </button>
              <button
                onClick={limparSelecao}
                className="text-sm sm:text-base font-medium text-ink-muted hover:text-ink transition-colors"
                type="button"
              >
                Limpar
              </button>
            </div>
          </div>

          {/* Region quick-select */}
          <RegionSelector selected={ufsSelecionadas} onToggleRegion={toggleRegion} />

          {/* UF Grid */}
          <div className="grid grid-cols-5 sm:grid-cols-7 md:grid-cols-9 gap-2">
            {UFS.map(uf => (
              <button
                key={uf}
                onClick={() => toggleUf(uf)}
                type="button"
                title={UF_NAMES[uf]}
                aria-pressed={ufsSelecionadas.has(uf)}
                className={`px-2 py-2 sm:px-4 rounded-button border text-sm sm:text-base font-medium transition-all duration-200 ${
                  ufsSelecionadas.has(uf)
                    ? "bg-brand-navy text-white border-brand-navy hover:bg-brand-blue-hover"
                    : "bg-surface-0 text-ink-secondary border hover:border-accent hover:text-brand-blue hover:bg-brand-blue-subtle"
                }`}
              >
                {uf}
              </button>
            ))}
          </div>

          <p className="text-sm sm:text-base text-ink-muted mt-2">
            {ufsSelecionadas.size === 1 ? '1 estado selecionado' : `${ufsSelecionadas.size} estados selecionados`}
          </p>

          {validationErrors.ufs && (
            <p className="text-sm sm:text-base text-error mt-2 font-medium" role="alert">
              {validationErrors.ufs}
            </p>
          )}
        </section>

        {/* Date Range Section */}
        <section className="mb-6 animate-fade-in-up stagger-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="data-inicial" className="block text-base font-semibold text-ink mb-2">
                Data inicial:
              </label>
              <input
                id="data-inicial"
                type="date"
                value={dataInicial}
                onChange={e => { setDataInicial(e.target.value); setResult(null); }}
                className="w-full border border-strong rounded-input px-4 py-3 text-base
                           bg-surface-0 text-ink
                           focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
                           transition-colors"
              />
            </div>
            <div>
              <label htmlFor="data-final" className="block text-base font-semibold text-ink mb-2">
                Data final:
              </label>
              <input
                id="data-final"
                type="date"
                value={dataFinal}
                onChange={e => { setDataFinal(e.target.value); setResult(null); }}
                className="w-full border border-strong rounded-input px-4 py-3 text-base
                           bg-surface-0 text-ink
                           focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
                           transition-colors"
              />
            </div>
          </div>

          {validationErrors.date_range && (
            <p className="text-sm sm:text-base text-error mt-3 font-medium" role="alert">
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
          className="w-full bg-brand-navy text-white py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                     hover:bg-brand-blue-hover active:bg-brand-blue
                     disabled:bg-ink-faint disabled:text-ink-muted disabled:cursor-not-allowed
                     transition-all duration-200"
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
          <div className="mt-6 sm:mt-8 p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card animate-fade-in-up" role="alert">
            <p className="text-sm sm:text-base font-medium text-error mb-3">{error}</p>
            <button
              onClick={buscar}
              disabled={loading}
              className="px-4 py-2 bg-error text-white rounded-button text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
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
          <div className="mt-6 sm:mt-8 space-y-4 sm:space-y-6 animate-fade-in-up">
            {/* Summary Card */}
            <div className="p-4 sm:p-6 bg-brand-blue-subtle border border-accent rounded-card">
              <p className="text-base sm:text-lg leading-relaxed text-ink">
                {result.resumo.resumo_executivo}
              </p>

              <div className="flex flex-col sm:flex-row flex-wrap gap-4 sm:gap-8 mt-4 sm:mt-6">
                <div>
                  <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
                    {result.resumo.total_oportunidades}
                  </span>
                  <span className="text-sm sm:text-base text-ink-secondary block mt-1">licitações</span>
                </div>
                <div>
                  <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
                    R$ {result.resumo.valor_total.toLocaleString("pt-BR")}
                  </span>
                  <span className="text-sm sm:text-base text-ink-secondary block mt-1">valor total</span>
                </div>
              </div>

              {result.resumo.alerta_urgencia && (
                <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-warning-subtle border border-warning/20 rounded-card" role="alert">
                  <p className="text-sm sm:text-base font-medium text-warning">
                    <span aria-hidden="true">Atenção: </span>
                    {result.resumo.alerta_urgencia}
                  </p>
                </div>
              )}

              {result.resumo.destaques.length > 0 && (
                <div className="mt-4 sm:mt-6">
                  <h4 className="text-base sm:text-lg font-semibold font-display text-ink mb-2 sm:mb-3">Destaques:</h4>
                  <ul className="list-disc list-inside text-sm sm:text-base space-y-2 text-ink-secondary">
                    {result.resumo.destaques.map((d, i) => (
                      <li key={i} className="animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>{d}</li>
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
              className="w-full bg-brand-navy text-white py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                         hover:bg-brand-blue-hover active:bg-brand-blue
                         disabled:bg-ink-faint disabled:text-ink-muted disabled:cursor-not-allowed
                         transition-all duration-200
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
              <div className="p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card" role="alert">
                <p className="text-sm sm:text-base font-medium text-error">{downloadError}</p>
              </div>
            )}

            {/* Stats */}
            <div className="text-xs sm:text-sm text-ink-muted text-center">
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

      {/* Footer */}
      <footer className="border-t mt-12 py-6 text-center text-xs text-ink-muted">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          DescompLicita &mdash; Licitações e Contratos de Forma Descomplicada
        </div>
      </footer>
    </div>
  );
}
