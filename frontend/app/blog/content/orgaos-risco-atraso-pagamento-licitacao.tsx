import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-11: Como Identificar Orgaos com Maior Risco de Atraso no Pagamento
 * Target: 2,000-2,500 words | Cluster: inteligencia em licitacoes
 */
export default function OrgaosRiscoAtrasoPagamentoLicitacao() {
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
                name: 'Como consultar o histórico de pagamento de um órgão público antes de participar de uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'As principais fontes são o Portal da Transparência (transparencia.gov.br) para órgãos federais, os portais de transparência estaduais e municipais, e o SIAFI (Sistema Integrado de Administração Financeira) para consulta de empenhos e pagamentos do governo federal. No Portal da Transparência, acesse Despesas > Pagamentos e filtre pelo órgão. Verifique o tempo médio entre a emissão da nota de empenho e o pagamento efetivo nos últimos 12 meses.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que são restos a pagar e por que são um indicador de risco?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Restos a pagar são despesas empenhadas em um exercício financeiro que não foram pagas até 31 de dezembro. Dividem-se em processados (serviço prestado, aguardando pagamento) e não processados (ainda em execução). Um volume alto de restos a pagar processados indica que o órgão tem dívidas reconhecidas sem recursos para pagar, sinalizando risco de atraso para novos contratos. Em 2024, os restos a pagar do governo federal totalizaram R$ 232,4 bilhões.',
                },
              },
              {
                '@type': 'Question',
                name: 'Órgãos federais pagam mais rápido que estaduais e municipais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Em geral, sim. Órgãos federais operam com o Tesouro Nacional como fonte pagadora, o que garante maior previsibilidade. O prazo médio de pagamento em órgãos federais é de 30 a 45 dias. Em órgãos estaduais, varia de 45 a 90 dias dependendo da saúde fiscal do estado. Em municípios, a variação é maior: de 30 dias em municípios superavitários a mais de 180 dias em municípios com dificuldades fiscais.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível incluir cláusula de correção monetária no contrato para compensar atrasos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. A Lei 14.133/2021 (Nova Lei de Licitações) prevê em seu artigo 92, inciso V, a obrigatoriedade de cláusula de atualização financeira em contratos. Além disso, o artigo 137 permite a suspensão do contrato pelo fornecedor em caso de atraso superior a 2 meses nos pagamentos devidos pela Administração. Na prática, porém, acionar essas cláusulas gera desgaste na relação com o órgão.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        No mercado de licitações públicas, a obsessão com a adjudicação
        ofusca um risco igualmente crítico: a capacidade do órgão contratante
        de honrar os pagamentos no prazo. Ganhar um pregão e assinar um
        contrato de R$ 500 mil não significa receber R$ 500 mil. Para
        empresas B2G que dependem de fluxo de caixa previsível, avaliar o
        risco de inadimplência do órgão antes de participar de uma licitação
        é tão importante quanto avaliar a competitividade do preço.
      </p>

      <p>
        Neste artigo, apresentamos um framework prático com 5 indicadores
        objetivos para classificar o risco de atraso no pagamento de órgãos
        públicos, com as fontes oficiais de consulta e critérios de
        classificação que podem ser incorporados na sua triagem de editais.
      </p>

      <h2>O risco que ninguém avalia: receber é tão importante quanto ganhar</h2>

      <p>
        A maioria das empresas que participa de licitações avalia preço,
        prazo, concorrência e requisitos técnicos antes de decidir disputar
        um pregão. Poucas, no entanto, investigam se o órgão contratante
        tem histórico de pagar em dia. Esse é um ponto cego que pode
        transformar um contrato aparentemente lucrativo em um problema de
        fluxo de caixa.
      </p>

      <p>
        O impacto financeiro é direto. Uma empresa que fornece mercadorias
        ou presta serviços sob contrato público arca com os custos de
        produção, logística e folha de pagamento antes de receber. Quando o
        pagamento atrasa 60, 90 ou 120 dias além do prazo contratual, a
        empresa precisa financiar o capital de giro com recursos próprios ou
        crédito bancário, corroendo a margem do contrato.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: inadimplência e atrasos no setor público</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; Em 2024, o estoque de restos a pagar inscritos do governo federal totalizou R$ 232,4 bilhões,
            dos quais R$ 148,7 bilhões eram processados (despesa já reconhecida, aguardando pagamento). Esse
            volume cresceu 11,3% em relação a 2023 (Fonte: Tesouro Nacional, Relatório de Avaliação de Receitas
            e Despesas Primárias, 4o bimestre de 2024).
          </li>
          <li>
            &bull; Segundo levantamento da Confederação Nacional de Municípios (CNM), 38% dos municípios
            brasileiros encerraram 2023 com déficit orçamentário, comprometendo a capacidade de pagamento
            de contratos vigentes (Fonte: CNM, Estudo sobre Finanças Municipais, 2024).
          </li>
          <li>
            &bull; O prazo médio de pagamento a fornecedores pelo governo federal foi de 37 dias em 2024, mas
            a mediana por órgão varia de 18 dias (órgãos militares) a 73 dias (universidades federais), indicando
            disparidade significativa entre unidades gestoras (Fonte: Portal da Transparência, dados de execução
            orçamentária, 2024).
          </li>
        </ul>
      </div>

      <h2>Onde consultar histórico de pagamento de órgãos públicos</h2>

      <p>
        Antes de detalhar os indicadores de risco, é importante conhecer as
        fontes oficiais de dados. Todas são públicas e gratuitas:
      </p>

      <h3>Portal da Transparência (transparencia.gov.br)</h3>

      <p>
        Principal fonte para órgãos federais. Permite consultar despesas por
        órgão, por favorecido (CNPJ do fornecedor) e por período. A seção
        &ldquo;Despesas&rdquo; mostra o ciclo completo: empenho, liquidação
        e pagamento. A diferença de datas entre liquidação e pagamento revela
        o prazo efetivo de pagamento do órgão. É possível exportar dados em
        CSV para análise quantitativa.
      </p>

      <h3>SIAFI (Sistema Integrado de Administração Financeira)</h3>

      <p>
        O SIAFI é o sistema de execução orçamentária do governo federal. Embora
        o acesso direto seja restrito a usuários credenciados, os dados
        consolidados são publicados no Portal da Transparência e no Tesouro
        Gerencial. Para análises mais detalhadas, o Tesouro Gerencial
        (tesourogerencial.tesouro.gov.br) oferece cubos OLAP com cruzamentos
        por órgão, função, subfunção e natureza de despesa.
      </p>

      <h3>Portais estaduais e municipais de transparência</h3>

      <p>
        A Lei de Acesso à Informação (Lei 12.527/2011) obriga todos os entes
        federativos a manter portais de transparência. A qualidade dos dados
        varia significativamente. Estados como São Paulo, Minas Gerais e
        Paraná mantêm portais com dados detalhados de execução orçamentária.
        Municípios menores frequentemente publicam apenas o mínimo legal, o
        que dificulta a análise.
      </p>

      <h3>Tribunal de Contas (TCU, TCEs, TCMs)</h3>

      <p>
        Os tribunais de contas publicam relatórios de auditoria, contas
        anuais e pareceres sobre a gestão fiscal dos órgãos. O TCU
        disponibiliza dados no portal <em>Contas Públicas</em>. Processos
        de tomada de contas especial (TCE) contra um órgão indicam problemas
        graves de gestão financeira.
      </p>

      <h2>5 indicadores de risco de atraso no pagamento</h2>

      <p>
        Com base nas fontes acima, é possível construir uma avaliação de
        risco estruturada para cada órgão. Os cinco indicadores a seguir
        cobrem as dimensões financeira, orçamentária e de gestão que mais
        impactam a pontualidade dos pagamentos.
      </p>

      <h3>Indicador 1: Volume de restos a pagar processados</h3>

      <p>
        Restos a pagar processados são despesas em que o serviço já foi
        prestado ou a mercadoria já foi entregue, mas o pagamento não foi
        efetuado dentro do exercício financeiro. Um volume crescente de
        restos a pagar processados em relação ao orçamento total do órgão
        indica que as obrigações estão se acumulando mais rápido do que a
        capacidade de pagamento.
      </p>

      <p>
        <strong>Como medir:</strong> divida o valor de restos a pagar
        processados pelo orçamento anual do órgão. Acima de 15% é sinal de
        alerta; acima de 25% é risco elevado.
      </p>

      <h3>Indicador 2: Prazo médio entre liquidação e pagamento</h3>

      <p>
        No ciclo orçamentário, a liquidação confirma que o fornecedor cumpriu
        sua obrigação contratual. O pagamento é a transferência efetiva de
        recursos. O prazo entre liquidação e pagamento é o indicador mais
        direto de pontualidade. No Portal da Transparência, é possível
        calcular esse prazo para órgãos federais consultando as datas de
        liquidação e pagamento de contratos recentes.
      </p>

      <p>
        <strong>Como medir:</strong> calcule a mediana do prazo
        liquidação-pagamento nos últimos 6 meses. Até 30 dias: regular.
        De 30 a 60 dias: atenção. Acima de 60 dias: risco.
      </p>

      <BlogInlineCTA slug="orgaos-risco-atraso-pagamento-licitacao" campaign="b2g" />

      <h3>Indicador 3: Histórico de contingenciamento orçamentário</h3>

      <p>
        Contingenciamento é o bloqueio temporário de dotações orçamentárias
        pelo Poder Executivo para cumprir metas fiscais. Órgãos
        frequentemente contingenciados tendem a atrasar pagamentos nos
        períodos de restrição, que tipicamente ocorrem no segundo semestre.
        Universidades, institutos de pesquisa e órgãos de saúde são
        historicamente mais afetados por contingenciamentos.
      </p>

      <p>
        <strong>Como medir:</strong> consulte os decretos de programação
        orçamentária e financeira publicados pelo Ministério do Planejamento.
        Compare o orçamento aprovado (LOA) com o orçamento efetivamente
        liberado para cada órgão.
      </p>

      <h3>Indicador 4: Empenhos cancelados ou anulados</h3>

      <p>
        O cancelamento de notas de empenho é um sinal preocupante. Indica que
        o órgão não conseguiu ou não quis honrar compromissos já assumidos. Um
        volume elevado de empenhos anulados em relação ao total emitido
        sugere problemas de planejamento orçamentário ou restrições de caixa.
      </p>

      <p>
        <strong>Como medir:</strong> no Portal da Transparência, filtre por
        órgão e verifique a proporção de empenhos com situação
        &ldquo;cancelado&rdquo; ou &ldquo;anulado&rdquo; nos últimos 12
        meses. Acima de 10% é sinal de alerta.
      </p>

      <h3>Indicador 5: Tomadas de contas especiais (TCE) em andamento</h3>

      <p>
        A instauração de tomada de contas especial pelo Tribunal de Contas
        indica irregularidade na gestão de recursos públicos. Órgãos com
        TCEs em andamento apresentam risco institucional elevado, pois a
        situação sugere problemas sistêmicos de gestão que frequentemente
        afetam a pontualidade dos pagamentos.
      </p>

      <p>
        <strong>Como medir:</strong> consulte o portal do TCU (pesquisa de
        processos) ou do TCE do respectivo estado. A existência de mais de
        uma TCE em andamento contra o mesmo órgão nos últimos 3 anos é
        indicador de risco elevado.
      </p>

      <h2>Classificação de risco: verde, amarelo, vermelho</h2>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Exemplo prático: classificação de risco de um órgão</p>
        <div className="space-y-3 text-sm text-ink-secondary">
          <p>
            <strong>Cenário:</strong> Sua empresa está avaliando um pregão de R$ 320 mil publicado por uma
            universidade federal no Nordeste. Antes de investir tempo na proposta, você consulta os 5
            indicadores:
          </p>
          <ul className="space-y-1.5">
            <li>&bull; Restos a pagar processados / orçamento: 22% (amarelo)</li>
            <li>&bull; Prazo médio liquidação-pagamento: 54 dias (amarelo)</li>
            <li>&bull; Contingenciamento no exercício atual: sim, 18% do orçamento bloqueado (amarelo)</li>
            <li>&bull; Empenhos cancelados nos últimos 12 meses: 7% (verde)</li>
            <li>&bull; TCEs em andamento: nenhuma (verde)</li>
          </ul>
          <p className="mt-2">
            <strong>Resultado:</strong> 3 indicadores amarelos e 2 verdes = classificação geral AMARELA.
          </p>
          <p>
            <strong>Decisão:</strong> O órgão não apresenta risco crítico, mas o prazo de pagamento estimado
            é de 45 a 70 dias. Antes de participar, a empresa deve: (1) verificar se sua margem comporta o
            custo financeiro de 60 dias de capital de giro, estimado em R$ 3.200 (taxa CDI sobre R$ 320 mil
            por 2 meses); (2) considerar cláusula de atualização financeira conforme Art. 92 da Lei
            14.133/2021.
          </p>
        </div>
      </div>

      <p>
        A classificação segue uma lógica simples baseada na contagem de
        indicadores em cada faixa:
      </p>

      <p>
        <strong>Verde (risco baixo):</strong> pelo menos 4 dos 5 indicadores
        verdes. O órgão demonstra capacidade de pagamento consistente.
        Participação recomendada sem restrições adicionais.
      </p>

      <p>
        <strong>Amarelo (risco moderado):</strong> 2 ou 3 indicadores
        amarelos. O órgão apresenta sinais de pressão orçamentária.
        Participação recomendada com ajuste de preço para compensar o custo
        financeiro do atraso esperado e com atenção redobrada a cláusulas
        de reajuste e correção monetária.
      </p>

      <p>
        <strong>Vermelho (risco elevado):</strong> 2 ou mais indicadores
        vermelhos, ou 1 vermelho combinado com 2 ou mais amarelos. O órgão
        tem alta probabilidade de atraso significativo nos pagamentos. A
        participação só é recomendada se o contrato tiver margem suficiente
        para absorver atrasos de 90 a 180 dias e se a empresa tiver capital
        de giro para sustentar a operação sem esse recebimento.
      </p>

      <h2>Como incorporar a análise de risco na triagem de editais</h2>

      <p>
        A avaliação de risco de pagamento deve ser integrada ao processo de
        triagem de editais, não tratada como etapa separada. Na prática,
        isso significa que cada oportunidade identificada pelo{' '}
        <Link href="/buscar">
          sistema de busca
        </Link>{' '}
        recebe, além da avaliação de viabilidade técnica e comercial, uma
        nota de risco financeiro do órgão contratante.
      </p>

      <p>
        Para empresas que utilizam ferramentas de inteligência em licitações,
        o fator geográfico já oferece uma primeira camada de triagem. Órgãos
        localizados em municípios com déficit orçamentário recorrente ou em
        estados com histórico de contingenciamento elevado recebem pontuação
        menor na avaliação de viabilidade geográfica. Essa análise
        automatizada não substitui a consulta direta aos indicadores
        orçamentários, mas funciona como filtro inicial para direcionar a
        investigação aprofundada.
      </p>

      <p>
        O fluxo recomendado é o seguinte: a ferramenta de busca identifica
        os editais relevantes por setor e região. A{' '}
        <Link href="/blog/escolher-editais-maior-probabilidade-vitoria">
          análise de viabilidade
        </Link>{' '}
        filtra por competitividade e aderência técnica. O analista então
        aplica os 5 indicadores de risco financeiro aos editais
        pré-qualificados, eliminando aqueles com classificação vermelha (a
        menos que haja justificativa estratégica para aceitar o risco).
      </p>

      <h3>Integrando risco financeiro ao custo da proposta</h3>

      <p>
        Quando o órgão é classificado como amarelo, o custo financeiro do
        atraso esperado deve ser incorporado na formação de preço da
        proposta. A fórmula é direta: custo financeiro = valor do contrato
        x taxa de juros mensal x número estimado de meses de atraso. Esse
        custo deve ser somado à margem, não absorvido por ela.
      </p>

      <p>
        Empresas que não fazem esse cálculo descobrem tarde demais que um
        contrato &ldquo;vencido&rdquo; com margem de 12% se transformou em
        prejuízo líquido quando o pagamento atrasou 120 dias. A disciplina
        de precificar o risco de inadimplência antes de enviar a proposta é
        uma das práticas que separam{' '}
        <Link href="/blog/custo-invisivel-disputar-pregoes-errados">
          empresas lucrativas de empresas que faturam muito e lucram pouco
        </Link>.
        {' '}Vale também entender como avaliar as{' '}
        <Link href="/blog/clausulas-escondidas-editais-licitacao">
          cláusulas escondidas que eliminam fornecedores
        </Link>{' '}
        antes mesmo de chegar à fase de preços, e{' '}
        <Link href="/blog/identificar-clientes-gargalo-operacional-licitacoes">
          como consultorias identificam clientes com gargalo operacional em licitações
        </Link>{' '}
        para priorizar onde atuar.
      </p>

      <h2>Fontes de dados complementares</h2>

      <p>
        Além dos portais oficiais, duas fontes complementares podem enriquecer
        a avaliação de risco:
      </p>

      <p>
        <strong>CADIN (Cadastro Informativo de Créditos não Quitados):</strong>{' '}
        embora voltado para devedores do governo federal, consultar se o órgão
        tem fornecedores inscritos no CADIN pode indicar inadimplência
        sistêmica com o setor privado.
      </p>

      <p>
        <strong>Relatórios de gestão fiscal (LRF):</strong> a Lei de
        Responsabilidade Fiscal obriga entes federativos a publicar
        bimestralmente relatórios de execução orçamentária. Esses
        relatórios, disponibilizados nos portais das secretarias de
        fazenda, revelam a saúde fiscal do ente e sua capacidade de honrar
        compromissos.
      </p>

      {/* CTA — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Avalie a viabilidade geográfica e institucional com o SmartLic
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic avalia cada oportunidade com 4 critérios objetivos, incluindo
          viabilidade geográfica, ajudando sua equipe a priorizar órgãos com
          melhor histórico de execução orçamentária.
        </p>
        <Link
          href="/consultoria-b2g?source=blog&article=orgaos-risco-atraso-pagamento-licitacao&utm_source=blog&utm_medium=cta&utm_content=orgaos-risco-atraso-pagamento-licitacao&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Pedir um diagnóstico à CONFENGE
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/consultoria-b2g" className="underline hover:text-ink">
            Ver planos
          </Link>
        </p>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Como consultar o histórico de pagamento de um órgão público antes de participar de uma licitação?</h3>
      <p>
        As principais fontes são o Portal da Transparência
        (transparencia.gov.br) para órgãos federais, os portais de
        transparência estaduais e municipais, e o SIAFI para consulta de
        empenhos e pagamentos do governo federal. No Portal da
        Transparência, acesse Despesas, depois Pagamentos, e filtre pelo
        órgão. Verifique o tempo médio entre a emissão da nota de empenho
        e o pagamento efetivo nos últimos 12 meses.
      </p>

      <h3>O que são restos a pagar e por que são um indicador de risco?</h3>
      <p>
        Restos a pagar são despesas empenhadas em um exercício financeiro
        que não foram pagas até 31 de dezembro. Dividem-se em processados
        (serviço prestado, aguardando pagamento) e não processados (ainda
        em execução). Um volume alto de restos a pagar processados indica
        que o órgão tem dívidas reconhecidas sem recursos para pagar,
        sinalizando risco de atraso para novos contratos. Em 2024, os
        restos a pagar do governo federal totalizaram R$ 232,4 bilhões.
      </p>

      <h3>Órgãos federais pagam mais rápido que estaduais e municipais?</h3>
      <p>
        Em geral, sim. Órgãos federais operam com o Tesouro Nacional como
        fonte pagadora, o que garante maior previsibilidade. O prazo médio
        de pagamento em órgãos federais é de 30 a 45 dias. Em órgãos
        estaduais, varia de 45 a 90 dias dependendo da saúde fiscal do
        estado. Em municípios, a variação é maior: de 30 dias em municípios
        superavitários a mais de 180 dias em municípios com dificuldades
        fiscais.
      </p>

      <h3>É possível incluir cláusula de correção monetária no contrato para compensar atrasos?</h3>
      <p>
        Sim. A Lei 14.133/2021 (Nova Lei de Licitações) prevê em seu
        artigo 92, inciso V, a obrigatoriedade de cláusula de atualização
        financeira em contratos. Além disso, o artigo 137 permite a
        suspensão do contrato pelo fornecedor em caso de atraso superior
        a 2 meses nos pagamentos devidos pela Administração. Na prática,
        porém, acionar essas cláusulas gera desgaste na relação com o
        órgão e pode prejudicar a empresa em futuras licitações.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
