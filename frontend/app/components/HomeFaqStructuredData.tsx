import Script from 'next/script';

const HOME_FAQ_ITEMS = [
  {
    q: "O que é o SmartLic?",
    a: "Plataforma de inteligência em licitações públicas. Cruza seu perfil de empresa com cada edital publicado em portais oficiais e recomenda apenas as oportunidades com chance real de retorno — em vez de você gastar tempo abrindo editais um por um.",
  },
  {
    q: "Como funciona o trial de 14 dias?",
    a: "Ao criar sua conta, você experimenta o produto completo por 14 dias gratuitamente, sem limites e sem informar dados de pagamento. Excel, pipeline, classificação por IA e histórico todos liberados.",
  },
  {
    q: "Quanto custa o SmartLic após o trial?",
    a: "SmartLic Pro a partir de R$ 297/mês no plano anual (economia de 25%). Mensal R$ 397, semestral R$ 357. Sem contrato de fidelidade — cancele quando quiser.",
  },
  {
    q: "De onde vêm os dados das licitações?",
    a: "Todos os dados vêm diretamente dos portais oficiais de contratações públicas do Brasil, consolidando licitações federais, estaduais e municipais — incluindo autarquias, fundações e empresas públicas. Cobertura nas 27 unidades federativas.",
  },
  {
    q: "Posso cancelar a qualquer momento?",
    a: "Sim. Sem contrato de fidelidade. Cancele quando quiser e mantenha acesso até o fim do período já pago. Após essa data, o acesso é encerrado automaticamente.",
  },
];

export function HomeFaqStructuredData() {
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: HOME_FAQ_ITEMS.map((item) => ({
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
      id="home-faq-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(faqSchema),
      }}
    />
  );
}
