import type { TourStep } from "../../../hooks/useShepherdTour";

// Trial value type matching backend TrialValueResponse
export interface TrialValue {
  total_opportunities: number;
  total_value: number;
  searches_executed: number;
  avg_opportunity_value: number;
  top_opportunity: { title: string; value: number } | null;
}

// STORY-313: Tour step definitions (static, outside component to avoid re-creation)
export const SEARCH_TOUR_STEPS: TourStep[] = [
  {
    id: 'search-setor',
    title: 'Escolha seu setor',
    text: '<span class="tour-step-counter">Passo 1 de 4</span><p>Escolha o setor da sua empresa para filtrar oportunidades relevantes.</p>',
    attachTo: { element: '[data-tour="setor-filter"]', on: 'bottom' },
  },
  {
    id: 'search-ufs',
    title: 'Selecione os estados',
    text: '<span class="tour-step-counter">Passo 2 de 4</span><p>Selecione os estados onde sua empresa atua ou quer atuar.</p>',
    attachTo: { element: '[data-tour="uf-selector"]', on: 'bottom' },
    beforeShowPromise: () => new Promise<void>((resolve) => {
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
    text: '<span class="tour-step-counter">Passo 3 de 4</span><p>Defina o período para buscar editais recentes.</p>',
    attachTo: { element: '[data-tour="period-selector"]', on: 'bottom' },
  },
  {
    id: 'search-button',
    title: 'Inicie sua busca!',
    text: '<span class="tour-step-counter">Passo 4 de 4</span><p>Clique para iniciar sua busca inteligente!</p>',
    attachTo: { element: '[data-tour="search-button"]', on: 'top' },
  },
];

export const RESULTS_TOUR_STEPS: TourStep[] = [
  {
    id: 'results-card',
    title: 'Suas oportunidades',
    text: '<span class="tour-step-counter">Passo 1 de 4</span><p>Cada card mostra uma oportunidade com data, valor e órgão.</p>',
    attachTo: { element: '[data-tour="result-card"]', on: 'bottom' },
  },
  {
    id: 'results-viability',
    title: 'Score de viabilidade',
    text: '<span class="tour-step-counter">Passo 2 de 4</span><p>O score de viabilidade indica o potencial desta oportunidade para sua empresa.</p>',
    attachTo: { element: '[data-tour="viability-badge"]', on: 'bottom' },
  },
  {
    id: 'results-pipeline',
    title: 'Pipeline de oportunidades',
    text: '<span class="tour-step-counter">Passo 3 de 4</span><p>Clique em "Pipeline" para salvar oportunidades promissoras e acompanhá-las no kanban.</p>',
    attachTo: { element: '[data-tour="pipeline-button"]', on: 'bottom' },
  },
  {
    id: 'results-excel',
    title: 'Exporte para Excel',
    text: '<span class="tour-step-counter">Passo 4 de 4</span><p>Exporte resultados para Excel para análise detalhada.</p>',
    attachTo: { element: '[data-tour="excel-button"]', on: 'top' },
  },
];
