/**
 * PSEOTemplate — Template programático SEO variável {setor}/{uf}/{municipio}
 *
 * Issue #1004 (COPY-PSEO-005). Componente compartilhado de copy para páginas
 * programáticas: hero, intro, "Como o SmartLic encontra…", FAQ, CTAs e
 * banner Founders. Variáveis interpoladas a partir de PSEOContext.
 *
 * Escopo desta PR:
 *  - Apenas template/copy variável + JSON-LD FAQPage.
 *  - NÃO inclui o bloco de dados (5 últimos editais, top órgãos,
 *    top fornecedores) — deliverable da PR #1007 (PSEODataBlock).
 *  - NÃO altera helpers de noindex (#1018).
 *  - NÃO toca canonical/hreflang (#990/#988).
 *
 * Voice "português de obra" — proibido: outrossim, no que tange,
 * robusta, ecossistema, stakeholders.
 */
import Link from "next/link";
import PreviewCTA from "./PreviewCTA";

export type PSEOContext = {
  setor: string;              // "Pavimentação asfáltica"
  setorSlug: string;          // "pavimentacao-asfaltica"
  ufNome?: string;            // "Santa Catarina"
  ufSigla?: string;           // "SC"
  municipio?: string;         // "Joinville"
  totalOpen: number;          // 47
  totalOpenSemana: number;    // 12
  totalOpenMunicipio?: number;
  valorMedio: string;         // "R$ 320.000"
  valorMin?: string;
  valorMax?: string;
  modalidadeTop?: string;     // "Pregão Eletrônico"
  modalidadePercents?: { pregao: number; concorrencia: number; dispensa: number };
  keywordsCount?: number;
  planoMensal?: string;       // "R$ 397"
  dataHoje?: string;          // "10/05/2026"
};

/** Beachhead positioning: município > UF > Brasil. */
function getRegionLabel(ctx: PSEOContext): string {
  if (ctx.municipio && ctx.ufSigla) return `${ctx.municipio} (${ctx.ufSigla})`;
  if (ctx.municipio) return ctx.municipio;
  if (ctx.ufNome) return ctx.ufNome;
  return "Brasil";
}

/** Total a exibir: município se presente, senão total geral. */
function getTotalForRegion(ctx: PSEOContext): number {
  if (ctx.municipio && typeof ctx.totalOpenMunicipio === "number") {
    return ctx.totalOpenMunicipio;
  }
  return ctx.totalOpen;
}

export function buildPSEOH1(ctx: PSEOContext): string {
  const total = getTotalForRegion(ctx);
  const region = getRegionLabel(ctx);
  return `${total} editais abertos de ${ctx.setor} em ${region}`;
}

export function buildPSEOFaqs(ctx: PSEOContext) {
  const region = getRegionLabel(ctx);
  const mp = ctx.modalidadePercents;
  const modalidadeAnswer = mp
    ? `Em ${ctx.setor} no SmartLic, ${mp.pregao}% dos editais de ${region} são Pregão Eletrônico, ` +
      `${mp.concorrencia}% Concorrência e ${mp.dispensa}% Dispensa. ` +
      `Pregão domina porque a Lei 14.133 prioriza o eletrônico para bens e serviços comuns. ` +
      `Quem participa só de licitação presencial perde a maior fatia de oportunidades.`
    : `Em ${ctx.setor}, a maioria dos editais públicos roda como Pregão Eletrônico ` +
      `(modalidade prioritária da Lei 14.133 para bens e serviços comuns). ` +
      `Concorrência aparece em obras e contratos de maior valor. Dispensa é direta, sem disputa pública. ` +
      `Quem só atende presencial perde a maior parte do mercado.`;

  const ticketAnswer =
    `O ticket médio de contratos de ${ctx.setor} em ${region} no SmartLic está em ${ctx.valorMedio}. ` +
    (ctx.valorMin && ctx.valorMax
      ? `O menor sai em torno de ${ctx.valorMin} e o maior chega a ${ctx.valorMax}. `
      : "") +
    `O ticket varia muito por porte do órgão: prefeitura pequena gira valores menores que governo estadual. ` +
    `Use o filtro de valor mínimo/máximo no SmartLic para focar onde sua estrutura entrega bem.`;

  const alertaAnswer =
    `O SmartLic monitora PNCP, Portal de Compras Públicas e ComprasGov todo dia. ` +
    `Quando abre edital novo de ${ctx.setor} em ${region}, você recebe alerta por email com link direto para o edital — ` +
    `sem precisar abrir 3 portais nem mexer em planilha. ` +
    `O teste grátis de 14 dias já liga os alertas no seu cadastro.`;

  const assessorAnswer =
    `Não. Para participar de licitação você precisa de CNPJ ativo, certidões em dia e cadastro nos portais oficiais (PNCP, ComprasNet, sistemas estaduais). ` +
    `Assessor cobra mensalidade pra fazer o que você consegue fazer sozinho com ferramenta certa. ` +
    `O SmartLic substitui a parte de busca e análise de viabilidade — você lê o edital, decide se entra, monta a proposta e mantém suas certidões. ` +
    `Quem fatura com licitação dispensa intermediário.`;

  const precoAnswer =
    `O SmartLic tem 14 dias grátis sem cartão. Depois, planos mensais a partir de ` +
    `${ctx.planoMensal ?? "R$ 397"} por mês com cancelamento livre. ` +
    `Existe também o plano Fundadores: R$ 997 uma vez, acesso vitalício — vagas limitadas, encerra 30/06. ` +
    `Quem usa todo mês sai ganhando no plano vitalício.`;

  return [
    {
      question: `Quais modalidades são mais comuns em ${ctx.setor}?`,
      answer: modalidadeAnswer,
    },
    {
      question: `Qual ticket médio de contrato de ${ctx.setor} em ${region}?`,
      answer: ticketAnswer,
    },
    {
      question: `Como saber quando abre novo edital de ${ctx.setor}?`,
      answer: alertaAnswer,
    },
    {
      question: `Preciso de assessor de licitação para participar?`,
      answer: assessorAnswer,
    },
    {
      question: `Quanto custa o SmartLic?`,
      answer: precoAnswer,
    },
  ];
}

export function buildFaqJsonLd(ctx: PSEOContext): Record<string, unknown> {
  const faqs = buildPSEOFaqs(ctx);
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((f) => ({
      "@type": "Question",
      name: f.question,
      acceptedAnswer: { "@type": "Answer", text: f.answer },
    })),
  };
}

type Props = {
  ctx: PSEOContext;
  /** Slot para PSEODataBlock (#1007) — entre intro e CTA primário. */
  dataBlock?: React.ReactNode;
};

export default function PSEOTemplate({ ctx, dataBlock }: Props) {
  const region = getRegionLabel(ctx);
  const total = getTotalForRegion(ctx);
  const faqs = buildPSEOFaqs(ctx);
  const ctaRef = `pseo-${ctx.setorSlug}${ctx.ufSigla ? `-${ctx.ufSigla.toLowerCase()}` : ""}`;

  return (
    <main id="main-content" className="min-h-screen bg-white dark:bg-gray-950">
      {/* Hero variável (AC: H1 + sub data atualização + fontes) */}
      <section className="bg-gradient-to-br from-brand-blue to-blue-700 text-white py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl md:text-5xl font-bold mb-4">
            {buildPSEOH1(ctx)}
          </h1>
          <p className="text-lg text-blue-100 max-w-3xl">
            Atualizado em {ctx.dataHoje ?? "hoje"} · fontes oficiais PNCP, Portal de Compras Públicas e ComprasGov.
          </p>
        </div>
      </section>

      {/* Bloco de dados (slot — preenchido pela PR #1007) */}
      {dataBlock ? (
        <section
          aria-label="Dados do setor"
          className="max-w-5xl mx-auto py-8 px-4"
          data-testid="pseo-data-block-slot"
        >
          {dataBlock}
        </section>
      ) : null}

      {/* CTA app-específico inline (AC: contexto após dados) */}
      <section className="max-w-5xl mx-auto px-4 py-8">
        <div className="rounded-2xl border border-brand-blue/30 bg-brand-blue/5 p-6 sm:p-8">
          <p className="text-lg text-gray-900 dark:text-white mb-4">
            Quer receber os próximos {ctx.totalOpenSemana} editais de {ctx.setor} em {region} por email,
            no dia em que abrirem?
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              href={`/consultoria-b2g?ref=${ctaRef}`}
              className="inline-block px-6 py-3 bg-brand-blue text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Receber alertas grátis 14 dias →
            </Link>
            <Link
              href={`/observatorio/${ctx.setorSlug}`}
              className="inline-block px-6 py-3 bg-white dark:bg-gray-900 text-brand-navy dark:text-white font-medium rounded-lg border border-gray-300 dark:border-gray-700 hover:border-brand-blue transition-colors"
            >
              Só quero ver os dados
            </Link>
          </div>
        </div>
      </section>

      {/* Preview CTA secundário (#1009 COPY-PSEO-CTA-010): "Ver 3 editais grátis" com blurred premium */}
      <PreviewCTA
        setor={ctx.setorSlug}
        uf={ctx.ufSigla}
        setorLabel={ctx.setor}
        ufLabel={ctx.ufNome ?? ""}
        totalOpen={total}
      />

      {/* Como o SmartLic encontra editais antes de você (AC: educativo problem/solution aware) */}
      <section className="max-w-5xl mx-auto py-12 px-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Como o SmartLic encontra editais de {ctx.setor} antes de você
        </h2>
        <div className="prose dark:prose-invert max-w-3xl text-gray-700 dark:text-gray-300">
          <p>
            Edital de {ctx.setor} aparece em três portais diferentes: PNCP, Portal de Compras Públicas e ComprasGov.
            Cada portal tem layout próprio, filtro próprio e nem sempre conversa entre si. Quem só olha um perde edital
            que abriu em outro.
          </p>
          <p>
            O SmartLic puxa os três portais ao mesmo tempo, junta o que é o mesmo edital e separa o que é diferente.
            Em cima desse monte de edital bruto, a IA classifica o que é {ctx.setor} de verdade e o que é só palavra
            parecida. No fim, sobra a lista limpa em {region} — só o que faz sentido pra você ler.
          </p>
          <p>
            Cada edital sai com nota de viabilidade que considera modalidade, prazo, valor e geografia. Você vê em 3 minutos
            o que normalmente levaria a tarde inteira.
          </p>
        </div>
      </section>

      {/* FAQ específico por setor — 5 perguntas (AC: FAQPage rich snippets) */}
      <section className="bg-gray-50 dark:bg-gray-900 py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">
            Perguntas frequentes sobre {ctx.setor} em {region}
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <details
                key={i}
                className="group bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <summary className="flex items-center justify-between p-5 cursor-pointer font-medium text-gray-900 dark:text-white">
                  {faq.question}
                  <span className="ml-2 text-gray-400 group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <div className="px-5 pb-5 text-gray-600 dark:text-gray-300 leading-relaxed">
                  {faq.answer}
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Cross-sell Founders rodapé (AC: COPY-CROSS-007 banner R$997) */}
      <section className="max-w-5xl mx-auto py-8 px-4">
        <div className="rounded-xl border border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-700 p-6 text-center">
          <p className="text-base text-gray-900 dark:text-white mb-3">
            Vai usar SmartLic todo mês? Existe plano vitalício R$ 997 (vagas limitadas, encerra 30/06).
          </p>
          <Link
            href={`/fundadores?src=${ctaRef}`}
            className="inline-block px-5 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-lg transition-colors"
          >
            Saber mais →
          </Link>
        </div>
      </section>

      {/* Sticky bottom CTA mobile (AC: variável total + setor) */}
      <div
        className="fixed bottom-0 left-0 right-0 z-40 sm:hidden bg-brand-navy text-white px-4 py-3 shadow-lg"
        data-testid="pseo-sticky-cta"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm font-medium">
            {total} editais abertos · {ctx.setor}
          </span>
          <Link
            href={`/consultoria-b2g?ref=${ctaRef}-sticky`}
            className="px-4 py-2 bg-brand-blue rounded-lg text-sm font-semibold whitespace-nowrap"
          >
            Receber alertas →
          </Link>
        </div>
      </div>

      {/* JSON-LD FAQPage (AC: rich snippets) */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(buildFaqJsonLd(ctx)) }}
      />
    </main>
  );
}
