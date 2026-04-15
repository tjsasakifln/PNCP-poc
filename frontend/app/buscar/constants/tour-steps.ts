import type { TourStepDef } from "../../../components/tour/Tour";

// Trial value type matching backend TrialValueResponse
export interface TrialValue {
  total_opportunities: number;
  total_value: number;
  searches_executed: number;
  avg_opportunity_value: number;
  top_opportunity: { title: string; value: number } | null;
}

// STORY-313: Tour step definitions (static, outside component to avoid re-creation)
export const SEARCH_TOUR_STEPS: TourStepDef[] = [
  {
    id: 'search-setor',
    title: 'Escolha seu setor',
    text: 'Escolha o setor da sua empresa para filtrar oportunidades relevantes.',
    attachTo: { selector: '[data-tour="setor-filter"]', placement: 'bottom' },
  },
  {
    id: 'search-ufs',
    title: 'Selecione os estados',
    text: 'Selecione os estados onde sua empresa atua ou quer atuar.',
    attachTo: { selector: '[data-tour="uf-selector"]', placement: 'bottom' },
    beforeShow: () => new Promise<void>((resolve) => {
      const btn = document.querySelector('[data-tour="customize-toggle"]') as HTMLElement;
      if (btn?.getAttribute('aria-expanded') === 'false') {
        btn.click();
        setTimeout(resolve, 400);
      } else {
        resolve();
      }
    }),
  },
  {
    id: 'search-period',
    title: 'Defina o período',
    text: 'Defina o período para buscar editais recentes.',
    attachTo: { selector: '[data-tour="period-selector"]', placement: 'bottom' },
  },
  {
    id: 'search-button',
    title: 'Inicie sua busca!',
    text: 'Clique para iniciar sua busca inteligente!',
    attachTo: { selector: '[data-tour="search-button"]', placement: 'top' },
  },
];

// STORY-442: Guided tour for /buscar — 5-step post-onboarding tour (AC2)
// localStorage key: smartlic_buscar_tour_completed
export const GUIDED_TOUR_STEPS: TourStepDef[] = [
  {
    id: 'guided-busca',
    title: 'Busca inteligente',
    text: 'Escolha seu setor e os estados onde sua empresa atua para encontrar as melhores oportunidades.',
    attachTo: { selector: '[data-tour="setor-filter"]', placement: 'bottom' },
  },
  {
    id: 'guided-viability',
    title: 'Score de viabilidade',
    text: 'Cada oportunidade recebe um score de viabilidade com base em modalidade, prazo, valor e geografia.',
    attachTo: { selector: '[data-tour="viability-badge"]', placement: 'bottom' },
    showOn: () => !!document.querySelector('[data-tour="viability-badge"]'),
  },
  {
    id: 'guided-ia-summary',
    title: 'Resumo com IA',
    text: 'A IA resume o objeto da licitação e destaca os pontos mais relevantes para sua empresa.',
    attachTo: { selector: '[data-tour="result-card"]', placement: 'bottom' },
    showOn: () => !!document.querySelector('[data-tour="result-card"]'),
  },
  {
    id: 'guided-pipeline',
    title: 'Pipeline de oportunidades',
    text: 'Salve oportunidades promissoras no pipeline para acompanhá-las no kanban e não perder prazos.',
    attachTo: { selector: '[data-tour="pipeline-button"]', placement: 'bottom' },
    showOn: () => !!document.querySelector('[data-tour="pipeline-button"]'),
  },
  {
    id: 'guided-export',
    title: 'Exportar para Excel',
    text: 'Exporte todas as oportunidades encontradas para Excel e compartilhe com sua equipe.',
    attachTo: { selector: '[data-tour="excel-button"]', placement: 'top' },
    showOn: () => !!document.querySelector('[data-tour="excel-button"]'),
  },
];

export const RESULTS_TOUR_STEPS: TourStepDef[] = [
  {
    id: 'results-card',
    title: 'Suas oportunidades',
    text: 'Cada card mostra uma oportunidade com data, valor e órgão.',
    attachTo: { selector: '[data-tour="result-card"]', placement: 'bottom' },
  },
  {
    id: 'results-viability',
    title: 'Score de viabilidade',
    text: 'O score de viabilidade indica o potencial desta oportunidade para sua empresa.',
    attachTo: { selector: '[data-tour="viability-badge"]', placement: 'bottom' },
  },
  {
    id: 'results-pipeline',
    title: 'Pipeline de oportunidades',
    text: 'Clique em "Pipeline" para salvar oportunidades promissoras e acompanhá-las no kanban.',
    attachTo: { selector: '[data-tour="pipeline-button"]', placement: 'bottom' },
  },
  {
    id: 'results-excel',
    title: 'Exporte para Excel',
    text: 'Exporte resultados para Excel para análise detalhada.',
    attachTo: { selector: '[data-tour="excel-button"]', placement: 'top' },
  },
];
