/**
 * Zero-state fallback for blog programmatic pages.
 *
 * Fetches historical contract activity from `pncp_supplier_contracts` (via the
 * backend /blog/stats/contratos endpoints) so pages with zero open editais
 * still deliver genuine value — and so FAQ text stops contradicting the
 * visible "0 editais" counter.
 *
 * Kept as a separate module from `programmatic.ts` to isolate the feature and
 * avoid accidental regressions in the heavily-watched main file.
 */

import { formatBRL, getUfPrep } from './programmatic';

// ---------------------------------------------------------------------------
// Shared entry types (mirror the backend ContratosSetor* models)
// ---------------------------------------------------------------------------

export interface ContractTopEntry {
  nome: string;
  cnpj: string;
  total_contratos: number;
  valor_total: number;
}

export interface ContractMonthlyTrend {
  month: string;
  count: number;
  value: number;
}

interface ContractCommonFields {
  total_contracts: number;
  total_value: number;
  avg_value: number;
  top_orgaos: ContractTopEntry[];
  top_fornecedores: ContractTopEntry[];
  monthly_trend: ContractMonthlyTrend[];
  last_updated: string;
}

export interface ContratosSetorUfStats extends ContractCommonFields {
  sector_id: string;
  sector_name: string;
  uf: string;
}

export interface ContratosCidadeStats extends ContractCommonFields {
  cidade: string;
  uf: string;
}

export interface ContratosCidadeSetorStats extends ContractCommonFields {
  cidade: string;
  uf: string;
  sector_id: string;
  sector_name: string;
}

// ---------------------------------------------------------------------------
// Fetchers — all cached by Next.js ISR (24h)
// ---------------------------------------------------------------------------

export async function fetchContratosSetorUfStats(
  sectorSlug: string,
  uf: string,
): Promise<ContratosSetorUfStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const sectorId = sectorSlug.replace(/-/g, '_');
    const res = await fetch(
      `${backendUrl}/v1/blog/stats/contratos/${sectorId}/uf/${uf.toUpperCase()}`,
      { next: { revalidate: 86400 } },
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchContratosCidadeStats(
  cidadeSlug: string,
): Promise<ContratosCidadeStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const res = await fetch(
      `${backendUrl}/v1/blog/stats/contratos/cidade/${encodeURIComponent(cidadeSlug)}`,
      { next: { revalidate: 86400 } },
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchContratosCidadeSetorStats(
  cidadeSlug: string,
  sectorSlug: string,
): Promise<ContratosCidadeSetorStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const sectorId = sectorSlug.replace(/-/g, '_');
    const res = await fetch(
      `${backendUrl}/v1/blog/stats/contratos/cidade/${encodeURIComponent(cidadeSlug)}/setor/${sectorId}`,
      { next: { revalidate: 86400 } },
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Context extraction for FAQ generators
// ---------------------------------------------------------------------------

/**
 * Lightweight FAQ context derived from any of the 3 contract response shapes.
 * Callers build this when the page has zero open editais so FAQ answers
 * reference historical activity instead of contradicting the visible counter.
 */
export interface ContractsFallbackContext {
  totalContracts: number;
  avgContractValue: number;
  topOrgao?: string;
}

export function buildContractsContext(
  data:
    | ContratosSetorUfStats
    | ContratosCidadeStats
    | ContratosCidadeSetorStats
    | null
    | undefined,
): ContractsFallbackContext | undefined {
  if (!data || data.total_contracts === 0) return undefined;
  return {
    totalContracts: data.total_contracts,
    avgContractValue: data.avg_value,
    topOrgao: data.top_orgaos[0]?.nome,
  };
}

// ---------------------------------------------------------------------------
// FAQ generators that eliminate the "diversas" contradiction
// ---------------------------------------------------------------------------

type Faq = { question: string; answer: string };

/**
 * Sector × UF FAQ — replaces `generateLicitacoesFAQs` from programmatic.ts.
 *
 * When `totalEditais === 0`, FAQ answers reference historical contract activity
 * instead of the vague "diversas" placeholder (which contradicts the visible
 * "0 editais publicados" counter in the page hero).
 */
export function generateLicitacoesFAQsWithFallback(
  sectorName: string,
  ufName: string,
  totalEditais: number | undefined,
  avgValue: number | undefined,
  contractsContext: ContractsFallbackContext | undefined,
  uf?: string,
): Faq[] {
  const count = totalEditais ?? 0;
  const hasContracts = !!contractsContext && contractsContext.totalContracts > 0;

  // FAQ 1
  let faq1: string;
  if (count > 0) {
    faq1 = `Nos últimos 10 dias, foram publicadas ${count} licitações de ${sectorName} ${getUfPrep(uf)} ${ufName}, consolidando dados do PNCP, Portal de Compras Públicas e ComprasGov. O SmartLic atualiza esses números automaticamente a cada 24 horas.`;
  } else if (hasContracts) {
    const ctx = contractsContext!;
    faq1 = `Nos últimos 10 dias não há editais abertos de ${sectorName} ${getUfPrep(uf)} ${ufName}. Porém, nos últimos 12 meses foram assinados ${ctx.totalContracts.toLocaleString('pt-BR')} contratos deste setor no estado (valor médio de ${formatBRL(ctx.avgContractValue)}), indicando demanda recorrente. Cadastre-se no SmartLic para receber alerta quando novos editais forem publicados.`;
  } else {
    faq1 = `Nos últimos 10 dias não há editais abertos de ${sectorName} ${getUfPrep(uf)} ${ufName} e também não identificamos contratos recentes neste filtro. Você pode explorar UFs vizinhas ou outros setores — o SmartLic monitora 15 setores em 27 estados em tempo real.`;
  }

  // FAQ 2
  let faq2: string;
  if (avgValue && avgValue > 0) {
    faq2 = `O valor médio estimado é de ${formatBRL(avgValue)}. Os editais de ${sectorName} ${getUfPrep(uf)} ${ufName} vão desde compras pequenas até contratos de grande porte. No SmartLic você filtra por faixa de valor.`;
  } else if (hasContracts) {
    const ctx = contractsContext!;
    faq2 = `Não há editais abertos com valor estimado no momento, mas contratos deste setor assinados ${getUfPrep(uf)} ${ufName} nos últimos 12 meses tiveram valor médio de ${formatBRL(ctx.avgContractValue)} — uma referência útil para dimensionar propostas. No SmartLic você filtra por faixa de valor quando novos editais abrirem.`;
  } else {
    faq2 = `O valor varia conforme a modalidade é o escopo. Os editais de ${sectorName} ${getUfPrep(uf)} ${ufName} vão desde compras pequenas até contratos de grande porte. No SmartLic você filtra por faixa de valor.`;
  }

  const faq3 = `O primeiro passo é monitorar as publicações no PNCP e portais estaduais. Depois, análise a viabilidade de cada edital verificando modalidade, prazo, valor e exigências técnicas. O SmartLic automatiza essa triagem usando IA, economizando horas de análise manual.`;

  const faq4 = hasContracts && contractsContext!.topOrgao
    ? `O pregão eletrônico é a modalidade predominante para compras de ${sectorName}, seguido pela dispensa de licitação para valores menores. No histórico recente de ${ufName}, ${contractsContext!.topOrgao} foi um dos maiores compradores deste setor. A Lei 14.133/2021 consolidou o pregão como via preferencial para bens e serviços comuns.`
    : `O pregão eletrônico é a modalidade predominante para compras de ${sectorName}, seguido pela dispensa de licitação para valores menores. A Lei 14.133/2021 consolidou o pregão como via preferencial para bens e serviços comuns, beneficiando empresas cadastradas nas plataformas eletrônicas.`;

  return [
    { question: `Quantas licitações de ${sectorName} estão abertas ${getUfPrep(uf)} ${ufName}?`, answer: faq1 },
    { question: `Qual o valor médio das licitações de ${sectorName} ${getUfPrep(uf)} ${ufName}?`, answer: faq2 },
    { question: `Como participar de licitações de ${sectorName} ${getUfPrep(uf)} ${ufName}?`, answer: faq3 },
    { question: `Quais modalidades são mais comuns para ${sectorName} ${getUfPrep(uf)} ${ufName}?`, answer: faq4 },
    {
      question: `Posso testar o SmartLic para buscar licitações de ${sectorName}?`,
      answer: `Sim, o SmartLic oferece teste grátis de 14 dias sem necessidade de cartão de crédito. Durante o teste você tem acesso completo à busca com IA, análise de viabilidade por 4 fatores, pipeline de oportunidades e exportação de relatórios em Excel.`,
    },
  ];
}

/**
 * City × Sector FAQ — replaces `generateCidadeSectorFAQs` from programmatic.ts.
 */
export function generateCidadeSectorFAQsWithFallback(
  cityName: string,
  uf: string,
  sectorName: string,
  totalEditais: number | undefined,
  avgValue: number | undefined,
  contractsContext: ContractsFallbackContext | undefined,
): Faq[] {
  const count = totalEditais ?? 0;
  const sectorLower = sectorName.toLowerCase();
  const hasContracts = !!contractsContext && contractsContext.totalContracts > 0;

  let faq1: string;
  if (count > 0) {
    faq1 = `Nos últimos 10 dias, foram identificadas ${count} licitações de ${sectorLower} em ${cityName}/${uf}, consolidando dados do PNCP, Portal de Compras Públicas e ComprasGov. O SmartLic atualiza esses números automaticamente a cada 24 horas.`;
  } else if (hasContracts) {
    const ctx = contractsContext!;
    faq1 = `Nos últimos 10 dias não há editais abertos de ${sectorLower} em ${cityName}/${uf}. Porém, nos últimos 12 meses foram assinados ${ctx.totalContracts.toLocaleString('pt-BR')} contratos deste setor no município (valor médio de ${formatBRL(ctx.avgContractValue)}), indicando demanda recorrente. Cadastre-se no SmartLic para receber alertas automáticos.`;
  } else {
    faq1 = `Nos últimos 10 dias não há editais abertos de ${sectorLower} em ${cityName}/${uf} e também não identificamos contratos recentes neste filtro. O SmartLic monitora 15 setores em 27 estados — explore municípios vizinhos ou outros setores.`;
  }

  let faq2: string;
  if (avgValue && avgValue > 0) {
    faq2 = `O valor médio estimado é de ${formatBRL(avgValue)}. As licitações de ${sectorLower} em ${cityName} vão desde compras de pequeno porte até contratos expressivos. No SmartLic você filtra por faixa de valor.`;
  } else if (hasContracts) {
    const ctx = contractsContext!;
    faq2 = `Não há editais abertos com valor estimado no momento, mas contratos deste setor assinados em ${cityName} nos últimos 12 meses tiveram valor médio de ${formatBRL(ctx.avgContractValue)} — uma referência útil para dimensionar propostas.`;
  } else {
    faq2 = `O valor varia conforme a modalidade é o escopo do edital. As licitações de ${sectorLower} em ${cityName} vão desde compras de pequeno porte até contratos expressivos. No SmartLic você filtra por faixa de valor.`;
  }

  const faq3 = hasContracts && contractsContext!.topOrgao
    ? `${contractsContext!.topOrgao} foi um dos maiores compradores de ${sectorLower} em ${cityName} nos últimos 12 meses, ao lado de prefeituras, secretarias estaduais e órgãos federais com representação local. O SmartLic identifica automaticamente os órgãos com maior volume de publicações.`
    : `Os principais compradores de ${sectorLower} em ${cityName} incluem prefeituras, secretarias estaduais e órgãos federais com representação local. O SmartLic identifica automaticamente os órgãos com maior volume de publicações, ajudando a priorizar relacionamento comercial com compradores recorrentes.`;

  return [
    { question: `Quantas licitações de ${sectorName} estão abertas em ${cityName}?`, answer: faq1 },
    { question: `Qual o valor médio dos editais de ${sectorName} em ${cityName}?`, answer: faq2 },
    { question: `Quais órgãos mais compram ${sectorName} em ${cityName}?`, answer: faq3 },
    {
      question: `Como participar de licitações de ${sectorName} em ${cityName}/${uf}?`,
      answer: `O primeiro passo é monitorar as publicações nos portais oficiais (PNCP, PCP e ComprasGov). Depois, análise a viabilidade de cada edital verificando modalidade, prazo, valor e exigências técnicas. O SmartLic automatiza essa triagem usando inteligência artificial, economizando horas de análise manual e identificando as oportunidades com maior chance de adjudicação.`,
    },
  ];
}

/**
 * City-only FAQ (no sector filter). Uses `contractsContext` aggregated over
 * all sectors in the city to keep FAQ consistent with the "0 editais" counter.
 */
export function generateCidadeFAQsWithFallback(
  cityName: string,
  uf: string,
  totalEditais: number | undefined,
  avgValue: number | undefined,
  contractsContext: ContractsFallbackContext | undefined,
  liveTopOrgaos?: string[],
): Faq[] {
  const count = totalEditais ?? 0;
  const hasContracts = !!contractsContext && contractsContext.totalContracts > 0;

  const faq1 = `No SmartLic você acompanha em tempo real todos os editais publicados por órgãos públicos de ${cityName} (${uf}) e do restante do Brasil. A plataforma consolida dados de PNCP, PCP e ComprasGov, aplica classificação por setor via IA e envia alertas automáticos de novas oportunidades.`;

  let faq2: string;
  if (count > 0) {
    const avgText = avgValue && avgValue > 0 ? ` O valor médio estimado é ${formatBRL(avgValue)}.` : '';
    faq2 = `Nos últimos 10 dias foram identificados ${count} editais em ${cityName}.${avgText} Esse número varia diariamente conforme novas publicações.`;
  } else if (hasContracts) {
    const ctx = contractsContext!;
    faq2 = `Nos últimos 10 dias não há editais abertos em ${cityName}. Porém, nos últimos 12 meses foram assinados ${ctx.totalContracts.toLocaleString('pt-BR')} contratos públicos no município (valor médio de ${formatBRL(ctx.avgContractValue)}), indicando demanda recorrente. Cadastre-se no SmartLic para receber alertas automáticos.`;
  } else {
    faq2 = `Nos últimos 10 dias não há editais abertos em ${cityName} e também não identificamos contratos recentes. Cadastre-se no SmartLic para receber alertas assim que novas licitações forem publicadas.`;
  }

  let faq3: string;
  if (liveTopOrgaos && liveTopOrgaos.length > 0) {
    faq3 = `Os órgãos mais ativos recentemente em ${cityName} são: ${liveTopOrgaos.slice(0, 3).join(', ')}. No SmartLic você acompanha cada um deles individualmente.`;
  } else if (hasContracts && contractsContext!.topOrgao) {
    faq3 = `${contractsContext!.topOrgao} é um dos órgãos mais ativos em ${cityName} nos últimos 12 meses. Prefeituras, secretarias e autarquias locais também são compradores frequentes. Use o SmartLic para mapear o histórico de compras de cada órgão.`;
  } else {
    faq3 = `Prefeituras, secretarias e autarquias locais são os compradores mais frequentes em ${cityName}. Use o SmartLic para mapear o histórico de compras de cada órgão.`;
  }

  const faq4 = `Para participar de uma licitação em ${cityName}, sua empresa precisa estar regular (CNDs, SICAF quando aplicável), ter objeto social compatível com o edital e apresentar proposta no portal indicado (PNCP, Comprasnet ou portal próprio). O SmartLic ajuda a filtrar apenas os editais em que você é elegível.`;

  return [
    { question: `Como encontrar licitações abertas em ${cityName}?`, answer: faq1 },
    { question: `Quantas licitações existem atualmente em ${cityName}?`, answer: faq2 },
    { question: `Quais órgãos mais compram em ${cityName}?`, answer: faq3 },
    { question: `Como participar de uma licitação em ${cityName}/${uf}?`, answer: faq4 },
  ];
}
