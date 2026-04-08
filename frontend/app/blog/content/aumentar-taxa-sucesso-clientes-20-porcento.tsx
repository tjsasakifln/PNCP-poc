import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-263 CONS-14: Aumentar Taxa de Sucesso dos Clientes em 20%
 *
 * Content cluster: inteligência em licitações para consultorias
 * Target: 2,500-3,000 words | Primary KW: aumentar taxa de vitória clientes
 */
export default function AumentarTaxaSucessoClientes20Porcento() {
  return (
    <>
      {/* FAQPage JSON-LD — STORY-263 AC5/AC11 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: [
              {
                '@type': 'Question',
                name: 'É realista prometer um aumento de 20% na taxa de adjudicação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, desde que a métrica seja contextualizada corretamente. O aumento de 20% é relativo, não absoluto: uma empresa que adjudica 15% das propostas enviadas pode atingir 18% (aumento de 20% sobre a base). Esse incremento é consistente com benchmarks de melhoria operacional em processos B2G, onde a principal alavanca é a qualidade da seleção de editais, não o volume de participações. Estudos de eficiência em compras públicas indicam que empresas que implementam triagem estruturada com critérios de viabilidade aumentam a taxa de adjudicação entre 15% e 30% em 6 meses.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto tempo leva para implementar o framework de 5 etapas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O timeline de implementação recomendado é de 90 dias. No primeiro mês (dias 1-30), implementam-se as etapas 1 (triagem rigorosa) e 2 (análise de viabilidade), que geram impacto imediato na qualidade da seleção. No segundo mês (dias 31-60), implementa-se a etapa 3 (otimização da proposta comercial) e inicia-se a etapa 4 (monitoramento pós-envio). No terceiro mês (dias 61-90), ativa-se a etapa 5 (feedback loop com análise pós-pregão) e coleta-se a primeira rodada de dados comparativos. Os primeiros resultados mensuráveis aparecem entre o segundo e o terceiro mês.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como a triagem rigorosa aumenta a taxa de adjudicação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A triagem rigorosa aumenta a taxa de adjudicação por um mecanismo simples: ao eliminar editais de baixa viabilidade antes da elaboração da proposta, a empresa concentra recursos nos editais onde tem maior probabilidade de vencer. O efeito é matemático — se uma empresa envia 20 propostas por mês e vence 3 (taxa de 15%), ao filtrar as 8 piores oportunidades e concentrar esforço nas 12 melhores, pode vencer 3 ou 4 com propostas de maior qualidade (taxa de 25% a 33%). A triagem não aumenta o número absoluto de vitórias imediatamente, mas aumenta a taxa de conversão e reduz o custo por contrato conquistado.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o impacto financeiro de aumentar a taxa de adjudicação em 20%?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O impacto financeiro depende do ticket médio dos contratos. Para uma empresa que participa de 15 licitações por mês com ticket médio de R$ 200.000 e taxa de adjudicação de 15% (2,25 contratos/mês = R$ 450.000/mês), um aumento de 20% na taxa (de 15% para 18%) gera 0,45 contratos adicionais por mês, equivalente a R$ 90.000 em receita adicional mensal ou R$ 1.080.000 por ano. Para empresas com ticket médio maior, o impacto é proporcionalmente maior.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        <strong>Aumentar a taxa de vitória dos clientes</strong> é o
        indicador mais poderoso que uma consultoria de licitação pode
        apresentar. Não o número de editais encontrados, não o volume de
        propostas elaboradas, mas o percentual de licitações disputadas
        que resultam em contrato adjudicado. Quando a consultoria consegue
        demonstrar que seus clientes vencem 20% mais do que antes, o
        serviço deixa de ser um custo operacional e passa a ser um
        investimento com retorno mensurável.
      </p>

      <p>
        Este artigo apresenta um framework de 5 etapas para consultorias
        que querem mover a taxa de adjudicação dos seus clientes de forma
        consistente e documentável. Não se trata de uma promessa vaga --
        cada etapa tem impacto estimado, indicadores de acompanhamento e
        prazo de implementação. O framework é complementar às estratégias
        de{' '}
        <Link href="/blog/como-aumentar-taxa-vitoria-licitacoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          aumento da taxa de vitória em licitações
        </Link>{' '}
        aplicadas diretamente pelas empresas B2G, mas adaptado para o
        contexto de consultorias que prestam serviço a múltiplos clientes
        simultaneamente.
      </p>

      <h2>A promessa: +20% de taxa de adjudicação</h2>

      <p>
        Antes de detalhar o framework, é necessário contextualizar a
        métrica. O aumento de 20% é relativo, não absoluto. Uma empresa
        que hoje adjudica 15% das propostas enviadas pode atingir 18% --
        um incremento de 3 pontos percentuais, que representa 20% de
        melhoria sobre a base. Essa distinção é importante porque evita
        expectativas irrealistas e posiciona a promessa em território
        sustentável.
      </p>

      <p>
        A fundamentação para esse incremento vem de três fontes. Primeiro,
        benchmarks de eficiência em compras públicas compilados pelo TCU e
        pelo IPEA indicam que a qualidade da seleção de editais é o fator
        com maior influência sobre a taxa de adjudicação — acima da
        precificação e da qualidade da proposta técnica. Segundo, estudos
        de operações B2B mostram que a implementação de critérios
        estruturados de qualificação de oportunidades (pipeline
        qualification) melhora a taxa de conversão entre 15% e 30% em
        6 meses. Terceiro, a experiência prática do mercado de
        consultorias de licitação confirma que clientes que recebem
        recomendações baseadas em análise de viabilidade vencem mais do
        que clientes que recebem apenas listas de editais.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: taxa de adjudicação no mercado B2G brasileiro</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; <strong>Taxa média de adjudicação em pregões eletrônicos:</strong> Empresas B2G
            de médio porte que participam regularmente de pregões eletrônicos reportam taxas de
            adjudicação entre 12% e 22% sobre propostas enviadas. A mediana situa-se em torno de
            16% (Fonte: análise de dados do Painel de Compras do Governo Federal, 2023/2024).
          </li>
          <li>
            &bull; <strong>Impacto da triagem estruturada:</strong> Empresas que implementam
            critérios de seleção baseados em viabilidade (modalidade, valor, prazo, geografia)
            reportam aumento de 15% a 30% na taxa de adjudicação em 6 meses, comparadas com
            empresas que selecionam editais por palavra-chave apenas (Fonte: benchmarks de
            eficiência operacional B2G, adaptados de pesquisa TCU sobre custos de participação).
          </li>
          <li>
            &bull; <strong>Custo médio de uma proposta sem retorno:</strong> O custo de elaboração
            de uma proposta para pregão eletrônico de médio porte (R$ 100 mil a R$ 500 mil) é
            estimado entre R$ 1.200 e R$ 3.500, incluindo horas de equipe, documentação e
            garantias. Uma empresa que envia 15 propostas por mês e adjudica 2 gasta entre
            R$ 15.600 e R$ 45.500 em propostas não convertidas (Fonte: estimativas baseadas em
            pesquisa CNI sobre custos de compliance em licitações, 2023).
          </li>
        </ul>
      </div>

      <h2>Etapa 1: triagem rigorosa — filtrar para conquistar</h2>

      <p>
        A primeira etapa é, paradoxalmente, a mais contraintuitiva:
        recomendar ao cliente que participe de menos licitações. A maioria
        das empresas B2G opera com a mentalidade de volume --
        &ldquo;quanto mais propostas, mais chances de vencer&rdquo;. Essa
        lógica ignora que propostas têm custo e que participar de editais
        de baixa viabilidade consome recursos que poderiam ser investidos
        em oportunidades de alta probabilidade.
      </p>

      <p>
        A triagem rigorosa aplica 4 filtros de viabilidade antes de
        recomendar a participação: modalidade (peso 30% — pregão
        eletrônico favorece empresas de menor porte; concorrência
        favorece experiência técnica), timeline (25% — prazo entre
        publicação e sessão deve ser compatível com a capacidade de
        elaboração do cliente), valor estimado (25% — faixa de valor
        deve estar dentro da capacidade de entrega e margem mínima do
        cliente) e geografia (20% — capacidade logística de atender o
        órgão contratante).
      </p>

      <p>
        O impacto estimado da triagem rigorosa na taxa de adjudicação é
        de +5% a +8% sobre a base. Essa melhoria vem da concentração de
        esforço: em vez de diluir recursos em 20 propostas medianas, o
        cliente investe em 12 propostas de alta viabilidade, com mais
        tempo para detalhamento técnico e precificação competitiva.
      </p>

      <h2>Etapa 2: análise de viabilidade pré-proposta</h2>

      <p>
        A segunda etapa complementa a triagem com uma análise mais
        profunda dos editais que passaram pelo primeiro filtro. Enquanto a
        triagem avalia critérios objetivos (modalidade, valor, prazo,
        geografia), a análise de viabilidade avalia fatores qualitativos:
        complexidade do objeto, histórico de compras do órgão, nível de
        concorrência esperado e requisitos de habilitação.
      </p>

      <p>
        A análise de viabilidade pré-proposta responde a uma pergunta
        específica: &ldquo;dado que este edital passou na triagem, quais
        são os riscos específicos que podem comprometer o sucesso?&rdquo;
        Um edital pode ter modalidade favorável, valor dentro da faixa e
        prazo adequado, mas exigir atestado de capacidade técnica que o
        cliente não possui, ou ter objeto com especificação tão restritiva
        que favorece um fornecedor específico.
      </p>

      <p>
        O impacto estimado da análise de viabilidade na taxa de
        adjudicação é de +3% a +5% adicional. Combinada com a triagem
        da Etapa 1, o impacto acumulado é de +8% a +13% — já próximo da
        meta de 20%.
      </p>

      <BlogInlineCTA slug="aumentar-taxa-sucesso-clientes-20-porcento" campaign="consultorias" />

      <h2>Etapa 3: otimização da proposta comercial</h2>

      <p>
        A terceira etapa foca na qualidade da proposta em si. Com menos
        propostas para elaborar (resultado das Etapas 1 e 2), a equipe
        do cliente — ou a própria consultoria, se o escopo incluir
        elaboração — dispõe de mais tempo e atenção para cada proposta
        individual.
      </p>

      <p>
        A otimização da proposta comercial envolve três práticas: análise
        de preços de referência (verificar o preço estimado do edital, o
        histórico de preços em licitações similares do mesmo órgão e o
        preço praticado pelo mercado), revisão de requisitos de
        habilitação (garantir que toda a documentação está em
        conformidade, eliminando desclassificações por falha formal) e
        adequação da proposta técnica (quando aplicável — em
        concorrências e tomadas de preço, a proposta técnica pode ser
        decisiva).
      </p>

      <p>
        O impacto estimado da otimização de proposta é de +3% a +5% na
        taxa de adjudicação. A principal fonte desse ganho é a redução de
        desclassificações por falha formal ou preço inexequível — erros
        que são evitáveis com revisão estruturada e que, segundo dados do
        PNCP, respondem por 15% a 20% das eliminações em pregões
        eletrônicos.
      </p>

      <h2>Etapa 4: monitoramento pós-envio</h2>

      <p>
        A quarta etapa cobre um ponto cego de muitas operações B2G: o
        que acontece entre o envio da proposta e o resultado do certame.
        Empresas que enviam a proposta e simplesmente esperam o resultado
        perdem oportunidades de intervenção — impugnações, pedidos de
        esclarecimento, fases de lance e recursos.
      </p>

      <p>
        O monitoramento pós-envio inclui: acompanhamento do calendário
        do certame (sessão, fase de lances, habilitação), monitoramento
        de impugnações e esclarecimentos que possam alterar as condições
        do edital, preparação para fase de lances (em pregões
        eletrônicos, definir limites de desconto e estratégia de lance)
        e acompanhamento da fase de habilitação (estar preparado para
        apresentar documentação complementar se necessário).
      </p>

      <p>
        O impacto estimado do monitoramento pós-envio é de +2% a +4%.
        Embora menor que as etapas anteriores, esse incremento vem de
        oportunidades que seriam perdidas por omissão — propostas
        desclassificadas por não atender a esclarecimento, ou lances
        não otimizados por falta de acompanhamento.
      </p>

      <h2>Etapa 5: feedback loop — análise pós-pregão</h2>

      <p>
        A quinta etapa é a que garante a melhoria contínua do framework.
        Após cada resultado de licitação — vitória ou derrota — a
        consultoria realiza uma análise estruturada que alimenta as
        etapas anteriores com dados reais.
      </p>

      <p>
        A análise pós-pregão responde a 4 perguntas: (1) A triagem foi
        correta? O edital era realmente uma oportunidade de alta
        viabilidade? (2) A análise de viabilidade identificou os riscos
        relevantes? (3) A proposta comercial estava competitiva? Qual foi
        a diferença para o vencedor? (4) Houve algum fator não previsto
        que influenciou o resultado?
      </p>

      <p>
        Esse feedback é o que calibra o framework ao longo do tempo.
        Consultorias que mantêm uma base de dados de análises pós-pregão
        refinam progressivamente os critérios de triagem e viabilidade,
        tornando as recomendações mais precisas a cada ciclo. O impacto
        da Etapa 5 é indireto, mas cumulativo: ela melhora a eficácia
        das Etapas 1 a 4 em cada iteração. Consultorias que já utilizam{' '}
        <Link href="/blog/aumentar-retencao-clientes-inteligencia-editais" className="text-brand-navy dark:text-brand-blue hover:underline">
          inteligência em editais para aumentar a retenção
        </Link>{' '}
        reconhecem que o feedback loop é o que transforma dados em
        conhecimento acumulado.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Framework: impacto estimado de cada etapa na taxa de adjudicação</p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>Etapa 1 — Triagem rigorosa:</strong> +5% a +8% sobre a base. Principal
            alavanca: concentração de esforço em editais de alta viabilidade. Implementação:
            semanas 1-4.
          </li>
          <li>
            <strong>Etapa 2 — Análise de viabilidade:</strong> +3% a +5% adicional. Principal
            alavanca: eliminação de participações com riscos ocultos. Implementação: semanas 2-6.
          </li>
          <li>
            <strong>Etapa 3 — Otimização de proposta:</strong> +3% a +5% adicional. Principal
            alavanca: redução de desclassificações e precificação competitiva. Implementação:
            semanas 4-8.
          </li>
          <li>
            <strong>Etapa 4 — Monitoramento pós-envio:</strong> +2% a +4% adicional. Principal
            alavanca: captura de oportunidades perdidas por omissão. Implementação: semanas 6-10.
          </li>
          <li>
            <strong>Etapa 5 — Feedback loop:</strong> Melhoria contínua das etapas 1-4. Principal
            alavanca: calibração progressiva dos critérios com dados reais. Implementação:
            semanas 8-12 (ciclo contínuo).
          </li>
          <li>
            <strong>Impacto acumulado estimado:</strong> +13% a +22% sobre a base em 90 dias.
            A meta de +20% está no centro da faixa de estimativa e é consistente com benchmarks
            de melhoria operacional em processos B2G.
          </li>
        </ul>
      </div>

      <h2>A matemática: como 20% se traduz em receita adicional</h2>

      <p>
        Para uma consultoria que precisa justificar o investimento no
        framework, a tradução em receita é o argumento mais eficaz.
        Considere um cliente típico: participa de 15 licitações por mês,
        com ticket médio de R$ 200.000, e taxa de adjudicação atual de
        15%.
      </p>

      <p>
        No cenário atual, esse cliente adjudica 2,25 contratos por mês
        (15 x 15%), gerando R$ 450.000 em receita mensal de contratos
        públicos. Com o aumento de 20% na taxa (de 15% para 18%), o
        cliente passa a adjudicar 2,7 contratos por mês — 0,45 contratos
        adicionais, equivalentes a R$ 90.000 em receita mensal adicional.
        Em um ano, são R$ 1.080.000 em contratos que o cliente não teria
        conquistado sem a melhoria.
      </p>

      <p>
        Mesmo que a consultoria cobre R$ 4.000/mês pelo serviço, o ROI
        para o cliente é de 22,5x no primeiro ano (R$ 1.080.000 /
        R$ 48.000). Esse é o tipo de evidência que não apenas retém o
        cliente, mas justifica aumento de ticket. Para apresentar essa
        evidência de forma estruturada, vale consultar o artigo sobre{' '}
        <Link href="/blog/usar-dados-provar-eficiencia-licitacoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como usar dados para provar a eficiência em licitações
        </Link>.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Simulação de impacto financeiro por perfil de cliente</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; <strong>Perfil A — PME (10 propostas/mês, ticket R$ 80 mil, taxa 12%):</strong> Receita
            atual: R$ 96.000/mês. Com +20% na taxa (de 12% para 14,4%): R$ 115.200/mês.
            Ganho: R$ 19.200/mês ou R$ 230.400/ano.
          </li>
          <li>
            &bull; <strong>Perfil B — Média empresa (15 propostas/mês, ticket R$ 200 mil, taxa 16%):</strong> Receita
            atual: R$ 480.000/mês. Com +20% na taxa (de 16% para 19,2%): R$ 576.000/mês.
            Ganho: R$ 96.000/mês ou R$ 1.152.000/ano.
          </li>
          <li>
            &bull; <strong>Perfil C — Grande empresa (25 propostas/mês, ticket R$ 500 mil, taxa 18%):</strong> Receita
            atual: R$ 2.250.000/mês. Com +20% na taxa (de 18% para 21,6%): R$ 2.700.000/mês.
            Ganho: R$ 450.000/mês ou R$ 5.400.000/ano.
          </li>
        </ul>
      </div>

      <h2>Timeline de implementação: 90 dias</h2>

      <p>
        O framework de 5 etapas foi desenhado para implementação em 90
        dias, com entregas progressivas que geram resultado desde o
        primeiro mês. A sequência é importante porque cada etapa constrói
        sobre a anterior.
      </p>

      <p>
        <strong>Mês 1 (dias 1-30):</strong> Implementação das Etapas 1
        (triagem rigorosa) e 2 (análise de viabilidade). Essas duas etapas
        concentram o maior impacto individual (+8% a +13% sobre a base)
        e são as mais facilmente automatizáveis. A consultoria configura
        os critérios de triagem e viabilidade para cada cliente,
        calibrando os filtros com base no perfil de atuação (setores,
        UFs, faixas de valor, modalidades).
      </p>

      <p>
        <strong>Mês 2 (dias 31-60):</strong> Implementação da Etapa 3
        (otimização de proposta) e início da Etapa 4 (monitoramento
        pós-envio). Com a triagem mais rigorosa, o volume de propostas
        diminui e a qualidade de cada proposta individual pode ser
        elevada. A consultoria implementa checklists de revisão e
        processos de análise de preço de referência.
      </p>

      <p>
        <strong>Mês 3 (dias 61-90):</strong> Ativação da Etapa 5
        (feedback loop) e primeira coleta de dados comparativos. Ao final
        do terceiro mês, a consultoria já tem dados suficientes para
        comparar a taxa de adjudicação do período com a baseline — e
        apresentar ao cliente a evolução documentada.
      </p>

      {/* CTA Section — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Implemente as etapas 1 e 2 automaticamente com o SmartLic
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Triagem multi-fonte com classificação setorial por IA e análise de
          viabilidade em 4 fatores (modalidade, prazo, valor, geografia).
          Automatize as etapas que geram maior impacto na taxa de adjudicação.
        </p>
        <Link
          href="/signup?source=blog&article=aumentar-taxa-sucesso-clientes-20-porcento&utm_source=blog&utm_medium=cta&utm_content=aumentar-taxa-sucesso-clientes-20-porcento&utm_campaign=consultorias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/features" className="underline hover:text-ink">Veja todas as funcionalidades</Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>É realista prometer um aumento de 20% na taxa de adjudicação?</h3>
      <p>
        Sim, desde que a métrica seja contextualizada corretamente. O
        aumento de 20% é relativo, não absoluto: uma empresa que adjudica
        15% das propostas enviadas pode atingir 18% (aumento de 20% sobre
        a base). Esse incremento é consistente com benchmarks de melhoria
        operacional em processos B2G, onde a principal alavanca é a
        qualidade da seleção de editais, não o volume de participações.
        Estudos de eficiência em compras públicas indicam que empresas
        que implementam triagem estruturada com critérios de viabilidade
        aumentam a taxa de adjudicação entre 15% e 30% em 6 meses.
      </p>

      <h3>Quanto tempo leva para implementar o framework de 5 etapas?</h3>
      <p>
        O timeline de implementação recomendado é de 90 dias. No primeiro
        mês, implementam-se as etapas 1 (triagem rigorosa) e 2 (análise
        de viabilidade), que geram impacto imediato. No segundo mês,
        implementa-se a etapa 3 (otimização da proposta) e inicia-se a
        etapa 4 (monitoramento pós-envio). No terceiro mês, ativa-se a
        etapa 5 (feedback loop) e coleta-se a primeira rodada de dados
        comparativos. Os primeiros resultados mensuráveis aparecem entre
        o segundo e o terceiro mês.
      </p>

      <h3>Como a triagem rigorosa aumenta a taxa de adjudicação?</h3>
      <p>
        A triagem rigorosa aumenta a taxa de adjudicação ao eliminar
        editais de baixa viabilidade antes da elaboração da proposta. A
        empresa concentra recursos nos editais onde tem maior
        probabilidade de vencer. Se uma empresa envia 20 propostas por
        mês e vence 3 (taxa de 15%), ao filtrar as 8 piores oportunidades
        e concentrar esforço nas 12 melhores, pode vencer 3 ou 4 com
        propostas de maior qualidade (taxa de 25% a 33%). A triagem não
        aumenta o número absoluto de vitórias imediatamente, mas aumenta
        a taxa de conversão e reduz o custo por contrato conquistado.
      </p>

      <h3>Qual o impacto financeiro de aumentar a taxa de adjudicação em 20%?</h3>
      <p>
        O impacto depende do ticket médio dos contratos. Para uma empresa
        que participa de 15 licitações por mês com ticket médio de
        R$ 200.000 e taxa de adjudicação de 15%, um aumento de 20% na
        taxa (de 15% para 18%) gera 0,45 contratos adicionais por mês,
        equivalente a R$ 90.000 em receita adicional mensal ou
        R$ 1.080.000 por ano. Para empresas com ticket médio maior, o
        impacto é proporcionalmente maior. A chave é apresentar a
        projeção com os dados reais do cliente, não com médias genéricas.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
