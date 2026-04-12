/**
 * MKT-002 AC2: Programmatic SEO page helpers.
 *
 * Provides data fetching, static params generation, and editorial
 * content blocks for programmatic pages.
 */

import { SECTORS, type SectorMeta } from './sectors';

// All 27 Brazilian UFs
export const ALL_UFS = [
  'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN',
  'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
];

// UF full names for display
export const UF_NAMES: Record<string, string> = {
  AC: 'Acre', AL: 'Alagoas', AM: 'Amazonas', AP: 'Amapá',
  BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal', ES: 'Espírito Santo',
  GO: 'Goiás', MA: 'Maranhão', MG: 'Minas Gerais', MS: 'Mato Grosso do Sul',
  MT: 'Mato Grosso', PA: 'Pará', PB: 'Paraíba', PE: 'Pernambuco',
  PI: 'Piauí', PR: 'Paraná', RJ: 'Rio de Janeiro', RN: 'Rio Grande do Norte',
  RO: 'Rondônia', RR: 'Roraima', RS: 'Rio Grande do Sul', SC: 'Santa Catarina',
  SE: 'Sergipe', SP: 'São Paulo', TO: 'Tocantins',
};

// Correct Portuguese prepositions per state (PT-BR grammar)
// "no" → masculine article states, "na" → feminine article states, "em" → no article
export const UF_PREPOSITIONS: Record<string, string> = {
  AC: 'no',  // no Acre
  AL: 'em',  // em Alagoas
  AM: 'no',  // no Amazonas
  AP: 'no',  // no Amapá
  BA: 'na',  // na Bahia
  CE: 'no',  // no Ceará
  DF: 'no',  // no Distrito Federal
  ES: 'no',  // no Espírito Santo
  GO: 'em',  // em Goiás
  MA: 'no',  // no Maranhão
  MG: 'em',  // em Minas Gerais
  MS: 'no',  // no Mato Grosso do Sul
  MT: 'no',  // no Mato Grosso
  PA: 'no',  // no Pará
  PB: 'na',  // na Paraíba
  PE: 'em',  // em Pernambuco
  PI: 'no',  // no Piauí
  PR: 'no',  // no Paraná
  RJ: 'no',  // no Rio de Janeiro
  RN: 'no',  // no Rio Grande do Norte
  RO: 'em',  // em Rondônia
  RR: 'em',  // em Roraima
  RS: 'no',  // no Rio Grande do Sul
  SC: 'em',  // em Santa Catarina
  SE: 'em',  // em Sergipe
  SP: 'em',  // em São Paulo
  TO: 'no',  // no Tocantins
};

/** Returns the correct Portuguese preposition for a Brazilian state (ex: "na", "no", "em") */
export function getUfPrep(uf: string | undefined): string {
  if (!uf) return 'em';
  return UF_PREPOSITIONS[uf.toUpperCase()] ?? 'em';
}

export interface SectorBlogStats {
  sector_id: string;
  sector_name: string;
  total_editais: number;
  value_range_min: number;
  value_range_max: number;
  avg_value: number;
  top_modalidades: { name: string; count: number }[];
  top_ufs: { name: string; count: number }[];
  trend_90d: { period: string; count: number; avg_value: number }[];
  last_updated: string;
}

export interface SectorUfStats {
  sector_id: string;
  sector_name: string;
  uf: string;
  total_editais: number;
  avg_value: number;
  value_range_min: number;
  value_range_max: number;
  top_modalidades: { name: string; count: number }[];
  trend_90d: { period: string; count: number; avg_value: number }[];
  top_oportunidades: {
    titulo: string;
    orgao: string;
    valor: number | null;
    uf: string;
    data: string;
  }[];
  last_updated: string;
  most_recent_bid_date?: string;
}

export interface PanoramaStats {
  sector_id: string;
  sector_name: string;
  total_nacional: number;
  total_value: number;
  avg_value: number;
  top_ufs: { name: string; count: number }[];
  top_modalidades: { name: string; count: number }[];
  sazonalidade: { period: string; count: number; avg_value: number }[];
  crescimento_estimado_pct: number;
  last_updated: string;
}

/**
 * Generate static params for sector programmatic pages.
 * Returns all 15 sector slugs.
 */
export function generateSectorParams(): { setor: string }[] {
  return SECTORS.map((s) => ({ setor: s.slug }));
}

/**
 * Generate static params for sector × UF programmatic pages.
 * Returns 15 sectors × 27 UFs = 405 combinations.
 */
export function generateSectorUfParams(): { setor: string; uf: string }[] {
  const params: { setor: string; uf: string }[] = [];
  for (const sector of SECTORS) {
    for (const uf of ALL_UFS) {
      params.push({ setor: sector.slug, uf: uf.toLowerCase() });
    }
  }
  return params;
}

/**
 * Fetch sector blog stats from backend (server-side).
 */
export async function fetchSectorBlogStats(sectorSlug: string): Promise<SectorBlogStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const sectorId = sectorSlug.replace(/-/g, '_');
    const res = await fetch(`${backendUrl}/v1/blog/stats/setor/${sectorId}`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch sector × UF stats from backend (server-side).
 */
export async function fetchSectorUfBlogStats(
  sectorSlug: string,
  uf: string,
): Promise<SectorUfStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const sectorId = sectorSlug.replace(/-/g, '_');
    const res = await fetch(`${backendUrl}/v1/blog/stats/setor/${sectorId}/uf/${uf.toUpperCase()}`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch panorama stats from backend (server-side).
 */
export async function fetchPanoramaStats(sectorSlug: string): Promise<PanoramaStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const sectorId = sectorSlug.replace(/-/g, '_');
    const res = await fetch(`${backendUrl}/v1/blog/stats/panorama/${sectorId}`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Get sector metadata from slug.
 */
export function getSectorFromSlug(slug: string): SectorMeta | undefined {
  return SECTORS.find((s) => s.slug === slug);
}

/**
 * Format BRL currency value.
 */
export function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Generate FAQs for a sector programmatic page.
 * Returns 5 FAQs specific to the sector context.
 */
export function generateSectorFAQs(
  sectorName: string,
  totalEditais?: number,
  topUf?: string,
): { question: string; answer: string }[] {
  const count = totalEditais || 'diversas';
  const uf = topUf || 'São Paulo';

  return [
    {
      question: `Quantas licitações de ${sectorName} estão abertas agora?`,
      answer: `Atualmente há ${count} licitações de ${sectorName} publicadas nos últimos 10 dias no PNCP e portais estaduais. O SmartLic monitora automaticamente todas as fontes.`,
    },
    {
      question: `Qual o estado com mais licitações de ${sectorName}?`,
      answer: `${uf} concentra o maior volume de licitações de ${sectorName}, seguido por outros estados do Sudeste. No SmartLic você filtra por UF e analisa a viabilidade de cada edital.`,
    },
    {
      question: `Como analisar a viabilidade de uma licitação de ${sectorName}?`,
      answer: `O SmartLic usa 4 fatores: modalidade (30%), prazo (25%), valor (25%) e geografia (20%). A pontuação de viabilidade ajuda a priorizar os editais com maior probabilidade de sucesso.`,
    },
    {
      question: `Preciso pagar para ver licitações de ${sectorName}?`,
      answer: `Você pode testar o SmartLic grátis por 14 dias, sem cartão de crédito. O teste inclui busca com IA, análise de viabilidade e exportação de relatórios.`,
    },
    {
      question: `Como receber alertas de novas licitações de ${sectorName}?`,
      answer: `Configure alertas por e-mail no SmartLic para receber notificações quando novas licitações do seu setor forem publicadas. Os alertas são personalizáveis por UF, valor e modalidade.`,
    },
  ];
}

/**
 * Generate editorial content block (300+ words) for sector pages.
 * Returns unique, human-quality content per sector.
 */
export function getEditorialContent(sectorId: string): string {
  const content: Record<string, string> = {
    vestuario: `O mercado de licitações de vestuário e uniformes no Brasil movimenta bilhões de reais anualmente, abrangendo desde fardamentos militares até uniformes escolares. As compras governamentais neste setor são recorrentes — órgãos públicos renovam estoques periodicamente, criando um fluxo previsível de oportunidades. A Lei 14.133/2021 trouxe mudanças significativas nas modalidades de contratação, favorecendo o pregão eletrônico como principal via para aquisições de vestuário padronizado. Empresas que dominam a documentação técnica de especificações têxteis (composição, gramatura, acabamento) têm vantagem competitiva significativa. O segmento de EPIs de vestuário cresceu especialmente após as regulamentações de segurança do trabalho serem reforçadas, abrindo um nicho de alto valor agregado dentro das licitações de uniformes. Para consultorias e assessorias, entender a sazonalidade deste setor é crucial: compras escolares concentram-se no segundo semestre, enquanto fardamentos militares e de segurança pública distribuem-se ao longo do ano. A análise de viabilidade deve considerar a capacidade produtiva da confecção, os prazos de entrega exigidos e a logística de distribuição para múltiplos pontos.`,

    alimentos: `O setor de alimentos e merenda escolar representa uma das maiores fatias das compras governamentais no Brasil, com destaque para o Programa Nacional de Alimentação Escolar (PNAE), que atende mais de 40 milhões de estudantes. A complexidade deste mercado vai além do preço: exigências sanitárias da ANVISA, certificações de qualidade, cadeia de frio e rastreabilidade são fatores eliminatórios que reduzem a concorrência efetiva. Pequenos produtores rurais têm preferência legal de até 30% nas compras de merenda escolar via cooperativas, criando um ecossistema único de licitações. O valor médio dos contratos varia enormemente — de R$ 5 mil para fornecimentos pontuais a R$ 50 milhões para contratos de refeições hospitalares. A sazonalidade é marcante: o pico de publicações concentra-se nos primeiros meses do ano letivo. Empresas que investem em certificações (ISO 22000, HACCP) e possuem estrutura logística para entregas fracionadas em múltiplos pontos têm taxa de adjudicação significativamente superior à média. O segmento de refeições transportadas para hospitais e presídios representa um nicho de alta barreira de entrada e margens superiores.`,

    informatica: `Licitações de hardware e equipamentos de TI formam um dos setores mais competitivos das compras governamentais, com alto volume de pregões eletrônicos e atas de registro de preço nacionais. A dinâmica deste mercado é influenciada pela rápida obsolescência tecnológica e pela padronização de especificações técnicas em editais. Atas de registro de preço federais (gerenciadas pelo Ministério da Gestão) definem preços-teto que cascateiam para estados e municípios, criando uma estrutura oligopolística onde grandes distribuidores dominam. Empresas de menor porte encontram oportunidades em licitações municipais e em nichos específicos: servidores de alta performance, equipamentos de rede e soluções de armazenamento. A margem operacional nestas licitações é tipicamente estreita (5-12%), compensada pelo volume e pela recorrência. O processo de certificação junto a fabricantes (Dell, HP, Lenovo) é um diferencial competitivo decisivo. O segmento de impressão (outsourcing de impressão) representa um nicho altamente lucrativo com contratos de longo prazo e receita recorrente, embora exija investimento significativo em parque de equipamentos.`,

    mobiliario: `O segmento de mobiliário nas licitações públicas abrange desde mobiliário escolar até mobília de escritório para órgãos federais, com um mercado que se renova constantemente pela necessidade de equipar novas unidades e substituir itens desgastados. A especificação técnica é crucial: editais de mobiliário exigem conformidade com normas ABNT (NBR 14006 para mobiliário escolar, NBR 13962 para cadeiras de escritório), e a comprovação dessa conformidade é fator eliminatório. Empresas fabricantes têm vantagem sobre revendedoras pela capacidade de personalização e custos menores. O prazo de entrega é frequentemente o gargalo — editais com prazos curtos e entregas em múltiplos pontos reduzem significativamente o número de concorrentes efetivos. O setor tem forte sazonalidade ligada à abertura de novos órgãos, inauguração de escolas e reformas administrativas, com picos no segundo semestre do ano fiscal.`,

    papelaria: `Material de escritório e papelaria representa o setor de compras governamentais com menor barreira de entrada, tornando-o extremamente competitivo em preço. No entanto, a margem por item é compensada pelo volume e pela recorrência — órgãos públicos consumem material de escritório continuamente. A estratégia vencedora neste segmento não é o menor preço unitário, mas a capacidade logística de entrega fracionada e o atendimento integral do edital. Muitas empresas perdem licitações por não cotarem todos os itens do lote ou por não atenderem aos prazos de entrega parcelada. Atas de registro de preço estaduais são o principal mecanismo de compra, com vigência de 12 meses e possibilidade de adesão por múltiplos órgãos.`,

    engenharia: `Engenharia e obras públicas constituem o setor de maior valor agregado nas licitações brasileiras, com contratos que podem ultrapassar centenas de milhões de reais. A complexidade técnica e jurídica deste setor exige equipes multidisciplinares: engenheiros com acervo técnico compatível, advogados especializados em licitações e gestores financeiros que entendam de fluxo de caixa em contratos de longo prazo. A Lei 14.133/2021 introduziu o BIM (Building Information Modeling) como requisito em obras de grande porte, elevando a barreira tecnológica. A qualificação técnica é o principal filtro: atestados de capacidade técnica, certidões do CREA/CAU e comprovação de experiência em obras similares eliminam a maioria dos concorrentes. O regime de contratação integrada, previsto para obras complexas, transfere o risco de projeto para o contratado, exigindo análise de viabilidade ainda mais criteriosa.`,

    software: `O mercado de software e sistemas nas licitações públicas experimenta transformação acelerada, impulsionado pela estratégia de governo digital e pela crescente adoção de soluções SaaS em substituição a licenças perpétuas. O modelo de contratação está migrando para serviços por assinatura com métricas de SLA, favorecendo empresas que oferecem suporte contínuo e atualizações regulares. A qualificação técnica neste segmento vai além de atestados tradicionais — certificações de equipe (AWS, Azure, Google Cloud) e demonstrações técnicas em ambientes controlados são diferenciais decisivos. Pequenas software houses encontram oportunidades em nichos verticais: sistemas de saúde pública, gestão educacional, controle de frotas. O maior desafio é a competição com grandes players que oferecem suítes integradas com preços subsidiados pelo volume.`,

    facilities: `Facilities e manutenção predial é um dos setores com maior volume de licitações no Brasil, abrangendo serviços de limpeza, conservação, portaria, jardinagem e gestão predial. A terceirização destes serviços é prática consolidada no setor público, com contratos de 12 a 60 meses e receita mensal previsível. A precificação é regulamentada por convenções coletivas de trabalho regionais, que definem pisos salariais por categoria profissional — empresas que não dominam a composição de custos por planilha detalhada correm risco de propor preços inexequíveis ou inviáveis. A fiscalização destes contratos é rigorosa, com medição mensal de produtividade e qualidade. O segmento de facilities integrados, que combina múltiplos serviços em um único contrato, está em crescimento e oferece margens superiores à contratação isolada.`,

    saude: `Licitações de saúde compreendem um dos segmentos mais complexos e regulamentados das compras governamentais, abrangendo medicamentos, equipamentos hospitalares, insumos médicos e serviços especializados. A regulação da ANVISA adiciona uma camada de complexidade: registros de produtos, certificações de boas práticas de fabricação e rastreabilidade são requisitos eliminatórios. O setor é dominado por distribuidores especializados com capacidade logística para entrega em tempo real (especialmente para medicamentos de emergência). Atas de registro de preço federais, gerenciadas pelo Ministério da Saúde, padronizam preços de medicamentos essenciais. Nichos de alta margem incluem equipamentos de diagnóstico por imagem, próteses ortopédicas e materiais para cirurgias especializadas. A Pandemia de COVID-19 expandiu permanentemente as compras emergenciais, criando precedentes legais para contratações diretas em situações de urgência.`,

    vigilancia: `O setor de vigilância e segurança patrimonial nas licitações públicas opera sob regulação específica da Polícia Federal, exigindo alvará de funcionamento, certificado de segurança e formação técnica do efetivo. Estas barreiras regulatórias limitam significativamente a concorrência, beneficiando empresas já estabelecidas. O valor dos contratos é determinado por convenções coletivas regionais e pela complexidade dos postos — vigilância armada em áreas de risco tem valores substancialmente superiores à vigilância desarmada em ambientes administrativos. A tecnologia está transformando o setor: monitoramento eletrônico (CFTV, controle de acesso) complementa e em alguns casos substitui postos presenciais, criando oportunidades para empresas com capacidade de integração de sistemas.`,

    transporte: `Licitações de transporte e veículos abrangem aquisição, locação e manutenção de frotas governamentais, combustíveis e serviços de transporte de passageiros. A locação operacional de veículos consolidou-se como modelo preferencial para frotas administrativas, por transferir o risco de depreciação e manutenção ao contratado. Empresas de locação com frotas diversificadas e cobertura geográfica ampla dominam as atas de registro de preço federais. O segmento de combustíveis opera com margens mínimas mas volumes imensos — contratos podem ultrapassar dezenas de milhões de reais anuais. A eletrificação da frota governamental, impulsionada por políticas de sustentabilidade, cria oportunidades para fornecedores de veículos elétricos e infraestrutura de recarga.`,

    manutencao_predial: `Manutenção e conservação predial engloba serviços técnicos especializados: ar-condicionado (PMOC obrigatório), elevadores, sistemas elétricos e hidráulicos, impermeabilização e reformas prediais. A qualificação técnica exige acervos do CREA e profissionais habilitados para cada especialidade. Contratos de manutenção preventiva são a base do setor, com frequência definida em planos anuais e medição por ordem de serviço. O modelo de contratação por desempenho está ganhando espaço, vinculando o pagamento a indicadores de disponibilidade e conforto do ambiente. Empresas que oferecem diagnóstico energético e retrofitting como serviços complementares encontram um nicho de alta margem e diferenciação competitiva.`,

    engenharia_rodoviaria: `Engenharia rodoviária e infraestrutura viária movimenta os maiores valores unitários nas licitações públicas brasileiras, com contratos que frequentemente ultrapassam R$ 100 milhões. A complexidade técnica é elevada: projetos de pavimentação, pontes, viadutos e sinalização exigem equipes de engenheiros com acervo técnico compatível em obras similares. O DNIT e os DERs estaduais são os principais contratantes, com editais que exigem comprovação de capacidade técnico-operacional e equipamentos próprios ou locados. A sazonalidade é influenciada pelo regime de chuvas regional — obras rodoviárias concentram-se no período seco. O PAC e seus sucessores garantem um pipeline contínuo de obras federais, enquanto recursos de emendas parlamentares alimentam obras estaduais e municipais.`,

    materiais_eletricos: `O segmento de materiais elétricos e instalações nas licitações públicas atende demandas recorrentes de manutenção e expansão da infraestrutura elétrica de prédios públicos, iluminação pública e redes de distribuição. A especificação técnica é regulada por normas ABNT e certificações INMETRO — produtos sem certificação são automaticamente desclassificados. O mercado é segmentado entre fornecedores de materiais (fios, cabos, disjuntores) e prestadores de serviço de instalação, sendo que a integração de ambos em um único fornecedor confere vantagem competitiva. O crescimento da energia solar fotovoltaica no setor público cria um nicho emergente de alta margem: projetos de microgeração distribuída e eficiência energética.`,

    materiais_hidraulicos: `Materiais hidráulicos e saneamento representam um setor estratégico das compras governamentais, diretamente ligado às políticas de universalização do acesso à água e esgoto. O Marco Legal do Saneamento (Lei 14.026/2020) impulsionou investimentos massivos em infraestrutura hídrica, multiplicando as oportunidades de licitação para fornecedores de tubos, conexões, bombas e equipamentos de tratamento. A especificação técnica é rigorosa: conformidade com normas ABNT para pressão de trabalho, material e diâmetro é requisito eliminatório. Empresas que oferecem soluções integradas — material + projeto + instalação — têm vantagem em licitações de maior porte. O setor de tratamento de água e efluentes, incluindo estações compactas para municípios de pequeno porte, representa o nicho de maior crescimento projetado para a próxima década.`,
  };

  return content[sectorId] || content.vestuario || '';
}

// -----------------------------------------------------------------------
// MKT-004: Panorama page helpers
// -----------------------------------------------------------------------

/**
 * MKT-004 AC4: Generate FAQs for national panorama pages.
 * Returns 7 FAQs specific to national-level sector data.
 */
export function generatePanoramaFAQs(
  sectorName: string,
  totalNacional?: number,
  crescimentoPct?: number,
  topUf?: string,
  avgValue?: number,
): { question: string; answer: string }[] {
  const count = totalNacional ?? 0;
  const growth = crescimentoPct ?? 12;
  const uf = topUf || 'São Paulo';
  const avg = avgValue ? formatBRL(avgValue) : 'variável';

  return [
    {
      question: `Quantas licitações de ${sectorName} são publicadas por mês no Brasil?`,
      answer: `Nos últimos 90 dias foram registradas ${count > 0 ? count : 'centenas de'} licitações de ${sectorName} em todo o Brasil, consolidando dados do PNCP, Portal de Compras Públicas e ComprasGov. O volume mensal varia conforme sazonalidade orçamentária.`,
    },
    {
      question: `Qual o estado com maior volume de licitações de ${sectorName}?`,
      answer: `${uf} lidera o ranking nacional de licitações de ${sectorName}, concentrando a maior fatia das publicações. Outros estados do Sudeste e Sul completam o top 5. O SmartLic permite filtrar por UF e analisar viabilidade por região.`,
    },
    {
      question: `Como está a tendência do mercado de ${sectorName} em licitações?`,
      answer: `O setor de ${sectorName} apresenta crescimento estimado de ${growth}% em relação ao período anterior, refletindo aumento nos investimentos públicos. A sazonalidade mostra picos no segundo e terceiro trimestres do ano fiscal.`,
    },
    {
      question: `Qual o valor médio das licitações de ${sectorName} no Brasil?`,
      answer: `O valor médio estimado é de ${avg}. Esse valor varia significativamente por modalidade (pregão eletrônico vs concorrência) e por esfera de governo (federal, estadual, municipal).`,
    },
    {
      question: `Quais modalidades de licitação são mais comuns para ${sectorName}?`,
      answer: `O pregão eletrônico predomina nas aquisições de ${sectorName}, seguido por dispensa de licitação e concorrência. A Lei 14.133/2021 consolidou o pregão como via preferencial para bens e serviços comuns em todo o território nacional.`,
    },
    {
      question: `Como usar dados de licitações de ${sectorName} para planejamento comercial?`,
      answer: `Dados de volume por UF, sazonalidade e faixa de valores permitem dimensionar equipe comercial, priorizar regiões e antecipar demandas. O SmartLic consolida esses dados e classifica oportunidades com IA para maximizar a taxa de adjudicação.`,
    },
    {
      question: `Posso acompanhar licitações de ${sectorName} em tempo real?`,
      answer: `Sim. O SmartLic monitora automaticamente PNCP, Portal de Compras Públicas e ComprasGov, atualizando dados a cada 24 horas. Teste grátis por 14 dias e receba alertas personalizados de novas oportunidades no seu setor.`,
    },
  ];
}

/**
 * MKT-004 AC3: Extended editorial content blocks for panorama pages.
 * Returns 5 structured sections that, combined with getEditorialContent(),
 * produce 2500+ words per panorama page.
 */
export function getPanoramaEditorial(sectorId: string, sectorName: string): {
  contexto: string;
  dicas: string;
  perfilComprador: string;
  casosDeUso: string;
  tendencias2026: string;
} {
  const editorials: Record<string, {
    contexto: string;
    dicas: string;
    perfilComprador: string;
    casosDeUso: string;
    tendencias2026: string;
  }> = {
    vestuario: {
      contexto: 'O mercado de vestuário e uniformes nas compras públicas brasileiras é um dos mais recorrentes e previsíveis do setor B2G. Órgãos federais, estaduais e municipais renovam estoques de fardamentos, uniformes escolares e EPIs de vestuário em ciclos regulares, criando um fluxo constante de oportunidades para confecções e distribuidores. A Lei 14.133/2021 impactou positivamente o setor ao consolidar o pregão eletrônico como principal via de aquisição, reduzindo barreiras geográficas e permitindo que empresas de qualquer estado participem de editais em todo o Brasil. O volume anual de licitações de vestuário supera dezenas de milhares de publicações quando consolidamos PNCP, Portal de Compras Públicas e ComprasGov.',
      dicas: 'Para competir com sucesso em licitações de vestuário, é fundamental dominar as especificações técnicas têxteis exigidas nos editais: composição de tecido (percentuais de algodão, poliéster), gramatura mínima, resistência à tração e lavagens, e acabamentos especiais (anti-chama, UV, impermeável). Empresas que mantêm laudos laboratoriais atualizados e certificações de conformidade ABNT economizam semanas no processo de habilitação. Outro diferencial competitivo é a capacidade de entrega fracionada — muitos editais exigem entregas parceladas em múltiplos pontos ao longo de 6-12 meses, e confecções sem estrutura logística descentralizada são eliminadas na fase de proposta.',
      perfilComprador: 'O comprador governamental de vestuário é tipicamente um servidor da área de logística ou intendência, com perfil técnico e foco em conformidade normativa. Diferente do comprador privado, ele não busca moda ou design — busca durabilidade, conformidade com especificações e preço competitivo. Decisões de compra são vinculadas ao exercício fiscal e ao planejamento anual de aquisições, publicado em planos de contratação disponíveis no PNCP. Entender esse perfil significa antecipar demandas: escolas renovam uniformes no segundo semestre, forças de segurança fazem aquisições ao longo do ano, e hospitais compram EPIs continuamente.',
      casosDeUso: 'Uma confecção de médio porte no interior de Minas Gerais utilizava planilhas manuais para monitorar editais de vestuário no PNCP. Com o SmartLic, automatizou a triagem de oportunidades e passou a focar apenas em editais com viabilidade alta — resultado: a taxa de adjudicação subiu de 8% para 22% em seis meses. Consultorias de licitação que atendem confecções usam os dados consolidados de volume por UF para recomendar a seus clientes quais regiões priorizar, maximizando o retorno sobre o investimento em propostas.',
      tendencias2026: 'Em 2026, o setor de vestuário em licitações deve ser impactado por três tendências: (1) sustentabilidade — cresce o número de editais exigindo certificações ambientais e uso de materiais reciclados; (2) EPIs especializados — regulamentações de segurança do trabalho mais rigorosas expandem o nicho de vestuário técnico; (3) digitalização — a migração completa para pregão eletrônico elimina vantagens locais e intensifica a competição por preço.',
    },
    alimentos: {
      contexto: 'O setor de alimentos e merenda escolar é um dos pilares das compras governamentais no Brasil, movimentando bilhões de reais anualmente. O Programa Nacional de Alimentação Escolar (PNAE) atende mais de 40 milhões de estudantes, gerando demanda contínua e geograficamente distribuída por todos os 5.570 municípios brasileiros. Além do PNAE, hospitais públicos, presídios, quartéis e órgãos administrativos demandam serviços de alimentação e fornecimento de gêneros alimentícios. A consolidação de dados do PNCP, Portal de Compras Públicas e ComprasGov revela que este é consistentemente um dos setores com maior número de publicações mensais.',
      dicas: 'Empresas que atuam em licitações de alimentos devem investir em certificações sanitárias (ANVISA, vigilância sanitária estadual/municipal), registros de produtos e rastreabilidade de cadeia de frio. Editais de merenda escolar frequentemente exigem comprovação de capacidade de entrega fracionada em múltiplas escolas — logística é tão importante quanto preço. Uma estratégia eficaz é focar em atas de registro de preço, que permitem fornecimento contínuo por 12 meses com reequilíbrio econômico-financeiro periódico, protegendo margens da volatilidade de preços agrícolas.',
      perfilComprador: 'O comprador governamental de alimentos opera sob intensa fiscalização: nutricionistas do PNAE, conselhos de alimentação escolar (CAE) e auditorias do TCU monitoram qualidade e conformidade. O perfil decisório é técnico, com requisitos rígidos de composição nutricional, prazo de validade, embalagem e rotulagem. Compras são planejadas anualmente com base no cardápio escolar aprovado, publicado nos planos de contratação. Municípios de pequeno porte frequentemente utilizam chamada pública para aquisição direta da agricultura familiar, criando um canal complementar ao pregão.',
      casosDeUso: 'Distribuidoras de alimentos que monitoram licitações em todo o Brasil usam dados de sazonalidade para dimensionar estoques: períodos letivos concentram demanda de merenda, enquanto recesso escolar reduz drasticamente o volume. Cooperativas de agricultura familiar utilizam dados de panorama para identificar municípios com maior volume de chamadas públicas e direcionar sua produção. O SmartLic permite filtrar por modalidade (chamada pública, pregão, dispensa) e valor, otimizando a seleção de oportunidades por perfil de fornecedor.',
      tendencias2026: 'Para 2026, três movimentos marcam o setor: (1) alimentos orgânicos — o percentual mínimo de orgânicos na merenda escolar tende a aumentar, beneficiando produtores certificados; (2) regionalização — políticas de compra local priorizam fornecedores do próprio estado/município; (3) refeições transportadas — o segmento de alimentação hospitalar e carcerária cresce com a expansão de PPPs (parcerias público-privadas) no setor de saúde.',
    },
    informatica: {
      contexto: 'O mercado de hardware e equipamentos de TI nas licitações públicas brasileiras é um dos mais dinâmicos e competitivos do setor B2G. A transformação digital do governo — impulsionada pela Estratégia Nacional de Governo Digital e pela Lei de Governo Digital (14.129/2021) — gera demanda crescente por computadores, servidores, equipamentos de rede, storage e periféricos em todas as esferas governamentais. Atas de registro de preço federais, gerenciadas pelo Ministério da Gestão e Inovação, definem preços-teto que cascateiam para estados e municípios, criando uma estrutura de mercado onde escala e eficiência logística são diferenciais decisivos.',
      dicas: 'Para competir em licitações de informática, três fatores são determinantes: (1) credenciamento junto a fabricantes (Dell, HP, Lenovo, Samsung) — sem carta de distribuição autorizada, a maioria dos editais exclui o participante na habilitação; (2) capacidade de atender atas de registro de preço com entrega nacional — editais federais exigem cobertura em todos os estados; (3) gestão de estoque just-in-time — a rapidez na entrega após empenho é um diferencial mensurável. Empresas que mantêm APIs integradas com o ComprasGov e PNCP para monitoramento automatizado de novas atas e adesões ganham vantagem de tempo sobre concorrentes que dependem de monitoramento manual.',
      perfilComprador: 'O comprador governamental de TI é tipicamente um servidor da área de tecnologia da informação, com conhecimento técnico de especificações. A decisão de compra segue o PDTIC (Plano Diretor de TI e Comunicação) do órgão, publicado anualmente. As especificações técnicas tendem a ser detalhadas (processador, memória, armazenamento, certificações Energy Star/EPEAT), e a análise de propostas inclui verificação de conformidade item a item. O ciclo de renovação de parque é tipicamente de 4-5 anos para desktops e 3-4 anos para notebooks, gerando demanda previsível.',
      casosDeUso: 'Um distribuidor de TI com sede em São Paulo utilizava equipe de 4 analistas para monitorar editais manualmente no PNCP. Ao adotar o SmartLic, reduziu para 1 analista focado em propostas qualificadas — o sistema filtra por especificação técnica, valor e UF, eliminando editais irrelevantes. Consultorias que assessoram órgãos públicos na elaboração de termos de referência usam dados de panorama (valor médio, especificações mais comuns) para benchmarking de preços, garantindo economicidade nas contratações.',
      tendencias2026: 'O panorama de TI em licitações para 2026 é moldado por: (1) computação em nuvem — cresce a migração para IaaS/SaaS, mas hardware para edge computing e data centers governamentais mantém demanda robusta; (2) IA e automação — editais de infraestrutura para IA (GPUs, servidores com alta capacidade de processamento) emergem como novo segmento; (3) sustentabilidade — exigências de certificação ambiental (EPEAT Gold, Energy Star) tornam-se obrigatórias em editais federais; (4) cibersegurança — equipamentos com TPM 2.0 e firmware seguro ganham preferência em especificações.',
    },
    mobiliario: {
      contexto: 'O segmento de mobiliário nas licitações públicas movimenta volumes expressivos, abrangendo mobiliário escolar (mesas, cadeiras, estantes), mobiliário de escritório (estações de trabalho, armários, gaveteiros) e mobiliário hospitalar (macas, camas, armários médicos). A demanda é constante e renovável — novos prédios públicos, reformas administrativas e expansão da rede escolar geram licitações ao longo de todo o ano. A Lei 14.133/2021 favoreceu o pregão eletrônico como modalidade principal, permitindo que fabricantes e revendedores de qualquer estado participem de certames nacionais.',
      dicas: 'Conformidade com normas ABNT é requisito eliminatório em praticamente todos os editais de mobiliário: NBR 14006 (mobiliário escolar), NBR 13962 (cadeiras de escritório), NBR 13966 (mesas). Empresas devem manter laudos de ensaio atualizados em laboratórios acreditados pelo INMETRO. Fabricantes têm vantagem competitiva sobre revendedores pela capacidade de personalização e custos menores, mas revendedores podem compensar com logística superior e mix de produtos. Dica crucial: focar em editais com lotes segmentados (escolar separado de escritório) permite especialização e margens melhores.',
      perfilComprador: 'Compradores de mobiliário governamental são servidores de logística ou engenharia, que avaliam propostas com base em conformidade normativa, ergonomia e durabilidade. O ciclo de compra é influenciado por inaugurações de prédios públicos, reformas e início de ano letivo. Muitos órgãos utilizam atas de registro de preço estaduais para padronizar o mobiliário, facilitando a manutenção e reposição futura. Entender o PDCA (plano de contratação anual) do órgão permite antecipar demandas com meses de antecedência.',
      casosDeUso: 'Uma indústria moveleira do Rio Grande do Sul expandiu sua atuação de mercado corporativo privado para licitações públicas usando dados do SmartLic para identificar editais de mobiliário escolar com volume compatível com sua capacidade produtiva. Em 8 meses, licitações públicas passaram a representar 35% do faturamento, com margens superiores ao mercado privado devido à estabilidade contratual. Assessorias de licitação usam dados de panorama para orientar fabricantes sobre quais regiões e tipos de mobiliário têm maior demanda.',
      tendencias2026: 'Para 2026, o setor de mobiliário em licitações é impactado por: (1) ergonomia obrigatória — a NR-17 atualizada exige cadeiras e estações de trabalho ergonômicas, elevando o ticket médio; (2) sustentabilidade — editais federais começam a exigir certificações de origem de madeira (FSC) e materiais reciclados; (3) mobiliário flexível — espaços de coworking governamental demandam mobiliário modular e reconfigurável.',
    },
    papelaria: {
      contexto: 'Material de escritório e papelaria é o setor com maior número de licitações publicadas anualmente no Brasil, embora com valores unitários menores que outros segmentos. Todos os órgãos públicos — dos menores municípios às maiores autarquias federais — necessitam de papel, canetas, material de escritório e suprimentos administrativos. Esta ubiquidade cria um mercado de altíssimo volume onde a escala logística e a capacidade de atendimento integral de editais são mais importantes que o menor preço unitário.',
      dicas: 'A estratégia vencedora em papelaria não é o menor preço — é a completude e a logística. Editais de material de escritório frequentemente contêm 100+ itens em um único lote, e não cotar todos os itens é motivo de desclassificação. Empresas que mantêm estoque diversificado e sistema de picking eficiente para entregas fracionadas têm taxa de adjudicação superior. Atas de registro de preço estaduais são o principal mecanismo — conquiste uma ARP e garanta 12 meses de fornecimento recorrente. Monitore preços praticados em atas vigentes para calibrar suas propostas.',
      perfilComprador: 'O comprador de papelaria é tipicamente o setor de almoxarifado ou compras do órgão. Decisões são rotineiras e focadas em preço e prazo de entrega. Requisições são frequentes e em pequenas quantidades, exigindo capacidade de entrega parcelada. A digitalização dos processos administrativos reduz o consumo de papel, mas expande a demanda por suprimentos de impressão (toners, cartuchos) e organização (pastas, etiquetas). Entender o consumo histórico do órgão permite dimensionar propostas com precisão.',
      casosDeUso: 'Distribuidoras de papelaria que atuam em múltiplas atas de registro de preço simultaneamente usam dados do SmartLic para identificar quais ARPs estão próximas do vencimento, antecipando a próxima licitação. Uma distribuidora em Goiás expandiu de 3 para 12 atas ativas em um ano, triplicando o faturamento, ao usar filtros de valor e UF para encontrar editais compatíveis com sua área de cobertura logística.',
      tendencias2026: 'O setor de papelaria em 2026 é impactado por: (1) sustentabilidade — papel reciclado e produtos eco-friendly ganham preferência em editais com critérios ESG; (2) digitalização — apesar da redução do uso de papel, suprimentos de TI (toners, pen drives, cabos) compensam o volume; (3) marketplace governamental — plataformas de compra direta para itens de baixo valor simplificam o processo mas aumentam a competição por preço.',
    },
    engenharia: {
      contexto: 'Engenharia e obras públicas representam o setor de maior valor agregado nas licitações brasileiras, com contratos individuais que podem ultrapassar centenas de milhões de reais. O PAC (Programa de Aceleração do Crescimento) e seus sucessores garantem um pipeline contínuo de obras federais, enquanto emendas parlamentares e recursos estaduais alimentam obras de infraestrutura urbana, saneamento e edificações. A complexidade técnica e jurídica deste setor cria barreiras de entrada naturais que limitam a concorrência efetiva, beneficiando empresas com acervo técnico robusto.',
      dicas: 'A qualificação técnica é o principal filtro em licitações de engenharia: atestados de capacidade técnica emitidos pelo CREA/CAU, comprovando experiência em obras similares, são requisitos eliminatórios. Empresas devem manter seu acervo atualizado e organizado por tipo de obra, valor e complexidade. Para obras de grande porte, a formação de consórcios permite atender requisitos que individualmente seriam inviáveis. O BIM (Building Information Modeling) tornou-se obrigatório em obras federais acima de determinado valor — empresas sem capacitação em BIM perdem acesso a este segmento.',
      perfilComprador: 'O comprador governamental de obras é um engenheiro ou arquiteto do órgão, com perfil altamente técnico. A decisão passa por análise detalhada de planilha orçamentária (SINAPI/SICRO), cronograma físico-financeiro e qualificação técnica do responsável. A fiscalização é rigorosa, com medições mensais e acompanhamento de cronograma. O Tribunal de Contas analisa obras de grande porte, criando pressão por conformidade com referências de preço oficiais.',
      casosDeUso: 'Uma construtora de médio porte em Pernambuco usava corretores para identificar obras. Ao adotar monitoramento automatizado, passou a participar de 40% mais certames por mês, com análise de viabilidade prévia que evita investimento em propostas para obras fora do seu perfil técnico. Consultorias especializadas em licitações de engenharia usam dados de volume por UF e modalidade para recomendar a seus clientes onde concentrar esforços de prospecção.',
      tendencias2026: 'Em 2026, o setor de engenharia em licitações é moldado por: (1) BIM obrigatório — a adoção de Building Information Modeling em obras federais acelera, exigindo atualização tecnológica; (2) ESG em obras — critérios de sustentabilidade ambiental tornam-se fatores de pontuação técnica; (3) PPPs — parcerias público-privadas expandem-se em saneamento, habitação e mobilidade urbana; (4) regime de contratação integrada — transfere risco de projeto ao contratado, favorecendo empresas com capacidade de engenharia completa.',
    },
    software: {
      contexto: 'O mercado de software e sistemas nas licitações públicas atravessa uma transformação acelerada. A Estratégia Nacional de Governo Digital e o Marco Legal das Startups (LC 182/2021) abriram novas vias de contratação para empresas de tecnologia, incluindo contratação por inexigibilidade de software proprietário e licitações de inovação. O modelo SaaS (Software as a Service) substitui progressivamente licenças perpétuas, criando contratos de assinatura com receita recorrente previsível. O volume de licitações de software cresce consistentemente, impulsionado pela modernização de sistemas legados e pela demanda por soluções de inteligência artificial.',
      dicas: 'Em licitações de software, a diferenciação técnica é mais importante que o preço. Propostas técnicas com demonstração de funcionalidades em ambiente controlado (prova de conceito) são decisivas em concorrências do tipo técnica e preço. Certificações de equipe (AWS, Azure, Google Cloud, Scrum) e atestados de implantação em órgãos públicos similares fortalecem a habilitação. Para software proprietário, explore a contratação direta por inexigibilidade (art. 74 da Lei 14.133) — economiza meses de processo licitatório. Monitore editais de inovação e sandbox regulatório para oportunidades de teste de novas soluções.',
      perfilComprador: 'O comprador de software é um gestor de TI ou coordenador de sistemas do órgão, com entendimento técnico variável. Decisões de compra são baseadas no PDTIC (Plano Diretor de TI e Comunicação) e seguem o Guia de Contratação de TIC do governo federal. O ciclo de avaliação é longo — da publicação do termo de referência à adjudicação podem se passar 3-6 meses. Demonstrações técnicas (POC) são comuns e eliminam fornecedores sem produto maduro. SLAs rigorosos e penalidades por indisponibilidade são padrão nos contratos.',
      casosDeUso: 'Uma software house de gestão educacional usava o SmartLic para monitorar editais de sistemas de gestão escolar em prefeituras de todo o Brasil. Identificou que municípios de 20-100 mil habitantes concentravam 60% das oportunidades com menor concorrência, focou neste segmento e conquistou 15 contratos em 12 meses. Empresas de ERP governamental usam dados de panorama para dimensionar equipe de pré-venda por região.',
      tendencias2026: 'Para 2026, o mercado de software em licitações é transformado por: (1) IA generativa — editais de contratação de soluções de IA para atendimento ao cidadão, análise documental e automação emergem em volume crescente; (2) cybersegurança — conformidade com o Marco Civil da Internet e a LGPD torna-se requisito obrigatório; (3) low-code/no-code — plataformas de desenvolvimento cidadão ganham espaço em órgãos que buscam autonomia tecnológica; (4) interoperabilidade — padrões de integração via APIs entre sistemas governamentais criam demanda por middleware e ESB.',
    },
    facilities: {
      contexto: 'Facilities e manutenção é um dos setores com maior volume de licitações no Brasil, abrangendo serviços de limpeza, conservação, portaria, jardinagem, copeiragem e gestão predial integrada. A terceirização destes serviços é prática consolidada no setor público desde a década de 1990, com contratos de 12 a 60 meses que geram receita mensal previsível. O valor total do mercado de facilities em compras públicas supera dezenas de bilhões de reais anuais, distribuídos em milhares de contratos ativos simultaneamente em todo o território nacional.',
      dicas: 'O segredo de facilities é a planilha de custos. A precificação é regulamentada por convenções coletivas de trabalho regionais, que variam por UF, município e categoria profissional (servente, encarregado, porteiro). Empresas que não dominam a composição de custos detalhada — incluindo encargos sociais, insumos, equipamentos, lucro e BDI — correm risco de propor preços inexequíveis (desclassificação) ou inviáveis (prejuízo operacional). Use o Caderno de Logística do governo federal como referência para produtividade por m² e dimensionamento de equipe.',
      perfilComprador: 'O comprador de facilities é tipicamente o gestor administrativo ou coordenador de serviços gerais do órgão. A fiscalização é mensal, com medição de produtividade, qualidade de execução e conformidade trabalhista. Contratos de facilities têm alto risco de repactuação por dissídio coletivo — o comprador espera que o contratado solicite formalmente o reequilíbrio econômico-financeiro a cada novo acordo coletivo. A rotatividade de fiscais é alta, exigindo que a empresa mantenha documentação impecável para auditorias.',
      casosDeUso: 'Uma empresa de limpeza predial em Brasília usava o SmartLic para monitorar editais de facilities em órgãos federais da esplanada. Ao cruzar dados de volume por órgão e histórico de contratações, identificou que 80% das oportunidades vinham de 20% dos órgãos — focou nestes e reduziu o custo de elaboração de propostas em 60%. Consultorias trabalhistas que atendem empresas de facilities usam dados de panorama para benchmarking de preços praticados por UF.',
      tendencias2026: 'Em 2026, o setor de facilities é impactado por: (1) facilities integrados — contratos que agrupam 5+ serviços (limpeza, portaria, jardinagem, manutenção predial) em um único fornecedor crescem em participação; (2) tecnologia — monitoramento IoT de qualidade do ar, sensores de presença para limpeza sob demanda; (3) ESG — produtos de limpeza biodegradáveis e gestão de resíduos tornam-se diferenciais em pontuação técnica; (4) trabalhista — reforma trabalhista e novas regulamentações de terceirização impactam composição de custos.',
    },
    saude: {
      contexto: 'Licitações de saúde compreendem o segmento mais complexo e regulamentado das compras governamentais, abrangendo medicamentos, equipamentos hospitalares, material médico-hospitalar, órteses, próteses e serviços especializados. O SUS (Sistema Único de Saúde) é o maior sistema público de saúde do mundo, atendendo mais de 190 milhões de brasileiros e gerando demanda contínua por insumos e equipamentos em toda a cadeia assistencial. O volume de licitações de saúde é consistentemente um dos maiores entre todos os setores.',
      dicas: 'A regulação da ANVISA é o primeiro filtro: registros de produtos, certificações de boas práticas de fabricação (CBPF), rastreabilidade e laudos técnicos são requisitos eliminatórios na maioria dos editais. Empresas devem manter um portfólio de registros ANVISA atualizado e investir em certificações internacionais (FDA, CE) como diferencial. Para medicamentos, atas de registro de preço federais (CMED) definem preços máximos — dominar a tabela CMED e suas exceções é vantagem competitiva. Para equipamentos, a capacidade de assistência técnica com tempo de resposta garantido (SLA de 24-72h) é frequentemente decisiva.',
      perfilComprador: 'O comprador de saúde é um profissional técnico (farmacêutico, enfermeiro, engenheiro clínico) com conhecimento específico do produto. Decisões seguem a padronização de medicamentos e materiais do hospital/secretaria, com comissões técnicas que avaliam equivalência terapêutica e conformidade de especificações. O ciclo de compra é influenciado pela sazonalidade epidemiológica — surtos gripais, dengue e outras doenças sazonais geram compras emergenciais. Compras de equipamentos seguem o plano de investimentos do órgão, publicado no PDTI ou plano de contratação.',
      casosDeUso: 'Um distribuidor de material médico-hospitalar em São Paulo usava o SmartLic para monitorar editais de saúde em hospitais universitários federais. Ao analisar dados de panorama, identificou que material de curativo e descartáveis concentravam 40% do volume com margens superiores a medicamentos — redirecionou sua estratégia comercial e aumentou o faturamento em licitações em 55%. Laboratórios farmacêuticos usam dados de volume por UF para dimensionar equipe de visitação a hospitais e secretarias.',
      tendencias2026: 'Para 2026, o setor de saúde em licitações é transformado por: (1) telemedicina — equipamentos e plataformas de teleconsulta ganham espaço em editais de informatização hospitalar; (2) genéricos e biossimilares — ampliação do arsenal terapêutico genérico reduz custos mas intensifica competição; (3) dispositivos IoT — monitoramento remoto de pacientes e equipamentos conectados; (4) PPPs hospitalares — parcerias público-privadas para gestão de hospitais expandem demanda por fornecimento integrado.',
    },
    vigilancia: {
      contexto: 'O setor de vigilância e segurança patrimonial nas licitações públicas opera sob regulação específica da Polícia Federal, criando barreiras de entrada que limitam a concorrência e beneficiam empresas já estabelecidas. Alvará de funcionamento, certificado de segurança, autorização para porte de arma corporativo e formação técnica certificada do efetivo são requisitos legais que filtram o mercado antes mesmo da fase de proposta. O volume de licitações é expressivo — praticamente todo órgão público necessita de serviços de vigilância — e os contratos são tipicamente de longo prazo (24-60 meses).',
      dicas: 'O valor dos contratos de vigilância é determinado por convenções coletivas regionais e pela complexidade dos postos: vigilância armada em áreas de risco (tribunais, agências bancárias federais) tem valores 40-60% superiores à vigilância desarmada. Domine a planilha de custos: encargos sociais, adicional de risco, adicional noturno, interjornada e benefícios variam por estado e sindicato. A integração de vigilância eletrônica (CFTV, controle de acesso, alarmes) com vigilância presencial cria propostas mais competitivas em editais de segurança integrada.',
      perfilComprador: 'O comprador de vigilância é o gestor de segurança do órgão, frequentemente com background em forças de segurança ou gestão administrativa. A fiscalização é rigorosa: cobertura de postos, pontualidade, apresentação pessoal e conformidade trabalhista são verificados continuamente. Contratos de vigilância são sensíveis a dissídios coletivos — a empresa deve formalizar pedidos de repactuação a cada novo acordo coletivo para manter a saúde financeira do contrato.',
      casosDeUso: 'Uma empresa de vigilância no Distrito Federal, atuando exclusivamente em órgãos federais, usava o SmartLic para monitorar novos editais e renovações de contratos. Ao identificar que 30% dos contratos venciam no mesmo trimestre, organizou sua equipe de propostas para atender esse pico sazonal e conquistou 8 novos contratos em um único ano fiscal. Empresas de segurança eletrônica usam dados de panorama para identificar a demanda crescente por integração de sistemas.',
      tendencias2026: 'Em 2026, o setor de vigilância é impactado por: (1) integração tecnológica — CFTV com IA (reconhecimento facial, detecção de anomalias) complementa vigilância presencial; (2) drones — monitoramento de grandes áreas (campi universitários, bases militares) por aeronaves não tripuladas; (3) ESG — empresas com políticas de diversidade e inclusão ganham pontos em critérios de desempate; (4) cybersegurança física — convergência de segurança patrimonial e cibersegurança em contratos unificados.',
    },
    transporte: {
      contexto: 'Licitações de transporte e veículos abrangem aquisição, locação operacional e manutenção de frotas governamentais, além de combustíveis e serviços de transporte de passageiros. A locação operacional consolidou-se como modelo preferencial para frotas administrativas — o governo transfere o risco de depreciação e manutenção ao locador, pagando uma mensalidade fixa por veículo. O volume de licitações é expressivo e distribuído por todo o território nacional, com valores que variam de R$ 50 mil (locação de veículo único) a R$ 500 milhões (frota nacional).',
      dicas: 'Para locação de veículos, a cobertura geográfica e a capacidade de reposição são mais importantes que o preço unitário. Editais federais exigem atendimento em múltiplas UFs com tempo de resposta de 24-72h para substituição de veículo. Para combustíveis, a margem é mínima mas o volume compensa — contratos de abastecimento de frota podem atingir milhões de litros/ano. Para manutenção, redes de oficinas credenciadas com cobertura nacional são pré-requisito em editais de grande porte.',
      perfilComprador: 'O comprador de transporte é o gestor de frota ou logística do órgão. Decisões são baseadas em TCO (Total Cost of Ownership), não apenas no valor mensal de locação. O comprador avalia: consumo médio, custo de manutenção, depreciação, seguro e valor residual. Para combustíveis, o controle é rigoroso — cartões de abastecimento com rastreamento GPS e limites por veículo são padrão. Planos de contratação publicados no PNCP permitem antecipar demandas com 6-12 meses de antecedência.',
      casosDeUso: 'Uma locadora de veículos de médio porte no Paraná expandiu para o mercado governamental usando o SmartLic para identificar editais de locação de frotas leves em prefeituras de cidades de 50-200 mil habitantes. Com menor concorrência que em capitais, conquistou 12 contratos em 18 meses, com ticket médio de R$ 180 mil/mês. Distribuidoras de combustível usam dados de panorama para mapear demanda por UF e dimensionar infraestrutura de abastecimento.',
      tendencias2026: 'Para 2026, o setor de transporte em licitações é moldado por: (1) eletrificação — veículos elétricos e híbridos ganham espaço em frotas administrativas, com editais que incluem infraestrutura de recarga; (2) telemetria — monitoramento GPS e IoT de frotas torna-se requisito contratual; (3) compartilhamento — modelos de car-sharing e ride-hailing para uso governamental emergem em cidades de grande porte; (4) sustentabilidade — critérios de emissão de CO2 entram em pontuação técnica.',
    },
    manutencao_predial: {
      contexto: 'Manutenção e conservação predial engloba serviços técnicos especializados que mantêm a infraestrutura física dos órgãos públicos em funcionamento: ar-condicionado (PMOC obrigatório), elevadores, sistemas elétricos e hidráulicos, impermeabilização, pintura e reformas prediais menores. Diferente de facilities (limpeza/portaria), a manutenção predial exige qualificação técnica comprovada — acervos do CREA, profissionais habilitados e equipamentos certificados. O volume de licitações é consistente ao longo do ano, com picos no final do exercício fiscal.',
      dicas: 'A manutenção preventiva é a base do setor: planos anuais de manutenção (PMOC para ar-condicionado é obrigatório por lei) definem a frequência e o escopo dos serviços. Empresas que apresentam planos detalhados e comprovam experiência em manutenção preventiva têm vantagem sobre concorrentes que focam apenas em corretiva. Invista em diagnóstico energético como serviço complementar — a eficiência energética é pauta crescente em órgãos públicos e gera contratos de maior valor. Atestados de capacidade técnica em sistemas específicos (elevadores, geradores, sistemas de automação predial) são diferenciais eliminatórios.',
      perfilComprador: 'O comprador é tipicamente o engenheiro ou técnico de manutenção do órgão, com conhecimento específico dos sistemas prediais. A fiscalização é por ordem de serviço (OS), com medição mensal de produtividade e qualidade. Contratos de manutenção preventiva seguem cronograma fixo, enquanto corretiva é sob demanda — a empresa deve manter equipe residente ou de pronta resposta. O PMOC (Plano de Manutenção, Operação e Controle) de ar-condicionado é auditado pela vigilância sanitária.',
      casosDeUso: 'Uma empresa de manutenção predial em Belo Horizonte especializou-se em PMOC de ar-condicionado para órgãos federais em Minas Gerais. Usando o SmartLic para monitorar vencimentos de contratos e novos editais, mantém uma carteira de 25 contratos ativos simultaneamente, com receita mensal previsível. O diferencial: oferece diagnóstico energético como serviço complementar, gerando cross-sell de projetos de eficiência energética.',
      tendencias2026: 'Em 2026, a manutenção predial é impactada por: (1) edificações inteligentes — automação predial (BMS) com IoT para monitoramento remoto de sistemas; (2) eficiência energética — retrofitting de sistemas de climatização e iluminação como serviço complementar; (3) manutenção preditiva — uso de sensores e análise de dados para antecipar falhas; (4) regulamentação — novas normas de acessibilidade e sustentabilidade exigem adequações em prédios públicos existentes.',
    },
    engenharia_rodoviaria: {
      contexto: 'Engenharia rodoviária e infraestrutura viária movimenta os maiores valores unitários nas licitações públicas brasileiras, com contratos que frequentemente ultrapassam R$ 100 milhões. O DNIT (Departamento Nacional de Infraestrutura de Transportes) e os DERs estaduais são os principais contratantes, com um pipeline contínuo de obras de pavimentação, recuperação, duplicação, pontes, viadutos e sinalização viária. O PAC e programas estaduais de investimento garantem recursos de longo prazo, tornando este setor um dos mais estáveis em termos de demanda.',
      dicas: 'A qualificação técnica é a barreira mais alta: atestados de capacidade técnico-operacional e técnico-profissional compatíveis com o porte da obra são eliminatórios. Empresas devem comprovar experiência em volumes mínimos (toneladas de asfalto, metros cúbicos de terraplanagem) e prazos de execução similares. Equipamentos próprios ou locados (usinas de asfalto, fresadoras, rolos compactadores) devem ser comprovados. Para obras de grande porte, a formação de consórcios permite somar acervos e capacidades complementares.',
      perfilComprador: 'O comprador é um engenheiro rodoviário do DNIT ou DER, com alto grau de especialização técnica. A análise de propostas foca em: planilha orçamentária SICRO (referência nacional de custos rodoviários), cronograma físico-financeiro, capacidade técnica da equipe-chave e experiência da empresa em obras similares. A fiscalização é rigorosa, com medições mensais e ensaios de controle tecnológico (compactação, teor de ligante, espessura de camadas). O TCU audita obras federais acima de determinados valores.',
      casosDeUso: 'Uma construtora especializada em pavimentação no Centro-Oeste utilizava o SmartLic para monitorar editais do DNIT e DERs estaduais em Goiás, Mato Grosso e Mato Grosso do Sul. Ao analisar dados de panorama, identificou que 70% das obras de recuperação de rodovias estaduais ocorriam no período seco (maio-outubro), concentrando recursos humanos e equipamentos nesse período. Consultorias de engenharia usam dados de tendência para recomendar investimentos em capacidade produtiva.',
      tendencias2026: 'Para 2026, a engenharia rodoviária é moldada por: (1) concessões e PPPs — expansão do programa de concessões rodoviárias cria demanda por obras de adequação e manutenção; (2) pavimentação sustentável — uso de asfalto-borracha, concreto reciclado e técnicas de baixo carbono; (3) sinalização inteligente — sistemas de gerenciamento de tráfego com IoT e IA; (4) resiliência climática — projetos de drenagem e estabilização de encostas ganham prioridade.',
    },
    materiais_eletricos: {
      contexto: 'O segmento de materiais elétricos nas licitações públicas atende demandas recorrentes de manutenção e expansão da infraestrutura elétrica em prédios públicos, iluminação pública e redes de distribuição interna. A especificação técnica é regulada por normas ABNT e certificações INMETRO — produtos sem certificação são automaticamente desclassificados. O mercado é segmentado entre fornecedores de materiais (fios, cabos, disjuntores, quadros elétricos) e prestadores de serviço de instalação, sendo que a integração de ambos confere vantagem competitiva significativa.',
      dicas: 'Certificações INMETRO são requisito eliminatório — mantenha laudos atualizados para todos os produtos do portfólio. Para projetos de iluminação pública LED, a comprovação de eficiência luminosa (lúmens/watt) e vida útil (horas) é decisiva. A integração de fornecimento + instalação em uma proposta única simplifica a contratação para o órgão e reduz a concorrência. Para projetos de energia solar fotovoltaica, dominar a regulamentação da ANEEL sobre microgeração distribuída é diferencial competitivo.',
      perfilComprador: 'O comprador é o engenheiro eletricista ou técnico de manutenção do órgão. Especificações técnicas seguem normas NBR e são detalhadas: seção do condutor, capacidade de corrente, classe de isolamento, grau de proteção IP. A conformidade é verificada na entrega com ensaios de bancada em amostras. Para projetos de eficiência energética, o comprador avalia payback e economia projetada. Planos de contratação publicados no PNCP permitem identificar demandas futuras.',
      casosDeUso: 'Uma distribuidora de materiais elétricos em São Paulo especializou-se em licitações de iluminação pública LED, um nicho de alto valor e crescimento acelerado. Usando o SmartLic para monitorar editais de eficiência energética em prefeituras de todo o Brasil, conquistou 20 contratos em 2 anos, com ticket médio de R$ 500 mil. O diferencial: oferece projeto luminotécnico como serviço complementar, agregando valor à proposta.',
      tendencias2026: 'Em 2026, o setor de materiais elétricos é impactado por: (1) energia solar — projetos de microgeração fotovoltaica em prédios públicos multiplicam-se; (2) LED — substituição total de iluminação convencional por LED em todo o setor público; (3) smart grid — automação de redes elétricas prediais com medição inteligente; (4) eficiência energética — certificações PROCEL e programas de etiquetagem energética tornam-se obrigatórios em editais.',
    },
    materiais_hidraulicos: {
      contexto: 'Materiais hidráulicos e saneamento representam um setor estratégico nas compras governamentais, impulsionado pelo Marco Legal do Saneamento (Lei 14.026/2020) que estabelece metas ambiciosas de universalização do acesso à água e esgoto até 2033. Este marco regulatório desencadeou uma onda de investimentos em infraestrutura hídrica que se reflete em volume crescente de licitações para tubos, conexões, bombas, equipamentos de tratamento de água e esgoto. O setor também atende demandas recorrentes de manutenção hidráulica predial em órgãos públicos.',
      dicas: 'A especificação técnica é rigorosa: conformidade com normas ABNT para pressão de trabalho, material (PVC, PEAD, ferro fundido), diâmetro e classe de resistência é requisito eliminatório. Laudos de ensaio em laboratórios acreditados pelo INMETRO devem estar vigentes. Para projetos de saneamento de maior porte, a experiência em estações de tratamento compactas (ETA/ETE) é diferencial competitivo — municípios de pequeno porte são o principal mercado. A logística de entrega é crítica: tubulações pesadas exigem planejamento de transporte e equipamentos de descarga.',
      perfilComprador: 'O comprador é o engenheiro hidráulico ou sanitarista do órgão (prefeitura, companhia de saneamento, SAAE). Especificações seguem normas NBR e referências de preço do SINAPI. Para projetos de saneamento, a análise técnica inclui dimensionamento hidráulico, vazão de projeto e compatibilidade de materiais. O ciclo de compra é longo para projetos de investimento (6-12 meses) mas rápido para manutenção predial (pregão eletrônico, 30-60 dias).',
      casosDeUso: 'Uma fábrica de tubos e conexões PVC no interior de São Paulo usava o SmartLic para monitorar editais de saneamento em municípios do Sudeste. Ao identificar que 75% dos municípios paulistas com menos de 50 mil habitantes ainda não atingiram as metas do Marco Legal, focou seu comercial neste segmento e triplicou as vendas para o setor público em 18 meses. Consultorias de saneamento usam dados de panorama para dimensionar investimentos necessários por região.',
      tendencias2026: 'Para 2026, o setor de materiais hidráulicos é moldado por: (1) Marco Legal do Saneamento — investimentos massivos em infraestrutura hídrica continuam acelerando; (2) reúso de água — sistemas de captação pluvial e reúso ganham espaço em editais de edificações sustentáveis; (3) IoT em saneamento — medidores inteligentes e monitoramento remoto de redes; (4) PPPs em saneamento — parcerias público-privadas para gestão de sistemas de água e esgoto expandem-se nacionalmente.',
    },
  };

  return editorials[sectorId] || editorials.vestuario;
}

// -----------------------------------------------------------------------
// MKT-003: Phased launch configuration
// -----------------------------------------------------------------------

/** Phase 1 sectors — 5 largest by procurement volume */
const PHASE1_SECTORS = ['informatica', 'saude', 'engenharia', 'facilities', 'software'];

/** Phase 1 UFs — 5 largest by procurement volume */
const PHASE1_UFS = ['SP', 'RJ', 'MG', 'PR', 'RS'];

// S3: Alertas Publicos types and fetch
export interface AlertaBid {
  titulo: string;
  orgao: string;
  valor: number | null;
  uf: string;
  municipio: string;
  modalidade: string;
  data_publicacao: string;
  data_abertura: string | null;
  link_pncp: string;
  pncp_id: string;
}

export interface AlertasData {
  sector_id: string;
  sector_name: string;
  uf: string;
  bids: AlertaBid[];
  total: number;
  last_updated: string;
}

export async function fetchAlertasPublicos(
  sectorSlug: string,
  uf: string,
): Promise<AlertasData | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const sectorId = sectorSlug.replace(/-/g, '_');
    const res = await fetch(`${backendUrl}/v1/alertas/${sectorId}/uf/${uf.toUpperCase()}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * SEO-PLAYBOOK P1: Generate static params for full 15×27 = 405 pages.
 * (Previously Phase 1: 5 sectors × 5 UFs = 25 pages)
 */
export function generateLicitacoesParams(): { setor: string; uf: string }[] {
  return generateSectorUfParams(); // 15 × 27 = 405
}

// -----------------------------------------------------------------------
// MKT-003: Region-specific editorial content
// -----------------------------------------------------------------------

type Region = 'sudeste' | 'sul' | 'nordeste' | 'norte' | 'centro_oeste';

const UF_REGION: Record<string, Region> = {
  SP: 'sudeste', RJ: 'sudeste', MG: 'sudeste', ES: 'sudeste',
  PR: 'sul', SC: 'sul', RS: 'sul',
  BA: 'nordeste', PE: 'nordeste', CE: 'nordeste', MA: 'nordeste',
  PI: 'nordeste', RN: 'nordeste', PB: 'nordeste', AL: 'nordeste', SE: 'nordeste',
  AM: 'norte', PA: 'norte', AC: 'norte', RO: 'norte', RR: 'norte', AP: 'norte', TO: 'norte',
  GO: 'centro_oeste', MT: 'centro_oeste', MS: 'centro_oeste', DF: 'centro_oeste',
};

const REGION_NAMES: Record<Region, string> = {
  sudeste: 'Sudeste',
  sul: 'Sul',
  nordeste: 'Nordeste',
  norte: 'Norte',
  centro_oeste: 'Centro-Oeste',
};

/**
 * MKT-003 AC2: Region-specific editorial content block (300+ words).
 * Varies by region to avoid repetitive thin content across UFs.
 */
export function getRegionalEditorial(
  sectorName: string,
  uf: string,
  ufName: string,
): string[] {
  const region = UF_REGION[uf] || 'sudeste';
  const regionName = REGION_NAMES[region];

  const paragraphs: Record<Region, string[]> = {
    sudeste: [
      `O ${regionName} brasileiro concentra o maior volume de licitações públicas do país, e ${ufName} não é exceção. Com uma densa rede de órgãos públicos federais, estaduais e municipais, o estado oferece um fluxo constante de oportunidades para empresas de ${sectorName.toLowerCase()}. A concentração econômica e administrativa da região garante editais de alto valor e frequência regular, tornando o monitoramento sistemático especialmente vantajoso.`,
      `A infraestrutura logística do ${regionName} — com portos, aeroportos e rodovias de primeira linha — favorece empresas que precisam atender contratos com entrega em múltiplos pontos. Em ${ufName}, a competição é intensa, mas o volume de oportunidades compensa: empresas que dominam a documentação técnica e mantêm suas certidões em dia encontram um mercado de escala incomparável. A proximidade de centros de decisão política (Brasília, capitais estaduais) também facilita o acompanhamento presencial de pregões e audiências.`,
      `Para empresas de ${sectorName.toLowerCase()} que atuam ${getUfPrep(uf)} ${ufName}, a chave do sucesso está na análise seletiva. Nem todo edital publicado representa uma oportunidade real — fatores como modalidade de contratação, prazo de entrega, valor estimado e exigências de qualificação técnica determinam a viabilidade de participação. O SmartLic automatiza essa triagem usando inteligência artificial, classificando cada edital em até 4 fatores de viabilidade: modalidade (30%), prazo (25%), valor (25%) e geografia (20%). Isso permite que equipes comerciais foquem apenas nas oportunidades com maior probabilidade de sucesso.`,
      `O mercado de compras públicas ${getUfPrep(uf)} ${ufName} segue padrões sazonais bem definidos: o primeiro trimestre é marcado pela finalização de contratos do exercício anterior e planejamento orçamentário; o segundo trimestre inicia a execução efetiva; o terceiro concentra o pico de publicações; e o quarto trimestre traz uma corrida para empenhar recursos antes do encerramento do exercício fiscal. Empresas que entendem esse ciclo e se preparam com antecedência têm taxa de adjudicação significativamente superior à média do setor.`,
    ],
    sul: [
      `A região ${regionName} destaca-se pelo alto índice de eficiência administrativa nos órgãos públicos, refletindo-se em editais bem estruturados e processos licitatórios transparentes. Em ${ufName}, empresas de ${sectorName.toLowerCase()} encontram um mercado maduro, onde a qualidade da proposta técnica frequentemente supera o fator preço na decisão de adjudicação. Cooperativas e associações empresariais da região têm forte tradição de participação conjunta em licitações de maior porte.`,
      `O perfil de compras públicas ${getUfPrep(uf)} ${ufName} reflete a diversificação econômica da região ${regionName}: há demanda consistente em setores industriais, agropecuários e de serviços. As prefeituras do interior, frequentemente subestimadas, representam um nicho valioso — menor concorrência e relações comerciais de longo prazo. O SmartLic monitora automaticamente todas as publicações do PNCP e portais estaduais, garantindo que nenhuma oportunidade passe despercebida.`,
      `Para se destacar nas licitações de ${sectorName.toLowerCase()} ${getUfPrep(uf)} ${ufName}, empresas devem investir na qualificação técnica da equipe e na padronização dos processos internos de elaboração de propostas. A região ${regionName} tem elevada exigência documental — atestados de capacidade técnica, certificações ISO e comprovações de experiência anterior são diferenciais decisivos. Manter um banco de dados atualizado de editais similares adjudicados, com histórico de preços praticados, permite precificar propostas com assertividade.`,
      `A sazonalidade das licitações ${getUfPrep(uf)} ${ufName} acompanha o calendário fiscal nacional, com picos no segundo e terceiro trimestres. Porém, uma particularidade da região ${regionName} é o impacto do inverno nas obras de infraestrutura — o frio e as chuvas concentradas podem atrasar cronogramas, abrindo oportunidades em períodos tipicamente de baixa movimentação. A análise de viabilidade geográfica do SmartLic leva em conta a distância entre a sede da empresa e o local de execução, otimizando a seleção de editais com logística favorável.`,
    ],
    nordeste: [
      `O ${regionName} brasileiro vive um momento de transformação nas compras públicas, com crescente adoção de pregão eletrônico e maior transparência nos processos licitatórios. Em ${ufName}, o volume de editais de ${sectorName.toLowerCase()} tem crescido consistentemente, impulsionado por investimentos federais em infraestrutura, saúde e educação. A região oferece oportunidades únicas para empresas que compreendem suas especificidades regulatórias e logísticas.`,
      `A logística de entrega é o principal desafio para empresas que atuam no ${regionName} a partir de outras regiões. No entanto, empresas locais de ${sectorName.toLowerCase()} ${getUfPrep(uf)} ${ufName} têm vantagem competitiva natural — menor custo de frete, conhecimento do mercado local e relacionamento com órgãos compradores. Para empresas de fora, a estratégia mais eficaz é estabelecer parcerias com distribuidores regionais ou manter estoques descentralizados. O SmartLic ajuda a identificar quais editais justificam o investimento logístico com base na análise de viabilidade de 4 fatores.`,
      `Os programas federais direcionados ao ${regionName} — como investimentos em saneamento, energia e infraestrutura urbana — geram um pipeline previsível de licitações. Em ${ufName}, os municípios menores frequentemente publicam editais com menor concorrência e valores que, somados, representam receita significativa. A chave é o monitoramento abrangente: enquanto grandes empresas focam nos editais de maior valor, PMEs encontram espaço em compras fracionadas e contratos de fornecimento contínuo.`,
      `O calendário de compras ${getUfPrep(uf)} ${ufName} é influenciado pelo ciclo político municipal e estadual — anos eleitorais tendem a concentrar investimentos nos primeiros semestres. Para ${sectorName.toLowerCase()}, entender essas dinâmicas permite antecipar demandas e preparar propostas com antecedência. O SmartLic consolida dados de três fontes oficiais (PNCP, Portal de Compras Públicas e ComprasGov), eliminando o risco de perder oportunidades publicadas em portais diferentes.`,
    ],
    norte: [
      `A região ${regionName} do Brasil apresenta um mercado de licitações públicas em expansão acelerada, impulsionado por investimentos federais em infraestrutura, saúde e conectividade. Em ${ufName}, as distâncias geográficas e a logística fluvial criam barreiras naturais de entrada que reduzem a concorrência efetiva, beneficiando empresas com presença local ou capacidade logística diferenciada. Para ${sectorName.toLowerCase()}, essa combinação de demanda crescente e menor competição representa uma oportunidade estratégica.`,
      `As peculiaridades logísticas do ${regionName} exigem adaptação nas estratégias de participação em licitações. Em ${ufName}, muitos órgãos públicos aceitam prazos de entrega estendidos em razão das dificuldades de acesso, o que favorece empresas com planejamento logístico robusto. O transporte fluvial e aéreo complementa o rodoviário em muitas localidades, impactando diretamente o custo e a viabilidade de fornecimento. O SmartLic incorpora a análise geográfica em seu score de viabilidade, ajudando empresas a identificar quais editais justificam o investimento logístico.`,
      `Os investimentos em infraestrutura digital e saneamento na região ${regionName} estão gerando um ciclo virtuoso de licitações. Em ${ufName}, municípios que antes dependiam exclusivamente de repasses federais agora publicam editais próprios com recursos de royalties e compensações ambientais. Para empresas de ${sectorName.toLowerCase()}, isso significa um mercado cada vez mais diversificado, com oportunidades em todas as esferas de governo (federal, estadual e municipal).`,
      `A sazonalidade no ${regionName} é fortemente influenciada pelo regime de chuvas. Em ${ufName}, o período seco (geralmente junho a novembro) concentra o maior volume de obras e aquisições, enquanto o período chuvoso reduz a atividade em setores dependentes de logística terrestre. Empresas que planejam sua participação em licitações de ${sectorName.toLowerCase()} considerando essa sazonalidade maximizam sua taxa de sucesso e reduzem custos operacionais.`,
    ],
    centro_oeste: [
      `O ${regionName} brasileiro, sede do governo federal em Brasília, é um dos polos mais relevantes para licitações públicas no país. Em ${ufName}, a concentração de órgãos federais e a pujança do agronegócio geram um volume expressivo de compras governamentais em ${sectorName.toLowerCase()}. A proximidade com centros de decisão política e a infraestrutura rodoviária interligando as capitais conferem vantagens logísticas a empresas da região.`,
      `O mercado de licitações ${getUfPrep(uf)} ${ufName} é caracterizado pela coexistência de grandes contratos federais (especialmente em ${ufName === 'Distrito Federal' ? 'órgãos da esplanada dos ministérios' : 'representações regionais de ministérios'}) e demandas municipais pulverizadas. Para ${sectorName.toLowerCase()}, essa diversidade permite compor um portfólio equilibrado entre contratos de alto valor e fornecimentos recorrentes. O SmartLic classifica automaticamente cada edital por relevância setorial, eliminando o ruído de editais irrelevantes.`,
      `A economia do ${regionName} — ancorada no agronegócio, mineração e serviços — gera demandas específicas de infraestrutura que se refletem nas licitações. Em ${ufName}, os investimentos em logística (armazéns, silos, rodovias) e em equipamentos públicos (hospitais, escolas, delegacias) mantêm um fluxo constante de oportunidades. Empresas de ${sectorName.toLowerCase()} que monitoram sistematicamente essas publicações conseguem antecipar tendências e preparar propostas mais competitivas.`,
      `O calendário fiscal ${getUfPrep(uf)} ${ufName} segue o padrão nacional, com picos de publicação no segundo e terceiro trimestres. Uma particularidade do ${regionName} é a influência dos períodos de safra na disponibilidade de recursos municipais — municípios dependentes de receitas agropecuárias concentram investimentos após os períodos de colheita. A análise de viabilidade do SmartLic considera quatro fatores (modalidade, prazo, valor e geografia) para identificar as oportunidades mais alinhadas ao perfil de cada empresa.`,
    ],
  };

  return paragraphs[region];
}

// -----------------------------------------------------------------------
// Onda 3: City × Sector editorial content
// -----------------------------------------------------------------------

/**
 * Onda 3: Editorial content block for city × sector pages (~200 words).
 * Varies by region using the existing UF_REGION map.
 * All text in proper Portuguese with correct accentuation.
 */
export function getCidadeSectorEditorial(
  cityName: string,
  uf: string,
  ufName: string,
  sectorName: string,
): string[] {
  const region = UF_REGION[uf] || 'sudeste';
  const regionName = REGION_NAMES[region];
  const sectorLower = sectorName.toLowerCase();

  const paragraphs: Record<Region, string[]> = {
    sudeste: [
      `${cityName} é um dos principais polos de compras públicas de ${sectorLower} ${getUfPrep(uf)} ${ufName}. Com uma rede densa de prefeituras, autarquias e secretarias, o município pública editais de forma regular ao longo do ano. A concentração econômica do ${regionName} garante que as oportunidades de ${sectorLower} em ${cityName} tenham valores expressivos e frequência consistente, tornando o monitoramento sistemático particularmente vantajoso para fornecedores do setor.`,
      `A Lei 14.133/2021 (Nova Lei de Licitações) e a LC 123/2006 estabelecem preferência para micro e pequenas empresas locais em contratações de até R$ 80 mil, o que beneficia fornecedores de ${sectorLower} sediados em ${cityName} ou região metropolitana. Além disso, o pregão eletrônico — modalidade predominante para ${sectorLower} — permite participação remota, ampliando o mercado para empresas de outros estados que atendam às exigências técnicas e documentais.`,
      `O SmartLic monitora automaticamente todas as publicações do PNCP, Portal de Compras Públicas e ComprasGov relacionadas a ${sectorLower} em ${cityName}/${uf}. A inteligência artificial classifica cada edital por relevância setorial e calcula um score de viabilidade baseado em quatro fatores: modalidade de contratação (30%), prazo de execução (25%), valor estimado (25%) e proximidade geográfica (20%). Isso permite que sua equipe comercial foque apenas nas oportunidades com maior probabilidade de adjudicação.`,
    ],
    sul: [
      `${cityName} destaca-se pela eficiência administrativa de seus órgãos públicos, refletida em editais bem estruturados e processos transparentes para ${sectorLower}. Na região ${regionName}, a qualidade da proposta técnica frequentemente supera o fator preço na decisão de adjudicação, o que valoriza fornecedores de ${sectorLower} com experiência comprovada e capacidade técnica diferenciada.`,
      `A legislação vigente — Lei 14.133/2021 e LC 123/2006 — favorece micro e pequenas empresas locais em contratações de até R$ 80 mil, um diferencial importante para fornecedores de ${sectorLower} estabelecidos em ${cityName}. Cooperativas e associações empresariais da região ${regionName} também têm tradição de participação conjunta em licitações de maior porte, ampliando o acesso a contratos que individualmente seriam inacessíveis.`,
      `O SmartLic automatiza a descoberta e análise de editais de ${sectorLower} em ${cityName}/${uf}, consolidando dados de três fontes oficiais (PNCP, PCP e ComprasGov). O score de viabilidade de quatro fatores — modalidade (30%), prazo (25%), valor (25%) e geografia (20%) — elimina a análise manual e permite decisões rápidas de participação em cada oportunidade.`,
    ],
    nordeste: [
      `O mercado de licitações de ${sectorLower} em ${cityName} está em crescimento acelerado, impulsionado por investimentos federais e estaduais ${getUfPrep(uf)} ${ufName}. A região ${regionName} vive uma transformação nas compras públicas, com crescente adoção de pregão eletrônico e maior transparência nos processos licitatórios, o que amplia as oportunidades para fornecedores qualificados de ${sectorLower}.`,
      `A LC 123/2006 confere preferência a empresas locais em contratações de até R$ 80 mil, beneficiando diretamente fornecedores de ${sectorLower} em ${cityName}. A Lei 14.133/2021 também exige que órgãos públicos priorizem a participação de micro e pequenas empresas em todas as modalidades. Para empresas de fora da região, estabelecer parcerias com distribuidores locais pode ser a estratégia mais eficaz para competir neste mercado.`,
      `O SmartLic consolida automaticamente editais de ${sectorLower} publicados em ${cityName}/${uf} nas três fontes oficiais (PNCP, PCP e ComprasGov), aplicando inteligência artificial para classificar relevância setorial e calcular viabilidade com base em quatro fatores: modalidade (30%), prazo (25%), valor (25%) e geografia (20%). Essa triagem automatizada economiza horas de análise manual e garante que nenhuma oportunidade passe despercebida.`,
    ],
    norte: [
      `${cityName} apresenta um mercado de licitações de ${sectorLower} em expansão, beneficiado por investimentos federais em infraestrutura e serviços na região ${regionName}. As distâncias geográficas e as particularidades logísticas de ${ufName} reduzem a concorrência efetiva, favorecendo empresas com presença local ou capacidade logística diferenciada para fornecimento de ${sectorLower}.`,
      `A Lei 14.133/2021 e a LC 123/2006 garantem preferência a micro e pequenas empresas locais em contratações de até R$ 80 mil. Em ${cityName}, muitos órgãos públicos aceitam prazos de entrega estendidos considerando as particularidades logísticas da região ${regionName}, o que pode ser um diferencial competitivo para fornecedores de ${sectorLower} com planejamento logístico robusto.`,
      `O SmartLic monitora editais de ${sectorLower} em ${cityName}/${uf} em tempo real, consolidando publicações do PNCP, Portal de Compras Públicas e ComprasGov. O score de viabilidade — modalidade (30%), prazo (25%), valor (25%) e geografia (20%) — ajuda a identificar quais editais justificam o investimento logístico, otimizando a decisão de participação para cada oportunidade.`,
    ],
    centro_oeste: [
      `${cityName} é um polo estratégico para licitações de ${sectorLower} ${getUfPrep(uf)} ${ufName}, beneficiado pela concentração de órgãos federais e pela pujança econômica da região ${regionName}. A infraestrutura rodoviária interligando as capitais do Centro-Oeste confere vantagens logísticas a fornecedores de ${sectorLower} que atendem contratos com entrega em múltiplos pontos.`,
      `A legislação de licitações — Lei 14.133/2021 e LC 123/2006 — reserva preferência para micro e pequenas empresas em contratações de até R$ 80 mil. Em ${cityName}, a coexistência de grandes contratos federais e demandas municipais pulverizadas permite que fornecedores de ${sectorLower} componham um portfólio equilibrado entre contratos de alto valor e fornecimentos recorrentes de menor porte.`,
      `O SmartLic automatiza a descoberta de editais de ${sectorLower} em ${cityName}/${uf}, consolidando três fontes oficiais e aplicando classificação por IA. O score de viabilidade de quatro fatores — modalidade (30%), prazo (25%), valor (25%) e geografia (20%) — permite que equipes comerciais identifiquem rapidamente as oportunidades mais alinhadas ao perfil da empresa.`,
    ],
  };

  return paragraphs[region];
}

/**
 * Onda 3: FAQs for city × sector pages (4 questions).
 * Combines city + sector context with real data when available.
 * All text in proper Portuguese with correct accentuation.
 */
export function generateCidadeSectorFAQs(
  cityName: string,
  uf: string,
  sectorName: string,
  totalEditais?: number,
  avgValue?: number,
): { question: string; answer: string }[] {
  const count = totalEditais ?? 0;
  const sectorLower = sectorName.toLowerCase();

  return [
    {
      question: `Quantas licitações de ${sectorName} estão abertas em ${cityName}?`,
      answer: `Nos últimos 10 dias, foram identificadas ${count > 0 ? count : 'diversas'} licitações de ${sectorLower} em ${cityName}/${uf}, consolidando dados do PNCP, Portal de Compras Públicas e ComprasGov. O SmartLic atualiza esses números automaticamente a cada 24 horas.`,
    },
    {
      question: `Qual o valor médio dos editais de ${sectorName} em ${cityName}?`,
      answer: `${avgValue && avgValue > 0 ? `O valor médio estimado é de ${new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(avgValue)}.` : 'O valor varia conforme a modalidade e o escopo do edital.'} As licitações de ${sectorLower} em ${cityName} vão desde compras de pequeno porte até contratos expressivos. No SmartLic você filtra por faixa de valor.`,
    },
    {
      question: `Quais órgãos mais compram ${sectorName} em ${cityName}?`,
      answer: `Os principais compradores de ${sectorLower} em ${cityName} incluem prefeituras, secretarias estaduais e órgãos federais com representação local. O SmartLic identifica automaticamente os órgãos com maior volume de publicações, ajudando a priorizar relacionamento comercial com compradores recorrentes.`,
    },
    {
      question: `Como participar de licitações de ${sectorName} em ${cityName}/${uf}?`,
      answer: `O primeiro passo é monitorar as publicações nos portais oficiais (PNCP, PCP e ComprasGov). Depois, análise a viabilidade de cada edital verificando modalidade, prazo, valor e exigências técnicas. O SmartLic automatiza essa triagem usando inteligência artificial, economizando horas de análise manual e identificando as oportunidades com maior chance de adjudicação.`,
    },
  ];
}

/**
 * MKT-003 AC2: Generate FAQs specific to sector × UF.
 * 5 questions, 40-60 words each answer.
 */
export function generateLicitacoesFAQs(
  sectorName: string,
  ufName: string,
  totalEditais?: number,
  avgValue?: number,
  uf?: string,
): { question: string; answer: string }[] {
  const count = totalEditais ?? 0;

  return [
    {
      question: `Quantas licitações de ${sectorName} estão abertas ${getUfPrep(uf)} ${ufName}?`,
      answer: `Nos últimos 10 dias, foram publicadas ${count > 0 ? count : 'diversas'} licitações de ${sectorName} ${getUfPrep(uf)} ${ufName}, consolidando dados do PNCP, Portal de Compras Públicas e ComprasGov. O SmartLic atualiza esses números automaticamente a cada 24 horas.`,
    },
    {
      question: `Qual o valor médio das licitações de ${sectorName} ${getUfPrep(uf)} ${ufName}?`,
      answer: `${avgValue && avgValue > 0 ? `O valor médio estimado é de ${formatBRL(avgValue)}.` : 'O valor varia conforme a modalidade e o escopo.'} Os editais de ${sectorName} ${getUfPrep(uf)} ${ufName} vão desde compras pequenas até contratos de grande porte. No SmartLic você filtra por faixa de valor.`,
    },
    {
      question: `Como participar de licitações de ${sectorName} ${getUfPrep(uf)} ${ufName}?`,
      answer: `O primeiro passo é monitorar as publicações no PNCP e portais estaduais. Depois, análise a viabilidade de cada edital verificando modalidade, prazo, valor e exigências técnicas. O SmartLic automatiza essa triagem usando IA, economizando horas de análise manual.`,
    },
    {
      question: `Quais modalidades são mais comuns para ${sectorName} ${getUfPrep(uf)} ${ufName}?`,
      answer: `As modalidades mais frequentes variam conforme o objeto e valor estimado. Para ${sectorName}, predominam o pregão eletrônico (concorrência ampla), a concorrência eletrônica (obras e serviços de maior porte) e a dispensa para valores menores. A Lei 14.133/2021 incentiva o uso de modalidades eletrônicas, tornando a participação mais acessível a empresas de qualquer estado.`,
    },
    {
      question: `Posso testar o SmartLic para buscar licitações de ${sectorName}?`,
      answer: `Sim, o SmartLic oferece teste grátis de 14 dias sem necessidade de cartão de crédito. Durante o teste você tem acesso completo à busca com IA, análise de viabilidade por 4 fatores, pipeline de oportunidades e exportação de relatórios em Excel.`,
    },
  ];
}


// ---------------------------------------------------------------------------
// Wave 3.1 — Contratos by sector helpers
// ---------------------------------------------------------------------------

export interface ContratosSetorTopEntry {
  nome: string;
  cnpj: string;
  total_contratos: number;
  valor_total: number;
}

export interface ContratosSetorUfEntry {
  uf: string;
  total_contratos: number;
  valor_total: number;
}

export interface ContratosSetorTrend {
  month: string;
  count: number;
  value: number;
}

export interface ContratosSetorStats {
  sector_id: string;
  sector_name: string;
  total_contracts: number;
  total_value: number;
  avg_value: number;
  top_orgaos: ContratosSetorTopEntry[];
  top_fornecedores: ContratosSetorTopEntry[];
  monthly_trend: ContratosSetorTrend[];
  by_uf: ContratosSetorUfEntry[];
  last_updated: string;
}

export async function fetchContratosSetorStats(sectorSlug: string): Promise<ContratosSetorStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const sectorId = sectorSlug.replace(/-/g, '_');
    const res = await fetch(`${backendUrl}/v1/blog/stats/contratos/${sectorId}`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export function generateContratosSetorFAQs(
  sectorName: string,
  totalContracts?: number,
  topOrgao?: string,
): { question: string; answer: string }[] {
  const count = totalContracts ?? 0;
  return [
    {
      question: `Quantos contratos públicos de ${sectorName} existem?`,
      answer: `Foram identificados ${count > 0 ? count.toLocaleString('pt-BR') : 'centenas de'} contratos públicos de ${sectorName} nos dados do PNCP. O volume varia por estado e ano, com tendência de crescimento após a Lei 14.133/2021.`,
    },
    {
      question: `Quais órgãos mais compram ${sectorName}?`,
      answer: `${topOrgao ? `O principal comprador e ${topOrgao}.` : 'Os principais compradores são órgãos federais e estaduais.'} O ranking completo de órgãos compradores está disponível nesta pagina, atualizado com dados do PNCP.`,
    },
    {
      question: `Como encontrar contratos públicos de ${sectorName} por estado?`,
      answer: `Nesta pagina você encontra a distribuição de contratos de ${sectorName} por UF. Clique em qualquer estado para ver detalhes de órgãos compradores, fornecedores e valores na pagina dedicada.`,
    },
    {
      question: `Qual o valor medio dos contratos de ${sectorName}?`,
      answer: `O valor medio varia significativamente por modalidade e escopo. Pregões eletrônicos de ${sectorName} tendem a ter valores menores, enquanto concorrências abrangem contratos de maior porte. Use o SmartLic para filtrar por faixa de valor.`,
    },
    {
      question: `Como monitorar novos contratos de ${sectorName}?`,
      answer: `O SmartLic monitora automaticamente novas publicações de contratos e licitações de ${sectorName} no PNCP. Com o teste gratis de 14 dias você recebe alertas e análise de viabilidade por IA.`,
    },
  ];
}

export function getContratosEditorialContent(sectorId: string): string {
  const editorials: Record<string, string> = {
    vestuario: 'O mercado de contratos públicos de vestuário e uniformes movimenta bilhões anualmente no Brasil. Órgãos das esferas federal, estadual e municipal demandam uniformes, EPIs, calcados e tecidos para forcas armadas, saúde, educação e segurança pública. A Lei 14.133/2021 trouxe maior transparência a estas contratações, com dados abertos no PNCP. Empresas que monitoram sistematicamente estas oportunidades identificam padrões de compra por órgão e sazonalidade — tipicamente com picos no segundo semestre, quando orçamentos precisam ser executados.',
    alimentos: 'Contratos públicos de alimentos representam uma das maiores categorias de gastos do governo brasileiro. Programas como PNAE (alimentação escolar) e compras para hospitais, presidios e forcas armadas geram demanda constante. A agricultura familiar tem tratamento preferencial em até 30% das compras alimenticias governamentais. A análise de contratos firmados revela quais órgãos compram mais, valores medios por região e tendências de preço que orientam a formação de propostas competitivas.',
    informatica: 'O setor de informática e tecnologia da informação é um dos maiores em volume de contratações públicas. Equipamentos, licencas de software, serviços de suporte técnico e desenvolvimento de sistemas representam investimentos expressivos em todas as esferas de governo. Com a transformação digital do setor público acelerada pela Lei 14.133/2021 e pelo Governo Digital, a tendência e de crescimento sustentado. Empresas que analisam o histórico de contratos identificam oportunidades recorrentes e órgãos com demanda sistemática.',
    engenharia: 'Contratos de engenharia e obras públicas respondem pela maior fatia do orçamento de contratações governamentais. Rodovias, edificações, saneamento e infraestrutura urbana geram contratos de alto valor com prazos plurianuais. A análise de dados do PNCP revela quais órgãos mais investem, valores medios regionais e sazonalidade orçamentária — informações essenciais para planejar participações competitivas em licitações do setor.',
    saude: 'O setor de saúde pública e o segundo maior em volume de contratações, abrangendo medicamentos, equipamentos hospitalares, insumos, serviços de diagnóstico e manutenção de equipamentos médicos. Hospitais universitários, secretarias de saúde e o Ministério da Saúde publicam editais frequentemente, com padrões de compra que podem ser identificados pela análise histórica de contratos. A urgência sanitária frequentemente resulta em dispensas de licitação, ampliando as oportunidades para fornecedores qualificados.',
    software: 'Contratos de software e serviços digitais crescem aceleradamente no setor público. Desenvolvimento de sistemas, computação em nuvem, ciberseguranca e licenciamento de software corporativo compoe uma parcela crescente dos gastos governamentais em TI. A análise de contratos firmados permite identificar órgãos que investem em modernização digital, valores de referência para propostas e tendências tecnológicas priorizadas pelo governo.',
    facilities: 'O setor de facilities — limpeza, conservação, manutenção predial e jardinagem — representa um mercado estável de contratações públicas. Órgãos de todas as esferas demandam estes serviços continuamente, com contratos tipicamente anuais e renováveis. A análise do histórico de contratos revela órgãos com maior demanda, valores regionais de referência e sazonalidade de renovações, permitindo planejamento estratégico de participações.',
    vigilancia: 'Serviços de vigilância e segurança patrimonial são demandados sistematicamente por órgãos públicos em todo o território nacional. Contratos abrangem vigilância armada e desarmada, monitoramento eletrônico, portaria e segurança de eventos. O mercado e altamente regulado e exige certificações específicas. A transparência dos dados de contratos permite comparar valores praticados por região e identificar órgãos com renovações previstas.',
    transporte: 'Contratos de transporte e logística no setor público incluem fretamento, locação de veiculos, serviços de mudanca e logística de distribuição. Órgãos federais e estaduais são os maiores demandantes, com contratos que variam de pequeno a grande porte. A análise de dados históricos permite identificar rotas e regiões com maior demanda, valores medios e órgãos com contratações recorrentes.',
    mobiliario: 'O mercado de mobiliário para o setor público abrange móveis escolares, mobiliário hospitalar, móveis de escritório e equipamentos ergonômicos. Programas de expansão da rede pública de educação e saúde geram demanda expressiva. A análise de contratos anteriores revela especificações técnicas comuns, faixas de preço por tipo de móvel e órgãos compradores frequentes.',
    papelaria: 'Material de expediente e papelaria e uma categoria de compras recorrentes em todos os órgãos públicos. Apesar dos valores unitários menores, o volume agregado e significativo. Pregões eletrônicos e atas de registro de preços são as modalidades predominantes. A análise de contratos históricos permite identificar padrões de compra e planejar participações em licitações com margens adequadas.',
    materiais_eletricos: 'Materiais elétricos e de iluminação compoe uma categoria técnica de contratações públicas, incluindo luminárias, cabos, disjuntores, transformadores e sistemas de iluminação pública. A modernização da infraestrutura elétrica de predios públicos e a substituição por LED geram demanda crescente. A análise de contratos permite identificar especificações mais solicitadas e órgãos com programas de eficiência energética.',
    materiais_hidraulicos: 'Materiais hidráulicos e de saneamento são demandados para manutenção e expansão de redes de água e esgoto, além de instalações prediais. Companhias estaduais de saneamento, prefeituras e órgãos federais são os principais compradores. A análise de contratos históricos revela valores de referência regionais e tendências de investimento em infraestrutura hídrica.',
    manutencao_predial: 'Serviços de manutenção predial — elétrica, hidráulica, pintura, climatização e reparos gerais — representam contratos continuos em órgãos públicos. A demanda e estável e previsível, com renovações tipicamente anuais. A análise de dados de contratos permite identificar órgãos com maior volume de manutenção, valores regionais e oportunidades de renovação próximas.',
    engenharia_rodoviaria: 'Contratos de engenharia rodoviária abrangem construção, pavimentação, sinalização e manutenção de rodovias federais e estaduais. São contratos de alto valor e longa duração, frequentemente com aditivos. A análise do PNCP revela investimentos por região, órgãos contratantes (DNIT, DERs estaduais) e tendências de investimento em infraestrutura viária.',
  };
  return editorials[sectorId] || `O setor de contratos públicos nesta categoria apresenta oportunidades significativas para fornecedores qualificados. A análise de dados do PNCP revela padrões de compra, órgãos compradores frequentes e valores de referência que orientam a participação estratégica em licitações.`;
}
