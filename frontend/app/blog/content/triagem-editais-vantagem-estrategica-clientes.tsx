import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-263 CONS-07: Triagem de Editais como Vantagem Estratégica para Clientes
 *
 * Content cluster: inteligência em licitações para consultorias
 * Target: 2,000-2,500 words | Primary KW: triagem de editais como serviço
 */
export default function TriagemEditaisVantagemEstrategicaClientes() {
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
                name: 'Qual a diferença entre triagem operacional e curadoria de editais como serviço?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A triagem operacional é uma atividade interna de filtragem — a consultoria descarta editais irrelevantes antes de repassar os restantes ao cliente. A curadoria como serviço transforma essa filtragem em um entregável estruturado: cada edital recomendado vem acompanhado de score de viabilidade, justificativa de aderência setorial e análise de risco. A triagem é custo; a curadoria é receita.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto uma consultoria pode cobrar por um serviço de curadoria de editais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os modelos mais praticados são: fee fixo mensal entre R$ 2.000 e R$ 8.000 dependendo do número de setores e UFs monitorados; fee por edital qualificado entre R$ 150 e R$ 400 por oportunidade entregue com relatório completo; ou modelo híbrido com fee mensal base mais bônus por contrato adjudicado a partir de editais recomendados. O valor percebido pelo cliente depende diretamente da qualidade da justificativa e do score de viabilidade.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que deve conter um relatório de curadoria de editais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Um relatório de curadoria profissional deve conter: resumo executivo com número de editais monitorados versus recomendados; ficha individual por edital com objeto, valor, modalidade, prazo e órgão; score de viabilidade com detalhamento dos 4 fatores (modalidade, timeline, valor, geografia); justificativa de aderência setorial; e recomendação clara — disputar, monitorar ou descartar. Consultorias que adicionam análise de concorrência estimada e histórico do órgão elevam ainda mais o valor percebido.',
                },
              },
              {
                '@type': 'Question',
                name: 'A triagem automatizada por IA substitui o trabalho da consultoria?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não substitui — potencializa. A automação executa a camada de filtragem mecânica (classificação setorial, filtro geográfico, verificação de faixa de valor) em segundos. A consultoria agrega valor na camada estratégica: interpretação do contexto do cliente, análise de cláusulas restritivas, avaliação de concorrência e recomendação personalizada. A IA é o motor; a consultoria é o piloto.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como demonstrar ao cliente o valor da curadoria de editais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A métrica mais eficaz é o tempo economizado traduzido em valor financeiro. Se o cliente gastava 30 horas/mês triando editais com um analista de R$ 10.000/mês, a triagem interna custava R$ 1.700/mês. Ao receber uma curadoria que elimina essa atividade e ainda melhora a taxa de vitória, o ROI é demonstrável. Consultorias que rastreiam a taxa de conversão dos editais recomendados (propostas enviadas que resultam em contrato) constroem evidência quantitativa de valor.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: triagem de editais como serviço */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A maioria das consultorias de licitação trata a <strong>triagem de
        editais como serviço</strong> implícito — algo que acontece nos
        bastidores, sem visibilidade para o cliente e sem remuneração direta.
        O analista acessa os portais, filtra publicações, descarta as
        irrelevantes e encaminha as restantes. Essa atividade consome entre 20
        e 40 horas mensais por cliente atendido, mas raramente aparece como
        item de entrega no contrato. O resultado é previsível: a consultoria
        absorve um custo operacional significativo sem capturar valor
        proporcional. Este artigo propõe uma inversão de perspectiva —
        transformar a triagem em curadoria, reposicionando-a como o serviço de
        maior valor percebido da consultoria.
      </p>

      {/* Section 1 */}
      <h2>Triagem como custo versus triagem como serviço</h2>

      <p>
        A distinção é estrutural, não semântica. Quando a triagem é tratada
        como custo, ela opera como pré-requisito invisível para outras
        entregas. A consultoria seleciona editais internamente e apresenta ao
        cliente uma lista de &ldquo;oportunidades identificadas&rdquo; sem
        detalhar o processo de filtragem, os critérios aplicados ou a razão
        pela qual determinados editais foram incluídos e outros excluídos. O
        cliente recebe uma lista — não um serviço.
      </p>

      <p>
        Quando a triagem é reposicionada como curadoria, ela se torna o
        produto principal. O cliente não recebe uma lista genérica; recebe um
        relatório estruturado onde cada edital recomendado vem acompanhado de
        score de viabilidade, justificativa de aderência setorial, análise de
        risco e recomendação explícita. A diferença entre &ldquo;encontramos 12
        editais para você esta semana&rdquo; e &ldquo;dos 340 editais
        publicados no seu setor, identificamos 12 com viabilidade acima de 70%
        — aqui está a análise de cada um&rdquo; é a diferença entre
        commodity e serviço premium.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência — Valor percebido em serviços de consultoria B2B
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Pesquisa Source Information Services (2024):</strong> 73%
            dos tomadores de decisão B2B afirmam que o valor de uma consultoria
            está na curadoria e recomendação, não na quantidade de informação
            entregue. Relatórios com recomendação explícita têm 2,4x mais
            chance de gerar renovação de contrato.
          </li>
          <li>
            <strong>Precificação de consultoria B2B no Brasil (IBCO, 2024):</strong>{' '}
            Serviços de inteligência de mercado com entregáveis estruturados
            são precificados entre R$ 3.000 e R$ 15.000/mês, enquanto
            serviços de monitoramento sem análise ficam na faixa de R$ 500 a
            R$ 2.000/mês — uma diferença de 3x a 7x.
          </li>
          <li>
            <strong>Retenção de clientes (Bain &amp; Company, 2023):</strong>{' '}
            Consultorias que entregam insights acionáveis (não apenas dados)
            têm taxa de retenção de 85% contra 52% de consultorias que
            entregam apenas informação bruta.
          </li>
        </ul>
      </div>

      {/* Section 2 */}
      <h2>O que o cliente realmente quer: não editais, mas recomendações</h2>

      <p>
        O cliente da consultoria de licitação não precisa de mais editais. Ele
        precisa de menos — mas melhores. O problema de informação em
        licitações públicas não é escassez; é excesso. O PNCP publica em
        média 3.200 processos por dia útil. Para uma empresa que atua em dois
        ou três setores e monitora meia dúzia de UFs, o volume semanal de
        publicações potencialmente relevantes pode ultrapassar 400. A questão
        operacional não é &ldquo;onde encontrar editais&rdquo;, mas
        &ldquo;quais editais merecem atenção&rdquo;.
      </p>

      <p>
        A consultoria que entende essa dinâmica reposiciona seu valor. Em vez
        de ser a intermediária que acessa portais em nome do cliente, ela se
        torna a curadoria que traduz volume em decisão. O entregável deixa de
        ser &ldquo;lista de editais&rdquo; e passa a ser &ldquo;recomendação
        fundamentada de oportunidades&rdquo;. Essa mudança é particularmente
        relevante porque, como demonstrado em{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao" className="text-brand-navy dark:text-brand-blue hover:underline">
          como saber se vale a pena disputar um pregão
        </Link>, a decisão de participar ou não de um certame envolve múltiplos
        fatores que o cliente raramente consegue avaliar com rigor sozinho.
      </p>

      {/* Section 3 */}
      <h2>O framework de recomendação: triagem + score + justificativa</h2>

      <p>
        A curadoria profissional de editais se estrutura em três camadas
        complementares. A primeira camada é a triagem mecânica — filtragem
        por setor, UF, valor e modalidade que elimina editais estruturalmente
        incompatíveis. A segunda camada é a pontuação de viabilidade — um
        score numérico que avalia cada edital sobrevivente em fatores
        objetivos. A terceira camada é a justificativa consultiva — a análise
        qualitativa que contextualiza o score para o perfil específico do
        cliente.
      </p>

      <h3>Camada 1: Triagem mecânica</h3>
      <p>
        Esta camada elimina aproximadamente 85% do volume total de
        publicações. Os critérios são binários: o edital pertence ao setor do
        cliente? A UF é compatível com a estratégia geográfica? O valor
        estimado está dentro da faixa de atuação? A modalidade é adequada ao
        perfil competitivo? Editais que falham em qualquer desses critérios
        são descartados sem análise adicional. Esta é a camada que mais se
        beneficia de automação — ferramentas com classificação setorial por
        IA executam essa filtragem em segundos, liberando o consultor para as
        camadas de maior valor agregado.
      </p>

      <h3>Camada 2: Score de viabilidade</h3>
      <p>
        Os editais que sobrevivem à triagem mecânica recebem uma pontuação de
        viabilidade baseada em quatro fatores ponderados: modalidade (30%),
        timeline (25%), valor (25%) e geografia (20%). O score resulta em uma
        nota de 0 a 100 que permite ordenar editais por probabilidade de
        retorno. Editais com score acima de 70 são candidatos prioritários;
        entre 50 e 70, merecem avaliação condicional; abaixo de 50, devem ser
        descartados salvo circunstância excepcional.
      </p>

      <h3>Camada 3: Justificativa consultiva</h3>
      <p>
        É nesta camada que a consultoria agrega valor insubstituível. O score
        numérico é contextualizado para o perfil do cliente: &ldquo;Este
        pregão tem score 78, mas o órgão tem histórico de atrasos de
        pagamento — recomendamos participar com margem de segurança
        adicional&rdquo; ou &ldquo;Score 65, porém o objeto é estratégico para
        o portfólio de atestados do cliente — recomendamos disputar como
        investimento de qualificação&rdquo;. A justificativa transforma dados
        em conselho.
      </p>

      <BlogInlineCTA slug="triagem-editais-vantagem-estrategica-clientes" campaign="consultorias" />

      {/* Section 4 */}
      <h2>Como apresentar a triagem como entregável premium</h2>

      <p>
        A apresentação é tão importante quanto o conteúdo. Um relatório de
        curadoria mal formatado em planilha Excel transmite a mesma mensagem
        que uma lista genérica — independentemente da qualidade da análise
        por trás dele. A embalagem do entregável precisa comunicar
        profissionalismo e rigor analítico.
      </p>

      <p>
        Os elementos essenciais de um relatório de curadoria são: resumo
        executivo com métricas de funil (editais monitorados, filtrados,
        recomendados); ficha individual por edital com dados estruturados;
        score de viabilidade com barra visual de cada fator; recomendação
        explícita (disputar / monitorar / descartar); e tendências do período
        (volume por setor, distribuição geográfica, variação de valores).
        Consultorias que incluem análise comparativa entre períodos demonstram
        evolução e reforçam o valor contínuo do serviço.
      </p>

      <p>
        Ferramentas como o SmartLic geram automaticamente os scores de
        viabilidade e a classificação setorial, fornecendo a base quantitativa
        que a consultoria complementa com a camada interpretativa. Para
        aprofundar como a análise de editais se converte em diferencial
        competitivo para a consultoria, veja{' '}
        <Link href="/blog/analise-edital-diferencial-competitivo-consultoria" className="text-brand-navy dark:text-brand-blue hover:underline">
          como transformar a análise de editais em diferencial competitivo
        </Link>.
      </p>

      {/* Section 5 */}
      <h2>Precificação: quanto cobrar pela curadoria</h2>

      <p>
        A precificação da curadoria de editais como serviço depende de três
        variáveis: escopo de monitoramento (número de setores e UFs), nível
        de profundidade analítica e modelo de cobrança. Os três modelos mais
        praticados no mercado brasileiro de consultoria em licitações são:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Framework de precificação — Curadoria de editais como serviço
        </p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li>
            <strong>Modelo 1 — Fee mensal fixo:</strong> R$ 2.000 a
            R$ 8.000/mês por cliente, dependendo do número de setores
            monitorados (1 a 3) e UFs cobertas (3 a 10). Inclui relatório
            semanal de curadoria com score e justificativa. Vantagem:
            previsibilidade de receita. Risco: desalinhamento entre esforço e
            resultado.
          </li>
          <li>
            <strong>Modelo 2 — Fee por edital qualificado:</strong> R$ 150
            a R$ 400 por oportunidade entregue com relatório completo de
            viabilidade. O cliente paga apenas por editais que atendem ao
            critério mínimo de score. Vantagem: alinhamento entre valor
            entregue e valor cobrado. Risco: receita variável mês a mês.
          </li>
          <li>
            <strong>Modelo 3 — Híbrido com success fee:</strong> Fee mensal
            base (R$ 1.500 a R$ 3.000) mais bônus de 1% a 3% sobre o valor
            de contratos adjudicados a partir de editais recomendados pela
            curadoria. Vantagem: incentiva qualidade da recomendação e
            alinha interesses. Risco: complexidade contratual e
            rastreabilidade.
          </li>
          <li className="pt-2 font-semibold">
            Referência de margem: consultorias que operam com ferramentas de
            automação na triagem mecânica reportam custo operacional de
            R$ 300 a R$ 800 por cliente/mês para a camada de curadoria,
            permitindo margens de 60% a 75% nos modelos de fee fixo
            (IBCO, Pesquisa de Rentabilidade em Consultoria, 2024).
          </li>
        </ul>
      </div>

      <p>
        A escolha do modelo depende do perfil do cliente e do posicionamento
        da consultoria. Clientes de maior porte que valorizam previsibilidade
        tendem a preferir o fee fixo. Clientes menores, que estão testando a
        consultoria, respondem melhor ao modelo por edital qualificado. O
        modelo híbrido funciona melhor em relações de longo prazo onde há
        confiança mútua.
      </p>

      {/* Section 6 */}
      <h2>Template de relatório de curadoria</h2>

      <p>
        O relatório de curadoria é o artefato tangível do serviço. A estrutura
        abaixo serve como modelo adaptável para consultorias que desejam
        padronizar a entrega.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Estrutura de relatório semanal de curadoria
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>1. Resumo executivo:</strong> Editais monitorados no
            período (ex.: 287), editais que passaram na triagem setorial
            (ex.: 43), editais com score de viabilidade acima de 60 (ex.: 11),
            editais recomendados com justificativa (ex.: 7).
          </li>
          <li>
            <strong>2. Ficha por edital recomendado:</strong> Número do
            processo | Órgão | UF | Objeto (resumo) | Valor estimado |
            Modalidade | Data de abertura | Score de viabilidade (0-100) |
            Detalhamento dos 4 fatores | Recomendação (disputar / monitorar /
            descartar).
          </li>
          <li>
            <strong>3. Justificativa consultiva:</strong> Contextualização do
            score para o perfil do cliente — experiência prévia com o órgão,
            compatibilidade de atestados, análise de concorrência estimada,
            observações sobre cláusulas relevantes.
          </li>
          <li>
            <strong>4. Radar de tendências:</strong> Variação de volume por
            setor no período, novos órgãos publicando no segmento, tendência
            de valores estimados, oportunidades de ata de registro de preços
            em formação.
          </li>
          <li>
            <strong>5. Métricas de desempenho:</strong> Taxa de conversão
            acumulada (editais recomendados que resultaram em proposta e
            contrato), comparativo com períodos anteriores, ROI demonstrável
            da curadoria.
          </li>
        </ul>
      </div>

      <p>
        Para consultorias que buscam transformar esse modelo em serviço
        recorrente com diagnóstico de eficiência, o conceito de{' '}
        <Link href="/blog/diagnostico-eficiencia-licitacao-servico-premium" className="text-brand-navy dark:text-brand-blue hover:underline">
          diagnóstico de eficiência em licitação como serviço premium
        </Link>{' '}
        complementa a curadoria com uma camada analítica de melhoria contínua.
      </p>

      <h2>Da triagem operacional à receita recorrente</h2>

      <p>
        O reposicionamento da triagem como curadoria não é apenas uma mudança
        de nomenclatura. É uma mudança de modelo de negócio. A consultoria
        que vende &ldquo;assessoria em licitação&rdquo; como pacote genérico
        compete por preço. A consultoria que vende curadoria de editais com
        score de viabilidade, justificativa consultiva e métricas de
        desempenho compete por valor. A primeira escala adicionando analistas;
        a segunda escala adicionando tecnologia na camada mecânica e
        reservando horas humanas para a camada estratégica.
      </p>

      <p>
        O percurso é claro: automatizar a camada de triagem mecânica com
        ferramentas de classificação setorial e viabilidade, investir a
        capacidade humana na camada de justificativa e recomendação, e
        formalizar o entregável como serviço precificado de forma
        independente. O resultado é uma consultoria com custo operacional
        controlado, receita recorrente previsível e valor percebido
        demonstrável pelo cliente.
      </p>

      {/* CTA Section — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Gere scores de viabilidade automaticamente para seus clientes
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic classifica editais por setor com IA e calcula viabilidade
          em 4 fatores. Use os scores como base para seus relatórios de
          curadoria e escale sua consultoria sem escalar equipe.
        </p>
        <Link
          href="/signup?source=blog&article=triagem-editais-vantagem-estrategica-clientes&utm_source=blog&utm_medium=cta&utm_content=triagem-editais-vantagem-estrategica-clientes&utm_campaign=consultorias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">
            página de recursos
          </Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Qual a diferença entre triagem operacional e curadoria de editais como serviço?</h3>
      <p>
        A triagem operacional é uma atividade interna de filtragem — a
        consultoria descarta editais irrelevantes antes de repassar os
        restantes ao cliente. A curadoria como serviço transforma essa
        filtragem em um entregável estruturado: cada edital recomendado vem
        acompanhado de score de viabilidade, justificativa de aderência
        setorial e análise de risco. A triagem é custo absorvido; a curadoria
        é receita faturada.
      </p>

      <h3>Quanto uma consultoria pode cobrar por um serviço de curadoria de editais?</h3>
      <p>
        Os modelos mais praticados são: fee fixo mensal entre R$ 2.000 e
        R$ 8.000 dependendo do número de setores e UFs monitorados; fee por
        edital qualificado entre R$ 150 e R$ 400 por oportunidade entregue
        com relatório completo; ou modelo híbrido com fee mensal base mais
        bônus por contrato adjudicado a partir de editais recomendados. O
        valor percebido pelo cliente depende diretamente da qualidade da
        justificativa e do score de viabilidade apresentado.
      </p>

      <h3>O que deve conter um relatório de curadoria de editais?</h3>
      <p>
        Um relatório profissional deve conter: resumo executivo com métricas
        de funil (editais monitorados versus recomendados), ficha individual
        por edital com objeto, valor, modalidade, prazo e órgão, score de
        viabilidade com detalhamento dos quatro fatores, justificativa de
        aderência setorial e recomendação clara — disputar, monitorar ou
        descartar. Consultorias que adicionam análise de concorrência
        estimada e histórico do órgão elevam significativamente o valor
        percebido.
      </p>

      <h3>A triagem automatizada por IA substitui o trabalho da consultoria?</h3>
      <p>
        Não substitui — potencializa. A automação executa a camada de
        filtragem mecânica (classificação setorial, filtro geográfico,
        verificação de faixa de valor) em segundos. A consultoria agrega valor
        na camada estratégica: interpretação do contexto do cliente, análise
        de cláusulas restritivas, avaliação de concorrência e recomendação
        personalizada. A IA é o motor de processamento; a consultoria é a
        inteligência de aplicação.
      </p>

      <h3>Como demonstrar ao cliente o valor da curadoria de editais?</h3>
      <p>
        A métrica mais eficaz é o tempo economizado traduzido em valor
        financeiro. Se o cliente gastava 30 horas por mês triando editais com
        um analista de R$ 10.000/mês, a triagem interna custava cerca de
        R$ 1.700/mês. Ao receber uma curadoria que elimina essa atividade e
        melhora a taxa de vitória, o ROI é demonstrável. Consultorias que
        rastreiam a taxa de conversão dos editais recomendados — propostas
        enviadas que resultam em contrato — constroem evidência quantitativa
        irrefutável de valor.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
