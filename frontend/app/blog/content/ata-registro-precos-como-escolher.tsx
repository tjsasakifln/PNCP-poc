import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-14: Ata de Registro de Precos — Como Escolher
 * Target: 2,500-3,000 words | Category: Empresas B2G
 */
export default function AtaRegistroPrecoComoEscolher() {
  return (
    <>
      {/* FAQPage JSON-LD — STORY-262 AC5/AC11 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: [
              {
                '@type': 'Question',
                name: 'O fornecedor e obrigado a fornecer toda a quantidade registrada na ARP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. Conforme o art. 83 da Lei 14.133/2021, o fornecedor registrado e obrigado a fornecer até o quantitativo máximo registrado, nas condições estabelecidas na ata. A recusa injustificada pode resultar em sanções previstas nos arts. 155 a 163 da mesma lei, incluindo impedimento de licitar.',
                },
              },
              {
                '@type': 'Question',
                name: 'E possível pedir reequilíbrio econômico-financeiro durante a vigência da ARP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O art. 82, inciso VI, da Lei 14.133/2021 preve a revisão dos preços registrados quando houver alteração de fato que eleve o custo do bem ou serviço. O fornecedor deve comprovar documentalmente o aumento dos custos, apresentando planilha detalhada e índices de referência. O órgão gerenciador tem discricionariedade para aceitar ou negar o pedido.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a diferença entre ARP e contrato direto por licitação convencional?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Na licitação convencional, o contrato e firmado com quantidade e prazo definidos. Na ARP, o órgão registra preços e quantitativos estimados, mas não há obrigação de aquisição mínima por parte da Administração. O fornecedor, por outro lado, e obrigado a fornecer quando demandado. Isso cria uma assimetria de risco que precisa ser avaliada.',
                },
              },
              {
                '@type': 'Question',
                name: 'Órgãos não participantes podem aderir a ARP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, conforme o art. 86 da Lei 14.133/2021, órgãos não participantes podem aderir a ARP mediante autorização do órgão gerenciador, desde que não ultrapasse os limites legais. As adesões são limitadas a 50% do quantitativo registrado para órgãos federais, é a legislação estadual e municipal pode estabelecer regras próprias.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quando devo recusar participar de uma ARP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Recuse quando o volume estimado exceder sua capacidade de entrega, quando a margem entre o preço registrado e seu custo atualizado for inferior a 8-10%, quando houver alta volatilidade de custos sem cláusula de reequilíbrio adequada, ou quando o órgão gerenciador tiver histórico de demandas irregulares e atrasos no pagamento.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A Ata de Registro de Precos é um dos instrumentos mais utilizados nas
        compras públicas brasileiras, e também um dos menos compreendidos por
        fornecedores. Muitas empresas tratam toda ARP como uma oportunidade
        automática de receita, sem avaliar os riscos específicos desse modelo
        de contratação. O resultado é previsível: fornecedores que se
        comprometem com preços que não sustentam, volumes que não conseguem
        atender e obrigações que desconheciam ao registrar a proposta. Este
        artigo apresenta os 6 critérios objetivos para avaliar se uma ARP
        realmente vale sua participação, fundamentados na Lei 14.133/2021 é na
        prática do mercado B2G.
      </p>

      <h2>O que é uma ARP e por que é diferente de licitação convencional</h2>

      <p>
        O Sistema de Registro de Precos (SRP) está disciplinado nos artigos
        82 a 86 da Lei 14.133/2021 (Nova Lei de Licitações). Diferentemente
        da licitação convencional, onde a Administração contrata uma quantidade
        definida com prazo certo, o SRP registra preços e condições para
        aquisições futuras, sem compromisso de quantidade mínima por parte do
        órgão comprador.
      </p>

      <p>
        Na prática, isso significa que o fornecedor registrado se obriga a
        manter o preço é a disponibilidade durante toda a vigência da ata (até
        12 meses, conforme o art. 84 da Lei 14.133/2021), enquanto a
        Administração pode comprar tudo, parte ou nada do que foi registrado.
        Essa assimetria é o ponto central que diferência a ARP de um contrato
        convencional e que exige avaliação cuidadosa antes da participação.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: Registro de Precos no Brasil</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• Em 2025, aproximadamente 42% das contratações publicadas no PNCP utilizaram o Sistema de Registro de Precos, totalizando mais de 500 mil processos (Fonte: Painel de Compras do Governo Federal, consolidado dez/2025).</li>
          <li>• A vigência média das ARPs registradas em 2025 foi de 10,3 meses, com 68% das atas tendo vigência de 12 meses (Fonte: Painel PNCP, Estatisticas de Compras, 2025).</li>
          <li>• O Tribunal de Contas da União registrou aumento de 27% nos pedidos de reequilíbrio econômico-financeiro em ARPs entre 2023 e 2025, refletindo a volatilidade de custos no período (Fonte: TCU, Relatório de Auditoria em Compras Públicas, 2025).</li>
        </ul>
      </div>

      <h2>Vantagens reais da ARP para o fornecedor</h2>

      <p>
        Antes de analisar os riscos, é importante reconhecer as vantagens
        genuinas que a ARP oferece ao fornecedor bem posicionado.
      </p>

      <p>
        <strong>Previsibilidade de demanda estimada.</strong> Embora não haja
        garantia de compra, a ARP fornece uma estimativa de demanda que permite
        planejamento de produção, estoque e logística. Fornecedores que
        compreendem o padrão de consumo do órgão gerenciador podem antecipar
        pedidos e otimizar sua operação.
      </p>

      <p>
        <strong>Relacionamento institucional.</strong> Estar registrado em uma
        ARP cria um vinculo formal com o órgão comprador. Quando a demanda
        surge, o fornecedor registrado é o primeiro a ser acionado. Isso
        elimina a necessidade de competir novamente por cada pedido individual
        durante a vigência da ata.
      </p>

      <p>
        <strong>Possibilidade de adesões.</strong> Conforme o art. 86 da Lei
        14.133/2021, órgãos não participantes da licitação original podem aderir
        a ARP, ampliando o volume potencial de vendas sem nova competição. Para
        o fornecedor, cada adesão representa receita adicional com custo
        comercial zero.
      </p>

      <h2>Riscos subestimados da ARP</h2>

      <p>
        Os riscos da ARP são sistematicamente subestimados por fornecedores,
        especialmente aqueles com pouca experiência no modelo. Os tres riscos
        principais são:
      </p>

      <p>
        <strong>Obrigação de fornecimento unilateral.</strong> O art. 83 da Lei
        14.133/2021 estabelece que o fornecedor registrado e obrigado a fornecer
        até o quantitativo máximo registrado. A recusa injustificada sujeita a
        empresa as sanções dos arts. 155 a 163, incluindo multa, impedimento de
        licitar e até declaração de inidoneidade. Não existe a opção de
        &ldquo;desistir&rdquo; de uma ARP vigente sem consequências.
      </p>

      <p>
        <strong>Volume incerto.</strong> A Administração pode demandar 100% do
        quantitativo registrado ou 0%. O fornecedor que dimensionou sua operação
        para atender o volume total pode ficar com estoque parado. O que
        dimensionou para atender o mínimo pode não ter capacidade quando a
        demanda cheia se materializar.
      </p>

      <p>
        <strong>Defasagem de preços.</strong> Em atas com vigência de 12 meses,
        a variação de custos de insumos pode corroer a margem do fornecedor.
        O pedido de reequilíbrio é um direito, mas sua concessão depende de
        comprovação documental rigorosa é da discricionariedade do órgão. Não
        há garantia de aprovação, nem de celeridade no processo.
      </p>

      <BlogInlineCTA slug="ata-registro-preços-como-escolher" campaign="b2g" />

      <h2>Os 6 critérios para avaliar uma ARP</h2>

      <p>
        A decisão de participar de uma ARP deve ser baseada em critérios
        objetivos, não em otimismo. Os seis critérios a seguir formam um
        framework de avaliação que pode ser aplicado a qualquer ARP, independente
        do setor ou do porte da empresa. Esse tipo de análise estruturada é o
        que diferência empresas que participam de{' '}
        <Link href="/blog/escolher-editais-maior-probabilidade-vitória">
          editais com maior probabilidade de vitória
        </Link>.
      </p>

      <h3>Critério 1: Volume estimado vs. capacidade de entrega</h3>

      <p>
        O primeiro critério é o mais fundamental: a empresa tem capacidade
        operacional para atender o volume máximo registrado? Não o volume
        médio, não o volume esperado, mas o volume máximo. Porque a
        Administração pode exigir tudo de uma vez, é a recusa injustificada
        gera sanção.
      </p>

      <p>
        A avaliação deve considerar não apenas a capacidade de produção, mas
        também logística de entrega, capacidade de armazenamento, e fluxo de
        caixa para antecipar custos antes do pagamento. Se o volume máximo
        da ARP excede 70% da capacidade operacional da empresa (considerando
        outros contratos ativos), o risco é elevado.
      </p>

      <h3>Critério 2: Preco registrado vs. custo atualizado</h3>

      <p>
        O preço proposto no momento da licitação era competitivo e rentável.
        Mas entre a proposta é o primeiro pedido podem se passar semanas ou
        meses. A pergunta correta não é &ldquo;o preço esta bom hoje?&rdquo;
        mas &ldquo;o preço estara viável daqui a 6 meses?&rdquo;.
      </p>

      <p>
        A recomendação e calcular a margem liquida considerando o cenário de
        custos projetado para o período da ata. Se a margem projetada for
        inferior a 8% no pior cenário, a ARP representa risco financeiro
        relevante. Em setores com alta volatilidade de insumos (alimentos,
        materiais elétricos, combustíveis), a margem de segurança deve ser
        ainda maior.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Exemplo prático: cálculo de margem em ARP de materiais de escritorio</p>
        <p className="text-sm text-ink-secondary mb-3">
          Uma empresa avalia uma ARP para fornecimento de materiais de
          escritorio a órgãos federais. O preço registrado para o kit básico
          é de R$ 85,00 por unidade. O volume máximo registrado é de 12.000
          unidades em 12 meses.
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• <strong>Custo atual do kit:</strong> R$ 68,00 (margem atual: 20%)</li>
          <li>• <strong>Projeção de custo em 6 meses:</strong> R$ 74,00 (inflação de insumos + frete, estimativa conservadora baseada em IPCA acumulado de 5,2% e reajuste de frete rodoviário)</li>
          <li>• <strong>Projeção de custo em 12 meses:</strong> R$ 79,00</li>
          <li>• <strong>Margem no pior cenário (12 meses):</strong> (85 - 79) / 85 = 7,1%</li>
          <li>• <strong>Decisão:</strong> Margem abaixo de 8% no cenário projetado. Participar somente se a ARP contiver cláusula de reequilíbrio clara é o órgão tiver histórico de aceitar pedidos de revisão.</li>
        </ul>
      </div>

      <h3>Critério 3: Quantidade de participantes (diluição)</h3>

      <p>
        Em ARPs com multiplos fornecedores registrados, o volume total e
        distribuído entre os participantes. Quanto mais fornecedores, menor
        o volume garantido para cada um. A avaliação deve considerar quantos
        fornecedores o edital preve registrar e qual a regra de distribuição
        (rodizio, preferência por ordem de classificação, ou demanda livre).
      </p>

      <p>
        ARPs que registram mais de 5 fornecedores para o mesmo item diluem
        significativamente o volume individual. Se o edital não específica
        critério de distribuição, o risco de volume baixo e real, é o
        fornecedor pode manter obrigação contratual para um volume que nunca
        se materializa.
      </p>

      <h3>Critério 4: Órgão gerenciador e histórico de demanda</h3>

      <p>
        O comportamento do órgão gerenciador é um indicador preditivo
        importante. Órgãos com histórico consistente de consumo tendem a
        demandar volumes próximos ao estimado. Órgãos com histórico de atas
        subutilizadas representam risco de volume ocioso.
      </p>

      <p>
        A verificação pode ser feita consultando contratações anteriores do
        mesmo órgão no PNCP, verificando se houve atas para o mesmo objeto
        nos anos anteriores e qual foi o percentual efetivamente demandado.
        Essa análise de histórico é um dos fatores que o{' '}
        <Link href="/features">
          SmartLic incorpora na avaliação de viabilidade
        </Link>{' '}
        de cada oportunidade.
      </p>

      <h3>Critério 5: Prazo de vigência vs. volatilidade de custos</h3>

      <p>
        Atas com vigência de 12 meses em setores com alta volatilidade de
        custos são inerentemente mais arriscadas do que atas de 6 meses em
        setores estáveis. A avaliação deve cruzar o prazo da ata com a
        previsibilidade dos custos dos insumos principais.
      </p>

      <p>
        Em setores como alimentos e combustíveis, onde os preços podem variar
        20% ou mais em 12 meses, a vigência longa é um fator de risco crítico.
        Em setores como papelaria e mobiliário, onde a variação de custos e
        mais moderada, o risco da vigência longa e menor. As{' '}
        <Link href="/blog/cláusulas-escondidas-editais-licitação">
          cláusulas do edital que impactam essa avaliação
        </Link>{' '}
        precisam ser analisadas com atenção. Quem acompanha o mercado sabe
        que{' '}
        <Link href="/blog/nova-geração-ferramentas-mercado-licitações">
          novas ferramentas que estão mudando o mercado de licitações
        </Link>{' '}
        já automatizam parte dessa análise de cláusulas e vigência.
      </p>

      <h3>Critério 6: Cláusula de reequilíbrio</h3>

      <p>
        O sexto critério e frequentemente o mais negligenciado: como o edital
        trata o reequilíbrio econômico-financeiro? A Lei 14.133/2021, no art.
        82, inciso VI, preve a possibilidade de revisão de preços, mas a
        implementação prática varia significativamente entre órgãos.
      </p>

      <p>
        Verifique se o edital específica: (a) qual índice de referência sera
        utilizado para avaliar pedidos de reequilíbrio, (b) qual o prazo máximo
        para resposta ao pedido, (c) se há previsão de reequilíbrio automático
        por índice ou apenas por solicitação fundamentada, e (d) se ha
        precedentes de reequilíbrio concedido pelo mesmo órgão em atas
        anteriores.
      </p>

      <p>
        Um edital que menciona reequilíbrio apenas de forma genérica, sem
        definir índice, prazo ou procedimento, oferece baixa segurança ao
        fornecedor. Em contrapartida, editais com cláusula detalhada de
        reequilíbrio reduzem significativamente o risco de defasagem.
      </p>

      <h2>Quando recusar uma ARP</h2>

      <p>
        A decisão de não participar de uma ARP é tão importante quanto a
        decisão de participar. Recuse quando:
      </p>

      <p>
        <strong>O volume máximo excede sua capacidade.</strong> Se você não
        consegue atender 100% do quantitativo registrado considerando seus
        outros contratos ativos, o risco de inadimplência e real. E a
        consequência e sanção administrativa.
      </p>

      <p>
        <strong>A margem projetada e insuficiente.</strong> Se o cálculo de
        margem no cenário pessimista (custo máximo projetado vs. preço
        registrado) indica margem liquida inferior a 8%, a ARP pode se
        transformar em contrato deficitário.
      </p>

      <p>
        <strong>O órgão tem histórico problemático.</strong> Órgãos com
        histórico de atrasos no pagamento superiores a 60 dias, ou com
        histórico de negar sistematicamente pedidos de reequilíbrio, representam
        risco financeiro desproporcional.
      </p>

      <p>
        <strong>A volatilidade do setor e incompatível com o prazo.</strong>{' '}
        Ata de 12 meses para itens cujos insumos variam mais de 15% ao ano,
        sem cláusula de reequilíbrio robusta, é uma aposta contra o fornecedor.
      </p>

      <p>
        O artigo sobre{' '}
        <Link href="/blog/disputar-todas-licitações-matemática-real">
          a matemática real de disputar todas as licitações
        </Link>{' '}
        aprofunda o raciocínio quantitativo por tras dessa seletividade.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Checklist rápido: avaliação de ARP em 10 minutos</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• Volume máximo registrado cabe na sua capacidade operacional? (Sim/Não)</li>
          <li>• Margem liquida projetada no pior cenário de custos e superior a 8%? (Sim/Não)</li>
          <li>• Ha menos de 5 fornecedores registrados para o mesmo item? (Sim/Não)</li>
          <li>• O órgão gerenciador tem histórico de demanda consistente? (Sim/Não)</li>
          <li>• A vigência da ata e compatível com a volatilidade dos seus custos? (Sim/Não)</li>
          <li>• O edital tem cláusula de reequilíbrio detalhada com índice de referência? (Sim/Não)</li>
          <li>• <strong>Resultado:</strong> 5 ou 6 respostas &ldquo;Sim&rdquo; = ARP viável. 3 ou 4 = Requer análise aprofundada. Menos de 3 = Recusar.</li>
        </ul>
      </div>

      <h2>Considerações sobre a Lei 14.133/2021</h2>

      <p>
        A Nova Lei de Licitações trouxe mudancas relevantes para o SRP que
        impactam diretamente a avaliação do fornecedor. O art. 82 estabelece
        que o SRP sera adotado preferencialmente quando a Administração não
        puder definir previamente o quantitativo a ser demandado, quando for
        conveniente a aquisição parcelada, ou quando atender a mais de um
        órgão.
      </p>

      <p>
        O art. 84 limita a vigência da ARP a 12 meses, prorrogável por igual
        período (totalizando 24 meses). O art. 86 disciplina as adesões por
        órgãos não participantes, limitando-as a 50% do quantitativo
        registrado no ambito federal. Essas regras devem ser consideradas no
        cálculo de volume potencial total.
      </p>

      <p>
        Um ponto frequentemente ignorado e que a Lei 14.133/2021 exige que o
        edital contenha o quantitativo máximo de cada item, vedada a
        indicação de quantitativo mínimo (art. 82, par. 5). Isso reforça a
        assimetria do modelo: o fornecedor se compromete com o máximo, a
        Administração não se compromete com nenhum mínimo.
      </p>

      {/* CTA — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Filtre ARPs por viabilidade real
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic analisa modalidade, valor, prazo e região de cada
          oportunidade. Identifique rapidamente quais ARPs valem sua
          participação e quais devem ser descartadas.
        </p>
        <Link
          href="/signup?source=blog&article=ata-registro-preços-como-escolher&utm_source=blog&utm_medium=cta&utm_content=ata-registro-preços-como-escolher&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/planos" className="underline hover:text-ink">
            Ver planos
          </Link>
        </p>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>O fornecedor e obrigado a fornecer toda a quantidade registrada na ARP?</h3>
      <p>
        Sim. Conforme o art. 83 da Lei 14.133/2021, o fornecedor registrado e
        obrigado a fornecer até o quantitativo máximo registrado, nas condições
        estabelecidas na ata. A recusa injustificada pode resultar em sanções
        previstas nos arts. 155 a 163 da mesma lei, incluindo multa,
        impedimento de licitar e declaração de inidoneidade. Por isso, a
        avaliação de capacidade operacional antes da participação e
        indispensável.
      </p>

      <h3>E possível pedir reequilíbrio econômico-financeiro durante a vigência da ARP?</h3>
      <p>
        Sim. O art. 82, inciso VI, da Lei 14.133/2021 preve a revisão dos
        preços registrados quando houver alteração de fato que eleve o custo
        do bem ou serviço. O fornecedor deve comprovar documentalmente o
        aumento dos custos, apresentando planilha detalhada e índices de
        referência aceitos pelo órgão. É importante notar que o órgão
        gerenciador tem discricionariedade para aceitar ou negar o pedido,
        é o processo pode levar semanas ou meses.
      </p>

      <h3>Qual a diferença entre ARP e contrato direto por licitação convencional?</h3>
      <p>
        Na licitação convencional, o contrato e firmado com quantidade definida,
        prazo de execução e valor total estabelecido. O órgão se compromete a
        adquirir é o fornecedor se compromete a entregar. Na ARP, há uma
        assimetria fundamental: o órgão registra quantidades estimadas sem
        obrigação de compra mínima, enquanto o fornecedor se obriga a fornecer
        até o quantitativo máximo quando demandado. Essa assimetria transfere
        o risco de demanda para o fornecedor.
      </p>

      <h3>Órgãos não participantes podem aderir a ARP?</h3>
      <p>
        Sim, conforme o art. 86 da Lei 14.133/2021. Órgãos não participantes
        podem aderir a ARP mediante autorização do órgão gerenciador e
        aceitação do fornecedor, desde que respeitados os limites legais. No
        ambito federal, as adesões são limitadas a 50% do quantitativo
        registrado. Para o fornecedor, as adesões podem representar
        oportunidade de receita adicional, mas também ampliam o volume total
        de obrigação, o que deve ser considerado no dimensionamento de
        capacidade.
      </p>

      <h3>Quando devo recusar participar de uma ARP?</h3>
      <p>
        Recuse quando o volume máximo estimado exceder sua capacidade de
        entrega considerando outros contratos ativos, quando a margem liquida
        projetada para o pior cenário de custos for inferior a 8-10%, quando
        houver alta volatilidade de custos no seu setor sem cláusula de
        reequilíbrio adequada no edital, ou quando o órgão gerenciador tiver
        histórico de demandas irregulares e atrasos significativos no
        pagamento. A seletividade na participação é um indicador de maturidade
        operacional.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
