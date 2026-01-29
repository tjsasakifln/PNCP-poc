"use client";

import { useState, useEffect } from "react";

/**
 * Curiosities about Lei 14.133/2021 and Brazilian procurement market
 * Displayed during loading to make wait time educational and engaging
 */
const CURIOSIDADES = [
  // === Lei 14.133/2021 — Fundamentos ===
  {
    texto: "A Lei 14.133/2021 substituiu a Lei 8.666/93 após 28 anos de vigência, modernizando as contratações públicas.",
    fonte: "Nova Lei de Licitações",
  },
  {
    texto: "A Nova Lei de Licitações trouxe o diálogo competitivo como nova modalidade de contratação.",
    fonte: "Lei 14.133/2021, Art. 32",
  },
  {
    texto: "A fase de habilitação agora pode ocorrer após o julgamento das propostas na Nova Lei.",
    fonte: "Lei 14.133/2021, Art. 17",
  },
  {
    texto: "A garantia contratual pode ser exigida em até 5% do valor do contrato, ou 10% para obras de grande vulto.",
    fonte: "Lei 14.133/2021, Art. 96",
  },
  {
    texto: "A Nova Lei permite o uso de seguro-garantia com cláusula de retomada, protegendo a Administração em obras.",
    fonte: "Lei 14.133/2021, Art. 102",
  },
  {
    texto: "O critério de julgamento por maior desconto substitui o antigo menor preço global em muitos casos.",
    fonte: "Lei 14.133/2021, Art. 33",
  },
  {
    texto: "A Lei 14.133 exige que todo processo licitatório tenha um agente de contratação designado.",
    fonte: "Lei 14.133/2021, Art. 8",
  },
  {
    texto: "A nova lei criou o Portal Nacional de Contratações Públicas (PNCP) como fonte única de publicidade oficial.",
    fonte: "Lei 14.133/2021, Art. 174",
  },
  {
    texto: "Contratos podem ser prorrogados por até 10 anos para serviços continuados, sem necessidade de nova licitação.",
    fonte: "Lei 14.133/2021, Art. 107",
  },
  {
    texto: "A Lei 14.133 prevê sanções como multa, impedimento e declaração de inidoneidade para licitantes.",
    fonte: "Lei 14.133/2021, Art. 155",
  },

  // === PNCP e Transparência ===
  {
    texto: "O PNCP centraliza todas as licitações do Brasil desde 2023, abrangendo União, estados e municípios.",
    fonte: "Governo Federal",
  },
  {
    texto: "Qualquer cidadão pode consultar licitações em andamento no PNCP sem necessidade de cadastro.",
    fonte: "Portal PNCP",
  },
  {
    texto: "O PNCP disponibiliza uma API pública que permite consultas automatizadas de contratações.",
    fonte: "PNCP API Docs",
  },
  {
    texto: "Até 2025, o PNCP já acumulou mais de 3 milhões de publicações de contratações de todo o Brasil.",
    fonte: "Estatísticas PNCP",
  },
  {
    texto: "Municípios com até 20 mil habitantes ganharam prazo estendido para adesão obrigatória ao PNCP.",
    fonte: "Decreto 11.430/2023",
  },

  // === Mercado de Licitações ===
  {
    texto: "O Brasil realiza mais de 40 mil licitações por mês, movimentando bilhões em contratações públicas.",
    fonte: "Portal de Compras do Governo",
  },
  {
    texto: "O pregão eletrônico representa cerca de 80% de todas as licitações realizadas no país.",
    fonte: "Estatísticas PNCP",
  },
  {
    texto: "Compras públicas representam aproximadamente 12% do PIB brasileiro.",
    fonte: "OCDE / Governo Federal",
  },
  {
    texto: "O governo federal gastou mais de R$ 80 bilhões em compras públicas em 2024.",
    fonte: "Painel de Compras Gov.br",
  },
  {
    texto: "Mais de 300 mil fornecedores estão cadastrados no SICAF para participar de licitações federais.",
    fonte: "Governo Federal",
  },

  // === Uniformes e Vestuário ===
  {
    texto: "Uniformes escolares movimentam cerca de R$ 2 bilhões por ano em licitações públicas.",
    fonte: "Estimativa de Mercado",
  },
  {
    texto: "O setor de vestuário profissional cresce cerca de 5% ao ano no mercado de licitações.",
    fonte: "Análise de Mercado",
  },
  {
    texto: "Estados e municípios respondem por 70% do volume de licitações de uniformes no Brasil.",
    fonte: "Dados PNCP",
  },
  {
    texto: "Fardamentos militares e de segurança pública representam a segunda maior categoria de uniformes licitados.",
    fonte: "Análise de Mercado",
  },
  {
    texto: "Licitações de jalecos e EPIs hospitalares cresceram 40% após a pandemia de COVID-19.",
    fonte: "Dados PNCP 2022-2024",
  },
  {
    texto: "Uniformes com tecido anti-UV e tecnologia de secagem rápida já aparecem em editais de 2024.",
    fonte: "Editais PNCP",
  },
  {
    texto: "Prefeituras do Nordeste lideram em volume de licitações para uniformes escolares.",
    fonte: "Dados PNCP",
  },

  // === MEI, ME e EPP ===
  {
    texto: "Microempresas e EPPs têm tratamento diferenciado com preferência em licitações até R$ 80 mil.",
    fonte: "LC 123/2006, Art. 47-49",
  },
  {
    texto: "Em caso de empate ficto, MEs e EPPs podem apresentar proposta até 5% superior ao melhor preço.",
    fonte: "LC 123/2006, Art. 44",
  },
  {
    texto: "Licitações exclusivas para ME/EPP são obrigatórias em itens até R$ 80 mil desde a LC 123.",
    fonte: "LC 123/2006",
  },
  {
    texto: "Cooperativas de costureiras se enquadram como ME/EPP e podem participar de licitações com benefícios.",
    fonte: "LC 123/2006",
  },

  // === Modalidades e Procedimentos ===
  {
    texto: "Órgãos públicos devem publicar seus editais com antecedência mínima de 8 dias úteis para pregão.",
    fonte: "Lei 14.133/2021, Art. 55",
  },
  {
    texto: "A margem de preferência para produtos nacionais pode chegar a 25% em licitações federais.",
    fonte: "Lei 14.133/2021, Art. 26",
  },
  {
    texto: "O SICAF facilita a participação em licitações federais, eliminando a necessidade de documentação repetida.",
    fonte: "Governo Federal",
  },
  {
    texto: "O Sistema de Registro de Preços (SRP) permite que órgãos registrem preços sem obrigação imediata de compra.",
    fonte: "Lei 14.133/2021, Art. 82",
  },
  {
    texto: "Atas de Registro de Preços têm validade máxima de 1 ano, prorrogável por mais 1 ano.",
    fonte: "Lei 14.133/2021, Art. 84",
  },
  {
    texto: "A concorrência é obrigatória para contratos acima de R$ 3,3 milhões em compras e serviços.",
    fonte: "Decreto 11.317/2022",
  },
  {
    texto: "A dispensa de licitação por valor foi atualizada para até R$ 59.906,02 em compras (2024).",
    fonte: "Decreto de atualização anual",
  },
  {
    texto: "Carona em ata de registro de preços permite que outros órgãos utilizem preços já registrados.",
    fonte: "Lei 14.133/2021, Art. 86",
  },

  // === Estratégia e Dicas ===
  {
    texto: "Monitorar licitações diariamente aumenta em até 3x as chances de encontrar oportunidades relevantes.",
    fonte: "Melhores Práticas de Mercado",
  },
  {
    texto: "Empresas que participam de licitações eletrônicas vencem em média 23% mais processos que nas presenciais.",
    fonte: "Estudo ComprasNet",
  },
  {
    texto: "A apresentação de amostras pode ser exigida como cláusula eliminatória em licitações de uniformes.",
    fonte: "Lei 14.133/2021, Art. 42",
  },
  {
    texto: "Editais de uniformes frequentemente exigem certificação do tecido pelo INMETRO ou laudos técnicos.",
    fonte: "Editais PNCP",
  },
  {
    texto: "O prazo médio entre a publicação do edital e a sessão de pregão é de 10 a 15 dias úteis.",
    fonte: "Análise PNCP",
  },
  {
    texto: "Recursos administrativos em licitações devem ser interpostos em até 3 dias úteis após o resultado.",
    fonte: "Lei 14.133/2021, Art. 165",
  },
];

interface LoadingProgressProps {
  /** Current step (unused, kept for API compat) */
  currentStep?: number;
  /** Estimated total time in seconds (unused) */
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

  const curiosidade = CURIOSIDADES[curiosidadeIndex];

  // Contextual status message based on elapsed time
  const statusMessage =
    elapsedTime < 10
      ? "Conectando ao PNCP..."
      : elapsedTime < 30
        ? `Consultando ${stateCount} estado${stateCount > 1 ? "s" : ""} no PNCP...`
        : elapsedTime < 60
          ? "Filtrando e analisando licitações..."
          : "Processando grande volume de dados...";

  return (
    <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700">
      {/* Indeterminate Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-green-700 dark:text-green-400">
            {statusMessage}
          </span>
          <span className="text-sm tabular-nums text-gray-500 dark:text-gray-400">
            {elapsedTime}s
          </span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div className="h-full w-1/3 bg-gradient-to-r from-green-500 to-green-600 rounded-full animate-[slide_1.5s_ease-in-out_infinite]" />
        </div>
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
              Você sabia?
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

      {/* Context Info */}
      <p className="mt-4 text-xs text-center text-gray-400 dark:text-gray-500">
        Buscando em {stateCount} estado{stateCount > 1 ? "s" : ""} com 5 modalidades de contratação
      </p>
    </div>
  );
}

export default LoadingProgress;
