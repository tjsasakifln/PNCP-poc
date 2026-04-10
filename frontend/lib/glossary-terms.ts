/**
 * Shared glossary term definitions for SmartLic SEO glossary pages.
 *
 * Used by:
 * - /glossario (hub page)
 * - /glossario/[termo] (individual term pages)
 */

export interface GlossaryTerm {
  term: string;
  slug: string;
  definition: string;
  example: string;
  guideHref: string;
  guideLabel: string;
  /** Brief reference to Lei 14.133 article or other legal basis (optional). */
  legalBasis?: string;
  /** Slugs of 2-3 related glossary terms. */
  relatedTerms?: string[];
  /** 2 FAQ entries for FAQPage structured data. */
  faqEntries?: { question: string; answer: string }[];
}

export const GLOSSARY_TERMS: GlossaryTerm[] = [
  // A
  {
    term: 'Adjudicação',
    slug: 'adjudicacao',
    definition:
      'Ato formal pelo qual a autoridade competente atribui o objeto da licitação ao licitante que apresentou a proposta mais vantajosa. Na Lei 14.133/2021, a adjudicação ocorre após a habilitação e o julgamento dos recursos, consolidando o direito do vencedor a assinatura do contrato.',
    example:
      'Após o pregão eletrônico para aquisição de 500 computadores, o pregoeiro adjudicou o objeto a empresa que ofertou R$ 2.800 por unidade, o menor preço válido após a fase de lances.',
    guideHref: '/blog',
    guideLabel: 'Como funciona o processo licitatório',
    legalBasis: 'Lei 14.133/2021, art. 71',
    relatedTerms: ['homologacao', 'habilitacao', 'recurso'],
    faqEntries: [
      {
        question: 'Qual a diferença entre adjudicação e homologação?',
        answer:
          'A adjudicação é o ato do pregoeiro/comissão que atribui o objeto ao vencedor, enquanto a homologação é o ato da autoridade superior que ratifica todo o procedimento licitatório. A homologação ocorre após a adjudicação é autoriza a assinatura do contrato.',
      },
      {
        question: 'A adjudicação garante a assinatura do contrato?',
        answer:
          'A adjudicação consolida o direito do vencedor, mas não é contrato. A administração pode revogar ou anular o processo por razões supervenientes antes da assinatura. O vencedor tem direito à indenização se a revogação for indevida.',
      },
    ],
  },
  {
    term: 'Aditivo Contratual',
    slug: 'aditivo-contratual',
    definition:
      'Instrumento jurídico utilizado para alterar cláusulas de um contrato administrativo vigente, podendo modificar prazos, valores ou escopo. A Lei 14.133 limita acréscimos e supressões a 25% do valor original (50% para reformas de edifícios ou equipamentos).',
    example:
      'Um contrato de manutenção predial de R$ 1.200.000 recebeu aditivo de 20% (R$ 240.000) para incluir a reforma do sistema de ar-condicionado, dentro do limite legal.',
    guideHref: '/blog',
    guideLabel: 'Gestão de contratos públicos',
    legalBasis: 'Lei 14.133/2021, art. 124–125',
    relatedTerms: ['contrato-administrativo', 'reequilibrio-economico-financeiro', 'reajuste'],
    faqEntries: [
      {
        question: 'Qual o limite para aditivos contratuais em obras?',
        answer:
          'Para obras e serviços de engenharia, a Lei 14.133/2021 permite acréscimos de até 25% do valor original do contrato. Para reformas de edifícios ou equipamentos, o limite é de 50%. Supressões ficam limitadas a 25% em qualquer caso.',
      },
      {
        question: 'É possível fazer aditivo de prazo sem aditivo de valor?',
        answer:
          'Sim. Aditivos de prazo e de valor são independentes. Um aditivo de prazo pode ser celebrado sem alteração de valor quando a prorrogação se justifica por fato não imputável ao contratado (caso fortuito, força maior, paralisação da administração, etc.).',
      },
    ],
  },
  {
    term: 'Anulação',
    slug: 'anulacao',
    definition:
      'Invalidação de um processo licitatório ou contrato administrativo por vício de legalidade identificado pela própria administração ou pelo Judiciário. A anulação tem efeito retroativo (ex tunc), desfazendo todos os atos práticados desde a origem do vício.',
    example:
      'O Tribunal de Contas determinou a anulação de um pregão porque o edital exigia certificação ISO específica que restringia a competitividade sem justificativa técnica.',
    guideHref: '/blog',
    guideLabel: 'Recursos e impugnações em licitações',
    legalBasis: 'Lei 14.133/2021, art. 71, § 1º',
    relatedTerms: ['revogacao', 'impugnacao', 'recurso'],
    faqEntries: [
      {
        question: 'Qual a diferença entre anulação e revogação de licitação?',
        answer:
          'A anulação ocorre por ilegalidade (vício formal ou material) é tem efeito retroativo, desfazendo todos os atos. A revogação ocorre por interesse público superveniente e tem efeito a partir da decisão (ex nunc). Ambas devem ser fundamentadas.',
      },
      {
        question: 'A anulação gera direito a indenização para o vencedor?',
        answer:
          'Se a anulação decorrer de fato imputável à administração, o contratado tem direito à indenização pelos danos comprovados. Se a ilegalidade foi causada pelo próprio contratado, não há indenização.',
      },
    ],
  },
  {
    term: 'Ata de Registro de Preços',
    slug: 'ata-de-registro-de-precos',
    definition:
      'Documento vinculativo que formaliza preços, fornecedores, órgãos participantes e condições para aquisições futuras dentro do Sistema de Registro de Preços (SRP). A ata tem validade de até 1 ano (prorrogável por mais 1 ano na Lei 14.133) e não obriga o órgão a contratar.',
    example:
      'A Secretaria de Saúde registrou preços de 30 tipos de medicamentos com 5 fornecedores. Durante 12 meses, qualquer hospital da rede pode emitir ordens de compra com os preços registrados sem nova licitação.',
    guideHref: '/blog',
    guideLabel: 'Sistema de Registro de Preços na prática',
    legalBasis: 'Lei 14.133/2021, art. 82–86; Decreto 11.462/2023',
    relatedTerms: ['sistema-de-registro-de-precos', 'pregao-eletronico', 'nota-de-empenho'],
    faqEntries: [
      {
        question: 'A ata de registro de preços obriga o órgão a comprar?',
        answer:
          'Não. A ata de registro de preços não gera obrigação de aquisição. O órgão gerenciador e os participantes podem ou não emitir pedidos de compra. O fornecedor, porém, é obrigado a atender as demandas dentro da validade da ata.',
      },
      {
        question: 'Outros órgãos que não participaram da licitação podem usar a ata?',
        answer:
          'Sim, desde que haja autorização expressa do órgão gerenciador e o edital tenha previsto a possibilidade de adesão ("carona"). O Decreto 11.462/2023 limita o volume de adesões ao quantitativo registrado para o órgão gerenciador.',
      },
    ],
  },
  {
    term: 'Atestado de Capacidade Técnica',
    slug: 'atestado-de-capacidade-tecnica',
    definition:
      'Documento emitido por pessoa jurídica de direito público ou privado, comprovando que a empresa executou anteriormente serviço ou obra similar ao objeto licitado. E o principal instrumento de qualificação técnica na fase de habilitação.',
    example:
      'Para participar de licitação de pavimentação asfáltica de 15 km, a empresa apresentou atestado de prefeitura vizinha comprovando execução de 12 km de pavimentação concluída em 2024.',
    guideHref: '/blog',
    guideLabel: 'Habilitação técnica em licitações',
    legalBasis: 'Lei 14.133/2021, art. 67, III',
    relatedTerms: ['habilitacao', 'proposta-tecnica', 'atestado-de-capacidade-tecnica'],
    faqEntries: [
      {
        question: 'Quem pode emitir atestado de capacidade técnica?',
        answer:
          'Qualquer pessoa jurídica de direito público (prefeituras, estados, autarquias, empresas públicas) ou privado (empresas contratantes) pode emitir o atestado. O documento deve conter identificação do signatário, CNPJ do emitente, descrição do serviço e período de execução.',
      },
      {
        question: 'O atestado precisa ser registrado no CREA ou CAU?',
        answer:
          'Para obras e serviços de engenharia, o atestado deve ser acompanhado da respectiva Certidão de Acervo Técnico (CAT) emitida pelo CREA ou CAU, vinculando o responsável técnico à execução. Para serviços não técnicos, o registro não é exigido.',
      },
    ],
  },
  // B
  {
    term: 'Balanço Patrimonial',
    slug: 'balanco-patrimonial',
    definition:
      'Demonstração contábil que apresenta a posição financeira da empresa em determinada data, evidenciando ativos, passivos e patrimônio líquido. E exigido na habilitação econômico-financeira para comprovar índices como liquidez geral e endividamento.',
    example:
      'O edital exigia Índice de Liquidez Geral >= 1,0. A empresa apresentou balanço patrimonial de 2025 com ativo circulante de R$ 3.200.000 e passivo circulante de R$ 2.100.000, resultando em ILG de 1,52 — aprovada na habilitação.',
    guideHref: '/blog',
    guideLabel: 'Habilitação econômico-financeira',
    legalBasis: 'Lei 14.133/2021, art. 69, I',
    relatedTerms: ['habilitacao', 'certidao-negativa', 'sicaf'],
    faqEntries: [
      {
        question: 'Qual balanço patrimonial devo apresentar em licitações?',
        answer:
          'Em regra, o último balanço patrimonial exigível (do exercício anterior). Para empresas com obrigatoriedade de auditoria, deve ser registrado na Junta Comercial. MEIs e microempresas com receita abaixo de R$ 360 mil podem substituir por declaração simplificada.',
      },
      {
        question: 'Quais são os índices financeiros mais exigidos em editais?',
        answer:
          'Os índices mais comuns são: Liquidez Geral (ativo total / passivo total) — mínimo 1,0; Liquidez Corrente (ativo circulante / passivo circulante) — mínimo 1,0; e Grau de Endividamento (passivo total / ativo total) — máximo 1,0. Os limites variam por edital.',
      },
    ],
  },
  {
    term: 'BDI (Beneficios e Despesas Indiretas)',
    slug: 'bdi',
    definition:
      'Percentual aplicado sobre o custo direto de obras ou serviços que engloba despesas indiretas (administração central, seguros, garantias), tributos e lucro. O BDI compoe o preço final da proposta e e objeto de análise detalhada pelos órgãos de controle.',
    example:
      'Em licitação de obra pública, a empresa calculou custo direto de R$ 800.000 e aplicou BDI de 28,5%, resultando em preço final de R$ 1.028.000. O TCU considerou o percentual compatível com a referência SINAPI.',
    guideHref: '/blog',
    guideLabel: 'Formação de preços em obras públicas',
    legalBasis: 'Lei 14.133/2021, art. 23; Acórdão TCU 2622/2013',
    relatedTerms: ['preco-de-referencia', 'proposta-comercial', 'concorrencia'],
    faqEntries: [
      {
        question: 'Qual é o BDI máximo aceito pelo TCU em obras?',
        answer:
          'O TCU (Acórdão 2622/2013-Plenário) estabelece benchmarks por tipo de obra. Para obras civis em geral, o BDI referencial é 25,5%. Para obras de linha de distribuição elétrica chega a 34,8%. O TCU pode glosar valores acima dos referenciais sem justificativa técnica.',
      },
      {
        question: 'ISS e COFINS entram no BDI ou no custo direto?',
        answer:
          'ISS, COFINS, PIS e outros tributos incidentes sobre a receita compõem o BDI (despesas tributárias). Os materiais e mão de obra que compõem o serviço formam o custo direto. Esta distinção é fundamental para evitar glosamento pelo TCU.',
      },
    ],
  },
  {
    term: 'BEC (Bolsa Eletrônica de Compras)',
    slug: 'bec',
    definition:
      'Sistema eletrônico de compras do governo do estado de São Paulo, utilizado para aquisição de bens e serviços por órgãos estaduais e municipais paulistas. Funciona como plataforma de pregão eletrônico e oferta de compra com catalogo de produtos padronizados.',
    example:
      'A Secretaria de Educação de SP públicou oferta de compra na BEC para 10.000 cadeiras escolares. Fornecedores cadastrados no CAUFESP ofertaram preços diretamente na plataforma durante 3 dias.',
    guideHref: '/blog',
    guideLabel: 'Portais de compras estaduais',
    legalBasis: 'Decreto Estadual SP 47.297/2002',
    relatedTerms: ['pregao-eletronico', 'comprasnet', 'pncp'],
    faqEntries: [
      {
        question: 'Qual a diferença entre BEC e PNCP?',
        answer:
          'A BEC é o portal de compras eletrônicas do governo do Estado de São Paulo, criado pelo Decreto 47.297/2002. O PNCP é o portal nacional obrigatório criado pela Lei 14.133/2021 para todos os entes federativos. São Paulo pública no PNCP e pode operar as compras pela BEC simultaneamente.',
      },
      {
        question: 'Como me cadastrar na BEC para vender para o governo de SP?',
        answer:
          'É necessário fazer o cadastro no CAUFESP (Cadastro Unificado de Fornecedores do Estado de SP) em qualquer Poupatempo ou online em caufesp.sp.gov.br. Após aprovação, o acesso à BEC é automático para as categorias de produtos cadastradas.',
      },
    ],
  },
  // C
  {
    term: 'Cadastro de Fornecedores (SICAF)',
    slug: 'sicaf',
    definition:
      'O Sistema de Cadastramento Unificado de Fornecedores (SICAF) e o registro oficial do governo federal que centraliza dados cadastrais, habilitação jurídica, regularidade fiscal e qualificação econômica de empresas que fornecem ao poder público. O cadastro simplifica a participação em licitações federais.',
    example:
      'Antes de participar do pregão do Ministério da Saúde, a empresa atualizou seu SICAF com certidões negativas federais, estaduais e municipais, balanço patrimonial e contrato social atualizado.',
    guideHref: '/blog',
    guideLabel: 'Como se cadastrar no SICAF',
    legalBasis: 'Lei 14.133/2021, art. 87–88; IN SEGES 3/2018',
    relatedTerms: ['habilitacao', 'certidao-negativa', 'balanco-patrimonial'],
    faqEntries: [
      {
        question: 'O SICAF é obrigatório para participar de licitações federais?',
        answer:
          'Para a maioria dos pregões eletrônicos federais, o SICAF é exigido. Ele centraliza a habilitação documental, dispensando a apresentação física de documentos a cada licitação. Municípios e estados podem ter seus próprios cadastros (ex.: CAUFESP em SP).',
      },
      {
        question: 'Com que frequência preciso renovar o SICAF?',
        answer:
          'Certidões negativas têm validade variável (CND federal: 180 dias; FGTS: 30 dias). O SICAF exibe alertas de vencimento. Recomenda-se revisar o cadastro mensalmente e atualizar documentos com antecedência de ao menos 10 dias antes do vencimento.',
      },
    ],
  },
  {
    term: 'Certidão Negativa',
    slug: 'certidao-negativa',
    definition:
      'Documento oficial emitido por órgãos públicos que atesta a inexistência de débitos ou pendencias do contribuinte. Na habilitação, são exigidas certidões negativas de débitos federais (CND/PGFN), estaduais, municipais, FGTS e trabalhistas (CNDT).',
    example:
      'A empresa foi inabilitada porque a Certidão Negativa de Débitos Trabalhistas (CNDT) estava vencida ha 3 dias na data da sessão do pregão — ressaltando a importância de monitorar vencimentos.',
    guideHref: '/blog',
    guideLabel: 'Documentos de habilitação',
    legalBasis: 'Lei 14.133/2021, art. 68, II; Lei 12.440/2011 (CNDT)',
    relatedTerms: ['habilitacao', 'sicaf', 'balanco-patrimonial'],
    faqEntries: [
      {
        question: 'Quais certidões negativas são exigidas em licitações federais?',
        answer:
          'As principais são: (1) CND/PGFN — débitos federais e dívida ativa; (2) Certidão FGTS (CEF) — 30 dias de validade; (3) CNDT — Certidão Negativa de Débitos Trabalhistas (TST); (4) Certidão de regularidade estadual; (5) Certidão de regularidade municipal. Todas devem estar válidas na data da sessão.',
      },
      {
        question: 'A empresa pode ser habilitada com certidão positiva com efeito de negativa?',
        answer:
          'Sim. A Certidão Positiva com Efeito de Negativa (CPEN) equivale à certidão negativa para fins de habilitação. Ela é emitida quando existem débitos com exigibilidade suspensa (parcelamento, recurso administrativo ou ação judicial).',
      },
    ],
  },
  {
    term: 'Chamada Pública',
    slug: 'chamada-publica',
    definition:
      'Modalidade simplificada de seleção utilizada principalmente para aquisição de alimentos da agricultura familiar no ambito do Programa Nacional de Alimentação Escolar (PNAE). A Lei 11.947/2009 determina que no mínimo 30% dos recursos do PNAE sejam destinados a compras via chamada pública.',
    example:
      'A prefeitura públicou chamada pública para aquisição de 5 toneladas de hortaliças orgânicas de agricultores familiares locais para merenda escolar, com preço baseado no mercado atacadista regional.',
    guideHref: '/blog',
    guideLabel: 'Vendendo para programas de alimentação escolar',
    legalBasis: 'Lei 11.947/2009, art. 14; Resolução FNDE 6/2020',
    relatedTerms: ['dispensa-de-licitacao', 'edital', 'me-epp'],
    faqEntries: [
      {
        question: 'Quem pode participar de chamada pública do PNAE?',
        answer:
          'Agricultores familiares, empreendedores familiares rurais e suas organizações (cooperativas, associações) com DAP/CAF ativa. A prioridade é dada a assentamentos de reforma agrária, comunidades quilombolas e indígenas, e depois aos demais produtores locais.',
      },
      {
        question: 'Qual o limite de venda por agricultor familiar em chamada pública?',
        answer:
          'Cada unidade familiar pode vender até R$ 20.000 por ano por entidade executora (prefeitura/estado). Cooperativas e associações têm limite de R$ 20.000 por CPF dos sócios, multiplicado pelo número de associados habilitados.',
      },
    ],
  },
  {
    term: 'ComprasNet',
    slug: 'comprasnet',
    definition:
      'Portal eletrônico de compras do governo federal brasileiro, operado desde 2000, que concentra pregões eletrônicos, cotações e licitações federais. Esta sendo gradualmente substituido pelo PNCP (Portal Nacional de Contratações Públicas) conforme a Lei 14.133/2021.',
    example:
      'Até 2025, o ComprasNet processou mais de R$ 50 bilhões/ano em pregões eletrônicos federais. Empresas que já operavam no ComprasNet precisam migrar seus cadastros para o PNCP até o prazo de transição.',
    guideHref: '/blog',
    guideLabel: 'Migração ComprasNet para PNCP',
    legalBasis: 'Decreto 10.947/2022 (transição para o PNCP)',
    relatedTerms: ['pncp', 'pregao-eletronico', 'bec'],
    faqEntries: [
      {
        question: 'O ComprasNet ainda funciona em 2026?',
        answer:
          'O ComprasNet (SIASG/COMPRASNET) segue operando para licitações federais em transição, mas novos processos são publicados no PNCP conforme cronograma do Decreto 10.947/2022. A migração total para o PNCP ainda está em curso no governo federal.',
      },
      {
        question: 'O cadastro no SICAF vale para o PNCP?',
        answer:
          'Sim. O SICAF continua sendo o sistema de cadastramento unificado de fornecedores do governo federal. O PNCP é o portal de publicação/divulgação das contratações, mas a habilitação ainda usa o SICAF.',
      },
    ],
  },
  {
    term: 'Concorrência',
    slug: 'concorrencia',
    definition:
      'Modalidade licitatória destinada a contratações de maior vulto, com ampla publicidade e prazos mais longos. Na Lei 14.133/2021, a concorrência e utilizada para obras, serviços de engenharia e compras acima dos limites do pregão, admitindo os critérios de julgamento menor preço, melhor técnica ou técnica e preço.',
    example:
      'O DNIT abriu concorrência para construção de ponte com valor estimado de R$ 45 milhões. O prazo de públicação do edital foi de 35 dias úteis, permitindo ampla participação de construtoras de todo o país.',
    guideHref: '/blog',
    guideLabel: 'Modalidades de licitação',
    legalBasis: 'Lei 14.133/2021, art. 29, I',
    relatedTerms: ['pregao-eletronico', 'dialogo-competitivo', 'edital'],
    faqEntries: [
      {
        question: 'Qual o valor mínimo para usar concorrência em obras?',
        answer:
          'A Lei 14.133/2021 não fixa um valor mínimo para a concorrência. Ela é obrigatória para obras e serviços de engenharia que não possam ser contratados por pregão (quando o objeto não é padronizável como "serviço ou bem comum"). Para compras de bens e serviços comuns, o pregão é preferencial.',
      },
      {
        question: 'A concorrência pode ter fase de lances como o pregão?',
        answer:
          'Sim. A Lei 14.133/2021 permite que a concorrência inclua fase de lances quando o critério de julgamento for menor preço ou maior desconto, aproximando-a do pregão nesse aspecto. Os prazos de publicação são maiores que os do pregão.',
      },
    ],
  },
  {
    term: 'Consórcio',
    slug: 'consorcio',
    definition:
      'Agrupamento formal de duas ou mais empresas para participar conjuntamente de licitação, somando capacidades técnicas e financeiras. O consórcio não cria nova pessoa jurídica — cada consorciada mantem sua individualidade e responde solidariamente pelas obrigações.',
    example:
      'Três empresas de TI formaram consórcio para disputar contrato de R$ 80 milhões de modernização de datacenter: uma com expertise em infraestrutura, outra em segurança e a terceira em cloud migration.',
    guideHref: '/blog',
    guideLabel: 'Consórcio em licitações',
    legalBasis: 'Lei 14.133/2021, art. 15',
    relatedTerms: ['habilitacao', 'atestado-de-capacidade-tecnica', 'contrato-administrativo'],
    faqEntries: [
      {
        question: 'Todo edital permite a participação em consórcio?',
        answer:
          'Não. A admissão de consórcios é facultativa ao edital. A vedação deve ser expressamente justificada. O TCU orienta que editais de grande vulto ou que exijam capacidade técnica complementar deveriam admitir consórcios para ampliar a competitividade.',
      },
      {
        question: 'Como funciona a responsabilidade solidária no consórcio?',
        answer:
          'Todas as empresas consorciadas respondem solidariamente pelas obrigações do consórcio perante a administração. Internamente, o contrato de consórcio distribui responsabilidades, mas a administração pode cobrar de qualquer consorciada pelo valor total da obrigação.',
      },
    ],
  },
  {
    term: 'Contrato Administrativo',
    slug: 'contrato-administrativo',
    definition:
      'Acordo formal celebrado entre a administração pública e o fornecedor vencedor da licitação, estabelecendo direitos, obrigações, prazos e condições de execução. Diferente dos contratos privados, o contrato administrativo possui cláusulas exorbitantes que conferem prerrogativas especiais ao poder público.',
    example:
      'Após adjudicação e homologação de pregão para serviços de limpeza, o hospital público assinou contrato administrativo de 12 meses com a empresa vencedora, no valor mensal de R$ 185.000, com cláusulas de fiscalização e penalidades.',
    guideHref: '/blog',
    guideLabel: 'Execução de contratos públicos',
    legalBasis: 'Lei 14.133/2021, art. 89–108',
    relatedTerms: ['aditivo-contratual', 'fiscalizacao', 'penalidade-sancao'],
    faqEntries: [
      {
        question: 'O que são cláusulas exorbitantes no contrato administrativo?',
        answer:
          'Cláusulas exorbitantes são prerrogativas da administração que não existem em contratos privados: rescisão unilateral, modificação unilateral, fiscalização, aplicação de penalidades, retomada do objeto, restrição de cessão. Elas garantem o interesse público mas devem ser exercidas com proporcionalidade.',
      },
      {
        question: 'Por quanto tempo pode durar um contrato administrativo?',
        answer:
          'A Lei 14.133/2021 permite contratos de até 5 anos para serviços contínuos (prorrogáveis por mais 5, totalizando 10). Para obras, o prazo segue o projeto. Contratos de fornecimento contínuo de bens essenciais podem chegar a 10 anos. O prazo deve ser justificado tecnicamente.',
      },
    ],
  },
  // D
  {
    term: 'Diálogo Competitivo',
    slug: 'dialogo-competitivo',
    definition:
      'Modalidade licitatória introduzida pela Lei 14.133/2021 para contratações de objetos inovadores ou técnicamente complexos, onde a administração dialoga com licitantes pre-selecionados para desenvolver soluções antes da fase de propostas. E indicado quando o órgão não consegue definir específicacoes técnicas de forma precisa.',
    example:
      'O Ministério da Ciência abriu diálogo competitivo para sistema de inteligência artificial de monitoramento ambiental. Três empresas foram selecionadas para 60 dias de diálogos técnicos antes de submeterem propostas finais.',
    guideHref: '/blog',
    guideLabel: 'Novas modalidades da Lei 14.133',
    legalBasis: 'Lei 14.133/2021, art. 32',
    relatedTerms: ['concorrencia', 'estudo-tecnico-preliminar', 'proposta-tecnica'],
    faqEntries: [
      {
        question: 'Para quais objetos é adequado o diálogo competitivo?',
        answer:
          'O diálogo competitivo é indicado para: inovações tecnológicas sem solução de mercado conhecida, objetos de elevada complexidade técnica onde a administração não consegue elaborar especificações precisas, e contratações de estruturas de financiamento ou jurídicas complexas.',
      },
      {
        question: 'Quantas empresas participam do diálogo competitivo?',
        answer:
          'A lei não fixa número mínimo, mas o edital deve estabelecer critérios de pré-seleção e o número de participantes das rodadas de diálogo. O processo termina quando a administração identifica a solução adequada e convoca a fase de propostas.',
      },
    ],
  },
  {
    term: 'Dispensa de Licitação',
    slug: 'dispensa-de-licitacao',
    definition:
      'Hipótese de contratação direta prevista em lei, onde a licitação é dispensável pôr razões de valor (até R$ 59.906,02 para compras em 2026), emergência, situação específica ou outros casos do art. 75 da Lei 14.133. Difere da inexigibilidade porque a competição seria possível, mas a lei autoriza sua dispensa.',
    example:
      'A universidade contratou diretamente serviço de conserto de ar-condicionado pôr R$ 42.000, enquadrado na dispensa pôr valor (limite de R$ 59.906,02 para serviços em 2026), com pesquisa de preços de 3 fornecedores.',
    guideHref: '/blog',
    guideLabel: 'Contratação direta: dispensa e inexigibilidade',
    legalBasis: 'Lei 14.133/2021, art. 75',
    relatedTerms: ['inexigibilidade', 'cotacao', 'contrato-administrativo'],
    faqEntries: [
      {
        question: 'Qual o limite de valor para dispensa de licitação em 2026?',
        answer:
          'Os limites são atualizados anualmente pelo Ministério da Gestão. Em 2026: R$ 59.906,02 para obras e serviços de engenharia; R$ 29.953,01 para compras e demais serviços. Estes valores são por objeto contratado, sendo vedado o fracionamento para fugir dos limites.',
      },
      {
        question: 'É obrigatória a pesquisa de preços na dispensa por valor?',
        answer:
          'Sim. Mesmo na dispensa por valor, a Lei 14.133 exige pesquisa de preços com ao menos 3 fornecedores, salvo impossibilidade justificada. O processo deve ser formalizado em autos e publicado no PNCP para contratações acima de R$ 10.000.',
      },
    ],
  },
  {
    term: 'Dotação Orçamentária',
    slug: 'dotacao-orcamentaria',
    definition:
      'Previsão de recursos financeiros consignada no orçamento público (LOA) destinada a cobrir determinada despesa. Nenhuma licitação pode ser lancada sem dotação orçamentária que garanta os recursos necessários para pagamento da contratação.',
    example:
      'O edital de pregão para mobiliário escolar indicou a dotação orçamentária 12.361.0001.2035 — Programa de Equipamentos Escolares, com crédito disponível de R$ 2.300.000 no exercicio de 2026.',
    guideHref: '/blog',
    guideLabel: 'Orçamento público e licitações',
    legalBasis: 'Lei 14.133/2021, art. 11, § 3º; Lei 4.320/1964',
    relatedTerms: ['nota-de-empenho', 'plano-de-contratacoes-anual', 'edital'],
    faqEntries: [
      {
        question: 'O que acontece se não houver dotação orçamentária para uma licitação?',
        answer:
          'Sem dotação orçamentária suficiente, a licitação não pode ser instaurada. Se a dotação se esgotar durante o processo, o certame deve ser revogado. O descumprimento desta regra configura infração à Lei de Responsabilidade Fiscal.',
      },
      {
        question: 'Como identificar a dotação orçamentária no edital?',
        answer:
          'Editais federais usam a estrutura: Órgão.Unidade/Função.Subfunção/Programa.Ação/Natureza da Despesa.Fonte de Recursos. A indicação da dotação é obrigatória no edital e na nota de empenho.',
      },
    ],
  },
  // E
  {
    term: 'Edital',
    slug: 'edital',
    definition:
      'Instrumento convocatório que estabelece todas as regras, exigências, prazos e critérios de uma licitação. E a "lei interna" do processo licitatório — tudo o que não está no edital não pode ser exigido, e tudo o que está nele vincula tanto a administração quanto os licitantes.',
    example:
      'O edital do Pregão Eletrônico 045/2026 da Prefeitura de Curitiba específicava: objeto (500 notebooks), prazo de entrega (60 dias), critério de julgamento (menor preço por lote), habilitação exigida e modelo de proposta.',
    guideHref: '/blog',
    guideLabel: 'Como analisar editais de licitação',
    legalBasis: 'Lei 14.133/2021, art. 25',
    relatedTerms: ['impugnacao', 'pregao-eletronico', 'termo-de-referencia'],
    faqEntries: [
      {
        question: 'Quais são as partes obrigatórias de um edital de licitação?',
        answer:
          'A Lei 14.133 exige: objeto e suas especificações, critério de julgamento, habilitação exigida, prazo de entrega, condições de pagamento, sanções, recursos cabíveis, dotação orçamentária e modelos de proposta. O edital deve ser publicado no PNCP.',
      },
      {
        question: 'O edital pode ser alterado após publicado?',
        answer:
          'Sim, através de aditamento (errata). Se a alteração afetar a elaboração das propostas, o prazo deve ser reaberto. Se for retificação de erro material sem impacto nas propostas, a reabertura de prazo não é obrigatória, mas deve ser comunicada a todos os que retiraram o edital.',
      },
    ],
  },
  {
    term: 'Estudo Técnico Preliminar (ETP)',
    slug: 'estudo-tecnico-preliminar',
    definition:
      'Documento obrigatório na fase preparatória da licitação (Lei 14.133, art. 18) que demonstra a necessidade da contratação, analisa soluções disponíveis no mercado e define requisitos técnicos. O ETP embasa o Termo de Referência e e públicado no PNCP.',
    example:
      'Antes de licitar sistema de gestão hospitalar, o ETP comparou 4 soluções de mercado (SaaS vs on-premise), analisou custos em 5 anos e concluiu que SaaS seria 35% mais econômico, justificando a opção técnica do Termo de Referência.',
    guideHref: '/blog',
    guideLabel: 'Fase preparatória na Lei 14.133',
    legalBasis: 'Lei 14.133/2021, art. 18',
    relatedTerms: ['mapa-de-riscos', 'edital', 'pncp'],
    faqEntries: [
      {
        question: 'O ETP é obrigatório para todas as licitações?',
        answer:
          'Sim, o ETP é obrigatório para todos os contratos acima dos limites de dispensa por valor, salvo exceções regulamentadas (contratações emergenciais, por exemplo). Para dispensa por valor, uma pesquisa de mercado simplificada pode substituir o ETP completo.',
      },
      {
        question: 'Quais elementos são obrigatórios no ETP?',
        answer:
          'O ETP deve conter: descrição da necessidade, estimativa da quantidade, levantamento de mercado (soluções disponíveis), descrição da solução escolhida, estimativa de preços, impacto de não contratar e declaração de viabilidade. O Decreto 10.947/2022 detalha os requisitos.',
      },
    ],
  },
  // F
  {
    term: 'Fiscalização',
    slug: 'fiscalizacao',
    definition:
      'Atividade exercida por servidor ou comissão designada pelo órgão contratante para acompanhar a execução do contrato, verificar qualidade, prazos e conformidade com as cláusulas pactuadas. A Lei 14.133 torna obrigatória a designação de fiscal para todo contrato.',
    example:
      'O fiscal do contrato de serviços de TI identificou que a equipe alocada estava com 2 profissionais a menos que o exigido. Notificou a empresa, que regularizou em 5 dias, evitando aplicação de multa contratual de 2%.',
    guideHref: '/blog',
    guideLabel: 'Fiscalização de contratos públicos',
    legalBasis: 'Lei 14.133/2021, art. 117',
    relatedTerms: ['contrato-administrativo', 'medicao', 'penalidade-sancao'],
    faqEntries: [
      {
        question: 'Quais são as responsabilidades do fiscal de contrato?',
        answer:
          'O fiscal deve: acompanhar a execução em conformidade com o contrato, anotar irregularidades em livro de registro, comunicar ao gestor desvios que exijam providências, atestar medições, e instruir eventual aplicação de penalidades. A negligência do fiscal pode responsabilizá-lo pessoalmente.',
      },
      {
        question: 'O fiscal de contrato pode ser o mesmo servidor que elaborou o edital?',
        answer:
          'Não há vedação legal expressa, mas é recomendado que sejam funções distintas para garantir a independência de julgamento. Para contratos de grande vulto ou complexidade, a Lei 14.133 incentiva a separação entre gestor e fiscal do contrato.',
      },
    ],
  },
  // G
  {
    term: 'Garantia Contratual',
    slug: 'garantia-contratual',
    definition:
      'Garantia exigida do contratado para assegurar a execução do contrato, podendo ser caução em dinheiro, seguro-garantia ou fianca bancária. A Lei 14.133 permite exigir até 5% do valor do contrato (até 10% para obras de grande vulto).',
    example:
      'Para contrato de R$ 10 milhões em obras de saneamento, a construtora apresentou seguro-garantia de R$ 500.000 (5%) emitido por seguradora autorizada pela SUSEP, com vigência até 90 dias após o recebimento definitivo.',
    guideHref: '/blog',
    guideLabel: 'Garantias em contratos públicos',
    legalBasis: 'Lei 14.133/2021, art. 96–99',
    relatedTerms: ['garantia-de-proposta', 'contrato-administrativo', 'penalidade-sancao'],
    faqEntries: [
      {
        question: 'Quais as modalidades de garantia contratual aceitas?',
        answer:
          'A Lei 14.133/2021 aceita três modalidades: (1) caução em dinheiro ou títulos da dívida pública; (2) seguro-garantia emitido por seguradora autorizada pela SUSEP; (3) fiança bancária emitida por instituição financeira. A escolha é do contratado.',
      },
      {
        question: 'Quando a garantia contratual é devolvida?',
        answer:
          'A garantia deve ser devolvida após o cumprimento integral do contrato e o recebimento definitivo do objeto. Para obras, o prazo usual é 90 dias após o recebimento definitivo. Se houver pendências (multas, reparações), a administração pode reter o valor correspondente.',
      },
    ],
  },
  {
    term: 'Garantia de Proposta',
    slug: 'garantia-de-proposta',
    definition:
      'Garantia exigida na fase de licitação para assegurar a seriedade da proposta apresentada. A Lei 14.133 permite exigir garantia de até 1% do valor estimado da contratação, devolvida após a adjudicação.',
    example:
      'Em concorrência para construção de viaduto estimada em R$ 25 milhões, o edital exigiu garantia de proposta de R$ 250.000 (1%). A empresa apresentou fianca bancária, que foi devolvida 15 dias após a homologação.',
    guideHref: '/blog',
    guideLabel: 'Garantias em licitações',
    legalBasis: 'Lei 14.133/2021, art. 58',
    relatedTerms: ['garantia-contratual', 'adjudicacao', 'homologacao'],
    faqEntries: [
      {
        question: 'A garantia de proposta é obrigatória em todos os editais?',
        answer:
          'Não. A exigência de garantia de proposta é facultativa ao edital — a administração avalia a necessidade conforme o vulto e complexidade da contratação. É mais comum em concorrências de grande valor e menos usual em pregões.',
      },
      {
        question: 'Quando a garantia de proposta pode ser executada?',
        answer:
          'A garantia pode ser executada se o vencedor desistir da proposta após a adjudicação, recusar-se a assinar o contrato no prazo fixado, ou deixar de apresentar documentos necessários à contratação. O valor é revertido ao erário.',
      },
    ],
  },
  // H
  {
    term: 'Habilitação',
    slug: 'habilitacao',
    definition:
      'Fase do processo licitatório em que se verifica a documentação jurídica, fiscal, trabalhista, técnica e econômico-financeira dos licitantes. Na Lei 14.133, a habilitação ocorre após o julgamento das propostas (inversão de fases), exceto quando o edital determina o contrário.',
    example:
      'Dos 12 participantes do pregão, 3 foram inabilitados: um por CNDT vencida, outro por falta de atestado técnico compatível e o terceiro por índice de liquidez abaixo do mínimo exigido de 1,0.',
    guideHref: '/blog',
    guideLabel: 'Habilitação em licitações',
    legalBasis: 'Lei 14.133/2021, art. 62–70',
    relatedTerms: ['certidao-negativa', 'atestado-de-capacidade-tecnica', 'sicaf'],
    faqEntries: [
      {
        question: 'Quais os documentos de habilitação exigidos em licitações?',
        answer:
          'A habilitação envolve 5 categorias: (1) jurídica — contrato social, CNPJ; (2) fiscal e trabalhista — certidões negativas federal, estadual, municipal, FGTS, CNDT; (3) técnica — atestados de capacidade; (4) econômico-financeira — balanço patrimonial, índices; (5) declarações — de não emprego de menores, não sancionado, etc.',
      },
      {
        question: 'O que é a inversão de fases na Lei 14.133?',
        answer:
          'Na Lei 14.133, a habilitação ocorre depois do julgamento das propostas por padrão (diferente da Lei 8.666 onde a habilitação era primeiro). Isso significa que só o vencedor precisa apresentar documentação, agilizando o processo. O edital pode prever a ordem inversa com justificativa.',
      },
    ],
  },
  {
    term: 'Homologação',
    slug: 'homologacao',
    definition:
      'Ato da autoridade superior que ratifica todo o procedimento licitatório após verificar sua legalidade e conveniência. A homologação e o último ato antes da convocação para assinatura do contrato e pode ser precedida de parecer jurídico.',
    example:
      'O Secretário de Administração homologou o pregão eletrônico 30 dias após a adjudicação, confirmando que todas as etapas foram conduzidas conforme a lei e autorizando a assinatura do contrato com o vencedor.',
    guideHref: '/blog',
    guideLabel: 'Etapas do processo licitatório',
    legalBasis: 'Lei 14.133/2021, art. 71',
    relatedTerms: ['adjudicacao', 'recurso', 'contrato-administrativo'],
    faqEntries: [
      {
        question: 'A homologação pode ser negada mesmo após a adjudicação?',
        answer:
          'Sim. A autoridade pode negar a homologação se verificar irregularidade no processo (ilegalidade) ou conveniência administrativa que justifique a revogação. A negativa deve ser fundamentada, e o licitante vencedor pode recorrer se for indevida.',
      },
      {
        question: 'Quem tem competência para homologar uma licitação?',
        answer:
          'A competência é da autoridade superior ao pregoeiro ou comissão — geralmente o ordenador de despesas (secretário, diretor, reitor, presidente). Em municípios menores, pode ser o próprio prefeito. A delegação de competência é possível se expressa em ato normativo.',
      },
    ],
  },
  // I
  {
    term: 'Impugnação',
    slug: 'impugnacao',
    definition:
      'Instrumento jurídico pelo qual qualquer cidadão ou licitante questiona termos do edital antes da realização da sessão pública. A impugnação deve ser apresentada em até 3 dias úteis antes da abertura (cidadão) ou até 3 dias úteis (licitante) na Lei 14.133.',
    example:
      'Uma empresa de software impugnou edital que exigia "sistema desenvolvido em Java" sem justificativa técnica, argumentando que a específicacao de linguagem restringia a concorrência. A comissão acatou e alterou para "sistema web multiplataforma".',
    guideHref: '/blog',
    guideLabel: 'Impugnação de editais',
    legalBasis: 'Lei 14.133/2021, art. 164',
    relatedTerms: ['edital', 'recurso', 'anulacao'],
    faqEntries: [
      {
        question: 'Qual o prazo para impugnar um edital?',
        answer:
          'Pela Lei 14.133/2021, qualquer pessoa pode impugnar o edital até 3 dias úteis antes da abertura da sessão pública. O prazo da Lei 8.666 (ainda vigente em alguns processos de transição) era diferente: 5 dias úteis para cidadão e 2 dias úteis para fornecedor.',
      },
      {
        question: 'A impugnação suspende o prazo do pregão?',
        answer:
          'Não automaticamente. A impugnação pode, a critério da autoridade, ensejar a republicação do edital com reabertura de prazo — o que suspende o prazo original. Se a resposta não alterar o edital, o certame segue normalmente com o prazo original.',
      },
    ],
  },
  {
    term: 'Inexigibilidade',
    slug: 'inexigibilidade',
    definition:
      'Contratação direta quando ha inviabilidade de competição, ou seja, quando o objeto só pode ser fornecido por um único prestador ou quando a natureza do serviço torna impossível a comparação objetiva. Difere da dispensa, onde a competição seria possível mas e dispensada por lei.',
    example:
      'A universidade contratou por inexigibilidade o único representante autorizado no Brasil de equipamento de ressonância magnética Siemens MAGNETOM para manutenção corretiva, pois a fabricante não credencia terceiros.',
    guideHref: '/blog',
    guideLabel: 'Contratação direta: dispensa e inexigibilidade',
    legalBasis: 'Lei 14.133/2021, art. 74',
    relatedTerms: ['dispensa-de-licitacao', 'contrato-administrativo', 'pncp'],
    faqEntries: [
      {
        question: 'Quais são as hipóteses de inexigibilidade na Lei 14.133?',
        answer:
          'O art. 74 da Lei 14.133 prevê: (I) fornecedor exclusivo; (II) serviço técnico especializado de natureza predominantemente intelectual; (III) profissional do setor artístico consagrado; (IV) credenciamento de prestadores para escolha pelo usuário. O rol é exemplificativo — qualquer inviabilidade comprovada se enquadra.',
      },
      {
        question: 'O que comprova a exclusividade do fornecedor na inexigibilidade?',
        answer:
          'O órgão deve juntar aos autos declaração de exclusividade emitida por entidade representativa do setor (sindicato, associação, câmara de comércio) ou pesquisa de mercado que demonstre a inexistência de outros fornecedores. A documentação deve ser publicada no PNCP.',
      },
    ],
  },
  // L
  {
    term: 'Leilão',
    slug: 'leilao',
    definition:
      'Modalidade licitatória utilizada para alienação (venda) de bens móveis e imóveis da administração pública ao maior lance. Na Lei 14.133, o leilão pode ser presencial ou eletrônico e exige avaliação prévia dos bens.',
    example:
      'O Exercito realizou leilão eletrônico de 50 veiculos descaracterizados com lance mínimo de R$ 8.000 cada. Os veiculos foram arrematados com agio medio de 45% sobre a avaliação.',
    guideHref: '/blog',
    guideLabel: 'Leilão de bens públicos',
    legalBasis: 'Lei 14.133/2021, art. 31',
    relatedTerms: ['concorrencia', 'adjudicacao', 'homologacao'],
    faqEntries: [
      {
        question: 'Qualquer pessoa pode participar de leilão de bens públicos?',
        answer:
          'Em geral sim, desde que preencha os requisitos do edital (cadastro prévio, lance mínimo, capacidade de pagamento). Leilões de imóveis podem exigir representação por advogado. Servidores do órgão realizador e seus parentes costumam ser impedidos de participar.',
      },
      {
        question: 'Como é feita a avaliação dos bens antes do leilão?',
        answer:
          'A avaliação é obrigatória e realizada por perito credenciado (Caixa Econômica, BNDES ou avaliador particular habilitado). Para veículos, costuma-se usar a tabela FIPE como referência. O lance mínimo é fixado pela administração, podendo ser inferior à avaliação.',
      },
    ],
  },
  {
    term: 'Licitação Deserta',
    slug: 'licitacao-deserta',
    definition:
      'Situação em que nenhum interessado comparece ao processo licitatório. Quando a licitação e deserta, a administração pode repetir o processo ou realizar contratação direta (dispensa) desde que mantenha as mesmas condições do edital original.',
    example:
      'O pregão para fornecimento de refeições em municipio do interior teve zero propostas. A prefeitura reabriu o certame com prazo estendido e, novamente deserto, contratou diretamente por dispensa (art. 75, III da Lei 14.133).',
    guideHref: '/blog',
    guideLabel: 'Licitação deserta e fracassada',
    legalBasis: 'Lei 14.133/2021, art. 75, III',
    relatedTerms: ['licitacao-fracassada', 'dispensa-de-licitacao', 'edital'],
    faqEntries: [
      {
        question: 'Qual a diferença entre licitação deserta e fracassada?',
        answer:
          'Na licitação deserta, nenhum interessado comparece (ausência de participantes). Na licitação fracassada, há participantes, mas todos são inabilitados ou suas propostas são desclassificadas. Em ambos os casos, a administração pode contratar diretamente sob as mesmas condições.',
      },
      {
        question: 'Uma licitação deserta pode ser repetida com condições diferentes?',
        answer:
          'Sim. A Lei 14.133 permite alterar condições do edital antes de repetir o certame. Se a licitação for novamente deserta, a contratação direta por dispensa exige que as condições sejam iguais às do edital original que resultou em deserto.',
      },
    ],
  },
  {
    term: 'Licitação Fracassada',
    slug: 'licitacao-fracassada',
    definition:
      'Situação em que todos os licitantes são inabilitados ou todas as propostas são desclassificadas. Diferentemente da deserta (ninguem aparece), na fracassada houve participantes, mas nenhum atendeu aos requisitos. A Lei 14.133 permite fixar prazo para adequação antes de repetir.',
    example:
      'Na concorrência para construção de escola, as 5 propostas foram desclassificadas por preços acima do orçamento estimado. A comissão fixou prazo de 8 dias para readequação, conforme art. 75, III, da Lei 14.133.',
    guideHref: '/blog',
    guideLabel: 'Licitação deserta e fracassada',
    legalBasis: 'Lei 14.133/2021, art. 75, III',
    relatedTerms: ['licitacao-deserta', 'habilitacao', 'preco-de-referencia'],
    faqEntries: [
      {
        question: 'Todos os licitantes serem inabilitados torna a licitação fracassada?',
        answer:
          'Sim. A licitação fracassada ocorre quando: todos os licitantes são inabilitados, ou todas as propostas são desclassificadas, ou o único licitante habilitado tem proposta desclassificada. A administração deve analisar a causa para corrigir o edital ou a análise.',
      },
      {
        question: 'Como a administração deve proceder após uma licitação fracassada?',
        answer:
          'A Lei 14.133 permite: (1) fixar prazo de 8 dias úteis para os licitantes readequarem suas propostas; (2) cancelar e repetir o certame com condições mais adequadas; (3) contratar diretamente por dispensa. A escolha depende da análise da causa do fracasso.',
      },
    ],
  },
  // M
  {
    term: 'Mapa de Riscos',
    slug: 'mapa-de-riscos',
    definition:
      'Documento elaborado na fase preparatória da licitação que identifica os principais riscos do processo de contratação, suas probabilidades e impactos. A Lei 14.133 tornou obrigatória sua elaboração como parte do planejamento da contratação.',
    example:
      'O mapa de riscos de contratação de datacenter identificou 12 riscos, sendo o mais crítico "indisponibilidade superior a 4h/mês" com probabilidade alta e impacto severo, levando a inclusão de SLA com multas progressivas no contrato.',
    guideHref: '/blog',
    guideLabel: 'Gestão de riscos em contratações',
    legalBasis: 'Lei 14.133/2021, art. 18, X',
    relatedTerms: ['matriz-de-riscos', 'estudo-tecnico-preliminar', 'contrato-administrativo'],
    faqEntries: [
      {
        question: 'Qual a diferença entre mapa de riscos e matriz de riscos?',
        answer:
          'O mapa de riscos é elaborado na fase preparatória para subsidiar o planejamento da contratação — é um documento interno de análise. A matriz de riscos é uma cláusula do contrato que distribui formalmente os riscos entre contratante e contratado, vinculando ambas as partes.',
      },
      {
        question: 'Quem deve elaborar o mapa de riscos?',
        answer:
          'O mapa de riscos é elaborado pelo órgão contratante, com participação da área técnica, jurídica e financeira. Em contratos complexos, pode-se contratar consultoria especializada. O documento deve ser publicado junto ao ETP no PNCP.',
      },
    ],
  },
  {
    term: 'Matriz de Riscos',
    slug: 'matriz-de-riscos',
    definition:
      'Cláusula contratual que distribui de forma objetiva as responsabilidades sobre eventos supervenientes entre contratante e contratado. Diferentemente do mapa de riscos (fase preparatória), a matriz de riscos faz parte do contrato e vincula ambas as partes.',
    example:
      'Na matriz de riscos do contrato de obra rodoviária, o risco de variação do preço do asfalto acima de 10% ficou com a administração (reequilíbrio automático), enquanto o risco de atraso por falta de mao-de-obra ficou com a construtora.',
    guideHref: '/blog',
    guideLabel: 'Gestão de riscos em contratações',
    legalBasis: 'Lei 14.133/2021, art. 103',
    relatedTerms: ['mapa-de-riscos', 'reequilibrio-economico-financeiro', 'contrato-administrativo'],
    faqEntries: [
      {
        question: 'A matriz de riscos é obrigatória em todos os contratos?',
        answer:
          'A Lei 14.133 torna a matriz de riscos obrigatória para obras e serviços de grande vulto. Para outros contratos, é facultativa mas fortemente recomendada. Sua ausência em contratos complexos pode dificultar a gestão de eventos imprevistos.',
      },
      {
        question: 'A matriz de riscos pode excluir o direito ao reequilíbrio econômico-financeiro?',
        answer:
          'Sim, para os riscos expressamente alocados ao contratado na matriz. Se a matriz atribui determinado risco ao contratado, este não pode solicitar reequilíbrio por este evento. Por isso, é fundamental analisar a matriz antes de assinar o contrato.',
      },
    ],
  },
  {
    term: 'ME/EPP',
    slug: 'me-epp',
    definition:
      'Microempresa (receita bruta anual até R$ 360.000) e Empresa de Pequeno Porte (receita até R$ 4.800.000) recebem tratamento diferenciado em licitações: direito de preferência quando a proposta for até 5% superior (pregão) ou 10% (demais modalidades) a melhor oferta, além de prazo extra para regularização fiscal.',
    example:
      'No pregão para material de escritório, a ME ofertou R$ 52.000 contra R$ 50.000 da empresa de grande porte. Como a diferença foi inferior a 5%, a ME foi convocada para cobrir o lance e ofertou R$ 49.800, vencendo o certame.',
    guideHref: '/blog',
    guideLabel: 'Vantagens de ME/EPP em licitações',
    legalBasis: 'Lei Complementar 123/2006, art. 43–44; Lei 14.133/2021, art. 4º',
    relatedTerms: ['pregao-eletronico', 'habilitacao', 'certidao-negativa'],
    faqEntries: [
      {
        question: 'Quais os benefícios de ME/EPP em licitações públicas?',
        answer:
          'As principais vantagens da Lei Complementar 123/2006 são: (1) prazo de 5 dias úteis para regularizar documentação fiscal irregular; (2) direito de empate ficto — pode cobrir a melhor proposta se sua oferta for até 5% (pregão) ou 10% (demais) superior; (3) licitações exclusivas para ME/EPP até R$ 80.000.',
      },
      {
        question: 'Como comprovar enquadramento como ME ou EPP em licitações?',
        answer:
          'Basta apresentar declaração de enquadramento como ME ou EPP no edital. Não é necessário certidão da Junta Comercial. O enquadramento é verificado pela receita bruta do exercício anterior. A declaração falsa sujeita à inabilitação e penalidades previstas em lei.',
      },
    ],
  },
  {
    term: 'Medição',
    slug: 'medicao',
    definition:
      'Procedimento periódico (geralmente mensal) de verificação e quantificação dos serviços ou obras efetivamente executados pelo contratado, servindo como base para emissão da nota fiscal e pagamento. A medição e atestada pelo fiscal do contrato.',
    example:
      'Na 3a medição mensal do contrato de limpeza hospitalar, o fiscal verificou que 95% da área foi atendida (2 alas em reforma ficaram sem serviço) e autorizou pagamento proporcional de R$ 142.500 sobre os R$ 150.000 mensais.',
    guideHref: '/blog',
    guideLabel: 'Execução de contratos de serviços',
    legalBasis: 'Lei 14.133/2021, art. 140',
    relatedTerms: ['fiscalizacao', 'recebimento-provisorio', 'recebimento-definitivo'],
    faqEntries: [
      {
        question: 'Qual o prazo para a administração pagar após a medição?',
        answer:
          'A Lei 14.133/2021 estabelece prazo de até 30 dias para pagamento após a liquidação da despesa (atestação do fiscal). O prazo começa a contar após a apresentação da nota fiscal regular. O descumprimento gera atualização monetária automática.',
      },
      {
        question: 'A medição pode ser impugnada pelo contratado?',
        answer:
          'Sim. O contratado pode contestar a medição se discordar dos quantitativos ou valores apurados. A contestação deve ser formal e documentada. Durante a análise, a administração pode reter o pagamento da parcela contestada.',
      },
    ],
  },
  // N
  {
    term: 'Nota de Empenho',
    slug: 'nota-de-empenho',
    definition:
      'Documento emitido pelo órgão público que reserva dotação orçamentária para cobrir despesa específica. O empenho e a primeira fase da execução da despesa pública e precede a liquidação e o pagamento. Em compras de pequeno valor, pode substituir o contrato formal.',
    example:
      'Após homologação do pregão de material de limpeza (R$ 38.000), o setor financeiro emitiu Nota de Empenho vinculada a dotação 3.3.90.30 — Material de Consumo, autorizando o fornecedor a iniciar a entrega.',
    guideHref: '/blog',
    guideLabel: 'Ciclo da despesa pública',
    legalBasis: 'Lei 4.320/1964, art. 58–61; Lei 14.133/2021, art. 95',
    relatedTerms: ['dotacao-orcamentaria', 'contrato-administrativo', 'medicao'],
    faqEntries: [
      {
        question: 'A nota de empenho pode substituir o contrato administrativo?',
        answer:
          'Sim, para compras de pronto pagamento e valor igual ou inferior ao limite de dispensa por valor (R$ 29.953,01 para bens/serviços em 2026). Nesses casos, a nota de empenho é o instrumento hábil da contratação, dispensando contrato formal.',
      },
      {
        question: 'O que acontece se o empenho for cancelado?',
        answer:
          'O cancelamento do empenho não é possível após o início da execução do contrato. Para empenhos não iniciados, o cancelamento é possível por insuficiência orçamentária ou desistência fundamentada da contratação. O fornecedor deve ser notificado formalmente.',
      },
    ],
  },
  // O
  {
    term: 'Ordem de Serviço',
    slug: 'ordem-de-servico',
    definition:
      'Documento emitido pelo órgão contratante que autoriza formalmente o início da execução do contrato ou de uma etapa específica. Define data de início, escopo da demanda e prazo de conclusão, sendo obrigatória em contratos de serviços continuados.',
    example:
      'A Ordem de Serviço n. 001/2026 autorizou a empresa de TI a iniciar o desenvolvimento do modulo de RH do sistema, com prazo de 90 dias e equipe mínima de 5 profissionais, conforme cronograma do contrato.',
    guideHref: '/blog',
    guideLabel: 'Gestão de contratos de serviços',
    legalBasis: 'Lei 14.133/2021, art. 116; IN SEGES 5/2017 (serviços)',
    relatedTerms: ['contrato-administrativo', 'fiscalizacao', 'medicao'],
    faqEntries: [
      {
        question: 'A ordem de serviço é obrigatória em todos os contratos?',
        answer:
          'A emissão de ordem de serviço é obrigatória em contratos de serviços contínuos (segurança, limpeza, TI). Em obras, é obrigatória para marcar o início das atividades (prazo do contrato começa a contar da OS). Em fornecimentos de material, é substituída pelo pedido de compra ou nota de empenho.',
      },
      {
        question: 'O prazo contratual começa a contar da assinatura ou da ordem de serviço?',
        answer:
          'Depende do que está definido no contrato. A prática mais comum em obras é que o prazo começa da ordem de serviço, o que dá tempo para o contratado mobilizar equipe e materiais. Em serviços contínuos, o prazo costuma começar da assinatura.',
      },
    ],
  },
  // P
  {
    term: 'Penalidade/Sanção',
    slug: 'penalidade-sancao',
    definition:
      'Punição aplicada ao fornecedor por descumprimento contratual ou conduta irregular em licitação. A Lei 14.133 preve 4 tipos: advertência, multa (até 30% do contrato), impedimento de licitar (até 3 anos) e declaração de inidoneidade (3 a 6 anos). Sanções são registradas no PNCP.',
    example:
      'Após 3 notificações por atraso na entrega de medicamentos, o hospital aplicou multa de 10% do valor mensal (R$ 45.000) e impedimento de licitar por 2 anos, com registro no SICAF e PNCP.',
    guideHref: '/blog',
    guideLabel: 'Sanções em contratos públicos',
    legalBasis: 'Lei 14.133/2021, art. 155–163',
    relatedTerms: ['contrato-administrativo', 'fiscalizacao', 'pncp'],
    faqEntries: [
      {
        question: 'Quais as penalidades previstas na Lei 14.133/2021?',
        answer:
          'A Lei 14.133 prevê 4 sanções: (1) advertência — para infrações leves; (2) multa — até 30% do valor do contrato por inexecução total; (3) impedimento de licitar — até 3 anos, no âmbito do ente federativo; (4) declaração de inidoneidade — 3 a 6 anos, aplicável em todo território nacional por ato do ministro/secretário.',
      },
      {
        question: 'Como uma empresa com sanção pode voltar a licitar?',
        answer:
          'Advertência e multa não impedem a participação em licitações. O impedimento de licitar tem prazo determinado (até 3 anos) e expira automaticamente. A inidoneidade exige pedido formal de reabilitação após cumprido o prazo e reparados os danos.',
      },
    ],
  },
  {
    term: 'Plano de Contratações Anual (PCA)',
    slug: 'plano-de-contratacoes-anual',
    definition:
      'Instrumento de planejamento obrigatório (Lei 14.133, art. 12, VII) em que cada órgão lista todas as contratações previstas para o exercicio seguinte. O PCA e públicado no PNCP e permite que fornecedores se preparem com antecedência para as licitações do ano.',
    example:
      'O PCA 2026 do Ministério da Educação listou 847 itens de contratação, totalizando R$ 2,3 bilhões. Empresas de TI identificaram 23 contratações relevantes e iniciaram preparação de atestados e certidões 6 meses antes dos pregões.',
    guideHref: '/blog',
    guideLabel: 'Planejamento de contratações',
    legalBasis: 'Lei 14.133/2021, art. 12, VII; Decreto 10.947/2022',
    relatedTerms: ['pncp', 'estudo-tecnico-preliminar', 'dotacao-orcamentaria'],
    faqEntries: [
      {
        question: 'Quando o PCA é publicado e onde posso acessá-lo?',
        answer:
          'O PCA deve ser elaborado até 15 de agosto do exercício anterior e publicado no PNCP (pncp.gov.br). Cada órgão federal, estadual e municipal tem seu próprio PCA. A consulta é pública e gratuita, permitindo que fornecedores identifiquem oportunidades com meses de antecedência.',
      },
      {
        question: 'O PCA obriga o órgão a fazer as contratações previstas?',
        answer:
          'Não. O PCA é um instrumento de planejamento, não um compromisso vinculante. Mudanças de prioridade, contingenciamento orçamentário ou alterações na programação podem levar ao cancelamento ou postergação de itens. O PCA deve ser revisado quando necessário.',
      },
    ],
  },
  {
    term: 'PNCP (Portal Nacional de Contratações Públicas)',
    slug: 'pncp',
    definition:
      'Portal eletrônico oficial é obrigatório, criado pela Lei 14.133/2021, que centraliza a divulgação de todas as licitações, contratações diretas, atas de registro de preços e contratos dos três níveis de governo (federal, estadual e municipal). E a principal fonte de dados para monitoramento de oportunidades.',
    example:
      'O SmartLic monitora diariamente o PNCP para identificar novas licitações públicadas em 27 UFs, classificando automaticamente por setor e avaliando viabilidade. Em média, são públicadas 2.000+ contratações/dia no portal.',
    guideHref: '/blog',
    guideLabel: 'Como usar o PNCP',
    legalBasis: 'Lei 14.133/2021, art. 174–179',
    relatedTerms: ['plano-de-contratacoes-anual', 'comprasnet', 'ata-de-registro-de-precos'],
    faqEntries: [
      {
        question: 'O PNCP substituiu o ComprasNet para licitações federais?',
        answer:
          'O PNCP centraliza a publicação de todas as contratações públicas, mas o ComprasNet/SIASG ainda opera para a execução de alguns processos federais em transição. A meta é que todas as fases das licitações federais sejam realizadas pelo PNCP até o prazo final da transição.',
      },
      {
        question: 'Municípios são obrigados a publicar no PNCP?',
        answer:
          'Sim. A Lei 14.133/2021 torna obrigatória a publicação de todas as contratações — federais, estaduais e municipais — no PNCP, incluindo licitações, dispensas, inexigibilidades, contratos e atas de registro de preços. A obrigação para municípios aplica-se conforme o cronograma de transição.',
      },
    ],
  },
  {
    term: 'Preço de Referência',
    slug: 'preco-de-referencia',
    definition:
      'Valor estimado pela administração como parametro do preço justo para a contratação. E obtido por pesquisa de mercado (mínimo 3 cotações), consulta a bancos de preços (Painel de Preços, SINAPI, SICRO) ou contratações anteriores similares. O preço de referência define o teto aceitável.',
    example:
      'Para licitação de notebooks, o órgão pesquisou: Painel de Preços (R$ 4.200), 3 cotações de mercado (média R$ 4.350) e ata de registro vigente (R$ 4.100). O preço de referência foi fixado em R$ 4.217 (média ponderada).',
    guideHref: '/blog',
    guideLabel: 'Pesquisa de preços em licitações',
    legalBasis: 'Lei 14.133/2021, art. 23; Decreto 12.002/2024',
    relatedTerms: ['edital', 'proposta-comercial', 'bdi'],
    faqEntries: [
      {
        question: 'O preço de referência deve ser sigiloso?',
        answer:
          'A Lei 14.133/2021 mantém o orçamento sigiloso até a fase de lances no pregão eletrônico — para evitar que fornecedores ajustem propostas ao teto. Após a abertura das propostas, o preço de referência é revelado. Em concorrências com critério técnica e preço, pode ser divulgado antes.',
      },
      {
        question: 'O que acontece se todas as propostas forem acima do preço de referência?',
        answer:
          'Se todas as propostas estiverem acima do preço de referência, o pregoeiro pode negociar com o primeiro colocado. Se a negociação não resultar em preço aceitável, a licitação pode ser declarada fracassada. O órgão deve revisar o orçamento antes de repetir o certame.',
      },
    ],
  },
  {
    term: 'Pregão Eletrônico',
    slug: 'pregao-eletronico',
    definition:
      'Modalidade licitatória realizada integralmente em plataforma digital, destinada a aquisição de bens e serviços comuns pelo critério de menor preço ou maior desconto. E a modalidade mais utilizada no Brasil, respondendo por mais de 80% das licitações federais. A fase de lances permite redução competitiva dos preços em tempo real.',
    example:
      'No pregão eletrônico para 1.000 licencas de antivirus, 8 empresas participaram da fase de lances que durou 15 minutos. O preço caiu de R$ 89/licenca para R$ 52/licenca — economia de 42% para a administração.',
    guideHref: '/blog',
    guideLabel: 'Guia completo do pregão eletrônico',
    legalBasis: 'Lei 14.133/2021, art. 28, § 2º; Lei 10.520/2002 (revogada gradualmente)',
    relatedTerms: ['ata-de-registro-de-precos', 'lance', 'comprasnet'],
    faqEntries: [
      {
        question: 'Qual a diferença entre pregão eletrônico e pregão presencial?',
        answer:
          'O pregão eletrônico é realizado integralmente em plataforma digital (PNCP, BEC, BLL, etc.), permitindo participação de todo o Brasil. O pregão presencial ocorre em sessão física no órgão licitante. A Lei 14.133/2021 exige que o pregão seja preferencialmente eletrônico.',
      },
      {
        question: 'Quem pode participar de pregão eletrônico?',
        answer:
          'Qualquer empresa com CNPJ ativo pode participar de pregão eletrônico, desde que cadastrada na plataforma do certame (PNCP, SICAF ou sistema similar) e sem sanções vigentes. Não há exigência de credenciamento prévio na maioria dos portais.',
      },
    ],
  },
  {
    term: 'Proposta Comercial',
    slug: 'proposta-comercial',
    definition:
      'Documento formal apresentado pelo licitante contendo preços, condições de pagamento, prazo de entrega e validade da oferta. Deve seguir rigorosamente o modelo exigido no edital. A proposta vincula o licitante, que não pode alterala após a abertura, exceto em negociação com o pregoeiro.',
    example:
      'A proposta comercial para fornecimento de 200 impressoras incluiu: preço unitário R$ 1.890, prazo de entrega 30 dias, garantia 36 meses on-site, validade da proposta 90 dias, conforme modelo do Anexo II do edital.',
    guideHref: '/blog',
    guideLabel: 'Como elaborar propostas vencedoras',
    legalBasis: 'Lei 14.133/2021, art. 59',
    relatedTerms: ['edital', 'preco-de-referencia', 'proposta-tecnica'],
    faqEntries: [
      {
        question: 'Por quanto tempo a proposta comercial deve ter validade?',
        answer:
          'O edital define o prazo de validade da proposta, geralmente 60 ou 90 dias. A proposta vincula o licitante durante esse período — ele não pode retirá-la ou alterá-la após a abertura da sessão. A prorrogação da validade pode ser solicitada pelo órgão com anuência do licitante.',
      },
      {
        question: 'O que ocorre se a proposta comercial não seguir o modelo do edital?',
        answer:
          'A proposta em desconformidade com o modelo do edital pode ser desclassificada, dependendo da gravidade da irregularidade. Erros formais leves (digitação, formatação) costumam ser relevados. Ausência de informações essenciais (preço unitário, validade) leva à desclassificação.',
      },
    ],
  },
  {
    term: 'Proposta Técnica',
    slug: 'proposta-tecnica',
    definition:
      'Documento que descreve a solução técnica, metodologia, equipe e plano de trabalho ofertados pelo licitante em licitações do tipo "técnica e preço" ou "melhor técnica". E avaliada por comissão técnica segundo critérios objetivos definidos no edital.',
    example:
      'Na licitação de consultoria ambiental (técnica e preço, peso 60/40), a proposta técnica incluiu: metodologia de diagnóstico em 3 fases, equipe de 8 especialistas com curriculos, cronograma detalhado de 180 dias e 3 estudos de caso similares.',
    guideHref: '/blog',
    guideLabel: 'Licitações de técnica e preço',
    legalBasis: 'Lei 14.133/2021, art. 36–37',
    relatedTerms: ['proposta-comercial', 'concorrencia', 'atestado-de-capacidade-tecnica'],
    faqEntries: [
      {
        question: 'Em quais modalidades é exigida proposta técnica?',
        answer:
          'A proposta técnica é exigida nas licitações com critério de julgamento "melhor técnica" (apenas proposta técnica) ou "técnica e preço" (ambas). É comum em contratações de serviços de TI, consultoria, projetos de engenharia complexos e serviços de saúde especializados.',
      },
      {
        question: 'A proposta técnica pode ser ajustada após a abertura do certame?',
        answer:
          'Não. A proposta técnica é imutável após a abertura da sessão. A comissão avalia exatamente o que foi submetido. Por isso, é fundamental revisar a proposta técnica antes do envio, verificando se atende a todos os subcritérios de pontuação definidos no edital.',
      },
    ],
  },
  // R
  {
    term: 'Recebimento Definitivo',
    slug: 'recebimento-definitivo',
    definition:
      'Ato formal que confirma a aceitação final do objeto contratado após verificação completa de qualidade, quantidade e conformidade com as específicacoes. Ocorre após o recebimento provisório é autoriza o pagamento integral remanescente. É realizado por comissão ou servidor designado.',
    example:
      'Após 15 dias de testes do sistema de gestão implantado, a comissão de recebimento emitiu o Termo de Recebimento Definitivo, atestando que os 47 requisitos funcionais do Termo de Referência foram atendidos integralmente.',
    guideHref: '/blog',
    guideLabel: 'Recebimento de objetos contratuais',
    legalBasis: 'Lei 14.133/2021, art. 140, II',
    relatedTerms: ['recebimento-provisorio', 'fiscalizacao', 'medicao'],
    faqEntries: [
      {
        question: 'Qual o prazo para recebimento definitivo após o provisório?',
        answer:
          'A Lei 14.133/2021 não fixa prazo único — o prazo deve ser estipulado no contrato ou edital, adequado à natureza do objeto. Para bens, costuma ser 15 a 30 dias. Para obras, pode ser 90 dias. Para serviços de TI com período de garantia, pode ser mais longo.',
      },
      {
        question: 'O recebimento definitivo encerra a responsabilidade do contratado?',
        answer:
          'Não completamente. O recebimento definitivo encerra a responsabilidade pela execução do contrato, mas não extingue a garantia dos bens/obras pelo prazo legal (5 anos para obras pelo Código Civil, e conforme garantia contratual). Vícios ocultos descobertos após o recebimento podem gerar responsabilidade.',
      },
    ],
  },
  {
    term: 'Recebimento Provisório',
    slug: 'recebimento-provisorio',
    definition:
      'Aceite inicial do objeto contratado, realizado pelo fiscal para fins de posterior verificação detalhada de conformidade. Não constitui aceite definitivo — é uma etapa intermediária que permite a administração conferir qualidade e quantidade antes do recebimento definitivo.',
    example:
      'O fiscal do contrato emitiu recebimento provisório das 500 cadeiras escolares no ato da entrega, verificando apenas quantidade e integridade das embalagens. A conferência detalhada (material, dimensões, acabamento) foi realizada nos 15 dias seguintes.',
    guideHref: '/blog',
    guideLabel: 'Recebimento de objetos contratuais',
    legalBasis: 'Lei 14.133/2021, art. 140, I',
    relatedTerms: ['recebimento-definitivo', 'fiscalizacao', 'contrato-administrativo'],
    faqEntries: [
      {
        question: 'O prazo de pagamento começa do recebimento provisório ou definitivo?',
        answer:
          'O prazo de pagamento começa após a liquidação da despesa, que ocorre com o recebimento definitivo e emissão da nota fiscal. O recebimento provisório não autoriza o pagamento integral. Pode-se pagar parcialmente após o provisório se o contrato assim prever.',
      },
      {
        question: 'O que ocorre se o objeto tiver defeito após o recebimento provisório?',
        answer:
          'O contratado deve sanar os defeitos antes do recebimento definitivo, sem ônus para a administração. Se recusar ou não for possível, o objeto pode ser recusado, abrindo prazo para substituição. A recusa reiterada pode ensejar penalidades contratuais.',
      },
    ],
  },
  {
    term: 'Recurso',
    slug: 'recurso',
    definition:
      'Instrumento processual pelo qual o licitante pede revisão de decisão tomada durante a licitação (habilitação, julgamento, adjudicação). Na Lei 14.133, o prazo para recurso e de 3 dias úteis após a públicação do ato, com efeito suspensivo automático.',
    example:
      'A empresa classificada em 2o lugar interpôs recurso contra a habilitação da vencedora, demonstrando que o atestado de capacidade técnica apresentado não atingia 50% do quantitativo exigido. O recurso foi provido e a recorrente foi declarada vencedora.',
    guideHref: '/blog',
    guideLabel: 'Recursos em licitações',
    legalBasis: 'Lei 14.133/2021, art. 165–168',
    relatedTerms: ['adjudicacao', 'habilitacao', 'impugnacao'],
    faqEntries: [
      {
        question: 'Qual o prazo para interpor recurso em pregão eletrônico?',
        answer:
          'No pregão, o licitante deve manifestar intenção de recorrer imediatamente após o anúncio do vencedor, sob pena de preclusão. Após aceita a intenção, tem 3 dias úteis para apresentar as razões do recurso, e os demais licitantes têm 3 dias úteis para contrarrazões.',
      },
      {
        question: 'O recurso tem efeito suspensivo automático?',
        answer:
          'No pregão, a mera intenção de recurso não suspende o certame — apenas a decisão que aceitar o recurso. Na Lei 14.133, os recursos contra decisões da fase de habilitação e julgamento têm efeito suspensivo. O pregoeiro pode negar provimento sem efeito suspensivo.',
      },
    ],
  },
  {
    term: 'Reequilíbrio Econômico-Financeiro',
    slug: 'reequilibrio-economico-financeiro',
    definition:
      'Mecanismo de restauração das condições econômicas originais do contrato quando eventos imprevisíveis e extraordinários alteram significativamente os custos. Diferencia-se do reajuste (previsível, por índice) pôr exigir comprovação de fato superveniente e impacto financeiro concreto.',
    example:
      'Após aumento de 40% no preço do aco em 3 meses devido a crise logística global, a construtora solicitou reequilíbrio do contrato de obra, apresentando notas fiscais comparativas que demonstravam impacto de R$ 1,2 milhão sobre o custo original.',
    guideHref: '/blog',
    guideLabel: 'Reequilíbrio e reajuste contratual',
    legalBasis: 'Constituição Federal, art. 37, XXI; Lei 14.133/2021, art. 124–125',
    relatedTerms: ['reajuste', 'matriz-de-riscos', 'aditivo-contratual'],
    faqEntries: [
      {
        question: 'Quais documentos são necessários para pedir reequilíbrio econômico-financeiro?',
        answer:
          'O pedido deve incluir: (1) descrição do evento imprevisível e extraordinário; (2) notas fiscais de compra antes e após o evento; (3) planilha demonstrando o impacto no custo do contrato; (4) documentação que comprove a relação de causalidade entre o evento e o desequilíbrio.',
      },
      {
        question: 'Reajuste anual e reequilíbrio podem ser pedidos simultaneamente?',
        answer:
          'Sim, mas são pedidos independentes. O reajuste é automático pelo índice contratual e aplica-se ao valor total. O reequilíbrio é excepcional e aplica-se apenas ao item/insumo afetado pelo evento imprevisível. Os dois podem coexistir em um mesmo contrato.',
      },
    ],
  },
  {
    term: 'Reajuste',
    slug: 'reajuste',
    definition:
      'Atualização periódica do valor contratual com base em índice de preços préviamente definido no contrato (IPCA, IGPM, INPC ou índice setorial). O reajuste e aplicado anualmente, a partir da data da proposta, e não depende de comprovação de desequilíbrio — e automático conforme cláusula contratual.',
    example:
      'O contrato de serviços de vigilância prévia reajuste anual pelo IPCA. Após 12 meses, o índice acumulado foi de 4,87%, e o valor mensal foi reajustado de R$ 120.000 para R$ 125.844 automaticamente.',
    guideHref: '/blog',
    guideLabel: 'Reequilíbrio e reajuste contratual',
    legalBasis: 'Lei 14.133/2021, art. 92, V',
    relatedTerms: ['reequilibrio-economico-financeiro', 'aditivo-contratual', 'contrato-administrativo'],
    faqEntries: [
      {
        question: 'O reajuste precisa ser pedido ou é aplicado automaticamente?',
        answer:
          'O reajuste deve ser solicitado formalmente pelo contratado, mesmo que a cláusula contratual seja automática. O prazo para pedido costuma ser determinado no contrato. A falta de pedido no prazo pode gerar preclusão do direito ao reajuste do período.',
      },
      {
        question: 'Qual índice de reajuste é mais comum em contratos de serviços continuados?',
        answer:
          'Para serviços com predominância de mão de obra, costuma-se usar o INPC ou o dissídio da categoria profissional. Para contratos de materiais, usa-se IPCA ou índices setoriais (INCC para construção, IPC para insumos industriais). A escolha deve refletir a composição de custos do serviço.',
      },
    ],
  },
  {
    term: 'Revogação',
    slug: 'revogacao',
    definition:
      'Anulação da licitação por razões de interesse público superveniente, devidamente justificadas pela autoridade competente. Diferente da anulação (por ilegalidade), a revogação decorre de conveniência administrativa e tem efeito a partir da decisão (ex nunc).',
    example:
      'A prefeitura revogou a licitação para construção de quadra esportiva porque o terreno previsto foi desaprópriado para passagem de via expressa estadual, inviabilizando o projeto original.',
    guideHref: '/blog',
    guideLabel: 'Anulação e revogação de licitações',
    legalBasis: 'Lei 14.133/2021, art. 71',
    relatedTerms: ['anulacao', 'edital', 'adjudicacao'],
    faqEntries: [
      {
        question: 'A administração pode revogar uma licitação após a adjudicação?',
        answer:
          'Sim, mas com maior rigor. Após a adjudicação, a revogação pode gerar direito à indenização para o adjudicatário pelos prejuízos comprovados. A administração deve demonstrar que o interesse público superveniente é de alta relevância e que não havia como prevê-lo.',
      },
      {
        question: 'O licitante pode questionar a revogação de uma licitação?',
        answer:
          'Sim. O licitante pode impugnar a revogação administrativa via recurso administrativo (3 dias úteis) ou ação judicial. A revogação deve ser fundamentada — motivação genérica ou insuficiente pode ser anulada pelo Judiciário ou pelo TCU.',
      },
    ],
  },
  // S
  {
    term: 'Sistema de Registro de Preços (SRP)',
    slug: 'sistema-de-registro-de-precos',
    definition:
      'Conjunto de procedimentos para registro formal de preços com fornecedores, permitindo contratações futuras nas quantidades e prazos necessários, sem obrigatoriedade de compra. É formalizado por Ata de Registro de Preços com validade de até 1 ano. Ideal para compras frequentes com quantidades incertas.',
    example:
      'O governo estadual registrou preços de 200 itens de informática via SRP. Durante 12 meses, 45 órgãos participantes emitiram 312 ordens de compra totalizando R$ 18 milhões — sem precisar realizar nova licitação para cada aquisição.',
    guideHref: '/blog',
    guideLabel: 'SRP: vantagens e como participar',
    legalBasis: 'Lei 14.133/2021, art. 82–86; Decreto 11.462/2023',
    relatedTerms: ['ata-de-registro-de-precos', 'pregao-eletronico', 'nota-de-empenho'],
    faqEntries: [
      {
        question: 'Quais as vantagens de participar de SRP como fornecedor?',
        answer:
          'O SRP garante ao fornecedor: previsibilidade de receita durante 12 meses, múltiplos pedidos de vários órgãos sem novas licitações, menos burocracia (uma licitação, múltiplas vendas) e registro formal do preço com reajuste previsto. É especialmente vantajoso para produtores de bens padronizados.',
      },
      {
        question: 'O fornecedor registrado em SRP é obrigado a atender todos os pedidos?',
        answer:
          'Sim, dentro da validade da ata e do quantitativo máximo registrado. A recusa injustificada de fornecimento pode ensejar cancelamento do registro e aplicação de penalidades. Se não puder atender, deve comunicar com antecedência para a administração acionar o próximo fornecedor registrado.',
      },
    ],
  },
];
