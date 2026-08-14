import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-06: Vale a Pena Disputar Todas as Licitações do Seu Segmento? A Matemática Real
 *
 * Target: 2,500–3,000 words | Cluster: inteligência em licitações
 * Primary keyword: disputar todas as licitações
 */
export default function DisputarTodasLicitacoesMatematicaReal() {
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
                name: 'Qual o custo médio de participar de uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo médio de participação em um pregão eletrônico varia de R$ 2.500 a R$ 8.000 por processo, considerando horas de analista para triagem e análise do edital, elaboração da proposta técnica e comercial, preparação e atualização de documentação habilitatória, tempo dedicado à sessão do pregão (disputa de lances), e custos administrativos (certidões, autenticações, garantias). Licitações de maior complexidade (concorrências, técnica e preço) podem custar de R$ 10.000 a R$ 25.000 por processo.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a taxa média de adjudicação em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A taxa média de adjudicação (percentual de licitações vencidas sobre o total de participações) varia significativamente conforme a estratégia adotada. Empresas que participam indiscriminadamente de todas as licitações do seu segmento operam com taxas entre 5% e 12%. Empresas seletivas, que aplicam critérios de viabilidade antes de participar, alcançam taxas entre 20% e 35%. A diferença decorre da qualidade da seleção e da capacidade de concentrar recursos nos certames mais compatíveis.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quantas licitações uma empresa deve disputar por ano?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não existe um número universal ideal. O número ótimo depende da capacidade operacional da equipe, do custo médio de participação, da taxa histórica de adjudicação e do valor médio dos contratos do segmento. A análise de ponto de equilíbrio mostra que a maioria das empresas de médio porte maximiza o retorno disputando entre 25 e 45 licitações por ano com seleção criteriosa, em vez de 80 a 120 sem filtro de viabilidade.',
                },
              },
              {
                '@type': 'Question',
                name: 'Disputar mais licitações sempre gera mais contratos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não necessariamente. A relação entre volume de participações e contratos obtidos segue uma curva de rendimento marginal decrescente. Até um determinado ponto, aumentar o volume de participações aumenta o número de contratos. Acima desse ponto, a diluição de recursos entre muitos processos reduz a qualidade das propostas e a taxa de adjudicação cai. Empresas que ultrapassam sua capacidade operacional ótima podem, paradoxalmente, vencer menos licitações ao participar de mais.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como calcular o ROI de participar de licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O cálculo de ROI em licitações considera: (1) investimento total = número de participações x custo médio por participação; (2) receita gerada = número de contratos obtidos x valor médio do contrato x margem líquida; (3) ROI = (receita líquida - investimento total) / investimento total x 100. Uma empresa que gasta R$ 4.500 por participação, disputa 30 licitações/ano, vence 8 (taxa de 27%) com contratos médios de R$ 180.000 e margem de 15%, tem ROI de (R$ 216.000 - R$ 135.000) / R$ 135.000 = 60%.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — must contain primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A premissa de que <strong>disputar todas as licitações</strong> do seu
        segmento é a melhor forma de maximizar contratos públicos é
        intuitivamente atraente — e matematicamente incorreta. A análise
        quantitativa dos custos de participação, das taxas de adjudicação e
        dos retornos efetivos revela que, a partir de determinado volume, cada
        licitação adicional disputada reduz o retorno sobre o investimento
        total. Este artigo apresenta os números reais, compara dois cenários
        operacionais e propõe um método para calcular o número ideal de
        disputas para a sua empresa.
      </p>

      <h2>A ilusão do volume</h2>

      <p>
        O raciocínio mais comum em empresas B2G é probabilístico:
        &ldquo;quanto mais licitações disputarmos, maior a chance de
        vencer&rdquo;. Essa lógica funciona em sistemas onde o custo marginal
        de cada participação é zero — o que não é o caso. Cada licitação
        disputada consome horas de análise, elaboração de proposta,
        preparação documental e, frequentemente, participação em sessões de
        disputa. Esses custos são reais, mensuráveis e cumulativos.
      </p>

      <p>
        O segundo problema da estratégia de volume é a diluição de recursos.
        Uma equipe com capacidade finita que tenta cobrir 100 licitações por
        ano inevitavelmente dedica menos atenção a cada uma do que uma equipe
        que seleciona 30 licitações e concentra esforços. A qualidade da
        proposta diminui proporcionalmente ao volume de processos simultâneos —
        e a qualidade da proposta é o principal determinante da taxa de
        adjudicação. Para uma análise complementar sobre esse dilema, consulte{' '}
        <Link href="/blog/licitacao-volume-ou-inteligencia">
          Licitação por Volume ou por Inteligência: Qual Estratégia Dá mais Lucro
        </Link>.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • O custo médio de participação em um pregão eletrônico
            (incluindo horas de analista, documentação e custos
            administrativos) varia de R$ 2.500 a R$ 8.000 por processo,
            dependendo da complexidade do objeto (Sebrae, Pesquisa Custo de
            Participação em Licitações 2024)
          </li>
          <li>
            • A taxa média de adjudicação de empresas que participam sem
            critério de seleção situa-se entre 5% e 12%, enquanto empresas
            com processo estruturado de triagem alcançam 20% a 35% (TCU,
            Relatório Consolidado de Competitividade em Pregões 2023-2024)
          </li>
          <li>
            • Segundo dados do PNCP (2024), o número médio de participantes
            por pregão eletrônico foi de 6,8 empresas, com mediana de 5 —
            indicando que a competição por edital é significativa e que a
            simples presença não garante resultado
          </li>
          <li>
            • O valor médio de contratos adjudicados em pregões eletrônicos
            para bens e serviços comuns foi de R$ 187.000 em 2024 (PNCP,
            Painel Estatístico de Contratações 2024)
          </li>
        </ul>
      </div>

      <h2>O cálculo completo: custo de participação, probabilidade e valor do contrato</h2>

      <p>
        Para avaliar racionalmente se vale a pena disputar uma licitação, três
        variáveis precisam ser consideradas simultaneamente: o custo de
        participação (investimento), a probabilidade de adjudicação
        (probabilidade) e o valor do contrato multiplicado pela margem líquida
        (retorno).
      </p>

      <p>
        A fórmula do valor esperado por licitação é:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Fórmula de valor esperado</p>
        <p className="text-sm text-ink-secondary mb-2">
          <strong>VE = (P x V x M) - C</strong>
        </p>
        <ul className="space-y-1 text-sm text-ink-secondary">
          <li>• VE = Valor Esperado (lucro esperado por licitação)</li>
          <li>• P = Probabilidade de adjudicação (taxa de vitória)</li>
          <li>• V = Valor do contrato</li>
          <li>• M = Margem líquida estimada</li>
          <li>• C = Custo de participação</li>
        </ul>
        <p className="text-sm text-ink-secondary mt-3">
          Uma licitação só vale a pena quando VE &gt; 0, ou seja, quando
          <strong> P x V x M &gt; C</strong>.
        </p>
      </div>

      <p>
        Essa fórmula revela por que a estratégia de volume pode ser
        prejudicial: ao disputar licitações com baixa probabilidade de
        vitória (P baixo) ou com contratos de valor insuficiente para cobrir
        o custo de participação (V x M menor que C/P), a empresa está
        investindo em processos com valor esperado negativo.
      </p>

      <h2>Cenário 1: empresa que disputa tudo (100 pregões/ano)</h2>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Cenário 1 — Empresa de TI, estratégia de volume
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          <strong>Premissas:</strong> Empresa de hardware e equipamentos de TI,
          atuação nacional, equipe de 3 analistas. Participa de todos os
          pregões identificados no setor, sem filtro de viabilidade.
        </p>
        <ul className="space-y-1 text-sm text-ink-secondary mb-3">
          <li>• Pregões disputados por ano: 100</li>
          <li>• Custo médio por participação: R$ 4.500</li>
          <li>• Investimento anual total: R$ 450.000</li>
          <li>• Taxa de adjudicação: 8% (abaixo da média por diluição de esforço)</li>
          <li>• Contratos obtidos: 8</li>
          <li>• Valor médio por contrato: R$ 180.000</li>
          <li>• Margem líquida: 12% (comprimida pela competição em editais inadequados)</li>
          <li>• Receita líquida total: 8 x R$ 180.000 x 12% = R$ 172.800</li>
        </ul>
        <p className="text-sm text-ink-secondary font-medium">
          <strong>Resultado:</strong> Investimento de R$ 450.000 para retorno
          líquido de R$ 172.800.{' '}
          <strong>ROI = -61,6%</strong> (prejuízo operacional).
        </p>
        <p className="text-sm text-ink-secondary mt-2">
          Mesmo os 8 contratos vencidos não cobrem o custo total de
          participação nos 100 processos. A empresa precisa do faturamento
          bruto dos contratos (R$ 1.440.000) para operar, mas o lucro
          líquido atribuível à atividade de licitação é negativo quando se
          contabiliza o custo de participação em todos os 92 pregões perdidos.
        </p>
      </div>

      <BlogInlineCTA slug="disputar-todas-licitacoes-matematica-real" campaign="b2g" />

      <h2>Cenário 2: empresa seletiva (30 pregões/ano)</h2>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Cenário 2 — Mesma empresa de TI, estratégia seletiva
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          <strong>Premissas:</strong> Mesma empresa, mesma equipe. Aplica
          critérios de viabilidade (setor, valor, modalidade, geografia,
          histórico do órgão) antes de decidir participar. Disputa apenas
          editais com valor esperado positivo.
        </p>
        <ul className="space-y-1 text-sm text-ink-secondary mb-3">
          <li>• Pregões disputados por ano: 30</li>
          <li>• Custo médio por participação: R$ 4.500</li>
          <li>• Investimento anual total: R$ 135.000</li>
          <li>• Taxa de adjudicação: 27% (maior por foco em editais compatíveis)</li>
          <li>• Contratos obtidos: 8</li>
          <li>• Valor médio por contrato: R$ 210.000 (seleção inclui contratos de maior valor)</li>
          <li>• Margem líquida: 15% (propostas mais elaboradas e competitivas)</li>
          <li>• Receita líquida total: 8 x R$ 210.000 x 15% = R$ 252.000</li>
        </ul>
        <p className="text-sm text-ink-secondary font-medium">
          <strong>Resultado:</strong> Investimento de R$ 135.000 para retorno
          líquido de R$ 252.000.{' '}
          <strong>ROI = +86,7%</strong> (lucro operacional).
        </p>
        <p className="text-sm text-ink-secondary mt-2">
          Mesmo número de contratos (8), mas com maior valor médio e maior
          margem — resultado direto da seleção mais criteriosa e da
          dedicação superior a cada proposta. O investimento total é 70%
          menor, e o retorno líquido é 46% superior.
        </p>
      </div>

      <h2>Comparação de ROI: volume vs. inteligência</h2>

      <p>
        A comparação direta entre os dois cenários revela a assimetria da
        estratégia seletiva:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Comparativo: volume vs. inteligência
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • <strong>Pregões disputados:</strong> 100 (volume) vs. 30
            (seletiva) — 70% menos esforço
          </li>
          <li>
            • <strong>Investimento total:</strong> R$ 450.000 vs. R$ 135.000
            — 70% menos investimento
          </li>
          <li>
            • <strong>Contratos obtidos:</strong> 8 vs. 8 — mesmo resultado
          </li>
          <li>
            • <strong>Receita líquida:</strong> R$ 172.800 vs. R$ 252.000
            — 46% mais retorno
          </li>
          <li>
            • <strong>ROI:</strong> -61,6% vs. +86,7% — diferença de 148
            pontos percentuais
          </li>
          <li>
            • <strong>Horas da equipe liberadas:</strong> ~1.400 horas/ano
            (equivalente a quase 1 analista em tempo integral)
          </li>
        </ul>
      </div>

      <p>
        O dado mais relevante é que os dois cenários produzem o mesmo número
        de contratos — 8 por ano. A diferença está no custo para obtê-los e
        na margem líquida de cada contrato. A empresa seletiva gasta menos,
        ganha o mesmo, e lucra mais. O tempo liberado pode ser investido em
        atividades de maior valor: melhoria de propostas, relacionamento com
        órgãos, diversificação geográfica ou desenvolvimento de novos
        segmentos.
      </p>

      <h2>O ponto de equilíbrio</h2>

      <p>
        O ponto de equilíbrio é o número de licitações acima do qual cada
        participação adicional reduz o retorno sobre o investimento total. Ele
        depende de três variáveis específicas da empresa: capacidade
        operacional da equipe, custo médio de participação e taxa de
        adjudicação histórica.
      </p>

      <p>
        A lógica é a seguinte: enquanto a equipe consegue dedicar atenção
        adequada a cada processo, a taxa de adjudicação se mantém estável ou
        cresce. A partir do momento em que o volume supera a capacidade, a
        qualidade das propostas cai e a taxa de adjudicação diminui. O ponto
        de equilíbrio é o momento exato em que o custo marginal de uma
        licitação adicional iguala o retorno marginal esperado.
      </p>

      <p>
        Para a maioria das empresas de médio porte com equipes de 2 a 4
        analistas, a faixa ótima se situa entre 25 e 45 licitações por ano
        — ou seja, 2 a 4 processos simultâneos por mês. Acima desse patamar,
        a curva de rendimento marginal se torna decrescente. Essa análise
        complementa o que abordamos em{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao">
          Como Saber se Vale a Pena Disputar um Pregão
        </Link>, onde detalhamos os 4 critérios de avaliação individual.
      </p>

      <h2>Como definir o número ideal para sua empresa</h2>

      <p>
        O cálculo do número ideal de licitações segue um processo de 4 etapas:
      </p>

      <h3>Etapa 1: Mapeie sua capacidade operacional</h3>
      <p>
        Quantifique as horas disponíveis da equipe para atividades de
        licitação (triagem, análise, elaboração, disputa). Divida pelo tempo
        médio por processo para obter a capacidade máxima mensal. Se a equipe
        tem 320 horas/mês disponíveis e cada processo consome em média 25
        horas, a capacidade é de 12-13 processos/mês — mas a capacidade
        ótima é menor, para garantir qualidade.
      </p>

      <h3>Etapa 2: Calcule seu custo médio de participação</h3>
      <p>
        Some todas as despesas diretas e indiretas de cada participação:
        horas de analista (valoradas pelo custo total do profissional),
        custos de documentação, garantias, deslocamentos e administrativos.
        Inclua o custo proporcional das licitações em que houve sessão de
        disputa mas não houve adjudicação.
      </p>

      <h3>Etapa 3: Levante sua taxa histórica de adjudicação</h3>
      <p>
        Analise os últimos 24 meses de participações: quantas licitações
        disputou e quantas venceu. Se possível, segmente por faixa de valor,
        modalidade e órgão. Identifique os segmentos com maior taxa de
        adjudicação — esses são os que devem receber prioridade na alocação
        de recursos.
      </p>

      <h3>Etapa 4: Aplique a fórmula de valor esperado</h3>
      <p>
        Para cada licitação potencial, calcule o valor esperado:
        VE = (P x V x M) - C. Participe apenas das licitações com VE
        positivo. Classifique as licitações elegíveis por VE decrescente e
        selecione tantas quanto sua capacidade operacional ótima permitir.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático: aplicação da fórmula
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          <strong>Empresa de facilities, custo de participação
          R$ 3.800:</strong>
        </p>
        <ul className="space-y-1 text-sm text-ink-secondary mb-3">
          <li>
            • Pregão A: contrato de R$ 450.000, probabilidade estimada 30%,
            margem 14%.
            VE = (0,30 x 450.000 x 0,14) - 3.800 = R$ 18.900 - R$ 3.800 ={' '}
            <strong>R$ 15.100</strong> (vale participar)
          </li>
          <li>
            • Pregão B: contrato de R$ 85.000, probabilidade estimada 12%,
            margem 10%.
            VE = (0,12 x 85.000 x 0,10) - 3.800 = R$ 1.020 - R$ 3.800 ={' '}
            <strong>-R$ 2.780</strong> (não vale participar)
          </li>
          <li>
            • Pregão C: contrato de R$ 220.000, probabilidade estimada 22%,
            margem 16%.
            VE = (0,22 x 220.000 x 0,16) - 3.800 = R$ 7.744 - R$ 3.800 ={' '}
            <strong>R$ 3.944</strong> (vale participar)
          </li>
        </ul>
        <p className="text-sm text-ink-secondary font-medium">
          Neste exemplo, os Pregões A e C têm valor esperado positivo e
          devem ser priorizados. O Pregão B, apesar de ser do setor correto,
          tem valor esperado negativo — a combinação de valor baixo,
          probabilidade baixa e custo de participação torna-o
          financeiramente inviável. Esse é exatamente o tipo de edital que a
          estratégia de volume faria a empresa disputar desnecessariamente.
        </p>
      </div>

      <h2>A curva de rendimento marginal</h2>

      <p>
        O conceito econômico de rendimento marginal decrescente aplica-se
        diretamente à estratégia de licitações. Os primeiros pregões
        selecionados são, naturalmente, os de maior valor esperado — aqueles
        com melhor combinação de probabilidade, valor e margem. À medida que
        a empresa expande o volume de participações, os pregões adicionais
        têm valor esperado progressivamente menor, até que o valor esperado
        se torna negativo.
      </p>

      <p>
        A curva tem formato de sino assimétrico: o retorno total cresce
        rapidamente nas primeiras licitações selecionadas, atinge um platô
        na faixa ótima e começa a declinar quando o volume ultrapassa a
        capacidade da equipe. O ponto de máximo retorno coincide,
        tipicamente, com 60-70% da capacidade operacional máxima — não com
        100%, pois é necessário preservar margem para imprevistos, aditivos
        contratuais e oportunidades extraordinárias.
      </p>

      <p>
        Empresas que compreendem essa dinâmica investem em melhorar a
        qualidade da seleção (identificar os editais de maior valor esperado)
        em vez de aumentar a quantidade de participações. Ferramentas de
        inteligência em licitações, como o{' '}
        <Link href="/features">SmartLic</Link>, viabilizam essa estratégia
        ao automatizar a triagem por setor, viabilidade e relevância —
        permitindo que a equipe concentre esforço nos pregões que realmente
        justificam o investimento. Para complementar essa análise com o custo
        invisível das disputas equivocadas, leia{' '}
        <Link href="/blog/custo-invisivel-disputar-pregoes-errados">
          O Custo Invisível de Disputar Pregões Errados
        </Link>. Para ver{' '}
        <Link href="/blog/consultorias-modernas-inteligencia-priorizar-oportunidades">
          como consultorias modernas priorizam oportunidades com inteligência
        </Link>, a lógica de seleção apresentada aqui aplica-se igualmente a
        quem opera no modelo de assessoria.
      </p>

      {/* CTA — BEFORE FAQ — STORY-262 AC13 */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Calcule automaticamente quais licitações valem seu investimento
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic avalia viabilidade em 4 fatores (modalidade, timeline,
          valor e geografia) e classifica editais por relevância setorial com
          IA, para que sua equipe dispute apenas os pregões com retorno
          esperado positivo.
        </p>
        <Link
          href="/consultoria-b2g?source=blog&article=disputar-todas-licitacoes-matematica-real&utm_source=blog&utm_medium=cta&utm_content=disputar-todas-licitacoes-matematica-real&utm_campaign=b2g"
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

      <h3>Qual o custo médio de participar de uma licitação?</h3>
      <p>
        O custo médio de participação em um pregão eletrônico varia de
        R$ 2.500 a R$ 8.000 por processo, considerando horas de analista para
        triagem e análise do edital, elaboração da proposta técnica e
        comercial, preparação e atualização de documentação habilitatória,
        tempo dedicado à sessão do pregão (disputa de lances) e custos
        administrativos (certidões, autenticações, garantias). Licitações de
        maior complexidade (concorrências, técnica e preço) podem custar de
        R$ 10.000 a R$ 25.000 por processo.
      </p>

      <h3>Qual a taxa média de adjudicação em licitações?</h3>
      <p>
        A taxa média de adjudicação varia significativamente conforme a
        estratégia adotada. Empresas que participam indiscriminadamente de
        todas as licitações do seu segmento operam com taxas entre 5% e 12%.
        Empresas seletivas, que aplicam critérios de viabilidade antes de
        participar, alcançam taxas entre 20% e 35%. A diferença decorre da
        qualidade da seleção e da capacidade de concentrar recursos nos
        certames mais compatíveis.
      </p>

      <h3>Quantas licitações uma empresa deve disputar por ano?</h3>
      <p>
        O número ideal depende da capacidade operacional da equipe, do custo
        médio de participação, da taxa histórica de adjudicação e do valor
        médio dos contratos do segmento. A análise de ponto de equilíbrio
        mostra que a maioria das empresas de médio porte maximiza o retorno
        disputando entre 25 e 45 licitações por ano com seleção criteriosa,
        em vez de 80 a 120 sem filtro de viabilidade.
      </p>

      <h3>Disputar mais licitações sempre gera mais contratos?</h3>
      <p>
        Não necessariamente. A relação entre volume de participações e
        contratos obtidos segue uma curva de rendimento marginal decrescente.
        Até determinado ponto, aumentar o volume aumenta o número de
        contratos. Acima desse ponto, a diluição de recursos reduz a
        qualidade das propostas e a taxa de adjudicação cai. Empresas que
        ultrapassam sua capacidade operacional ótima podem, paradoxalmente,
        vencer menos licitações ao participar de mais.
      </p>

      <h3>Como calcular o ROI de participar de licitações?</h3>
      <p>
        O cálculo considera: investimento total (número de participações
        vezes custo médio por participação), receita gerada (contratos
        obtidos vezes valor médio vezes margem líquida) e ROI = (receita
        líquida menos investimento total) dividido pelo investimento total.
        Uma empresa que gasta R$ 4.500 por participação, disputa 30
        licitações/ano, vence 8 (taxa de 27%) com contratos médios de
        R$ 180.000 e margem de 15%, obtém ROI de 60%. O{' '}
        <Link href="/features">SmartLic</Link> ajuda a maximizar esse
        retorno ao filtrar automaticamente os editais com maior valor
        esperado.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
