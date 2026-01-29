"use client";

import { useState, useEffect } from "react";

const CURIOSIDADES = [
  { texto: "A Lei 14.133/2021 substituiu a Lei 8.666/93 após 28 anos de vigência, modernizando as contratações públicas.", fonte: "Nova Lei de Licitações" },
  { texto: "A Nova Lei de Licitações trouxe o diálogo competitivo como nova modalidade de contratação.", fonte: "Lei 14.133/2021, Art. 32" },
  { texto: "A fase de habilitação agora pode ocorrer após o julgamento das propostas na Nova Lei.", fonte: "Lei 14.133/2021, Art. 17" },
  { texto: "A garantia contratual pode ser exigida em até 5% do valor do contrato, ou 10% para obras de grande vulto.", fonte: "Lei 14.133/2021, Art. 96" },
  { texto: "A Nova Lei permite o uso de seguro-garantia com cláusula de retomada, protegendo a Administração em obras.", fonte: "Lei 14.133/2021, Art. 102" },
  { texto: "O critério de julgamento por maior desconto substitui o antigo menor preço global em muitos casos.", fonte: "Lei 14.133/2021, Art. 33" },
  { texto: "A Lei 14.133 exige que todo processo licitatório tenha um agente de contratação designado.", fonte: "Lei 14.133/2021, Art. 8" },
  { texto: "A nova lei criou o Portal Nacional de Contratações Públicas (PNCP) como fonte única de publicidade oficial.", fonte: "Lei 14.133/2021, Art. 174" },
  { texto: "Contratos podem ser prorrogados por até 10 anos para serviços continuados, sem necessidade de nova licitação.", fonte: "Lei 14.133/2021, Art. 107" },
  { texto: "A Lei 14.133 prevê sanções como multa, impedimento e declaração de inidoneidade para licitantes.", fonte: "Lei 14.133/2021, Art. 155" },
  { texto: "O PNCP centraliza todas as licitações do Brasil desde 2023, abrangendo União, estados e municípios.", fonte: "Governo Federal" },
  { texto: "Qualquer cidadão pode consultar licitações em andamento no PNCP sem necessidade de cadastro.", fonte: "Portal PNCP" },
  { texto: "O PNCP disponibiliza uma API pública que permite consultas automatizadas de contratações.", fonte: "PNCP API Docs" },
  { texto: "Até 2025, o PNCP já acumulou mais de 3 milhões de publicações de contratações de todo o Brasil.", fonte: "Estatísticas PNCP" },
  { texto: "O Brasil realiza mais de 40 mil licitações por mês, movimentando bilhões em contratações públicas.", fonte: "Portal de Compras do Governo" },
  { texto: "O pregão eletrônico representa cerca de 80% de todas as licitações realizadas no país.", fonte: "Estatísticas PNCP" },
  { texto: "Compras públicas representam aproximadamente 12% do PIB brasileiro.", fonte: "OCDE / Governo Federal" },
  { texto: "Uniformes escolares movimentam cerca de R$ 2 bilhões por ano em licitações públicas.", fonte: "Estimativa de Mercado" },
  { texto: "Microempresas e EPPs têm tratamento diferenciado com preferência em licitações até R$ 80 mil.", fonte: "LC 123/2006, Art. 47-49" },
  { texto: "Monitorar licitações diariamente aumenta em até 3x as chances de encontrar oportunidades relevantes.", fonte: "Melhores Práticas de Mercado" },
];

interface LoadingProgressProps {
  currentStep?: number;
  estimatedTime?: number;
  stateCount?: number;
}

const STEPS = [
  { label: "Conectando ao PNCP", icon: "globe" },
  { label: "Consultando licitações", icon: "search" },
  { label: "Filtrando resultados", icon: "filter" },
  { label: "Gerando relatório", icon: "doc" },
];

export function LoadingProgress({
  currentStep = 1,
  estimatedTime = 45,
  stateCount = 1,
}: LoadingProgressProps) {
  const [curiosidadeIndex, setCuriosidadeIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCuriosidadeIndex((prev) => (prev + 1) % CURIOSIDADES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const curiosidade = CURIOSIDADES[curiosidadeIndex];

  // Determine active step based on elapsed time and state count
  const fetchTime = Math.max(15, stateCount * 5);
  const activeStep =
    elapsedTime < 5 ? 0
    : elapsedTime < fetchTime ? 1
    : elapsedTime < fetchTime + 10 ? 2
    : 3;

  // Estimated progress percentage (asymptotic — never reaches 100%)
  const rawProgress = Math.min(95, (elapsedTime / estimatedTime) * 85);
  const progress = Math.round(rawProgress);

  const statusMessage =
    elapsedTime < 5
      ? "Conectando ao PNCP..."
      : elapsedTime < fetchTime
        ? `Consultando ${stateCount} estado${stateCount > 1 ? "s" : ""} no PNCP...`
        : elapsedTime < fetchTime + 10
          ? "Filtrando e analisando licitações..."
          : "Gerando relatório e resumo executivo...";

  // Format elapsed time
  const minutes = Math.floor(elapsedTime / 60);
  const seconds = elapsedTime % 60;
  const timeDisplay = minutes > 0
    ? `${minutes}min ${seconds.toString().padStart(2, "0")}s`
    : `${seconds}s`;

  // Remaining estimate
  const remaining = Math.max(0, estimatedTime - elapsedTime);
  const remainingMin = Math.floor(remaining / 60);
  const remainingSec = remaining % 60;
  const remainingDisplay = remaining > 0
    ? remainingMin > 0
      ? `~${remainingMin}min ${remainingSec}s restantes`
      : `~${remainingSec}s restantes`
    : "Finalizando...";

  return (
    <div className="mt-8 p-6 bg-surface-1 rounded-card border animate-fade-in-up">
      {/* Progress Header */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-brand-blue">
            {statusMessage}
          </span>
          <span className="text-sm tabular-nums font-data text-ink-muted">
            {timeDisplay}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-blue to-brand-navy rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${Math.max(progress, 3)}%` }}
          />
        </div>
        <div className="flex justify-between items-center mt-1.5">
          <span className="text-xs text-ink-muted">{remainingDisplay}</span>
          <span className="text-xs tabular-nums font-data text-ink-muted">{progress}%</span>
        </div>
      </div>

      {/* Step Indicators */}
      <div className="flex items-center justify-between mb-6 px-2">
        {STEPS.map((step, i) => (
          <div key={step.label} className="flex items-center gap-1.5">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
              i < activeStep
                ? "bg-brand-navy text-white"
                : i === activeStep
                  ? "bg-brand-blue text-white animate-pulse"
                  : "bg-surface-2 text-ink-muted"
            }`}>
              {i < activeStep ? (
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                i + 1
              )}
            </div>
            <span className={`text-xs hidden sm:inline ${
              i <= activeStep ? "text-ink font-medium" : "text-ink-muted"
            }`}>
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <div className={`w-4 sm:w-8 h-0.5 mx-1 ${
                i < activeStep ? "bg-brand-navy" : "bg-surface-2"
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Curiosity Card */}
      <div className="p-4 bg-surface-0 rounded-card border transition-all duration-300">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 bg-brand-blue-subtle rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-ink-muted mb-1">Você sabia?</p>
            <p className="text-base text-ink leading-relaxed">{curiosidade.texto}</p>
            <p className="text-xs text-ink-muted mt-2">Fonte: {curiosidade.fonte}</p>
          </div>
        </div>
      </div>

      {/* Context Info */}
      <p className="mt-4 text-xs text-center text-ink-muted">
        Buscando em {stateCount} estado{stateCount > 1 ? "s" : ""} com 5 modalidades de contratação
      </p>
    </div>
  );
}

export default LoadingProgress;
