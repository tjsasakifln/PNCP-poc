export interface MockBid {
  id: string;
  titulo: string;
  orgao: string;
  valor: number;
  uf: string;
  municipio: string;
  modalidade: string;
  data_publicacao: string;
  data_abertura: string;
  viability_score: number;
  viability_factors: {
    modalidade: { score: number; label: string };
    prazo: { score: number; label: string };
    valor: { score: number; label: string };
    geografia: { score: number; label: string };
  };
}

export const MOCK_BIDS: MockBid[] = [
  {
    id: 'demo-001',
    titulo: 'Contratação de empresa especializada para execução de obras de reforma e ampliação do Terminal Rodoviário Municipal',
    orgao: 'Prefeitura Municipal de Campinas',
    valor: 4_800_000,
    uf: 'SP',
    municipio: 'Campinas',
    modalidade: 'Concorrência',
    data_publicacao: '2026-04-02',
    data_abertura: '2026-04-28',
    viability_score: 87,
    viability_factors: {
      modalidade: { score: 90, label: 'Concorrência — alta aderência ao porte da empresa' },
      prazo: { score: 88, label: '26 dias — prazo confortável para preparação' },
      valor: { score: 85, label: 'R$ 4,8M — dentro da faixa ideal (R$ 1M–R$ 10M)' },
      geografia: { score: 82, label: 'SP capital + interior — logística favorável' },
    },
  },
  {
    id: 'demo-002',
    titulo: 'Pregão Eletrônico para contratação de serviços continuados de manutenção predial e conservação nas unidades da Secretaria de Educação',
    orgao: 'Secretaria de Educação do Estado de São Paulo',
    valor: 2_100_000,
    uf: 'SP',
    municipio: 'São Paulo',
    modalidade: 'Pregão Eletrônico',
    data_publicacao: '2026-04-03',
    data_abertura: '2026-04-22',
    viability_score: 81,
    viability_factors: {
      modalidade: { score: 95, label: 'Pregão Eletrônico — formato mais competitivo' },
      prazo: { score: 75, label: '19 dias — prazo adequado mas exige agilidade' },
      valor: { score: 80, label: 'R$ 2,1M — faixa de valor acessível' },
      geografia: { score: 72, label: 'Grande São Paulo — alta concentração de concorrentes' },
    },
  },
  {
    id: 'demo-003',
    titulo: 'Licitação para obras de construção de ponte sobre o Rio Atibaia com instalação de iluminação LED e sinalização viária',
    orgao: 'Departamento de Estradas de Rodagem — DER/SP',
    valor: 7_900_000,
    uf: 'SP',
    municipio: 'Atibaia',
    modalidade: 'Concorrência',
    data_publicacao: '2026-04-01',
    data_abertura: '2026-04-30',
    viability_score: 75,
    viability_factors: {
      modalidade: { score: 90, label: 'Concorrência — adequado ao porte da obra' },
      prazo: { score: 72, label: '29 dias — razoável para obra de alta complexidade' },
      valor: { score: 68, label: 'R$ 7,9M — valor elevado, requer maior capacidade técnica' },
      geografia: { score: 68, label: 'Interior SP — deslocamento moderado de equipe' },
    },
  },
  {
    id: 'demo-004',
    titulo: 'Pregão Eletrônico para contratação de empresa de engenharia para serviços de inspeção e laudo técnico em pontes e viadutos municipais',
    orgao: 'Prefeitura Municipal de Sorocaba',
    valor: 380_000,
    uf: 'SP',
    municipio: 'Sorocaba',
    modalidade: 'Pregão Eletrônico',
    data_publicacao: '2026-04-04',
    data_abertura: '2026-04-17',
    viability_score: 62,
    viability_factors: {
      modalidade: { score: 95, label: 'Pregão Eletrônico — ampla concorrência esperada' },
      prazo: { score: 65, label: '13 dias — prazo curto, risco de habilitação incompleta' },
      valor: { score: 45, label: 'R$ 380k — margem reduzida para mobilização' },
      geografia: { score: 58, label: 'Sorocaba — 90km de SP capital' },
    },
  },
  {
    id: 'demo-005',
    titulo: 'Contratação de empresa para execução de obra de pavimentação asfáltica em vias urbanas no Distrito Industrial Norte',
    orgao: 'Prefeitura Municipal de Ribeirão Preto',
    valor: 1_450_000,
    uf: 'SP',
    municipio: 'Ribeirão Preto',
    modalidade: 'Tomada de Preços',
    data_publicacao: '2026-04-05',
    data_abertura: '2026-04-25',
    viability_score: 55,
    viability_factors: {
      modalidade: { score: 70, label: 'Tomada de Preços — habilitação prévia obrigatória' },
      prazo: { score: 60, label: '20 dias — prazo justo para documentação' },
      valor: { score: 55, label: 'R$ 1,45M — valor adequado mas competição intensa' },
      geografia: { score: 38, label: 'Ribeirão Preto — 310km, custo de mobilização elevado' },
    },
  },
  {
    id: 'demo-006',
    titulo: 'Dispensa de Licitação para serviços emergenciais de recuperação estrutural em escola municipal — laudo de risco emitido',
    orgao: 'Prefeitura Municipal de Osasco',
    valor: 180_000,
    uf: 'SP',
    municipio: 'Osasco',
    modalidade: 'Dispensa',
    data_publicacao: '2026-04-05',
    data_abertura: '2026-04-10',
    viability_score: 31,
    viability_factors: {
      modalidade: { score: 20, label: 'Dispensa — execução imediata exigida, sem proposta competitiva' },
      prazo: { score: 25, label: '5 dias — prazo insuficiente para mobilização' },
      valor: { score: 40, label: 'R$ 180k — ticket baixo, custo-benefício marginal' },
      geografia: { score: 62, label: 'Osasco — Grande SP, acesso rápido' },
    },
  },
];

export const DEMO_SECTOR = { id: 'engenharia', name: 'Engenharia e Construção' };
export const DEMO_UF = 'SP';

export function formatBRL(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

export function getViabilityColor(score: number): { bg: string; text: string; ring: string } {
  if (score >= 70) return { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-700 dark:text-emerald-300', ring: 'ring-emerald-200 dark:ring-emerald-700' };
  if (score >= 50) return { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-300', ring: 'ring-amber-200 dark:ring-amber-700' };
  return { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-300', ring: 'ring-red-200 dark:ring-red-700' };
}
