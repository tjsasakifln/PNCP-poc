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
  tooltip?: string;
  icon?: React.ComponentType<Record<string, unknown>>;
}

// GTM-COPY-001 AC9: Risk-oriented comparison — "Outros" = risk, "SmartLic" = concrete result
export const comparisonTable: ComparisonRow[] = [
  {
    feature: "Seleção de editais",
    traditional: "Você adivinha palavras-chave e torce para acertar",
    smartlic: "O sistema cruza seu perfil com cada edital e entrega só o que é compatível",
    advantage: "Elimina a maioria do ruído",
    icon: Search,
  },
  {
    feature: "Avaliação",
    traditional: "Você lê dezenas de páginas para descobrir se vale a pena",
    smartlic: "Cada edital vem com avaliação objetiva: vale a pena ou não, e por quê",
    advantage: "Decisão em segundos",
    icon: Bot,
  },
  {
    feature: "Priorização",
    traditional: "Risco de investir proposta em editais com baixa chance de retorno",
    smartlic: "Priorização por compatibilidade: setor, valor, prazo e região",
    advantage: "Foco onde o retorno é maior",
    icon: Target,
  },
  {
    feature: "Cobertura",
    traditional: "Risco de perder oportunidades em portais que você não monitora",
    smartlic: "27 UFs cobertas automaticamente com consolidação de fontes oficiais",
    advantage: "Nenhum edital invisível",
    icon: Globe,
  },
  {
    feature: "Timing",
    traditional: "Risco de descobrir tarde e perder prazo de proposta",
    smartlic: "Editais disponíveis assim que publicados nas fontes oficiais",
    advantage: "Você se posiciona primeiro",
    icon: TrendingUp,
  },
  {
    feature: "Custo",
    traditional: "Taxas ocultas inflam o custo real do serviço",
    smartlic: "Investimento fixo mensal, tudo incluso, sem surpresas",
    advantage: "Previsibilidade total",
    icon: CircleDollarSign,
  },
  {
    feature: "Cancelamento",
    traditional: "Risco de ficar preso em contratos com burocracia para sair",
    smartlic: "1 clique para cancelar, sem ligação, sem retenção",
    advantage: "Liberdade total",
    icon: CheckCircle2,
  },
  {
    feature: "Suporte",
    traditional: "Dias para conseguir resposta quando algo trava",
    smartlic: "Resposta em até 24 horas úteis",
    advantage: "Problema resolvido rápido",
    icon: LifeBuoy,
  },
  {
    feature: "Interface",
    traditional: "Curva de aprendizado longa antes de conseguir usar",
    smartlic: "Produtivo desde a primeira sessão",
    advantage: "Sem treinamento",
    icon: Sparkles,
  },
  {
    feature: "Confiabilidade",
    traditional: "Risco de sistema fora do ar quando você precisa decidir",
    smartlic: "Infraestrutura moderna, disponível quando você precisa",
    advantage: "Disponível 24/7",
    tooltip: "Monitoramento contínuo com alertas automáticos",
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
    claim: "3 fontes oficiais federais + portal de compras públicas com cobertura em todos os 27 estados",
    proofSource: "Technical architecture — multi-source integration (PNCP + PCP v2 + ComprasGov v3)",
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
  icon: React.ComponentType<Record<string, unknown>>;
}

// GTM-COPY-001 AC6: Concrete consequences, not features
export const beforeAfter: BeforeAfterItem[] = [
  {
    aspect: "Editais",
    before: "Você analisa dezenas de editais irrelevantes por semana",
    after: "A maioria descartados automaticamente — sobra só o que é compatível com seu perfil",
    icon: Target,
  },
  {
    aspect: "Decisão",
    before: "Lê 100 páginas de edital para descobrir que não se encaixa",
    after: "Avaliação objetiva em segundos: vale a pena ou não, e por quê",
    icon: Bot,
  },
  {
    aspect: "Oportunidades",
    before: "Perde contratos porque não sabia que existiam",
    after: "Cobertura nacional automática — 27 UFs, fontes oficiais consolidadas",
    icon: Globe,
  },
  {
    aspect: "Concorrência",
    before: "Descobre editais quando o prazo já está curto",
    after: "Acesso assim que publicados — você se posiciona antes",
    icon: TrendingUp,
  },
  {
    aspect: "Custo",
    before: "Taxas ocultas inflam o custo real",
    after: "Investimento fixo mensal, tudo incluso",
    icon: CircleDollarSign,
  },
  {
    aspect: "Cancelamento",
    before: "Burocracia para sair — ligações, retenção",
    after: "1 clique, sem perguntas",
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
