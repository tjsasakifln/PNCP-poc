import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-263 CONS-02: Análise de Edital como Diferencial Competitivo da Consultoria
 *
 * Content cluster: inteligência em licitações para consultorias
 * Target: 2,500-3,000 words | Primary KW: diferencial consultoria licitação
 */
export default function AnaliseEditalDiferencialCompetitivoConsultoria() {
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
                name: 'Quais são os níveis de maturidade de uma consultoria de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Consultorias de licitação podem ser classificadas em três níveis de maturidade. Nível 1 (Operacional): busca editais em portais e repassa listas filtradas por palavra-chave, cobrando entre R$ 800 e R$ 2.000/mês. Nível 2 (Analítico): além da busca, aplica triagem com critérios de viabilidade e entrega relatórios de aderência, cobrando entre R$ 2.500 e R$ 5.000/mês. Nível 3 (Estratégico): oferece curadoria de oportunidades com análise de viabilidade, recomendação de priorização, acompanhamento de resultado e inteligência setorial, cobrando entre R$ 5.000 e R$ 15.000/mês dependendo do porte do cliente.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como diferenciar uma consultoria de licitação da concorrência?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A diferenciação se constrói em três eixos: profundidade da análise (ir além da busca e entregar viabilidade e recomendação), tangibilidade da entrega (relatórios com métricas de resultado, não apenas listas de editais) e especialização setorial (dominar 2 a 4 setores em profundidade, acumulando conhecimento de preços, órgãos e concorrentes). Consultorias que operam nos três eixos conseguem cobrar 3 a 5 vezes mais que concorrentes operacionais e apresentam taxas de retenção 2 a 3 vezes superiores.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto uma consultoria de licitação pode cobrar por análise de viabilidade?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A análise de viabilidade, quando integrada ao serviço recorrente da consultoria, permite elevar o ticket médio em 40% a 80%. Consultorias de Nível 2 que adicionam viabilidade estruturada ao pacote tipicamente cobram entre R$ 2.500 e R$ 5.000/mês. Quando a viabilidade é vendida como serviço avulso por edital, o preço praticado varia entre R$ 150 e R$ 500 por análise, dependendo da complexidade do objeto e da modalidade da licitação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a diferença entre busca de editais e curadoria de oportunidades?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Busca de editais é uma atividade operacional: localizar licitações em portais públicos usando palavras-chave e filtros básicos. Curadoria de oportunidades é uma atividade estratégica: selecionar, analisar e recomendar as licitações que oferecem a melhor relação entre probabilidade de vitória e retorno para o cliente específico. A curadoria exige conhecimento do perfil do cliente, análise de viabilidade em múltiplos fatores e julgamento sobre priorização. É um serviço que o cliente dificilmente replica internamente.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como migrar uma consultoria de licitação do modelo operacional para o estratégico?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A migração deve ser feita em fases. Fase 1 (mês 1-2): adotar ferramenta de busca multi-fonte com classificação setorial para eliminar triagem manual e liberar tempo da equipe. Fase 2 (mês 2-3): implementar análise de viabilidade padronizada com critérios objetivos (modalidade, prazo, valor, geografia) e passar a entregar relatórios com métricas de aderência. Fase 3 (mês 3-6): adicionar recomendação estratégica para clientes premium, incluindo contexto de mercado, histórico do órgão e sugestão de priorização. A receita adicional das fases 2 e 3 tipicamente cobre o investimento em ferramentas da fase 1 em 45 a 60 dias.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O <strong>diferencial de uma consultoria de licitação</strong> raramente
        está na capacidade de encontrar editais. Os portais são públicos, as
        ferramentas de busca estão cada vez mais acessíveis, e qualquer
        profissional com acesso ao PNCP consegue localizar licitações em
        minutos. O diferencial está no que a consultoria faz entre a busca
        e a recomendação — e é justamente esse espaço que a maioria das
        consultorias deixa vazio.
      </p>

      <p>
        Este artigo examina como a análise de editais pode ser transformada
        de commodity em diferencial competitivo, permitindo que consultorias
        reposicionem seu serviço, cobrem mais e retenham melhor. Não se
        trata de teoria de marketing, mas de um modelo operacional com
        três níveis claros de maturidade e faixas de precificação
        correspondentes.
      </p>

      <h2>O mercado de consultoria em licitação: cenário atual</h2>

      <p>
        O mercado brasileiro de licitações públicas movimentou mais de
        R$ 198 bilhões em 2024, segundo dados do Portal Nacional de
        Contratações Públicas (PNCP). Desse volume, uma parcela crescente
        passa por alguma forma de intermediação ou assessoria: consultorias
        que ajudam empresas a localizar, analisar e disputar editais.
      </p>

      <p>
        O mercado de consultoria em licitação, entretanto, é fragmentado e
        pouco diferenciado. A maior parte das consultorias opera no modelo
        que chamaremos de &ldquo;busca e repasse&rdquo;: localizam editais
        em portais públicos, filtram por palavras-chave do setor do cliente
        e enviam listas periódicas. Esse serviço, embora útil, é
        estruturalmente vulnerável à comoditização.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: mercado de consultoria em licitação</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; <strong>Volume de licitações:</strong> O PNCP registrou mais de 287 mil licitações
            publicadas em 2024, com valor estimado total de R$ 198 bilhões. Esse volume representa
            um crescimento de 12% em relação a 2023, impulsionado pela consolidação da Nova Lei de
            Licitações (14.133/2021) como regime predominante (Fonte: PNCP, Painel Estatístico, 2024).
          </li>
          <li>
            &bull; <strong>Fragmentação do mercado:</strong> Não existem dados oficiais sobre o
            número de consultorias de licitação no Brasil, mas estimativas setoriais apontam entre
            3.000 e 5.000 consultorias ativas, incluindo profissionais autônomos, microempresas e
            escritórios especializados. A grande maioria (estimados 70% a 80%) opera no modelo
            &ldquo;busca e repasse&rdquo; com ticket médio inferior a R$ 2.000/mês
            (Fonte: estimativas de mercado, SEBRAE e associações setoriais, 2023-2024).
          </li>
          <li>
            &bull; <strong>Disposição de pagamento:</strong> Pesquisa do SEBRAE com empresas
            fornecedoras do governo indica que 68% das empresas que contratam assessoria em
            licitação estariam dispostas a pagar mais por um serviço que incluísse análise de
            viabilidade e recomendação de priorização, além da busca básica
            (Fonte: SEBRAE, Pesquisa Fornecedores Governamentais, 2023).
          </li>
        </ul>
      </div>

      <p>
        O dado sobre disposição de pagamento é revelador. Existe demanda
        latente por um serviço mais sofisticado — os clientes querem mais
        do que estão recebendo. A oportunidade para consultorias que
        conseguem entregar análise, e não apenas busca, é concreta e
        quantificável.
      </p>

      <h2>O serviço commodity: buscar e listar editais</h2>

      <p>
        O serviço de busca e listagem de editais é a base sobre a qual a
        maioria das consultorias opera. O processo típico é: o consultor
        acessa diariamente os portais públicos (PNCP, ComprasGov, Portal de
        Compras Públicas, portais estaduais), busca por palavras-chave
        relacionadas ao setor do cliente, filtra por UF e faixa de valor,
        e compila uma lista que é enviada por e-mail ou plataforma.
      </p>

      <p>
        Esse serviço tem dois problemas estruturais. O primeiro é a
        replicabilidade: qualquer concorrente com acesso aos mesmos portais
        pode entregar a mesma lista. O segundo é a transferência de
        trabalho: a lista de editais, por si só, não reduz o trabalho do
        cliente — apenas muda o local de busca. Em vez de buscar no portal,
        o cliente busca na lista da consultoria. A triagem, a análise de
        viabilidade e a decisão de participar continuam sendo
        responsabilidade do cliente.
      </p>

      <p>
        Quando o serviço é percebido como mera busca, a consequência é
        previsível: o cliente compara pelo preço. E em uma comparação de
        preço, a consultoria que cobra menos vence. Esse é o ciclo da
        comoditização que corrói margem e alimenta churn.
      </p>

      <h2>O serviço diferenciado: curadoria + viabilidade + recomendação</h2>

      <p>
        A alternativa à comoditização é subir na cadeia de valor. Em vez
        de entregar uma lista, entregar uma curadoria. Em vez de filtrar
        por palavra-chave, classificar por viabilidade. Em vez de deixar
        a decisão para o cliente, recomendar a priorização.
      </p>

      <p>
        A curadoria de oportunidades é um serviço qualitativamente
        diferente da busca de editais. Ela pressupõe conhecimento do perfil
        do cliente (setores, capacidade, histórico, geografia), critérios
        objetivos de viabilidade (modalidade, prazo, valor, concorrência) e
        julgamento estratégico (quais licitações priorizar dado os recursos
        limitados do cliente). Parte fundamental dessa curadoria é saber
        identificar as{' '}
        <Link href="/blog/clausulas-escondidas-editais-licitacao" className="text-brand-navy dark:text-brand-blue hover:underline">
          cláusulas escondidas em editais que eliminam fornecedores experientes
        </Link>{' '}
        antes de recomendar a participação.
      </p>

      <p>
        A análise de viabilidade, em particular, é o elemento que mais
        diferencia o serviço premium do básico. Como discutido no artigo
        sobre{' '}
        <Link href="/blog/consultorias-modernas-inteligência-priorizar-oportunidades" className="text-brand-navy dark:text-brand-blue hover:underline">
          como consultorias modernas usam inteligência para priorizar oportunidades
        </Link>,
        a viabilidade transforma a triagem de subjetiva em objetiva, de
        intuitiva em mensurável.
      </p>

      <h2>Os 3 níveis de maturidade da consultoria</h2>

      <p>
        Para estruturar a transição de commodity para diferencial, é útil
        pensar em três níveis de maturidade, cada um com entregáveis,
        competências e faixas de preço distintos.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Os 3 níveis de maturidade da consultoria de licitação</p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>Nível 1 — Operacional (busca e repasse):</strong> Entregáveis: lista de editais
            filtrada por palavras-chave e UF. Frequência: diária ou semanal. Competência: conhecimento
            de portais públicos. Ticket médio: R$ 800 a R$ 2.000/mês. Churn típico: 35% a 45% ao ano.
            Diferenciação: baixa (serviço facilmente replicável).
          </li>
          <li>
            <strong>Nível 2 — Analítico (triagem + viabilidade):</strong> Entregáveis: oportunidades
            triadas com score de viabilidade, relatório mensal de aderência e métricas de resultado.
            Frequência: semanal com alertas diários para alta viabilidade. Competência: critérios de
            viabilidade + ferramentas de classificação. Ticket médio: R$ 2.500 a R$ 5.000/mês. Churn
            típico: 18% a 25% ao ano. Diferenciação: média (exige metodologia e ferramentas).
          </li>
          <li>
            <strong>Nível 3 — Estratégico (curadoria + recomendação + acompanhamento):</strong>
            Entregáveis: curadoria de oportunidades com recomendação de priorização, análise de
            concorrência, contexto do órgão, acompanhamento de propostas e dashboard de resultado.
            Frequência: contínua com reuniões quinzenais de alinhamento. Competência: inteligência
            setorial + relacionamento + análise estratégica. Ticket médio: R$ 5.000 a R$ 15.000/mês.
            Churn típico: 8% a 15% ao ano. Diferenciação: alta (difícil de replicar sem experiência
            setorial).
          </li>
        </ul>
      </div>

      <p>
        A maioria das consultorias opera no Nível 1. As que se destacam
        operam no Nível 2 ou 3. A transição entre níveis não exige uma
        reformulação completa da operação — exige a adição de camadas
        de valor sobre a base existente.
      </p>

      <BlogInlineCTA slug="analise-edital-diferencial-competitivo-consultoria" campaign="consultorias" />

      <h3>O que muda em cada transição</h3>

      <p>
        A transição do Nível 1 para o Nível 2 é fundamentalmente
        metodológica. A consultoria precisa definir critérios objetivos de
        viabilidade (em vez de depender da intuição do consultor),
        implementar uma ferramenta que automatize a triagem (liberando tempo
        para análise) e criar um formato padrão de relatório que comunique
        métricas ao cliente.
      </p>

      <p>
        A transição do Nível 2 para o Nível 3 é fundamentalmente relacional
        e setorial. A consultoria precisa acumular conhecimento profundo
        sobre os setores dos seus clientes (preços históricos, concorrentes
        frequentes, padrões de órgãos contratantes), estabelecer rotinas de
        alinhamento estratégico com o cliente e ser capaz de emitir
        recomendações fundamentadas, não apenas dados.
      </p>

      <h2>Como migrar do nível 1 para o nível 3</h2>

      <p>
        A migração prática segue três fases com marcos claros de
        implementação.
      </p>

      <h3>Fase 1: automatizar a base (mês 1-2)</h3>

      <p>
        O primeiro passo é eliminar o tempo gasto com busca manual. Adotar
        uma ferramenta de busca multi-fonte com classificação setorial
        automatizada libera imediatamente de 2 a 4 horas por dia por
        consultor. Esse tempo liberado é o recurso que será investido
        nas fases seguintes.
      </p>

      <p>
        Nesta fase, a consultoria também padroniza o formato de entrega:
        em vez de listas brutas, passa a enviar oportunidades categorizadas
        por nível de aderência (alta, média, baixa) com justificativa breve
        para cada classificação.
      </p>

      <h3>Fase 2: implementar viabilidade (mês 2-3)</h3>

      <p>
        A segunda fase adiciona a análise de viabilidade estruturada. Para
        cada oportunidade, a consultoria aplica um scoring que considera
        modalidade, prazo, valor estimado e geografia. O resultado é uma
        classificação que o cliente entende imediatamente: alta viabilidade
        (priorizar), média viabilidade (avaliar) ou baixa viabilidade
        (declinar).
      </p>

      <p>
        Nesta fase, a consultoria cria o relatório mensal de valor com
        métricas: oportunidades apresentadas, taxa de aderência, economia
        de tempo estimada. Esse relatório é o principal instrumento de
        retenção, porque torna visível o valor que a consultoria entrega.
        A{' '}
        <Link href="/blog/triagem-editais-vantagem-estratégica-clientes" className="text-brand-navy dark:text-brand-blue hover:underline">
          triagem de editais como vantagem estratégica
        </Link>{' '}
        é o conceito central dessa fase.
      </p>

      <h3>Fase 3: adicionar recomendação estratégica (mês 3-6)</h3>

      <p>
        A terceira fase é a que mais diferencia a consultoria. Para
        clientes premium, a consultoria passa a entregar recomendações
        completas: resumo do objeto, pontos de atenção do edital, estimativa
        de concorrência, histórico de compras do órgão e sugestão explícita
        (disputar, monitorar ou declinar) com fundamentação.
      </p>

      <p>
        Essa fase exige investimento em inteligência setorial: construir e
        manter bases de dados sobre preços históricos, concorrentes
        frequentes e padrões dos órgãos contratantes nos setores dos
        clientes. O esforço é cumulativo — cada licitação analisada
        alimenta a base de conhecimento para as próximas.
      </p>

      <h2>Precificação: quanto vale a inteligência</h2>

      <p>
        A precificação é o reflexo direto da percepção de valor. Quando o
        serviço é busca de editais, o cliente compara com o custo de fazer
        ele mesmo (uma pessoa dedicando 2 horas/dia). Quando o serviço é
        inteligência de oportunidades, o cliente compara com o retorno
        gerado (contratos adjudicados a partir das recomendações).
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Faixas de precificação por nível de serviço</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; <strong>Nível 1 (Operacional):</strong> R$ 800 a R$ 2.000/mês. Margem líquida
            típica: 30% a 40%. Capacidade por consultor: 20 a 30 clientes. Receita por consultor:
            R$ 24.000 a R$ 48.000/mês. Este nível é viável para volume, mas vulnerável a churn
            e compressão de margem por concorrência de preço.
          </li>
          <li>
            &bull; <strong>Nível 2 (Analítico):</strong> R$ 2.500 a R$ 5.000/mês. Margem líquida
            típica: 45% a 55%. Capacidade por consultor: 12 a 18 clientes (maior dedicação por
            cliente). Receita por consultor: R$ 36.000 a R$ 72.000/mês. Viabilidade econômica
            superior ao Nível 1 apesar de atender menos clientes, porque o ticket e a retenção
            compensam.
          </li>
          <li>
            &bull; <strong>Nível 3 (Estratégico):</strong> R$ 5.000 a R$ 15.000/mês. Margem líquida
            típica: 50% a 65%. Capacidade por consultor: 6 a 10 clientes (alta dedicação). Receita
            por consultor: R$ 45.000 a R$ 120.000/mês. Este nível exige senioridade e conhecimento
            setorial, mas gera a maior rentabilidade e a menor taxa de churn. Fontes: benchmarks
            de precificação de serviços B2B especializados e consultorias de gestão, 2023-2024.
          </li>
        </ul>
      </div>

      <p>
        O ponto mais relevante desses dados é a receita por consultor. Um
        consultor de Nível 3 pode gerar até 2,5 vezes mais receita do que
        um de Nível 1, atendendo menos clientes com maior margem. Isso
        significa que a migração de nível não apenas melhora a retenção —
        melhora a economia da operação como um todo.
      </p>

      <h3>A lógica da precificação baseada em valor</h3>

      <p>
        A precificação dos Níveis 2 e 3 deve ser justificada em termos de
        retorno para o cliente, não em termos de custo para a consultoria.
        Um cliente que paga R$ 5.000/mês por uma consultoria de Nível 2 e
        adjudica R$ 200.000 em contratos por trimestre a partir das
        recomendações tem um custo de aquisição de contrato de 7,5% — muito
        inferior ao custo de manter uma equipe interna de licitação.
      </p>

      <p>
        Essa lógica de precificação exige que a consultoria meça e comunique
        resultados. O relatório mensal de valor não é um diferencial
        cosmético — é o instrumento que sustenta a precificação premium.
      </p>

      <h2>Posicionamento de marca: linguagem e entregáveis</h2>

      <p>
        A transição de nível não é apenas operacional — é também de
        posicionamento. A forma como a consultoria se apresenta,
        os termos que usa e os entregáveis que destaca determinam a
        percepção do mercado sobre seu serviço.
      </p>

      <h3>Linguagem de Nível 1 versus Nível 3</h3>

      <p>
        Uma consultoria de Nível 1 tipicamente se posiciona com termos como
        &ldquo;monitoramento de editais&rdquo;, &ldquo;busca de
        licitações&rdquo; e &ldquo;alerta de oportunidades&rdquo;. Esses
        termos descrevem uma atividade operacional — e o cliente interpreta
        como tal.
      </p>

      <p>
        Uma consultoria de Nível 3 se posiciona com termos como
        &ldquo;inteligência de oportunidades&rdquo;, &ldquo;curadoria
        estratégica&rdquo; e &ldquo;gestão de pipeline de licitações&rdquo;.
        Esses termos descrevem um serviço consultivo — e o cliente
        interpreta como investimento, não custo. O artigo sobre{' '}
        <Link href="/blog/diagnóstico-eficiência-licitação-serviço-premium" className="text-brand-navy dark:text-brand-blue hover:underline">
          diagnóstico de eficiência como serviço premium
        </Link>{' '}
        aprofunda como estruturar esse posicionamento em entregáveis concretos.
      </p>

      <h3>Entregáveis que comunicam valor</h3>

      <p>
        Os entregáveis devem refletir o nível de serviço. No Nível 1, o
        entregável é uma lista em Excel ou e-mail. No Nível 2, é um
        relatório com scoring de viabilidade e métricas de aderência. No
        Nível 3, é um dashboard com pipeline de oportunidades, histórico
        de recomendações e tracking de resultados.
      </p>

      <p>
        A forma do entregável importa quase tanto quanto o conteúdo. Um
        relatório bem formatado com métricas claras comunica profissionalismo
        e rigor metodológico. Uma lista em texto corrido no corpo do e-mail
        comunica improviso. O investimento em apresentação não é vaidade —
        é estratégia de retenção.
      </p>

      <h2>O papel da tecnologia na diferenciação</h2>

      <p>
        A tecnologia não cria diferenciação por si só, mas é o habilitador
        que torna a diferenciação escalável. Uma consultoria pode entregar
        serviço de Nível 3 para 3 clientes sem nenhuma ferramenta, apenas
        com dedicação e experiência. Mas não consegue entregar Nível 2 para
        15 clientes sem automatizar a triagem e a classificação setorial.
      </p>

      <p>
        Ferramentas de inteligência em licitações que oferecem busca
        multi-fonte, classificação setorial automatizada e análise de
        viabilidade permitem que a consultoria opere no Nível 2 com a mesma
        equipe que antes operava no Nível 1. A diferença de custo
        operacional é o investimento na ferramenta; a diferença de receita
        é o delta entre os tickets dos dois níveis.
      </p>

      <p>
        O{' '}
        <Link href="/planos" className="text-brand-navy dark:text-brand-blue hover:underline">
          SmartLic
        </Link>{' '}
        foi projetado para esse cenário: busca multi-fonte (PNCP, Portal
        de Compras Públicas, ComprasGov), classificação por IA em 15 setores
        e análise de viabilidade em 4 fatores. A consultoria usa a plataforma
        como motor de triagem e dedica o tempo da equipe à análise e
        recomendação — as camadas que justificam o preço premium.
      </p>

      {/* CTA Section — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Ofereça viabilidade automatizada como parte do seu serviço premium
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Classifique oportunidades por setor e viabilidade em minutos. Sua
          equipe foca na recomendação estratégica — o diferencial que o
          cliente não encontra em nenhum outro lugar.
        </p>
        <Link
          href="/signup?source=blog&article=analise-edital-diferencial-competitivo-consultoria&utm_source=blog&utm_medium=cta&utm_content=analise-edital-diferencial-competitivo-consultoria&utm_campaign=consultorias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">página de recursos</Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Quais são os níveis de maturidade de uma consultoria de licitação?</h3>
      <p>
        Consultorias de licitação podem ser classificadas em três níveis de
        maturidade. Nível 1 (Operacional): busca editais em portais e
        repassa listas filtradas por palavra-chave, cobrando entre R$ 800
        e R$ 2.000/mês. Nível 2 (Analítico): além da busca, aplica triagem
        com critérios de viabilidade e entrega relatórios de aderência,
        cobrando entre R$ 2.500 e R$ 5.000/mês. Nível 3 (Estratégico):
        oferece curadoria de oportunidades com análise de viabilidade,
        recomendação de priorização, acompanhamento de resultado e
        inteligência setorial, cobrando entre R$ 5.000 e R$ 15.000/mês
        dependendo do porte do cliente.
      </p>

      <h3>Como diferenciar uma consultoria de licitação da concorrência?</h3>
      <p>
        A diferenciação se constrói em três eixos: profundidade da análise
        (ir além da busca e entregar viabilidade e recomendação),
        tangibilidade da entrega (relatórios com métricas de resultado,
        não apenas listas de editais) e especialização setorial (dominar
        2 a 4 setores em profundidade, acumulando conhecimento de preços,
        órgãos e concorrentes). Consultorias que operam nos três eixos
        conseguem cobrar 3 a 5 vezes mais que concorrentes operacionais e
        apresentam taxas de retenção 2 a 3 vezes superiores.
      </p>

      <h3>Quanto uma consultoria de licitação pode cobrar por análise de viabilidade?</h3>
      <p>
        A análise de viabilidade, quando integrada ao serviço recorrente da
        consultoria, permite elevar o ticket médio em 40% a 80%.
        Consultorias de Nível 2 que adicionam viabilidade estruturada ao
        pacote tipicamente cobram entre R$ 2.500 e R$ 5.000/mês. Quando a
        viabilidade é vendida como serviço avulso por edital, o preço
        praticado varia entre R$ 150 e R$ 500 por análise, dependendo da
        complexidade do objeto e da modalidade da licitação.
      </p>

      <h3>Qual a diferença entre busca de editais e curadoria de oportunidades?</h3>
      <p>
        Busca de editais é uma atividade operacional: localizar licitações
        em portais públicos usando palavras-chave e filtros básicos.
        Curadoria de oportunidades é uma atividade estratégica: selecionar,
        analisar e recomendar as licitações que oferecem a melhor relação
        entre probabilidade de vitória e retorno para o cliente específico.
        A curadoria exige conhecimento do perfil do cliente, análise de
        viabilidade em múltiplos fatores e julgamento sobre priorização.
        É um serviço que o cliente dificilmente replica internamente.
      </p>

      <h3>Como migrar uma consultoria de licitação do modelo operacional para o estratégico?</h3>
      <p>
        A migração deve ser feita em fases. Fase 1 (mês 1-2): adotar
        ferramenta de busca multi-fonte com classificação setorial para
        eliminar triagem manual e liberar tempo da equipe. Fase 2 (mês 2-3):
        implementar análise de viabilidade padronizada com critérios
        objetivos (modalidade, prazo, valor, geografia) e passar a entregar
        relatórios com métricas de aderência. Fase 3 (mês 3-6): adicionar
        recomendação estratégica para clientes premium, incluindo contexto
        de mercado, histórico do órgão e sugestão de priorização. A receita
        adicional das fases 2 e 3 tipicamente cobre o investimento em
        ferramentas da fase 1 em 45 a 60 dias.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
