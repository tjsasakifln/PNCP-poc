/**
 * Shared Q&A registry for SmartLic public procurement FAQ pages (S10).
 *
 * Used by:
 * - /perguntas (hub page)
 * - /perguntas/[slug] (individual question pages)
 *
 * 53 questions across 6 categories covering Brazilian public procurement
 * under Lei 14.133/2021 with references to PNCP data where applicable.
 */

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export type QuestionCategory =
  | 'modalidades'
  | 'prazos-cronogramas'
  | 'documentacao-habilitacao'
  | 'precos-propostas'
  | 'setores-especificos'
  | 'tecnologia-sistemas';

export interface Question {
  slug: string;
  title: string;
  category: QuestionCategory;
  answer: string;
  legalBasis?: string;
  relatedTerms: string[];
  relatedSectors: string[];
  relatedArticles: string[];
  metaDescription: string;
}

/* ------------------------------------------------------------------ */
/*  Category metadata                                                  */
/* ------------------------------------------------------------------ */

export const CATEGORY_META: Record<
  QuestionCategory,
  { label: string; description: string }
> = {
  modalidades: {
    label: 'Modalidades de Licitação',
    description:
      'Pregão, concorrência, dispensa, inexigibilidade e outras modalidades da Lei 14.133/2021.',
  },
  'prazos-cronogramas': {
    label: 'Prazos e Cronogramas',
    description:
      'Prazos legais para impugnação, recurso, publicação, vigência e pagamento em licitações.',
  },
  'documentacao-habilitacao': {
    label: 'Documentação e Habilitação',
    description:
      'Documentos exigidos, SICAF, certidões, atestados e qualificação técnica.',
  },
  'precos-propostas': {
    label: 'Preços e Propostas',
    description:
      'Calculo de preços, BDI, inexequibilidade, reequilíbrio e registro de preços.',
  },
  'setores-especificos': {
    label: 'Setores Específicos',
    description:
      'Requisitos especiais por setor: TI, saúde, engenharia, alimentos, facilities.',
  },
  'tecnologia-sistemas': {
    label: 'Tecnologia e Sistemas',
    description:
      'PNCP, ComprasNet, certificado digital, assinatura eletrônica e IA em licitações.',
  },
};

/* ------------------------------------------------------------------ */
/*  Questions                                                          */
/* ------------------------------------------------------------------ */

export const QUESTIONS: Question[] = [
  /* ================================================================ */
  /*  MODALIDADES (10)                                                 */
  /* ================================================================ */
  {
    slug: 'o-que-e-pregao-eletronico',
    title: 'O que e pregão eletrônico e como funciona?',
    category: 'modalidades',
    answer:
      'O pregão eletrônico e a modalidade de licitação mais utilizada no Brasil para aquisição de bens e serviços comuns. Funciona inteiramente pela internet, em plataformas como o ComprasNet (ComprasGov) ou sistemas estaduais/municipais homologados.\n\n' +
      'Na Lei 14.133/2021, o pregão está previsto nos artigos 6, inciso XLI, e 29, sendo obrigatoriamente na forma eletrônica (art. 17, parágrafo 2). O processo segue estas etapas principais:\n\n' +
      '1. **Publicação do edital** no PNCP e em jornal de grande circulação, com prazo mínimo de 8 dias úteis para bens/serviços comuns.\n' +
      '2. **Fase de propostas** em que os licitantes registram seus preços iniciais no sistema eletrônico.\n' +
      '3. **Fase de lances** com disputa em tempo real, onde os participantes reduzem progressivamente seus preços. O modo de disputa pode ser aberto (lances públicos em tempo real), fechado (proposta única) ou aberto-fechado (combinação).\n' +
      '4. **Julgamento** pelo menor preço ou maior desconto, critérios obrigatórios para o pregão.\n' +
      '5. **Habilitação** apenas do licitante classificado em primeiro lugar (inversão de fases em relação a concorrência tradicional).\n' +
      '6. **Adjudicação e homologação** pela autoridade competente.\n\n' +
      'O pregão eletrônico oferece vantagens significativas: maior competitividade (participantes de todo o país), transparência (lances registrados eletronicamente), economia (redecoes médias de 20-30% sobre o preço estimado) e celeridade (processos concluídos em dias, não meses).\n\n' +
      'Para participar, a empresa precisa de certificado digital válido (tipo A1 ou A3), cadastro no sistema eletrônico correspondente (SICAF para o federal) e documentos de habilitação atualizados. é fundamental acompanhar o chat do sistema durante a sessão, pois o pregoeiro pode solicitar esclarecimentos em tempo real.',
    legalBasis: 'Lei 14.133/2021, arts. 6 (XLI), 17 (par. 2), 29',
    relatedTerms: ['pregao-eletronico', 'lance', 'pregoeiro'],
    relatedSectors: [],
    relatedArticles: ['pregao-eletronico-guia-passo-a-passo'],
    metaDescription:
      'Entenda o que e pregão eletrônico, como funciona na Lei 14.133/2021, etapas do processo, e como participar de licitações online.',
  },
  {
    slug: 'diferenca-pregao-concorrencia',
    title: 'Qual a diferença entre pregão e concorrência na Lei 14.133?',
    category: 'modalidades',
    answer:
      'Pregão e concorrência são as duas principais modalidades de licitação na Lei 14.133/2021 e possuem diferenças fundamentais quanto ao objeto, critério de julgamento, prazos e procedimento.\n\n' +
      '**Pregão** (art. 29): exclusivo para aquisição de bens e serviços comuns, cujos padrões de desempenho e qualidade possam ser objetivamente definidos pelo edital. O critério de julgamento é obrigatoriamente menor preço ou maior desconto. O prazo mínimo de publicação e de 8 dias úteis. A fase de habilitação ocorre após o julgamento (inversão de fases), tornando o processo mais ágil.\n\n' +
      '**Concorrência** (art. 29, II): utilizada para obras, serviços especiais, compras de grande vulto e qualquer objeto que não se enquadre como bem ou serviço comum. Admite critérios de julgamento variados: menor preço, melhor técnica, técnica e preço, maior retorno econômico ou maior lance. O prazo mínimo de publicação e mais longo — 25 dias úteis para técnica e preço, 15 dias úteis para demais casos.\n\n' +
      '**Principais diferenças práticas:**\n\n' +
      '| Aspecto | Pregão | Concorrência |\n' +
      '|---------|--------|--------------|\n' +
      '| Objeto | Bens/serviços comuns | Obras, serviços especiais, qualquer objeto |\n' +
      '| Critério | Menor preço/maior desconto | Vários critérios |\n' +
      '| Prazo edital | 8 dias úteis | 15-25 dias úteis |\n' +
      '| Fase habilitação | Após julgamento | Antes ou após (escolha do gestor) |\n' +
      '| Forma | Obrigatoriamente eletrônica | Preferencialmente eletrônica |\n\n' +
      'Na prática, o pregão corresponde a cerca de 80% das licitações federais por volume, dada sua agilidade. A concorrência e predominante em obras de engenharia e contratações complexas que exigem avaliação técnica qualitativa. A Lei 14.133 permite que o gestor escolha a inversão de fases também na concorrência, aproximando os procedimentos.',
    legalBasis: 'Lei 14.133/2021, arts. 28, 29, 33, 34',
    relatedTerms: ['pregao-eletronico', 'concorrencia', 'modalidade'],
    relatedSectors: [],
    relatedArticles: ['pregao-eletronico-guia-passo-a-passo'],
    metaDescription:
      'Compare pregão e concorrência na Lei 14.133/2021: objeto, critérios de julgamento, prazos e quando usar cada modalidade.',
  },
  {
    slug: 'quando-usar-dispensa-licitacao',
    title: 'Quando é possível usar dispensa de licitação?',
    category: 'modalidades',
    answer:
      'A dispensa de licitação é a contratação direta permitida por lei em situações específicas onde o processo licitatório é inexigível na prática ou inconveniente ao interesse público. A Lei 14.133/2021 traz as hipóteses de dispensa no artigo 75.\n\n' +
      '**Principais hipóteses de dispensa (art. 75):**\n\n' +
      '1. **Por valor (incisos I e II):** Obras e serviços de engenharia até R$ 119.812,20 (atualizado por decreto); demais compras e serviços até R$ 59.906,10. Esses limites são atualizados anualmente pelo IPCA.\n' +
      '2. **Emergência ou calamidade (inciso VIII):** Contratação direta para atender situação emergencial que possa causar prejuízo ou comprometer a continuidade de serviços públicos. Vigência máxima de 1 ano, improrrogável.\n' +
      '3. **Licitação deserta ou fracassada (incisos III e IV):** Quando nenhum interessado comparece ou todas as propostas são desclassificadas, desde que mantidas as condições do edital.\n' +
      '4. **Compras entre órgãos (inciso IX):** Aquisição de bens por órgão integrante da administração junto a outro ente público.\n' +
      '5. **Gêneros perecíveis (inciso IV, alínea d):** Compra de alimentos frescos durante o tempo necessário para realização de processo licitatório.\n' +
      '6. **Pesquisa e inovação (inciso V):** Contratação de instituição brasileira dedicada a pesquisa, ensino ou desenvolvimento tecnológico.\n\n' +
      '**Procedimento obrigatório:** Mesmo na dispensa, a Lei 14.133 exige procedimento simplificado: pesquisa de preços com no mínimo 3 cotações, justificativa da situação, parecer jurídico, publicação no PNCP e comprovação de que o contratado atende aos requisitos de habilitação. O processo deve ser transparente e auditável.\n\n' +
      '**Atenção:** A Lei 14.133 criou a "dispensa eletrônica" (art. 75, parágrafo 3), processo simplificado conduzido em plataforma digital que amplia a competitividade mesmo nas contratações diretas.',
    legalBasis: 'Lei 14.133/2021, art. 75',
    relatedTerms: ['dispensa', 'licitacao', 'edital'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Saiba quando a dispensa de licitação é permitida pela Lei 14.133/2021: limites de valor, emergência, licitação deserta e mais.',
  },
  {
    slug: 'o-que-e-inexigibilidade',
    title: 'O que é inexigibilidade de licitação e quais os requisitos?',
    category: 'modalidades',
    answer:
      'A inexigibilidade de licitação ocorre quando a competição é inviável, ou seja, quando não é possível realizar um processo licitatório porque só existe um fornecedor capaz de atender a demanda, ou porque o objeto possui características tão singulares que tornam a comparação entre propostas impossível.\n\n' +
      'A Lei 14.133/2021 disciplina a inexigibilidade no artigo 74, estabelecendo três hipóteses principais:\n\n' +
      '1. **Fornecedor exclusivo (inciso I):** Aquisição de materiais, equipamentos ou gêneros que só possam ser fornecidos por produtor, empresa ou representante comercial exclusivo. A exclusividade deve ser comprovada por atestado de exclusividade emitido pelo órgão competente (como Juntas Comerciais ou sindicatos patronais).\n\n' +
      '2. **Serviços técnicos especializados (inciso III):** Contratação de profissionais ou empresas de notória especialização para serviços listados no art. 74, inciso III (pareceres, auditorias, consultorias, patrocinio jurídico, treinamentos, restauração de obras de arte, entre outros). A notória especialização deve ser comprovada por publicações, experiência e reconhecimento no mercado.\n\n' +
      '3. **Profissional do setor artístico (inciso II):** Contratação de artista consagrado pela crítica especializada ou pela opinião pública.\n\n' +
      '**Requisitos obrigatórios para inexigibilidade:**\n' +
      '- Justificativa fundamentada da inviabilidade de competição\n' +
      '- Razão da escolha do contratado\n' +
      '- Justificativa do preço (pesquisa de mercado ou comprovação de compatibilidade)\n' +
      '- Parecer jurídico aprovando a contratação\n' +
      '- Publicação no PNCP em até 10 dias úteis\n\n' +
      'A diferença fundamental em relação a dispensa é que na inexigibilidade a competição e IMPOSSIVEL (não ha alternativa), enquanto na dispensa a competição é possível mas a lei AUTORIZA a contratação direta por conveniência. A inexigibilidade é uma constatação factual; a dispensa é uma opção legal.',
    legalBasis: 'Lei 14.133/2021, art. 74',
    relatedTerms: ['inexigibilidade', 'licitacao', 'proposta'],
    relatedSectors: ['consultoria'],
    relatedArticles: [],
    metaDescription:
      'Entenda o que é inexigibilidade de licitação na Lei 14.133/2021: hipóteses, requisitos legais e diferença para dispensa.',
  },
  {
    slug: 'dialogo-competitivo-quando-usar',
    title: 'O que é diálogo competitivo e quando usar?',
    category: 'modalidades',
    answer:
      'O diálogo competitivo é uma modalidade de licitação introduzida pela Lei 14.133/2021 (art. 32) para contratações complexas em que a administração não consegue definir com precisão a solução técnica ou as condições comerciais mais adequadas. E inspirado no modelo europeu (Competitive Dialogue) e representa uma inovação significativa no ordenamento jurídico brasileiro.\n\n' +
      '**Quando usar o diálogo competitivo:**\n\n' +
      '1. **Inovação tecnológica ou técnica:** Quando o órgão público precisa de solução inovadora e não consegue especificar antecipadamente todos os requisitos técnicos.\n' +
      '2. **Impossibilidade de definir meios de execução:** Quando ha múltiplas abordagens possíveis e o gestor não tem certeza de qual é a mais adequada.\n' +
      '3. **Necessidade de adaptação de soluções disponíveis:** Quando as soluções de mercado precisam ser customizadas.\n\n' +
      '**Como funciona o processo:**\n\n' +
      '1. **Pre-seleção:** O órgão pública edital com os requisitos mínimos e critérios de pre-seleção. Empresas interessadas se candidatam e são pre-qualificadas.\n' +
      '2. **Fase de diálogo:** O órgão dialoga individualmente com cada participante pre-selecionado (mínimo 3) para explorar soluções técnicas e comerciais. As discussões são confidenciais — nenhuma informação de um participante e compartilhada com os demais sem autorização.\n' +
      '3. **Fase competitiva:** Após encerrar o diálogo, o órgão elabora os critérios definitivos e convida os participantes a apresentarem propostas finais.\n' +
      '4. **Julgamento e contratação:** As propostas são avaliadas pelos critérios definidos.\n\n' +
      '**Requisitos importantes:** Mínimo de 3 participantes pre-selecionados; comissão de contratação com pelo menos 3 membros; sigilo das informações compartilhadas durante o diálogo; e publicação no PNCP com prazo mínimo de 25 dias úteis.\n\n' +
      'Na prática, o diálogo competitivo é indicado para projetos de TI complexos, PPPs e concessões inovadoras.',
    legalBasis: 'Lei 14.133/2021, art. 32',
    relatedTerms: ['modalidade', 'edital', 'licitacao'],
    relatedSectors: ['informatica'],
    relatedArticles: [],
    metaDescription:
      'Saiba o que é diálogo competitivo na Lei 14.133/2021, quando usar, etapas do processo é requisitos para participar.',
  },
  {
    slug: 'leilao-eletronico-como-funciona',
    title: 'Como funciona o leilão eletrônico na Lei 14.133?',
    category: 'modalidades',
    answer:
      'O leilão é a modalidade de licitação utilizada para alienação (venda) de bens imóveis ou móveis inservibles pela administração pública. Na Lei 14.133/2021, o leilão está previsto no artigo 31 e pode ser realizado na forma eletrônica ou presencial.\n\n' +
      '**Quando o leilão é utilizado:**\n\n' +
      '1. **Bens móveis inservibles:** Veiculos, equipamentos, mobiliário e materiais em desuso que não atendem mais ao serviço público.\n' +
      '2. **Bens imóveis:** Predios, terrenos e outros imóveis cuja alienação seja autorizada por lei.\n' +
      '3. **Bens apreendidos ou penhorados:** Produtos apreendidos por órgãos fiscalizadores ou penhorados em execuções fiscais.\n' +
      '4. **Produtos legalmente apreendidos ou abandonados:** Mercadorias apreendidas pela Receita Federal, por exemplo.\n\n' +
      '**Como funciona o leilão eletrônico:**\n\n' +
      '1. **Publicação:** O edital é publicado no PNCP com prazo mínimo de 15 dias úteis, descrevendo os bens, o valor mínimo de arrematação (avaliação prévia obrigatória) e as condições de pagamento.\n' +
      '2. **Visitação:** Período para que os interessados inspecionem os bens pessoalmente.\n' +
      '3. **Sessão de lances:** Os participantes oferecem lances crescentes em plataforma eletrônica. O critério de julgamento é obrigatoriamente o maior lance.\n' +
      '4. **Arrematação:** O bem é adjudicado ao autor do maior lance que atinja ou supere o valor mínimo.\n' +
      '5. **Pagamento e retirada:** O arrematante efetua o pagamento nas condições do edital e retira o bem.\n\n' +
      '**Particularidades importantes:**\n' +
      '- O leiloeiro pode ser servidor designado ou leiloeiro oficial (art. 31, parágrafo 1).\n' +
      '- Bens imóveis exigem avaliação prévia e autorização legislativa.\n' +
      '- O leilão e aberto a qualquer interessado — não exige cadastro prévio no SICAF.\n' +
      '- A comissão do leiloeiro oficial é fixada no edital (em geral 5% sobre o valor da arrematação).\n\n' +
      'O leilão eletrônico tem crescido significativamente, com plataformas como o Licitações-e (Banco do Brasil) e o próprio ComprasGov disponibilizando modulos de leilão.',
    legalBasis: 'Lei 14.133/2021, art. 31',
    relatedTerms: ['modalidade', 'licitacao', 'edital'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Entenda como funciona o leilão eletrônico na Lei 14.133/2021: quando é usado, etapas do processo e como participar.',
  },
  {
    slug: 'concorrencia-eletronica-passo-a-passo',
    title: 'Como participar de uma concorrência eletrônica?',
    category: 'modalidades',
    answer:
      'A concorrência eletrônica é a modalidade utilizada para contratações de maior complexidade — obras de engenharia, serviços especiais, concessões e compras de grande vulto. Na Lei 14.133/2021, a concorrência e disciplinada nos artigos 29 a 30 e deve ser preferencialmente na forma eletrônica.\n\n' +
      '**Passo a passo para participar:**\n\n' +
      '**1. Identificação da oportunidade:**\n' +
      'Monitore publicações no PNCP (Portal Nacional de Contratações Públicas), diários oficiais e portais de compras estaduais/municipais. Use ferramentas como o SmartLic para receber alertas automatizados por setor e região.\n\n' +
      '**2. Análise do edital:**\n' +
      'Leia atentamente todas as cláusulas, especialmente: objeto, critério de julgamento (menor preço, técnica e preço, melhor técnica), requisitos de habilitação, prazo de execução e condições de pagamento. O prazo para impugnação e de até 3 dias úteis antes da abertura.\n\n' +
      '**3. Preparação da documentação:**\n' +
      'Reuna os documentos de habilitação: jurídica, fiscal/trabalhista, econômico-financeira e técnica. Mantenha o SICAF atualizado se for licitação federal. Prepare atestados de capacidade técnica conforme exigido.\n\n' +
      '**4. Elaboração da proposta:**\n' +
      'Formule a proposta técnica (se aplicável) e a proposta de preços conforme modelo do edital. Em concorrências de técnica e preço, a proposta técnica e avaliada separadamente e tem peso na nota final.\n\n' +
      '**5. Envio no sistema eletrônico:**\n' +
      'Acesse a plataforma indicada no edital (ComprasGov, BEC-SP, Licitações-e, etc.) com seu certificado digital. Envie propostas e documentos dentro do prazo.\n\n' +
      '**6. Acompanhamento da sessão:**\n' +
      'Na data marcada, acompanhe a abertura das propostas, a fase de lances (se modo aberto) e a habilitação. Esteja preparado para responder diligências em até 2 horas.\n\n' +
      '**7. Recursos e contrato:**\n' +
      'Se classificado em primeiro lugar, aguarde a habilitação e o prazo recursal. Após a homologação, assine o contrato no prazo estipulado (em geral 5 dias corridos).',
    legalBasis: 'Lei 14.133/2021, arts. 29, 30, 33, 34',
    relatedTerms: ['concorrencia', 'habilitacao', 'proposta'],
    relatedSectors: ['engenharia', 'construcao'],
    relatedArticles: ['checklist-habilitacao-licitacao-2026'],
    metaDescription:
      'Guia passo a passo para participar de concorrência eletrônica: do edital a assinatura do contrato na Lei 14.133/2021.',
  },
  {
    slug: 'diferenca-dispensa-inexigibilidade',
    title: 'Qual a diferença entre dispensa e inexigibilidade?',
    category: 'modalidades',
    answer:
      'Dispensa e inexigibilidade são formas de contratação direta previstas na Lei 14.133/2021, mas possuem fundamentos jurídicos completamente diferentes. Entender essa distinção é essencial para fornecedores que desejam atuar no mercado público.\n\n' +
      '**Inexigibilidade (art. 74):**\n' +
      'Ocorre quando a competição é INVIAVEL — ou seja, não é possível comparar propostas porque só existe um fornecedor ou porque o objeto é singular. A inexigibilidade é uma constatação de fato. As hipóteses mais comuns são:\n' +
      '- Fornecedor exclusivo (comprovado por atestado)\n' +
      '- Serviços técnicos especializados de notória especialização\n' +
      '- Contratação de artista consagrado\n\n' +
      '**Dispensa (art. 75):**\n' +
      'Ocorre quando a competição é POSSIVEL, mas a lei AUTORIZA a contratação direta por razões de conveniência pública. A dispensa é uma opção legal. As hipóteses incluem:\n' +
      '- Valor abaixo dos limites legais (R$ 59.906,10 para compras; R$ 119.812,20 para obras)\n' +
      '- Situação de emergência ou calamidade\n' +
      '- Licitação deserta ou fracassada\n' +
      '- Compra de gêneros perecíveis\n\n' +
      '**Comparação direta:**\n\n' +
      '| Aspecto | Inexigibilidade | Dispensa |\n' +
      '|---------|----------------|----------|\n' +
      '| Competição | Inviável (impossível) | Possível (mas dispensada) |\n' +
      '| Natureza | Constatação factual | Autorização legal |\n' +
      '| Hipóteses | Rol exemplificativo (caput art. 74) | Rol taxativo (art. 75) |\n' +
      '| Justificativa | Comprovar singularidade/exclusividade | Enquadrar em hipótese legal |\n\n' +
      '**Para o fornecedor:** Se você e o único que atende determinada demanda, oriente o órgão público sobre a possibilidade de inexigibilidade — apresentando atestados de exclusividade ou comprovando notória especialização. Se o valor e pequeno, a dispensa por valor pode ser o caminho mais rapido. Em ambos os casos, a publicação no PNCP é obrigatória e a pesquisa de preços deve demonstrar compatibilidade com o mercado.',
    legalBasis: 'Lei 14.133/2021, arts. 74 e 75',
    relatedTerms: ['dispensa', 'inexigibilidade', 'licitacao'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Entenda a diferença entre dispensa e inexigibilidade de licitação na Lei 14.133/2021: fundamentos, hipóteses e quando usar.',
  },
  {
    slug: 'pregao-presencial-ainda-existe',
    title: 'O pregão presencial ainda existe na nova lei de licitações?',
    category: 'modalidades',
    answer:
      'A Lei 14.133/2021 estabelece que o pregão deve ser realizado PREFERENCIALMENTE na forma eletrônica (art. 17, parágrafo 2). Isso significa que o pregão presencial não foi expressamente extinto, mas sua utilização passou a ser excepcional é exige justificativa fundamentada.\n\n' +
      '**O que mudou na prática:**\n\n' +
      'Durante a vigência da Lei 10.520/2002 (antiga lei do pregão), o pregão presencial era amplamente utilizado, especialmente em municipios menores que não tinham infraestrutura tecnológica. Com a Lei 14.133/2021, houve uma forte orientação para a digitalização completa das compras públicas.\n\n' +
      '**Quando o pregão presencial pode ser usado:**\n' +
      '- Comprovada inviabilidade técnica do meio eletrônico (problemas de conectividade, por exemplo)\n' +
      '- Justificativa formal no processo administrativo\n' +
      '- Aprovação da autoridade superior\n\n' +
      'Na prática, a tendência é de extinção progressiva do pregão presencial. O Decreto Federal 10.024/2019, ainda vigente para regulamentação do pregão no ambito federal, já tornava o eletrônico obrigatório. Municipios que antes realizavam pregões presenciais estão migrando para plataformas eletrônicas como BLL, Compras BR, Portal de Compras Públicas e outros sistemas homologados.\n\n' +
      '**Impacto para fornecedores:**\n\n' +
      'A virtualização do pregão amplia significativamente o mercado para fornecedores, que podem participar de licitações em qualquer municipio do país sem deslocamento físico. Por outro lado, exige:\n' +
      '- Certificado digital ativo (tipo A1 ou A3 da ICP-Brasil)\n' +
      '- Familiaridade com as diferentes plataformas eletrônicas\n' +
      '- Conexão estável de internet durante as sessões\n' +
      '- Atenção aos prazos e notificações do sistema\n\n' +
      'Para empresas que atuam em licitações, o investimento em infraestrutura digital e treinamento de equipe para operação em plataformas eletrônicas e agora indispensável. O pregão presencial pode existir pontualmente, mas não deve ser considerado como estratégia de atuação.',
    legalBasis: 'Lei 14.133/2021, art. 17, par. 2',
    relatedTerms: ['pregao-eletronico', 'pregao-presencial', 'pregoeiro'],
    relatedSectors: [],
    relatedArticles: ['pregao-eletronico-guia-passo-a-passo'],
    metaDescription:
      'Descubra se o pregão presencial ainda existe na Lei 14.133/2021 e quais as exceções para sua utilização.',
  },
  {
    slug: 'manifestacao-interesse-pmi',
    title: 'O que é Procedimento de Manifestação de Interesse (PMI)?',
    category: 'modalidades',
    answer:
      'O Procedimento de Manifestação de Interesse (PMI) é um instrumento previsto na Lei 14.133/2021 (art. 81) que permite a administração pública solicitar ao setor privado a elaboração de estudos, projetos, levantamentos e investigações necessários para a estruturação de contratações complexas — especialmente concessões, parcerias público-privadas (PPPs) e grandes obras de infraestrutura.\n\n' +
      '**Como funciona o PMI:**\n\n' +
      '1. **Publicação do chamamento:** O órgão público pública edital convocando empresas, pessoas físicas ou jurídicas interessadas em apresentar projetos, estudos ou investigações para determinado empreendimento.\n' +
      '2. **Apresentação de propostas:** Os interessados elaboram e submetem seus estudos de viabilidade técnica, econômico-financeira, jurídica e ambiental.\n' +
      '3. **Avaliação:** O órgão avalia os estudos recebidos, podendo selecionar um ou combinar elementos de diferentes propostas.\n' +
      '4. **Ressarcimento:** Os autores dos estudos aproveitados tem direito ao ressarcimento dos custos, que sera pago pelo futuro contratado (vencedor da licitação) — não pelo órgão público.\n\n' +
      '**Pontos críticos do PMI:**\n\n' +
      '- O PMI NAO garante a contratação do proponente. O autor dos estudos pode participar da licitação subsequente, mas não tem preferência.\n' +
      '- Os estudos passam a ser propriedade da administração.\n' +
      '- Múltiplos interessados podem apresentar propostas concorrentes.\n' +
      '- A confidencialidade dos estudos é mantida até a publicação da licitação.\n\n' +
      '**Quando o PMI é estratégico para empresas:**\n\n' +
      'Participar de um PMI permite a empresa influenciar as especificações técnicas do futuro edital (dentro dos limites legais), demonstrar conhecimento técnico ao órgão público, obter informações privilegiadas sobre o empreendimento (que serão depois publicadas) e posicionar-se antecipadamente no mercado. É uma ferramenta estratégica especialmente para empresas de engenharia, consultoria e tecnologia que atuam em grandes projetos de infraestrutura.',
    legalBasis: 'Lei 14.133/2021, art. 81',
    relatedTerms: ['licitacao', 'edital', 'termo-referencia'],
    relatedSectors: ['engenharia', 'consultoria'],
    relatedArticles: [],
    metaDescription:
      'Saiba o que é o PMI (Procedimento de Manifestação de Interesse), como funciona e quando participar na Lei 14.133/2021.',
  },

  /* ================================================================ */
  /*  PRAZOS E CRONOGRAMAS (8)                                         */
  /* ================================================================ */
  {
    slug: 'prazo-impugnacao-edital',
    title: 'Qual o prazo para impugnar um edital de licitação?',
    category: 'prazos-cronogramas',
    answer:
      'A impugnação do edital e o instrumento pelo qual qualquer cidadão ou licitante pode questionar cláusulas ilegais, restritivas ou descabidas de um edital de licitação. Na Lei 14.133/2021, o prazo para impugnação está definido no artigo 164.\n\n' +
      '**Prazos de impugnação:**\n\n' +
      '- **Qualquer cidadão:** Até 3 (três) dias úteis ANTES da data de abertura das propostas.\n' +
      '- **Licitante:** Até 3 (três) dias úteis ANTES da data de abertura das propostas.\n\n' +
      'A Lei 14.133 unificou o prazo em 3 dias úteis para ambos os casos, diferente da legislação anterior que diferenciava os prazos. A impugnação deve ser feita preferencialmente por meio eletrônico, diretamente na plataforma onde a licitação está sendo conduzida.\n\n' +
      '**Procedimento de impugnação:**\n\n' +
      '1. **Apresentação:** Protocolar a impugnação pela plataforma eletrônica (ComprasGov, portal estadual/municipal) ou fisicamente no órgão.\n' +
      '2. **Resposta:** A administração tem o dever de responder em até 3 dias úteis, contados do recebimento.\n' +
      '3. **Efeito:** A impugnação NAO suspende automaticamente o processo licitatório. O órgão pode decidir suspender ou não, conforme a relevância da matéria.\n' +
      '4. **Recurso:** Se a impugnação for indeferida, o impugnante pode recorrer ao Tribunal de Contas ou ao Judiciário.\n\n' +
      '**Fundamentos válidos para impugnação:**\n' +
      '- Exigências de habilitação excessivas ou restritivas\n' +
      '- Especificações técnicas direcionadas a marca ou fornecedor\n' +
      '- Prazos de execução inexequíveis\n' +
      '- Critérios de julgamento inadequados ao objeto\n' +
      '- Ausência de pesquisa de preços adequada\n' +
      '- Violação de normas da Lei 14.133/2021\n\n' +
      '**Dica prática:** Leia o edital imediatamente após a publicação. Não deixe para analisar nos últimos dias — a fundamentação técnica e jurídica exige tempo de preparação. Impugnações bem fundamentadas com citação de jurisprudência do TCU tem maior probabilidade de acolhimento.',
    legalBasis: 'Lei 14.133/2021, art. 164',
    relatedTerms: ['impugnacao', 'edital', 'recurso'],
    relatedSectors: [],
    relatedArticles: ['impugnacao-edital-quando-como-contestar'],
    metaDescription:
      'Saiba o prazo para impugnar edital de licitação na Lei 14.133/2021: 3 dias úteis antes da abertura, para qualquer cidadão.',
  },
  {
    slug: 'prazo-recurso-licitacao',
    title: 'Qual o prazo para recurso em licitação?',
    category: 'prazos-cronogramas',
    answer:
      'O recurso administrativo e o meio pelo qual o licitante contesta decisões tomadas durante o processo licitatório. Na Lei 14.133/2021, os prazos recursais estão previstos nos artigos 165 a 168.\n\n' +
      '**Prazos de recurso na Lei 14.133/2021:**\n\n' +
      '- **Intenção de recurso:** Deve ser manifestada IMEDIATAMENTE após a declaração do vencedor, na própria sessão pública (presencial ou eletrônica).\n' +
      '- **Razões do recurso:** 3 (três) dias úteis contados a partir da manifestação de intenção.\n' +
      '- **Contrarrazões:** Os demais licitantes tem 3 (três) dias úteis para apresentar contrarrazões, contados do termino do prazo do recorrente.\n\n' +
      '**Decisões passíveis de recurso (art. 165):**\n' +
      '1. Julgamento das propostas\n' +
      '2. Habilitação ou inabilitação de licitante\n' +
      '3. Anulação ou revogação da licitação\n' +
      '4. Extinção do contrato\n' +
      '5. Aplicação de sanções\n\n' +
      '**Procedimento recursal:**\n\n' +
      '1. O licitante manifesta intenção de recurso imediatamente na sessão, com breve exposição de motivos.\n' +
      '2. O pregoeiro/comissão avalia a admissibilidade da intenção.\n' +
      '3. Se admitido, o recorrente tem 3 dias úteis para apresentar as razões escritas fundamentadas.\n' +
      '4. Os demais licitantes são notificados e tem 3 dias úteis para contrarrazões.\n' +
      '5. O pregoeiro/comissão analisa e decide — se mantiver a decisão, encaminha a autoridade superior.\n' +
      '6. A autoridade superior decide em até 10 dias úteis.\n\n' +
      '**Efeito suspensivo:** O recurso contra o julgamento de propostas e habilitação tem efeito suspensivo automático — o processo fica paralisado até a decisão. Recursos contra anulação e sanções também possuem efeito suspensivo.\n\n' +
      '**Dica prática:** A manifestação de intenção de recurso é OBRIGATORIA para preservar o direito. Se o licitante não se manifestar imediatamente na sessão, perde o prazo — não existe segunda chance. Esteja sempre presente (ou com representante) na sessão de abertura.',
    legalBasis: 'Lei 14.133/2021, arts. 165 a 168',
    relatedTerms: ['recurso', 'adjudicacao', 'homologacao'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Entenda os prazos para recurso em licitação na Lei 14.133: intenção imediata, 3 dias para razões e 3 para contrarrazões.',
  },
  {
    slug: 'prazo-publicacao-edital',
    title: 'Qual o prazo mínimo de publicação de edital na Lei 14.133?',
    category: 'prazos-cronogramas',
    answer:
      'A Lei 14.133/2021 estabelece prazos mínimos entre a publicação do edital e a data de abertura das propostas, variando conforme a modalidade e o critério de julgamento. Esses prazos estão definidos no artigo 55.\n\n' +
      '**Prazos mínimos de publicação:**\n\n' +
      '| Situação | Prazo Mínimo |\n' +
      '|----------|-------------|\n' +
      '| Concorrência — técnica e preço | 25 dias úteis |\n' +
      '| Concorrência — menor preço/maior desconto | 15 dias úteis |\n' +
      '| Pregão — bens e serviços comuns | 8 dias úteis |\n' +
      '| Leilão | 15 dias úteis |\n' +
      '| Diálogo competitivo | 25 dias úteis |\n' +
      '| Concurso | 35 dias úteis |\n\n' +
      '**Regras de publicação (art. 54):**\n\n' +
      '1. **PNCP obrigatório:** Todos os editais devem ser publicados no Portal Nacional de Contratações Públicas, independente da esfera (federal, estadual, municipal).\n' +
      '2. **Diário Oficial:** Publicação em diário oficial da unidade federativa.\n' +
      '3. **Jornal de grande circulação:** Obrigatório para licitações acima de determinados valores.\n' +
      '4. **Site do órgão:** O edital completo deve estar disponível no site institucional.\n\n' +
      '**Contagem do prazo:**\n' +
      '- Conta-se a partir do primeiro dia útil seguinte a publicação.\n' +
      '- Exclui-se o dia da publicação e inclui-se o dia do vencimento.\n' +
      '- Somente dias úteis (excluem-se sabados, domingos e feriados).\n\n' +
      '**Alteração de edital e republicação:**\n' +
      'Se o edital for alterado após a publicação e a alteração afetar a formulação das propostas, o prazo de publicação deve ser reaberto integralmente. Alterações menores que não impactam a proposta não exigem reabertura de prazo, mas devem ser comunicadas a todos os interessados.\n\n' +
      '**Dica para fornecedores:** Configure alertas no PNCP e em plataformas como o SmartLic para receber notificações assim que editais de seu setor forem publicados. Isso maximiza o tempo disponível para análise e preparação da proposta.',
    legalBasis: 'Lei 14.133/2021, arts. 54, 55',
    relatedTerms: ['edital', 'licitacao', 'pncp'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Confira os prazos mínimos de publicação de edital na Lei 14.133/2021: 8 dias (pregão), 15-25 dias (concorrência) e mais.',
  },
  {
    slug: 'vigencia-contrato-administrativo',
    title: 'Qual a vigência máxima de um contrato administrativo?',
    category: 'prazos-cronogramas',
    answer:
      'A Lei 14.133/2021 trouxe mudancas significativas nos prazos de vigência de contratos administrativos, ampliando consideravelmente os limites anteriores. Os prazos estão definidos nos artigos 105 a 114.\n\n' +
      '**Vigência por tipo de contrato:**\n\n' +
      '1. **Serviços e fornecimentos continuados (art. 106):** Vigência inicial até 5 anos, prorrogável por até 10 anos no total. Serviços com dedicação exclusiva de mao de obra podem chegar a 10 anos.\n\n' +
      '2. **Obras e serviços de engenharia (art. 111):** A vigência deve contemplar o prazo necessário para conclusão do objeto, acrescido de prazo para liquidação e pagamento.\n\n' +
      '3. **Aluguel de equipamentos e utilização de programas de informática (art. 106, par. 2):** Vigência até 5 anos, podendo ser prorrogada por até 10 anos.\n\n' +
      '4. **Contratos de receita (art. 110):** Concessões de uso de espaco público e similares podem ter vigência de até 10 anos.\n\n' +
      '5. **Concessões de serviço público (Lei 8.987/95):** Prazos variam conforme a complexidade — tipicamente 20 a 35 anos para concessões de infraestrutura.\n\n' +
      '**Prorrogação contratual:**\n\n' +
      'A prorrogação exige:\n' +
      '- Previsão no edital e no contrato original\n' +
      '- Justificativa por escrito do gestor\n' +
      '- Demonstração de vantajosidade da prorrogação versus nova licitação\n' +
      '- Anuência do contratado\n' +
      '- Parecer jurídico favorável\n\n' +
      '**Extinção antecipada:**\n' +
      'O contrato pode ser extinto antecipadamente por inadimplemento, interesse público superveniente, caso fortuito ou forca maior. O contratado tem direito a indenização pelos prejuízos comprovados.\n\n' +
      '**Dica para fornecedores:** Ao elaborar a proposta, considere o período total possível de contratação (incluindo prorrogações) para calcular o retorno do investimento. Contratos de serviços continuados com potencial de 10 anos representam receita previsível de longo prazo — precifique considerando ganhos de escala ao longo do tempo.',
    legalBasis: 'Lei 14.133/2021, arts. 105 a 114',
    relatedTerms: ['contrato-administrativo', 'licitacao', 'edital'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Saiba a vigência máxima de contratos administrativos na Lei 14.133: até 5 anos iniciais, prorrogável a 10 anos ou mais.',
  },
  {
    slug: 'prazo-assinatura-contrato',
    title: 'Qual o prazo para assinatura do contrato após adjudicação?',
    category: 'prazos-cronogramas',
    answer:
      'Após a adjudicação e homologação do processo licitatório, o licitante vencedor e convocado para assinar o contrato dentro do prazo estabelecido no edital. A Lei 14.133/2021 trata desse tema no artigo 90.\n\n' +
      '**Regras de prazo:**\n\n' +
      '1. **Prazo do edital:** O edital deve fixar o prazo para assinatura do contrato, que geralmente varia entre 5 e 30 dias corridos, conforme a complexidade do objeto.\n' +
      '2. **Prazo legal supletivo:** Se o edital não fixar prazo, aplica-se o prazo de 10 dias corridos a partir da convocação.\n' +
      '3. **Prorrogação:** O prazo pode ser prorrogado uma vez, por igual período, quando solicitado justificadamente pelo convocado e aceito pela administração.\n\n' +
      '**Consequências da não assinatura:**\n\n' +
      'Se o vencedor não assinar o contrato no prazo:\n' +
      '- Perde o direito a contratação.\n' +
      '- Pode ser penalizado com impedimento de licitar (art. 156, III) por prazo de até 3 anos.\n' +
      '- A administração convoca o segundo classificado, nas mesmas condições do primeiro.\n' +
      '- Se o segundo também recusar, convoca o terceiro, e assim sucessivamente.\n\n' +
      '**Documentos exigidos na assinatura:**\n' +
      '- Documentos de habilitação atualizados (certidões negativas com validade vigente)\n' +
      '- Comprovante de garantia contratual (se exigida no edital)\n' +
      '- Comprovante de ART/RRT (para obras e serviços de engenharia)\n' +
      '- Dados bancários para pagamento\n\n' +
      '**Assinatura eletrônica:**\n' +
      'A Lei 14.133 permite a assinatura eletrônica de contratos (art. 91), o que acelera significativamente o processo. Muitos órgãos já utilizam plataformas como SEI (Sistema Eletrônico de Informações) ou gov.br para assinatura digital.\n\n' +
      '**Dica prática:** Mantenha todas as certidões negativas atualizadas ANTES do resultado da licitação. Certidões vencidas na data da convocação podem impedir a assinatura e levar a desclassificação.',
    legalBasis: 'Lei 14.133/2021, arts. 90, 91',
    relatedTerms: ['adjudicacao', 'contrato-administrativo', 'habilitacao'],
    relatedSectors: [],
    relatedArticles: ['checklist-habilitacao-licitacao-2026'],
    metaDescription:
      'Saiba o prazo para assinar contrato após adjudicação na Lei 14.133: entre 5 e 30 dias conforme edital, prorrogável uma vez.',
  },
  {
    slug: 'renovacao-contrato-servicos-continuados',
    title:
      'Como funciona a renovação de contratos de serviços continuados?',
    category: 'prazos-cronogramas',
    answer:
      'Contratos de serviços continuados são aqueles cuja interrupção compromete a continuidade das atividades da administração — como limpeza, vigilância, manutenção, TI e alimentação. A Lei 14.133/2021 disciplina a prorrogação desses contratos no artigo 107.\n\n' +
      '**Regras de prorrogação:**\n\n' +
      '1. **Vigência inicial:** Até 5 anos (art. 106).\n' +
      '2. **Prorrogação máxima:** O contrato pode ser prorrogado sucessivamente, desde que:\n' +
      '   - O prazo total não exceda 10 anos (art. 107)\n' +
      '   - A prorrogação esteja prevista no edital\n' +
      '   - O contratado concorde\n' +
      '   - O gestor justifique a vantajosidade\n' +
      '   - O parecer jurídico seja favorável\n\n' +
      '3. **Serviços com dedicação exclusiva de mao de obra:** Podem atingir 10 anos de vigência total. A administração deve verificar se os custos continuam vantajosos comparados a nova licitação.\n\n' +
      '**Procedimento de prorrogação:**\n\n' +
      '1. **Pesquisa de preços:** Antes da prorrogação, o gestor deve comparar os preços contratados com os praticados no mercado.\n' +
      '2. **Parecer do gestor:** Justificativa técnica e financeira da vantajosidade.\n' +
      '3. **Anuência do contratado:** O fornecedor deve concordar expressamente.\n' +
      '4. **Reajuste/repactuação:** A prorrogação e o momento adequado para aplicar reajuste pelo índice contratual ou repactuação por convenção coletiva.\n' +
      '5. **Termo aditivo:** Formalização por aditivo contratual, publicado no PNCP.\n\n' +
      '**Reajuste versus repactuação:**\n' +
      '- **Reajuste:** Correção automática por índice (IPCA, INPC, IGP-M). Anual, a partir da data do orçamento.\n' +
      '- **Repactuação:** Revisão detalhada dos custos com base em convenção coletiva de trabalho. Exclusiva para serviços com dedicação de mao de obra.\n\n' +
      '**Dica estratégica:** Para fornecedores, contratos de serviços continuados são os mais valiosos no mercado público — receita recorrente por até 10 anos. Invista na qualidade da execução e no relacionamento com o gestor do contrato, pois a decisão de prorrogar depende diretamente da avaliação de desempenho.',
    legalBasis: 'Lei 14.133/2021, arts. 106, 107',
    relatedTerms: [
      'contrato-administrativo',
      'reajuste',
      'reequilibrio-economico-financeiro',
    ],
    relatedSectors: ['facilities', 'seguranca'],
    relatedArticles: [],
    metaDescription:
      'Entenda como funciona a prorrogação de contratos de serviços continuados: vigência até 10 anos, reajuste e repactuação.',
  },
  {
    slug: 'prazo-pagamento-contrato-publico',
    title: 'Qual o prazo de pagamento em contratos públicos?',
    category: 'prazos-cronogramas',
    answer:
      'O prazo de pagamento em contratos públicos e uma das maiores preocupações de fornecedores que atuam com o governo. A Lei 14.133/2021 estabelece regras mais claras sobre prazos e penalidades por atraso.\n\n' +
      '**Prazo legal de pagamento (art. 141):**\n\n' +
      'A administração pública deve efetuar o pagamento em até 30 (trinta) dias corridos contados do recebimento definitivo do objeto e da apresentação correta da nota fiscal/fatura. Esse e o prazo máximo — o edital pode fixar prazo menor.\n\n' +
      '**Fluxo de pagamento:**\n\n' +
      '1. **Entrega/execução:** O fornecedor entrega o bem ou executa o serviço.\n' +
      '2. **Recebimento provisório:** O gestor recebe e verifica preliminarmente (prazo do edital, geralmente 15 dias).\n' +
      '3. **Recebimento definitivo:** Após conferência completa, emite o termo de recebimento definitivo.\n' +
      '4. **Emissão da nota fiscal:** O fornecedor emite NF conforme instruções do órgão.\n' +
      '5. **Ateste:** O gestor do contrato atesta a nota fiscal, confirmando a execução.\n' +
      '6. **Liquidação e pagamento:** O setor financeiro processa o pagamento em até 30 dias.\n\n' +
      '**Atraso no pagamento:**\n\n' +
      'A Lei 14.133 garante ao contratado o direito a atualização monetária do valor devido em caso de atraso (art. 141, par. único). Além disso:\n' +
      '- Atraso superior a 2 meses autoriza o contratado a suspender a execução (art. 137, par. 2, IV).\n' +
      '- O contratado pode optar pela extinção do contrato se o atraso for reiterado.\n' +
      '- Juros de mora são devidos pelo poder público (em geral 1% ao mês).\n\n' +
      '**Antecipação de pagamento:**\n' +
      'A Lei 14.133 permite antecipação de pagamento mediante garantia (art. 145), especialmente para obras e fornecimentos que exijam investimento inicial do contratado.\n\n' +
      '**Realidade prática:** Apesar do prazo legal de 30 dias, atrasos são frequentes, especialmente em municipios menores. Considere esse risco no seu fluxo de caixa e precifique adequadamente.',
    legalBasis: 'Lei 14.133/2021, arts. 141, 145',
    relatedTerms: ['contrato-administrativo', 'licitacao', 'edital'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Saiba o prazo de pagamento em contratos públicos na Lei 14.133: até 30 dias do recebimento definitivo. Veja direitos do fornecedor.',
  },
  {
    slug: 'cronograma-pregao-eletronico',
    title: 'Quanto tempo demora um pregão eletrônico do início ao fim?',
    category: 'prazos-cronogramas',
    answer:
      'O tempo total de um pregão eletrônico varia conforme a complexidade do objeto, o número de participantes e eventuais recursos. Em média, o processo completo leva entre 30 e 90 dias da publicação do edital a assinatura do contrato.\n\n' +
      '**Cronograma típico de um pregão eletrônico:**\n\n' +
      '| Fase | Duração Típica |\n' +
      '|------|---------------|\n' +
      '| Publicação do edital | D+0 |\n' +
      '| Prazo de impugnação | 3 a 8 dias úteis |\n' +
      '| Prazo mínimo para propostas | 8 dias úteis |\n' +
      '| Sessão pública (abertura + lances) | 1 dia (2-6 horas) |\n' +
      '| Habilitação do vencedor | 1-5 dias úteis |\n' +
      '| Manifestação de intenção de recurso | Imediata (sessão) |\n' +
      '| Prazo para razões de recurso | 3 dias úteis |\n' +
      '| Prazo para contrarrazões | 3 dias úteis |\n' +
      '| Decisão do recurso | 5-10 dias úteis |\n' +
      '| Adjudicação + homologação | 1-5 dias úteis |\n' +
      '| Convocação para contrato | 5-10 dias corridos |\n\n' +
      '**Cenários de tempo total:**\n\n' +
      '- **Sem recursos:** 25-35 dias corridos (melhor cenário)\n' +
      '- **Com 1 recurso:** 40-60 dias corridos\n' +
      '- **Com diligências + recursos:** 60-90 dias corridos\n' +
      '- **Com impugnação acatada (republicação):** 50-80 dias corridos\n\n' +
      '**Fatores que aceleram o processo:**\n' +
      '- Termo de referência bem elaborado (menos pedidos de esclarecimento)\n' +
      '- Poucos itens no certame\n' +
      '- Licitantes com documentação atualizada no SICAF\n' +
      '- Ausência de recursos\n\n' +
      '**Fatores que atrasam:**\n' +
      '- Impugnações acatadas (republicação integral)\n' +
      '- Múltiplos recursos em cadeia\n' +
      '- Diligências para esclarecimentos\n' +
      '- Licitantes com certidões vencidas (nova convocação necessária)\n\n' +
      '**Dica para fornecedores:** Planeje seu calendário de licitações considerando 60 dias como média segura do edital ao contrato. Mantenha estoque/equipe prontos para iniciar a execução rapidamente após a assinatura — atrasos na mobilização podem gerar sanções contratuais.',
    legalBasis: 'Lei 14.133/2021, arts. 55, 164, 165',
    relatedTerms: ['pregao-eletronico', 'edital', 'adjudicacao'],
    relatedSectors: [],
    relatedArticles: ['pregao-eletronico-guia-passo-a-passo'],
    metaDescription:
      'Veja quanto tempo demora um pregão eletrônico: de 30 a 90 dias. Cronograma completo de cada fase do processo.',
  },

  /* ================================================================ */
  /*  DOCUMENTACAO E HABILITACAO (10)                                  */
  /* ================================================================ */
  {
    slug: 'documentos-habilitacao-licitacao',
    title: 'Quais documentos são exigidos na habilitação de licitação?',
    category: 'documentacao-habilitacao',
    answer:
      'A habilitação e a fase do processo licitatório em que a administração verifica se o licitante possui condições jurídicas, fiscais, técnicas e financeiras para executar o contrato. A Lei 14.133/2021 define os documentos exigíveis nos artigos 62 a 70.\n\n' +
      '**Categorias de documentos de habilitação:**\n\n' +
      '**1. Habilitação jurídica (art. 66):**\n' +
      '- Ato constitutivo (contrato social ou estatuto) atualizado\n' +
      '- Documento de identidade do representante legal\n' +
      '- Procuração (se representante não for socio)\n\n' +
      '**2. Regularidade fiscal e trabalhista (art. 68):**\n' +
      '- CND Federal (conjunta PGFN/RFB)\n' +
      '- CND Estadual (ICMS)\n' +
      '- CND Municipal (ISS)\n' +
      '- CRF do FGTS\n' +
      '- CNDT (Certidão Negativa de Débitos Trabalhistas)\n' +
      '- Prova de inscrição no CNPJ\n\n' +
      '**3. Qualificação econômico-financeira (art. 69):**\n' +
      '- Balanço patrimonial do último exercicio\n' +
      '- Certidão negativa de falência/recuperação judicial\n' +
      '- Índices financeiros (liquidez geral, liquidez corrente, solvência geral — mínimo 1,0 salvo justificativa)\n' +
      '- Capital social mínimo ou patrimônio líquido (até 10% do valor estimado)\n\n' +
      '**4. Qualificação técnica (art. 67):**\n' +
      '- Registro no conselho profissional (CREA, CRA, CRN, etc.)\n' +
      '- Atestados de capacidade técnica\n' +
      '- Indicação de equipe técnica (para serviços especializados)\n\n' +
      '**Regras importantes:**\n' +
      '- O edital NAO pode exigir documentos além dos previstos na Lei 14.133 (art. 62, par. 1).\n' +
      '- Micro e pequenas empresas podem regularizar a documentação fiscal até a assinatura do contrato (art. 43, par. 1).\n' +
      '- O SICAF substitui a apresentação de documentos nele cadastrados.\n' +
      '- Certidões obtidas por internet podem ser verificadas diretamente pelo pregoeiro.\n\n' +
      '**Dica prática:** Crie um checklist permanente de todos os documentos e verifique validades mensalmente. Certidões vencem a cada 180 dias e a falta de uma única pode causar inabilitação.',
    legalBasis: 'Lei 14.133/2021, arts. 62 a 70',
    relatedTerms: ['habilitacao', 'certidao-negativa', 'sicaf'],
    relatedSectors: [],
    relatedArticles: ['checklist-habilitacao-licitacao-2026'],
    metaDescription:
      'Veja todos os documentos exigidos na habilitação de licitação: jurídica, fiscal, técnica e financeira conforme Lei 14.133.',
  },
  {
    slug: 'sicaf-o-que-e-como-cadastrar',
    title: 'O que e SICAF e como se cadastrar?',
    category: 'documentacao-habilitacao',
    answer:
      'O SICAF (Sistema de Cadastramento Unificado de Fornecedores) e o cadastro oficial do Governo Federal para empresas que desejam participar de licitações federais. Mantido pelo Ministério da Gestão e da Inovação em Serviços Públicos, o SICAF centraliza é válida a documentação dos fornecedores.\n\n' +
      '**O que o SICAF oferece:**\n' +
      '- Cadastro unificado para todas as licitações federais\n' +
      '- Validação automática de certidões (via integração com órgãos emissores)\n' +
      '- Substituição da apresentação física de documentos na habilitação\n' +
      '- Níveis de credenciamento progressivos\n\n' +
      '**Como se cadastrar no SICAF:**\n\n' +
      '1. **Acesse o portal:** Entre em comprasnet.gov.br (ou comprasgov.br) com login gov.br.\n' +
      '2. **Solicite o cadastro:** Selecione "Cadastrar Fornecedor" é preencha os dados básicos (CNPJ, razão social, endereco, atividade econômica).\n' +
      '3. **Selecione níveis de cadastro:**\n' +
      '   - Nível I: Credenciamento (dados básicos)\n' +
      '   - Nível II: Habilitação jurídica (contrato social)\n' +
      '   - Nível III: Regularidade fiscal (certidões federais, estaduais, municipais)\n' +
      '   - Nível IV: Qualificação técnica (registro profissional)\n' +
      '   - Nível V: Qualificação econômico-financeira (balanço patrimonial)\n' +
      '   - Nível VI: Completo (todos os níveis)\n' +
      '4. **Envie documentos digitalizados:** Faca upload dos documentos correspondentes a cada nível.\n' +
      '5. **Validação:** O sistema válida certidões automaticamente. Documentos que exigem análise manual são avaliados em até 3 dias úteis.\n\n' +
      '**Manutenção do SICAF:**\n' +
      '- Certidões vencem a cada 180 dias — renove antes do vencimento.\n' +
      '- O balanço patrimonial deve ser atualizado anualmente (até 30 de abril).\n' +
      '- Alterações contratuais devem ser refletidas imediatamente.\n\n' +
      '**O SICAF é obrigatório?**\n' +
      'Para licitações federais, o SICAF é o sistema padrão e seu uso e fortemente recomendado. Para licitações estaduais e municipais, cada ente pode ter seu próprio cadastro (como CAUFESP em SP ou CRC nos municipios), mas o SICAF e amplamente aceito como referência.',
    legalBasis: 'Lei 14.133/2021, art. 87',
    relatedTerms: ['sicaf', 'habilitacao', 'certidao-negativa'],
    relatedSectors: [],
    relatedArticles: ['sicaf-como-cadastrar-manter-ativo-2026'],
    metaDescription:
      'Entenda o que e SICAF, como se cadastrar passo a passo, níveis de credenciamento e dicas para manter o cadastro ativo.',
  },
  {
    slug: 'atestado-capacidade-tecnica',
    title: 'O que é atestado de capacidade técnica é quem emite?',
    category: 'documentacao-habilitacao',
    answer:
      'O atestado de capacidade técnica (ACT) e o documento que comprova que uma empresa já executou com sucito serviços ou fornecimentos similares ao objeto da licitação. E emitido por clientes anteriores — órgãos públicos ou empresas privadas — e constitui a principal prova de experiência técnica exigida nos processos licitatórios.\n\n' +
      '**Quem emite o atestado:**\n' +
      '- Órgãos públicos que contrataram o fornecedor\n' +
      '- Empresas privadas que receberam serviços ou produtos\n' +
      '- Qualquer pessoa jurídica de direito público ou privado\n\n' +
      '**O que o atestado deve conter:**\n' +
      '1. Identificação do emitente (razão social, CNPJ, endereco)\n' +
      '2. Descrição detalhada do serviço ou fornecimento realizado\n' +
      '3. Quantidades executadas (parcelas de maior relevância)\n' +
      '4. Período de execução (datas de início e termino)\n' +
      '5. Avaliação de qualidade (desempenho satisfatório)\n' +
      '6. Assinatura do responsável pelo emitente\n\n' +
      '**Regras da Lei 14.133/2021 (art. 67):**\n\n' +
      '- A administração pode exigir atestados que comprovem a execução de **parcelas de maior relevância técnica** e de **valor significativo** do objeto.\n' +
      '- é vedado exigir quantitativos mínimos ou prazos máximos de experiência (sumula 263 TCU), salvo em casos tecnicamente justificados.\n' +
      '- Os atestados devem ser referentes a serviços de natureza e complexidade similares ao objeto — não idênticos.\n' +
      '- O órgão licitante pode realizar diligência para confirmar as informações do atestado.\n\n' +
      '**Acervo técnico (CREA/CAU):**\n' +
      'Para serviços de engenharia e arquitetura, além do atestado da empresa, exige-se a Certidão de Acervo Técnico (CAT) emitida pelo CREA ou CAU, que comprova a experiência dos profissionais indicados como responsáveis técnicos.\n\n' +
      '**Dica prática:** Solicite atestados de TODOS os seus clientes ao final de cada contrato, mesmo os privados. Mantenha um portfolio organizado por tipo de serviço e valor. Quanto maior seu acervo de atestados, mais licitações você atendera.',
    legalBasis: 'Lei 14.133/2021, art. 67',
    relatedTerms: ['habilitacao', 'licitacao', 'parecer-tecnico'],
    relatedSectors: ['engenharia', 'construcao'],
    relatedArticles: ['checklist-habilitacao-licitacao-2026'],
    metaDescription:
      'Saiba o que e atestado de capacidade técnica, quem emite, o que deve conter e como usar em licitações (Lei 14.133).',
  },
  {
    slug: 'certidoes-negativas-obrigatorias',
    title: 'Quais certidões negativas são obrigatórias em licitações?',
    category: 'documentacao-habilitacao',
    answer:
      'As certidões negativas de débito são documentos que comprovam a regularidade fiscal e trabalhista da empresa perante os órgãos governamentais. Na Lei 14.133/2021, as certidões exigíveis estão listadas no artigo 68.\n\n' +
      '**Certidões obrigatórias:**\n\n' +
      '1. **CND Federal (Conjunta PGFN/RFB):**\n' +
      '   - Certidão Conjunta de Débitos Relativos a Tributos Federais e a Divida Ativa da União\n' +
      '   - Emissão: site da Receita Federal (www.gov.br/receitafederal)\n' +
      '   - Validade: 180 dias\n\n' +
      '2. **CRF do FGTS:**\n' +
      '   - Certificado de Regularidade do FGTS\n' +
      '   - Emissão: site da Caixa Econômica Federal (www.caixa.gov.br)\n' +
      '   - Validade: 30 dias\n\n' +
      '3. **CNDT (Trabalhista):**\n' +
      '   - Certidão Negativa de Débitos Trabalhistas\n' +
      '   - Emissão: site do TST (www.tst.jus.br)\n' +
      '   - Validade: 180 dias\n\n' +
      '4. **CND Estadual (ICMS):**\n' +
      '   - Certidão de Regularidade Fiscal Estadual\n' +
      '   - Emissão: site da Secretaria de Fazenda do estado\n' +
      '   - Validade: varia por estado (60-180 dias)\n\n' +
      '5. **CND Municipal (ISS):**\n' +
      '   - Certidão de Regularidade Fiscal Municipal\n' +
      '   - Emissão: site da Prefeitura ou Secretaria de Financas\n' +
      '   - Validade: varia por municipio (60-180 dias)\n\n' +
      '6. **Certidão Negativa de Falência/Recuperação Judicial:**\n' +
      '   - Emissão: distribuidor judicial da comarca da sede da empresa\n' +
      '   - Validade: 90 dias (em geral)\n\n' +
      '**Certidão positiva com efeitos de negativa:**\n' +
      'Se a empresa tiver débitos com exigibilidade suspensa (parcelamento, liminar judicial, etc.), a certidão emitida sera "positiva com efeitos de negativa" — tem o mesmo valor da certidão negativa para fins de habilitação.\n\n' +
      '**Beneficio para ME/EPP:**\n' +
      'Micro e pequenas empresas podem participar da licitação mesmo com certidões fiscais irregulares, desde que regularizem a situação em até 5 dias úteis após a declaração de vencedor (art. 43, par. 1 da LC 123/2006).\n\n' +
      '**Dica:** Configure alertas de vencimento para cada certidão. A falta de uma única certidão válida no momento da habilitação resulta em inabilitação automática.',
    legalBasis: 'Lei 14.133/2021, art. 68',
    relatedTerms: ['certidao-negativa', 'habilitacao', 'sicaf'],
    relatedSectors: [],
    relatedArticles: ['checklist-habilitacao-licitacao-2026'],
    metaDescription:
      'Lista completa de certidões negativas obrigatórias em licitações: CND Federal, CRF FGTS, CNDT, estadual e municipal.',
  },
  {
    slug: 'qualificacao-tecnica-lei-14133',
    title: 'O que mudou na qualificação técnica com a Lei 14.133?',
    category: 'documentacao-habilitacao',
    answer:
      'A Lei 14.133/2021 trouxe mudancas significativas na qualificação técnica exigida em licitações, buscando equilibrar a necessidade de comprovar capacidade com o principio da competitividade. As regras estão no artigo 67.\n\n' +
      '**Principais mudancas:**\n\n' +
      '**1. Profissional de referência (art. 67, I e II):**\n' +
      'A lei distingue entre qualificação técnico-profissional (do responsável técnico) e técnico-operacional (da empresa). Para obras e serviços de engenharia, pode ser exigida a comprovação de que a empresa possui profissional com experiência em parcelas de maior relevância técnica.\n\n' +
      '**2. Limite de exigência de quantitativos (art. 67, par. 1):**\n' +
      'A administração não pode exigir atestados com quantidades idênticas ao objeto — deve aceitar atestados que demonstrem capacidade técnica proporcional. A jurisprudência do TCU admite até 50% do quantitativo como referência razoável.\n\n' +
      '**3. Experiência com especificidade (art. 67, par. 3):**\n' +
      'A lei permite exigir experiência específica em parcelas de maior relevância técnica e valor significativo, devidamente justificadas no estudo técnico preliminar.\n\n' +
      '**4. Indicação da equipe técnica (art. 67, par. 6):**\n' +
      'A equipe técnica indicada na habilitação deve ser mantida durante a execução. A substituição só é permitida com anuência da administração e por profissional de experiência equivalente ou superior.\n\n' +
      '**5. Visita técnica facultativa (art. 63, par. 2):**\n' +
      'A visita técnica ao local da obra/serviço não pode ser exigida como condicio obrigatória — deve ser substituida por declaração de conhecimento das condições locais.\n\n' +
      '**6. Soma de atestados (art. 67, par. 2):**\n' +
      'Quando o edital exigir comprovação de capacidade para parcelas de diferentes naturezas, permite-se a apresentação de atestados distintos (somatórios) para cada parcela, ampliando a participação.\n\n' +
      '**Impacto prático:**\n' +
      'Essas mudancas beneficiam principalmente empresas de medio porte, que agora tem mais facilidade para comprovar capacidade técnica em licitações maiores. A proibição de exigências excessivas amplia a competitividade e reduz o direcionamento.',
    legalBasis: 'Lei 14.133/2021, art. 67',
    relatedTerms: ['habilitacao', 'parecer-tecnico', 'licitacao'],
    relatedSectors: ['engenharia', 'construcao'],
    relatedArticles: ['checklist-habilitacao-licitacao-2026'],
    metaDescription:
      'Veja as mudancas na qualificação técnica da Lei 14.133: novos limites para atestados, soma de experiências e mais.',
  },
  {
    slug: 'me-epp-beneficios-licitacao',
    title: 'Quais beneficios ME e EPP tem em licitações?',
    category: 'documentacao-habilitacao',
    answer:
      'Microempresas (ME) e Empresas de Pequeno Porte (EPP) possuem tratamento diferenciado e favorecido em licitações públicas, garantido pela Lei Complementar 123/2006 e reafirmado pela Lei 14.133/2021 (arts. 4 e 48).\n\n' +
      '**Principais beneficios:**\n\n' +
      '**1. Empate ficto / lance diferenciado (art. 44, LC 123):**\n' +
      'Se a proposta da ME/EPP for até 5% superior a melhor proposta (10% na concorrência), ela tem direito a oferecer um lance final inferior, empatando ou superando o primeiro colocado. No pregão eletrônico, o sistema convoca automaticamente.\n\n' +
      '**2. Regularização fiscal tardia (art. 43, par. 1, LC 123):**\n' +
      'ME/EPP com certidões fiscais irregulares pode participar da licitação e, se vencedora, tem até 5 dias úteis para regularizar a situação. Esse beneficio não se aplica a qualificação técnica ou econômico-financeira.\n\n' +
      '**3. Licitações exclusivas (art. 48, I, LC 123):**\n' +
      'Contratações de até R$ 80.000,00 podem ser destinadas exclusivamente a ME/EPP. Muitos órgãos usam esse limite regularmente.\n\n' +
      '**4. Subcontratação obrigatória (art. 48, II, LC 123):**\n' +
      'O edital pode exigir que o vencedor subcontrate ME/EPP para até 30% do objeto.\n\n' +
      '**5. Cota reservada (art. 48, III, LC 123):**\n' +
      'Em licitações de bens divisíveis, até 25% do quantitativo pode ser reservado para ME/EPP.\n\n' +
      '**6. Credenciamento simplificado no SICAF:**\n' +
      'Processo de cadastro facilitado com menos documentos.\n\n' +
      '**Como comprovar o enquadramento:**\n' +
      '- ME: Faturamento bruto anual até R$ 360.000,00\n' +
      '- EPP: Faturamento bruto anual entre R$ 360.000,01 e R$ 4.800.000,00\n' +
      '- Declaração no sistema eletrônico no momento do cadastro da proposta\n' +
      '- Certidão da Junta Comercial ou declaração do contador\n\n' +
      '**Atenção:** A declaração falsa de enquadramento como ME/EPP constitui fraude, sujeitando a empresa a sanções administrativas e penais. Além disso, o beneficio do empate ficto não se aplica quando ME/EPP ultrapassa o limite de faturamento no exercicio anterior.',
    legalBasis:
      'LC 123/2006, arts. 43-49; Lei 14.133/2021, arts. 4, 48',
    relatedTerms: ['licitacao', 'habilitacao', 'pregao-eletronico'],
    relatedSectors: [],
    relatedArticles: ['mei-microempresa-vantagens-licitacoes'],
    metaDescription:
      'Conheca os beneficios de ME e EPP em licitações: empate ficto, regularização fiscal, cotas exclusivas e licitações até R$80 mil.',
  },
  {
    slug: 'consorcio-licitacao-como-funciona',
    title: 'Como funciona consórcio em licitações públicas?',
    category: 'documentacao-habilitacao',
    answer:
      'O consórcio e a união temporária de duas ou mais empresas para participar de licitações e executar contratos públicos que, individualmente, nenhuma delas teria capacidade técnica ou financeira suficiente. A Lei 14.133/2021 disciplina os consorcios no artigo 15.\n\n' +
      '**Quando formar consórcio:**\n' +
      '- Obras de grande porte que exigem especializações complementares\n' +
      '- Contratos com exigências de qualificação técnica e financeira elevadas\n' +
      '- Quando a soma de atestados de diferentes empresas é necessária\n' +
      '- Projetos que combinam engenharia civil, elétrica, mecânica, etc.\n\n' +
      '**Regras legais (art. 15):**\n\n' +
      '1. **Compromisso de constituição:** Apresentar compromisso público ou particular de constituição do consórcio, assinado pelos consorciados.\n' +
      '2. **Lider do consórcio:** Indicar uma empresa lider, responsável pela representação perante a administração.\n' +
      '3. **Responsabilidade solidária:** Todos os consorciados são solidariamente responsáveis pelas obrigações do consórcio.\n' +
      '4. **Habilitação individual:** Cada consorciado apresenta seus próprios documentos de habilitação.\n' +
      '5. **Soma de capacidades:** A qualificação técnica e econômico-financeira pode ser somada entre os consorciados.\n\n' +
      '**Acréscimo na qualificação (art. 15, par. 1):**\n' +
      'O edital pode exigir acréscimo de até 30% nos requisitos de qualificação econômico-financeira para consorcios, como forma de garantir capacidade adequada.\n\n' +
      '**Vedação de participação simultanea (art. 15, par. 4):**\n' +
      'A empresa consorciada não pode participar da mesma licitação individualmente ou em outro consórcio.\n\n' +
      '**Consórcio de ME/EPP:**\n' +
      'Nas licitações exclusivas para ME/EPP, admite-se a participação de consórcio formado exclusivamente por essas empresas, mantendo os beneficios da LC 123/2006.\n\n' +
      '**Dica prática:** Antes de formar consórcio, defina claramente em contrato particular: a participação percentual de cada empresa, a divisão de responsabilidades, o regime de faturamento e a gestão de riscos. O acordo de consórcio deve ser solido para evitar conflitos durante a execução.',
    legalBasis: 'Lei 14.133/2021, art. 15',
    relatedTerms: ['licitacao', 'habilitacao', 'proposta'],
    relatedSectors: ['engenharia', 'construcao'],
    relatedArticles: [],
    metaDescription:
      'Entenda como funciona consórcio em licitações: quando formar, regras da Lei 14.133, responsabilidade solidária e habilitação.',
  },
  {
    slug: 'subcontratacao-permitida-licitacao',
    title: 'Quando a subcontratação é permitida em licitações?',
    category: 'documentacao-habilitacao',
    answer:
      'A subcontratação e a transferência parcial da execução do contrato a terceiros, mantendo o contratado original como responsável perante a administração. A Lei 14.133/2021 regula o tema no artigo 122.\n\n' +
      '**Regras gerais de subcontratação:**\n\n' +
      '1. **Previsão no edital:** A subcontratação só é permitida se expressamente prevista no edital e no contrato. Sem previsão, é vedada.\n' +
      '2. **Limites:** O edital define o percentual máximo subcontratável e as parcelas que podem ser subcontratadas.\n' +
      '3. **Nucleo do objeto:** A parcela principal do objeto (nucleo) não pode ser subcontratada — está é reservada ao contratado.\n' +
      '4. **Autorização prévia:** O contratado deve solicitar autorização a administração antes de subcontratar.\n' +
      '5. **Qualificação do subcontratado:** O subcontratado deve atender aos requisitos de qualificação técnica exigidos para a parcela subcontratada.\n\n' +
      '**O que não pode ser subcontratado:**\n' +
      '- A totalidade do objeto\n' +
      '- Parcelas para as quais se exigiu qualificação técnica específica na habilitação\n' +
      '- Parcelas que justificaram a contratação do fornecedor específico\n\n' +
      '**Responsabilidade:**\n' +
      'Mesmo com subcontratação, o contratado original permanece integralmente responsável perante a administração. Problemas causados pelo subcontratado são atribuidos ao contratado principal.\n\n' +
      '**Subcontratação obrigatória de ME/EPP:**\n' +
      'Conforme a LC 123/2006 (art. 48, II), o edital pode exigir que o vencedor subcontrate ME/EPP para até 30% do objeto, como mecanismo de fomento a participação de pequenas empresas.\n\n' +
      '**Dica para fornecedores:** Se você planeja subcontratar parte da execução, declare isso na proposta e identifique o subcontratado. Escolha parceiros de confianca — você responde por eles. Mantenha controle rigoroso sobre qualidade e prazos da parcela subcontratada.',
    legalBasis: 'Lei 14.133/2021, art. 122',
    relatedTerms: ['contrato-administrativo', 'licitacao', 'habilitacao'],
    relatedSectors: ['engenharia', 'facilities'],
    relatedArticles: [],
    metaDescription:
      'Saiba quando a subcontratação é permitida em licitações na Lei 14.133: limites, regras, autorização e responsabilidades.',
  },
  {
    slug: 'garantia-proposta-licitacao',
    title: 'O que é garantia de proposta e quando é exigida?',
    category: 'documentacao-habilitacao',
    answer:
      'A garantia de proposta é uma caução exigida dos licitantes para assegurar que o vencedor cumprira sua obrigação de assinar o contrato. Trata-se de uma inovação da Lei 14.133/2021, prevista no artigo 58.\n\n' +
      '**O que é a garantia de proposta:**\n\n' +
      'É um valor que o licitante deposita ou apresenta como caução ao participar da licitação. Se o vencedor desistir de assinar o contrato sem justificativa, a administração executa a garantia. Se o licitante não vencer ou se o processo for normal, a garantia é devolvida integralmente.\n\n' +
      '**Quando é exigida:**\n' +
      '- Em licitações de obras, serviços e fornecimentos de GRANDE VULTO (art. 58, parágrafo único)\n' +
      '- Quando o valor estimado da contratação justificar a exigência\n' +
      '- A critério da administração, desde que prevista no edital\n' +
      '- NAO pode ser exigida em pregão para bens e serviços comuns de baixo valor\n\n' +
      '**Limites:**\n' +
      '- Até 1% do valor estimado da contratação (art. 58)\n\n' +
      '**Modalidades de garantia aceitas:**\n' +
      '1. **Caução em dinheiro:** Deposito em conta bancária indicada pelo órgão\n' +
      '2. **Seguro-garantia:** Apolice emitida por seguradora autorizada pela SUSEP\n' +
      '3. **Fianca bancária:** Carta de fianca emitida por instituição financeira\n' +
      '4. **Titulo da divida pública:** Titulos federais escriturais\n\n' +
      '**Diferença entre garantia de proposta e garantia contratual:**\n\n' +
      '| Aspecto | Garantia de Proposta | Garantia Contratual |\n' +
      '|---------|---------------------|--------------------|\n' +
      '| Fase | Licitação | Contrato |\n' +
      '| Limite | Até 1% | Até 5% (30% para grande vulto) |\n' +
      '| Finalidade | Assegurar assinatura | Assegurar execução |\n' +
      '| Devolução | Após adjudicação | Após execução completa |\n\n' +
      '**Dica prática:** Ao participar de licitações de grande vulto, já tenha pre-aprovação de seguro-garantia com sua seguradora. O custo da apolice e geralmente entre 0,5% e 2% do valor segurado — inclua esse custo na formação do preço da proposta.',
    legalBasis: 'Lei 14.133/2021, art. 58',
    relatedTerms: ['proposta', 'licitacao', 'contrato-administrativo'],
    relatedSectors: ['engenharia', 'construcao'],
    relatedArticles: [],
    metaDescription:
      'Entenda o que é garantia de proposta na Lei 14.133: até 1% do valor estimado, quando é exigida e modalidades aceitas.',
  },
  {
    slug: 'cadastro-pncp-fornecedor',
    title: 'Como se cadastrar no PNCP como fornecedor?',
    category: 'documentacao-habilitacao',
    answer:
      'O PNCP (Portal Nacional de Contratações Públicas) e a plataforma oficial do Governo Federal para divulgação e centralização de informações sobre licitações e contratos públicos de todas as esferas (federal, estadual e municipal). Foi instituido pela Lei 14.133/2021 (art. 174).\n\n' +
      '**Importante esclarecer:** O PNCP é primariamente um portal de PUBLICIDADE e TRANSPARENCIA, não um sistema transacional de licitações como o ComprasGov. Ou seja, as licitações são publicadas no PNCP, mas a participação efetiva (envio de propostas, lances, documentos) ocorre na plataforma específica indicada no edital.\n\n' +
      '**Como acessar o PNCP como fornecedor:**\n\n' +
      '1. **Acesse o portal:** Navegue até pncp.gov.br\n' +
      '2. **Login gov.br:** Faca login com sua conta gov.br (nível prata ou ouro)\n' +
      '3. **Vincule seu CNPJ:** Associe o CNPJ da empresa a sua conta pessoal\n' +
      '4. **Consulte licitações:** Use os filtros de busca para encontrar oportunidades por:\n' +
      '   - Palavra-chave no objeto\n' +
      '   - UF e municipio\n' +
      '   - Modalidade de licitação\n' +
      '   - Faixa de valor estimado\n' +
      '   - Data de publicação\n' +
      '   - Órgão contratante\n\n' +
      '**Para participar de licitações, você precisa se cadastrar nos sistemas transacionais:**\n' +
      '- **ComprasGov (federal):** comprasgov.br — exige certificado digital e SICAF\n' +
      '- **BEC-SP (São Paulo):** bec.sp.gov.br — cadastro próprio\n' +
      '- **Licitações-e (Banco do Brasil):** licitacoes-e.com.br — cadastro e certificado digital\n' +
      '- **Portal de Compras Públicas:** portaldecompraspublicas.com.br — cadastro gratuito\n' +
      '- **BLL Compras:** bllcompras.com — cadastro e certificado digital\n\n' +
      '**Beneficios de acompanhar o PNCP:**\n' +
      '- Visão centralizada de todas as licitações do país\n' +
      '- Acesso a atas, contratos e aditivos publicados\n' +
      '- Consulta a histórico de preços practicados\n' +
      '- Transparência total do processo licitatório\n\n' +
      '**Dica:** Use o SmartLic para monitorar o PNCP automaticamente com alertas por setor, região e valor — muito mais eficiente do que consultas manuais diárias.',
    legalBasis: 'Lei 14.133/2021, art. 174',
    relatedTerms: ['pncp', 'sicaf', 'licitacao'],
    relatedSectors: [],
    relatedArticles: ['sicaf-como-cadastrar-manter-ativo-2026'],
    metaDescription:
      'Aprenda a acessar o PNCP como fornecedor, consultar licitações e se cadastrar nos sistemas de compras públicas.',
  },

  /* ================================================================ */
  /*  PRECOS E PROPOSTAS (9)                                           */
  /* ================================================================ */
  {
    slug: 'como-calcular-preco-proposta-licitacao',
    title: 'Como calcular o preço de uma proposta de licitação?',
    category: 'precos-propostas',
    answer:
      'O calculo correto do preço de uma proposta de licitação e o fator determinante entre vencer o certame com lucro ou ser desclassificado por inexequibilidade. A formação de preços deve ser técnica, documentada e competitiva.\n\n' +
      '**Estrutura básica de formação de preços:**\n\n' +
      '1. **Custos diretos:** Materiais, insumos, mao de obra direta, equipamentos, transporte.\n' +
      '2. **Custos indiretos:** Supervisão, administração de obra/serviço, alimentação, EPI.\n' +
      '3. **Despesas administrativas:** Aluguel, contabilidade, departamento pessoal, seguros.\n' +
      '4. **Encargos sociais e trabalhistas:** INSS, FGTS, 13o, férias, rescisão (entre 60% e 90% do salário, conforme o regime).\n' +
      '5. **BDI (Bonificações e Despesas Indiretas):** Para obras e serviços de engenharia.\n' +
      '6. **Tributos:** ISS, PIS, COFINS, IRPJ, CSLL (variam conforme regime tributário).\n' +
      '7. **Lucro:** Margem de retorno sobre o investimento.\n\n' +
      '**Fontes para pesquisa de preços:**\n' +
      '- **Painel de preços do governo** (paineldeprecos.planejamento.gov.br)\n' +
      '- **PNCP:** Contratos e atas de registro de preços similares\n' +
      '- **SINAPI/SICRO:** Tabelas referenciais para obras (Caixa/DNIT)\n' +
      '- **Cotações de fornecedores:** Mínimo 3 cotações\n' +
      '- **Contratos anteriores:** Seus próprios contratos como referência\n\n' +
      '**Passo a passo:**\n\n' +
      '1. Leia o edital e o termo de referência integralmente\n' +
      '2. Identifique todos os custos envolvidos na execução\n' +
      '3. Pesquise preços de mercado e referências públicas\n' +
      '4. Monte a planilha de custos item a item\n' +
      '5. Aplique encargos sociais e tributos corretos\n' +
      '6. Adicione margem de lucro realista\n' +
      '7. Verifique se o preço final está acima do limite de inexequibilidade\n' +
      '8. Compare com o valor estimado do edital (quando divulgado)\n\n' +
      '**Regra de ouro:** O preço deve ser competitivo o suficiente para vencer, mas alto o bastante para garantir execução com qualidade e lucro. Vencer com preço inexequível e pior do que perder.',
    legalBasis: 'Lei 14.133/2021, arts. 23, 59',
    relatedTerms: ['proposta', 'licitacao', 'bdi'],
    relatedSectors: [],
    relatedArticles: ['como-calcular-preco-proposta-licitacao'],
    metaDescription:
      'Aprenda a calcular o preço de proposta para licitação: custos diretos, encargos, BDI, tributos e margem de lucro.',
  },
  {
    slug: 'preco-inexequivel-licitacao',
    title: 'O que é preço inexequível e como evitar desclassificação?',
    category: 'precos-propostas',
    answer:
      'Preço inexequível e aquele manifestamente insuficiente para cobrir os custos de execução do contrato. A administração deve desclassificar propostas com preços inexequíveis para proteger o interesse público, evitando contratações que resultem em inadimplemento.\n\n' +
      '**Critérios de inexequibilidade na Lei 14.133/2021:**\n\n' +
      '**Para obras e serviços de engenharia (art. 59, par. 4):**\n' +
      'Considera-se inexequível a proposta cujo valor global seja inferior a 75% do orçamento estimado pela administração. Para itens individuais, o limite é 75% do custo unitário.\n\n' +
      '**Para bens e serviços em geral (art. 59, par. 3):**\n' +
      'Considera-se potencialmente inexequível a proposta com desconto superior a 50% em relação ao valor estimado. Nesse caso, o licitante deve comprovar a viabilidade dos preços.\n\n' +
      '**Regra complementar (art. 59, par. 2):**\n' +
      'A proposta não sera desclassificada automaticamente — o licitante tera a oportunidade de demonstrar a compatibilidade do preço com os custos, apresentando planilha detalhada e comprovantes.\n\n' +
      '**Como evitar a desclassificação por inexequibilidade:**\n\n' +
      '1. **Planilha detalhada:** Tenha uma planilha de composição de preços completa, com custos unitários de materiais, mao de obra, encargos e tributos.\n' +
      '2. **Cotações de fornecedores:** Apresente cotações que comprovem os preços de insumos.\n' +
      '3. **Contratos anteriores:** Demonstre que já executou serviços similares com preços equivalentes.\n' +
      '4. **Economia de escala:** Justifique preços baixos com ganhos de escala, produtividade superior ou inovação tecnológica.\n' +
      '5. **Regime tributário:** Empresas do Simples Nacional podem ter carga tributária menor, justificando preços mais baixos.\n\n' +
      '**Atenção com "jogo de planilha":**\n' +
      'A prática de colocar preços irrisoriamente baixos em itens de menor quantidade e preços altos em itens de maior quantidade (para manipular a classificação) é vedada é pode resultar em sanções.\n\n' +
      '**Dica:** Sempre calcule o custo real ANTES de definir o preço de lance. Se durante a fase de lances você se aproximar do limite de inexequibilidade, pare de dar lances — melhor perder a licitação do que vencer com preço inviável.',
    legalBasis: 'Lei 14.133/2021, art. 59',
    relatedTerms: ['proposta', 'lance', 'licitacao'],
    relatedSectors: [],
    relatedArticles: [
      'erros-desclassificam-propostas-licitacao',
      'como-calcular-preco-proposta-licitacao',
    ],
    metaDescription:
      'Entenda o que é preço inexequível em licitação, os limites da Lei 14.133 e como evitar desclassificação da proposta.',
  },
  {
    slug: 'bdi-composicao-licitacao',
    title: 'Como compor o BDI para licitações de obras e serviços?',
    category: 'precos-propostas',
    answer:
      'O BDI (Bonificações e Despesas Indiretas) e o percentual aplicado sobre os custos diretos de uma obra ou serviço para cobrir as despesas indiretas, tributos e lucro. É um componente essencial na formação de preços para licitações de engenharia.\n\n' +
      '**Composição do BDI:**\n\n' +
      '| Componente | Faixa Típica |\n' +
      '|------------|-------------|\n' +
      '| Administração central | 3% a 6% |\n' +
      '| Seguros e garantias | 0,5% a 1,5% |\n' +
      '| Riscos e imprevistos | 0,5% a 1,5% |\n' +
      '| Despesas financeiras | 0,5% a 1,5% |\n' +
      '| Lucro | 5% a 10% |\n' +
      '| Tributos (ISS, PIS, COFINS, IRPJ, CSLL) | 6% a 10% |\n' +
      '| **BDI Total Típico** | **20% a 30%** |\n\n' +
      '**Formula do BDI:**\n\n' +
      'BDI = [(1+AC)(1+S)(1+R)(1+DF)(1+L) / (1-T)] - 1\n\n' +
      'Onde: AC=administração central, S=seguros, R=riscos, DF=despesas financeiras, L=lucro, T=tributos.\n\n' +
      '**Referências do TCU (Acórdão 2622/2013):**\n' +
      '- Obras: BDI entre 20,34% e 28,43% (referência)\n' +
      '- Fornecimento de materiais e equipamentos: BDI entre 11,10% e 18,30%\n' +
      '- Serviços especializados: BDI entre 22% e 30%\n\n' +
      '**BDI diferenciado:**\n' +
      'A Lei 14.133 permite a utilização de BDIs diferenciados para parcelas distintas da obra. Por exemplo:\n' +
      '- BDI cheio para serviços (25%)\n' +
      '- BDI reduzido para materiais e equipamentos (15%)\n' +
      '- BDI específico para instalações e montagens (20%)\n\n' +
      '**Erros comuns:**\n' +
      '- Incluir encargos sociais no BDI (devem estar nos custos de mao de obra)\n' +
      '- Usar BDI de obras para serviços continuados (são diferentes)\n' +
      '- Não considerar o regime tributário correto (Simples, Lucro Presumido, Lucro Real)\n' +
      '- Aplicar BDI sobre materiais fornecidos pelo órgão\n\n' +
      '**Dica:** Use a tabela SINAPI da Caixa como referência para custos unitários e o Acórdão TCU 2622/2013 como parametro para faixas de BDI. BDI fora da faixa de referência exige justificativa detalhada.',
    legalBasis: 'Lei 14.133/2021, art. 23, par. 1; Acórdão TCU 2622/2013',
    relatedTerms: ['bdi', 'proposta', 'licitacao'],
    relatedSectors: ['engenharia', 'construcao'],
    relatedArticles: ['como-calcular-preco-proposta-licitacao'],
    metaDescription:
      'Aprenda a compor o BDI para licitações de obras: formula, faixas de referência do TCU e erros comuns a evitar.',
  },
  {
    slug: 'margem-preferencia-produto-nacional',
    title: 'O que e margem de preferência para produtos nacionais?',
    category: 'precos-propostas',
    answer:
      'A margem de preferência é um mecanismo previsto na Lei 14.133/2021 (art. 26) que permite ao poder público pagar um preço até determinado percentual superior por produtos e serviços nacionais em relação a concorrentes estrangeiros, como forma de fomentar a indústria nacional.\n\n' +
      '**Como funciona:**\n\n' +
      'Quando o edital preve margem de preferência, os produtos manufaturados ou serviços nacionais podem ser classificados em primeiro lugar mesmo que sejam até X% mais caros que o concorrente estrangeiro. Esse percentual é definido por decreto do Poder Executivo.\n\n' +
      '**Limites legais (art. 26):**\n' +
      '- Margem normal: até 10% sobre o preço do produto estrangeiro\n' +
      '- Margem adicional para produtos com tecnologia nacional: até 20% cumulativamente\n' +
      '- Deve ser baseada em estudos que demonstrem geração de emprego e renda, inovação tecnológica e desenvolvimento produtivo\n\n' +
      '**Setores com margem de preferência regulamentada:**\n' +
      '- Equipamentos de TI e comunicações (Decreto 7.903/2013)\n' +
      '- Farmacos e medicamentos (Decreto 7.713/2012)\n' +
      '- Equipamentos médico-hospitalares\n' +
      '- Veiculos e automóveis\n' +
      '- Confecções e calcados\n\n' +
      '**Como comprovar origem nacional:**\n' +
      '- Processo Produtivo Básico (PPB) para eletrônicos e informática\n' +
      '- Certificado de Registro do INPI para inovação\n' +
      '- Processo produtivo com etapas significativas realizadas no Brasil\n\n' +
      '**Regras da Lei 14.133:**\n' +
      '- A margem de preferência só se aplica quando prevista em decreto regulamentador específico\n' +
      '- Não se aplica quando não houver produção nacional suficiente para atender a demanda\n' +
      '- O órgão deve justificar a aplicação no processo administrativo\n\n' +
      '**Impacto para fornecedores nacionais:**\n' +
      'A margem de preferência pode ser decisiva em licitações com participação de empresas estrangeiras. Se você fábrica ou fornece produtos com tecnologia nacional, solicite ao órgão licitante a inclusão da margem de preferência quando aplicável — é um direito previsto em lei.',
    legalBasis: 'Lei 14.133/2021, art. 26',
    relatedTerms: ['licitacao', 'proposta', 'edital'],
    relatedSectors: ['informatica', 'equipamentos-medicos'],
    relatedArticles: [],
    metaDescription:
      'Saiba o que e margem de preferência para produtos nacionais em licitações: até 10-20% conforme Lei 14.133/2021.',
  },
  {
    slug: 'reequilibrio-economico-financeiro',
    title:
      'Como solicitar reequilíbrio econômico-financeiro de contrato?',
    category: 'precos-propostas',
    answer:
      'O reequilíbrio econômico-financeiro e o instrumento que permite a revisão dos preços contratuais quando eventos extraordinários, imprevisíveis e alheios a vontade das partes alteram significativamente os custos de execução. Diferentemente do reajuste (previsível e automático), o reequilíbrio é excepcional.\n\n' +
      '**Fundamento legal:**\n' +
      'A Lei 14.133/2021 garante a manutenção do equilíbrio econômico-financeiro do contrato no artigo 124, inciso II, alínea "d", e artigo 134. A Constituição Federal também protege esse direito (art. 37, XXI).\n\n' +
      '**Quando solicitar reequilíbrio:**\n' +
      '- Aumento extraordinário de custos de insumos (acima da inflação normal)\n' +
      '- Alteração de carga tributária que impacte o contrato\n' +
      '- Eventos de forca maior (pandemias, guerras, desastres naturais)\n' +
      '- Mudancas legislativas que aumentem custos de execução\n' +
      '- Variação cambial abrupta (para insumos importados)\n\n' +
      '**Como solicitar — passo a passo:**\n\n' +
      '1. **Identificar o evento:** Documente o fato extraordinário que causou o desequilíbrio.\n' +
      '2. **Demonstrar nexo causal:** Prove que o evento impactou diretamente os custos do contrato.\n' +
      '3. **Quantificar o impacto:** Apresente planilha comparativa de custos antes/depois do evento.\n' +
      '4. **Reunir evidências:** Notas fiscais, cotações, tabelas de preços, noticias, decretos.\n' +
      '5. **Protocolar requerimento:** Enderece ao gestor do contrato com toda a documentação.\n' +
      '6. **Negociar:** O órgão analisa e negocia o percentual de reequilíbrio.\n' +
      '7. **Termo aditivo:** Se aprovado, formaliza-se por aditivo contratual.\n\n' +
      '**Diferença entre reajuste, repactuação e reequilíbrio:**\n\n' +
      '| Mecanismo | Previsibilidade | Base | Periodicidade |\n' +
      '|-----------|----------------|------|---------------|\n' +
      '| Reajuste | Previsível | Índice (IPCA, IGP-M) | Anual |\n' +
      '| Repactuação | Previsível | Convenção coletiva | Anual |\n' +
      '| Reequilíbrio | Imprevisível | Evento extraordinário | Quando necessário |\n\n' +
      '**Dica:** Não espere o contrato se tornar inviável para solicitar reequilíbrio. Protocole o pedido assim que identificar o desequilíbrio, com documentação robusta.',
    legalBasis: 'Lei 14.133/2021, arts. 124 (II, d), 134',
    relatedTerms: [
      'reequilibrio-economico-financeiro',
      'reajuste',
      'contrato-administrativo',
    ],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Aprenda a solicitar reequilíbrio econômico-financeiro de contrato público: quando, como e documentação necessária.',
  },
  {
    slug: 'planilha-custos-formacao-precos',
    title: 'Como preencher a planilha de custos e formação de preços?',
    category: 'precos-propostas',
    answer:
      'A planilha de custos e formação de preços e o documento que detalha todos os componentes do preço proposto em licitações de serviços, especialmente aqueles com dedicação exclusiva de mao de obra (limpeza, vigilância, portaria, etc.). Sua correta elaboração é obrigatória é determinante para a classificação.\n\n' +
      '**Estrutura padrão da planilha (IN SEGES/ME 65/2021):**\n\n' +
      '**Modulo 1 — Composição da remuneração:**\n' +
      '- Salário-base (conforme convenção coletiva)\n' +
      '- Adicional de periculosidade/insalubridade\n' +
      '- Adicional noturno (se aplicável)\n' +
      '- Outros adicionais previstos em CCT\n\n' +
      '**Modulo 2 — Encargos e beneficios:**\n' +
      '- Submudulo 2.1: 13o salário, férias + 1/3\n' +
      '- Submudulo 2.2: Encargos previdenciários (INSS, SAT/RAT, Terceiros)\n' +
      '- Submudulo 2.3: FGTS\n' +
      '- Submudulo 2.4: Vale-transporte, vale-alimentação, assistência médica\n\n' +
      '**Modulo 3 — Provisões para rescisão:**\n' +
      '- Aviso prévio indenizado/trabalhado\n' +
      '- Multa do FGTS (40%)\n' +
      '- Incidência do FGTS sobre aviso prévio\n\n' +
      '**Modulo 4 — Custos indiretos, tributos e lucro:**\n' +
      '- Custos indiretos: administração, supervisão, uniformes, EPI, treinamento\n' +
      '- Tributos: ISS, PIS, COFINS, IRPJ, CSLL\n' +
      '- Lucro: percentual sobre o custo total\n\n' +
      '**Erros frequentes que levam a desclassificação:**\n' +
      '1. Salário abaixo do piso da convenção coletiva\n' +
      '2. Encargos sociais calculados incorretamente\n' +
      '3. Beneficios da CCT omitidos (cesta básica, seguro de vida)\n' +
      '4. Tributos inconsistentes com o regime tributário declarado\n' +
      '5. Custos indiretos irrealistas (muito baixos)\n\n' +
      '**Dica essencial:** Obtenha a Convenção Coletiva de Trabalho (CCT) vigente da categoria profissional na região de execução do serviço. O salário-base e todos os beneficios obrigatórios estão la. Use a CCT correta — usar a de outra região ou categoria e causa de inabilitação.',
    legalBasis: 'Lei 14.133/2021, art. 63; IN SEGES/ME 65/2021',
    relatedTerms: ['proposta', 'bdi', 'licitacao'],
    relatedSectors: ['facilities', 'seguranca'],
    relatedArticles: ['como-calcular-preco-proposta-licitacao'],
    metaDescription:
      'Guia completo para preencher a planilha de custos e formação de preços em licitações: modulos, encargos e erros a evitar.',
  },
  {
    slug: 'lance-minimo-pregao-eletronico',
    title: 'Qual o valor de lance mínimo no pregão eletrônico?',
    category: 'precos-propostas',
    answer:
      'No pregão eletrônico, o lance e a oferta de preço feita pelos licitantes durante a fase de disputa em tempo real. O valor mínimo de diferença entre lances (decremento mínimo) é definido pelo pregoeiro no edital e varia conforme o objeto é o valor estimado.\n\n' +
      '**Regras sobre lances na Lei 14.133/2021:**\n\n' +
      '**Modos de disputa (art. 56):**\n\n' +
      '1. **Modo aberto:** Lances públicos e sucessivos em tempo real. É o mais comum no pregão.\n' +
      '   - Intervalo entre lances: definido no edital (ex: R$ 0,01, R$ 1,00, R$ 100,00)\n' +
      '   - Tempo de disputa: aleatório após período mínimo (2 a 30 minutos, conforme o sistema)\n' +
      '   - Lances crescentes (leilão) ou decrescentes (pregão)\n\n' +
      '2. **Modo fechado:** Proposta única, sem fase de lances. Usado quando não e adequada a disputa em tempo real.\n\n' +
      '3. **Modo aberto-fechado:** Fase aberta de lances seguida de lance final fechado dos 3 primeiros colocados.\n\n' +
      '**Decremento mínimo:**\n\n' +
      'O edital fixa o valor ou percentual mínimo de diferença entre os lances. Exemplos típicos:\n' +
      '- Bens de baixo valor: R$ 0,01 a R$ 0,50\n' +
      '- Serviços: R$ 1,00 a R$ 50,00\n' +
      '- Obras: R$ 100,00 a R$ 1.000,00\n' +
      '- Percentual: 0,1% a 1% do valor do lance anterior\n\n' +
      '**Regras práticas:**\n' +
      '- O lance deve ser inferior ao seu lance anterior (você não pode aumentar)\n' +
      '- O lance deve respeitar o decremento mínimo do edital\n' +
      '- Lances iguais ou superiores ao anterior são rejeitados pelo sistema automaticamente\n' +
      '- Você pode dar lances a qualquer momento durante a fase aberta\n' +
      '- O lance e irretratável — uma vez enviado, não pode ser cancelado\n\n' +
      '**Estratégia de lances:**\n' +
      '- Conheca seu preço mínimo viável ANTES da sessão\n' +
      '- Comece com lances moderados, não revele seu melhor preço de imediato\n' +
      '- Acompanhe os lances dos concorrentes em tempo real\n' +
      '- Nos segundos finais do tempo aleatório, esteja preparado para o lance decisivo\n' +
      '- Nunca va abaixo do seu custo — a vitória a qualquer preço não é vitória',
    legalBasis: 'Lei 14.133/2021, art. 56',
    relatedTerms: ['lance', 'pregao-eletronico', 'pregoeiro'],
    relatedSectors: [],
    relatedArticles: ['pregao-eletronico-guia-passo-a-passo'],
    metaDescription:
      'Entenda como funcionam os lances no pregão eletrônico: decremento mínimo, modos de disputa e estratégias para vencer.',
  },
  {
    slug: 'ata-registro-precos-como-funciona',
    title: 'Como funciona a Ata de Registro de Preços (SRP)?',
    category: 'precos-propostas',
    answer:
      'O Sistema de Registro de Preços (SRP) e um procedimento especial de licitação em que a administração registra os preços de fornecedores para futuras aquisições, sem compromisso imediato de compra. A Ata de Registro de Preços (ARP) é o documento que formaliza esse registro.\n\n' +
      '**Quando usar o SRP (art. 82, Lei 14.133):**\n' +
      '- Aquisições frequentes do mesmo objeto\n' +
      '- Contratação por mais de um órgão (compra compartilhada)\n' +
      '- Quando não é possível definir o quantitativo exato antecipadamente\n' +
      '- Bens com entrega parcelada\n\n' +
      '**Como funciona na prática:**\n\n' +
      '1. **Licitação:** O órgão gerenciador realiza pregão ou concorrência para registrar preços.\n' +
      '2. **Ata de Registro:** Os fornecedores classificados assinam a ARP com preços, quantitativos e condições.\n' +
      '3. **Vigência da ata:** Até 1 ano, prorrogável por mais 1 ano (total 2 anos — art. 84).\n' +
      '4. **Emissão de pedidos:** Quando necessitar, o órgão emite ordens de fornecimento contra a ata.\n' +
      '5. **Adesão (carona):** Outros órgãos podem aderir a ata, nas condições registradas.\n\n' +
      '**Vantagens para fornecedores:**\n' +
      '- Garantia de preço registrado por até 2 anos\n' +
      '- Possibilidade de fornecimento para múltiplos órgãos (via adesão)\n' +
      '- Fluxo de pedidos recorrente sem nova licitação\n' +
      '- Volume potencial significativo\n\n' +
      '**Obrigações do fornecedor registrado:**\n' +
      '- Manter o preço registrado durante a vigência\n' +
      '- Atender os pedidos dentro do prazo estipulado\n' +
      '- Manter as condições de habilitação\n' +
      '- O fornecedor NAO e obrigado a fornecer além do quantitativo registrado\n\n' +
      '**Adesão a ata (carona):**\n' +
      'A Lei 14.133 limitou a adesão: órgãos não participantes podem aderir até o limite de 50% dos quantitativos registrados, e cada adesão individual esta limitada a 50% do total (art. 86). O fornecedor pode aceitar ou recusar a adesão.\n\n' +
      '**Dica estratégica:** Participar de registros de preços de órgãos gerenciadores grandes (como ministérios e secretarias estaduais) pode gerar volume significativo de vendas via adesões.',
    legalBasis: 'Lei 14.133/2021, arts. 82 a 86',
    relatedTerms: ['registro-precos', 'ata-registro-precos', 'pregao-eletronico'],
    relatedSectors: [],
    relatedArticles: ['ata-registro-precos-estrategia-licitacao'],
    metaDescription:
      'Entenda como funciona o Sistema de Registro de Preços (SRP) e a Ata de Registro: vigência, adesão e estratégias.',
  },
  {
    slug: 'indice-reajuste-contrato-publico',
    title: 'Qual índice usar para reajuste de contrato público?',
    category: 'precos-propostas',
    answer:
      'O reajuste contratual e a correção periódica dos preços do contrato para compensar a inflação e manter o poder de compra do valor pactuado. A Lei 14.133/2021 trata do reajuste no artigo 92, parágrafo 3, e artigos 134-135.\n\n' +
      '**Índices mais utilizados em contratos públicos:**\n\n' +
      '| Índice | Órgão | Uso Principal |\n' +
      '|--------|-------|---------------|\n' +
      '| IPCA | IBGE | Índice oficial de inflação; contratos de bens e serviços em geral |\n' +
      '| INPC | IBGE | Contratos com componente de mao de obra; base para salário mínimo |\n' +
      '| IGP-M | FGV | Contratos de aluguel, fornecimentos de longo prazo |\n' +
      '| SINAPI | Caixa | Obras e serviços de engenharia (custo unitário) |\n' +
      '| SICRO | DNIT | Obras rodoviárias |\n' +
      '| IPC-Fipe | FIPE | Contratos municipais (São Paulo) |\n\n' +
      '**Regras de reajuste na Lei 14.133:**\n\n' +
      '1. **Periodicidade:** O reajuste só pode ocorrer após 12 meses da data do orçamento estimativo da contratação (não da assinatura do contrato).\n' +
      '2. **Previsão contratual:** O índice de reajuste deve estar previsto no edital e no contrato.\n' +
      '3. **Automaticidade:** O reajuste é um direito do contratado — não depende de pedido formal se estiver previsto contratualmente.\n' +
      '4. **Retroatividade:** Se o pedido for tardio, retroage a data-base.\n\n' +
      '**Reajuste versus repactuação:**\n' +
      '- **Reajuste por índice:** Aplicação automática de índice sobre o valor total. Para bens e serviços em geral.\n' +
      '- **Repactuação:** Revisão detalhada da planilha com base em convenção coletiva. Para serviços com dedicação de mao de obra.\n\n' +
      '**Qual índice escolher?**\n' +
      '- Para bens e serviços gerais: IPCA (mais conservador) ou IGP-M (mais volatil)\n' +
      '- Para obras: SINAPI ou SICRO (setoriais, mais precisos)\n' +
      '- Para serviços com mao de obra: INPC + repactuação por CCT\n' +
      '- Para TI: IPCA ou índice setorial de TI (quando disponível)\n\n' +
      '**Dica:** Ao formular proposta, verifique qual índice o edital preve para reajuste. Índices como o IGP-M tendem a variar mais que o IPCA, o que pode ser vantajoso ou desvantajoso dependendo do cenário econômico.',
    legalBasis: 'Lei 14.133/2021, arts. 92 (par. 3), 134, 135',
    relatedTerms: ['reajuste', 'contrato-administrativo', 'reequilibrio-economico-financeiro'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Saiba qual índice usar para reajuste de contrato público: IPCA, IGP-M, SINAPI e regras da Lei 14.133/2021.',
  },

  /* ================================================================ */
  /*  SETORES ESPECIFICOS (7)                                          */
  /* ================================================================ */
  {
    slug: 'licitacao-ti-requisitos-especificos',
    title: 'Quais requisitos específicos existem em licitações de TI?',
    category: 'setores-especificos',
    answer:
      'As licitações de Tecnologia da Informação e Comunicação (TIC) possuem normas específicas que vão além da Lei 14.133/2021, incluindo a IN SGD/ME 94/2022 (Instrução Normativa de Contratações de TIC) e o Modelo de Contratação de Soluções de TIC.\n\n' +
      '**Normas específicas para TI:**\n\n' +
      '1. **IN SGD/ME 94/2022:** Regulamenta contratações de TIC no Executivo Federal.\n' +
      '2. **Modelo de Contratação (MCTIC):** Fases de planejamento, seleção e gestão.\n' +
      '3. **Lei 14.133, art. 20:** Exigência de estudo técnico preliminar (ETP) detalhado.\n\n' +
      '**Etapas obrigatórias no planejamento de TI:**\n\n' +
      '1. **DOD (Documento de Oficialização de Demanda):** Formalização da necessidade.\n' +
      '2. **ETP (Estudo Técnico Preliminar):** Análise de viabilidade, alternativas de mercado, custos.\n' +
      '3. **Análise de riscos:** Mapeamento de riscos técnicos, financeiros e operacionais.\n' +
      '4. **Termo de referência:** Especificação detalhada da solução, níveis de serviço (SLA), métricas.\n\n' +
      '**Requisitos técnicos comuns:**\n' +
      '- Certificações (ISO 27001, ISO 20000, CMMI, ITIL)\n' +
      '- Equipe técnica com certificações específicas (AWS, Azure, CISSP, PMP)\n' +
      '- Atestados de capacidade técnica em projetos similares\n' +
      '- Plano de transição para troca de fornecedor\n' +
      '- Política de segurança da informação\n' +
      '- Plano de backup e recuperação de desastres\n\n' +
      '**SLA (Service Level Agreement):**\n' +
      'Licitações de TI frequentemente incluem métricas de SLA:\n' +
      '- Disponibilidade: 99,5% a 99,99%\n' +
      '- Tempo de resposta a incidentes: 15min a 4h\n' +
      '- Tempo de resolução: 2h a 48h\n' +
      '- Aplicação de glosas pôr descumprimento\n\n' +
      '**Particularidades de contratação SaaS:**\n' +
      '- Backup e portabilidade de dados são obrigatórios\n' +
      '- Dados em território nacional (LGPD compliance)\n' +
      '- Plano de saida (exit plan) com exportação de dados\n' +
      '- Propriedade intelectual dos dados e do contratante\n\n' +
      '**Dica para empresas de TI:** Invista em certificações (ISO 27001, CMMI) e mantenha equipe certificada. Esses são os diferenciais mais exigidos em licitações federais de TI.',
    legalBasis: 'Lei 14.133/2021, art. 20; IN SGD/ME 94/2022',
    relatedTerms: ['termo-referencia', 'habilitacao', 'licitacao'],
    relatedSectors: ['informatica'],
    relatedArticles: [],
    metaDescription:
      'Conheca os requisitos específicos de licitações de TI: IN SGD 94/2022, SLAs, certificações e contratação de SaaS.',
  },
  {
    slug: 'licitacao-saude-anvisa-requisitos',
    title: 'Quais exigências da ANVISA se aplicam a licitações de saúde?',
    category: 'setores-especificos',
    answer:
      'Licitações de produtos e serviços de saúde possuem exigências regulatórias adicionais da ANVISA (Agência Nacional de Vigilância Sanitária) que devem ser atendidas tanto pelo edital quanto pelos licitantes. Essas exigências visam garantir a segurança e eficacia dos produtos utilizados no SUS e em serviços de saúde públicos.\n\n' +
      '**Exigências de registro e autorização:**\n\n' +
      '1. **Registro na ANVISA:** Medicamentos, equipamentos médicos, materiais hospitalares e produtos para saúde devem ter registro válido na ANVISA (ou notificação, conforme a classe de risco).\n' +
      '2. **AFE (Autorização de Funcionamento):** A empresa deve possuir AFE expedida pela ANVISA para fabricar, importar ou distribuir produtos sujeitos a vigilância sanitária.\n' +
      '3. **Licenca sanitária:** Emitida pela vigilância sanitária estadual/municipal do local de fabricação ou armazenamento.\n' +
      '4. **CBPF (Certificado de Boas Práticas de Fabricação):** Obrigatório para fabricantes de medicamentos, produtos biológicos e alguns dispositivos médicos.\n\n' +
      '**Classificação de risco de dispositivos médicos:**\n' +
      '- Classe I (baixo risco): notificação (ex: luvas, seringas)\n' +
      '- Classe II (medio risco): registro (ex: equipamentos de monitoramento)\n' +
      '- Classe III e IV (alto risco): registro com análise mais rigorosa (ex: implantes, equipamentos de suporte a vida)\n\n' +
      '**Exigências em editais de saúde:**\n' +
      '- Registro ANVISA vigente (número e validade)\n' +
      '- AFE do fabricante e do distribuidor\n' +
      '- Laudo de análise ou certificado de qualidade\n' +
      '- Rastreabilidade completa do produto\n' +
      '- Prazo de validade mínimo (geralmente 75% da validade total na entrega)\n' +
      '- Amostras para avaliação técnica\n\n' +
      '**Compras emergenciais de saúde:**\n' +
      'Em situações de emergência sanitária, a ANVISA pode conceder registro temporário ou autorização de uso emergencial (como ocorreu com vacinas da COVID-19), flexibilizando requisitos sem comprometer a segurança.\n\n' +
      '**Dica para fornecedores de saúde:** Mantenha todos os registros ANVISA atualizados com antecedência — o processo de renovação pode levar meses. Verifique se o distribuidor autorizado também possui AFE e licenca sanitária vigentes.',
    legalBasis:
      'Lei 14.133/2021; Lei 6.360/1976; RDC ANVISA 185/2001',
    relatedTerms: ['habilitacao', 'licitacao', 'edital'],
    relatedSectors: ['saude', 'equipamentos-medicos'],
    relatedArticles: [],
    metaDescription:
      'Saiba quais exigências da ANVISA se aplicam a licitações de saúde: registro, AFE, CBPF e requisitos pôr classe de risco.',
  },
  {
    slug: 'licitacao-obras-engenharia-qualificacao',
    title: 'Qual qualificação técnica e exigida em obras de engenharia?',
    category: 'setores-especificos',
    answer:
      'Licitações de obras e serviços de engenharia possuem os requisitos mais rigorosos de qualificação técnica, dada a complexidade, os riscos envolvidos e os valores tipicamente elevados. A Lei 14.133/2021 detalha essas exigências nos artigos 67 e 68.\n\n' +
      '**Qualificação técnico-profissional (art. 67, I):**\n\n' +
      '1. **Registro no CREA/CAU:** A empresa deve ter registro no Conselho Regional de Engenharia e Agronomia ou no Conselho de Arquitetura e Urbanismo.\n' +
      '2. **Responsável técnico:** Indicação de profissional(is) com:\n' +
      '   - Registro ativo no CREA/CAU\n' +
      '   - CAT (Certidão de Acervo Técnico) comprovando experiência em parcelas de maior relevância técnica\n' +
      '   - Vinculo com a empresa (contrato de trabalho, contrato social ou contrato de prestação de serviços)\n\n' +
      '**Qualificação técnico-operacional (art. 67, II):**\n\n' +
      '1. **Atestados da empresa:** Comprovação de que a empresa executou obras/serviços de natureza e complexidade similares ao objeto.\n' +
      '2. **Parcelas de maior relevância:** O edital deve definir quais parcelas são de maior relevância técnica e valor significativo.\n' +
      '3. **Quantitativos:** Não pode exigir quantidades idênticas ao objeto — a jurisprudência do TCU admite até 50% como parametro.\n\n' +
      '**Documentos específicos de engenharia:**\n' +
      '- ART/RRT (Anotação de Responsabilidade Técnica / Registro de Responsabilidade Técnica)\n' +
      '- CAT (Certidão de Acervo Técnico)\n' +
      '- Registro no CREA/CAU (empresa e profissionais)\n' +
      '- Atestados com acervo registrado\n' +
      '- Declaração de disponibilidade de equipamentos\n\n' +
      '**Exigências complementares comuns:**\n' +
      '- ISO 9001 (sistema de gestão de qualidade)\n' +
      '- PBQP-H (Programa Brasileiro de Qualidade e Produtividade do Habitat) — nível A\n' +
      '- Certificação ambiental (ISO 14001)\n' +
      '- Programa de segurança (PCMSO, PPRA)\n\n' +
      '**Limites das exigências (jurisprudência TCU):**\n' +
      '- Vedado exigir número mínimo de obras executadas (Sumula 263)\n' +
      '- Vedado exigir atestados de obra idêntica (deve aceitar similar)\n' +
      '- Vedado exigir tempo mínimo de experiência da empresa\n' +
      '- Permitido exigir experiência em parcelas de maior relevância com quantitativos razoáveis',
    legalBasis: 'Lei 14.133/2021, arts. 67, 68; Sumula TCU 263',
    relatedTerms: ['habilitacao', 'parecer-tecnico', 'licitacao'],
    relatedSectors: ['engenharia', 'construcao'],
    relatedArticles: ['checklist-habilitacao-licitacao-2026'],
    metaDescription:
      'Veja a qualificação técnica exigida em obras de engenharia: CREA/CAU, CAT, atestados e limites do TCU.',
  },
  {
    slug: 'licitacao-alimentos-merenda-regras',
    title:
      'Quais regras especiais existem para licitações de merenda escolar?',
    category: 'setores-especificos',
    answer:
      'As licitações de alimentação escolar (merenda) possuem legislação específica que vai além da Lei 14.133/2021. O Programa Nacional de Alimentação Escolar (PNAE), gerido pelo FNDE, estabelece regras próprias para aquisição de alimentos para escolas públicas.\n\n' +
      '**Legislação específica:**\n' +
      '- Lei 11.947/2009 (PNAE)\n' +
      '- Resolução FNDE 06/2020 (regulamentação do PNAE)\n' +
      '- Lei 14.133/2021 (licitações em geral)\n\n' +
      '**Regra dos 30% para agricultura familiar (art. 14, Lei 11.947):**\n\n' +
      'No mínimo 30% dos recursos do FNDE destinados a merenda escolar devem ser utilizados na compra de alimentos diretamente da agricultura familiar e do empreendedor familiar rural. Essa compra utiliza a **Chamada Pública** (dispensa de licitação), não pregão.\n\n' +
      '**Requisitos nutricionais:**\n' +
      '- Cardapio elaborado por nutricionista (RT do PNAE)\n' +
      '- Respeito a habitos alimentares regionais\n' +
      '- Proibição de bebidas com baixo teor nutricional\n' +
      '- Oferta de frutas e hortaliças (mínimo 3x por semana)\n' +
      '- Limite de acucar, sodio e gordura saturada\n\n' +
      '**Exigências sanitárias:**\n' +
      '- Alvara sanitário vigente do fornecedor\n' +
      '- Licenca de funcionamento da vigilância sanitária\n' +
      '- Controle de qualidade com laudos laboratoriais\n' +
      '- Rastreabilidade dos produtos (lote, validade, procedência)\n' +
      '- Rotulagem conforme normas da ANVISA\n' +
      '- Transporte adequado (cadeia fria para perecíveis)\n\n' +
      '**Particularidades das licitações de alimentos:**\n\n' +
      '1. **Amostras obrigatórias:** O edital pode exigir amostras para degustação e análise.\n' +
      '2. **Marca:** Permitido indicar marcas como referência de qualidade.\n' +
      '3. **Entrega parcelada:** Obrigatória para perecíveis (semanal ou quinzenal).\n' +
      '4. **SRP (Registro de Preços):** Muito utilizado pela variação sazonal de preços.\n' +
      '5. **Orgânicos:** Preferência para alimentos orgânicos e agroecológicos.\n\n' +
      '**Dica para fornecedores:** O mercado de merenda escolar é enorme e recorrente. Se você atua com alimentos, mantenha alvara sanitário atualizado, invista em logística de entrega e considere se cadastrar como fornecedor da agricultura familiar (DAP/CAF) para acessar os 30% reservados.',
    legalBasis:
      'Lei 11.947/2009, art. 14; Resolução FNDE 06/2020; Lei 14.133/2021',
    relatedTerms: ['licitacao', 'dispensa', 'registro-precos'],
    relatedSectors: ['alimentos', 'educacao'],
    relatedArticles: [],
    metaDescription:
      'Conheca as regras especiais de licitação de merenda escolar: 30% agricultura familiar, PNAE, requisitos sanitários.',
  },
  {
    slug: 'licitacao-software-saas-contratacao',
    title: 'Como funciona a contratação de software SaaS pelo governo?',
    category: 'setores-especificos',
    answer:
      'A contratação de software como serviço (SaaS — Software as a Service) pelo governo brasileiro segue regras específicas da IN SGD/ME 94/2022 e da Lei 14.133/2021, além de orientações do Tribunal de Contas da União.\n\n' +
      '**Enquadramento legal:**\n' +
      'SaaS e classificado como serviço (não licenciamento de software), o que permite contratação por pregão eletrônico na modalidade de menor preço por item ou global. A assinatura mensal/anual é tratada como serviço continuado.\n\n' +
      '**Requisitos obrigatórios em contratação SaaS:**\n\n' +
      '1. **Segurança da informação:**\n' +
      '   - Dados armazenados em território nacional (LGPD, art. 33)\n' +
      '   - Criptografia em transito e em repouso\n' +
      '   - Autenticação multifator\n' +
      '   - Logs de auditoria acessíveis\n' +
      '   - Conformidade com a Política de Segurança do órgão\n\n' +
      '2. **Portabilidade e interoperabilidade:**\n' +
      '   - Exportação de dados em formato aberto (CSV, JSON, XML)\n' +
      '   - API documentada para integração\n' +
      '   - Plano de transição para troca de fornecedor (exit plan)\n' +
      '   - Prazo de 90 dias após encerramento para exportação\n\n' +
      '3. **Níveis de serviço (SLA):**\n' +
      '   - Disponibilidade mínima: 99,5% a 99,9%\n' +
      '   - Tempo de resposta a incidentes\n' +
      '   - RPO e RTO definidos (backup e recuperação)\n' +
      '   - Penalidades (glosas) por descumprimento\n\n' +
      '4. **LGPD compliance:**\n' +
      '   - Contrato de processamento de dados (DPA)\n' +
      '   - Encarregado de dados (DPO) indicado\n' +
      '   - Registro de operações de tratamento\n\n' +
      '**Modelo de precificação aceito:**\n' +
      '- Por usuário/mês (mais comum)\n' +
      '- Por volume de transações\n' +
      '- Por modulo funcional\n' +
      '- Tarifa fixa mensal\n\n' +
      '**Vigência contratual:**\n' +
      'Contratos de SaaS são classificados como serviços continuados — vigência de até 5 anos, prorrogável a 10 anos (art. 106).\n\n' +
      '**Dica para empresas de SaaS:** Prepare uma documentação técnica robusta (arquitetura, segurança, SLA, política de backup, LGPD) que possa ser anexada a qualquer proposta. Muitos editais exigem esses documentos na habilitação técnica.',
    legalBasis: 'Lei 14.133/2021, art. 106; IN SGD/ME 94/2022; LGPD',
    relatedTerms: ['termo-referencia', 'licitacao', 'pregao-eletronico'],
    relatedSectors: ['informatica'],
    relatedArticles: [],
    metaDescription:
      'Entenda como funciona a contratação de SaaS pelo governo: LGPD, SLA, portabilidade de dados e requisitos da IN SGD 94.',
  },
  {
    slug: 'licitacao-vigilancia-requisitos-pf',
    title:
      'Quais requisitos da Polícia Federal se aplicam a vigilância?',
    category: 'setores-especificos',
    answer:
      'A prestação de serviços de vigilância patrimonial e segurança privada para órgãos públicos e regulamentada pela Lei 7.102/1983, pelo Decreto 89.056/1983 e por portarias da Polícia Federal. Esses requisitos são adicionais aos da Lei 14.133/2021.\n\n' +
      '**Autorização da Polícia Federal:**\n\n' +
      '1. **Autorização de funcionamento:** A empresa deve possuir autorização de funcionamento expedida pela Delegacia de Controle de Segurança Privada (DELESP) ou Comissão de Vistoria da PF, válida para o estado de execução do serviço.\n' +
      '2. **Revisão de autorização:** A autorização deve ser revisada anualmente.\n' +
      '3. **Certificado de Segurança:** Documento que atesta a regularidade da empresa junto a PF.\n\n' +
      '**Requisitos para a empresa:**\n' +
      '- Capital social integralizado mínimo (definido pela PF conforme a região)\n' +
      '- Instalações físicas adequadas (escritório, deposito de armamento)\n' +
      '- Seguro de vida em grupo para vigilantes\n' +
      '- Contrato de seguro de responsabilidade civil\n' +
      '- Plano de segurança aprovado\n\n' +
      '**Requisitos para os vigilantes:**\n' +
      '- Curso de formação de vigilante (reciclagem a cada 2 anos)\n' +
      '- Certificado de aptidão psicológica\n' +
      '- Certidão negativa de antecedentes criminais\n' +
      '- Carteira Nacional de Vigilante (CNV) válida\n' +
      '- Aptidão física comprovada\n\n' +
      '**Exigências em editais de vigilância:**\n' +
      '- Autorização da PF para vigilância patrimonial (obrigatória)\n' +
      '- Certificado de Segurança vigente\n' +
      '- Atestados de capacidade técnica em postos de vigilância\n' +
      '- Planilha de custos conforme CCT da categoria\n' +
      '- Uniforme e equipamentos conforme Portaria DG/PF\n' +
      '- Se armada: certificado de registro de armas, apolice de seguro, plano de transporte\n\n' +
      '**Vigilância armada versus desarmada:**\n' +
      '- Armada: requisitos adicionais de controle de armamento, cofre, plano de tiro\n' +
      '- Desarmada: requisitos simplificados, sem controle de armas\n' +
      '- Eletrônica: CFTV, alarmes, monitoramento 24h — requisitos tecnológicos adicionais\n\n' +
      '**Dica:** A regularização junto a PF pode levar meses. Se você está iniciando no segmento de segurança privada, comece o processo de autorização com bastante antecedência.',
    legalBasis: 'Lei 7.102/1983; Decreto 89.056/1983; Portarias DG/PF',
    relatedTerms: ['habilitacao', 'licitacao', 'edital'],
    relatedSectors: ['seguranca'],
    relatedArticles: [],
    metaDescription:
      'Conheca os requisitos da Polícia Federal para licitações de vigilância: autorização, CNV, seguro e controle de armamento.',
  },
  {
    slug: 'licitacao-facilities-planilha-custos',
    title:
      'Como montar a planilha de custos em licitações de facilities?',
    category: 'setores-especificos',
    answer:
      'Licitações de facilities (gestão de facilidades) abrangem serviços como limpeza, manutenção predial, portaria, jardinagem, controle de pragas e serviços administrativos. Por envolverem dedicação exclusiva de mao de obra, exigem planilha de custos detalhada conforme a IN SEGES/ME 65/2021.\n\n' +
      '**Estrutura da planilha de custos para facilities:**\n\n' +
      '**1. Remuneração (baseada na CCT):**\n' +
      '- Salário-base da categoria (zelador, porteiro, auxiliar de limpeza)\n' +
      '- Adicional de insalubridade (limpeza: 20% ou 40% do salário mínimo)\n' +
      '- Adicional noturno (portaria 24h: 20% para 22h-05h)\n' +
      '- Hora extra habitual (se prevista na CCT)\n\n' +
      '**2. Encargos sociais e trabalhistas:**\n' +
      '- Grupo A: INSS (20%), SAT/RAT (1-3%), Terceiros (5,8%), FGTS (8%) = ~37%\n' +
      '- Grupo B: 13o salário (8,33%), férias + 1/3 (11,11%) = ~20%\n' +
      '- Grupo C: Aviso prévio, multa FGTS = ~5-7%\n' +
      '- Grupo D: Incidência cumulativa dos grupos\n' +
      '- **Total encargos: 65% a 85%** do salário (varia por CCT e regime)\n\n' +
      '**3. Beneficios (conforme CCT):**\n' +
      '- Vale-transporte (6% do salário descontado do empregado)\n' +
      '- Vale-alimentação/refeição (valor da CCT)\n' +
      '- Assistência médica (se previsto na CCT)\n' +
      '- Seguro de vida (obrigatório pela CCT em muitas categorias)\n' +
      '- Cesta básica (se previsto)\n\n' +
      '**4. Insumos e custos operacionais:**\n' +
      '- Uniformes e EPI (quantidade anual por funcionário)\n' +
      '- Materiais de limpeza (litros/unidades por m2)\n' +
      '- Equipamentos (aspiradores, lavadoras, etc.)\n' +
      '- Treinamento e reciclagem\n\n' +
      '**5. Custos indiretos, lucro e tributos:**\n' +
      '- Administração/supervisão: 3% a 5%\n' +
      '- Lucro: 5% a 10%\n' +
      '- Tributos: ISS (2-5%), PIS (0,65-1,65%), COFINS (3-7,6%), IRPJ, CSLL\n\n' +
      '**Erros fatais em planilhas de facilities:**\n' +
      '- Usar CCT da categoria errada ou de outro estado\n' +
      '- Esquecer adicional de insalubridade para limpeza\n' +
      '- Não considerar intrajornada para jornada 12x36\n' +
      '- Subestimar custo de substituição (férias, faltas, licencas)\n' +
      '- Não prever custo de supervisão/encarregado\n\n' +
      '**Dica:** A CCT da categoria na região de execução é a BIBLIA da sua planilha. Consulte o sindicato patronal e laboral para obter a convenção vigente com todas as cláusulas econômicas.',
    legalBasis: 'Lei 14.133/2021, art. 63; IN SEGES/ME 65/2021',
    relatedTerms: ['proposta', 'bdi', 'licitacao'],
    relatedSectors: ['facilities', 'servicos-gerais'],
    relatedArticles: ['como-calcular-preco-proposta-licitacao'],
    metaDescription:
      'Guia completo para montar planilha de custos em licitações de facilities: remuneração, encargos, CCT e erros a evitar.',
  },

  /* ================================================================ */
  /*  TECNOLOGIA E SISTEMAS (9)                                        */
  /* ================================================================ */
  {
    slug: 'pncp-o-que-e-como-usar',
    title: 'O que é o PNCP e como consultar licitações?',
    category: 'tecnologia-sistemas',
    answer:
      'O PNCP (Portal Nacional de Contratações Públicas) e a plataforma digital oficial do Governo Federal criada pela Lei 14.133/2021 para centralizar a divulgação de todas as licitações, contratações diretas, atas de registro de preços e contratos públicos do país — nas esferas federal, estadual e municipal.\n\n' +
      '**O que o PNCP oferece:**\n' +
      '- Publicação obrigatória de editais de todas as esferas\n' +
      '- Acesso a atas, contratos e aditivos\n' +
      '- Consulta de preços praticados em contratações\n' +
      '- Dados abertos para pesquisa e análise\n' +
      '- API pública para integração com sistemas\n\n' +
      '**Como consultar licitações no PNCP:**\n\n' +
      '1. **Acesse pncp.gov.br** — o portal e público, não exige login para consulta.\n' +
      '2. **Use a busca avancada** com filtros:\n' +
      '   - Palavra-chave no objeto da contratação\n' +
      '   - UF e municipio do órgão contratante\n' +
      '   - Modalidade (pregão, concorrência, dispensa)\n' +
      '   - Esfera (federal, estadual, municipal)\n' +
      '   - Data de publicação\n' +
      '   - Faixa de valor estimado\n' +
      '3. **Análise os resultados:** Cada licitação exibe o resumo do objeto, órgão contratante, valor estimado, data de abertura e situação.\n' +
      '4. **Acesse o edital completo:** Clique na licitação para ver o edital, anexos e documentos.\n\n' +
      '**API do PNCP:**\n' +
      'O PNCP disponibiliza uma API REST pública (pncp.gov.br/api) para consulta automatizada de contratações. Isso permite que ferramentas como o SmartLic agreguem e classifiquem licitações automaticamente, facilitando a descoberta de oportunidades por setor e região.\n\n' +
      '**Limitações atuais do PNCP:**\n' +
      '- Nem todos os municipios publicam no PNCP ainda (adesão progressiva)\n' +
      '- A busca textual e básica (sem sinônimos ou classificação inteligente)\n' +
      '- Dados históricos anteriores a 2023 são incompletos\n' +
      '- O sistema de filtros pode ser lento em horários de pico\n\n' +
      '**Dica:** Para maximizar a cobertura, combine o PNCP com plataformas complementares como o Portal de Compras Públicas, BLL, Licitações-e e portais estaduais. Ou use o SmartLic, que consolida todas essas fontes em uma busca única com classificação por setor.',
    legalBasis: 'Lei 14.133/2021, arts. 174, 175, 176',
    relatedTerms: ['pncp', 'licitacao', 'edital'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Saiba o que é o PNCP, como consultar licitações, usar filtros de busca e acessar editais de todas as esferas do governo.',
  },
  {
    slug: 'comprasnet-como-participar',
    title: 'Como participar de licitações no ComprasNet/ComprasGov?',
    category: 'tecnologia-sistemas',
    answer:
      'O ComprasGov (antigo ComprasNet) e o sistema eletrônico de compras do Governo Federal, operado pelo Ministério da Gestão e da Inovação. E a principal plataforma para participação em licitações federais — pregões, concorrências e dispensas eletrônicas.\n\n' +
      '**Como se cadastrar e participar:**\n\n' +
      '**1. Cadastro no gov.br:**\n' +
      '- Crie uma conta gov.br (https://acesso.gov.br) com nível prata ou ouro\n' +
      '- Vincule o CPF do representante legal ao CNPJ da empresa\n\n' +
      '**2. Cadastro no SICAF:**\n' +
      '- Acesse comprasgov.br e selecione "Fornecedor"\n' +
      '- Complete o cadastro SICAF com documentos de habilitação\n' +
      '- Obtenha credenciamento nos níveis necessários (I a VI)\n\n' +
      '**3. Certificado digital:**\n' +
      '- Adquira certificado digital ICP-Brasil tipo A1 (arquivo) ou A3 (token/cartão)\n' +
      '- Associe o certificado ao CNPJ da empresa no sistema\n\n' +
      '**4. Participando de uma licitação:**\n\n' +
      'a) **Busca de editais:** Use o modulo "Editais" para encontrar licitações por palavra-chave, UASG, data ou tipo.\n' +
      'b) **Leitura do edital:** Baixe e leia o edital completo, incluindo termo de referência e planilhas.\n' +
      'c) **Cadastro de proposta:** Na data indicada, acesse o modulo do certame e cadastre sua proposta com preços e declarações.\n' +
      'd) **Sessão pública:** No dia e horário marcados, acompanhe a sessão eletrônica para a fase de lances.\n' +
      'e) **Lances:** Oferte lances decrescentes em tempo real durante a fase de disputa.\n' +
      'f) **Habilitação:** Se classificado em primeiro lugar, o pregoeiro verifica seus documentos no SICAF.\n' +
      'g) **Adjudicação:** Sendo habilitado é após prazo recursal, o objeto é adjudicado.\n\n' +
      '**Dicas importantes:**\n' +
      '- Teste seu certificado digital ANTES da sessão — problemas técnicos no dia podem impedir a participação.\n' +
      '- Fique atento ao chat do sistema — o pregoeiro pode solicitar documentos ou esclarecimentos durante a sessão com prazos curtos (2-4 horas).\n' +
      '- Mantenha o SICAF atualizado — certidões vencidas impedem a habilitação.\n' +
      '- Acompanhe o resultado pelo sistema — recursos e convocações são notificados eletronicamente.',
    legalBasis: 'Lei 14.133/2021; Decreto 10.024/2019',
    relatedTerms: ['pregao-eletronico', 'sicaf', 'pncp'],
    relatedSectors: [],
    relatedArticles: ['pregao-eletronico-guia-passo-a-passo'],
    metaDescription:
      'Guia completo para participar de licitações no ComprasGov: cadastro, SICAF, certificado digital e passo a passo.',
  },
  {
    slug: 'certificado-digital-licitacao',
    title: 'Qual certificado digital é necessário para licitações?',
    category: 'tecnologia-sistemas',
    answer:
      'O certificado digital é indispensável para participar de licitações eletrônicas no Brasil. Ele autêntica a identidade do licitante no sistema e garante a validade jurídica das propostas, lances e documentos enviados.\n\n' +
      '**Tipo de certificado necessário:**\n\n' +
      'Para licitações, você precisa de um certificado digital e-CNPJ (pessoa jurídica) ou e-CPF (representante legal) da cadeia ICP-Brasil (Infraestrutura de Chaves Públicas Brasileira).\n\n' +
      '**Formatos disponíveis:**\n\n' +
      '| Tipo | Armazenamento | Validade | Preço Medio |\n' +
      '|------|--------------|----------|-------------|\n' +
      '| A1 | Arquivo no computador | 1 ano | R$ 150-300 |\n' +
      '| A3 (token USB) | Token criptográfico | 1-3 anos | R$ 200-500 |\n' +
      '| A3 (cartão) | Smart card + leitora | 1-3 anos | R$ 250-550 |\n' +
      '| A3 (nuvem) | Servidor remoto | 1-5 anos | R$ 200-450 |\n\n' +
      '**Recomendação para licitantes:**\n' +
      '- **A1:** Mais prático para uso diário, pode ser instalado em múltiplos computadores (com copia segura). Ideal para empresas que participam de muitas licitações.\n' +
      '- **A3 token/cartão:** Mais seguro (chave privada não sai do dispositivo), mas exige o token/cartão fisicamente presente. Ideal para quem prioriza segurança.\n' +
      '- **A3 nuvem:** Combina segurança e praticidade — acesso de qualquer dispositivo com autenticação.\n\n' +
      '**Autoridades Certificadoras (AC) reconhecidas:**\n' +
      '- Serasa Experian, Certisign, Valid Certificadora, Safeweb, AC Soluti, entre outras credenciadas pelo ITI.\n\n' +
      '**Como obter:**\n' +
      '1. Escolha uma AC credenciada pelo ITI (iti.gov.br)\n' +
      '2. Solicite o certificado online\n' +
      '3. Agende validação presencial (ou por videoconferência, para A1/A3 nuvem)\n' +
      '4. Apresente documentos da empresa e do representante legal\n' +
      '5. Receba o certificado (download para A1, entrega do token/cartão para A3)\n\n' +
      '**Plataformas que exigem certificado digital:**\n' +
      '- ComprasGov (obrigatório)\n' +
      '- BEC-SP (obrigatório)\n' +
      '- Licitações-e (obrigatório)\n' +
      '- Portal de Compras Públicas (aceita login sem certificado para consulta)\n\n' +
      '**Dica:** Tenha sempre um certificado reserva (ou backup do A1 em local seguro). Se seu certificado expirar ou apresentar problemas no dia de uma sessão, você perde a oportunidade.',
    legalBasis: 'MP 2.200-2/2001 (ICP-Brasil); Lei 14.133/2021',
    relatedTerms: ['pregao-eletronico', 'sicaf', 'licitacao'],
    relatedSectors: [],
    relatedArticles: ['pregao-eletronico-guia-passo-a-passo'],
    metaDescription:
      'Saiba qual certificado digital usar em licitações: tipos A1 e A3, onde comprar, preços e como instalar.',
  },
  {
    slug: 'assinatura-eletronica-contratos-publicos',
    title:
      'Como funciona a assinatura eletrônica em contratos públicos?',
    category: 'tecnologia-sistemas',
    answer:
      'A assinatura eletrônica em contratos públicos foi ampliada pela Lei 14.063/2020 e reafirmada pela Lei 14.133/2021, que permite a formalização de contratos administrativos por meio eletrônico, eliminando a necessidade de documentos físicos.\n\n' +
      '**Níveis de assinatura eletrônica (Lei 14.063/2020):**\n\n' +
      '1. **Assinatura simples:** Identifica o signatário de forma básica (ex: login/senha em sistema). Aceita para atos de menor complexidade.\n\n' +
      '2. **Assinatura avancada:** Utiliza certificados não emitidos pela ICP-Brasil, mas com mecanismos de autenticação robustos (ex: gov.br nível prata/ouro). Aceita para:\n' +
      '   - Interações com entes públicos\n' +
      '   - Atos de gestão interna\n' +
      '   - Documentos entre órgãos públicos\n\n' +
      '3. **Assinatura qualificada:** Utiliza certificado ICP-Brasil. Obrigatória para:\n' +
      '   - Contratos administrativos\n' +
      '   - Atos de transferência de bens imóveis\n' +
      '   - Documentos em que a lei exija reconhecimento de firma\n\n' +
      '**Sistemas utilizados para assinatura:**\n\n' +
      '| Sistema | Ambito | Tipo |\n' +
      '|---------|--------|------|\n' +
      '| SEI (Sistema Eletrônico de Informações) | Federal/Estadual/Municipal | Avancada/Qualificada |\n' +
      '| gov.br (assinatura digital) | Federal | Avancada |\n' +
      '| Portal de Compras (contrato digital) | Plataformas de compras | Qualificada |\n' +
      '| DocuSign / Adobe Sign | Aceitos se ICP-Brasil | Qualificada |\n\n' +
      '**Fluxo típico de assinatura eletrônica de contrato:**\n\n' +
      '1. O órgão elabora a minuta do contrato no sistema (SEI, e-Licitação, etc.)\n' +
      '2. O contratado recebe notificação eletrônica para assinar\n' +
      '3. O contratado acessa o sistema com certificado digital ou conta gov.br\n' +
      '4. Revisa o documento e aplica a assinatura eletrônica\n' +
      '5. O ordenador de despesa do órgão contrassina\n' +
      '6. O contrato e publicado automaticamente no PNCP\n\n' +
      '**Validade jurídica:**\n' +
      'Documentos assinados eletronicamente com certificado ICP-Brasil tem a mesma validade jurídica de documentos assinados em cartório (MP 2.200-2/2001). A integridade e autenticidade são verificáveis a qualquer momento.\n\n' +
      '**Dica prática:** Configure a assinatura eletrônica no seu certificado digital antes da primeira contratação. Familiarize-se com o sistema SEI ou a plataforma do órgão — a assinatura pode ter prazo curtíssimo (24-48h) após notificação.',
    legalBasis:
      'Lei 14.063/2020; Lei 14.133/2021, art. 91; MP 2.200-2/2001',
    relatedTerms: ['contrato-administrativo', 'licitacao', 'pncp'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Entenda como funciona a assinatura eletrônica em contratos públicos: níveis, sistemas, validade jurídica e passo a passo.',
  },
  {
    slug: 'governo-digital-impacto-licitacoes',
    title: 'Como a estratégia de Governo Digital impacta licitações?',
    category: 'tecnologia-sistemas',
    answer:
      'A Estratégia Nacional de Governo Digital (EGD), instituida pelo Decreto 10.332/2020 e atualizada periodicamente, esta transformando profundamente o processo de compras públicas no Brasil. O objetivo e tornar as contratações mais transparentes, eficientes e acessíveis por meio da tecnologia.\n\n' +
      '**Principais impactos nas licitações:**\n\n' +
      '**1. Digitalização completa dos processos:**\n' +
      '- Todos os atos (publicação, proposta, lance, habilitação, recurso, contrato) realizados eletronicamente\n' +
      '- Eliminação de documentos físicos (art. 12, Lei 14.133)\n' +
      '- Assinatura eletrônica em todos os documentos\n\n' +
      '**2. PNCP como plataforma central:**\n' +
      '- Centralização de todas as licitações do país em um único portal\n' +
      '- Dados abertos para consulta pública e análise\n' +
      '- Integração com sistemas estaduais e municipais\n\n' +
      '**3. Identidade digital unificada (gov.br):**\n' +
      '- Login único para todos os sistemas de compras públicas\n' +
      '- Autenticação por biometria e reconhecimento facial\n' +
      '- Nível prata/ouro para operações mais complexas\n\n' +
      '**4. Interoperabilidade de dados:**\n' +
      '- Validação automática de certidões (CND, CRF, CNDT)\n' +
      '- Consulta em tempo real a bases governamentais\n' +
      '- Redução de documentos exigidos na habilitação\n\n' +
      '**5. Inteligência de dados:**\n' +
      '- Painel de Preços com histórico de contratações\n' +
      '- Análise de preços praticados em compras similares\n' +
      '- Detecção de anomalias e irregularidades via IA\n\n' +
      '**Impacto para fornecedores:**\n\n' +
      '- **Maior acessibilidade:** Empresas de qualquer região participam de licitações em todo o país sem deslocamento.\n' +
      '- **Transparência ampliada:** Decisões, atas e contratos acessíveis publicamente.\n' +
      '- **Agilidade:** Processos mais rapidos com menos burocracia documental.\n' +
      '- **Dados para inteligência:** Acesso a dados históricos para análise de mercado e precificação.\n\n' +
      '**Desafios da transição digital:**\n' +
      '- Municipios pequenos com infraestrutura tecnológica limitada\n' +
      '- Necessidade de capacitação de servidores e fornecedores\n' +
      '- Integração entre múltiplos sistemas (federal, estadual, municipal)\n' +
      '- Segurança cibernética e proteção de dados\n\n' +
      '**Para fornecedores, a mensagem é clara:** investir em capacitação digital não é opcional — é uma exigência do mercado de compras públicas.',
    legalBasis: 'Decreto 10.332/2020; Lei 14.133/2021, art. 12',
    relatedTerms: ['pncp', 'licitacao', 'sicaf'],
    relatedSectors: ['informatica'],
    relatedArticles: [],
    metaDescription:
      'Veja como a Estratégia de Governo Digital transforma licitações: PNCP, login único, dados abertos e processos 100% digitais.',
  },
  {
    slug: 'bec-sp-bolsa-eletronica-compras',
    title: 'O que é a BEC/SP Bolsa Eletrônica de Compras?',
    category: 'tecnologia-sistemas',
    answer:
      'A BEC/SP (Bolsa Eletrônica de Compras do Estado de São Paulo) e o sistema eletrônico de compras utilizado pelo Governo do Estado de São Paulo para realizar pregões eletrônicos, dispensas eletrônicas e cotações eletrônicas. É um dos maiores portais de compras públicas do país em volume de transações.\n\n' +
      '**O que a BEC/SP oferece:**\n' +
      '- Pregões eletrônicos estaduais\n' +
      '- Oferta de compra (dispensa eletrônica)\n' +
      '- Cotação eletrônica\n' +
      '- Catalogo de materiais e serviços (Banco BEC)\n' +
      '- Atas de registro de preços estaduais\n\n' +
      '**Como participar:**\n\n' +
      '1. **Cadastro no CAUFESP:** O Cadastro Unificado de Fornecedores do Estado de São Paulo e pre-requisito para participar. Acesse www.bec.sp.gov.br e selecione "Cadastro de Fornecedores".\n' +
      '2. **Documentos necessários:** CNPJ, contrato social, procuração (se aplicável), certidões de regularidade.\n' +
      '3. **Certificado digital:** Obrigatório para participar de pregões (ICP-Brasil).\n' +
      '4. **Senha BEC:** Após o cadastro CAUFESP, solicite senha de acesso ao sistema de pregões.\n\n' +
      '**Particularidades da BEC/SP:**\n\n' +
      '- **Catalogo de materiais:** A BEC mantem um catalogo padronizado de itens (codigos BEC) que facilita a cotação e comparação de preços.\n' +
      '- **Oferta de compra:** Sistema de dispensa eletrônica em que o fornecedor cadastrado oferece preço para demandas do estado — funciona como "balcão virtual".\n' +
      '- **Volume expressivo:** São Paulo é o maior comprador público estadual do Brasil, com milhares de unidades gestoras (secretarias, autarquias, prefeituras conveniadas).\n' +
      '- **Convenio com municipios:** Municipios paulistas podem utilizar a BEC mediante convenio, ampliando o alcance.\n\n' +
      '**Diferença entre BEC/SP e ComprasGov:**\n\n' +
      '| Aspecto | BEC/SP | ComprasGov |\n' +
      '|---------|--------|------------|\n' +
      '| Ambito | Estado de SP + municipios conveniados | Federal |\n' +
      '| Cadastro | CAUFESP | SICAF |\n' +
      '| Catalogo | Banco BEC (codigos próprios) | CATMAT/CATSER |\n' +
      '| Pregão | Sistema próprio | ComprasGov |\n\n' +
      '**Dica para fornecedores:** Se você atua em São Paulo, o cadastro na BEC é praticamente obrigatório. O estado de SP realiza milhares de pregões por mês e o registro de preços estadual pode gerar pedidos de centenas de unidades gestoras.',
    legalBasis: 'Decreto Estadual SP 49.722/2005; Lei 14.133/2021',
    relatedTerms: ['pregao-eletronico', 'licitacao', 'sicaf'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Entenda o que é a BEC/SP, como se cadastrar no CAUFESP e participar de licitações do Estado de São Paulo.',
  },
  {
    slug: 'licitacao-sustentavel-criterios-verdes',
    title: 'O que é licitação sustentável e quais critérios são exigidos?',
    category: 'tecnologia-sistemas',
    answer:
      'A licitação sustentável (ou compra pública verde) é a incorporação de critérios ambientais, sociais e econômicos no processo de contratação pública, buscando reduzir impactos negativos e promover o desenvolvimento sustentável. A Lei 14.133/2021 tornou a sustentabilidade um principio obrigatório (art. 5 e art. 11, IV).\n\n' +
      '**Fundamentos legais:**\n' +
      '- Lei 14.133/2021, art. 11, IV (desenvolvimento nacional sustentável como objetivo)\n' +
      '- Decreto 7.746/2012 (critérios e práticas de sustentabilidade)\n' +
      '- IN SLTI/MP 01/2010 (critérios sustentáveis em compras federais)\n\n' +
      '**Critérios ambientais comuns em editais:**\n\n' +
      '1. **Eficiência energética:** Selo PROCEL/INMETRO classe A para equipamentos elétricos.\n' +
      '2. **Materiais reciclados:** Preferência por produtos com conteúdo reciclado.\n' +
      '3. **Gestão de residuos:** Plano de gerenciamento de residuos solidos (PGRS).\n' +
      '4. **Substâncias tóxicas:** Restrição a materiais com substâncias nocivas (RoHS).\n' +
      '5. **Embalagens:** Preferência por embalagens recicláveis ou biodegradáveis.\n' +
      '6. **Água:** Equipamentos com selo de economia de água (torneiras, descargas).\n' +
      '7. **Certificações ambientais:** ISO 14001, FSC (madeira), selo orgânico.\n\n' +
      '**Critérios sociais:**\n' +
      '- Inserção de trabalhadores com deficiência\n' +
      '- Aprendizagem e formação profissional\n' +
      '- Igualdade de gênero\n' +
      '- Respeito a legislação trabalhista e previdenciária\n\n' +
      '**Como a sustentabilidade afeta a proposta:**\n\n' +
      'O edital pode:\n' +
      '- Exigir certificações ambientais como requisito de habilitação\n' +
      '- Usar critério de julgamento "técnica e preço" com pontuação para sustentabilidade\n' +
      '- Aplicar margem de preferência para produtos sustentáveis\n' +
      '- Exigir logística reversa após o consumo\n' +
      '- Prever ciclo de vida do produto (TCO — Total Cost of Ownership)\n\n' +
      '**Setores mais impactados:**\n' +
      '- Construção civil (edificações verdes, PBQP-H)\n' +
      '- TI (descarte de eletrônicos, eficiência energética de data centers)\n' +
      '- Alimentação (orgânicos, rastreabilidade)\n' +
      '- Facilities (produtos biodegradáveis, gestão de residuos)\n' +
      '- Transporte (frotas eletricias/hibridas)\n\n' +
      '**Dica:** A sustentabilidade não é mais diferencial — e requisito. Invista em certificações ambientais e prepare sua empresa para comprovar práticas sustentáveis na cadeia produtiva.',
    legalBasis:
      'Lei 14.133/2021, arts. 5, 11 (IV); Decreto 7.746/2012',
    relatedTerms: ['licitacao', 'edital', 'termo-referencia'],
    relatedSectors: ['meio-ambiente', 'energia'],
    relatedArticles: [],
    metaDescription:
      'Entenda o que é licitação sustentável, quais critérios verdes são exigidos e como preparar sua empresa (Lei 14.133).',
  },
  {
    slug: 'portal-compras-estadual-diferenca-federal',
    title:
      'Qual a diferença entre portais de compras estaduais e federal?',
    category: 'tecnologia-sistemas',
    answer:
      'O ecossistema de compras públicas no Brasil é fragmentado entre plataformas federais, estaduais e municipais, cada uma com regras, cadastros e interfaces próprias. Entender essas diferenças é essencial para empresas que desejam atuar em múltiplas esferas.\n\n' +
      '**Portal federal — ComprasGov (comprasgov.br):**\n' +
      '- Ambito: Todos os órgãos do Executivo Federal\n' +
      '- Cadastro: SICAF (unificado)\n' +
      '- Catalogo: CATMAT (materiais) e CATSER (serviços)\n' +
      '- Certificado digital: Obrigatório (ICP-Brasil)\n' +
      '- Volume: ~200 mil processos/ano\n\n' +
      '**Principais portais estaduais:**\n\n' +
      '| Estado | Portal | Cadastro |\n' +
      '|--------|--------|----------|\n' +
      '| SP | BEC/SP (bec.sp.gov.br) | CAUFESP |\n' +
      '| RJ | SIGA (compras.rj.gov.br) | SIGA-RJ |\n' +
      '| MG | Portal de Compras MG | CAGEF |\n' +
      '| RS | CELIC (celic.rs.gov.br) | CFRS |\n' +
      '| PR | DECOM/PR | Cadastro SEAP |\n' +
      '| BA | Comprasnet.BA | SAEB |\n\n' +
      '**Plataformas privadas usadas por estados e municipios:**\n\n' +
      '| Plataforma | Cobertura |\n' +
      '|------------|----------|\n' +
      '| Portal de Compras Públicas | 2.500+ órgãos |\n' +
      '| BLL Compras | 4.000+ órgãos |\n' +
      '| Licitações-e (BB) | Federal + estadual + municipal |\n' +
      '| Compras BR | Municipal |\n' +
      '| Licitar Digital | Municipal |\n\n' +
      '**Diferenças práticas para fornecedores:**\n\n' +
      '1. **Cadastro:** Cada plataforma exige cadastro próprio. O SICAF federal não e automaticamente aceito em portais estaduais.\n' +
      '2. **Interface:** Cada sistema tem interface e fluxo diferentes — familiarize-se antes de participar.\n' +
      '3. **Regras:** Embora a Lei 14.133 seja nacional, regulamentações estaduais/municipais podem ter particularidades.\n' +
      '4. **Certificado digital:** Obrigatório em quase todos, mas alguns portais permitem acesso com login/senha para consulta.\n' +
      '5. **Publicação:** O PNCP está centralizando progressivamente, mas nem todos os municipios publicam la.\n\n' +
      '**Estratégia para fornecedores:**\n' +
      '- Cadastre-se nas plataformas dos estados onde deseja atuar\n' +
      '- Mantenha cadastros atualizados em múltiplos portais\n' +
      '- Use ferramentas de monitoramento (como SmartLic) que agregam todas as fontes\n' +
      '- Priorize estados com maior volume de compras no seu setor',
    legalBasis: 'Lei 14.133/2021, art. 175',
    relatedTerms: ['pncp', 'sicaf', 'pregao-eletronico'],
    relatedSectors: [],
    relatedArticles: [],
    metaDescription:
      'Compare portais de compras federal (ComprasGov), estaduais (BEC, SIGA, CELIC) e privados: cadastros, regras e como participar.',
  },
  {
    slug: 'inteligencia-artificial-licitacoes',
    title:
      'Como a inteligência artificial está transformando licitações?',
    category: 'tecnologia-sistemas',
    answer:
      'A inteligência artificial (IA) está revolucionando tanto o lado do comprador público quanto do fornecedor no mercado de licitações. Desde a análise automatizada de editais até a detecção de fraudes, a IA está criando novas possibilidades e vantagens competitivas.\n\n' +
      '**IA no lado do governo (comprador):**\n\n' +
      '1. **Pesquisa de preços automatizada:** Algoritmos analisam histórico de contratações no PNCP para estimar valores de referência com maior precisão.\n' +
      '2. **Detecção de fraudes:** Machine learning identifica padrões suspeitos como conluio entre licitantes, direcionamento de editais e sobrepreco.\n' +
      '3. **Chatbots para fornecedores:** Assistentes virtuais respondem dúvidas sobre editais e processos em tempo real.\n' +
      '4. **Classificação automática:** IA categoriza e rotula contratações, facilitando a busca e análise.\n' +
      '5. **Análise de risco de fornecedores:** Modelos preditivos avaliam a probabilidade de inadimplemento.\n\n' +
      '**IA no lado do fornecedor:**\n\n' +
      '1. **Monitoramento inteligente de editais:** Ferramentas como o SmartLic usam IA para classificar licitações por relevância setorial, filtrando o que realmente importa dentre milhares de publicações diárias.\n' +
      '2. **Análise de viabilidade:** Algoritmos avaliam automaticamente a viabilidade de participação com base em modalidade, prazo, valor e localização.\n' +
      '3. **Inteligência de preços:** IA analisa contratos históricos para sugerir faixas de preços competitivos por tipo de serviço e região.\n' +
      '4. **Geração de documentos:** LLMs (Large Language Models) auxiliam na elaboração de propostas técnicas, recursos e impugnações.\n' +
      '5. **Análise concorrencial:** IA mapeia concorrentes por setor, identificando seus históricos de participação e taxas de sucesso.\n\n' +
      '**Exemplos práticos de IA em licitações:**\n\n' +
      '- **TCU:** Utiliza o sistema ALICE (Análise de Licitações e Editais) para auditar contratações automaticamente.\n' +
      '- **CGU:** Emprega IA para detecção de sobrepreco em obras públicas.\n' +
      '- **SmartLic:** Classifica setorialmente editais usando GPT-4.1-nano para zero-match classification.\n' +
      '- **Painel de Preços:** Usa algoritmos para calcular preços de referência a partir de contratos históricos.\n\n' +
      '**O futuro próximo:**\n' +
      '- Editais gerados por IA (rascunhos automatizados)\n' +
      '- Negociação assistida por IA em dispensas e inexigibilidades\n' +
      '- Gestão de contratos preditiva (alertas de risco antes de problemas)\n' +
      '- Matching automático entre demandas públicas e capacidades de fornecedores\n\n' +
      '**Para fornecedores:** Adotar ferramentas de IA para monitoramento e análise de licitações não e mais vantagem competitiva — e sobrevivência. Quem analisa editais manualmente não consegue competir em escala com quem usa inteligência artificial.',
    legalBasis: 'Lei 14.133/2021; LGPD (Lei 13.709/2018)',
    relatedTerms: ['pncp', 'licitacao', 'edital'],
    relatedSectors: ['informatica'],
    relatedArticles: [],
    metaDescription:
      'Descubra como a IA está transformando licitações: monitoramento inteligente, análise de preços, detecção de fraudes e mais.',
  },
];

/* ------------------------------------------------------------------ */
/*  Helper functions                                                   */
/* ------------------------------------------------------------------ */

export function getQuestionBySlug(slug: string): Question | undefined {
  return QUESTIONS.find((q) => q.slug === slug);
}

export function getQuestionsByCategory(
  category: QuestionCategory,
): Question[] {
  return QUESTIONS.filter((q) => q.category === category);
}

export function getAllQuestionSlugs(): string[] {
  return QUESTIONS.map((q) => q.slug);
}

export function getQuestionsForGlossaryTerm(termSlug: string): Question[] {
  return QUESTIONS.filter((q) => q.relatedTerms.includes(termSlug));
}

export function getQuestionsForSector(sectorSlug: string): Question[] {
  return QUESTIONS.filter((q) => q.relatedSectors.includes(sectorSlug));
}
