// Shared types for onboarding components

export interface OnboardingData {
  cnae: string;
  objetivo_principal: string;
  ufs_atuacao: string[];
  faixa_valor_min: number;
  faixa_valor_max: number;
  // Keep legacy fields for backward compat with PerfilContexto
  porte_empresa: string;
  experiencia_licitacoes: string;
}

// CNAE suggestions for autocomplete (AC7)
export const CNAE_SUGGESTIONS = [
  { code: "4781-4/00", label: "Comércio varejista de artigos de vestuário e acessórios" },
  { code: "1412-6/01", label: "Confecção de peças de vestuário profissional" },
  { code: "8121-4/00", label: "Limpeza em prédios e em domicílios" },
  { code: "8011-1/01", label: "Atividades de vigilância e segurança privada" },
  { code: "2710-4/01", label: "Fabricação de equipamentos elétricos" },
  { code: "3250-7/01", label: "Fabricação de instrumentos e materiais para uso médico" },
  { code: "1011-2/01", label: "Abate de reses" },
  { code: "1091-1/01", label: "Fabricação de produtos de panificação" },
  { code: "6201-5/01", label: "Desenvolvimento de software sob encomenda" },
  { code: "6202-3/00", label: "Desenvolvimento e licenciamento de software" },
] as const;

// Value presets in BRL
export const VALUE_PRESETS = [
  { value: 50_000, label: "R$ 50 mil" },
  { value: 100_000, label: "R$ 100 mil" },
  { value: 250_000, label: "R$ 250 mil" },
  { value: 500_000, label: "R$ 500 mil" },
  { value: 1_000_000, label: "R$ 1 milhão" },
  { value: 2_000_000, label: "R$ 2 milhões" },
  { value: 5_000_000, label: "R$ 5 milhões" },
];

export const REGIONS: Record<string, string[]> = {
  Norte: ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
  Nordeste: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  "Centro-Oeste": ["DF", "GO", "MS", "MT"],
  Sudeste: ["ES", "MG", "RJ", "SP"],
  Sul: ["PR", "RS", "SC"],
};
