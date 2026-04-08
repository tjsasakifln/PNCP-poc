/**
 * S13: Masterclass registry — Track E SEO implementation.
 * Provides type definitions and data for the /masterclass/* routes.
 */

export interface Masterclass {
  tema: string;
  title: string;
  description: string;
  duration: string;       // ISO 8601
  durationMinutes: number;
  instructor: string;     // author slug
  topics: string[];
  level: 'iniciante' | 'intermediario' | 'avancado';
  keywords: string[];
}

export const MASTERCLASSES: Masterclass[] = [
  {
    tema: 'primeiro-edital',
    title: 'Como Participar do Seu Primeiro Edital em 2026',
    description:
      'Passo a passo completo para iniciantes: desde a documentação de habilitação até a apresentação da proposta de preço. Aprenda o fluxo completo de participação em pregões eletrônicos.',
    duration: 'PT60M',
    durationMinutes: 60,
    instructor: 'tiago-sasaki',
    topics: [
      'Documentação de habilitação obrigatória',
      'Como ler e interpretar um edital',
      'Cadastro em plataformas de compras públicas',
      'Elaboração da proposta de preço',
      'Participação no pregão eletrônico passo a passo',
      'Erros comuns que desclassificam empresas',
    ],
    level: 'iniciante',
    keywords: ['primeiro edital', 'como participar de licitação', 'pregão eletrônico iniciante'],
  },
  {
    tema: 'analise-viabilidade',
    title: 'Análise de Viabilidade: Os 4 Fatores que Decidem se Você Deve Disputar',
    description:
      'Aprenda a avaliar objetivamente se uma licitação vale a pena antes de investir tempo e recursos. Metodologia de 4 fatores usada pelo SmartLic para classificar oportunidades.',
    duration: 'PT45M',
    durationMinutes: 45,
    instructor: 'tiago-sasaki',
    topics: [
      'Fator 1: Modalidade — impacto na complexidade',
      'Fator 2: Prazo — janela de preparação adequada',
      'Fator 3: Valor — margem vs esforço',
      'Fator 4: Geografia — custos logísticos e presença local',
      'Como calcular o score de viabilidade',
      'Casos reais: editais que pareciam bons mas não eram',
    ],
    level: 'intermediario',
    keywords: ['viabilidade licitação', 'análise de edital', 'vale a pena participar'],
  },
  {
    tema: 'inteligencia-setorial',
    title: 'Inteligência Setorial: Use Dados do PNCP para Mapear Oportunidades',
    description:
      'Aprenda a usar dados públicos do PNCP para identificar tendências, mapear concorrentes e antecipar oportunidades no seu setor. Técnicas avançadas de análise de mercado B2G.',
    duration: 'PT40M',
    durationMinutes: 40,
    instructor: 'tiago-sasaki',
    topics: [
      'Como consultar dados abertos do PNCP',
      'Análise de tendências por setor e UF',
      'Identificação de sazonalidade nas compras públicas',
      'Mapeamento de concorrentes por CNPJ',
      'Estimativa de valor total do mercado B2G por nicho',
      'Ferramentas e técnicas de monitoramento contínuo',
    ],
    level: 'avancado',
    keywords: ['inteligência setorial B2G', 'dados PNCP', 'mercado licitações'],
  },
];

export function getMasterclassByTema(tema: string): Masterclass | undefined {
  return MASTERCLASSES.find((m) => m.tema === tema);
}

export function getAllMasterclassTemas(): string[] {
  return MASTERCLASSES.map((m) => m.tema);
}
