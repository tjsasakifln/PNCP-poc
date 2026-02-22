import Script from 'next/script';

/**
 * GTM-COPY-006 AC6: FAQPage structured data for /ajuda
 *
 * Renders JSON-LD FAQPage schema with all FAQ items.
 * Server component — rendered from ajuda/layout.tsx.
 */

const FAQ_ITEMS = [
  {
    q: "Como faço uma busca por oportunidades de licitação?",
    a: "Acesse a página de Busca, selecione os estados (UFs) de interesse, defina o período desejado e clique em Buscar. O sistema consultará automaticamente as fontes oficiais e retornará as oportunidades filtradas para o seu setor.",
  },
  {
    q: "Posso buscar em mais de um estado ao mesmo tempo?",
    a: "Sim. Na página de busca, você pode selecionar múltiplos estados simultaneamente. O sistema buscará oportunidades em todos os estados selecionados de forma paralela.",
  },
  {
    q: "O que significam os filtros de setor?",
    a: "Os setores representam as áreas de atuação (ex.: TI, Engenharia, Saúde). Ao selecionar um setor, o sistema aplica filtros inteligentes de palavras-chave para encontrar licitações relevantes àquela área específica.",
  },
  {
    q: "Quanto tempo leva uma busca?",
    a: "A duração varia conforme o número de estados selecionados e o período de busca. Normalmente, uma busca leva entre 10 segundos e 2 minutos. Você acompanha o progresso em tempo real na tela.",
  },
  {
    q: "Como faço download dos resultados em Excel?",
    a: "Após a busca ser concluída, clique no botão Download Excel que aparece junto aos resultados. O arquivo será gerado e baixado automaticamente com todas as oportunidades encontradas.",
  },
  {
    q: "Como funciona a avaliação por IA?",
    a: "Após cada busca, nosso sistema avalia automaticamente cada oportunidade usando IA, indicando adequação ao seu perfil, critérios de elegibilidade, competitividade e pontos de atenção.",
  },
  {
    q: "Qual a diferença entre o período de avaliação e o SmartLic Pro?",
    a: "Durante os 7 dias de avaliação, você usa o produto completo. A única diferença é o limite de 3 análises. O SmartLic Pro oferece até 1.000 análises por mês e histórico de 5 anos.",
  },
  {
    q: "Posso testar antes de assinar?",
    a: "Sim! Ao criar sua conta, você experimenta o produto completo por 7 dias com 3 análises incluídas. Não é necessário informar dados de pagamento.",
  },
  {
    q: "Posso cancelar a qualquer momento?",
    a: "Sim. Sem contrato de fidelidade. Cancele quando quiser e mantenha o acesso até o fim do período já pago.",
  },
  {
    q: "Existe desconto para pagamento anual?",
    a: "Sim! O acesso anual tem economia de 20% em relação ao mensal — R$ 1.599/mês em vez de R$ 1.999/mês.",
  },
  {
    q: "O pagamento é seguro?",
    a: "Sim. Todos os pagamentos são processados pelo Stripe, plataforma certificada PCI-DSS nível 1. Nós nunca armazenamos os dados do seu cartão.",
  },
  {
    q: "De onde vêm os dados das licitações?",
    a: "Todos os dados são obtidos diretamente de portais oficiais de contratações públicas do Brasil, que consolidam licitações federais, estaduais e municipais — incluindo autarquias, fundações e empresas públicas. Os dados são públicos e abertos.",
  },
  {
    q: "Com que frequência os dados são atualizados?",
    a: "Os dados são consultados em tempo real a cada busca. Quando você realiza uma busca, o sistema consulta as fontes oficiais naquele momento.",
  },
  {
    q: "O SmartLic cobre todas as licitações do Brasil?",
    a: "O SmartLic consulta todas as licitações publicadas nas fontes oficiais de contratações públicas. Órgãos municipais, estaduais e federais que publicam nos portais oficiais são cobertos.",
  },
  {
    q: "Como entro em contato com o suporte?",
    a: "Você pode entrar em contato pelo e-mail suporte@smartlic.tech ou através da página de Mensagens dentro da plataforma. Respondemos em até 24 horas úteis.",
  },
];

export function FaqStructuredData() {
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQ_ITEMS.map((item) => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.a,
      },
    })),
  };

  return (
    <Script
      id="faq-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(faqSchema),
      }}
    />
  );
}
