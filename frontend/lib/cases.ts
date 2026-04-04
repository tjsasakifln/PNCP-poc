/**
 * SEO-PLAYBOOK P5: Case studies data module.
 *
 * 5 real case studies extracted from beta reports (docs/reports/).
 * Company names anonymized, numbers are real.
 */

export interface CaseMetrics {
  editaisAnalisados: number;
  valorIdentificado: string;
  tempoAnalise: string;
  scoreMedio: number;
  editaisPerdidosSemFiltro: number;
  reducaoTriagem: string;
}

export interface CaseStudy {
  slug: string;
  title: string;
  description: string;
  sector: string;
  sectorSlug: string;
  uf: string;
  company: string;
  companyProfile: string;
  problem: string;
  process: string;
  result: string;
  metrics: CaseMetrics;
  publishDate: string;
  lastModified?: string;
  keywords: string[];
}

const CASES: CaseStudy[] = [
  {
    slug: 'construtora-es-103m-oportunidades',
    title: 'Como uma construtora no ES identificou R$ 17,1M em obras compatíveis em uma única análise',
    description:
      'Construtora de pequeno porte em Vitória/ES analisou 8 editais e encontrou 3 oportunidades de alta viabilidade totalizando R$ 17,1M — todas na mesma UF, sem custo de mobilização.',
    sector: 'Engenharia e Construção',
    sectorSlug: 'engenharia',
    uf: 'ES',
    company: 'Construtora de pequeno porte em Vitória/ES',
    companyProfile:
      'EPP com capital social de R$ 1,4M, 18 anos de mercado, especializada em obras civis e infraestrutura urbana. Equipe de 12 pessoas.',
    problem:
      'A construtora participava de 2 a 3 editais por mês no setor de engenharia, escolhidos manualmente. O processo de triagem ocupava 6 horas semanais do engenheiro responsável. Dos editais analisados, cerca de 60% eram incompatíveis por valor acima da capacidade técnica ou distância geográfica inviável — mas só eram descartados depois de horas de leitura. A empresa não tinha visibilidade do volume real de oportunidades publicadas no Espírito Santo.',
    process:
      'Em março de 2026, rodou uma análise completa no SmartLic: setor Engenharia, UF Espírito Santo, período de 10 dias. Em menos de 2 minutos, o sistema identificou 8 editais publicados no período. Desses, descartou automaticamente 5 — 3 por valor acima de R$ 20M (fora do range da empresa) e 2 por modalidade de inexigibilidade. Os 3 restantes receberam score de viabilidade acima de 70/100, todos em municípios a menos de 100km de Vitória, eliminando custos de mobilização.',
    result:
      'Valor total dos 3 contratos identificados com viabilidade alta: R$ 17,1M. Todos os editais estavam dentro da capacidade técnica comprovada da empresa (acervo de CATs). A análise revelou que a construtora estava perdendo em média 5 editais compatíveis por mês por não monitorar o PNCP sistematicamente. Tempo de triagem semanal reduzido de 6 horas para 20 minutos.',
    metrics: {
      editaisAnalisados: 8,
      valorIdentificado: 'R$ 17,1M',
      tempoAnalise: '2 minutos',
      scoreMedio: 78,
      editaisPerdidosSemFiltro: 5,
      reducaoTriagem: 'de 6h para 20min/semana',
    },
    publishDate: '2026-03-15',
    keywords: [
      'licitação engenharia',
      'obras públicas ES',
      'construtora pequeno porte licitação',
      'como encontrar editais de obras',
    ],
  },
  {
    slug: 'infraestrutura-sc-38m-contratos',
    title: 'Como uma empresa de terraplanagem em SC mapeou R$ 33M em contratos de infraestrutura',
    description:
      'Empresa de infraestrutura viária em SC analisou 31 editais e identificou 15 oportunidades viáveis totalizando R$ 33M — concentradas no programa Casa Catarina e Novo PAC.',
    sector: 'Engenharia e Construção',
    sectorSlug: 'engenharia',
    uf: 'SC',
    company: 'Empresa de terraplanagem de médio porte em Blumenau/SC',
    companyProfile:
      'Empresa com capital de R$ 5M, 8 anos de mercado, especializada em terraplanagem, pavimentação e infraestrutura viária. Foco em contratos municipais no Oeste catarinense.',
    problem:
      'A empresa monitorava editais manualmente no PNCP e em portais municipais. Com 27 prefeituras no radar, a equipe comercial gastava 10 horas por semana apenas para triagem. Muitos editais do programa Casa Catarina e Novo PAC passavam despercebidos porque eram publicados com termos genéricos que não apareciam nas buscas por palavra-chave tradicionais.',
    process:
      'Em março de 2026, executou uma análise no SmartLic cobrindo o setor de Engenharia em Santa Catarina, período de 10 dias. O sistema encontrou 31 editais relevantes. A classificação por IA identificou 15 editais com viabilidade alta (score > 70), 9 para avaliar com cautela, e 7 incompatíveis. A filtragem automática detectou editais do Casa Catarina que usavam terminologia como "infraestrutura habitacional" — invisíveis em buscas por "terraplanagem".',
    result:
      'Valor total dos editais recomendados: R$ 33,1M. A análise identificou uma concentração de oportunidades no Oeste catarinense que a empresa não estava monitorando. O insight mais valioso: 40% dos editais compatíveis usavam termos que a busca manual por palavra-chave jamais encontraria. Triagem semanal reduzida de 10 horas para 45 minutos.',
    metrics: {
      editaisAnalisados: 31,
      valorIdentificado: 'R$ 33,1M',
      tempoAnalise: '3 minutos',
      scoreMedio: 74,
      editaisPerdidosSemFiltro: 12,
      reducaoTriagem: 'de 10h para 45min/semana',
    },
    publishDate: '2026-03-18',
    keywords: [
      'licitação terraplanagem',
      'editais infraestrutura SC',
      'programa Casa Catarina licitações',
      'como monitorar editais municipais',
    ],
  },
  {
    slug: 'distribuidora-ce-materiais-hospitalares',
    title: 'Como uma distribuidora no CE filtrou 126 editais para encontrar 3 oportunidades reais',
    description:
      'Distribuidora de materiais hospitalares com 1.000 contratos em 21 estados usou filtro inteligente para reduzir 126 editais a 3 compatíveis — eliminando 97% de falsos positivos.',
    sector: 'Saúde e Materiais Hospitalares',
    sectorSlug: 'saude',
    uf: 'CE',
    company: 'Distribuidora de materiais hospitalares em Sobral/CE',
    companyProfile:
      'Empresa com capital de R$ 2,8M, portfólio de 1.000 contratos governamentais em 21 estados. Especializada em materiais hospitalares, escolares e produtos de limpeza institucional.',
    problem:
      'Com atuação em 21 estados, a distribuidora recebia centenas de alertas de novos editais por semana. A equipe de 3 analistas passava 15 horas semanais lendo editais que, na maioria, eram incompatíveis — seja por distância logística (custo de frete > margem), seja por especificações técnicas diferentes dos produtos em estoque. O custo de analisar editais errados era maior que o custo de perder editais certos.',
    process:
      'Em março de 2026, rodou uma análise para o setor de Saúde no Ceará, período de 10 dias. O SmartLic identificou 126 editais com menção a materiais hospitalares ou correlatos. A filtragem automática por 4 fatores (modalidade, prazo, valor, geografia) descartou 123 editais: 89 por valor fora do range (lotes < R$ 10K ou > R$ 5M), 21 por distância logística inviável, 13 por modalidade incompatível. Restaram 3 editais com viabilidade real.',
    result:
      'Valor total das 3 oportunidades viáveis: R$ 622K. A análise revelou que 97,6% dos editais encontrados eram falsos positivos para o perfil da empresa — informação que validou a decisão de usar filtro inteligente em vez de monitoramento manual. Tempo de triagem reduzido de 15 horas para 30 minutos por semana. O insight-chave: focar em editais regionais (Nordeste) reduz custo logístico e aumenta competitividade.',
    metrics: {
      editaisAnalisados: 126,
      valorIdentificado: 'R$ 622K',
      tempoAnalise: '2 minutos',
      scoreMedio: 65,
      editaisPerdidosSemFiltro: 0,
      reducaoTriagem: 'de 15h para 30min/semana',
    },
    publishDate: '2026-03-20',
    keywords: [
      'licitação materiais hospitalares',
      'distribuição hospitalar governo',
      'editais saúde pública',
      'como filtrar editais de saúde',
    ],
  },
  {
    slug: 'studio-rs-projetos-tecnicos',
    title: 'Como um escritório de projetos no RS encontrou uma licitação de R$ 155K com score 73/100',
    description:
      'Escritório de arquitetura e projetos técnicos em RS identificou 1 oportunidade viável entre 4 editais — com score de viabilidade 73/100 e alinhamento perfeito com seu acervo técnico.',
    sector: 'Projetos Técnicos e Arquitetura',
    sectorSlug: 'informatica',
    uf: 'RS',
    company: 'Escritório de projetos técnicos em Porto Alegre/RS',
    companyProfile:
      'EPP com capital de R$ 80K, 4 contratos governamentais anteriores (IFSC, IFFAR). Especializado em projetos de edificações educacionais e públicas. Equipe de 5 profissionais.',
    problem:
      'O escritório dependia de indicações e buscas esporádicas no PNCP para encontrar editais. Com apenas 4 contratos no histórico, precisava ampliar o portfólio de CATs (Certidões de Acervo Técnico) para se qualificar em licitações maiores. O sócio-fundador dedicava 3 horas semanais a buscas manuais, mas a maioria dos editais encontrados exigia acervo técnico que a empresa ainda não tinha.',
    process:
      'Em março de 2026, analisou o setor de serviços de engenharia no Rio Grande do Sul, período de 10 dias. O SmartLic encontrou 4 editais relevantes. A análise de viabilidade por 4 fatores identificou 1 edital com score 73/100 (alta viabilidade): projeto de edificação educacional com valor de R$ 155K, prazo de 18 dias para proposta, modalidade pregão eletrônico, e localização a 180km — compatível com execução remota.',
    result:
      'O edital identificado era perfeitamente alinhado com o acervo técnico existente da empresa (projetos educacionais para institutos federais). Os 3 editais descartados tinham valor acima de R$ 800K — requerendo CATs que o escritório ainda não possuía. O insight mais valioso: a análise de valor × acervo evitou que a empresa gastasse tempo preparando propostas para licitações inelegíveis. Economia de 2 horas por semana em propostas sem chance.',
    metrics: {
      editaisAnalisados: 4,
      valorIdentificado: 'R$ 155K',
      tempoAnalise: '1 minuto',
      scoreMedio: 73,
      editaisPerdidosSemFiltro: 1,
      reducaoTriagem: 'de 3h para 15min/semana',
    },
    publishDate: '2026-03-22',
    keywords: [
      'licitação projetos técnicos',
      'editais arquitetura governo',
      'escritório projetos licitação pública',
      'como participar licitação serviços engenharia',
    ],
  },
  {
    slug: 'construtora-mg-rodovias-30m',
    title: 'Como uma construtora rodoviária em MG identificou R$ 30,9M em obras viárias urgentes',
    description:
      'Especialista em pavimentação e manutenção rodoviária analisou 19 editais e encontrou oportunidades de R$ 30,9M — incluindo uma de R$ 15M com prazo de resposta de 4 dias.',
    sector: 'Infraestrutura Rodoviária',
    sectorSlug: 'engenharia',
    uf: 'MG',
    company: 'Construtora de infraestrutura rodoviária em Belo Horizonte/MG',
    companyProfile:
      'Empresa especializada em pavimentação, manutenção e recuperação de rodovias estaduais e municipais em Minas Gerais. Atuação regional consolidada.',
    problem:
      'A construtora focava em contratos recorrentes de manutenção rodoviária com prefeituras conhecidas. Sem monitoramento sistemático, perdia editais de obras novas que exigiam resposta rápida — especialmente pregões eletrônicos com prazo de 5 a 7 dias entre publicação e abertura. A equipe comercial só descobria esses editais quando o prazo já era insuficiente para preparar documentação técnica completa.',
    process:
      'Em março de 2026, rodou uma análise para o setor de Engenharia em Minas Gerais, período de 10 dias. O SmartLic identificou 19 editais de infraestrutura, sendo 4 abertos e 15 já encerrados. A análise de viabilidade identificou 1 oportunidade de alta viabilidade (R$ 404K, score 80/100), 1 de média viabilidade que exigia avaliação urgente (R$ 15M, score 74/100 — com apenas 4 dias de prazo), e 2 incompatíveis por exigências de acervo específico.',
    result:
      'Valor total das oportunidades mapeadas: R$ 30,9M. O alerta de urgência para o edital de R$ 15M (prazo de 4 dias) foi o diferencial — sem monitoramento automático, a empresa não teria descoberto a tempo. A análise dos 15 editais encerrados revelou o volume real do mercado: R$ 30,5M em contratos perdidos no período por falta de monitoramento contínuo. Decisão: implementar monitoramento diário para capturar 100% das oportunidades.',
    metrics: {
      editaisAnalisados: 19,
      valorIdentificado: 'R$ 30,9M',
      tempoAnalise: '2 minutos',
      scoreMedio: 77,
      editaisPerdidosSemFiltro: 15,
      reducaoTriagem: 'de 8h para 25min/semana',
    },
    publishDate: '2026-03-19',
    keywords: [
      'licitação pavimentação',
      'editais rodovias MG',
      'manutenção rodoviária governo',
      'como monitorar editais de obras viárias',
    ],
  },
];

export function getAllCases(): CaseStudy[] {
  return CASES;
}

export function getCaseBySlug(slug: string): CaseStudy | undefined {
  return CASES.find((c) => c.slug === slug);
}

export function getAllCaseSlugs(): string[] {
  return CASES.map((c) => c.slug);
}
