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

  const statusMessage =
    elapsedTime < 10
      ? "Conectando ao PNCP..."
      : elapsedTime < 30
        ? `Consultando ${stateCount} estado${stateCount > 1 ? "s" : ""} no PNCP...`
        : elapsedTime < 60
          ? "Filtrando e analisando licitações..."
          : "Processando grande volume de dados...";

  return (
    <div className="mt-8 p-6 bg-surface-1 rounded-card border animate-fade-in-up">
      {/* Indeterminate Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-brand-blue">
            {statusMessage}
          </span>
          <span className="text-sm tabular-nums font-data text-ink-muted">
            {elapsedTime}s
          </span>
        </div>
        <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
          <div className="h-full w-1/3 bg-gradient-to-r from-brand-blue to-brand-navy rounded-full animate-[slide_1.5s_ease-in-out_infinite]" />
        </div>
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
