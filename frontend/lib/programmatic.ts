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
      answer: `Você pode testar o SmartLic grátis por 30 dias, sem cartão de crédito. O teste inclui busca com IA, análise de viabilidade e exportação de relatórios.`,
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
// MKT-003: Phased launch configuration
// -----------------------------------------------------------------------

/** Phase 1 sectors — 5 largest by procurement volume */
const PHASE1_SECTORS = ['informatica', 'saude', 'engenharia', 'facilities', 'software'];

/** Phase 1 UFs — 5 largest by procurement volume */
const PHASE1_UFS = ['SP', 'RJ', 'MG', 'PR', 'RS'];

/**
 * MKT-003 AC5: Generate static params for phased launch.
 * Phase 1: 5 sectors × 5 UFs = 25 pages.
 */
export function generateLicitacoesParams(): { setor: string; uf: string }[] {
  const params: { setor: string; uf: string }[] = [];
  for (const sector of SECTORS) {
    if (!PHASE1_SECTORS.includes(sector.id)) continue;
    for (const uf of PHASE1_UFS) {
      params.push({ setor: sector.slug, uf: uf.toLowerCase() });
    }
  }
  return params;
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
      `Para empresas de ${sectorName.toLowerCase()} que atuam em ${ufName}, a chave do sucesso está na análise seletiva. Nem todo edital publicado representa uma oportunidade real — fatores como modalidade de contratação, prazo de entrega, valor estimado e exigências de qualificação técnica determinam a viabilidade de participação. O SmartLic automatiza essa triagem usando inteligência artificial, classificando cada edital em até 4 fatores de viabilidade: modalidade (30%), prazo (25%), valor (25%) e geografia (20%). Isso permite que equipes comerciais foquem apenas nas oportunidades com maior probabilidade de sucesso.`,
      `O mercado de compras públicas em ${ufName} segue padrões sazonais bem definidos: o primeiro trimestre é marcado pela finalização de contratos do exercício anterior e planejamento orçamentário; o segundo trimestre inicia a execução efetiva; o terceiro concentra o pico de publicações; e o quarto trimestre traz uma corrida para empenhar recursos antes do encerramento do exercício fiscal. Empresas que entendem esse ciclo e se preparam com antecedência têm taxa de adjudicação significativamente superior à média do setor.`,
    ],
    sul: [
      `A região ${regionName} destaca-se pelo alto índice de eficiência administrativa nos órgãos públicos, refletindo-se em editais bem estruturados e processos licitatórios transparentes. Em ${ufName}, empresas de ${sectorName.toLowerCase()} encontram um mercado maduro, onde a qualidade da proposta técnica frequentemente supera o fator preço na decisão de adjudicação. Cooperativas e associações empresariais da região têm forte tradição de participação conjunta em licitações de maior porte.`,
      `O perfil de compras públicas em ${ufName} reflete a diversificação econômica da região ${regionName}: há demanda consistente em setores industriais, agropecuários e de serviços. As prefeituras do interior, frequentemente subestimadas, representam um nicho valioso — menor concorrência e relações comerciais de longo prazo. O SmartLic monitora automaticamente todas as publicações do PNCP e portais estaduais, garantindo que nenhuma oportunidade passe despercebida.`,
      `Para se destacar nas licitações de ${sectorName.toLowerCase()} em ${ufName}, empresas devem investir na qualificação técnica da equipe e na padronização dos processos internos de elaboração de propostas. A região ${regionName} tem elevada exigência documental — atestados de capacidade técnica, certificações ISO e comprovações de experiência anterior são diferenciais decisivos. Manter um banco de dados atualizado de editais similares adjudicados, com histórico de preços praticados, permite precificar propostas com assertividade.`,
      `A sazonalidade das licitações em ${ufName} acompanha o calendário fiscal nacional, com picos no segundo e terceiro trimestres. Porém, uma particularidade da região ${regionName} é o impacto do inverno nas obras de infraestrutura — o frio e as chuvas concentradas podem atrasar cronogramas, abrindo oportunidades em períodos tipicamente de baixa movimentação. A análise de viabilidade geográfica do SmartLic leva em conta a distância entre a sede da empresa e o local de execução, otimizando a seleção de editais com logística favorável.`,
    ],
    nordeste: [
      `O ${regionName} brasileiro vive um momento de transformação nas compras públicas, com crescente adoção de pregão eletrônico e maior transparência nos processos licitatórios. Em ${ufName}, o volume de editais de ${sectorName.toLowerCase()} tem crescido consistentemente, impulsionado por investimentos federais em infraestrutura, saúde e educação. A região oferece oportunidades únicas para empresas que compreendem suas especificidades regulatórias e logísticas.`,
      `A logística de entrega é o principal desafio para empresas que atuam no ${regionName} a partir de outras regiões. No entanto, empresas locais de ${sectorName.toLowerCase()} em ${ufName} têm vantagem competitiva natural — menor custo de frete, conhecimento do mercado local e relacionamento com órgãos compradores. Para empresas de fora, a estratégia mais eficaz é estabelecer parcerias com distribuidores regionais ou manter estoques descentralizados. O SmartLic ajuda a identificar quais editais justificam o investimento logístico com base na análise de viabilidade de 4 fatores.`,
      `Os programas federais direcionados ao ${regionName} — como investimentos em saneamento, energia e infraestrutura urbana — geram um pipeline previsível de licitações. Em ${ufName}, os municípios menores frequentemente publicam editais com menor concorrência e valores que, somados, representam receita significativa. A chave é o monitoramento abrangente: enquanto grandes empresas focam nos editais de maior valor, PMEs encontram espaço em compras fracionadas e contratos de fornecimento contínuo.`,
      `O calendário de compras em ${ufName} é influenciado pelo ciclo político municipal e estadual — anos eleitorais tendem a concentrar investimentos nos primeiros semestres. Para ${sectorName.toLowerCase()}, entender essas dinâmicas permite antecipar demandas e preparar propostas com antecedência. O SmartLic consolida dados de três fontes oficiais (PNCP, Portal de Compras Públicas e ComprasGov), eliminando o risco de perder oportunidades publicadas em portais diferentes.`,
    ],
    norte: [
      `A região ${regionName} do Brasil apresenta um mercado de licitações públicas em expansão acelerada, impulsionado por investimentos federais em infraestrutura, saúde e conectividade. Em ${ufName}, as distâncias geográficas e a logística fluvial criam barreiras naturais de entrada que reduzem a concorrência efetiva, beneficiando empresas com presença local ou capacidade logística diferenciada. Para ${sectorName.toLowerCase()}, essa combinação de demanda crescente e menor competição representa uma oportunidade estratégica.`,
      `As peculiaridades logísticas do ${regionName} exigem adaptação nas estratégias de participação em licitações. Em ${ufName}, muitos órgãos públicos aceitam prazos de entrega estendidos em razão das dificuldades de acesso, o que favorece empresas com planejamento logístico robusto. O transporte fluvial e aéreo complementa o rodoviário em muitas localidades, impactando diretamente o custo e a viabilidade de fornecimento. O SmartLic incorpora a análise geográfica em seu score de viabilidade, ajudando empresas a identificar quais editais justificam o investimento logístico.`,
      `Os investimentos em infraestrutura digital e saneamento na região ${regionName} estão gerando um ciclo virtuoso de licitações. Em ${ufName}, municípios que antes dependiam exclusivamente de repasses federais agora publicam editais próprios com recursos de royalties e compensações ambientais. Para empresas de ${sectorName.toLowerCase()}, isso significa um mercado cada vez mais diversificado, com oportunidades em todas as esferas de governo (federal, estadual e municipal).`,
      `A sazonalidade no ${regionName} é fortemente influenciada pelo regime de chuvas. Em ${ufName}, o período seco (geralmente junho a novembro) concentra o maior volume de obras e aquisições, enquanto o período chuvoso reduz a atividade em setores dependentes de logística terrestre. Empresas que planejam sua participação em licitações de ${sectorName.toLowerCase()} considerando essa sazonalidade maximizam sua taxa de sucesso e reduzem custos operacionais.`,
    ],
    centro_oeste: [
      `O ${regionName} brasileiro, sede do governo federal em Brasília, é um dos polos mais relevantes para licitações públicas no país. Em ${ufName}, a concentração de órgãos federais e a pujança do agronegócio geram um volume expressivo de compras governamentais em ${sectorName.toLowerCase()}. A proximidade com centros de decisão política e a infraestrutura rodoviária interligando as capitais conferem vantagens logísticas a empresas da região.`,
      `O mercado de licitações em ${ufName} é caracterizado pela coexistência de grandes contratos federais (especialmente em ${ufName === 'Distrito Federal' ? 'órgãos da esplanada dos ministérios' : 'representações regionais de ministérios'}) e demandas municipais pulverizadas. Para ${sectorName.toLowerCase()}, essa diversidade permite compor um portfólio equilibrado entre contratos de alto valor e fornecimentos recorrentes. O SmartLic classifica automaticamente cada edital por relevância setorial, eliminando o ruído de editais irrelevantes.`,
      `A economia do ${regionName} — ancorada no agronegócio, mineração e serviços — gera demandas específicas de infraestrutura que se refletem nas licitações. Em ${ufName}, os investimentos em logística (armazéns, silos, rodovias) e em equipamentos públicos (hospitais, escolas, delegacias) mantêm um fluxo constante de oportunidades. Empresas de ${sectorName.toLowerCase()} que monitoram sistematicamente essas publicações conseguem antecipar tendências e preparar propostas mais competitivas.`,
      `O calendário fiscal em ${ufName} segue o padrão nacional, com picos de publicação no segundo e terceiro trimestres. Uma particularidade do ${regionName} é a influência dos períodos de safra na disponibilidade de recursos municipais — municípios dependentes de receitas agropecuárias concentram investimentos após os períodos de colheita. A análise de viabilidade do SmartLic considera quatro fatores (modalidade, prazo, valor e geografia) para identificar as oportunidades mais alinhadas ao perfil de cada empresa.`,
    ],
  };

  return paragraphs[region];
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
): { question: string; answer: string }[] {
  const count = totalEditais ?? 0;

  return [
    {
      question: `Quantas licitações de ${sectorName} estão abertas em ${ufName}?`,
      answer: `Nos últimos 10 dias, foram publicadas ${count > 0 ? count : 'diversas'} licitações de ${sectorName} em ${ufName}, consolidando dados do PNCP, Portal de Compras Públicas e ComprasGov. O SmartLic atualiza esses números automaticamente a cada 24 horas.`,
    },
    {
      question: `Qual o valor médio das licitações de ${sectorName} em ${ufName}?`,
      answer: `${avgValue && avgValue > 0 ? `O valor médio estimado é de ${formatBRL(avgValue)}.` : 'O valor varia conforme a modalidade e o escopo.'} Os editais de ${sectorName} em ${ufName} vão desde compras pequenas até contratos de grande porte. No SmartLic você filtra por faixa de valor.`,
    },
    {
      question: `Como participar de licitações de ${sectorName} em ${ufName}?`,
      answer: `O primeiro passo é monitorar as publicações no PNCP e portais estaduais. Depois, analise a viabilidade de cada edital verificando modalidade, prazo, valor e exigências técnicas. O SmartLic automatiza essa triagem usando IA, economizando horas de análise manual.`,
    },
    {
      question: `Quais modalidades são mais comuns para ${sectorName} em ${ufName}?`,
      answer: `O pregão eletrônico é a modalidade predominante para compras de ${sectorName}, seguido pela dispensa de licitação para valores menores. A Lei 14.133/2021 consolidou o pregão como via preferencial para bens e serviços comuns, beneficiando empresas cadastradas nas plataformas eletrônicas.`,
    },
    {
      question: `Posso testar o SmartLic para buscar licitações de ${sectorName}?`,
      answer: `Sim, o SmartLic oferece teste grátis de 30 dias sem necessidade de cartão de crédito. Durante o teste você tem acesso completo à busca com IA, análise de viabilidade por 4 fatores, pipeline de oportunidades e exportação de relatórios em Excel.`,
    },
  ];
}
