import Link from 'next/link';

/**
 * STORY-262 B2G-01: Como Aumentar sua Taxa de Vitoria em Licitacoes
 *
 * Content cluster: inteligencia em licitacoes para empresas B2G
 * Target: 2,500-3,000 words | Primary KW: taxa de vitoria em licitacoes
 */
export default function ComoAumentarTaxaVitoriaLicitacoes() {
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
                name: 'Qual a taxa de vitória média em licitações públicas no Brasil?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A taxa média de adjudicação de empresas que participam regularmente de licitações públicas gira entre 8% e 15%, segundo dados consolidados do Painel de Compras do Governo Federal. Empresas com processos estruturados de triagem atingem taxas entre 25% e 35%.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é triagem por viabilidade em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Triagem por viabilidade é um processo de avaliação prévia de editais com base em critérios objetivos — modalidade, prazo, valor estimado e localização geográfica — que permite identificar, antes de investir tempo na análise completa, quais oportunidades têm maior probabilidade de retorno para o perfil da empresa.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quantas licitações por mês uma empresa deve disputar para ser rentável?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não existe um número fixo. A rentabilidade depende da taxa de conversão, não do volume. Uma empresa que disputa 8 licitações por mês com taxa de 30% de adjudicação gera mais contratos do que outra que disputa 30 com taxa de 8%. O indicador correto é o ROI por proposta, não o volume absoluto.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como calcular o custo real de participar de uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo real inclui horas de análise do edital (4-12h), elaboração da proposta técnica e comercial (8-40h), documentação de habilitação (2-6h), custos de certidões e garantias, além do custo de oportunidade. Para uma empresa de médio porte, o custo total por licitação varia entre R$ 3.000 e R$ 15.000, dependendo da complexidade.',
                },
              },
              {
                '@type': 'Question',
                name: 'Ferramentas de inteligência em licitações realmente aumentam a taxa de vitória?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, quando utilizadas para filtrar oportunidades antes da decisão de participar. O benefício principal não é encontrar mais licitações, mas descartar as inviáveis antes de investir recursos. Ferramentas que combinam classificação setorial com análise de viabilidade permitem que a equipe concentre esforço nas oportunidades com melhor encaixe para o perfil da empresa.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: taxa de vitoria em licitacoes */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A maioria das empresas que participa de licitações públicas no Brasil
        opera com <strong>taxas de vitória entre 8% e 15%</strong>. Isso
        significa que, para cada dez propostas elaboradas, no máximo uma ou
        duas resultam em contrato efetivo. O custo acumulado dessa ineficiência
        ao longo de um ano frequentemente supera o valor de um contrato inteiro.
        Este artigo apresenta um modelo estruturado para aumentar a taxa de
        vitória em licitações sem expandir a equipe -- concentrando o esforço
        nas oportunidades certas, em vez de distribuí-lo em todas as
        disponíveis.
      </p>

      {/* Section 1 */}
      <h2>O paradoxo da licitação: participar mais nem sempre significa ganhar mais</h2>

      <p>
        Existe uma premissa intuitiva, mas incorreta, que orienta a estratégia
        de muitas empresas B2G: quanto mais licitações disputar, maior o
        faturamento com o governo. A lógica parece simples -- mais tentativas,
        mais chances. Na prática, os dados mostram o oposto.
      </p>

      <p>
        O Painel de Compras do Governo Federal registrou, em 2024, mais de
        240.000 processos de contratação publicados somente na esfera federal.
        Somando estados e municípios no PNCP, esse número ultrapassa 800.000
        publicações anuais. Uma empresa de médio porte em um setor específico
        pode encontrar entre 50 e 300 oportunidades relevantes por mês,
        dependendo do segmento e da abrangência geográfica.
      </p>

      <p>
        Disputar todas seria inviável operacionalmente. Mas o problema real não
        é a quantidade -- é a <strong>falta de critério na seleção</strong>. Quando
        a triagem é baseada apenas em leitura superficial do objeto e do valor,
        a empresa acaba investindo tempo em editais onde não tem vantagem
        competitiva, onde o prazo é insuficiente para mobilização, ou onde a
        modalidade favorece concorrentes com perfil diferente.
      </p>

      <p>
        O resultado é previsível: muitas propostas elaboradas, poucas
        adjudicações, equipe sobrecarregada, e a percepção equivocada de que
        o mercado está mais competitivo do que realmente está.
      </p>

      {/* Section 2 */}
      <h2>Diagnóstico: qual a taxa de adjudicação saudável</h2>

      <p>
        Antes de buscar melhoria, é necessário estabelecer uma referência.
        A taxa de adjudicação -- percentual de licitações disputadas que
        resultam em contrato -- varia significativamente por modalidade e
        setor.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência -- Taxa de adjudicação por modalidade
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Pregão Eletrônico:</strong> taxa média de adjudicação entre
            10% e 18% para empresas que participam sem triagem estruturada.
            Empresas com triagem por viabilidade atingem 25% a 35%
            (Fonte: Painel de Compras do Governo Federal, dados agregados 2023-2024).
          </li>
          <li>
            <strong>Concorrência:</strong> taxa média de 15% a 22%, refletindo
            o menor número de concorrentes e a maior complexidade técnica
            (Fonte: Relatórios de gestão do TCU, exercício 2023).
          </li>
          <li>
            <strong>Dispensa de licitação:</strong> taxa de conversão mais alta
            (30% a 50%), mas volumes menores e valores unitários mais baixos
            (Fonte: PNCP, consolidação de dispensas Lei 14.133/2021, art. 75).
          </li>
          <li>
            <strong>Volume mensal no PNCP:</strong> o Portal Nacional de
            Contratações Públicas registra entre 60.000 e 90.000 publicações
            por mês, incluindo todas as modalidades e esferas federativas
            (Fonte: PNCP, painel de estatísticas, dados de 2024-2025).
          </li>
        </ul>
      </div>

      <p>
        Se sua empresa opera com taxa abaixo de 15% em pregão eletrônico,
        o problema provavelmente não está na qualidade das propostas -- está
        na seleção dos editais que decide disputar. Empresas com taxas acima de
        25% não são necessariamente melhores em precificação; elas são melhores
        em <strong>decidir quais licitações não disputar</strong>.
      </p>

      {/* Section 3 */}
      <h2>Os 3 filtros que separam oportunidade de ruído</h2>

      <p>
        A transição de uma estratégia de volume para uma estratégia de
        inteligência passa por três camadas de filtragem, aplicadas antes da
        decisão de elaborar proposta.
      </p>

      <h3>Filtro 1: Relevância setorial</h3>

      <p>
        O primeiro filtro é binário: o objeto da licitação está ou não está
        dentro do segmento de atuação da empresa. Parece óbvio, mas na
        prática, objetos genéricos como &ldquo;contratação de serviços de
        tecnologia da informação&rdquo; podem englobar desde desenvolvimento de
        software até manutenção de impressoras. A classificação setorial
        precisa ir além do título e analisar a descrição completa do objeto,
        identificando palavras-chave específicas e excluindo termos que indicam
        segmentos diferentes.
      </p>

      <h3>Filtro 2: Encaixe operacional</h3>

      <p>
        Mesmo dentro do setor correto, nem toda licitação é operacionalmente
        viável. Este filtro avalia se a empresa consegue atender aos
        requisitos de prazo, localização e capacidade. Uma empresa sediada em
        São Paulo pode ter margem competitiva em editais de Minas Gerais, mas
        dificilmente será competitiva em um pregão presencial no Amapá com
        prazo de mobilização de cinco dias.
      </p>

      <h3>Filtro 3: Viabilidade econômica</h3>

      <p>
        O terceiro filtro avalia se o valor estimado da contratação está
        dentro da faixa operacional da empresa. Disputar licitações cujo valor
        estimado está muito abaixo do custo de mobilização ou muito acima da
        capacidade de execução é desperdiçar recursos. A viabilidade econômica
        considera a faixa de valor onde a empresa historicamente tem melhor
        competitividade.
      </p>

      <p>
        Esses três filtros, aplicados de forma consistente, eliminam em média
        60% a 75% dos editais antes que qualquer analista gaste tempo com
        leitura detalhada. Para entender como avaliar cada critério em detalhe,
        veja{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao" className="text-brand-navy dark:text-brand-blue hover:underline">
          como saber se vale a pena disputar um pregão antes de investir horas na análise
        </Link>.
      </p>

      {/* Section 4 */}
      <h2>Como funciona a triagem por viabilidade: os 4 fatores</h2>

      <p>
        Um modelo estruturado de triagem vai além de filtros binários. A
        análise de viabilidade combina quatro fatores com pesos diferentes,
        gerando uma pontuação que permite comparar oportunidades e priorizar
        as que merecem análise completa.
      </p>

      <h3>Fator 1: Modalidade (peso 30%)</h3>

      <p>
        Cada modalidade de licitação tem características que favorecem perfis
        específicos de empresa. Pregão eletrônico favorece quem tem agilidade
        na fase de lances e documentação padronizada. Concorrência favorece
        quem tem capacidade técnica diferenciada. Diálogo competitivo favorece
        quem oferece soluções inovadoras. Uma empresa de engenharia com
        portfólio técnico robusto pode ter vantagem em concorrências, mas
        desvantagem em pregões de menor preço onde a competição se reduz a
        centavos.
      </p>

      <h3>Fator 2: Timeline (peso 25%)</h3>

      <p>
        O prazo entre a publicação do edital e a data de abertura das propostas
        determina se a empresa consegue preparar uma proposta competitiva.
        Adicionalmente, o prazo de execução contratual precisa ser compatível
        com a capacidade operacional. Licitações com prazos comprimidos
        favorecem empresas que já possuem documentação atualizada e equipe
        disponível.
      </p>

      <h3>Fator 3: Valor estimado (peso 25%)</h3>

      <p>
        A faixa de valor ideal varia por setor. Uma empresa de uniformes que
        opera entre R$ 100.000 e R$ 500.000 não deveria investir tempo em
        editais de R$ 2 milhões que exigem atestados de capacidade técnica
        proporcionais, nem em editais de R$ 10.000 cuja margem não cobre o
        custo de elaboração da proposta.
      </p>

      <h3>Fator 4: Geografia (peso 20%)</h3>

      <p>
        O custo de deslocamento e a logística de execução impactam diretamente
        a margem. Para serviços, a proximidade é crítica. Para fornecimento de
        bens, o custo de frete pode viabilizar ou inviabilizar a operação.
        Editais com execução na mesma região da empresa ou em regiões com
        estrutura logística favorável recebem pontuação maior.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático -- Cálculo de viabilidade
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          Empresa de TI em Curitiba avalia um pregão eletrônico para
          fornecimento de software em Florianópolis, valor estimado de
          R$ 280.000, prazo de 15 dias para proposta:
        </p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>Modalidade (30%):</strong> Pregão eletrônico, boa
            compatibilidade com perfil da empresa = 8/10 x 0,30 = 2,40
          </li>
          <li>
            <strong>Timeline (25%):</strong> 15 dias para proposta, prazo
            adequado = 7/10 x 0,25 = 1,75
          </li>
          <li>
            <strong>Valor (25%):</strong> R$ 280.000 dentro da faixa ideal
            (R$ 100k-500k) = 9/10 x 0,25 = 2,25
          </li>
          <li>
            <strong>Geografia (20%):</strong> Florianópolis, mesma região sul,
            logística viável = 7/10 x 0,20 = 1,40
          </li>
          <li className="pt-2 font-semibold">
            Pontuação total: 7,80/10 -- Viabilidade alta, recomendado prosseguir
            com análise completa.
          </li>
        </ul>
      </div>

      {/* Section 5 */}
      <h2>Estudo de caso: empresa de TI que foi de 12% para 28% de taxa de adjudicação</h2>

      <p>
        Uma empresa de software de gestão com sede no Paraná e atuação em seis
        estados do Sul e Sudeste enfrentava uma situação típica: equipe de três
        analistas dedicados a licitações, volume de 25 a 30 propostas
        elaboradas por mês, e taxa de adjudicação de 12%. O faturamento com
        contratos públicos era de aproximadamente R$ 3,2 milhões anuais, mas o
        custo operacional do setor de licitações -- salários, certidões, viagens
        para vistoria -- consumia R$ 680.000 por ano.
      </p>

      <p>
        O diagnóstico revelou que 65% das propostas elaboradas eram para
        editais com baixa viabilidade: valor fora da faixa ideal, prazo
        insuficiente para customização, ou localização que exigia deslocamento
        sem retorno proporcional. A equipe estava ocupada, mas não produtiva.
      </p>

      <p>
        A mudança envolveu três etapas ao longo de seis meses:
      </p>

      <p>
        <strong>Mês 1-2:</strong> Implementação de critérios de triagem
        formais. Antes de iniciar qualquer proposta, o edital passava por uma
        avaliação estruturada de viabilidade com os quatro fatores descritos
        acima. Editais com pontuação abaixo de 5,5/10 eram descartados sem
        análise detalhada.
      </p>

      <p>
        <strong>Mês 3-4:</strong> Adoção de ferramenta de inteligência em
        licitações para automatizar a triagem inicial. A classificação setorial
        por IA reduziu o tempo de identificação de oportunidades de 3 horas
        para 40 minutos por dia. Os analistas passaram a receber editais já
        pré-filtrados por setor e viabilidade.
      </p>

      <p>
        <strong>Mês 5-6:</strong> Refinamento dos critérios com base nos
        resultados. A empresa identificou que editais com valor entre
        R$ 150.000 e R$ 400.000 em modalidade pregão eletrônico nos estados do
        PR, SC e SP concentravam 80% das suas adjudicações. O foco foi
        redirecionado para essa faixa.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Resultados após 6 meses
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Volume de propostas:</strong> reduzido de 28/mês para
            14/mês (-50%)
          </li>
          <li>
            <strong>Taxa de adjudicação:</strong> de 12% para 28% (+133%)
          </li>
          <li>
            <strong>Contratos mensais:</strong> de 3,4 para 3,9 contratos/mês
            (+15%)
          </li>
          <li>
            <strong>Faturamento anual:</strong> de R$ 3,2M para R$ 4,1M (+28%)
          </li>
          <li>
            <strong>Custo operacional:</strong> de R$ 680.000 para R$ 520.000
            (-24%)
          </li>
          <li>
            <strong>ROI por proposta:</strong> de R$ 9.500 para R$ 24.400
            (+157%)
          </li>
        </ul>
      </div>

      <p>
        O ponto central é que a empresa ganhou mais contratos elaborando menos
        propostas. A equipe não cresceu; a inteligência na seleção é que
        aumentou. O tempo liberado pela eliminação de editais de baixa
        viabilidade foi redistribuído para a qualidade das propostas nos editais
        viáveis -- o que por sua vez alimentou a melhoria da taxa.
      </p>

      {/* Section 6 */}
      <h2>Passo a passo para implementar na sua empresa</h2>

      <p>
        A transição de um modelo de volume para um modelo de inteligência pode
        ser implementada em etapas, sem interrupção das operações correntes.
      </p>

      <h3>Etapa 1: Levante seus números atuais</h3>

      <p>
        Calcule, para os últimos 12 meses: quantas propostas foram elaboradas,
        quantas resultaram em adjudicação, qual o custo médio por proposta
        (horas x custo-hora + custos diretos), e qual o valor médio dos
        contratos obtidos. Esses números são a linha de base para medir
        evolução.
      </p>

      <h3>Etapa 2: Defina seus critérios de viabilidade</h3>

      <p>
        Com base no histórico de adjudicações, identifique os padrões das
        licitações que a empresa venceu: faixas de valor, modalidades,
        regiões, prazos. Esses padrões formam o perfil de oportunidade ideal.
        Editais que se afastam significativamente desse perfil devem ser
        descartados na triagem.
      </p>

      <h3>Etapa 3: Implemente a triagem antes da análise</h3>

      <p>
        Crie uma etapa formal no processo: antes de qualquer analista começar a
        ler um edital, o mesmo passa por avaliação de viabilidade. Se a
        pontuação for inferior ao limiar definido (recomendação inicial:
        5,5/10), o edital é descartado. Essa decisão deve ser registrada para
        análise posterior.
      </p>

      <h3>Etapa 4: Automatize a descoberta e classificação</h3>

      <p>
        A triagem manual de portais como PNCP, ComprasGov e Portal de Compras
        Públicas consome horas diárias. Ferramentas de inteligência em
        licitações automatizam a descoberta e classificação setorial,
        entregando à equipe apenas os editais que passaram pelo primeiro filtro
        de relevância. Para entender como reduzir esse tempo operacional,
        consulte{' '}
        <Link href="/blog/reduzir-tempo-analisando-editais-irrelevantes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como reduzir em 50% o tempo gasto analisando editais irrelevantes
        </Link>.
      </p>

      <h3>Etapa 5: Meça e refine mensalmente</h3>

      <p>
        Acompanhe a taxa de adjudicação, o custo por proposta e o ROI por
        contrato mês a mês. Ajuste os critérios de viabilidade conforme os
        resultados. A tendência esperada é de estabilização em 3 a 4 meses,
        com taxa de adjudicação entre 20% e 35% dependendo do setor e da
        concorrência.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Custo médio de elaboração de proposta por setor
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Tecnologia da Informação:</strong> R$ 4.500 a R$ 12.000
            por proposta (inclui análise técnica, precificação, documentação)
          </li>
          <li>
            <strong>Engenharia e Obras:</strong> R$ 8.000 a R$ 25.000
            por proposta (inclui orçamento, cronograma, visita técnica)
          </li>
          <li>
            <strong>Fornecimento de bens (materiais, uniformes):</strong> R$ 2.000 a R$ 6.000
            por proposta (cotações, logística, documentação)
          </li>
          <li className="pt-2 text-xs">
            Fonte: estimativas setoriais baseadas em pesquisa da ABES (Associação
            Brasileira de Empresas de Software) e CBIC (Câmara Brasileira da
            Indústria da Construção), 2023-2024.
          </li>
        </ul>
      </div>

      <p>
        A adoção de um modelo de triagem por viabilidade não exige
        investimento em infraestrutura ou contratação. Exige uma mudança de
        mentalidade: de &ldquo;precisamos participar de tudo&rdquo; para
        &ldquo;precisamos participar do que faz sentido&rdquo;. O resultado é
        uma equipe menos sobrecarregada, propostas de maior qualidade e uma
        taxa de vitória que justifica o investimento.
      </p>

      <p>
        Para uma análise detalhada de como empresas de alto desempenho em
        licitações operam, consulte{' '}
        <Link href="/blog/escolher-editais-maior-probabilidade-vitoria" className="text-brand-navy dark:text-brand-blue hover:underline">
          como escolher editais com maior probabilidade de vitória
        </Link>.
      </p>

      {/* CTA Section — STORY-262 AC18/AC19 — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Experimente a triagem inteligente do SmartLic -- 30 dias grátis
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic analisa cada edital com base em 4 fatores de viabilidade e
          classifica oportunidades por relevância setorial usando IA. Sua equipe
          recebe apenas os editais que merecem atenção.
        </p>
        <Link
          href="/signup?source=blog&article=como-aumentar-taxa-vitoria-licitacoes&utm_source=blog&utm_medium=article&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Comece Grátis
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">
            página de recursos
          </Link>.
        </p>
      </div>

      {/* FAQ Section — STORY-262 AC5 */}
      <h2>Perguntas Frequentes</h2>

      <h3>Qual a taxa de vitória média em licitações públicas no Brasil?</h3>
      <p>
        A taxa média de adjudicação de empresas que participam regularmente de
        licitações públicas gira entre 8% e 15%, segundo dados consolidados do
        Painel de Compras do Governo Federal. Empresas com processos
        estruturados de triagem atingem taxas entre 25% e 35%. A variação
        depende do setor de atuação, das modalidades disputadas e da
        abrangência geográfica.
      </p>

      <h3>O que é triagem por viabilidade em licitações?</h3>
      <p>
        Triagem por viabilidade é um processo de avaliação prévia de editais
        com base em critérios objetivos -- modalidade, prazo, valor estimado e
        localização geográfica -- que permite identificar, antes de investir
        tempo na análise completa, quais oportunidades têm maior probabilidade
        de retorno para o perfil da empresa. Diferente de uma filtragem
        simples por setor, a triagem por viabilidade pondera múltiplos fatores
        com pesos calibrados.
      </p>

      <h3>Quantas licitações por mês uma empresa deve disputar para ser rentável?</h3>
      <p>
        Não existe um número fixo. A rentabilidade depende da taxa de
        conversão, não do volume. Uma empresa que disputa 8 licitações por mês
        com taxa de 30% de adjudicação gera mais contratos do que outra que
        disputa 30 com taxa de 8%. O indicador correto é o ROI por proposta,
        não o volume absoluto.
      </p>

      <h3>Como calcular o custo real de participar de uma licitação?</h3>
      <p>
        O custo real inclui horas de análise do edital (4 a 12 horas),
        elaboração da proposta técnica e comercial (8 a 40 horas),
        documentação de habilitação (2 a 6 horas), custos de certidões e
        garantias, além do custo de oportunidade. Para uma empresa de médio
        porte, o custo total por licitação varia entre R$ 3.000 e R$ 15.000,
        dependendo da complexidade do objeto e da modalidade.
      </p>

      <h3>Ferramentas de inteligência em licitações realmente aumentam a taxa de vitória?</h3>
      <p>
        Sim, quando utilizadas para filtrar oportunidades antes da decisão de
        participar. O benefício principal não é encontrar mais licitações, mas
        descartar as inviáveis antes de investir recursos. Ferramentas que
        combinam classificação setorial com análise de viabilidade permitem que
        a equipe concentre esforço nas oportunidades com melhor encaixe para o
        perfil da empresa, elevando a taxa de adjudicação de forma consistente.
      </p>
    </>
  );
}
