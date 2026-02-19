/**
 * SmartLic vs. Traditional Platforms - Competitive Comparison Data
 *
 * GTM-001: Rewritten for decision intelligence positioning
 * GTM-007: PNCP sanitization — Zero user-visible PNCP mentions
 *
 * @date 2026-02-15
 */

import {
  Search,
  Target,
  Globe,
  Bot,
  CircleDollarSign,
  CheckCircle2,
  LifeBuoy,
  Sparkles,
  ShieldCheck,
  TrendingUp,
} from '@/lib/icons';

// ============================================================================
// COMPARISON TABLE DATA
// ============================================================================

export interface ComparisonRow {
  feature: string;
  traditional: string;
  smartlic: string;
  advantage: string;
  icon?: React.ComponentType<any>;
}

export const comparisonTable: ComparisonRow[] = [
  {
    feature: "Tipo de Busca",
    traditional: "Por termos específicos (precisa adivinhar)",
    smartlic: "Por setor de atuação (1 clique)",
    advantage: "Cobertura completa do mercado",
    icon: Search,
  },
  {
    feature: "Inteligência",
    traditional: "Lista de resultados sem avaliação",
    smartlic: "Avaliação objetiva de cada oportunidade",
    advantage: "Decisão informada",
    icon: Bot,
  },
  {
    feature: "Priorização",
    traditional: "Você filtra manualmente",
    smartlic: "IA prioriza por adequação ao seu perfil",
    advantage: "Foco no que gera resultado",
    icon: Target,
  },
  {
    feature: "Fontes Consultadas",
    traditional: "Fonte única ou busca manual em múltiplos portais",
    smartlic: "Fontes oficiais consolidadas automaticamente com cobertura nacional",
    advantage: "Visibilidade completa",
    icon: Globe,
  },
  {
    feature: "Vantagem Competitiva",
    traditional: "Sem diferencial (mesma informação que todos)",
    smartlic: "Posicione-se antes da concorrência",
    advantage: "Quem vê primeiro, vence mais",
    icon: TrendingUp,
  },
  {
    feature: "Preço",
    traditional: "Taxas ocultas ou cobranças por consulta",
    smartlic: "Investimento fixo mensal (tudo incluso)",
    advantage: "Transparente",
    icon: CircleDollarSign,
  },
  {
    feature: "Cancelamento",
    traditional: "Burocrático (ligações, retenção)",
    smartlic: "1 clique (sem burocracia)",
    advantage: "Confiança total",
    icon: CheckCircle2,
  },
  {
    feature: "Suporte",
    traditional: "Lento (dias para responder)",
    smartlic: "Resposta em até 24 horas úteis",
    advantage: "Problemas resolvidos rapidamente",
    icon: LifeBuoy,
  },
  {
    feature: "Interface",
    traditional: "Confusa (curva de aprendizado longa)",
    smartlic: "Intuitiva (produtivo desde o primeiro uso)",
    advantage: "Produtividade imediata",
    icon: Sparkles,
  },
  {
    feature: "Confiabilidade",
    traditional: "Sistemas lentos ou instáveis",
    smartlic: "Infraestrutura moderna, disponível quando você precisa",
    advantage: "Confiável 24/7",
    icon: ShieldCheck,
  },
];

// ============================================================================
// DEFENSIVE MESSAGING TEMPLATES
// ============================================================================

export interface DefensiveMessage {
  painPoint: string;
  traditionalProblem: string;
  smartlicSolution: string;
  quantifiedBenefit: string;
}

export const defensiveMessaging: Record<string, DefensiveMessage> = {
  cost: {
    painPoint: "Custo alto + cobranças ocultas",
    traditionalProblem:
      "Outras plataformas cobram por consulta ou têm taxas ocultas que inflam o custo real",
    smartlicSolution:
      "No SmartLic, investimento fixo mensal com tudo incluso. Sem surpresas",
    quantifiedBenefit: "Uma licitação ganha paga o investimento do ano inteiro",
  },

  cancellation: {
    painPoint: "Cancelamento difícil + renovação forçada",
    traditionalProblem:
      "Outras plataformas dificultam o cancelamento com burocracia e ligações",
    smartlicSolution: "No SmartLic, cancele em 1 clique, sem perguntas",
    quantifiedBenefit:
      "Liberdade total. Acreditamos que você vai querer ficar pela qualidade",
  },

  visibility: {
    painPoint: "Falta de visibilidade do mercado",
    traditionalProblem:
      "Sem visibilidade completa, você perde oportunidades para concorrentes que encontram antes",
    smartlicSolution: "No SmartLic, visibilidade total com fontes oficiais consolidadas automaticamente",
    quantifiedBenefit:
      "Cada licitação perdida por falta de visibilidade pode custar R$ 50.000 ou mais",
  },

  searchMethod: {
    painPoint: "Busca por termos específicos (adivinhação)",
    traditionalProblem:
      "Outras plataformas exigem que você adivinhe dezenas de palavras-chave",
    smartlicSolution:
      "No SmartLic, selecione seu setor e receba oportunidades do seu mercado",
    quantifiedBenefit:
      "Cobertura completa do seu mercado sem adivinhação de termos",
  },

  decision: {
    painPoint: "Falta de inteligência para decidir",
    traditionalProblem:
      "Outras plataformas entregam listas sem avaliação — você precisa analisar tudo manualmente",
    smartlicSolution:
      "No SmartLic, IA avalia cada oportunidade e indica se vale a pena investir",
    quantifiedBenefit:
      "Decisões baseadas em critérios objetivos, não em intuição",
  },

  sources: {
    painPoint: "Fonte única ou busca manual em múltiplos portais",
    traditionalProblem:
      "Outras plataformas consultam uma única fonte ou exigem busca manual em dezenas de portais",
    smartlicSolution:
      "No SmartLic, consolidamos fontes oficiais automaticamente com cobertura nacional",
    quantifiedBenefit:
      "Nunca perca uma oportunidade. Visibilidade completa do mercado",
  },

  ai: {
    painPoint: "Sem inteligência artificial (análise manual)",
    traditionalProblem:
      "Outras plataformas exigem análise manual de cada oportunidade",
    smartlicSolution:
      "No SmartLic, IA avalia cada oportunidade: vale a pena ou não, e por quê",
    quantifiedBenefit:
      "Avaliação objetiva. Invista seu tempo onde o retorno é maior",
  },

  support: {
    painPoint: "Suporte lento e ineficiente",
    traditionalProblem:
      "Outras plataformas demoram dias para responder",
    smartlicSolution: "No SmartLic, suporte com resposta em até 24 horas úteis",
    quantifiedBenefit:
      "Problemas resolvidos rapidamente. Seu tempo vale ouro",
  },

  interface: {
    painPoint: "Interface confusa (curva de aprendizado)",
    traditionalProblem:
      "Outras plataformas têm interfaces complexas que exigem treinamento",
    smartlicSolution:
      "No SmartLic, interface intuitiva — produtivo desde o primeiro uso",
    quantifiedBenefit:
      "Descubra oportunidades logo na primeira sessão",
  },

  stability: {
    painPoint: "Sistemas lentos e instáveis",
    traditionalProblem:
      "Outras plataformas sofrem com lentidão e instabilidade frequente",
    smartlicSolution:
      "No SmartLic, infraestrutura moderna com alta disponibilidade",
    quantifiedBenefit:
      "Sempre disponível quando você precisa tomar decisões",
  },
};

// ============================================================================
// PAIN POINTS SUMMARY (10 Market Pain Points — Decision Intelligence Focus)
// ============================================================================

export interface PainPoint {
  id: number;
  title: string;
  userComplaint: string;
  impact: string;
  smartlicDifferentiator: string;
  metric?: string;
}

export const painPoints: PainPoint[] = [
  {
    id: 1,
    title: "Falta de Visibilidade do Mercado",
    userComplaint: "Não sei quantas oportunidades existem para o meu setor",
    impact: "Empresas perdem contratos para concorrentes com mais informação",
    smartlicDifferentiator:
      "Visibilidade completa: fontes oficiais monitoradas com cobertura nacional",
    metric: "27 estados cobertos",
  },
  {
    id: 2,
    title: "Decisões Baseadas em Intuição",
    userComplaint: "Não sei se vale a pena investir tempo nesta licitação",
    impact: "Empresas investem em oportunidades erradas e perdem as certas",
    smartlicDifferentiator:
      "Avaliação objetiva por IA: vale a pena ou não, e por quê",
    metric: "Critérios objetivos",
  },
  {
    id: 3,
    title: "Concorrência Posiciona Antes",
    userComplaint: "Quando encontro a licitação, o prazo já está curto",
    impact: "Propostas apressadas com menor chance de vitória",
    smartlicDifferentiator: "Oportunidades identificadas assim que publicadas",
    metric: "Análises sob demanda",
  },
  {
    id: 4,
    title: "Custo Alto + Cobranças Ocultas",
    userComplaint: "Mensalidades baixas mas cobram extras por tudo",
    impact: "Empresas não conseguem prever custo total",
    smartlicDifferentiator:
      "Investimento fixo mensal, tudo incluso, sem surpresas",
  },
  {
    id: 5,
    title: "Renovação Automática e Cancelamento Difícil",
    userComplaint: "Pedidos de cancelamento repetidamente adiados",
    impact: "Usuários se sentem presos, perdem confiança",
    smartlicDifferentiator:
      "Cancelamento em 1 clique (sem burocracia, sem ligações)",
  },
  {
    id: 6,
    title: "Busca por Termos (Adivinhação)",
    userComplaint: "Preciso adivinhar palavras-chave para encontrar oportunidades",
    impact: "Empresas perdem oportunidades por não saber os termos certos",
    smartlicDifferentiator:
      "Busca por setor de atuação com cobertura automática de termos",
    metric: "15 setores especializados",
  },
  {
    id: 7,
    title: "Busca Manual em Múltiplos Portais",
    userComplaint: "Preciso acessar dezenas de sites diferentes",
    impact: "Empresas perdem oportunidades por não conseguir monitorar tudo",
    smartlicDifferentiator:
      "Consolidação automática de fontes oficiais com cobertura nacional",
    metric: "Cobertura nacional",
  },
  {
    id: 8,
    title: "Interface Confusa e Pouco Intuitiva",
    userComplaint: "Não sei onde encontrar as melhores oportunidades",
    impact: "Curva de aprendizado longa, frustração",
    smartlicDifferentiator: "Interface intuitiva, produtivo desde o primeiro uso",
  },
  {
    id: 9,
    title: "Sem Inteligência Artificial",
    userComplaint: "Preciso analisar cada oportunidade manualmente",
    impact: "Gestores gastam tempo em análise manual de documentos extensos",
    smartlicDifferentiator:
      "IA avalia oportunidades e entrega análise objetiva",
  },
  {
    id: 10,
    title: "Atendimento Lento",
    userComplaint: "Demora dias para receber suporte",
    impact: "Problemas não resolvidos a tempo",
    smartlicDifferentiator: "Suporte com resposta em até 24 horas úteis",
  },
];

// ============================================================================
// PROOF POINTS (Data to Back Claims — Decision Intelligence)
// ============================================================================

export interface ProofPoint {
  claim: string;
  proofSource: string;
  disclaimerIfNeeded?: string;
}

export const proofPoints: Record<string, ProofPoint> = {
  coverage: {
    claim: "Fontes oficiais consolidadas com cobertura em todos os 27 estados",
    proofSource: "Technical architecture — multi-source integration",
  },

  sectors: {
    claim: "15 setores especializados com cobertura completa de termos",
    proofSource: "System capability — sector-specific keyword databases",
  },

  opportunities: {
    claim: "Cobertura completa de licitações federais e estaduais em 27 UFs",
    proofSource: "Platform capability — multi-source official integration",
  },

  monitoring: {
    claim: "Análises sob demanda de todas as fontes oficiais",
    proofSource: "System uptime and crawl frequency metrics",
  },

  supportSLA: {
    claim: "Suporte com resposta em até 24 horas úteis",
    proofSource: "Customer support policy SLA commitment",
  },

  nationalCoverage: {
    claim: "27 UFs cobertas com fontes federais, estaduais e municipais",
    proofSource: "System capability (IBGE data + multi-source integration)",
  },
};

// ============================================================================
// BEFORE/AFTER COMPARISON (Visual Contrast — Decision Focus)
// ============================================================================

export interface BeforeAfterItem {
  aspect: string;
  before: string;
  after: string;
  icon: React.ComponentType<any>;
}

export const beforeAfter: BeforeAfterItem[] = [
  {
    aspect: "Visibilidade de Mercado",
    before: "Visão parcial — perda de oportunidades por falta de cobertura",
    after: "Visão completa — fontes oficiais monitoradas com cobertura nacional",
    icon: Globe,
  },
  {
    aspect: "Tomada de Decisão",
    before: "Decisões por intuição — sem dados para avaliar oportunidades",
    after: "Avaliação objetiva por IA — vale a pena ou não, e por quê",
    icon: Bot,
  },
  {
    aspect: "Posicionamento Competitivo",
    before: "Chega tarde — concorrentes encontram e se posicionam antes",
    after: "Posicione-se primeiro — oportunidades assim que publicadas",
    icon: TrendingUp,
  },
  {
    aspect: "Priorização",
    before: "Análise manual de cada oportunidade — tempo investido em tudo",
    after: "Priorização inteligente — foco no que se adequa ao seu perfil",
    icon: Target,
  },
  {
    aspect: "Custo",
    before: "Taxas ocultas e cobranças imprevisíveis",
    after: "Investimento fixo mensal, tudo incluso",
    icon: CircleDollarSign,
  },
  {
    aspect: "Cancelamento",
    before: "Burocrático (ligações, retenção)",
    after: "1 clique (sem retenção)",
    icon: CheckCircle2,
  },
];

// ============================================================================
// COMPETITIVE ADVANTAGE SCORING (Internal Use — Decision Intelligence)
// ============================================================================

export interface AdvantageScore {
  advantage: string;
  strength: number;
  defensibility: number;
  userImpact: number;
  totalScore: number;
  priority: "high" | "medium" | "low";
}

export const advantageScores: AdvantageScore[] = [
  {
    advantage: "Decision Intelligence (AI Evaluation)",
    strength: 10,
    defensibility: 9,
    userImpact: 10,
    totalScore: 29,
    priority: "high",
  },
  {
    advantage: "Market Visibility (Multi-Source)",
    strength: 9,
    defensibility: 8,
    userImpact: 10,
    totalScore: 27,
    priority: "high",
  },
  {
    advantage: "Competitive Positioning (Speed to Market)",
    strength: 9,
    defensibility: 7,
    userImpact: 9,
    totalScore: 25,
    priority: "high",
  },
  {
    advantage: "Intelligent Prioritization",
    strength: 9,
    defensibility: 8,
    userImpact: 8,
    totalScore: 25,
    priority: "high",
  },
  {
    advantage: "Sector Specialization (12 sectors)",
    strength: 8,
    defensibility: 7,
    userImpact: 8,
    totalScore: 23,
    priority: "medium",
  },
  {
    advantage: "Transparent Pricing",
    strength: 7,
    defensibility: 5,
    userImpact: 7,
    totalScore: 19,
    priority: "medium",
  },
  {
    advantage: "1-Click Cancel",
    strength: 6,
    defensibility: 4,
    userImpact: 7,
    totalScore: 17,
    priority: "low",
  },
  {
    advantage: "Intuitive UX",
    strength: 8,
    defensibility: 5,
    userImpact: 8,
    totalScore: 21,
    priority: "medium",
  },
];

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get defensive message by pain point key
 */
export function getDefensiveMessage(key: keyof typeof defensiveMessaging) {
  return defensiveMessaging[key];
}

/**
 * Format defensive message as template
 */
export function formatDefensiveMessage(key: keyof typeof defensiveMessaging): string {
  const msg = defensiveMessaging[key];
  return `${msg.traditionalProblem}. ${msg.smartlicSolution}. ${msg.quantifiedBenefit}.`;
}

/**
 * Get pain point by ID
 */
export function getPainPoint(id: number): PainPoint | undefined {
  return painPoints.find((p) => p.id === id);
}

/**
 * Get top N advantages by total score
 */
export function getTopAdvantages(n: number = 3): AdvantageScore[] {
  return [...advantageScores].sort((a, b) => b.totalScore - a.totalScore).slice(0, n);
}

/**
 * Get comparison row by feature name
 */
export function getComparisonRow(feature: string): ComparisonRow | undefined {
  return comparisonTable.find((row) => row.feature === feature);
}

// ============================================================================
// EXPORT ALL
// ============================================================================

export default {
  comparisonTable,
  defensiveMessaging,
  painPoints,
  proofPoints,
  beforeAfter,
  advantageScores,
  // Utility functions
  getDefensiveMessage,
  formatDefensiveMessage,
  getPainPoint,
  getTopAdvantages,
  getComparisonRow,
};
