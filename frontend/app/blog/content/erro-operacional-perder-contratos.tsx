import Link from 'next/link';

/**
 * STORY-261 AC8: Sample article content — placeholder for STORY-262.
 */
export default function ErroOperacionalPerderContratos() {
  return (
    <>
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Perder uma licitação por preço é uma coisa. Perder por erro operacional
        é outra completamente diferente — e muito mais frustrante. Estima-se que
        até 40% das desclassificações em pregões eletrônicos ocorrem por falhas
        evitáveis na documentação ou no processo.
      </p>

      <h2>1. Documentação incompleta ou desatualizada</h2>

      <p>
        Certidões vencidas, atestados sem correspondência com o objeto, ou
        documentos fora do padrão exigido são a causa número um de
        desclassificação. O problema não é falta de competência — é falta de
        processo.
      </p>

      <h2>2. Análise superficial do edital</h2>

      <p>
        Ler o edital por cima e focar apenas no objeto e no preço é um erro
        clássico. As cláusulas sobre habilitação, garantias e prazos de entrega
        escondem requisitos que eliminam concorrentes despreparados.{' '}
        <Link href="/como-avaliar-licitacao">
          Veja como avaliar um edital de forma completa
        </Link>.
      </p>

      <h2>3. Proposta de preço sem margem de segurança</h2>

      <p>
        Em pregões de menor preço, a pressão por competitividade leva empresas
        a apresentar valores que não cobrem imprevistos. O resultado é um
        contrato deficitário que consome recursos e reputação.
      </p>

      <h2>4. Ignorar o histórico de compras do órgão</h2>

      <p>
        Órgãos públicos têm padrões de compra identificáveis. Conhecer os
        valores praticados em licitações anteriores, os fornecedores habituais
        e as preferências técnicas do órgão é uma vantagem competitiva
        significativa.
      </p>

      {/* CTA — AC13 */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Evite erros com análise inteligente
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic identifica riscos e oportunidades em cada edital antes que
          você invista tempo na proposta.
        </p>
        <Link
          href="/signup?source=blog-erros"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Comece Grátis
        </Link>
      </div>
    </>
  );
}
