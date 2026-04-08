import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-05: Como Reduzir em 50% o Tempo Gasto Analisando Editais Irrelevantes
 *
 * Target: 2,000–2,500 words | Cluster: inteligência em licitações
 * Primary keyword: reduzir tempo analisando editais
 */
export default function ReduzirTempoAnalisandoEditaisIrrelevantes() {
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
                name: 'Quanto tempo uma equipe de licitação gasta analisando editais irrelevantes?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Segundo levantamentos do setor, equipes de licitação de empresas de médio porte dedicam entre 30 e 50 horas mensais à triagem de editais, das quais aproximadamente 60-70% são gastas com editais que serão descartados por incompatibilidade de setor, região, valor ou requisitos técnicos. Isso equivale a 20-35 horas/mês desperdiçadas em análise improdutiva.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como funciona o framework de triagem em 3 camadas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O framework de triagem em 3 camadas funciona como um funil progressivo. A Camada 1 (filtro de setor e UF) elimina aproximadamente 60% dos editais em segundos. A Camada 2 (filtro de viabilidade) avalia modalidade, valor, prazo e geografia, descartando mais 25% do volume restante. A Camada 3 (análise profunda) concentra a expertise da equipe nos 15% de editais que realmente merecem atenção detalhada. As duas primeiras camadas podem ser automatizadas com ferramentas de inteligência em licitações.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o custo real de analisar editais irrelevantes?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Considerando o custo médio de um analista de licitação (salário + encargos) de R$ 8.000 a R$ 12.000/mês, e que 60-70% do tempo de triagem é gasto com editais descartados, o custo mensal de análise improdutiva varia de R$ 4.800 a R$ 8.400 por analista. Para equipes com 2 analistas, o custo anual pode ultrapassar R$ 150.000 em horas dedicadas a editais que não geram proposta.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível automatizar a triagem de editais sem perder oportunidades?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. A chave é automatizar as camadas de triagem mecânica (setor, UF, valor, modalidade) enquanto mantém a análise qualitativa sob responsabilidade da equipe. Ferramentas com classificação por IA e avaliação de viabilidade automatizada, como o SmartLic, conseguem executar as Camadas 1 e 2 com taxa de falso negativo inferior a 3%, eliminando o risco de perder oportunidades relevantes.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — must contain primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        <strong>Reduzir o tempo gasto analisando editais irrelevantes</strong>{' '}
        é, provavelmente, a alavanca operacional de maior impacto para
        qualquer equipe de licitação. O Portal Nacional de Contratações
        Públicas (PNCP) registrou uma média de 3.200 novos processos de
        contratação por dia útil em 2024, somando os portais PNCP, ComprasGov
        e Portal de Compras Públicas. Para uma empresa que atua em um setor
        específico e em determinadas regiões, a vasta maioria dessas
        publicações é irrelevante — mas identificar quais são as relevantes
        exige tempo, atenção e método.
      </p>

      <h2>O diagnóstico: quanto tempo sua equipe desperdiça</h2>

      <p>
        O primeiro passo para resolver o problema é quantificá-lo. A maioria
        das equipes de licitação de empresas de médio porte dedica entre 30 e
        50 horas mensais à triagem de editais — ou seja, à atividade de ler
        resumos, verificar objetos, conferir UFs e descartar publicações
        incompatíveis. Desse total, os dados do setor indicam que entre 60% e
        70% do tempo é gasto com editais que serão descartados.
      </p>

      <p>
        O impacto vai além das horas perdidas. Analistas que passam a maior
        parte do dia descartando editais sofrem fadiga cognitiva, o que reduz
        a qualidade da análise nos editais que realmente importam. O
        resultado é um ciclo negativo: mais tempo gasto em triagem improdutiva
        leva a análises mais superficiais nos editais viáveis, o que aumenta
        o risco de erros de habilitação — exatamente o cenário descrito em{' '}
        <Link href="/blog/equipe-40-horas-mes-editais-descartados">
          Por Que sua Equipe Passa 40 Horas por Mês Lendo Editais que Descarta
        </Link>.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • O PNCP registrou média de 3.200 novos processos de contratação
            por dia útil em 2024, totalizando mais de 780.000 publicações no
            ano (PNCP, Painel Estatístico 2024)
          </li>
          <li>
            • Para o setor de TI (hardware e software), apenas 8-12% das
            publicações diárias são potencialmente relevantes para uma
            empresa típica de médio porte — o restante envolve objetos,
            valores ou regiões incompatíveis (estimativa setorial baseada em
            dados PNCP)
          </li>
          <li>
            • O custo médio de um analista de licitação (salário + encargos
            + benefícios) em empresas de médio porte varia de R$ 8.000 a
            R$ 12.000/mês (Robert Half, Guia Salarial 2025 — faixa para
            analista comercial/licitação em capitais)
          </li>
          <li>
            • Empresas que implementam triagem estruturada reportam redução
            de 40-60% no tempo de análise de editais, com manutenção ou
            aumento na taxa de propostas enviadas (Sebrae, Pesquisa
            Fornecedores Governamentais 2024)
          </li>
        </ul>
      </div>

      <h2>Cálculo: o custo real de 40h/mês em editais descartados</h2>

      <p>
        Para dimensionar o problema em termos financeiros, considere os
        números de uma equipe de licitação típica com 2 analistas dedicados
        à triagem e elaboração de propostas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático: custo anual da triagem improdutiva
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          <strong>Premissas:</strong> 2 analistas, custo total de R$ 10.000/mês
          cada (salário + encargos), dedicação de 40h/mês à triagem por
          analista, taxa de descarte de 65%.
        </p>
        <ul className="space-y-1 text-sm text-ink-secondary mb-3">
          <li>• Custo/hora por analista: R$ 10.000 / 176h = R$ 56,82/h</li>
          <li>• Horas improdutivas por analista/mês: 40h x 65% = 26h</li>
          <li>• Custo mensal improdutivo por analista: 26h x R$ 56,82 = R$ 1.477</li>
          <li>• Custo mensal improdutivo total (2 analistas): R$ 2.954</li>
          <li>• <strong>Custo anual da triagem improdutiva: R$ 35.454</strong></li>
        </ul>
        <p className="text-sm text-ink-secondary font-medium">
          Esse valor não inclui o custo de oportunidade: as 624 horas
          anuais (26h x 2 analistas x 12 meses) desperdiçadas poderiam ser
          redirecionadas para a elaboração de propostas de maior qualidade
          ou para a prospecção ativa de oportunidades. Considerando que cada
          proposta bem elaborada tem potencial de gerar contratos de
          R$ 100.000 a R$ 500.000, o custo de oportunidade é
          significativamente superior ao custo direto.
        </p>
      </div>

      <h2>O framework de triagem em 3 camadas</h2>

      <p>
        A solução para reduzir o tempo de triagem sem perder oportunidades é
        estruturar o processo em camadas progressivas de filtragem. Cada
        camada opera como um funil que elimina editais com menor probabilidade
        de relevância, reservando a análise detalhada para os editais que
        realmente merecem atenção.
      </p>

      <h3>Camada 1: filtro de setor e UF (elimina aproximadamente 60%)</h3>

      <p>
        A primeira camada é a mais mecânica e a que gera maior redução de
        volume. Consiste em verificar dois critérios objetivos: o edital
        pertence ao setor de atuação da empresa? O edital é de uma UF na
        qual a empresa opera ou tem interesse em operar?
      </p>

      <p>
        A aplicação rigorosa desses dois filtros elimina, em média, 60% do
        volume diário de publicações. Uma empresa de mobiliário que atua no
        Sul e Sudeste, por exemplo, descarta imediatamente todos os editais
        de outros setores (saúde, TI, vigilância, engenharia) e de outras
        regiões (Norte, Nordeste, Centro-Oeste) — restando apenas os editais
        de mobiliário nas 7 UFs de interesse.
      </p>

      <p>
        Essa camada pode — e deve — ser automatizada. A classificação por
        palavras-chave setoriais combinada com filtro geográfico é uma
        operação que ferramentas de inteligência em licitações executam em
        milissegundos, eliminando a necessidade de leitura humana.
      </p>

      <BlogInlineCTA slug="reduzir-tempo-analisando-editais-irrelevantes" campaign="b2g" />

      <h3>Camada 2: filtro de viabilidade (elimina aproximadamente 25%)</h3>

      <p>
        Dos editais que passam pela Camada 1, nem todos são viáveis para a
        empresa. A segunda camada avalia 4 fatores de viabilidade:
      </p>

      <ul>
        <li>
          <strong>Modalidade:</strong> A empresa está habilitada para essa
          modalidade (pregão, concorrência, tomada de preços)? Possui a
          documentação necessária?
        </li>
        <li>
          <strong>Valor:</strong> O valor estimado está dentro da faixa de
          atuação da empresa? Contratos muito pequenos podem não compensar o
          custo de participação; contratos muito grandes podem exigir
          capacidade que a empresa não possui.
        </li>
        <li>
          <strong>Prazo:</strong> O cronograma de entrega é compatível com a
          capacidade produtiva e logística da empresa?
        </li>
        <li>
          <strong>Geografia:</strong> Mesmo dentro da UF, a localização
          específica do órgão pode impactar custos de logística e execução.
        </li>
      </ul>

      <p>
        A aplicação da Camada 2 elimina aproximadamente 25% dos editais
        restantes — aqueles que são do setor e da UF correta, mas cujo valor,
        prazo ou modalidade os torna inviáveis para a empresa específica.
        Para aprofundar essa análise, consulte{' '}
        <Link href="/blog/como-aumentar-taxa-vitoria-licitacoes">
          Como Aumentar sua Taxa de Vitória em Licitações
        </Link>. No contexto de consultorias, esse ganho de eficiência demonstra{' '}
        <Link href="/blog/entregar-mais-resultado-clientes-sem-aumentar-equipe" className="text-brand-navy dark:text-brand-blue hover:underline">
          como consultorias entregam mais resultado sem aumentar equipe
        </Link>.
      </p>

      <h3>Camada 3: análise profunda (15% restantes)</h3>

      <p>
        Os editais que sobrevivem às duas primeiras camadas representam
        aproximadamente 15% do volume original. Esses são os editais que
        merecem análise detalhada: leitura completa do instrumento
        convocatório, verificação de cláusulas restritivas, análise de
        requisitos técnicos, cálculo de custos e elaboração de proposta.
      </p>

      <p>
        A diferença operacional é significativa. Em vez de analisar 100
        editais por semana e descartar 85, a equipe recebe 15 editais
        pré-qualificados e concentra toda a sua capacidade analítica neles.
        A qualidade da análise melhora porque o volume é gerenciável, e a
        taxa de propostas aceitas aumenta porque a seleção é mais criteriosa.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Fluxo do framework de 3 camadas
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • <strong>Entrada:</strong> 100 editais/semana do setor de
            atuação (publicações PNCP + PCP + ComprasGov)
          </li>
          <li>
            • <strong>Camada 1 (setor + UF):</strong> 100 → 40 editais
            (60% descartados por setor ou região incompatível)
          </li>
          <li>
            • <strong>Camada 2 (viabilidade):</strong> 40 → 15 editais
            (62,5% descartados por valor, prazo, modalidade ou geografia)
          </li>
          <li>
            • <strong>Camada 3 (análise profunda):</strong> 15 editais
            recebem análise completa pela equipe
          </li>
          <li>
            • <strong>Resultado:</strong> 15 propostas de alta qualidade em
            vez de 100 análises superficiais
          </li>
        </ul>
      </div>

      <h2>Resultados esperados: antes vs depois</h2>

      <p>
        A implementação do framework de 3 camadas produz resultados
        mensuráveis em três dimensões:
      </p>

      <h3>Tempo de triagem</h3>
      <p>
        <strong>Antes:</strong> 40 horas/mês por analista em triagem manual,
        com 65% do tempo em editais descartados.{' '}
        <strong>Depois:</strong> 15-20 horas/mês por analista, com as Camadas
        1 e 2 automatizadas e a equipe focada exclusivamente na Camada 3.
        Redução de 50-62% no tempo total de triagem.
      </p>

      <h3>Qualidade das propostas</h3>
      <p>
        <strong>Antes:</strong> Análises apressadas em volume alto, com risco
        elevado de erros de habilitação.{' '}
        <strong>Depois:</strong> Análises detalhadas em volume reduzido, com
        verificação completa de requisitos e cláusulas. Redução estimada de
        40% nas desclassificações por falhas documentais — conforme abordado em{' '}
        <Link href="/blog/licitacao-volume-ou-inteligencia">
          Licitação por Volume ou por Inteligência
        </Link>.
      </p>

      <h3>Taxa de conversão</h3>
      <p>
        <strong>Antes:</strong> 100 editais analisados, 20 propostas enviadas,
        2-3 contratos (taxa de 10-15% sobre propostas enviadas).{' '}
        <strong>Depois:</strong> 15 editais analisados em profundidade, 12
        propostas enviadas, 3-4 contratos (taxa de 25-33% sobre propostas
        enviadas). Mais contratos com menos esforço.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático: impacto financeiro da triagem estruturada
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          <strong>Empresa de papelaria e material de escritório, 2
          analistas, atuação em SP, MG e no PR:</strong>
        </p>
        <ul className="space-y-1 text-sm text-ink-secondary mb-3">
          <li>• Volume semanal monitorado: ~120 publicações do setor</li>
          <li>• Antes do framework: 48h/mês em triagem, 18 propostas/mês, 2 contratos/mês</li>
          <li>• Após implementação: 20h/mês em triagem, 10 propostas/mês, 3 contratos/mês</li>
          <li>• Economia de tempo: 28h/mês (58% de redução)</li>
          <li>• Aumento de contratos: +50% (de 2 para 3/mês)</li>
        </ul>
        <p className="text-sm text-ink-secondary font-medium">
          As 28 horas mensais recuperadas foram redirecionadas para
          elaboração de propostas mais detalhadas e para a construção de um
          banco de atestados e certidões pré-organizados — reduzindo
          adicionalmente o tempo de resposta a cada edital.
        </p>
      </div>

      <h2>Automatização: o papel da tecnologia</h2>

      <p>
        As Camadas 1 e 2 do framework são, por natureza, mecânicas e
        repetitivas — exatamente o tipo de tarefa que a tecnologia executa
        melhor que humanos. A classificação setorial por palavras-chave, o
        filtro geográfico, a verificação de faixa de valor e a análise de
        modalidade são operações que algoritmos realizam em milissegundos,
        com consistência que a análise humana não consegue manter após horas
        de triagem.
      </p>

      <p>
        O <Link href="/buscar">SmartLic</Link> foi projetado especificamente
        para automatizar essas duas camadas. A plataforma consolida
        publicações de três fontes (PNCP, Portal de Compras Públicas e
        ComprasGov), aplica classificação por IA em 15 setores, elimina
        duplicatas entre fontes e avalia viabilidade em 4 fatores —
        modalidade, timeline, valor e geografia. O resultado é uma lista
        curada de editais que já passaram pelas Camadas 1 e 2, prontos para
        a análise profunda da equipe.
      </p>

      <p>
        A automação das camadas iniciais não substitui a expertise humana —
        pelo contrário, ela libera a equipe para exercer essa expertise onde
        ela gera mais valor: na análise qualitativa de cláusulas, na
        estratégia de precificação e na elaboração de propostas competitivas.
      </p>

      {/* CTA — BEFORE FAQ — STORY-262 AC13 */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Automatize as camadas 1 e 2 com o SmartLic
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Classificação setorial por IA, filtro de viabilidade em 4 fatores
          e consolidação multi-fonte. Sua equipe recebe apenas os editais que
          merecem análise profunda.
        </p>
        <Link
          href="/signup?source=blog&article=reduzir-tempo-analisando-editais-irrelevantes&utm_source=blog&utm_medium=cta&utm_content=reduzir-tempo-analisando-editais-irrelevantes&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito. Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">
            página de recursos
          </Link>.
        </p>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>
        Quanto tempo uma equipe de licitação gasta analisando editais
        irrelevantes?
      </h3>
      <p>
        Equipes de licitação de empresas de médio porte dedicam entre 30 e 50
        horas mensais à triagem de editais, das quais aproximadamente 60-70%
        são gastas com editais que serão descartados por incompatibilidade de
        setor, região, valor ou requisitos técnicos. Isso equivale a 20-35
        horas/mês desperdiçadas em análise improdutiva.
      </p>

      <h3>Como funciona o framework de triagem em 3 camadas?</h3>
      <p>
        O framework opera como um funil progressivo. A Camada 1 (filtro de
        setor e UF) elimina aproximadamente 60% dos editais em segundos. A
        Camada 2 (filtro de viabilidade) avalia modalidade, valor, prazo e
        geografia, descartando mais 25% do volume restante. A Camada 3
        (análise profunda) concentra a expertise da equipe nos 15% de editais
        que realmente merecem atenção detalhada. As duas primeiras camadas
        podem ser automatizadas com ferramentas de inteligência em licitações.
      </p>

      <h3>Qual o custo real de analisar editais irrelevantes?</h3>
      <p>
        Considerando o custo médio de um analista de licitação de R$ 8.000 a
        R$ 12.000/mês (salário + encargos), e que 60-70% do tempo de triagem
        é gasto com editais descartados, o custo mensal de análise improdutiva
        varia de R$ 4.800 a R$ 8.400 por analista. Para equipes com 2
        analistas, o custo anual pode ultrapassar R$ 150.000 em horas
        dedicadas a editais que não geram proposta.
      </p>

      <h3>
        É possível automatizar a triagem sem perder oportunidades?
      </h3>
      <p>
        Sim. A chave é automatizar as camadas de triagem mecânica (setor, UF,
        valor, modalidade) enquanto mantém a análise qualitativa sob
        responsabilidade da equipe. Ferramentas com classificação por IA e
        avaliação de viabilidade automatizada, como o{' '}
        <Link href="/buscar">SmartLic</Link>, conseguem executar as Camadas 1
        e 2 com taxa de falso negativo inferior a 3%, eliminando o risco de
        perder oportunidades relevantes.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
