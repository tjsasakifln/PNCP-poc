import Link from 'next/link';

/**
 * STORY-261 AC8: Sample article content — placeholder for STORY-262.
 */
export default function ComoAumentarTaxaVitoriaLicitacoes() {
  return (
    <>
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A maioria das empresas que participa de licitações públicas opera com
        taxas de vitória entre 5% e 15%. Isso significa que, para cada 10
        propostas elaboradas, no máximo uma ou duas resultam em contrato.
        O custo oculto dessa ineficiência é enorme.
      </p>

      <h2>Selecione antes de competir</h2>

      <p>
        O primeiro passo para aumentar sua taxa de vitória não é melhorar suas
        propostas — é melhorar sua <strong>seleção de editais</strong>. Empresas
        com taxas acima de 30% têm algo em comum: elas recusam mais licitações
        do que aceitam.
      </p>

      <p>
        A lógica é contraintuitiva: participar de menos licitações, mas das
        certas, gera mais contratos do que atirar para todos os lados.{' '}
        <Link href="/como-avaliar-licitacao">
          Conheça os 5 critérios para avaliar se uma licitação vale a pena
        </Link>.
      </p>

      <h2>Use dados, não intuição</h2>

      <p>
        Empresas que baseiam suas decisões em dados históricos — taxa de vitória
        por modalidade, por faixa de valor, por região — conseguem identificar
        padrões que a intuição sozinha não percebe.
      </p>

      <blockquote>
        <p>
          &ldquo;Depois que começamos a filtrar editais por viabilidade antes de
          decidir participar, nossa taxa de vitória subiu de 8% para 27% em
          seis meses.&rdquo; — Diretor comercial, empresa de TI do Paraná
        </p>
      </blockquote>

      <h2>Automatize a triagem inicial</h2>

      <p>
        Com milhares de licitações publicadas diariamente nos portais PNCP,
        ComprasGov e Portal de Compras Públicas, a triagem manual não escala.
        Ferramentas de inteligência em licitações como o{' '}
        <Link href="/features">SmartLic</Link> automatizam essa etapa,
        classificando editais por relevância setorial e viabilidade antes que
        sua equipe invista tempo em análise detalhada.
      </p>

      {/* CTA Section — AC13: link to product pages */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Filtre licitações por viabilidade real
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic cruza seu perfil com cada edital e recomenda apenas
          oportunidades com chance real de retorno.
        </p>
        <Link
          href="/signup?source=blog-taxa-vitoria"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Comece Grátis
        </Link>
      </div>
    </>
  );
}
