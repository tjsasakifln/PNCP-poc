"use client";

import { useState, useEffect } from "react";

/**
 * Curiosities about Lei 14.133/2021 and Brazilian procurement market
 * Displayed during loading to make wait time educational and engaging
 */
const CURIOSIDADES = [
  {
    texto: "A Lei 14.133/2021 substituiu a Lei 8.666/93 apos 28 anos de vigencia.",
    fonte: "Nova Lei de Licitacoes",
  },
  {
    texto: "O Brasil realiza mais de 40 mil licitacoes por mes, movimentando bilhoes em contratacoes publicas.",
    fonte: "Portal de Compras do Governo",
  },
  {
    texto: "O pregao eletronico representa cerca de 80% de todas as licitacoes realizadas no pais.",
    fonte: "Estatisticas PNCP",
  },
  {
    texto: "A Nova Lei de Licitacoes trouxe o dialogo competitivo como nova modalidade de contratacao.",
    fonte: "Lei 14.133/2021",
  },
  {
    texto: "Uniformes escolares movimentam cerca de R$ 2 bilhoes por ano em licitacoes publicas.",
    fonte: "Estimativa de Mercado",
  },
  {
    texto: "O PNCP (Portal Nacional de Contratacoes Publicas) centraliza todas as licitacoes do Brasil desde 2023.",
    fonte: "Governo Federal",
  },
  {
    texto: "Microempresas e EPPs tem tratamento diferenciado com preferencia em licitacoes ate R$ 80 mil.",
    fonte: "LC 123/2006",
  },
  {
    texto: "A fase de habilitacao agora pode ocorrer apos o julgamento das propostas na Nova Lei.",
    fonte: "Lei 14.133/2021",
  },
  {
    texto: "Orgaos publicos devem publicar seus editais com antecedencia minima de 8 dias uteis para pregao.",
    fonte: "Lei 14.133/2021",
  },
  {
    texto: "O setor de vestuario profissional cresce cerca de 5% ao ano no mercado de licitacoes.",
    fonte: "Analise de Mercado",
  },
  {
    texto: "Estados e municipios respondem por 70% do volume de licitacoes de uniformes no Brasil.",
    fonte: "Dados PNCP",
  },
  {
    texto: "A margem de preferencia para produtos nacionais pode chegar a 25% em licitacoes federais.",
    fonte: "Lei 14.133/2021",
  },
  {
    texto: "O SICAF (Sistema de Cadastramento Unificado de Fornecedores) facilita a participacao em licitacoes federais.",
    fonte: "Governo Federal",
  },
  {
    texto: "Contratos de uniformes geralmente tem vigencia de 12 meses, prorrogaveis por ate 10 anos.",
    fonte: "Lei 14.133/2021",
  },
  {
    texto: "A garantia contratual pode ser exigida em ate 5% do valor do contrato.",
    fonte: "Lei 14.133/2021",
  },
];

interface ProgressStep {
  id: string;
  label: string;
  status: "pending" | "active" | "completed";
}

interface LoadingProgressProps {
  /** Current step (1-4) */
  currentStep?: number;
  /** Estimated total time in seconds */
  estimatedTime?: number;
  /** Number of states being searched */
  stateCount?: number;
}

/**
 * Loading progress component with educational curiosities
 *
 * Features:
 * - Progress bar with percentage
 * - Step-by-step status indicators
 * - Rotating curiosity facts about Lei 14.133 and procurement
 * - Estimated time remaining
 */
export function LoadingProgress({
  currentStep = 1,
  estimatedTime = 45,
  stateCount = 1,
}: LoadingProgressProps) {
  const [curiosidadeIndex, setCuriosidadeIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Rotate curiosities every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCuriosidadeIndex((prev) => (prev + 1) % CURIOSIDADES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Track elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const steps: ProgressStep[] = [
    {
      id: "fetch",
      label: "Consultando PNCP",
      status: currentStep > 1 ? "completed" : currentStep === 1 ? "active" : "pending",
    },
    {
      id: "filter",
      label: "Filtrando resultados",
      status: currentStep > 2 ? "completed" : currentStep === 2 ? "active" : "pending",
    },
    {
      id: "llm",
      label: "Gerando resumo com IA",
      status: currentStep > 3 ? "completed" : currentStep === 3 ? "active" : "pending",
    },
    {
      id: "excel",
      label: "Preparando Excel",
      status: currentStep > 4 ? "completed" : currentStep === 4 ? "active" : "pending",
    },
  ];

  // Calculate progress percentage based on step
  const progressPercent = Math.min(((currentStep - 1) / 4) * 100 + 12.5, 100);

  const curiosidade = CURIOSIDADES[curiosidadeIndex];

  return (
    <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Progresso
          </span>
          <span className="text-sm font-medium text-green-600 dark:text-green-400">
            {Math.round(progressPercent)}%
          </span>
        </div>
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3 mb-6">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center gap-3">
            {/* Status indicator */}
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300
                ${step.status === "completed" ? "bg-green-600 text-white" : ""}
                ${step.status === "active" ? "bg-green-600 text-white animate-pulse ring-4 ring-green-200 dark:ring-green-900" : ""}
                ${step.status === "pending" ? "bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500" : ""}
              `}
            >
              {step.status === "completed" ? (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </div>

            {/* Label */}
            <span
              className={`text-base transition-colors duration-300
                ${step.status === "active" ? "font-semibold text-green-700 dark:text-green-400" : ""}
                ${step.status === "completed" ? "text-gray-500 dark:text-gray-400 line-through" : ""}
                ${step.status === "pending" ? "text-gray-400 dark:text-gray-500" : ""}
              `}
            >
              {step.label}
              {step.status === "active" && "..."}
            </span>
          </div>
        ))}
      </div>

      {/* Curiosity Card */}
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200/60 dark:border-gray-700/40">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
            <svg
              className="w-4 h-4 text-green-600 dark:text-green-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Voce sabia?
            </p>
            <p className="text-base text-gray-800 dark:text-gray-200 leading-relaxed">
              {curiosidade.texto}
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
              Fonte: {curiosidade.fonte}
            </p>
          </div>
        </div>
      </div>

      {/* Time Info */}
      <div className="mt-4 flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
        <span>
          Buscando em {stateCount} estado{stateCount > 1 ? "s" : ""}
        </span>
        <span>
          {elapsedTime}s / ~{estimatedTime}s
        </span>
      </div>
    </div>
  );
}

export default LoadingProgress;
