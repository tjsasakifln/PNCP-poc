/**
 * STORY-324 AC17: FAQ content per sector for SEO landing pages.
 *
 * Each sector has 4-5 FAQs covering:
 * - Types of procurement in the sector
 * - How to find opportunities on PNCP
 * - Average contract values
 * - How SmartLic helps
 * - Sector-specific question
 */

export interface SectorFaq {
  question: string;
  answer: string;
}

export const SECTOR_FAQS: Record<string, SectorFaq[]> = {
  vestuario: [
    {
      question: "Quais tipos de licitação existem para Vestuário e Uniformes?",
      answer:
        "As principais modalidades são Pregão Eletrônico (mais comum), Dispensa de Licitação para valores menores e Concorrência para contratos de maior valor. Pregões eletrônicos representam a maioria das aquisições de uniformes, fardamentos e EPIs no setor público.",
    },
    {
      question: "Como encontrar licitações de vestuário no PNCP?",
      answer:
        "O PNCP (Portal Nacional de Contratações Públicas) centraliza todas as licitações federais, estaduais e municipais. Você pode buscar por termos como 'uniforme', 'fardamento', 'vestuário' e 'EPI'. O SmartLic automatiza essa busca e filtra apenas as oportunidades relevantes para seu negócio.",
    },
    {
      question: "Qual o valor médio das licitações de vestuário?",
      answer:
        "O valor médio varia de R$ 50.000 a R$ 2.000.000, dependendo do volume e tipo de produto. Uniformes escolares tendem a ter valores menores, enquanto fardamentos militares e conjuntos de EPIs podem ultrapassar R$ 1 milhão.",
    },
    {
      question: "Como o SmartLic ajuda empresas de vestuário?",
      answer:
        "O SmartLic busca automaticamente licitações de vestuário em todas as fontes oficiais, classifica por relevância com IA, e calcula um score de viabilidade considerando modalidade, prazo, valor e região. Você recebe apenas oportunidades que realmente fazem sentido para sua empresa.",
    },
    {
      question: "Preciso de registro no SICAF para participar de licitações de uniformes?",
      answer:
        "Para licitações federais via Pregão Eletrônico, o cadastro no SICAF é obrigatório. Para licitações estaduais e municipais, cada órgão pode ter requisitos próprios. O SmartLic indica a modalidade de cada licitação para que você saiba antecipadamente os requisitos.",
    },
  ],

  alimentos: [
    {
      question: "Quais tipos de licitação existem para Alimentação e Merenda?",
      answer:
        "Pregão Eletrônico é a modalidade dominante para aquisição de gêneros alimentícios. Chamadas Públicas são usadas para compras da agricultura familiar (PNAE). Dispensas ocorrem para valores menores ou situações emergenciais.",
    },
    {
      question: "Como encontrar licitações de alimentação no PNCP?",
      answer:
        "Busque no PNCP por termos como 'gêneros alimentícios', 'merenda escolar', 'refeição', 'rancho'. O SmartLic monitora essas buscas diariamente e notifica você sobre novas oportunidades no setor.",
    },
    {
      question: "Qual o valor médio das licitações de alimentação?",
      answer:
        "Contratos de merenda escolar variam de R$ 100.000 a R$ 5.000.000 dependendo do município. Fornecimento de refeições para órgãos pode ultrapassar R$ 10 milhões anuais.",
    },
    {
      question: "Como o SmartLic ajuda empresas de alimentação?",
      answer:
        "O SmartLic identifica automaticamente licitações de gêneros alimentícios, merenda e refeições, filtrando por região e valor. A análise de viabilidade considera prazos de entrega, modalidade e competitividade regional.",
    },
    {
      question: "Empresas pequenas podem participar de licitações de merenda?",
      answer:
        "Sim. A Lei 14.133/2021 incentiva a participação de ME/EPP com margens de preferência. Chamadas Públicas do PNAE priorizam a agricultura familiar. O SmartLic filtra oportunidades adequadas ao porte da sua empresa.",
    },
  ],

  informatica: [
    {
      question: "Quais tipos de licitação existem para Hardware e TI?",
      answer:
        "Pregão Eletrônico é a modalidade padrão para aquisição de computadores, servidores, periféricos e equipamentos de rede. Atas de Registro de Preços são muito comuns para padronizar compras de TI no setor público.",
    },
    {
      question: "Como encontrar licitações de TI no PNCP?",
      answer:
        "Busque por 'computador', 'servidor', 'notebook', 'switch', 'storage', 'impressora'. O PNCP e o ComprasGov centralizam essas publicações. O SmartLic monitora todas as fontes simultaneamente.",
    },
    {
      question: "Qual o valor médio das licitações de hardware?",
      answer:
        "Compras de microcomputadores variam de R$ 50.000 a R$ 2.000.000. Servidores e infraestrutura de rede podem ultrapassar R$ 5.000.000. Atas de Registro de Preços costumam ter valores agregados maiores.",
    },
    {
      question: "Como o SmartLic ajuda empresas de TI?",
      answer:
        "O SmartLic diferencia licitações de hardware de software automaticamente, identifica atas de registro de preços e calcula a viabilidade considerando especificações técnicas, prazos e competitividade.",
    },
    {
      question: "Preciso de certificações para vender hardware ao governo?",
      answer:
        "Depende do edital. Muitos exigem certificações como ISO 9001, compatibilidade com padrões técnicos específicos e garantia estendida. O SmartLic mostra os requisitos de cada licitação para você avaliar antes de investir tempo na proposta.",
    },
  ],

  mobiliario: [
    {
      question: "Quais tipos de licitação existem para Mobiliário?",
      answer:
        "Pregão Eletrônico domina as compras de mesas, cadeiras, armários e estantes para o setor público. Concorrência pode ocorrer para projetos de mobiliário sob medida de maior valor.",
    },
    {
      question: "Como encontrar licitações de mobiliário no PNCP?",
      answer:
        "Pesquise por 'mesa', 'cadeira', 'armário', 'estante', 'mobiliário', 'móveis de escritório'. O SmartLic filtra automaticamente menções irrelevantes (como 'mesa de negociação') usando IA.",
    },
    {
      question: "Qual o valor médio das licitações de mobiliário?",
      answer:
        "Lotes de mobiliário de escritório variam de R$ 30.000 a R$ 1.000.000. Projetos de mobiliário para escolas ou hospitais podem ter valores maiores, especialmente quando incluem instalação.",
    },
    {
      question: "Como o SmartLic ajuda empresas de mobiliário?",
      answer:
        "O SmartLic usa palavras-chave contextuais para filtrar apenas licitações reais de mobiliário, excluindo falsos positivos. A análise de viabilidade considera região de entrega, prazo e valor do contrato.",
    },
  ],

  papelaria: [
    {
      question: "Quais tipos de licitação existem para Material de Escritório?",
      answer:
        "Pregão Eletrônico e Atas de Registro de Preços são as modalidades mais comuns. Dispensas de licitação ocorrem para compras de menor valor. Material de escritório é uma das categorias com maior volume de licitações.",
    },
    {
      question: "Como encontrar licitações de papelaria no PNCP?",
      answer:
        "Busque por 'material de escritório', 'papel', 'caneta', 'toner', 'suprimentos administrativos'. O SmartLic agrega resultados do PNCP, PCP e ComprasGov em uma busca unificada.",
    },
    {
      question: "Qual o valor médio das licitações de papelaria?",
      answer:
        "Compras de material de escritório variam de R$ 10.000 a R$ 500.000. Atas de Registro de Preços podem agregar valores maiores ao longo do período de vigência.",
    },
    {
      question: "Como o SmartLic ajuda empresas de papelaria?",
      answer:
        "O SmartLic monitora diariamente todas as fontes oficiais e identifica oportunidades de material de escritório. Filtra por região, valor e modalidade para que você foque apenas nas oportunidades viáveis.",
    },
  ],

  engenharia: [
    {
      question: "Quais tipos de licitação existem para Engenharia e Obras?",
      answer:
        "Concorrência é comum para obras de maior valor. Tomada de Preços e Convite são usados conforme faixas de valor. RDC (Regime Diferenciado de Contratações) é aplicado em obras específicas. A Lei 14.133/2021 trouxe o Diálogo Competitivo para projetos complexos.",
    },
    {
      question: "Como encontrar licitações de engenharia no PNCP?",
      answer:
        "Pesquise por 'obra', 'reforma', 'construção', 'pavimentação', 'projeto executivo'. O PNCP centraliza publicações de todas as esferas. O SmartLic filtra por especialidade e porte.",
    },
    {
      question: "Qual o valor médio das licitações de engenharia?",
      answer:
        "Obras públicas variam enormemente — de R$ 100.000 para reformas a dezenas de milhões para infraestrutura. Projetos e consultorias de engenharia ficam na faixa de R$ 50.000 a R$ 2.000.000.",
    },
    {
      question: "Como o SmartLic ajuda empresas de engenharia?",
      answer:
        "O SmartLic classifica licitações de engenharia por especialidade (civil, elétrica, ambiental), calcula viabilidade considerando localização e porte da obra, e alerta sobre prazos de submissão de propostas.",
    },
    {
      question: "É necessário ter CREA para participar de licitações de engenharia?",
      answer:
        "Sim, a maioria das licitações de engenharia exige registro no CREA e responsável técnico habilitado. Atestados de capacidade técnica também são frequentemente solicitados. O SmartLic mostra os requisitos de cada edital.",
    },
  ],

  software: [
    {
      question: "Quais tipos de licitação existem para Software e Sistemas?",
      answer:
        "Pregão Eletrônico é predominante para licenças de software e SaaS. Inexigibilidade pode ocorrer para softwares proprietários sem concorrência. Desenvolvimento de sistemas customizados usa Pregão ou Concorrência.",
    },
    {
      question: "Como encontrar licitações de software no PNCP?",
      answer:
        "Busque por 'software', 'sistema', 'licença', 'SaaS', 'desenvolvimento de sistema', 'consultoria de TI'. O SmartLic separa automaticamente licitações de software de hardware.",
    },
    {
      question: "Qual o valor médio das licitações de software?",
      answer:
        "Licenças de software variam de R$ 20.000 a R$ 2.000.000. Desenvolvimento de sistemas customizados pode ultrapassar R$ 5.000.000. Contratos de SaaS são recorrentes e crescem ano a ano no setor público.",
    },
    {
      question: "Como o SmartLic ajuda empresas de software?",
      answer:
        "O SmartLic identifica oportunidades de software, SaaS e desenvolvimento de sistemas, distinguindo de licitações de hardware. A análise de viabilidade considera complexidade técnica, prazo e valor.",
    },
  ],

  facilities: [
    {
      question: "Quais tipos de licitação existem para Facilities e Manutenção?",
      answer:
        "Pregão Eletrônico é a modalidade padrão para serviços de limpeza, portaria, recepção e conservação. Contratos contínuos (12-60 meses) são a norma neste setor.",
    },
    {
      question: "Como encontrar licitações de facilities no PNCP?",
      answer:
        "Pesquise por 'limpeza', 'conservação', 'portaria', 'recepção', 'zeladoria', 'jardinagem', 'copa'. O SmartLic monitora todas as fontes e filtra por tipo de serviço.",
    },
    {
      question: "Qual o valor médio das licitações de facilities?",
      answer:
        "Contratos de limpeza e conservação variam de R$ 200.000 a R$ 10.000.000 anuais, dependendo da área e complexidade. Serviços de portaria seguem faixa similar.",
    },
    {
      question: "Como o SmartLic ajuda empresas de facilities?",
      answer:
        "O SmartLic identifica automaticamente oportunidades de serviços continuados, calcula a viabilidade considerando mão de obra regional, prazo contratual e valor estimado por posto de trabalho.",
    },
  ],

  saude: [
    {
      question: "Quais tipos de licitação existem para Saúde?",
      answer:
        "Pregão Eletrônico para medicamentos, insumos e equipamentos. Dispensa de licitação para compras emergenciais. Registro de Preços é muito utilizado para padronizar aquisições hospitalares em redes de saúde.",
    },
    {
      question: "Como encontrar licitações de saúde no PNCP?",
      answer:
        "Busque por 'medicamento', 'equipamento hospitalar', 'insumo médico', 'material de laboratório', 'órtese', 'prótese'. O SmartLic agrega PNCP, PCP e ComprasGov para cobertura completa.",
    },
    {
      question: "Qual o valor médio das licitações de saúde?",
      answer:
        "Licitações de saúde têm grande amplitude — de R$ 50.000 para insumos básicos a dezenas de milhões para equipamentos de diagnóstico. Medicamentos representam o maior volume em valor.",
    },
    {
      question: "Como o SmartLic ajuda empresas de saúde?",
      answer:
        "O SmartLic classifica licitações de saúde por subcategoria (medicamentos, equipamentos, insumos), filtra por especialidade e calcula viabilidade considerando exigências técnicas e regulatórias.",
    },
    {
      question: "É necessário registro na ANVISA para participar?",
      answer:
        "Para medicamentos e dispositivos médicos, o registro na ANVISA é obrigatório. Equipamentos hospitalares também precisam de certificação. O SmartLic identifica essas exigências nos editais.",
    },
  ],

  vigilancia: [
    {
      question: "Quais tipos de licitação existem para Vigilância e Segurança?",
      answer:
        "Pregão Eletrônico é a modalidade padrão para vigilância patrimonial (armada e desarmada), segurança eletrônica (CFTV, alarmes) e controle de acesso. Contratos são tipicamente contínuos.",
    },
    {
      question: "Como encontrar licitações de segurança no PNCP?",
      answer:
        "Pesquise por 'vigilância', 'segurança patrimonial', 'CFTV', 'alarme', 'controle de acesso', 'portaria armada'. O SmartLic monitora e filtra automaticamente.",
    },
    {
      question: "Qual o valor médio das licitações de vigilância?",
      answer:
        "Contratos de vigilância patrimonial variam de R$ 500.000 a R$ 20.000.000 anuais. Sistemas de CFTV e segurança eletrônica ficam entre R$ 100.000 e R$ 3.000.000.",
    },
    {
      question: "Como o SmartLic ajuda empresas de segurança?",
      answer:
        "O SmartLic diferencia vigilância patrimonial de segurança eletrônica, identifica contratos contínuos e calcula viabilidade considerando número de postos, turnos e região.",
    },
  ],

  transporte: [
    {
      question: "Quais tipos de licitação existem para Transporte e Veículos?",
      answer:
        "Pregão Eletrônico para aquisição e locação de veículos, combustíveis e peças. Registro de Preços é comum para frotas. Concorrência pode ocorrer para grandes contratos de transporte coletivo.",
    },
    {
      question: "Como encontrar licitações de transporte no PNCP?",
      answer:
        "Busque por 'veículo', 'combustível', 'locação de veículo', 'manutenção de frota', 'pneu', 'peças automotivas'. O SmartLic filtra por tipo de serviço e região.",
    },
    {
      question: "Qual o valor médio das licitações de transporte?",
      answer:
        "Aquisição de veículos varia de R$ 100.000 a R$ 5.000.000. Combustíveis podem ultrapassar R$ 10.000.000 anuais. Locação de frota fica entre R$ 500.000 e R$ 15.000.000.",
    },
    {
      question: "Como o SmartLic ajuda empresas de transporte?",
      answer:
        "O SmartLic classifica por subcategoria (veículos, combustíveis, peças, locação), identifica atas de registro de preços e calcula viabilidade considerando frota e região de atuação.",
    },
  ],

  manutencao_predial: [
    {
      question: "Quais tipos de licitação existem para Manutenção Predial?",
      answer:
        "Pregão Eletrônico para serviços de manutenção preventiva e corretiva. Contratos contínuos (PMOC, ar-condicionado, elevadores) são comuns. Concorrência para reformas prediais maiores.",
    },
    {
      question: "Como encontrar licitações de manutenção predial no PNCP?",
      answer:
        "Pesquise por 'manutenção predial', 'PMOC', 'ar condicionado', 'elevador', 'pintura predial', 'impermeabilização'. O SmartLic monitora todas as fontes oficiais.",
    },
    {
      question: "Qual o valor médio das licitações de manutenção predial?",
      answer:
        "Contratos de manutenção preventiva variam de R$ 50.000 a R$ 2.000.000 anuais. PMOC (ar-condicionado) fica entre R$ 100.000 e R$ 1.000.000. Reformas podem ultrapassar R$ 5.000.000.",
    },
    {
      question: "Como o SmartLic ajuda empresas de manutenção predial?",
      answer:
        "O SmartLic identifica oportunidades de manutenção por especialidade (elétrica, hidráulica, climatização), filtra por região e calcula viabilidade considerando escopo e duração do contrato.",
    },
  ],

  engenharia_rodoviaria: [
    {
      question: "Quais tipos de licitação existem para Engenharia Rodoviária?",
      answer:
        "Concorrência e RDC são as modalidades predominantes para obras rodoviárias. Tomada de Preços para obras de menor porte. Licitações de conservação rodoviária frequentemente usam Pregão.",
    },
    {
      question: "Como encontrar licitações de engenharia rodoviária no PNCP?",
      answer:
        "Busque por 'pavimentação', 'rodovia', 'ponte', 'viaduto', 'sinalização viária', 'conservação rodoviária'. O SmartLic filtra especificamente por infraestrutura viária.",
    },
    {
      question: "Qual o valor médio das licitações rodoviárias?",
      answer:
        "Obras rodoviárias têm valores tipicamente altos — de R$ 1.000.000 a centenas de milhões. Conservação rodoviária fica entre R$ 500.000 e R$ 20.000.000.",
    },
    {
      question: "Como o SmartLic ajuda empresas de infraestrutura viária?",
      answer:
        "O SmartLic identifica licitações de infraestrutura viária, diferenciando de engenharia civil geral. A análise de viabilidade considera porte da obra, prazo e experiência técnica necessária.",
    },
  ],

  materiais_eletricos: [
    {
      question: "Quais tipos de licitação existem para Materiais Elétricos?",
      answer:
        "Pregão Eletrônico é a modalidade padrão para fios, cabos, disjuntores e quadros elétricos. Concorrência para projetos de iluminação pública e subestações de maior porte.",
    },
    {
      question: "Como encontrar licitações de materiais elétricos no PNCP?",
      answer:
        "Pesquise por 'material elétrico', 'fio', 'cabo', 'disjuntor', 'quadro elétrico', 'iluminação pública', 'luminária LED'. O SmartLic automatiza essa busca.",
    },
    {
      question: "Qual o valor médio das licitações de materiais elétricos?",
      answer:
        "Compras de materiais elétricos variam de R$ 20.000 a R$ 1.000.000. Projetos de iluminação pública podem ultrapassar R$ 5.000.000. Subestações têm valores ainda maiores.",
    },
    {
      question: "Como o SmartLic ajuda empresas de materiais elétricos?",
      answer:
        "O SmartLic identifica oportunidades específicas de materiais e instalações elétricas, separando de obras civis gerais. Filtra por tipo de material, região e valor.",
    },
  ],

  materiais_hidraulicos: [
    {
      question: "Quais tipos de licitação existem para Materiais Hidráulicos?",
      answer:
        "Pregão Eletrônico para tubos, conexões e bombas. Concorrência para obras de saneamento e redes de distribuição. Contratos de manutenção de sistemas hidráulicos usam Pregão.",
    },
    {
      question: "Como encontrar licitações de materiais hidráulicos no PNCP?",
      answer:
        "Busque por 'tubo', 'conexão hidráulica', 'bomba', 'tratamento de água', 'esgoto', 'saneamento'. O SmartLic monitora PNCP, PCP e ComprasGov simultaneamente.",
    },
    {
      question: "Qual o valor médio das licitações de materiais hidráulicos?",
      answer:
        "Compras de materiais hidráulicos variam de R$ 30.000 a R$ 500.000. Obras de saneamento e redes de distribuição podem ultrapassar R$ 10.000.000.",
    },
    {
      question: "Como o SmartLic ajuda empresas de saneamento?",
      answer:
        "O SmartLic identifica oportunidades no setor de saneamento e hidráulica, filtra por escopo (materiais vs obras), região e valor. A análise de viabilidade considera complexidade técnica e prazos.",
    },
  ],
};

/**
 * Get FAQs for a sector by its ID.
 * Returns empty array if sector not found.
 */
export function getSectorFaqs(sectorId: string): SectorFaq[] {
  return SECTOR_FAQS[sectorId] || [];
}
