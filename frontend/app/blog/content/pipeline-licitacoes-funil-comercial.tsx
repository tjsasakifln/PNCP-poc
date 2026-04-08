import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-13: Pipeline de Licitações como Funil Comercial
 * Target: 2,500-3,000 words | Category: Empresas B2G
 */
export default function PipelineLicitacoesFunilComercial() {
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
                name: 'Qual a diferença entre um pipeline de licitações é um CRM tradicional?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O pipeline de licitações segue etapas reguladas por lei (publicação, habilitação, julgamento, adjudicação), com prazos definidos em edital e critérios objetivos de avaliação. Diferentemente do CRM B2B, não há negociação direta com o comprador, é o processo decisorio e transparente e auditável. A ferramenta precisa refletir essas particularidades.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quantas licitações um pipeline saudável deve conter simultaneamente?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Depende da capacidade operacional da equipe. Uma regra prática e manter entre 3x e 5x o número de contratos que a empresa deseja fechar por trimestre. Se a meta é 4 contratos no trimestre é a taxa de conversão histórica e 20%, o pipeline deve conter pelo menos 20 oportunidades ativas distribuidas entre as etapas.',
                },
              },
              {
                '@type': 'Question',
                name: 'E possível implementar um pipeline de licitações em planilha?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, e muitas empresas começam assim. O problema é que planilhas não oferecem alertas automáticos de prazo, não consolidam fontes de dados e exigem atualização manual constante. Para equipes que gerenciam até 10 oportunidades simultâneas, a planilha funciona. Acima disso, o risco de perder prazos e duplicar esforços cresce significativamente.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a taxa de conversão média em funis de licitação pública?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A taxa de conversão média do mercado B2G brasileiro fica entre 8% e 15% (prospecção até adjudicação). Empresas com processos estruturados de triagem e análise de viabilidade reportam taxas entre 20% e 35%. A diferença está na qualidade da seleção inicial, não no volume de participações.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto tempo leva para implementar um pipeline de licitações funcional?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Com disciplina e ferramentas adequadas, um pipeline básico pode estar operacional em 30 dias. As duas primeiras semanas são dedicadas a definir etapas, critérios de avanço e métricas. As duas semanas seguintes servem para popular o pipeline com oportunidades reais e calibrar os filtros de triagem.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A maioria das empresas que atua no mercado B2G trata a participação em
        licitações como uma sequência de eventos isolados: apareceu um edital,
        alguém analisa, a equipe decide se participa, elabora a proposta e torce
        pelo resultado. Esse modelo reativo tem um problema fundamental: ele não
        oferece previsibilidade de receita. Empresas que faturam consistentemente
        com contratos públicos operam de forma diferente. Elas tratam licitações
        como um funil comercial estruturado, com etapas definidas, métricas de
        conversão e gestão ativa de oportunidades. Este artigo mostra como
        construir esse pipeline na prática.
      </p>

      <h2>Por que licitação precisa de pipeline</h2>

      <p>
        No mercado B2B privado, nenhuma empresa séria levaria gestão comercial
        sem um funil de vendas. Existe prospecção, qualificação, proposta,
        negociação e fechamento. Cada etapa tem métricas, responsáveis e prazos.
        O mercado B2G, por alguma razão, resiste a aplicar a mesma lógica.
      </p>

      <p>
        O resultado dessa resistência é visível: equipes sobrecarregadas que não
        sabem quantas oportunidades estão em andamento, gestores que não
        conseguem prever o faturamento do próximo trimestre, e analistas que
        gastam tempo igual em editais de R$ 50 mil e de R$ 5 milhões. Sem
        pipeline, não há priorização. Sem priorização, não há eficiência.
      </p>

      <p>
        A verdade é que licitação não é sorte. É processo. Empresas com
        processos estruturados de gestão de oportunidades apresentam taxas de
        adjudicação significativamente superiores as que operam de forma reativa.
        Segundo levantamento da Associação Brasileira de Empresas de Tecnologia
        da Informação e Comunicação (Brasscom, 2024), empresas de TI com
        processos formalizados de gestão de licitações reportam taxa de
        adjudicação média de 23%, contra 9% das que operam sem processo definido.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: funil de licitações no Brasil</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• O PNCP registrou mais de 1,2 milhão de contratações publicadas em 2025, um crescimento de 38% em relação a 2024 (Fonte: Painel PNCP, dados consolidados dez/2025).</li>
          <li>• Empresas B2G com pipeline estruturado reportam taxa de conversão entre 20% e 35%, contra 8%-15% da média do mercado (Fonte: Brasscom, Pesquisa Setorial de Compras Públicas, 2024).</li>
          <li>• O tempo médio entre publicação do edital e abertura de propostas em pregões eletrônicos é de 8 a 15 dias úteis, exigindo processos ágeis de triagem (Fonte: Tribunal de Contas da União, Relatório de Fiscalização de Compras, 2024).</li>
        </ul>
      </div>

      <h2>As 5 etapas do pipeline de licitações</h2>

      <p>
        Adaptar o conceito de funil comercial para licitações exige respeitar as
        particularidades do processo de compras públicas. As etapas não são
        idênticas as de um CRM B2B, mas a lógica é a mesma: cada oportunidade
        avança por estágios com critérios claros de progressao e descarte.
      </p>

      <h3>Etapa 1: Prospecção</h3>

      <p>
        A prospecção no mercado B2G é o monitoramento sistemático de editais
        publicados nos portais oficiais: PNCP, Portal de Compras Públicas,
        ComprasGov e portais estaduais. O objetivo não é ler todos os editais,
        mas capturar aqueles que correspondem ao perfil da empresa em termos de
        objeto, região, modalidade e faixa de valor.
      </p>

      <p>
        Nessa etapa, o volume é alto e a qualidade é baixa. Uma empresa do setor
        de informática que monitora 10 estados pode encontrar 200 a 500
        publicações relevantes por semana. O papel da prospecção e alimentar o
        funil, não qualificar. A qualificação vem na etapa seguinte. Ferramentas
        de{' '}
        <Link href="/features">
          busca multi-fonte com classificação setorial
        </Link>{' '}
        automatizam essa etapa e reduzem o esforço manual de captura.
      </p>

      <h3>Etapa 2: Triagem</h3>

      <p>
        A triagem é o filtro mais crítico do pipeline. Aqui, cada oportunidade
        capturada na prospecção e avaliada contra critérios objetivos de
        viabilidade. Os quatro fatores fundamentais são: adequação da modalidade,
        prazo disponível para preparação, faixa de valor compatível com o porte
        da empresa e viabilidade geográfica.
      </p>

      <p>
        O objetivo da triagem e eliminar rapidamente as oportunidades
        inadequadas. Uma triagem eficiente descarta entre 60% e 80% dos editais
        capturados na prospecção. Isso não é desperdício de prospecção; e
        exatamente o funcionamento esperado de um funil. O artigo sobre{' '}
        <Link href="/blog/como-aumentar-taxa-vitória-licitações">
          como aumentar a taxa de vitória
        </Link>{' '}
        detalha os critérios de triagem que impactam diretamente a conversão.
      </p>

      <h3>Etapa 3: Análise</h3>

      <p>
        As oportunidades que sobrevivem a triagem entram na fase de análise
        detalhada. Aqui, a equipe le o edital completo, verifica requisitos de
        habilitação, analisa o termo de referência, levanta custos e avalia a
        competitividade da empresa para aquele objeto específico.
      </p>

      <p>
        A análise é a etapa mais intensiva em tempo e conhecimento técnico. Um
        edital complexo pode exigir 4 a 8 horas de análise detalhada. Por isso,
        a qualidade da triagem na etapa anterior é tão importante: cada edital
        que chega a análise sem merecimento consome recursos que poderiam ser
        aplicados em oportunidades melhores.
      </p>

      <BlogInlineCTA slug="pipeline-licitações-funil-comercial" campaign="b2g" />

      <h3>Etapa 4: Proposta</h3>

      <p>
        Com a análise positiva, a equipe elabora a proposta comercial e reune a
        documentação de habilitação. Essa etapa envolve precificação, redação
        técnica, coleta de certidões e atestados, e revisão final antes do
        envio. O prazo entre a decisão de participar é a data de abertura e
        frequentemente curto, o que exige processos internos ágeis.
      </p>

      <p>
        Empresas com pipeline estruturado mantém documentação-base atualizada
        permanentemente (certidões, atestados, balancos), reduzindo o tempo de
        preparação de proposta em até 40%. Essa prática transforma a etapa de
        proposta de um gargalo em uma operação previsível.
      </p>

      <h3>Etapa 5: Acompanhamento</h3>

      <p>
        Após o envio da proposta, a oportunidade entra em acompanhamento.
        Isso inclui monitorar a sessao pública, responder a diligências,
        acompanhar recursos e impugnações, e validar o resultado da
        adjudicação. O acompanhamento não termina na adjudicação: a
        homologação, a assinatura do contrato é o primeiro faturamento
        completam o ciclo.
      </p>

      <p>
        Um erro comum e abandonar o acompanhamento após a adjudicação. Contratos
        podem ser anulados, recursos podem reverter resultados, e atrasos na
        homologação podem afetar o planejamento financeiro. O pipeline so
        considera a oportunidade concluída quando há contrato assinado.
      </p>

      <h2>Metricas de cada etapa</h2>

      <p>
        Um pipeline sem métricas é apenas uma lista organizada. O valor real do
        funil está na capacidade de medir a eficiência de cada etapa e
        identificar gargalos. As métricas essenciais são tres: taxa de
        conversão entre etapas, tempo médio de permanência em cada estagio e
        volume de oportunidades ativas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Benchmarks de conversão por etapa (referência para empresas B2G de médio porte)</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• <strong>Prospecção para Triagem:</strong> 100% (toda oportunidade capturada e triada)</li>
          <li>• <strong>Triagem para Análise:</strong> 20% a 40% (60%-80% descartados na triagem)</li>
          <li>• <strong>Análise para Proposta:</strong> 50% a 70% (análise detalhada elimina inadequações técnicas)</li>
          <li>• <strong>Proposta para Adjudicação:</strong> 15% a 30% (concorrência e preço definem o resultado)</li>
          <li>• <strong>Conversao total (Prospecção a Adjudicação):</strong> 3% a 8% é normal; acima de 15% indica processo maduro</li>
        </ul>
      </div>

      <p>
        O tempo médio de permanência em cada etapa também é revelador. Se
        oportunidades ficam presas na etapa de análise por mais de 5 dias úteis,
        há um gargalo de capacidade técnica. Se a taxa de conversão entre triagem
        e análise está acima de 60%, a triagem está frouxa e permite editais de
        baixa qualidade avancar.
      </p>

      <h2>O dashboard do setor de licitação: o que medir</h2>

      <p>
        Além das métricas por etapa, o gestor do setor de licitação precisa de
        indicadores consolidados que permitam tomada de decisão estratégica.
        Esses indicadores devem ser acompanhados semanalmente e revisados
        mensalmente.
      </p>

      <h3>Indicadores de volume</h3>

      <p>
        Quantidade de oportunidades ativas no pipeline, distribuidas por etapa.
        Um pipeline saudável tem formato de funil: muitas oportunidades nas
        etapas iniciais e poucas nas finais. Se o formato é de cilindro (mesmo
        volume em todas as etapas), a triagem não está funcionando. Se é de funil
        invertido (mais propostas do que prospecções), há risco de secagem do
        pipeline em semanas futuras.
      </p>

      <h3>Indicadores de valor</h3>

      <p>
        Valor total estimado das oportunidades em cada etapa, ponderado pela
        probabilidade de conversão. Uma oportunidade na etapa de análise com
        valor estimado de R$ 500 mil e probabilidade de 30% representa
        R$ 150 mil em receita potencial ponderada. A soma de todas as
        oportunidades ponderadas fornece a previsão de receita do pipeline.
      </p>

      <h3>Indicadores de velocidade</h3>

      <p>
        Tempo médio do ciclo completo (da prospecção a adjudicação) e tempo
        médio por etapa. Reduzir o tempo de ciclo sem comprometer a qualidade
        da análise é o objetivo central. Empresas que monitoram velocidade
        conseguem identificar rapidamente quando uma oportunidade esta
        estagnada e requer ação.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Exemplo prático: pipeline de empresa de facilities</p>
        <p className="text-sm text-ink-secondary mb-3">
          Uma empresa de facilities com faturamento anual de R$ 8 milhões em
          contratos públicos opera com o seguinte pipeline:
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• <strong>Prospecção:</strong> 120 editais capturados por mes (monitoramento de 12 UFs)</li>
          <li>• <strong>Triagem:</strong> 35 aprovados (taxa de aprovação de 29%)</li>
          <li>• <strong>Análise:</strong> 20 analisados em detalhe (57% da triagem)</li>
          <li>• <strong>Proposta:</strong> 12 propostas enviadas (60% da análise)</li>
          <li>• <strong>Adjudicação:</strong> 3 contratos fechados por mes (25% das propostas)</li>
        </ul>
        <p className="text-sm text-ink-secondary mt-3">
          Conversao total: 2,5% (3/120). Valor médio por contrato: R$ 220 mil.
          Receita mensal: R$ 660 mil. O pipeline permite prever que, mantendo o
          volume de prospecção é as taxas de conversão, o faturamento anual
          será de aproximadamente R$ 7,9 milhões. Qualquer desvio nas métricas
          intermediarias acende um alerta antes que o impacto chegue ao
          faturamento.
        </p>
      </div>

      <h2>Ferramentas: planilha vs. sistema dedicado</h2>

      <p>
        A pergunta mais comum ao implementar um pipeline de licitações e qual
        ferramenta usar. A resposta depende do estagio da empresa é do volume
        de oportunidades gerenciadas.
      </p>

      <h3>Planilha (até 15 oportunidades simultâneas)</h3>

      <p>
        Para equipes pequenas que gerenciam até 15 oportunidades ativas, uma
        planilha bem estruturada funciona. O modelo deve conter: identificação
        do edital (número, órgão, UF), objeto resumido, valor estimado, data de
        abertura, etapa atual, responsável, próxima ação e data limite.
        O problema da planilha aparece na escala: sem alertas automáticos, sem
        consolidação de fontes e sem visão de pipeline, a gestão manual se
        torna frágil e dependente de disciplina individual.
      </p>

      <h3>Sistema dedicado (acima de 15 oportunidades)</h3>

      <p>
        Acima de 15 oportunidades simultâneas, um sistema dedicado oferece
        vantagens decisivas: visão kanban com drag-and-drop entre etapas,
        alertas automáticos de prazo, integração com fontes de dados (PNCP,
        portais), métricas consolidadas e histórico completo. O{' '}
        <Link href="/features">
          SmartLic
        </Link>{' '}
        integra pipeline com busca multi-fonte e classificação por IA, permitindo
        que a oportunidade seja movida da prospecção a triagem com dados de
        viabilidade já preenchidos.
      </p>

      <p>
        A transição de planilha para sistema dedicado deve acontecer quando a
        equipe percebe que esta perdendo prazos, duplicando análises ou não
        consegue responder rapidamente a pergunta: &ldquo;quantas oportunidades
        temos ativas e qual o valor total do pipeline?&rdquo;. Se a resposta
        exige mais de 30 segundos, a planilha já não é suficiente.
      </p>

      <h2>Como implementar em 30 dias</h2>

      <p>
        A implementação de um pipeline de licitações não precisa ser um projeto
        de meses. Com foco e disciplina, é possível ter um funil funcional em
        quatro semanas.
      </p>

      <h3>Semana 1: Definição de etapas e critérios</h3>

      <p>
        Reuna a equipe e defina as etapas do pipeline (as cinco descritas
        anteriormente servem como modelo-base). Para cada etapa, estabeleca os
        critérios de avanço é os critérios de descarte. Documente em uma pagina.
        Não complique: a primeira versao sera ajustada com o uso.
      </p>

      <h3>Semana 2: Configuração da ferramenta</h3>

      <p>
        Escolha a ferramenta (planilha ou sistema) e configure as colunas,
        etapas e campos obrigatorios. Se usar planilha, crie um modelo-padrão
        com validações. Se usar um sistema como o SmartLic, configure os filtros
        de busca para alimentar automaticamente a etapa de prospecção.
      </p>

      <h3>Semana 3: População e calibração</h3>

      <p>
        Popule o pipeline com todas as oportunidades ativas e recentes.
        Classifique cada uma na etapa correta. Execute o processo de triagem
        pela primeira vez usando os critérios definidos na semana 1. Ajuste os
        critérios conforme a realidade: se a triagem esta descartando
        oportunidades que deveriam avancar (ou aprovando as que deveriam ser
        descartadas), recalibre os parametros.
      </p>

      <h3>Semana 4: Metricas e rotina</h3>

      <p>
        Estabeleca a rotina de atualização do pipeline. Uma reuniao semanal de
        15 minutos para revisar o funil e suficiente. Defina quem e responsável
        por cada etapa. Comece a medir as taxas de conversão é os tempos de
        permanência. Após 30 dias, você tera dados suficientes para o primeiro
        ajuste estruturado.
      </p>

      <p>
        O artigo sobre{' '}
        <Link href="/blog/estruturar-setor-licitação-5-milhões">
          como estruturar um setor de licitação
        </Link>{' '}
        complementa essa implementação com o modelo operacional é a definição de
        papeis da equipe. E para entender o que diferência as empresas com
        melhores resultados, veja a análise de{' '}
        <Link href="/blog/empresas-vencem-30-porcento-pregões">
          empresas que vencem 30% dos pregões
        </Link>.
        {' '}Consultorias que oferecem gestão de pipeline como serviço para
        clientes B2G podem se inspirar em como funciona o{' '}
        <Link href="/blog/diagnóstico-eficiência-licitação-serviço-premium">
          diagnóstico de eficiência em licitação como serviço premium
        </Link>.
      </p>

      <h2>Erros comuns na gestão de pipeline</h2>

      <p>
        Mesmo com o pipeline implementado, alguns erros recorrentes comprometem
        sua eficacia. Os mais frequentes são:
      </p>

      <p>
        <strong>Não descartar oportunidades.</strong> O medo de perder uma
        licitação leva equipes a manter oportunidades inadviáveis no pipeline,
        inflando artificialmente o volume é distorcendo as métricas. Um pipeline
        eficiente descarta ativamente. Se uma oportunidade não atende aos
        critérios de triagem, ela deve sair do funil.
      </p>

      <p>
        <strong>Não atualizar o status.</strong> Um pipeline desatualizado e
        pior do que não ter pipeline, porque gera falsa confianca. A
        atualização deve ser diária ou, no mínimo, a cada movimentação
        relevante (avancar etapa, descartar, receber resultado).
      </p>

      <p>
        <strong>Tratar todas as oportunidades igualmente.</strong> Um edital de
        R$ 2 milhões em uma modalidade favorável não deve receber o mesmo nível
        de atenção que um de R$ 80 mil em uma modalidade desconhecida. O
        pipeline deve permitir priorização por valor e probabilidade.
      </p>

      <p>
        <strong>Não usar os dados históricos.</strong> Após 3 a 6 meses de
        operação, o pipeline gera dados suficientes para identificar padrões:
        quais tipos de edital a empresa vence mais, quais regiões são mais
        rentáveis, quais modalidades tem melhor conversão. Ignorar esses dados e
        desperdicar o principal ativo do pipeline.
      </p>

      <h2>Do pipeline a previsibilidade de receita</h2>

      <p>
        O benefício final de um pipeline bem gerenciado não é organização: e
        previsibilidade. Quando a empresa sabe que precisa de 100 oportunidades
        na prospecção para gerar 3 contratos no final do funil, ela pode
        planejar investimentos, contratações e fluxo de caixa com base em dados
        reais.
      </p>

      <p>
        Essa previsibilidade transforma o setor de licitação de um centro de
        custo reativo em um motor de receita previsível. E isso muda a forma
        como a diretoria enxerga o mercado público: não mais como uma aposta,
        mas como um canal comercial com métricas gerenciáveis.
      </p>

      {/* CTA — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          O SmartLic tem pipeline integrado com drag-and-drop
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Gerencie oportunidades da prospecção a adjudicação com visão kanban,
          alertas de prazo e métricas automáticas. Integrado com busca
          multi-fonte e classificação por IA.
        </p>
        <Link
          href="/signup?source=blog&article=pipeline-licitações-funil-comercial&utm_source=blog&utm_medium=cta&utm_content=pipeline-licitações-funil-comercial&utm_campaign=b2g"
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

      <h3>Qual a diferença entre um pipeline de licitações é um CRM tradicional?</h3>
      <p>
        O pipeline de licitações segue etapas reguladas por lei (publicação,
        habilitação, julgamento, adjudicação), com prazos definidos em edital e
        critérios objetivos de avaliação. Diferentemente do CRM B2B, não há
        negociação direta com o comprador, é o processo decisorio e
        transparente e auditável. A ferramenta precisa refletir essas
        particularidades, como prazos legais e modalidades específicas.
      </p>

      <h3>Quantas licitações um pipeline saudável deve conter simultaneamente?</h3>
      <p>
        Depende da capacidade operacional da equipe. Uma regra prática e manter
        entre 3x e 5x o número de contratos que a empresa deseja fechar por
        trimestre. Se a meta é 4 contratos no trimestre é a taxa de conversão
        histórica e 20%, o pipeline deve conter pelo menos 20 oportunidades
        ativas distribuidas entre as etapas.
      </p>

      <h3>E possível implementar um pipeline de licitações em planilha?</h3>
      <p>
        Sim, e muitas empresas começam assim. A planilha funciona para equipes
        que gerenciam até 10-15 oportunidades simultâneas. Acima disso, a
        ausência de alertas automáticos, a falta de consolidação de fontes de
        dados é a necessidade de atualização manual constante tornam a planilha
        um gargalo operacional. A transição para um sistema dedicado deve
        ocorrer quando a equipe percebe que esta perdendo prazos ou duplicando
        esforços.
      </p>

      <h3>Qual a taxa de conversão média em funis de licitação pública?</h3>
      <p>
        A taxa de conversão média do mercado B2G brasileiro fica entre 8% e
        15% considerando o funil completo (prospecção até adjudicação). Empresas
        com processos estruturados de triagem e análise de viabilidade reportam
        taxas entre 20% e 35%. A diferença esta primariamente na qualidade da
        seleção inicial, não no volume de participações.
      </p>

      <h3>Quanto tempo leva para implementar um pipeline de licitações funcional?</h3>
      <p>
        Com disciplina e ferramentas adequadas, um pipeline básico pode estar
        operacional em 30 dias. As duas primeiras semanas são dedicadas a
        definir etapas, critérios de avanço e métricas. As duas semanas
        seguintes servem para popular o pipeline com oportunidades reais e
        calibrar os filtros de triagem. Após 3 meses de operação, os dados
        históricos permitem otimizações mais profundas.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
