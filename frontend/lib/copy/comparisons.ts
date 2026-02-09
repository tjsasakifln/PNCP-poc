/**
 * SmartLic vs. Traditional Platforms - Competitive Comparison Data
 *
 * Structured data for comparison tables and defensive positioning messaging
 * Based on validated market pain points (STORY-173)
 *
 * @agent @ux-design-expert (Uma)
 * @date 2026-02-08
 * @updated 2026-02-09 - Migrated from Unicode emojis to Lucide icons (@dev Felix)
 */

import {
  Search,
  Zap,
  Target,
  Globe,
  Bot,
  CircleDollarSign,
  CheckCircle2,
  LifeBuoy,
  Sparkles,
  ShieldCheck,
} from '@/lib/icons';

// ============================================================================
// COMPARISON TABLE DATA
// ============================================================================

export interface ComparisonRow {
  feature: string;
  traditional: string;
  smartlic: string;
  advantage: string;
  icon?: React.ComponentType<any>; // Lucide icon component
}

export const comparisonTable: ComparisonRow[] = [
  {
    feature: "Tipo de Busca",
    traditional: "Por termos específicos (precisa adivinhar)",
    smartlic: "Por ramo de atividade (1 clique)",
    advantage: "10x mais fácil",
    icon: Search,
  },
  {
    feature: "Tempo Médio",
    traditional: "8+ horas (busca manual)",
    smartlic: "3 minutos (160x mais rápido)",
    advantage: "160x mais rápido",
    icon: Zap,
  },
  {
    feature: "Precisão",
    traditional: "~20% (muito ruído)",
    smartlic: "95% (filtros inteligentes)",
    advantage: "5x mais preciso",
    icon: Target,
  },
  {
    feature: "Fontes Consultadas",
    traditional: "Apenas PNCP",
    smartlic: "PNCP + 27 portais estaduais/municipais",
    advantage: "27x mais cobertura",
    icon: Globe,
  },
  {
    feature: "Resumos IA",
    traditional: "Não (leitura manual)",
    smartlic: "Sim (resumos executivos de 3 linhas)",
    advantage: "Insights instantâneos",
    icon: Bot,
  },
  {
    feature: "Preço",
    traditional: "Taxas ocultas ou por consulta",
    smartlic: "Fixo mensal (50-1000 buscas/mês conforme plano)",
    advantage: "Transparente",
    icon: CircleDollarSign,
  },
  {
    feature: "Cancelamento",
    traditional: "Difícil (burocrático)",
    smartlic: "1 clique (sem burocracia)",
    advantage: "Trust-first",
    icon: CheckCircle2,
  },
  {
    feature: "Suporte",
    traditional: "2-7 dias (resposta lenta)",
    smartlic: "4 horas (resposta garantida)",
    advantage: "40x mais rápido",
    icon: LifeBuoy,
  },
  {
    feature: "Interface",
    traditional: "Confusa (curva de aprendizado)",
    smartlic: "Intuitiva (onboarding de 30 seg)",
    advantage: "Produtividade imediata",
    icon: Sparkles,
  },
  {
    feature: "Estabilidade",
    traditional: "Sistemas lentos ou instáveis",
    smartlic: "99.9% uptime (infraestrutura moderna)",
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
      "Outras plataformas cobram por consulta ou têm taxas ocultas",
    smartlicSolution:
      "No SmartLic, você paga um valor fixo mensal para cota de buscas (50-1000 conforme plano)",
    quantifiedBenefit: "Orçamento previsível, sem surpresas",
  },

  cancellation: {
    painPoint: "Cancelamento difícil + renovação forçada",
    traditionalProblem:
      "Outras plataformas dificultam o cancelamento com burocracia e ligações",
    smartlicSolution: "No SmartLic, você cancela em 1 clique, sem perguntas",
    quantifiedBenefit:
      "Liberdade total. Acreditamos que você vai querer ficar pela qualidade",
  },

  speed: {
    painPoint: "Buscas manuais lentas (8+ horas)",
    traditionalProblem:
      "Buscas manuais em portais governamentais levam 8+ horas por semana",
    smartlicSolution: "No SmartLic, você tem o resultado em 3 minutos",
    quantifiedBenefit:
      "Economize 10 horas por semana para preparar propostas vencedoras",
  },

  searchMethod: {
    painPoint: "Busca por termos específicos (adivinhação)",
    traditionalProblem:
      "Outras plataformas exigem que você adivinhe dezenas de palavras-chave",
    smartlicSolution:
      "No SmartLic, você seleciona seu setor e nosso algoritmo encontra tudo",
    quantifiedBenefit:
      "1 clique vs. 20+ buscas. Cobertura completa sem guesswork",
  },

  precision: {
    painPoint: "Muito ruído (20% precisão)",
    traditionalProblem:
      "Outras plataformas entregam milhares de resultados irrelevantes",
    smartlicSolution:
      "No SmartLic, 95% de precisão significa que você analisa apenas o que realmente importa",
    quantifiedBenefit:
      "Economize horas de filtragem manual. Apenas o ouro, zero ruído",
  },

  sources: {
    painPoint: "Fonte única (apenas PNCP)",
    traditionalProblem:
      "Outras plataformas consultam apenas o PNCP ou exigem que você busque em dezenas de portais separadamente",
    smartlicSolution:
      "No SmartLic, consolidamos PNCP + 27 portais estaduais e municipais em uma única busca automática",
    quantifiedBenefit:
      "Nunca perca uma oportunidade. Cobertura nacional completa",
  },

  ai: {
    painPoint: "Sem IA/automação (leitura manual)",
    traditionalProblem:
      "Outras plataformas exigem que você leia editais de 50 páginas",
    smartlicSolution:
      "No SmartLic, a IA gera um resumo executivo de 3 linhas",
    quantifiedBenefit:
      "Decida em 30 segundos, não em 20 minutos. IA que trabalha para você",
  },

  support: {
    painPoint: "Suporte lento (2-7 dias)",
    traditionalProblem:
      "Outras plataformas demoram dias para responder (2-7 dias em média)",
    smartlicSolution: "No SmartLic, garantimos resposta em até 4 horas",
    quantifiedBenefit:
      "Problemas resolvidos no mesmo dia. Seu tempo vale ouro",
  },

  interface: {
    painPoint: "Interface confusa (curva de aprendizado)",
    traditionalProblem:
      "Outras plataformas têm interfaces complexas que exigem treinamento",
    smartlicSolution:
      "No SmartLic, interface intuitiva com onboarding de 30 segundos",
    quantifiedBenefit:
      "Encontre sua primeira oportunidade em menos de 1 minuto. Sem manual",
  },

  stability: {
    painPoint: "Sistemas lentos e instáveis",
    traditionalProblem:
      "Outras plataformas sofrem com lentidão e instabilidade frequente",
    smartlicSolution:
      "No SmartLic, infraestrutura moderna com 99.9% uptime garantido",
    quantifiedBenefit:
      "Sempre disponível quando você precisa. 3 minutos do clique ao relatório",
  },
};

// ============================================================================
// PAIN POINTS SUMMARY (10 Market Pain Points)
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
    title: "Custo Alto + Cobranças Ocultas",
    userComplaint: "Mensalidades baixas mas cobram valores extras por visita",
    impact: "Empresas pequenas não conseguem prever custo total",
    smartlicDifferentiator:
      "Preço transparente sem surpresas (plano único all-inclusive)",
    metric: "R$ 297/mês fixo",
  },
  {
    id: 2,
    title: "Renovação Automática e Cancelamento Difícil",
    userComplaint: "Pedidos de cancelamento repetidamente adiados",
    impact: "Usuários se sentem presos, perdem confiança",
    smartlicDifferentiator:
      "Cancelamento em 1 clique (sem burocracia, sem ligações)",
  },
  {
    id: 3,
    title: "Burocracia Excessiva (Processo Manual)",
    userComplaint: "Processos lentos, excessivamente burocráticos",
    impact: "Empresas gastam 8+ horas/semana em buscas manuais",
    smartlicDifferentiator: "Busca por setor em vez de termos (1 clique)",
    metric: "160x mais rápido",
  },
  {
    id: 4,
    title: "Interface Confusa e Pouco Intuitiva",
    userComplaint: "Não sei onde encontrar as melhores oportunidades",
    impact: "Curva de aprendizado longa, frustração",
    smartlicDifferentiator: "Interface clean, moderna, intuitiva",
    metric: "30 segundos onboarding",
  },
  {
    id: 5,
    title: "Falta de Filtros Inteligentes (Muito Ruído)",
    userComplaint: "Muito ruído, resultados irrelevantes",
    impact: "Empresas gastam horas filtrando manualmente",
    smartlicDifferentiator: "Precisão de 95% (algoritmos proprietários)",
    metric: "5x mais preciso",
  },
  {
    id: 6,
    title: "Busca Apenas por Termos Específicos (Não por Setor)",
    userComplaint: "Busca manual no PNCP exige adivinhar palavras-chave",
    impact: "Empresas perdem oportunidades porque não sabem quais termos usar",
    smartlicDifferentiator:
      "Busca por ramo de atividade (ex: Uniformes, TI)",
    metric: "50+ sinônimos automáticos",
  },
  {
    id: 7,
    title: "Busca Manual em Múltiplos Portais",
    userComplaint: "Preciso buscar em dezenas de sites diferentes",
    impact: "Empresas perdem oportunidades porque não conseguem monitorar",
    smartlicDifferentiator:
      "Consolidação automática (PNCP + portais estaduais + municipais)",
    metric: "27+ fontes consolidadas",
  },
  {
    id: 8,
    title: "Velocidade Lenta e Sistemas Instáveis",
    userComplaint: "Sistema lento, não carrega",
    impact: "Perda de tempo, frustração, perda de prazos",
    smartlicDifferentiator: "Resultado em 3 minutos, 99.9% uptime",
    metric: "3 minutos total",
  },
  {
    id: 9,
    title: "Falta de Inteligência Artificial e Automação",
    userComplaint: "Preciso ler centenas de editais manualmente",
    impact: "Gestores gastam tempo lendo documentos extensos",
    smartlicDifferentiator:
      "Resumos executivos gerados por IA (IA analisa editais)",
    metric: "3 linhas vs 50 páginas",
  },
  {
    id: 10,
    title: "Atendimento Lento e Falta de Suporte",
    userComplaint: "Tempo médio de resposta: 7 dias",
    impact: "Problemas não resolvidos a tempo",
    smartlicDifferentiator: "Suporte humano em até 4 horas (email + chat)",
    metric: "40x mais rápido",
  },
];

// ============================================================================
// PROOF POINTS (Data to Back Claims)
// ============================================================================

export interface ProofPoint {
  claim: string;
  proofSource: string;
  disclaimerIfNeeded?: string;
}

export const proofPoints: Record<string, ProofPoint> = {
  speed160x: {
    claim: "160x mais rápido (3 min vs 8+ horas)",
    proofSource: "Internal timing + user research",
    disclaimerIfNeeded:
      "Comparação: busca manual média (8.5h) vs. SmartLic automatizado (3 min)",
  },

  precision95: {
    claim: "95% de precisão",
    proofSource: "Internal testing",
    disclaimerIfNeeded:
      "*Baseado em testes internos com 10.000+ buscas. Metodologia disponível sob solicitação.",
  },

  multiSource: {
    claim: "PNCP + 27 portais estaduais e municipais",
    proofSource: "Technical architecture",
  },

  timeSaved: {
    claim: "Economize 10h/semana",
    proofSource: "User research (avg 2h/day on manual searches = 10h/week)",
  },

  supportSLA: {
    claim: "Resposta em 4h",
    proofSource: "Customer support policy SLA commitment",
  },

  nationalCoverage: {
    claim: "27 UFs + 5.570 municípios",
    proofSource: "System capability (IBGE data)",
  },
};

// ============================================================================
// BEFORE/AFTER COMPARISON (Visual Contrast)
// ============================================================================

export interface BeforeAfterItem {
  aspect: string;
  before: string;
  after: string;
  icon: React.ComponentType<any>; // Lucide icon component
}

export const beforeAfter: BeforeAfterItem[] = [
  {
    aspect: "Tempo de Busca",
    before: "8+ horas por semana em buscas por termos",
    after: "3 minutos por busca (160x mais rápido)",
    icon: Zap,
  },
  {
    aspect: "Precisão dos Resultados",
    before: "~20% de precisão (muito ruído)",
    after: "95% de precisão (apenas oportunidades relevantes)",
    icon: Target,
  },
  {
    aspect: "Fontes Consultadas",
    before: "Apenas PNCP (busca manual em outros portais)",
    after: "PNCP + 27 portais em 1 busca automática",
    icon: Globe,
  },
  {
    aspect: "Análise de Documentos",
    before: "Leitura manual de editais de 50 páginas",
    after: "Resumos IA de 3 linhas",
    icon: Bot,
  },
  {
    aspect: "Custo Mensal",
    before: "Taxas ocultas e cobranças por consulta",
    after: "Fixo mensal (R$ 297-1.497)",
    icon: CircleDollarSign,
  },
  {
    aspect: "Cancelamento",
    before: "Difícil (ligações, burocracia)",
    after: "1 clique (sem retenção)",
    icon: CheckCircle2,
  },
];

// ============================================================================
// COMPETITIVE ADVANTAGE SCORING (Internal Use)
// ============================================================================

export interface AdvantageScore {
  advantage: string;
  strength: number; // 1-10
  defensibility: number; // 1-10 (hard to replicate)
  userImpact: number; // 1-10
  totalScore: number;
  priority: "high" | "medium" | "low";
}

export const advantageScores: AdvantageScore[] = [
  {
    advantage: "Speed (160x)",
    strength: 10,
    defensibility: 8,
    userImpact: 10,
    totalScore: 28,
    priority: "high",
  },
  {
    advantage: "Precision (95%)",
    strength: 9,
    defensibility: 9,
    userImpact: 9,
    totalScore: 27,
    priority: "high",
  },
  {
    advantage: "Consolidation (27 sources)",
    strength: 8,
    defensibility: 7,
    userImpact: 8,
    totalScore: 23,
    priority: "high",
  },
  {
    advantage: "AI Summaries",
    strength: 9,
    defensibility: 6,
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
    advantage: "4h Support SLA",
    strength: 7,
    defensibility: 6,
    userImpact: 6,
    totalScore: 19,
    priority: "medium",
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
 * Format defensive message as "Outras plataformas... SmartLic..." template
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
