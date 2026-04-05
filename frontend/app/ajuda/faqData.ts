/**
 * Shared FAQ dataset for the Central de Ajuda.
 *
 * Used by:
 *   - AjudaFaqClient (interactive accordion UI)
 *   - AjudaPage (server component → FAQPage JSON-LD via SchemaMarkup)
 *
 * Keep icons out of this file — they're defined in the client component
 * where React JSX/SVG is rendered. This file stays serializable so the
 * server component can import it without pulling any client boundaries.
 */

export interface FAQItem {
  question: string;
  answer: string;
}

export interface FAQCategoryData {
  id: string;
  title: string;
  items: FAQItem[];
}

export const FAQ_DATA: FAQCategoryData[] = [
  {
    id: 'como-buscar',
    title: 'Como Buscar',
    items: [
      {
        question: 'Como faço uma análise por oportunidades de licitação?',
        answer:
          'Acesse a página de Análise, selecione os estados (UFs) de interesse e clique em "Buscar". O sistema consultará automaticamente as fontes oficiais de contratações públicas e retornará as oportunidades filtradas para o seu setor.',
      },
      {
        question: 'Posso buscar em mais de um estado ao mesmo tempo?',
        answer:
          'Sim. Na página de análise, você pode selecionar múltiplos estados simultaneamente. O sistema buscará oportunidades em todos os estados selecionados de forma paralela.',
      },
      {
        question: 'O que significam os filtros de setor?',
        answer:
          'Os setores representam as áreas de atuação (ex.: TI, Engenharia, Saúde). Ao selecionar um setor, o sistema aplica filtros inteligentes de palavras-chave para encontrar licitações relevantes àquela área específica.',
      },
      {
        question: 'Quanto tempo leva uma análise?',
        answer:
          'A duração varia conforme o número de estados selecionados. Normalmente, uma análise leva entre 10 segundos e 2 minutos. Você acompanha o progresso em tempo real na tela.',
      },
      {
        question: 'Como faço download dos resultados em Excel?',
        answer:
          'Após a análise ser concluída, clique no botão "Download Excel" que aparece junto aos resultados. O arquivo será gerado e baixado automaticamente com todas as oportunidades encontradas. Este recurso está disponível em planos pagos.',
      },
      {
        question: 'Como funciona a avaliação por IA?',
        answer:
          'Após cada análise, nosso sistema avalia automaticamente cada oportunidade usando IA, indicando adequação ao seu perfil, critérios de elegibilidade, competitividade e pontos de atenção. Você decide em segundos se vale a pena investir tempo.',
      },
    ],
  },
  {
    id: 'planos',
    title: 'Planos',
    items: [
      {
        question: 'Qual a diferença entre o período de avaliação e o SmartLic Pro?',
        answer:
          'Durante os 14 dias de avaliação gratuita, você usa o produto completo sem restrições: Excel, Pipeline, IA completa e histórico. Após o período de avaliação, assine o SmartLic Pro para continuar com acesso completo.',
      },
      {
        question: 'Posso testar antes de assinar?',
        answer:
          'Sim! Ao criar sua conta, você experimenta o produto completo por 14 dias gratuitamente, sem limites. Não é necessário informar dados de pagamento.',
      },
      {
        question: 'Como amplio meu acesso?',
        answer:
          'Acesse a página de Opções, escolha a modalidade desejada e clique em "Continuar". Você será redirecionado para o checkout seguro. A mudança é imediata após a confirmação do pagamento.',
      },
      {
        question: 'O que acontece se eu cancelar meu acesso?',
        answer:
          'Você mantém acesso completo até o fim do período já pago. Após essa data, o acesso ao sistema é encerrado. O período de avaliação gratuita é exclusivo para os primeiros 14 dias após o cadastro inicial e não é reativado após um cancelamento.',
      },
      {
        question: 'O que acontece quando minhas análises mensais acabam?',
        answer:
          'Quando suas análises mensais se esgotam, elas são renovadas automaticamente no próximo ciclo de faturamento.',
      },
    ],
  },
  {
    id: 'pagamentos',
    title: 'Pagamentos',
    items: [
      {
        question: 'Quais formas de pagamento são aceitas?',
        answer:
          'Aceitamos cartão de crédito (Visa, Mastercard, American Express, Elo) e Boleto Bancário, processados de forma segura pelo Stripe. O Boleto pode levar até 3 dias úteis para confirmação. PIX em breve.',
      },
      {
        question: 'O pagamento é seguro?',
        answer:
          'Sim. Todos os pagamentos são processados pelo Stripe, plataforma certificada PCI-DSS nível 1. Nós nunca armazenamos os dados do seu cartão em nossos servidores.',
      },
      {
        question: 'Como cancelo minha assinatura?',
        answer:
          'Você pode cancelar a qualquer momento acessando Minha Conta. O acesso permanece ativo até o final do período já pago. Após essa data, o acesso ao sistema é encerrado.',
      },
      {
        question: 'Receberei nota fiscal?',
        answer:
          'Sim, uma nota fiscal (invoice) é gerada automaticamente pelo Stripe a cada cobrança e enviada para o e-mail cadastrado na sua conta.',
      },
      {
        question: 'Existe desconto para pagamento anual?',
        answer:
          'Sim! O acesso anual tem economia de 25% em relação ao mensal — R$ 297/mês em vez de R$ 397/mês.',
      },
    ],
  },
  {
    id: 'fontes-dados',
    title: 'Fontes de Dados',
    items: [
      {
        question: 'De onde vêm os dados das licitações?',
        answer:
          'Todos os dados são obtidos diretamente de portais oficiais de contratações públicas do Brasil, que consolidam licitações federais, estaduais e municipais — incluindo autarquias, fundações e empresas públicas. Os dados são públicos e abertos.',
      },
      {
        question: 'Com que frequência os dados são atualizados?',
        answer:
          'Os dados são consultados em tempo real a cada análise. Quando você realiza uma análise, o sistema consulta as fontes oficiais naquele momento, garantindo que os resultados estejam sempre atualizados.',
      },
      {
        question: 'O SmartLic cobre todas as licitações do Brasil?',
        answer:
          'O SmartLic consulta todas as licitações publicadas nas fontes oficiais de contratações públicas. Órgãos municipais, estaduais e federais que publicam nos portais oficiais são cobertos. Órgãos que utilizam exclusivamente sistemas legados podem não aparecer.',
      },
      {
        question: 'Os valores apresentados são exatos?',
        answer:
          'Os valores exibidos são os valores estimados publicados pelos órgãos nas fontes oficiais. Valores finais de contratação podem diferir após o processo licitatório.',
      },
    ],
  },
  {
    id: 'confianca',
    title: 'Confiança e Credibilidade',
    items: [
      {
        question: 'Como o SmartLic decide quais licitações recomendar?',
        answer:
          'Cada licitação é avaliada com 5 critérios objetivos: compatibilidade setorial, faixa de valor, prazo de preparação, região de atuação e modalidade. O resultado é um nível de aderência (Alta, Média ou Baixa) que indica o quanto a oportunidade se encaixa no seu perfil. Não há opinião envolvida — são critérios documentados e verificáveis.',
      },
      {
        question: 'De onde vêm os dados das licitações (credibilidade)?',
        answer:
          'Todos os dados são obtidos de portais oficiais de contratações públicas do Brasil, que cobrem licitações de todas as esferas — federal, estadual e municipal. O SmartLic consolida automaticamente múltiplas fontes oficiais para garantir cobertura nacional (27 UFs) e atualização contínua.',
      },
      {
        question: 'Quem está por trás do SmartLic?',
        answer:
          'O SmartLic é desenvolvido pela CONFENGE Avaliações e Inteligência Artificial LTDA, empresa com experiência em avaliações técnicas e inteligência artificial aplicada ao mercado B2G. Você pode saber mais na nossa página Sobre.',
      },
    ],
  },
  {
    id: 'minha-conta',
    title: 'Minha Conta',
    items: [
      {
        question: 'Como altero minha senha?',
        answer:
          'Acesse Minha Conta e utilize o formulário "Alterar senha". Após a alteração, você será desconectado e precisará fazer login novamente com a nova senha.',
      },
      {
        question: 'Como excluo minha conta?',
        answer:
          'Acesse Minha Conta, na seção "Dados e Privacidade", clique em "Excluir Minha Conta". Esta ação é irreversível e apaga permanentemente todos os seus dados, incluindo histórico de análises e assinaturas.',
      },
      {
        question: 'Posso exportar meus dados?',
        answer:
          'Sim. Na página Minha Conta, seção "Dados e Privacidade", clique em "Exportar Meus Dados". Será gerado um arquivo JSON com todas as suas informações, conforme previsto pela LGPD.',
      },
      {
        question: 'Esqueci minha senha. Como recupero?',
        answer:
          'Na tela de login, clique em "Esqueci minha senha". Um e-mail com instruções de redefinição será enviado para o endereço cadastrado. Verifique também a pasta de spam.',
      },
      {
        question: 'Como entro em contato com o suporte?',
        answer:
          'Você pode entrar em contato através da página de Mensagens dentro da plataforma. Respondemos em até 24 horas úteis.',
      },
    ],
  },
];

/** Flatten every category's items into a single list for JSON-LD FAQPage. */
export function getAllFAQs(): FAQItem[] {
  return FAQ_DATA.flatMap((category) => category.items);
}
