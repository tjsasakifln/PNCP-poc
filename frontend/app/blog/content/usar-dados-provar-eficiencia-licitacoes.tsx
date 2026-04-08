import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-263 CONS-05: Como Usar Dados Para Provar Sua Eficiência ao Cliente
 *
 * Content cluster: inteligência em licitações para consultorias
 * Target: 2,500-3,000 words | Primary KW: KPIs consultoria licitação
 */
export default function UsarDadosProvarEficienciaLicitacoes() {
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
                name: 'Quais são os principais KPIs para uma consultoria de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os oito KPIs essenciais são: taxa de adjudicação (percentual de vitórias sobre participações), tempo médio de triagem (horas por edital analisado), taxa de descarte (percentual de editais descartados antes da proposta), valor total adjudicado (soma dos contratos vencidos no período), ROI do serviço (relação entre honorários pagos e valor adjudicado), tempo de resposta (dias entre publicação do edital e submissão da proposta), diversificação de órgãos (número de órgãos contratantes distintos) e taxa de reincidência (percentual de contratos recorrentes com o mesmo órgão).',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a taxa de adjudicação média de consultorias de licitação no Brasil?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não há uma pesquisa nacional consolidada, mas dados do Painel de Compras do Governo Federal e pesquisas setoriais do SEBRAE indicam que a taxa média de adjudicação de empresas B2G fica entre 8% e 12%. Consultorias que implementam seleção estratégica de editais com análise de viabilidade reportam taxas entre 18% e 30%. A diferença entre o percentil 25 e o percentil 75 é expressiva, indicando que a metodologia de seleção é o principal diferencial.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como calcular o ROI de uma consultoria de licitação para apresentar ao cliente?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O ROI da consultoria é calculado pela fórmula: (Valor Total Adjudicado - Custo Total do Serviço) / Custo Total do Serviço x 100. O custo total inclui honorários da consultoria, custos de proposta (certidões, garantias, horas internas do cliente) e custos de oportunidade. Para uma consultoria com honorário mensal de R$ 5.000 que gera R$ 200.000 em contratos adjudicados no trimestre, o ROI é de (200.000 - 15.000) / 15.000 x 100 = 1.233%. É importante apresentar o ROI acumulado trimestral ou semestral, não mensal, para suavizar a variabilidade natural do ciclo de licitações.',
                },
              },
              {
                '@type': 'Question',
                name: 'Com que frequência uma consultoria deve apresentar relatórios de performance ao cliente?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A recomendação é adotar três cadências: relatório semanal operacional (editais triados, propostas submetidas, status dos processos em andamento), relatório mensal tático (KPIs de performance, pipeline de oportunidades, análise de vitórias e derrotas) e relatório trimestral estratégico (ROI acumulado, evolução da taxa de adjudicação, recomendações de ajuste de setor ou região). O relatório trimestral é o mais crítico para retenção, pois é nele que o cliente avalia o retorno sobre o investimento na consultoria.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é taxa de descarte em licitações e por que é um KPI positivo?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Taxa de descarte é o percentual de editais identificados que foram deliberadamente não-disputados após análise de viabilidade. Ao contrário do que parece, uma taxa de descarte alta (60% a 80%) é um indicador positivo — significa que a consultoria está evitando que o cliente desperdice recursos em oportunidades de baixa probabilidade. Cada edital descartado com justificativa economiza entre R$ 800 e R$ 2.500 em custos de proposta. Uma consultoria que descarta 70% dos editais triados e recomenda apenas os 30% mais viáveis está gerando valor pela curadoria, não pelo volume.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A maioria das consultorias de licitação vende experiência. Anos de mercado, conhecimento
        dos portais, familiaridade com a legislação, relacionamento com órgãos. São diferenciais
        reais — mas intangíveis. Quando o cliente questiona se o serviço está gerando retorno,
        a resposta costuma ser qualitativa: &ldquo;estamos trabalhando bem&rdquo;, &ldquo;o mercado
        está competitivo&rdquo;, &ldquo;vamos ajustar a estratégia&rdquo;. Consultorias que dominam
        os <strong>KPIs de consultoria de licitação</strong> e os apresentam de forma estruturada
        não precisam justificar — demonstram. E consultorias que demonstram retorno retêm
        clientes por anos, não por meses.
      </p>

      <h2>O problema: consultorias vendem experiência sem métricas</h2>

      <p>
        O mercado de consultoria em licitações opera, em grande parte, na base da confiança
        pessoal. O consultor conhece o setor, entende os editais, sabe montar proposta.
        O cliente confia nessa competência e paga mensalmente — até que os resultados não
        aparecem. Sem métricas objetivas, a avaliação de performance fica subjetiva: o
        cliente &ldquo;sente&rdquo; que não está funcionando, e o consultor não tem dados para
        contestar ou confirmar essa percepção.
      </p>

      <p>
        Segundo pesquisa da Fundação Getúlio Vargas sobre maturidade de gestão em
        prestadores de serviços B2B (FGV, 2023), apenas 22% das consultorias de pequeno
        e médio porte no Brasil utilizam dashboards ou relatórios periódicos com KPIs
        para seus clientes. No segmento de licitações, esse percentual é ainda menor —
        estimado em 12% a 15%, dado que a maioria das consultorias opera com equipes
        de 1 a 5 pessoas e prioriza a execução operacional sobre a gestão de performance.
      </p>

      <p>
        O resultado é previsível: a taxa de churn (cancelamento) de consultorias de
        licitação sem reporting estruturado é de 35% a 45% ao ano, segundo dados de
        associações do setor. Consultorias com reporting trimestral apresentam churn
        de 15% a 20%. A correlação é direta: dados geram confiança, confiança gera
        retenção.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Impacto do reporting estruturado na retenção de clientes</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>12% a 15%:</strong> Percentual estimado de consultorias de licitação que utilizam KPIs estruturados (fonte: estimativa setorial baseada em pesquisa FGV 2023 sobre maturidade B2B)</li>
          <li><strong>35% a 45%:</strong> Taxa de churn anual de consultorias sem reporting periódico</li>
          <li><strong>15% a 20%:</strong> Taxa de churn anual de consultorias com reporting trimestral estruturado</li>
          <li><strong>22%:</strong> Percentual de consultorias B2B de pequeno porte que utilizam dashboards de KPIs (fonte: FGV, Pesquisa Maturidade Gestão B2B 2023)</li>
        </ul>
      </div>

      <h2>Por que dados importam para o cliente B2G</h2>

      <p>
        Empresas que participam de licitações são, por natureza, orientadas a processo.
        Elas operam com documentação formal, prazos rígidos e requisitos objetivos. O
        cliente B2G entende linguagem de dados — ele vive isso diariamente na relação
        com órgãos públicos. Quando a consultoria apresenta resultados em formato
        estruturado, com números comparáveis e tendências claras, ela fala a linguagem
        do cliente.
      </p>

      <p>
        Além disso, muitas empresas B2G de médio e grande porte têm conselhos ou
        diretorias que cobram retorno sobre investimentos em serviços terceirizados. O
        gestor do setor de licitações precisa justificar internamente o gasto com a
        consultoria. Se ele não recebe dados, precisa fabricar argumentos qualitativos
        — e isso fragiliza tanto a posição dele quanto a da consultoria. Fornecer
        dados é proteger o seu próprio contrato.
      </p>

      <BlogInlineCTA slug="usar-dados-provar-eficiencia-licitacoes" campaign="consultorias" />

      <h2>Os 8 KPIs essenciais para consultoria de licitação</h2>

      <p>
        Os KPIs a seguir foram organizados em ordem de importância para a demonstração
        de valor ao cliente. Cada um pode ser extraído de dados operacionais que a
        consultoria já possui (ou deveria possuir) — registros de participações,
        resultados, e histórico de editais analisados.
      </p>

      <h3>KPI 1: Taxa de adjudicação</h3>

      <p>
        A métrica mais direta de eficácia. Calculada como o número de licitações vencidas
        dividido pelo número de licitações disputadas, expressa em percentual. A média do
        mercado B2G fica entre 8% e 12% (fonte: Painel de Compras do Governo Federal, dados
        2023-2024). Uma consultoria competente deve posicionar seus clientes acima desse
        patamar — taxas entre 18% e 30% indicam seleção estratégica eficaz.
      </p>

      <p>
        Apresente esse KPI com contexto: &ldquo;Sua taxa de adjudicação neste trimestre foi
        de 24%, contra uma média de mercado de 10%. Isso significa que sua empresa vence
        2,4x mais que a média do setor.&rdquo; A comparação com benchmark transforma um
        número isolado em prova de valor. Para aprofundar como elevar essa métrica, veja
        o artigo sobre{' '}
        <Link href="/blog/aumentar-taxa-sucesso-clientes-20-porcento" className="text-brand-navy dark:text-brand-blue hover:underline">
          como aumentar a taxa de sucesso dos clientes em 20%
        </Link>{' '}
        e entenda por que{' '}
        <Link href="/blog/empresas-vencem-30-porcento-pregoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          empresas que vencem 30% dos pregões fazem isso diferente
        </Link>.
      </p>

      <h3>KPI 2: Tempo médio de triagem</h3>

      <p>
        Mede quantas horas a consultoria investe por edital analisado, desde a identificação
        até a recomendação de participar ou descartar. Uma triagem manual consome entre 45
        minutos e 2 horas por edital. Com ferramentas de classificação automatizada, esse
        tempo cai para 5 a 15 minutos por edital, concentrando o tempo humano na análise
        dos editais já pré-qualificados.
      </p>

      <p>
        Para o cliente, esse KPI demonstra eficiência operacional: &ldquo;Analisamos 142 editais
        este mês em uma média de 12 minutos cada, recomendando 23 para participação. Sem
        automação, essa triagem consumiria 213 horas da sua equipe.&rdquo;
      </p>

      <h3>KPI 3: Taxa de descarte</h3>

      <p>
        O percentual de editais identificados que foram deliberadamente não-disputados após
        análise de viabilidade. Contraintuitivamente, uma taxa de descarte alta é positiva —
        significa que a consultoria está evitando desperdício. Taxas entre 60% e 80% são
        típicas de consultorias com triagem estruturada.
      </p>

      <p>
        Apresente com a economia gerada: &ldquo;Descartamos 108 de 142 editais analisados
        (76% de taxa de descarte). Considerando um custo médio de R$ 1.200 por proposta,
        evitamos R$ 129.600 em investimentos de baixo retorno.&rdquo;
      </p>

      <h3>KPI 4: Valor total adjudicado</h3>

      <p>
        A soma dos valores dos contratos vencidos no período. É o KPI mais tangível para o
        cliente — o número que aparece no fluxo de caixa. Apresente em acumulado trimestral
        e com tendência: &ldquo;Valor adjudicado neste trimestre: R$ 847.000 (+32% vs.
        trimestre anterior).&rdquo;
      </p>

      <p>
        Dados do PNCP indicam que o valor médio de pregões eletrônicos adjudicados em 2024
        foi de R$ 185.000 para materiais e R$ 340.000 para serviços continuados. Use esses
        benchmarks para contextualizar o desempenho do cliente.
      </p>

      <h3>KPI 5: ROI do serviço</h3>

      <p>
        O retorno sobre o investimento do cliente na consultoria. Fórmula: (Valor Adjudicado
        - Custo Total) / Custo Total x 100, onde custo total inclui honorários da consultoria
        mais custos de proposta. Um ROI saudável para consultoria de licitação fica entre
        500% e 2.000% no acumulado semestral.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Modelo de cálculo de ROI — exemplo prático</p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li><strong>Honorário trimestral da consultoria:</strong> R$ 15.000 (R$ 5.000/mês)</li>
          <li><strong>Custos de proposta (12 participações x R$ 1.200):</strong> R$ 14.400</li>
          <li><strong>Custo total do período:</strong> R$ 29.400</li>
          <li><strong>Valor total adjudicado no trimestre:</strong> R$ 380.000 (3 contratos vencidos de 12 disputados)</li>
          <li><strong>ROI:</strong> (380.000 - 29.400) / 29.400 x 100 = <strong>1.193%</strong></li>
          <li><strong>Interpretação:</strong> Para cada R$ 1 investido na consultoria + propostas, o cliente recebeu R$ 12,93 em contratos</li>
        </ul>
      </div>

      <p>
        Apresente o ROI com a ressalva de que o valor adjudicado é receita bruta — a margem
        líquida do contrato depende da execução. Ainda assim, o ROI sobre receita gerada é
        uma métrica poderosa de justificativa.
      </p>

      <h3>KPI 6: Tempo de resposta</h3>

      <p>
        O número de dias entre a publicação do edital e a submissão da proposta pelo cliente.
        Prazos de publicação de pregões eletrônicos variam de 8 a 30 dias úteis, dependendo
        da modalidade e do valor. Um tempo de resposta abaixo de 60% do prazo disponível
        indica eficiência operacional; acima de 80% indica risco de atraso e pressão na
        qualidade da proposta.
      </p>

      <h3>KPI 7: Diversificação de órgãos</h3>

      <p>
        O número de órgãos contratantes distintos com os quais o cliente adjudicou contratos.
        A concentração em poucos órgãos cria risco de dependência. Um portfólio saudável para
        empresas de médio porte inclui contratos com pelo menos 4 a 6 órgãos distintos.
        Monitore e apresente a evolução trimestral.
      </p>

      <h3>KPI 8: Reincidência</h3>

      <p>
        O percentual de contratos adjudicados com órgãos que já contrataram o cliente
        anteriormente. Uma taxa de reincidência de 30% a 50% indica boa reputação junto
        aos órgãos contratantes — o cliente está sendo reconhecido pela qualidade da
        execução. Acima de 70% pode indicar excesso de dependência; abaixo de 15% sugere
        que a execução dos contratos anteriores pode não estar gerando renovação.
      </p>

      <h2>Como apresentar relatórios ao cliente</h2>

      <p>
        A apresentação é tão importante quanto os dados. Um relatório de KPIs mal formatado
        ou excessivamente técnico perde o impacto. A recomendação é adotar três cadências
        com escopos distintos.
      </p>

      <h3>Relatório semanal — operacional</h3>

      <p>
        Uma página, preferencialmente por email. Conteúdo: editais triados na semana,
        propostas submetidas, status dos processos em andamento (aguardando resultado,
        em fase de lances, em recurso). Objetivo: manter o cliente informado sem exigir
        reunião.
      </p>

      <h3>Relatório mensal — tático</h3>

      <p>
        Duas a três páginas com gráficos. Conteúdo: todos os 8 KPIs com evolução mensal,
        pipeline de oportunidades em andamento, análise de vitórias e derrotas do mês (o
        que funcionou, o que não funcionou, ajustes planejados). Objetivo: demonstrar
        gestão ativa e orientação por dados. Para referência sobre como consultorias
        estruturam essa comunicação, veja o artigo sobre{' '}
        <Link href="/blog/aumentar-retencao-clientes-inteligencia-editais" className="text-brand-navy dark:text-brand-blue hover:underline">
          retenção de clientes com inteligência em editais
        </Link>.
      </p>

      <h3>Relatório trimestral — estratégico</h3>

      <p>
        Cinco a oito páginas, idealmente apresentado em reunião. Conteúdo: ROI acumulado,
        evolução comparativa dos KPIs, benchmarks de mercado, recomendações estratégicas
        (expandir para novos setores, ajustar faixa de valor alvo, explorar novos órgãos).
        Objetivo: renovar o contrato. Este é o relatório que o gestor do cliente vai
        apresentar à diretoria para justificar a continuidade do investimento.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Benchmarks de KPIs por perfil de consultoria</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>Consultoria individual (1-2 pessoas):</strong> Taxa de adjudicação 12-18%, 15-25 editais triados/semana, ROI semestral 400-800% (fonte: estimativa setorial, associações de consultores)</li>
          <li><strong>Consultoria de médio porte (3-8 pessoas):</strong> Taxa de adjudicação 18-28%, 40-80 editais triados/semana, ROI semestral 800-1.500%</li>
          <li><strong>Consultoria com ferramentas de automação:</strong> Taxa de adjudicação 22-32%, 100-200 editais triados/semana, ROI semestral 1.000-2.500%</li>
          <li><strong>Valor médio adjudicado por pregão (2024):</strong> R$ 185.000 (materiais) e R$ 340.000 (serviços continuados) — fonte: PNCP, dados consolidados 2024</li>
        </ul>
      </div>

      <p>
        A diferença entre uma consultoria que o cliente mantém e uma que o cliente substitui
        quase nunca é técnica. É de comunicação. Consultorias que dominam a linguagem de
        dados e apresentam performance de forma estruturada criam uma barreira de saída
        natural: o cliente sabe exatamente o que está recebendo, e trocar de consultoria
        significa perder essa visibilidade. Para aprofundar como a análise de editais gera
        diferencial competitivo, veja o artigo sobre{' '}
        <Link href="/blog/analise-edital-diferencial-competitivo-consultoria" className="text-brand-navy dark:text-brand-blue hover:underline">
          análise de edital como diferencial competitivo
        </Link>.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">O SmartLic gera dashboards e relatórios que comprovam seu valor ao cliente</p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Analytics integrados, histórico de buscas e relatórios Excel estilizados que você pode personalizar e enviar ao cliente. Dados concretos, não justificativas.
        </p>
        <Link
          href="/signup?source=blog&article=usar-dados-provar-eficiencia-licitacoes&utm_source=blog&utm_medium=cta&utm_content=usar-dados-provar-eficiencia-licitacoes&utm_campaign=consultorias"
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

      <h3>Quais são os principais KPIs para uma consultoria de licitação?</h3>
      <p>
        Os oito KPIs essenciais são: taxa de adjudicação, tempo médio de triagem, taxa de
        descarte, valor total adjudicado, ROI do serviço, tempo de resposta, diversificação
        de órgãos e taxa de reincidência. Juntos, eles cobrem eficácia (o cliente está
        vencendo?), eficiência (com qual custo?) e sustentabilidade (o portfólio está
        diversificado?).
      </p>

      <h3>Qual a taxa de adjudicação média de consultorias de licitação no Brasil?</h3>
      <p>
        A média do mercado B2G fica entre 8% e 12%, segundo dados do Painel de Compras do
        Governo Federal. Consultorias com seleção estratégica de editais e análise de
        viabilidade reportam taxas entre 18% e 30%. A diferença está na qualidade da
        triagem, não na qualidade da documentação.
      </p>

      <h3>Como calcular o ROI da consultoria para apresentar ao cliente?</h3>
      <p>
        Fórmula: (Valor Total Adjudicado - Custo Total) / Custo Total x 100. Custo total
        inclui honorários da consultoria mais custos de proposta. Apresente em acumulado
        trimestral ou semestral para suavizar a variabilidade do ciclo de licitações. Um
        ROI saudável fica entre 500% e 2.000% no semestre.
      </p>

      <h3>Com que frequência devo apresentar relatórios ao cliente?</h3>
      <p>
        Três cadências: semanal (operacional — editais triados e status de processos),
        mensal (tático — KPIs com evolução e análise de vitórias/derrotas) e trimestral
        (estratégico — ROI acumulado, benchmarks e recomendações). O relatório trimestral
        é o mais crítico para retenção, pois é usado pelo cliente para justificar o
        investimento internamente.
      </p>

      <h3>O que é taxa de descarte e por que é um KPI positivo?</h3>
      <p>
        Taxa de descarte é o percentual de editais descartados após análise de viabilidade.
        Uma taxa de 60% a 80% indica que a consultoria está evitando que o cliente
        desperdice recursos em oportunidades de baixo retorno. Cada edital descartado
        economiza entre R$ 800 e R$ 2.500 em custos de proposta. É valor gerado pela
        curadoria, não pelo volume.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
