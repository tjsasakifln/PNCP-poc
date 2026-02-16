"use client";

import { useState, useEffect, useRef } from "react";
import { useAnalytics } from "../../hooks/useAnalytics";

const CURIOSIDADES = [
  { texto: "A Lei 14.133/2021 substituiu a Lei 8.666/93 após 28 anos de vigência, modernizando as contratações públicas.", fonte: "Nova Lei de Licitações" },
  { texto: "A Nova Lei de Licitações trouxe o diálogo competitivo como nova modalidade de contratação.", fonte: "Lei 14.133/2021, Art. 32" },
  { texto: "A fase de habilitação agora pode ocorrer após o julgamento das propostas na Nova Lei.", fonte: "Lei 14.133/2021, Art. 17" },
  { texto: "A garantia contratual pode ser exigida em até 5% do valor do contrato, ou 10% para obras de grande vulto.", fonte: "Lei 14.133/2021, Art. 96" },
  { texto: "A Nova Lei permite o uso de seguro-garantia com cláusula de retomada, protegendo a Administração em obras.", fonte: "Lei 14.133/2021, Art. 102" },
  { texto: "O critério de julgamento por maior desconto substitui o antigo menor preço global em muitos casos.", fonte: "Lei 14.133/2021, Art. 33" },
  { texto: "A Lei 14.133 exige que todo processo licitatório tenha um agente de contratação designado.", fonte: "Lei 14.133/2021, Art. 8" },
  { texto: "A nova lei criou um portal nacional como fonte única de publicidade oficial para contratações.", fonte: "Lei 14.133/2021, Art. 174" },
  { texto: "Contratos podem ser prorrogados por até 10 anos para serviços continuados, sem necessidade de nova licitação.", fonte: "Lei 14.133/2021, Art. 107" },
  { texto: "A Lei 14.133 prevê sanções como multa, impedimento e declaração de inidoneidade para licitantes.", fonte: "Lei 14.133/2021, Art. 155" },
  { texto: "O portal nacional centraliza todas as licitações do Brasil desde 2023, abrangendo União, estados e municípios.", fonte: "Governo Federal" },
  { texto: "Qualquer cidadão pode consultar licitações em andamento nos portais oficiais sem necessidade de cadastro.", fonte: "Governo Federal" },
  { texto: "Fontes oficiais disponibilizam APIs públicas que permitem consultas automatizadas de contratações.", fonte: "Governo Federal" },
  { texto: "Os portais oficiais já acumulam mais de 3 milhões de publicações de contratações de todo o Brasil.", fonte: "Governo Federal" },
  { texto: "O Brasil realiza mais de 40 mil licitações por mês, movimentando bilhões em contratações públicas.", fonte: "Portal de Compras do Governo" },
  { texto: "O pregão eletrônico representa cerca de 80% de todas as licitações realizadas no país.", fonte: "Governo Federal" },
  { texto: "Compras públicas representam aproximadamente 12% do PIB brasileiro.", fonte: "OCDE / Governo Federal" },
  { texto: "Uniformes escolares movimentam cerca de R$ 2 bilhões por ano em licitações públicas.", fonte: "Estimativa de Mercado" },
  { texto: "Microempresas e EPPs têm tratamento diferenciado com preferência em licitações até R$ 80 mil.", fonte: "LC 123/2006, Art. 47-49" },
  { texto: "Monitorar licitações diariamente aumenta em até 3x as chances de encontrar oportunidades relevantes.", fonte: "Melhores Práticas de Mercado" },
];

type SearchStage = 'connecting' | 'fetching' | 'filtering' | 'summarizing' | 'generating_excel';

interface LoadingProgressProps {
  currentStep?: number;
  estimatedTime?: number;
  stateCount?: number;
}

// 5-Stage Progress Indicator Configuration
const STAGES = [
  {
    id: 'connecting' as SearchStage,
    label: "Conectando às fontes oficiais",
    icon: "🔍",
    progressStart: 0,
    progressEnd: 20,
  },
  {
    id: 'fetching' as SearchStage,
    label: "Buscando licitações",
    icon: "📥",
    progressStart: 20,
    progressEnd: 50,
  },
  {
    id: 'filtering' as SearchStage,
    label: "Filtrando resultados",
    icon: "🎯",
    progressStart: 50,
    progressEnd: 75,
  },
  {
    id: 'summarizing' as SearchStage,
    label: "Gerando resumo IA",
    icon: "🤖",
    progressStart: 75,
    progressEnd: 90,
  },
  {
    id: 'generating_excel' as SearchStage,
    label: "Preparando planilha",
    icon: "✅",
    progressStart: 90,
    progressEnd: 100,
  },
];

// Time estimation formula (calibrated from production data - Jan 2026)
// Real-world measurements show ~20-25s per state due to PNCP API latency
const estimateTotalTime = (ufCount: number): number => {
  const baseTime = 15;     // 15s minimum (connection + initial setup)
  const perUfTime = 20;    // 20s per state (PNCP API is slow)
  const filteringTime = 3; // 3s filtering
  const llmTime = 8;       // 8s LLM (GPT-4.1-nano)
  const excelTime = 5;     // 5s Excel generation

  return baseTime + (ufCount * perUfTime) + filteringTime + llmTime + excelTime;
};

export function LoadingProgress({
  currentStep = 1,
  estimatedTime,
  stateCount = 1,
}: LoadingProgressProps) {
  const [curiosidadeIndex, setCuriosidadeIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const { trackEvent } = useAnalytics();

  // Track which stages have been reached (to avoid duplicate events)
  const stagesReachedRef = useRef<Set<SearchStage>>(new Set());

  // Use estimated time from formula if not provided
  const totalEstimatedTime = estimatedTime || estimateTotalTime(stateCount);

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

  // Calculate current stage based on elapsed time
  const getCurrentStage = (): SearchStage => {
    const progressPercent = (elapsedTime / totalEstimatedTime) * 100;

    for (const stage of STAGES) {
      if (progressPercent >= stage.progressStart && progressPercent < stage.progressEnd) {
        return stage.id;
      }
    }

    // If beyond 100%, return last stage
    return 'generating_excel';
  };

  const currentStage = getCurrentStage();
  const currentStageIndex = STAGES.findIndex(s => s.id === currentStage);
  const stageConfig = STAGES[currentStageIndex];

  // Calculate progress percentage (0-100) with asymptotic behavior
  const calculateProgress = (): number => {
    const rawProgress = (elapsedTime / totalEstimatedTime) * 100;

    // Asymptotic function: never reaches 100% until actually complete
    // Progress slows down as it approaches 100%
    const asymptotic = Math.min(95, rawProgress * 0.95);

    return Math.round(asymptotic);
  };

  const progress = calculateProgress();

  // Track stage progression (analytics)
  useEffect(() => {
    if (!stagesReachedRef.current.has(currentStage)) {
      stagesReachedRef.current.add(currentStage);

      trackEvent('loading_stage_reached', {
        stage: currentStage,
        stage_index: currentStageIndex,
        elapsed_time_s: elapsedTime,
        estimated_total_s: totalEstimatedTime,
        progress_percent: progress,
        state_count: stateCount,
      });
    }
  }, [currentStage, currentStageIndex, elapsedTime, totalEstimatedTime, progress, stateCount, trackEvent]);

  // Track loading abandonment (user navigates away)
  useEffect(() => {
    const handleBeforeUnload = () => {
      trackEvent('loading_abandoned', {
        last_stage: currentStage,
        last_stage_index: currentStageIndex,
        elapsed_time_s: elapsedTime,
        progress_percent: progress,
        state_count: stateCount,
      });
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [currentStage, currentStageIndex, elapsedTime, progress, stateCount, trackEvent]);

  // Dynamic status messages based on current stage
  const getStatusMessage = (): string => {
    switch (currentStage) {
      case 'connecting':
        return "Estabelecendo conexão com Portal Nacional...";
      case 'fetching':
        const estimatedPages = Math.ceil(stateCount * 1.5); // Rough estimate
        return `Consultando ${stateCount} estado${stateCount > 1 ? "s" : ""} em ~${estimatedPages} página${estimatedPages > 1 ? "s" : ""}...`;
      case 'filtering':
        return "Aplicando filtros de setor e valor...";
      case 'summarizing':
        return "Analisando licitações com IA...";
      case 'generating_excel':
        return "Finalizando Excel...";
      default:
        return "Processando...";
    }
  };

  const statusMessage = getStatusMessage();

  // Format elapsed time - cap display at estimated time when exceeded
  const displayElapsed = elapsedTime > totalEstimatedTime ? totalEstimatedTime : elapsedTime;
  const minutes = Math.floor(displayElapsed / 60);
  const seconds = displayElapsed % 60;

  // Check if time exceeded estimated - show different message
  const isTimeExceeded = elapsedTime > totalEstimatedTime;
  const timeDisplay = isTimeExceeded
    ? "Finalizando..."
    : minutes > 0
      ? `${minutes}min ${seconds.toString().padStart(2, "0")}s`
      : `${seconds}s`;

  // Remaining estimate - show "Finalizando..." when exceeded
  const remaining = Math.max(0, totalEstimatedTime - elapsedTime);
  const remainingMin = Math.floor(remaining / 60);
  const remainingSec = remaining % 60;
  const remainingDisplay = isTimeExceeded
    ? "Quase la! A busca esta demorando mais que o esperado..."
    : remaining > 0
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
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        <div className="flex justify-between items-center mt-1.5">
          <span className="text-xs text-ink-muted">{remainingDisplay}</span>
          <span className="text-xs tabular-nums font-data text-ink-muted">{progress}%</span>
        </div>
      </div>

      {/* 5-Stage Indicators */}
      <div className="flex items-center justify-between mb-6 px-2">
        {STAGES.map((stage, i) => {
          const isPast = i < currentStageIndex;
          const isCurrent = i === currentStageIndex;
          const isFuture = i > currentStageIndex;

          return (
            <div key={stage.id} className="flex items-center gap-1.5">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                isPast
                  ? "bg-brand-navy text-white"
                  : isCurrent
                    ? "bg-brand-blue text-white animate-pulse shadow-lg"
                    : "bg-surface-2 text-ink-muted"
              }`}>
                {isPast ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3} role="img" aria-label="Completed">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span className="text-base" aria-hidden="true">{stage.icon}</span>
                )}
              </div>
              <div className="flex flex-col hidden sm:block">
                <span className={`text-xs font-medium ${
                  isPast || isCurrent ? "text-ink" : "text-ink-muted"
                }`}>
                  {stage.label}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <div className={`w-3 sm:w-6 h-0.5 mx-1 transition-colors duration-300 ${
                  isPast ? "bg-brand-navy" : "bg-surface-2"
                }`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Current Stage Detail (Mobile-friendly) */}
      <div className="sm:hidden mb-4 p-3 bg-surface-0 rounded-lg border border-accent">
        <div className="flex items-center gap-2">
          <span className="text-xl" aria-hidden="true">{stageConfig.icon}</span>
          <div className="flex-1">
            <p className="text-sm font-semibold text-ink">{stageConfig.label}</p>
            <p className="text-xs text-ink-muted">{statusMessage}</p>
          </div>
        </div>
      </div>

      {/* Curiosity Card */}
      <div className="p-4 bg-surface-0 rounded-card border transition-all duration-300">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 bg-brand-blue-subtle rounded-full flex items-center justify-center">
            <svg
              role="img"
              aria-label="Informação" className="w-4 h-4 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
