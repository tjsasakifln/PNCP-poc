"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/app/components/AuthProvider";
import LandingNavbar from "@/app/components/landing/LandingNavbar";

/**
 * STORY-226 AC25-AC28: FAQ / Central de Ajuda
 *
 * Searchable FAQ page at /ajuda with collapsible accordion items
 * organized by category. Portuguese language throughout.
 */

// ---- FAQ Data ----

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQCategory {
  id: string;
  title: string;
  icon: React.ReactNode;
  items: FAQItem[];
}

const FAQ_DATA: FAQCategory[] = [
  {
    id: "como-buscar",
    title: "Como Buscar",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    items: [
      {
        question: "Como faço uma busca por oportunidades de licitação?",
        answer:
          "Acesse a página de Busca, selecione os estados (UFs) de interesse, defina o período desejado e clique em \"Buscar\". O sistema consultará automaticamente as fontes oficiais de contratações públicas e retornará as oportunidades filtradas para o seu setor.",
      },
      {
        question: "Posso buscar em mais de um estado ao mesmo tempo?",
        answer:
          "Sim. Na página de busca, você pode selecionar múltiplos estados simultaneamente. O sistema buscará oportunidades em todos os estados selecionados de forma paralela.",
      },
      {
        question: "O que significam os filtros de setor?",
        answer:
          "Os setores representam as áreas de atuação (ex.: Facilities, Uniformes, Limpeza). Ao selecionar um setor, o sistema aplica filtros inteligentes de palavras-chave para encontrar licitações relevantes àquela área específica.",
      },
      {
        question: "Quanto tempo leva uma busca?",
        answer:
          "A duração varia conforme o número de estados selecionados e o período de busca. Normalmente, uma busca leva entre 10 segundos e 2 minutos. Você acompanha o progresso em tempo real na tela.",
      },
      {
        question: "Como faço download dos resultados em Excel?",
        answer:
          "Após a busca ser concluída, clique no botão \"Download Excel\" que aparece junto aos resultados. O arquivo será gerado e baixado automaticamente com todas as oportunidades encontradas. Este recurso está disponível em planos pagos.",
      },
      {
        question: "Como funciona a avaliação por IA?",
        answer:
          "Após cada busca, nosso sistema avalia automaticamente cada oportunidade usando IA, indicando adequação ao seu perfil, critérios de elegibilidade, competitividade e pontos de atenção. Você decide em segundos se vale a pena investir tempo.",
      },
    ],
  },
  {
    id: "planos",
    title: "Planos",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
    items: [
      {
        question: "Qual a diferença entre o período de avaliação e o SmartLic Pro?",
        answer:
          "Durante os 7 dias de avaliação, você usa o produto completo: Excel, Pipeline, IA completa e histórico de 1 ano. A única diferença é o limite de 3 análises. O SmartLic Pro oferece até 1.000 análises por mês e histórico de 5 anos.",
      },
      {
        question: "Posso testar antes de assinar?",
        answer:
          "Sim! Ao criar sua conta, você experimenta o produto completo por 7 dias com 3 análises incluídas. Não é necessário informar dados de pagamento.",
      },
      {
        question: "Como faço upgrade do meu plano?",
        answer:
          "Acesse a página de Planos e Preços, escolha o plano desejado e clique em \"Fazer upgrade\". Você será redirecionado para o checkout seguro. A mudança de plano é imediata após a confirmação do pagamento.",
      },
      {
        question: "Posso fazer downgrade do meu plano?",
        answer:
          "Sim, você pode alterar para um plano inferior a qualquer momento pela página de Planos. Note que ao fazer downgrade, alguns recursos do plano atual deixarão de estar disponíveis.",
      },
      {
        question: "O que acontece quando meus créditos de busca acabam?",
        answer:
          "Quando seus créditos mensais se esgotam, você pode aguardar a renovação no próximo ciclo de faturamento ou fazer upgrade para um plano com mais buscas.",
      },
    ],
  },
  {
    id: "pagamentos",
    title: "Pagamentos",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
    ),
    items: [
      {
        question: "Quais formas de pagamento são aceitas?",
        answer:
          "Aceitamos cartão de crédito (Visa, Mastercard, American Express, Elo) processado de forma segura pelo Stripe. Boleto e PIX estão em fase de implementação.",
      },
      {
        question: "O pagamento é seguro?",
        answer:
          "Sim. Todos os pagamentos são processados pelo Stripe, plataforma certificada PCI-DSS nível 1. Nós nunca armazenamos os dados do seu cartão em nossos servidores.",
      },
      {
        question: "Como cancelo minha assinatura?",
        answer:
          "Você pode cancelar sua assinatura a qualquer momento acessando Minha Conta. O acesso ao plano pago permanece ativo até o final do período já pago.",
      },
      {
        question: "Receberei nota fiscal?",
        answer:
          "Sim, uma nota fiscal (invoice) é gerada automaticamente pelo Stripe a cada cobrança e enviada para o e-mail cadastrado na sua conta.",
      },
      {
        question: "Existe desconto para pagamento anual?",
        answer:
          "Sim! O acesso anual tem economia de 20% em relação ao mensal — R$ 1.599/mês em vez de R$ 1.999/mês.",
      },
    ],
  },
  {
    id: "fontes-dados",
    title: "Fontes de Dados",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
    items: [
      {
        question: "De onde vêm os dados das licitações?",
        answer:
          "Todos os dados são obtidos diretamente de fontes oficiais do Governo Federal para publicação de contratações públicas. Os dados são públicos e abertos.",
      },
      {
        question: "Com que frequência os dados são atualizados?",
        answer:
          "Os dados são consultados em tempo real a cada busca. Quando você realiza uma busca, o sistema consulta as fontes oficiais naquele momento, garantindo que os resultados estejam sempre atualizados.",
      },
      {
        question: "O SmartLic cobre todas as licitações do Brasil?",
        answer:
          "O SmartLic consulta todas as licitações publicadas nas fontes oficiais de contratações públicas. Órgãos municipais, estaduais e federais que publicam nos portais oficiais são cobertos. Órgãos que utilizam exclusivamente sistemas legados podem não aparecer.",
      },
      {
        question: "Os valores apresentados são exatos?",
        answer:
          "Os valores exibidos são os valores estimados publicados pelos órgãos nas fontes oficiais. Valores finais de contratação podem diferir após o processo licitatório.",
      },
    ],
  },
  {
    id: "minha-conta",
    title: "Minha Conta",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    items: [
      {
        question: "Como altero minha senha?",
        answer:
          "Acesse Minha Conta e utilize o formulário \"Alterar senha\". Após a alteração, você será desconectado e precisará fazer login novamente com a nova senha.",
      },
      {
        question: "Como excluo minha conta?",
        answer:
          "Acesse Minha Conta, na seção \"Dados e Privacidade\", clique em \"Excluir Minha Conta\". Esta ação é irreversível e apaga permanentemente todos os seus dados, incluindo histórico de buscas e assinaturas.",
      },
      {
        question: "Posso exportar meus dados?",
        answer:
          "Sim. Na página Minha Conta, seção \"Dados e Privacidade\", clique em \"Exportar Meus Dados\". Será gerado um arquivo JSON com todas as suas informações, conforme previsto pela LGPD.",
      },
      {
        question: "Esqueci minha senha. Como recupero?",
        answer:
          "Na tela de login, clique em \"Esqueci minha senha\". Um e-mail com instruções de redefinição será enviado para o endereço cadastrado. Verifique também a pasta de spam.",
      },
      {
        question: "Como entro em contato com o suporte?",
        answer:
          "Você pode entrar em contato conosco pelo e-mail suporte@smartlic.tech ou através da página de Mensagens dentro da plataforma. Respondemos em até 24 horas úteis.",
      },
    ],
  },
];

// ---- Accordion Item Component ----

function AccordionItem({
  item,
  isOpen,
  onToggle,
}: {
  item: FAQItem;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-b border-[var(--border)] last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-4 px-1 text-left
                   hover:text-[var(--brand-blue)] transition-colors
                   focus-visible:outline-none focus-visible:ring-2
                   focus-visible:ring-[var(--brand-blue)] focus-visible:ring-offset-2
                   rounded"
        aria-expanded={isOpen}
      >
        <span className="text-sm font-medium text-[var(--ink)] pr-4">
          {item.question}
        </span>
        <svg
          className={`w-5 h-5 flex-shrink-0 text-[var(--ink-muted)] transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div
        className={`overflow-hidden transition-all duration-200 ${
          isOpen ? "max-h-96 pb-4" : "max-h-0"
        }`}
      >
        <p className="text-sm text-[var(--ink-secondary)] leading-relaxed px-1">
          {item.answer}
        </p>
      </div>
    </div>
  );
}

// ---- Main FAQ Page ----

export default function AjudaPage() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Filter FAQ items by search query
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) {
      return activeCategory
        ? FAQ_DATA.filter((cat) => cat.id === activeCategory)
        : FAQ_DATA;
    }

    const query = searchQuery.toLowerCase().trim();
    const result: FAQCategory[] = [];

    for (const category of FAQ_DATA) {
      if (activeCategory && category.id !== activeCategory) continue;

      const matchingItems = category.items.filter(
        (item) =>
          item.question.toLowerCase().includes(query) ||
          item.answer.toLowerCase().includes(query)
      );

      if (matchingItems.length > 0) {
        result.push({ ...category, items: matchingItems });
      }
    }

    return result;
  }, [searchQuery, activeCategory]);

  const totalResults = filteredData.reduce((sum, cat) => sum + cat.items.length, 0);

  const toggleItem = (key: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      <LandingNavbar />
      {/* Hero Section */}
      <div className="bg-[var(--surface-0)] border-b border-[var(--border)]">
        <div className="max-w-4xl mx-auto px-4 py-12 text-center">
          <h1 className="text-3xl font-display font-bold text-[var(--ink)] mb-3">
            Central de Ajuda
          </h1>
          <p className="text-[var(--ink-secondary)] mb-8 max-w-lg mx-auto">
            Encontre respostas para as dúvidas mais comuns sobre o SmartLic.
          </p>

          {/* Search Input */}
          <div className="relative max-w-xl mx-auto">
            <svg
              className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--ink-muted)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Buscar nas perguntas frequentes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-button border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         placeholder:text-[var(--ink-muted)]
                         focus:border-[var(--brand-blue)] focus:outline-none
                         focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--ink-muted)]
                           hover:text-[var(--ink)] transition-colors"
                aria-label="Limpar busca"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Category Pills */}
        <div className="flex flex-wrap gap-2 mb-8">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
              ${
                activeCategory === null
                  ? "bg-[var(--brand-navy)] text-white"
                  : "bg-[var(--surface-1)] text-[var(--ink-secondary)] hover:bg-[var(--surface-2)] border border-[var(--border)]"
              }`}
          >
            Todas
          </button>
          {FAQ_DATA.map((category) => (
            <button
              key={category.id}
              onClick={() =>
                setActiveCategory(activeCategory === category.id ? null : category.id)
              }
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                flex items-center gap-1.5
                ${
                  activeCategory === category.id
                    ? "bg-[var(--brand-navy)] text-white"
                    : "bg-[var(--surface-1)] text-[var(--ink-secondary)] hover:bg-[var(--surface-2)] border border-[var(--border)]"
                }`}
            >
              {category.icon}
              {category.title}
            </button>
          ))}
        </div>

        {/* Search Results Count */}
        {searchQuery.trim() && (
          <p className="text-sm text-[var(--ink-muted)] mb-4">
            {totalResults === 0
              ? "Nenhum resultado encontrado"
              : `${totalResults} resultado${totalResults !== 1 ? "s" : ""} encontrado${totalResults !== 1 ? "s" : ""}`}
          </p>
        )}

        {/* FAQ Categories */}
        {filteredData.length === 0 ? (
          <div className="text-center py-16">
            <svg
              className="w-16 h-16 mx-auto text-[var(--ink-muted)] mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="text-lg font-semibold text-[var(--ink)] mb-2">
              Nenhuma pergunta encontrada
            </h3>
            <p className="text-[var(--ink-secondary)] mb-4">
              Tente buscar com termos diferentes ou entre em contato conosco.
            </p>
            <a
              href="mailto:suporte@smartlic.tech"
              className="inline-flex items-center gap-2 text-[var(--brand-blue)] hover:underline"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              suporte@smartlic.tech
            </a>
          </div>
        ) : (
          <div className="space-y-6">
            {filteredData.map((category) => (
              <div
                key={category.id}
                className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card overflow-hidden"
              >
                {/* Category Header */}
                <div className="flex items-center gap-3 px-6 py-4 bg-[var(--surface-1)] border-b border-[var(--border)]">
                  <span className="text-[var(--brand-blue)]">{category.icon}</span>
                  <h2 className="text-lg font-semibold text-[var(--ink)]">
                    {category.title}
                  </h2>
                  <span className="text-xs text-[var(--ink-muted)] ml-auto">
                    {category.items.length} pergunta{category.items.length !== 1 ? "s" : ""}
                  </span>
                </div>

                {/* Accordion Items */}
                <div className="px-6">
                  {category.items.map((item, index) => {
                    const key = `${category.id}-${index}`;
                    return (
                      <AccordionItem
                        key={key}
                        item={item}
                        isOpen={openItems.has(key)}
                        onToggle={() => toggleItem(key)}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Contact Section */}
        <div id="contato" className="mt-12 text-center bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 scroll-mt-24">
          <h3 className="text-xl font-semibold text-[var(--ink)] mb-2">
            Ainda tem dúvidas?
          </h3>
          <p className="text-[var(--ink-secondary)] mb-6">
            Nossa equipe está pronta para ajudar.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {user ? (
              <Link
                href="/mensagens"
                className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                           rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Enviar Mensagem
              </Link>
            ) : (
              <a
                href="mailto:suporte@smartlic.tech"
                className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                           rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Enviar E-mail
              </a>
            )}
            <a
              href="mailto:suporte@smartlic.tech"
              className="inline-flex items-center gap-2 px-6 py-3 border border-[var(--border)]
                         text-[var(--ink)] rounded-button font-semibold
                         hover:bg-[var(--surface-1)] transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              suporte@smartlic.tech
            </a>
          </div>
        </div>

        {/* Back Link */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-[var(--ink-muted)] hover:underline">
            Voltar para a página inicial
          </Link>
        </div>
      </div>
    </div>
  );
}
