import { Metadata } from 'next';
import Link from 'next/link';
import LandingNavbar from '../components/landing/LandingNavbar';
import Footer from '../components/Footer';

export const metadata: Metadata = {
  title: 'Glossário de Licitações: 50 Termos Essenciais | SmartLic',
  description:
    'Glossário completo com 50 termos de licitações públicas explicados de forma prática. Adjudicação, pregão eletrônico, PNCP, SRP e mais. Referência essencial para empresas B2G.',
  alternates: {
    canonical: 'https://smartlic.tech/glossário',
  },
  openGraph: {
    title: 'Glossário de Licitações: 50 Termos Essenciais | SmartLic',
    description:
      'Referência completa para profissionais de licitações. 50 termos explicados com definições claras e exemplos práticos.',
    type: 'website',
    url: 'https://smartlic.tech/glossário',
    siteName: 'SmartLic',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Glossário de Licitações: 50 Termos Essenciais | SmartLic',
    description:
      'Referência completa para profissionais de licitações. 50 termos explicados com definições claras e exemplos práticos.',
  },
};

/* ---------------------------------------------------------------------------
 * Data
 * --------------------------------------------------------------------------- */

interface GlossaryTerm {
  term: string;
  slug: string;
  definition: string;
  example: string;
  guideHref: string;
  guideLabel: string;
}

const TERMS: GlossaryTerm[] = [
  // A
  {
    term: 'Adjudicação',
    slug: 'adjudicação',
    definition:
      'Ato formal pelo qual a autoridade competente atribui o objeto da licitação ao licitante que apresentou a proposta mais vantajosa. Na Lei 14.133/2021, a adjudicação ocorre após a habilitação e o julgamento dos recursos, consolidando o direito do vencedor a assinatura do contrato.',
    example:
      'Após o pregão eletrônico para aquisição de 500 computadores, o pregoeiro adjudicou o objeto a empresa que ofertou R$ 2.800 por unidade, o menor preco valido após a fase de lances.',
    guideHref: '/blog',
    guideLabel: 'Como funciona o processo licitatório',
  },
  {
    term: 'Aditivo Contratual',
    slug: 'aditivo-contratual',
    definition:
      'Instrumento jurídico utilizado para alterar cláusulas de um contrato administrativo vigente, podendo modificar prazos, valores ou escopo. A Lei 14.133 limita acrescimos e supressoes a 25% do valor original (50% para reformas de edificios ou equipamentos).',
    example:
      'Um contrato de manutenção predial de R$ 1.200.000 recebeu aditivo de 20% (R$ 240.000) para incluir a reforma do sistema de ar-condicionado, dentro do limite legal.',
    guideHref: '/blog',
    guideLabel: 'Gestão de contratos públicos',
  },
  {
    term: 'Anulação',
    slug: 'anulação',
    definition:
      'Invalidacao de um processo licitatório ou contrato administrativo por vicio de legalidade identificado pela própria administracao ou pelo Judiciario. A anulação tem efeito retroativo (ex tunc), desfazendo todos os atos práticados desde a origem do vicio.',
    example:
      'O Tribunal de Contas determinou a anulação de um pregão porque o edital exigia certificacao ISO específica que restringia a competitividade sem justificativa técnica.',
    guideHref: '/blog',
    guideLabel: 'Recursos e impugnacoes em licitações',
  },
  {
    term: 'Ata de Registro de Precos',
    slug: 'ata-de-registro-de-precos',
    definition:
      'Documento vinculativo que formaliza precos, fornecedores, órgãos participantes e condições para aquisicoes futuras dentro do Sistema de Registro de Precos (SRP). A ata tem validade de até 1 ano (prorrogável por mais 1 ano na Lei 14.133) e não obriga o órgão a contratar.',
    example:
      'A Secretaria de Saude registrou precos de 30 tipos de medicamentos com 5 fornecedores. Durante 12 meses, qualquer hospital da rede pode emitir ordens de compra com os precos registrados sem nova licitação.',
    guideHref: '/blog',
    guideLabel: 'Sistema de Registro de Precos na prática',
  },
  {
    term: 'Atestado de Capacidade Técnica',
    slug: 'atestado-de-capacidade-técnica',
    definition:
      'Documento emitido por pessoa jurídica de direito público ou privado, comprovando que a empresa executou anteriormente servico ou obra similar ao objeto licitado. E o principal instrumento de qualificação técnica na fase de habilitação.',
    example:
      'Para participar de licitação de pavimentacao asfaltica de 15 km, a empresa apresentou atestado de prefeitura vizinha comprovando execução de 12 km de pavimentacao concluida em 2024.',
    guideHref: '/blog',
    guideLabel: 'Habilitação técnica em licitações',
  },
  // B
  {
    term: 'Balanco Patrimonial',
    slug: 'balanco-patrimonial',
    definition:
      'Demonstracao contabil que apresenta a posicao financeira da empresa em determinada data, evidenciando ativos, passivos e patrimonio liquido. E exigido na habilitação econômico-financeira para comprovar indices como liquidez geral e endividamento.',
    example:
      'O edital exigia Indice de Liquidez Geral >= 1,0. A empresa apresentou balanco patrimonial de 2025 com ativo circulante de R$ 3.200.000 e passivo circulante de R$ 2.100.000, resultando em ILG de 1,52 — aprovada na habilitação.',
    guideHref: '/blog',
    guideLabel: 'Habilitação econômico-financeira',
  },
  {
    term: 'BDI (Beneficios e Despesas Indiretas)',
    slug: 'bdi',
    definition:
      'Percentual aplicado sobre o custo direto de obras ou servicos que engloba despesas indiretas (administracao central, seguros, garantias), tributos e lucro. O BDI compoe o preco final da proposta e e objeto de analise detalhada pelos órgãos de controle.',
    example:
      'Em licitação de obra pública, a empresa calculou custo direto de R$ 800.000 e aplicou BDI de 28,5%, resultando em preco final de R$ 1.028.000. O TCU considerou o percentual compativel com a referência SINAPI.',
    guideHref: '/blog',
    guideLabel: 'Formacao de precos em obras públicas',
  },
  {
    term: 'BEC (Bolsa Eletrônica de Compras)',
    slug: 'bec',
    definition:
      'Sistema eletrônico de compras do governo do estado de Sao Paulo, utilizado para aquisição de bens e servicos por órgãos estaduais e municipais paulistas. Funciona como plataforma de pregão eletrônico e oferta de compra com catalogo de produtos padronizados.',
    example:
      'A Secretaria de Educacao de SP públicou oferta de compra na BEC para 10.000 cadeiras escolares. Fornecedores cadastrados no CAUFESP ofertaram precos diretamente na plataforma durante 3 dias.',
    guideHref: '/blog',
    guideLabel: 'Portais de compras estaduais',
  },
  // C
  {
    term: 'Cadastro de Fornecedores (SICAF)',
    slug: 'sicaf',
    definition:
      'O Sistema de Cadastramento Unificado de Fornecedores (SICAF) e o registro oficial do governo federal que centraliza dados cadastrais, habilitação jurídica, regularidade fiscal e qualificação econômica de empresas que fornecem ao poder público. O cadastro simplifica a participação em licitações federais.',
    example:
      'Antes de participar do pregão do Ministerio da Saude, a empresa atualizou seu SICAF com certidoes negativas federais, estaduais e municipais, balanco patrimonial e contrato social atualizado.',
    guideHref: '/blog',
    guideLabel: 'Como se cadastrar no SICAF',
  },
  {
    term: 'Certidao Negativa',
    slug: 'certidao-negativa',
    definition:
      'Documento oficial emitido por órgãos públicos que atesta a inexistencia de debitos ou pendencias do contribuinte. Na habilitação, sao exigidas certidoes negativas de debitos federais (CND/PGFN), estaduais, municipais, FGTS e trabalhistas (CNDT).',
    example:
      'A empresa foi inabilitada porque a Certidao Negativa de Debitos Trabalhistas (CNDT) estava vencida ha 3 dias na data da sessão do pregão — ressaltando a importancia de monitorar vencimentos.',
    guideHref: '/blog',
    guideLabel: 'Documentos de habilitação',
  },
  {
    term: 'Chamada Pública',
    slug: 'chamada-pública',
    definition:
      'Modalidade simplificada de seleção utilizada principalmente para aquisição de alimentos da agricultura familiar no ambito do Programa Nacional de Alimentacao Escolar (PNAE). A Lei 11.947/2009 determina que no mínimo 30% dos recursos do PNAE sejam destinados a compras via chamada pública.',
    example:
      'A prefeitura públicou chamada pública para aquisição de 5 toneladas de hortalicas organicas de agricultores familiares locais para merenda escolar, com preco baseado no mercado atacadista regional.',
    guideHref: '/blog',
    guideLabel: 'Vendendo para programas de alimentacao escolar',
  },
  {
    term: 'ComprasNet',
    slug: 'comprasnet',
    definition:
      'Portal eletrônico de compras do governo federal brasileiro, operado desde 2000, que concentra pregoes eletrônicos, cotacoes e licitações federais. Esta sendo gradualmente substituido pelo PNCP (Portal Nacional de Contratações Públicas) conforme a Lei 14.133/2021.',
    example:
      'Até 2025, o ComprasNet processou mais de R$ 50 bilhoes/ano em pregoes eletrônicos federais. Empresas que ja operavam no ComprasNet precisam migrar seus cadastros para o PNCP até o prazo de transicao.',
    guideHref: '/blog',
    guideLabel: 'Migracao ComprasNet para PNCP',
  },
  {
    term: 'Concorrência',
    slug: 'concorrência',
    definition:
      'Modalidade licitatória destinada a contratações de maior vulto, com ampla publicidade e prazos mais longos. Na Lei 14.133/2021, a concorrência e utilizada para obras, servicos de engenharia e compras acima dos limites do pregão, admitindo os critérios de julgamento menor preco, melhor técnica ou técnica e preco.',
    example:
      'O DNIT abriu concorrência para construcao de ponte com valor estimado de R$ 45 milhoes. O prazo de públicação do edital foi de 35 dias uteis, permitindo ampla participação de construtoras de todo o pais.',
    guideHref: '/blog',
    guideLabel: 'Modalidades de licitação',
  },
  {
    term: 'Consórcio',
    slug: 'consórcio',
    definition:
      'Agrupamento formal de duas ou mais empresas para participar conjuntamente de licitação, somando capacidades técnicas e financeiras. O consórcio não cria nova pessoa jurídica — cada consorciada mantem sua individualidade e responde solidariamente pelas obrigações.',
    example:
      'Tres empresas de TI formaram consórcio para disputar contrato de R$ 80 milhoes de modernizacao de datacenter: uma com expertise em infraestrutura, outra em seguranca e a terceira em cloud migration.',
    guideHref: '/blog',
    guideLabel: 'Consórcio em licitações',
  },
  {
    term: 'Contrato Administrativo',
    slug: 'contrato-administrativo',
    definition:
      'Acordo formal celebrado entre a administracao pública e o fornecedor vencedor da licitação, estabelecendo direitos, obrigações, prazos e condições de execução. Diferente dos contratos privados, o contrato administrativo possui cláusulas exorbitantes que conferem prerrogativas especiais ao poder público.',
    example:
      'Após adjudicação e homologação de pregão para servicos de limpeza, o hospital público assinou contrato administrativo de 12 meses com a empresa vencedora, no valor mensal de R$ 185.000, com cláusulas de fiscalização e penalidades.',
    guideHref: '/blog',
    guideLabel: 'Execução de contratos públicos',
  },
  // D
  {
    term: 'Diálogo Competitivo',
    slug: 'diálogo-competitivo',
    definition:
      'Modalidade licitatória introduzida pela Lei 14.133/2021 para contratações de objetos inovadores ou técnicamente complexos, onde a administracao dialoga com licitantes pre-selecionados para desenvolver solucoes antes da fase de propostas. E indicado quando o órgão não consegue definir específicacoes técnicas de forma precisa.',
    example:
      'O Ministerio da Ciencia abriu diálogo competitivo para sistema de inteligencia artificial de monitoramento ambiental. Tres empresas foram selecionadas para 60 dias de diálogos técnicos antes de submeterem propostas finais.',
    guideHref: '/blog',
    guideLabel: 'Novas modalidades da Lei 14.133',
  },
  {
    term: 'Dispensa de Licitação',
    slug: 'dispensa-de-licitação',
    definition:
      'Hipotese de contratação direta prevista em lei, onde a licitação e dispensavel por razoes de valor (até R$ 59.906,02 para compras em 2026), emergencia, situação específica ou outros casos do art. 75 da Lei 14.133. Difere da inexigibilidade porque a competicao seria possivel, mas a lei autoriza sua dispensa.',
    example:
      'A universidade contratou diretamente servico de conserto de ar-condicionado por R$ 42.000, enquadrado na dispensa por valor (limite de R$ 59.906,02 para servicos em 2026), com pesquisa de precos de 3 fornecedores.',
    guideHref: '/blog',
    guideLabel: 'Contratação direta: dispensa e inexigibilidade',
  },
  {
    term: 'Dotação Orçamentária',
    slug: 'dotação-orçamentária',
    definition:
      'Previsão de recursos financeiros consignada no orçamento público (LOA) destinada a cobrir determinada despesa. Nenhuma licitação pode ser lancada sem dotação orçamentária que garanta os recursos necessarios para pagamento da contratação.',
    example:
      'O edital de pregão para mobiliario escolar indicou a dotação orçamentária 12.361.0001.2035 — Programa de Equipamentos Escolares, com credito disponivel de R$ 2.300.000 no exercicio de 2026.',
    guideHref: '/blog',
    guideLabel: 'Orçamento público e licitações',
  },
  // E
  {
    term: 'Edital',
    slug: 'edital',
    definition:
      'Instrumento convocatorio que estabelece todas as regras, exigencias, prazos e critérios de uma licitação. E a "lei interna" do processo licitatório — tudo o que não esta no edital não pode ser exigido, e tudo o que esta nele vincula tanto a administracao quanto os licitantes.',
    example:
      'O edital do Pregão Eletrônico 045/2026 da Prefeitura de Curitiba específicava: objeto (500 notebooks), prazo de entrega (60 dias), critério de julgamento (menor preco por lote), habilitação exigida e modelo de proposta.',
    guideHref: '/blog',
    guideLabel: 'Como analisar editais de licitação',
  },
  {
    term: 'Estudo Técnico Preliminar (ETP)',
    slug: 'estudo-técnico-preliminar',
    definition:
      'Documento obrigatório na fase preparatoria da licitação (Lei 14.133, art. 18) que demonstra a necessidade da contratação, analisa solucoes disponiveis no mercado e define requisitos técnicos. O ETP embasa o Termo de Referência e e públicado no PNCP.',
    example:
      'Antes de licitar sistema de gestão hospitalar, o ETP comparou 4 solucoes de mercado (SaaS vs on-premise), analisou custos em 5 anos e concluiu que SaaS seria 35% mais econômico, justificando a opção técnica do Termo de Referência.',
    guideHref: '/blog',
    guideLabel: 'Fase preparatoria na Lei 14.133',
  },
  // F
  {
    term: 'Fiscalização',
    slug: 'fiscalização',
    definition:
      'Atividade exercida por servidor ou comissao designada pelo órgão contratante para acompanhar a execução do contrato, verificar qualidade, prazos e conformidade com as cláusulas pactuadas. A Lei 14.133 torna obrigatória a designacao de fiscal para todo contrato.',
    example:
      'O fiscal do contrato de servicos de TI identificou que a equipe alocada estava com 2 profissionais a menos que o exigido. Notificou a empresa, que regularizou em 5 dias, evitando aplicação de multa contratual de 2%.',
    guideHref: '/blog',
    guideLabel: 'Fiscalização de contratos públicos',
  },
  // G
  {
    term: 'Garantia Contratual',
    slug: 'garantia-contratual',
    definition:
      'Garantia exigida do contratado para assegurar a execução do contrato, podendo ser caucao em dinheiro, seguro-garantia ou fianca bancaria. A Lei 14.133 permite exigir até 5% do valor do contrato (até 10% para obras de grande vulto).',
    example:
      'Para contrato de R$ 10 milhoes em obras de saneamento, a construtora apresentou seguro-garantia de R$ 500.000 (5%) emitido por seguradora autorizada pela SUSEP, com vigencia até 90 dias após o recebimento definitivo.',
    guideHref: '/blog',
    guideLabel: 'Garantias em contratos públicos',
  },
  {
    term: 'Garantia de Proposta',
    slug: 'garantia-de-proposta',
    definition:
      'Garantia exigida na fase de licitação para assegurar a seriedade da proposta apresentada. A Lei 14.133 permite exigir garantia de até 1% do valor estimado da contratação, devolvida após a adjudicação.',
    example:
      'Em concorrência para construcao de viaduto estimada em R$ 25 milhoes, o edital exigiu garantia de proposta de R$ 250.000 (1%). A empresa apresentou fianca bancaria, que foi devolvida 15 dias após a homologação.',
    guideHref: '/blog',
    guideLabel: 'Garantias em licitações',
  },
  // H
  {
    term: 'Habilitação',
    slug: 'habilitação',
    definition:
      'Fase do processo licitatório em que se verifica a documentacao jurídica, fiscal, trabalhista, técnica e econômico-financeira dos licitantes. Na Lei 14.133, a habilitação ocorre após o julgamento das propostas (inversão de fases), exceto quando o edital determina o contrario.',
    example:
      'Dos 12 participantes do pregão, 3 foram inabilitados: um por CNDT vencida, outro por falta de atestado técnico compativel e o terceiro por indice de liquidez abaixo do mínimo exigido de 1,0.',
    guideHref: '/blog',
    guideLabel: 'Habilitação em licitações',
  },
  {
    term: 'Homologação',
    slug: 'homologação',
    definition:
      'Ato da autoridade superior que ratifica todo o procedimento licitatório após verificar sua legalidade e conveniencia. A homologação e o último ato antes da convocação para assinatura do contrato e pode ser precedida de parecer jurídico.',
    example:
      'O Secretario de Administracao homologou o pregão eletrônico 30 dias após a adjudicação, confirmando que todas as etapas foram conduzidas conforme a lei e autorizando a assinatura do contrato com o vencedor.',
    guideHref: '/blog',
    guideLabel: 'Etapas do processo licitatório',
  },
  // I
  {
    term: 'Impugnação',
    slug: 'impugnação',
    definition:
      'Instrumento jurídico pelo qual qualquer cidadao ou licitante questiona termos do edital antes da realizacao da sessão pública. A impugnação deve ser apresentada em até 3 dias uteis antes da abertura (cidadao) ou até 3 dias uteis (licitante) na Lei 14.133.',
    example:
      'Uma empresa de software impugnou edital que exigia "sistema desenvolvido em Java" sem justificativa técnica, argumentando que a específicacao de linguagem restringia a concorrência. A comissao acatou e alterou para "sistema web multiplataforma".',
    guideHref: '/blog',
    guideLabel: 'Impugnação de editais',
  },
  {
    term: 'Inexigibilidade',
    slug: 'inexigibilidade',
    definition:
      'Contratação direta quando ha inviabilidade de competicao, ou seja, quando o objeto so pode ser fornecido por um único prestador ou quando a natureza do servico torna impossivel a comparação objetiva. Difere da dispensa, onde a competicao seria possivel mas e dispensada por lei.',
    example:
      'A universidade contratou por inexigibilidade o único representante autorizado no Brasil de equipamento de ressonancia magnetica Siemens MAGNETOM para manutenção corretiva, pois a fabricante não credencia terceiros.',
    guideHref: '/blog',
    guideLabel: 'Contratação direta: dispensa e inexigibilidade',
  },
  // L
  {
    term: 'Leilão',
    slug: 'leilão',
    definition:
      'Modalidade licitatória utilizada para alienação (venda) de bens moveis e imoveis da administracao pública ao maior lance. Na Lei 14.133, o leilão pode ser presencial ou eletrônico e exige avaliação prévia dos bens.',
    example:
      'O Exercito realizou leilão eletrônico de 50 veiculos descaracterizados com lance mínimo de R$ 8.000 cada. Os veiculos foram arrematados com agio medio de 45% sobre a avaliação.',
    guideHref: '/blog',
    guideLabel: 'Leilão de bens públicos',
  },
  {
    term: 'Licitação Deserta',
    slug: 'licitação-deserta',
    definition:
      'Situação em que nenhum interessado comparece ao processo licitatório. Quando a licitação e deserta, a administracao pode repetir o processo ou realizar contratação direta (dispensa) desde que mantenha as mesmas condições do edital original.',
    example:
      'O pregão para fornecimento de refeicoes em municipio do interior teve zero propostas. A prefeitura reabriu o certame com prazo estendido e, novamente deserto, contratou diretamente por dispensa (art. 75, III da Lei 14.133).',
    guideHref: '/blog',
    guideLabel: 'Licitação deserta e fracassada',
  },
  {
    term: 'Licitação Fracassada',
    slug: 'licitação-fracassada',
    definition:
      'Situação em que todos os licitantes sao inabilitados ou todas as propostas sao desclassificadas. Diferentemente da deserta (ninguem aparece), na fracassada houve participantes, mas nenhum atendeu aos requisitos. A Lei 14.133 permite fixar prazo para adequação antes de repetir.',
    example:
      'Na concorrência para construcao de escola, as 5 propostas foram desclassificadas por precos acima do orçamento estimado. A comissao fixou prazo de 8 dias para readequação, conforme art. 75, III, da Lei 14.133.',
    guideHref: '/blog',
    guideLabel: 'Licitação deserta e fracassada',
  },
  // M
  {
    term: 'Mapa de Riscos',
    slug: 'mapa-de-riscos',
    definition:
      'Documento elaborado na fase preparatoria da licitação que identifica os principais riscos do processo de contratação, suas probabilidades e impactos. A Lei 14.133 tornou obrigatória sua elaboração como parte do planejamento da contratação.',
    example:
      'O mapa de riscos de contratação de datacenter identificou 12 riscos, sendo o mais critico "indisponibilidade superior a 4h/mes" com probabilidade alta e impacto severo, levando a inclusão de SLA com multas progressivas no contrato.',
    guideHref: '/blog',
    guideLabel: 'Gestão de riscos em contratações',
  },
  {
    term: 'Matriz de Riscos',
    slug: 'matriz-de-riscos',
    definition:
      'Cláusula contratual que distribui de forma objetiva as responsabilidades sobre eventos supervenientes entre contratante e contratado. Diferentemente do mapa de riscos (fase preparatoria), a matriz de riscos faz parte do contrato e vincula ambas as partes.',
    example:
      'Na matriz de riscos do contrato de obra rodoviaria, o risco de variacao do preco do asfalto acima de 10% ficou com a administracao (reequilíbrio automatico), enquanto o risco de atraso por falta de mao-de-obra ficou com a construtora.',
    guideHref: '/blog',
    guideLabel: 'Gestão de riscos em contratações',
  },
  {
    term: 'ME/EPP',
    slug: 'me-epp',
    definition:
      'Microempresa (receita bruta anual até R$ 360.000) e Empresa de Pequeno Porte (receita até R$ 4.800.000) recebem tratamento diferenciado em licitações: direito de preferência quando a proposta for até 5% superior (pregão) ou 10% (demais modalidades) a melhor oferta, alem de prazo extra para regularização fiscal.',
    example:
      'No pregão para material de escritorio, a ME ofertou R$ 52.000 contra R$ 50.000 da empresa de grande porte. Como a diferenca foi inferior a 5%, a ME foi convocada para cobrir o lance e ofertou R$ 49.800, vencendo o certame.',
    guideHref: '/blog',
    guideLabel: 'Vantagens de ME/EPP em licitações',
  },
  {
    term: 'Medição',
    slug: 'medição',
    definition:
      'Procedimento periódico (geralmente mensal) de verificação e quantificacao dos servicos ou obras efetivamente executados pelo contratado, servindo como base para emissão da nota fiscal e pagamento. A medição e atestada pelo fiscal do contrato.',
    example:
      'Na 3a medição mensal do contrato de limpeza hospitalar, o fiscal verificou que 95% da area foi atendida (2 alas em reforma ficaram sem servico) e autorizou pagamento proporcional de R$ 142.500 sobre os R$ 150.000 mensais.',
    guideHref: '/blog',
    guideLabel: 'Execução de contratos de servicos',
  },
  // N
  {
    term: 'Nota de Empenho',
    slug: 'nota-de-empenho',
    definition:
      'Documento emitido pelo órgão público que reserva dotação orçamentária para cobrir despesa específica. O empenho e a primeira fase da execução da despesa pública e precede a liquidacao e o pagamento. Em compras de pequeno valor, pode substituir o contrato formal.',
    example:
      'Após homologação do pregão de material de limpeza (R$ 38.000), o setor financeiro emitiu Nota de Empenho vinculada a dotação 3.3.90.30 — Material de Consumo, autorizando o fornecedor a iniciar a entrega.',
    guideHref: '/blog',
    guideLabel: 'Ciclo da despesa pública',
  },
  // O
  {
    term: 'Ordem de Servico',
    slug: 'ordem-de-servico',
    definition:
      'Documento emitido pelo órgão contratante que autoriza formalmente o inicio da execução do contrato ou de uma etapa específica. Define data de inicio, escopo da demanda e prazo de conclusão, sendo obrigatória em contratos de servicos continuados.',
    example:
      'A Ordem de Servico n. 001/2026 autorizou a empresa de TI a iniciar o desenvolvimento do modulo de RH do sistema, com prazo de 90 dias e equipe mínima de 5 profissionais, conforme cronograma do contrato.',
    guideHref: '/blog',
    guideLabel: 'Gestão de contratos de servicos',
  },
  // P
  {
    term: 'Penalidade/Sanção',
    slug: 'penalidade-sanção',
    definition:
      'Punição aplicada ao fornecedor por descumprimento contratual ou conduta irregular em licitação. A Lei 14.133 preve 4 tipos: advertencia, multa (até 30% do contrato), impedimento de licitar (até 3 anos) e declaração de inidoneidade (3 a 6 anos). Sanções sao registradas no PNCP.',
    example:
      'Após 3 notificacoes por atraso na entrega de medicamentos, o hospital aplicou multa de 10% do valor mensal (R$ 45.000) e impedimento de licitar por 2 anos, com registro no SICAF e PNCP.',
    guideHref: '/blog',
    guideLabel: 'Sanções em contratos públicos',
  },
  {
    term: 'Plano de Contratações Anual (PCA)',
    slug: 'plano-de-contratações-anual',
    definition:
      'Instrumento de planejamento obrigatório (Lei 14.133, art. 12, VII) em que cada órgão lista todas as contratações previstas para o exercicio seguinte. O PCA e públicado no PNCP e permite que fornecedores se preparem com antecedencia para as licitações do ano.',
    example:
      'O PCA 2026 do Ministerio da Educacao listou 847 itens de contratação, totalizando R$ 2,3 bilhoes. Empresas de TI identificaram 23 contratações relevantes e iniciaram preparacao de atestados e certidoes 6 meses antes dos pregoes.',
    guideHref: '/blog',
    guideLabel: 'Planejamento de contratações',
  },
  {
    term: 'PNCP (Portal Nacional de Contratações Públicas)',
    slug: 'pncp',
    definition:
      'Portal eletrônico oficial e obrigatório, criado pela Lei 14.133/2021, que centraliza a divulgacao de todas as licitações, contratações diretas, atas de registro de precos e contratos dos tres niveis de governo (federal, estadual e municipal). E a principal fonte de dados para monitoramento de oportunidades.',
    example:
      'O SmartLic monitora diariamente o PNCP para identificar novas licitações públicadas em 27 UFs, classificando automaticamente por setor e avaliando viabilidade. Em media, sao públicadas 2.000+ contratações/dia no portal.',
    guideHref: '/blog',
    guideLabel: 'Como usar o PNCP',
  },
  {
    term: 'Preco de Referência',
    slug: 'preco-de-referência',
    definition:
      'Valor estimado pela administracao como parametro do preco justo para a contratação. E obtido por pesquisa de mercado (mínimo 3 cotacoes), consulta a bancos de precos (Painel de Precos, SINAPI, SICRO) ou contratações anteriores similares. O preco de referência define o teto aceitavel.',
    example:
      'Para licitação de notebooks, o órgão pesquisou: Painel de Precos (R$ 4.200), 3 cotacoes de mercado (media R$ 4.350) e ata de registro vigente (R$ 4.100). O preco de referência foi fixado em R$ 4.217 (media ponderada).',
    guideHref: '/blog',
    guideLabel: 'Pesquisa de precos em licitações',
  },
  {
    term: 'Pregão Eletrônico',
    slug: 'pregão-eletrônico',
    definition:
      'Modalidade licitatória realizada integralmente em plataforma digital, destinada a aquisição de bens e servicos comuns pelo critério de menor preco ou maior desconto. E a modalidade mais utilizada no Brasil, respondendo por mais de 80% das licitações federais. A fase de lances permite redução competitiva dos precos em tempo real.',
    example:
      'No pregão eletrônico para 1.000 licencas de antivirus, 8 empresas participaram da fase de lances que durou 15 minutos. O preco caiu de R$ 89/licenca para R$ 52/licenca — economia de 42% para a administracao.',
    guideHref: '/blog',
    guideLabel: 'Guia completo do pregão eletrônico',
  },
  {
    term: 'Proposta Comercial',
    slug: 'proposta-comercial',
    definition:
      'Documento formal apresentado pelo licitante contendo precos, condições de pagamento, prazo de entrega e validade da oferta. Deve seguir rigorosamente o modelo exigido no edital. A proposta vincula o licitante, que não pode alterala após a abertura, exceto em negociação com o pregoeiro.',
    example:
      'A proposta comercial para fornecimento de 200 impressoras incluiu: preco unitario R$ 1.890, prazo de entrega 30 dias, garantia 36 meses on-site, validade da proposta 90 dias, conforme modelo do Anexo II do edital.',
    guideHref: '/blog',
    guideLabel: 'Como elaborar propostas vencedoras',
  },
  {
    term: 'Proposta Técnica',
    slug: 'proposta-técnica',
    definition:
      'Documento que descreve a solucao técnica, metodologia, equipe e plano de trabalho ofertados pelo licitante em licitações do tipo "técnica e preco" ou "melhor técnica". E avaliada por comissao técnica segundo critérios objetivos definidos no edital.',
    example:
      'Na licitação de consultoria ambiental (técnica e preco, peso 60/40), a proposta técnica incluiu: metodologia de diagnostico em 3 fases, equipe de 8 especialistas com curriculos, cronograma detalhado de 180 dias e 3 estudos de caso similares.',
    guideHref: '/blog',
    guideLabel: 'Licitações de técnica e preco',
  },
  // R
  {
    term: 'Recebimento Definitivo',
    slug: 'recebimento-definitivo',
    definition:
      'Ato formal que confirma a aceitacao final do objeto contratado após verificação completa de qualidade, quantidade e conformidade com as específicacoes. Ocorre após o recebimento provisorio e autoriza o pagamento integral remanescente. E realizado por comissao ou servidor designado.',
    example:
      'Após 15 dias de testes do sistema de gestão implantado, a comissao de recebimento emitiu o Termo de Recebimento Definitivo, atestando que os 47 requisitos funcionais do Termo de Referência foram atendidos integralmente.',
    guideHref: '/blog',
    guideLabel: 'Recebimento de objetos contratuais',
  },
  {
    term: 'Recebimento Provisorio',
    slug: 'recebimento-provisorio',
    definition:
      'Aceite inicial do objeto contratado, realizado pelo fiscal para fins de posterior verificação detalhada de conformidade. Não constitui aceite definitivo — e uma etapa intermediaria que permite a administracao conferir qualidade e quantidade antes do recebimento definitivo.',
    example:
      'O fiscal do contrato emitiu recebimento provisorio das 500 cadeiras escolares no ato da entrega, verificando apenas quantidade e integridade das embalagens. A conferencia detalhada (material, dimensoes, acabamento) foi realizada nos 15 dias seguintes.',
    guideHref: '/blog',
    guideLabel: 'Recebimento de objetos contratuais',
  },
  {
    term: 'Recurso',
    slug: 'recurso',
    definition:
      'Instrumento processual pelo qual o licitante pede revisao de decisao tomada durante a licitação (habilitação, julgamento, adjudicação). Na Lei 14.133, o prazo para recurso e de 3 dias uteis após a públicação do ato, com efeito suspensivo automatico.',
    example:
      'A empresa classificada em 2o lugar interpôs recurso contra a habilitação da vencedora, demonstrando que o atestado de capacidade técnica apresentado não atingia 50% do quantitativo exigido. O recurso foi provido e a recorrente foi declarada vencedora.',
    guideHref: '/blog',
    guideLabel: 'Recursos em licitações',
  },
  {
    term: 'Reequilíbrio Econômico-Financeiro',
    slug: 'reequilíbrio-econômico-financeiro',
    definition:
      'Mecanismo de restauracao das condições econômicas originais do contrato quando eventos imprevisiveis e extraordinarios alteram significativamente os custos. Diferencia-se do reajuste (previsivel, por indice) por exigir comprovação de fato superveniente e impacto financeiro concreto.',
    example:
      'Após aumento de 40% no preco do aco em 3 meses devido a crise logistica global, a construtora solicitou reequilíbrio do contrato de obra, apresentando notas fiscais comparativas que demonstravam impacto de R$ 1,2 milhao sobre o custo original.',
    guideHref: '/blog',
    guideLabel: 'Reequilíbrio e reajuste contratual',
  },
  {
    term: 'Reajuste',
    slug: 'reajuste',
    definition:
      'Atualização periódica do valor contratual com base em indice de precos préviamente definido no contrato (IPCA, IGPM, INPC ou indice setorial). O reajuste e aplicado anualmente, a partir da data da proposta, e não depende de comprovação de desequilibrio — e automatico conforme cláusula contratual.',
    example:
      'O contrato de servicos de vigilancia prévia reajuste anual pelo IPCA. Após 12 meses, o indice acumulado foi de 4,87%, e o valor mensal foi reajustado de R$ 120.000 para R$ 125.844 automaticamente.',
    guideHref: '/blog',
    guideLabel: 'Reequilíbrio e reajuste contratual',
  },
  {
    term: 'Revogação',
    slug: 'revogação',
    definition:
      'Anulação da licitação por razoes de interesse público superveniente, devidamente justificadas pela autoridade competente. Diferente da anulação (por ilegalidade), a revogação decorre de conveniencia administrativa e tem efeito a partir da decisao (ex nunc).',
    example:
      'A prefeitura revogou a licitação para construcao de quadra esportiva porque o terreno previsto foi desaprópriado para passagem de via expressa estadual, inviabilizando o projeto original.',
    guideHref: '/blog',
    guideLabel: 'Anulação e revogação de licitações',
  },
  // S
  {
    term: 'Sistema de Registro de Precos (SRP)',
    slug: 'sistema-de-registro-de-precos',
    definition:
      'Conjunto de procedimentos para registro formal de precos com fornecedores, permitindo contratações futuras nas quantidades e prazos necessarios, sem obrigatoriedade de compra. E formalizado por Ata de Registro de Precos com validade de até 1 ano. Ideal para compras frequentes com quantidades incertas.',
    example:
      'O governo estadual registrou precos de 200 itens de informatica via SRP. Durante 12 meses, 45 órgãos participantes emitiram 312 ordens de compra totalizando R$ 18 milhoes — sem precisar realizar nova licitação para cada aquisição.',
    guideHref: '/blog',
    guideLabel: 'SRP: vantagens e como participar',
  },
];

/* ---------------------------------------------------------------------------
 * Helpers
 * --------------------------------------------------------------------------- */

/** Extract unique first letters (uppercase) from sorted terms. */
function getAlphabetLetters(terms: GlossaryTerm[]): string[] {
  const set = new Set<string>();
  for (const t of terms) {
    set.add(t.term.charAt(0).toUpperCase());
  }
  return Array.from(set).sort();
}

/** Group terms by their first letter. */
function groupByLetter(terms: GlossaryTerm[]): Record<string, GlossaryTerm[]> {
  const groups: Record<string, GlossaryTerm[]> = {};
  for (const t of terms) {
    const letter = t.term.charAt(0).toUpperCase();
    if (!groups[letter]) groups[letter] = [];
    groups[letter].push(t);
  }
  return groups;
}

/* ---------------------------------------------------------------------------
 * Component
 * --------------------------------------------------------------------------- */

export default function GlossárioPage() {
  const letters = getAlphabetLetters(TERMS);
  const grouped = groupByLetter(TERMS);

  /* JSON-LD: BreadcrumbList */
  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: 'https://smartlic.tech',
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Glossário',
        item: 'https://smartlic.tech/glossário',
      },
    ],
  };

  /* JSON-LD: DefinedTerm array */
  const definedTermsLd = TERMS.map((t) => ({
    '@type': 'DefinedTerm',
    name: t.term,
    description: t.definition,
    inDefinedTermSet: {
      '@type': 'DefinedTermSet',
      name: 'Glossário de Licitações SmartLic',
    },
  }));

  const definedTermSetLd = {
    '@context': 'https://schema.org',
    '@type': 'DefinedTermSet',
    name: 'Glossário de Licitações SmartLic',
    description:
      'Glossário com 50 termos essenciais sobre licitações públicas no Brasil.',
    url: 'https://smartlic.tech/glossário',
    hasDefinedTerm: definedTermsLd,
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(definedTermSetLd) }}
      />

      <main className="flex-1">
        {/* ── Hero ── */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 lg:py-20 text-center">
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              Glossário de Licitações
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl mx-auto leading-relaxed">
              50 termos essenciais explicados de forma prática para quem participa de licitações públicas no Brasil
            </p>
          </div>
        </div>

        {/* ── Alphabetical Navigation ── */}
        <div className="sticky top-0 z-20 bg-canvas/95 backdrop-blur-sm border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav
              aria-label="Navegacao alfabetica"
              className="flex flex-wrap gap-1 py-3 justify-center"
            >
              {letters.map((letter) => (
                <a
                  key={letter}
                  href={`#letra-${letter}`}
                  className="inline-flex items-center justify-center w-9 h-9 rounded-md text-sm font-semibold text-ink-secondary hover:text-brand-blue hover:bg-surface-1 transition-colors"
                >
                  {letter}
                </a>
              ))}
            </nav>
          </div>
        </div>

        {/* ── Terms ── */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {letters.map((letter) => (
            <section key={letter} id={`letra-${letter}`} className="mb-12">
              <h2 className="text-2xl font-bold text-brand-blue border-b-2 border-brand-blue/20 pb-2 mb-6">
                {letter}
              </h2>

              <div className="space-y-8">
                {grouped[letter].map((t) => (
                  <article
                    key={t.slug}
                    id={t.slug}
                    className="scroll-mt-24"
                  >
                    <h3 className="text-lg font-bold text-ink mb-1">
                      {t.term}
                    </h3>
                    <p className="text-ink-secondary leading-relaxed mb-3">
                      {t.definition}
                    </p>

                    {/* Example box */}
                    <div className="text-sm bg-surface-1 border border-[var(--border)] rounded-lg p-3 mb-2">
                      <span className="font-semibold text-ink">Exemplo: </span>
                      <span className="text-ink-secondary">{t.example}</span>
                    </div>

                    <Link
                      href={t.guideHref}
                      className="text-brand-blue hover:underline text-sm"
                    >
                      {t.guideLabel} &rarr;
                    </Link>
                  </article>
                ))}
              </div>
            </section>
          ))}

          {/* ── CTA ── */}
          <section className="mt-16 mb-8 rounded-2xl bg-brand-blue p-8 sm:p-10 text-center">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
              Encontre licitações do seu setor automaticamente
            </h2>
            <p className="text-white/85 max-w-xl mx-auto mb-6">
              O SmartLic monitora PNCP, PCP e ComprasGov diariamente, classifica por setor com IA e avalia viabilidade para voce focar nas melhores oportunidades.
            </p>
            <Link
              href="/signup?source=glossário-cta"
              className="inline-flex items-center gap-2 bg-white text-brand-blue px-8 py-4 rounded-lg font-semibold hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
            >
              Testar gratis por 14 dias
            </Link>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
